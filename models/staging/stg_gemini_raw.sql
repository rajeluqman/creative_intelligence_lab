-- Flatten verbatim Gemini JSON -> one row per semantic chunk.
-- Full logic: architecture/SPEC_v1.5_performance_marts.md §1 + DATA_MODEL.md §5
-- Bronze is asset-grain (one row per asset, raw_response = the verbatim Gemini JSON envelope,
-- untouched — ADR-003). The explosion into one row per chunk happens HERE, at this hop, per
-- ADR-003 Rationale 2 ("one Bronze blob -> N Silver rows is a clean fan-out") and the grain
-- this model declares (asset_id + chunk_sequence, DATA_MODEL §5). chunk_id is generated here,
-- deterministically, from asset_id + position — re-parsing the same frozen Bronze row always
-- yields the same chunk_id (reproducibility, ADR-003 Rationale 4).
select
    asset_id,
    asset_id || '_' || lpad(chunk_sequence::varchar, 3, '0')   as chunk_id,
    chunk_sequence,
    (chunk ->> 'start_sec')::double                            as start_sec,
    (chunk ->> 'end_sec')::double                              as end_sec,
    chunk ->> 'transcript_segment'                             as transcript_segment,
    chunk ->> 'chunk_theme'                                    as chunk_theme,
    chunk ->> 'sentiment'                                      as sentiment,
    (chunk ->> 'standalone_score')::integer                    as standalone_score,
    cast(chunk -> 'next_compatible_themes' as varchar[])       as next_compatible_themes,  -- array; exploded downstream (Gold)
    cast(chunk -> 'keywords' as varchar[])                     as keywords,                -- array; exploded downstream (Gold)
    model_version, prompt_version
from {{ source('bronze', 'bronze_asset_raw') }},
    unnest(cast(json_extract(raw_response, '$.chunks') as json[])) with ordinality as t(chunk, chunk_sequence)
order by asset_id, chunk_sequence
