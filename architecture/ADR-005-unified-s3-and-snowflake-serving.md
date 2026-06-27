# ADR-005 — Unified S3 canonical storage + Snowflake Cortex serving veneer

- **Status:** Accepted (owner override; ratified-with-conditions by @data-architect)
- **Date:** 2026-06-22
- **Deciders:** owner (override), @data-architect (ultimate veto — conditional approve),
  @finops-agent (co-sign on teardown), @scope-guardian (boundary-override recorded),
  @senior-data-engineer (buildability)
- **Amends:** ADR-001 (storage + serving axis only — DuckDB stays the transform engine),
  `STACK_AND_FLOW.md` §1 (serving row + "rejected at this scale" list), `CLAUDE.md` stack boundary.
- **Does NOT touch:** ADR-002 (graph over star), ADR-003 (chunking in Silver), ADR-004
  (perf-veto) — the data model is unchanged (two facts, the bridges, SCD all intact).

## Context
Owner directive (2026-06-22): make **S3 the single unified storage substrate** for the whole
pipeline (landing → bronze → silver → gold), and serve via **Snowflake Cortex**. Cost is covered
by a Snowflake 30-day / $400 trial and low-cost AWS S3. The earlier cabinet "local-first /
MinIO-for-dev" recommendation and the ADR-001/`STACK_AND_FLOW` "no always-on Snowflake" line are
overridden by the owner. Two technical facts from the convene shaped the final form:
1. Snowflake external tables **cannot read MinIO** — so a unified surface must be real S3, not MinIO.
2. v1 Gold is still stubs — serving is **sequenced after** Gold emits real rows; no provisioning yet.

## Decision

### A — Unified S3 storage (no MinIO)
- **All layers persist to S3.** `landing/`, `bronze/`, `silver/`, `gold/` are S3 prefixes.
  Silver/Gold dbt models materialize as **`external` parquet** on S3, read via DuckDB `httpfs`.
- **MinIO is dropped entirely.** Its only benefit was free offline dev; credits cover real S3,
  and it cannot back Snowflake. Dev, staging, and (future) troubleshooting drills all use **real
  S3 buckets** — a separate staging/throwaway bucket for any drill/overwrite work, never the
  canonical bucket.
- **DuckDB = compute only.** The DuckDB catalog is ephemeral (in-process); it is never the truth.

### B — Snowflake Cortex serving (read-only veneer over Gold S3)
- Snowflake **external tables** over `gold/` S3 (read-only) + **Cortex Search** for semantic/
  vector search + **Power BI** for BI. This is the showcased serving demo.
- **Embeddings = bring-your-own (Gemini), generated in the ELT and persisted in Gold S3** —
  NOT Cortex `EMBED_TEXT`. Reason: keep the one content-hash skip-existing idempotency gate the
  pipeline already has; never create a second metered embedding surface (FinOps + senior-DE).
- **DuckDB VSS over the same Gold S3 is retained as the $0 fallback / default serving path.**
  DuckDB reads S3 via httpfs, so the fallback needs no MinIO. This is what a fresh clone (or the
  post-trial demo) runs.

## THE SOURCE-OF-TRUTH BOUNDARY (the spine — do not overwrite)
**Gold S3 parquet is the sole source of truth. Snowflake is a read-only projection.**
- No Gold fact may exist only in Snowflake. The whole veneer must be reconstructible from
  S3 Bronze→Silver→Gold.
- A **reconciliation test** gates the serving layer: Snowflake external-table row counts + key
  sets must exact-match the DuckDB-over-S3 read of the same Gold parquet.
- 🛑 @data-architect veto re-fires if Snowflake becomes a second source of truth (a Snowflake-only
  fact, a CTAS-internal copy that diverges, or a KPI persisted in Snowflake not reproducible from S3).

## Cost discipline (FinOps co-sign — hard preconditions before any Snowflake provisioning)
1. ~~`COST_LOG.md` records the trial start date + a **day-25 teardown reminder** (not day-30).~~
   **Superseded 2026-06-25 — see Addendum below.** No forced teardown deadline; `COST_LOG.md`
   still records the start date as a monitoring practice, not a countdown.
2. The **$0 fallback demo is built and proven BEFORE the trial clock starts** — DuckDB VSS path
   (or a recorded screen-capture), so the portfolio never depends on a live trial.
3. Embeddings single-sourced (BYO Gemini, content-hash-gated) — no re-embed on unchanged chunks.
4. Cortex Search is **suspended/dropped when idle**; it bills wall-clock, not per-query.
- Killing Snowflake at trial-end = **$0 loss** (truth is on S3). Re-provision later = re-run the
  capture-as-code provisioning script against the same S3 prefix, not a backfill.

