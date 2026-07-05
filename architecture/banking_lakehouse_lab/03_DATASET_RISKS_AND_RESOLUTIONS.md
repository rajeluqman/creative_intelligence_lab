# Dataset Risk Register — all known problems + resolutions (30 items)

> Feeds `journey/01_DATASET_AND_SOURCES.md` (risks) and `journey/06_DQ_PLAN.md` (items tagged
> **DQ-gate**). Every item = (problem → why it happens → resolution → where it lands).
> IDs are stable — cite them in STTM/DQ docs as R-xx.

## A. Home Credit → PostgreSQL ("Sales / Loan Dept")

| ID | Problem | Why | Resolution | Lands in |
|----|---------|-----|------------|----------|
| R-01 | **No timestamp columns at all** — dataset is a static snapshot; high-watermark extraction impossible out of the box | Kaggle competition data, not an OLTP dump | Seeding adds `created_at`/`updated_at` to EVERY table; drip-feed touches `updated_at` on update (D-03) | seed spec, 07 |
| R-02 | `application` has ~122 anonymized columns (`EXT_SOURCE_*` etc.) — schema noise, meaningless names downstream | Anonymized competition export | Bronze keeps ALL columns verbatim; Silver prunes to STTM-selected set; STTM records meaning of every kept column | 05_STTM |
| R-03 | **Orphan foreign keys** — `bureau`/`previous_application` rows whose `SK_ID_CURR` has no `application` parent (and `bureau_balance`→`bureau`) | Sampled export | FK-integrity **DQ-gate**; orphans → quarantine table, counted and reported — never silently dropped | 06_DQ |
| R-04 | Null-heavy columns (many >50% null) poison aggregates | Sparse optional fields | Per-column null-rate expectations; explicit keep/drop ruling per column | 03_REQ, 06_DQ |
| R-05 | Volume skew — `installments_payments` ~13.6M rows; full dump per run kills the laptop and defeats the exercise | Big child tables | Seed deterministically (fixed subset or one-time full); extraction is incremental-only after that; chunked COPY at seed | seed spec, 07 |

## B. PaySim → MS SQL Server ("Credit Card + Fraud")

| ID | Problem | Why | Resolution | Lands in |
|----|---------|-----|------------|----------|
| R-06 | `step` is a simulation hour index (1–744), **no real dates** — no watermark, no daily partitions possible | Synthetic simulator output | At seed: `txn_ts = base_date + step×1h`, rebased so max = seed day (D-03) | seed spec |
| R-07 | `nameOrig`/`nameDest` are synthetic codes (C…/M…) — unlinkable to home-credit or Berka | Independent generators | `dim_customer_xwalk` assigns bank-wide `customer_id` at seed (D-04) | 04_MODEL |
| R-08 | `isFraud` vs `isFlaggedFraud` semantic confusion → wrong fraud KPIs if mixed up | Two different concepts: ground-truth label vs naive in-sim rule | Data-dictionary ruling: `isFraud` = label (Gold KPIs use this); `isFlaggedFraud` = system-rule flag only, kept for rule-performance analysis | 05_STTM |
| R-09 | Merchant rows (M…) have empty balance columns **by design** → false DQ failures | Simulator doesn't model merchant balances | Expectation scoped: balance-null allowed where entity type = merchant; not a failure | 06_DQ |
| R-10 | 6.3M rows — `SELECT *` per run hammers source + transfer | Naive full extract | High-watermark extraction + date-partitioned landing — this IS drill O-DSN-04/05 | 07 |
| R-11 | Known PaySim quirk: `oldbalance`/`newbalance` don't always reconcile with `amount` | Simulator artifact | Balance-reconciliation check runs at **WARN** severity, documented as source quirk — data is NOT silently "fixed" | 06_DQ |

## C. Berka (PKDD'99) → SAP-sim file drop ("Internal CRM")

