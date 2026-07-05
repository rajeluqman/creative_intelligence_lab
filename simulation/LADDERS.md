# Difficulty Ladders — Troubleshooting (T) & Optimization (O)

> **Imported from** pharma_novartis_sttm's `learning/DIFFICULTY_LADDER.md`, **rebuilt for this
> stack** (DuckDB / S3 / Snowflake serving — NO Spark). The pharma ladder graded Spark/Delta
> incidents; this one grades the same *skills* against this repo's real fault catalog
> ([faults/README.md](faults/README.md)).
>
> **The ladder separates** *what breaks* (the fault id) from *how hard it is to find* (symptom
> distance, red herrings, recovery complexity). You climb one level at a time
> ([PEDAGOGY_PREFS.md](PEDAGOGY_PREFS.md) principle 3 — never jump to the hard case).
>
> **Grading is methodology, not speed:** observability-first before touching code, one hypothesis at
> a time, every finding gated on evidence (command output / `file:line`), counts reconciled before
> re-enabling. (See [CIKGU_DRILL_PROTOCOL.md](CIKGU_DRILL_PROTOCOL.md).)

---

## Ladder T — Troubleshooting (Sim #3, the production-support credibility)

| Lvl | Skill it trains | Key challenge | Fault id(s) | RBC task | Resume bullet it strengthens |
|----|-----------------|---------------|-------------|----------|------------------------------|
| **T-L01** | Execute checklist | symptom = root (gate names it) | `dq_dup_pk` | 13,16,83 | Home Credit "dedup"; PaySim "49/49 dbt tests" |
| **T-L02** | Pinpoint the layer | near-root error signal | `dq_null_key` | 20 | Home Credit "null/sentinel nullification" |
| **T-L03** | Code vs data | rerun on clean sample to split | `dq_type_mismatch` | 18 | Olist "data integrity"; defensive casting |
| **T-L04** | Backward trace, 1 hop | schema shift → downstream type/NULL | `dq_schema_drift` | 19 | all 4 projects "schema validation" |
| **T-L05** | Trace from the KPI | far from root (mart numbers look off) | `av_missing_partition` | 8,88 | Volve "hard DQ gate Task 6"; freshness |
| **T-L06** | Safe recovery / idempotency | naive re-run doubles counts | `av_missing_partition` (+backfill) | 14,21,26 | Home Credit "idempotent restart/backfill" |
| **T-L07** | Navigate a red herring | decoy log beside the real cause | `rec_filter_omission` | 13 | reconciliation under a scary-but-harmless signal |
| **T-L08** | SLA / SEV1 discipline | growing blast radius, MTTR | `av_late_file` | 2,9 | Volve "10-task DAG, SLA gate" |
| **T-L09** | Multi-cause isolation | two faults at once (`--stack`) | `dq_schema_drift` + `rec_silent_drift` | 15 | senior RCA — separate independent causes |
| **T-L10** | Compound + rollback | a bad fix makes it worse | `rec_silent_drift` + non-idempotent backfill | 15,22 | "rollback test", recovery discipline |

## Ladder O — Optimization (Sim #5, "the number is the story")

| Lvl | Skill it trains | Key motion | Fault id | DuckDB technique | → Spark interview vocab | Resume bullet |
|----|-----------------|-----------|----------|------------------|-------------------------|---------------|
| **O-O01** | Read the plan | `EXPLAIN ANALYZE` before touching anything | `perf_full_scan` | spot full scan | "read the Spark UI / physical plan" | "Query Performance Optimisation" |
| **O-O02** | Predicate pushdown | make the filter sargable | `perf_full_scan` | push filter to scan | "predicate pushdown / pruning" | "Query Performance Optimisation" |
| **O-O03** | Partition pruning | scan only needed partitions | `perf_full_scan` (partitioned) | parquet partition pruning | "partition pruning" | resume "Partitioning" |
| **O-O04** | Join-grain fix | kill the fan-out before the join | `perf_exploding_join` | dedup/pre-agg to grain | "broadcast / fix shuffle skew" | Olist/PaySim grain control |
| **O-O05** | Small-file compaction | fewer, bigger files | `perf_small_files` | compact parquet output | "Delta OPTIMIZE / file compaction" | resume "Partitioning/IO" |
| **O-O06** | Skew diagnosis | break up a hot key | `perf_skew` | repartition / salt | "data-skew, long-tail stage" | senior perf diagnosis |

> **Spark vocab column is study-only.** You map the DuckDB *reasoning* to Spark *words* for interview
> answers — you never build Spark here (ADR-001 boundary; pharma's Z-Order/OPTIMIZE/VACUUM are
> `❌ study, don't fake` in [specs/06_RBC_TASK_MAP.md](specs/06_RBC_TASK_MAP.md)).

---

## How to use a ladder
1. Pick the lowest level you have NOT passed. Read its drill in [drills/](drills/).
2. Run the drill with `@cikgu` (or solo) per [CIKGU_DRILL_PROTOCOL.md](CIKGU_DRILL_PROTOCOL.md).
   The answer lives in `.solutions/` — **gated**; you attempt first.
3. Pass = Definition of Done in the drill met + STAR row filled + `check_isolation.py` PASS.
4. Log the pass in [../learning/LEARNING_LOG.md](../learning/LEARNING_LOG.md); only then climb.

## Build status (Option-1 scaffold)
- ✅ Ladders defined (this file).  ✅ One worked drill each: `T-L01`, `O-O01` (the templates).
- ⏳ `T-L02..T-L10`, `O-O02..O-O06` — Sonnet mass-produces from the templates via
  [SONNET_KICKOFF_PROMPT.md](SONNET_KICKOFF_PROMPT.md). Each needs its `inject.py` mutate fn too.

## Bank-sourced drills (added 2026-07-04, ADR-014 handover)
A second drill source now exists alongside this ladder's own `T-L`/`O-O` numbering: the saboteur
**problem bank** (`architecture/control_plane_lab/saboteur/PROBLEM_BANK_TROUBLESHOOT.md` +
`PROBLEM_BANK_OPTIMIZATION.md`, 100+100 entries) with its own `Lvl` column (L1 detect/read → L2
diagnose/fix → L3 own-the-incident) — same grading discipline as this ladder, but IDs stay in the
bank's own `T-XXX-NN` form rather than being renumbered into `T-Lxx`/`O-Oxx` slots. Which bank IDs
are actually injectable in CIL today (this repo has no Spark/Fabric) is tracked separately in
[`faults/catalog/CIL_INJECTABLE_MAP.md`](faults/catalog/CIL_INJECTABLE_MAP.md).

Two bank-sourced drills are built so far, both **outside this ladder's own numbering** — climb
them whenever, they don't block T-L/O-O progression:
- [`drills/T-SRV-04_rbac_future_grant.md`](drills/T-SRV-04_rbac_future_grant.md) — bank Lvl L1.
- [`drills/T-SEC-01_leaked_key.md`](drills/T-SEC-01_leaked_key.md) — bank Lvl L3, the first drill
  graded against the full `INCIDENT_RUNBOOK.md` 8-phase lifecycle, not just a fix.
