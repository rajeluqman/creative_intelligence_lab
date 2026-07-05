# Problem Bank — Optimization (100)

> Instructor sheet for @saboteur optimization drills. Discipline per CARD_FORMAT: **baseline
> number first, ONE change, re-measure, keep/revert** — a drill with no before/after number is
> not passed. "Signal" = when this lever is the right one (optimizing without the signal =
> speculative tuning, the junior mistake). All drills run in sim/staging first.

## O-LAY — Storage layout (14)
| ID | Task | Signal (when to apply) | Action | Proof metric | Stacks | Lvl |
|---|---|---|---|---|---|---|
| O-LAY-01 | Partition by date | Full scans for date-filtered queries | Re-layout by `dt=` partition; readers prune | bytes-scanned before/after | S3,SPK | L1 |
| O-LAY-02 | Fix over-partitioning | 50k partitions of 2MB each; planning > execution | Coarser key (day not hour; drop 2nd key) | file count, planning time | S3,SPK | L2 |
| O-LAY-03 | Compact small files | Millions of KB-size files | OPTIMIZE/compaction job; batch upstream writes | avg file size → 128MB–1GB; runtime | SPK,S3 | L1 |
| O-LAY-04 | Right-size row groups | Poor scan parallelism / row-group per file =1 huge | Tune parquet row-group size for engine | scan time, memory | DDB,SPK | L2 |
| O-LAY-05 | Choose compression codec | CPU-bound scans (gzip) or bloated storage (none) | Benchmark snappy vs zstd on real data | size × scan-time table | ALL | L2 |
| O-LAY-06 | Z-ORDER / clustering | Selective filters on non-partition column | Z-order/cluster on that column | files pruned %, query time | SPK | L2 |
| O-LAY-07 | Tune VACUUM + log retention | Storage creep on Delta; slow log replay | Retention aligned to rollback SLA; scheduled vacuum | storage GB, table-open time | SPK | L2 |
| O-LAY-08 | Drop unused wide columns from Silver | 200-col table, marts read 30 | Prune at Silver; keep Bronze full | scan bytes, storage | ALL | L2 |
| O-LAY-09 | Sort within files | Min/max stats useless (random order) | Sort on filter key at write | files skipped via stats | SPK,DDB | L3 |
| O-LAY-10 | Bucketing for repeated join | Same big-table join key shuffled nightly | Bucket both sides on key | shuffle bytes eliminated | SPK | L3 |
| O-LAY-11 | JSON→parquet at landing edge | Every downstream reader re-parses JSON | One conversion step post-landing (keep raw JSON) | downstream runtime sum | S3 | L1 |
| O-LAY-12 | Hot/cold tiering | Old partitions read ~never, priced hot | Lifecycle to IA/archive tier by age | storage cost/month | S3 | L1 |
| O-LAY-13 | Selective denormalization | Read-heavy join repeated in every dashboard query | Materialize joined gold table (view→table, measured) | p95 dashboard query time | SF,DBT | L3 |
| O-LAY-14 | Delta checkpoint interval | Many-commit table slow to open | Tune checkpoint frequency | table-open/planning time | SPK | L3 |

