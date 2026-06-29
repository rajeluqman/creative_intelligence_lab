# Sonnet Build Kickoff — Control-Plane Airflow Lab (Fasa 1)

> Paste the "PROMPT TO PASTE" block below into a **fresh Sonnet session inside the
> `airflow_dag_running_pipeline` workspace** (separate from CIL, owner's choice). Before pasting,
> copy `00_MASTER_SPEC.md` + `01_OPUS_DECISIONS.md` from CIL into the new repo at
> `architecture/control_plane_lab/` so Sonnet can read them locally.

## How to use (owner steps in the NEW airflow workspace)
1. Open a Codespace/workspace on `rajeluqman/airflow_dag_running_pipeline`.
   ⚠️ The repo is currently **EMPTY** (no commits on `main`, verified 2026-06-29). Sonnet's first
   act must be an initial commit to `main` (e.g. README + .gitignore) so the later
   `framework/fasa-1-scaffold` → PR(base=main) flow has a base to diff against.
2. Copy the **entire `architecture/control_plane_lab/` folder** from CIL into this repo at the
   same path. It is self-contained — it holds the 3 build-authority docs AND a `_source_to_port/`
   subfolder with the source files Sonnet must port (Sonnet CANNOT "port from CIL as-is" across a
   separate workspace, so they are bundled):
   - `_source_to_port/gen_repo_map.py`            → repo-map generator (adapt paths for this repo)
   - `_source_to_port/doc_reference_contract.py`  → doc-ref gate
   - `_source_to_port/sync_docs_to_confluence.py` → Confluence sync (gap #4 fix)
   - `_source_to_port/governance_guard.py`        → CIL's pre/post-edit hook — PORT as the starting
     point for deliverable #3 (adapt the governed-file map to `01_OPUS_DECISIONS §Governed-file
     map`); do not rewrite from scratch.

   Note: a 4th build-authority doc — `03_PIPELINE_SIDE_CONTRACT.md` — governs a SEPARATE, parallel
   task (adding the orchestration contract to the 5 pipeline repos), NOT the Fasa-1 control-plane
   scaffold below. Carry it in the folder; act on it per its own §6 sequencing, not as part of this
   prompt.
3. (No separate hunt needed — everything is in that one folder.)
4. Confirm the Codespace secret `GH_AIRFLOW` is assigned to this repo (it is — PAT verified ADMIN
   on all 5 repos 2026-06-29).
5. Paste the block below to Sonnet. Set model = Sonnet.

---

## PROMPT TO PASTE

You are Sonnet building **Fasa 1** of the Control-Plane Airflow Lab in this repo
(`airflow_dag_running_pipeline`). The full build authority is in
`architecture/control_plane_lab/00_MASTER_SPEC.md` and `01_OPUS_DECISIONS.md` — **read both
fully before writing anything**. Opus designed them; you build the scaffold; Opus reviews.

### Your scope = Fasa 1 ONLY: repo scaffold, NO cloud
Build the framework skeleton so all contracts pass locally. Do NOT provision any cloud, do NOT
write real DAG compute, do NOT clone the pipeline repos yet. Deliverables:

1. **CLAUDE.md** — ops-layer governance. This file is WHY CIL performs (token-thrift, no missing
   gaps, cheap resume) — port the full OPERATING ENVIRONMENT, not just the stop-gate. Enumerate
   these sections (content = ORCHESTRATION, not data):
   - **STOP-GATE** — ops version (saboteur-containment + env-promotion + cross-stack, not lineage).
   - **ANTI-SHORTCUT PROTOCOL** — verbatim discipline: read-before-touch, enumerate-don't-sample,
     reconcile-before-done (evidence per item), tag-assumptions. This is the "no missing gap" engine.
   - **Token Discipline** (port CIL's section): checkpoint-first (read PROJECT_STATUS before code),
     max ~3 files/turn, use Explore subagent for "where is X", update checkpoint before ending turn.
   - **Token-efficiency & session discipline** (ADR-010, ports CIL ADR-012): model routing
     (platform-architect/Opus only for the heavy orchestration calls; minor rulings →
     scope-guardian/Sonnet or a gate), gate-over-reread, context-bar checkpointing (red>75% =
     checkpoint + fresh session via the RESUME-HERE block).
   - **Conversational language** (ADR-009, ports CIL ADR-011): English default, Manglish opt-in.
   - **What NOT to commit** (`.env*`, `*.tfstate*`, connections secrets, logs) + **Intentionally
     committed** (CLAUDE.md, PROJECT_STATUS.md, learning logs — self-contained repo by design).
   Hook-backed (governance_guard.py).
2. **.claude/agents/** — the roster from `01_OPUS_DECISIONS.md §Agent roster`:
   platform-architect, scope-guardian, platform-engineer, sre-incident-commander, saboteur,
   finops-agent, cikgu. (data-quality-steward = part-time, optional file.)
3. **.claude/hooks/governance_guard.py** — protect the governed-file map in `01_OPUS_DECISIONS.md
   §Governed-file map`.
4. **airflow/dags/ trigger-STUB DAGs** (one per pipeline: cil, home_credit, olist, paysim, volve)
   — **REQUIRED in Fasa 1**, not Fasa 2, so the gates below have a real target (a contract with
   nothing to check is a dead gate). Each DAG = an operator placeholder + a connection reference
   ONLY: no SQL/PySpark body, no real job IDs yet (use clearly-marked `# TODO Fasa 2` stubs).
   `cross_stack_contract.py` must pass against these stubs.
5. **airflow/connections/ + secrets-backend abstraction** (gap fix — MWAA portability). DAGs/stubs
   read connection IDs from a single indirection layer (env-var → later swappable to a Secrets
   Manager backend), NEVER hardcoded creds. Add `architecture/SECRETS_BACKEND.md` documenting the
   one-config-swap path codespace→MWAA. This is the "baked-in day one" portability promise.
6. **tests/** contracts (the OPS gates — write real, runnable checks):
   - `cross_stack_contract.py` — DAGs are trigger-only: no SQL/PySpark transform body, no import
     of pipeline business logic. Run against the Fasa-1 stub DAGs (item 4).
   - `saboteur_containment_contract.py` — `simulation/faults/` references no prod credential;
     every fault declares blast-radius + has a reversible reset; staging-only.
   - `cost_guard.py` — every drill defines auto-teardown + per-stack budget ceiling.
   - `env_promotion_contract.py` — no direct prod edit; promotion requires staging-green + MTTR.
   - `doc_reference_contract.py` — port from the CIL copy (item 3 of How-to-use).
7. **scripts/gen_repo_map.py** + `architecture/REPO_MAP.md` (port from the CIL copy; adapt paths;
   run `--check` green).
8. **confluence/** (gap fix — owner values this highly) — port `scripts/sync_docs_to_confluence.py`
   from the CIL copy + a `confluence/00_START_HERE.md` landing page for THIS repo (what it is /
   what it orchestrates / how to run a drill). One Confluence space per repo was owner's original
   ask; this repo gets its own space.
9. **architecture/** — `CROSS_STACK_CONTRACT.md`, `REPO_REGISTRY.md` (5 pipelines + stack +
   compute target + operator), and `ADR/` with the 10 ADRs listed in `00_MASTER_SPEC §7`
   (draft each from the rationale already in the two spec docs — do NOT fabricate deliberation;
   tag anything inferred "(reconstructed — owner confirm)").
10. **learning/** — `CURRICULUM.md` (debug/troubleshoot/optimize/incident path, English-first,
    mental-model→debug→syntax-last per CIL's learning-style) + `LEARNING_LOG.md`.
11. **simulation/** skeleton — `ISOLATION_CONTRACT.md`, `check_isolation.py`, `faults/`
    (`inject.py`/`reset.py` stubs, staging-only, reversible), `runbooks/`, `MTTR_SCORECARD.md`.
    This is a LIVE-cloud range (unlike CIL's local sim) — but Fasa 1 = skeleton only, no live faults.
12. **observability/** — pointer doc for the log surfaces (CloudWatch/Databricks/Snowflake/Airflow)
    + Slack alert wiring stub.
13. **.gitignore** (gap fix — security) — must exclude `.env*`, `**/connections/*.env`,
    `*.tfstate*` + `.terraform/` (Terraform state holds secrets — Fasa 3), `__pycache__/`,
    `*.log`, and any local credential file. Add a no-`.env`-committed guard to ci.yml (item 14).
14. **.github/workflows/ci.yml** — static gates only, NO cloud secrets: ruff, py_compile, all
    contracts above, `gen_repo_map.py --check`, `check_isolation.py`, and a committed-secret guard.
15. **PROJECT_STATUS.md / COST_LOG.md / DECISION_LOG.md / INFRA_LIMITS_LOG.md / INTERVIEW_GUIDE.md**
    — scaffold with a "▶ RESUME HERE" block in PROJECT_STATUS.

### FIRST: seed the auto-memory (this is WHY CIL resumes cheap — don't skip)
The auto-memory (`~/.claude/projects/<workspace>/memory/` + `MEMORY.md` index) is harness-level and
**keyed per workspace** — this airflow workspace starts with an EMPTY memory, so CIL's "memory
betul, cache perform" benefit is LOST until you seed it. As your first action, write `MEMORY.md` +
these carried-over fact files into THIS workspace's memory (port the *content*, adapt names):
- `control-plane-airflow-lab` (this project — the 5 locked decisions + 4 Opus additions)
- `anti-shortcut-protocol`, `repo-map-navigation-gate`, `doc-reference-contract-tool`,
  `adr-addendum-parity`, `token-efficiency-operating-protocol`, `conversational-language-protocol`
- `learning-style-formula`, `direct-teaching-over-cikgu`, `cikgu-drill-feedback-research-and-visual`
- `retrofit-push-blocker-token-scope` (the PAT/credential-hygiene lessons)
Keep `MEMORY.md` as a one-line-per-fact index. After this, every session resumes from the
RESUME-HERE block + memory, not a cold re-read — that is the token-thrift you're replicating.

### Hard rules (binding — these are why the repo exists)
- **Port philosophy, not content.** Do NOT copy CIL's lineage/identity/Clean-ERD gates — this
  repo models no data. Anti-shortcut + repo-map + doc-ref port; the rest is new ops content.
- **DAGs are trigger-only.** Never put business logic in this repo. `cross_stack_contract.py`
  must enforce it and must be GREEN.
- **Saboteur containment is non-negotiable.** Even as a Fasa-1 skeleton, `faults/` must be
  structurally staging-only and the containment contract green.
- **Anti-shortcut protocol applies to YOU:** read-before-touch, enumerate-don't-sample,
  reconcile-before-done (restate scope as a checklist with `file:line` / command-output evidence
  per item — no evidence = say "unverified", not "done"), tag assumptions "(unverified)".
- **Credential hygiene:** if you ever push, use `GH_TOKEN=$GH_AIRFLOW gh ...` per-command and
  `git push https://rajeluqman:${GH_AIRFLOW}@github.com/...`. NEVER `gh auth login --with-token`,
  NEVER `git push -u` with token-in-URL. Token is in Codespace secret `GH_AIRFLOW` — never write
  it to any file or commit.

### Do NOT (scope discipline — @scope-guardian)
- Do NOT provision cloud, run Terraform, or create real Glue/Databricks jobs (that's Fasa 3+).
- Do NOT clone or copy any pipeline's business logic into this repo.
- Do NOT build a new pipeline. The 5 are the universe.
- Do NOT stand up MWAA.

### Definition of done (Fasa 1)
All contracts + `gen_repo_map.py --check` + `check_isolation.py` + ci.yml gates exit 0, verified
by running them directly (not by trusting your own build report). Then write the "▶ RESUME HERE"
block in PROJECT_STATUS.md and a numbered reconcile-checklist with per-item evidence.

Push flow (repo starts EMPTY — no `main` yet): (1) initial commit to `main` (README + .gitignore)
so a base exists; (2) build the scaffold on `framework/fasa-1-scaffold`; (3) open PR(base=main)
for Opus review. Use the credential-hygiene rules above for every push.

---

## Note to owner
Fasa 1 needs NO cloud and NO pipeline running — Sonnet builds the scaffold while you settle
home-credit end-to-end in parallel (Pilihan A, vertical slice). You meet at Fasa 2 (registering
home-credit's Glue job as the first real trigger DAG), which Opus designs after reviewing the
Fasa-1 PR.
