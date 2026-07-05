# RBC Simulation Lab — Master Plan

> **What this is:** a *self-contained* practice environment that reproduces the day-to-day of a
> mature-enterprise data role (RBC: ~2,500 pipelines, Teradata/AWS legacy → Databricks/Snowflake
> target, 80–90% migration + maintenance). It exists **only** to generate real, screen-shareable
> artifacts and STAR interview stories. It is **NOT part of v1 product scope** (no scope-guardian
> conflict — see `ISOLATION_CONTRACT.md`).

> **Why it's isolated:** the lab is designed to be *deliberately broken and slowed down later* so you
> can practice **troubleshooting and optimization** on demand. That only works if the sim can never
> corrupt the real ("main") pipeline. Isolation is therefore a hard contract, enforced by
> `check_isolation.py`, not a guideline.

---

## Model routing (ADR-012)
- **Opus (this session) = design.** Every spec, contract, the isolation guard, the fault catalog,
  the kickoff prompt, and skeleton stubs are written here so the hard reasoning is done once.
- **Sonnet (next session) = execution.** It follows the step-by-step specs to write the actual dbt
  models, fault code, and reconcile logic. It should need **zero high-level design decisions** — if
  it does, that's a gap in these specs; record it in `runbook/` and escalate, don't improvise.

Start the Sonnet session by pasting `SONNET_KICKOFF_PROMPT.md`.

---

## The five tracks

| # | Track | Spec | RBC skill it proves | Artifact produced |
|---|-------|------|---------------------|-------------------|
| 1 | **Migration dry-run** | `specs/01_SIM_migration_dryrun.md` | Teradata→Snowflake logic migration, STTM, cutover, rollback | `runbook/01_migration_case_study.md` + reconciled marts |
| 2 | **PySpark parity** | `specs/02_SIM_pyspark_parity.md` | "same logic, two engines" (dbt-SQL ↔ Spark) — closes the no-Spark gap | `spark/parity_notebook.py` + diff report |
| 3 | **Incident E2E (troubleshoot)** | `specs/03_SIM_incident_e2e.md` | inject fault → detect via gate → RCA → fix → postmortem | `runbook/03_postmortem_<incident>.md` |
| 4 | **Value-level reconciliation** | `specs/04_SIM_value_reconciliation.md` | "row-count match ≠ done; values reconcile" (the banking skill) | `reconcile/` harness + reconciliation report |
| 5 | **Optimization lab** | `specs/05_OPTIMIZATION_LAB.md` | profile a slow/skewed job → tune → measure delta | `runbook/05_optimization_<case>.md` (before/after numbers) |

Reference: `specs/06_RBC_TASK_MAP.md` (the 100 day-to-day tasks, tagged by what this lab can
simulate) · `specs/07_INTERVIEW_CHEATSHEET.md` (STAR stories, filled in as each track completes).

---

## Recommended sequence
1. **Build the clean baseline first** (Sim #1 up to a green reconcile) — everything else needs a
   known-good state to break and reset against.
2. **Sim #4** — formalize the reconciliation harness (reused by #3 and #5).
3. **Sim #3 + Sim #5** — these *consume* the fault lab (`faults/`). Do them repeatedly; each
   inject→fix or inject→tune cycle is a fresh story.
4. **Sim #2** — independent; do any time to close the Spark gap.

---

## The fault lab (`faults/`) — the engine for tracks 3 & 5
A named, **reversible** fault is the unit of practice. `faults/inject.py <fault_id>` mutates the
sim's clean state; `faults/reset.py` restores it (re-seed + re-build sim — clean state is always
rebuildable, never hand-patched). Catalog: `faults/README.md`. Categories: data-quality,
reconciliation (silent value drift — the worst), availability, **performance** (skew, exploding
join, small-file, unpartitioned scan — these feed Sim #5).

---

## Global Definition of Done (every track)
1. `python simulation/check_isolation.py` → PASS (lab never touched main).
2. The track's own gate passes (named in its spec) — run the real gate, don't eyeball.
3. The named artifact exists in `runbook/`, `spark/`, or `reconcile/`.
4. The STAR row in `specs/07_INTERVIEW_CHEATSHEET.md` is filled with evidence (`file:line` / command
   output), not adjectives.
5. The lab is left in (or resettable to) a clean state.

> Anti-shortcut (CLAUDE.md): no track is "done" on a parse-clean. Run the gate, restate the spec as
> a checklist, attach evidence per item. No evidence = "unverified", not "done".

---

## Directory map
```
simulation/
  00_MASTER_PLAN.md          ← you are here
  ISOLATION_CONTRACT.md      ← the binding isolation rules
  check_isolation.py         ← guard (run before every session + commit)
  SONNET_KICKOFF_PROMPT.md   ← paste this to start the execution session
  sim_dbt/                   ← isolated dbt project (name: sim_creative_intel, target: sim)
    dbt_project.yml          ← built (stub) — Sonnet adds models
    profiles.sim.yml.example ← copy to ~/.dbt or DBT_PROFILES_DIR
    models/legacy/           ← synthetic "Teradata" source-of-truth (Sonnet builds)
    models/migrated/         ← the Snowflake/Spark target (Sonnet builds)
    seeds/                   ← synthetic legacy extract (Sonnet builds)
  spark/                     ← Sim #2 PySpark parity
  faults/                    ← inject.py / reset.py / catalog/ (Sonnet builds; spec'd here)
  reconcile/                 ← Sim #4 harness (Sonnet builds; spec'd here)
  runbook/                   ← YOUR practice writeups (postmortems, case studies, opt logs)
  specs/                     ← 01–07 (all written by Opus, this session)
```
