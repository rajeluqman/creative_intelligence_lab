-- The three demo queries (full text: SPEC_v1.5_performance_marts.md §8).
-- 1) v1 north-star search   2) Hook-theme x Hook Rate correlation   3) mine unused RAW chunks
-- Run with: dbt compile -s demo_queries  (then read target/compiled/...)

-- =====================================================================================
-- 1) v1 NORTH-STAR SEARCH — architecture/SPEC_v1_search.md §2.2, adapted to real Gold data.
-- Reusable clips matching a theme + sentiment + free-text, ranked by safety.
-- Real-data note (not a bug): the spec's literal example (chunk_theme='Hook',
-- sentiment='energetic', contains='jimat elektrik') matches close to nothing against the real
-- voltecx data — 'Hook' is a thin 1-row slice of 50 distinct freeform chunk_theme strings
-- Gemini emits (see chunk_theme vocabulary-drift finding, PROJECT_STATUS.md 2026-06-25), and
-- 'jimat elektrik' does not literally occur in the transcripts. Swapped to real high-volume
-- values so this query actually returns rows: chunk_theme='Problem' (50 rows),
-- sentiment='frustrated' (34 rows), contains='minyak' (49 rows) — same predicate shape as the
-- spec, just real literals. CLI equivalent: scripts/search_cli.py --theme Problem
-- --sentiment frustrated --min-score 4 --contains minyak
select
    c.chunk_id, c.asset_id, a.asset_name,
    c.start_sec, c.end_sec, c.standalone_score,
    c.chunk_theme, c.sentiment, c.transcript_segment
from {{ ref('fact_chunk') }} c
join {{ ref('dim_asset') }} a using (asset_id)
where c.chunk_theme = 'Problem'
  and c.sentiment   = 'frustrated'
  and c.standalone_score >= 4
  and c.transcript_segment ilike '%minyak%'   -- v1.5: replace/augment with FTS or VSS
order by c.standalone_score desc, c.start_sec

-- =====================================================================================
-- 2) HOOK-THEME x HOOK-RATE CORRELATION — TODO, BLOCKED ON v1.5 PERFORMANCE DATA.
-- Needs fact_ad_performance (currently a `where 1=0` stub, see PROJECT_STATUS.md) joined back
-- to fact_chunk via bridge_ad_chunk to correlate chunk_theme='Hook' usage against an actual
-- hook-rate performance metric. No performance rows exist yet — do not attempt this until
-- v1.5 performance marts land (architecture/SPEC_v1.5_performance_marts.md). Out of scope for
-- the v1 search/mix-and-match demo (this task).

-- =====================================================================================
-- 3) MINE UNUSED RAW CHUNKS — TODO, BLOCKED ON v1.5 PERFORMANCE DATA.
-- Needs map_ad_asset / edit_decision_list reconciliation (DQD.md §3 item 3, still OPEN) to
-- know which RAW-asset chunks were never selected into any EDITED ad, so they can be
-- surfaced as candidate "unused footage" for the marketer. Same v1.5 dependency as above —
-- out of scope for the v1 search/mix-and-match demo (this task).
