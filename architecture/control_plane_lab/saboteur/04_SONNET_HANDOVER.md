# Sonnet Handover — security layer + saboteur wiring (Fable-settled, 2026-07-04)

> ONE build session, all units together (owner instruction — they touch the same files).
> Design is SETTLED; do not re-litigate. If a spec detail is genuinely missing, log an
> Unresolved Question in the relevant PROJECT_STATUS and continue with other units — do not
> assume (ADR-000 spirit). Verify every "done" with the named gate, not a parse-clean.

## U1 — CIL security layer (owner override: simulate-real-work ⇒ RBAC is IN)
1. **ADR-014 — Security & Access Model (simulation-grade).** Content per the Fable brief
   (2026-07-04 session): RBAC role matrix (real GRANTs, not prose), data classification
   (inventory: `account_support_owner` email in dim_client; talent face/voice in footage),
   audit = platform-native enablement (S3 access logs + Snowflake ACCOUNT_USAGE — custom
   audit build REJECTED), PDPA talent-consent named-not-built. Cite the owner override
   precedent (ADR-005 pattern) + ChatGPT-scorecard verification from the session.
2. **`CREATIVE_INTEL_ANALYST_RO` role** in `scripts/provision_snowflake_serving.py`:
   Gold-serving SELECT only (incl. FUTURE TABLES grant — see T-SRV-04), no Bronze/Silver
   stage access, no warehouse OPERATE. ⚠️ Governed file — Fable already designed this change
   (this handover IS the architecture sign-off); implement exactly, run existing gates.
3. **2 security drills** in `simulation/drills/`: T-SEC-01 (credential leak incident,
   full 8-phase runbook) + T-SRV-04/RBAC misconfig (analyst can't see / can see too much).
   Use CARD_FORMAT; saboteur reveals Scenario+Symptom only.
4. BACKLOG.md: record REJECTED items (9-file security folder, threat_model/incident_response
   as standalone docs, custom audit) with date + reason.

## U2 — framework_template security upgrade (kit v1.1.0)
1. `journey/09_SECURITY_AND_ACCESS.md` — **mandatory 9th journey doc** (owner ruling), with
   UNFILLED sentinel line like the other 8. Sections: secrets management · data classification
   · **RBAC role matrix (role × layer × permission — required table)** · service identities ·
   audit/log enablement · PII handling · compliance flags (GDPR/PDPA/CCPA as N/A-able rows) ·
   incident contacts. Every section individually N/A-able with reason.
2. `gates/secrets_scan.py` — config-driven via `framework.yml` (add `secrets_scan:` section:
   extra_patterns, allowlist_paths). Detect: `password/api_key/secret/token = "literal"`,
   AWS `AKIA[0-9A-Z]{16}`, private-key headers, connection strings with embedded passwords.
   Scan tracked text files; skip `.env.example`, docs code-fences flagged as examples via
   allowlist. Stdlib only. MUST have a self-test mode like the other gates were dry-run
   validated (plant a fake key in a temp copy → expect exit 1).
3. `framework.yml`: `journey.required_docs` +09; `ci.yml.template`: add secrets_scan step.
4. Kit `governance/ADR/ADR-001-security-layer-mandatory.md` recording this decision (the
   kit's own first numbered ADR — ADR-000 is the intake protocol).
5. `CHANGELOG.md` v1.1.0 entry. Update `00_START_HERE.md` step 3 (8→9 docs).
6. Re-run the full dry-run validation loop from v1.0.0 (copy to scratch, unfilled→fail,
   fill→pass, planted secret→fail). The two v1.0.0 bug classes (hollow gate, self-matching
   regex) were found ONLY by dry-run — do not skip it.

## U3 — Saboteur problem bank wiring
1. Bank lives here (`PROBLEM_BANK_TROUBLESHOOT.md` 100 · `PROBLEM_BANK_OPTIMIZATION.md` 100 ·
   `INCIDENT_RUNBOOK.md` · `README.md`) — verified counts, no dup IDs. Do NOT renumber.
2. CIL `simulation/faults/catalog`: map which T-IDs are injectable in CIL today (tags DDB/DBT/
   S3/AF/SF/GE/LLM per README tag map) — a mapping file, not 100 inject scripts. Write
   inject/reset for the 2 U1 drills only; further drills author faults on demand.
3. Control-plane repo port note: when `airflow_dag_running_pipeline` Fasa-1 builds, this
   folder moves there wholesale; `saboteur_containment_contract.py` (per 01_OPUS_DECISIONS)
   must treat the bank as read-only input — @saboteur picks from it, never edits answer keys
   mid-drill.
4. `simulation/LADDERS.md`: add pointer — ladder levels now draw from the bank by Lvl column
   (L1→L2→L3), same scoring as existing T-L01/O-O01 convention.

## U4 — Close-out (all units)
- Run: all CIL contracts + `gen_repo_map.py --check` (regenerate if the new files shift it) +
  kit dry-run + `python tests/doc_reference_contract.py` on any doc you touched in
  `architecture/` top-level.
- Update CIL `PROJECT_STATUS.md` ▶ RESUME HERE + this folder's PROJECT_STATUS.
- Reconcile-before-done: numbered checklist U1.1–U4, each with command output or file:line.
