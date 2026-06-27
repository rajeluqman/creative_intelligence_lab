# ERD — CONSOLIDATED DATA MODEL (v1 + v1.5)

**Status:** Consolidated reference · authority = `DATA_MODEL.md` + `DATA_MODEL_v1.5_PERFORMANCE.md`.
**Paradigm:** asset-lineage **graph + chunk feature store** + a descriptive **within-winners
performance-correlation** layer. NOT a Kimball star.

---

## 1. Entity map (the whole model on one screen)

```
   ┌──────────────────────────────┐
   │          dim_client          │  tenancy boundary (ADR-006)
   │  PK client_id                │  client_name, account_support_owner,
   │     drive_folder_id          │  landing_ttl_days, status   (SCD0 seed)
   └──────────────┬───────────────┘
                  │ 1 client → N assets
                  ▼
                                  ┌──────────────────────────────┐
                          ┌──────►│          dim_asset           │◄────┐  parent_asset_id
            asset_type    │       │  PK asset_id =SHA256(client_id│─────┘  (self-ref, RAW→EDITED,
            = RAW|EDITED  │       │     ':' content_sha256)      │        DISCOVERY ONLY)
                          │       │     client_id (FK→dim_client)│
                          │       │     content_sha256 (non-key, │
                          │       │       intra-client near-dup) │
                          │       │     parent_asset_id (FK self)│
                          │       │     asset_type, duration_sec │
                          │       │     source_uri, dq_flag      │
                          │       └───────────┬──────────────────┘
                          │                   │ 1 asset → N chunks
                          │                   ▼
   ┌──────────────────────┴───┐   ┌──────────────────────────────┐   ┌──────────────────────────────┐
   │   bridge_asset_lineage   │   │          fact_chunk          │   │   bridge_chunk_compatibility │
   │  parent_asset_id  (FK)   │   │  PK chunk_id                 │◄──┤  chunk_id          (FK)      │
   │  child_asset_id   (FK)   │   │     asset_id        (FK)     │   │  compatible_theme            │
   │  (RAW ──► EDITED)        │   │     chunk_sequence           │   │  theme_match_score           │
   └──────────────────────────┘   │     start_sec, end_sec       │   └──────────────────────────────┘
                                   │     transcript_segment       │
   ┌──────────────────────────┐   │     chunk_theme              │   ┌──────────────────────────────┐
   │  dim_keyword_bridge      │◄──┤     sentiment                ├──►│   dim_theme_bridge           │
   │  chunk_id, keyword       │   │     standalone_score (1..5)  │   │   chunk_id, theme            │
   └──────────────────────────┘   │     embedding (BUILT, VSS)   │   └──────────────────────────────┘
                                   └───────────┬──────────────────┘
                                               │ chunk_id
                  ══════════════ v1.5 PERFORMANCE LAYER ══════════════
                                               │
                                   ┌───────────┴──────────────────┐        ┌─────────────────────┐
                                   │       bridge_ad_chunk        │        │    dim_platform     │
                                   │  PK (ad_id, chunk_id)        │        │  PK platform_id     │
                                   │     asset_id   (FK, EDITED)  │        │     platform_name   │
                                   │     chunk_role (hook|body|   │        │     hook_window_sec │
                                   │                cta|...)      │        │     hold_milestones │
                                   │     position_in_ad           │        └──────────┬──────────┘
                                   │     start_sec, end_sec       │                   │
                                   └───────────┬──────────────────┘                   │
                                               │ ad_id                                │ platform_id
                                               ▼                                      ▼
                                   ┌──────────────────────────────────────────────────────────┐
                                   │                 fact_ad_performance                       │
                                   │  PK (ad_id, platform_id, perf_date)                       │
                                   │     asset_id (FK → dim_asset, asset_type='EDITED')         │
                                   │     impressions, plays_3s/25/50/75/100                     │
                                   │     sum_watch_time_sec, play_count                         │
                                   │     link_clicks, results, spend                           │
                                   └──────────────────────────────────────────────────────────┘

   ┌──────────────────────────────┐   (enhancement — operational telemetry, not a business fact)
   │      fact_extraction_run     │   PK run_id · asset_id (FK) · prompt_version · model_version
   │  tokens_in/out · api_cost    │   · processing_time_sec · retry_count · extraction_confidence
   └──────────────────────────────┘
```

---

## 2. Table inventory

