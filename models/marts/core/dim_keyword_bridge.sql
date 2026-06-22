select chunk_id, unnest(keywords) as keyword
from {{ ref('int_chunk_cleaned') }}
