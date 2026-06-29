# Control-Plane Airflow Lab — MASTER SPEC (Fasa 0, Opus)

> Build contract for `rajeluqman/airflow_dag_running_pipeline`. Sonnet builds from this.
> Reads with `01_OPUS_DECISIONS.md` (locked rulings). Owner-confirmed 2026-06-29.
> Durable planning location = CIL `architecture/control_plane_lab/` (same precedent as
> `pipeline_retrofit/`). The repo itself is cloned/built once PAT (`GH_AIRFLOW`) is live.

## 1. What this repo IS (3-in-1)
1. **Control-plane** — ONE Airflow hub orchestrating 5 pipelines (CIL + home-credit + olist +
   paysim + Volve) across 4 real stacks. DAGs are **trigger-only**: no business logic, logic
   stays in each pipeline's own repo. Compute on cloud; transform dev'd in codespace
   (PySpark-local / DuckDB stand-in) then ported to Glue/Databricks.
2. **Teaching lab** — port CIL framework PHILOSOPHY (anti-shortcut, repo-map, doc-ref gate,
   cikgu), NOT its data content (no lineage/identity/Clean-ERD — this repo models no data).
3. **Live-chaos range** — `@saboteur` injects faults LIVE in staging; `@sre-incident-commander`
   responds; MTTR scored. staging→prod promotion across 2 real cloud environments.

## 2. The ANTI-PATTERN to avoid (load-bearing)
Do NOT copy CIL gates verbatim. CIL is a DATA repo (lineage/identity/Clean-ERD). This is an
OPS repo. Port the *philosophy* ("gates not vigilance, code tak penat"); the *content* is new
and about orchestration + operations + chaos containment.

| CIL gate | This repo |
|---|---|
| lineage_contract / identity | ❌ drop — repo models no data |
| Clean-ERD doctrine + data-architect | ❌ drop — no new data models built here |
| boundary (reject Spark/Databricks) | ✅ but INVERTED — here Glue/Databricks are REQUIRED |
| anti-shortcut protocol | ✅ port |
| repo-map navigation gate | ✅ port |
| doc-reference contract | ✅ port |

## 3. New gates/contracts (the OPS content)
- **cross_stack_contract.py** — proves DAGs are trigger-only: no SQL/PySpark transform body in
  DAG files, no `import` of any pipeline repo's business logic. DAG = operator + connection ref.
- **saboteur_containment_contract.py** — proves `@saboteur` can touch `staging` ONLY: no prod
  credential reference in any `faults/` path; every fault has a declared blast-radius +
  reversible `reset`. CI-gated. This is the HARD safety boundary.
