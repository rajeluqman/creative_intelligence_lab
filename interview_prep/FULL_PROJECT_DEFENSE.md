# Full Project Defense — Five Data Pipelines (prose, copy-paste ready)

> Spoken-delivery prose, full paragraphs, from executive summary to interview defense, now including
> the data model and grain for each project. Verified against the actual repos. Theme across all
> five: right-sizing both the stack AND the data model to the problem.

---

## 1. Volve — Offshore Oil Well Sensor Pipeline (Databricks / Delta / Glue)

**Executive summary.** I built a large-scale time-series ingestion and processing platform for
offshore oil-well sensor data from Equinor's Volve field, using a Medallion architecture on
Databricks with Delta Lake over S3. The single decision that drove most of the value was moving away
from always-on Spark clusters toward serverless SQL warehouses combined with physical Z-Ordering on
the time dimension, which let high-frequency, historically delayed sensor streams be fully processed
and served to Snowflake dashboards by the morning shift while sharply cutting compute runtime and
idle cost.

**The problem.** Raw data arrived in inconsistent, awkward formats — WITSML XML and Excel exports —
so no two batches looked alike, and analytical queries over millions of un-indexed sensor rows were
forced into full-table scans. Asking a simple question like "what was the downhole pressure last
Tuesday?" meant reading essentially the entire multi-terabyte table, which was both slow and
expensive.

**The fix and why.** I landed the raw streams untouched into a Bronze layer on Delta Lake, pushed the
heavy cleaning into Silver, and served business-ready tables from Gold. Keeping Bronze immutable gives
full data lineage and, crucially, lets me re-run downstream logic for free if a transformation rule
changes — I never have to re-ingest. Delta Lake also gave me ACID transactions on streams that were
previously prone to corruption during in-flight writes; without that guarantee, two concurrent writers
behave like two people editing the same document with autosave off, where the last writer silently
wins and the other's data is lost.

**The data model and grain.** This is a time-series snapshot model layered through the medallion. The
raw Bronze grain is one row per WITSML trajectory, where the survey stations sit in a nested array;
Silver explodes that array down to one row per survey station so each measurement becomes addressable;
and the Gold mart settles on a daily-snapshot grain of one row per well per production day —
`(DATEPRD, well_id)` — carrying the rolling averages, pressure deltas, and anomaly flags, with a
parallel ML feature table at the same grain. I chose a daily-per-well grain rather than keeping the
raw per-reading grain because the business questions are daily operational KPIs and trend detection,
not sub-second telemetry, so aggregating to the decision grain makes the dashboards fast and the
storage sane; keeping everything at raw sensor resolution in Gold would multiply row counts by orders
of magnitude for no analytical benefit. The grain is fixed and explicit, which is what makes the
rolling-window and lag features well-defined — you can't compute a clean day-over-day pressure delta
unless "a day" is the locked grain.

**Troubleshooting.** When a run failed, my first move was to query the `dq_results` table that Great
Expectations writes into, rather than reading raw logs, because a structured table answers "which gate
failed, on which table, with what value" in a single SQL query; parsing Airflow or CloudWatch text
logs scales badly, since at millions of rows the real message is buried in pages of unrelated lines
and every engineer reads them differently, so the payoff is mean-time-to-detection dropping from
roughly half an hour of log-reading to a ten-second query, with the bonus that structured results let
me chart data-quality health over time and catch slow degradation early. For tracing corrupt or
duplicate readings I relied on lineage metadata — `ingestion_ts`, `batch_id`, `source_file` — stamped
at the moment of ingestion, because path- or filename-based provenance forces you to scan millions of
S3 prefixes by hand and breaks the instant a file is renamed, whereas an injected `batch_id` lets me
reprocess one bad batch surgically instead of rolling back a whole table, which protects the validity
of the morning reports. And I split the pipeline into roughly ten Airflow tasks rather than one
monolithic script, because in a monolith a single well's transient network timeout forces a re-run of
every well that had already succeeded; isolating tasks means I resume only the failed one and preserve
the other nine, cutting wasted compute during an incident by up to ninety percent.

