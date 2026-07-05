# REPO_MAP — generated navigation index

> **GENERATED — do not hand-edit.** `python scripts/gen_repo_map.py` rebuilds it from
> ground truth; CI runs `--check` and fails if this file is stale. Purpose is extracted
> from each file's own docstring / first heading / leading comment; *Uses* and *Used by*
> are parsed (`ast` for Python, `ref()` for dbt), never authored.
>
> **This is a pointer, not a cache.** It tells you which file to open — then READ THAT
> FILE FRESH before you edit or assert about it (ANTI-SHORTCUT PROTOCOL, CLAUDE.md). A
> pointer trusted without opening the file is just a bigger stale cache.
>
> Not mapped (by design): `.github/`, lockfiles, `*.example`, secret templates, settings.

**232 files mapped.**

## Architecture Decision Records

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `architecture/ADR-001-duckdb-over-spark.md` | ADR-001 — DuckDB + dbt over (local) PySpark for the transform layer | — | — |
| `architecture/ADR-002-graph-over-star.md` | ADR-002 — Asset-lineage graph + chunk feature store over a Kimball star | — | — |
| `architecture/ADR-003-chunking-in-silver.md` | ADR-003 — Semantic chunking lives in Silver; Bronze stays verbatim | — | — |
| `architecture/ADR-004-performance-veto-converted.md` | ADR-004 — Performance-correlation layer: veto converted, not reversed | — | — |
| `architecture/ADR-005-unified-s3-and-snowflake-serving.md` | ADR-005 — Unified S3 canonical storage + Snowflake Cortex serving veneer | — | — |
| `architecture/ADR-006-multi-client-tenancy.md` | ADR-006 — Multi-client tenancy (dim_client + tenant-scoped asset identity) | — | — |
| `architecture/ADR-007-landing-ttl.md` | ADR-007 — Landing TTL (hard-delete aged non-golden videos at 30 days) | — | — |
| `architecture/ADR-008-airflow-orchestration-wiring.md` | ADR-008 — Airflow orchestration: isolated venv + cross-venv script invocation | — | — |
| `architecture/ADR-009-slack-alerts-and-confluence-doc-sync.md` | ADR-009 — Operational notifications: Slack failure alerts + Confluence doc sync | — | — |
| `architecture/ADR-010-repo-map-and-adr-coupling-gates.md` | ADR-010 — Navigation index (REPO_MAP) + ADR-coupling gate | — | — |
| `architecture/ADR-011-conversational-language-protocol.md` | ADR-011 — Conversational language protocol (Malaysian Technical Manglish for narration) | — | — |
| `architecture/ADR-012-token-efficiency-and-session-discipline.md` | ADR-012 — Token-efficiency & session-discipline operating protocol | — | — |
| `architecture/ADR-013-aws-oidc-ci-federation.md` | ADR-013 — AWS OIDC role federation for real dbt build in CI | — | — |
| `architecture/ADR-014-security-and-access-model.md` | ADR-014 — Security & Access Model (simulation-grade) | — | — |

