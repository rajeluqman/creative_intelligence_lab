# DATA MODEL & ARCHITECTURE OF RECORD — Creative Intelligence Pipeline

**Owner:** @data-architect · **Status:** Ratified 2026-06-20 (cabinet convene)
**Source of truth for rulings:** `../debate/DEBATE_LOG.md`

> **Paradigm (locked):** Asset-lineage **graph + chunk feature store**
> (+ vector index *beside* the relational model, v2). **NOT** a Kimball star.
> Governing principle: *model the domain you actually have, not the one your resume wants.*

---

## 1. Conceptual model

Two first-class entities and two graph-natured relationships:

```
        ┌────────────────────┐        parent_asset_id (self-edge)
        │      ASSET         │◄──────────────────────────────┐
        │ (raw OR edited     │   RAW ──"cut into"──► EDITED   │
        │  creative video)   │───────────────────────────────┘
        └─────────┬──────────┘
                  │ 1 asset → N chunks  (fan-out in Silver)
                  ▼
        ┌────────────────────┐    compatible_with (chunk↔chunk edge)
        │       CHUNK        │◄──────────────────────────────┐
        │ (one standalone    │   "what theme can follow this" │
        │  marketing beat)   │───────────────────────────────┘
        └────────────────────┘
```

- **ASSET** — a creative video, raw or edited. `parent_asset_id` is a **discovery
  lineage** edge (RAW→EDITED), used to "find more clips like this winning edit." It is
  **NOT** a performance-attribution edge (see §6 / Veto 1).
- **CHUNK** — the unit of value: a semantically complete marketing beat (Hook, Problem,
  Solution, Social Proof, CTA…) that can stand on its own. **Grain of the whole model.**
- **chunk↔chunk compatibility** — the adjacency that powers safe mix-and-match and
  prevents "Frankenstein content" (problem P3).

## 2. Grain

**One row = one semantic chunk** (`chunk_id`). Not one row per video, not per timestamp
slice. Chunks are emitted by Gemini as meaning-bounded segments (not fixed 10s cuts),
each carrying `chunk_theme`, `sentiment`, `standalone_score` (1–5), `next_compatible_themes[]`.

## 3. Medallion layers & the immutability contract

| Layer | Object | Content | Rule |
|-------|--------|---------|------|
| **Landing** | `landing/video/<asset_id>.<ext>` | original video **bytes** | write-once; **the only place full binary lives**; content-hash named |
| **Bronze** | `bronze_asset_raw` | verbatim Gemini JSON | append-only, **immutable**; + `model_version`, `content_sha256`, `load_ts`; **no business logic** |
| **Silver** | `silver_chunk` | flattened, conformed chunk rows | **chunking happens here**; filler removed, timestamps normalized; GE schema + range gates |
| **Gold** | `dim_asset`, `fact_chunk`, `bridge_asset_lineage`, `bridge_chunk_compatibility`, `dim_keyword_bridge`/`dim_theme_bridge` | query-shaped feature/graph tables | arrays exploded → **no array columns in Gold** |

**Why chunking lives in Silver, not Bronze:** Bronze must stay the verbatim, immutable
Gemini response so any downstream re-model is a **re-parse, never a re-pay** (cost firewall,
§7). Chunking is a transformation → Silver. Gold would be too late (it already models
relationships *between* chunks). **Why video bytes never enter the lake:** binary store and
analytical store are separated; the lake holds metadata + transcripts + **pointers**
(`s3_uri` + `start_ts` + `end_ts`) so apps can seek into the original for playback without
the warehouse ever storing frames.

## 4. Logical schema (Gold)

### `dim_asset` (node)
| column | type | notes |
|--------|------|-------|
| `asset_id` (PK) | VARCHAR | SHA-256 of video bytes |
| `parent_asset_id` (FK→self) | VARCHAR | RAW→EDITED **discovery lineage only**; NULL for raw |
| `asset_name` | VARCHAR | original filename |
| `asset_type` | VARCHAR | `RAW` \| `EDITED` |
| `duration_sec` | INT | |
| `source_uri` | VARCHAR | pointer to `landing/video/...` |
| `dq_flag` | VARCHAR | e.g. `likely_near_dup` (MEDIUM signal, no auto-merge) |
| `load_ts` | TIMESTAMP | |

### `fact_chunk` (feature row — grain = one chunk)
| column | type | notes |
|--------|------|-------|
| `chunk_id` (PK) | VARCHAR | |
| `asset_id` (FK→dim_asset) | VARCHAR | |
| `chunk_sequence` | INT | order within asset |
| `start_ts` / `end_ts` | TIME | Gemini-set semantic boundaries (not hardcoded) |
| `transcript_segment` | TEXT | cleaned dialogue |
| `chunk_theme` | VARCHAR | Hook / Problem / Solution / Social Proof / CTA … |
| `sentiment` | VARCHAR | enum-bounded |
| `standalone_score` | INT | **1–5, GE range-gated** — safe-to-reuse-alone score |

### `bridge_chunk_compatibility` (chunk↔chunk edge — explodes `next_compatible_themes[]`)
| column | type | notes |
|--------|------|-------|
| `chunk_id` (FK) | VARCHAR | |
| `compatible_theme` | VARCHAR | one row per chunk per compatible theme |
| `theme_match_score` | DECIMAL | optional ranking |

### `bridge_asset_lineage` (asset↔asset edge)
| column | type | notes |
|--------|------|-------|
| `parent_asset_id` (FK) | VARCHAR | RAW |
| `child_asset_id` (FK) | VARCHAR | EDITED |

