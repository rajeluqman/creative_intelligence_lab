# Banking Multi-Source Lakehouse — Master Spec (Fasa-0 planning)

> Planning artifact for a NEW external portfolio repo (suggested name:
> `banking-multisource-lakehouse`). Build happens in that repo, NOT in CIL — this folder is
> the design/decision record only, same pattern as `../pipeline_retrofit/` and
> `../control_plane_lab/`. Opus designs here; Sonnet executes via `02_SONNET_BUILD_KICKOFF.md`.
> Origin: owner's Gemini brainstorm (2026-07-04) — enterprise banking data-platform simulation,
> multi-source seeding → landing → medallion, batch-first then CDC.

## What this project is
Simulate a bank's data estate end-to-end: seed 3 "production" source systems + 1 live sandbox
API from complementary public datasets, then build the real data-engineering layer — incremental
extraction → **Landing → Bronze → Silver → Gold** (4-layer medallion, D-15) — governed by the
`framework_template/` kit (journey docs + gates + agents).

**The resume claim it must defend:** "I built a multi-source banking lakehouse: 4 heterogeneous
sources (2 RDBMS, 1 file-drop ERP export, 1 REST API), high-watermark incremental ingestion,
a Landing→Bronze transport-integrity gate that quarantines incomplete pulls/duplicate deliveries,
MDM customer crosswalk (no shared keys across sources), 4-layer medallion with DQ gates,
Customer-360 / fraud / loan-funnel marts — upgrade path to CDC without touching Bronze-down."

## Source systems and their datasets

| Source system | Role in the "bank" | Dataset (seed) | Key tables / content | Native key |
|---|---|---|---|---|
| PostgreSQL (Docker) | Sales / Loan Dept | **Home Credit Default Risk** (owner already has it — retrofit repo) | application, bureau, previous_application, installments (7+ relational tables) | `SK_ID_CURR` |
| MS SQL Server (Docker) | Credit Card + Fraud | **PaySim** (owner already has it — retrofit repo) | ~6.3M synthetic txns, `isFraud` label | `nameOrig`/`nameDest` |
| SAP-sim (file drop, SFTP-style folder) | Internal CRM / customer master | **Berka — PKDD'99 Czech Financial Dataset** (Kaggle: "Czech bank financial dataset") | client, account, disp, card, loan, trans, district (8 relational tables) | `client_id`, `account_id` |
| Open Bank Project sandbox | Core Banking API | none — sandbox generates its own | accounts, balances, transactions (nested JSON) | OBP `account_id` |
| *(optional enrich)* | FX / market rates | **BNM OpenAPI** (genuinely live, no auth) | daily exchange/base rates | `date` |

**Rejected sources** (from the Gemini convo, with reasons): `ga4_obfuscated_sample_ecommerce`
(static Nov-2020–Jan-2021, NOT live — Gemini factual error), Wise sandbox (auth complexity buys
nothing over OBP), SAP BTP trial / ABAP Docker (90-day wall / 16–32GB RAM; file-export simulation
is both cheaper AND more realistic for legacy SAP integration).

## Architecture