## Consequences
- **Positive:** one storage surface (simpler than dual local/MinIO); real Snowflake + Cortex +
  Power BI portfolio story; truth stays cheap + permanent on S3; veneer is disposable.
- **Negative / accepted (owner-accepted):** the project is **no longer fully standalone / offline-$0**
  while built against real S3 — a fresh clone needs AWS credentials to run the ELT, and needs a
  funded Snowflake account to run the *Snowflake* serving demo (the DuckDB-VSS fallback keeps the
  core feature store runnable at $0 given S3 read access). The CLAUDE.md "no Snowflake in v1"
  hard-limit line is amended by this ADR, not silently breached.
- **Provisioning stays owner-gated:** any `aws s3 mb` / Snowflake `CREATE` is confirmed by the
  owner before execution.
- **Sequencing:** serving is built **after** v1 Gold emits real rows. Building Cortex Search over
  empty stub Gold is out of order; the 30-day clock does not justify it.

## Addendum (2026-06-25) — day-25 teardown requirement lifted

**Owner instruction:** the Snowflake trial is not charging the linked card; keep it provisioned
long-running, no forced teardown deadline. This replaces Cost discipline item 1's "day-25
teardown reminder" — `COST_LOG.md` still records the trial start date (monitoring practice,
not removed), but there is no countdown forcing a teardown action.

**What this does NOT change** (per the owner's own addendum-parity rule — an addendum amends
narrowly, it doesn't reopen the whole ADR): the SOURCE-OF-TRUTH BOUNDARY above is untouched —
Gold S3 remains sole truth, Snowflake remains a read-only, disposable projection, and the
reconciliation test still gates it. Cost discipline items 2–4 (the $0 fallback **proven first**,
single-sourced embeddings, suspend-Cortex-Search-when-idle) remain in force, unrevised — this
addendum lifts the time-pressure on item 1 only, not the build-order or the other three
spending guards. If the card ever starts being charged (trial converts, limits change), this
addendum is void and the original day-25 discipline resumes — re-evaluate before that happens,
don't wait for a surprise invoice.

## Addendum (2026-06-25 #2) — Silver/Gold external-parquet path convention (client-partitioned)

§A ratified that Silver/Gold materialize as `external` parquet on S3 but did not fix the path
**layout**. Implementing it (Silver `int_chunk_cleaned` + Gold `marts.core`) forced the call.

**Decision:** `s3://<bucket>/<layer>/<model>/<CLIENT_ID>/<model>.parquet` — model-first, then a
**per-client partition**. Set via the `s3_external(layer, name)` macro (`macros/s3_external.sql`),
called from each model's `config(location=...)`. Tenancy is **path-level** (`env_var('CLIENT_ID')`,
no default → fail-loud), never a data column.

**Why client-partitioned, not un-partitioned `gold/<model>/*.parquet`:** dbt-duckdb's `external`
materialization does a **full overwrite** of its location every run, and bronze is read **one
client per dbt run** (ADR-006; `_sources.yml` has no `CLIENT_ID` default; the DAG Param is single-
client). An un-partitioned path would therefore make client B's build **clobber client A's** Gold
parquet — there is no single build that emits all clients at once. (This supersedes a loose
"un-partitioned is the natural fit, Gold spans all clients" note in the 2026-06-25 completion
plan, which assumed an all-clients-in-one-build that this pipeline never does.)

**Why path-level and not DuckDB-native `partition_by`:** `fact_chunk` (and the bridges) carry **no
`client_id` column** — Clean-ERD axis 4 keeps `client_id` on `dim_asset` only, reached by join —
so partitioning by a data column cannot apply. Path-level tenancy mirrors the already-shipped
`landing/<client_id>/` and `bronze/<client_id>/` layout.

**Cross-client serving read** (when needed) globs the partition: `gold/<model>/*/<model>.parquet`.

**Carried-forward finding (for the Snowflake serving workstream — does NOT block this ADR):** the
two `where 1=0` v1 stubs (`bridge_asset_lineage`, `fact_extraction_run`) write a **1-row all-NULL**
parquet — dbt-duckdb pads empty models so the schema survives. dbt's own read-back view filters
that row (logical count 0), but a **raw** reader (Snowflake external table / DuckDB-VSS) sees 1
phantom row. The ADR-005 reconciliation test must read **consistently** (both raw or both
null-filtered) or it will false-positive on these two stubs. Verified 2026-06-25: the 6 non-stub
models reconcile exactly (dbt-view count == raw httpfs S3 read: 169/169 chunks, 19 assets,
363/924/169); only the two stubs show the 0-vs-1 gap.

## Addendum (2026-06-27) — account objects + storage integration + external tables built

§B's "showcased serving demo" gets its first real account-level objects. The trial Snowflake
account turned out to be **shared with the sibling `pharma_novartis_sttm` project** (same login,
`NOVARTISMANG` / `NOVARTIS_STTM_ROLE`) — confirmed via a real read-only `SHOW WAREHOUSES`/`SHOW
DATABASES` before touching anything, not assumed from the trial having one account.

