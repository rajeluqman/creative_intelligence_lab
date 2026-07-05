# Optimization & Troubleshooting — Deep Drill-Down (2–3 layers per decision)

> Interview-defense prose. Each decision is drilled past the "what" into "why this instead of the
> obvious alternative," and then into the cost/time consequence of that choice. Written for spoken
> delivery — full paragraphs, copy-paste ready. Verified against the actual repos
> (`interview_repos_output/`). Five separate stacks; right-sizing each to its data is the theme.

---

## 1. Volve — Offshore Oil Well Sensor Pipeline (Databricks / Delta / Glue)

### Troubleshooting

**Centralized data-quality results table instead of reading logs.** When a run failed, the first
thing I'd query was the `dq_results` table that Great Expectations writes into, not the raw task
logs. The first layer of "why" is that a structured table answers "which gate failed, on which
table, with what value" in a single SQL query. The second layer — why not just grep the Airflow or
CloudWatch text logs — is that text logs scale badly: at millions of sensor rows the failure
message is buried in pages of unrelated INFO lines, and every engineer parses them slightly
differently, so the same incident gets diagnosed three different ways. The third layer, the actual
payoff, is mean-time-to-detection: a schema mismatch that used to cost roughly half an hour of
log-reading becomes a ten-second query, and because the result is structured I can also chart DQ
health over time and catch a slow-creeping degradation before it becomes an outage. The cost saving
is engineer billable hours per incident; the time saving is detection latency dropping from minutes
to seconds.

**Injected lineage metadata at the moment of ingestion instead of reconstructing it later.** Every
Bronze row carries `ingestion_ts`, `batch_id`, and `source_file`, stamped the instant the data
lands. The first "why" is traceability: when a corrupted or duplicate sensor reading surfaces in
Silver, those keys point straight back to the exact incoming payload. The second layer — why not
just derive provenance from the S3 directory path or the filename — is that path-based tracing
forces you to scan millions of S3 prefixes by hand, and filenames get renamed or reused, so the
trail breaks exactly when you need it most. The third layer is the blast-radius argument: with an
injected `batch_id` I can isolate and reprocess one bad batch surgically instead of rolling back a
whole table, which protects the validity of the morning operational reports and avoids a broad,
expensive reload. Cost: avoided full-table rollbacks; time: corrupted-payload pinpointing drops to
a couple of minutes.

**Modular multi-task DAG instead of a monolithic script.** The pipeline is split into roughly ten
Airflow tasks rather than one big job. The first "why" is fault isolation — a transient network
timeout on one well's stream fails only that task. The second layer, why this matters more than the
simplicity of a single script, is recovery economics: in a monolith, one well's blip forces a
re-run of every well that had already succeeded, throwing away good compute. The third layer is the
concrete number — isolating the failure lets me resume only the failed task and preserve the work
of the other nine, cutting wasted compute during an incident by up to ~90%. Cost: you re-pay for
one-tenth of the work, not all of it; time: recovery is one task's runtime, not the whole pipeline's.

### Optimization

**Z-Ordering instead of high-cardinality hive partitioning.** I ran `OPTIMIZE ... ZORDER BY
(DATEPRD)` on the big Delta tables. The first "why" is data skipping: Z-Order physically co-locates
rows with nearby time values on disk, so a query for one day reads a small contiguous slice and
Databricks skips the rest using file statistics. The second layer — why not just partition by the
timestamp column, which is the instinctive move — is that partitioning on a high-cardinality
time field creates the "small file problem": thousands of tiny files, each with its own open/read
overhead, which actually *slows* I/O and bloats metadata. The third layer is the measured result:
co-locating high-frequency time data turned multi-terabyte full-table scans into second-level reads
for specific pressure-signal windows, an 80%-plus query-time reduction, while keeping file sizes
healthy. Cost: less data scanned means smaller warehouses and lower compute bills; time: targeted
reads in seconds instead of exhaustive scans.