**Optimization.** The headline optimization was Z-Ordering the big Delta tables on the production date,
which physically co-locates rows with nearby time values on disk so a query for one day reads a small
contiguous slice and skips the rest via file statistics; the obvious alternative, partitioning on the
high-cardinality timestamp, actually backfires by creating the small-file problem — thousands of tiny
files each carrying open-and-read overhead, which slows I/O and bloats metadata — so Z-Order turned
multi-terabyte scans into second-level reads for specific pressure-signal windows, an
eighty-percent-plus query-time reduction, while keeping file sizes healthy. Underneath that I
partitioned coarsely by year and well so the optimizer could prune whole irrelevant years or wells
before reading a byte, deliberately staying coarse rather than partitioning finely by timestamp, which
would reintroduce small files; pruning plus skipping together cut the data pulled into memory by about
seventy percent. Finally I ran the daily batch on serverless SQL warehouses with an aggressive
auto-stop, because a scheduled batch is idle most of the day and a standard interactive cluster carries
both a warm-up delay and a longer minimum idle window that bleeds budget while waiting for late data;
stopping the meter almost immediately after the last query cut idle compute on the order of forty
percent with no loss of throughput.

**The business decision.** An always-on cluster is a rented bulldozer left running in the car park
overnight; serverless is a pay-per-use taxi. For a daily batch that sits idle twenty-two hours a day,
the taxi wins on cost without costing anything on latency, because serverless scales up fast enough
that the trade is free.

**In plain terms.** Think of this as an automated watchdog monitoring oil wells thousands of feet
underwater: instead of engineers manually pulling messy spreadsheets and looking at yesterday's
problems, the platform cleans the data automatically and surfaces critical pressure anomalies before an
expensive pipe failure can happen.

**Interview defense.** If asked why serverless over a standard interactive Spark cluster, my answer is
that a daily analytical batch is idle most of the day, so an interactive cluster's warm-up delay and
idle cost are pure waste; serverless scales up on demand and stops billing right after the run, which
is the right cost shape for a bursty, scheduled workload — I'd only keep a long-lived cluster for
continuous streaming.

---

## 2. PaySim — Real-Time Fraud Intelligence Pipeline (Spark / Delta / Snowflake)

**Executive summary.** I processed 6.3 million financial transactions (6,362,620 exactly) with Spark
and Delta Lake, and the design that delivered most of the value was a hybrid Kimball-plus-cumulative
data model: a standard transaction-grain star for slicing and dicing, plus a cumulative daily-balance
table that maintains each account's running balance incrementally, so security analysts could compare
a customer's immediate behavior against their entire historical baseline instantly instead of waiting
on the multi-hour aggregations a naive architecture would demand.

**The problem.** To catch rapid "account drain" fraud, the pipeline had to compute a rolling balance
for every active account, and running those multi-million-row aggregations live on every analytical
query crippled the serving database and froze the fraud dashboards under load.

**The fix and why.** I engineered a stateful cumulative design in Silver using Delta `MERGE`: rather
than recompute balances from day one across millions of rows, the pipeline reads yesterday's
accumulated state and merges in only today's net-new transactions. This shifts the complexity of the
historical calculation from O(N) in all history — which gets slower every single day — to an
effectively O(1)-per-day footprint, because you only ever touch the new deltas. The analogy is keeping
a running bank-statement balance instead of re-adding every transaction since the account opened every
time you want to know where you stand.

**The data model and grain.** I deliberately ran two fact tables at two different grains because they
answer two different questions. The first is `fact_transactions`, a classic Kimball star at the grain
of one row per transaction, surrounded by conformed dimensions — `dim_customer`, `dim_transaction_type`,
`dim_merchant`, and `dim_time` — and that grain is right for forensic, "show me every transaction that
matched this pattern" analysis. The second is `fact_customer_daily_balance`, a cumulative table at the
grain of one row per customer per day, which is what makes the "sudden drain" detection cheap: the
running balance is precomputed and stored, not recomputed at query time. The justification for the
hybrid is that a single grain can't serve both needs efficiently — forcing balance questions onto the
transaction grain means re-aggregating millions of rows per query, while forcing transaction-level
forensics onto the daily grain loses the per-event detail you need to actually explain a fraud case. I
accept the one real cost of this, which is that an analytics engineer has to understand two grains, and
I document them explicitly so nobody accidentally joins across them at the wrong cardinality.

