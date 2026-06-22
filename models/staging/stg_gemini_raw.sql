-- Flatten verbatim Gemini JSON -> one row per semantic chunk.
-- Full logic: architecture/SPEC_v1.5_performance_marts.md §1 + DATA_MODEL.md §5
select
    asset_id,
    chunk_sequence,
    chunk_id,
    start_sec, end_sec,
    transcript_segment, chunk_theme, sentiment, standalone_score,
    next_compatible_themes,   -- array; exploded downstream
    keywords,                 -- array; exploded downstream
    model_version, prompt_version
from {{ source('bronze', 'bronze_asset_raw') }}
