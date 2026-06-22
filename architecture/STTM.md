# STTM — Source-to-Target Mapping
## Creative Intelligence Pipeline

**Owner:** @data-architect
**Status:** DRAFT — pending review
**Date:** 2026-06-22

> The most genuinely missing artifact found by the doc-gap convene (2026-06-22) — it
> doesn't move any logic, it **records where the already-locked logic lives**, making the
> Bronze-verbatim boundary (`architecture/ADR-003-chunking-in-silver.md`) auditable
> column-by-column. Three binding rules from @data-architect's gate ruling, applied below:
> 1. The Source→Bronze row is deliberately boring — "verbatim / no transform" — the instant
>    a transform expression appears there, that's an ADR-003 violation.
> 2. Array explosion (`next_compatible_themes[]`, keywords, themes) is shown as the
>    Silver→Gold step, never earlier — Gold has no array columns
>    (`architecture/DATA_MODEL.md` §3).
> 3. `bridge_ad_chunk`'s source is the **EDL seed** (editor's asserted cut), not Gemini —
>    kept in its own lane so no one conflates an assertion with an extraction.

---

## How to read this

`Source → Bronze → Silver → Gold`, one block per Gold target. "Transform" describes what
actually happens at that hop; "verbatim" means explicitly no transform.

---

## Target: `bronze_asset_raw` (Bronze)

| Hop | Detail |
|-----|--------|
| Source | Gemini API structured-output response (`responseSchema`) for one video asset |
| Transform | **None — verbatim.** Bronze stores the raw JSON exactly as returned. Only metadata is added: `content_sha256`, `load_ts`, `model_version`, `prompt_version`. |
| Rule enforced | ADR-003: Bronze must stay the verbatim, immutable Gemini response so any re-model is a re-parse, never a re-pay. |

## Target: `silver_chunk` (Silver)

| Hop | Detail |
|-----|--------|
| Source | `bronze_asset_raw` (one Bronze row → N Silver rows, a clean fan-out) |
| Transform | Flatten JSON → one row per semantic chunk (`stg_gemini_raw`, grain = `asset_id` + `chunk_sequence`); filler removed, timestamps normalized, `standalone_score` passed through with a GE range gate (`int_chunk_cleaned`) — `architecture/DATA_MODEL.md` §5 |
| Rule enforced | ADR-003: chunking happens here, not Bronze, not Gold. |

## Target: `dim_asset` (Gold)

| Source field | Bronze/Silver column | Target column | Transform |
|--------------|----------------------|----------------|-----------|
| video bytes (Landing) | — | `asset_id` | SHA-256 of video bytes (identity, not from Gemini) |
| Drive file metadata | — | `asset_name`, `source_uri` | passthrough |
| (not yet specified — see note) | — | `parent_asset_id` | discovery-lineage edge; **mechanism for populating this is not yet defined in any ratified doc** — flagged here rather than invented |
| `silver_chunk` (aggregated) | — | `duration_sec` | derived from chunk boundaries / video metadata |
| near-dup detection | — | `dq_flag` | content-hash collision signal; MEDIUM, no auto-merge (`architecture/DATA_MODEL.md` §4) |

## Target: `fact_chunk` (Gold)

| Source field (Gemini JSON, via Bronze) | Silver column | Target column | Transform |
|------------------------------------------|---------------|-----------------|-----------|
| (Gemini-set boundaries) | `start_ts`/`end_ts` | `start_sec`/`end_sec` | passthrough |
| `transcript_segment` | cleaned `transcript_segment` | `transcript_segment` | filler removed (Silver) |
| `chunk_theme` | `chunk_theme` | `chunk_theme` | passthrough |
| `sentiment` | `sentiment` | `sentiment` | passthrough, enum-gated |
| `standalone_score` | `standalone_score` | `standalone_score` | passthrough, range-gated 1–5 |
| — | — | `embedding` | v1.5 addition, BYO Gemini embedding generated in ELT (`architecture/ADR-005-unified-s3-and-snowflake-serving.md`) — **not** a source-field passthrough |

## Target: `bridge_chunk_compatibility` (Gold)

| Hop | Detail |
|-----|--------|
| Source | `silver_chunk.next_compatible_themes[]` (Gemini JSON field, array) |
| Transform | **Array exploded at Silver→Gold** — one row per chunk per compatible theme. This is the array-explosion hop; no array column survives into Gold (`architecture/DATA_MODEL.md` §3). |

## Target: `bridge_asset_lineage` (Gold)

| Hop | Detail |
|-----|--------|
| Source | `dim_asset.parent_asset_id` (self-referencing) |
| Transform | One row per RAW→EDITED pair found |
| Note | Same open question as `dim_asset.parent_asset_id` above — population mechanism not yet specified. |

