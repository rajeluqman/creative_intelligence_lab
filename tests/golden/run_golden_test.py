#!/usr/bin/env python3
"""Golden-dataset test — proves fact_chunk computes the RIGHT values, not just valid-shaped ones.

dbt's own schema tests (not_null/unique/relationships/range) prove SHAPE. They cannot catch a
silently-wrong VALUE (e.g. standalone_score off by one, a swapped chunk_theme/sentiment column,
a chunk_sequence/chunk_id mismatch) — every existing gate would still pass. This is the Layer-4
"Revenue = Sales, not Sales - Refund" class of bug for this pipeline.

Mechanism: write fixture_data.RAW_RESPONSE as a local Bronze-shaped parquet, run the REAL dbt
chain (stg_gemini_raw -> int_chunk_cleaned -> fact_chunk) against it via the `golden_test` dbt
target (models/staging/_sources.yml routes bronze_asset_raw to this local fixture instead of S3
when target.name == 'golden_test' — $0, no cloud, CI-safe), then diff the actual fact_chunk rows
against fixture_data.EXPECTED_FACT_CHUNK (a hand-authored answer key, not derived from the same
code path as the input — see fixture_data.py docstring).

Run:  python tests/golden/run_golden_test.py     # exit 0 = matches exactly, 1 = drift
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import duckdb
import pandas as pd

import fixture_data as fx

REPO = Path(__file__).resolve().parent.parent.parent
GOLDEN_DB = REPO / "target" / "golden_test.duckdb"


def _write_bronze_fixture(bronze_dir: Path) -> None:
    bronze_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([{
        "asset_id": fx.ASSET_ID,
        "raw_response": fx.RAW_RESPONSE,
        "model_version": fx.MODEL_VERSION,
        "prompt_version": fx.PROMPT_VERSION,
        "content_sha256": fx.CONTENT_SHA256,
        "chunk_count": len(fx.RAW_CHUNKS),
        "load_ts": fx.LOAD_TS,
    }])
    # explicit register (not relying on duckdb's implicit local-scope df scan, which is invisible
    # to ruff's static analysis and was flagged F841 unused) — same pattern as
    # run_gemini_extract.py's _write_bronze_parquet.
    duckdb.register("golden_fixture_df", df)
    duckdb.sql("SELECT * FROM golden_fixture_df").write_parquet(str(bronze_dir / f"{fx.ASSET_ID}.parquet"))
    duckdb.unregister("golden_fixture_df")


def _run_dbt(profiles_dir: Path, bronze_glob: str) -> None:
    cmd = [
        "dbt", "run", "-s", "+fact_chunk", "--target", "golden_test",
        "--vars", f'{{"golden_bronze_path": "{bronze_glob}"}}',
    ]
    env = {
        **os.environ,
        "DBT_PROFILES_DIR": str(profiles_dir),
        "CLIENT_ID": "golden_test_client",
        "S3_BUCKET": "unused-golden-test-placeholder",
    }
    result = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit("dbt run failed — see output above")


def _actual_fact_chunk() -> list[dict]:
    con = duckdb.connect(str(GOLDEN_DB), read_only=True)
    rows = con.execute(
        "select chunk_id, asset_id, chunk_sequence, start_sec, end_sec, "
        "transcript_segment, chunk_theme, sentiment, standalone_score "
        "from main.fact_chunk order by chunk_sequence"
    ).fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    return [dict(zip(cols, r)) for r in rows]


def run() -> int:
    work = Path(tempfile.mkdtemp(prefix="golden_test_"))
    bronze_dir = work / "bronze_fixture"
    profiles_dir = work / "profiles"
    try:
        _write_bronze_fixture(bronze_dir)
        profiles_dir.mkdir()
        shutil.copy(REPO / "profiles.yml.example", profiles_dir / "profiles.yml")

        _run_dbt(profiles_dir, str(bronze_dir / "*.parquet"))
        actual = _actual_fact_chunk()
        expected = fx.EXPECTED_FACT_CHUNK

        if actual == expected:
            print(f"GOLDEN TEST OK — {len(actual)} fact_chunk row(s) match the answer key exactly.")
            return 0

        print(f"GOLDEN TEST FAILED — {len(expected)} expected row(s), {len(actual)} actual row(s).")
        for i, (e, a) in enumerate(zip(expected, actual)):
            if e != a:
                print(f"  row {i} (chunk_sequence={e.get('chunk_sequence')}):")
                print(f"    expected: {e}")
                print(f"    actual:   {a}")
        if len(actual) != len(expected):
            print("  ROW COUNT MISMATCH — a chunk was dropped, duplicated, or never built.")
        return 1
    finally:
        shutil.rmtree(work, ignore_errors=True)
        GOLDEN_DB.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(run())
