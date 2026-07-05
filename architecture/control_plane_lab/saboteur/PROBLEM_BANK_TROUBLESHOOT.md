# Problem Bank — Troubleshooting (100)

> Instructor sheet for @saboteur. During a drill only **Problem + Symptom** are revealed; Root
> cause + Fix direction are the answer key. Lvl: L1 detect/read · L2 diagnose/fix · L3 own the
> incident end-to-end (runbook phases 2/3/7/8 graded). Stacks: see README tag map.
> Every T-drill is graded against `INCIDENT_RUNBOOK.md` phases, not just the fix.

## T-ING — Ingestion & sources (14)
| ID | Problem | Symptom you see | Root cause | Fix direction | Stacks | Lvl |
|---|---|---|---|---|---|---|
| T-ING-01 | API token expires mid-run | Job green yesterday, today 401 halfway; partial batch landed | Token TTL < batch duration; no refresh logic | Refresh/re-auth per page; make batch resumable from last cursor | ALL | L2 |
| T-ING-02 | Rate-limit retry storm | 429s then provider blocks the key entirely | Naive immediate retry hammers the API | Exponential backoff + jitter; respect Retry-After; pool to cap concurrency | AF | L2 |
| T-ING-03 | Pagination silently drops last page | Row counts ~3% low vs source, no error anywhere | Loop exits on `len(page)<page_size` but API returns exact multiple | Loop on `next` cursor/token, not page size; reconciliation count gate | ALL | L3 |
| T-ING-04 | Source adds a new column | Strict-schema ingest rejects every batch since 03:00 | Upstream deployed without notice; schema contract strict by design | Decide: evolve schema (additive OK) vs quarantine; document contract with provider | S3,SPK | L2 |
| T-ING-05 | Source renames a column | No error; downstream KPI silently becomes NULL | Rename ≠ add: old col gone, mapping still selects it with NULL passthrough | Fail-fast on missing expected column at landing; STTM update; backfill | ALL | L3 |
| T-ING-06 | Late-arriving file | Daily batch ran at 06:00, file landed 06:20; empty partition "succeeded" | Time-triggered run, no data-availability check | Sensor/data-aware trigger on file arrival + zero-row guard that FAILS, not passes | AF,S3 | L1 |
| T-ING-07 | Zero-byte file delivered | Pipeline green, marts show 0 rows for the day | Provider export glitch; no row-count floor gate | GE volume expectation (min rows); alert provider; rerun on redelivery | GE,S3 | L1 |
| T-ING-08 | Unescaped delimiter in CSV text field | Column shift: names appear in amount column from row 40k | Naive split on comma; source has `"Smith, John"` unquoted | Proper CSV parser config/quoting; reject-lane for malformed rows; count rejects | ALL | L2 |
| T-ING-09 | Encoding mismatch (UTF-8 vs latin-1) | Customer names show `Ã©` mojibake in gold | Source exports latin-1; ingest assumes UTF-8 | Detect/declare encoding at landing; re-decode backfill; add encoding check | ALL | L2 |
| T-ING-10 | Duplicate file delivery | Revenue exactly 2x for one day | Provider redelivered same file with new name; loader appends | Idempotency by content hash (not filename) — the CIL asset_id lesson | S3 | L2 |
| T-ING-11 | Timezone drift at source | Events cluster oddly at midnight; day totals off vs source report | Source stamps local time, pipeline assumes UTC (or vice versa) | Declare tz at contract; normalize at Silver; backfill affected partitions | ALL | L2 |
| T-ING-12 | Upstream backfilled history | Yesterday's numbers changed but our copy didn't; auditors ask why | Source mutated old rows; our incremental only reads new watermark | Detect via periodic checksum-window reconciliation; re-pull changed window | ALL | L3 |
| T-ING-13 | Drive/SFTP permission revoked | Ingest 403 at 02:00; on-call paged | Service account removed from share during "cleanup" | Restore grant; add auth canary check that runs BEFORE the batch window | S3,AF | L1 |
| T-ING-14 | Field type flips int→string in JSON | Cast exception on 3% of records only | Provider now sends `"123"` for some records (mixed fleet during deploy) | Tolerant cast at Bronze parse + type expectation at Silver; quarantine mixed batch | LLM,S3 | L2 |

