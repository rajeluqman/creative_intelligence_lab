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

## Addendum (2026-06-27 #2) — §B amended: Cortex Search Service permitted as a second, scoped embedding surface

**The conflict found while starting the "Cortex Search" workstream above:** Snowflake's managed
`CREATE CORTEX SEARCH SERVICE` computes its **own** embeddings server-side over a chosen text
column (`EMBEDDING_MODEL`) — it has no input for a precomputed vector, so it cannot be pointed at
`chunk_embedding.embedding` (BYO Gemini) at all. The originally-planned "cast `VARIANT`→`VECTOR` and
build Cortex Search over it" path named in the 2026-06-27 addendum above is **not actually how the
feature works** — that path only enables raw `VECTOR_COSINE_SIMILARITY`/`VECTOR_L2_DISTANCE` SQL,
not the managed Cortex Search Service. Building the real managed service therefore means Snowflake
re-embeds `transcript_segment` itself, which is literally the "second metered embedding surface"
§B's original line forbade.

**Owner decision (asked directly, not defaulted): build the real managed Cortex Search Service,
accepting the second embedding surface.** §B's BYO-only rule is amended, narrowly:
- **What changes:** the Snowflake serving veneer's search-relevance ranking now uses Snowflake's
  own embedding model (Cortex Search default `EMBEDDING_MODEL`) over `"transcript_segment"` —
  computed and held entirely inside the Cortex Search Service object, an internal Snowflake search
  index, not a persisted fact.
- **What does NOT change:** `chunk_embedding.embedding` (BYO Gemini, content-hash-gated,
  idempotent) stays the **sole persisted/canonical** embedding in Gold S3; the DuckDB VSS `$0`
  fallback (`search_cli.py --semantic`) is untouched and stays 100% BYO-only; Gold S3 remains sole
  source of truth — the Cortex Search index is a rebuildable Snowflake-internal artifact (drop +
  re-`CREATE` via the capture-as-code script reproduces it from `FACT_CHUNK`, same posture as every
  other object in this ADR), never a fact queried as if it were ground truth.
- **Cost (FinOps-relevant, ties to Cost discipline item 4 above):** Cortex Search has no
  per-query/idle-suspend knob the way a warehouse does — it bills wall-clock while it exists.
  Mitigation is the same one already accepted for the rest of the veneer: `DROP CORTEX SEARCH
  SERVICE` when not actively demoing, re-provision later via
  `python scripts/provision_snowflake_serving.py --phase search --apply` (idempotent `IF NOT
  EXISTS`, same script, new phase) — **$0 loss**, not a backfill.
- **Object, scoped:** `CREATIVE_INTEL_DB.PUBLIC.CHUNK_SEARCH_SVC`, search column
  `"transcript_segment"`, attributes `"chunk_id"`, `"asset_id"`, `"chunk_theme"`, `"sentiment"`,
  `"standalone_score"` (quoted lowercase — the same `INFER_SCHEMA` naming gotcha from the addendum
  above), `WAREHOUSE = CREATIVE_INTEL_WH`, source query `SELECT ... FROM PUBLIC.FACT_CHUNK`.
  `CREATIVE_INTEL_ROLE` granted `USAGE` on the service only (not on the warehouse beyond the
  existing `USAGE, OPERATE` grant it already has).

## Addendum (2026-06-27 #3) — second blocker found live: Dynamic Tables reject EXTERNAL_TABLE; a scoped native-table search cache is the fix

