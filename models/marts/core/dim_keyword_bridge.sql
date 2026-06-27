{{ config(**silver_gold_config('gold', 'dim_keyword_bridge')) }}
select chunk_id, unnest(keywords) as keyword
from {{ ref('int_chunk_cleaned') }}
