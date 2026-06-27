#!/usr/bin/env python3
"""Self-test for adr_coupling_contract.py — the gate is itself tested (house pattern).

Exercises the PURE core (dep_names + evaluate) with synthetic changes and a fake base lookup,
so no real git history is needed. Mirrors tests/test_doc_reference_contract.py's style.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adr_coupling_contract as acc  # noqa: E402

LOCAL_PY = {"env_guard", "ingest_drive_to_s3"}


def _check(name: str, cond: bool) -> None:
    if not cond:
        print(f"SELF-TEST FAIL: {name}")
        raise SystemExit(1)


def main() -> int:
    # dep_names: local import counts, stdlib does not; SQL-in-string is not an import.
    py = "import json\nfrom env_guard import assert_safe\nq = 'from fact_chunk c'\n"
    _check("py local import detected", acc.dep_names(py, ".py", LOCAL_PY) == {"env_guard"})
    _check("py stdlib ignored", "json" not in acc.dep_names(py, ".py", LOCAL_PY))

    # dep_names: sql ref() targets.
    sql = "select * from {{ ref('fact_chunk') }} join {{ ref('dim_asset') }} using (asset_id)"
    _check("sql refs detected", acc.dep_names(sql, ".sql", LOCAL_PY) == {"fact_chunk", "dim_asset"})

    base = {
        "scripts/old.py": "from env_guard import x\n",
        "models/marts/core/fact_chunk.sql": "select * from {{ ref('int_chunk_cleaned') }}",
        "seeds/dim_client.csv": "client_id,name\nc1,Acme\n",
    }

    def base_text(rel: str):
        return base.get(rel)

    # 1. Added governed file, no ADR → structural, blocked.
    structural, adr = acc.evaluate(
        [{"status": "A", "path": "scripts/new_step.py", "head_text": "print(1)"}], base_text, LOCAL_PY)
    _check("added governed is structural", structural and not adr)

    # 2. Added governed file WITH an ADR touched → passes.
    structural, adr = acc.evaluate([
        {"status": "A", "path": "scripts/new_step.py", "head_text": "print(1)"},
        {"status": "A", "path": "architecture/ADR-099-new-step.md", "head_text": "# ADR"},
    ], base_text, LOCAL_PY)
    _check("added governed + ADR passes", structural and adr)

    # 3. Modified .sql with a NEW ref() → structural (edge changed).
    structural, adr = acc.evaluate([{
        "status": "M", "path": "models/marts/core/fact_chunk.sql",
        "head_text": "select * from {{ ref('int_chunk_cleaned') }} join {{ ref('dim_asset') }} using(x)",
    }], base_text, LOCAL_PY)
    _check("new ref is structural", any(p == "models/marts/core/fact_chunk.sql" for _, p in structural))

    # 4. Modified .sql with SAME refs (cosmetic) → not structural.
    structural, adr = acc.evaluate([{
        "status": "M", "path": "models/marts/core/fact_chunk.sql",
        "head_text": "select *  from {{ ref('int_chunk_cleaned') }}  -- reformatted",
    }], base_text, LOCAL_PY)
    _check("cosmetic sql edit not structural", not structural)

    # 5. Modified seed (.csv) content → NOT structural (no edge concept; a new ROW isn't architecture).
    structural, adr = acc.evaluate([{
        "status": "M", "path": "seeds/dim_client.csv", "head_text": "client_id,name\nc1,Acme\nc2,Beta\n",
    }], base_text, LOCAL_PY)
    _check("seed row edit not structural", not structural)

    # 6. Non-governed file (a test) added → not structural.
    structural, adr = acc.evaluate(
        [{"status": "A", "path": "tests/test_foo.py", "head_text": "x=1"}], base_text, LOCAL_PY)
    _check("non-governed not structural", not structural)

    # 7. Deleted governed file → structural.
    structural, adr = acc.evaluate(
        [{"status": "D", "path": "models/marts/core/fact_chunk.sql", "head_text": None}], base_text, LOCAL_PY)
    _check("deleted governed is structural", structural)

    print("SELF-TEST OK — local/stdlib imports distinguished, sql refs parsed, structural vs cosmetic "
          "and governed vs not all classified, ADR-touch satisfies the gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
