# DATA DICTIONARY — Creative Intelligence Pipeline
## Business-facing glossary for the Gold serving layer

**Owner:** @data-architect
**Status:** DRAFT — pending review
**Date:** 2026-06-22
**Audience:** marketing/creative team and Power BI consumers of the Snowflake Cortex
serving veneer (`architecture/ADR-005-unified-s3-and-snowflake-serving.md`) — a different
audience, at a different altitude, than `architecture/DATA_MODEL.md` (structural/FK/grain)
or `architecture/ERD_consolidated.md` (cardinality/SCD).

> **Precedence rule (binding):** if this dictionary ever disagrees with
> `architecture/ERD_consolidated.md` or `architecture/DATA_MODEL.md` on a column's
> type, range, or existence, **the ERD/DATA_MODEL wins.** This doc is generated *from*
> the model; it is never authoritative *over* it. Per @data-architect's gate ruling
> (2026-06-22): a dictionary that overrides the model is a governance inversion.

---

## `dim_asset` — one row per creative video (RAW or EDITED)

| Column | Business meaning |
|--------|-------------------|
| `asset_id` | Unique ID for the video — a content hash, so two uploads of the exact same file always get the same ID (this is how near-duplicates are caught). |
| `parent_asset_id` | If this video was cut down from a raw source, points to that source. **For finding related footage only — never used to attribute performance.** |
| `asset_name` | Original filename. |
| `asset_type` | `RAW` (untouched source footage) or `EDITED` (a finished ad). |
| `duration_sec` | Length of the video. |
| `source_uri` | Where the original file lives (for playback) — not the analytical data itself. |
| `dq_flag` | Flags a likely near-duplicate of another asset. Informational only — assets are never auto-merged. |

## `fact_chunk` — one row per semantic "beat" inside a video

This is the core inventory marketers search against.

| Column | Business meaning |
|--------|-------------------|
| `chunk_id` | Unique ID for this beat. |
| `asset_id` | Which video this beat came from. |
| `chunk_sequence` | Its order within that video. |
| `start_sec` / `end_sec` | Where in the video this beat starts/ends (for playback seek). |
| `transcript_segment` | The cleaned dialogue/voiceover for this beat. |
| `chunk_theme` | What kind of beat this is — Hook, Problem, Solution, Social Proof, CTA, etc. |
| `sentiment` | The emotional tone of the beat. |
| `standalone_score` | **1–5: how safe is this beat to reuse on its own**, outside its original ad. This is the field that answers "can I just grab this clip for a new ad?" |
| `embedding` | (v1.5) Vector representation used for semantic similarity search — not human-readable, not for direct business consumption. |

## `bridge_chunk_compatibility` — which beats can follow which

| Column | Business meaning |
|--------|-------------------|
| `chunk_id` | The beat you're starting from. |
| `compatible_theme` | A theme that can validly come *next* without the message feeling disjointed. |
| `theme_match_score` | Optional strength-of-fit ranking. |

This table is the literal mechanism behind "assemble a new ad from compatible beats"
without producing Frankenstein content.

## `bridge_asset_lineage` — which edited ad came from which raw source

| Column | Business meaning |
|--------|-------------------|
| `parent_asset_id` | The raw source video. |
| `child_asset_id` | The edited ad cut from it. |

Navigation only — "find more footage like this winning edit." **Never** used to credit a
raw clip with a finished ad's performance.

## `dim_keyword_bridge` / `dim_theme_bridge` — searchable tags per beat

One row per beat per keyword/theme it carries. This is what lets a marketer filter "show
me all Hook beats mentioning [keyword]."

---

## v1.5 — Performance layer (winning ads only)

## `dim_platform`

| Column | Business meaning |
|--------|-------------------|
| `platform_id` | Internal ID. |
| `platform_name` | `meta` or `tiktok`. |
| `hook_window_sec` | How many seconds count as "the hook" on this platform (Meta = 3s, TikTok = 6s) — platforms measure this differently, never pooled. |
| `hold_milestones[]` | The retention checkpoints this platform reports (25%/50%/75%/100% watched). |

## `fact_ad_performance` — daily performance of a winning ad, per platform

| Column | Business meaning |
|--------|-------------------|
| `ad_id` | The platform's own ID for the creative that ran. |
| `platform_id` | Which platform this row is for. |
| `perf_date` | The day this snapshot covers. |
| `asset_id` | Which edited ad this is (always an `EDITED` asset — performance is never attached to raw footage). |
| `impressions` | Times shown. |
| `plays_3s` / `25` / `50` / `75` / `100` | How many viewers kept watching to each checkpoint. |
| `sum_watch_time_sec`, `play_count` | Raw counts only — **do not divide these yourself**; the ratio (Average Play Time) is derived in `fct_ad_kpi` below. |
| `link_clicks`, `results`, `spend` | Raw counts/spend, same rule — ratios live in `fct_ad_kpi`. |

**Every ratio metric (Hook Rate, Hold Rate, CTR-Link, CPA, CVR, Average Play Time) is
derived in the `fct_ad_kpi` view — none of them are stored columns here.** Storing a
ratio breaks re-aggregation (sum-of-ratios ≠ ratio-of-sums) — see
`architecture/DATA_MODEL_v1.5_PERFORMANCE.md` §2.

## `bridge_ad_chunk` — which beats are physically in a winning ad

| Column | Business meaning |
|--------|-------------------|
| `ad_id` | The winning ad. |
| `chunk_id` | A beat that's in it (the ad's **own** chunk rows, on the ad's own timeline — not the raw source's). |
| `chunk_role` | What job this beat does in the ad: `hook` / `body` / `social_proof` / `cta`. |
| `position_in_ad` | Order in the final cut. |

This is the editor's own record of what's in the ad — a recorded fact, not a guess.

## `fct_ad_kpi` (view, not a table) — the ratio metrics

Hook Rate, Hold Rate, Average Play Time, CTR (Link), CPA, CVR — every ratio a marketer
would ask for, computed from `fact_ad_performance`'s raw counts. **This is the only place
ratios exist.** If a number you need isn't here, it hasn't been derived yet — it is not
hiding as a stored column elsewhere.

## Correlation mart — "which themes show up more in winners"

Honesty framing is mandatory on every reading from this mart: it is a **within-winners,
within-platform, descriptive correlation**, never a causal or "this chunk drove the
result" claim, and is suppressed entirely below 5 ads in a comparison group. See
`architecture/ADR-004-performance-veto-converted.md` G1–G4 before interpreting any number
from this mart.

---

## Sign-off Gate

| Agent | Status | Reason | Date |
|-------|--------|--------|------|
| @data-architect | ✅ APPROVED (doc-gap convene) | Distinct audience/purpose from DATA_MODEL §4 / ERD; precedence rule + view-not-column labelling applied | 2026-06-22 |
| @scope-guardian | ✅ APPROVED (doc-gap convene) | Describes existing columns only; any column gap found during drafting routes back through @data-architect, not absorbed here | 2026-06-22 |
