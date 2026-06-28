# Opus Decisions — Pipeline Retrofit (signed-off ruling)

> Reads with `00_MASTER_SPEC.md` (Sonnet's map). This file = Opus's verified rulings after
> ground-truth recheck. Owner approved 2026-06-28: additions #1 (INTERVIEW_GUIDE), sequencing
> (home-credit first), executor-tier rejection, and routing the build to Sonnet.
> Branch: `framework/pipeline-retrofit-plan`.

## Verified corrections to the master spec
1. **CIL Confluence is BUILT** — `scripts/sync_docs_to_confluence.py` (250 lines, real Atlassian
   API) + curated `confluence/` 9-page set (00_START_HERE … 08_DEPLOYMENT_GUIDE). → CIL is the
   PRIMARY Confluence reference; pharma's `publish_to_confluence.py` is cross-check only.
2. **CIL Slack is BUILT** — `_notify_slack_failure` in `dags/creative_intel_pipeline.py:111`,
   DAG-level `on_failure_callback`, graceful degradation. → reference for olist/Volve backfill.
   home-credit + paysim KEEP their own working Slack.
3. **Volve = 0 ADRs** (repo-wide code search) — confirmed worst-off; ADR folder built from zero.
4. **paysim `.mcp.json`** identical to home-credit (snowflake/databricks/aws-docs/dbt); no `.claude/`.
5. **olist ADR-001** is sound (grain + per-dim SCD + consequences); only needs MORE ADRs.

## Approved framework elements (build as-is)
- CLAUDE.md (CIL structure: stop-gate + anti-shortcut, hook-backed) — English default (ADR-011 lesson).
- `governance_guard.py` hook — governed-file map tailored per repo (see table below).
- Contracts: `doc_reference_contract.py` (universal), `boundary_contract.py` (per-repo locked stack),
  `lineage_contract.py` renamed **identity contract** (per-repo identity key).
- `gen_repo_map.py` + REPO_MAP.md (all 4).
- ADR system (CIL numbering + pharma mid-build-addendum discipline).
- Token/model-routing protocol (ADR-012).
- Confluence via CIL's script+page-set; Slack per repo (keep home-credit/paysim, backfill olist/Volve).
- Log subset: PROJECT_STATUS.md, COST_LOG.md, DECISION_LOG.md (+ INFRA_LIMITS_LOG.md for Volve & home-credit only).

## REJECTED (with reason)
- **Haiku executor tier** (data-engineer, analytics-engineer, devops-orchestrator) — repos are
  finished; no live repetitive build to amortize. Violates ADR-012 (no routing without volume).
- **project-manager agent** — README "Phase Completion" table already serves this.
- **standalone qa-engineer** — CIL conditional-seat rule; fold into senior-data-engineer.
- Net: lean 8–10 roster per repo, mirroring CIL's 8, NOT pharma's 20. Reversible if a repo
  re-enters active build.

## ADDENDUM 2026-06-28 — gym/learning layer is IN scope (reverses earlier out-of-scope ruling)
Owner clarified the TRUE purpose: each repo becomes a **self-teaching lab like CIL** so owner can
(a) rebuild the pipeline from scratch with @cikgu, (b) practice optimization + troubleshooting +
simulation drills, **without touching `main`** — and end up able to DEFEND every resume claim.
Therefore the learning/gym layer (previously "out of scope") is now REQUIRED per repo:
- **+1 agent: `cikgu`** added to every roster (English-first teaching, per `learning-style-formula`
  memory: mental-model → ETL use-case → production bug → debug → syntax LAST).
- **`learning/CURRICULUM.md`** — module path to rebuild THAT repo's pipeline from scratch, tailored
  to its stack (olist=ADF/Databricks/ADLS·home-credit=Glue/PySpark·paysim=Databricks SQL+cumulative·
  Volve=Databricks+MLflow). Scored, WHY-before-HOW, DIY tickets. Pattern = CIL `learning/`.
- **`learning/LEARNING_LOG.md`** — scored progress (start 100, hint=-5).
- **`simulation/`** — isolated practice lab. Pattern = CIL `simulation/`: `ISOLATION_CONTRACT.md`
  (R1 own storage prefix · R2 own dbt/compute project · R3 no ref into real models) +
  `check_isolation.py` + `faults/` (inject.py/reset.py, named reversible faults) + specs
  (migration / troubleshoot-E2E / optimization / value-reconciliation). Drills run on **per-drill
  git branches** (`gym/round-NN` or `drill/<id>`), NEVER `main`.
- Roster therefore: olist 9 · Volve 11 · home-credit 11 · paysim 10 (each = prior count +cikgu).

## Push & branch workflow (per repo)
- Retrofit lands on a feature branch (e.g. `framework/governance-retrofit`) → PR → push to that repo.
- Learning/drills happen on throwaway branches (`drill/*`, `gym/*`) — main stays clean & defensible.
- `simulation/` is committed but isolation-contracted; faults only mutate sim state, never main.

## Per-roster roster (final — pre-addendum base; +cikgu per addendum above)
| Agent | olist | Volve | home-credit | paysim |
|---|---|---|---|---|
| data-architect (Opus, veto) | ✅ | ✅ | ✅ | ✅ |
| scope-guardian (veto) | ✅ | ✅ | ✅ | ✅ |
| senior-data-engineer (absorbs dbt+QA+orchestration) | ✅ | ✅ | ✅ | ✅ |
| data-quality-steward | ✅ | ✅ | ✅ | ✅ |
| product-owner | ✅ | ✅ | ✅ | ✅ |
| business-analyst (DRD + resume-claim reconciliation) | ✅ | ✅ | ✅ | ✅ |
| data-platform-engineer (absorbs devops) | ✅ | ✅ | ✅ | ✅ |
| documentation-sherpa | ✅ | ✅ | ✅ | ✅ |
| finops-agent | ❌ | ✅ | ✅ | ✅ |
| infra-reality-agent | ❌ | ✅ | ✅ | ❌ |
| **count** | 8 | 10 | 10 | 9 |

## Per-repo governed-file map (hook targets)
| Repo | governance_guard protects | identity key | boundary (rejected tech) |
|---|---|---|---|
| olist | gold/dbt_models/models/marts/, docs/DATA_MODEL.md, docs/ADR/, silver/transform_*_scd*.py | SCD2 surrogate keys | non-ADLS/Databricks/Snowflake compute |
| Volve | gold/*.py (Databricks Gold — NO dbt), ml/train_*.py, docs/DATA_MODEL.md, docs/ADR/ | well_id + date grain | non-Databricks compute |
| home-credit | glue/glue_silver_*.py, dbt_home_credit/models/mart/, snapshots/, docs/ADR/ | SK_ID_CURR + SCD2 | Spark outside Glue; Databricks beyond query-only |
| paysim | gold/models/marts/, silver/cumulative_pipeline.py, docs/ADR/ | cumulative-table grain | non-Databricks/Snowflake |

## Additions requiring (now granted) owner sign-off
1. **INTERVIEW_GUIDE.md** per repo — APPROVED. Must contain a **"Resume Claim ↔ Repo Evidence"
   reconciliation table**: every resume bullet → `file:line` evidence, else flagged unsupported
   (backfill repo OR soften resume). Owner: business-analyst + documentation-sherpa.
2. Per-repo ADRs to backfill:
   - olist: SCD-strategy ADR, Slack-alerting ADR.
   - Volve: full ADR set from zero — storage/compute, free-tier well cap, 3 ML-model choices —
     each tagged "(reconstructed from README — owner confirm rationale)" (NO fabricated deliberation).
   - home-credit: PII-mask-order ADR, Kimball-over-OBT sizing ADR.
   - paysim: GE 14/15 WARN ADR — fix OR formally accept with written rationale.

## Known resume↔repo mismatches for Sonnet to reconcile during build
- **olist:** resume says "Azure Data Factory (ADF)"; repo uses Databricks COPY INTO + Kaggle CLI.
  → either evidence ADF in repo or correct the resume claim.
- **home-credit:** resume lists "Lambda, Step Functions"; README shows Glue + Airflow only.
- **Volve:** resume "84 tests, 0 failures" — verify against repo test count.
- **paysim:** resume "Silver 14/15" — the 1 WARN must become a documented decision (addition #2).

## Sequencing (approved)
home-credit FIRST (template — Helix-Lending match, has .mcp.json, smallest gap) → port pattern
(NOT literal copy; stacks differ) to olist → paysim → Volve (most work, last).

## Routing
Build authoring = Sonnet (mechanical, per ADR-012). Opus reviews. Kickoff: `02_SONNET_BUILD_KICKOFF.md`.
