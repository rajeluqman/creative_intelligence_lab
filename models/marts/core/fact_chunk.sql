-- Feature row. GRAIN = one semantic chunk. ADR-002.
{{ config(**silver_gold_config('gold', 'fact_chunk')) }}
-- `embedding`: SPEC_v1_search.md §1 / ERD_consolidated.md reserved this column, nullable in v1,
-- "no model change needed to add it later" — this is that later. LEFT JOIN (not a required join)
-- so chunks with no embedding yet still surface as a row with embedding=NULL, matching the
-- reserved/nullable contract; populated by scripts/generate_embeddings.py (ADR-005 §B), not here.
-- Skipped entirely under golden_test (no fixture for this source, and the $0/no-cloud golden
-- test never asserts on `embedding` — see tests/golden/run_golden_test.py's column list) so the
-- fixed local fixture target never makes a doomed real-S3 read against a placeholder bucket.
select
    c.chunk_id, c.asset_id, c.chunk_sequence,
    c.start_sec, c.end_sec, c.transcript_segment,
    c.chunk_theme, c.sentiment, c.standalone_score,
    {% if target.name == 'golden_test' -%}
    cast(null as double[]) as embedding
    {%- else -%}
    e.embedding
    {%- endif %}
from {{ ref('int_chunk_cleaned') }} c
{% if target.name != 'golden_test' -%}
left join {{ source('gold', 'chunk_embedding') }} e using (chunk_id)
{%- endif %}