**Coarse partitioning (date_year + well_id) layered under Z-Order, instead of either extreme.** The
lake is partitioned coarsely by year and well, then micro-optimized with Z-Order inside each
partition. The first "why" is partition pruning — the optimizer can discard whole irrelevant years
or wells before reading a single byte. The second layer is why I deliberately went coarse rather
than partition finely by timestamp (too many small files) or not at all (every query scans
everything): coarse partitions give big pruning wins without the small-file penalty, and Z-Order
handles the within-partition precision. The third layer is the combined effect — pruning plus
skipping cuts the data pulled into memory by roughly 70%, which keeps clusters lean and runtimes
tight. Cost: ~70% less data in memory; time: proportionally shorter processing.

**Serverless SQL Warehouses with aggressive auto-stop instead of always-on interactive clusters.**
The daily batch runs on serverless warehouses that stop billing shortly after the last query. The
first "why" is killing idle "ghost compute" — a scheduled batch is idle most of the day. The second
layer, why not a standard interactive cluster, is that interactive clusters carry both a warm-up
delay and a longer minimum idle window, so they bleed budget while waiting for late-arriving data or
after a task finishes early. The third layer is the FinOps number: an aggressive auto-stop halts the
meter almost immediately after work ends, cutting unnecessary idle compute by a large margin (on the
order of 40%) with no loss of throughput. Cost: you stop paying for parking the bulldozer overnight;
time: serverless scales up fast enough that the trade costs you nothing on latency.

---

## 2. PaySim — Real-Time Fraud Intelligence Pipeline (Spark / Delta / Snowflake)

### Troubleshooting

**Row-count reconciliation right after landing instead of trusting transfer status codes.** Straight
after the raw CSVs land in Bronze, I compare the source row count against the Bronze Delta count.
The first "why" is zero-loss ingestion: a mismatch means rows were dropped in transit. The second
layer — why not just trust the cloud transfer's success code — is that a network blip can drop a
multi-thousand-row chunk *and still return success*, so the status code lies about completeness. The
third layer is the fraud-specific stakes: incomplete transaction data feeding a fraud model produces
false negatives, i.e. real fraud goes undetected, which is far more expensive than a failed
pipeline. Cost: avoided undetected-fraud losses and hours of debugging skewed downstream metrics;
time: the gap is caught at the gate, not three layers downstream.

**Automated dbt integrity tests for orphaned records instead of runtime DB constraints.** I enforce
referential integrity (no transaction pointing at a non-existent customer) as dbt test gates on
every run. The first "why" is that orphaned transactions silently corrupt fraud risk scoring. The
second layer — why a test gate rather than a foreign-key constraint — is that Delta Lake doesn't
enforce foreign keys at runtime, so there is no engine-level safety net; the contract has to live in
the test suite. The third layer is who it protects: catching the violation at entry stops polluted
data from ever reaching the BI analysts, so they never publish a skewed risk metric that someone
acts on. Cost: avoided bad downstream decisions; time: caught at build, not after a stakeholder
escalation.

**Delta transaction-log triage (`DESCRIBE HISTORY`) instead of disabling parallelism.** When the
pipeline locked up, I read the Delta commit history to see which concurrent write hit a
write-conflict on which partition. The first "why" is precision — the history names the exact
offending operation. The second layer — why not just turn off parallelism or insert long `sleep`
timers between tasks — is that those are blunt instruments that throw away throughput to mask a
problem you haven't actually located. The third layer is that knowing the real culprit lets me tune
DAG concurrency limits on evidence, keeping as much parallelism as is safe instead of serializing
everything defensively. Cost: you keep the throughput you'd otherwise sacrifice; time: targeted fix
instead of trial-and-error sleeps.

### Optimization