## T-ORC — Orchestration / Airflow (16)
| ID | Problem | Symptom you see | Root cause | Fix direction | Stacks | Lvl |
|---|---|---|---|---|---|---|
| T-ORC-01 | DAG vanished from UI | Consumers say "pipeline didn't run"; DAG not listed | Import error (syntax/missing dep) — check import-errors panel/logs | Fix import; add CI `py_compile`/DAG-import test so it can't merge broken | AF | L1 |
| T-ORC-02 | Task stuck in `queued` forever | Nothing running, queue grows | Pool/slot exhaustion or no worker of required queue type | Inspect pools/slots; free zombie slots; size pools deliberately | AF | L2 |
| T-ORC-03 | Zombie task | Task "running" 9 hours; no worker process exists | Worker died mid-task; heartbeat lost | Clear task instance; tune zombie detection; make task idempotent for rerun | AF | L2 |
| T-ORC-04 | Scheduler silently down | No runs since 04:00; UI loads fine | Scheduler crashed/OOM; webserver ≠ scheduler | Restart + monitor scheduler heartbeat with its own alert | AF | L1 |
| T-ORC-05 | Missed run after unpause | Paused 3 days, expected catch-up didn't happen | `catchup=False` — by design, but nobody knew | Explicit backfill command for the gap; document catchup policy per DAG | AF | L1 |
| T-ORC-06 | Backfill storm | Unpaused DAG launched 300 runs, source API rate-limited, bill spikes | `catchup=True` + 10-month-old `start_date` | Pause; set sane start_date/catchup; pools to cap; teach depends-on-design | AF | L2 |
| T-ORC-07 | Sensor eats a worker slot for hours | Other DAGs late; one sensor poking since 01:00 | Poke-mode sensor holds slot; upstream never landed | Deferrable operator / reschedule mode + timeout + on-timeout alert | AF | L2 |
| T-ORC-08 | XCom bloat | Metadata DB huge; tasks fail passing data | Team passing DataFrames through XCom | XCom for pointers only (paths/ids); data goes through storage | AF | L2 |
| T-ORC-09 | depends_on_past deadlock | Everything waiting; one ancient failed run at the head | `depends_on_past=True` + one unresolved old failure | Clear/mark the blocker consciously; question whether DOP is needed at all | AF | L2 |
| T-ORC-10 | Retry duplicates rows | Flaky network → retry succeeded → day counted twice | Task not idempotent; append semantics + auto-retry | Merge/overwrite-partition semantics; then retries are safe (design fix, not retry removal) | AF,DBT | L3 |
| T-ORC-11 | DST double-fire/skip | Job ran twice (or skipped) on DST transition day | Cron in local tz | Schedule in UTC; if business needs local, handle transition explicitly | AF | L2 |
| T-ORC-12 | Two runs write same partition | Corrupt/partial partition; counts nondeterministic | `max_active_runs>1` + non-atomic overwrite | Cap concurrency; write-then-swap (staging path + atomic publish) | AF,S3 | L3 |
| T-ORC-13 | Missing Variable/Connection after migration | `KeyError: conn_id` in fresh env only | Env config not in code; hand-created in old env | Externalize conn/vars into IaC/secrets manager; env-parity check in CI | AF | L1 |
| T-ORC-14 | Wrong day processed | "Yesterday's" job processed day-before-yesterday | `execution_date`/logical-date semantics misunderstood (interval END runs the job) | Teach interval semantics; use data_interval_start explicitly in code | AF | L2 |
| T-ORC-15 | Upgrade breaks operator imports | Post-upgrade: DeprecationWarning wall then ImportError | Provider-package paths moved between major versions | Pin providers; staged upgrade in sim first; import-test gate | AF | L2 |
| T-ORC-16 | Failure callback itself crashes | Pipeline failed at 02:00, NOBODY was alerted | `on_failure_callback` raised (bad Slack token) and died silently | Wrap callback in try/except + fallback channel; test the alert path itself (fire drill) | AF | L3 |