## Architecture docs (record)

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `architecture/BOUNDARY_CONTRACT.md` | STACK + SCOPE BOUNDARY CONTRACT | — | — |
| `architecture/BRD.md` | BRD — Business Requirements Document | — | — |
| `architecture/DATA_DICTIONARY.md` | DATA DICTIONARY — Creative Intelligence Pipeline | — | — |
| `architecture/DATA_MODEL.md` | DATA MODEL & ARCHITECTURE OF RECORD — Creative Intelligence Pipeline | — | — |
| `architecture/DATA_MODEL_v1.5_PERFORMANCE.md` | DATA MODEL — v1.5 PERFORMANCE ADDENDUM | — | — |
| `architecture/DBT_DAG.md` | dbt PROJECT STRUCTURE & DAG — Creative Intelligence Pipeline | — | — |
| `architecture/DQD.md` | DQD — Data Quality Document | — | — |
| `architecture/DRD.md` | DRD — Data Requirements Document | — | — |
| `architecture/ERD_consolidated.md` | ERD — CONSOLIDATED DATA MODEL (v1 + v1.5) | — | — |
| `architecture/LINEAGE_CONTRACT.md` | LINEAGE & DATA-FIDELITY CONTRACT | — | — |
| `architecture/SPEC_v1.5_performance_marts.md` | BUILD SPEC — v1.5 Performance Marts (fct_ad_kpi + correlation layer) | — | — |
| `architecture/SPEC_v1_search.md` | BUILD SPEC — v1 Search & Mix-and-Match Demo (ships FIRST) | — | — |
| `architecture/STACK_AND_FLOW.md` | STACK & END-TO-END FLOW — Creative Intelligence Pipeline | — | — |
| `architecture/STTM.md` | STTM — Source-to-Target Mapping | — | — |
| `architecture/banking_lakehouse_lab/00_MASTER_SPEC.md` | Banking Multi-Source Lakehouse — Master Spec (Fasa-0 planning) | — | — |
| `architecture/banking_lakehouse_lab/01_OPUS_DECISIONS.md` | Opus Decisions — Banking Multi-Source Lakehouse (Fasa-0 rulings) | — | — |
| `architecture/banking_lakehouse_lab/02_SONNET_BUILD_KICKOFF.md` | Sonnet Build Kickoff — banking-multisource-lakehouse | — | — |
| `architecture/banking_lakehouse_lab/03_DATASET_RISKS_AND_RESOLUTIONS.md` | Dataset Risk Register — all known problems + resolutions (35 items) | — | — |
| `architecture/banking_lakehouse_lab/04_BUSINESS_QUESTIONS.md` | The 10 Business Questions — what 80% of bank stakeholders actually ask | — | — |
| `architecture/banking_lakehouse_lab/05_BUILD_AND_VERIFY_PROMPTS.md` | Build & Verify Prompts — banking-multisource-lakehouse | — | — |
| `architecture/banking_lakehouse_lab/06_SECURITY_MODEL.md` | Security Model — banking-multisource-lakehouse (content source for journey/09) | — | — |
| `architecture/banking_lakehouse_lab/PROJECT_STATUS.md` | Banking Lakehouse Lab — Project Status | — | — |
| `architecture/control_plane_lab/00_MASTER_SPEC.md` | Control-Plane Airflow Lab — MASTER SPEC (Fasa 0, Opus) | — | — |
| `architecture/control_plane_lab/01_OPUS_DECISIONS.md` | Opus Decisions — Control-Plane Airflow Lab (signed-off ruling) | — | — |
| `architecture/control_plane_lab/02_SONNET_BUILD_KICKOFF.md` | Sonnet Build Kickoff — Control-Plane Airflow Lab (Fasa 1) | — | — |
| `architecture/control_plane_lab/03_PIPELINE_SIDE_CONTRACT.md` | Pipeline-Side Orchestration Contract (Fasa 0, Opus) | — | — |
| `architecture/control_plane_lab/PROJECT_STATUS.md` | Control-Plane Airflow Lab — PROJECT STATUS (resume-safe checkpoint) | — | — |
| `architecture/control_plane_lab/_source_to_port/doc_reference_contract.py` | Doc-reference contract — deterministic gate against documentation drift. | — | — |
| `architecture/control_plane_lab/_source_to_port/gen_repo_map.py` | Repo-map generator — the NAVIGATION half of the ANTI-SHORTCUT PROTOCOL (see CLAUDE.md). | — | — |
| `architecture/control_plane_lab/_source_to_port/governance_guard.py` | Governance hook — makes Claude check governed docs/ADRs BEFORE and AFTER touching governed files. | — | — |
| `architecture/control_plane_lab/_source_to_port/sync_docs_to_confluence.py` | Publish the curated onboarding doc set to Confluence as living documentation. | — | — |
| `architecture/control_plane_lab/saboteur/04_SONNET_HANDOVER.md` | Sonnet Handover — security layer + saboteur wiring (Fable-settled, 2026-07-04) | — | — |
| `architecture/control_plane_lab/saboteur/INCIDENT_RUNBOOK.md` | Incident Runbook — the 8-phase lifecycle every troubleshoot drill follows | — | — |
| `architecture/control_plane_lab/saboteur/PROBLEM_BANK_OPTIMIZATION.md` | Problem Bank — Optimization (100) | — | — |
| `architecture/control_plane_lab/saboteur/PROBLEM_BANK_TROUBLESHOOT.md` | Problem Bank — Troubleshooting (100) | — | — |
| `architecture/control_plane_lab/saboteur/README.md` | Saboteur Problem Bank — architecture (Fable design, 2026-07-04) | — | — |
| `architecture/erd.dbml` | — | — | — |
| `architecture/pipeline_retrofit/00_MASTER_SPEC.md` | Pipeline Retrofit — Master Spec (feed for Opus thinktank) | — | — |
| `architecture/pipeline_retrofit/01_OPUS_DECISIONS.md` | Opus Decisions — Pipeline Retrofit (signed-off ruling) | — | — |
| `architecture/pipeline_retrofit/02_SONNET_BUILD_KICKOFF.md` | Sonnet Build Kickoff — Pipeline Retrofit | — | — |
| `architecture/pipeline_retrofit/PROJECT_STATUS.md` | Pipeline Retrofit — PROJECT STATUS (resume-safe checkpoint) | — | — |
| `architecture/pipeline_retrofit/repo_archives/README.md` | repo_archives/ — full-history backups of the 4 ported repos | — | — |
| `architecture/pipeline_retrofit/repo_archives/Volve-Sensor-Production-Analytics-Pipeline-porting.tar.gz` | — | — | — |
| `architecture/pipeline_retrofit/repo_archives/home-credit-pipeline-porting.tar.gz` | — | — | — |
| `architecture/pipeline_retrofit/repo_archives/olist-ecommerce-pipeline-porting.tar.gz` | — | — | — |
| `architecture/pipeline_retrofit/repo_archives/paysim-fraud-pipeline-porting.tar.gz` | — | — | — |

