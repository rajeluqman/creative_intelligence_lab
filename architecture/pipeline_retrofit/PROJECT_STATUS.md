# Pipeline Retrofit — PROJECT STATUS (resume-safe checkpoint)

> Token-safe checkpoint for the 4-repo porting effort. If context runs out, a fresh session reads
> the ▶ RESUME HERE block below FIRST (not the whole folder). Per ADR-012 session discipline.
> Branch: `framework/pipeline-retrofit-plan`. Plan docs in this same folder (00/01/02).

## ▶ RESUME HERE (read this first)
**Where we are:** Planning + decisions COMPLETE and owner-approved. NO target-repo files built yet.
**The true goal (owner, 2026-06-28):** turn each of the 4 external repos into a **self-teaching lab
like CIL** — rebuild-from-scratch with @cikgu + optimize/troubleshoot/simulation drills on isolated
branches so `main` stays clean → owner becomes able to **defend every resume claim**.
**Next action:** start the Sonnet BUILD phase on **home-credit-pipeline** (template repo). Clone it
into a working dir, follow `02_SONNET_BUILD_KICKOFF.md` + the per-repo checklist below, land on a
feature branch, push, PR. Then port the pattern to olist → paysim → Volve.
**Do NOT:** swap any repo's data stack; fabricate Volve ADRs (tag reconstructed); build on `main`.

## The 4 repos + their stacks (preserve as-is)
| Repo | Stack (untouched) | Existing Slack | Existing ADRs |
|---|---|---|---|
| home-credit-pipeline | AWS S3 + Glue PySpark + dbt/Snowflake + Airflow + GH Actions | ✅ keep | 1 |
| olist-ecommerce-pipeline | ADLS Gen2 + Databricks + dbt/Snowflake + Airflow + Power BI | ❌ backfill | 2 |
| paysim-fraud-pipeline | S3 + Databricks SQL + dbt/Snowflake + Airflow | ✅ keep | 1 |
| Volve-...-Pipeline | Databricks + Delta + MLflow + Snowflake + Airflow | ❌ backfill | 0 ← worst |

## Per-repo build checklist (tick as done; evidence = file:line, not "done")
Legend: ⬜ todo · 🟡 in progress · ✅ done+verified

### home-credit-pipeline (TEMPLATE — do first)
- ⬜ CLAUDE.md (real Glue/Snowflake stack, governed-file map)
- ⬜ .claude/agents/ ×11 (8 core + finops + infra-reality + cikgu)
- ⬜ .claude/hooks/governance_guard.py (targets: glue/glue_silver_*.py, dbt mart/, snapshots/, docs/ADR/)
- ⬜ tests: doc_reference_contract.py + boundary_contract.py + identity_contract.py (SK_ID_CURR+SCD2)
- ⬜ scripts/gen_repo_map.py + REPO_MAP.md
- ⬜ ADRs: PII-mask-order, Kimball-over-OBT sizing
- ⬜ Confluence sync (adapt CIL script + 9-page set); keep existing Slack
- ⬜ Logs: PROJECT_STATUS, COST_LOG, DECISION_LOG, INFRA_LIMITS_LOG (Glue OOM)
- ⬜ learning/CURRICULUM.md + LEARNING_LOG.md (rebuild-from-scratch path, Glue/PySpark tailored)
- ⬜ simulation/ (ISOLATION_CONTRACT R1/R2/R3 + check_isolation.py + faults/ + specs)
- ⬜ INTERVIEW_GUIDE.md + Resume↔Evidence table (reconcile: "Lambda/Step Functions", "58M rows")
- ⬜ .github/workflows/ci.yml wires the 3 contracts
- ⬜ push feature branch + PR

### olist-ecommerce-pipeline
- ⬜ same checklist; roster ×9 (no finops, no infra-reality, +cikgu)
- ⬜ identity contract = SCD2 keys; boundary = ADLS/Databricks/Snowflake
- ⬜ ADRs: SCD-strategy, Slack-alerting; Slack BACKFILL from CIL _notify_slack_failure
- ⬜ Resume↔Evidence: reconcile "Azure Data Factory (ADF)" (repo uses Databricks COPY INTO)

### paysim-fraud-pipeline
- ⬜ same checklist; roster ×10 (no infra-reality, +cikgu); keep Slack
- ⬜ identity contract = cumulative-table grain; ADR for GE 14/15 WARN (fix or accept w/ rationale)

### Volve-Sensor-Production-Analytics-Pipeline (most work — LAST)
- ⬜ same checklist; roster ×11; Slack BACKFILL
- ⬜ ADR folder FROM ZERO (storage/compute, free-tier well cap, 3 ML-model choices) — tag "(reconstructed — owner confirm)"
- ⬜ docs/DATA_MODEL.md + DATA_DICTIONARY.md (missing entirely)
- ⬜ identity contract = well_id+date grain; NO dbt (Gold = Databricks .py); INFRA_LIMITS_LOG (3/29 wells)
- ⬜ Resume↔Evidence: verify "84 tests, 0 failures"

## Known resume↔repo mismatches (must resolve during build)
- olist: resume "ADF" ✗ repo Databricks COPY INTO
- home-credit: resume "Lambda, Step Functions" ✗ repo Glue+Airflow only
- Volve: resume "84 tests" — verify
- paysim: "Silver 14/15 WARN" — make it a documented decision

## Decision log (this effort)
- 2026-06-28: Plan approved. CIL=primary ref, pharma=gap-fill. Lean 8–11 roster (Haiku tier rejected).
  Gym/learning IN scope (addendum, 01_OPUS_DECISIONS). Sequencing home-credit→olist→paysim→Volve.
  Build routed to Sonnet; Opus reviews.
