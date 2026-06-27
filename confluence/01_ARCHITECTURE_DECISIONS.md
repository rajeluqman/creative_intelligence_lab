# Creative Intelligence Pipeline — Architecture Decisions (start here)

> The important decisions behind this pipeline, in one place, for someone joining the project. Each
> entry is the decision + *why it matters when you maintain or optimize this code.* The full record
> (context, rejected alternatives, consequences) lives in the repo at the linked path — read it
> before you challenge or change a decision. The individual ADR files are the source of truth; this
> page is the curated onboarding view.

## Read these first — the pipeline's shape (Core)

These five define the engine, the model, the grain, the storage truth, and identity. You cannot
safely change anything without understanding them.

### 1. DuckDB, not Spark — `architecture/ADR-001-duckdb-over-spark.md`
The transform engine is dbt + DuckDB. The data is KB–MB (transcripts and small structured output,
not big video bytes), so a distributed engine would be pure overhead. **Why it matters:** if you're
tempted to "scale this with Spark/Glue," that's a settled no — the boundary contract will fail the
build. Optimize within DuckDB (vectorization, pushdown), not by changing engines.
*(Amended on the storage/serving axis by ADR-005.)*

### 2. Graph + star, not pure star — `architecture/ADR-002-graph-over-star.md`
Reuse needs relationships *between* chunks (which chunk can follow which), so the model is a hybrid:
star facts (`fact_chunk`) **plus** graph edges (bridge tables like `bridge_chunk_compatibility`).
**Why it matters:** N:N relationships are real bridge tables, never resolved in a CTE at query time —
that's the Clean-ERD doctrine. Keep cardinality explicit and testable.

### 3. Chunk in Silver, keep Bronze verbatim — `architecture/ADR-003-chunking-in-silver.md`
Bronze stores the **verbatim Gemini response** (one row per asset, untouched). The split into
one-row-per-chunk happens in Silver (`stg_gemini_raw` unnests it). **Why it matters:** this is what
lets you re-model freely without re-calling the paid API — re-parse Bronze, never re-pay. Don't move
chunking upstream into the extraction script.

### 4. Unified S3 storage + Snowflake serving veneer — `architecture/ADR-005-unified-s3-and-snowflake-serving.md`
All layers persist to **real S3**; DuckDB's catalog is ephemeral/compute-only. **Gold S3 is the sole
source of truth.** Snowflake is a read-only serving veneer over Gold (with a DuckDB VSS $0
fallback). **Why it matters:** never let Snowflake (or any serving layer) become a second copy of the
truth — serving is a view over Gold, not a duplicate. No MinIO (owner override). A checked-in,
re-runnable reconciliation script (`tests/reconcile_snowflake_serving.py`) is the live trip-wire for
this rule — it has been run live against the real account and exact-matches on all 8 models.
**Addendum, same ADR (2026-06-27):** the managed Cortex Search Service was tried for real and
abandoned after three genuine blockers, the last one terminal — `EMBED_TEXT_768` is gated off
trial-tier Snowflake accounts entirely, a billing wall, not an engineering gap. Built instead: a
native `VECTOR(FLOAT, 768)` view (`PUBLIC.FACT_CHUNK_VECTOR`) over the BYO-Gemini embedding column,
queried with `VECTOR_COSINE_SIMILARITY` — same answer shape as the DuckDB VSS path, zero second
embedding surface. **Why it matters:** if you're tempted to re-attempt Cortex Search Service on this
account, don't — the wall is account-tier, not code; see ADR-005 Addenda #2–#4 for the full trail.

### 5. Content-hash identity, multi-client — `architecture/ADR-006-multi-client-tenancy.md`
`asset_id = sha256("{client_id}:{content_sha256}")`. Identity is the content, scoped per client, so
two clients' byte-identical footage never collides and re-uploads are idempotent (skip-existing).
`client_id` lives on `dim_asset` only, reached elsewhere by join. **Why it matters:** this is the
answer to the near-duplicate problem. Never invent a random surrogate key for an asset; never store
`client_id` on `fact_chunk`.

## Read these next — scope & operations (Secondary)

### 6. Performance-veto converted — `architecture/ADR-004-performance-veto-converted.md`
Ad-performance (ROAS/impressions) was vetoed from v1 and converted to a v1.5 mart that needs real
platform exports. **Why it matters:** raw footage has no performance data — don't wire perf
assumptions into v1 models.

### 7. Landing TTL (guarded hard-delete @ 30 days) — `architecture/ADR-007-landing-ttl.md`
Raw landing files are hard-deleted after 30 days, with guards (golden exemption, no delete without a
confirmed Bronze row, a frozen-asset log per delete). **Why it matters:** re-parse from Bronze
survives a delete; re-extraction on a new prompt/model does not. Know this before relying on landing.

### 8. Airflow orchestration wiring — `architecture/ADR-008-airflow-orchestration-wiring.md`
Airflow runs in an isolated `venv_airflow/` and shells out to the real scripts in the main `venv/`.
**Why it matters:** keep the orchestration deps separate from the pipeline deps; tasks invoke
scripts cross-venv, they don't import them.

### 9. AWS OIDC role federation for CI — `architecture/ADR-013-aws-oidc-ci-federation.md`
CI's `real-build` job (push-to-`main` only, never `pull_request`) assumes a dedicated
`creative-intel-ci-role` via GitHub's OIDC token, then runs a real `dbt build -s +marts.core`
against real S3 — least-privilege (read-only Bronze, read+write Silver/Gold only). **No long-lived
AWS key is stored anywhere.** **Why it matters:** if you're adding a new CI job that needs AWS
access, federate through this same role/pattern — don't add a static-key GitHub secret.

## Internal / governance ADRs (not pipeline architecture — skim only)

These govern *how the project and its AI assistant operate*, not the pipeline. You generally don't
need them to maintain the data flow:

- **ADR-009** — Slack failure alerts + Confluence doc sync (this page is published by it).
- **ADR-010** — repo-map navigation gate + ADR-coupling gate (CI tooling).
- **ADR-011** — conversational language protocol (how the AI assistant narrates; English-default).
- **ADR-012** — token-efficiency & session-discipline (how the AI assistant manages its own cost).

Full records for all of the above are in the repo under `architecture/`.
