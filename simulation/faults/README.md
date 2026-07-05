# Fault Library — the `@bottleneck-saboteur`, as a tool

> This is the **reincarnated `@bottleneck-saboteur`** (the gym agent rejected as a *roster* member —
> [AGENT_ROSTER_RECOMMENDATION.md:29](../../AGENT_ROSTER_RECOMMENDATION.md#L29),
> [BACKLOG.md:18](../../BACKLOG.md#L18)). Here it is a **deterministic tool**, not an agent, living
> in the out-of-product sandbox — so it gives you the drill capability without re-litigating the
> roster ruling.

A fault is **named, reversible, and isolated**. It mutates only the sim's clean state.

```bash
python simulation/faults/inject.py <fault_id>   # break something
python simulation/faults/reset.py               # restore clean baseline (re-seed + re-build sim)
python simulation/check_isolation.py            # confirm still isolated from main
```

**Authoring rule (inherited from cheatsheets/):** the drills produce *simulated* incidents. Their
writeups live in `simulation/runbook/` using the real cheatsheet **card format**, clearly labeled
SIMULATED — they are **never** written into the real `cheatsheets/` (that gate needs a real post-v1
incident; faking it is forbidden).

---

## Catalog (Sonnet builds one mutate fn per row in `inject.py`, one note in `catalog/<id>.md`)

### Data-quality faults → feed **Sim #3 (Incident E2E)**
| id | injects | manifests as | caught by | skill trained |
|----|---------|--------------|-----------|---------------|
| `dq_schema_drift` | rename/drop a source column in the legacy seed | migrated build errors or silent NULLs | boundary/schema gate, `dbt build` fail | trace symptom→source, schema-mismatch RCA |
| `dq_null_key` | NULLs into a join key | null explosion / dropped rows | row-count gate, not-null test | null-handling, join semantics |
| `dq_dup_pk` | duplicate rows on the grain key | fan-out, inflated aggregates | uniqueness/grain test | grain violation RCA |
| `dq_type_mismatch` | string into a numeric column | cast error or coerced garbage | `dbt build` fail / range gate | type-safety, defensive casting |

### Reconciliation faults → feed **Sim #4 (the banking skill)**
| id | injects | manifests as | caught by | skill trained |
|----|---------|--------------|-----------|---------------|
| `rec_silent_drift` | change a value in `migrated` only (rounding / off-by-cent) | **row counts MATCH, values DON'T** | value-level reconcile harness | "counts ≠ done" — the headline RBC skill |
| `rec_filter_omission` | drop a `WHERE` clause in `migrated` | extra rows, wrong totals | aggregate reconcile | logic-equivalence under migration |
| `rec_dedup_logic` | different dedup rule legacy vs migrated | off-by-N | count + value reconcile | semantic parity, not syntactic |

### Availability faults → feed **Sim #3**
| id | injects | manifests as | caught by | skill trained |
|----|---------|--------------|-----------|---------------|
| `av_missing_partition` | delete a sim parquet partition | incomplete load | freshness/completeness gate | partial-load recovery, backfill |
| `av_late_file` | withhold an input until "after SLA" | SLA breach | duration/SLA monitor | SLA triage, dependency mgmt |

### Performance faults → feed **Sim #5 (Optimization Lab)**
| id | injects | manifests as | tuned via | skill trained |
|----|---------|--------------|-----------|---------------|
| `perf_skew` | concentrate keys (hot partition) | one slow stage, long tail | repartition / pre-aggregate | data-skew diagnosis |
| `perf_exploding_join` | many-to-many blow-up | row explosion + slow + memory | fix join grain / dedup first | join-grain optimization |
| `perf_small_files` | shatter output into many tiny parquet | metadata/IO overhead | compaction / OPTIMIZE-equivalent | small-file problem |
| `perf_full_scan` | non-sargable filter / drop pruning | full table scan, slow | partition pruning / predicate pushdown | scan-avoidance, EXPLAIN reading |

> DuckDB-world translation of "Spark UI / shuffle spill / executor OOM" → `EXPLAIN ANALYZE`,
> `SET memory_limit`, dbt run timing, `run_results.json` (see
> [cheatsheets/troubleshooting/00_INDEX.md](../../cheatsheets/troubleshooting/00_INDEX.md) binding
> translation table). Reuse it — the diagnosis motion transfers to Spark for interviews.

## `inject.py` / `reset.py` contract (Sonnet implements)
- `inject.py <fault_id>`: assert clean baseline exists → apply mutation → append a record to
  `faults/.active_faults.json` (what changed, where, which gate should catch it) → print the
  expected symptom + the gate to run. One fault at a time unless `--stack`.
- `reset.py`: rebuild clean state from sim seeds (`dbt seed && dbt build` on `sim_dbt`) → clear
  `.active_faults.json` → run `check_isolation.py`. Reset must be *total* (no hand-patching).
