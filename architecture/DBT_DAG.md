# dbt PROJECT STRUCTURE & DAG — Creative Intelligence Pipeline

**Status:** model-level lineage (v1 + v1.5) · authority = `STACK_AND_FLOW.md`, `ERD_consolidated.md`,
`SPEC_v1.5_performance_marts.md`. **Engine:** dbt-duckdb.

---

## 1. Project tree

```
creative_intelligence/
├── dbt_project.yml
├── packages.yml                     # dbt_utils, dbt_expectations
├── seeds/
│   ├── map_ad_asset.csv             # ad_id → asset_id (manual, v1.5)
│   └── dim_platform.csv             # meta=3s, tiktok=6s windows
├── models/
│   ├── staging/
│   │   ├── _sources.yml             # bronze_asset_raw, bronze_ad_performance_raw
│   │   ├── stg_gemini_raw.sql       # flatten Gemini JSON → 1 row per chunk
│   │   ├── stg_meta_perf.sql        # conform Meta funnel columns        (v1.5)
│   │   ├── stg_tiktok_perf.sql      # conform TikTok funnel columns      (v1.5)
│   │   └── _staging.yml             # schema tests
│   ├── intermediate/
│   │   ├── int_chunk_cleaned.sql    # filler removal, ts normalize, scoring
│   │   ├── int_ad_perf_unioned.sql  # meta ∪ tiktok + platform           (v1.5)
│   │   └── int_metric_chunk_alignment.sql  # metric → owning chunk (time-range join, v1.5)
│   └── marts/
│       ├── core/                    # the graph + feature store (v1)
│       │   ├── dim_asset.sql
│       │   ├── fact_chunk.sql
│       │   ├── bridge_asset_lineage.sql
│       │   ├── bridge_chunk_compatibility.sql
│       │   ├── dim_keyword_bridge.sql
│       │   ├── dim_theme_bridge.sql
│       │   └── fact_extraction_run.sql       # telemetry (enhancement)
│       ├── performance/             # v1.5
│       │   ├── dim_platform.sql
│       │   ├── fact_ad_performance.sql
│       │   ├── bridge_ad_chunk.sql
│       │   ├── fct_ad_kpi.sql                 # view: ratios
│       │   ├── fct_ad_metric_chunk.sql
│       │   └── mart_chunk_perf_correlation.sql
│       └── _marts.yml               # tests incl. honesty gates
├── great_expectations/              # suites per layer (run outside dbt)
└── analyses/
    └── demo_queries.sql             # the 3 north-star / correlation / mining queries
```

---

## 2. The DAG (node-by-node lineage)

```
SEEDS                STAGING                  INTERMEDIATE                MARTS (Gold)
═════                ═══════                  ════════════                ════════════

                                                                   ┌─► dim_asset ─────────────┐
bronze_asset_raw ──► stg_gemini_raw ──► int_chunk_cleaned ─────────┤                          │
   (source)                                       │                ├─► fact_chunk ◄───────────┤
                                                  │                │      │   │   │           │
                                                  │                │      │   │   └─► bridge_chunk_compatibility
                                                  │                │      │   └─────► dim_keyword_bridge
                                                  │                │      └─────────► dim_theme_bridge
                                                  └────────────────┴─► bridge_asset_lineage ◄─┘
                                                                       (dim_asset self-join)

bronze_asset_raw ──► (ops fields) ─────────────────────────────────► fact_extraction_run
   (source)                                                              (tokens/cost/latency)

──────────────────────────────────── v1.5 PERFORMANCE ────────────────────────────────────

dim_platform(seed) ───────────────────────────────────────────────► dim_platform
map_ad_asset(seed) ──────────────────────────────────┐
                                                      │
bronze_ad_performance_raw ─► stg_meta_perf  ──┐       │
   (source, Meta CSV)                         ├─► int_ad_perf_unioned ─► fact_ad_performance
bronze_ad_performance_raw ─► stg_tiktok_perf ─┘                              │  ▲
   (source, TikTok CSV)                                                      │  │ (asset_id, EDITED-only)
                                                                             │  └── dim_asset
                                            (editor's cut, manual/derived)   │
                                            bridge_ad_chunk ─────────────────┤
                                                  │  ▲ chunk_id              │
                                                  │  └── fact_chunk          │
                                                  ▼                          ▼
                                         int_metric_chunk_alignment ◄── dim_platform
                                                  │   (time-range join: metric → 1 chunk)
                                                  ▼
                          fct_ad_kpi ──────► fct_ad_metric_chunk ──► mart_chunk_perf_correlation
                          (view, ratios)          │                        │
                                                  │                        └─► (Python post-step:
                                                  │                             Mann-Whitney + Bonferroni
                                                  │                             for SUGGESTIVE tier)
                                                  ▼
                                         analyses/demo_queries.sql  (serving)
```

---

## 3. Materialization & tests per model

| Model | Matl. | Layer | Key tests | Ver |
|-------|-------|-------|-----------|-----|
| `stg_gemini_raw` | view | staging | `unique(asset_id,chunk_sequence)`, `not_null(chunk_id)` | v1 |
| `int_chunk_cleaned` | view | int | `dbt_expectations` range `standalone_score` 1–5 | v1 |
| `dim_asset` | table | mart | `unique(asset_id)`, `accepted_values(asset_type)` | v1 |
| `fact_chunk` | table (external) | mart | `unique(chunk_id)`, `relationships`→dim_asset | v1 |
| `bridge_asset_lineage` | table | mart | FK both sides → dim_asset | v1 |
| `bridge_chunk_compatibility` | table | mart | FK chunk_id → fact_chunk | v1 |
| `dim_keyword_bridge`/`dim_theme_bridge` | table | mart | FK chunk_id | v1 |
| `fact_extraction_run` | table | mart | `not_null(run_id, asset_id)` | enh |
| `stg_meta_perf`/`stg_tiktok_perf` | view | staging | conformed-column not_null | v1.5 |
| `int_ad_perf_unioned` | view | int | `accepted_values(platform)` | v1.5 |
| `dim_platform` | table (seed) | mart | `unique(platform_id)` | v1.5 |
| `fact_ad_performance` | table | mart | counts/spend ≥0, **asset EDITED-only**, every ad→≥1 chunk | v1.5 |
| `bridge_ad_chunk` | table | mart | `accepted_values(chunk_role)`, FK chunk_id+ad_id | v1.5 |
| `int_metric_chunk_alignment` | view | int | **exactly 1 chunk per (ad,platform,metric)**, LOW excluded | v1.5 |
| `fct_ad_kpi` | view | mart | rates ∈ [0,1] | v1.5 |
| `fct_ad_metric_chunk` | table | mart | **G4 no double-count** | v1.5 |
| `mart_chunk_perf_correlation` | table | mart | **G3 n<5 = BLOCK**, `honesty_note` not_null | v1.5 |

**Honesty gates (G1/G2/G3/G4)** are structural in `mart_chunk_perf_correlation` +
`fct_ad_metric_chunk` — release blockers owned by @data-quality-steward (see SPEC §7).

---

## 4. Run order (dbt selectors)

```bash
# v1 only (search demo ships first)
dbt build --select staging.stg_gemini_raw+ marts.core

# v1.5 add-on (after v1 is green)
dbt seed                                    # map_ad_asset, dim_platform
dbt build --select staging.stg_meta_perf+ staging.stg_tiktok_perf+ marts.performance
python scripts/significance_post_step.py    # Mann-Whitney + Bonferroni on SUGGESTIVE rows
```
