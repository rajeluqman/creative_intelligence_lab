# ERD — CONSOLIDATED DATA MODEL (v1 + v1.5)

**Status:** Consolidated reference · authority = `DATA_MODEL.md` + `DATA_MODEL_v1.5_PERFORMANCE.md`.
**Paradigm:** asset-lineage **graph + chunk feature store** + a descriptive **within-winners
performance-correlation** layer. NOT a Kimball star.

---

## 1. Entity map (the whole model on one screen)

```
                                  ┌──────────────────────────────┐
                          ┌──────►│          dim_asset           │◄────┐  parent_asset_id
            asset_type    │       │  PK asset_id (SHA-256)       │─────┘  (self-ref, RAW→EDITED,
            = RAW|EDITED  │       │     parent_asset_id (FK self)│        DISCOVERY ONLY)
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
   └──────────────────────────┘   │     embedding (v1.5, VSS)    │   └──────────────────────────────┘
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

**Two grains, two first-class facts:**
- `fact_chunk` — grain = **semantic chunk** (the unit of creative value).
- `fact_ad_performance` — grain = **ad × platform × day** (the unit of measured performance).
- Bridged by `bridge_ad_chunk` — composition is an **asserted fact** (editor's cut), not an
  inference.

---

## 3. Relationships & cardinality

| From | To | Cardinality | Meaning |
|------|----|-------------|---------|
| `dim_asset` → `dim_asset` | self | 1 : N | `parent_asset_id` RAW→EDITED (**discovery only**) |
| `dim_asset` → `fact_chunk` | | 1 : N | one asset fans out to N chunks (in Silver) |
| `fact_chunk` → `bridge_chunk_compatibility` | | 1 : N | mix-and-match adjacency |
| `fact_chunk` → `bridge_asset_lineage` | via asset | N : N | trace chunk to raw source |
| `fact_ad_performance` → `bridge_ad_chunk` | | 1 : N | one ad composed of N chunks |
| `bridge_ad_chunk` → `fact_chunk` | | N : 1 | each bridge row points to one (edited-ad) chunk |
| `fact_ad_performance` → `dim_platform` | | N : 1 | metrics semantics per platform |
| `fact_ad_performance` → `dim_asset` | | N : 1 | only `asset_type='EDITED'` |

---

## 4. The three traversals that matter

**T1 — Search (v1 north-star):** `fact_chunk` filtered by theme/sentiment/`standalone_score`
(+ VSS embedding similarity in v1.5).

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
| `dim_asset` | append + SCD0 on identity | asset_id is content hash → immutable identity |
| `fact_chunk` | rebuild from immutable Bronze | non-deterministic source → re-parse, never re-pay |
| `dim_platform` | SCD0 | reference data, rarely changes |
| `fact_ad_performance` | daily snapshot, additive | platforms restate → daily grain is the honest one |
| `bridge_*` | rebuild | derived edges |

---

## 6. What is deliberately NOT in this model (vetoed → v2)

- ❌ Proxy performance on RAW (`parent_asset_id` carries **no** metrics — permanent).
- ❌ Causal "chunk caused conversion" anything (no table encodes it; needs swap-one-chunk experiment).
- ❌ Cross-platform pooled metrics (no conformed cross-platform rate column exists by design).
- ❌ Predictive score column / variant-factory output table / RAG store / dedicated vector DB.
- ❌ `fact_ad_performance` ratio columns (ratios live only in the `fct_ad_kpi` view).
