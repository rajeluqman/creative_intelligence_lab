# Release Notes

> **Audience: everyone.** What changed, most recent first. This project has no versioned
> deploys/tags yet (still pre-serving build phase) — these are curated from the real dated
> checkpoints in `PROJECT_STATUS.md`, which remains the detailed source of truth (evidence,
> row counts, real command output) behind every line here.

## 2026-06-27 — Operating protocol
- Confluence restructured into this onboarding-shaped page set (was a 1:1 mirror of every ADR file).
- Token-efficiency & session-discipline operating protocol adopted (model routing, session-guard
  via context-usage checkpoints, cheap session resume).
- Conversational-language default changed: English by default (was Manglish-by-default).

## 2026-06-25 — v1.5 completion push
- **Silver/Gold now materialize on real S3** (was local-DuckDB-only) — the blocker fix for
  "Gold S3 = sole source of truth."
- **Semantic search shipped**: DuckDB VSS embedding pipeline + `search_cli.py --semantic`, verified
  against real Malay-language ad transcripts (cross-lingual retrieval confirmed working).
- **v1 search/assemble demo shipped**: theme/sentiment/score search + cross-asset Hook→Body→CTA
  sequence assembly, run for real against the 169-chunk dataset.
- **Airflow orchestration wired and run for real** (ADR-008) — all 5 DAG tasks call real scripts;
  the cost-firewall (skip-if-nothing-new) proven live, not just claimed.
- **Slack failure alerts + Confluence doc sync shipped and went live** (ADR-009).
- **5th LLM-output gate** added — catches a schema-valid-but-empty Gemini response that previously
  passed every other check.
- v1.5 performance marts smoke-tested against synthetic data, then fully reverted (no synthetic
  residue left committed) — proved the significance-testing pipe works; still waiting on real
  Meta/TikTok exports to use it for real.

## 2026-06-24 — Gemini quota resume
- Remaining 6/19 assets extracted once the free-tier daily quota reset; **19/19 real assets**
  through the pipeline, zero code changes needed (idempotent skip-existing worked as designed).

## 2026-06-22 — First real client run
- First real Drive folder run for a real client (rename: `demo_client` → `voltecx`).
- Multi-client tenancy (ADR-006) and 30-day landing TTL (ADR-007) implemented ahead of the real
  run, by owner directive, to avoid rework right after testing.
- Two automated governance contracts added: lineage + stack/scope boundary, enforced on every edit
  (hook) and every CI run.
- Doc-completeness audit ("doc-gap convene") closed 5 missing doc types (BRD, DRD, Data Dictionary,
  DQD, STTM) against this project's own architecture-of-record.

See **Known Issues** for what's still open, and **Architecture Decisions** for why these choices
were made.
