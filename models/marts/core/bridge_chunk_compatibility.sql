-- Mix-and-match adjacency. Explodes next_compatible_themes[].
{{ config(**silver_gold_config('gold', 'bridge_chunk_compatibility')) }}
select
    chunk_id,
    unnest(next_compatible_themes) as compatible_theme,
    cast(null as decimal) as theme_match_score
from {{ ref('int_chunk_cleaned') }}
