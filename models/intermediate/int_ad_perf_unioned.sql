-- Meta UNION TikTok + platform tag (v1.5).
select 'meta'   as platform_name, * from {{ ref('stg_meta_perf') }}
union all
select 'tiktok' as platform_name, * from {{ ref('stg_tiktok_perf') }}
