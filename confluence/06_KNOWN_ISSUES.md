# Known Issues

> **Audience: the team.** Every item here is a real, currently-open gap — pulled from
> `PROJECT_STATUS.md`'s own "named, not fixed" / "bounded" / "flagged" entries, not re-derived from
> memory. None of these are silent — each was named honestly at the point it was found, per this
> project's own convention (DQD.md §3: "name gaps honestly"). Each links to the section with full
> context. This page is curated; `PROJECT_STATUS.md` is the source of truth if a citation goes stale.

## Data quality

**`chunk_theme` vocabulary drift — 50 distinct freeform strings across 169 chunks.**
Gemini's free-text theme labels aren't a controlled vocabulary (e.g. `'How It Works'` vs
`'How it works'`, `'Benefit'`/`'Benefits'`/`'Benefit Demonstration'` near-duplicates). Exact-match
filtering (search CLI, assembler adjacency join) silently misses near-duplicate themes. Routes to
@data-architect / @data-quality-steward for a real design call (extraction-prompt redesign or a
normalization/enum gate) — not unilaterally fixed. *(PROJECT_STATUS.md, "v1 search/mix-and-match
demo" + re-confirmed under "Smaller named gaps".)*

**EDL→`bridge_ad_chunk` reconciliation test has no demonstrated red→green proof.**
The anti-join singular test passes against the (currently empty) EDL seed. A live adversarial proof
(inject a bad row, confirm FAIL, revert) was attempted and blocked by the harness's own permission
classifier as risky local file destruction — not retried around. Correctness rests on the anti-join
idiom being structurally sound, not on a demonstrated failing-then-passing run. *(PROJECT_STATUS.md,
"Smaller named gaps".)*

## Serving / storage

**Two Gold stub models produce a phantom row when read raw — confirmed handled, not a live risk.**
`bridge_asset_lineage` and `fact_extraction_run` are `where 1=0` stubs; dbt-duckdb pads an empty
`external` model with a 1-row all-NULL parquet, which a **raw** reader (DuckDB httpfs or a
Snowflake external table) sees as 1 row. `tests/reconcile_snowflake_serving.py` reads both sides
raw on purpose, so this reconciles as 1/1 by design — confirmed on the real 2026-06-27 live run, not
a false-positive. Still worth knowing if you write a *different* check against these two models.
*(PROJECT_STATUS.md, "Silver/Gold S3 materialization — FIXED"; "Snowflake refresh + reconciliation
— RUN LIVE FOR REAL".)*

**RESOLVED 2026-06-27 — Snowflake serving is built and live.** External tables (8, row-for-row
reconciled live against real Gold S3) + a native `VECTOR` semantic-search view replace the managed
Cortex Search Service, which was tried for real and abandoned (trial-tier accounts can't run the
`EMBED_TEXT_768` AI function it needs — an account-tier wall, not an engineering gap; full trail in
ADR-005 Addenda #2–#4). DuckDB VSS remains the $0 fallback. *(PROJECT_STATUS.md, "Snowflake refresh
+ reconciliation — RUN LIVE FOR REAL".)*

## Orchestration / ops (owner decisions, not defaults)

**Airflow DAG is manual-trigger only (`schedule=None`).** Flipping to `@daily` would make it
autonomously call Drive + Gemini on a timer, unattended — a real cost/automation decision this
project's FinOps posture treats as owner-gated, not a default to silently flip. *(PROJECT_STATUS.md,
"Smaller named gaps" item 4.)*

**RESOLVED 2026-06-27 — `dbt build` now runs in CI for real.** Owner chose AWS OIDC role
federation over a static-key GitHub secret (ADR-013) — no long-lived AWS credential is stored
anywhere. Gated `push`-to-`main` only, never `pull_request`. Proven on a real Actions run: OIDC
handshake succeeded, all 8 Gold external models built through the least-privilege role.
*(PROJECT_STATUS.md, "AWS OIDC for real `dbt build` in CI".)*

**ADR-007's guarded-delete isn't scheduled yet.** `scripts/enforce_landing_ttl.py` is fully built and
tested at the CLI/function level, but the ADR names it as "a scheduled Airflow task" and no DAG task
exists for it (couldn't validate against a real `DagBag` import without inventing untested
orchestration code). *(PROJECT_STATUS.md, "Multi-client tenancy + landing TTL".)*

**Confluence/Slack sync is manual-run only.** Not wired into CI or the DAG by design — an unverified
integration shouldn't be on an automated trigger until it's succeeded once with real credentials
(ADR-009 rejected-alternative #4). *(PROJECT_STATUS.md, "Operational notifications".)*

## Test coverage gaps

**No seed-fixture framework for the search-demo golden test.** SPEC §4's "search smoke" row (a
golden CLI test against seed fixtures) has nothing to run against — `seeds/` holds real production
data, not test fixtures. Building that framework is separate, bigger work (DQD.md §1 gate 3).
*(PROJECT_STATUS.md, "v1 search/mix-and-match demo".)*

**Multi-client cross-partition reads are out of scope today.** The current dbt build resolves
exactly one client per run; a multi-tenant backfill (globbing across all `client_id`s in one build)
isn't built. Also open: whether `client_id` partitioning is mandatory or optional-with-blank-fallback
— both code paths exist in `ingest_drive_to_s3.py`, pre-existing doc conflict, not introduced by any
single fix. *(PROJECT_STATUS.md, "Bronze source wiring".)*

## Cosmetic

**dbt 1.10 deprecation warning** on `relationships` tests in `_core.yml`/`_performance.yml`
(top-level arguments should nest under `arguments`) — 7 occurrences, doesn't fail the build. Flagged
for a future cleanup pass. *(PROJECT_STATUS.md, "5th LLM-output gate".)*
