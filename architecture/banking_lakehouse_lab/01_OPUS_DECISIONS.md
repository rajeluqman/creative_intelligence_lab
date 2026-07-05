# Opus Decisions — Banking Multi-Source Lakehouse (Fasa-0 rulings)

> Reads with `00_MASTER_SPEC.md`. Same contract as the retrofit/control-plane decision docs:
> these are locked unless the owner overrides. Date: 2026-07-05. Branch (planning only):
> `framework/pipeline-retrofit-plan` in CIL.
> **STACK RATIFIED 2026-07-05 — see D-01 Addendum #3 (the current, binding stack ruling);
> the local-first D-01 body + Addenda #1/#2 below are superseded history, kept for the
> justification trail.**

## D-01 — Stack: local-first lakehouse ⚠️ OWNER RATIFY
**Recommendation (default if no objection):**
- Sources: Docker Compose — `postgres:latest` + `mcr.microsoft.com/mssql/server:2022`
  (Developer edition, free, no expiry) + a plain folder as the SAP-sim SFTP drop.
- Transform engine: **PySpark local mode** (needed for Delta `MERGE`), **DuckDB** for
  validation/ad-hoc queries.
- Lake storage: **Delta on S3** under a new prefix `s3://<bucket>/banking/` (reuse the owner's
  existing bucket — $0 new infra). Local-disk fallback if S3 creds absent, same layout.
- **Microsoft Fabric/OneLake: NOT during build.** The Gemini convo assumed Fabric; CIL already
  paid the trial-tier lesson once (Snowflake Cortex wall, CIL ADR-005 Addenda #2–#4). A 60-day
  Fabric trial expiring mid-build is the same trap. Fabric may return LATER as a serving-veneer
  decision (own ADR in the new repo), exactly how CIL admitted Snowflake — read-only, never
  source of truth.
- Why ratify: the only argument FOR Fabric is CV keyword value. Owner call, not a technical one.

## D-01 Addendum (2026-07-05) — owner already holds an ACTIVE Fabric trial
Fact surfaced after the original ruling: trial capacity active since 2026-07-02 (East Asia,
~57 days left → expires ~2026-08-31). Ruling stands at the foundation, amended at the top:
- **S3 remains the lake and sole source of truth** — the build stays trial-proof. If the trial
  vanished tomorrow, every gate still runs green locally. Nothing upstream of serving may
  touch Fabric. (Same shape as CIL ADR-005: Snowflake admitted as read-only veneer only.)
- **The trial is admitted as a timeboxed serving veneer** — new OPTIONAL Fasa E in the kickoff:
  1. OneLake **S3 shortcut** → the Gold prefix (needs a read-only IAM key scoped to
     `banking/` only — NEVER the CIL admin credentials).
  2. One **Direct Lake Power BI page** over the shortcut (BQ-01 Customer-360 + BQ-02 fraud
     trend — the two most demo-able marts).
  3. Optionally ONE Fabric Data Factory pipeline as a CV demo (e.g. the OBP API copy activity)
     — a duplicate demo of an extractor that already exists in code, never a replacement.
- **Evidence-first deadline:** screenshots + config notes harvested into `journey/08` by
  **2026-08-24** (one-week buffer before expiry). The artifact that survives is the evidence,
  not the workspace. If Gold isn't ready by then, Fasa E shrinks or is skipped — it is
  garnish, never a dependency.
- Cost caveat (finops): cross-cloud reads from East Asia → AWS incur small S3 egress
  (cents at this data size); log it, don't fear it.
- Why still not build ON Fabric despite the free window: the 57-day deadline would then apply
  to the WHOLE project (seed → Gold → learning drills), and post-expiry the repo must still be
  runnable for interview defense — a portfolio that needs a paid capacity to demo is a dead
  portfolio. Renting the window for a demo is fine; mortgaging the build to it is not.

## D-01 Addendum #2 (2026-07-05, later same day) — Fabric DROPPED from scope; serving = Snowflake
Owner's ruling, and it supersedes Addendum #1's Fasa-E-on-Fabric: pick tech that defends the
RESUME, and the resume says **Snowflake · Databricks · AWS** — not Fabric. Therefore:
- **Fabric is OUT of this project entirely** (build AND serving). The active Fabric trial and
  the J-019 small-pool fix stay valuable for the owner's separate `home-credit-fabric-migration`
  project — nothing wasted, just not here.
- **Fasa E re-scoped: Snowflake serving veneer** — external tables over the Gold S3 prefix +
  a Power BI page (BQ-01 + BQ-02). This is the exact pattern already proven live in CIL
  (ADR-005: Snowflake = read-only window, lake = sole truth); reuse the CIL setup knowledge
  wholesale.
- **Timing discipline (evidence-first):** do NOT start/spend a Snowflake trial until Fasa D
  Gold exists — check whether the CIL Snowflake account is still alive first; if it is dead
  and no fresh trial is wanted, **DuckDB is the $0 fallback** (also the proven CIL pattern).
  Power BI can read exported Gold parquet directly in the worst case.
- Databricks: deliberately NOT forced into this repo — olist/paysim/Volve already carry the
  Databricks story; banking carries the multi-source + MDM + Snowflake-serving story. One
  repo, one story.

## D-01 Addendum #3 (2026-07-05) — RATIFIED STACK (binding; supersedes body + #1/#2)
Owner chose, after the Databricks-depth + storage decision: **Databricks = primary engine,
S3 = truth, Snowflake = serving.** This is the current stack. Concretely:
- **Compute: ALL transform on Databricks** (Bronze→Silver→Gold), PySpark + Delta,
  **Unity Catalog** governing S3 **external locations**. UC over multi-source MDM is
  banking's distinct governance story (olist/paysim/Volve carry the plain-Databricks story;
  this one carries UC + multi-source). Supersedes Addendum #2's "Databricks not forced in".
