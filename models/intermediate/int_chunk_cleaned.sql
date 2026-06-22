-- Filler removal, timestamp normalize, score passthrough. (Silver, ADR-003)
select
    chunk_id, asset_id, chunk_sequence,
    start_sec, end_sec, transcript_segment,
    chunk_theme, sentiment, standalone_score,
    next_compatible_themes, keywords
from {{ ref('stg_gemini_raw') }}