**The blocker (real error from the first live `--apply` of Addendum #2's plan, not theoretical):**

```
SQL Compilation error: Object ref FACT_CHUNK of type EXTERNAL_TABLE not supported in Dynamic Table definition
```

Cortex Search Service is implemented internally as a Dynamic Table. Dynamic Tables **cannot be
built on top of an `EXTERNAL_TABLE` at all**, regardless of `TARGET_LAG` or which column is
searched — this is a hard Snowflake product limitation, not a config mistake. Since every Gold
object in Snowflake is an external table over S3 (the whole point of this ADR's spine), the
managed Cortex Search Service cannot point at `FACT_CHUNK` as it exists today.

**Owner decision (asked directly — this is a second architecture question the spine itself
warns about, not something to route around silently): a scoped native-table search cache.**
- **New object:** `CREATIVE_INTEL_DB.PUBLIC.FACT_CHUNK_SEARCH_CACHE` — a native Snowflake `TABLE`,
  `CREATE OR REPLACE TABLE ... AS SELECT "chunk_id", "asset_id", "transcript_segment",
  "chunk_theme", "sentiment", "standalone_score" FROM PUBLIC.FACT_CHUNK`. Cortex Search Service's
  `AS` query now targets this cache, not the external table directly.
  `provision_snowflake_serving.py`'s `search` phase issues the `CREATE OR REPLACE` (not `IF NOT
  EXISTS` like every other statement in this script) **on purpose** — the whole point is a full
  resync against the external table on every run, not a one-time idempotent create. Different
  idempotency flavor from the rest of the script (always-fresh-replace vs. no-op-if-exists), both
  still safe to re-run.
- **Scope fence (this is what keeps it from being the second-source-of-truth the spine forbids):**
  this cache exists **only** as Cortex Search Service's required input. Nobody queries it as a
  fact — `CREATIVE_INTEL_ROLE` is **not** granted `SELECT` on it (only `USAGE` on the search
  service, as in Addendum #2). BI/Power BI/any analytical consumer reads `PUBLIC.FACT_CHUNK` (the
  external table) directly, never the cache. The `_SEARCH_CACHE` name suffix is deliberate —
  anyone who finds the object in `SHOW TABLES` should immediately read it as derived, not
  authoritative.
- **Staleness is a named, accepted risk, not solved here:** the cache is only as fresh as the last
  `--phase search --apply` run. It is **not** wired to Airflow's `refresh_serving` task yet — that
  wiring (already an open item from Addendum #2026-06-27) now also needs to re-run this `CREATE OR
  REPLACE` on every refresh, not just `ALTER EXTERNAL TABLE ... REFRESH`. Until that's wired, a
  human re-running the script after a Gold rebuild is the only refresh path. Flagging honestly
  rather than claiming an automatic sync that doesn't exist yet.
- **Reconstructible, same posture as the rest of the veneer:** the cache is dropped and rebuilt
  from `FACT_CHUNK` (itself reconstructible from S3) by re-running the script — **$0 loss**, same
  as every other object in this ADR.

## Addendum (2026-06-27 #4) — Cortex Search Service abandoned (trial-tier wall); native VECTOR similarity built instead; Addenda #2/#3 superseded

**Third real blocker, terminal this time:** the live `--apply` of Addendum #3's plan got past the
Dynamic-Table restriction (the cache table built and resynced correctly, 169/169 rows) but failed
on `CREATE CORTEX SEARCH SERVICE` itself:

```
AI function EMBED_TEXT_768 is not available for trial accounts.
```

Cortex Search Service's embedding step requires a Snowflake AI function gated off entirely on
trial-tier accounts. No SQL or schema workaround fixes this — only upgrading the account off the
trial tier would, which is a real billing decision on an account shared with the
`pharma_novartis_sttm` project, out of scope to decide unilaterally.

**Owner decision: abandon the managed Cortex Search Service. Addenda #2 and #3 above are
superseded, not deleted** (kept as the real record of what was tried and why each layer failed —
BYO-embedding-vs-managed-service, then Dynamic-Table-vs-external-table, then trial-tier — each a
genuine finding, not a wrong guess corrected in hindsight). **§B's original single-embedding-surface
rule is restored, not amended**: no Snowflake-side embedding model is used anywhere in this
project. The orphaned `FACT_CHUNK_SEARCH_CACHE` table (created, never consumed — the search
service that would have read it was never successfully created) was dropped.

**Built instead — native `VECTOR` similarity, zero second embedding surface, zero Cortex AI
functions:**
- `CREATE OR REPLACE VIEW PUBLIC.FACT_CHUNK_VECTOR` casts `FACT_CHUNK."embedding"` (lands as
  `VARIANT` via `INFER_SCHEMA`, per the Addendum-2026-06-27 naming/typing gotcha) to native
  `VECTOR(FLOAT, 768)`, filtering to non-null embeddings. **A view, not a copy** — this is squarely
  Clean-ERD's own "serving = view, never a duplicated physical table" line, the thing the cache-table
  workaround in Addendum #3 could not be (a view can't be a Dynamic Table's source either, but it
  doesn't need to be — plain `SELECT ... ORDER BY VECTOR_COSINE_SIMILARITY(...)` queries work fine
  against a view over an external table; only the *managed* search-service/Dynamic-Table machinery
  rejected external tables).
- Query pattern: embed the search text client-side with the same Gemini model/dimension
  `scripts/search_cli.py`'s `--semantic` already uses (`task_type=RETRIEVAL_QUERY`,
  `output_dimensionality=768`), then `SELECT ... VECTOR_COSINE_SIMILARITY("embedding_vec",
  <query_vector>::VECTOR(FLOAT,768)) AS sim FROM PUBLIC.FACT_CHUNK_VECTOR ORDER BY sim DESC`. Same
  BYO-Gemini vector, same shape of answer as the DuckDB `$0` fallback — this is the Snowflake-side
  mirror of that path, not a different feature.
- `provision_snowflake_serving.py`'s `search` phase now builds this view (`CREATE OR REPLACE VIEW`,
  same always-fresh-resync rationale as the cache table it replaces) + `GRANT SELECT` to
  `CREATIVE_INTEL_ROLE`, instead of the Cortex Search Service + cache-table statements.
**Verified for real:** see PROJECT_STATUS.md for the live query run and result evidence.

## Addendum (2026-06-27 #5) — last three "Still open" items closed: reconciliation test, COST_LOG.md, refresh_serving wiring

Addendum #4 above named three items still open after the native-`VECTOR` build. All three close
in this addendum, no new architecture decision beyond what #1–#4 already ratified:

1. **Checked-in, automated row-count+key reconciliation test** — `tests/reconcile_snowflake_serving.py`
   (new). Replaces 2026-06-27's manual one-off query with a re-runnable script: for each of the 8
   Gold models, reads the SAME S3 parquet two ways — DuckDB httpfs (ground truth) and the
   Snowflake external table via `CREATIVE_INTEL_ROLE` — and exact-matches both row **count** and
   the **key-column multiset** (`collections.Counter`, not a set, so a duplicate on either side is
   caught rather than dedup'd away). Both reads are deliberately "raw" (no dbt logical-view
   null-filter), so the two known `where 1=0` stubs (`bridge_asset_lineage`, `fact_extraction_run`)
   reconcile as 1/1 phantom-null rows on both sides, not a false-positive (same convention named in
   Addendum 2026-06-25 #2). NOT a CI gate — needs live AWS+Snowflake credentials, which `ci.yml`'s
   own header forbids ($0/no-cloud/no-secrets); registered in `tests/GATES.md` as a manual/Airflow
   gate instead. Added as a row there in this same change (adr-coupling discipline).
2. **`COST_LOG.md`** — created at repo root (gitignored per CLAUDE.md "What NOT To Commit" /
   `.gitignore`, a monitoring artifact, not a build output). Records the 2026-06-27 account/object
   creation dates and the now-abandoned Cortex Search Service attempt + cleanup, honestly flagging
   that the underlying **trial's own start date** is unverified from this repo (the account is
   shared with `pharma_novartis_sttm`, created before this project touched it).
3. **Airflow `refresh_serving` wired to real Snowflake calls** — `dags/creative_intel_pipeline.py`'s
   `refresh_serving` task, for `SERVING_BACKEND=snowflake_cortex` only (the default `duckdb_vss`
   path stays the honest no-op it always was — no separate index file exists to refresh). Shells
   out cross-venv (ADR-008's existing boundary, no new pattern) to (a) `scripts/provision_snowflake_serving.py`
   's new `refresh` phase (run as `--phase refresh --apply`):
   `ALTER EXTERNAL TABLE ... REFRESH` on all 8 Gold tables + a `CREATE OR REPLACE VIEW`
   resync of `FACT_CHUNK_VECTOR` (reuses `search_statements`' own view SQL, no duplicated DDL to
   drift), then (b) `tests/reconcile_snowflake_serving.py` from item 1 — a reconciliation mismatch
   raises and fails the Airflow task loud, the live trip-wire for this ADR's own veto line.

**FinOps preconditions (Cost discipline items 1–4) are now ALL satisfied**, closing the gate
ADR-008 named for why `refresh_serving`'s `snowflake_cortex` branch stayed a no-op until now:
(1) `COST_LOG.md` exists, (2) the $0 DuckDB-VSS fallback was proven first (2026-06-25), (3)
embeddings stay single-sourced BYO-Gemini throughout (§B, restored by Addendum #4), (4) the only
candidate for an idle always-billing object (the managed Cortex Search Service) was abandoned and
its orphaned cache table dropped — nothing idle is left running.

**Verified for real:** see PROJECT_STATUS.md's "Snowflake Cortex serving" item 3 for the dry-run
evidence and governance-gate re-run; a live `--apply` of the new `refresh` phase + a live run of
the reconciliation script against the real account were deferred pending owner confirmation
(ADR-005's own "provisioning stays owner-gated" line — `CREATE OR REPLACE VIEW` inside `refresh`
is still a CREATE statement, even though `ALTER ... REFRESH` itself is not).