- **cost_guard.py** — asserts every drill defines an auto-teardown (cluster terminate / warehouse
  suspend) and a per-stack budget ceiling. Aggressive: credits > convenience (owner decision #5).
- **env_promotion_contract.py** — staging→prod gate: a change only promotes after staging drill
  green + MTTR recorded. No direct prod edits.
- **doc_reference_contract.py / gen_repo_map.py** — ported from CIL as-is.

## 4. Stacks orchestrated (trigger-only; preserve each, never homogenize)
| Pipeline | Compute target | Airflow operator |
|---|---|---|
| home-credit | AWS Glue (PySpark) | `GlueJobOperator` |
| olist | Azure Databricks (ADLS) | `DatabricksRunNowOperator` |
| paysim | Databricks SQL / PySpark+Delta | `DatabricksRunNowOperator` |
| Volve | Databricks + MLflow | `DatabricksSubmitRunOperator` |
| CIL | DuckDB→Snowflake | bash/python trigger |
| (all dbt) | Snowflake | `DbtCloudRunJobOperator` / bash |

## 5. The 4 Opus additions (beyond owner's prompt — all confirmed)
- **A. Saboteur-Containment Contract** — staging-only, blast-radius, auto-rollback, CI-gated.
- **B. Cost circuit-breaker + auto-teardown** after every drill (trial credits finite; runaway
  Databricks/Snowflake is existential cost).
- **C. Terraform IaC** — the engine for staging≈prod parity + cheap teardown + rebuild. Without
  it, "staging→prod" and "auto-teardown" are not real.
- **D. Observability** — CloudWatch (Glue) + Databricks job logs + Snowflake query history +
  Airflow task logs + Slack alert. Can't debug live faults blind. This is the heart of "debug".

## 6. Repo skeleton (Sonnet builds)
```
airflow_dag_running_pipeline/
├── CLAUDE.md                      # ops-layer governance (stop-gate + anti-shortcut, hook-backed)
├── airflow/
│   ├── dags/{cil,home_credit,olist,paysim,volve}_dag.py   # trigger-only
│   ├── connections/               # aws/azure/databricks/snowflake (secret-backend refs)
│   └── docker-compose.yml         # 1 Airflow hub, codespace
├── infra/terraform/{staging,prod}/   # IaC per environment (start: AWS/Glue)
├── .claude/agents/                # roster §7 of 01_OPUS_DECISIONS
├── .claude/hooks/governance_guard.py
├── tests/{cross_stack_contract,saboteur_containment_contract,cost_guard,
│           env_promotion_contract,doc_reference_contract}.py
├── scripts/gen_repo_map.py
├── architecture/{ADR/,REPO_MAP.md,CROSS_STACK_CONTRACT.md,REPO_REGISTRY.md}
├── learning/{CURRICULUM.md,LEARNING_LOG.md}   # debug/troubleshoot/optimize/incident path
├── simulation/                    # LIVE-cloud chaos range (not local like CIL)
│   ├── ISOLATION_CONTRACT.md  check_isolation.py
│   ├── faults/{inject.py,reset.py}   # saboteur faults, reversible, staging-only
│   └── runbooks/  MTTR_SCORECARD.md
├── observability/                 # log-pointer + Slack alert wiring
├── .github/workflows/ci.yml       # static gates (no cloud secrets in CI)
├── PROJECT_STATUS.md  COST_LOG.md  DECISION_LOG.md  INFRA_LIMITS_LOG.md
└── INTERVIEW_GUIDE.md             # "manage many pipelines" + MTTR evidence
```

## 7. ADRs to author (Fasa 0 → repo `architecture/ADR/`)
- ADR-001 — control-plane boundary (DAG = trigger-only, logic stays in pipeline repos)
- ADR-002 — one Airflow hub over per-repo Airflow (chosen by owner)
- ADR-003 — codespace-first dev, cloud compute, MWAA on-demand only (cost rationale)
- ADR-004 — two real cloud environments (staging + prod, sit-on-2-cloud)
- ADR-005 — saboteur-containment policy (staging-only, blast-radius, the safety doctrine)
- ADR-006 — aggressive cost circuit-breaker + auto-teardown
- ADR-007 — Terraform IaC for parity + teardown
- ADR-008 — observability stack (the debug substrate)
- ADR-009 — conversational language (port CIL ADR-011: English default, Manglish opt-in)
- ADR-010 — token-efficiency/session-discipline (port CIL ADR-012)

## 8. Build sequencing (Opus designs, Sonnet builds)
- **Fasa 0** (Opus, now): this spec + 01_OPUS_DECISIONS + ADR drafts + contract specs.
- **Fasa 1** (Sonnet): repo scaffold — CLAUDE.md, agents, hooks, gates, cikgu, sim skeleton,
  confluence sync, .gitignore, secrets-backend abstraction, **+ 5 trigger-STUB DAGs** (so
  `cross_stack_contract.py` has a real target — a gate with nothing to check is dead). NO cloud
  yet, stubs only. All contracts green locally. Repo starts EMPTY: initial commit to `main` first.
- **Fasa 2** (Sonnet): Airflow running in codespace (docker-compose) + wire the stub DAGs to real
  job triggers (mocked/local targets first).
- **Fasa 3** (Sonnet): Terraform staging — AWS/Glue first (cheapest, most interview-relevant).
- **Fasa 4** (Sonnet+owner): first `@saboteur` ⚔️ `@sre-incident-commander` drill on staging.
- **Fasa 5**: expand to 4 stacks + prod env + MTTR scorecard maturity.

## 9. PAT / credential hygiene (binding)
Secret = Codespace secret **`GH_AIRFLOW`** (token never written to any file or memory).
Use per-command: `GH_TOKEN=$GH_AIRFLOW gh ...` and
`git push https://rajeluqman:${GH_AIRFLOW}@github.com/...`. NEVER `gh auth login --with-token`
(persists globally), NEVER `git push -u` with token-in-URL (embeds into `.git/config`). Both
slips happened before — see PROJECT_STATUS of pipeline_retrofit.