## dbt — staging

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `models/staging/_sources.yml` | — | — | — |
| `models/staging/_staging.yml` | — | — | — |
| `models/staging/stg_gemini_raw.sql` | Flatten verbatim Gemini JSON -> one row per semantic chunk. | — | fact_extraction_run.sql, int_chunk_cleaned.sql |
| `models/staging/stg_meta_perf.sql` | Conform Meta funnel columns to the canonical schema (v1.5). | — | int_ad_perf_unioned.sql |
| `models/staging/stg_tiktok_perf.sql` | Conform TikTok funnel columns to the canonical schema (v1.5). | — | int_ad_perf_unioned.sql |

## dbt — intermediate

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `models/intermediate/_intermediate.yml` | — | — | — |
| `models/intermediate/int_ad_perf_unioned.sql` | Meta UNION TikTok + platform tag (v1.5). | stg_meta_perf.sql, stg_tiktok_perf.sql | fact_ad_performance.sql |
| `models/intermediate/int_chunk_cleaned.sql` | Filler removal, timestamp normalize, score passthrough. (Silver, ADR-003) | stg_gemini_raw.sql | bridge_chunk_compatibility.sql, dim_keyword_bridge.sql, dim_theme_bridge.sql, fact_chunk.sql |
| `models/intermediate/int_metric_chunk_alignment.sql` | Position-aligned mapping: each funnel metric -> the ONE owning chunk. SPEC §4. | bridge_ad_chunk.sql, dim_asset.sql, fact_ad_performance.sql | fct_ad_metric_chunk.sql |

## dbt — marts/core

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `models/marts/core/_core.yml` | — | — | — |
| `models/marts/core/bridge_asset_lineage.sql` | RAW -> EDITED edge. Navigation only; NEVER carries metrics. ADR-002/004. | dim_asset.sql | — |
| `models/marts/core/bridge_chunk_compatibility.sql` | Mix-and-match adjacency. Explodes next_compatible_themes[]. | int_chunk_cleaned.sql | assemble_sequence.sql, assert_assemble_sequence_standalone_safe.sql |
| `models/marts/core/dim_asset.sql` | Node table. RAW + EDITED. Sourced from the ingestion manifest — asset_type and | — | bridge_asset_lineage.sql, demo_queries.sql, int_metric_chunk_alignment.sql |
| `models/marts/core/dim_keyword_bridge.sql` | (no leading -- comment) | int_chunk_cleaned.sql | — |
| `models/marts/core/dim_theme_bridge.sql` | (no leading -- comment) | int_chunk_cleaned.sql | — |
| `models/marts/core/fact_chunk.sql` | Feature row. GRAIN = one semantic chunk. ADR-002. | int_chunk_cleaned.sql | assemble_sequence.sql, assert_assemble_sequence_standalone_safe.sql, assert_edl_bridge_ad_chunk_reconciles.sql, bridge_ad_chunk.sql, demo_queries.sql, fct_ad_metric_chunk.sql |
| `models/marts/core/fact_extraction_run.sql` | Operational telemetry (enhancement): tokens/cost/latency/confidence. | stg_gemini_raw.sql | — |

