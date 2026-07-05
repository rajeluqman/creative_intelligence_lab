#!/usr/bin/env python3
"""faults/reset.py — restore the sim lab's clean baseline (total undo of any injected fault).

    python simulation/faults/reset.py

Clean state is ALWAYS rebuildable — reset never hand-patches a fault away, it regenerates or
deletes. That guarantees every drill starts from an identical baseline.

Implemented (2026-07-04, ADR-014 handover U3): fixture-based faults (the 2 security drills —
`sec_leaked_key`, `sec_missing_future_grant`) are cleared by deleting the file(s) the active-fault
log recorded. The dbt seed/build rebuild only runs if `simulation/sim_dbt/seeds/` actually has
seeds — it doesn't yet (no dq_*/rec_*/av_*/perf_* fault is built), so that step degrades to a
no-op note rather than failing, until a data-domain fault is authored.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SIM = Path(__file__).resolve().parents[1]
REPO = SIM.parent
SIM_DBT = SIM / "sim_dbt"
ACTIVE = SIM / "faults" / ".active_faults.json"


def _clear_fixtures() -> None:
    if not ACTIVE.exists():
        return
    log = json.loads(ACTIVE.read_text())
    for entry in log:
        fixture = entry.get("fixture")
        if not fixture:
            continue
        path = REPO / fixture
        if path.exists():
            path.unlink()
            print(f"removed {fixture}")
    ACTIVE.unlink()


def _rebuild_sim_dbt() -> None:
    seeds_dir = SIM_DBT / "seeds"
    if not seeds_dir.exists() or not any(seeds_dir.glob("*.csv")):
        print(
            "note: simulation/sim_dbt has no seeds yet — skipping dbt rebuild (no data-domain "
            "fault is built yet; this reset only cleared fixture-based faults, if any)."
        )
        return
    env = {**os.environ, "DBT_PROFILES_DIR": str(SIM_DBT)}
    subprocess.run(["dbt", "seed"], cwd=SIM_DBT, env=env, check=True)
    subprocess.run(["dbt", "build"], cwd=SIM_DBT, env=env, check=True)


def main() -> int:
    _clear_fixtures()
    _rebuild_sim_dbt()
    return subprocess.run([sys.executable, str(SIM / "check_isolation.py")]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
