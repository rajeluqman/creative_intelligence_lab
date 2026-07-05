# Sonnet Build Kickoff — banking-multisource-lakehouse

> Paste-able kickoff for the executing Sonnet session. Opus has finished architecture/design/
> planning — do NOT re-litigate decisions; they live in `01_OPUS_DECISIONS.md` (D-01…D-12).
> If a real conflict appears mid-build, STOP and surface it (ADR-000 feature-intake protocol),
> don't silently improvise. Work fasa by fasa; run the gates at every checkpoint; keep
> PROJECT_STATUS.md's "▶ RESUME HERE" current.

## Context to load (in order, nothing else first)
1. `architecture/banking_lakehouse_lab/00_MASTER_SPEC.md` — what & why + architecture
2. `01_OPUS_DECISIONS.md` — locked rulings
3. `03_DATASET_RISKS_AND_RESOLUTIONS.md` — R-01…R-30 (your DQ/edge-case checklist)
4. `04_BUSINESS_QUESTIONS.md` — BQ-01…BQ-10 (the ENTIRE Gold scope)
5. `framework_template/00_START_HERE.md` — kit adoption steps

## Pre-flight (blockers to confirm with owner)
- [ ] D-01 stack ratified (default: local-first, Delta on S3 prefix — see decision)
- [ ] New GitHub repo created + PAT available for push (D-11 — GITHUB_TOKEN won't work)
- [ ] S3 prefix confirmed (`s3://<bucket>/banking/`) or local-disk fallback accepted
- [ ] Kaggle files on hand: home-credit + paysim (from retrofit repos) + Berka download

## Build order

### Fasa 0 — repo bootstrap (kit adoption)
1. Init repo, copy `framework_template/` in per its `00_START_HERE.md` steps 1–8.
2. Fill `gates/framework.yml` FIRST (paths, banned tech from the REJECTED list, identity =
   `customer_id` via xwalk).
3. `CLAUDE.md` from template — stop-gate + anti-shortcut sections, English default.
4. Agents per D-09 (7 roles; copy cikgu pattern from CIL).
5. Journey docs: 01 + 02 filled directly from lab docs `03_…RISKS…` and `04_BUSINESS_QUESTIONS`;
   03–09 drafted per the mapping table in `00_MASTER_SPEC.md` (full set — N/A needs a reason).
6. CI from `gates/ci.yml.template`. **Gate:** all four bootstrap gates green.

### Fasa A — sources + seeding
1. `docker-compose.yml`: postgres + mssql2022 (+ named volumes); `sap_drop/` folder.
2. `seed/`: loaders implementing D-03 exactly (PK+timestamps, global date-rebase,
   paysim step→ts, deterministic seed, currency codes) + `build_xwalk.py` (D-04).
3. `drip_feed.py` — interval INSERT/UPDATE + soft deletes (D-06).
4. **Gate:** row-count manifest per table (seeded vs source file), xwalk covers 100% of
   customers in all 4 systems, rebuild-from-scratch produces identical counts.

### Fasa B — ingestion → Landing → Bronze (4-layer, D-15)
1. Extract into **LANDING** (transient, as-arrived): watermark extractors for Postgres/MSSQL
   (overlap window R-26; watermark state in the lake, not code); file-drop pickup; OBP client
   (token refresh, backoff, pagination-to-exhaustion, verbatim JSON, R-18…R-22).
2. **Landing→Bronze PROMOTION GATE = transport integrity ONLY** (D-15): `_SUCCESS` present +
   manifest/checksum match + pagination reconciled vs API totals + dedup redeliveries +
   multi-file set complete → promote to **BRONZE** (permanent raw archive); else **quarantine**
   in Landing, alert, Bronze untouched, pipeline continues on last-good Bronze. NO business
   cleansing here — Bronze stays raw.
3. **Gate:** (a) kill-and-rerun any extractor mid-run → no dupes, no gaps; (b) feed a partial/
   truncated/duplicate arrival → it lands, fails promotion, is quarantined, and Bronze is
   provably unchanged (the D-15 isolation proof).

### Fasa C — Silver (Bronze→Silver = CONTENT quality, D-15)
MERGE upserts (latest per PK), birth_number decode (R-12, unit-tested), OBP JSON flatten,
PII masking (D-07), quarantine tables for R-03 orphans. **Gate:** DQ suite per the R-register.
(Content quality lives HERE, never at the Landing→Bronze gate.)

### Fasa D — Gold + evidence
Dims/facts/marts = exactly the BQ table, nothing more. `mart_pipeline_health` (BQ-10) is
mandatory, not garnish. **Gate:** one runnable query per BQ with output captured in
`journey/08` — that IS the definition of done.

### Fasa E — Snowflake serving veneer (OPTIONAL, after Gold — D-01 Addendum #2)
ONLY after Fasa D Gold exists: Snowflake **external tables** over the Gold S3 prefix
(read-only IAM key scoped to `banking/` — never CIL admin creds) + one Power BI page
(BQ-01 + BQ-02). Reuse the CIL ADR-005 pattern wholesale — Snowflake is a read-only window,
the lake stays sole truth. Timing: check whether the CIL Snowflake account is still alive
BEFORE spending anything; if dead, either time a fresh trial to start when Gold is ready, or
fall back to **DuckDB ($0, also CIL-proven)**. Evidence (queries + screenshots) → `journey/08`.
Fabric is OUT of this project entirely (owner ruling — not on the resume; the Fabric trial
serves the separate home-credit-fabric-migration project instead).

## Stack (RATIFIED — D-01 Addendum #3)
Layers = **Landing → Bronze → Silver → Gold** (4-layer medallion, D-15).
Compute = **Databricks** for ALL transform (Landing→Bronze→Silver→Gold), portable PySpark + Delta,
**Unity Catalog** over S3 external locations. Storage = **S3** (`s3://<bucket>/banking/`), sole
truth, reuse CIL bucket. Serving = **Snowflake** external tables over Gold + Power BI (Fasa E).
Dev on local Spark / subset (free); canonical full runs on the **disposable Databricks trial**
(run a few times, screenshot success + UC lineage into journey/08, drill/troubleshoot, delete).
Portable code = mandatory so the repo still runs locally for defense after the workspace is gone.

## Do-NOTs
- No Fabric — out of scope entirely (D-01 Addendum #2). No Terraform (D-13).
- No Databricks-locked constructs on the critical path (DLT / notebook-only magic / heavy
  `dbutils`) — keep transforms portable PySpark so they survive trial deletion (D-01 Add #3).
- No streaming/Kafka, no ML training, no dashboards beyond the Fasa E page, no new marts beyond BQ-01…10
  (scope-guardian has the veto; ADR-000 for any intake).
- No editing gate `.py` scripts to fit the repo — values go in `framework.yml`.
- Bronze is never transformed, masked, or "cleaned". Silver does that.
- Don't trust these docs blindly against reality: if a dataset column named here doesn't
  exist on disk, surface it — the R-register is a map, the file is the territory.