## T-STO — Storage / lake (12)
| ID | Problem | Symptom you see | Root cause | Fix direction | Stacks | Lvl |
|---|---|---|---|---|---|---|
| T-STO-01 | Sudden S3 403 | All writes fail 03:00; creds "unchanged" | IAM policy tightened / role trust edited by another team | Audit CloudTrail for the change; restore least-priv grant; ownership contract for shared roles | S3 | L2 |
| T-STO-02 | Partition path drift | New data invisible to readers; writer says success | Writer deployed `dt=YYYY-MM-DD` → readers expect `date=` (path contract broken) | Path contract as code (the CIL lineage-contract pattern); migrate or alias; backfill catalog | S3 | L2 |
| T-STO-03 | Small-files explosion | List operations minutes-long; query planning dominates runtime | Per-record/per-minute writes; no compaction | Compaction job (OPTIMIZE/repartition); write batching upstream | S3,SPK | L2 |
| T-STO-04 | Accidental prefix delete | Analyst script wiped `silver/2026-06/` | Broad delete perms + wildcard script | Restore from versioning/replica; then: deny-delete policy, versioning on, TTL as the ONLY deleter (ADR-007 pattern) | S3 | L3 |
| T-STO-05 | Lifecycle rule deleted needed data | Month-old landing files gone; reprocess impossible | TTL rule scoped too broad (hit curated prefix, not just landing) | Restore if possible; scope lifecycle by prefix + tag; guarded-delete manifest check | S3 | L3 |
| T-STO-06 | Reader misses just-written files | Downstream job sees N-2 files, later N — flaky counts | Listing raced the write job (no completion signal) | Publish a `_SUCCESS`/manifest marker; readers consume manifest, never raw listing | S3,SPK | L2 |
| T-STO-07 | Cross-region surprise | Job 4x slower + egress line item appears | New bucket created in wrong region | Co-locate compute/storage; region check in provisioning gate | S3 | L1 |
| T-STO-08 | KMS key rotated, decrypt fails | `KMS.AccessDenied` on old objects only | New key policy missing pipeline role; old objects on old key | Grant decrypt on both keys; key-rotation runbook incl. data-plane consumers | S3 | L2 |
| T-STO-09 | Delta log checkpoint corruption | Table unreadable: `_delta_log` parse error | Manual file deletion inside `_delta_log/` (someone "cleaned up") | Restore log from backup/time-travel-capable replica; NEVER hand-touch _delta_log; deny-list it | SPK | L3 |
| T-STO-10 | VACUUM broke time travel | Rollback to yesterday fails: files missing | VACUUM retention < time-travel window needed | Align retention policy with rollback SLA; document the tradeoff | SPK | L2 |
| T-STO-11 | Storage bill doubles in a month | Cost alert; no new pipelines | Versioning on + no noncurrent-version expiry; failed-run debris | Lifecycle for noncurrent versions + staging cleanup; cost dashboards per prefix | S3 | L2 |
| T-STO-12 | Concurrent Delta writers conflict | `ConcurrentModificationException` nightly | Two jobs MERGE same table same window | Serialize via orchestration dependency, or partition-disjoint writes; retry-on-conflict last | SPK,AF | L2 |