## dbt — marts/performance

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `models/marts/performance/_performance.yml` | — | — | — |
| `models/marts/performance/bridge_ad_chunk.sql` | Editor's asserted cut: ad -> chunk + role + position (the v1.5 unlock). SPEC §2. | fact_chunk.sql | int_metric_chunk_alignment.sql |
| `models/marts/performance/fact_ad_performance.sql` | GRAIN: 1 edited-ad x 1 platform x 1 DAY. Raw counts only. ADR-004 / SPEC §2. | int_ad_perf_unioned.sql | fct_ad_kpi.sql, int_metric_chunk_alignment.sql |
| `models/marts/performance/fct_ad_kpi.sql` | Ratios derived here ONLY (ratio-of-sums). SPEC §3. | fact_ad_performance.sql | fct_ad_metric_chunk.sql |
| `models/marts/performance/fct_ad_metric_chunk.sql` | 1 ad x platform x metric -> metric value + mapped chunk features. SPEC §5. | fact_chunk.sql, fct_ad_kpi.sql, int_metric_chunk_alignment.sql | mart_chunk_perf_correlation.sql |
| `models/marts/performance/mart_chunk_perf_correlation.sql` | Surfaced insight. Within-platform, within-winners, sample-gated. SPEC §6. | fct_ad_metric_chunk.sql | — |

## Seeds

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `seeds/asset_manifest.csv` | seed · asset_id,client_id,content_sha256,asset_name,asset_type,parent_asset_id,duration_sec,source_uri,ingest… | — | — |
| `seeds/dim_client.csv` | seed · client_id,client_name,account_support_owner,drive_folder_id,landing_ttl_days,status | — | — |
| `seeds/dim_platform.csv` | seed · platform_id,platform_name,hook_window_sec,hold_milestones | — | — |
| `seeds/edit_decision_list.csv` | seed · ad_id,chunk_id,chunk_role,position_in_ad,start_sec,end_sec | — | — |
| `seeds/map_ad_asset.csv` | seed · ad_id,asset_id | — | — |

## Scripts

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `scripts/enforce_landing_ttl.py` | Landing TTL guarded delete — hard-delete aged non-golden videos (ADR-007). | env_guard.py | — |
| `scripts/env_guard.py` | Fail-closed env guard (mirror of pharma gym_guard). Import + call assert_safe() in any | — | enforce_landing_ttl.py, generate_embeddings.py, ingest_drive_to_s3.py, list_unextracted_assets.py, reconcile_snowflake_serving.py, run_gemini_extract.py |
| `scripts/gen_repo_map.py` | Repo-map generator — the NAVIGATION half of the ANTI-SHORTCUT PROTOCOL (see CLAUDE.md). | — | — |
| `scripts/generate_embeddings.py` | Silver chunk text -> Gemini embeddings -> gold/chunk_embedding (BYO, content-hash-gated). | env_guard.py | — |
| `scripts/ingest_drive_to_s3.py` | Drive -> S3 landing. Tenant-scoped content-hash naming, skip-existing (idempotent). | env_guard.py | run_gemini_extract.py |
| `scripts/list_unextracted_assets.py` | List asset_ids landed for a client that do NOT yet have a Bronze extraction. | env_guard.py | — |
| `scripts/provision_snowflake_serving.py` | Capture-as-code Snowflake serving provisioning (ADR-005 §B). | — | — |
| `scripts/run_gemini_extract.py` | S3 video -> Gemini (Flash, responseSchema) -> bronze_asset_raw (verbatim JSON). | env_guard.py, ingest_drive_to_s3.py | — |
| `scripts/search_cli.py` | v1 search + mix-and-match demo CLI — architecture/SPEC_v1_search.md (Owner: @senior-data-engineer). | — | — |
| `scripts/significance_post_step.py` | SUGGESTIVE-tier significance: DuckDB -> pandas -> scipy Mann-Whitney U + Bonferroni. | — | — |
| `scripts/sync_docs_to_confluence.py` | Publish the curated onboarding doc set to Confluence as living documentation. | — | — |
| `setup.sh` | — | — | — |

