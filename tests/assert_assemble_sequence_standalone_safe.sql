-- Singular dbt test — SPEC_v1_search.md §4 "assembler safety" row.
-- Asserts every chunk RETURNED BY the leg (b) mix-and-match query (analyses/assemble_sequence.sql
-- / scripts/search_cli.py --assemble) has standalone_score >= 4. This re-runs the actual
-- assembler predicate (not a broader claim about the whole compatibility graph — the graph in
-- bridge_chunk_compatibility legitimately contains edges to low-score chunks; that's fine,
-- because the assembler's own `standalone_score >= 4` filter is what's supposed to exclude them
-- before they ever reach a marketer). A failing row here means that filter has a gap somewhere
-- (e.g. dropped from one hop of the 3-step chain) and the anti-Frankenstein rule (SPEC §3.1) has
-- been violated.
--
-- dbt singular test convention: a model that returns 0 rows = pass, >0 rows = fail.
with assembled as (
    select
        h.chunk_id as hook_chunk, h.standalone_score as hook_score,
        n.chunk_id as next_chunk, n.standalone_score as next_score
    from {{ ref('fact_chunk') }} h
    join {{ ref('bridge_chunk_compatibility') }} bc on bc.chunk_id = h.chunk_id
    join {{ ref('fact_chunk') }} n
         on n.chunk_theme = bc.compatible_theme
        and n.chunk_id <> h.chunk_id
    where h.chunk_theme = 'Hook'
      and h.standalone_score >= 4
      and n.standalone_score >= 4
)
select * from assembled
where hook_score < 4 or next_score < 4
