-- Editor's asserted cut: ad -> chunk + role + position (the v1.5 unlock). SPEC §2.
-- Captured as a manual Edit Decision List seed at 3-15 ads (gap-check B2). The EDL is
-- the editor's RECORDED assertion of what is physically in the cut — a fact, not an
-- inference (ADR-004). asset_id resolves from the chunk's own fact_chunk row.
select
    edl.ad_id,
    edl.chunk_id,
    fc.asset_id,
    edl.chunk_role,
    edl.position_in_ad,
    edl.start_sec,
    edl.end_sec
from {{ ref('edit_decision_list') }} edl
join {{ ref('fact_chunk') }} fc on fc.chunk_id = edl.chunk_id
