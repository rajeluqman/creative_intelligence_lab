<!-- FRAMEWORK_TEMPLATE: UNFILLED — remove this line once real project content is added below -->
# 06 — Data Quality Plan (DQD)

> If not applicable: `N/A — <reason>`. See `00_START_HERE.md`.

## Gates per layer
| Layer | Check | Tool (GE / dbt test / custom script) | Fail action (block build / warn / log) |
|---|---|---|---|

## LLM/ML-output-specific gates (if this pipeline has a non-deterministic step)
Non-deterministic outputs (LLM extraction, ML scoring) need a different quality strategy than
deterministic ETL — a golden dataset + value-range/schema gate, not exact-match assertion.
Describe the golden-dataset approach here, or write `N/A` if this pipeline is fully deterministic.

## PII / sensitive-field handling
Mask order, hashing algorithm, and which ADR governs this (should cross-reference an ADR named
in `04_DATA_MODEL.md` or a dedicated PII ADR).

## Known accepted quality gaps
Anything currently failing or WARN-ing that's been formally accepted rather than silently
ignored (mirrors the CIL "paysim GE 14/15 WARN → written rationale" precedent — an accepted gap
must have a dated written reason, not just a passing eye).