## O-QRY — SQL & dbt modeling (16)
| ID | Task | Signal | Action | Proof metric | Stacks | Lvl |
|---|---|---|---|---|---|---|
| O-QRY-01 | Kill SELECT * | Wide scans for narrow outputs | Explicit column lists in models | bytes scanned | ALL | L1 |
| O-QRY-02 | Filter before join | Join then filter in plan; huge intermediate | Push predicate into CTE/subquery pre-join | intermediate rows, runtime | ALL | L1 |
| O-QRY-03 | De-correlate subquery | Per-row subquery execution in plan | Rewrite as join/window | runtime, plan shape | ALL | L2 |
| O-QRY-04 | Window over self-join | Self-join for prev-row/rank | LAG/ROW_NUMBER instead | runtime, readability | ALL | L2 |
| O-QRY-05 | Efficient dedupe | DISTINCT over 40 columns to kill dupes | ROW_NUMBER()=1 by key + tie-break (QUALIFY) | runtime + correctness (deterministic) | ALL | L2 |
| O-QRY-06 | Materialize reused CTE | Same CTE computed in 4 models | Intermediate model, built once | total build time | DBT | L2 |
| O-QRY-07 | Full rebuild → incremental | Nightly rebuilds 3yr of history for 1 new day | Incremental with unique_key/merge | build time, compute cost | DBT | L2 |
| O-QRY-08 | Incremental lookback window | Late data forces periodic full refresh | `WHERE ts > max(ts) - interval N` pattern | correctness at fraction of full cost | DBT | L3 |
| O-QRY-09 | Join order by selectivity | Optimizer picks bad order (stats missing) | Reorder/hint: most selective first; fix stats | runtime, plan | ALL | L2 |
| O-QRY-10 | Remove DISTINCT-as-bandaid | DISTINCT hiding a fanout join | Fix grain (aggregate/bridge) — perf AND correctness | rows pre-DISTINCT, runtime | ALL | L3 |
| O-QRY-11 | Pre-aggregate before join | Fact-to-fact join at raw grain, then GROUP BY | Aggregate each side to target grain first | shuffle/intermediate size | ALL | L2 |
| O-QRY-12 | UNION ALL where safe | UNION forcing dedupe sort on disjoint sets | UNION ALL when overlap impossible (prove it) | runtime | ALL | L1 |
| O-QRY-13 | Approximate distinct | Exact COUNT(DISTINCT) on 1B rows for a trend chart | APPROX_COUNT_DISTINCT/HLL where tolerance OK (business sign-off) | runtime; error bound documented | SF,SPK | L2 |
| O-QRY-14 | Prune trivial model sprawl | 40 models of `SELECT *` renames; DAG overhead | Collapse pass-through models | build time, DAG size | DBT | L2 |
| O-QRY-15 | Right materialization per model | Ephemeral recomputed 6x / table rebuilt never-read | Audit usage → view/table/incremental per pattern | total build time | DBT | L2 |
| O-QRY-16 | Pushdown-friendly extract query | Extract pulls full table, filters in pipeline | WHERE/columns at source; verify index use (EXPLAIN) | rows transferred, source load | ALL | L2 |

## O-SPK — Spark / Databricks / Glue (14)
| ID | Task | Signal | Action | Proof metric | Stacks | Lvl |
|---|---|---|---|---|---|---|
| O-SPK-01 | Broadcast the small side | Shuffle join with a 10MB dim | Broadcast hint/threshold | shuffle bytes → ~0, stage time | SPK | L1 |
| O-SPK-02 | Salt/AQE the skewed join | One task = 90% of stage time | Salting or AQE skew-join on | max/median task-time ratio | SPK | L2 |
| O-SPK-03 | Tune shuffle partitions | 200 default: thousands of empty tasks OR few giant ones | Set to data size / target-partition (or AQE coalesce) | task count, stage time | SPK | L1 |
| O-SPK-04 | Verify AQE on & effective | Old cluster config; static plans | Enable AQE; confirm runtime plan changes | plan diff, runtime | SPK | L1 |
| O-SPK-05 | Cache with proof | Same DF recomputed in 3 actions (lineage re-executes) | cache() + unpersist(); measure BOTH ways | end-to-end time (cache can LOSE) | SPK | L2 |
| O-SPK-06 | Kill the collect() | Driver pulls millions of rows for a count/sample | Aggregate in-engine; limit samples | driver memory, runtime | SPK | L1 |
| O-SPK-07 | Repartition vs coalesce at write | 2000 tiny output files, or 1 giant | Right final partition count; know shuffle vs no-shuffle | output file profile | SPK | L1 |
| O-SPK-08 | Replace Python UDF | Row-at-a-time UDF dominates stage | Built-in fns / pandas UDF | stage time (often 5–10x) | SPK | L2 |
| O-SPK-09 | Arrow for pandas boundary | Slow toPandas/from_pandas | Enable Arrow; batch size tune | conversion time | SPK | L2 |
| O-SPK-10 | Executor sizing sweep | OOMs (too thin) or idle cores (too fat) | Sweep 2-3 configs, measure, pick | cost × runtime frontier | SPK | L3 |
| O-SPK-11 | Dynamic allocation bounds | Cluster idle-billing between stages | Min/max executors matched to stage profile | cluster-hours per run | SPK | L2 |
| O-SPK-12 | Verify partition pushdown | Input-read = whole table despite filter | Fix filter type mismatch/casting blocking pruning | input bytes read | SPK | L2 |
| O-SPK-13 | Explicit schema on read | inferSchema double-reads huge CSV/JSON | Declare schema (from contract) | read time halves | SPK | L1 |
| O-SPK-14 | mapPartitions for setup cost | Per-row DB/API connection setup | Per-partition init, reuse connection | connections opened, runtime | SPK | L3 |

