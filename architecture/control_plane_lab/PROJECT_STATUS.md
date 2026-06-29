# Control-Plane Airflow Lab — PROJECT STATUS (resume-safe checkpoint)

> Fasa-0 design lives HERE in CIL (`architecture/control_plane_lab/`); the BUILD happens in the
> separate `airflow_dag_running_pipeline` workspace (Sonnet). Read this block first, not the whole
> spec. Memory: [[control-plane-airflow-lab]].

## ▶ RESUME HERE (next session — read THIS first)
**Status: Fasa 0 (Opus design) COMPLETE. Awaiting owner to (a) commit/carry the folder to the
airflow workspace + run the Sonnet kickoff, and (b) continue open design questions with Opus here.**
Owner said 2026-06-29: "banyak lagi nak tanya dkt session lain" — so the next CIL/Opus session is
MORE DESIGN Q&A, not build.

**Paste-ready first prompt for next session (Opus, CIL workspace):**
`Read architecture/control_plane_lab/PROJECT_STATUS.md "▶ RESUME HERE" + 00_MASTER_SPEC + 01_OPUS_DECISIONS. Fasa-0 design of the control-plane Airflow lab (repo airflow_dag_running_pipeline) is done — 3 spec docs + _source_to_port/ bundled, 5 decisions locked, Sonnet kickoff ready. I have more design questions before building. Do NOT rebuild the spec; answer my questions and amend the spec if needed (hunt gaps first — I keep finding them).`

## What is DONE (Fasa 0)
- `00_MASTER_SPEC.md` — full build contract (3-in-1 repo: control-plane + teaching lab + live-chaos
  range; port-philosophy-not-content; OPS gates; skeleton; 10 ADRs; 6 fasa; PAT hygiene).
- `01_OPUS_DECISIONS.md` — 5 locked decisions + ops-focused agent roster + REJECTED list + governed-file map.
- `02_SONNET_BUILD_KICKOFF.md` — paste-ready Sonnet prompt, 15 Fasa-1 deliverables + memory-seeding step.
- `_source_to_port/` — gen_repo_map.py, doc_reference_contract.py, sync_docs_to_confluence.py
  (bundled so the airflow workspace can port them — it has no CIL access).

## Locked decisions (2026-06-29)
1. agent `@saboteur` · 2. start stack AWS/Glue · 3. TWO real cloud envs (staging+prod) ·
4. PAT done — Codespace secret `GH_AIRFLOW` (classic, ADMIN on all 5 repos, verified) ·
5. cost circuit-breaker AGGRESSIVE (auto-teardown).

## Opus's 4 additions beyond owner's prompt
A. Saboteur-Containment Contract (staging-only) · B. Cost circuit-breaker + auto-teardown ·
C. Terraform IaC (parity + teardown + rebuild) · D. Observability (can't debug blind).

## Gaps found + closed this session (anti-shortcut — owner kept catching them)
Empty-repo PR flow · port-from-CIL impossible cross-workspace (→ _source_to_port/ bundle) ·
contract-with-no-target (→ stub DAGs REQUIRED in Fasa 1) · Confluence missing · .gitignore/tfstate
hygiene · secrets-backend abstraction · Token-Discipline operating section · MEMORY+cache seeding ·
commit-policy sections. All folded into the 3 docs.

## Workflow decided (Pilihan A — vertical slice)
Owner settles home-credit end-to-end → Confluence → port compute to AWS Glue, FIRST (one pipeline
all the way through the chain), while Sonnet builds the control-plane scaffold (Fasa 1) in parallel.
Meet at Fasa 2 = register home-credit's Glue job as the first real trigger DAG.

## NOT yet done / open
- Folder NOT committed to git yet (untracked `??`) — owner deciding whether to commit so it's
  pullable into the airflow workspace.
- Sonnet Fasa-1 build NOT started (happens in the airflow workspace).
- Owner has MORE design questions (next session).
- Cost-ceiling numbers per stack: undefined (owner to supply when cloud comes, Fasa 3).
