# Gate registry

One row = one gate = one bug class that **cannot recur**, because code (not memory) checks it.
Per CLAUDE.md's ANTI-SHORTCUT PROTOCOL: "for anything high-cost, build a gate." This table is
the answer to "can that bug happen again?" — if a bug class isn't here, it isn't closed yet.

When fixing a real bug (not a feature): add a row here in the same change, or name why no gate
applies. A bug class that recurs without a new row is an architecture gap, not a one-off.

| Gate | Bug class it prevents | Where it runs | Layer |
|---|---|---|---|
| `tests/lineage_contract.py` | Orphan client_id, asset_id≠sha256(client_id:content_sha256), path/column lineage drift, placeholder client_id reaching prod (ADR-006) | CI + `.claude/hooks/governance_guard.py` post-edit | Drift / lineage |
| `tests/boundary_contract.py` | Banned stack creeping in (Spark/Databricks/MinIO/vector-DB/RAG/dashboard imports), v1 scope creep (ADR-001/004/005) | CI + `.claude/hooks/governance_guard.py` post-edit | Drift / scope |
| `tests/doc_reference_contract.py` | A doc names a model/path that doesn't exist (e.g. `lineage_guard.py` claimed in 3 docs but never built; `stg_meta`/`stg_tiktok` vs real `stg_meta_perf`/`stg_tiktok_perf`) — both found and fixed 2026-06-25 | CI | Drift / docs |
| `tests/test_doc_reference_contract.py` | The doc-reference gate itself silently breaking and waving real drift through unnoticed | CI | Drift (meta — guards the guard) |
| `models/marts/core/_core.yml` + `_performance.yml` dbt schema tests | Null/duplicate PKs, broken FK relationships, out-of-range `standalone_score`, missing `bridge_ad_chunk` grain guard | `dbt build` (manual today; not yet in CI — see open items) | Column-level / shape |
| `great_expectations/expectations/bronze_asset_raw.json` (chunk_count ≥ 1, `severity: warn`) | A schema-valid-but-empty `{"chunks": []}` Gemini response silently vanishing before any Silver row exists to test (DQD.md §1 gate 1, the 5th LLM-output gate) | `dbt build` (parse-time column test on the source) | Data quality (LLM output) |
| `great_expectations/expectations/silver_chunk.json` | Null/duplicate `chunk_id`, out-of-range `standalone_score`, null `chunk_theme`, `sentiment` outside the fixed enum | Authored; **not yet executed against real data** — only JSON-validity-checked in CI today (open item below) | Data quality |
| `tests/golden/run_golden_test.py` | A silently-WRONG computed value that still passes every shape/range test — e.g. `standalone_score` off-by-one, a swapped `chunk_theme`/`sentiment` column, a `chunk_sequence`/`chunk_id` mismatch in the `stg_gemini_raw` unnest. The "Revenue = Sales, not Sales − Refund" class of bug | CI (`golden_test` dbt target, local fixture, $0/no-cloud) | **Logic** |

## Open (named, not yet gated)

| Gap | Severity | Why it's not closed yet |
|---|---|---|
| EDL → `bridge_ad_chunk` row-count reconciliation (inner join can silently drop EDL rows whose `chunk_id` is absent from `fact_chunk`) | HIGH (DQD.md §3 item 2) | Scoped for the v1.5 performance-marts pass, not yet built |
| GE suites authored but not executed against real data in CI (only JSON-validity-checked) | MEDIUM | `dbt build` itself isn't in CI yet (only `parse`+`seed`); wiring real GE checkpoints is the natural follow-up once that's true |
| Row-count / null% / freshness / volume-anomaly monitoring (Layer 7) | MEDIUM | No baseline yet to anomaly-detect against — needs more real production days first |
| Enumeration / scope discipline (reviewing all N files in a module, not a sample) | — | Protocol-only (CLAUDE.md ANTI-SHORTCUT rule 2) — not mechanically gateable |
