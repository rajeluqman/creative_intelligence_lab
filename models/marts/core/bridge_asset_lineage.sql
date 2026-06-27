-- RAW -> EDITED edge. Navigation only; NEVER carries metrics. ADR-002/004.
{{ config(**silver_gold_config('gold', 'bridge_asset_lineage')) }}
select asset_id as parent_asset_id, asset_id as child_asset_id
from {{ ref('dim_asset') }}
where 1 = 0   -- stub: populate from edit lineage
