#!/usr/bin/env bash
# =============================================================================
# setup.sh — Creative Intelligence Pipeline scaffold + environment
#
# Generates the runnable dbt-duckdb repo (config, seeds, 18 model stubs wired
# into a valid DAG, scripts, env), creates a venv, installs deps, and verifies
# with `dbt parse`. Idempotent: existing files are SKIPPED (your edits are safe).
#
# Usage:
#   bash setup.sh              # scaffold + venv + install + dbt parse
#   SKIP_INSTALL=1 bash setup.sh   # scaffold files only (no venv/pip/dbt)
# =============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
echo "==> Scaffolding into: $ROOT"

# write-file helper: writes heredoc to $1 only if it does not already exist
wf(){ local p="$1"; mkdir -p "$(dirname "$p")"
  if [ -e "$p" ]; then echo "  skip   $p"; cat >/dev/null; else cat >"$p"; echo "  create $p"; fi; }

mkdir -p seeds models/staging models/intermediate models/marts/core models/marts/performance \
         scripts great_expectations analyses data/landing logs

# ---------------------------------------------------------------- root config
wf requirements.txt <<'EOF'
dbt-duckdb>=1.8
duckdb>=1.1
great-expectations>=0.18
google-genai>=2.0                # current SDK (google-generativeai is fully EOL — see run_gemini_extract.py)
google-api-python-client>=2.100   # Drive API v3 (ingest_drive_to_s3.py) — direct dep, not transitive
google-auth>=2.23                # service-account credentials for headless Drive auth
pandas>=2.0
scipy>=1.11
boto3>=1.34
tqdm>=4.66
ruff>=0.6
EOF