| Table | Type | Grain | Layer | Version |
|-------|------|-------|-------|---------|
| `dim_client` | dimension | 1 client account | Gold | v1 |
| `dim_asset` | dimension / node | 1 video asset (RAW or EDITED) | Gold | v1 |
| `fact_chunk` | fact / feature row | **1 semantic chunk** | Gold | v1 |
| `bridge_asset_lineage` | bridge / edge | RAW→EDITED pair | Gold | v1 |
| `bridge_chunk_compatibility` | bridge / edge | chunk × compatible-theme | Gold | v1 |
| `dim_keyword_bridge` | bridge | chunk × keyword | Gold | v1 |
| `dim_theme_bridge` | bridge | chunk × theme | Gold | v1 |
| `dim_platform` | dimension | 1 ad platform | Gold | v1.5 |
| `fact_ad_performance` | fact | **1 ad × platform × DAY** | Gold | v1.5 |
| `bridge_ad_chunk` | bridge / edge | ad × chunk (editor's cut) | Gold | v1.5 |
| `fact_extraction_run` | fact (ops) | 1 extraction run | Gold | enhancement |

**11 tables.** (Count excludes the `fct_ad_kpi` / correlation **views** and the v1.5-deferred
`bridge_client_asset_curation` — see §6.)

**Two grains, two first-class facts:**
- `fact_chunk` — grain = **semantic chunk** (the unit of creative value).
- `fact_ad_performance` — grain = **ad × platform × day** (the unit of measured performance).
- Bridged by `bridge_ad_chunk` — composition is an **asserted fact** (editor's cut), not an
  inference.

`dim_client` is the tenancy boundary (ADR-006): one domain = one dimension. It carries
client **operational** attributes (`drive_folder_id`, `landing_ttl_days`, `status`) so those
never overload `dim_asset`.

---

## 3. Relationships & cardinality

| From | To | Cardinality | Meaning |
|------|----|-------------|---------|
| `dim_client` → `dim_asset` | | 1 : N | tenancy — every asset belongs to exactly one client (ADR-006) |
| `dim_asset` → `dim_asset` | self | 1 : N | `parent_asset_id` RAW→EDITED (**discovery only**) |
| `dim_asset` → `fact_chunk` | | 1 : N | one asset fans out to N chunks (in Silver) |
| `fact_chunk` → `bridge_chunk_compatibility` | | 1 : N | mix-and-match adjacency |
| `fact_chunk` → `bridge_asset_lineage` | via asset | N : N | trace chunk to raw source |
| `fact_ad_performance` → `bridge_ad_chunk` | | 1 : N | one ad composed of N chunks |
| `bridge_ad_chunk` → `fact_chunk` | | N : 1 | each bridge row points to one (edited-ad) chunk |
| `fact_ad_performance` → `dim_platform` | | N : 1 | metrics semantics per platform |
| `fact_ad_performance` → `dim_asset` | | N : 1 | only `asset_type='EDITED'` |

> **Client scoping is reached by join, not a stored fact column (ADR-006 / Clean-ERD axis 4):**
> `fact_chunk.asset_id → dim_asset.client_id`. No `client_id` lives on `fact_chunk`; if a
> serving surface needs it pre-joined, it appears on a **VIEW**.

---

## 4. The three traversals that matter

**T1 — Search (v1 north-star):** `fact_chunk` filtered by theme/sentiment/`standalone_score`
(+ VSS embedding similarity, v1.5, BUILT 2026-06-25 — `search_cli.py --semantic`), **scoped to
one client** via `fact_chunk → dim_asset.client_id` (ADR-006).

**T2 — Performance correlation (v1.5):**
`fact_ad_performance → bridge_ad_chunk → fact_chunk` , aligned by chunk **role** via
`int_metric_chunk_alignment`, aggregated **within-platform** at theme/sentiment grain.

**T3 — Mine the library (v1.5):**
`fact_ad_performance → bridge_ad_chunk → fact_chunk(edited) → bridge_asset_lineage → RAW source`,
then candidate pool = `fact_chunk WHERE theme IN (winning) AND standalone_score>=4 AND chunk_id
NOT IN (bridge_ad_chunk)`. This is a **search**, never a metric attribution.

---

## 5. SCD / immutability per table

| Table | Strategy | Note |
|-------|----------|------|
| `dim_client` | SCD0 reference (seed) | immutable `client_id`; descriptive cols hand-curated, rebuilt each run |
| `dim_asset` | append + SCD0 on identity | `asset_id = SHA-256(client_id ':' content_sha256)` → immutable tenant-scoped identity (ADR-006) |
| `fact_chunk` | rebuild from immutable Bronze | non-deterministic source → re-parse, never re-pay |
| `dim_platform` | SCD0 | reference data, rarely changes |
| `fact_ad_performance` | daily snapshot, additive | platforms restate → daily grain is the honest one |
| `bridge_*` | rebuild | derived edges |

---

## 6. What is deliberately NOT in this model (vetoed → v2 / deferred)

- ❌ Proxy performance on RAW (`parent_asset_id` carries **no** metrics — permanent).
- ❌ Causal "chunk caused conversion" anything (no table encodes it; needs swap-one-chunk experiment).
- ❌ Cross-platform pooled metrics (no conformed cross-platform rate column exists by design).
- ❌ Predictive score column / variant-factory output table / RAG store / dedicated vector DB.
- ❌ `fact_ad_performance` ratio columns (ratios live only in the `fct_ad_kpi` view).
- ❌ `client_id` as a stored column on `fact_chunk` (reached by join; serving-view only — axis 4).
- ⏸️ **Asset removal / re-curation tracking — deferred to v1.5 (ADR-006 §F).** When support
  staff remove a video from a client's curated set, that membership change is **OUT for v1**.
  The v1.5 home is `bridge_client_asset_curation` (SCD2 membership of an asset in a client's
  current curated set). **Landing/Bronze stay append-only — removal never deletes Bronze.**
  Named here so the deferral is deliberate, not an accidental gap.
