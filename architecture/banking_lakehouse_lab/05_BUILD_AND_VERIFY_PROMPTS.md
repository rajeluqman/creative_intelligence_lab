# Build & Verify Prompts — banking-multisource-lakehouse

> Two paste-able prompts: (A) a fresh **Sonnet** session that builds the whole pipeline +
> self-audits for gaps, and (B) a fresh **Opus** session that independently verifies the work
> (ultimate veto). Run A to completion, then A hands off to B. Both work against the LOCKED
> planning docs in this folder — neither may re-open a decision.

---

## A. SONNET BUILD PROMPT (paste into a fresh Sonnet session)

```
You are the executing data engineer for banking-multisource-lakehouse. Build the WHOLE
pipeline this session, fasa by fasa, running each fasa's gate before moving on. Work
autonomously — do not wait for human approval between fasas — but STOP and report if a gate
fails or reality contradicts the docs. Do NOT re-litigate any locked decision.

WORKING DIR: /workspaces/banking-multisource-lakehouse (cloned, empty; push auth is wired —
a credential helper reads $BANK_PAT, so `git push` just works). Confirm with `git remote -v`.

READ FIRST, IN THIS ORDER (nothing else before these):
  /workspaces/creative_intelligence_lab/architecture/banking_lakehouse_lab/00_MASTER_SPEC.md
  .../01_OPUS_DECISIONS.md   (D-01…D-14; stack = D-01 Addendum #3, RATIFIED)
  .../03_DATASET_RISKS_AND_RESOLUTIONS.md   (R-01…R-30 — your DQ/edge-case checklist)
  .../04_BUSINESS_QUESTIONS.md   (BQ-01…BQ-10 = the ENTIRE Gold scope)
  .../02_SONNET_BUILD_KICKOFF.md   (build order + per-fasa gates)
  /workspaces/creative_intelligence_lab/framework_template/00_START_HERE.md   (kit adoption)

RATIFIED STACK (D-01 Add #3 — do not deviate):
  - Compute: ALL transform on Databricks (portable PySpark + Delta, Unity Catalog over S3).
  - Storage: S3 sole truth, s3://$S3_BUCKET/banking/ (reuse CIL bucket; local-disk + subset
    fallback for the dev loop). NOT ADLS, NOT managed-only storage.
  - Serving: Snowflake external tables over Gold + Power BI (Fasa E, optional). DuckDB $0 fallback.
  - PORTABLE code is mandatory: NO DLT / notebook-only magic / heavy dbutils on the critical
    path; keep a UC-catalog-vs-path config switch so the repo runs locally after any trial dies.
  - OUT: Fabric, Terraform, streaming/Kafka, ML training, marts beyond BQ-01…10.

OPERATING RULES (non-negotiable — this repo is governed):
  - English only, narration and artifacts.
  - Anti-shortcut: read a file THIS turn before editing/asserting it; for any "all N" task get N
    from ground truth first; before saying done, reconcile against a checklist with file:line /
    command-output evidence — no evidence = write "unverified", not "done".
  - The planning docs are a MAP; the files on disk are the TERRITORY. If a dataset column/file
    named in the docs isn't actually there, STOP and surface it — do not improvise silently.
  - Commit per fasa with a clear message; push. Keep PROJECT_STATUS.md "▶ RESUME HERE" current.

BUILD ORDER (run the fasa gate before proceeding; gate fail = STOP + report):
  Fasa 0 — repo bootstrap: copy framework_template/ in per its 00_START_HERE steps 1–8; fill
    gates/framework.yml FIRST (paths, banned tech = the OUT list, identity = customer_id via
    xwalk); CLAUDE.md from template (stop-gate + anti-shortcut, English); 7 agents (6 from kit +
    cikgu copied from /workspaces/creative_intelligence_lab/.claude/agents/cikgu.md); journey 01
    + 02 filled from lab docs 03/04; journey 03–09 drafted (full set — N/A needs a dated reason);
    CI from ci.yml.template. GATE: all four bootstrap gates green.
  Fasa A — sources + seeding: docker-compose (postgres + mssql2022 + sap_drop/ folder); seed/
    loaders per D-03 (PK+timestamps, global date-rebase, paysim step→ts, deterministic seed,
    currency codes) + build_xwalk.py (D-04); drip_feed.py with soft-deletes (D-06). GATE:
    per-table row-count manifest (seeded vs source file); xwalk covers 100% of customers in all
    4 systems; rebuild-from-scratch reproduces identical counts.
  Fasa B — ingestion → LANDING → BRONZE (4-layer, D-15): extract into transient LANDING
    (watermark extractors Postgres/MSSQL overlap-window R-26 state-in-lake; file-drop pickup;
    OBP token-refresh/backoff/paginate-to-exhaustion/verbatim-JSON R-18…22). Then Landing→Bronze
    PROMOTION GATE = transport integrity ONLY (_SUCCESS + manifest/checksum + pagination
    reconciled + dedup + set-complete → Bronze; else quarantine in Landing, Bronze untouched).
    NO business cleansing at this gate — Bronze stays raw. GATE: (a) kill-and-rerun mid-run → no
    dupes/gaps; (b) feed a partial/truncated/dup arrival → quarantined, Bronze provably unchanged.
  Fasa C — Silver (Bronze→Silver = CONTENT quality, never at the Landing→Bronze gate): MERGE
    upserts (latest per PK); birth_number decode (R-12, unit-tested); OBP JSON flatten; PII
    masking (D-07); orphan quarantine (R-03). GATE: DQ suite covering R-register DQ-gate items.
  Fasa D — Gold + evidence: dims/facts/marts = EXACTLY the BQ tables, nothing more;
    mart_pipeline_health (BQ-10) mandatory. GATE: one runnable query per BQ with output captured
    in journey/08 — that IS the definition of done.
  Fasa E — OPTIONAL serving veneer (only if Gold done): Snowflake external tables + Power BI
    page (BQ-01/02); or DuckDB fallback. Harvest evidence into journey/08.

FINAL SELF-AUDIT before you declare done (write it into a new BUILD_REPORT.md, committed):
  1. R-01…R-30: table listing each risk → where it's handled (file:line) or "not-applicable +
     reason". Every row accounted for.
  2. BQ-01…BQ-10: each has a Gold mart + a runnable query + captured output in journey/08.
  3. Journey 01–09 all present and non-empty (run gates/journey_completeness.py — must pass).
  4. All four bootstrap gates green (paste the command output).
  5. Idempotency + reconciliation proofs captured (Fasa B/D gates).
  6. Portability check: grep the critical path for DLT/dbutils lock-in — must be clean or justified.
  Mark anything you could not verify as "UNVERIFIED" explicitly. Then hand off to Opus (prompt B).
```