## Airflow DAGs

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `dags/creative_intel_pipeline.py` | Creative Intelligence pipeline DAG (local Airflow). | — | — |

## Tests / contracts

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `tests/GATES.md` | Gate registry | — | — |
| `tests/adr_coupling_contract.py` | ADR-coupling contract — a STRUCTURAL change to a governed file must ship with an ADR touch. | — | test_adr_coupling_contract.py |
| `tests/assert_assemble_sequence_standalone_safe.sql` | Singular dbt test — SPEC_v1_search.md §4 "assembler safety" row. | bridge_chunk_compatibility.sql, fact_chunk.sql | — |
| `tests/assert_edl_bridge_ad_chunk_reconciles.sql` | Singular dbt test — DQD.md §3 item 2 / PROJECT_STATUS.md finding #3 (HIGH, OPEN until now). | fact_chunk.sql | — |
| `tests/boundary_contract.py` | Stack + scope boundary contract — deterministic gate over rejected tech & v2-backlog scope. | — | — |
| `tests/doc_reference_contract.py` | Doc-reference contract — deterministic gate against documentation drift. | — | test_doc_reference_contract.py |
| `tests/golden/fixture_data.py` | Golden-dataset fixture: one frozen Gemini-shaped Bronze response + its hand-verified answer key. | — | run_golden_test.py |
| `tests/golden/run_golden_test.py` | Golden-dataset test — proves fact_chunk computes the RIGHT values, not just valid-shaped ones. | fixture_data.py | — |
| `tests/lineage_contract.py` | Lineage & data-fidelity contract — deterministic gate over the landing manifest. | — | — |
| `tests/reconcile_snowflake_serving.py` | Snowflake serving reconciliation gate (ADR-005 spine). | env_guard.py | — |
| `tests/test_adr_coupling_contract.py` | Self-test for adr_coupling_contract.py — the gate is itself tested (house pattern). | adr_coupling_contract.py | — |
| `tests/test_doc_reference_contract.py` | Self-test for tests/doc_reference_contract.py — proves the gate actually fires. | doc_reference_contract.py | — |

## Great Expectations suites

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `great_expectations/README.md` | Great Expectations suites (per layer) | — | — |
| `great_expectations/expectations/bronze_asset_raw.json` | — | — | — |
| `great_expectations/expectations/fact_ad_performance.json` | — | — | — |
| `great_expectations/expectations/mart_chunk_perf_correlation.json` | — | — | — |
| `great_expectations/expectations/silver_chunk.json` | — | — | — |

## Governance hooks

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `.claude/hooks/governance_guard.py` | Governance hook — makes Claude check governed docs/ADRs BEFORE and AFTER touching governed files. | — | — |

## Cabinet agents

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `.claude/agents/cikgu.md` | name: cikgu | — | — |
| `.claude/agents/data-architect.md` | name: data-architect | — | — |
| `.claude/agents/data-quality-steward.md` | name: data-quality-steward | — | — |
| `.claude/agents/finops-agent.md` | name: finops-agent | — | — |
| `.claude/agents/product-owner.md` | name: product-owner | — | — |
| `.claude/agents/qa-engineer.md` | name: qa-engineer | — | — |
| `.claude/agents/scope-guardian.md` | name: scope-guardian | — | — |
| `.claude/agents/senior-data-engineer.md` | name: senior-data-engineer | — | — |

## Config

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `dbt_project.yml` | — | — | — |
| `framework_template/gates/framework.yml` | framework.yml — the ONE config every gate script in gates/ reads. | — | — |
| `packages.yml` | — | — | — |
| `profiles.yml` | Copy to ~/.dbt/profiles.yml (or set DBT_PROFILES_DIR to this folder). | — | — |
| `simulation/sim_dbt/dbt_project.yml` | — | — | — |

