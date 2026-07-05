# Pipeline Retrofit — PROJECT STATUS (resume-safe checkpoint)

> Token-safe checkpoint for the 4-repo porting effort. If context runs out, a fresh session reads
> the ▶ RESUME HERE block below FIRST (not the whole folder). Per ADR-012 session discipline.
> Branch: `framework/pipeline-retrofit-plan`. Plan docs in this same folder (00/01/02).

## ▶ RESUME HERE (read this first)
**ALL 4 REPOS PUSHED + PRs OPEN (2026-06-29):** owner supplied a PAT (classic `repo` scope,
Codespace secret `GH_PUSH_TOKEN`, repo-scoped to CIL). Pushed all 4 `framework/governance-retrofit`
branches via `git push https://rajeluqman:${GH_PUSH_TOKEN}@github.com/rajeluqman/<repo>.git
framework/governance-retrofit:framework/governance-retrofit`, then `gh pr create` per repo
(base=main, head=framework/governance-retrofit) with `GH_TOKEN` set per-command (NOT
`gh auth login --with-token`, which would have persisted the PAT into the global `gh` credential
store beyond this task's scope). PRs:
- home-credit-pipeline: https://github.com/rajeluqman/home-credit-pipeline/pull/1
- olist-ecommerce-pipeline: https://github.com/rajeluqman/olist-ecommerce-pipeline/pull/1
- paysim-fraud-pipeline: https://github.com/rajeluqman/paysim-fraud-pipeline/pull/1
- Volve-Sensor-Production-Analytics-Pipeline: https://github.com/rajeluqman/Volve-Sensor-Production-Analytics-Pipeline/pull/3

Note: the home-credit push used `-u` (set-upstream), which embedded the PAT into the local
branch's tracking URL in `.git/config` (a credential-on-disk risk) — caught and cleaned up
immediately (`git config --unset branch.framework/governance-retrofit.{remote,merge}`); the
remaining 3 pushes omitted `-u` to avoid the same issue. The PAT itself lives only in the
Codespace secret `GH_PUSH_TOKEN`, never written to any file in this repo or memory.

**Week-1-readability doc pass + push attempt (2026-06-29, Opus session):**
- **Doc gap closed on all 4 repos** (owner-approved: all-4 scope, evidence DEFERRED, no fabricated
  metrics). Each README now has **Purpose / Business-Questions / Results&Evidence** sections;
  each `confluence/00_START_HERE.md` answers "why it exists / what it answers / what's proven vs
  not" up front (home-credit's landing page was created + registered in its sync PUBLISH_SET +
  README added to the set). New commits: home-credit `bdc8966`, olist `e3a48cb`, paysim `7c60ccb`,
  Volve `b6c99eb`. All re-archived in `repo_archives/`.
- **Gates:** the CI-run doc-ref check (`docs/` default) + boundary contract are GREEN on all 4.
  README-scoped doc-ref is green on home-credit/paysim/Volve. paysim needed 2 reasoned ALLOW
  entries (`fact_transactions`/`fact_customer_daily_balance` are real Silver Delta tables, not dbt
  models — the C1 check over-matches). **olist has 1 PRE-EXISTING README drift** (line ~151: a
  screenshot link is `%20`-encoded but the file on disk has a literal space; the C2 check doesn't
  decode `%20`). NOT introduced by this pass, NOT gating CI (CI scans `docs/`, not README).
  ⏳ **Open decision for owner:** fix olist by renaming the spaced screenshot files (best practice)
  or teach the contract to `unquote()` `%20` — left untouched pending owner call.
- **PUSH STILL BLOCKED — real cause now confirmed:** the codespace's auto `GITHUB_TOKEN` (`ghu_…`)
  only has WRITE to `creative_intelligence_lab` (its parent repo). Push to all 4 external repos
  returns **403** ("denied to rajeluqman"); read (`ls-remote`) works because they're public.
  `gh api …/permissions` showing `push:true` is the *account* capability, NOT the token's scope —
  do not be misled by it. **To push: owner must supply a PAT** (classic `repo` scope, or
  fine-grained Contents:write+PR:write on the 4 repos), then `git push -u origin
  framework/governance-retrofit` + `gh pr create` per repo. Original "owner cannot push" KIV was
  correct for writes.

