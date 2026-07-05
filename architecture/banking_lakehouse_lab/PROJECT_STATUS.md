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

## Architecture note (D-15, 2026-07-05)
Medallion is **4-layer: Landing → Bronze → Silver → Gold** (not 3). Landing = transient messy
arrival zone; Bronze = permanent trusted raw archive; promotion Landing→Bronze judges
TRANSPORT INTEGRITY only, Bronze→Silver judges CONTENT. Full rationale + interview defense in
`01_OPUS_DECISIONS.md` D-15. All docs/diagram/prompts updated to match.

## Security note (D-16, 2026-07-05)
Banking is a real-PII domain (birth_number, account/card numbers) + owner targets bank roles
(RBC) → security is a top interview differentiator. Deepened by filling the ALREADY-MANDATORY
`journey/09` richly from new `06_SECURITY_MODEL.md` (secrets, data classification, UC RBAC
matrix, service identities, audit/lineage, PII, compliance/erasure, threat model). **No 9-file
`security/` folder** — that was rejected by kit ADR-001 rej-alt #2 + CIL ADR-014; content lives
in journey/09. New risks R-31…R-35 (RBAC, service identity, audit, erasure, secrets). Aligned
with kit ADR-001, CIL ADR-014, D-01 Add #3 (UC=RBAC/audit), D-05/D-07/D-15, secrets_scan gate.

## Status log
- 2026-07-05 — Fasa-0 planning complete (this folder created). Origin: owner's Gemini
  brainstorm 2026-07-04; Opus verified/corrected it (GA4 "live" claim false; Berka added as
  the CRM seed; crosswalk identified as keystone). Datasets: home-credit→Postgres,
  paysim→MSSQL, Berka→SAP-sim file drop, OBP sandbox API, BNM OpenAPI optional.