## T-TRF — Transform (dbt / Spark / SQL) (18)
| ID | Problem | Symptom you see | Root cause | Fix direction | Stacks | Lvl |
|---|---|---|---|---|---|---|
| T-TRF-01 | Executor OOM | Spark stage dies `OutOfMemory`, retries, dies again | Skewed join key (one customer = 30% of rows) | Identify skew (task-duration histogram); salt/AQE skew handling; broadcast the small side | SPK | L2 |
| T-TRF-02 | One task 20x longer than siblings | Job "hangs" at 199/200 tasks | Hot partition (null key bucket / one giant client) | Same skew toolkit; consider null-key pre-filter (nulls shouldn't join anyway) | SPK | L2 |
| T-TRF-03 | Job 10x slower, same data | No code change; shuffle spill metrics huge | Input grew past memory threshold; spill to disk began | Right-size shuffle partitions/executor memory; reduce shuffle (pre-aggregate) | SPK | L2 |
| T-TRF-04 | Incremental undercounts | Month-end total < source; daily runs all green | Late rows older than incremental watermark silently skipped | Lookback window on incremental; late-data policy documented; periodic full reconcile | DBT | L3 |
| T-TRF-05 | Rerun duplicates rows | Yesterday rerun → 2x rows for that day | Incremental strategy = append, no unique key | `unique_key`/merge or delete+insert by partition; idempotency test in CI | DBT | L2 |
| T-TRF-06 | Accidental full refresh | 6-hour run, history table truncated-rebuilt, SCD history lost | `--full-refresh` flag on incremental with pre-hook truncate | Restore from snapshot/backup; protect: `full_refresh: false` config on protected models | DBT | L3 |
| T-TRF-07 | Two `is_current` rows per entity | Downstream joins fan out; counts inflate slowly | SCD2 merge-expire raced / snapshot ran twice in window | Repair validity windows; add uniqueness gate on (key, is_current=true); serialize snapshot | DBT,SPK | L3 |
| T-TRF-08 | Snapshot misses changes | Attribute changed at source, SCD2 shows no new version | `check` strategy column list missing the changed column | Snapshot all tracked columns explicitly / hash-compare strategy; test with golden change | DBT | L2 |
| T-TRF-09 | Row count 100x after "small change" | Join fanout: cartesian on partial key | Join key not unique on one side (grain violation, not a join bug) | Fix grain upstream or aggregate before join; grain test on both sides (Clean-ERD rule) | ALL | L2 |
| T-TRF-10 | Rows silently vanish in join | Gold has 8% fewer orders than Silver | NULL join keys drop in INNER join | Decide: null-key quarantine lane vs LEFT join + unknown-member dim | ALL | L2 |
| T-TRF-11 | Negative revenue total | Monthly aggregate overflows to negative | int32 sum over threshold | BIGINT/DECIMAL; range expectation catches next time | ALL | L1 |
| T-TRF-12 | Pennies don't reconcile | Gold vs source differs by 0.03 across 10M rows | float arithmetic for money | DECIMAL end-to-end; reconciliation tolerance = 0 for money | ALL | L2 |
| T-TRF-13 | KPI is NULL for some days | Division result null, dashboard gap | Divide-by-zero returns NULL and propagates through AVG | NULLIF + explicit zero-denominator policy (0? null? exclude?) — business call, documented | ALL | L1 |
| T-TRF-14 | Model built from stale upstream | Numbers right after full build, wrong after selective build | `--select model` without `+` upstream; ref graph bypassed | Teach selection syntax; state-based builds; CI builds with deps | DBT | L1 |
| T-TRF-15 | Nondeterministic sample in CTE | Same query, different results per run | CTE with LIMIT/no ORDER BY evaluated per-reference | Deterministic ordering or materialize the sample once | ALL | L2 |
| T-TRF-16 | Metrics shifted 8 hours | All hourly metrics offset after "tz fix" | TZ conversion applied twice (source already UTC) | Single conversion point (Silver), assert with known-event fixture | ALL | L2 |
| T-TRF-17 | MERGE fails: multiple source rows | `Duplicate row in MERGE source` error nightly | Dedup step upstream removed; source no longer unique on merge key | Restore dedup with deterministic tie-break (latest updated_at, then id) | SPK,DBT | L2 |
| T-TRF-18 | Nulls creep into parsed field | `standalone_score` null-rate rising weekly | Regex/parse pattern doesn't match a NEW format variant; silent `else null` | Parse-failure counter + threshold alert; quarantine unparsed for pattern review | LLM,ALL | L3 |

## T-DQ — Data quality (12)
| ID | Problem | Symptom you see | Root cause | Fix direction | Stacks | Lvl |
|---|---|---|---|---|---|---|
| T-DQ-01 | Freshness breach unnoticed 2 days | Consumer discovers stale dashboard before the team does | No freshness expectation; alerts only on task FAILURE, not on no-run | Freshness check on the TABLE (not the job); detection-source postmortem | GE | L2 |
| T-DQ-02 | Volume anomaly | Today's rows = 8% of daily average, all gates green | Only schema checks existed; volume never gated | GE volume expectation vs trailing window; route to quarantine on breach | GE | L1 |
| T-DQ-03 | Null spike in critical column | 40% nulls in `customer_id` since 03:00 | Upstream JOIN change; nulls flowed through | Null-rate expectation + fail-fast at Silver; trace to source; backfill | GE | L1 |
| T-DQ-04 | Duplicate PKs in gold | BI shows double-counted orders | Merge key drift after refactor | Uniqueness test on every PK (dbt test/GE); find merge bug; dedupe + backfill | DBT,GE | L2 |
| T-DQ-05 | Orphan facts | 3% fact rows have no dim match | Dim load ran AFTER fact (dependency inversion) | Relationship test + orchestration dependency fix; late-dim policy (unknown member) | DBT | L2 |
| T-DQ-06 | Negative amounts appear | `amount < 0` on refunds-not-modeled | Source encodes refunds as negatives; model assumed non-negative | Business ruling: separate refund flow vs allow negatives — document + range test | GE | L2 |
| T-DQ-07 | Future timestamps | Events dated 2099 in fact table | Source sentinel value / fat-finger; no upper-bound check | Range expectation (`<= now + tolerance`); quarantine offenders | GE | L1 |
| T-DQ-08 | Distribution drift | Category share shifted 20pp overnight; model/report assumptions break | Upstream enum remap (category consolidation) nobody announced | Drift monitor on key categoricals; contract with upstream; remap table | GE | L3 |
| T-DQ-09 | LLM output schema drift | Parser nulls spike after provider model update | Response key/format changed (`chunk_theme`→`chunkTheme`) | Golden-dataset regression + response-schema gate at parse; pin model version | LLM,GE | L2 |
| T-DQ-10 | LLM invents enum value | `sentiment='enthusiastic'` — not in allowed set | Non-deterministic output; value-set gate missing | Allowed-set expectation; map-or-quarantine policy; prompt tightened | LLM,GE | L2 |
| T-DQ-11 | Totals don't reconcile to source | Gold revenue ≠ source system by 0.4% | Multiple small leaks: rejected rows + join drops + late data | Build a loss-accounting query: every source row lands, rejects, or is explained (100% accounting) | ALL | L3 |
| T-DQ-12 | DQ gate passes everything | Suite green for 3 months incl. a day you KNOW was bad | Expectation suite pointed at wrong/empty asset since a rename | Test-the-tests: seeded-failure canary (mutate a copy, expect red) run periodically | GE | L3 |

## T-SRV — Serving / warehouse (10)
| ID | Problem | Symptom you see | Root cause | Fix direction | Stacks | Lvl |
|---|---|---|---|---|---|---|
| T-SRV-01 | External table stale | Gold parquet updated; Snowflake shows old data | `ALTER EXTERNAL TABLE ... REFRESH` not part of pipeline | Refresh step post-write (or auto-refresh notif); staleness check in reconcile script | SF | L1 |
| T-SRV-02 | First-query latency complaints | "Dashboard slow every morning" | Warehouse auto-suspends overnight; cold resume + cold cache | Business call: pre-warm schedule vs accept + comms; don't oversize to hide it | SF | L1 |
| T-SRV-03 | Warehouse credit cap hit mid-day | Queries error at 14:00; monitor tripped | Runaway query + monthly monitor threshold | Find offender in query history; statement timeout; raise cap consciously not reflexively | SF | L2 |
| T-SRV-04 | New table invisible to analysts | "Table doesn't exist" for role ANALYST_RO | GRANT missing (no future grants configured) | `GRANT ... ON FUTURE TABLES` / grant step in provisioning script — the RBAC drill | SF | L1 |
| T-SRV-05 | View breaks after model rename | Dashboards 500; view references dropped column | Serving view coupled to physical names; rename shipped without view update | Contract: serving views in same PR as renames; view-compile gate in CI | SF,DBT | L2 |
| T-SRV-06 | Query queueing | Concurrency saturated at 09:00 daily standup | One warehouse for ETL + BI + ad-hoc | Workload isolation: separate warehouses; queue metrics per workload | SF | L2 |
| T-SRV-07 | Result cache hides staleness | "It's fast now" — but data is old; debugging confused | Cached result returned; underlying refresh actually failing | Recognize cache in query profile; fix the refresh, don't trust the speed | SF | L1 |
| T-SRV-08 | BI refresh fails at 06:00 | Power BI dataset error: auth | Service principal secret expired (90-day policy nobody tracked) | Rotate + secret-expiry calendar/alert; longer-term: managed identity | SF,FAB | L1 |
| T-SRV-09 | Two dashboards disagree | "Revenue" differs 3% between two reports | Metric defined twice with different filters (definition fork) | Single semantic definition in gold/metrics layer; deprecate one; governance note | ALL | L3 |
| T-SRV-10 | Tenant sees another tenant's rows | Client A's search returns Client B asset | Missing tenant filter in serving view / RLS policy gap (CIL multi-client class) | IMMEDIATE contain (revoke/patch view), incident comms, audit exposure window, RLS test in CI | SF | L3 |

## T-SEC — Security & access (8)
| ID | Problem | Symptom you see | Root cause | Fix direction | Stacks | Lvl |
|---|---|---|---|---|---|---|
| T-SEC-01 | API key committed to git | Secret scanner (or a stranger's email) flags a key in history | `.env` committed / key pasted in notebook | Rotate FIRST, then purge history, audit usage logs for abuse window, add pre-commit scan | ALL | L3 |
| T-SEC-02 | Secret rotated, pipeline not updated | 401 cascade at 02:00 after security team rotation | No consumer inventory for the secret | Update env; build secret→consumers map; rotation runbook includes consumers | ALL | L2 |
| T-SEC-03 | PII in logs | Customer emails visible in Airflow task logs | Debug print of full row; logs retained 30d, broadly readable | Scrub/mask in logging layer; log-retention policy; who-read-logs audit | AF | L2 |
| T-SEC-04 | Over-privileged pipeline role | Audit finds ETL role can DROP any table + read HR schema | Convenience grants accreted over time | Least-privilege refit: inventory actual usage from query history → new role → shadow-run → swap | SF,S3 | L3 |
| T-SEC-05 | Bucket accidentally public | Security scanner: landing bucket world-readable since Tuesday | Broad policy edit for a "quick share" | Close, then audit access logs for the exposure window, disclose per policy, block-public-access org-wide | S3 | L3 |
| T-SEC-06 | Cross-tenant path violation | Client A asset found under Client B prefix | Ingest script defaulted client_id when env var unset | The CIL lineage-contract class: no silent defaults; contract gate + quarantine + re-ingest | S3 | L2 |
| T-SEC-07 | TLS cert expired on internal endpoint | Ingest fails `SSL: CERTIFICATE_VERIFY_FAILED` | Internal CA cert expired; nobody owned renewal | Renew + expiry monitoring; do NOT "fix" by disabling verification (the junior trap) | ALL | L1 |
| T-SEC-08 | Departed employee's key still active | Audit: personal PAT running a prod cron | Offboarding checklist missed machine credentials | Migrate to service identity; offboarding includes credential inventory | ALL | L2 |

## T-INF — Infra / environment (10)
| ID | Problem | Symptom you see | Root cause | Fix direction | Stacks | Lvl |
|---|---|---|---|---|---|---|
| T-INF-01 | Dependency conflict after upgrade | `pip` resolver error / import crash on deploy | Unpinned transitive dep moved major version | Pin + lockfile; staged dep-upgrade PRs with CI import test | ALL | L1 |
| T-INF-02 | Two venvs, wrong python | Script works in shell, fails under scheduler | Airflow venv ≠ pipeline venv (CIL ADR-008 class) | Explicit cross-venv invocation contract; document which venv owns what | AF | L2 |
| T-INF-03 | Worker disk full | Crash mid-write; partial files left behind | Temp/spill files accumulated; no cleanup | Clean temp on start (not just exit); disk alert at 80%; partial-file quarantine sweep | ALL | L2 |
| T-INF-04 | Image pull failure | K8s/task start error: tag not found | Mutable `latest` tag repointed/deleted | Pin digests; retain images; staging pull-test before prod rollout | ALL | L1 |
| T-INF-05 | Driver OOM | `collect()` on 50M rows kills the driver | Result pulled to driver for a "quick check" | Aggregate/sample in-engine; hard rule: no unbounded collect in prod code | SPK | L1 |
| T-INF-06 | New firewall kills API calls | Timeouts to provider since network change | Egress rule tightened; pipeline CIDR not allow-listed | Allow-list; dependency map of pipeline↔external endpoints for change review | ALL | L2 |
| T-INF-07 | Cloud quota hit | 5th concurrent Glue job won't start end-of-month | Account concurrency limit; batch pileup at month-end | Stagger schedule/pool; quota increase request with usage evidence | SPK,AF | L2 |
| T-INF-08 | Intermittent auth failures | ~2% of calls fail signature validation | Clock skew on one worker (NTP drift) | Fix NTP; add skew to intermittent-auth debug checklist | ALL | L3 |
| T-INF-09 | Region outage | Provider region degraded 4 hours mid-batch | Single-region design (deliberate, cost) | Execute the documented degrade choice: wait + comms vs failover; postmortem the SLA math | ALL | L3 |
| T-INF-10 | CA bundle outdated in container | SSL errors only in the container, not on host | Old base image; CA store stale | Rebuild on maintained base; scheduled base-image refresh | ALL | L1 |
