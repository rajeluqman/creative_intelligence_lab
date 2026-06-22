-- 1 ad x platform x metric -> metric value + mapped chunk features. SPEC §5.
select
    al.ad_id, al.platform_id, al.metric_name,
    case al.metric_name
        when 'hook_rate'    then k.hook_rate
        when 'hold_rate_25' then k.hold_rate_25
        when 'ctr_link'     then k.ctr_link
    end as metric_value,
    al.chunk_id, al.chunk_role, al.coverage_confidence,
    fc.chunk_theme, fc.sentiment, fc.standalone_score
from {{ ref('int_metric_chunk_alignment') }} al
join {{ ref('fct_ad_kpi') }} k using (ad_id, platform_id)
join {{ ref('fact_chunk') }} fc on fc.chunk_id = al.chunk_id
where al.coverage_confidence in ('HIGH','MEDIUM')
