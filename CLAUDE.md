# Creative Intelligence Pipeline — AI Context

> Auto-loaded by Claude Code every session. Standalone project (no parent gym dependency).

## Project Overview
**Domain**: Advertising / creative-ops intelligence
**Problem**: Turn messy raw ad video (a client's Google Drive folder of near-duplicate
compilation footage) into a **structured, queryable creative feature store** — every line
of dialogue, hook, theme, sentiment, and a `standalone_score` (can this clip be reused
alone?) — so a marketing team can search past footage and assemble new ad scripts.
**Modelling**: Hybrid — asset-graph + star marts (see ADR-002).
**Purpose**: Data Engineering portfolio project (single-dev).

## v1 Scope (LOCKED — see @scope-guardian)
v1 = the **queryable creative feature store** only. Explicitly OUT (v2 BACKLOG):
1. AI creative search engine  2. RAG script generator  3. creative-ops dashboard
4. automated tagging/archiving. Also OUT: ROAS / ad-performance ingestion, vector DB.

## Stack (locked)
| Layer | Storage | Compute / engine | Notes |
|-------|---------|------------------|-------|
| Source | client Google Drive folder | `scripts/ingest_drive_to_s3.py` | near-duplicate videos |
| Landing (Bronze raw) | **S3** raw, append-only | `scripts/run_gemini_extract.py` | keep Gemini response **word-for-word**; re-parse without re-paying |
| Identity | — | content hash (MD5/SHA-256) = `asset_id` | skip-existing idempotency |
| Silver | **S3 (`external` parquet)** | dbt-duckdb | row-per-semantic-chunk; filler removed, timestamps normalized |
| Gold / marts | **S3 (`external` parquet)** | dbt-duckdb `models/marts/{core,performance}` | graph edges + star facts + perf marts (SPEC_v1.5) |
| Quality | Great Expectations | per-layer suites + golden-dataset | LLM-output gates |
| Orchestration | local Airflow | `dags/creative_intel_pipeline.py` | deferrable |
| Significance | Python post-step | `scripts/significance_post_step.py` | v1.5 |
| **Serving** | reads Gold S3 | **Snowflake Cortex** (external tables + Cortex Search + Power BI); **DuckDB VSS = $0 fallback** | read-only veneer; Gold S3 = sole truth (ADR-005) |

⚠️ Stack boundary (ADR-001 + **ADR-005**): **storage = unified S3** (no MinIO; DuckDB catalog
ephemeral/compute-only). DuckDB over Spark settled (ADR-001) — DuckDB stays the transform engine.
Snowflake admitted ONLY as a read-only serving veneer over Gold S3 (ADR-005 override), never as
transform engine or source of truth. Still rejected: Spark / Databricks / Glue / dedicated vector DB.

## Architecture of Record
`architecture/` — DATA_MODEL.md (+ v1.5), ERD_consolidated.md / erd.dbml, STACK_AND_FLOW.md,
DBT_DAG.md, SPEC_v1_search.md, SPEC_v1.5_performance_marts.md, and:
- ADR-001 — DuckDB over Spark (amended on storage/serving axis by ADR-005)
- ADR-002 — graph over star
- ADR-003 — chunking in Silver
- ADR-004 — performance-veto converted
- ADR-005 — unified S3 storage + Snowflake Cortex serving veneer (owner override, no MinIO)

## The hard problems (the design drivers)
- **Identity**: near-duplicate videos → content hash, not random key.
- **No performance data**: raw footage has no spend/impressions → feature store, not a
  media-buying dashboard.
- **Frankenstein content**: mixing 10s slices breaks message → model for coherent reuse.
- **Semantic chunking**: cut by *meaning* not *duration*; Gemini emits `chunk_theme`,
  `sentiment`, `standalone_score` (1–5), `next_compatible_themes`.
- **Testing a non-deterministic LLM pipeline**: golden-dataset + value-range/schema gates.

## Cabinet (7 agents) — see `.claude/agents/`
**Veto holders**: @data-architect (Opus, ultimate — the model is the hard part) ·
@scope-guardian (Sonnet, hard veto on scope creep).
**Build**: @senior-data-engineer (Sonnet) · @data-quality-steward (Sonnet) ·
@product-owner (Sonnet) · @finops-agent (Sonnet, part-time — Gemini token cost).
**Conditional**: @qa-engineer (Haiku — activate when golden-dataset testing is its own workstream).
@cikgu (Sonnet) is the optional teaching mentor — NOT a build agent; he teaches, never builds.
Roster rationale: `AGENT_ROSTER_RECOMMENDATION.md`.

## Build quickstart
See `README_BUILD.md`. Short version:
1. `bash setup.sh`  → scaffold + venv + deps + `dbt parse`
2. `cp .env.example .env` → fill `GEMINI_API_KEY`, `S3_BUCKET`
3. `cp profiles.yml.example ~/.dbt/profiles.yml` (or `DBT_PROFILES_DIR=.`)
4. Implement stubs marked `where 1=0` / `TODO` from `architecture/SPEC_*`
5. `dbt seed && dbt build -s marts.core` (v1), then `marts.performance` + significance step (v1.5)

## Token Discipline (all agents + main session)
1. Checkpoint first: read `PROJECT_STATUS.md` (and `DEBUG_CHECKPOINT.md` if debugging,
   `learning/LEARNING_LOG.md` if a cikgu session) BEFORE reading code.
2. Scope: read only files in the current module — max ~3 files/turn.
3. Use the Explore subagent to find "where is X" instead of reading many files inline.
4. Update the checkpoint before ending a turn.

## What NOT To Commit
CLAUDE.md, PROJECT_STATUS.md, COST_LOG.md, DEBUG_CHECKPOINT.md, LEARNING_LOG.md,
SIGN_OFF_LOG.md, .env*, data/, *.parquet, *.csv (except seeds/), raw video.
