-- Position-aligned mapping: each funnel metric -> the ONE owning chunk. SPEC §4.
-- Time-anchored metrics (hook/hold) via range join on the EDITED ad's timeline;
-- role-anchored metric (ctr_link) via chunk_role='cta'. Deterministic tie-break +
-- coverage_confidence. Exactly one chunk per (ad,platform,metric) = the double-count guard.
with ad_platform as (
    select distinct ad_id, platform_id from {{ ref('fact_ad_performance') }}
),
anchors as (
    -- hook anchor = platform hook window (Meta 3s / TikTok 6s, from dim_platform)
    select ap.ad_id, ap.platform_id, 'hook_rate' as metric_name,
           pl.hook_window_sec::double as anchor_sec
    from ad_platform ap
    join {{ ref('dim_platform') }} pl using (platform_id)
    union all
    -- hold anchor = pct * edited-asset duration
    select ap.ad_id, ap.platform_id, m.metric_name, m.pct * a.duration_sec as anchor_sec
    from ad_platform ap
    join {{ ref('map_ad_asset') }} ma using (ad_id)
    join {{ ref('dim_asset') }} a on a.asset_id = ma.asset_id
    cross join (values ('hold_rate_25', 0.25)) m(metric_name, pct)
),
time_aligned as (
    select an.ad_id, an.platform_id, an.metric_name, b.chunk_id, b.chunk_role,
           case when an.anchor_sec >= b.start_sec and an.anchor_sec < b.end_sec
                then 'HIGH' else 'MEDIUM' end as coverage_confidence,
           row_number() over (
             partition by an.ad_id, an.platform_id, an.metric_name
             order by case when an.anchor_sec >= b.start_sec and an.anchor_sec < b.end_sec then 0 else 1 end,
                      (least(b.end_sec, an.anchor_sec) - greatest(b.start_sec, an.anchor_sec)) desc,
                      b.position_in_ad asc
           ) as pick
    from anchors an
    join {{ ref('bridge_ad_chunk') }} b using (ad_id)
),
role_aligned as (
    select ap.ad_id, ap.platform_id, 'ctr_link' as metric_name, b.chunk_id, b.chunk_role,
           'HIGH' as coverage_confidence,
           row_number() over (partition by ap.ad_id, ap.platform_id order by b.position_in_ad) as pick
    from ad_platform ap
    join {{ ref('bridge_ad_chunk') }} b on b.ad_id = ap.ad_id and b.chunk_role = 'cta'
)
select ad_id, platform_id, metric_name, chunk_id, chunk_role, coverage_confidence
from time_aligned where pick = 1
union all
select ad_id, platform_id, metric_name, chunk_id, chunk_role, coverage_confidence
from role_aligned where pick = 1
