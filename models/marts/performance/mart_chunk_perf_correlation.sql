-- Surfaced insight. Within-platform, within-winners, sample-gated. SPEC §6.
with base as (
    select platform_id, metric_name, 'chunk_theme' as feature_dim,
           chunk_theme as feature_value, ad_id, metric_value
    from {{ ref('fct_ad_metric_chunk') }} where metric_value is not null
),
grouped as (
    select platform_id, metric_name, feature_dim, feature_value,
           count(distinct ad_id) as n_ads, median(metric_value) as median_metric
    from base group by 1,2,3,4
)
select *,
    rank() over (partition by platform_id, metric_name order by median_metric desc) as rank_in_platform,
    case when n_ads < 5 then 'BLOCK' when n_ads < 12 then 'DIRECTIONAL' else 'SUGGESTIVE' end as evidence_regime,
    'Among winning ads only - within-platform ranking, correlation not causation' as honesty_note
from grouped