```
              FASA A — SEEDING (once, Python scripts + drip-feed)
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Kaggle CSV (home-credit) ──▶  POSTGRES        "Sales / Loan Dept"      │
  │  Kaggle CSV (paysim)      ──▶  MS SQL          "Credit Card + Fraud"    │
  │  Kaggle CSV (berka)       ──▶  SAP-SIM folder  "Internal CRM" (CSV)     │
  │  (no seed — sandbox)           OPEN BANK PROJ  "Core Banking" (API)     │
  │                                                                         │
  │  Seeding rules (D-03): every table gets PK + created_at/updated_at;     │
  │  date-rebase all sets so max(date)=seed day; paysim step→timestamp;     │
  │  dim_customer_xwalk generated HERE (D-04).                              │
  │  + drip-feed script: INSERT/UPDATE a few rows every X minutes           │
  └─────────────────────────────────────────────────────────────────────────┘

   COMPUTE (D-01 Addendum #3): ALL transform below runs on DATABRICKS clusters
   (portable PySpark + Delta, Unity Catalog over S3 external locations). S3 = sole
   truth; dev loop iterates on local Spark / subset; canonical full runs on the
   disposable Databricks trial with evidence screenshotted. Snowflake serves Gold.

              FASA B — INGESTION (batch-first, D-02)

   POSTGRES             MS SQL              SAP-SIM folder      OPEN BANK API
      │                    │                     │                    │
      │ incremental        │ incremental         │ file pickup        │ OAuth token,
      │ WHERE updated_at   │ WHERE updated_at    │ (manifest of       │ GET /accounts
      │   > :watermark     │   > :watermark      │  processed files)  │ /transactions
      ▼                    ▼                     ▼                    ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ LANDING — transient arrival zone (short TTL), as-arrived, MESSY by design│
  │   landing/postgres_sales/dt=…/*.parquet   landing/mssql_cards/dt=…/*.pq  │
  │   landing/sap_crm/dt=…/*.csv              landing/openbank_api/dt=…/*.json│
  │   may contain: partial pulls · truncated pages · dup/re-dropped files ·  │
  │   redelivered CDC events                                                 │
  └─────────────────────────────────────────────────────────────────────────┘
      ▼  PROMOTION GATE = TRANSPORT INTEGRITY only (D-15): _SUCCESS present ·
         manifest/checksum match · pagination reconciled vs API totals ·
         dedup redeliveries · multi-file set complete → else QUARANTINE
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ BRONZE — permanent trusted raw archive, append-only, verbatim (D-05)    │
  │   transport-complete & exactly-once; still RAW (no business cleansing);  │
  │   raw JSON kept word-for-word, never flattened                          │
  └─────────────────────────────────────────────────────────────────────────┘
      ▼  CONTENT-QUALITY gate (Bronze→Silver, D-15): MERGE upsert (latest per
         PK), flatten nested JSON, type standardization, PII masking (D-07),
         dedupe drip vs historical, orphan/null/birth_number handling
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SILVER (Delta) — cleaned + conformed, 1 row = latest state per entity   │
  │   + dim_customer_xwalk (MDM crosswalk — the project's keystone)         │
  └─────────────────────────────────────────────────────────────────────────┘
      ▼  star schema + aggregates
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ GOLD — dim_customer (golden record), fact_txn, fact_card_fraud,         │
  │        marts: customer_360 · loan_funnel · fraud_followup ·             │
  │        cross_sell · dormancy · daily_flows · pipeline_health            │
  └─────────────────────────────────────────────────────────────────────────┘
      ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SERVING (Fasa E, optional, read-only — D-01 Addendum #2/#3)             │
  │   Snowflake external tables over Gold S3 + Power BI page (BQ-01/02);    │
  │   DuckDB = $0 fallback. Lake stays sole truth (CIL ADR-005 pattern).    │
  └─────────────────────────────────────────────────────────────────────────┘
   + evidence layer: journey/08 (one runnable query per BQ)

  FASA C (later): swap Postgres/MSSQL batch arrows for CDC (Debezium+Kafka or
  platform-native mirroring). CDC events land in LANDING like everything else; the
  transport-integrity promotion gate absorbs duplicate/out-of-order events, so
  BRONZE-and-below is UNCHANGED (the Landing split is what makes this clean — D-15).
```

## Framework adoption map (kit → this project)
Copy `framework_template/` wholesale into the new repo (per `00_START_HERE.md` steps 1–8),
then fill the journey docs with the content already drafted in this lab folder:

| Journey doc | Content source |
|---|---|
| `01_DATASET_AND_SOURCES.md` | Source table above + `03_DATASET_RISKS_AND_RESOLUTIONS.md` |
| `02_BUSINESS_QUESTIONS.md` | `04_BUSINESS_QUESTIONS.md` (the 10 BQs) |
| `03_DATA_REQUIREMENTS.md` | Derive from BQs: entities, retention, null/keep-drop rulings |
| `04_DATA_MODEL.md` | Star schema for Gold (dims/facts listed above) + xwalk design |
| `05_STTM.md` | Source→target mapping per table incl. birth_number decode, step→ts |
| `06_DQ_PLAN.md` | Risk register items marked `DQ-gate` in `03_DATASET_RISKS…` |
| `07_PIPELINE_SPEC.md` | Fasa A/B/C mechanics: watermark, Landing→Bronze promotion gate (transport integrity, `_SUCCESS`+manifest — D-15), MERGE, retry/backoff |
| `08_SERVING_AND_EVIDENCE.md` | Mart outputs + reconciliation evidence per BQ |
| `09_SECURITY_AND_ACCESS.md` | PII masking rules (D-07), Bronze access restriction, secrets |

Drill prep already staged: O-DSN-04 (CDC over full dump — *banking-project prep*) and O-DSN-05
(high-watermark extraction) in `../control_plane_lab/saboteur/PROBLEM_BANK_OPTIMIZATION.md:130`.

## Orchestration
Local runs first (Makefile / simple scheduler). The repo MUST expose the control-plane
orchestration contract (`../control_plane_lab/03_PIPELINE_SIDE_CONTRACT.md`) so
`airflow_dag_running_pipeline` can drive it later as pipeline #6. Do not build a private
Airflow inside this repo.

## Companion docs in this folder
- `01_OPUS_DECISIONS.md` — locked rulings D-01…D-15 (stack ratified; 4-layer medallion)
- `02_SONNET_BUILD_KICKOFF.md` — execution handoff
- `03_DATASET_RISKS_AND_RESOLUTIONS.md` — full risk register (R-01…R-30)
- `04_BUSINESS_QUESTIONS.md` — the 10 stakeholder BQs with join paths
- `05_BUILD_AND_VERIFY_PROMPTS.md` — Sonnet build+self-audit / Opus verify paste-prompts
- `PROJECT_STATUS.md` — resume-safe status