**Decision: dedicated objects, not reuse.** `CREATIVE_INTEL_WH` (XSMALL, `AUTO_SUSPEND=60`),
`CREATIVE_INTEL_DB`, and a new scoped `CREATIVE_INTEL_ROLE` (USAGE+OPERATE on the warehouse, USAGE
on the database, SELECT on exactly the 8 Gold external tables below — not the Novartis project's
own `SNOWFLAKE_GOLD_READER`, which was checked and confirmed unrelated/Novartis-only before being
ruled out as a candidate, and not blanket `ALL` privileges, which this session tried once and was
correctly the broader/non-minimal grant). Created via `ACCOUNTADMIN` — the only role with
account-level `CREATE WAREHOUSE`/`CREATE DATABASE`; `NOVARTIS_STTM_ROLE` lacks it, confirmed by a
real failed attempt first, not assumed.

**Storage integration over reusing static credentials.** A first attempt embedded the AWS access
key/secret directly in a `CREATE STAGE` statement — correctly blocked, because that leaves the
secret sitting in plaintext in Snowflake's own `QUERY_HISTORY`, a persistent queryable log on an
account shared with another project. Fixed with a **storage integration** (IAM role trust, zero
static secrets sent to Snowflake): `CREATIVE_INTEL_S3_INTEGRATION`
(`STORAGE_ALLOWED_LOCATIONS = ('s3://creative-intel-lake/gold/')` only) → `DESC STORAGE
INTEGRATION` gives Snowflake's own IAM user ARN + external ID → those get pasted into the trust
policy of an AWS-console-created IAM role (`creative-intel-snowflake-role`, inline policy scoped
to `s3:GetObject`/`s3:ListBucket` on `gold/*` only) → `GOLD_STAGE` created against the integration
(no `CREDENTIALS` clause) → `LIST @GOLD_STAGE` returning all 8 real files proved the trust live
before any table DDL ran.

**All 8 Gold models built as external tables** (`CREATE ... USING TEMPLATE` + `INFER_SCHEMA`, one
`ALTER ... REFRESH` each): the 7 `marts.core` models + `chunk_embedding` (the BYO-embedding model
from `scripts/generate_embeddings.py`, same client-partitioned `gold/<model>/<CLIENT_ID>/` path
convention as Addendum #2 above — the stage URL is the shared `gold/` prefix, so one stage covers
every model). **Row-count reconciliation, both sides fresh:** a direct DuckDB httpfs read of the
same S3 parquet vs. `SELECT COUNT(*)` through Snowflake using `CREATIVE_INTEL_ROLE` (not
`ACCOUNTADMIN`) matched exactly on all 8, including the two known-stub phantom-rows (1/1, per the
"Carried-forward finding" above — observed live through Snowflake exactly as predicted, not a new
bug).

**Naming gotcha to carry forward:** `USING TEMPLATE`/`INFER_SCHEMA` quotes every inferred column
name, so columns are case-sensitive lowercase in Snowflake (`"asset_id"`, not
`ASSET_ID`/`asset_id` unquoted) — any future query, BI tool, or Cortex Search build against these
tables must quote column names or hit `invalid identifier`.

**Governance gap closed in the same pass it was found:** this session's SQL was originally run ad
hoc with no checked-in artifact — broke this repo's "governance is code, not vigilance" pattern
used everywhere else (hooks, CI contracts), and contradicted this ADR's own Cost-discipline promise
("re-provision later = re-run the capture-as-code provisioning script ... not a backfill"). Fixed:
`scripts/provision_snowflake_serving.py` (new) — idempotent `IF NOT EXISTS` SQL for all three
phases above (account / storage / tables), dry-run by default (prints the plan, no connection, no
credentials needed), `--apply` to actually execute. Re-running it against the objects created this
session is a no-op, not a re-creation — verified via `--phase all` dry-run reproducing exactly the
warehouse/role/integration/table names and the real `S3_BUCKET`/`CLIENT_ID` values already in
`.env`.

**Still open** (next workstream, not this addendum): Cortex Search over `chunk_embedding.embedding`
— it infers as `VARIANT` via `INFER_SCHEMA`, not Snowflake's native `VECTOR`, so Cortex Search needs
an explicit cast/reshape step first, never Cortex's own `EMBED_TEXT` (§B — single embedding surface
rule unchanged). Also open: a *checked-in, automated* reconciliation test (today's match was a real
but manual one-off query, not a script that re-runs on every refresh), `COST_LOG.md`, and wiring
Airflow's `refresh_serving` task to an `ALTER EXTERNAL TABLE ... REFRESH` call per model (it remains
the honest no-op named in ADR-008).