**Cumulative Table Design instead of recomputing running balances from day one.** To track each
account's rolling balance, I read yesterday's accumulated state and merge in only today's new
transactions with a Delta `MERGE`. The first "why" is algorithmic: naive recomputation is O(N) in
all history, so it gets slower every single day, whereas the cumulative approach is effectively O(1)
per day because you only ever touch the new deltas. The second layer — why not run the aggregation
live inside each analytical query — is that recomputing multi-million-row running totals on every
dashboard hit froze the serving database under load. The third layer is the durability of the win:
because daily compute stays flat regardless of how many years accumulate, the pipeline's cost and
runtime are predictable far into the future instead of degrading with data growth. Cost: flat daily
compute instead of ever-rising; time: dashboards read a precomputed column instead of triggering a
full-history scan.

**Predicate-scoped MERGE instead of a blanket full-table MERGE.** The merge is restricted to the
account IDs that actually moved money in the current batch window. The first "why" is that you only
update what changed. The second layer — why not a simple full-table merge — is that scanning all 6.3
million accounts every day to update the few thousand active ones wastes almost all of the compute.
The third layer is the scaling property: because the merge cost tracks daily *activity* rather than
total *database size*, runtimes stay uniform as the customer base grows. Cost: compute proportional
to activity, not to table size; time: constant-ish merge duration over years of growth.

**Arrow CloudFetch instead of row-by-row JDBC/ODBC for the Databricks→Snowflake hop.** The processed
results stream to Snowflake using vectorized, columnar Arrow transfer. The first "why" is that
columnar batch transfer moves data in large blocks instead of one row at a time. The second layer —
why not the default JDBC/ODBC driver — is that row-by-row drivers become the pipeline's bottleneck
when you're moving millions of rows between clouds, dominating wall-clock time. The third layer is
the magnitude: vectorized fetch is several times faster (on the order of 7x), which removes hours of
daily pipeline wait and gets the data onto analysts' dashboards with minimal latency. Cost: fewer
cluster-hours held open waiting on transfer; time: multi-hour transfer windows collapse.

**Scheduled VACUUM with tight retention instead of leaving file versions unmanaged.** I run regular
`VACUUM` to delete dead, unreferenced Delta files. The first "why" is that every Delta update writes
new files and leaves the old versions behind, so storage grows like an uncleared cache. The second
layer — why not rely on default cloud object-lifecycle policies — is that those operate on age, not
on Delta's notion of which files are still referenced, so they either delete too aggressively
(breaking time-travel) or not at all. The third layer is the storage number: targeted VACUUM clears
the dead parquet and drops object-storage overhead by roughly a third. Cost: ~35% less storage
spend; time: smaller file listings also speed up metadata operations.

---

## 3. Olist — E-Commerce Order-to-Cash Pipeline (PySpark / Delta / ADLS / Snowflake)

### Troubleshooting

**Schema-drift validation at the Bronze→Silver boundary instead of letting it fail downstream.** A
validator checks incoming structure against the documented contract before promoting to Silver. The
first "why" is early failure — a dropped or retyped upstream column halts the run at the gate. The
second layer — why not let it surface later in dbt or Power BI — is that by then the corrupt records
are already loaded, and cleaning a polluted production layer is a full day of work versus a clean
stop at the boundary. The third layer is containment: failing at one well-defined checkpoint means
one place to look and one place to fix, instead of chasing symptoms across every downstream model.
Cost: avoided day-long cleanups; time: failure localized to the boundary.

**Null-rate monitoring with a ~5% alert gate instead of silently defaulting nulls.** When
`order_approved_at` is null I substitute the purchase timestamp, but I also monitor how often that
fallback fires. The first "why" is that the substitution keeps a real order from being dropped. The
second layer — why monitor it rather than just default silently — is that a silent default hides a
source outage: if the upstream system suddenly nulls a huge fraction of approvals, you'd never know.
The third layer is the trigger logic — crossing the ~5% threshold raises an alert so I fix the
source API before the fallback masks a genuine operational problem in the DSO metric. Cost: avoided
a masked outage corrupting a financial KPI; time: detected on the run it happens, not at month-end
close.

