# Creative Intelligence Pipeline — AI Context

> Auto-loaded by Claude Code every session. Standalone project (no parent gym dependency).

## 🛑 STOP-GATE — read before ANY data/model/lineage work
This project is governed. Before you edit a model, seed, schema, storage path, or ingest
script — or before you "proceed" past a lineage/identity question — you MUST:
1. **Open the ADR/spec that governs it first.** Lineage & identity → ADR-006 +
   `architecture/LINEAGE_CONTRACT.md`. Grain/graph/star → ADR-002 + DATA_MODEL.md.
   Stack boundary (rejected tech) → ADR-001/004/005 + `architecture/BOUNDARY_CONTRACT.md`.
   Scope → CLAUDE.md "v1 Scope (LOCKED)" + `architecture/BOUNDARY_CONTRACT.md` + @scope-guardian.
2. **Validate lineage & fidelity BEFORE building downstream.** Every asset must trace to a
   **real registered client** (`dim_client.csv`) and a content hash, with a storage path
   that proves it: `s3://<bucket>/landing/<client_id>/video/<asset_id>.<ext>` where
   `asset_id == sha256("{client_id}:{content_sha256}")` (ADR-006). Run
   `python tests/lineage_contract.py` and `python tests/boundary_contract.py` — these are the
   binding checks, not your judgement.
3. **If a rule and the request conflict, STOP and surface it** — do not silently proceed.
   Mixed-domain dimension, placeholder client_id, path/column drift, banned tech
   (Spark/Databricks/MinIO/vector-DB/RAG/dashboard), scope creep → name it, cite the doc, and
   ask @data-architect / @scope-guardian before writing code.

This gate is enforced three ways so it cannot be skipped: this prompt (soft), the
`.claude/hooks/governance_guard.py` pre/post-edit hook (blocks edits to governed files), and
CI `tests/lineage_contract.py` + `tests/boundary_contract.py` (blocks the PR). Governance is
code, not vigilance.

## 🔁 ANTI-SHORTCUT PROTOCOL — read-before-touch, reconcile-before-done
The #1 way work goes wrong here is the *shortcut*: writing code or a claim from in-context
memory instead of from the file as it is NOW. Context goes stale after an edit and in long
threads. These four rules apply to EVERY edit, claim, and "done" — each is observable in the
transcript, so a skipped step is visible, not a matter of trust:
1. **Read-before-touch** — never edit or assert about a file from memory. Read it THIS turn
   first. (The migration-map class of bug is always this rule skipped.)
2. **Enumerate, don't sample** — for any "all N" task, get N from ground truth (`ls`/`grep`/
   manifest) BEFORE acting, then re-count after. N_before must equal N_after.
3. **Reconcile-before-done** — before saying done/fixed/green, restate the request as a
   numbered checklist with evidence (command output / `file:line`) per item. No evidence =
   say "unverified", not "done". Run the actual gate; don't declare on a parse-clean.
4. **Tag assumptions** — any load-bearing claim not checked this turn is marked "(unverified)".

