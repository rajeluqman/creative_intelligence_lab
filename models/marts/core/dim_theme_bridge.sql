{{ config(**silver_gold_config('gold', 'dim_theme_bridge')) }}
select chunk_id, chunk_theme as theme
from {{ ref('int_chunk_cleaned') }}
