{#
  s3_external(layer, name) — build the client-partitioned external-parquet S3 location for a
  Silver/Gold model (ADR-005 §A: Gold S3 = sole source of truth; DuckDB catalog is compute-only).

  Path: s3://<S3_BUCKET>/<layer>/<name>/<CLIENT_ID>/<name>.parquet  (model-first, then client).

  Why client-partitioned and not un-partitioned: dbt-duckdb's `external` materialization does a
  FULL OVERWRITE of its location every run, and bronze is read one client per dbt run (ADR-006,
  _sources.yml has no CLIENT_ID default). An un-partitioned path would make client B's build
  clobber client A's parquet. Tenancy is PATH-level (env_var CLIENT_ID), never a data column —
  fact_chunk has no client_id (Clean-ERD axis 4; it reaches client via dim_asset), so DuckDB's
  native partition_by-a-column cannot apply. Mirrors landing/<client_id>/ + bronze/<client_id>/.

  env_var() has no default on purpose: a missing S3_BUCKET / CLIENT_ID must FAIL LOUD at parse
  rather than silently write to a wrong path — same fail-closed guard as _sources.yml + the
  lineage contract. Called from each model's config() (parse-time), so env_var renders there;
  this is NOT in dbt_project.yml because project-level +location renders before `this`/name exist.
#}
{% macro s3_external(layer, name) %}
  {{- return("s3://" ~ env_var('S3_BUCKET') ~ "/" ~ layer ~ "/" ~ name ~ "/" ~ env_var('CLIENT_ID') ~ "/" ~ name ~ ".parquet") -}}
{% endmacro %}

{#
  silver_gold_config(layer, name) — the config() dict every Silver/Gold model uses, target-aware.

  Under `target.name == 'golden_test'` (the $0/no-cloud/CI-safe fixture target — see
  models/staging/_sources.yml's matching target.name branch on bronze_asset_raw), Silver/Gold
  fall back to plain local view/table — NEVER `external` — so the golden-dataset test
  (tests/golden/run_golden_test.py, run in CI with a literal placeholder S3_BUCKET that does
  not exist) never attempts a real S3 call. This was a real regression caught by actually
  running that test after wiring `external` everywhere: it 404'd against the fake bucket
  because materialization was unconditionally `external`, not just the path.

  Real (dev / production) targets get the genuine ADR-005 `external` + client-partitioned path.
#}
{% macro silver_gold_config(layer, name) %}
  {%- if target.name == 'golden_test' -%}
    {{ return({'materialized': 'view'}) }}
  {%- else -%}
    {{ return({'materialized': 'external', 'location': s3_external(layer, name)}) }}
  {%- endif -%}
{% endmacro %}