**Troubleshooting.** Immediately after landing I reconciled the source CSV row count against the Bronze
Delta count, because a network blip can drop a multi-thousand-row chunk and still return a success
status, so trusting the transfer's status code would let incomplete data reach the fraud models and
produce false negatives — missed fraud — which is far costlier than a failed pipeline. I also enforced
referential integrity through automated dbt tests rather than runtime constraints, because Delta Lake
doesn't enforce foreign keys at runtime, so an orphaned transaction pointing at a non-existent customer
would silently corrupt risk scoring unless the contract lives in the test suite; catching it at entry
stops polluted data from ever reaching the analysts who would otherwise publish a skewed metric. When
the pipeline locked up, I read the Delta commit history with `DESCRIBE HISTORY` to identify exactly
which concurrent write hit a write-conflict on which partition, rather than reaching for blunt
instruments like disabling parallelism or inserting arbitrary sleep timers, which sacrifice throughput
to mask a problem you haven't actually located; knowing the real culprit let me tune DAG concurrency on
evidence and keep as much parallelism as was safe.

**Optimization.** Beyond the cumulative design itself, I scoped every `MERGE` with a predicate
restricting it to the account IDs that actually moved money in the current batch window, because a
blanket full-table merge would scan all 6.3 million accounts daily just to update the few thousand
active ones; tying merge cost to daily activity rather than total database size keeps runtimes uniform
as the customer base grows. I moved the processed results to Snowflake using vectorized Arrow CloudFetch
instead of a row-by-row JDBC or ODBC driver, because row-by-row transfer becomes the pipeline's
bottleneck when you're shipping millions of rows between clouds, and columnar batch transfer is several
times faster, removing hours of daily wait and getting data onto analysts' dashboards with minimal
latency. And I scheduled regular `VACUUM` with tight retention to clear dead, unreferenced Delta files,
because every update writes new files and leaves the old versions behind like an uncleared cache;
default cloud lifecycle policies act on file age rather than Delta's notion of which files are still
referenced, so they either delete too aggressively and break time-travel or don't clean up at all,
whereas a targeted VACUUM dropped storage overhead by roughly a third.

**The business decision.** Spark genuinely is justified here: 6.3 million rows with stateful per-account
history is a real distributed-compute problem. That's the deliberate contrast with my Creative
Intelligence project, where I rejected Spark for a kilobyte-to-megabyte workload — knowing when the
heavy engine is right and when it's overkill is the actual judgment.

**In plain terms.** We built an intelligent guard dog for bank accounts: instead of judging a
transaction in isolation, it remembers every penny an account has ever moved, so when a criminal
compromises an account and tries to empty it in seconds, the system notices the sudden break from
historical pattern and flags it instantly.

**Interview defense.** If asked why not a standard dbt incremental model for the running totals, my
answer is that dbt incrementals excel at append-only logs but struggle with a lifelong changing state
like a rolling balance, forcing awkward self-joins or slow row-by-row updates; the cumulative design
keeps daily compute flat regardless of how deep the history gets, and that O(1)-per-day property is the
entire point.

---

## 3. Olist — E-Commerce Order-to-Cash Pipeline (PySpark / Delta / ADLS / Snowflake)

**Executive summary.** I built order-to-cash analytics for the Olist e-commerce dataset on a Kimball
star schema, and the decision driving most of the reporting accuracy was implementing Slowly Changing
Dimensions Type 2 via PySpark windowing, which kept a flawless chronological record of shifting seller
and customer geographies and gave the business mathematically correct freight costs and logistics
margins at any point in history.

**The problem.** The source overwrote seller addresses in place — classic SCD Type 1 behavior — so when
a seller relocated, historical orders that had shipped from the old warehouse were retroactively
evaluated against the new location, corrupting past shipping KPIs. On top of that, missing timestamps on
key pipeline states, such as a null `order_approved_at`, broke the corporate Days-Sales-Outstanding
metric.

**The fix and why.** I designed a PySpark transformation that reads incoming changes, computes
historical time boundaries with start and end dates, and assigns an `is_current` flag, so instead of
overwriting a seller's address I keep a new versioned row each time it changes — the difference between
editing a Wikipedia page so the old text vanishes and keeping Wikipedia's full edit history with every
version timestamped. For missing data I injected a structural fallback: if `order_approved_at` arrives
null, the system substitutes the purchase timestamp, which preserves a real order and protects the
executive dashboards rather than discarding valuable records.

