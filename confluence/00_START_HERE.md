# Creative Intelligence Pipeline — Start Here

> **New here? Read this page top to bottom, then follow the reading path at the bottom.**
> By the end you should understand *what this pipeline does, why it's built the way it is, and
> where to look before you change anything.* Source of truth is the git repo; these Confluence
> pages are published from it (`scripts/sync_docs_to_confluence.py`).

## What this project is

Turn messy raw ad video — a client's Google Drive folder of near-duplicate compilation footage —
into a **structured, queryable creative feature store.** Every line of dialogue, hook, theme,
sentiment, and a `standalone_score` (can this clip be reused on its own?) becomes a row a marketing
team can search, so they can find past footage and assemble new ad scripts.

**North-star:** "find me frustrated-customer 'engine feels heavy' clips that stand alone, and stitch
a Hook → Body → CTA sequence from different source videos." That cross-video assembly — without
creating Frankenstein nonsense — is the whole point.

**Domain:** advertising / creative-ops intelligence. **Modelling:** hybrid asset-graph + star marts.

## The hard problems (this is *why* the architecture looks the way it does)

A newcomer who understands these five will understand every major decision:

1. **Identity** — the videos are near-duplicates, so the key can't be a random id. Identity is a
   **content hash** (`asset_id = sha256("{client_id}:{content_sha256}")`). Same bytes = same asset.
2. **No performance data** — raw footage has no spend/impressions. So this is a **feature store**,
   not a media-buying dashboard. (Ad-performance marts exist but are v1.5 and need real exports.)
3. **Frankenstein content** — naively mixing 10-second slices breaks the message. The model captures
   *which chunks can legitimately follow which* so reuse stays coherent.
4. **Semantic chunking** — cut by *meaning*, not by duration. The LLM (Gemini) emits `chunk_theme`,
   `sentiment`, `standalone_score` (1–5), `next_compatible_themes` per chunk.
5. **Testing a non-deterministic LLM pipeline** — you can't assert exact output. So quality is
   golden-dataset + value-range/schema gates, not equality checks.

## The stack (locked)

| Layer | Storage | Engine | Note |
|-------|---------|--------|------|
| Source | client Google Drive | `ingest_drive_to_s3.py` | near-duplicate videos |
| Landing / Bronze | **S3** (append-only) | `run_gemini_extract.py` | verbatim Gemini response kept — re-parse, never re-pay |
| Silver | **S3** external parquet | dbt-duckdb | row-per-semantic-chunk |
| Gold / marts | **S3** external parquet | dbt-duckdb | graph edges + star facts |
| Serving | reads Gold S3 | Snowflake Cortex; **DuckDB VSS = $0 fallback** | read-only veneer; Gold S3 = sole truth |
| Orchestration | local Airflow | `dags/creative_intel_pipeline.py` | deferrable |

**Rejected tech (do not reintroduce):** Spark, Databricks, Glue, MinIO, a dedicated vector DB.
Why: see the Architecture Decisions page. The data is KB–MB; DuckDB is the right-sized engine.

## Before you change anything (the rule that keeps this repo honest)

This project is **governed as code, not by vigilance.** Before editing a model, schema, storage
path, or identity rule, open the ADR that governs it (see the **Architecture Decisions** page) and
run the binding checks: `tests/lineage_contract.py`, `tests/boundary_contract.py`,
`tests/doc_reference_contract.py`. If a change conflicts with a decision, the gate goes red — that's
the design, not an obstacle.

## Your onboarding reading path

Nine pages, in order — the standard DE-team doc set plus one added for real CI/cloud deployment
mechanics, each page telling you who it's for:

1. **Pipeline Documentation** — the flow, source → landing → bronze → silver → gold. Read by
   everyone. `confluence/02_PIPELINE_DOCUMENTATION.md`
2. **Data Contract** — schema, types, mandatory fields, null rules, lineage/identity rules. Read by
   the source team & data engineers. `confluence/03_DATA_CONTRACT.md`
3. **Architecture Decisions (ADR)** — why DuckDB not Spark, content-hash identity, etc. Read by
   architects & reviewers. `confluence/01_ARCHITECTURE_DECISIONS.md`
4. **Data Dictionary** — what every column means. Read by BI & analysts. `architecture/DATA_DICTIONARY.md`
5. **Runbook** — how to rerun the pipeline on failure, with real cited incidents. Read by support &
   ops. `confluence/04_RUNBOOK.md`
6. **Release Notes** — what changed, most recent first. Read by everyone. `confluence/05_RELEASE_NOTES.md`
7. **Known Issues** — bugs/gaps not yet fixed. Read by the team. `confluence/06_KNOWN_ISSUES.md`
8. **Incident Postmortem** — root cause of production issues. Read by engineering. **Stub today** —
   no real incident yet. `confluence/07_INCIDENT_POSTMORTEM.md`
9. **Deployment Guide** — how CI/CD and Snowflake serving actually deploy (AWS OIDC role
   federation, the 5-phase Snowflake provisioning script). Read by whoever maintains CI or stands
   this up on a new account. `confluence/08_DEPLOYMENT_GUIDE.md`

After this, you'll know enough to pick up a maintenance or optimization task and know which ADR and
which gate it answers to. The detailed build log behind all of this is `PROJECT_STATUS.md`.
