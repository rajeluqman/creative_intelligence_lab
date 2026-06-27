#!/usr/bin/env python3
"""Snowflake serving reconciliation gate (ADR-005 spine).

ADR-005's SOURCE-OF-TRUTH BOUNDARY: "Gold S3 parquet is the sole source of truth. Snowflake is
a read-only projection... A reconciliation test gates the serving layer: Snowflake external-
table row counts + key sets must exact-match the DuckDB-over-S3 read of the same Gold parquet."
2026-06-27's manual one-off query (see PROJECT_STATUS.md "Row-count reconciliation, real
numbers") matched on all 8 models; this is that same check made into a checked-in, re-runnable
script instead of a one-time ad hoc query — closes the last-named item in ADR-005 Addendum
2026-06-27 ("a checked-in, automated row-count+key reconciliation test").

NOT a CI gate: needs live AWS (httpfs read of real Gold S3) + Snowflake (CREATIVE_INTEL_ROLE)
credentials, which contradicts CI's $0/no-cloud/no-secrets rule (ci.yml header). Run manually,
or from Airflow's refresh_serving task after each Gold rebuild (dags/creative_intel_pipeline.py)
— a non-zero exit there fails the task loud, which is exactly the live trip-wire ADR-005's own
veto line asks for: "@data-architect veto re-fires if Snowflake becomes a second source of
truth."

Reads BOTH sides "raw" (no dbt logical-view null-filter) on purpose. The two `where 1=0` v1
stubs (bridge_asset_lineage, fact_extraction_run) pad a 1-row all-NULL parquet — dbt-duckdb's
empty-model behavior (ADR-005 Addendum 2026-06-25 #2's "carried-forward finding"). A raw reader
sees that row on both sides, so it reconciles as 1/1, not a false-positive mismatch.

Key columns per model = each model's documented grain (DATA_MODEL.md §4), compared as a
collections.Counter (multiset, not a set) so a duplicated row on one side is caught, not
silently absorbed by set-dedup.

Run:  python tests/reconcile_snowflake_serving.py
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from env_guard import assert_safe  # noqa: E402

# Grain per model (DATA_MODEL.md §4 / model SQL) — the columns whose multiset must exact-match
# between the raw S3 parquet read and the Snowflake external-table read of the SAME files.
KEY_COLUMNS: dict[str, list[str]] = {
    "dim_asset": ["asset_id"],
    "fact_chunk": ["chunk_id"],
    "fact_extraction_run": ["asset_id"],
    "bridge_asset_lineage": ["parent_asset_id", "child_asset_id"],
    "bridge_chunk_compatibility": ["chunk_id", "compatible_theme"],
    "dim_keyword_bridge": ["chunk_id", "keyword"],
    "dim_theme_bridge": ["chunk_id", "theme"],
    "chunk_embedding": ["chunk_id"],
}

REQUIRED_ENV = ["S3_BUCKET", "CLIENT_ID", "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]


def _gold_location(bucket: str, client_id: str, model: str) -> str:
    # Mirrors macros/s3_external.sql's client-partitioned convention (ADR-005 Addendum 2025-06-25 #2).
    return f"s3://{bucket}/gold/{model}/{client_id}/{model}.parquet"


def _s3_side(model: str, keys: list[str]) -> tuple[int, Counter]:
    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(
        f"CREATE OR REPLACE SECRET s3_secret (TYPE S3, PROVIDER CREDENTIAL_CHAIN, "
        f"REGION '{os.environ.get('AWS_REGION', '')}');"
    )
    loc = _gold_location(os.environ["S3_BUCKET"], os.environ["CLIENT_ID"], model)
    cols = ", ".join(keys)
    rows = con.execute(f"select {cols} from read_parquet('{loc}')").fetchall()
    return len(rows), Counter(rows)


def _snowflake_side(model: str, keys: list[str], conn) -> tuple[int, Counter]:
    # USING TEMPLATE/INFER_SCHEMA quotes every column lowercase (ADR-005 Addendum 2026-06-27
    # "naming gotcha") — quote here too or this hits "invalid identifier".
    cols = ", ".join(f'"{k}"' for k in keys)
    cur = conn.cursor()
    cur.execute(f"SELECT {cols} FROM PUBLIC.{model.upper()}")
    rows = cur.fetchall()
    return len(rows), Counter(tuple(r) for r in rows)


def reconcile() -> list[str]:
    import snowflake.connector

    errors: list[str] = []
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "CREATIVE_INTEL_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "CREATIVE_INTEL_DB"),
        role=os.environ.get("SNOWFLAKE_ROLE", "CREATIVE_INTEL_ROLE"),
    )
    try:
        for model, keys in KEY_COLUMNS.items():
            s3_count, s3_keys = _s3_side(model, keys)
            sf_count, sf_keys = _snowflake_side(model, keys, conn)
            if s3_count != sf_count:
                errors.append(f"{model}: row count mismatch — S3={s3_count} Snowflake={sf_count}")
            elif s3_keys != sf_keys:
                only_s3 = list((s3_keys - sf_keys).elements())[:5]
                only_sf = list((sf_keys - s3_keys).elements())[:5]
                errors.append(
                    f"{model}: key-set mismatch (count matched {s3_count}) — "
                    f"only-in-S3 sample={only_s3} only-in-Snowflake sample={only_sf}"
                )
            else:
                print(f"  ✓ {model}: {s3_count} row(s), key set matches")
    finally:
        conn.close()
    return errors


def main() -> int:
    assert_safe()
    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        print(
            f"reconcile_snowflake_serving: missing required env var(s): {', '.join(missing)} "
            f"- refusing to run.",
            file=sys.stderr,
        )
        return 1

    print("Reconciling Snowflake external tables against real Gold S3 (DuckDB httpfs)...")
    errors = reconcile()
    if errors:
        print(f"\n❌ RECONCILIATION FAILED — {len(errors)} model(s) diverged:", file=sys.stderr)
        for e in errors:
            print(f"   • {e}", file=sys.stderr)
        print(
            "\n   Snowflake must stay a read-only projection of Gold S3 (ADR-005 spine). "
            "Investigate before trusting Snowflake reads.",
            file=sys.stderr,
        )
        return 1
    print(f"\n✅ reconciliation OK — Snowflake exact-matches Gold S3 on all {len(KEY_COLUMNS)} models")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
