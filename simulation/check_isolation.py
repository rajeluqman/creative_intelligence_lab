#!/usr/bin/env python3
"""Isolation guard for the RBC simulation lab (simulation/).

Governance-as-code (mirrors tests/lineage_contract.py et al.): proves the sim lab cannot touch the
real ("main") project, so fault-injection / optimization drills can never corrupt canonical data or
models. Deterministic, no AWS / no network. Run before every sim session AND before committing sim
work:

    python simulation/check_isolation.py

Exit 0 = isolated (safe to break things). Exit 1 = a boundary was crossed (STOP). Enforces R1/R2/R3
of ISOLATION_CONTRACT.md (the high-value, low-false-positive rules); R4/R5 stay partly human.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "simulation"
REAL_DBT = ROOT / "dbt_project.yml"
SIM_DBT = SIM / "sim_dbt" / "dbt_project.yml"
SIM_PREFIX = "/sim/"  # every s3:// path the sim touches must contain this


def project_name(p: Path) -> str | None:
    if not p.exists():
        return None
    m = re.search(r"^\s*name:\s*['\"]?([\w-]+)", p.read_text(errors="ignore"), re.M)
    return m.group(1) if m else None


def main() -> int:
    failures: list[str] = []
    notes: list[str] = []

    # R2 — sim dbt project name must differ from the real one.
    real_name = project_name(REAL_DBT)
    sim_name = project_name(SIM_DBT)
    if sim_name is None:
        notes.append("R2: simulation/sim_dbt/dbt_project.yml not present yet — name check skipped")
    elif real_name and sim_name == real_name:
        failures.append(f"R2: sim dbt project name '{sim_name}' equals real '{real_name}' — must differ")

    # R3 — no sim SQL may ref() a real model (cross-project contamination).
    real_models = {p.stem for p in (ROOT / "models").rglob("*.sql")} if (ROOT / "models").exists() else set()
    sim_sql = list(SIM.rglob("*.sql"))
    for f in sim_sql:
        text = f.read_text(errors="ignore")
        for ref in re.findall(r"ref\(\s*['\"]([\w]+)['\"]\s*\)", text):
            if ref in real_models:
                failures.append(f"R3: {f.relative_to(ROOT)} ref()s real model '{ref}'")

    # R1 — every s3:// path in an EXECUTABLE sim file must live under /sim/.
    #      (.md docs are excluded: the contract docs legitimately cite forbidden paths as examples.)
    exec_files = (
        sim_sql
        + [p for p in SIM.rglob("*.py") if p.name != "check_isolation.py"]
        + list(SIM.rglob("*.yml"))
        + list(SIM.rglob("*.yaml"))
    )
    for f in exec_files:
        text = f.read_text(errors="ignore")
        for path in re.findall(r"s3://[^\s'\"\)\]]+", text):
            # accept the sim root itself (".../sim") and anything under it (".../sim/...")
            if SIM_PREFIX not in (path.rstrip("/") + "/"):
                failures.append(f"R1: {f.relative_to(ROOT)} has an s3 path not under '{SIM_PREFIX}': {path}")

    # Report
    for n in notes:
        print(f"  note: {n}")
    if failures:
        print("\nISOLATION CHECK: FAIL — the sim lab crossed a boundary into main:")
        for x in failures:
            print(f"  ✗ {x}")
        print("\nFix before continuing — see simulation/ISOLATION_CONTRACT.md.")
        return 1
    print("ISOLATION CHECK: PASS — sim lab is isolated from main. Safe to inject faults.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
