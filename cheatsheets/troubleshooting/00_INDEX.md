# Troubleshooting Library — Creative Intelligence Pipeline (INDEX)

> Failure-path twin of the optimization library, mirroring the pharma gym's troubleshooting
> structure. One card per failure mode, per phase. Symptom presented FAR from root → trace
> backward (observability-first). Content is English.

## Binding translation note (read first)
This project has **no Spark / Databricks**. Where generic DE troubleshooting advice says
"check the Spark UI / executor logs / shuffle spill", translate to the DuckDB + dbt + Airflow
reality of this stack:

| Generic (Spark world) | This project (DuckDB/dbt/Airflow) |
|-----------------------|-----------------------------------|
| Spark UI / stage timeline | DuckDB `EXPLAIN ANALYZE`, `PRAGMA database_size`, dbt run timing |
| Executor OOM / shuffle spill | DuckDB single-node memory limit; `SET memory_limit`; spill-to-disk temp dir |
| Cluster/driver logs | Airflow task logs (local) + dbt `target/run_results.json` |
| S3A connector errors | DuckDB `httpfs` + endpoint/creds env |
| Stuck stage | Airflow deferrable trigger / `gemini_api` Pool exhaustion |

## Card format (copy this)
```
### <ID> — <symptom, far from root>
- **Phase:** triage | ingestion | extraction | transformation | load | validation | orchestration | cicd | postmortem
- **Status:** ✅ HARDENED (fix cited) | 🟡 APPLICABLE (real, undrilled)
- **Symptom (business/observability):** what a stakeholder/monitor sees first.
- **Backward trace:** observable → … → root.
- **Root cause:** the actual defect.
- **Fix / guard:** `path/to/file:LN` (✅ only).
- **LLM-specific twist:** what makes this harder than deterministic ETL (if any).
- **Junior mistake:** the wrong first move.
```

## Phase files (create as cards accumulate)
| File | Phase | Example failure modes for this project |
|------|-------|----------------------------------------|
| `01_triage.md` | Triage | "search returns nothing" / "correlation mart empty" — where to look first |
| `03_ingestion.md` | Drive→S3 | 0-byte download, truncated video, hash collision, Drive rate limit |
| `04_extraction.md` | Gemini | malformed JSON, truncated response, schema drift across model_version, hallucinated theme |
| `05_transformation.md` | Silver/Gold | array-explode fan-out blow-up, FK orphan chunk, double-count across bridge_ad_chunk |
| `06_validation.md` | DQ | constraint gate flapping on LLM variance, golden-set drift, sample-gate blocking everything |
| `07_orchestration.md` | Airflow | Pool exhaustion, deferrable trigger stuck, 429 storm, skip-existing not firing |
| `08_load_perf.md` | Perf ingest | ad_id→asset_id unmapped, EDITED-only FK violation, restated metrics double-loaded |
| `09_postmortem.md` | Postmortem | template + sealed-rubric pattern |

## Example card (seed)
### TS-EXT-01 — "Silver chunk count dropped to zero for a batch, but no error logged"
- **Phase:** extraction
- **Status:** 🟡 APPLICABLE (undrilled)
- **Symptom:** overnight run "succeeded" (exit 0) but `silver_chunk` gained 0 rows for 12 videos.
- **Backward trace:** empty Silver → Bronze rows present but `chunks` array empty →
  Gemini returned valid JSON with `{"chunks": []}` → prompt/model returned no segments (or a
  content-safety block) → no schema violation, so nothing quarantined.
- **Root cause:** valid-but-empty LLM output passes the schema gate; only a *non-empty* business
  rule catches it.
- **Fix / guard:** add a GE expectation `chunks length >= 1` at the Bronze→Silver boundary
  (`great_expectations/` suite) → quarantine empties for human review.
- **LLM-specific twist:** "schema-valid yet semantically empty" — the unreliable-narration risk;
  deterministic ETL never produces this.
- **Junior mistake:** trusting exit 0 + valid JSON as "data is fine."

## Gym pattern (optional, mirrors pharma ADR-006)
If you want a drill loop: inject one failure per card in an **incubator** (fake creds, throwaway
bucket, per-drill branch), work the trace backward, write the post-mortem, diff vs a sealed rubric.
Keep it fenced from any real cloud. See the pharma gym's `INCUBATOR.md` for the mechanical guard pattern.
