# Sim #3 — Incident End-to-End (troubleshooting drill)

**Objective:** inject a fault → let a gate catch it → trace symptom back to root → fix → write a
postmortem. Repeatable: each fault id is a fresh drill. This is the production-support credibility.

**RBC tasks covered:** 13–27 (incident/support), esp. 13 investigate, 15 RCA+postmortem, 16/19/20 fix,
24 known-issues, 26 idempotency.

**Interview story (STAR):**
> S: overnight pipeline failed / produced bad data. T: restore correctness + prevent recurrence.
> A: traced from symptom (far downstream) back to root via observability; fixed; postmortem.
> R: MTTR ___, gate added so it can't recur silently. (fill per drill)

## Sonnet steps (per drill — pick a data-quality or availability fault)
1. Baseline green (`faults/reset.py`), `check_isolation.py` PASS.
2. `python simulation/faults/inject.py <dq_*|av_*>` — note the expected symptom it prints.
3. **Observe, don't peek at the fault.** Run the sim build + gates; capture the symptom *as it
   surfaces* (downstream), then trace backward (DuckDB `EXPLAIN`/logs/`run_results.json` — use the
   DuckDB-translation table in `cheatsheets/troubleshooting/00_INDEX.md`).
4. Root-cause, fix in `migrated/` (or add a guard), rebuild, confirm gate green.
5. Write `runbook/03_postmortem_<fault_id>.md` using the **troubleshooting card format** (symptom →
   trace → root cause → fix `file:line` → prevention). Labeled SIMULATED — NOT promoted to real
   `cheatsheets/` (no-fabrication gate).

## Definition of Done
1. The injected fault was caught by a NAMED gate (not eyeballing) — record which.
2. Fix verified by re-running that gate green; `check_isolation.py` PASS; `reset.py` works after.
3. `runbook/03_postmortem_<fault_id>.md` cites the real fix `file:line`.
4. STAR row filled. (Do ≥2 different faults for ≥2 stories.)