| ID | Problem | Why | Resolution | Lands in |
|----|---------|-----|------------|----------|
| R-12 | `birth_number` encodes gender inside the date (**month+50 = female**), format YYMMDD → naive parse = wrong DOB and no gender | 1990s Czech national-ID convention | Silver decode rule → `birth_date` + `gender`; unit-tested with known fixtures | 05_STTM |
| R-13 | Data spans 1993–1998 → timeline clash with 2026 drip-feed and rebased paysim dates | 1999 dataset | Global date-shift at seed: max(date) = seed day, relative offsets preserved (D-03) | seed spec |
| R-14 | Amounts in CZK vs paysim unitless vs home-credit — mixed currencies corrupt Customer-360 sums | Independent datasets | Every monetary column gets a currency code at seed; Gold normalizes via static FX seed table (BNM OpenAPI = optional live enrich) (D-12) | 04_MODEL |
| R-15 | File-drop hazards: duplicate drops, partial writes, re-drops of the same export | File-based legacy integration | Processed-file **manifest** (filename+checksum), atomic write (tmp→rename), idempotent re-process | 07 |
| R-16 | CSV schema drift between drops ("SAP export changed") → silent column shift | No contract on file exports | Schema check on pickup; mismatch → quarantine folder + alert; never best-effort parse | 06_DQ, 07 |
| R-17 | Czech encoding/diacritics → mojibake in names/districts | Legacy encodings | Force UTF-8 (verify actual encoding at seed); encoding expectation in DQ | 06_DQ |

## D. Open Bank Project sandbox API ("Core Banking")

| ID | Problem | Why | Resolution | Lands in |
|----|---------|-----|------------|----------|
| R-18 | Token expiry mid-extract → partial pulls | OAuth/DirectLogin TTL | Refresh-on-401 + resume; every run idempotent per date partition | 07 |
| R-19 | Deeply nested JSON + API version drift → parser breakage | Sandbox evolves | Bronze stores the response **verbatim** (re-parse without re-call — CIL lesson); API version recorded in landing path | 07 |
| R-20 | Rate limits / sandbox downtime → failed runs | Shared free sandbox | Retry with backoff + circuit-break + alert; rerun-safe by partition | 07 |
| R-21 | Sandbox data is small and **may reset anytime** → volume/continuity assumptions break | Free sandbox, not SLA'd | Treat OBP as snapshot-append only; volume story lives in paysim; snapshot diff detects resets | 01_SOURCES |
| R-22 | Pagination on `/transactions` → silent truncation | Default page limits | Paginate to exhaustion + reconcile counts vs API-reported totals | 07, 06_DQ |

## E. Cross-source / systemic

| ID | Problem | Why | Resolution | Lands in |
|----|---------|-----|------------|----------|
| R-23 | **No common key across the 4 sources** — the keystone problem | Datasets never designed to join | `dim_customer_xwalk` generated at seed (D-04); interview story = MDM / entity resolution | 04_MODEL |
| R-24 | Conflicting customer attributes across systems (name/address/DOB differ) | Multiple masters | Golden-record **survivorship rules**: source priority CRM > core > loans > cards, latest `updated_at` tiebreak | 04_MODEL |
| R-25 | **Hard deletes are invisible** to watermark batch | Watermark only sees rows that still exist | Fasa B: soft-delete flag (`is_deleted` + touch `updated_at`). Hard deletes = Fasa C CDC only (`op='d'`). Named, documented limitation (D-06) | 07 |
| R-26 | Late/out-of-order updates — drip-feed races the extractor at the watermark boundary → missed rows | Non-atomic write vs read | Overlap window (watermark − 5 min) + MERGE dedupe on PK + `updated_at` | 07 |
| R-27 | **PII lands raw in Bronze** — `birth_number`, account/card numbers | Verbatim-Bronze rule (D-05) | Mask at Silver; Bronze access restricted; `secrets_scan.py` gate; full ruling in journey/09 (D-07) | 09_SECURITY |
| R-28 | Source schema evolution (new column added mid-project) → break or silent loss | Live-ish sources | Controlled Delta schema evolution: explicit `mergeSchema` + drift alert — never auto-silent | 07 |
| R-29 | Late-arriving dimension — card txn lands before its customer exists in the CRM extract | Independent extract schedules | Unknown-member key (−1) + re-link job on next run | 04_MODEL |
| R-30 | No reconciliation = no stakeholder trust in ANY number | End-to-end pipeline | Per-run source→Bronze→Silver row-count reconciliation with tolerances; surfaced in `mart_pipeline_health` (BQ-10) | 06_DQ, 08 |
