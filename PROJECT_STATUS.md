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

## Doc-gap convene — 2026-06-22 (5 docs added, +1 stale-doc fix)
Compared this repo's doc set against two sibling portfolio repos (olist-ecommerce-pipeline,
pharma_novartis_sttm) on the same "DE Cabinet Gym" 7-doc framework. @data-architect (Clean-ERD
gate) + @scope-guardian (scope gate) **both approved all 5 additions, no veto** — ruled
documentation-debt closure, not scope creep (no new model objects, no new pipeline behavior).
- **Added:** `architecture/{BRD,DRD,DATA_DICTIONARY,DQD,STTM}.md`. BRD/DQD carry PENDING
  owner-review rows (@product-owner / @data-quality-steward drafted-by-convene, not yet
  directly reviewed). STTM was flagged the most genuinely-missing artifact.
- **Required fix done first:** `DATA_MODEL.md` §4/§6 still called `fact_ad_performance` VETOED
  (stale vs ADR-004's conversion + ERD/v1.5 carrying it as built). Reconciled — §6 now scopes
  the *permanent* veto to backward-propagation onto RAW via `parent_asset_id` only; the fact
  itself is a v1.5 object. ERD_consolidated.md (10-table inventory) is authoritative.
- **Deliberately NOT added** (confirmed by @scope-guardian, not re-litigated): OPS_RUNBOOK,
  INTERVIEW_GUIDE, RUNBOOK_cloud_migration (all Phase-5/post-ship or post-execution — Gold still
  stubs); AH.md + erwin/ERD.md (duplicate STACK_AND_FLOW + ERD_consolidated); INCUBATOR/SLA/
  incidents gym apparatus (already REJECTED in BACKLOG.md); PLAYBOOK_REFERENCE (standalone repo).
- **New open items surfaced by STTM:** `dim_asset.parent_asset_id` / `bridge_asset_lineage`
  population mechanism is unspecified in any ratified doc — routes to @data-architect when needed.

## Real findings from the convene (fix during v1)
1. ✅ **DONE — `bridge_ad_chunk` CRITICAL uniqueness test** added to `_performance.yml`
   (`unique_combination_of_columns [ad_id, chunk_id, position_in_ad]` + not_nulls + position range).
   Hand-entered EDL seed had no grain guard = silent fan-out risk (pharma `stg_beta__ndc` bug class).
2. ⬜ **TODO — 5th LLM-output gate (non-triviality / completeness-floor).** @data-quality-steward:
   the 4 existing gates all pass a schema-valid-but-empty `{"chunks": []}` Gemini response. Add a GE
   expectation `chunks length >= 1` (or duration-ratio floor) at the Bronze→Silver boundary; quarantine empties.
3. ⬜ **TODO — row-count reconciliation** EDL→`bridge_ad_chunk` (inner join can silently drop EDL
   rows whose `chunk_id` is absent from `fact_chunk`). HIGH.

## Bronze source wiring — FIXED 2026-06-22 (@senior-data-engineer)
Gap: `source('bronze','bronze_asset_raw')` / `bronze_ad_performance_raw` had no pointer to real
S3 — `_sources.yml` had no `meta.external_location`, no `macros/` existed, `profiles.yml`'s S3
settings were commented out. Found while building `scripts/run_gemini_extract.py` /
`ingest_drive_to_s3.py` (those write real S3 paths; dbt couldn't read them back).
- **`profiles.yml`**: activated `settings: {s3_region: ...}` (was commented out), reading
  `AWS_REGION` env var (default `ap-southeast-1`, matches `.env.example`). Credentials resolve
  via default AWS credential chain — same chain the scripts' `CREATE SECRET (..., PROVIDER
  CREDENTIAL_CHAIN)` pattern uses, no new auth mechanism introduced.
- **`models/staging/_sources.yml`**: added `meta.external_location` to both tables (dbt-duckdb
  native source feature — confirmed in `relation.py`, not a custom macro):
  - `bronze_asset_raw` → `s3://{S3_BUCKET}/bronze/{CLIENT_ID}/asset_raw/*.parquet` (glob across
    all asset files for the active client partition — matches `run_gemini_extract.py`'s
    one-file-per-`asset_id` write pattern exactly).
  - `bronze_ad_performance_raw` → `s3://{S3_BUCKET}/bronze/{CLIENT_ID}/ad_performance_raw/*.parquet`
    (same naming convention; no writer script exists yet for this one — path is ready, not yet fed).
  - `CLIENT_ID` defaults to `demo_client` (matches `.env.example` + the DAG's `Param` default) —
    resolves ONE client per dbt invocation, mirroring the DAG's single-client-per-run contract.
- **No macro needed** — `meta.external_location` is sufficient; did not add a `macros/` directory.
- **Verified**: `dbt parse` clean, `dbt compile` clean (18 models / 17 tests / 4 seeds / 2 sources,
  zero errors), `dbt seed` 4/4 PASS. Compiled SQL confirmed resolving to
  `s3://creative-intel-lake/bronze/demo_client/asset_raw/*.parquet` (proof, not just parse-success).
- **Flagged, not decided here** (routes to @data-architect if/when needed): multi-client
  cross-partition reads (globbing across ALL `client_id`s in one dbt build, e.g. for a multi-tenant
  backfill) are out of scope — current fix resolves exactly one client per run, matching today's
  DAG contract. Also unresolved (pre-existing, not introduced by this fix, flagged in
  `ingest_drive_to_s3.py`'s own header): whether `client_id` partitioning is mandatory or
  optional-with-blank-fallback — both code paths exist; DAG always populates it today so this
  didn't block the fix, but the doc conflict is still open.

## Bronze grain — VETOED + FIXED 2026-06-22 (@data-architect)
`run_gemini_extract.py`'s first draft wrote chunk-grain Bronze (one row per chunk), matching
what `stg_gemini_raw.sql` happened to already assume (a `select` with no `unnest()`).
**@data-architect VETOED this** — it re-litigates ADR-003's own "Rejected alternatives" row
("Chunk in the Python extraction step (pre-Bronze)": rejected because "the raw artifact
would no longer be the verbatim API response"). Required fix = Option B:
- **`scripts/run_gemini_extract.py`**: now writes Bronze at **asset grain** — one row per
  asset, `raw_response` = the verbatim Gemini JSON envelope untouched, +
  `asset_id`/`content_sha256`/`model_version`/`prompt_version`/`chunk_count`/`load_ts`.
  `chunk_count` = `len(chunks)` from the response, satisfying
  `great_expectations/expectations/bronze_asset_raw.json`'s CRITICAL gate (confirmed by DA as
  already-correctly-asset-grain — no change needed to that file).
- **`models/staging/stg_gemini_raw.sql`**: now does the actual explosion its own header
  comment always promised — `unnest(cast(json_extract(raw_response,'$.chunks') as json[]))
  with ordinality`, generating `chunk_id` deterministically (`asset_id || '_' ||
  lpad(chunk_sequence,3,'0')`) so re-parsing the same frozen Bronze row is reproducible.
  `int_chunk_cleaned.sql` and everything in Gold are unchanged (same chunk-grain contract
  they always expected).
- Added `json` to `profiles.yml` extensions (needed for `json_extract`/array casts).
- **Verified for real** (not just parse-clean): wrote a real asset-grain Bronze parquet to
  the throwaway `S3_STAGING_BUCKET`, read it back, ran the exact compiled `stg_gemini_raw.sql`
  unnest logic against it via real S3 — got the correct 2-row chunk-grain output with right
  types (`VARCHAR[]` arrays intact). Cleaned up all test artifacts after. `dbt parse` +
  `dbt compile` + `dbt seed` + `dbt build -s +marts.core` all clean — single expected failure
  remains (`stg_gemini_raw`: no real Bronze data exists yet for `demo_client`, since no real
  video has been extracted) — same failure point as before this fix, now with a wiring-proves
  error message ("no files match") instead of a wiring-is-broken one ("schema does not exist").

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
