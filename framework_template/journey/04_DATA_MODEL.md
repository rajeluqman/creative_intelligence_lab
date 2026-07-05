<!-- FRAMEWORK_TEMPLATE: UNFILLED — remove this line once real project content is added below -->
# 04 — Data Model

> If not applicable: `N/A — <reason>`. See `00_START_HERE.md`.

## Modelling approach chosen (and why)
State it plainly: star schema / graph / vault / OBT / hybrid. Cite the ADR that made this call
(`governance/ADR/`). If no ADR exists yet for this decision, write one before continuing — this
is exactly the kind of decision ADR-000 requires be gated, not assumed.

## Grain declarations (one row per table/model)
| Table/model | Grain (what one row represents) | Business entity | Layer (bronze/silver/gold) |
|---|---|---|---|

## Clean-model doctrine (non-negotiable regardless of stack)
- 1 table = 1 grain = 1 business entity — no mixed-domain dimensions.
- Bridge tables (not CTEs) for N:N relationships.
- Serving layer = view, never a duplicated physical copy of Gold.
- One isolated SCD strategy per table, stated explicitly (Type 1 / Type 2 / snapshot / none).
- What's deliberately OUT of the model stays named here, not silently absent.

## ERD / diagram
Link or embed. If using `.dbml` or similar, note the file path here.

## Identity / grain fidelity
How are records identified across near-duplicates or re-ingests (content hash? natural key?
surrogate key + SCD2)? This becomes the identity axis a gate script checks — see
`gates/framework.yml` → `identity`.
