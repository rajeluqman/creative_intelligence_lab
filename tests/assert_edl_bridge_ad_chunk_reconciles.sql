-- Singular dbt test — DQD.md §3 item 2 / PROJECT_STATUS.md finding #3 (HIGH, OPEN until now).
-- bridge_ad_chunk.sql INNER JOINs edit_decision_list -> fact_chunk. An EDL row whose chunk_id is
-- absent from fact_chunk (a stale/typo'd manual entry — EDL is hand-entered, gap-check B2) would
-- silently vanish from that join instead of failing loudly. This re-derives exactly which EDL
-- rows the inner join would drop and fails if there are any, so a future hand-entered EDL row
-- referencing a chunk_id that doesn't exist in fact_chunk is caught here, not lost silently.
--
-- dbt singular test convention: a model that returns 0 rows = pass, >0 rows = fail.
select edl.ad_id, edl.chunk_id, edl.position_in_ad
from {{ ref('edit_decision_list') }} edl
left join {{ ref('fact_chunk') }} fc on fc.chunk_id = edl.chunk_id
where fc.chunk_id is null
