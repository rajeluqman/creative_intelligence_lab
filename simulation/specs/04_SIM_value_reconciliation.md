# Sim #4 — Value-Level Reconciliation (the headline banking skill)

**Objective:** build a reconciliation harness that proves migrated == legacy at the **value** level,
not just row counts — and catch a `rec_silent_drift` fault that row-counts would miss. This is the
single most differentiating RBC-migration skill.

**RBC tasks covered:** 47 row-count, 48 checksum/value, 58 aggregate reconcile, 81–90 (DQ/reconcile),
85 source-target reconciliation.

**Interview soundbite this proves:** *"Row-count match is necessary, not sufficient — migration is
done when values reconcile, not when counts do."*

## Sonnet steps
1. `reconcile/reconcile.py` — given two relations (legacy, migrated):
   - **Level 1 — row count:** assert equal; report delta.
   - **Level 2 — key set:** symmetric diff of PKs (rows only in one side).
   - **Level 3 — value:** for matched keys, column-by-column compare (with explicit tolerance for
     float/rounding — and *log* the tolerance, since "rounding" is where silent drift hides).
   - **Level 4 — aggregates:** SUM/COUNT/MIN/MAX per measure both sides (catches offsetting errors).
   - Output `reconcile/report_<run>.md`: PASS/FAIL per level + the first N mismatching keys.
2. Wire it into Sim #1's DoD (the cutover gate).
3. **Prove it bites:** `faults/inject.py rec_silent_drift` → run reconcile → Level 1 PASS but
   Level 3/4 FAIL. Capture that contrast in `runbook/04_reconciliation_demo.md` — *this screenshot is
   the interview.*

## Definition of Done
1. On clean baseline: all 4 levels PASS.
2. With `rec_silent_drift`: Level 1 (count) PASS, Level 3/4 (value/agg) FAIL — captured as evidence.
3. `reconcile/report_*.md` + `runbook/04_reconciliation_demo.md` exist; `check_isolation.py` PASS.
4. STAR row filled.
