# Creative Intelligence Pipeline

> **Status: built and verified against real infrastructure.** v1 + v1.5 delivered — real assets
> extracted and chunked, Silver/Gold on S3, and **two live query surfaces** for semantic search.
> This is production client-delivery work, not a prototype or a design exercise.
> Full evidence trail: `PROJECT_STATUS.md`; decisions: `architecture/ADR-001…013`.

## What is actually running

| Capability | Implementation | State |
|---|---|---|
| Ingestion | Google Drive → S3 landing (`scripts/ingest_drive_to_s3.py`), content-hash asset identity | Verified |
| AI extraction | Gemini API → Bronze, raw response preserved verbatim (`scripts/run_gemini_extract.py`) | Verified |
| Modelling | dbt star schema + bridges over S3 external tables (`models/marts/`) | Verified |
| **Serving A — local** | DuckDB VSS vector index over the chunk feature store | Verified |
| **Serving B — warehouse** | Snowflake **native `VECTOR`** view `FACT_CHUNK_VECTOR` using `VECTOR_COSINE_SIMILARITY`, over 8 external tables on real Gold S3, row-for-row reconciled | Verified |
| Embeddings | `scripts/generate_embeddings.py`; queried via `scripts/search_cli.py --snowflake-semantic` | Verified |
| Access control | Snowflake storage integration + `CREATIVE_INTEL_ROLE` least-privilege grants | Verified |
| Orchestration | Airflow (`dags/creative_intel_pipeline.py`), import-clean, `refresh_serving` does real work | Verified |
| CI/CD | GitHub Actions with **AWS OIDC role federation — no static cloud credentials** (ADR-013) | Verified |
| Data quality | Great Expectations suites + lineage / boundary / doc-reference / ADR-coupling gates | Verified |

**A dead end worth reading:** Snowflake Cortex Search Service was attempted for real and abandoned
after three successive blockers (BYO-embedding conflict → Dynamic Tables reject external tables →
trial-tier accounts cannot run the required AI function). The native `VECTOR_COSINE_SIMILARITY`
view is the permanent answer here. Trail: ADR-005 Addenda #2/#3/#4.

## What this project is
An ETL/ELT pipeline that turns **messy raw advertising video** (client uploads a Google
Drive folder of compilations — long, short, near-duplicate creative footage) into
**structured, queryable creative intelligence**: every line of dialogue, hook, theme,
sentiment, and a "can this clip stand alone?" score — so a marketing team can search,
mix-and-match, and generate new high-converting ad scripts from past footage.

## Pipeline flow (landing → Bronze → Silver → Gold)
1. **Source** — client Google Drive folder link (messy compilation videos).
2. **Landing (S3 raw)** — Drive → S3 via API/script. Near-duplicate videos exist
   (differ by 2–3 seconds) → need a content-based identity, not a random number.
3. **Bronze** — raw, append-only. Keep the *exact* Gemini API response word-for-word.
   No business logic yet (re-parse without re-paying API).
4. **Silver** — cleansed, tabular, row-per-segment. Filler words removed, timestamps
   normalized, entities/keywords extracted.
5. **Gold** — modelled (star / asset-graph / feature store) for query + downstream apps.

## The hard problems this design had to solve
- **P1 — Identity:** near-duplicate videos (differing by 2–3 seconds) need a deterministic
  identity, not a surrogate key. Resolved with a content hash (SHA-256) as `asset_id` —
  identical hash means exact duplicate, so re-processing is skipped and the API is not re-paid.
- **P2 — Attribution gap:** raw/unedited footage has NO ad-performance data; only the *edited*
  clip that actually ran has spend/impressions/conversions, and often not even that. Scoped
  deliberately to a **searchable, queryable creative feature store** rather than a media-buying
  dashboard, with an edit-decision-list bridge to carry performance back to source chunks.
- **P3 — Frankenstein content:** cutting 40 videos into ~10-second slices by timestamp and
  mixing them produces clips that are sometimes irrelevant / message-breaks. How do we
  model the data so mix-and-match stays coherent?
- **P4 — Semantic chunking:** cut by *meaning* rather than by *duration* — Gemini emits "semantic chunks" with `chunk_theme`, `sentiment`,
  `standalone_score` (1–5: safe to reuse alone), `next_compatible_themes`.
- **P5 — Testing:** how do we test an LLM-driven pipeline whose output is non-deterministic
  JSON with business-logic constraints?

## Downstream apps this Gold layer enables
1. AI-powered creative search engine (SQL/text/vector over the feature store).
2. RAG-based script/creative-brief generator (retrieve winning segments → Gemini).
3. Creative-ops analytics dashboard (which hooks/themes correlate with winners).
4. Automated tagging + asset archiving (auto-organize the messy Drive/S3).

## Design record
- `debate/00_AGENDA.md` — the contested design questions.
- `debate/DEBATE_LOG.md` — positions considered and the rulings taken.
- `architecture/DATA_MODEL.md` — conceptual/logical data model + star/graph schema.
- `PROJECT_STATUS.md` — dated build/verification log, newest first.