**The data model and grain.** This is a textbook Kimball star with three fact tables, each locked to a
distinct grain that matches a real business event. `fact_orders` is one row per order, `fact_order_items`
is one row per line item within an order, and `fact_payments` is one row per payment installment; around
them sit the conformed dimensions `dim_customers`, `dim_sellers`, `dim_products`, and `dim_date`. The
reason for three separate fact tables rather than one wide flattened table is that order, line item, and
installment are genuinely different grains — an order can contain several items and be paid in several
installments — so collapsing them into one table would either duplicate order-level facts across every
line and payment, inflating sums and double-counting revenue, or force awkward nulls. Keeping each fact
at its true grain means an aggregation like total freight or average installment count is correct by
construction. The dimensions, especially `dim_sellers`, are SCD Type 2 precisely so that a fact joins to
the version of the seller that was current when the order shipped, which is what preserves historical
accuracy through relocations.

**Troubleshooting.** I validated schema drift at the Bronze-to-Silver boundary, because if an upstream
e-commerce update silently drops a column or changes a datatype, halting at the gate is far cheaper than
letting corrupt records load and then spending a full day cleaning a polluted production layer; one
well-defined checkpoint also means one place to look and fix, instead of chasing symptoms across every
downstream model. I monitored the null-rate of the fallback with an alert threshold around five percent
rather than defaulting nulls silently, because a silent default would mask a source outage — if the
upstream system suddenly nulls a large fraction of approvals you'd never know — whereas crossing the
threshold alerts me to fix the source API before the fallback quietly hides a real operational problem in
the DSO figure. And when a load failed, I ran `LIST @stage` in Snowflake to see whether the exported
files were actually present and intact, because that instantly splits the problem into "the file never
arrived from ADLS" versus "the file arrived but didn't ingest," isolating an export failure from an
ingestion failure in under five minutes instead of starting from broad network or IAM checks.

**Optimization.** I forced broadcast joins with the `broadcast()` hint for the small dimension lookups,
because broadcasting copies the small table to every worker once so the join happens locally, whereas
Spark's default shuffle join would move millions of large transaction rows across the network to match a
tiny category list and saturate the network as the dominant bottleneck; keeping traffic low cut
processing time by up to sixty percent and prevented cluster-wide stalls. I loaded into Snowflake with an
explicit `COPY INTO ... PATTERN` regex that skips Spark's zero-byte metadata files like `_SUCCESS`,
because a generic folder import forces the engine to spin up a file handler for every object including
the empties, which slows the load and occasionally errors it. And during the deep SCD Type 2 merges I
used `df.checkpoint()` to materialize intermediate state and break Spark's long lineage graph, because
the real cause of the Out-Of-Memory failures was an over-long dependency chain rather than raw data
size, so checkpointing let complex historical updates finish reliably on standard, affordable instances
instead of buying permanently larger machines to treat the symptom.

**The business decision.** SCD Type 2 does inflate row counts, but only on the small dimensions —
sellers and customers — which are orders of magnitude smaller than the fast-growing fact tables, so the
historical-accuracy win of correct freight margins and no retroactive corruption far outweighs a
slightly larger dimension table.

**In plain terms.** We turned a chaotic pile of millions of online-shopping receipts into a clear
operational dashboard, so management can trace which stores ship fastest, which payments lag, and exactly
how a vendor relocating their warehouse changes shipping fees for the end customer.

**Interview defense.** If asked whether SCD Type 2 inflates rows and degrades joins, my answer is that it
expands the dimension, which is far smaller than the fact table; for live reporting I expose a simple
`is_current = true` filter, and for historical queries I join on bounded date ranges, so the warehouse
stays fast while history stays complete.

---

## 4. Home Credit — Loan Default Risk Pipeline (AWS Glue / Spark / dbt / Snowflake)