**`LIST @stage` in Snowflake instead of blind connection debugging.** When a load failed I listed the
Snowflake stage to see whether the exported files were actually present and intact. The first "why"
is that it instantly splits the problem into "file never arrived" versus "file arrived but didn't
ingest." The second layer — why not start from network settings or IAM role files — is that those
are slow, broad checks when the real question is simply whether the ADLS export landed. The third
layer is triage speed: one `LIST` isolates an export failure from an ingestion failure in under five
minutes, so you debug the right half of the pipeline. Cost: engineer time; time: triage in minutes
not hours.

### Optimization

**Broadcast joins instead of the default shuffle join for small dimensions.** I explicitly broadcast
small lookup tables (e.g. product categories) with the `broadcast()` hint. The first "why" is that
broadcasting copies the small table to every worker once, so the join happens locally with no
network shuffle. The second layer — why not let Spark default to a shuffle join — is that shuffling
millions of large transaction rows across the network to match a tiny dimension saturates the
network and creates the dominant bottleneck. The third layer is the result: keeping network traffic
low cuts processing time by up to ~60% and prevents cluster-wide stalls. Cost: fewer
cluster-hours; time: ~60% faster joins on the hot path.

**`COPY INTO ... PATTERN` regex instead of generic directory imports.** Snowflake loads use an
explicit pattern that skips Spark's 0-byte metadata files like `_SUCCESS`. The first "why" is that
the engine doesn't waste effort opening empty files. The second layer — why not just import the
whole folder — is that a generic `folder/*` forces Snowflake to spin up a file handler for every
object including the empties, slowing and occasionally erroring the load. The third layer is
reliability plus speed: skipping the junk makes ingestion both faster and less flaky. Cost: fewer
wasted file operations; time: shorter, more reliable loads.

**`df.checkpoint()` to truncate lineage instead of buying bigger machines.** During deep SCD Type 2
merges I checkpoint intermediate DataFrames to disk. The first "why" is that checkpointing
materializes state and breaks the long dependency graph Spark would otherwise hold in memory. The
second layer — why not just scale up to larger, more expensive instances — is that the real problem
isn't raw size, it's an over-long lineage chain that causes Out-Of-Memory failures; bigger machines
treat the symptom expensively. The third layer is the economic outcome: truncating lineage lets
complex historical updates complete reliably on standard, affordable compute, avoiding both OOM
crashes and a permanent instance-size upgrade. Cost: standard instances instead of premium; time:
reliable completion instead of crash-and-retry loops.

---

## 4. Home Credit — Loan Default Risk Pipeline (AWS Glue / Spark / dbt / Snowflake)

> Honesty note: this repo runs on ~1,000-row generated dev data; the *dataset* is Kaggle-scale
> (`bureau_balance` alone is ~27M rows). Say "designed for the dataset's scale," not "I processed
> 58M rows." The OIDC/secretless-CI story belongs to the Creative Intelligence project, not this one.

### Troubleshooting

**Hard-stop DQ gate immediately after masking instead of auditing after load.** A Great Expectations
gate runs right after the PII-masking phase and blocks the run if any unhashed value slips through.
The first "why" is that it stops clear-text PII before it can reach the shared lakehouse. The second
layer — why a hard stop rather than loading first and auditing afterward — is that once unmasked PII
lands in a shared layer the damage is done: you're into expensive manual cleanup and potential
regulatory exposure. The third layer is the asymmetry of cost: failing a pipeline run is cheap and
reversible, whereas a PII leak into a warehouse is neither. Cost: avoided compliance fines and
manual scrubbing; time: caught at the gate instead of during an audit.

**Glue DPU profiling via CloudWatch instead of over-allocating workers.** When a Glue job slowed
down I read the DPU utilization curve before changing anything. The first "why" is that the curve
reveals the *cause* — data skew versus an inefficient join. The second layer — why not just blindly
add workers — is that throwing hardware at a skewed join or a bad query plan costs more money without
fixing the underlying inefficiency, and often barely moves the runtime. The third layer is the
discipline: profiling lets me fix the code (repartition the skew, rewrite the join) so I get the
speedup *and* keep the worker count down. Cost: avoided permanent over-provisioning; time: real
speedup from a code fix instead of a marginal one from more nodes.

