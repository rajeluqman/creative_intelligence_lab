# STACK & END-TO-END FLOW — Creative Intelligence Pipeline

**Status:** Consolidated view (v1 + v1.5) · derived from the ratified `DATA_MODEL.md`,
`DATA_MODEL_v1.5_PERFORMANCE.md`, and the round-1/round-2 debates.
**Purpose:** one place to see every tool and the full flow.

---

## 1. The tool stack by layer

| Stage | Tool | Role | Status |
|-------|------|------|--------|
| **Source** | Google Drive API + Python | pull client's messy video folder | v1 |
| **Landing** | AWS S3 (write-once) + `hashlib` SHA-256 | content-addressed video bytes `landing/video/<asset_id>.<ext>` | v1 |
| **Extraction** | **Gemini API (Flash-first)** + `responseSchema` (structured output) | video → semantic-chunk JSON, verbatim | v1 |
| **Prompt mgmt** | versioned prompt registry (`prompt_version`/`prompt_hash`/`model_version`) | reproducibility + drift attribution | enhancement |
| **Bronze** | S3 (parquet/JSON) + **DuckDB via httpfs** (ephemeral catalog) | immutable raw Gemini JSON + raw Meta/TikTok CSV | v1 / v1.5 |
| **Silver** | **dbt-duckdb** (`external` parquet → S3) + **Great Expectations** | flatten → chunk rows; schema + range gates | v1 |
| **Gold** | **dbt-duckdb** marts (`external` parquet → S3) | graph + feature store + perf marts | v1 / v1.5 |

> **Storage = unified S3 (ADR-005, owner directive 2026-06-22).** All layers persist to S3:
> `landing/ bronze/ silver/ gold/`. Silver/Gold materialize as `external` parquet on S3, read via
> DuckDB `httpfs`; the DuckDB catalog is ephemeral (compute only). **No MinIO** — dev + staging +
> any future drill use real S3 buckets (a separate staging/throwaway bucket for overwrite work).
> Tradeoff (accepted): no longer offline-$0 standalone — a fresh clone needs AWS creds for the ELT.
| **Stats** | Python (pandas + scipy) | Mann-Whitney U + Bonferroni (SUGGESTIVE tier only) | v1.5 |
| **Serving / demo** | **Snowflake Cortex** (external tables over Gold S3 + Cortex Search + Power BI) — showcased serving; **DuckDB VSS over Gold S3 = $0 fallback** | semantic search + correlation queries (ADR-005) | v1 / v1.5 |
| **Orchestration** | **local Airflow** (deferrable ops, triggerer, `gemini_api` Pool, `expand()`, skip-existing) | async, rate-limit-aware run | v1 |
| **Quality** | Great Expectations + dbt tests | per-layer gates incl. honesty gates | v1 / v1.5 |
| **CI/CD** | GitHub Actions (`py_compile` + `ruff` + dbt parse + GE-JSON) | static gates, PR→main | v1 |
| **Telemetry** | `fact_extraction_run` (tokens/cost/latency/retries/confidence) | FinOps + ops dashboard | enhancement |
| **Render (v2)** | FFmpeg | stitch chunk sequence → candidate mp4 | v2 |

**Rejected at this scale (do not add):** Spark / Databricks / MWAA / Fivetran-Airbyte /
Pinecone-Weaviate. Reason: KB–MB structured scale; the only real cost/latency is the Gemini API
call. (Round-1 §7, round-2 ingest ruling.)
**Admitted by ADR-005 (owner override 2026-06-22):** Snowflake Cortex as a **read-only serving
veneer** over Gold S3 (NOT as transform engine — DuckDB stays that; NOT as a source of truth —
Gold S3 stays that). Disposable trial + day-25 teardown; DuckDB VSS retained as the $0 fallback.

---

## 2. End-to-end flow — the whole picture

