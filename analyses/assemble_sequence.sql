-- Leg (b) mix-and-match reference query — SPEC_v1_search.md §3.2.
-- Candidate Hook -> next-chunk pairs that are safe (standalone_score >= 4 at both ends) and
-- theme-compatible via the bridge_chunk_compatibility adjacency. This is the 2-step seed;
-- scripts/search_cli.py's `--assemble` flag chains this join twice more (fixed 3-step
-- Hook->Body->CTA per SPEC §3.3 — v1 deliberately stays fixed-length, not a recursive N-step
-- walk; that's a named v1.5 enhancement, SPEC §3.3/§5).
--
-- Run with: dbt compile -s assemble_sequence  (then read target/compiled/.../assemble_sequence.sql)
select
    h.chunk_id           as hook_chunk,   h.asset_id as hook_asset,  h.transcript_segment as hook_text,
    n.chunk_id           as next_chunk,   n.asset_id as next_asset,  n.chunk_theme as next_theme,
    n.transcript_segment as next_text
from {{ ref('fact_chunk') }} h
join {{ ref('bridge_chunk_compatibility') }} bc on bc.chunk_id = h.chunk_id
join {{ ref('fact_chunk') }} n
     on n.chunk_theme = bc.compatible_theme
    and n.chunk_id <> h.chunk_id
where h.chunk_theme = 'Hook'
  and h.standalone_score >= 4
  and n.standalone_score >= 4
order by h.chunk_id