**`doc_reference_contract.py` to validate columns against the glossary instead of manual review.** A
script checks that any new column matches the central business definitions. The first "why" is that
it keeps data definitions in sync automatically. The second layer — why not rely on manual model
review or a shared spreadsheet — is that human review of definitions is slow, error-prone, and drifts
out of date the moment someone forgets to update the sheet. The third layer is throughput: automated
contract validation collapses a cross-team alignment review from days of meetings to a few minutes of
CI. Cost: reclaimed review hours; time: alignment in minutes per change.

### Optimization

**Column pruning at read (~23 of 120+ columns) instead of carrying everything and dropping late.** I
select only the needed columns the moment the data is read. The first "why" is a smaller in-memory
footprint from the very first stage. The second layer — why not carry all 120+ columns and drop
unneeded ones at the end — is that the wide intermediate data inflates memory through the entire
pipeline and triggers Spark disk spill, which is slow. The third layer is the number: pruning at the
entry point cuts working memory by over ~75%, prevents spill, and shortens every transformation
downstream. Cost: smaller/fewer executors; time: faster runs with no spill stalls.

**Glue Auto Scaling with G.1X workers instead of a fixed max-size cluster.** The job scales workers
up only for the big historical files and back down for small daily runs. The first "why" is paying
for capacity only when it's actually needed. The second layer — why not provision a fixed cluster
sized for peak — is that a peak-sized cluster sits mostly idle on normal days, wasting budget on
unused nodes. The third layer is the FinOps result: elastic scaling cuts compute cost by roughly half
versus the fixed-peak approach while still handling the heavy days. Cost: ~50% lower compute; time:
no penalty — peaks still get the nodes they need.

**Upstream SHA-256 masking in Glue instead of Snowflake's native dynamic masking.** PII is hashed at
the Glue ingestion boundary, before anything is written to storage. The first "why" is that
everything persisted to the lake is already anonymous. The second layer — why not defer to
Snowflake's dynamic masking at query time — is that deferring means raw, clear-text PII first has to
travel through and rest unencrypted in the S3/ADLS landing zone, which widens the attack surface and
violates banking compliance posture. The third layer is the principle: in regulated environments you
minimize *where clear-text PII ever exists*, so masking before storage shrinks the blast radius to
effectively zero persisted clear-text. Cost: reduced regulatory exposure (and the fines/audit cost
that implies); time: no per-query masking overhead at serving time.

---

## 5. Creative Intelligence Lab — Semantic Video Feature Store (DuckDB / Gemini / Snowflake veneer)

> This repo deliberately rejects Spark, Databricks, Glue, MinIO, and any external vector DB. That
> rejection is a defended decision, not a gap — the data is KB–MB, so right-sizing beats scaling.

### Troubleshooting

**Trace-backward audit against the verbatim Bronze payload instead of treating empty output as a
generic failure.** When a Gold table came out empty I went back to the raw Gemini JSON stored in
Bronze. The first "why" is that the raw payload distinguishes an infrastructure bug from an LLM
safety-filter block — two completely different fixes. The second layer — why not just log a generic
connection error — is that "empty output" has many causes, and without the raw response you can't
tell whether the model refused the content, returned nothing, or the parser dropped it. The third
layer is that keeping the verbatim response makes the diagnosis a read, not a re-run: I never have to
re-call the paid API just to find out what happened. Cost: zero re-spend to diagnose; time: root
cause from an existing artifact in minutes.

**Golden-dataset gate on Jaccard similarity instead of exact-equality assertions.** Output quality is
checked by measuring token/tag overlap against a curated baseline. The first "why" is that an LLM is
non-deterministic, so exact equality is the wrong test — it would fail on harmless rewording. The
second layer — why not eyeball-review the outputs — is that manual review doesn't scale to thousands
of clips and is subjective, so regressions slip through. The third layer is the alerting behavior:
when a model or prompt change pushes outputs away from the approved baseline, the similarity score
drops and I'm alerted within minutes, before bad data reaches users. Cost: avoided shipping a quality
regression; time: drift caught on the run, not in production.

