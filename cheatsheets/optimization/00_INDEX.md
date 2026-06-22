# Optimization Library — Creative Intelligence Pipeline (INDEX)

> Mirror of the pharma gym's optimization library, adapted to this project.
> A **static catalog** of performance/cost techniques, one card per technique, each tied to a
> real layer of THIS pipeline. Cards are fed by real findings (an SLA/perf observation →
> 🟡 APPLICABLE → ✅ DONE once applied and cited). Content is English.

## How to use
1. Each layer file holds cards. Fill one card per technique.
2. Classify every card: **✅ DONE** (applied + cited `file:line`) · **🟡 APPLICABLE** (real, not yet
   applied) · **⬜ N/A** (doesn't apply here — say why).
3. Every ✅ card MUST cite a real `path:line`. No fabricated citations.

## Card format (copy this)
```
### <ID> — <technique name>
- **Layer:** ingestion | bronze | silver | gold | serving | orchestration | dq | shared
- **Status:** ✅ DONE | 🟡 APPLICABLE | ⬜ N/A
- **What:** one line — the technique.
- **Why here:** why it matters for THIS workload (video + LLM + small structured output).
- **Applied at:** `path/to/file.sql:LN` (✅ only) — or "not yet".
- **Junior mistake:** the trap a junior falls into that this avoids.
- **Measured effect:** before → after (latency / $ / rows), if known.
```

## Layer files (create as cards accumulate)
| File | Layer | Focus for this project |
|------|-------|------------------------|
| `01_ingestion.md` | Drive→S3 | content-hash skip-existing, parallel download, manifest watermark |
| `02_extraction_llm.md` | Gemini API | Flash-vs-Pro, structured output, prompt caching, batch, idempotent skip |
| `03_bronze.md` | Bronze | parquet over JSON, partition by date, immutable append |
| `04_silver.md` | Silver | DuckDB vectorization, projection/predicate pushdown over httpfs, array explode once |
| `05_gold.md` | Gold | bridge-table joins, incremental marts, VSS index build cost |
| `06_serving.md` | Serving | query shaping, VSS top-k, result caching |
| `07_orchestration.md` | Airflow | deferrable operators, gemini_api Pool sizing, dynamic task mapping |
| `08_dq.md` | Quality | gate ordering cheapest-first, quarantine-not-retry on LLM output |

## Example card (seed)
### OPT-EXT-01 — Cache raw Gemini JSON in Bronze forever (re-parse, never re-pay)
- **Layer:** bronze / extraction
- **Status:** 🟡 APPLICABLE (build pending)
- **What:** persist the verbatim Gemini response immutably; all re-models re-parse Bronze.
- **Why here:** the API call is the only real cost cliff; re-running it on a re-model is the
  single most expensive avoidable mistake (ADR-003, finops round-1).
- **Applied at:** not yet — target `models/staging/stg_gemini_raw.sql` reads Bronze, never the API.
- **Junior mistake:** re-calling Gemini whenever the schema changes → re-billing the whole library.
- **Measured effect:** target — a full re-model of 500 videos = $0 API (vs $20–150 re-pay).

## Cross-layer junior-mistakes drill table (fill as cards land)
| # | Junior mistake | Layer | Card |
|---|----------------|-------|------|
| 1 | Re-call Gemini on every re-model | bronze/ext | OPT-EXT-01 |
| 2 | Spark on KB–MB data | silver | (see ADR-001) |
| 3 | Store ratios in the fact | gold | OPT-GOLD-?? |
| 4 | Synchronous per-video polling in Airflow | orchestration | OPT-ORC-?? |
