-- Mix-and-match adjacency. Explodes next_compatible_themes[].
select
    chunk_id,
    unnest(next_compatible_themes) as compatible_theme,
    cast(null as decimal) as theme_match_score
from {{ ref('int_chunk_cleaned') }}
