-- Filler removal, timestamp normalize, score passthrough. (Silver, ADR-003)
-- Silver persists to real S3 as external parquet (ADR-005 §A). Client-partitioned PATH (env_var
-- CLIENT_ID), same reason as Gold in dbt_project.yml: `external` overwrites its location each run
-- and bronze is read one client per run, so an un-partitioned path would clobber across clients.
{{ config(**silver_gold_config('silver', 'int_chunk_cleaned')) }}
select
    chunk_id, asset_id, chunk_sequence,
    start_sec, end_sec, transcript_segment,
    chunk_theme, sentiment, standalone_score,
    next_compatible_themes, keywords
from {{ ref('stg_gemini_raw') }}