## O-DDB — DuckDB (8)
| ID | Task | Signal | Action | Proof metric | Stacks | Lvl |
|---|---|---|---|---|---|---|
| O-DDB-01 | memory_limit + threads | Spill/underuse on the codespace box | PRAGMA tuning to box reality | runtime, spill | DDB | L1 |
| O-DDB-02 | Query parquet in place | Load-then-query for one-shot transforms | Direct `read_parquet` scan; skip the load | end-to-end time | DDB | L1 |
| O-DDB-03 | Confirm pushdown on S3 scans | Full-object GETs for selective query | Filter/projection pushdown; check EXPLAIN + bytes | S3 bytes transferred | DDB | L2 |
| O-DDB-04 | Row-group size for DuckDB | Tiny row groups → per-group overhead | Rewrite hot parquet with larger groups | scan time | DDB | L2 |
| O-DDB-05 | Vectorize the Python loop | Row-loop in Python around DuckDB | Push logic into SQL (CASE/window/list fns) | runtime (often 100x) | DDB | L1 |
| O-DDB-06 | COPY for bulk I/O | INSERT-per-row export | COPY TO/FROM | rows/sec | DDB | L1 |
| O-DDB-07 | EXPLAIN ANALYZE the slow join | One mart 10x slower; no idea why | Read the profile: build side, hash size, spill | before/after plan + time | DDB | L2 |
| O-DDB-08 | Persistent catalog for repeated runs | Re-registering/re-scanning every invocation | Persistent .duckdb file where it wins (vs ephemeral rule — sim only) | warm-run time | DDB | L3 |

## O-WH — Warehouse / Snowflake (12)
| ID | Task | Signal | Action | Proof metric | Stacks | Lvl |
|---|---|---|---|---|---|---|
| O-WH-01 | Right-size warehouse | Queueing or local-disk spill in profile — or neither (oversized) | Size to evidence, not vibes | queue time, spill, cost | SF | L2 |
| O-WH-02 | Aggressive auto-suspend | Warehouse idles hot between hourly loads | 60s suspend; accept cold-start tradeoff consciously | idle credits/day | SF | L1 |
| O-WH-03 | Workload isolation | BI queries queue behind ETL merges | Separate warehouses per workload | per-workload queue metrics | SF | L2 |
| O-WH-04 | Clustering key with proof | Large table, selective filters, bad pruning stats | Cluster; watch automatic clustering COST too | partitions pruned %, net cost | SF | L3 |
| O-WH-05 | Materialized view for hot aggregate | Same GROUP BY burning credits hourly | MV (or scheduled table); count maintenance cost | credits: query vs maintain | SF | L2 |
| O-WH-06 | Respect the result cache | "Optimization" measured on cached reruns | Disable cache for benchmarks; use cache in prod knowingly | honest baseline | SF | L1 |
| O-WH-07 | Read the query profile | Slow query, everyone guessing | Profile: find the fat node (join explode? scan? sort?) | targeted fix from evidence | SF | L2 |
| O-WH-08 | Column-prune external tables | SELECT * over external parquet | Explicit columns; verify scan reduction | bytes scanned | SF | L1 |
| O-WH-09 | Partition columns on external tables | External table scans all files always | Register partition cols from path; prune | files scanned | SF | L2 |
| O-WH-10 | Guardrails: monitor + timeout | One runaway query ate the month's credits | Resource monitor + STATEMENT_TIMEOUT defaults | max single-query burn | SF | L1 |
| O-WH-11 | Search optimization — only if proven | Point lookups on big table are the ACTUAL pattern | Enable + measure; it costs storage/credits | lookup p95 vs added cost | SF | L3 |
| O-WH-12 | Batch the tiny INSERTs | Thousands of single-row INSERTs from a script | Stage + bulk COPY | load time, credits | SF | L1 |