## Ad-hoc analyses

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `analyses/assemble_sequence.sql` | Leg (b) mix-and-match reference query — SPEC_v1_search.md §3.2. | bridge_chunk_compatibility.sql, fact_chunk.sql | — |
| `analyses/demo_queries.sql` | The three demo queries (full text: SPEC_v1.5_performance_marts.md §8). | dim_asset.sql, fact_chunk.sql | — |

## Learning

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `learning/CURRICULUM.md` | Learning Curriculum — Creative Intelligence Pipeline | — | — |
| `learning/EXECUTIVE_STORYTELLING_TEMPLATE.md` | 🧠 Executive Storytelling Template — Technical Q&A → Architect-Level Answer | — | — |
| `learning/LEARNING_LOG.md` | Learning Log — Creative Intelligence Pipeline | — | — |
| `learning/diy/README.md` | DIY build practice | — | — |

## Cheatsheets

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `cheatsheets/optimization/00_INDEX.md` | Optimization Library — Creative Intelligence Pipeline (INDEX) | — | — |
| `cheatsheets/troubleshooting/00_INDEX.md` | Troubleshooting Library — Creative Intelligence Pipeline (INDEX) | — | — |

## Debate record

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `debate/00_AGENDA.md` | Debate Agenda — Creative Intelligence Pipeline | — | — |
| `debate/DEBATE_LOG.md` | DEBATE LOG — Creative Intelligence Pipeline Cabinet Convene | — | — |
| `debate/ROUND_02_PERFORMANCE_DEBATE.md` | ROUND 2 DEBATE LOG — Performance Data Arrives | — | — |