## Target: `dim_keyword_bridge` / `dim_theme_bridge` (Gold)

| Hop | Detail |
|-----|--------|
| Source | `silver_chunk` keyword/theme arrays (Gemini JSON fields) |
| Transform | **Array exploded at Silver→Gold** — one row per chunk per keyword/theme, same rule as `bridge_chunk_compatibility` above. |

---

## v1.5 — Performance layer

## Target: `bronze_ad_performance_raw` (Bronze)

| Hop | Detail |
|-----|--------|
| Source | Manual Meta/TikTok CSV export (client-provided) |
| Transform | **None — verbatim.** Append-only, immutable, + `load_ts`, `source_file`, `content_hash`. **Separate Bronze source from `bronze_asset_raw`** — never mixed (`architecture/DATA_MODEL_v1.5_PERFORMANCE.md` §3). |

## Target: `fact_ad_performance` (Gold)

| Hop | Detail |
|-----|--------|
| Source | `bronze_ad_performance_raw` |
| Transform | `stg_meta` + `stg_tiktok` → union (`architecture/STACK_AND_FLOW.md` §2); raw counts only, no ratio derived here |
| `asset_id` join | Manual seed `map_ad_asset.csv` (`ad_id` → `asset_id`), enforced by a dbt `relationships` test — **not** a Gemini-derived field |

## Target: `dim_platform` (Gold)

| Hop | Detail |
|-----|--------|
| Source | Reference/seed data (manually defined: `meta` hook window = 3s, `tiktok` = 6s) |
| Transform | None — static reference table, SCD0 |

## ⚠️ Target: `bridge_ad_chunk` (Gold) — separate lane, NOT Gemini lineage

| Hop | Detail |
|-----|--------|
| Source | **EDL seed (editor's recorded assertion of what's physically in the cut)** — a hand-entered fact, not an LLM extraction |
| Target chunk reference | `chunk_id` → the **edited ad's own** `fact_chunk` rows (the EDITED asset is run through the same Bronze→Silver→Gold chunking pipeline as RAW assets — `architecture/DATA_MODEL_v1.5_PERFORMANCE.md` §4) |
| Match metadata carried | `chunk_role` (`hook`/`body`/`social_proof`/`cta`), `position_in_ad` — per Clean-ERD Doctrine rule 3, a bridge carries its evidence, never silent NULL logic |
| Rule enforced | This lineage is an **assertion**, not an extraction — keep it in its own lane so it is never conflated with the Gemini-derived chunk fields above. |

## Target: `fct_ad_kpi` (view, not a table)

| Hop | Detail |
|-----|--------|
| Source | `fact_ad_performance` raw counts |
| Transform | Every ratio (Hook Rate, Hold Rate, Average Play Time, CTR-Link, CPA, CVR) derived here — the only place ratios exist (`architecture/DATA_MODEL_v1.5_PERFORMANCE.md` §2) |

## Target: `mart_chunk_perf_correlation` (Gold, v1.5)

| Hop | Detail |
|-----|--------|
| Source | `fact_ad_performance → bridge_ad_chunk → fact_chunk`, time-range joined via `int_metric_chunk_alignment` |
| Transform | Aggregated at theme/sentiment/chunk-role grain, **within a single platform**; carries `sample_size` + regime label + `honesty_note` (G1–G4, `architecture/ADR-004-performance-veto-converted.md`) |

---

## Exceptions / open items

- `dim_asset.parent_asset_id` and `bridge_asset_lineage`'s population mechanism is **not
  yet specified** in any ratified doc — flagged here rather than invented. Routes to
  @data-architect when it needs an answer, not resolved by this STTM.
- Both stale-doc TODOs from `architecture/DQD.md` §3 (5th LLM-output gate, row-count
  reconciliation) affect the Bronze→Silver and EDL→`bridge_ad_chunk` hops mapped above —
  this STTM documents the intended lineage; it does not imply those gates are built.

## Change log

- 2026-06-22 — initial draft, cabinet doc-gap convene (@data-architect + @scope-guardian
  gate-approved; see `architecture/DATA_DICTIONARY.md` and `architecture/DQD.md` for the
  sibling docs from the same convene).

---

## Sign-off Gate

| Agent | Status | Reason | Date |
|-------|--------|--------|------|
| @data-architect | ✅ APPROVED (doc-gap convene) | Enforces, does not violate, ADR-003; bridge_ad_chunk kept in its own asserted-fact lane | 2026-06-22 |
| @scope-guardian | ✅ APPROVED (doc-gap convene) | Documents existing lineage already implied across DATA_MODEL/SPEC docs; no new model object | 2026-06-22 |
