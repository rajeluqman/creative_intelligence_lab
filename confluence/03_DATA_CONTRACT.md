# Data Contract

> **Audience: source team & data engineers.** Schema, data types, mandatory fields, null rules,
> and the lineage/identity rules that make a field trustworthy. Full detail in the linked pages.

## Source-to-target mapping
`architecture/STTM.md` — exactly how each source field maps to its target column, including type
casts and transformation rules.

## Identity & lineage rules (binding)
`architecture/LINEAGE_CONTRACT.md` — the `asset_id` formula
(`sha256("{client_id}:{content_sha256}")`), required storage-path shape, and the checks
(`tests/lineage_contract.py`) that enforce it on every CI run.

## Stack & scope boundary (binding)
`architecture/BOUNDARY_CONTRACT.md` — what tech/scope is rejected (Spark, Databricks, MinIO,
vector DB, RAG, dashboards) and why, enforced by `tests/boundary_contract.py`.

## Data model (entities, grain, keys)
- `architecture/ERD_consolidated.md` — the authoritative entity-relationship diagram
- `architecture/DATA_MODEL.md` — conceptual/logical/physical model, v1
- `architecture/DATA_MODEL_v1.5_PERFORMANCE.md` — the v1.5 performance-marts extension

## Quality rules (mandatory fields, value ranges, null handling)
`architecture/DQD.md` — the Data Quality Document: the 5 LLM-output gates, severity levels,
golden-dataset threshold, and quarantine strategy.