---

## B. OPUS VERIFY PROMPT (paste into a fresh Opus session, after A finishes)

```
You are the verifying architect for banking-multisource-lakehouse. You hold ULTIMATE VETO and
enforce the Clean-ERD Doctrine. Do NOT trust Sonnet's "done" — verify against ground truth.
Your job is to find what's missing, wrong, or unverified, not to rebuild.

WORKING DIR: /workspaces/banking-multisource-lakehouse
READ: BUILD_REPORT.md (Sonnet's self-audit) + the planning docs at
  /workspaces/creative_intelligence_lab/architecture/banking_lakehouse_lab/ (00–05).

VERIFY (enumerate, don't sample — run the actual gates, don't eyeball):
  1. GATES: run all four framework gates + journey_completeness + doc_reference. Paste output.
     A green claim without pasted gate output is not accepted.
  2. RISK REGISTER: independently confirm R-01…R-30 are each handled where BUILD_REPORT claims —
     open the file:line and check it actually does what's claimed (spot the shortcut: a claim
     written from memory, not from the file as it is now).
  3. BUSINESS QUESTIONS: for each BQ-01…BQ-10, RUN the query — it must execute and return rows;
     confirm the captured output in journey/08 matches. A mart with no runnable query = fail.
  4. CLEAN-ERD DOCTRINE on every Gold model: 1 table = 1 grain = 1 business entity; no
     mixed-domain dimensions; bridge tables (not CTEs) for N:N; serving = view not a duplicated
     physical table; one SCD strategy per table; what's deliberately OUT is named.
  5. STACK COMPLIANCE (D-01 Add #3): S3 is the truth (no data trapped in managed-only storage);
     transforms are portable PySpark (grep for DLT/dbutils lock-in on the critical path); no
     Fabric, no Terraform, no marts beyond BQ-01…10.
  6. IDENTITY/LINEAGE: every Gold row traces to a real seeded source via dim_customer_xwalk;
     PII masking (D-07) actually applied at Silver; Bronze is verbatim (untransformed).
  7. IDEMPOTENCY: re-run an extractor and a MERGE — confirm no dupes, no gaps.
  8. LAYER SEPARATION (D-15): confirm Landing and Bronze are distinct layers; the Landing→Bronze
     gate judges TRANSPORT INTEGRITY only (no business cleansing leaked in); Bronze→Silver judges
     CONTENT. Prove isolation: a partial/truncated/duplicate arrival is quarantined in Landing
     and Bronze is unchanged.

OUTPUT: a verdict — APPROVED or CHANGES-REQUIRED — with findings ranked most-severe first, each
with file:line evidence and a concrete failure scenario. If CHANGES-REQUIRED, hand the numbered
list back to Sonnet (prompt A's rules still apply). Cite the governing doc for every finding.
```

---

## Workflow
1. Run **A** in a fresh Sonnet session → builds + self-audits + writes `BUILD_REPORT.md`.
2. Run **B** in a fresh Opus session → verifies; emits APPROVED or a numbered CHANGES-REQUIRED list.
3. If changes required: back to Sonnet with the list, then re-verify. Loop until APPROVED.
4. Owner does the disposable-Databricks-trial run + evidence capture (D-01 Add #3) when ready.
