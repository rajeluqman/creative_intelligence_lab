# RBC Day-to-Day Task Map (100) — tagged by lab simulatability

> Context: ~2,500 pipelines, 1–2 new/month, Teradata+AWS legacy → Databricks+Snowflake target.
> Work is ~80–90% migration + maintenance. Tags: `✅` simulate in this lab · `⚠️` partial/adaptable
> · `❌` needs external (Teradata/Spark/Kafka) — **study, don't fake**. Tally: ~70 ✅ · ~15 ⚠️ · ~15 ❌.

## A. Monitoring & SLA (1–12)
1✅ overnight build/DAG status · 2✅ SLA met · 3⚠️ Airflow job review · 4✅ Snowflake credit usage ·
5❌ Glue monitor · 6⚠️ Teradata workload · 7✅ duration trend · 8✅ ingestion-complete validation ·
9⚠️ delayed/missing file · 10❌ Kafka lag · 11✅ cost review · 12✅ daily health report

## B. Incident / production support (13–27)  → **Sim #3**
13✅ investigate failed stage · 14✅ idempotent restart/backfill · 15✅ RCA + postmortem ·
16✅ fix broken SQL · 17⚠️ missing source file · 18✅ corrupt input / bad JSON · 19✅ schema mismatch ·
20✅ null/dup fix · 21✅ backfill · 22⚠️ Time-Travel/clone restore · 23✅ permission/secret (OIDC) ·
24✅ close ticket + known-issues · 25✅ extend alert (Slack) · 26✅ idempotency/retry · 27✅ logging

## C. Enhancement / change requests (28–42)  → **Sim #1 pattern**
28✅ add column e2e · 29✅ business rule · 30✅ modify transform + reconcile · 31✅ new source/client ·
32✅ update dim · 33✅ SCD change · 34✅ audit cols · 35✅ lineage edge · 36✅ parameterize ·
37✅ notification · 38✅ config-driven · 39✅ GE thresholds · 40✅ golden case · 41✅ data dictionary ·
42✅ STTM update

## D. Migration — core RBC motion (43–60)  → **Sim #1 + #4**
43❌ read/convert BTEQ · 44❌ proc→task/stream · 45⚠️ Teradata SQL→Spark/Snowflake · 46⚠️ dbt→PySpark
(Sim #2) · 47✅ row-count validate · 48✅ value/checksum reconcile · 49✅ STTM · 50✅ parallel-run ·
51✅ cutover plan · 52✅ rollback test · 53✅ migration ADR · 54⚠️ decommission legacy · 55⚠️ archive
code · 56✅ release notes · 57⚠️ Teradata SQL (QUALIFY/MULTISET) · 58✅ aggregate reconcile ·
59✅ sign-off gate · 60✅ post-implementation review

## E. Databricks / Spark (61–70)  → mostly ❌, **Sim #2** closes one
61⚠️ build notebook · 62❌ debug Spark · 63❌ partition/shuffle tune · 64❌ broadcast join ·
65❌ cache · 66❌ Delta OPTIMIZE · 67❌ VACUUM · 68❌ Z-order · 69❌ cluster sizing ·
70⚠️ map DuckDB perf-thinking → Spark

## F. Snowflake (71–80)
71✅ schema/warehouse · 72✅ warehouse sizing · 73✅ credit monitor · 74⚠️ clustering keys ·
75⚠️ streams · 76⚠️ tasks · 77✅ serving views (never dup tables) · 78⚠️ Time Travel · 79⚠️ zero-copy
clone · 80✅ external tables over Gold S3

## G. Data quality & reconciliation (81–90)  → **Sim #4**, your strength
81✅ row-count · 82✅ null · 83✅ dup · 84✅ FK/referential · 85✅ source-target reconcile ·
86✅ business-rule · 87✅ outlier/range (LLM score 1–5) · 88✅ freshness · 89✅ completeness · 90✅ profiling

## H. Governance, docs, delivery (91–100)
91✅ Confluence sync · 92✅ lineage contract · 93✅ ERD/DBML · 94✅ STTM/mapping · 95✅ code review
(7-agent cabinet) · 96✅ PR + CI gates · 97✅ scope ruling · 98✅ prod deploy (OIDC) ·
99✅ post-implementation review · 100✅ knowledge transfer (repo-as-KT)