```
                          ┌──────────────────────────────────────────────────────────┐
                          │  CLIENT delivers a Google Drive folder (messy compilation │
                          │  of RAW creative video + sometimes EDITED winning ads)    │
                          └───────────────────────────────┬──────────────────────────┘
                                                          │ Google Drive API + Python
                                                          ▼
   PATH A — VIDEO (raw AND edited)            ┌──────────────────────────────┐
   ══════════════════════════════            │  LANDING  (S3, write-once)    │
                                             │  landing/video/<asset_id>.ext │  asset_id = SHA-256(bytes)
                                             └───────────────┬──────────────┘
                                                             │  skip-existing on hash (idempotent, $-firewall)
                                                             ▼
                                             ┌──────────────────────────────┐
                                             │  Gemini API (Flash)           │  structured output (responseSchema)
                                             │  prompt_version + model_version│  → semantic-chunk JSON, verbatim
                                             └───────────────┬──────────────┘
                                                             ▼
                                ┌────────────────────────────────────────────────────┐
                                │  BRONZE  bronze_asset_raw  (S3, immutable, append)  │  ← re-parse, NEVER re-pay
                                └───────────────────────────┬────────────────────────┘
                                                            │ dbt-duckdb + Great Expectations (schema gate)
                                                            ▼
                                ┌────────────────────────────────────────────────────┐
                                │  SILVER  silver_chunk  (1 row = 1 semantic chunk)   │  ← chunking lives HERE
                                │  filler removed · ts normalized · GE range gate     │     standalone_score 1..5
                                └───────────────────────────┬────────────────────────┘
                                                            │ dbt-duckdb marts
                                                            ▼
                ┌───────────────────────────────────────────────────────────────────────────┐
                │  GOLD (graph + feature store)                                              │
                │   dim_asset (RAW+EDITED, self-ref parent) · fact_chunk (grain=chunk)        │
                │   bridge_asset_lineage · bridge_chunk_compatibility · keyword/theme bridges │
                └───────────────────────────────────────────────┬───────────────────────────┘
                                                                 │
                                                                 │   ┌──────────────────────────────────────┐
                                                                 │   │  EDITED ad ALSO ingested via Path B  │
   PATH B — PERFORMANCE (Meta / TikTok)                          │   │  for its funnel metrics              │
   ════════════════════════════════════                         │   └──────────────────────────────────────┘
   manual CSV export ──► S3 ──► bronze_ad_performance_raw        │
        │  (immutable)            │  dbt-duckdb: stg_meta + stg_tiktok → union
        ▼                         ▼
   dim_platform           fact_ad_performance (grain: ad × platform × DAY, raw counts)
   (Meta 3s/TikTok 6s)            │
                                  │   bridge_ad_chunk  (editor's asserted cut: ad → chunk + role + position)
                                  ▼            │
                          int_metric_chunk_alignment  ◄────────────┘   (time-range join: Hook Rate ↔ hook chunk,
                                  │                                       CTR-Link ↔ cta chunk; one chunk per metric)
                                  ▼
                          fct_ad_kpi (ratios) ──► fct_ad_metric_chunk ──► mart_chunk_perf_correlation
                                                                                  │  (within-platform, within-winners,
                                                                                  │   sample-size regime, honesty_note)
                                                                                  ▼
                ┌───────────────────────────────────────────────────────────────────────────┐
                │  SERVING / DEMO  (Snowflake Cortex over Gold S3; DuckDB VSS = $0 fallback)  │
                │   • "find clips: theme=X, sentiment=Y, standalone_score>=4"   (v1 north-star)│
                │   • "which Hook-chunk themes correlate with Hook Rate >=25%?" (v1.5)         │
                │   • "mine unused RAW chunks matching winning themes"          (v1.5)         │
                └───────────────────────────────────────────────────────────────────────────┘

   ORCHESTRATION (local Airflow): deferrable upload→poll per asset, gemini_api Pool, expand() per video, skip-existing
   QUALITY (GE + dbt tests): per-layer gates + v1.5 honesty gates (within-winners / within-platform / sample ladder)
   CI/CD (GitHub Actions): py_compile + ruff + dbt parse + GE-JSON, PR→main
```

---

## 3. The two ingestion paths (why there are two)

- **Path A (video):** every video — RAW *and* EDITED — goes through Drive→S3→Gemini→Bronze→
  Silver→Gold. This produces `fact_chunk` rows. The EDITED ad gets its **own** chunk rows in its
  **own** timeline (needed for the position-aligned Hook-Rate mapping).
- **Path B (performance):** only EDITED ads that actually ran have Meta/TikTok metrics. These
  arrive as **manual CSV export → S3 → `bronze_ad_performance_raw`** and become
  `fact_ad_performance`. They are stitched to Path A through `bridge_ad_chunk` (which chunks are
  in the cut) — never by propagating metrics backward onto RAW (permanent veto).

**Join key reality:** `ad_id` (platform creative id) → `asset_id` (edited asset) is a manual
seed (`map_ad_asset.csv`) at 3–15 ads, enforced by a dbt `relationships` test.

---

## 4. Stage → resume-stack mapping (portfolio fit)

| This project uses | Resume line it demonstrates |
|-------------------|------------------------------|
| S3 + medallion + dbt-duckdb + GE + GitHub Actions | Medallion architecture, ELT, dbt Core, Great Expectations, CI/CD |
| Gemini API structured output + prompt versioning | LLM-in-production / Gemini API (the *distinct* differentiator) |
| local Airflow deferrable + Pool + dynamic mapping | Apache Airflow orchestration (advanced patterns, not toy DAGs) |
| star-vs-graph decision + bridge tables + SCD | Dimensional modelling, data architecture judgement |
| within-winners / sample-size honesty gates | Data quality, statistical literacy (rare in DE portfolios) |

**Distinctiveness vs the 4 existing pipelines:** this is the only one that is *LLM-extraction +
graph/feature-store + non-deterministic-output testing*. Not another batch star schema.
