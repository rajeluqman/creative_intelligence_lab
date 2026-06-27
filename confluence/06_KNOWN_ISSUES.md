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

**Two Gold stub models produce a phantom row when read raw.**
`bridge_asset_lineage` and `fact_extraction_run` are `where 1=0` stubs; dbt-duckdb pads an empty
`external` model with a 1-row all-NULL parquet. dbt's own view filters it to 0 rows, but a **raw**
parquet reader (e.g. Snowflake external table) sees 1 phantom row. ADR-005's reconciliation test
must read both sides consistently (both raw or both null-filtered) or it will false-positive.
*(PROJECT_STATUS.md, "Silver/Gold S3 materialization — FIXED".)*

**Snowflake Cortex serving is not built.** External tables + Cortex Search over the now-real Gold S3
data (completion-plan item 3) — blocked on filling `SNOWFLAKE_WAREHOUSE`/`DATABASE`/`ROLE` in
`.env`. DuckDB VSS already covers the $0-fallback search path for real. *(PROJECT_STATUS.md, "Next
step when resuming", item 3.)*

## Orchestration / ops (owner decisions, not defaults)

**Airflow DAG is manual-trigger only (`schedule=None`).** Flipping to `@daily` would make it
autonomously call Drive + Gemini on a timer, unattended — a real cost/automation decision this
project's FinOps posture treats as owner-gated, not a default to silently flip. *(PROJECT_STATUS.md,
"Smaller named gaps" item 4.)*

**`dbt build` is not in CI** — only `dbt parse` + `dbt seed` run (placeholder env, $0, no cloud).
Adding a real build needs AWS credentials as GitHub Actions secrets on a `pull_request`-triggered
workflow — a real security/access-grant decision needing explicit owner sign-off, not an
implementation detail. *(PROJECT_STATUS.md, "Smaller named gaps" item 3.)*

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
