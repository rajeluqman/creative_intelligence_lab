<!-- FRAMEWORK_TEMPLATE: UNFILLED — remove this line once real project content is added below -->
# 03 — Data Requirements (DRD)

> If not applicable: `N/A — <reason>`. See `00_START_HERE.md`.

## Required entities/attributes to answer 02's questions
Trace each metric in `02_BUSINESS_QUESTIONS.md` back to the raw field(s) it needs. If a metric
has no traceable field yet, that's a real gap — name it here, don't paper over it.

| Metric (from 02) | Required field(s) | Present in source today? | Gap / transform needed |
|---|---|---|---|
| | | | |

## Non-functional requirements
- Freshness (how stale can this be before the business question is unanswerable?)
- Retention (how long must raw/derived data be kept, and why — legal/replay/audit)
- PII/sensitive fields — list them; masking/handling approach goes in `06_DQ_PLAN.md`.

## Assumptions
Anything assumed about the source data that, if wrong, breaks downstream models. Tag each with
"(unverified)" if not checked directly against the source this session — per anti-shortcut
discipline, don't let an assumption silently become a fact.
