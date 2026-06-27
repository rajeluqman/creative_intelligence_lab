"""v1 search + mix-and-match demo CLI — architecture/SPEC_v1_search.md (Owner: @senior-data-engineer).
`--semantic` (v1.5 fast-follow, completion-plan item 2) added 2026-06-25.
`--snowflake-semantic` (Snowflake serving veneer leg) added 2026-06-27 — ADR-005 Addendum #4.

Four legs, one CLI:
  Leg (a) Search        — structured filter + ilike keyword match over `fact_chunk` joined to
                           `dim_asset` (SPEC §2.2). Deterministic predicate filtering.
  Leg (b) Mix-and-Match  — `--assemble` walks the compatibility graph
                           (`bridge_chunk_compatibility`) for a fixed 3-step Hook->Body->CTA
                           sequence (SPEC §3.2/§3.3). Only `standalone_score >= 4` chunks are
                           eligible at every step (anti-Frankenstein rule, SPEC §3.1).
  Leg (c) Semantic       — `--semantic "<query text>"`. DuckDB VSS $0 fallback (ADR-005 §B):
                           embeds the query with the same Gemini model/dimension used by
                           scripts/generate_embeddings.py, builds an ephemeral in-memory HNSW
                           index over `fact_chunk.embedding` (cheap at this row count — no
                           persistent index file, nothing to go stale), ranks by
                           `array_distance`. Was explicitly OUT of v1 (SPEC §1) — this is the
                           named v1.5 fast-follow, not a re-litigation of that ruling.
  Leg (d) Snowflake      — `--snowflake-semantic "<query text>"`. Same BYO-Gemini query vector as
            Semantic       leg (c), ranked instead by Snowflake's native `VECTOR_COSINE_SIMILARITY`
                           against `PUBLIC.FACT_CHUNK_VECTOR` (a VIEW casting `FACT_CHUNK.embedding`
                           VARIANT->VECTOR(FLOAT,768), built by
                           `scripts/provision_snowflake_serving.py --phase search`). This is the
                           Snowflake-serving mirror of leg (c), NOT the managed Cortex Search
                           Service — that path was tried and abandoned for real (ADR-005 Addenda
                           2026-06-27 #2/#3/#4: BYO-embedding conflict, then a Dynamic-Table
                           limitation, then a trial-tier AI-function wall, in that order).

Legs (a)/(b)/(c) read the already-built local DuckDB catalog read-only (`target/dev.duckdb`) — the
same file `dbt build -s +marts.core` produces; leg (c) needs a second, separate, in-memory
writable connection (HNSW `CREATE INDEX` needs write access; the catalog file is opened
read-only) — still no new direct-S3 connection path, since the rows themselves come from the
same read-only catalog query, just copied into memory to index. Leg (d) opens no local DuckDB
connection at all — it queries live Snowflake using `CREATIVE_INTEL_ROLE` (the scoped serving
role, not `ACCOUNTADMIN`).

Usage:
    python scripts/search_cli.py --theme Problem --sentiment frustrated --min-score 4 --contains minyak
    python scripts/search_cli.py --assemble
    python scripts/search_cli.py --assemble --hook-theme Problem --limit 5
    python scripts/search_cli.py --semantic "engine feels heavy and uses more fuel" --limit 5
    python scripts/search_cli.py --snowflake-semantic "engine feels heavy and uses more fuel" --limit 5
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import duckdb

EMBEDDING_DIM = 768  # must match scripts/generate_embeddings.py's EMBEDDING_DIM exactly

DB_PATH = Path(__file__).parent.parent / "target" / "dev.duckdb"

# Leg (a) reference query — SPEC_v1_search.md §2.2, adapted to real values (predicates are
# CLI-driven; --contains is optional, unlike the spec's hardcoded literal).
SEARCH_SQL = """
select
    c.chunk_id, c.asset_id, a.asset_name,
    c.start_sec, c.end_sec, c.standalone_score,
    c.chunk_theme, c.sentiment, c.transcript_segment
