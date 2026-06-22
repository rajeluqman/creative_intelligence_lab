-- Node table. RAW + EDITED. Sourced from the ingestion manifest — asset_type and
-- parent_asset_id come from the manifest, NOT a literal (gap-check B3). ADR-002/003.
-- The manifest is the system of record for asset identity; the ingestion script
-- appends one row per landed video (RAW on arrival; EDITED when an ad cut lands).
select
    asset_id,                 -- SHA-256(client_id ':' content_sha256) — tenant-scoped (ADR-006)
    client_id,                -- FK -> dim_client; tenancy boundary, NOT NULL
    content_sha256,           -- raw byte hash; non-key, intra-client near-dup detection
    parent_asset_id,          -- RAW->EDITED discovery lineage; NULL for RAW
    asset_name,
    asset_type,               -- RAW | EDITED
    duration_sec,
    source_uri,
    ingested_at,              -- when the bytes actually landed in S3 (provenance, immutable; @data-architect 2026-06-22)
    cast(null as varchar) as dq_flag,
    current_timestamp     as load_ts  -- when this row was last (re)built (audit, volatile) — NOT the same event as ingested_at
from {{ ref('asset_manifest') }}
