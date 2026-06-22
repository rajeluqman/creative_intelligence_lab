"""S3 video -> Gemini (Flash, responseSchema) -> bronze_asset_raw (verbatim JSON).

Path A's extraction step (architecture/STACK_AND_FLOW.md §2). One Gemini call per asset,
structured output, written as Bronze parquet — ONE ROW PER ASSET, raw_response = the
verbatim Gemini JSON envelope, completely untouched. The explosion into one row per chunk
happens downstream in models/staging/stg_gemini_raw.sql (the Bronze->Silver dbt hop), per
ADR-003 and @data-architect's ruling below. Idempotent: re-running an already-extracted
asset_id is a no-op (cost firewall #2 — never re-call Gemini on Bronze that already exists).

⚠️ SDK choice: `google-generativeai` (what requirements.txt previously pinned) is fully
end-of-life — "no longer receiving updates or bug fixes" per its own deprecation notice.
This script uses `google-genai` (the current, supported SDK) instead. requirements.txt
updated; confirmed nothing else in the repo imported the old package, so it was replaced
outright, not left alongside it.

Bronze grain — RESOLVED by @data-architect ruling (2026-06-22, VETOED): an earlier draft of
this script wrote chunk-grain Bronze rows, matching what models/staging/stg_gemini_raw.sql
happened to already assume (a `select` with no `unnest()`). @data-architect vetoed that as a
re-litigation of ADR-003's own "Rejected alternatives" row ("Chunk in the Python extraction
step (pre-Bronze)" — explicitly rejected: "the raw artifact would no longer be the verbatim
API response"). Bronze is asset-grain; stg_gemini_raw.sql now does the actual unnest/explode
that its own header comment always promised. See that file for the SQL-side half of this fix.

dbt-side S3 source wiring — FIXED by @senior-data-engineer (2026-06-22): profiles.yml +
models/staging/_sources.yml now point `source('bronze','bronze_asset_raw')` at
s3://$S3_BUCKET/bronze/<client_id>/asset_raw/*.parquet, matching the path this script writes
to. Verified via `dbt parse`/`dbt compile`/`dbt seed` — see PROJECT_STATUS.md.

Telemetry (tokens/cost/timing) is logged per-run to
s3://$S3_BUCKET/bronze/<client_id>/extraction_run_log/<asset_id>_<run_id>.json — append-only,
mirroring the bronze_ad_performance_raw "verbatim capture" pattern. NOT wired into
fact_extraction_run.sql (still `where 1=0` there) — that's a dbt-side follow-up, and Gold-
layer model changes need @data-architect sign-off per CLAUDE.md governance, not a unilateral
edit here. api_cost is intentionally left null — hardcoding a per-token rate that goes stale
silently is worse than no number; tokens_in/tokens_out are the real ground truth, priced
downstream against whatever the current rate card is.
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import boto3
import duckdb
import pandas as pd
from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).parent))
from env_guard import assert_safe  # noqa: E402
from ingest_drive_to_s3 import MANIFEST_PATH, _s3_exists  # noqa: E402

# Must match great_expectations/expectations/silver_chunk.json's value_set exactly.
SENTIMENT_ENUM = ["energetic", "frustrated", "aspirational", "neutral", "urgent", "calm"]

EXTRACTION_PROMPT = """Watch this advertising video and segment it into semantic chunks —
meaning-bounded marketing beats (e.g. Hook, Problem, Solution, Social Proof, CTA), NOT
fixed-duration slices. Cut chunk boundaries where the message/intent changes, not on a
timer. For each chunk, return:
- start_sec / end_sec: the chunk's boundaries in the video, in seconds.
- transcript_segment: the spoken dialogue or voiceover for this chunk, verbatim.
- chunk_theme: what kind of beat this is (e.g. Hook, Problem, Solution, Social Proof, CTA).
- sentiment: the emotional tone — choose exactly one from this fixed set: """ + ", ".join(SENTIMENT_ENUM) + """.
- standalone_score: 1-5 — how safe is this chunk to reuse on its own, outside this ad
  (1 = makes no sense without context, 5 = a complete message by itself).
- next_compatible_themes: theme names that could validly follow this chunk in a DIFFERENT
  ad without breaking the message (mix-and-match compatibility).
