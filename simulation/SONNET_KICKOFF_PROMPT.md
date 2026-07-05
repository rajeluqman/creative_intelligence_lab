# Sonnet kickoff prompt — RBC Simulation Lab execution

> Paste the block below into a fresh **Sonnet** session (cheap execution; Opus already did the
> design). It points Sonnet at the specs and the guardrails so it needs no high-level decisions.

---

```
You are executing the RBC simulation lab. Opus already designed it — your job is to BUILD per the
specs, making no high-level design decisions (if a spec is ambiguous, write the question into
simulation/runbook/OPEN_QUESTIONS.md and pick the smallest reasonable option, don't redesign).

READ FIRST, IN ORDER:
1. simulation/00_MASTER_PLAN.md      (the 5 tracks, sequencing, global Definition of Done)
2. simulation/ISOLATION_CONTRACT.md  (the hard isolation rules)
3. The spec for the track you're building (simulation/specs/0N_*.md)

HARD RULES (non-negotiable):
- Run `python simulation/check_isolation.py` before you start and before you finish. Must PASS.
- Everything stays inside simulation/. Never edit real models/, seeds/, architecture/, confluence/,
  dags/, tests/, or ADRs. Never reference s3://creative-intel-lake/... ; only s3://creative-intel-staging/sim/.
- Sim #2 (PySpark): pyspark goes ONLY in simulation/spark/requirements.txt, code ONLY in
  simulation/spark/ — then run `python tests/boundary_contract.py` and confirm PASS.
- Anti-shortcut (CLAUDE.md): no track is "done" on a parse-clean. Run the named gate, restate the
  spec's Definition of Done as a checklist, attach evidence (command output / file:line) per item.
  No evidence = "unverified", not "done".

BUILD ORDER (per 00_MASTER_PLAN sequencing):
1. Sim #1 migration dry-run → clean baseline (specs/01) — DO THIS FIRST.
2. Sim #4 reconciliation harness (specs/04) — reused by #1's cutover gate, #3, #5.
3. Faults library inject.py/reset.py (faults/README.md contract).
4. Sim #3 incident drills + Sim #5 optimization drills (consume the fault lab; do ≥2 each).
5. Sim #2 PySpark parity (independent).

After each track: fill its STAR row in simulation/specs/07_INTERVIEW_CHEATSHEET.md with evidence.

START with Sim #1. Confirm the isolation check passes, then build the sim_dbt seeds + legacy +
migrated models per specs/01_SIM_migration_dryrun.md.
```
