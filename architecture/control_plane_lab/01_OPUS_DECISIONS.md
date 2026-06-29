# Opus Decisions — Control-Plane Airflow Lab (signed-off ruling)

> Reads with `00_MASTER_SPEC.md`. This = Opus's locked rulings after the 2026-06-29 design
> session with owner. Build routed to Sonnet (Opus reviews), per ADR-012 model-routing.

## Owner-locked decisions (2026-06-29)
1. **Agent name `@saboteur`** — confirmed.
2. **Start stack = AWS/Glue** for Terraform + first drill (cheapest, most interview-relevant).
3. **TWO real cloud environments** — staging + prod, genuinely separate (project sits on 2 clouds).
4. **PAT** — taught; owner created Codespace secret `GH_AIRFLOW` (needs codespace rebuild to surface).
5. **Cost circuit-breaker = AGGRESSIVE** — auto-teardown after every drill, credits > convenience.

## Opus rulings
- **Port philosophy, not content.** CIL's lineage/identity/Clean-ERD gates are DROPPED here
  (this repo models no data). Anti-shortcut + repo-map + doc-ref are PORTED. New gates
  (cross-stack, saboteur-containment, cost-guard, env-promotion) are the ops-layer equivalents.
- **DAGs are trigger-only.** Enforced by `cross_stack_contract.py`. The single most important
  boundary: business logic NEVER enters this repo; it stays in each pipeline's own repo. This is
  what lets the repo orchestrate Databricks/Glue without violating any pipeline's own boundary.
- **Saboteur is the heart, containment is non-negotiable.** Live chaos on real cloud with real
  credits is only safe behind `saboteur_containment_contract.py`: staging-only, declared
  blast-radius, reversible reset, no prod credential reachable from `faults/`. CI-gated.
- **IaC + observability are NEEDS, not nice-to-haves.** Without Terraform there is no cheap
  teardown (credit protection) and no staging≈prod parity. Without observability there is no
  debugging — the entire teaching purpose collapses.
- **MWAA only on-demand.** MWAA bills per-hour always-on (~$350/mo), NOT per-run. Keep Airflow
  in codespace (~$0); stand MWAA up only to capture a showcase run, then tear down.

## Agent roster (differs from CIL — ops-focused)
| Agent | Role | Origin |
|---|---|---|
| @platform-architect (Opus, ULTIMATE VETO) | orchestration + cross-stack design | replaces data-architect |
| @scope-guardian (hard veto) | block creep (esp. "build a new pipeline here") | ported |
| @platform-engineer (Sonnet) | build DAGs, debug, port scripts to Glue/Databricks | replaces SDE |
| @sre-incident-commander (Sonnet) | lead incident drills, runbooks, MTTR | NEW |
| @saboteur (Sonnet, adversarial) | inject live faults within blast-radius | NEW |
| @finops-agent (Sonnet, elevated) | cost circuit-breaker, auto-teardown, credit watch | ported+elevated |
| @cikgu (Sonnet) | teach (English-first, mental-model→debug→syntax-last) | ported |

DROPPED from CIL: data-architect (Clean-ERD doctrine n/a). data-quality-steward = part-time only
(matters for "did the fix produce correct output", not a standing seat).

## REJECTED (scope discipline — @scope-guardian)
- Copying any pipeline's business logic into this repo. Logic stays in its own repo; this repo
  orchestrates + teaches ONLY.
- Building NEW pipelines here. The 5 are the universe.
- Power BI / serving veneers / vector DB / RAG. Not the debug/ops focus.
- Porting CIL's lineage/identity/Clean-ERD contracts. Wrong domain.
- Standing always-on MWAA. Per-hour burn with no per-run benefit for an occasional-run lab.

## Governed-file map (governance_guard.py targets)
| Protects | Why |
|---|---|
| airflow/dags/*.py | DAG must stay trigger-only (paired with cross_stack_contract) |
| simulation/faults/* | saboteur blast-radius — containment-critical |
| infra/terraform/prod/* | prod env — no edit without env-promotion gate |
| architecture/ADR/, CROSS_STACK_CONTRACT.md | orchestration doctrine |
| tests/*_contract.py, cost_guard.py | the gates themselves |

## Routing
Authoring = Sonnet (mechanical scaffold, per ADR-012). Opus reviews each Fasa. Kickoff doc to
follow once owner approves this spec: `02_SONNET_BUILD_KICKOFF.md`.
