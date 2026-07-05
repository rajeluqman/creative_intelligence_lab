# RBC Interview Cheat-Sheet — STAR stories from the sim lab

> Fill one STAR row per completed track, **with evidence** (`file:line` / command output), not
> adjectives. These are your spoken answers; the `runbook/` artifacts are what you screen-share.

## The three soundbites (memorize)
1. *"Row-count match is necessary, not sufficient — migration is done when values reconcile, not
   when counts do."*
2. *"At 2,500 pipelines, lineage and reconciliation aren't documentation, they're change-safety
   infrastructure — I treat them as contract tests in CI."*
3. *"I've made a real rollback call: a managed service hit a trial-tier wall, I reverted to a $0
   fallback and kept the source-of-truth in S3."* (ADR-005 — this one is *real*, not simulated.)

## Framing line (open with this when they mention scale)
> "At that scale the binding constraint isn't building — it's **change safety**. The work is
> reconciliation before cutover, lineage so you know the blast radius, and SLA/cost monitoring so
> regressions surface before the business does. Migrating Teradata logic *without silently changing
> a number* is the hard part."

## STAR table (fill as tracks complete)
| Track | Situation/Task | Action | Result (with evidence) | Artifact to show |
|-------|----------------|--------|------------------------|------------------|
| #1 Migration | Teradata→Snowflake, no number changes | | | `runbook/01_migration_case_study.md` |
| #2 PySpark parity | same logic on Spark | | | `runbook/02_parity_report.md` |
| #3 Incident (fault A) | overnight failure/bad data | | | `runbook/03_postmortem_<id>.md` |
| #3 Incident (fault B) | second failure mode | | | `runbook/03_postmortem_<id>.md` |
| #4 Reconciliation | counts match, values don't | | | `runbook/04_reconciliation_demo.md` |
| #5 Optimization (A) | slow/skewed job | | | `runbook/05_optimization_<id>.md` |
| #5 Optimization (B) | second perf pattern | | | `runbook/05_optimization_<id>.md` |

## Honesty guardrails (say these if asked)
- The lab is a **simulation** — synthetic data, injected faults. Say so plainly; the *skills and
  motions* are real, the incidents are drills. Interviewers respect "I built a fault-injection lab to
  practice the RBC migration/maintenance loop" far more than a fabricated war story.
- Real, non-simulated wins from this project: the Cortex→VECTOR→DuckDB rollback (ADR-005), the
  governance-as-code gates (lineage/boundary/doc contracts), AWS OIDC CI (ADR-013).

## Study-only gaps to read up on (the ❌ tasks)
Teradata: BTEQ, stored procs, `QUALIFY`, SET/MULTISET, PI/SI indexing. Databricks: Delta
`OPTIMIZE`/`VACUUM`/Z-order, partition/shuffle tuning, broadcast joins, cluster sizing. Streaming:
Kafka lag basics. Map each back to a DuckDB/dbt concept you *did* do (see `05` translation tables).