## Top-level docs

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `AGENT_ROSTER_RECOMMENDATION.md` | AGENT ROSTER RECOMMENDATION — Creative Intelligence Pipeline | — | — |
| `BACKLOG.md` | BACKLOG — Creative Intelligence Pipeline (rejected / closed items, historical record) | — | — |
| `CLAUDE.md` | Creative Intelligence Pipeline — AI Context | — | — |
| `PROJECT_STATUS.md` | PROJECT STATUS — Creative Intelligence Pipeline | — | — |
| `README.md` | Creative Intelligence Pipeline — Cabinet Convene (Side Project) | — | — |
| `README_BUILD.md` | Build quickstart | — | — |
| `confluence/00_START_HERE.md` | Creative Intelligence Pipeline — Start Here | — | — |
| `confluence/01_ARCHITECTURE_DECISIONS.md` | Creative Intelligence Pipeline — Architecture Decisions (start here) | — | — |
| `confluence/02_PIPELINE_DOCUMENTATION.md` | Pipeline Documentation | — | — |
| `confluence/03_DATA_CONTRACT.md` | Data Contract | — | — |
| `confluence/04_RUNBOOK.md` | Runbook | — | — |
| `confluence/05_RELEASE_NOTES.md` | Release Notes | — | — |
| `confluence/06_KNOWN_ISSUES.md` | Known Issues | — | — |
| `confluence/07_INCIDENT_POSTMORTEM.md` | Incident Postmortem | — | — |
| `confluence/08_DEPLOYMENT_GUIDE.md` | Deployment Guide | — | — |
| `framework_template/00_START_HERE.md` | Framework Template — how to use this kit | — | — |
| `framework_template/CHANGELOG.md` | Framework Template — Changelog | — | — |
| `framework_template/governance/ADR/ADR-000-feature-intake-protocol.md` | ADR-000 — Feature Intake Protocol (ad-hoc feature control) | — | — |
| `framework_template/governance/ADR/ADR-001-security-layer-mandatory.md` | ADR-001 (kit) — Security layer is mandatory, not tiered | — | — |
| `framework_template/governance/ADR/ADR-TEMPLATE.md` | ADR-NNN — {{Title}} | — | — |
| `framework_template/governance/BACKLOG.md` | Backlog — rejected / deferred ledger | — | — |
| `framework_template/governance/BOUNDARY_CONTRACT.md` | Boundary Contract — {{PROJECT}} | — | — |
| `framework_template/governance/plans/PLAN_TEMPLATE.md` | Plan — {{feature/change name}} | — | — |
| `framework_template/journey/01_DATASET_AND_SOURCES.md` | 01 — Dataset & Sources | — | — |
| `framework_template/journey/02_BUSINESS_QUESTIONS.md` | 02 — Business Questions (BRD-lite) | — | — |
| `framework_template/journey/03_DATA_REQUIREMENTS.md` | 03 — Data Requirements (DRD) | — | — |
| `framework_template/journey/04_DATA_MODEL.md` | 04 — Data Model | — | — |
| `framework_template/journey/05_STTM.md` | 05 — Source-to-Target Mapping (STTM) | — | — |
| `framework_template/journey/06_DQ_PLAN.md` | 06 — Data Quality Plan (DQD) | — | — |
| `framework_template/journey/07_PIPELINE_SPEC.md` | 07 — Pipeline Spec | — | — |
| `framework_template/journey/08_SERVING_AND_EVIDENCE.md` | 08 — Serving & Evidence | — | — |
| `framework_template/journey/09_SECURITY_AND_ACCESS.md` | 09 — Security & Access | — | — |
| `framework_template/operating/agents/architect.md` | name: architect | — | — |
| `framework_template/operating/agents/data-quality-steward.md` | name: data-quality-steward | — | — |
| `framework_template/operating/agents/finops-agent.md` | name: finops-agent | — | — |
| `framework_template/operating/agents/product-owner.md` | name: product-owner | — | — |
| `framework_template/operating/agents/scope-guardian.md` | name: scope-guardian | — | — |
| `framework_template/operating/agents/senior-data-engineer.md` | name: senior-data-engineer | — | — |
| `interview_prep/FULL_PROJECT_DEFENSE.md` | Full Project Defense — Five Data Pipelines (prose, copy-paste ready) | — | — |
| `interview_prep/INTERVIEW_MASTER.md` | Interview Master — Full Prep Bundle | — | — |
| `interview_prep/OPTIMIZATION_AND_TROUBLESHOOTING_DEEP_DIVE.md` | Optimization & Troubleshooting — Deep Drill-Down (2–3 layers per decision) | — | — |
| `simulation/.solutions/O-O01_full_scan.md` | 🔒 GATED SOLUTION — O-O01 Read the Plan (full scan) | — | — |
| `simulation/.solutions/T-L01_dup_pk.md` | 🔒 GATED SOLUTION — T-L01 Duplicate PK | — | — |
| `simulation/.solutions/T-SEC-01_leaked_key.md` | 🔒 GATED SOLUTION — T-SEC-01 Leaked Credential (8-phase incident) | — | — |
| `simulation/.solutions/T-SRV-04_rbac_future_grant.md` | 🔒 GATED SOLUTION — T-SRV-04 RBAC Future Grant | — | — |
| `simulation/00_MASTER_PLAN.md` | RBC Simulation Lab — Master Plan | — | — |
| `simulation/CARD_FORMAT.md` | Card Format — drill writeups & runbook entries | — | — |
| `simulation/CIKGU_DRILL_PROTOCOL.md` | Cikgu Drill Protocol — how a drill session runs | — | — |
| `simulation/HINT_LOG.md` | Hint Log — which hint level unblocked each drill | — | — |
| `simulation/ISOLATION_CONTRACT.md` | Isolation Contract — RBC Simulation Lab | — | — |
| `simulation/LADDERS.md` | Difficulty Ladders — Troubleshooting (T) & Optimization (O) | — | — |
| `simulation/PEDAGOGY_PREFS.md` | Pedagogy Preferences — How Luqman Learns | — | — |
| `simulation/SONNET_KICKOFF_PROMPT.md` | Sonnet kickoff prompt — RBC Simulation Lab execution | — | — |
| `simulation/drills/O-O01_full_scan.md` | Drill O-O01 — Read the Plan (the full scan) | — | — |
| `simulation/drills/T-L01_dup_pk.md` | Drill T-L01 — Duplicate PK (the inflated number) | — | — |
| `simulation/drills/T-SEC-01_leaked_key.md` | Drill T-SEC-01 — Credential leaked to git (full 8-phase incident) | — | — |
| `simulation/drills/T-SRV-04_rbac_future_grant.md` | Drill T-SRV-04 — New Gold model invisible to the analyst role | — | — |
| `simulation/faults/README.md` | Fault Library — the @bottleneck-saboteur, as a tool | — | — |
| `simulation/faults/catalog/CIL_INJECTABLE_MAP.md` | CIL Injectable Map — which bank T-IDs run against this repo's real stack today | — | — |
| `simulation/runbook/T-L01_dup_pk.md` | T-L01 — Duplicate PK in silver_chunk ✅ PASSED | — | — |
| `simulation/sim_dbt/README.md` | sim_dbt — isolated simulation dbt project | — | — |
| `simulation/specs/01_SIM_migration_dryrun.md` | Sim #1 — Migration Dry-Run (Teradata → Snowflake logic migration) | — | — |
| `simulation/specs/02_SIM_pyspark_parity.md` | Sim #2 — PySpark Parity (close the "no Spark" gap) | — | — |
| `simulation/specs/03_SIM_incident_e2e.md` | Sim #3 — Incident End-to-End (troubleshooting drill) | — | — |
| `simulation/specs/04_SIM_value_reconciliation.md` | Sim #4 — Value-Level Reconciliation (the headline banking skill) | — | — |
| `simulation/specs/05_OPTIMIZATION_LAB.md` | Sim #5 — Optimization Lab (profile → tune → measure) | — | — |
| `simulation/specs/06_RBC_TASK_MAP.md` | RBC Day-to-Day Task Map (100) — tagged by lab simulatability | — | — |
| `simulation/specs/07_INTERVIEW_CHEATSHEET.md` | RBC Interview Cheat-Sheet — STAR stories from the sim lab | — | — |

