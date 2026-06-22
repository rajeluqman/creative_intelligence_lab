-- Ratios derived here ONLY (ratio-of-sums). SPEC §3.
{{ config(materialized='view') }}
with agg as (
    select ad_id, platform_id,
           sum(impressions) impressions, sum(plays_3s) plays_3s, sum(plays_25) plays_25,
           sum(sum_watch_time_sec) watch_sec, sum(play_count) play_count,
           sum(link_clicks) link_clicks, sum(results) results, sum(spend) spend
    from {{ ref('fact_ad_performance') }} group by 1,2
)
select ad_id, platform_id,
    plays_3s::double    / nullif(impressions,0) as hook_rate,
    plays_25::double    / nullif(plays_3s,0)    as hold_rate_25,
    watch_sec::double   / nullif(play_count,0)  as avg_play_time_sec,
    link_clicks::double / nullif(impressions,0) as ctr_link,
    spend::double       / nullif(results,0)     as cpa,
    results::double     / nullif(link_clicks,0) as cvr
from agg