**Executive summary.** I consolidated loan data across five source tables — application, bureau,
bureau_balance, installments, and previous_application — with AWS Glue onto a Kimball star schema, and the
core decision that secured the compliance posture was applying SHA-256 PII masking natively inside the
Glue Spark jobs at the earliest ingestion boundary, which isolated sensitive customer identities from the
downstream lakehouse while dbt SCD Type 2 snapshots preserved auditable history of applicant attributes.
One honesty note I always state up front: the dataset is Kaggle-scale,
with `bureau_balance` alone around twenty-seven million rows, but I built and validated the pipeline on a
representative thousand-row development slice, so I'm describing a system designed for that scale rather
than claiming I personally crunched fifty-eight million rows in production.

**The problem.** The raw sources were full of dangerous data-quality anomalies — "magic numbers" like
the value 365243 hardcoded into a date field to signal a missing employment record — which, fed raw into
a model, becomes a nonsensical thousand-year tenure that corrupts default risk scores. Simultaneously,
unmasked customer ages, incomes, and credit profiles were exposed to downstream analysts, a serious
compliance liability.

**The fix and why.** I built custom cleaning functions in Glue that translate anomalous magic numbers
into standardized null markers according to a risk rulebook, cleaning the garbage at the front gate
before it can reach a model, and I masked the sensitive applicant fields — `DAYS_BIRTH` and
`DAYS_EMPLOYED` — with a SHA-256 hash during ingestion. SHA-256 is a one-way shredder: you can verify
whether two shredded documents are the same but you can never reassemble the original. The order matters
and is a real detail I'm proud of — the `365243` sentinel is converted to null *before* hashing
(data-integrity rule DI-002), so I never hash the magic number and turn garbage into a
legitimate-looking hash, and a Great Expectations gate asserts the masked column is never equal to
`sha256('365243')` to prove that ordering held. If I were hardening this for real production I'd add a
salt, because an unsalted hash of a low-cardinality field like age is brute-forceable — I'd call that
out honestly rather than overclaim the current implementation.

**The data model and grain.** The model is a Kimball star with one central fact and a constellation of
supporting facts, integrating the five source tables into a coherent whole. The central table is
`fact_loan_application` at the grain of one row per loan application, keyed by `SK_ID_CURR`; around it
are `fact_bureau_credit` at one row per external credit-bureau record (`SK_ID_BUREAU`) and
`fact_installment_payment` at one row per installment payment (`SK_ID_PREV` plus the instalment number).
The dimensions — `dim_applicant`, `dim_loan_type`, `dim_credit_status` — describe the who and the what,
with the applicant dimension tracked as SCD Type 2 so a risk score can be reconstructed against the
attributes as they were at decision time. The justification for distinct grains is that an application,
a bureau record, and an installment are different real-world events at very different cardinalities — one
application links to many bureau records and many installments — so anchoring each at its own grain keeps
aggregations honest and lets the risk features (counts, ratios, payment-history rollups) be computed
cleanly from the right base table rather than from a pre-joined mess that would double-count. Choosing
`SK_ID_CURR` as the conformed key across the constellation is what lets the five source tables actually join
into one applicant view.

**Troubleshooting.** I placed a hard-stop Great Expectations gate immediately after the masking phase, so
that if any unhashed value slips through, the run blocks before the data ever reaches the shared
lakehouse, because once clear-text PII lands in a shared layer the damage is done — you're into
expensive manual cleanup and potential regulatory exposure — and failing a pipeline run is cheap and
reversible whereas a PII leak is neither. When a Glue job slowed down I read the DPU utilization curve in
CloudWatch before changing anything, because the curve reveals whether the cause is data skew or an
inefficient join, and blindly adding workers would cost more money without fixing the underlying
inefficiency and would barely move the runtime; profiling let me fix the code — repartition the skew or
rewrite the join — and keep the worker count down. I also ran a documentation-contract script that
automatically checks new columns against the central business glossary, because manual review of
definitions across a team is slow and drifts out of date the moment someone forgets to update a
spreadsheet, so automated validation collapses an alignment review from days of meetings to a few minutes
of CI.