The machine half (so this doesn't depend on anyone remembering): `tests/doc_reference_contract.py`
proves every model/path a doc references actually exists — point it at a MIGRATION_MAP / spec
before trusting it (`python tests/doc_reference_contract.py <file.md>`). Same philosophy as the
lineage/boundary contracts: code does not get tired, and code does not write from memory.

The *navigation* half: `architecture/REPO_MAP.md` is a generated pointer index (file → purpose →
uses → used-by) so "what is X / what touches X" is one cheap read, not a whole-repo token burn.
It is 100% derived (`python scripts/gen_repo_map.py`; CI runs `--check` and fails if stale), so
it cannot drift — an ad-hoc change that shifts the import/`ref()` graph turns the gate red until
the index moves with it. **It is a pointer, not a cache: it tells you which file to open, then you
READ THAT FILE FRESH** (rule 1) before editing or asserting. Trusting the index without opening the
file is just the stale-cache bug at larger scale.

**Drafting & teaching aid (cikgu):** skeleton-first is encouraged — write intent as a numbered
pseudocode comment block, THEN fill in code ("programming by intention"). It forces what+why
before how. BUT: that scaffold is a thinking tool — before commit, strip comments that merely
restate WHAT the code obviously does (comment-rot); keep only WHY/non-obvious ones, matching the
sparse-comment house style. Do NOT make "comment every block" a commit rule.

## 🗣️ Conversational language (ADR-011, rescoped by Addendum 2026-06-27)
**Narration defaults to plain English; artifacts always English.** Manglish narration is now
**opt-in** — use Malaysian Technical Manglish only when the owner asks for it in-session (the
Manglish-first default was repealed; in practice it drifted into Indonesian-sounding output the
owner found unreadable). When Manglish *is* requested, follow the voice spec in ADR-011 §B
(`aku`/`kau`, markers `lah`/`je`/`ni`/`tu`, BM structure + English technical terms, no
Indonesian/formal-BM drift). `@cikgu` stays English-first teaching, Manglish as the Layer-2 unblock.
Full spec + the rescope rationale: `architecture/ADR-011-conversational-language-protocol.md`.

## 💸 Token-efficiency & session discipline (ADR-012 — operating protocol)
Cut redundancy, never the guardrails (the anti-shortcut protocol + gates above are what make
cost-cutting safe — rework is the worst burn). Full detail + the measured baseline/projection:
`architecture/ADR-012-token-efficiency-and-session-discipline.md`. The load-bearing habits:
- **Model routing:** @data-architect (Opus) only for the 6 Clean-ERD doctrine calls; minor rulings
  → @scope-guardian/Sonnet or a gate. Batch related cabinet questions into one spawn.
- **Subagents for verbose, *independent* work only.** Coupled work (e.g. SDE→DQ→SDE gate-loops)
  stays on the main thread — splitting it loses shared state AND costs ~7× in reloads.
- **Gate over re-read:** for any "is this consistent?" check, run the contract (≈0 tokens,
  deterministic) instead of re-reading files. Cheapest-gate-first, fail fast.
- **Session guard (Lever 6):** watch the Claude Context Bar — yellow (50–75%) = finish the current
  unit + keep `PROJECT_STATUS.md` "▶ RESUME HERE" current; **red (>75%) = checkpoint + start a fresh
  session** (before the ~80% auto-compact). Resume cheap: read the RESUME-HERE block, not all of
  PROJECT_STATUS. Assistant writes the next-session prompt into that block at the breakpoint.

## Project Overview
**Domain**: Advertising / creative-ops intelligence
**Problem**: Turn messy raw ad video (a client's Google Drive folder of near-duplicate
compilation footage) into a **structured, queryable creative feature store** — every line
of dialogue, hook, theme, sentiment, and a `standalone_score` (can this clip be reused
alone?) — so a marketing team can search past footage and assemble new ad scripts.
**Modelling**: Hybrid — asset-graph + star marts (see ADR-002).
**Purpose**: Data Engineering portfolio project (single-dev).

## v1 Scope (LOCKED — see @scope-guardian)
v1 = the **queryable creative feature store** — and per owner decision 2026-06-27, that is the
**entire, permanent scope of this project**. There is no v2 follow-on app horizon anymore; the
items below are not "deferred," they are **REJECTED — will not be built here**:
1. AI creative search engine  2. RAG script generator  3. creative-ops dashboard
4. automated tagging/archiving. Also REJECTED: ROAS/ad-performance live-connector ingestion
(the v1.5 performance *marts* — fed by a hand-supplied export, not a connector — stay IN),
dedicated vector DB. Full ruling: `BACKLOG.md`.

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
| **Serving** | reads Gold S3 | **Snowflake** (external tables + native `VECTOR` semantic search + Power BI; managed Cortex Search Service tried for real, abandoned — trial-tier wall, ADR-005 Addenda #2–#4); **DuckDB VSS = $0 fallback** | read-only veneer; Gold S3 = sole truth (ADR-005); reconciliation run live 2026-06-27 |

⚠️ Stack boundary (ADR-001 + **ADR-005**): **storage = unified S3** (no MinIO; DuckDB catalog
ephemeral/compute-only). DuckDB over Spark settled (ADR-001) — DuckDB stays the transform engine.
Snowflake admitted ONLY as a read-only serving veneer over Gold S3 (ADR-005 override), never as
transform engine or source of truth. Still rejected: Spark / Databricks / Glue / dedicated vector DB.

## Architecture of Record
`architecture/` — DATA_MODEL.md (+ v1.5), ERD_consolidated.md / erd.dbml, STACK_AND_FLOW.md,
DBT_DAG.md, SPEC_v1_search.md, SPEC_v1.5_performance_marts.md; the doc-gap set added by the
2026-06-22 convene — BRD.md, DRD.md, DATA_DICTIONARY.md, DQD.md, STTM.md (all @data-architect +
@scope-guardian gate-approved as documentation-debt closure, not scope creep); and:
- ADR-001 — DuckDB over Spark (amended on storage/serving axis by ADR-005)
- ADR-002 — graph over star
- ADR-003 — chunking in Silver
- ADR-004 — performance-veto converted
- ADR-005 — unified S3 storage + Snowflake Cortex serving veneer (owner override, no MinIO)
- ADR-006 — multi-client tenancy (`dim_client` + tenant-scoped asset identity)
- ADR-007 — landing TTL (guarded hard-delete @ 30 days)
- ADR-008 — Airflow orchestration wiring (isolated `venv_airflow/` + cross-venv script invocation)
- ADR-009 — Slack failure alerts + Confluence doc sync (Addendum 2026-06-27: curated onboarding set)
- ADR-010 — repo-map + ADR-coupling gates (the navigation/governance machinery itself)
- ADR-011 — conversational language protocol (Manglish opt-in, rescoped by Addendum 2026-06-27)
- ADR-012 — token-efficiency & session-discipline operating protocol
- ADR-013 — AWS OIDC role federation for real `dbt build` in CI (push-to-main only, no static keys)

**Governance gate:** @data-architect holds ULTIMATE VETO and enforces the **Clean-ERD
Doctrine** on every model change — 1 table = 1 grain = 1 business entity · no mixed-domain
dimensions · bridge tables (not CTEs) for N:N · serving = view, never a duplicated physical
table · one isolated SCD strategy per table · what's deliberately OUT stays named in ERD §6.
No Gold/marts work proceeds without architecture sign-off. Full doctrine + veto format:
`.claude/agents/data-architect.md`.

## Repo map (beyond architecture/)
- `BACKLOG.md` — v2-deferred items + the gym-apparatus-port ruling (cheatsheets/learning kept
  as templates, gym agents/incubator rejected — see `AGENT_ROSTER_RECOMMENDATION.md`)
- `debate/` — original cabinet convene record: `00_AGENDA.md` (contested questions) +
  `DEBATE_LOG.md` / `ROUND_02_PERFORMANCE_DEBATE.md` (rulings). Historical, not a build target.
- `great_expectations/` — suite README + per-layer expectation JSON (`expectations/`)
- `cheatsheets/{troubleshooting,optimization}/00_INDEX.md` — card-format libraries, English,
  DuckDB-native; templates only until v1 ships AND ≥1 real incident lands (BACKLOG-gated)
- `learning/CURRICULUM.md` — @cikgu's M0–M11 teaching path; `LEARNING_LOG.md` is the
  score/progress log (run @cikgu as a main session, not a subagent, for actual teaching)
- `analyses/demo_queries.sql` — ad-hoc dbt analyses (not models, not built/tested by `dbt build`)
- `.github/workflows/ci.yml` — static-gates-only CI ($0, no cloud, no secrets): ruff lint,
  py_compile, `dbt deps && dbt parse`, `dbt seed`, GE JSON validity, no-`.env`-committed guard

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
`.env*`, `data/`, `*.parquet`, `*.csv` (except `seeds/`), raw video, `COST_LOG.md`,
`DEBUG_CHECKPOINT.md`, `SIGN_OFF_LOG.md` (ephemeral working logs, created during build —
not yet present; add to `.gitignore` when they first appear).

**Intentionally committed** (unlike the parent gym pattern this project borrowed agents
from): `CLAUDE.md`, `PROJECT_STATUS.md`, `learning/LEARNING_LOG.md` — this is a standalone,
self-contained repo by design; see `PROJECT_STATUS.md` "Standalone status".
