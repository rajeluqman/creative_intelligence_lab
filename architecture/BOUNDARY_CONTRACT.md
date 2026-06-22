# STACK + SCOPE BOUNDARY CONTRACT

> **Owners:** @data-architect (stack, ULTIMATE VETO) + @scope-guardian (scope, HARD VETO).
> **Enforced by:** `tests/boundary_contract.py` (CI + pre/post-edit hook).
> **Source docs:** ADR-001, ADR-004, ADR-005, CLAUDE.md "v1 Scope (LOCKED)".

## Why this exists
Same problem as `LINEAGE_CONTRACT.md`: "DuckDB over Spark" and "v1 scope is locked" are
*prompts* until something actually fails the build when violated. This contract turns the
rejected-tech list and the v2-backlog scope boundary into a denylist that runs on every edit
and every PR — so a banned import is caught the moment it's written, not in review.

## What it scans
Executable/config surfaces only: `scripts/*.py`, `dags/*.py`, `models/**/*.sql`,
`analyses/*.sql`, `requirements*.txt`, `setup.sh`, `profiles.yml.example`, `dbt_project.yml`.
**Not** `architecture/`, `debate/`, `.claude/`, `cheatsheets/`, `BACKLOG.md` — those discuss
rejected tech by name on purpose; doc prose is not a violation.

## The rules
| # | Rule | Source |
|---|------|--------|
| ST1 | No Spark / Databricks import or dependency | ADR-001 — DuckDB over Spark |
| ST2 | No MinIO import, and `S3_ENDPOINT` must stay empty in committed config | ADR-005 — unified S3, no MinIO |
| ST3 | No dedicated vector DB client (Pinecone/Weaviate/Qdrant/Chroma/Milvus/FAISS) | ADR-001/004 + v1 scope OUT |
| ST4 | dbt profile `type:` must be `duckdb` everywhere | ADR-001/005 — DuckDB is the sole transform engine; Snowflake is serving-only, never a `target` |
| ST5 | No live ad-platform connector SDK (Meta/TikTok/Google Ads API, Fivetran, Airbyte) | ADR-004 — "connectorized ingest rejected… manual CSV→S3 until ~50+ ads/week + DA TCO sign-off" |
| SC1 | No RAG framework (LangChain, LlamaIndex) | v1 scope OUT — "RAG script generator" |
| SC2 | No dashboard app framework (Streamlit, Dash, Gradio) | v1 scope OUT — "creative-ops dashboard" |

## Named but NOT automatable (review-gated, not code-gated)
Two v1-OUT items are *behavior*, not an import signature, so a denylist would either miss them
or false-positive on legitimate code (e.g. `scipy` is already a dependency for ADR-004's
significance testing — banning "predictive stats" would break that):
- **Automated tagging/archiving** (CLAUDE.md v1 scope OUT)
- **Predictive ML scoring / variant factory** (ADR-004 "Rejected / still-vetoed")

These stay enforced by @scope-guardian review at PR time, cited here so the gap is visible
rather than silently assumed-covered.

## Why `fact_ad_performance` / `stg_meta_perf.sql` / `stg_tiktok_perf.sql` are NOT violations
ADR-004 converted (not reversed) the original performance veto: metrics are allowed IF they
arrive via **manual CSV→S3** landing and attach only to the **edited ad that ran** (never
propagated backward onto RAW). ST5 bans the *live API connector path* that ADR-004 explicitly
still rejects — it does not ban the performance marts themselves.

## How to run
```bash
python tests/boundary_contract.py
```
- **CI:** `.github/workflows/ci.yml` → "Boundary contract" gate (PR + push to main).
- **Hook:** `.claude/hooks/lineage_guard.py` auto-runs it after edits to `scripts/`, `dags/`,
  `models/`, `requirements*.txt`, `setup.sh`, or `profiles.yml.example`, and blocks on failure.

## Changing a rule
Stack rules (ST*) are owned by @data-architect; scope rules (SC*) by @scope-guardian. To
relax/extend one: update this doc AND `tests/boundary_contract.py` in the same change, with a
one-line rationale citing the ADR or scope decision that authorizes it.