### `dim_keyword_bridge` / `dim_theme_bridge`
One row per chunk per keyword/theme — arrays exploded for queryability (no `ARRAY` columns
survive into Gold).

> **`fact_ad_performance` is NOT in v1.** VETOED (§6). If perf ever lands it attaches to the
> EDITED asset that actually ran, behind a provenance/confidence qualifier — v2 backlog.

## 5. dbt materialization path

```
sources: bronze_asset_raw (raw Gemini JSON)
  → stg_gemini_raw        -- flatten JSON; grain = asset_id + chunk_sequence
  → int_chunk_cleaned     -- filler removal, timestamp normalize, score passthrough
  → marts (Gold):
        dim_asset
        fact_chunk                       (+ dbt_expectations range gate 1..5)
        bridge_chunk_compatibility       (explode next_compatible_themes[])
        bridge_asset_lineage
        dim_keyword_bridge / dim_theme_bridge
```
Tests: `unique`+`not_null` on `chunk_id`; `unique` on (`asset_id`,`chunk_sequence`);
`relationships` FK integrity; `dbt_expectations` range on `standalone_score`.

## 6. Vetoes embedded in the model

1. **`fact_ad_performance` + proxy-performance attribution → VETOED.** Raw clip A did not
   convert; edited clip B (possibly 10% A's footage + 9 other sources) did. Attributing B's
   conversions back to A manufactures causality. `parent_asset_id` is retained as a
   **navigation** relationship only. *Principle: a model must not encode an inference as if
   it were a fact — provenance before propagation.*
2. **Flat Gold table → REJECTED.** A flat table discards `bridge_chunk_compatibility` — the
   entire anti-Frankenstein value and the literal mechanism of the north-star query.
   **Graph-from-start**, even on 5–10 videos (the graph is trivially small; the demo is
   gated by Gemini API throughput, not by the join).

## 7. Quality gates (LLM non-determinism)

The novel risk: **Silver is "unreliable narration"** — a row can be schema-valid yet
semantically wrong. Four gates, cheapest-first:

1. **CRITICAL — JSON-schema gate** (Bronze→Silver): malformed/truncated → **quarantine**, never blocks batch.
2. **CRITICAL — business-constraint gate**: `1<=standalone_score<=5`, enum `sentiment`, non-empty `chunk_theme` → **quarantine the row, do not retry** (retrying non-deterministic input just burns API spend).
3. **HIGH — golden-dataset gate**: ~30–50 (pilot: 5) hand-labeled videos, re-run on every prompt/model change, require **≥80% semantic agreement (Jaccard, ±1 on score)** — **the only gate allowed to fail a deploy**, and only at the *pipeline* level, never per-row. On fail → human review, not auto-retry.
4. **MEDIUM — idempotency gate**: same `asset_id` reprocessed → drift beyond tolerance is a **signal, not a block** (LLM variance is expected).

Promotion rule: **Silver constraint-pass ≥95% before Gold build.**

## 8. Stack (locked at this scale)

| Concern | Choice | Why |
|---------|--------|-----|
| Landing transport | Python (Drive API → S3) | content-hash naming, write-once |
| Transcription/extraction | **Gemini API (Flash-first)** | per-second video billing; Flash 10–15× cheaper than Pro |
| Storage | **S3** (video bytes) + S3 (Bronze/Silver/Gold parquet) | pay-per-GB, zero idle |
| Compute / transforms | **DuckDB + dbt-duckdb** | KB–MB structured scale; bottleneck is the API call, not CPU |
| Orchestration | **local Airflow** — deferrable operators + triggerer, `gemini_api` Pool sized to QPM, backoff+jitter on 429, dynamic task mapping `expand()` per `asset_id`, skip-existing short-circuit on hash | async/rate-limit-bound; synchronous PythonOperator polling would pin worker slots |
| Quality | **Great Expectations** + dbt tests | per-layer gates above |
| Demo serving | **Snowflake Cortex** veneer over Gold S3 (Cortex Search + Power BI); **DuckDB VSS = $0 fallback** | satisfies north-star (ADR-005) |

**REJECTED at this scale:** Spark / Databricks / MWAA — over-engineering and idle-cost
anti-pattern for <10K videos. *(Revisit only if @data-architect justifies long-term TCO at
materially higher volume.)*
**ADMITTED by ADR-005 (owner override 2026-06-22):** Snowflake Cortex as a **read-only serving
veneer** over Gold S3 (disposable trial + day-25 teardown; Gold S3 stays sole source of truth).
Storage is now unified S3 (no MinIO).

## 9. Cost firewall

- Spend cliff = **Gemini API tokens** (video ~258–300 tok/sec): 40 vids ≈ $1–5,
  500 ≈ $20–150, 5000 ≈ $200–1500+. Storage/compute are noise by comparison.
- **Controls:** (a) Bronze keeps raw Gemini JSON **forever** → every re-model is re-parse,
  never re-pay; (b) idempotent **skip-existing on `content_sha256`**; (c) **Flash-first**
  model choice.

## 10. v1 scope line (agreed)

**IN:** Drive → S3 landing → Bronze (SHA-256-deduped raw Gemini JSON) → Silver (gated
semantic chunks) → Gold (chunk feature store + `dim_asset` + lineage & compatibility
bridges) → **one SQL/text search demo** returning sane, timestamped, standalone-scored clips
over 5–10 videos.

**OUT (BACKLOG):** all 4 downstream apps (search-engine UI, RAG generator, ops dashboard,
auto-archiver), vector DB, ad-performance ingestion, perceptual/fuzzy dedup,
`fact_ad_performance`.