**Optimization.** I pruned the input to the roughly twenty-three columns that mattered the moment the
data was read, rather than carrying all hundred-and-twenty-plus columns through the pipeline and dropping
them at the end, because the wide intermediate data would inflate memory through every stage and trigger
Spark disk spill; pruning at the entry point cut working memory by over seventy-five percent and
prevented spill. I enabled Glue Auto Scaling with G.1X workers so the job scales out only for the big
historical files and scales back down for small daily runs, rather than provisioning a fixed peak-sized
cluster that would sit mostly idle on normal days, which cut compute cost by roughly half while still
handling the heavy days. And the decision to mask upstream in Glue rather than rely on Snowflake's native
dynamic masking was deliberate: deferring masking to query time means raw clear-text PII first has to
travel through and rest unencrypted in the S3 landing zone, widening the attack surface and violating
banking compliance posture, whereas masking before storage means everything persisted to the lake is
already anonymous and the blast radius of persisted clear-text is effectively zero.

**The business decision.** In a regulated bank the principle is to minimize where clear-text PII ever
exists, so masking at the ingestion boundary instead of at serving time directly reduces regulatory
exposure and the audit-and-fine cost that comes with it, with no per-query masking overhead at serving
time.

**In plain terms.** We built an airtight digital vault: it ingests millions of background data points to
help the credit team judge who qualifies for a loan, but it locks away all personal data behind an
unbreakable digital mask so no one can ever leak or reconstruct a customer's identity.

**Interview defense.** If asked why mask in Glue instead of using Snowflake's dynamic masking, my answer
is that deferring to Snowflake means clear-text PII has to travel and sit unencrypted in S3 first,
widening the threat surface, whereas masking at the Glue ingestion boundary means nothing un-anonymized
is ever persisted — a smaller blast radius and a cleaner compliance story.

---

## 5. Creative Intelligence Lab — Semantic Video Feature Store (DuckDB / Gemini / Snowflake veneer)

**Executive summary.** I built a semantic feature store that turns near-duplicate ad video into
structured, searchable data on a hybrid asset-graph-plus-star model, and the engineering strategy that
unlocked most of the cost savings was decoupling the expensive LLM inference step from the cheap parsing
step and serving semantic search from an embedded DuckDB HNSW vector index, deliberately rejecting Spark,
a managed cluster, and any external vector database because the data is only kilobytes to megabytes of
text and metadata, so right-sizing beats scaling.

**The problem.** The naive approach cut video at fixed time intervals, which severed sentences and
destroyed meaning — "Frankenstein content" — and during development the API cost ran away because the
system re-called the expensive Gemini model every single time a developer adjusted the downstream parsing
code.

**The fix and why.** I switched to semantic chunking, cutting on shifts in narrative meaning rather than
on a clock, and I forced the raw, unstructured JSON from Gemini to land verbatim and untouched in Bronze,
with all parsing reading from Bronze rather than from a fresh model call. This completely separates the
expensive, irreversible step — the paid inference, which you can't un-watch — from the cheap, fixable
step — the parsing logic — so when an analyst wants a field extracted differently, I simply update the
parser and re-run from Bronze for free, bypassing the LLM entirely. It's the difference between recording
an interview once and transcribing from the recording as many times as you like, versus re-interviewing
the person every time you fix a typo in your notes.

**The data model and grain.** This is the one project where a pure star isn't enough, so the model is a
hybrid of an asset-graph and a star. The core grain is row-per-semantic-chunk: the Silver and Gold
`fact_chunk` is unique on `(client_id, asset_id, chunk_id)`, which I describe as the chunk's "IC number"
— one chunk, one identity — surrounded by `dim_asset` and `dim_client`. The star half handles all the
straightforward analytics: filter chunks by theme, sentiment, or standalone score and join up to the
source asset and client. But the genuinely interesting question — "which chunk can legitimately follow
which, so I can assemble a coherent ad without creating Frankenstein content" — is a graph relationship,
not a dimensional one, so it lives in a bridge table (`bridge_chunk_compatibility`) modelling the
many-to-many adjacency between chunks. I deliberately used a bridge table rather than a CTE or an array
column because a bridge is queryable, testable, and indexable on its own, and it doesn't vanish after one
query the way a CTE does. The grain discipline is enforced as code: a uniqueness test on the grain key in
dbt plus a Great Expectations gate, because every downstream fact trusts that Silver is unique on its
grain, and a single duplicate chunk would silently corrupt every aggregate built on top.

