# CIL Injectable Map — which bank T-IDs run against this repo's real stack today

> A **mapping file**, not 100 inject scripts (per the 2026-07-04 handover, U3). CIL's stack is
> DuckDB/dbt + S3 + Airflow + Snowflake serving + Great Expectations + Gemini/LLM extraction —
> **no Spark/Databricks, no Fabric/OneLake** (`CLAUDE.md` stack boundary, ADR-001/004/005).
> "Injectable" here means: every stack tag on that bank row (`../README.md`'s tag map) is one CIL
> actually has. A row tagged `SPK` or `FAB` anywhere is **not** injectable in CIL as-is — those
> stacks belong to the sibling pipeline_retrofit repos (home-credit/olist/paysim/Volve) or
> migration_fiber_home_credit_risk, not this repo. This is a classification pass over
> [PROBLEM_BANK_TROUBLESHOOT.md](../../../architecture/control_plane_lab/saboteur/PROBLEM_BANK_TROUBLESHOOT.md)'s
> existing 100 rows — it does not add, renumber, or edit any row.
>
> **86 of 100 are injectable in CIL today; 14 need Spark and/or Fabric** (see the excluded list
> per category below). `inject.py`/`reset.py` implement mutate functions **on demand**, one at a
> time, as a drill is actually authored for that ID — this file is the lookup, not the build.

## T-ING — Ingestion & sources (13/14 injectable)
All except **T-ING-04** (`S3,SPK` — schema-evolution-on-write is framed as a Spark-side decision
in the bank; CIL's ingestion is the Gemini extraction step, not a Spark writer).

## T-ORC — Orchestration / Airflow (16/16 injectable)
All — every row is `AF` or `AF,DBT`, and CIL runs real local Airflow (ADR-008) + dbt-duckdb.

## T-STO — Storage / lake (7/12 injectable)
Injectable: T-STO-01, 02, 04, 05, 07, 08, 11.
Excluded (need Spark): T-STO-03 (small-files, Spark-compaction framing), T-STO-06 (`S3,SPK`
manifest-vs-listing race), T-STO-09 (Delta log corruption — Delta is Databricks-specific),
T-STO-10 (Delta VACUUM/time-travel), T-STO-12 (concurrent Delta writers).

## T-TRF — Transform (13/18 injectable)
Injectable: T-TRF-04, 05, 06, 08, 09, 10, 11, 12, 13, 14, 15, 16, 18 — all dbt-duckdb-shaped
(incremental, snapshot, grain, NULLs, casting, LLM parse drift).
Excluded (need Spark): T-TRF-01, 02, 03 (executor OOM / skew / shuffle-spill — no Spark executor
in CIL), T-TRF-07 (SCD2 merge-expire race, framed `DBT,SPK` — doubly not injectable today: no
Spark, AND CIL has no *built* SCD2 table yet either, `bridge_client_asset_curation` is a named,
deliberately-not-built v1.5 model per
[ERD_consolidated.md](../../../architecture/ERD_consolidated.md) §6 — the DBT-only variant of
this drill would need that model built first, separate from the Spark gap), T-TRF-17 (`SPK,DBT` MERGE
dedup — CIL has no Spark MERGE surface).

## T-DQ — Data quality (12/12 injectable)
All — Great Expectations + dbt tests + the LLM-output gates are exactly CIL's real DQ layer.

## T-SRV — Serving / warehouse (9/10 injectable)
All except **T-SRV-08** (`SF,FAB` — Power BI/Fabric service-principal rotation; CIL's real BI
surface is Power BI over Snowflake per `CLAUDE.md`'s stack table, but the row's Fabric-specific
framing (OneLake service principal) doesn't map onto CIL's actual Snowflake auth path, which is
plain username/password env vars — `SNOWFLAKE_USER`/`SNOWFLAKE_PASSWORD` in
`scripts/provision_snowflake_serving.py` — not a Fabric/OneLake service principal at all).

## T-SEC — Security & access (8/8 injectable)
All — this is the category ADR-014 (this same session) built real infrastructure for. T-SEC-01
and T-SRV-04 are the two with drills + inject/reset built this session
(`../../drills/T-SEC-01_leaked_key.md`, `../../drills/T-SRV-04_rbac_future_grant.md`); the
remaining 7 T-SEC rows are injectable-in-principle, drills TBD on demand.

## T-INF — Infra / environment (8/10 injectable)
Injectable: T-INF-01, 02, 03, 04, 06, 08, 09, 10.
Excluded (need Spark): T-INF-05 (`SPK` driver OOM on `.collect()`), T-INF-07 (`SPK,AF` Glue
concurrency quota — CIL's own quota-shaped incidents would be Airflow-pool or Snowflake-warehouse
concurrency instead, which T-ORC-02/T-SRV-03 already cover).

## Using this map
1. Pick an ID marked injectable above.
2. Check `../README.md`'s existing fault catalog (`dq_*`/`rec_*`/`av_*`/`perf_*`) for a fault id
   that already covers it — several T-IDs map onto the SAME fault (e.g. T-DQ-04 duplicate PKs =
   `dq_dup_pk`, already built as the `T-L01` template drill).
3. If no fault id exists yet, author one in `../inject.py` (`FAULTS` dict) + a drill in
   `../../drills/` + a gated solution in `../../.solutions/` — following the shape of
   `T-L01_dup_pk.md` / `T-SRV-04_rbac_future_grant.md` (self-contained, no dbt sim scaffold
   required) or, once `../../sim_dbt/` has real seeds/models, the full `inject.py <fault_id>` path.
