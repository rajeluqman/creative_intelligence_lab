# PROJECT STATUS — Creative Intelligence Pipeline

> Resume checkpoint. Read this BEFORE reading code (token discipline, CLAUDE.md).

## Where we are
Standalone scaffold complete; **v1 product NOT built yet** — models are stubs (`where 1=0`).
Architecture of record is ratified (`architecture/`); cabinet of 7 agents seated in `.claude/agents/`.

## Cabinet convene — 2026-06-22 (roster ruling)
Convened all 6 core agents on: unified-S3 storage, ERD/DDL, the conformance/bridge principle,
and the proposed gym-apparatus port. Outcomes:
- **S3 storage:** convene found doc ahead of as-built (marts were local DuckDB). **Owner then
  overrode to unified S3 (no MinIO)** → now ratified as ADR-005; docs rewritten to S3-canonical.
- **ERD/DDL:** ERD governed ✓; dbt-models-ARE-DDL is correct — no separate `.sql` DDL artifact. No action.
- **Conformance/bridge principle:** present & clean (the model's spine) — full Clean-ERD Doctrine pass.
- **Gym port:** deferred/rejected → see `BACKLOG.md`. Pivot to v1.

## Real findings from the convene (fix during v1)
1. ✅ **DONE — `bridge_ad_chunk` CRITICAL uniqueness test** added to `_performance.yml`
   (`unique_combination_of_columns [ad_id, chunk_id, position_in_ad]` + not_nulls + position range).
   Hand-entered EDL seed had no grain guard = silent fan-out risk (pharma `stg_beta__ndc` bug class).
2. ⬜ **TODO — 5th LLM-output gate (non-triviality / completeness-floor).** @data-quality-steward:
   the 4 existing gates all pass a schema-valid-but-empty `{"chunks": []}` Gemini response. Add a GE
   expectation `chunks length >= 1` (or duration-ratio floor) at the Bronze→Silver boundary; quarantine empties.
3. ⬜ **TODO — row-count reconciliation** EDL→`bridge_ad_chunk` (inner join can silently drop EDL
   rows whose `chunk_id` is absent from `fact_chunk`). HIGH.

## Owner directive — 2026-06-22 → ratified as ADR-005
**Storage = unified S3 (no MinIO). Serving = Snowflake Cortex veneer over Gold S3.**
Owner overrode cabinet local-first + the "no Snowflake" boundary; trial credits cover cost.
Captured in `architecture/ADR-005-unified-s3-and-snowflake-serving.md`. Key points:
- **All layers persist to real S3** (`landing/bronze/silver/gold`); Silver/Gold = `external`
  parquet read via httpfs; DuckDB catalog ephemeral (compute only). **MinIO dropped** (couldn't
  back Snowflake + credits cover real S3). Staging/drills use a separate throwaway S3 bucket.
- **Snowflake Cortex = showcased serving** (external tables + Cortex Search + Power BI), BYO Gemini
  embeddings persisted in Gold. **DuckDB VSS over Gold S3 = retained $0 fallback** (`SERVING_BACKEND`).
- **Gold S3 = sole source of truth; Snowflake read-only veneer** (reconciliation test gates it;
  DA veto if it becomes a 2nd truth). Tradeoff accepted: no longer offline-$0 standalone.
- **Provisioning owner-gated** (`aws s3 mb` / Snowflake `CREATE` — confirm first). FinOps preconditions
  before Snowflake: COST_LOG + day-25 teardown + $0 fallback proven first + single-sourced embeddings.

## Next step when resuming (v1 path — build feature store FIRST, serve AFTER it has rows)
1. Implement stubs per `architecture/SPEC_v1_search.md` — staging (`stg_*`) → `int_chunk_cleaned`
   → `fact_chunk` + `dim_asset` + bridges. Set `dbt_project.yml` marts `materialized: external`
   + `location: s3://{{env_var('S3_BUCKET')}}/{silver,gold}/...`; set `s3_region` in profiles.
2. Implement ingest + Gemini scripts (TODO stubs) writing landing/bronze to S3; BYO embeddings in Gold.
3. Wire Great Expectations suites incl. the 5th non-triviality gate (finding #2).
4. v1.5: performance marts + significance post-step + semantic search — DuckDB VSS first ($0),
   then Snowflake Cortex veneer once Gold has real rows + teardown plan (ADR-005 sequencing).

## Standalone status
Self-contained — see audit in chat 2026-06-22. CLAUDE.md + 8 agents + setup.sh + CI all present;
no parent/gym path dependency. Regenerate `venv/` + `dbt_packages/` via `setup.sh` / `dbt deps`
on a fresh machine (both gitignored). Do NOT commit `.env`.