- keywords: notable terms/product names/claims mentioned in this chunk.
If the video has no discernible ad content, return an empty chunks list — do not force
chunks onto unrelated footage."""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "chunks": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "start_sec": {"type": "NUMBER"},
                    "end_sec": {"type": "NUMBER"},
                    "transcript_segment": {"type": "STRING"},
                    "chunk_theme": {"type": "STRING"},
                    "sentiment": {"type": "STRING", "enum": SENTIMENT_ENUM},
                    "standalone_score": {"type": "INTEGER"},
                    "next_compatible_themes": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "keywords": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["start_sec", "end_sec", "transcript_segment", "chunk_theme",
                             "sentiment", "standalone_score"],
            },
        }
    },
    "required": ["chunks"],
}

_MIME_BY_EXT = {".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm", ".avi": "video/x-msvideo"}


def _bronze_key(asset_id: str, client_id: str, suffix: str = "asset_raw", ext: str = "parquet") -> str:
    if client_id:
        return f"bronze/{client_id}/{suffix}/{asset_id}.{ext}"
    return f"bronze/{suffix}/{asset_id}.{ext}"  # matches STACK_AND_FLOW.md when no client_id


def _lookup_manifest_row(asset_id: str) -> dict | None:
    if not MANIFEST_PATH.exists():
        return None
    with MANIFEST_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["asset_id"] == asset_id:
                return row
    return None


def _parse_s3_uri(uri: str) -> tuple[str, str]:
    bucket, _, key = uri.removeprefix("s3://").partition("/")
    return bucket, key


def _upload_and_wait_active(client: "genai.Client", video_bytes: bytes, mime_type: str,
                             display_name: str, timeout_sec: int = 120, poll_sec: int = 3):
    uploaded = client.files.upload(
        file=io.BytesIO(video_bytes),
        config=types.UploadFileConfig(mime_type=mime_type, display_name=display_name),
    )
    deadline = time.monotonic() + timeout_sec
    while uploaded.state == types.FileState.PROCESSING:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Gemini file processing timed out for asset {display_name}")
        time.sleep(poll_sec)
        uploaded = client.files.get(name=uploaded.name)
    if uploaded.state == types.FileState.FAILED:
        raise RuntimeError(f"Gemini file processing failed for asset {display_name}: {uploaded.error}")
    return uploaded


def _write_bronze_parquet(bucket: str, key: str, rows: list[dict]) -> None:
    df = pd.DataFrame(rows)
    duckdb.sql("INSTALL httpfs; LOAD httpfs;")
    duckdb.sql(
        f"CREATE OR REPLACE SECRET s3_secret (TYPE S3, PROVIDER CREDENTIAL_CHAIN, "
        f"REGION '{os.environ.get('AWS_REGION', '')}');"
    )
    duckdb.register("bronze_rows", df)
    duckdb.sql(f"COPY (SELECT * FROM bronze_rows) TO 's3://{bucket}/{key}' (FORMAT PARQUET)")
    duckdb.unregister("bronze_rows")


def _log_extraction_run(s3, bucket: str, client_id: str, asset_id: str, **fields) -> None:
    run_id = str(uuid.uuid4())
    key = _bronze_key(asset_id, client_id, suffix="extraction_run_log", ext=f"{run_id}.json")
    body = json.dumps({"run_id": run_id, "asset_id": asset_id, **fields}).encode()
    s3.put_object(Bucket=bucket, Key=key, Body=body)


def extract_chunks(asset_id: str, client_id: str = "") -> str:
    """Matches dags/creative_intel_pipeline.py's extract_chunks task contract.

    Idempotent — if Bronze already has this asset_id, returns immediately with zero
    Gemini calls (cost firewall #2)."""
    assert_safe()
    bucket = os.environ["S3_BUCKET"]
    bronze_key = _bronze_key(asset_id, client_id)
    s3 = boto3.client("s3")

    if _s3_exists(s3, bucket, bronze_key):
        return asset_id  # already extracted — no-op, no API spend

    manifest_row = _lookup_manifest_row(asset_id)
    if not manifest_row:
        raise ValueError(f"asset_id {asset_id!r} not found in {MANIFEST_PATH} — run ingest_drive_to_s3 first")
    content_sha256 = manifest_row["content_sha256"]  # raw byte hash, distinct from asset_id (ADR-006)
    landing_bucket, landing_key = _parse_s3_uri(manifest_row["source_uri"])
    ext = Path(landing_key).suffix or ".mp4"
    video_bytes = s3.get_object(Bucket=landing_bucket, Key=landing_key)["Body"].read()

    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    prompt_version = os.environ.get("PROMPT_VERSION", "v1")
    gclient = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    started = time.monotonic()
    uploaded = _upload_and_wait_active(gclient, video_bytes, _MIME_BY_EXT.get(ext.lower(), "video/mp4"), asset_id)
    try:
        response = gclient.models.generate_content(
            model=model_name,
            contents=[uploaded, EXTRACTION_PROMPT],
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=RESPONSE_SCHEMA),
        )
    finally:
        gclient.files.delete(name=uploaded.name)  # don't leave video sitting on Gemini's file store
    processing_time_sec = round(time.monotonic() - started, 2)

    # Asset-grain Bronze (@data-architect ruling, 2026-06-22 — VETOED chunk-grain-at-extraction
    # as a re-litigation of ADR-003's already-rejected "chunk in the Python extraction step"
    # alternative). raw_response is response.text UNTOUCHED — the verbatim envelope, not parsed
    # beyond what's needed to count chunks for the GE gate below. The explosion into one row
    # per chunk happens downstream in stg_gemini_raw.sql, at the Bronze->Silver dbt hop.
    chunk_count = len(json.loads(response.text).get("chunks", []))
    load_ts = datetime.now(timezone.utc).isoformat()
    rows = [{
        "asset_id": asset_id,
        "raw_response": response.text,
        "model_version": model_name,
        "prompt_version": prompt_version,
        "content_sha256": content_sha256,  # raw byte hash from the manifest (ADR-006), not asset_id
        "chunk_count": chunk_count,  # great_expectations/expectations/bronze_asset_raw.json CRITICAL gate
        "load_ts": load_ts,
    }]

    _write_bronze_parquet(bucket, bronze_key, rows)

    usage = response.usage_metadata
    _log_extraction_run(
        s3, bucket, client_id, asset_id,
        model_version=model_name, prompt_version=prompt_version,
        tokens_in=usage.prompt_token_count if usage else None,
        tokens_out=usage.candidates_token_count if usage else None,
        api_cost=None,  # see module docstring — priced downstream, not hardcoded here
        processing_time_sec=processing_time_sec, retry_count=0,
        extraction_confidence=None,  # not derivable from the API without inventing one
        load_ts=load_ts,
    )
    return asset_id


if __name__ == "__main__":
    aid = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DEMO_ASSET_ID", "")
    if not aid:
        sys.exit("usage: run_gemini_extract.py <asset_id>  (or set DEMO_ASSET_ID)")
    print(extract_chunks(aid, client_id=os.environ.get("CLIENT_ID", "")))