## Other

| File | Purpose | Uses | Used by |
|------|---------|------|---------|
| `framework_template/gates/_config.py` | Shared config loader for gates/*.py — reads gates/framework.yml. | — | boundary_contract.py, doc_reference_contract.py, governance_guard.py, journey_completeness.py, secrets_scan.py |
| `framework_template/gates/boundary_contract.py` | Stack + scope boundary contract — config-driven, reads gates/framework.yml. | _config.py | — |
| `framework_template/gates/ci.yml.template` | — | — | — |
| `framework_template/gates/doc_reference_contract.py` | Doc-reference contract — config-driven, reads gates/framework.yml → paths:. | _config.py | — |
| `framework_template/gates/hooks/governance_guard.py` | Governance hook — config-driven, reads gates/framework.yml → governed_paths:. | _config.py | — |
| `framework_template/gates/journey_completeness.py` | Journey completeness gate — every mandatory journey/*.md doc must exist and be filled in. | _config.py | — |
| `framework_template/gates/secrets_scan.py` | Secrets scan gate — config-driven, reads gates/framework.yml secrets_scan:. | _config.py | — |
| `framework_template/operating/CLAUDE.md.template` | — | — | — |
| `framework_template/operating/PROJECT_STATUS.md.template` | — | — | — |
| `interview_repos_output/1_volve_sensor_pipeline.txt` | — | — | — |
| `interview_repos_output/2_paysim_fraud_pipeline.txt` | — | — | — |
| `interview_repos_output/3_olist_ecommerce_pipeline.txt` | — | — | — |
| `interview_repos_output/4_home_credit_pipeline.txt` | — | — | — |
| `interview_repos_output/5_creative_intelligence_lab.txt` | — | — | — |
| `macros/s3_external.sql` | (no leading -- comment) | — | — |
| `requirements-airflow.txt` | — | — | — |
| `requirements.txt` | — | — | — |
| `simulation/check_isolation.py` | Isolation guard for the RBC simulation lab (simulation/). | — | — |
| `simulation/faults/inject.py` | faults/inject.py — the @bottleneck-saboteur as a TOOL (not a roster agent). | — | — |
| `simulation/faults/reset.py` | faults/reset.py — restore the sim lab's clean baseline (total undo of any injected fault). | — | — |
| `simulation/sim_dbt/profiles.sim.yml.example` | — | — | — |