from fact_chunk c
join dim_asset a using (asset_id)
where 1=1
{theme_clause}
{sentiment_clause}
{score_clause}
{contains_clause}
order by c.standalone_score desc, c.start_sec
"""

# Leg (b) reference query — SPEC_v1_search.md §3.2, extended to a fixed 3-step
# Hook -> Body -> CTA walk per §3.3 (chain the 2-step join twice, not recursive in v1).
ASSEMBLE_SQL = """
with hook as (
    select * from fact_chunk
    where chunk_theme = ? and standalone_score >= 4
),
hook_to_body as (
    select
        h.chunk_id as hook_chunk_id, h.asset_id as hook_asset_id,
        h.start_sec as hook_start, h.end_sec as hook_end,
        h.transcript_segment as hook_text,
        b.chunk_id as body_chunk_id, b.asset_id as body_asset_id,
        b.chunk_theme as body_theme,
        b.start_sec as body_start, b.end_sec as body_end,
        b.transcript_segment as body_text
    from hook h
    join bridge_chunk_compatibility bc on bc.chunk_id = h.chunk_id
    join fact_chunk b
        on b.chunk_theme = bc.compatible_theme
       and b.chunk_id <> h.chunk_id
    where b.standalone_score >= 4
),
body_to_cta as (
    select
        hb.*,
        ct.chunk_id as cta_chunk_id, ct.asset_id as cta_asset_id,
        ct.chunk_theme as cta_theme,
        ct.start_sec as cta_start, ct.end_sec as cta_end,
        ct.transcript_segment as cta_text
    from hook_to_body hb
    join bridge_chunk_compatibility bc2 on bc2.chunk_id = hb.body_chunk_id
    join fact_chunk ct
        on ct.chunk_theme = bc2.compatible_theme
       and ct.chunk_id not in (hb.hook_chunk_id, hb.body_chunk_id)
    where ct.standalone_score >= 4
)
select * from body_to_cta
order by hook_chunk_id, body_chunk_id, cta_chunk_id
limit ?
"""


def _connect() -> duckdb.DuckDBPyConnection:
    if not DB_PATH.exists():
        print(
            f"error: {DB_PATH} not found — run `dbt build -s +marts.core` first.",
            file=sys.stderr,
        )
        sys.exit(1)
    return duckdb.connect(str(DB_PATH), read_only=True)


def run_search(con, args: argparse.Namespace) -> None:
    theme_clause = "and c.chunk_theme = ?" if args.theme else ""
    sentiment_clause = "and c.sentiment = ?" if args.sentiment else ""
    score_clause = "and c.standalone_score >= ?" if args.min_score is not None else ""
    contains_clause = "and c.transcript_segment ilike ?" if args.contains else ""

    sql = SEARCH_SQL.format(
        theme_clause=theme_clause,
        sentiment_clause=sentiment_clause,
        score_clause=score_clause,
        contains_clause=contains_clause,
    )

    params = []
    if args.theme:
        params.append(args.theme)
    if args.sentiment:
        params.append(args.sentiment)
    if args.min_score is not None:
        params.append(args.min_score)
    if args.contains:
        params.append(f"%{args.contains}%")

    rows = con.execute(sql, params).fetchall()
    cols = [d[0] for d in con.description]

    if not rows:
        print("No clips matched.")
        return

    print(f"{len(rows)} clip(s) matched:\n")
    for r in rows:
        rec = dict(zip(cols, r))
        print(
            f"[{rec['standalone_score']}] {rec['chunk_id']}  "
            f"theme={rec['chunk_theme']!r} sentiment={rec['sentiment']!r}  "
            f"{rec['start_sec']:.1f}s-{rec['end_sec']:.1f}s  asset={rec['asset_name']}"
        )
        print(f"      \"{rec['transcript_segment']}\"")


def run_assemble(con, args: argparse.Namespace) -> None:
    rows = con.execute(ASSEMBLE_SQL, [args.hook_theme, args.limit]).fetchall()
    cols = [d[0] for d in con.description]

    if not rows:
        print(
            f"No 3-step sequences found starting from chunk_theme={args.hook_theme!r}. "
            "Try a different --hook-theme."
        )
        return

    print(
        f"{len(rows)} candidate Hook->Body->CTA sequence(s) "
        f"(hook_theme={args.hook_theme!r}, standalone_score >= 4 at every step):\n"
    )
    for i, r in enumerate(rows, start=1):
        rec = dict(zip(cols, r))
        print(f"--- Sequence {i} ---")
        print(
            f"  HOOK  {rec['hook_chunk_id']}  asset={rec['hook_asset_id']}  "
            f"{rec['hook_start']:.1f}s-{rec['hook_end']:.1f}s"
        )
        print(f"        \"{rec['hook_text']}\"")
        print(
            f"  BODY  {rec['body_chunk_id']}  asset={rec['body_asset_id']}  "
            f"theme={rec['body_theme']!r}  {rec['body_start']:.1f}s-{rec['body_end']:.1f}s"
        )
        print(f"        \"{rec['body_text']}\"")
        print(
            f"  CTA   {rec['cta_chunk_id']}  asset={rec['cta_asset_id']}  "
            f"theme={rec['cta_theme']!r}  {rec['cta_start']:.1f}s-{rec['cta_end']:.1f}s"
        )
        print(f"        \"{rec['cta_text']}\"")
        print()


def _embed_query(query: str) -> list[float]:
    from google import genai
    from google.genai import types

    model = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    gclient = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = gclient.models.embed_content(
        model=model,
        contents=[query],
        # RETRIEVAL_QUERY (not RETRIEVAL_DOCUMENT, which generate_embeddings.py uses for the
        # stored chunks) — Gemini's asymmetric retrieval task types improve match quality when
        # query and document text differ in length/shape, same vector space either way.
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=EMBEDDING_DIM),
    )
    return list(response.embeddings[0].values)


def run_semantic(con, args: argparse.Namespace) -> None:
    rows = con.execute(
        """
        select c.chunk_id, c.asset_id, a.asset_name, c.start_sec, c.end_sec,
               c.standalone_score, c.chunk_theme, c.sentiment, c.transcript_segment, c.embedding
        from fact_chunk c
        join dim_asset a using (asset_id)
        where c.embedding is not null
        """
    ).fetchall()
    cols = [d[0] for d in con.description]

    if not rows:
        print("No embedded clips found — run scripts/generate_embeddings.py first.")
        return

    query_vec = _embed_query(args.semantic)

    # Ephemeral in-memory HNSW index (DuckDB VSS, ADR-005 $0 fallback) — built fresh per
    # invocation. Cheap at this row count; avoids a persistent index file that could go stale
    # against the next embeddings run.
    mem = duckdb.connect()
    mem.execute("INSTALL vss; LOAD vss;")
    mem.execute(f"create table chunk_index(chunk_id varchar, embedding float[{EMBEDDING_DIM}])")
    mem.executemany("insert into chunk_index values (?, ?)", [(r[0], r[9]) for r in rows])
    mem.execute("create index hnsw_idx on chunk_index using HNSW (embedding)")
    ranked = mem.execute(
        f"select chunk_id, array_distance(embedding, ?::float[{EMBEDDING_DIM}]) as distance "
        f"from chunk_index order by distance limit ?",
        [query_vec, args.limit],
    ).fetchall()
    mem.close()

    by_id = {dict(zip(cols, r))["chunk_id"]: dict(zip(cols, r)) for r in rows}
    print(f"Top {len(ranked)} semantic match(es) for {args.semantic!r}:\n")
    for chunk_id, distance in ranked:
        rec = by_id[chunk_id]
        print(
            f"[dist={distance:.4f}, score={rec['standalone_score']}] {rec['chunk_id']}  "
            f"theme={rec['chunk_theme']!r} sentiment={rec['sentiment']!r}  "
            f"{rec['start_sec']:.1f}s-{rec['end_sec']:.1f}s  asset={rec['asset_name']}"
        )
        print(f"      \"{rec['transcript_segment']}\"")


def run_snowflake_semantic(args: argparse.Namespace) -> None:
    import snowflake.connector

    query_vec = _embed_query(args.snowflake_semantic)
    vec_literal = "[" + ",".join(str(v) for v in query_vec) + "]"

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "CREATIVE_INTEL_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "CREATIVE_INTEL_DB"),
        role=os.environ.get("SNOWFLAKE_ROLE", "CREATIVE_INTEL_ROLE"),
    )
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT "chunk_id", "asset_id", "transcript_segment", "chunk_theme", "sentiment",
                   "standalone_score",
                   VECTOR_COSINE_SIMILARITY("embedding_vec", {vec_literal}::VECTOR(FLOAT, {EMBEDDING_DIM})) AS sim
            FROM PUBLIC.FACT_CHUNK_VECTOR
            ORDER BY sim DESC
            LIMIT %s
            """,
            (args.limit,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        print("No embedded clips found in PUBLIC.FACT_CHUNK_VECTOR.")
        return

    print(f"Top {len(rows)} Snowflake semantic match(es) for {args.snowflake_semantic!r}:\n")
    for chunk_id, asset_id, transcript, theme, sentiment, score, sim in rows:
        print(
            f"[sim={sim:.4f}, score={score}] {chunk_id}  theme={theme!r} sentiment={sentiment!r}  "
            f"asset={asset_id}"
        )
        print(f"      \"{transcript}\"")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="v1 creative feature store demo — search (leg a) + mix-and-match assembly (leg b)."
    )
    # Leg (a) — search
    parser.add_argument("--theme", help="exact match on fact_chunk.chunk_theme")
    parser.add_argument("--sentiment", help="exact match on fact_chunk.sentiment")
    parser.add_argument("--min-score", type=int, help="fact_chunk.standalone_score >= this")
    parser.add_argument("--contains", help="ilike substring match on transcript_segment")
    # Leg (b) — mix-and-match
    parser.add_argument(
        "--assemble",
        action="store_true",
        help="run the 3-step Hook->Body->CTA mix-and-match assembler instead of search",
    )
    parser.add_argument(
        "--hook-theme",
        default="Hook",
        help="chunk_theme to start the assembled sequence from (default: 'Hook'; real data also "
        "has high-volume themes like 'Problem' — see chunk_theme vocabulary-drift finding)",
    )
    parser.add_argument(
        "--limit", type=int, default=5,
        help="max results to print (--assemble: sequences; --semantic: nearest chunks)",
    )
    # Leg (c) — semantic (v1.5 fast-follow, DuckDB VSS $0 fallback, ADR-005 §B)
    parser.add_argument(
        "--semantic", help="free-text query; ranks fact_chunk.embedding by VSS array_distance"
    )
    # Leg (d) — Snowflake-served semantic (ADR-005 Addendum 2026-06-27 #4)
    parser.add_argument(
        "--snowflake-semantic",
        help="free-text query; ranks PUBLIC.FACT_CHUNK_VECTOR by VECTOR_COSINE_SIMILARITY "
        "via live Snowflake (needs SNOWFLAKE_* env vars; no local DuckDB catalog needed)",
    )
    args = parser.parse_args()

    if args.snowflake_semantic:
        run_snowflake_semantic(args)
        return

    con = _connect()
    try:
        if args.semantic:
            run_semantic(con, args)
        elif args.assemble:
            run_assemble(con, args)
        else:
            run_search(con, args)
    finally:
        con.close()


if __name__ == "__main__":
    main()
