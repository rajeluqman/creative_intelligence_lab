select chunk_id, chunk_theme as theme
from {{ ref('int_chunk_cleaned') }}
