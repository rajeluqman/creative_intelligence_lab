# Pipeline Documentation

> **Audience: everyone.** The flow: source → landing → bronze → silver → gold, and what each
> hop does. Full detail lives in the linked pages.

## The flow
`architecture/STACK_AND_FLOW.md` — source (client Google Drive) → landing (raw, S3) → Bronze
(verbatim Gemini JSON, S3, append-only) → Silver (one row per semantic chunk, S3 external parquet)
→ Gold/marts (graph edges + star facts, S3 external parquet) → serving (Snowflake external tables +
native VECTOR search, live; DuckDB VSS $0 fallback). See that page for the full layer-by-layer
detail and storage paths; see **Deployment Guide** for how Snowflake serving is actually
provisioned/refreshed.

## The dbt DAG
`architecture/DBT_DAG.md` — how the models depend on each other (staging → intermediate → marts),
build order, and where the graph edges vs star facts split.

## Requirements & specs behind this pipeline
These aren't in the standard 8-page taxonomy but are real planning artifacts worth knowing about:
- `architecture/BRD.md` — business requirements (who needs this, what problem it solves)
- `architecture/DRD.md` — design requirements (what the system must do, not how)
- `architecture/SPEC_v1_search.md` — the v1 search/mix-and-match feature spec
- `architecture/SPEC_v1.5_performance_marts.md` — the v1.5 performance-marts feature spec