**Where we are: ALL 4 REPOS DONE.** home-credit-pipeline, olist-ecommerce-pipeline,
paysim-fraud-pipeline, AND Volve-Sensor-Production-Analytics-Pipeline are all DONE on their own
local `framework/governance-retrofit` branches (home-credit commit `bef4714`, olist commit
`f17e225`, paysim commit `6a8aa10`, **Volve commit `08a12dc`**) — see checklists below, all four
independently re-verified (contracts run directly, not just trusting the build report). All 4
are now ALSO pushed with PRs open (see ▶ RESUME HERE above) — the porting effort + push/PR step
are both fully closed.
**Volve build (2026-06-29):** built directly in the main session per owner instruction (no
nested sub-agent delegation). Ground-truth read found Volve has the worst doc accuracy of the
4 repos — `docs/BRD.md`/`DRD.md`/`DQD.md`/`PIPELINE_SPEC.md` are stale v1.0, describing an
abandoned NiFi+AWS Glue+Great Expectations design; `ingestion/nifi/` and `bronze/glue_jobs/`
are orphaned `HOW_IT_WORKS.txt`-only stubs (never built); `tests/` and `data_quality/` contain
zero real code despite README claiming Phase 7 "Done" and a resume bullet claiming "84 tests,
0 failures". Per owner instruction (asked via AskUserQuestion before touching anything): **all
flagged, nothing deleted** — documented in `CLAUDE.md`/`INTERVIEW_GUIDE.md`/`DECISION_LOG.md`;
README Phase 7 corrected to describe the real inline-SQL DQ gate; building the missing
tests/GE suites explicitly **deferred** to a future session, not done in this retrofit pass.
7 ADRs migrated verbatim from real inline rationale already in `docs/ARCHITECTURE.md` §6 (NOT
reconstructed — corrects `01_OPUS_DECISIONS.md`'s "Volve = 0 ADRs" finding, which apparently
missed ADRs embedded in a non-`docs/ADR/` file); ADR-008 (identity grain) new from direct code
read; ADR-009 (ML model selection) new, tagged "(reconstructed — owner confirm)" per the
no-fabrication rule. `docs/DATA_MODEL.md` + `docs/DATA_DICTIONARY.md` written from scratch
(previously missing entirely). All 3 contracts + repo-map `--check` + sim isolation green,
verified directly (not just trusting the build).
**Owner-driven ground-truth audit (2026-06-29, ahead of a planned Microsoft Fabric
migration):** owner asked to re-check all 3 then-finished repos for doc/code accuracy before
porting — found and fixed 4 more real issues beyond the original retrofit pass (see each
repo's PROJECT_STATUS.md "Doc gap(s) found" for detail): paysim's dead ADLS upload code
(removed) + README Silver overstatement (corrected); olist's same Silver-overstatement bug
(corrected) + an undocumented Airflow stub-task gap (documented); home-credit's orphaned
broken scaffold DAG `pipeline_dag.py` (removed, **owner approved the deletion explicitly**
after being shown the evidence — do not unilaterally delete files without the same
present-evidence-then-ask pattern; applied again for Volve's stub dirs, where the owner chose
"flag, don't delete" instead).
**The true goal (owner, 2026-06-28):** turn each of the 4 external repos into a **self-teaching lab
like CIL** — rebuild-from-scratch with @cikgu + optimize/troubleshoot/simulation drills on isolated
branches so `main` stays clean → owner becomes able to **defend every resume claim**. All 4 now
have `learning/CURRICULUM.md` + `LEARNING_LOG.md` + `simulation/` labs.
**Stack preservation is paramount (owner, 2026-06-29):** the 4 repos have 4 DIFFERENT real,
historically-locked stacks (home-credit=S3/Glue, olist=ADLS/Databricks, paysim=S3/PySpark+
optional-Databricks-compute, Volve=Databricks SQL Warehouse-native, no dbt) — never homogenize
storage across repos. Removing genuinely dead/unreachable code within ONE repo (confirmed
unused, confirmed broken) is fine; swapping a repo's real, working storage/compute choice to
match another repo is NOT — that would be the actual "tukar stack suka hati" the owner pushed
back on.
**Push deferred (owner decision 2026-06-28, reconfirmed 2026-06-29) — RESOLVED 2026-06-29:**
owner supplied PAT `GH_PUSH_TOKEN`; all 4 repos' push+PR step is now done (see ▶ RESUME HERE).
**Archived 2026-06-29 (owner request — `/workspaces/*-porting` clones are ephemeral and have
already been lost once before):** all 4 repos backed up as full-history `.tar.gz` (the actual
clone incl. `.git`, not a file snapshot) in
`architecture/pipeline_retrofit/repo_archives/` — see that folder's `README.md` for the
restore+push steps and the commit/branch table. This is CIL's own durable, pushed location;
if `/workspaces/*-porting` disappears again before Opus's push pass, extract from here instead
of re-running the retrofit.

## The 4 repos + their stacks (preserve as-is)
| Repo | Stack (untouched) | Existing Slack | Existing ADRs |
|---|---|---|---|
| home-credit-pipeline | AWS S3 + Glue PySpark + dbt/Snowflake + Airflow + GH Actions | ✅ keep | 1 |
| olist-ecommerce-pipeline | ADLS Gen2 + Databricks + dbt/Snowflake + Airflow + Power BI | ❌ backfill | 2 |
| paysim-fraud-pipeline | S3 + Databricks SQL + dbt/Snowflake + Airflow | ✅ keep | 1 |
| Volve-...-Pipeline | Databricks + Delta + MLflow + Snowflake + Airflow | ❌ backfill | 0 ← worst |

## Per-repo build checklist (tick as done; evidence = file:line, not "done")
Legend: ⬜ todo · 🟡 in progress · ✅ done+verified

### home-credit-pipeline (TEMPLATE — do first) — ✅ built, ✅ pushed
Evidence: `/workspaces/home-credit-pipeline-porting` branch `framework/governance-retrofit`,
commit 57bdfd5. Verified by reading the branch tree directly 2026-06-28.
- ✅ CLAUDE.md (real Glue/Snowflake stack, governed-file map)
- ✅ .claude/agents/ ×11 (business-analyst, cikgu, data-architect, data-platform-engineer,
  data-quality-steward, documentation-sherpa, finops-agent, infra-reality-agent, product-owner,
  scope-guardian, senior-data-engineer)
- ✅ .claude/hooks/ present (governance_guard.py — not individually re-verified line-by-line)
- ✅ tests/: boundary_contract.py + doc_reference_contract.py + identity_contract.py + unit/
- ✅ scripts/ + architecture/ dirs present (repo-map not individually re-verified)
- ✅ ADRs: docs/ADR/ADR-001-kimball-star-schema.md, ADR-002-pii-mask-order.md,
  ADR-003-kimball-over-obt-sizing.md
- ✅ Confluence sync: scripts/sync_docs_to_confluence.py present
- ✅ Logs: PROJECT_STATUS.md, COST_LOG.md, DECISION_LOG.md, INFRA_LIMITS_LOG.md (root)
- ✅ learning/ dir present
- ✅ simulation/ dir present
- ✅ INTERVIEW_GUIDE.md present
- ✅ .github/workflows/ci.yml — confirmed wires ruff/pytest + the 3 contracts (CI has no AWS
  OIDC role yet, so it's static-gates-only — named gap, not silently skipped)
- ✅ **push feature branch + PR — DONE 2026-06-29.** PR:
  https://github.com/rajeluqman/home-credit-pipeline/pull/1

### olist-ecommerce-pipeline — ✅ built, ✅ pushed
Evidence: `/workspaces/olist-ecommerce-pipeline-porting` branch `framework/governance-retrofit`,
commit `c632fce`. Verified directly 2026-06-29 — ran all 4 contracts myself (not just trusting
the build report): `tests/identity_contract.py`, `tests/boundary_contract.py`,
`tests/doc_reference_contract.py`, `simulation/check_isolation.py` — all exit 0, all ✅.
- ✅ CLAUDE.md (real ADLS Gen2/Databricks/dbt-Snowflake/Airflow/Power BI stack, governed-file map)
- ✅ .claude/agents/ ×9 (data-architect, scope-guardian, senior-data-engineer,
  data-quality-steward, product-owner, business-analyst, data-platform-engineer,
  documentation-sherpa, cikgu) + .claude/hooks/governance_guard.py + .claude/settings.json
- ✅ tests/: boundary_contract.py + doc_reference_contract.py + identity_contract.py — all pass
- ✅ scripts/gen_repo_map.py run for real → architecture/REPO_MAP.md (108 files mapped)
- ✅ ADRs: docs/ADR/ADR-002-scd-strategy.md, ADR-003-slack-alerting.md (ADR-001 pre-existing,
  kept) — rationale evident from code, no "(reconstructed)" tag needed
- ✅ Slack backfill: airflow/dags/olist_pipeline_dag.py `_notify_slack_failure`, graceful
  no-op if SLACK_WEBHOOK_URL unset
- ✅ Confluence: scripts/sync_docs_to_confluence.py + confluence/00_START_HERE.md
- ✅ Logs: PROJECT_STATUS.md, COST_LOG.md, DECISION_LOG.md (root)
- ✅ INTERVIEW_GUIDE.md — Resume↔Evidence table, ADF claim flagged unsupported (repo uses
  Databricks COPY INTO + Kaggle CLI, confirmed 0 hits on "data factory|adf" grep)
- ✅ learning/CURRICULUM.md + LEARNING_LOG.md; simulation/ (ISOLATION_CONTRACT.md,
  check_isolation.py, faults/, 4 drill specs) — isolation contract passes
- ✅ .github/workflows/ci.yml — created fresh (olist had none), wires the 3 contracts +
  repo-map --check + isolation check
- ✅ **push feature branch + PR — DONE 2026-06-29.** PR:
  https://github.com/rajeluqman/olist-ecommerce-pipeline/pull/1

### paysim-fraud-pipeline — ✅ built, ✅ pushed
Evidence: `/workspaces/paysim-fraud-pipeline-porting` branch `framework/governance-retrofit`,
commit `c5724c6`. Verified directly 2026-06-29 — ran all 5 gates myself (not just trusting the
build report): `tests/identity_contract.py`, `tests/boundary_contract.py`,
`tests/doc_reference_contract.py`, `simulation/check_isolation.py`,
`scripts/gen_repo_map.py --check` — all exit 0, all ✅.
- ✅ CLAUDE.md (real PySpark/Delta Lake on S3 + Snowflake/dbt hybrid-grain stack, governed-file map)
- ✅ .claude/agents/ ×10 (data-architect, scope-guardian, senior-data-engineer,
  data-quality-steward, product-owner, business-analyst, data-platform-engineer,
  documentation-sherpa, finops-agent, cikgu) + .claude/hooks/governance_guard.py + .claude/settings.json
- ✅ tests/: boundary_contract.py + doc_reference_contract.py + identity_contract.py — all pass.
  Identity contract rebuilt around the DUAL grain (Kimball `fact_transactions` +
  cumulative-table `fact_customer_daily_balance`, idempotent Delta MERGE in
  `silver/cumulative_pipeline.py`), not a single SCD2 surrogate key like home-credit/olist.
- ✅ scripts/gen_repo_map.py run for real → architecture/REPO_MAP.md (80 files mapped)
- ✅ ADR-002 Silver GX WARN: traced README's unattributed "Silver 14/15 (1 WARN)" to the
  `merchant_balance_null` check (matches `docs/DQD.md`'s documented "Merchant balance = 0 → by
  design" anomaly) — formally ACCEPTED with written rationale, not fixed (ADR-001 pre-existing,
  kept)
- ✅ Slack: KEPT AS-IS (already working `slack_success`/`slack_failure` via
  `SlackWebhookOperator` in `airflow/dags/paysim_fraud_pipeline.py`) — no backfill needed
- ✅ Confluence: scripts/sync_docs_to_confluence.py + confluence/00_START_HERE.md
- ✅ Logs: PROJECT_STATUS.md, COST_LOG.md, DECISION_LOG.md (root)
- ✅ INTERVIEW_GUIDE.md — Resume↔Evidence table; Silver-WARN attribution; the
  `bronze/download_dataset.py` dead-code Azure ADLS upload path and the README Silver
  overstatement (below) are now RESOLVED, not just flagged (owner asked to solve both
  2026-06-29, same session)
- ✅ learning/CURRICULUM.md + LEARNING_LOG.md (M4 = cumulative-MERGE idempotency, the
  resume-proof centerpiece unique to this repo); simulation/ (ISOLATION_CONTRACT.md,
  check_isolation.py, faults/, 3 drill specs) — isolation contract passes
- ✅ .github/workflows/ci.yml — created fresh (paysim had none), wires the 3 contracts +
  repo-map --check + isolation check
- ✅ .gitignore — repo had a pre-existing "JANGAN COMMIT" rule excluding CLAUDE.md/.claude/
  PROJECT_STATUS.md/COST_LOG.md (same pattern home-credit/olist also had and overrode);
  amended with an explicit "now INTENTIONALLY committed" note, matching the other 2 repos'
  precedent — all retrofit artifacts are tracked in the commit, not silently gitignored
- ✅ **Both real findings RESOLVED (owner request, 2026-06-29, follow-up turn):**
  (1) `bronze/download_dataset.py`'s dead-code `upload_to_adls()` Azure path + the
  `CLOUD`/`elif cloud == "azure"` branching in `main()` — REMOVED (locked stack is S3-only;
  `tests/boundary_contract.py`'s `ALLOW_LINES` exception emptied, mechanism kept for future
  use). (2) `README.md`'s Stack table + architecture diagram overstated Silver as "Databricks
  SQL Warehouse — SQL CTAS + window functions" — CORRECTED to PySpark+Delta Lake (local or
  Databricks), matching `docs/ARCHITECTURE.md` (which already had this right) and
  `silver/silver_pipeline.py`/`cumulative_pipeline.py` ground truth. All 5 gates re-run green
  after both fixes (`identity_contract.py`, `boundary_contract.py`, `doc_reference_contract.py`,
  `check_isolation.py`, `gen_repo_map.py --check`).
- ✅ **push feature branch + PR — DONE 2026-06-29.** PR:
  https://github.com/rajeluqman/paysim-fraud-pipeline/pull/1

### Volve-Sensor-Production-Analytics-Pipeline (most work — LAST) — ✅ built, ✅ pushed
Evidence: `/workspaces/Volve-Sensor-Production-Analytics-Pipeline-porting` branch
`framework/governance-retrofit`, commit `08a12dc`. Verified directly 2026-06-29 — ran all 3
contracts + repo-map `--check` + sim isolation myself: `tests/identity_contract.py`,
`tests/boundary_contract.py`, `tests/doc_reference_contract.py`,
`scripts/gen_repo_map.py --check`, `simulation/check_isolation.py` — all exit 0, all ✅.
- ✅ CLAUDE.md (real Databricks SQL Warehouse-only stack, no dbt, stop-gate, doc-staleness flags)
- ✅ .claude/agents/ ×11 (data-architect, scope-guardian, senior-data-engineer,
  data-quality-steward, product-owner, business-analyst, data-platform-engineer,
  documentation-sherpa, finops-agent, infra-reality-agent, cikgu) + governance_guard.py hook
- ✅ tests/: boundary_contract.py + doc_reference_contract.py + identity_contract.py — all
  pass; no dbt-model check (this repo has none, ADR-008) — boundary contract also asserts no
  dbt project file appears anywhere
- ✅ scripts/gen_repo_map.py run for real → architecture/REPO_MAP.md (81 files mapped)
- ✅ docs/ADR/: ADR-001 through ADR-007 migrated VERBATIM from real inline rationale already
  in docs/ARCHITECTURE.md §6 (NOT reconstructed — corrects the original "Volve = 0 ADRs"
  finding, which missed ADRs embedded outside docs/ADR/); ADR-008 (identity grain) new, from
  direct code read; ADR-009 (ML model selection) new, tagged "(reconstructed — owner confirm)"
- ✅ docs/DATA_MODEL.md + docs/DATA_DICTIONARY.md — written from scratch (previously missing
  entirely, confirmed by directly reading gold/gold_production_daily.py for exact column names)
- ✅ identity contract = (well_id, DATEPRD) production grain + (well_id, md_m) trajectory
  grain; NO dbt (Gold = hand-written Databricks SQL .py scripts); INFRA_LIMITS_LOG.md (3/29
  well free-tier cap, 8GB Codespaces RAM ceiling)
- ✅ Slack: BACKFILLED `_notify_slack_failure` in airflow/dags/volve_daily_pipeline.py
  (`on_failure_callback`), ported from CIL's pattern — repo had none before
- ✅ Confluence: scripts/sync_docs_to_confluence.py + confluence/00_START_HERE.md
- ✅ Logs: PROJECT_STATUS.md, COST_LOG.md, DECISION_LOG.md, INFRA_LIMITS_LOG.md (root)
- ✅ **Real, large doc/code mismatch found and handled (owner sign-off via AskUserQuestion
  BEFORE touching anything, 2026-06-29):** `ingestion/nifi/` and `bronze/glue_jobs/` are
  `HOW_IT_WORKS.txt`-only stubs from an abandoned NiFi+Glue design (per ADR-001's own
  documented pivot) referencing scripts that were never built — owner chose **flag, don't
  delete**. `tests/` and `data_quality/` ALSO contain zero real code (just stub
  `HOW_IT_WORKS.txt`) despite README claiming Phase 7 "Data Quality (Great Expectations) —
  Done" and a resume bullet claiming "84 tests, 0 failures" — owner chose **document + correct
  the false claims now, defer building the actual missing tests/GE suites to later** (not
  pipeline-build scope for this retrofit). All of this is flagged in CLAUDE.md/
  INTERVIEW_GUIDE.md/DECISION_LOG.md; README Phase 7 row corrected in place.
- ✅ INTERVIEW_GUIDE.md — Resume↔Evidence table; "84 tests, 0 failures" and the GE-suite Phase
  7 claim both flagged ❌ unsupported with the reasoning above
- ✅ learning/CURRICULUM.md (12 modules; M0/M8/M11 uniquely teach the doc-honesty gap itself
  as a lesson) + LEARNING_LOG.md; simulation/ (ISOLATION_CONTRACT.md retargeted to Unity
  Catalog `claudecatalog`/Snowflake `VOLVE_DB` namespace checks — no dbt-project-name check,
  this repo has none — check_isolation.py, faults/, 4 drill specs) — isolation contract passes
- ✅ .github/workflows/ci.yml — created fresh (Volve had none, and `.github/` was previously
  gitignored — amended), wires the 3 contracts + repo-map --check + isolation check
- ✅ .gitignore — same "JANGAN COMMIT" pattern as the other 3 repos (excluded CLAUDE.md/
  .claude//PROJECT_STATUS.md, and uniquely also `.github/`); amended with an explicit
  "now INTENTIONALLY committed" note, all retrofit artifacts tracked in the commit
- ✅ **push feature branch + PR — DONE 2026-06-29.** PR:
  https://github.com/rajeluqman/Volve-Sensor-Production-Analytics-Pipeline/pull/3

## Known resume↔repo mismatches (must resolve during build)
- olist: resume "ADF" ✗ repo Databricks COPY INTO — ✅ resolved, flagged in INTERVIEW_GUIDE.md
- home-credit: resume "Lambda, Step Functions" ✗ repo Glue+Airflow only — ✅ resolved
- paysim: "Silver 14/15 WARN" — ✅ resolved, ADR-002 attributes it to `merchant_balance_null`
- Volve: "84 tests, 0 failures" — ✅ resolved (flagged unsupported, not fixed — `tests/` has
  zero real test files; README's Phase 7 "Great Expectations" claim also corrected to describe
  the real inline-SQL DQ gate)

## Decision log (this effort)
- 2026-06-28: Plan approved. CIL=primary ref, pharma=gap-fill. Lean 8–11 roster (Haiku tier rejected).
  Gym/learning IN scope (addendum, 01_OPUS_DECISIONS). Sequencing home-credit→olist→paysim→Volve.
  Build routed to Sonnet; Opus reviews.
- 2026-06-29: Volve (repo 4/4, last) built directly in the main session, no nested sub-agent
  delegation, per owner instruction. Largest doc/code gap of the 4 repos found and handled via
  AskUserQuestion before any change: orphaned NiFi/Glue stubs flagged-not-deleted; empty
  tests/data_quality dirs documented + false README/resume claims corrected, real test/GE-suite
  build explicitly deferred. This closes the 4-repo porting effort — only push/PR remained,
  owned by Opus across all 4 repos in one pass.
- 2026-06-29: Push+PR pass completed for all 4 repos using owner-supplied PAT (Codespace secret
  `GH_PUSH_TOKEN`). PRs: home-credit #1, olist #1, paysim #1, Volve #3 (all base=main, head=
  framework/governance-retrofit). Used `GH_TOKEN=<token> gh pr create` per-command rather than
  `gh auth login --with-token`, to avoid persisting the PAT into the global `gh` credential
  store. Caught and fixed one credential-hygiene slip: the home-credit push used `git push -u`,
  which embedded the PAT into `.git/config`'s branch-tracking URL — removed via `git config
  --unset branch.framework/governance-retrofit.{remote,merge}` immediately after. Token lives
  only in the Codespace secret, never committed or written to memory.