## O-ORC — Orchestration efficiency (10)
| ID | Task | Signal | Action | Proof metric | Stacks | Lvl |
|---|---|---|---|---|---|---|
| O-ORC-01 | Sensors → deferrable | Worker slots parked on poking sensors | Deferrable operators/triggerer | occupied slots, worker count | AF | L2 |
| O-ORC-02 | Right-size parallelism | Long serial chains that could fan out (or thrash) | Tune parallelism/max_active_tasks to bottleneck | DAG wall-clock | AF | L2 |
| O-ORC-03 | Kill unneeded catchup | Historical runs nobody uses on every unpause | catchup=False + documented backfill procedure | wasted runs count | AF | L1 |
| O-ORC-04 | Batch micro-tasks | 500 tasks × 5s each; scheduler overhead dominates | One mapped/batched task | scheduler lag, DAG runtime | AF | L2 |
| O-ORC-05 | Cut DAG parse time | Scheduler loop seconds-long; UI sluggish | Heavy imports into callables; no top-level API calls | parse time per file | AF | L2 |
| O-ORC-06 | Backoff with jitter | Retries hammer a recovering service in sync | Exponential backoff + jitter policy | recovery success rate | AF | L1 |
| O-ORC-07 | Alert on what matters | 40 alerts/day, all ignored (fatigue) | SLA-based paging; digest the rest | alerts/day vs incidents caught | AF | L3 |
| O-ORC-08 | Pools for scarce resources | API rate limit tripped by parallel tasks | Pool sized to the limit | 429 count → 0 | AF | L1 |
| O-ORC-09 | Split the monolith DAG | 60-task DAG; one failure blocks unrelated work | Independent DAGs + dataset-based deps | blast radius, parallel completion | AF | L3 |
| O-ORC-10 | Data-aware scheduling | Cron guessing upstream completion (+30min padding) | Dataset/sensor-driven triggering | end-to-end latency, padding removed | AF | L2 |

