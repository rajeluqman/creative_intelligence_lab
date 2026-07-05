#!/usr/bin/env python3
"""faults/inject.py — the @bottleneck-saboteur as a TOOL (not a roster agent).

Apply one named, REVERSIBLE fault to the sim lab's clean state, to practice troubleshooting
(Sim #3) and optimization (Sim #5). Catalog + contract: faults/README.md;
faults/catalog/CIL_INJECTABLE_MAP.md for which bank T-IDs this maps onto.

    python simulation/faults/inject.py <fault_id> [--scenario migration_v1]
    python simulation/faults/reset.py                 # undo (rebuild clean baseline)

ISOLATION: every mutation MUST stay in the local sim DuckDB, under `.fixtures/` (security-domain
faults), or under s3://creative-intel-staging/sim/. Never touch the real project.
check_isolation.py stays green.

Implemented (2026-07-04, ADR-014 handover U3): the 2 security-domain faults behind the T-SEC-01 /
T-SRV-04 drills — `sec_leaked_key` and `sec_missing_future_grant`. Both are fixture-file-based
(no dbt/sim_dbt dependency) since `simulation/sim_dbt/` has no seeds/models built yet. The
dq_*/rec_*/av_*/perf_* fault fns named in faults/README.md's catalog are still TODO — author one
on demand when a drill is actually built for it, per the injectable map's "Using this map" §3.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

SIM = Path(__file__).resolve().parents[1]
REPO = SIM.parent
ACTIVE = SIM / "faults" / ".active_faults.json"   # audit log so reset can verify a clean undo
FIXTURES = SIM / "faults" / ".fixtures"           # isolated scratch files security faults plant


def _sec_leaked_key(scenario: str) -> dict:
    """T-SEC-01: plant an obviously-fake, AWS-key-shaped literal — never a real credential."""
    FIXTURES.mkdir(parents=True, exist_ok=True)
    path = FIXTURES / "leaked_key_demo.py"
    # Split so THIS source file never contains the contiguous AKIA+16-char shape itself
    # (the "self-matching regex" trap named in framework_template's secrets_scan.py).
    fake_key = "AKIA" + "FAKEDEMOKEY12345"
    path.write_text(f'aws_access_key_id = "{fake_key}"\n')
    return {
        "fixture": str(path.relative_to(REPO)),
        "expected_symptom": "a regex scan for AWS-key-shaped literals finds a hit in "
        "simulation/faults/.fixtures/leaked_key_demo.py",
        "gate_to_run": "the inline regex check in drills/T-SEC-01_leaked_key.md §2 "
        "(mirrors framework_template/gates/secrets_scan.py's own patterns)",
    }


def _sec_missing_future_grant(scenario: str) -> dict:
    """T-SRV-04: snapshot the PRE-ADR-014 per-table-only grant pattern, one table short."""
    FIXTURES.mkdir(parents=True, exist_ok=True)
    path = FIXTURES / "rbac_grants_snapshot.json"
    path.write_text(json.dumps({
        "tables": ["dim_asset", "fact_chunk", "fact_extraction_run", "bridge_asset_lineage"],
        "analyst_grants": ["dim_asset", "fact_chunk", "fact_extraction_run"],
        "note": "bridge_asset_lineage shipped after the last per-table grant run — missing from "
        "analyst_grants, the exact drift a FUTURE TABLES grant (ADR-014) closes for good.",
    }, indent=2))
    return {
        "fixture": str(path.relative_to(REPO)),
        "expected_symptom": "CREATIVE_INTEL_ANALYST_RO can SELECT the first 3 tables but not "
        "bridge_asset_lineage",
        "gate_to_run": "python3 scripts/provision_snowflake_serving.py --phase tables | "
        "grep 'FUTURE TABLES'",
    }


# id -> callable(scenario) -> dict describing what it changed (for the audit log + learner print).
FAULTS: dict[str, Callable[[str], dict]] = {
    "sec_leaked_key": _sec_leaked_key,
    "sec_missing_future_grant": _sec_missing_future_grant,
    # TODO(on demand): "dq_schema_drift", "rec_silent_drift", "perf_skew", etc. — one mutate fn
    # per faults/README.md catalog row, authored when a drill is actually built for that id.
}


def _record(entry: dict) -> None:
    log = json.loads(ACTIVE.read_text()) if ACTIVE.exists() else []
    log.append(entry)
    ACTIVE.write_text(json.dumps(log, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Inject one reversible fault into the sim lab.")
    ap.add_argument("fault_id", choices=sorted(FAULTS), help="see faults/README.md")
    ap.add_argument("--scenario", default="migration_v1")
    args = ap.parse_args()

    if ACTIVE.exists() and json.loads(ACTIVE.read_text()):
        print(
            "A fault is already active (see faults/.active_faults.json). Run "
            "`python simulation/faults/reset.py` first — one fault at a time."
        )
        return 1

    change = FAULTS[args.fault_id](args.scenario)
    _record({"id": args.fault_id, "scenario": args.scenario, **change})
    print(f"INJECTED {args.fault_id}")
    print(f"  expected symptom: {change['expected_symptom']}")
    print(f"  gate to run:      {change['gate_to_run']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
