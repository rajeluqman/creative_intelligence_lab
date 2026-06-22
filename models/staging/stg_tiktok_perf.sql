-- Conform TikTok funnel columns to the canonical schema (v1.5).
select
    ad_id, perf_date,
    impressions, plays_3s, plays_25, plays_50, plays_75, plays_100,
    sum_watch_time_sec, play_count, link_clicks, results, spend
from {{ source('bronze', 'bronze_ad_performance_raw') }}
where platform_native = 'tiktok'