## O-CST — Cost / FinOps (14)
| ID | Task | Signal | Action | Proof metric | Stacks | Lvl |
|---|---|---|---|---|---|---|
| O-CST-01 | Skip-existing idempotency | Rerun re-pays LLM for already-processed assets | Content-hash check before calling API (CIL core pattern) | $ per rerun → ~0 | LLM | L1 |
| O-CST-02 | Store raw response, re-parse free | Parser bug forces re-extraction ($$) | Bronze keeps word-for-word response; parse is replayable | re-parse cost = 0 | LLM | L1 |
| O-CST-03 | Trim prompt context | Tokens/asset creeping up with prompt edits | Measure tokens/asset; cut boilerplate; cheaper model for easy cases | $/asset trend | LLM | L2 |
| O-CST-04 | Batch LLM calls | Per-chunk calls with fixed overhead | Batch chunks per request within quality limits | $/asset, latency | LLM | L2 |
| O-CST-05 | Landing lifecycle policy | TB of raw landing older than TTL still on hot tier | Age-based transition/expiry aligned with ADR-007-style guardrails | storage $/month | S3 | L1 |
| O-CST-06 | List less, manifest more | Millions of LIST requests in the bill | Manifest-driven reads; request-cost line item | request $ | S3 | L2 |
| O-CST-07 | Hunt idle warehouse burn | Credits at 03:00 with no scheduled loads | Query-history audit → who/what; suspend policy | idle credits found | SF | L2 |
| O-CST-08 | Job clusters + spot | All-purpose cluster running scheduled jobs 24/7 | Job clusters, spot/preemptible where restartable | $/run | SPK | L2 |
| O-CST-09 | Glue DPU right-size + flex | Default DPUs on small jobs; latency-tolerant batches on standard | Measure utilization; flex for off-peak | $/run | SPK | L2 |
| O-CST-10 | Always-on vs per-run math | Managed service bills hourly for occasional runs (MWAA lesson) | TCO comparison doc; on-demand stand-up pattern | $/month | AF | L3 |
| O-CST-11 | Auto-teardown drill debris | Staging resources from last month's drill still billing | Aggressive circuit-breaker: teardown after every drill (lab locked decision) | orphan resources = 0 | ALL | L1 |
| O-CST-12 | Keep processing in-region | Egress line item from cross-region reads | Co-locate; egress as a named review item | egress $ | ALL | L1 |
| O-CST-13 | $0-first CI design | Cloud creds/compute burning on every PR | Static gates on PR; cloud only post-merge (ADR-013 pattern) | CI $/month | ALL | L2 |
| O-CST-14 | Audit-driven deletion | "Keep everything forever" default | Usage audit → archive/drop unused tables & columns (with owner sign-off) | TB reclaimed | ALL | L3 |

## O-DSN — Pipeline design patterns (12)
| ID | Task | Signal | Action | Proof metric | Stacks | Lvl |
|---|---|---|---|---|---|---|
| O-DSN-01 | Idempotent writes everywhere | Any failure needs manual cleanup before rerun | Overwrite-partition / merge-on-key semantics | rerun = safe, MTTR | ALL | L2 |
| O-DSN-02 | Checkpoint long pipelines | 6h pipeline restarts from zero on late failure | Stage checkpoints; resume from last good | recovery time | ALL | L2 |
| O-DSN-03 | Watermark + late-data policy | Either miss late rows or reprocess everything nightly | Bounded lookback window, documented tolerance | reprocess volume vs completeness | ALL | L3 |
| O-DSN-04 | CDC over full dump | Nightly full-table extract of a 500GB source | Incremental CDC/high-watermark (banking-project prep) | transfer GB/night | ALL | L3 |
| O-DSN-05 | High-watermark extraction | Full SELECT * from source OLTP hurts prod DB | `WHERE updated_at > :watermark` + updated_at index | source DB load, rows moved | ALL | L2 |
| O-DSN-06 | Filter at the source | Pipeline pulls 100%, keeps 5% | Predicate in extract query | rows transferred | ALL | L1 |
| O-DSN-07 | Compute once in Silver | Same expensive derivation in 5 marts | Materialize in Silver; marts read it | total compute | DBT | L2 |
| O-DSN-08 | Fail fast at landing | Bad data travels to Gold before detection | Contract/schema checks at the edge; cheapest-gate-first | wasted downstream compute | ALL | L2 |
| O-DSN-09 | Quarantine lane design | One bad record fails whole batch (or slips through) | Reject-lane with accounting (100% row accounting rule) | availability + auditability | ALL | L3 |
| O-DSN-10 | Parameterized backfill | Backfills done by editing dates in code | Date-window parameters end-to-end; runbook'd | backfill lead time, error rate | AF | L2 |
| O-DSN-11 | Golden-dataset for the LLM step | Provider/model change silently shifts output quality/cost | Frozen input set + expected-output tolerance run in CI | regression caught pre-prod | LLM,GE | L3 |
| O-DSN-12 | Observability that answers 3 questions | Dashboards nobody uses; incidents found by consumers | Metrics for: is it late? is it wrong? what does it cost? — delete the rest | detection source (team vs consumer) | ALL | L3 |
