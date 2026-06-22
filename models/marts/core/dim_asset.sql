-- Node table. RAW + EDITED. Sourced from the ingestion manifest — asset_type and
-- parent_asset_id come from the manifest, NOT a literal (gap-check B3). ADR-002/003.
-- The manifest is the system of record for asset identity; the ingestion script
-- appends one row per landed video (RAW on arrival; EDITED when an ad cut lands).
select
    asset_id,
    parent_asset_id,          -- RAW->EDITED discovery lineage; NULL for RAW
    asset_name,
    asset_type,               -- RAW | EDITED
    duration_sec,
    source_uri,
    cast(null as varchar) as dq_flag,
    current_timestamp     as load_ts
from {{ ref('asset_manifest') }}