wf .gitignore <<'EOF'
.env
venv/
venv_airflow/
.venv/
target/
dbt_packages/
logs/
data/
*.duckdb
*.parquet
*.csv
!seeds/*.csv
great_expectations/uncommitted/
__pycache__/
EOF

wf .env.example <<'EOF'
# Copy to .env and fill. NEVER commit .env.
# Google Drive (client source folder) — service-account auth for headless ingestion.
# Share the client's Drive folder with the service account's client_email, then fill below.
GOOGLE_APPLICATION_CREDENTIALS=        # path to service-account JSON, NOT the JSON itself
DRIVE_FOLDER_ID=                       # the client's shared Drive folder id
CLIENT_ID=                             # THIS run's client slug — set to YOUR client, must match a row in seeds/dim_client.csv (no silent default; unset = dbt/script error)
# Storage = unified S3 (ADR-005, no MinIO). Real AWS for all layers.
S3_BUCKET=creative-intel-lake
S3_STAGING_BUCKET=creative-intel-staging   # throwaway: drills / overwrite work, never canonical
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ap-southeast-1
# Gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
PROMPT_VERSION=v1
# Serving (ADR-005): Snowflake Cortex veneer over Gold S3. DuckDB VSS = $0 fallback.
# Provision ONLY after v1 Gold has real rows + teardown plan (FinOps). Leave blank to use fallback.
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=
SNOWFLAKE_ROLE=
SERVING_BACKEND=duckdb_vss   # duckdb_vss (default, $0) | snowflake_cortex
EOF

wf dbt_project.yml <<'EOF'
name: 'creative_intelligence'
version: '1.0.0'
config-version: 2
profile: 'creative_intelligence'
model-paths: ["models"]
seed-paths: ["seeds"]
analysis-paths: ["analyses"]
target-path: "target"
clean-targets: ["target", "dbt_packages"]
models:
  creative_intelligence:
    staging:      {+materialized: view}
    intermediate: {+materialized: view}
    marts:
      core:        {+materialized: table}
      performance: {+materialized: table}
seeds:
  creative_intelligence:
    dim_platform:
      +column_types: {platform_id: varchar, platform_name: varchar, hook_window_sec: integer, hold_milestones: varchar}
    asset_manifest:
      +column_types: {asset_id: varchar, asset_name: varchar, asset_type: varchar, parent_asset_id: varchar, duration_sec: integer, source_uri: varchar}
    edit_decision_list:
      +column_types: {ad_id: varchar, chunk_id: varchar, chunk_role: varchar, position_in_ad: integer, start_sec: double, end_sec: double}
    map_ad_asset:
      +column_types: {ad_id: varchar, asset_id: varchar}
EOF

wf packages.yml <<'EOF'
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.1.0", "<2.0.0"]
  - package: calogica/dbt_expectations
    version: [">=0.10.0", "<0.11.0"]
EOF

wf profiles.yml.example <<'EOF'
# Copy to ~/.dbt/profiles.yml (or set DBT_PROFILES_DIR to this folder).
creative_intelligence:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "target/dev.duckdb"     # ephemeral local catalog
      extensions: [httpfs, parquet]
      # settings: {s3_region: "ap-southeast-1"}   # add for real S3 reads
EOF

# ---------------------------------------------------------------- seeds
wf seeds/dim_platform.csv <<'EOF'
platform_id,platform_name,hook_window_sec,hold_milestones
meta,meta,3,"25,50,75,100"
tiktok,tiktok,6,"25,50,75,100"
EOF

wf seeds/map_ad_asset.csv <<'EOF'
ad_id,asset_id
EOF

# ---------------------------------------------------------------- sources
wf models/staging/_sources.yml <<'EOF'
version: 2
sources:
  - name: bronze
    schema: bronze
    tables:
      - name: bronze_asset_raw           # verbatim Gemini JSON (immutable, ADR-003)
      - name: bronze_ad_performance_raw  # verbatim Meta/TikTok CSV (immutable, v1.5)
EOF

# ---------------------------------------------------------------- staging
wf models/staging/stg_gemini_raw.sql <<'EOF'
-- Flatten verbatim Gemini JSON -> one row per semantic chunk.
-- Full logic: architecture/SPEC_v1.5_performance_marts.md §1 + DATA_MODEL.md §5
select
    asset_id,
    chunk_sequence,
    chunk_id,
    start_sec, end_sec,
    transcript_segment, chunk_theme, sentiment, standalone_score,
    next_compatible_themes,   -- array; exploded downstream
    keywords,                 -- array; exploded downstream
    model_version, prompt_version
from {{ source('bronze', 'bronze_asset_raw') }}
EOF

wf models/staging/stg_meta_perf.sql <<'EOF'
-- Conform Meta funnel columns to the canonical schema (v1.5).
select
    ad_id, perf_date,
    impressions, plays_3s, plays_25, plays_50, plays_75, plays_100,
    sum_watch_time_sec, play_count, link_clicks, results, spend
from {{ source('bronze', 'bronze_ad_performance_raw') }}
where platform_native = 'meta'
EOF

wf models/staging/stg_tiktok_perf.sql <<'EOF'
-- Conform TikTok funnel columns to the canonical schema (v1.5).
select
    ad_id, perf_date,
    impressions, plays_3s, plays_25, plays_50, plays_75, plays_100,
    sum_watch_time_sec, play_count, link_clicks, results, spend
from {{ source('bronze', 'bronze_ad_performance_raw') }}
where platform_native = 'tiktok'
EOF

wf models/staging/_staging.yml <<'EOF'
version: 2
models:
  - name: stg_gemini_raw
    columns:
      - name: chunk_id
        tests: [not_null]
  - name: stg_meta_perf
  - name: stg_tiktok_perf
EOF

# ---------------------------------------------------------------- intermediate
wf models/intermediate/int_chunk_cleaned.sql <<'EOF'
-- Filler removal, timestamp normalize, score passthrough. (Silver, ADR-003)
select
    chunk_id, asset_id, chunk_sequence,
    start_sec, end_sec, transcript_segment,
    chunk_theme, sentiment, standalone_score,
    next_compatible_themes, keywords
from {{ ref('stg_gemini_raw') }}
EOF

wf models/intermediate/int_ad_perf_unioned.sql <<'EOF'
-- Meta UNION TikTok + platform tag (v1.5).
select 'meta'   as platform_name, * from {{ ref('stg_meta_perf') }}
union all
select 'tiktok' as platform_name, * from {{ ref('stg_tiktok_perf') }}
EOF

wf models/intermediate/int_metric_chunk_alignment.sql <<'EOF'
-- Position-aligned mapping: each funnel metric -> the ONE owning chunk.
-- Full time-range-join + tie-break + coverage_confidence logic:
--   architecture/SPEC_v1.5_performance_marts.md §4
select
    ad_id, platform_id, metric_name, chunk_id, chunk_role, coverage_confidence
from {{ ref('bridge_ad_chunk') }} b
cross join {{ ref('dim_platform') }} p          -- placeholder join; see SPEC §4 for real anchors
where 1 = 0                                     -- stub: replace with SPEC §4 body
EOF

# ---------------------------------------------------------------- marts/core
wf models/marts/core/dim_asset.sql <<'EOF'
-- Node table. RAW + EDITED. Self-ref parent (discovery only). ADR-002.
select distinct
    asset_id,
    cast(null as varchar) as parent_asset_id,
    cast(null as varchar) as asset_name,
    'RAW'                 as asset_type,
    cast(null as integer) as duration_sec,
    cast(null as varchar) as source_uri,
    cast(null as varchar) as dq_flag,
    current_timestamp     as load_ts
from {{ ref('int_chunk_cleaned') }}
EOF

wf models/marts/core/fact_chunk.sql <<'EOF'
-- Feature row. GRAIN = one semantic chunk. ADR-002.
select
    chunk_id, asset_id, chunk_sequence,
    start_sec, end_sec, transcript_segment,
    chunk_theme, sentiment, standalone_score
from {{ ref('int_chunk_cleaned') }}
EOF

wf models/marts/core/bridge_asset_lineage.sql <<'EOF'
-- RAW -> EDITED edge. Navigation only; NEVER carries metrics. ADR-002/004.
select asset_id as parent_asset_id, asset_id as child_asset_id
from {{ ref('dim_asset') }}
where 1 = 0   -- stub: populate from edit lineage
EOF

wf models/marts/core/bridge_chunk_compatibility.sql <<'EOF'
-- Mix-and-match adjacency. Explodes next_compatible_themes[].
select
    chunk_id,
    unnest(next_compatible_themes) as compatible_theme,
    cast(null as decimal) as theme_match_score
from {{ ref('int_chunk_cleaned') }}
EOF

wf models/marts/core/dim_keyword_bridge.sql <<'EOF'
select chunk_id, unnest(keywords) as keyword
from {{ ref('int_chunk_cleaned') }}
EOF

wf models/marts/core/dim_theme_bridge.sql <<'EOF'
select chunk_id, chunk_theme as theme
from {{ ref('int_chunk_cleaned') }}
EOF

wf models/marts/core/fact_extraction_run.sql <<'EOF'
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
EOF

wf models/marts/core/_core.yml <<'EOF'
version: 2
models:
  - name: dim_asset
    columns:
      - name: asset_id
        tests: [unique, not_null]
      - name: asset_type
        tests: [{accepted_values: {values: ['RAW','EDITED']}}]
  - name: fact_chunk
    columns:
      - name: chunk_id
        tests: [unique, not_null]
      - name: asset_id
        tests: [{relationships: {to: ref('dim_asset'), field: asset_id}}]
      - name: standalone_score
        tests: [{dbt_expectations.expect_column_values_to_be_between: {min_value: 1, max_value: 5}}]
EOF

# ---------------------------------------------------------------- marts/performance
# dim_platform is a SEED (seeds/dim_platform.csv) — no model, to avoid a duplicate-name
# collision. Everything refs ref('dim_platform') which resolves to the seed.

wf models/marts/performance/fact_ad_performance.sql <<'EOF'
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
EOF

wf models/marts/performance/bridge_ad_chunk.sql <<'EOF'
-- Editor's asserted cut: ad -> chunk + role + position (the v1.5 unlock). SPEC §2.
select
    cast(null as varchar) as ad_id,
    chunk_id,
    asset_id,
    cast(null as varchar) as chunk_role,
    cast(null as integer) as position_in_ad,
    start_sec, end_sec
from {{ ref('fact_chunk') }}
where 1 = 0   -- stub: populate from the edit-decision feed (manual seed v1.5)
EOF

wf models/marts/performance/fct_ad_kpi.sql <<'EOF'
-- Ratios derived here ONLY (ratio-of-sums). SPEC §3.
{{ config(materialized='view') }}
with agg as (
    select ad_id, platform_id,
           sum(impressions) impressions, sum(plays_3s) plays_3s, sum(plays_25) plays_25,
           sum(sum_watch_time_sec) watch_sec, sum(play_count) play_count,
           sum(link_clicks) link_clicks, sum(results) results, sum(spend) spend
    from {{ ref('fact_ad_performance') }} group by 1,2
)
select ad_id, platform_id,
    plays_3s::double    / nullif(impressions,0) as hook_rate,
    plays_25::double    / nullif(plays_3s,0)    as hold_rate_25,
    watch_sec::double   / nullif(play_count,0)  as avg_play_time_sec,
    link_clicks::double / nullif(impressions,0) as ctr_link,
    spend::double       / nullif(results,0)     as cpa,
    results::double     / nullif(link_clicks,0) as cvr
from agg
EOF

wf models/marts/performance/fct_ad_metric_chunk.sql <<'EOF'
-- 1 ad x platform x metric -> metric value + mapped chunk features. SPEC §5.
select
    al.ad_id, al.platform_id, al.metric_name,
    cast(null as double) as metric_value,   -- stub: case-map from fct_ad_kpi per SPEC §5
    al.chunk_id, al.chunk_role, al.coverage_confidence,
    fc.chunk_theme, fc.sentiment, fc.standalone_score
from {{ ref('int_metric_chunk_alignment') }} al
join {{ ref('fact_chunk') }} fc on fc.chunk_id = al.chunk_id
where al.coverage_confidence in ('HIGH','MEDIUM')
EOF

wf models/marts/performance/mart_chunk_perf_correlation.sql <<'EOF'
-- Surfaced insight. Within-platform, within-winners, sample-gated. SPEC §6.
with base as (
    select platform_id, metric_name, 'chunk_theme' as feature_dim,
           chunk_theme as feature_value, ad_id, metric_value
    from {{ ref('fct_ad_metric_chunk') }} where metric_value is not null
),
grouped as (
    select platform_id, metric_name, feature_dim, feature_value,
           count(distinct ad_id) as n_ads, median(metric_value) as median_metric
    from base group by 1,2,3,4
)
select *,
    rank() over (partition by platform_id, metric_name order by median_metric desc) as rank_in_platform,
    case when n_ads < 5 then 'BLOCK' when n_ads < 12 then 'DIRECTIONAL' else 'SUGGESTIVE' end as evidence_regime,
    'Among winning ads only - within-platform ranking, correlation not causation' as honesty_note
from grouped
EOF

wf models/marts/performance/_performance.yml <<'EOF'
version: 2
models:
  - name: fact_ad_performance
    columns:
      - name: spend
        tests: [{dbt_expectations.expect_column_values_to_be_between: {min_value: 0}}]
      - name: ad_id
        tests: [not_null]
  - name: bridge_ad_chunk
    columns:
      - name: chunk_role
        tests: [{accepted_values: {values: ['hook','body','social_proof','cta']}}]
  - name: mart_chunk_perf_correlation
    columns:
      - name: honesty_note
        tests: [not_null]
EOF

# ---------------------------------------------------------------- analyses
wf analyses/demo_queries.sql <<'EOF'
-- The three demo queries (full text: SPEC_v1.5_performance_marts.md §8).
-- 1) v1 north-star search   2) Hook-theme x Hook Rate correlation   3) mine unused RAW chunks
-- Run with: dbt compile -s demo_queries  (then read target/compiled/...)
select 'see SPEC §8' as todo
EOF

# ---------------------------------------------------------------- scripts
wf scripts/ingest_drive_to_s3.py <<'EOF'
"""Drive -> S3 landing. Content-hash (SHA-256) naming, skip-existing (idempotent)."""
# TODO: Google Drive API pull -> hashlib.sha256(bytes) -> s3://$S3_BUCKET/landing/video/<hash>.<ext>
# Skip if the hash already exists (cost firewall). See STACK_AND_FLOW.md §2 Path A.
EOF

wf scripts/run_gemini_extract.py <<'EOF'
"""S3 video -> Gemini (Flash, responseSchema) -> bronze_asset_raw (verbatim JSON)."""
# TODO: upload, poll (deferrable in Airflow), structured-output call, stamp model_version/prompt_version,
# write verbatim to Bronze. NEVER re-call on re-model (ADR-003). Log tokens/cost -> fact_extraction_run.
EOF

wf scripts/significance_post_step.py <<'EOF'
"""SUGGESTIVE-tier significance: DuckDB -> pandas -> scipy Mann-Whitney U + Bonferroni."""
# TODO: read mart_chunk_perf_correlation rows where evidence_regime='SUGGESTIVE';
# within-platform groups only; write back p_value + is_significant. SPEC §6.
EOF

wf scripts/env_guard.py <<'EOF'
"""Fail-closed env guard (mirror of pharma gym_guard). Import + call assert_safe() in any
runner that touches S3, so a misconfigured env aborts instead of hitting the wrong bucket."""
import os
import sys


def assert_safe():
    bucket = os.getenv("S3_BUCKET", "")
    if not bucket:
        sys.exit("env_guard: S3_BUCKET unset - refusing to run.")
    # Extend: in a gym/incubator context require a throwaway bucket + fake creds + local endpoint.


if __name__ == "__main__":
    assert_safe()
    print("env_guard: ok")
EOF

wf great_expectations/README.md <<'EOF'
# Great Expectations suites (per layer)
Bootstrap with `great_expectations init` after `setup.sh`. Suites to build:
- bronze_asset_raw: valid JSON, chunks length >= 1 (catches schema-valid-but-empty LLM output)
- silver_chunk: standalone_score in [1,5], sentiment enum, non-empty chunk_theme
- fact_ad_performance: counts/spend >= 0, platform enum, EDITED-only FK, every ad -> >=1 chunk
- mart_chunk_perf_correlation: n_ads<5 => BLOCK (not surfaced), honesty_note not null
See architecture/SPEC_v1.5_performance_marts.md §7 for the full gate list.
EOF

wf .github/workflows/ci.yml <<'EOF'
name: CI
# Static gates only - $0, no cloud, no secrets. Mirrors the pharma gym CI pattern.
on:
  pull_request: {branches: [main]}
  push:        {branches: [main]}
jobs:
  static-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - name: Install tooling
        run: pip install --upgrade pip ruff dbt-duckdb
      - name: Lint (ruff)
        run: ruff check scripts/
      - name: Compile Python
        run: |
          shopt -s nullglob
          for f in scripts/*.py; do python -m py_compile "$f"; done
      - name: dbt deps + parse
        env: {DBT_PROFILES_DIR: "${{ github.workspace }}"}
        run: |
          cp profiles.yml.example profiles.yml
          dbt deps
          dbt parse
      - name: dbt seed
        env: {DBT_PROFILES_DIR: "${{ github.workspace }}"}
        run: dbt seed
      - name: Guard - no .env committed
        run: |
          if git ls-files | grep -E '(^|/)\.env$'; then echo "::error::.env committed"; exit 1; fi
          echo "no .env tracked - ok"
EOF

wf README_BUILD.md <<'EOF'
# Build quickstart
1. `bash setup.sh`            # scaffold + venv + deps + dbt parse
2. `cp .env.example .env`     # fill GEMINI_API_KEY, S3_BUCKET
3. `cp profiles.yml.example ~/.dbt/profiles.yml`  (or set DBT_PROFILES_DIR=.)
4. Implement the stubs marked `where 1=0` / `TODO` using architecture/SPEC_v1.5_performance_marts.md
5. `dbt seed && dbt build -s marts.core`     # v1 first
6. `dbt build -s marts.performance` + `python scripts/significance_post_step.py`   # v1.5
Architecture of record: architecture/  (DATA_MODEL*, SPEC*, ADR-00*, STACK_AND_FLOW, ERD*, DBT_DAG)
EOF

echo "==> Files scaffolded."

# ---------------------------------------------------------------- environment
if [ "${SKIP_INSTALL:-0}" = "1" ]; then
  echo "==> SKIP_INSTALL=1 set; skipping venv/pip/dbt. Done."
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  echo "==> Creating venv + installing requirements..."
  python3 -m venv venv
  # shellcheck disable=SC1091
  . venv/bin/activate
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt
  [ -f .env ] || cp .env.example .env
  echo "==> Verifying dbt graph (dbt deps + parse)..."
  export DBT_PROFILES_DIR="$ROOT"
  [ -f "$ROOT/profiles.yml" ] || cp profiles.yml.example profiles.yml
  dbt deps  || echo "  (dbt deps failed - run manually after editing packages.yml)"
  dbt parse || echo "  (dbt parse failed - expected until stubs/sources are filled; graph wiring still checked)"
  echo "==> Done. Activate with: source venv/bin/activate"
else
  echo "==> python3 not found; scaffolded files only."
fi
