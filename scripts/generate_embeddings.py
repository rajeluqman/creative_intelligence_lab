"""Silver chunk text -> Gemini embeddings -> gold/chunk_embedding (BYO, content-hash-gated).

ADR-005 §B: embeddings are "bring-your-own (Gemini), generated in the ELT and persisted in
Gold S3" — NOT Cortex EMBED_TEXT, so there is never a second metered embedding surface. Cost
discipline item 3: single-sourced, content-hash-gated, no re-embed on unchanged chunks (mirrors
run_gemini_extract.py's asset-grain skip-existing, here at chunk grain since the embedding call
is genuinely one-vector-per-chunk-text, not a re-litigation of the asset-grain Bronze ruling).

Reads Silver (`silver/int_chunk_cleaned/<client_id>/...`, written by the int_chunk_cleaned
dbt model) directly via DuckDB httpfs — same direct-S3-read pattern run_gemini_extract.py uses
for Landing, just one layer up. Writes back to `gold/chunk_embedding/<client_id>/...` (the same
path models/staging/_sources.yml's `gold.chunk_embedding` source points dbt at), so
fact_chunk.sql's LEFT JOIN picks it up on the next `dbt build` with zero model change.

Fixed-size FLOAT[EMBEDDING_DIM] (DuckDB ARRAY, not LIST) on write — required for the VSS
extension's HNSW index (array_distance/HNSW need a fixed-width array, not a variable-length
list). output_dimensionality is pinned in the embed call so this width never silently drifts
between runs.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
import time
from pathlib import Path

import duckdb
from google import genai
from google.genai import errors, types

sys.path.insert(0, str(Path(__file__).parent))
from env_guard import assert_safe  # noqa: E402

EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = 768  # fixed width — must match across every stored + query embedding (VSS requirement)
# Free tier's embed_content_free_tier_requests quota is metered PER-MINUTE and, empirically (a
# batch of 100 texts in one call exhausted the 100/min ceiling immediately), per CONTENT ITEM, not
# per HTTP call. Small batch + backoff-retry on 429 (unlike run_gemini_extract.py's HARD-DAILY
# generate_content quota, this one is per-minute and backoff genuinely recovers it).
BATCH_SIZE = 20
MAX_RETRIES = 5
DEFAULT_RETRY_SEC = 65.0


def _retry_delay_sec(exc: "errors.ClientError") -> float:
    match = re.search(r"retryDelay': '(\d+(?:\.\d+)?)s'", str(exc))
    return float(match.group(1)) + 5 if match else DEFAULT_RETRY_SEC


def _embed_batch(gclient: "genai.Client", texts: list[str]):
    for attempt in range(MAX_RETRIES):
        try:
            return gclient.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT", output_dimensionality=EMBEDDING_DIM
                ),
            )
        except errors.ClientError as e:
            if e.code != 429 or attempt == MAX_RETRIES - 1:
                raise
            delay = _retry_delay_sec(e)
            print(f"generate_embeddings: 429 rate-limited, sleeping {delay:.0f}s (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)


def _silver_location(bucket: str, client_id: str) -> str:
    return f"s3://{bucket}/silver/int_chunk_cleaned/{client_id}/int_chunk_cleaned.parquet"


def _gold_location(bucket: str, client_id: str) -> str:
    return f"s3://{bucket}/gold/chunk_embedding/{client_id}/chunk_embedding.parquet"


def _s3_object_exists(bucket: str, key: str) -> bool:
    import boto3
    s3 = boto3.client("s3")
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def _connect_httpfs() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(
        f"CREATE OR REPLACE SECRET s3_secret (TYPE S3, PROVIDER CREDENTIAL_CHAIN, "
        f"REGION '{os.environ.get('AWS_REGION', '')}');"
    )
    return con


def generate_embeddings(client_id: str) -> int:
    """Returns the number of chunks newly embedded (0 = fully cached, no API spend)."""
    assert_safe()
    bucket = os.environ["S3_BUCKET"]
    con = _connect_httpfs()

    silver_loc = _silver_location(bucket, client_id)
    chunks = con.execute(
        f"select chunk_id, transcript_segment from read_parquet('{silver_loc}')"
    ).fetchall()
    if not chunks:
        print(f"generate_embeddings: no Silver chunks found at {silver_loc}")
        return 0

    gold_key = f"gold/chunk_embedding/{client_id}/chunk_embedding.parquet"
    gold_loc = _gold_location(bucket, client_id)
    existing: dict[str, tuple[str, list[float]]] = {}
    if _s3_object_exists(bucket, gold_key):
        rows = con.execute(
            f"select chunk_id, content_hash, embedding from read_parquet('{gold_loc}')"
        ).fetchall()
        existing = {r[0]: (r[1], list(r[2])) for r in rows}

    to_embed: list[tuple[str, str, str]] = []  # (chunk_id, text, content_hash)
    kept: list[tuple[str, str, list[float]]] = []  # (chunk_id, content_hash, embedding)
    for chunk_id, text in chunks:
        content_hash = hashlib.sha256((text or "").encode()).hexdigest()
        cached = existing.get(chunk_id)
        if cached and cached[0] == content_hash:
            kept.append((chunk_id, content_hash, cached[1]))  # unchanged — no re-embed (cost firewall)
        else:
            to_embed.append((chunk_id, text, content_hash))

    if not to_embed:
        print(f"generate_embeddings: all {len(chunks)} chunk(s) already embedded, no API calls.")
        return 0

    gclient = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    new_rows: list[tuple[str, str, list[float]]] = []
    for i in range(0, len(to_embed), BATCH_SIZE):
        batch = to_embed[i : i + BATCH_SIZE]
        response = _embed_batch(gclient, [text for _, text, _ in batch])
        for (chunk_id, _, content_hash), emb in zip(batch, response.embeddings):
            new_rows.append((chunk_id, content_hash, list(emb.values)))

    all_rows = kept + new_rows
    con.execute("create table chunk_embeddings(chunk_id varchar, content_hash varchar, embedding double[])")
    con.executemany("insert into chunk_embeddings values (?, ?, ?)", all_rows)
    con.execute(
        f"""
        copy (
            select chunk_id, content_hash, cast(embedding as float[{EMBEDDING_DIM}]) as embedding
            from chunk_embeddings
        ) to '{gold_loc}' (format parquet)
        """
    )

    print(
        f"generate_embeddings: embedded {len(new_rows)} new/changed chunk(s), "
        f"kept {len(kept)} cached, wrote {len(all_rows)} total rows to {gold_loc}"
    )
    return len(new_rows)


if __name__ == "__main__":
    cid = os.environ.get("CLIENT_ID", "")
    if not cid:
        sys.exit("usage: set CLIENT_ID env var (no default — multi-client misroute guard)")
    print(generate_embeddings(cid))
