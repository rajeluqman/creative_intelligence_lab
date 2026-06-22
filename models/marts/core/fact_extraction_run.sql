-- Operational telemetry (enhancement): tokens/cost/latency/confidence.
select
    cast(null as varchar) as run_id,
    asset_id,
    model_version, prompt_version,
    cast(null as bigint)  as tokens_in,
    cast(null as bigint)  as tokens_out,
    cast(null as decimal) as api_cost,
    cast(null as decimal) as processing_time_sec,
    cast(null as integer) as retry_count,
    cast(null as decimal) as extraction_confidence
from {{ ref('stg_gemini_raw') }}
where 1 = 0   -- stub: populate from the extraction script's run log
