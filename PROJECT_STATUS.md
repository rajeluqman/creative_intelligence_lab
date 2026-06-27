# PROJECT STATUS — Creative Intelligence Pipeline

> Resume checkpoint. Read this BEFORE reading code (token discipline, CLAUDE.md).

## ▶ RESUME HERE (next session — read THIS block first, not the whole file)
> Cheap-resume per ADR-012 Lever 6. This file is ~700 lines; you do NOT need to read it all to
> continue. Read this block, do the next step, expand into the dated sections below only for the
> evidence you actually need.

- **Paste-ready first prompt for next session:**
  `Read PROJECT_STATUS "▶ RESUME HERE" and do the next step. Don't re-read the whole repo — open only the files named here, fresh.`
- **Current state (1 line):** v1 + v1.5 built and verified for real (19/19 assets, 169 chunks,
  Silver/Gold on S3, perf marts smoke-tested+reverted); Snowflake serving live (2026-06-27) —
  storage integration + 8 external tables over real Gold S3 (row-for-row reconciled via
  `CREATIVE_INTEL_ROLE`) + a native-`VECTOR` semantic-search view (`PUBLIC.FACT_CHUNK_VECTOR`,
  `search_cli.py --snowflake-semantic`) mirroring the DuckDB VSS path — both query surfaces real
  and verified, see "Cortex Search — tried for real, abandoned..." under item 3 below for why it's
  a VECTOR view and not the managed Cortex Search Service. Airflow standalone restarted + verified
  clean this session (no import errors, `creative_intel_pipeline_v1` resolves). **Item 3's last
  three open sub-items closed same day** (ADR-005 Addendum 2026-06-27 #5) — see immediately below.
- **Cortex Search Service was tried and is a dead end on this account — don't re-attempt it.**
  Three real, successive blockers (BYO-embedding conflict → Dynamic Tables reject external tables
  → trial-tier accounts can't run the AI function it needs at all) — full account-tier wall, not
  an engineering gap. ADR-005 Addenda 2026-06-27 #2/#3/#4 have the complete trail. The native
  `VECTOR_COSINE_SIMILARITY` path built instead is the permanent answer for Snowflake-served
  semantic search here.
- **DONE 2026-06-27 — the three remaining "Snowflake Cortex serving" item 3 sub-items, per
  ADR-005 Addendum #5:** (1) `tests/reconcile_snowflake_serving.py` (new) — row-count + key-set
  reconciliation between real Gold S3 (DuckDB httpfs, ground truth) and the Snowflake external
  tables, via `CREATIVE_INTEL_ROLE`; registered in `tests/GATES.md`. (2) `COST_LOG.md` created
  (gitignored, local monitoring artifact per CLAUDE.md). (3) `dags/creative_intel_pipeline.py`'s
  `refresh_serving` task now does real work for `SERVING_BACKEND=snowflake_cortex`: shells out to
  the new `scripts/provision_snowflake_serving.py --phase refresh --apply` (8×
  `ALTER EXTERNAL TABLE ... REFRESH` + a `CREATE OR REPLACE VIEW` resync of `FACT_CHUNK_VECTOR`),
  then to the new reconciliation script — a mismatch fails the Airflow task loud. `duckdb_vss`
  (default) stays the honest no-op it always was. **Verified for real, not just parse-clean:**
  dry-run of `--phase refresh` reproduces the exact 8 `ALTER`/view/grant statements; the
  reconciliation script fails loud and exact on a missing credential
  (`missing required env var(s): SNOWFLAKE_PASSWORD - refusing to run`), mirroring `env_guard.py`'s
  convention; `airflow dags list-import-errors` clean after the DAG edit; full governance-gate
  sweep clean (ruff, lineage, boundary, doc-reference incl. self-test, repo-map `--check`,
  adr-coupling incl. self-test, golden test). **Not yet done — needs owner confirmation before
  executing for real** (ADR-005: "provisioning stays owner-gated" — `CREATE OR REPLACE VIEW`
  inside the new `refresh` phase is still a CREATE statement): an actual live `--apply` of
  `--phase refresh` and a live run of `reconcile_snowflake_serving.py` against the real account.
  Full detail: ADR-005 Addendum (2026-06-27 #5).
- **AWS OIDC for real `dbt build` in CI — DONE 2026-06-27 (all 4 parts, see ADR-013 + dated
  section below for full evidence).** Owner finished Parts A–C in the AWS console (OIDC provider,
  `creative-intel-ci-role`, trust policy, least-privilege inline policy) and handed over the role
  ARN; Part D (`ci.yml` wiring + the new `architecture/ADR-013-aws-oidc-ci-federation.md`) done
  this session, full governance sweep clean. **Still open, not closeable from here:** a real
  push-to-`main` to actually exercise the `real-build` job for the first time (this session only
  has a feature branch checked out) — whoever merges next should watch the Actions tab.
- **Next concrete step — ONE open thread (the AWS OIDC one above is now closed):** owner sign-off
  to run the new Snowflake `refresh` phase + `reconcile_snowflake_serving.py` live against the
  real account (unchanged from before, still open). Separately untouched: Airflow `@daily`,
  `chunk_theme` vocab-drift design (no default-without-asking answer for either).
- **Scope decision, 2026-06-27 (same session) — v2 BACKLOG permanently REJECTED, not deferred.**
  Owner: "this project is solely the data pipeline, full stop." `CLAUDE.md`'s "v1 Scope (LOCKED)"
  and `BACKLOG.md` both rewritten — the 4 downstream apps (search-engine UI, RAG generator,
  ops dashboard, auto-tagger) + ROAS live-connector ingestion + dedicated vector DB are now
  **REJECTED** (kept named per Clean-ERD "what's OUT stays named," not deleted), not "v2 backlog
  to maybe build later." v1.5 performance *marts* are unaffected (still core pipeline, just
  waiting on real ad-performance data — see the v1.5 section below). Verified: `ruff`, doc-reference
  contract, repo-map `--check` (regenerated — `BACKLOG.md`'s title line changed) all clean.
- **Real Airflow run + a real bug found and fixed, 2026-06-27 (same session):** owner asked to
  trigger Airflow now to use any remaining Gemini quota. Triggered
  `creative_intel_pipeline_v1` for real (`client_id=voltecx`, the real `DRIVE_FOLDER_ID` from
  `.env`) via the live `airflow dags trigger` (scheduler/webserver/triggerer already up on
  port 8080) — not `dags test`, so it ran through the real scheduler exactly as it would for any
  other trigger. **Real bug found:** `sync_drive_to_landing` failed twice
  (`FileNotFoundError: 'secrets/gdrive-service-account.json   # path to service-account JSON, NOT
  the JSON itself'`) — the DAG's hand-rolled `_load_dotenv()` (`dags/creative_intel_pipeline.py`)
  only skipped lines starting with `#`, not inline `# comment` suffixes after a value; bash's
  `source .env` (the documented manual-run path) strips those, so this gap was invisible until a
  non-bash parser hit it. Fixed: strip on `r"\s+#"` after `=`, matching bash's unquoted-comment
  semantics. **Verified for real:** the 3rd retry (post-fix, same DagRun, no manual clear needed —
  the next retry re-imports the fixed module) succeeded; full DagRun → **SUCCESS**:
  `sync_drive_to_landing` real (0 new — the client's Drive folder has no videos beyond the 19
  already-known assets), `list_new_assets` correctly SKIPPED (0 unextracted, **zero Gemini API
  calls** — cost firewall #2 held, confirming there was genuinely nothing new to spend quota on
  despite the ask), `extract_chunks` skip-cascaded, `dbt_build_marts`/`ge_validate`/
  `refresh_serving` all real SUCCESS (`refresh_serving` took the `duckdb_vss` no-op branch,
  matching `.env`'s `SERVING_BACKEND=duckdb_vss`, output text matches this session's new code
  exactly). Full governance-gate sweep re-run clean after the fix (ruff, lineage, boundary,
  repo-map `--check`, adr-coupling). **Honest bottom line for the owner:** there was nothing for
  Gemini to do this run — not a quota or pipeline problem, the Drive folder simply has no new
  videos right now. Add new videos to the same Drive folder and re-trigger to actually spend
  quota on them.
- **If Airflow isn't running when you resume:** it's a background process in this container, not
  guaranteed to survive a session/container restart. Restart with
  `AIRFLOW_HOME=/workspaces/creative_intelligence_lab/airflow_home` **explicitly set** — without
  it, `airflow standalone` silently defaults to `~/airflow` (a different, empty instance) and
  `creative_intel_pipeline_v1` won't appear. `airflow_home/airflow.cfg`'s `dags_folder` was already
  fixed to point at the real `dags/` path 2026-06-27, so that part doesn't need re-fixing. Admin
  login: `admin` / see `airflow_home/standalone_admin_password.txt`. **New gotcha found + fixed
  2026-06-27 (this session):** also `source venv_airflow/bin/activate` (put it on `PATH`) before
  `airflow standalone` — `standalone_command.py` spawns webserver/scheduler/triggerer as
  subprocesses by bare command name (`airflow webserver`, etc.), not by full path, so launching it
  via `venv_airflow/bin/airflow standalone` directly (without activating) makes every subprocess
  fail with `FileNotFoundError: 'airflow'` even though the top-level process itself starts fine.
- **Files in play for that step:** see "Next step when resuming" (bottom of this file) for the
  exact paths per item.
- **Gate to run before declaring any step done:** `python tests/doc_reference_contract.py <doc>` +
  `python tests/lineage_contract.py` + `python tests/boundary_contract.py` + `python scripts/gen_repo_map.py --check`.
- **Session discipline:** watch the Claude Context Bar — red (>75%) = checkpoint here + start fresh.

## Where we are
**Full real end-to-end run complete, 2026-06-24** (started 2026-06-22, real client, real Drive
folder, real Gemini calls — everything before this was synthetic fixtures). **19/19** real
videos fully through Bronze→Silver→Gold; `fact_chunk` has **169 real chunks** from real ad
transcripts (Malay-language automotive ads), both governance contracts green. The last 6 were
quota-blocked at the 2026-06-22 checkpoint (Gemini free-tier `generate_content_free_tier_requests`,
20/day for `gemini-2.5-flash`, confirmed HARD-DAILY) and resumed cleanly 2 days later with zero
pipeline-code change, exactly as that checkpoint predicted (idempotent skip-existing). See "First
real Drive run" below for the 2026-06-22 account (client_id renamed `demo_client`→`voltecx`,
two new automated contracts, three real bugs fixed) and "Gemini quota resume" below for the
2026-06-24 completion (one more real bug found: env vars weren't exported to the shell running
the extraction script).
`fact_extraction_run` and `bridge_asset_lineage` (v1 core) remain `where 1=0` stubs (correction
2026-06-25: this line previously misattributed the stub to `fact_ad_performance`, which is
actually a fully-written model per `architecture/SPEC_v1.5_performance_marts.md` — it's blocked
on missing real Meta/TikTok performance data, not on unwritten SQL; see "Next step" item 4).
Architecture of record is ratified (`architecture/`); cabinet of 7 agents seated in `.claude/agents/`.

## First real Drive run — 2026-06-22 (client: voltecx)
Owner's own Drive folder (25 files, 6 byte-identical dupes correctly collapsed by the
content-hash firewall → 19 real assets). Walked through `.env`/`seeds/dim_client.csv` setup,
service-account JSON placement (new gitignored `secrets/` dir), then ran the real chain.

**Mid-run pivot — `demo_client` → `voltecx` rename (owner caught this, not pre-empted):**
the placeholder `client_id=demo_client` was still wired for this real client. @data-architect
ruling: VETOED prefixing the client into the hash/filename (re-treads ADR-006 Rejected Alt
#2 — the hash already disambiguates tenants; path-level partition is where legibility belongs);
APPROVED the slug rename (asset_ids re-derived — the hash folds `client_id`, so this is a
migration, not a string swap) and a new `ingested_at` provenance column (additive, distinct
from the audit-only `load_ts`). Owner separately confirmed the DAG/script design is genuinely
not hardcoded — `client_id` flows through `CLIENT_ID` env / DAG `--conf` per run, multi-client
intact. Owner also caught that the rename default (`voltecx` as a fallback) was itself a
multi-client misroute risk → `_sources.yml`'s `env_var('CLIENT_ID', 'voltecx')` fallback was
**removed** (now fails loud: `env_var('CLIENT_ID')`, no default); same for the DAG `Param`
(now `""`, `minLength=1`, REQUIRED). CI sets `CLIENT_ID=voltecx` explicitly so the no-default
`env_var` still parses there.

**Two new automated governance contracts appeared this session** (`architecture/
LINEAGE_CONTRACT.md` + `tests/lineage_contract.py`; `architecture/BOUNDARY_CONTRACT.md` +
`tests/boundary_contract.py`; `.claude/hooks/governance_guard.py` + `.claude/settings.json`; a new
"🛑 STOP-GATE" section in this repo's `CLAUDE.md`) — rules-as-code mirroring this project's
existing GE-suite philosophy: lineage (asset_id formula, path/column consistency, no
placeholder `client_id`) and stack/scope boundaries (no Spark/MinIO/vector-DB/RAG/dashboard
imports) are now enforced on every Edit/Write (hook) and every CI run, not just reviewed.
`demo_client` is recorded `GRANDFATHERED`→now resolved (no rows use it; denylist stays).

**Drive folder reorganized mid-run** into `1-edited_video/2-winning_video/3-raw_video`
subfolders — `_list_videos()` was non-recursive (only saw files directly under the top
folder) and would have landed 0 videos; fixed to walk the tree recursively. "Winning ads"
ruled **EDITED**, not a third `asset_type` value — @data-architect: a winning ad is still
physically an edited cut; "which one won" is a performance signal with no ratified v1 home
(CLAUDE.md keeps ad-performance OUT of v1) — conflating the two axes would violate Clean-ERD
domain purity. `_infer_asset_type()` now matches `edited`/`winning`/`winners` → `EDITED`.

**Three real bugs found and fixed (not just the planned work):**
1. `seeds/asset_manifest.csv` mixed CRLF (Python `csv.DictWriter`'s RFC-4180 default) against
   an LF header → DuckDB's CSV sniffer failed outright ("could not detect dialect", reported
   0 columns). Fixed at the source: `_append_manifest_row` now passes `lineterminator="\n"`.
2. `dbt_project.yml`'s seed `+column_types` for `asset_manifest` still listed 8 columns after
   `ingested_at` was added as a 9th — caused the same sniffer failure independently. Fixed.
3. The local `target/dev.duckdb` catalog (ADR-005: ephemeral/compute-only by design) held a
   stale 8-column `asset_manifest` table from before the schema change; `dbt seed` does
   `TRUNCATE`+`COPY`, not `CREATE OR REPLACE`, so the new column never had anywhere to land
   until the catalog file was deleted and rebuilt fresh.

**Verified for real, not just parse-clean:** `dbt build -s +marts.core` → PASS=24 ERROR=0;
`dim_client` 1 row; `dim_asset` 19 rows (14 EDITED/5 RAW, matching the real subfolder split);
`fact_chunk` **131 real chunks** (3–18 per video) across the 13 extracted assets, from real
Malay-language automotive ad transcripts, correct `chunk_theme`/`sentiment`/`standalone_score`;
both contracts green.

**Open, time-gated (not a bug) — RESOLVED 2026-06-24, see "Gemini quota resume" below:** 6/19
assets still needed Gemini extraction at this checkpoint — blocked on the free-tier
`generate_content_free_tier_requests` quota (20/day for `gemini-2.5-flash`), confirmed
HARD-DAILY (backoff-retried, didn't help). Owner chose to wait for the daily reset rather than
enable billing. Missing asset_ids as of this checkpoint: `afbe9bb2…`, `f41426ce…`, `da4a31f7…`,
`bd8e89dc…`, `9965df85…`, `2e757f1e…` (full hashes in `seeds/asset_manifest.csv`) — all 6 done now.

## Gemini quota resume — 2026-06-24 (13/19 → 19/19, contracts green)
Quota reset as predicted; resumed the exact command from the 2026-06-22 checkpoint.

**One more real bug found (not part of the planned work):** `source venv/bin/activate` alone
does not load `.env` — there is no `python-dotenv` call anywhere in the scripts and no
documented `source .env` step, so a fresh shell has `google-genai`/`boto3` on `PATH` but
`os.getenv("S3_BUCKET")` etc. all empty. First extraction attempt failed fast and loud on all
6 assets (`env_guard: S3_BUCKET unset - refusing to run` — exactly the fail-closed behavior
`scripts/env_guard.py`'s docstring promises, not a hang or a silent wrong-bucket write). Fixed
by exporting the file before invoking the script: `set -a && source .env && set +a`. Not a
code change — this checkpoint is the fix (a documented resume step), since `scripts/env_guard.py`
already does its one job correctly; the gap was upstream of it, in how the venv-activate step
is documented. Worth wiring a `python-dotenv` load (or a `source .env` line in the quickstart)
if this trips up the next resume too.

**Verified for real, not just parse-clean:** all 6 extractions exit 0 (idempotent, asset-grain
Bronze written to S3 per `scripts/run_gemini_extract.py`'s contract); `dbt build -s +marts.core`
→ PASS=24 ERROR=0; `dim_asset` **19 rows** (14 EDITED/5 RAW, same subfolder split as before);
`fact_chunk` **169 real chunks** across all **19** distinct assets (queried directly off
`target/dev.duckdb`, not just dbt's own PASS count); `tests/lineage_contract.py` and
`tests/boundary_contract.py` both green.

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
  `dim_client.sql` wrapper model (in `models/marts/core/`, since deleted — see fix below) shared
  its name with `seeds/dim_client.csv` → dbt "two resources, identical database representation"
  collision. Fixed by deleting the
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

## 5th LLM-output gate (non-triviality / completeness-floor) — BUILT 2026-06-25 (@data-quality-steward)
DQD.md §3 item 1 / `PROJECT_STATUS.md` finding #2, closed. The gap: a schema-valid-but-empty
`{"chunks": []}` Gemini response passed all 4 pre-existing gates untouched, because
`stg_gemini_raw.sql`'s `unnest()` of an empty array produces **zero rows** for that asset — it
silently disappears before reaching any Silver-layer row a later gate could test. Fix: a
`dbt_expectations.expect_column_values_to_be_between` test (`min_value: 1`) on the **source**
column `bronze_asset_raw.chunk_count`, added in `models/staging/_sources.yml` (the GE JSON spec
at `great_expectations/expectations/bronze_asset_raw.json` line 12 already declared this check —
this just builds it). `config: {severity: warn, store_failures: true}` — deliberately not
`error`, per DQD.md §1 gate 1's own action-on-failure rule ("quarantine, never blocks batch"): a
failing row lands in dbt's audit-trail failures table for review, doesn't fail `dbt build`'s
exit code over one bad asset. No new quarantine-table model invented — `store_failures` is the
existing dbt-native mechanism. DQD.md (§1 gate table renumbered 0–4, §2, §3, Sign-off Gate) and
`great_expectations/README.md` updated to match.
**Verified for real, not just parse-clean:** `dbt build -s +marts.core` against the real 19-asset
S3 data → new test `dbt_expectations_source_..._chunk_count__1` **PASS** (all 19 real assets have
chunk_count ≥ 1, as expected — this gate exists to catch *future* empty-chunk responses, not a
known-bad row today); full build PASS=25 ERROR=0 WARN=0, nothing pre-existing broke.
**Noted, not fixed (pre-existing, unrelated to this change):** dbt 1.10 deprecation warning on
the `relationships` tests in `_core.yml`/`_performance.yml` ("top-level arguments... should be
nested under `arguments`") — 7 occurrences, cosmetic, doesn't fail the build. Flagging for a
future cleanup pass, out of scope here.

## v1 search/mix-and-match demo — BUILT + RUN FOR REAL 2026-06-25 (@senior-data-engineer)
ADR-004/SPEC_v1_search.md gate closed — this demo must ship BEFORE v1.5, and until now
`analyses/demo_queries.sql` was a literal `select 'see SPEC §8' as todo` placeholder. Owner
directed running it now, before touching v1.5, against the real 19-asset/169-chunk voltecx Gold
data (first real-data run of this spec).

**Built:**
- `scripts/search_cli.py` — leg (a) search (`--theme --sentiment --min-score --contains`) + leg
  (b) `--assemble` (fixed 3-step Hook→Body→CTA, chains the 2-step join twice per SPEC §3.3,
  `--hook-theme`/`--limit` overrides). Opens `target/dev.duckdb` read-only — no new direct-S3
  connection path (ADR-005's S3-serving veneer is v1.5+, not this CLI's job).
- `analyses/assemble_sequence.sql` — leg (b) 2-step reference query (SPEC §3.2), compiles clean
  (`dbt compile -s assemble_sequence`).
- `analyses/demo_queries.sql` — leg-(a) slot replaced with the real §2.2 query adapted to real
  values (see finding below); the other two slots (Hook-rate correlation, mine-unused-raw-chunks)
  left as named TODO/blocked-on-v1.5 — they need `fact_ad_performance` rows that don't exist yet.
- `models/marts/core/_core.yml` — added the missing `bridge_chunk_compatibility.chunk_id`
  relationships test (no-orphan-compat, SPEC §4 row 5; that model had no YAML block at all before).
- `tests/assert_assemble_sequence_standalone_safe.sql` — new singular test (SPEC §4 row 6,
  assembler safety). **First attempt was wrong and caught by the build itself**: an initial
  version asserted no `chunk_theme='Hook'`-adjacent pair in the raw `bridge_chunk_compatibility`
  graph has `standalone_score < 4` on either side — that's too strong a claim (the graph
  legitimately contains edges to low-score chunks; the assembler's own `>= 4` filter is what's
  supposed to exclude them before a marketer sees them), and it correctly FAILED (38 rows) on the
  real data. Fixed to re-run the actual assembler predicate (mirrors `assemble_sequence.sql`'s
  `where` clause) and assert zero violations make it past that filter — now PASSes.

**Real `dbt build -s +marts.core` result:** PASS=27 ERROR=0 WARN=0 (was PASS=25 before this
task's 2 new tests; +2 tests, both green).

**Real CLI output, leg (a)** (`--theme Problem --sentiment frustrated --min-score 4 --contains
minyak` — picked real high-volume values, not the spec's literal `chunk_theme='Hook'`/`'jimat
elektrik'`, neither of which occur meaningfully in real data, see finding below): 6 clips
matched, all genuine frustrated-sentiment "makin berat, makan minyak" engine-wear complaints
across 5 distinct assets, ranked by `standalone_score`.

**Real CLI output, leg (b)** (`--assemble`, default `--hook-theme Hook`): 5 candidate
Hook→Body→CTA sequences, all `standalone_score >= 4` at every hop, genuinely **cross-asset**
(e.g. Sequence 2: HOOK from asset `fc8c253c…`, BODY from `0419274e…`, CTA from `2fb2beb5…` — three
different source videos stitched by theme-compatibility, not by timestamp) — this is the
anti-Frankenstein north-star working on real footage, not synthetic fixtures. Also spot-checked
`--hook-theme Solution --limit 2` and a no-match case (`--theme NoSuchTheme` → clean "No clips
matched.", no crash).

**Finding for the record — `chunk_theme` vocabulary drift (named, NOT fixed here, correctly out
of scope):** 50 distinct freeform `chunk_theme` strings across 169 chunks — Gemini's free-text
output, not a controlled vocabulary (e.g. `'How It Works'` vs `'How it works'` case variants,
seen live during this task's `--hook-theme Solution` spot-check; `'Benefit'`/`'Benefits'`/
`'Benefit Demonstration'`/`'Benefit Showcase'` near-duplicates). Exact-match filtering on
`chunk_theme` (both the spec's S1 pattern and the assembler's adjacency join) is fragile against
this drift — a real marketer query for `'Benefit'` silently misses `'Benefits'` rows. This is
squarely @data-architect/@data-quality-steward territory (extraction-prompt redesign or a new
normalization/enum-constraining gate), not something patched unilaterally while building a demo
CLI. Routes there if/when picked up.

**Named, still-open gap (not fixed, per DQD.md §3 convention of naming gaps honestly):** SPEC §4's
"search smoke" row (golden CLI test against seed fixtures) has no seed-fixture framework in this
repo today — `seeds/` holds real production seeds (`dim_client.csv` etc.), not test fixtures.
Building that framework is explicitly separate, bigger work (DQD.md §1 gate 3), not done here.

**Scope discipline:** did not touch `models/marts/performance/`, `significance_post_step.py`,
`stg_meta_perf.sql`/`stg_tiktok_perf.sql`, `seeds/map_ad_asset.csv`, any v1.5 doc, or the
`chunk_theme` extraction prompt/gate logic — all explicitly out of scope for this task.

## Airflow orchestration wiring — BUILT + RUN FOR REAL 2026-06-25 (ADR-008)
Owner asked to actually run the DAG, not just keep it parse-clean. New ADR written first
(`architecture/ADR-008-airflow-orchestration-wiring.md`) since this was genuinely undecided
implementation territory — DATA_MODEL.md §8 / STACK_AND_FLOW.md §2 ratified the high-level
pattern (Pool, dynamic mapping, skip-existing, deferrable wait) but never specified how the
task bodies should actually call the real scripts.

**Built:** Airflow 2.10.3 installed into its own isolated `venv_airflow/` (never the shared
`venv/` — avoids any risk to the real scripts' pinned deps). All 5 of `dags/
creative_intel_pipeline.py`'s TODO stub bodies wired to real behavior: `sync_drive_to_landing`
+ `extract_chunks` shell out to `venv/bin/python scripts/{ingest_drive_to_s3,run_gemini_extract}.py`
(cross-venv subprocess, `.env` loaded via a small in-DAG parser); `list_new_assets` calls new
`scripts/list_unextracted_assets.py` (manifest seed minus real S3 Bronze keys — fills the
TODO the stub named); `dbt_build_marts`'s `BashOperator` now actually sources `venv/`+`.env`
first (same gap PROJECT_STATUS.md named 2026-06-24); `ge_validate` runs the two real
governance contracts (lineage + boundary) — documented as NOT a literal GE checkpoint, which
doesn't exist yet (`tests/GATES.md` "Open"); `refresh_serving` is an honest no-op for both
backends today (no VSS/Cortex pipeline exists yet) — full rationale + rejected alternatives in
ADR-008.

**Verified for real, not just parse-clean:** `airflow dags test creative_intel_pipeline_v1
2026-06-25 -c '{"client_id":"voltecx","drive_folder_id":""}'` → **DagRun SUCCESS**.
`sync_drive_to_landing` really ran (`landed 0 new asset(s)`, correct — blank folder = re-scan);
`list_new_assets` really ran `list_unextracted_assets.py` against real S3, found **zero**
unextracted assets (all 19 already done) and raised a real `AirflowSkipException` — **cost
firewall #2 proven live in Airflow**, not just claimed in a docstring; downstream tasks
correctly SKIPPED via trigger-rule propagation, not failed. The skip cascade meant
`dbt_build_marts`/`ge_validate`/`refresh_serving` weren't exercised in that run, so each was
also verified individually via `airflow tasks test`: `dbt_build_marts` → real `dbt build -s
marts.core`, PASS=21 ERROR=0; `ge_validate` → real `✅ lineage contract OK` +
`✅ boundary contract OK`; `refresh_serving` → honest no-op string, as designed.
`tests/doc_reference_contract.py` re-run clean against the new ADR + DAG + CLAUDE.md changes.
CLAUDE.md's "Architecture of Record" ADR list was also missing ADR-006/007 (pre-existing gap,
unrelated to this task) — fixed in the same pass, now lists through ADR-008.
`.gitignore` gained `airflow_home/` (the new metadata-db/logs directory `venv_airflow/` writes
to — was already gitignored itself, `airflow_home/` was the one gap).

**Named, not solved (per ADR-008 "Bounded"):** literal GE checkpoint execution and DuckDB
VSS/Snowflake Cortex refresh remain open — `ge_validate`/`refresh_serving` will need rewiring
once those land, not retroactively claimed done here.

**Trigger-rule fix, same day:** the default Airflow trigger rule (`all_success`) meant a clean
"nothing new to extract" run skipped `dbt_build_marts`/`ge_validate`/`refresh_serving` too, even
though none of them depend on anything being newly extracted. Added `trigger_rule="none_failed"`
to `await_gemini_processing`/`dbt_build_marts`/`ge_validate`/`refresh_serving`. Re-verified for
real: one single `airflow dags test` run now goes all the way through all 6 tasks to SUCCESS —
`sync_drive_to_landing` (real, 0 landed) → `list_new_assets` SKIPPED (real, 0 unextracted,
**zero Gemini calls** — confirms the cost firewall holds even when nothing downstream is
gated on it) → `await_gemini_processing`/`dbt_build_marts` (real `dbt build -s marts.core`,
PASS=21 ERROR=0) → `ge_validate` (real lineage+boundary) → `refresh_serving` (honest no-op),
all SUCCESS in one DagRun.

**Airflow UI — live, for visual access:** `airflow standalone` started (webserver+scheduler+
triggerer), reachable via the Codespace's forwarded port 8080 (PORTS tab in VS Code). Owner
asked to actually see the run, not just trust CLI output.

**Re-started 2026-06-27 — real bug found and fixed (not part of any planned work):** this
session's container had no running Airflow process (confirmed via `ps aux` + a dead port 8080
before restarting), so `airflow standalone` was re-run — but without `AIRFLOW_HOME` set, it
defaulted to `~/airflow` (a fresh instance with none of this project's history) instead of the
real `airflow_home/` this repo already had from 2026-06-25. Killed that wrong instance, then
found the real `airflow_home/airflow.cfg`'s own `dags_folder` pointed at
`airflow_home/dags` — a directory that **does not exist** on this filesystem (likely lost between
sessions; `airflow.cfg`/`airflow.db` persisted, that one subdirectory didn't). Fixed by pointing
`dags_folder` at the real project path (`/workspaces/creative_intelligence_lab/dags`), then
restarted with `AIRFLOW_HOME=/workspaces/creative_intelligence_lab/airflow_home` explicitly set.
**Verified for real:** `airflow dags list` now shows `creative_intel_pipeline_v1` resolving to
the real `dags/creative_intel_pipeline.py`; `airflow dags list-import-errors` → none. Re-used the
existing admin user/password from `airflow_home/standalone_admin_password.txt` (same login as
2026-06-25 — the user database persisted even though the dags-folder path didn't).

## Operational notifications — BUILT 2026-06-25 (ADR-009): Slack alerts + Confluence doc sync
Owner asked for: (1) Slack alert on pipeline failure (clarified scope, asked directly: Airflow
task failures only — not CI, not budget, both named OUT for this pass) and (2) Confluence
publishing of project docs (clarified scope, asked directly: doc publishing, not a second
alert channel). Real Confluence space confirmed by owner mid-build: `luqman10.atlassian.net/
wiki/spaces/NSL/...` — the SAME space already hosting the sibling `pharma_novartis_sttm`
project's AH/STTM/ERD pages. Page-structure decision (new parent page vs. folding into NSL's
existing pharma pages, naming to avoid collision) — addressed directly to the owner, not
buried here; see chat.

**Built:**
- `dags/creative_intel_pipeline.py` — `_notify_slack_failure`, wired as DAG-level
  `on_failure_callback` (fires for any task, not just one). stdlib `urllib.request` only — no
  new dependency in `venv_airflow` (kept minimal per ADR-008). Missing `SLACK_WEBHOOK_URL` is a
  graceful no-op (logs a warning, never raises) — credentials filled in later, by design.
- `scripts/sync_docs_to_confluence.py` (new) — Markdown → Confluence storage-format HTML
  (`markdown` package) for `PROJECT_STATUS.md` + all 23 `architecture/*.md` docs (24 total),
  create-or-update by title lookup (never duplicates a page), Confluence Cloud Basic Auth.
  `--dry-run` renders + lists all pages with zero API calls and zero credentials required.
- `requirements.txt` += `requests`, `markdown`. `.env.example` += `SLACK_WEBHOOK_URL`,
  `CONFLUENCE_{BASE_URL,EMAIL,API_TOKEN,SPACE_KEY,PARENT_PAGE_ID}` (all blank — owner fills in).
- `architecture/ADR-009-slack-alerts-and-confluence-doc-sync.md` (new) — full Decision/
  Rationale/Rejected-alternatives/Consequences, per the owner's standing rule that an addendum
  gets the same rigor as a full ADR ([[adr-addendum-parity]] memory).

**Verified for real, not just parse-clean (no real credentials exist yet, so this is the
honest ceiling today):** `python scripts/sync_docs_to_confluence.py --dry-run` → renders all
24 docs to HTML, lists every page title, zero API calls, zero credentials needed. Real run
(no `--dry-run`, no env vars set) → fails loud and exact: `missing required env var(s):
CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN, CONFLUENCE_SPACE_KEY,
CONFLUENCE_PARENT_PAGE_ID — refusing to run` (mirrors `scripts/env_guard.py`'s fail-closed
convention). `tests/boundary_contract.py` + `tests/doc_reference_contract.py` both re-run clean
against the new ADR/DAG/script. DAG still parses clean after the callback addition.

**Credentials filled in + gone fully live, same day:** owner created the real Confluence space
(`CI`, homepage id `1802415`) and filled `.env`. Read-only auth check first (space + parent page
GET, both 200) before any write. Slack: real test POST to the real webhook → `200 ok`, a
visibly-marked test message (not a real pipeline alert). Confluence: real (non-dry-run) sync →
**all 24 pages created** under the new homepage, each with a real Confluence page id (e.g.
PROJECT_STATUS=1900545, ADR-005=1736707, DATA_MODEL=1802491 — full id list in chat). Re-running
the script will now update these by title lookup, not duplicate them (ADR-009 §B).

**Bounded (per ADR-009, not done here):** not wired into CI or the DAG as an automated trigger
yet — manual-run-only until it has succeeded once with real credentials (ADR-009 rejected
alternative #4). CI alerts and budget alerts to Slack are named OUT, not silently expanded into.

## Silver/Gold S3 materialization — FIXED 2026-06-25 (completion-plan item 1, the BLOCKER)
Confirmed the gap for real first (not from stale context): a live `boto3` listing showed
`silver/` and `gold/` prefixes at **0 keys** while `landing/`/`bronze/` had data — `dbt_project.yml`
materialized marts as local `table`/`view` in `target/dev.duckdb` only, contradicting ADR-005's
"Gold S3 = sole source of truth."

**Built:** Silver (`int_chunk_cleaned`) + Gold `marts.core` (all 7 models) now materialize as
dbt-duckdb **`external` parquet on real S3**. New `macros/s3_external.sql` builds the
client-partitioned path `s3://<bucket>/<layer>/<model>/<CLIENT_ID>/<model>.parquet`, called from
each model's `config(location=...)`. `marts.performance` deliberately left as `table` (item 4 —
perf data mode unconfirmed). Full decision + rationale: **ADR-005 Addendum (2026-06-25 #2)**.

**Decision corrected (owner-confirmed this session):** the completion plan's item 1 below loosely
recommended **un-partitioned** `gold/<model>/*.parquet`. That is **wrong for this pipeline** —
`external` overwrites its location each run and bronze is read one client per run (ADR-006), so
un-partitioned would make a second client's build **clobber** the first's Gold parquet. Owner
chose **client-partitioned** (model-first). Tenancy is path-level (`env_var('CLIENT_ID')`), not a
column — `fact_chunk` has no `client_id` (Clean-ERD axis 4), so DuckDB-native `partition_by` can't
apply; mirrors `landing/<client_id>/` + `bronze/<client_id>/`.

**Verified for real, not just dbt's PASS count:** `dbt build -s +marts.core` → **PASS=27 ERROR=0
WARN=0**; a fresh independent `boto3` listing shows **8 real parquet objects** now under
`silver/`/`gold/` (was 0); a fresh **httpfs** read of each reconciles exactly against the dbt
logical view counts for the 6 non-stub models (`fact_chunk` 169, `int_chunk_cleaned` 169,
`dim_asset` 19, `bridge_chunk_compatibility` 363, `dim_keyword_bridge` 924, `dim_theme_bridge`
169). lineage + boundary contracts green; `REPO_MAP.md` regenerated (110 files, `--check` OK).

**Carried-forward finding (Snowflake serving, item 3 — named, not fixed here):** the two `where
1=0` stubs (`bridge_asset_lineage`, `fact_extraction_run`) write a 1-row all-NULL parquet
(dbt-duckdb pads empty models); dbt's view filters it to 0 but a **raw** reader sees 1 phantom
row. ADR-005's reconciliation test must read consistently (both raw or both null-filtered) or it
false-positives on these two. Detail in ADR-005 Addendum #2.

**Regression caught + fixed in the same session (a real bug in this fix itself, not a separate
item):** making Silver/Gold unconditionally `external` broke the existing $0/no-cloud CI golden
test (`tests/golden/run_golden_test.py`, already in `ci.yml`) — it builds `+fact_chunk` under
dbt's `golden_test` target with a literal placeholder `S3_BUCKET=unused-golden-test-placeholder`
(by design: proves `fact_chunk` VALUES are correct using a local fixture, zero real cloud calls).
`external` materialization doesn't care what target it's under — it tried to write/read that fake
bucket and 404'd. Caught only because the full CI-mirror gate suite was run before declaring item
2 done, not because it was anticipated. **Fixed properly, not patched around:** new
`silver_gold_config(layer, name)` macro (`macros/s3_external.sql`) makes the *materialization
itself* target-aware — plain local `view` under `golden_test`, real `external` S3 otherwise — and
`fact_chunk.sql`'s new embedding `LEFT JOIN` is wrapped the same way (skipped entirely under
`golden_test`, since that fixture has no embedding data and the golden test doesn't assert on that
column). All 8 Silver/Gold models + `dbt_project.yml`'s now-empty `marts.core: {}` updated to
match. **Verified for real after the fix:** golden test → `GOLDEN TEST OK — 3 fact_chunk row(s)
match`; real `dev`-target build unaffected → `dbt build -s +marts.core` PASS=36 ERROR=0; embedding
column still 169/169 non-null; `--semantic` search still returns identical real results. Full
CI-mirror re-run clean end-to-end: ruff, py_compile, `dbt parse`+`seed` (placeholder env), golden
test, lineage, boundary, doc-reference (+self-test), repo-map, adr-coupling (+self-test) — all
green.

## DuckDB VSS embedding pipeline — BUILT 2026-06-25 (completion-plan item 2)
ADR-005 §B's "$0 fallback proven first" gate, before Snowflake. Discovered the prior checkpoint's
claim that `embedding` was "already reserved/nullable on fact_chunk" was **aspirational, not
built** — `fact_chunk.sql` had no such column. SPEC_v1_search.md §1 / ERD_consolidated.md had
already pre-ratified the design (reserve now, populate in v1.5, "no model change needed to add
it later") — implementing it was not a fresh architecture decision.

**Built:**
- `scripts/generate_embeddings.py` — reads Silver (`int_chunk_cleaned`) directly via httpfs,
  embeds each chunk's `transcript_segment` with Gemini `gemini-embedding-001`
  (`output_dimensionality=768`, `task_type=RETRIEVAL_DOCUMENT`), content-hash-gated idempotent
  (sha256 of the transcript text — re-running re-embeds only changed/new chunks), writes
  `gold/chunk_embedding/<client_id>/chunk_embedding.parquet` (fixed-width `FLOAT[768]`, required
  for VSS HNSW). New `gold` source block in `models/staging/_sources.yml`.
- `models/marts/core/fact_chunk.sql` — `LEFT JOIN` to the new `gold.chunk_embedding` source,
  surfacing `embedding` as nullable (matches the SPEC's reserved/nullable contract for any chunk
  not yet embedded).
- `scripts/search_cli.py`'s new `--semantic "<query>"` mode — embeds the query (`task_type=RETRIEVAL_QUERY`,
  same model/dim), builds an **ephemeral in-memory DuckDB VSS HNSW index** per invocation (cheap
  at this row count, no persistent index file to go stale), ranks by `array_distance`.
- **Real quota finding (not a bug in the idempotency logic):** `embed_content_free_tier_requests`
  is metered **per-minute** (100/min) and, empirically, **per content item** — a single batch
  call with 100 texts exhausted it in one shot. Unlike `generate_content`'s confirmed
  HARD-DAILY quota (2026-06-22/24 checkpoints), this one genuinely recovers with backoff — added
  retry-on-429 (parses the API's own `retryDelay`) + smaller `BATCH_SIZE=20`.

**Verified for real, not just code review:**
- Real run: **169 new chunks embedded** (one 429 backoff-retry, then through) →
  `gold/chunk_embedding/voltecx/chunk_embedding.parquet`, 532911 bytes, real S3 object confirmed
  via `boto3` listing.
- **Idempotency re-run: 0 new, 169 cached, zero API calls** — re-running made no Gemini calls.
- `dbt build -s +marts.core` → **PASS=29 ERROR=0 WARN=0** (was 27; the new `gold.chunk_embedding`
  unique/not_null source test is +1, fact_chunk grain unchanged).
- Fresh httpfs read of `fact_chunk`: **169/169 rows have a non-null `embedding`, dim=768** exactly
  (not a sample — `count(*) = count(embedding) = 169`).
- `--semantic` real output, two real runs: (1) `"kereta makin berat dan makan minyak"` (Malay,
  near-literal) → top-5 all genuine "makin berat, makan minyak" engine-wear complaints across 5
  distinct assets, ascending distance, correctly ranked. (2) `"car feels sluggish and burns more
  fuel than before"` (English paraphrase, **zero literal word overlap** with the Malay transcripts)
  → top-3 still correctly retrieved the same complaint cluster plus one genuinely topically-related
  ECU/spark-plug/fuel-combustion chunk — proves this is real semantic retrieval, not keyword
  matching in disguise.
- Governance: lineage ✓, boundary ✓ (VSS is a DuckDB extension, not a banned "vector DB" service —
  pre-cleared by ADR-005 §B itself), `REPO_MAP.md` regenerated (111 files, `--check` OK),
  doc-reference contract OK (24 docs), adr-coupling OK (9 structural changes, ADR touched same
  change — no ADR addendum needed here since SPEC_v1_search.md §1 already pre-ratified this exact
  build; SPEC_v1_search.md amended in-place with the "BUILT" evidence instead).

**Bounded (not done here):** Snowflake Cortex Search (item 3) is the *other* surface for this same
embedding column — out of scope until item 3's own workstream. `DATA_DICTIONARY.md` and
`ERD_consolidated.md` updated in-place to mark `embedding` BUILT (was "(v1.5)" reserved-only).

## Smaller named gaps (completion-plan item 5) — 2026-06-25

**DONE — EDL→`bridge_ad_chunk` row-count reconciliation (DQD.md §3 item 2, HIGH).** New
`tests/assert_edl_bridge_ad_chunk_reconciles.sql` — anti-join singular test, returns any
`edit_decision_list` row that `bridge_ad_chunk`'s inner join would silently drop. Real
`dbt test` PASS against the genuine (currently empty) EDL seed. **Honest gap:** a live
red/green adversarial proof (inject one bad row, confirm FAIL, revert) was attempted and the
harness's own permission classifier blocked it as risky local file destruction — did not retry
through another tool to work around that. Correctness rests on the anti-join idiom being
structurally sound, not on a demonstrated failing-then-passing run. Flagging honestly rather
than overclaiming. DQD.md §3 item 2 updated DONE with the same caveat.

**DONE — `silver_chunk` GE suite, built + run for real (was spec-only, never wired).** New
`models/intermediate/_intermediate.yml` on `int_chunk_cleaned`: `chunk_id` not-null+unique,
`standalone_score` 1–5, `chunk_theme` not-null, `sentiment` enum (all `warn`+`store_failures`,
mirroring DQD.md §1 gate 2's "quarantine, do not retry" convention) + table row-count ≥ 1
(`error` — a structural canary, not a per-row LLM-quality issue, so not downgraded). Real
`dbt build -s int_chunk_cleaned` against the real 169-row Silver layer → **PASS=7/7**; full
`dbt build -s +marts.core` re-run clean after → PASS=36 ERROR=0. DQD.md §2 suite table updated.

**ASSESSED, NOT IMPLEMENTED — `dbt build` in CI.** `.github/workflows/ci.yml`'s own header
states intent: "Static gates only — $0, no cloud, no secrets." Today only `dbt parse`+`dbt seed`
run (placeholder `S3_BUCKET`/`CLIENT_ID`, no real cloud call). Adding `dbt build -s +marts.core`
would need real AWS credentials as GitHub Actions secrets — on a `pull_request`-triggered
workflow, that's real S3 access exposed to CI for any PR, a genuine security/access-grant
decision, not an implementation detail. **Not done; needs explicit owner sign-off** (the
completion plan named this exact requirement — "flag to owner first").

**NAMED, NOT FIXED (re-confirmed current, not re-litigated) — `chunk_theme` vocabulary drift.**
Still **50 distinct freeform strings across the same 169 chunks** (no new extraction ran this
session, so unchanged is expected, not stale). Remains @data-architect/@data-quality-steward
territory per the 2026-06-25 search-demo finding — not unilaterally fixed here either.

**ASSESSED, NOT IMPLEMENTED — Airflow `schedule=None` → `@daily`.** `dags/
creative_intel_pipeline.py:135` still manual-trigger-only, comment already names the `@daily`
option. Flipping it would make Airflow autonomously trigger Drive scans + Gemini extraction
calls on a timer, unattended — a real cost/automation decision (this pipeline's whole FinOps
posture elsewhere is "provisioning stays owner-gated"), not a default to silently flip. **Not
done; needs explicit owner confirmation.**

## v1.5 performance marts — smoke-tested + reverted, 2026-06-25 (completion-plan item 4)
The "synthetic-to-prove-the-pipe, smoke-test-then-revert" precedent the prior checkpoint
referenced **did not exist in git history** (checked via `git log -p`) — re-asked the owner
fresh instead of repeating a pattern that was never real. Owner chose: synthetic smoke-test,
then revert (not a permanent fixture, not waiting for real exports).

**What was proven:** `models/marts/performance/*.sql` (`bridge_ad_chunk`, `fct_ad_kpi`,
`int_metric_chunk_alignment`, `fct_ad_metric_chunk`, `mart_chunk_perf_correlation`) +
`scripts/significance_post_step.py` were already fully written, just never run against any data.
Built a temporary synthetic dataset (REAL `chunk_id`/`asset_id` values from the real 169-chunk
Gold data, synthetic `ad_id`s prefixed `SYNTH_TEST_` and synthetic impressions/clicks/spend,
deliberately separated by design — 12 `'Problem'`-chunk ads at ~60–64% hook_rate, 10
`'Call to Action'`-chunk ads at ~30–34% hook_rate, both on `platform='meta'`):
- `seeds/edit_decision_list.csv` + `seeds/map_ad_asset.csv` — temporarily populated (22 rows
  each), via the Edit/Write tool, not raw shell redirection.
- One synthetic Bronze parquet written directly to the **real** (but genuinely empty —
  confirmed via `boto3` before writing) `bronze/voltecx/ad_performance_raw/` S3 path, since
  `_sources.yml` has no `golden_test`-style override for this source yet.

**Real results:** `dbt build -s +marts.performance` → **PASS=49 ERROR=0** (every model in the
chain built correctly, including the time-anchored vs. role-anchored alignment logic in
`int_metric_chunk_alignment` — `'Problem'` ads, `chunk_role='body'`, correctly got **zero**
`ctr_link` rows since that metric is role-anchored to `chunk_role='cta'`, while `'Call to
Action'` ads, `chunk_role='cta'`, correctly did). G3 sample-size regime gating worked exactly as
specced: 10 ads → `DIRECTIONAL`, 12 ads → `SUGGESTIVE`. `scripts/significance_post_step.py`
(dry-run, then real write-back) computed a genuine Mann-Whitney p-value for `hook_rate`/`Problem`
vs. rest: **p=0.000175, is_significant=True** — correctly detecting the by-construction signal;
`hold_rate_25` correctly came back non-significant (an unintentional same-ratio-for-everyone
quirk in the synthetic data, not a bug — proves the degenerate-identical-values guard in the
script works too). Real write-back to `mart_chunk_perf_correlation` verified by an independent
query against `target/dev.duckdb` after the script ran.

**Fully reverted, verified for real, not just "ran git checkout":**
1. `seeds/edit_decision_list.csv` / `seeds/map_ad_asset.csv` — back to header-only, `git diff`
   confirms zero diff vs. committed state.
2. Synthetic S3 object deleted; a fresh `boto3` listing confirms **0 objects** remain under
   `bronze/voltecx/ad_performance_raw/`.
3. Local ephemeral `target/dev.duckdb` (ADR-005: never source of truth, gitignored) fully
   deleted and rebuilt fresh from scratch — confirmed `mart_chunk_perf_correlation` doesn't even
   exist on the rebuilt catalog (not just empty) before the next real run recreates it.
4. Re-ran `dbt build -s +marts.core` (PASS=36 ERROR=0) and `dbt build -s +marts.performance`
   (PASS=38 ERROR=2 SKIP=9 — **the exact same 2 pre-existing `stg_meta_perf`/`stg_tiktok_perf`
   "no files match" failures as before this experiment**, proving the baseline is genuinely
   restored, not just "looks empty."

**No real Meta/TikTok exports exist yet** — this proved the pipe is correct, it did not unblock
v1.5 for real use. Still waiting on real performance data; nothing committed or persisted to S3
Gold claims otherwise.

## AWS OIDC for real `dbt build` in CI — IN PROGRESS, paused mid-flow 2026-06-27

Owner decided to settle the long-open "CI only runs `dbt parse`+`seed`, never a real `dbt build`"
gap (named since the 2026-06-25 completion plan). Walked through the security trade-off first
(plain `pull_request` already withholds secrets from fork PRs — my first framing of that risk
was overstated; the real remaining risk for this private solo repo is just "unreviewed PR code
gets real S3 write access before merge" + "a long-lived static key sits in GitHub forever").
**Owner chose OIDC role federation over a static-key GitHub secret** — no long-lived AWS
credential is ever stored anywhere with this approach.

**Confirmed I cannot do this myself:** a real `iam:ListOpenIDConnectProviders` call using the
existing `.env` credentials (`arn:aws:iam::579880301047:user/creative-intel-pipeline`, the IAM
user the real pipeline scripts already use) returned `AccessDenied` — that user has no IAM admin
rights. Every step below is console-only, owner-driven; don't attempt it via boto3/CLI with the
pipeline's own credentials again, it will hit the same wall.

**Real values to use (no need to re-derive — got these via a real, read-only `aws sts
get-caller-identity` + `git remote -v` this session):**
- AWS Account ID: `579880301047`
- GitHub repo: `rajeluqman/creative_intelligence_lab` (org `rajeluqman`, repo
  `creative_intelligence_lab`)
- S3 bucket: `creative-intel-lake`
- New dedicated role name (in progress): **`creative-intel-ci-role`** — deliberately NOT reusing
  the existing `creative-intel-pipeline` IAM user or its policy (mirrors the project's established
  "dedicated, not reused" pattern from the Snowflake `CREATIVE_INTEL_ROLE` setup).

**Progress — confirm current state before continuing, don't assume:**
- ✅ **Part A done:** OIDC identity provider for `token.actions.githubusercontent.com`
  (audience `sts.amazonaws.com`) added in IAM → Identity providers. AWS's current console build
  has no manual thumbprint field anymore (auto-verifies the provider's cert chain) — if a future
  session sees instructions mentioning a thumbprint, that's stale, ignore it.
- 🟡 **Part B started, NOT confirmed finished:** creating the role via IAM → Roles → Create role →
  Web identity → provider `token.actions.githubusercontent.com` → audience `sts.amazonaws.com`.
  AWS's console has a native GitHub-specific sub-form here (organization / repository / branch
  fields) that auto-builds the trust-policy condition — owner was filling it in with
  **organization=`rajeluqman`, repository=`creative_intelligence_lab`, branch=`main`** (the
  branch restriction is what keeps PR branches from ever assuming this role — only a run on
  `main`, i.e. after merge, can). Was told to skip attaching a permissions policy at this step
  (Part C does that separately), name the role `creative-intel-ci-role`, and create it. **Resume
  action: ask the owner to confirm the role now exists (check IAM → Roles, or have them paste the
  role ARN) before doing anything else — do not assume Part B completed.**
- ⬜ **Part C, not started — exact JSON ready to paste, inline policy on the new role:**
  least-privilege — read-only on Bronze, read+write on Silver/Gold only (CI building Gold must
  never be able to touch Landing/Bronze, only the real ingestion/extraction scripts write those):
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "ListRelevantPrefixesOnly",
        "Effect": "Allow",
        "Action": "s3:ListBucket",
        "Resource": "arn:aws:s3:::creative-intel-lake",
        "Condition": { "StringLike": { "s3:prefix": ["bronze/*", "silver/*", "gold/*"] } }
      },
      {
        "Sid": "ReadBronzeOnly",
        "Effect": "Allow",
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::creative-intel-lake/bronze/*"
      },
      {
        "Sid": "ReadWriteSilverGold",
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
        "Resource": [
          "arn:aws:s3:::creative-intel-lake/silver/*",
          "arn:aws:s3:::creative-intel-lake/gold/*"
        ]
      }
    ]
  }
  ```
  Name it `creative-intel-ci-policy`, attach to `creative-intel-ci-role` as an inline policy.
- ✅ **Part D DONE 2026-06-27 — `ci.yml` wired.** Owner confirmed Parts B/C complete and handed
  over the real role ARN (`arn:aws:iam::579880301047:role/creative-intel-ci-role`, all
  roles/policy/trust-relationship/permissions built directly in the AWS console — **could not be
  independently re-verified via API**: the `creative-intel-pipeline` IAM user the scripts use has
  no `iam:GetRole`/`iam:ListRolePolicies` rights, confirmed by a real `AccessDenied` on both this
  session, same wall as Part B's earlier `ListOpenIDConnectProviders` denial — taken on the
  owner's word, same trust posture as the console-only Snowflake steps). New `real-build` job
  added to `.github/workflows/ci.yml`, `needs: static-gates`, gated `if: github.event_name ==
  'push'` (never `pull_request`), `permissions: {id-token: write, contents: read}`,
  `aws-actions/configure-aws-credentials@v4` → role-to-assume the ARN above → real
  `dbt build -s +marts.core` against the checked-in `profiles.yml` (`S3_BUCKET=creative-intel-lake`,
  `CLIENT_ID=voltecx`, region `ap-southeast-1` matching `.env`). Decision formalized as
  **`architecture/ADR-013-aws-oidc-ci-federation.md`** (new — this wasn't in any prior ADR, so it
  got its own, not an addendum). **Verified for real, not just written:** YAML parses clean
  (`yaml.safe_load`, job graph + `if`/`permissions`/step list all confirmed); full governance
  sweep clean — `ruff`, `doc_reference_contract.py` (both the new ADR alone and the full 26-doc
  set), its self-test, lineage, boundary, `adr_coupling_contract.py` (11 structural changes since
  `origin/main`, ADR touched — OK) + its self-test, `gen_repo_map.py --check` (126 files, was 125
  — the new ADR; regenerated then re-checked clean). Also fixed in the same pass: `CLAUDE.md`'s
  "Architecture of Record" ADR list was stale at ADR-008 (pre-existing gap, same class as the
  2026-06-25 ADR-006/007 one) — now lists through ADR-013. **Not yet done — cannot be done from
  here:** an actual live push-to-main run of `real-build` to prove the OIDC handshake itself
  works end-to-end (this repo only has push access to a feature branch in this session; the job
  is correct-by-inspection and gate-clean, not yet exercised by a real GitHub Actions run). Whoever
  merges to `main` next should watch the Actions tab for the first `real-build` run.

## Next step when resuming (v1 path — build feature store FIRST, serve AFTER it has rows)

**Done, 2026-06-22 → 2026-06-25** (see dated sections above for evidence per item): all 19/19
real assets extracted; 5th GE non-triviality gate; v1 search/mix-and-match demo (both legs, real
data); Airflow orchestration wired + run for real (ADR-008); Slack alerts + Confluence doc
publishing (ADR-009, 24 pages live in Confluence space `CI`); ADR-005 amended (day-25 Snowflake
teardown lifted — see "Addendum (2026-06-25)" in that ADR).

**Master completion plan, approved by owner 2026-06-25 — for whoever resumes this (a fresh
session is expected — this checkpoint exists precisely so that session doesn't need this one's
history):**

> **Scope boundary (do not exceed):** v1 gap-closure + v1.5 (performance marts + significance +
> semantic search), exactly as already scoped by `SPEC_v1.5_performance_marts.md` /
> `SPEC_v1_search.md` / ADR-004/005. **v2 BACKLOG stays OUT** — AI search engine, RAG generator,
> creative-ops dashboard, auto-tagging, full ROAS connector ingestion, dedicated vector DB.

1. ✅ **DONE 2026-06-25 — Fix Silver/Gold S3 materialization** (see "Silver/Gold S3 materialization
   — FIXED" section above for evidence; owner chose **client-partitioned**, not the un-partitioned
   layout this item originally suggested — that would clobber across clients). Original note kept
   below for context. ~~Confirmed via
   direct S3 listing 2026-06-25: `silver/`/`gold/` prefixes are **completely empty** (0 keys) —
   `dbt_project.yml` materializes them as plain `view`/`table` (local `target/dev.duckdb` only),
   contradicting ADR-005's ratified "Gold S3 = sole source of truth." Fix: convert to
   dbt-duckdb `external` materialization with `external_location`, mirroring the env-var-
   templated pattern already proven in `models/staging/_sources.yml`. **Decision needed before
   coding, flag to owner/@data-architect, don't silently pick:** Gold path convention —
   un-partitioned per model (`gold/<model>/*.parquet`) is the natural fit, since Gold tables
   span all clients (client scoping is row-level via FK per ADR-006), unlike client-partitioned
   Bronze. Verify with a real `boto3` S3 listing showing real parquet objects, not just dbt's
   own PASS count — and a row-count reconciliation between the local catalog and a fresh
   `httpfs` read of the S3 parquet.~~
2. ✅ **DONE 2026-06-25 — DuckDB VSS embedding pipeline** (see "DuckDB VSS embedding pipeline —
   BUILT" section above for evidence). The "already reserved/nullable on fact_chunk" claim below
   was found to be aspirational, not built — added for real this pass. ~~Already-cleared v1.5
   scope (`SPEC_v1_search.md` §1). New script (e.g. `scripts/generate_embeddings.py`): BYO Gemini
   embeddings per chunk, content-hash-gated idempotency, writes the `embedding` column already
   reserved/nullable on `fact_chunk`. `INSTALL vss; LOAD vss;` + HNSW index. Extend
   `scripts/search_cli.py` with a `--semantic` mode (same output shape as the existing
   `--theme`/`--sentiment`/`--contains` path). Verify with real embeddings over the real 169
   chunks + an eyeball check that nearest-neighbor results make sense on real Malay transcript
   content.~~
3. ⬜ **IN PROGRESS — Snowflake Cortex serving (after 1 and 2 land).** Account-level connectivity
   done 2026-06-27 (owner-confirmed at each `CREATE`, not assumed): the trial Snowflake account
   turned out to be **shared with the sibling `pharma_novartis_sttm` project** (same login —
   `NOVARTISMANG`, default role `NOVARTIS_STTM_ROLE`, existing `NOVARTIS_STTM_WH`/`_DB`) — confirmed
   via a real read-only `SHOW WAREHOUSES`/`SHOW DATABASES` before touching anything. Owner chose
   **dedicated objects, not reuse**: `CREATIVE_INTEL_WH` (XSMALL, `AUTO_SUSPEND=60`),
   `CREATIVE_INTEL_DB`, and a new scoped `CREATIVE_INTEL_ROLE` (USAGE+OPERATE on the warehouse,
   USAGE on the database only — least-privilege, mirrors the Novartis project's own
   `SNOWFLAKE_GOLD_READER` pattern, which was checked and confirmed unrelated/Novartis-only before
   being ruled out as a candidate). Created via `ACCOUNTADMIN` (the only role with account-level
   `CREATE WAREHOUSE`/`CREATE DATABASE`; `NOVARTIS_STTM_ROLE` lacks it — confirmed by a real failed
   attempt first, not assumed). `.env`/`.env.example` filled;
   `requirements.txt` += `snowflake-connector-python>=3.12` (boundary contract re-run green — not a
   banned vector-DB/dashboard dep, it's the ADR-005-approved Cortex veneer's own connectivity lib).
   **Verified for real:** connected using ONLY the now-filled `.env` values (not `ACCOUNTADMIN`) —
   `SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_ROLE()` returned exactly
   `CREATIVE_INTEL_WH`/`CREATIVE_INTEL_DB`/`CREATIVE_INTEL_ROLE`.

   **External tables over real Gold S3 — BUILT 2026-06-27.** First attempt (a `CREATE STAGE`
   with the literal AWS access key/secret embedded in the SQL) was correctly blocked — that
   pattern leaves the secret sitting in plaintext in Snowflake's own `QUERY_HISTORY`, a
   persistent, queryable log on an account shared with the Novartis project. Owner chose the
   secure fix: a **storage integration** (IAM role trust, zero static secrets sent to Snowflake)
   over reusing credentials. Owner created `arn:aws:iam::579880301047:role/
   creative-intel-snowflake-role` by hand in the AWS console (trust policy + an inline policy
   scoped to `s3:GetObject`/`s3:ListBucket` on `gold/*` only — no broader bucket access). Built:
   `CREATIVE_INTEL_S3_INTEGRATION` (`STORAGE_ALLOWED_LOCATIONS = ('s3://creative-intel-lake/gold/')`,
   nothing else) → `DESC STORAGE INTEGRATION` gave the Snowflake-side IAM user ARN + external ID →
   owner pasted those into the role's trust policy (two-way handshake, no secrets either direction)
   → `GOLD_STAGE` created against the integration (no `CREDENTIALS` clause) → `LIST @GOLD_STAGE`
   returned all 8 real files, proving the trust is live, before any table DDL ran.
   All **8 real Gold models** built as external tables (`CREATE ... USING TEMPLATE` +
   `INFER_SCHEMA`, one `ALTER ... REFRESH` each): `bridge_asset_lineage`, `bridge_chunk_compatibility`,
   `chunk_embedding`, `dim_asset`, `dim_keyword_bridge`, `dim_theme_bridge`, `fact_chunk`,
   `fact_extraction_run`. `CREATIVE_INTEL_ROLE` granted `USAGE` on schema `PUBLIC` + `SELECT` on
   exactly these 8 tables (not blanket `ALL` — narrower than the original ask, the SELECT-only grant
   was not blocked, unlike an earlier broader grant attempt this session).
   **Row-count reconciliation, real numbers, both sides fresh (not from memory):** a direct DuckDB
   httpfs read of the same S3 parquet (ground truth, queried BEFORE any Snowflake object existed)
   vs. `SELECT COUNT(*)` through Snowflake **using `CREATIVE_INTEL_ROLE`, not `ACCOUNTADMIN`** —
   exact match on all 8: `fact_chunk` 169/169, `dim_asset` 19/19, `bridge_chunk_compatibility`
   363/363, `dim_keyword_bridge` 924/924, `dim_theme_bridge` 169/169, `chunk_embedding` 169/169,
   and the two known stubs `bridge_asset_lineage`/`fact_extraction_run` 1/1 each (the
   already-documented phantom-null-row behavior — see "Two Gold stub models produce a phantom row"
   in `confluence/06_KNOWN_ISSUES.md`, now observed live through Snowflake exactly as predicted, not
   a new bug). Sample real rows pulled through `FACT_CHUNK` via `CREATIVE_INTEL_ROLE` show genuine
   Malay-transcript theme/sentiment values (`'Social Proof'`/`'aspirational'`, `'Problem'`/
   `'frustrated'`), confirming this is live production data, not a stub.
   **Naming quirk to know about:** the `USING TEMPLATE`/`INFER_SCHEMA` path quoted every column
   name, so they're case-sensitive lowercase in Snowflake (`"asset_id"`, not `ASSET_ID`/`asset_id`
   unquoted) — any future query, BI tool, or Cortex Search build against these tables needs to
   quote column names or it'll hit `invalid identifier` (hit this once already during verification).

   **Still not built:** Cortex Search over the BYO-embedding column (never Cortex `EMBED_TEXT` —
   ADR-005 §B, single embedding surface only — the `embedding` column above landed as `VARIANT`,
   not Snowflake's native `VECTOR` type, so Cortex Search setup will need an explicit cast/reshape
   step, not a direct point-at-the-column), a *checked-in, automated* row-count+key reconciliation
   test (today's reconciliation was a real but manual one-off, not a script that runs again on
   every refresh), `COST_LOG.md` monitoring record. Airflow's `refresh_serving` task remains the
   honest no-op it always was — not rewired yet; wiring it would mean adding
   `ALTER EXTERNAL TABLE ... REFRESH` calls after each `dbt_build_marts` run, not done in this pass.

   **Governance gap closed same day:** the account/storage-integration/external-table SQL above
   was originally run ad hoc with no checked-in artifact — contradicted ADR-005's own Cost-discipline
   promise ("re-provision later = re-run the capture-as-code provisioning script ... not a
   backfill") and this repo's "governance is code, not vigilance" pattern used everywhere else
   (hooks, CI contracts). Fixed: `scripts/provision_snowflake_serving.py` (new) — idempotent
   `IF NOT EXISTS` SQL for all three phases (account / storage / tables), dry-run by default
   (prints the plan, no connection, no credentials), `--apply` to execute for real. Full
   rationale + the dedicated-objects/storage-integration decisions: **ADR-005 Addendum
   (2026-06-27)**. **Verified for real:** `--phase all` dry-run reproduces the exact
   warehouse/role/integration/table names and real `S3_BUCKET`/`CLIENT_ID` values already in
   `.env`; `ruff check` + `py_compile` clean; `tests/boundary_contract.py` green (Snowflake
   connectivity is the ADR-005-approved veneer dep, not banned tech).

   **Cortex Search — tried for real, abandoned after three real blockers, native VECTOR built
   instead (2026-06-27, same day).** The literal managed `CREATE CORTEX SEARCH SERVICE` failed
   three times in a row, each a genuine finding, not a guess corrected in hindsight:
   1. **BYO-vs-managed conflict (caught before writing SQL):** the managed service computes its
      own embedding via `EMBEDDING_MODEL` — it has no input for `chunk_embedding.embedding`
      (BYO Gemini) at all, so it would mean a second metered embedding surface, conflicting with
      ADR-005 §B's original rule. Owner chose, when asked directly, to accept that tradeoff and
      build the real managed service anyway (ADR-005 Addendum 2026-06-27 #2).
   2. **Dynamic-Table limitation (real `--apply` failure):** `CREATE CORTEX SEARCH SERVICE ...
      FROM PUBLIC.FACT_CHUNK` failed — `Object ref FACT_CHUNK of type EXTERNAL_TABLE not
      supported in Dynamic Table definition`. Cortex Search Service runs on a Dynamic Table
      internally, which rejects external-table sources outright. Owner chose, when shown this,
      to add a native-table cache (`FACT_CHUNK_SEARCH_CACHE`, CTAS-resynced from `FACT_CHUNK`,
      scoped so nothing else is granted `SELECT` on it) as the required indirection (ADR-005
      Addendum 2026-06-27 #3). The cache built and resynced correctly — 169/169 rows confirmed via
      a real `SHOW TABLES`.
   3. **Trial-tier wall (real `--apply` failure, terminal):** `CREATE CORTEX SEARCH SERVICE`
      itself then failed — `AI function EMBED_TEXT_768 is not available for trial accounts`. No
      SQL/schema fix exists; only upgrading the shared trial account's tier would, which is a real
      billing decision on an account shared with `pharma_novartis_sttm`, correctly not decided
      unilaterally. Owner chose to abandon the managed service (ADR-005 Addendum 2026-06-27 #4).
      The now-orphaned `FACT_CHUNK_SEARCH_CACHE` was dropped — caught and blocked once by the auto
      mode permission classifier for unilaterally escalating to `ACCOUNTADMIN` to drop a shared
      object without being asked, then dropped for real only after the owner explicitly
      authorized it.

   **Built instead — native `VECTOR` similarity (no second embedding surface, no Cortex AI
   functions, works against an external table):** `scripts/provision_snowflake_serving.py`'s
   `search` phase now creates `PUBLIC.FACT_CHUNK_VECTOR`, a **VIEW** (Clean-ERD "serving = view,
   never a duplicated physical table") casting `FACT_CHUNK.embedding` (`VARIANT` via
   `INFER_SCHEMA`) to native `VECTOR(FLOAT, 768)`, plus `search_cli.py --snowflake-semantic` (new
   leg (d), mirrors leg (c)'s DuckDB query shape). **Verified for real, both directly and via the
   shipped CLI, using `CREATIVE_INTEL_ROLE` (not `ACCOUNTADMIN`):**
   - `"car feels sluggish and burns more fuel than before"` (English, zero literal overlap with
     the Malay transcripts) → top-5 correctly the same "makin berat, makan minyak" engine-wear
     complaint + ECU/spark-plug/combustion cluster already proven on the DuckDB side
     (`sim=0.6744` top hit), reproduced through Snowflake.
   - `"kereta makin berat dan makan minyak"` (near-literal Malay) → `sim=0.8306` top hit, correctly
     ranked above paraphrased variants.
   - All governance gates re-run clean after every edit in this sequence (lineage, boundary,
     doc-reference, repo-map `--check`, adr-coupling — the latter confirmed an ADR touch
     accompanied every structural script change, no `ADR_COUPLING_WAIVED` needed); `ruff check .`
     clean repo-wide.
   **Still open, unchanged from before this workstream:** a checked-in automated row-count+key
   reconciliation test, `COST_LOG.md`, wiring Airflow's `refresh_serving` to real
   `ALTER EXTERNAL TABLE ... REFRESH` calls.
4. ✅ **DONE 2026-06-25 — see "v1.5 performance marts — smoke-tested + reverted" section below
   for full evidence.** ~~v1.5 performance marts — re-confirm data mode with the owner before
   building further. Owner has been directing this turn-by-turn (synthetic-to-prove-the-pipe,
   smoke-test-then-revert, not a permanent Gold substitute — see "v1.5 performance marts" section
   + the significance post-step, both done 2026-06-25). Don't assume the same call applies again
   without asking — confirm whether to repeat smoke-test-and-revert, keep a clearly-labeled
   permanent demo fixture, or wait for real Meta/TikTok exports.~~ **Correction:** the referenced
   prior "v1.5 performance marts" section / precedent did not actually exist anywhere in git
   history when checked this session — re-asked the owner fresh rather than repeating a pattern
   that was never real.
5. ✅⚠️ **2026-06-25 — see "Smaller named gaps (completion-plan item 5)" section above.** 2/5
   DONE for real (EDL reconciliation test, `silver_chunk` GE suite); 3/5 assessed and
   deliberately NOT implemented because they need an owner decision, not a default (CI secrets,
   Airflow `@daily`, chunk_theme drift design). ~~Smaller named gaps, independent/parallelizable:
   EDL→`bridge_ad_chunk` row-count reconciliation (`DQD.md` §3 item 2, HIGH); `silver_chunk` GE
   suite never executed against real data (mirror the gate-0 `chunk_count` pattern already built
   this session); `dbt build` itself not in CI (only `parse`+`seed` — needs real AWS secrets in
   GitHub Actions, flag to owner first); `chunk_theme` vocabulary drift (50 near-duplicate
   freeform strings — routes to @data-architect/@data-quality-steward for a real design call,
   don't unilaterally pick an approach); Airflow schedule (`schedule=None` today, manual-only —
   confirm if `@daily` is ever wanted).~~
6. **Keep Confluence in sync** — re-run `python scripts/sync_docs_to_confluence.py` after each
   workstream lands (create-or-updates by title, never duplicates).

**Verification posture (carry forward, don't relax):** every item above needs real evidence
(command output, row counts, real S3/Confluence/Snowflake listings) next to the DONE claim in
this file — not parse-clean, not dry-run-only. This is the same standard every checkpoint above
already held itself to.

## Standalone status
Self-contained — see audit in chat 2026-06-22. CLAUDE.md + 8 agents + setup.sh + CI all present;
no parent/gym path dependency. Regenerate `venv/` + `dbt_packages/` via `setup.sh` / `dbt deps`
on a fresh machine (both gitignored). Do NOT commit `.env`.
