-- GRAIN: 1 edited-ad x 1 platform x 1 DAY. Raw counts only. ADR-004 / SPEC §2.
select
    u.ad_id,
    p.platform_id,
    u.perf_date,
    m.asset_id,
    u.impressions, u.plays_3s, u.plays_25, u.plays_50, u.plays_75, u.plays_100,
    u.sum_watch_time_sec, u.play_count, u.link_clicks, u.results, u.spend,
    current_timestamp as load_ts
from {{ ref('int_ad_perf_unioned') }} u
join {{ ref('dim_platform') }} p on p.platform_name = u.platform_name
join {{ ref('map_ad_asset') }} m on m.ad_id = u.ad_id
