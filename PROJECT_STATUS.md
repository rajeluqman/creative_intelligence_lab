# PROJECT STATUS — Creative Intelligence Pipeline

> Resume checkpoint. Read this BEFORE reading code (token discipline, CLAUDE.md).

## Where we are
Standalone scaffold complete. Core dimension layer is **real and tested**: `dim_client`,
`dim_asset`, `bridge_asset_lineage` build and pass all FK/uniqueness tests against seeded
data. Chunk-grain Silver/Gold (`stg_gemini_raw`, `int_chunk_cleaned`, `fact_chunk`, the
keyword/theme/compatibility bridges) are still wired-but-empty — correct SQL, blocked on
real Gemini output (no video has been extracted yet; see "Next step when resuming").
`fact_ad_performance` v1.5 models remain `where 1=0` stubs.
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

## Multi-client tenancy (ADR-006) + landing TTL (ADR-007) — IMPLEMENTED 2026-06-22
Owner brief: real agencies run multiple clients + ad-hoc batch triggers + a 30-day landing
holding period. Convened @data-architect on the brief; owner then directed "implement all of
it now, before testing with my own Drive folder" (so the as-built code wouldn't need rework
right after a real test). Both ADRs ratified-with-conditions; all code now matches them, and
the full chain was tested for real, not just parse-checked:
- **`architecture/ADR-006-multi-client-tenancy.md`** (new) — `dim_client` dimension;
  `asset_id = SHA-256(client_id ':' content_sha256)` (tenant-scoped identity, so two clients'
  byte-identical footage never collides); `client_id` lives on `dim_asset` only, reached on
  `fact_chunk` by join, never stored there (Clean-ERD axis 4). `DATA_MODEL.md`, `ERD_consolidated.md`,
  `DATA_DICTIONARY.md`, `STTM.md` amended to match.
- **`architecture/ADR-007-landing-ttl.md`** (new) — owner chose **hard-delete @ 30 days**,
  accepting the named consequence (aged non-golden assets become frozen: re-parse from Bronze
  survives, re-extraction on a new prompt/model does not). Three binding conditions: (1) golden
  exemption via the structurally-unscanned `landing/_golden/` prefix, (2) no delete without a
  confirmed Bronze row first, (3) every delete writes a frozen-asset log record.
- **`scripts/enforce_landing_ttl.py`** (new) — the guarded-delete script the ADR mandates (a
  bare S3 lifecycle rule can't do the conditional Bronze check). Dry-run by default, `--apply`
  to actually delete. **Functionally tested for real** against the throwaway `S3_STAGING_BUCKET`
  (not just parse-checked): aged asset *with* Bronze → deleted + frozen log written; aged asset
  *without* Bronze → skipped, not deleted. All three conditions verified end-to-end, test
  artifacts cleaned up after.
- **`scripts/ingest_drive_to_s3.py` / `run_gemini_extract.py`** — altered to the composite
  tenant-scoped `asset_id`, client-partitioned S3 paths (`landing/<client_id>/...`,
  `bronze/<client_id>/...`), and manifest-row lookup by full dict (not just `source_uri`) so
  `content_sha256` is available separately from `asset_id`.
- **Build-time bug found and fixed (not part of the ADRs themselves):** the data-architect's
  `models/marts/core/dim_client.sql` wrapper model shared its name with `seeds/dim_client.csv`
  → dbt "two resources, identical database representation" collision. Fixed by deleting the
  wrapper (1:1 passthrough with zero transform — same bare-seed pattern already used for
  `dim_platform`) and moving its column tests into `_core.yml`'s `seeds:` key.
- **Seed fixture rename:** `seeds/dim_client.csv` / `asset_manifest.csv` originally used a
  fictional `client_id=voltecx`, inconsistent with the `demo_client` default baked into
  `.env`/`.env.example`/the DAG's `Param`. Renamed to `demo_client` (asset_ids recomputed under
  the new client_id — the hash formula folds in `client_id`, so this wasn't just a string swap)
  so a fresh clone's `dbt seed && dbt build` passes with zero edits.
- **Verified:** `dbt seed` 5/5 PASS; `dbt build -s +marts.core` — `dim_client`/`dim_asset` all
  tests green (PK, FK to `dim_client`, `asset_type` enum); the one remaining failure
  (`stg_gemini_raw`: "no files match bronze/demo_client/asset_raw/*.parquet") is the **expected**
  failure point — no real video has been run through Gemini yet, same failure this repo has had
  since the Bronze-grain fix, now re-confirmed post-multi-client.
- **Flagged, not solved:** ADR-007 names the guarded-delete as "a scheduled Airflow task," but
  Airflow isn't installed in this environment (no `venv_airflow/` yet) and the main DAG's own
  tasks are still TODO-stubs not wired to the now-real scripts. Did not author a new DAG file
  for this — couldn't validate it against a real `DagBag` import here, and inventing
  orchestration code I can't test is worse than naming the gap. `scripts/enforce_landing_ttl.py`
  is fully real and tested at the CLI/function level; wiring it into Airflow is a clean follow-up
  once the orchestration venv exists.

## Next step when resuming (v1 path — build feature store FIRST, serve AFTER it has rows)
1. **Test with a real Drive folder** (the owner's own footage) — set `DRIVE_FOLDER_ID` +
   `GOOGLE_APPLICATION_CREDENTIALS` in `.env`, run `python scripts/ingest_drive_to_s3.py`, then
   `python scripts/run_gemini_extract.py <asset_id>` per landed asset, then `dbt build -s +marts.core`.
   This is the first real end-to-end run — everything above was tested with synthetic fixtures.
2. Wire Great Expectations suites incl. the 5th non-triviality gate (finding #2, still open).
3. v1.5: performance marts + significance post-step + semantic search — DuckDB VSS first ($0),
   then Snowflake Cortex veneer once Gold has real rows + teardown plan (ADR-005 sequencing).
4. Wire the DAG's stub tasks to the now-real scripts (`ingest_drive_to_s3.py`,
   `run_gemini_extract.py`, `enforce_landing_ttl.py`) once Airflow is actually installed.

## Standalone status
Self-contained — see audit in chat 2026-06-22. CLAUDE.md + 8 agents + setup.sh + CI all present;
no parent/gym path dependency. Regenerate `venv/` + `dbt_packages/` via `setup.sh` / `dbt deps`
on a fresh machine (both gitignored). Do NOT commit `.env`.
