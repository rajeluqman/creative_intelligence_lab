# Sim #1 — Migration Dry-Run (Teradata → Snowflake logic migration)

**Objective:** migrate a synthetic "Teradata" workload into a clean "Snowflake" rebuild and prove
they reconcile — the core RBC motion. This builds the **clean baseline** every other track resets to.

**RBC tasks covered:** 43–60 (migration), esp. 45 convert SQL, 47 row-count, 48 value reconcile,
49 STTM, 50 parallel-run, 51 cutover, 52 rollback, 53 ADR, 60 PIR. *(see `06_RBC_TASK_MAP.md`)*

**Interview story (STAR — fill after the run):**
> S: legacy Teradata-style workload, business needs it on Snowflake without changing a number.
> T: migrate the logic + prove equivalence + a safe cutover/rollback path.
> A: ________  R: reconciled to the cent, documented cutover+rollback, ___ rows / ___ measures.

## Preconditions
- `simulation/sim_dbt/` profile installed (`profiles.sim.yml.example`), `check_isolation.py` PASS.

## Sonnet steps
1. **Build the legacy source.** Author `sim_dbt/seeds/legacy_extract.csv` — a small denormalized,
   Teradata-flavored dataset (mixed types, embedded logic, e.g. ad-spend or transaction rows).
   Build `models/legacy/` encoding the legacy logic *as-is* (the source-of-truth baseline). Keep a
   short BTEQ-style `.sql` comment block documenting the original logic (so you practice reading it).
2. **Write the STTM.** Create `runbook/01_STTM.md` — source col → target col → transform rule, one
   row per field. This is *the* migration deliverable; mirror the real `architecture/STTM.md` format.
3. **Build the migrated target.** `models/migrated/` re-expresses the same logic in clean dbt-SQL.
4. **Reconcile.** Run Sim #4's harness (`reconcile/`) legacy-vs-migrated: row count AND value-level.
   Must be green to the cent before "cutover".
5. **Parallel-run + cutover doc.** `runbook/01_migration_case_study.md`: parallel-run evidence,
   cutover checklist, and an explicit **rollback** plan (point back to `legacy/`). Cite the real
   precedent: the Cortex→VECTOR→DuckDB rollback already in this repo (ADR-005) is your rollback story.
6. **ADR.** Short `runbook/01_ADR_migration.md` recording the decision + reconciliation evidence.

## Artifacts
`runbook/01_STTM.md`, `runbook/01_migration_case_study.md`, `runbook/01_ADR_migration.md`,
reconciled `migrated/` models.

## Definition of Done
1. `python simulation/check_isolation.py` → PASS.
2. `reconcile/` legacy-vs-migrated → 0 row diff AND 0 value diff (evidence pasted in case study).
3. All three runbook artifacts exist; STTM has one row per migrated field.
4. STAR row in `07_INTERVIEW_CHEATSHEET.md` filled with evidence.

## Reset
`python simulation/faults/reset.py` returns to this clean baseline.
