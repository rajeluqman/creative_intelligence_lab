# Banking Lakehouse Lab — Project Status

## ▶ RESUME HERE (2026-07-05, evening)
**Planning COMPLETE and RATIFIED. All blockers cleared — build may start.**
- **Stack (D-01 Addendum #3, final):** Databricks = primary engine for ALL transform
  (portable PySpark + Delta, Unity Catalog over S3). S3 = sole truth. Snowflake = serving.
  Fabric + Terraform OUT. Databricks trial is deliberately disposable — run a few times,
  screenshot success + UC lineage into journey/08, drill/troubleshoot, delete; portable code
  keeps the repo runnable locally for defense afterward.
- Repo live: `https://github.com/rajeluqman/banking-multisource-lakehouse`, cloned at
  `/workspaces/banking-multisource-lakehouse` (empty). Push auth verified: `BANK_PAT`
  Codespaces secret + per-repo credential helper (token never on disk); remote URL clean.
- **Next action:** fresh Sonnet session in `/workspaces/banking-multisource-lakehouse`
  using the paste-prompt the owner holds (reads this lab's docs in order, then executes
  `02_SONNET_BUILD_KICKOFF.md` fasa by fasa, stopping at each fasa gate).

## Known gate behaviour (expected, not drift)
`tests/doc_reference_contract.py` pointed manually at these docs flags the future model names
(`dim_customer_xwalk`, `mart_*`) — correct: they are the NEW repo's build targets, not CIL
models. This folder is spec-genre, which the contract's default sweep deliberately excludes
(see `_default_docs()` docstring), and CI only sweeps top-level `architecture/*.md` — so CI
stays green. Do NOT add these names to CIL's ALLOW list; they belong to another repo.

## Status log
- 2026-07-05 — Fasa-0 planning complete (this folder created). Origin: owner's Gemini
  brainstorm 2026-07-04; Opus verified/corrected it (GA4 "live" claim false; Berka added as
  the CRM seed; crosswalk identified as keystone). Datasets: home-credit→Postgres,
  paysim→MSSQL, Berka→SAP-sim file drop, OBP sandbox API, BNM OpenAPI optional.
