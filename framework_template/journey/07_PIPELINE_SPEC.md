<!-- FRAMEWORK_TEMPLATE: UNFILLED — remove this line once real project content is added below -->
# 07 — Pipeline Spec

> If not applicable: `N/A — <reason>`. See `00_START_HERE.md`.

## Layers and compute
| Layer | Storage | Compute/engine | Why this engine (cite ADR) |
|---|---|---|---|
| Landing/Bronze | | | |
| Silver | | | |
| Gold/marts | | | |
| Serving | | | |

## Orchestration
- Tool (Airflow/cron/manual) and DAG file location.
- Schedule/trigger.
- Deferrable/retry policy.

## Idempotency & rerun semantics
- Identity key used to detect "already processed" (skip-existing) — cite `04_DATA_MODEL.md`
  identity section.
- What happens on a partial-failure rerun — is it safe to just re-run, or is manual cleanup needed?
- Backfill procedure, if different from normal run.

## Failure handling
Alerting mechanism (Slack/email/none) and what triggers it. Cite the actual code path
(`file:line`), not "we have alerting" as an unverified claim.
