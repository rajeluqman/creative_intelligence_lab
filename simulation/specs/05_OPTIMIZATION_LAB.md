# Sim #5 — Optimization Lab (profile → tune → measure)

**Objective:** take a deliberately slow/skewed sim job, diagnose it, tune it, and **measure the
before/after delta**. The number is the story — "I cut runtime from X to Y by Z" beats any adjective.

**RBC tasks covered:** 7 duration trend, 61–70 (Databricks/Spark perf, transferable), 72/74 Snowflake
sizing/clustering, optimization half of day-to-day.

**Interview soundbite:** *"I optimize from evidence — EXPLAIN/profile first, change one thing,
measure. No speculative tuning."*

## Sonnet steps (per drill — pick a `perf_*` fault)
1. Baseline green + timed. Record clean runtime (`dbt build` timing / `run_results.json`).
2. `python simulation/faults/inject.py <perf_*>` (skew / exploding_join / small_files / full_scan).
3. **Profile before touching anything:** DuckDB `EXPLAIN ANALYZE`, row counts at each step, timing.
   Map to the Spark-world equivalent (shuffle/skew/scan) using the cheatsheet translation table —
   so the diagnosis transfers to a Databricks interview question.
4. Form ONE hypothesis, apply ONE fix (repartition / fix join grain / compact / add pruning).
5. Re-time. Compute the delta. If no improvement, revert and re-hypothesize (don't stack guesses).
6. `runbook/05_optimization_<fault_id>.md` in the **optimization card format** (technique · layer ·
   before → after · `file:line` of the change · why it worked). Labeled SIMULATED — not promoted to
   real `cheatsheets/optimization/` (gate needs a real post-v1 finding).

## Definition of Done
1. Before AND after timings recorded (real numbers, same machine/run).
2. Exactly one change attributed to the improvement (or an honest "no gain, reverted").
3. `runbook/05_optimization_<fault_id>.md` cites the change `file:line`; `check_isolation.py` PASS.
4. STAR row filled. (Do ≥2 `perf_*` faults for breadth.)

> Note: this is the legitimate, sandboxed home for the rejected gym "optimization drill" — outside
> product scope, never faking a real `cheatsheets/` card.