- **Storage: S3 stays sole source of truth** (`s3://<bucket>/banking/`), reuse CIL bucket.
  Both engines read S3 in place; neither owns it. NOT ADLS (keeps $0 reuse, no migration).
- **Serving: Snowflake** external tables over Gold S3 + Power BI (CIL ADR-005 pattern).
  DuckDB = $0 fallback if no live Snowflake account.
- **Fabric: still fully OUT** (Addendum #2 unchanged on this) — not on the resume; the Fabric
  trial serves the separate home-credit-fabric-migration project.

**Owner-confirmed operating model (2026-07-05): the Databricks trial is DELIBERATELY
DISPOSABLE.** Plan is explicit: run the pipeline a few times, screenshot every success +
UC lineage as evidence, use it for drills + troubleshooting practice, then **delete the
workspace**. So the 14-day limit is not a risk to fear — it's the intended lifecycle. The
only thing that must outlive it: the captured evidence + a repo that still runs (locally /
subset) for interview defense. That makes the mitigation below the PLAN, not a hedge —
Sonnet MUST:
1. **Write portable PySpark**, not Databricks-locked constructs (avoid DLT / heavy `dbutils` /
   notebook-only magic on the critical path) so the same transforms fall back to local Spark /
   Community Edition against S3 after the trial dies. UC table refs are the one accepted
   lock-in; keep a config switch (UC catalog vs path-based) so defense runs work without UC.
2. **Develop on the free path** (local subset or Community Edition — note CE has NO Unity
   Catalog and can't attach your S3 easily, so local-subset is the realistic dev default);
   reserve the paid trial for the **canonical full-scale run + UC lineage capture** in a
   concentrated window near the end.
3. **Evidence-first (hard rule):** during the trial window, harvest the full-run output + UC
   lineage/governance screenshots + `DESCRIBE HISTORY` + exported notebooks-with-output into
   `journey/08`. The portfolio is defended by that evidence + a local-runnable repo, never by
   an expired workspace.

### Alternatives considered (interview justification — why each choice beat its rival)
Pure architecture, trial-independent. This is the "why not X" you defend in an interview.

**Compute — Databricks over AWS Glue** (both managed Spark on S3):
- FOR Databricks: Unity Catalog (unified lineage/access/discovery — the value-add for a
  multi-source MDM theme; Glue's Catalog+Lake Formation is more fragmented); Photon (faster
  than Glue's OSS Spark); Delta-native (OPTIMIZE/Z-ORDER/liquid clustering/time-travel
  first-class; bolt-on in Glue); stronger notebook dev loop; portable multi-cloud skill.
- FOR Glue (what we give up): truly serverless (no cluster to size); zero-friction AWS-native
  plumbing (IAM/Athena/Step Functions); simpler per-second cost, no idle-cluster risk.
- Verdict: the project sells a GOVERNANCE story; UC is exactly that. Glue runs the same Spark
  but tells a weaker story.

**Storage — S3-as-truth (external Delta) over data-inside-Databricks (managed):**
- FOR S3-truth: open/no-lock-in (any engine reads plain Delta+Parquet — this is the ONLY
  reason Snowflake-serving is possible); compute/storage fully decoupled (wipe+rebuild compute,
  lake untouched); own the bucket lifecycle/cost/encryption.
- Cost of S3-truth: a little more setup (UC external locations + storage creds); some
  managed-table auto-optimization (predictive optimization, auto-vacuum) is smoothest on
  fully-managed tables. Nuance: UC managed tables CAN use your own S3 as managed location —
  so you keep most ergonomics without the lock-in.
- FOR managed (what we give up): simpler, Databricks owns layout/vacuum/newest features first.
  But: lock-in (external engines can't read it; Snowflake would need unload/Delta-Share) and
  data lifecycle coupled to the workspace. Kills the multi-engine architecture.
- Verdict: multi-engine (Databricks transforms + Snowflake serves) REQUIRES open storage.
  S3-truth is decisive.

**Serving — Snowflake over Databricks-SQL-only** (Databricks CAN serve BI directly, so this
is a deliberate addition, not a necessity — say so honestly):
- FOR Snowflake: separation of concerns (BI isolated from transform clusters, scales
  independently); best-in-class concurrent BI (elastic warehouses, caching); mirrors the real
  "Databricks-for-eng + Snowflake-for-serving" enterprise split — a credible interview story
  that puts a resume tech to genuine use.
- Cost of Snowflake: a second platform + two governance models (UC + Snowflake RBAC);
  external-table-over-S3 latency (native perf needs copy-in/duplication or Iceberg tables;
  external tables are fine for a demo).
- FOR Databricks-only (what we give up): one platform end-to-end, UC governs everything, zero
  data movement, always fresh, lower cost/complexity.
- Verdict: keep Snowflake as a deliberate "demonstrate the two-platform integration" choice,
  NOT because Databricks-SQL can't serve. Dropping Snowflake would cost nothing functionally —
  be ready to say exactly that.

## D-13 — Terraform: OUT of v1 (owner asked 2026-07-05)
The project's cloud infra surface is ~3 resources (S3 prefix, 1 read-only IAM policy/key for
serving, optionally an S3 lifecycle rule); local "infra" is docker-compose, which is already
code. Terraform for 3 resources is ceremony, and the governing rule of this portfolio is:
**build what defends a resume claim** — the resume does not claim Terraform/IaC. If the owner
adds an IaC claim to the resume later, revisit as a small post-v1 hardening module (IAM
policy + lifecycle + Snowflake external stage via provider) — never on the critical path.

## D-14 — Development workflow: dev-cheap, run-on-Databricks, vertical-slice, sample-set
Owner asked 2026-07-05 how the build actually runs day-to-day. Locked answer (aligned to the
ratified Databricks stack, D-01 Addendum #3):
- **Two environments, one portable codebase.** DEV loop = local Spark / subset (free, fast,
  no trial clock) for iterating logic. CANONICAL runs = **Databricks clusters** (full data,
  Unity Catalog over S3) during the disposable trial window, screenshots harvested. Same
  portable PySpark runs in both — that is what lets the repo still run for defense after the
  workspace is deleted. (NOT Glue — Glue is home-credit's story; banking = Databricks + UC.)
- **Vertical slice BEFORE horizontal layer** (the important methodology call). The Fasa
  A→B→C→D order is the macro sequence + gates, but WITHIN it, drive **one source end-to-end
  thin first** (e.g. Postgres → Bronze → Silver → one Gold check) to validate the
  Bronze→Silver contract, THEN replicate across the other 3 sources. Do NOT build all of
  Bronze (4 sources) then discover at Silver the Bronze format is wrong and redo 4 sources.
  First slice de-risks the contract; after it, widening is mechanical.
- **Sample-set throughout the dev loop.** Seed a small deterministic subset for fast
  iteration (seconds, no cost); run the full seeded set only for the "real" fasa-gate run.
  Determinism (D-03.4) means subset and full behave identically.
- Why logged: so "why did you build it this way" is answerable from the record, not memory.

## D-02 — Batch-first; CDC is Fasa C
Fasa B = high-watermark incremental (`WHERE updated_at > :watermark`). CDC
(Debezium+Kafka or platform-native) is a later fasa. **Bronze contract is frozen across
fasa** — the CDC upgrade swaps extractors only; Bronze-down never changes. This IS the
O-DSN-04/05 drill made real.

**Rationale (for interview defense — CDC is an optimization, not a correctness feature):**
1. Batch and CDC produce identical Silver/Gold — only the extractor differs. Build batch
   first and ~90% of the project (MERGE, crosswalk, marts, DQ) is already proven when CDC
   is swapped in.
2. The hard/valuable problems live in the transform (MDM crosswalk, birth_number decode,
   survivorship, reconciliation), not the extraction. CDC-first burns the early weeks on
   Kafka/Debezium plumbing before any portfolio-worthy logic exists.
3. Batch is cheaper to run and debug — no 24/7 Kafka/Debezium eating RAM, no offset/lag/
   schema-registry failure class confounding logic bugs. Batch fails visibly and re-runs
   deterministically.
4. It mirrors real bank migration order (Teradata→cloud): stand up incremental loads, prove
   reconciliation + stakeholder trust (BQ-10), THEN cut latency with CDC where the business
   needs it. Industry-correct sequence = better interview story than "went straight to Kafka".
5. Upgrade path is small once batch works (≈ `.read`→`.readStream`; watermark → CDC offset).
**Honest caveat (R-25):** pure batch high-watermark cannot see HARD deletes — a physically
deleted row never reappears in a `WHERE updated_at >` query. That specific gap is what CDC
closes later (`op='d'` from the log). So batch is not a throwaway prototype: it handles
inserts/updates correctly and completely; CDC is added specifically for deletes + latency.

## D-03 — Seeding rules (locked)
1. Every seeded table gets a PK + `created_at` + `updated_at`.
2. **Global date-rebase**: all datasets shifted so max(date) = seed day, relative offsets
   preserved (fixes R-01, R-06, R-13 in one rule).
3. PaySim `step` → real timestamps (`base_date + step×1h`).
4. Deterministic: fixed random seed; a rebuild produces identical databases.
5. `drip_feed.py` simulates live traffic — INSERT/UPDATE a few rows per interval, always
   touching `updated_at`; soft deletes per D-06.
6. Every monetary column gets a currency code (see D-12).

## D-04 — Customer crosswalk (MDM) at seed
`dim_customer_xwalk` maps one bank-wide `customer_id` → `SK_ID_CURR` (home-credit),
`nameOrig` (paysim), `client_id` (Berka), OBP account. Generated at seed, versioned as a seed
artifact. Golden-record survivorship: source priority **CRM > core > loans > cards**, latest
`updated_at` tiebreak (R-23/R-24). This is the project's keystone and its best interview story.

## D-05 — Bronze is verbatim, append-only
Raw as-is; API JSON stored word-for-word (re-parse without re-call — CIL's Gemini lesson);
`dt=YYYY-MM-DD` partitions; file-drop sources use a processed-file manifest (name+checksum).
No transformation of any kind in Bronze — masking happens at Silver (D-07).

## D-06 — Deletes: soft in Fasa B, hard only via CDC
Sources implement `is_deleted` + `updated_at` touch. Hard-delete capture is explicitly OUT
until Fasa C — written down as a known limitation in `journey/07`, not discovered later (R-25).

## D-07 — PII ruling
Mask at Silver: account/card numbers (last-4 only), `birth_number` (decode then drop raw).
Bronze holds raw but access-restricted; `gates/secrets_scan.py` + journey/09 mandatory
(kit v1.1.0 made 09 non-optional).

## D-08 — Framework kit adoption: full set, no skipping
Copy `framework_template/` wholesale per its `00_START_HERE.md` steps 1–8. `gates/framework.yml`
filled FIRST. Journey 01–09 all filled (N/A-with-reason allowed, blank not). The four bootstrap
gates green before the first real commit.

## D-09 — Roster: 7 agents
architect + scope-guardian (mandatory veto pair, kit ADR-000) + senior-data-engineer +
data-quality-steward + product-owner + finops (part-time — S3/API cost watch) + **cikgu**
(learning layer, per retrofit addendum 2026-06-28; not in the kit's `operating/agents/`,
copy pattern from CIL). NO Haiku executor tier (ADR-012: no routing without volume).

## D-10 — Orchestration
Makefile / simple scheduler first. Repo MUST expose the control-plane orchestration contract
(`../control_plane_lab/03_PIPELINE_SIDE_CONTRACT.md`) so `airflow_dag_running_pipeline` can
adopt it as pipeline #6. No private Airflow inside this repo.

## D-11 — Repo + push
Suggested name `banking-multisource-lakehouse`. Known blocker: codespace `GITHUB_TOKEN` is
CIL-scoped — pushing the new repo needs the owner's PAT (see `retrofit-push-blocker` memory;
`gh api permissions:push=true` is a trap). Build locally regardless.

## D-12 — Currency
Static FX seed table (CZK/MYR/USD → one reporting currency) is the v1 mechanism; BNM OpenAPI
is an optional live enrich, never a build dependency.

## REJECTED (named, with reasons)
- **Fabric/OneLake during build** — trial-wall risk (see D-01; owner may override).
- **Kafka/Debezium/streaming in v1** — batch-first ruling (D-02); CDC is a fasa, not the start.
- **SAP BTP trial / ABAP Docker** — 90-day wall / 16–32GB RAM; file-export sim is more
  realistic for legacy SAP anyway.
- **`ga4_obfuscated_sample_ecommerce`** — static (Nov 2020–Jan 2021), Gemini's "live" claim
  is false. If live BigQuery practice is wanted later: `thelook_ecommerce`.
- **Wise sandbox** — auth ceremony buys nothing over OBP.
- **ML model training** (fraud model, default model) — this is a DATA ENGINEERING portfolio
  repo; `isFraud` is a label to serve, not to predict.
- **Dashboard-first / BI build-out** — evidence = queries + captured outputs (journey/08);
  a Power BI page may come later as serving veneer, not as scope.
- **Vector DB / RAG / semantic anything** — wrong project.