**`EXPLAIN ANALYZE` in DuckDB instead of adding memory to the container.** When a search slowed down I
read the query plan first. The first "why" is that the plan shows whether the cost is poor indexing
or an inefficient query. The second layer — why not just bump the container's memory — is that more
RAM doesn't fix a missing index or a bad predicate; it hides the symptom at a recurring cost. The
third layer is that fixing the actual cause (the index or the query) makes searches fast on the
existing small footprint, with no infrastructure upsize. Cost: no bigger box; time: real speedup from
the right fix.

### Optimization

**In-memory DuckDB VSS HNSW index instead of a standalone vector database.** Semantic search runs on
DuckDB's built-in HNSW vector index inside the task container. The first "why" is that HNSW gives
fast approximate-nearest-neighbor search — it hops through a graph of "similar to similar" instead of
comparing the query against every vector. The second layer — why not stand up a dedicated vector DB
like Pinecone or Milvus — is that an external vector store adds a server to operate, network latency
on every query, and a recurring infrastructure bill, all to serve a dataset that comfortably fits in
memory. The third layer is the economics: embedding the index in DuckDB drops vector-search infra
cost to zero and runs queries in milliseconds locally, with nothing extra to deploy or secure. Cost:
$0 vector infra; time: in-process millisecond search, no network hop.

**Content-hash identity (MD5/SHA-256) on the video bytes instead of filename/metadata dedup.** Each
asset's identity is a hash of its content, and already-processed hashes are skipped. The first "why"
is that the hash makes re-processing idempotent — the same clip is recognized no matter what it's
called. The second layer — why not dedupe on filename or metadata — is that a rename or a metadata
tweak trivially defeats name-based dedup, so the same expensive video would be sent to the LLM again.
The third layer is the cost firewall: because the single real dollar cost in this pipeline is the
Gemini call, hashing the content and skipping known assets prevents redundant paid inference on
re-uploads, retries, and backfills — verified live as zero new calls on an already-processed batch.
Cost: no duplicate LLM spend; time: re-runs skip straight past done work.

**Decoupling LLM inference from parsing via a verbatim Bronze layer instead of re-calling on every
logic change.** The raw Gemini response is stored untouched, and all parsing reads from Bronze. The
first "why" is that it separates the expensive, irreversible step (the model call) from the cheap,
fixable one (the parsing code). The second layer — why not parse-and-discard the response, keeping
only the structured result — is that any later parsing bug or new field request would then force a
fresh, paid re-watch of the video. The third layer is the operational payoff: with the verbatim
response retained, a parsing fix or a schema change is a free re-parse from Bronze, turning what
would be a re-spend into a same-day code change. Cost: re-extraction is free instead of re-paid;
time: parsing iterations are instant, not gated on API runs.

**Isolated `venv_airflow` for media/orchestration instead of one shared environment.** Heavy media
and AI libraries live in a separate virtual environment from the core Airflow scheduler. The first
"why" is dependency isolation — no version conflicts between media libs and the orchestrator. The
second layer — why not install everything into the main Airflow nodes — is that mixing heavy
multimedia dependencies into the scheduler risks library clashes that can destabilize the whole
orchestration layer. The third layer is blast radius: keeping them isolated means one bad media task
can't break unrelated workflows, so the scheduler stays stable. Cost: avoided pipeline-wide outages
from a dependency clash; time: no debugging of cross-library conflicts.

---

## The through-line for the interview

Lead with the theme: across five pipelines the consistent judgment is **right-sizing the stack to
the data and the risk** — Spark/Databricks/Glue where the data is genuinely big and stateful (PaySim
6.3M rows, Volve sensor streams, Home Credit's five integrated source tables), and DuckDB with no Spark and no vector
DB where it isn't (Creative Intelligence, KB–MB). Every optimization above is defensible the same
way: name the alternative, explain why it's wrong *for this workload*, and close on the cost or time
it saved.
