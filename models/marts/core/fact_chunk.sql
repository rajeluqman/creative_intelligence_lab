-- Feature row. GRAIN = one semantic chunk. ADR-002.
select
    chunk_id, asset_id, chunk_sequence,
    start_sec, end_sec, transcript_segment,
    chunk_theme, sentiment, standalone_score
from {{ ref('int_chunk_cleaned') }}