**Troubleshooting.** When a Gold table came out empty, I traced backward to the verbatim Bronze payload,
because the raw Gemini response distinguishes an infrastructure bug from an automated safety-filter block
— two completely different fixes — and logging only a generic connection error would leave me unable to
tell a refusal from a parser drop; keeping the response also makes the diagnosis a read rather than a
re-run, so I never re-pay the API just to find out what happened. For quality I gated on golden-dataset
similarity using a Jaccard overlap score against a curated baseline, because an LLM is non-deterministic
so exact-equality assertions are the wrong test and would fail on harmless rewording, while manual eyeball
review doesn't scale to thousands of clips and is subjective; when a model or prompt change pushes outputs
away from the approved baseline the similarity drops and I'm alerted within minutes, before bad data
reaches users. And when a search slowed down I ran `EXPLAIN ANALYZE` in DuckDB to see whether the cost was
poor indexing or an inefficient query, rather than reflexively adding memory to the container, because
more RAM doesn't fix a missing index — it just hides the symptom at recurring cost — whereas fixing the
real cause keeps search fast on the existing small footprint.

**Optimization.** I built semantic search on DuckDB's in-memory HNSW vector index, which finds approximate
nearest neighbors by hopping through a graph of "similar to similar" instead of comparing the query
against every vector, rather than standing up a dedicated vector database like Pinecone or Milvus, because
an external store adds a server to operate, network latency on every query, and a recurring bill, all to
serve a dataset that fits comfortably in memory; embedding the index in DuckDB dropped vector-search
infrastructure cost to zero and runs queries in milliseconds locally with nothing extra to deploy or
secure. I made asset identity a content hash of the video bytes rather than a filename or metadata,
because a rename trivially defeats name-based deduplication and would re-send the same expensive video to
the model, whereas hashing the content makes reprocessing idempotent and acts as a cost firewall — since
the single real dollar cost in this pipeline is the Gemini call, skipping already-hashed assets prevents
redundant paid inference on re-uploads, retries, and backfills, which I verified live as zero new calls on
an already-processed batch. And I isolated the heavy media and AI libraries in a separate virtual
environment from the core Airflow scheduler, rather than installing everything onto the orchestration
nodes, because mixing heavy multimedia dependencies into the scheduler risks version clashes that can
destabilize the whole orchestration layer, so isolation means one bad media task can't break unrelated
workflows.

**The business decision.** This is my strongest contrast: I chose DuckDB over Spark on purpose, because
the data is kilobytes to megabytes of text and metadata, not millions of rows like my PaySim fraud
pipeline, and a distributed engine's cluster spin-up and inter-node shuffle overhead would cost more and
run slower than a single-process engine — matching the engine to the data, rather than defaulting to "big
data" tooling, is the actual engineering judgment.

**In plain terms.** We trained an AI to watch thousands of marketing videos and take detailed, structured
notes on every scene, so a design team can type a conceptual search and instantly pull the exact matching
clip, instead of fast-forwarding through hours of raw footage.

**Interview defense.** If asked why a lightweight engine like DuckDB over an industry-standard engine like
Spark for an AI feature store, my answer is that the workload is unstructured text and metadata well under
a gigabyte, so a distributed engine adds cluster spin-up and shuffle overhead that buys nothing at this
scale; DuckDB gives in-memory vector operations locally inside a single container at zero cluster cost,
and I can prove I know when not to use it because I deliberately used Spark on a 6.3 million-row fraud
pipeline where it genuinely was warranted.

---

## The through-line for the whole interview

Lead with the theme and let the five projects evidence it: across every pipeline the consistent judgment
is right-sizing both the stack and the data model to the data and the risk — Spark, Databricks, and Glue
on Kimball stars and cumulative tables where the data is genuinely big and stateful, as in PaySim's 6.3
million transactions, Volve's sensor streams, and Home Credit's five integrated source tables, and DuckDB on a
hybrid graph-plus-star with no Spark and no vector database where it isn't, as in the
kilobyte-to-megabyte Creative Intelligence feature store. The data-model discipline is the same
everywhere: one table, one grain, one business event; conformed dimensions; SCD Type 2 where history
must stay honest; bridge tables, not CTEs, for many-to-many relationships; and the grain enforced as a
test, not a hope. And one governance spine runs through all of them — a medallion layout with an
immutable, replayable Bronze, data-quality gates that fail fast, and a discipline of decoupling expensive
irreversible steps from cheap fixable ones.
