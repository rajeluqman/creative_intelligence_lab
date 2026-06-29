# Pipeline-Side Orchestration Contract (Fasa 0, Opus)

> Closes the reciprocal gap in the control-plane plan: `00_MASTER_SPEC` / `01_OPUS_DECISIONS` /
> `02_SONNET_BUILD_KICKOFF` fully specify the **control-plane** repo, but say nothing about what
> each of the **5 pipeline repos** must carry so the Claude working inside them knows it is being
> orchestrated. This doc fixes that. Owner-requested 2026-06-29.
>
> **Problem this solves:** auto-memory is keyed per-workspace and does NOT travel with a repo.
> When the owner enters the `home-credit` (or olist/paysim/volve) codespace, that workspace's
> memory is EMPTY — the only knowledge that survives is what is **committed in the repo**. So the
> transfer mechanism is **CLAUDE.md** (auto-loaded every session, travels with git), NOT memory.

## 1. The boundary this contract must NOT break
The control-plane repo enforces **DAGs are trigger-only** (`cross_stack_contract.py`). The mirror
rule on the pipeline side: **a pipeline repo must NOT import, vendor, or know the internals of the
Airflow control-plane.** It only needs to know the *interface*: "something external triggers a
named job in my compute stack." Keep the coupling to an interface, never to control-plane code.

```
control-plane repo  ──trigger(job_handle, via connection_id)──▶  pipeline repo's cloud job
   (logic: NONE)                                                    (logic: ALL lives here)
        │                                                                  │
   REPO_REGISTRY.md  ◀───────── single source of truth ─────────▶  CLAUDE.md §Orchestration
   (full cross-repo map)            (pointers both ways)            (short, points back to registry)
```

## 2. Source of truth = ONE file (anti-drift)
The full cross-repo map lives in **exactly one place**: `architecture/REPO_REGISTRY.md` in the
**control-plane** repo (Fasa-1 deliverable #9). Every pipeline repo only carries a **pointer** back
to it plus its own row. Do not duplicate the full table into each pipeline repo — that drifts.

## 3. What Sonnet adds to EACH of the 5 pipeline repos
Two artifacts per repo. Both committed (so they travel; memory does not).

### 3a. A `## Orchestration Contract` section appended to that repo's `CLAUDE.md`
Short and per-repo. Template (fill the bracketed values from the table in §4):

```markdown
## Orchestration Contract (control-plane integration)
This pipeline is orchestrated by an EXTERNAL control-plane: `rajeluqman/airflow_dag_running_pipeline`.
- **This repo owns ALL business logic.** The control-plane only *triggers* it — it holds no logic.
  Do NOT move transforms, SQL, or PySpark into the control-plane repo, and do NOT import or
  reference control-plane code here. The only contract is the trigger interface below.
- **Compute target:** [<AWS Glue (PySpark) | Azure Databricks | DuckDB→Snowflake>]
- **Trigger handle the control-plane references:** [<Glue job name | Databricks job id | bash entry>]
  — exposed via a **connection id**, never hardcoded creds. Owner/CI sets the real value.
- **Airflow operator used against me:** [<GlueJobOperator | DatabricksRunNowOperator | bash>]
- **Full cross-repo map (source of truth):** `architecture/REPO_REGISTRY.md` in the control-plane
  repo. This section is a pointer; the registry is authoritative.
- **Secrets:** connection ids resolve through a secrets-backend abstraction (env-var locally →
  Secrets Manager in cloud). Never commit a credential or job ARN to this repo.
```

### 3b. A `architecture/ORCHESTRATION_CONTRACT.md` in that repo (the detail)
One page: the diagram from §1, this repo's row from §4, what "triggerable job" means concretely for
this stack (e.g. Glue job name + expected args), and the no-creds-committed rule. Links back to the
control-plane `REPO_REGISTRY.md`. This is the file a fresh Claude reads to stop being "blur".

## 4. Per-repo values (Sonnet fills the templates from this — authoritative source = REPO_REGISTRY)
| Pipeline repo | Compute target | Airflow operator | Trigger handle (Fasa 2+, stub for now) |
|---|---|---|---|
| home-credit | AWS Glue (PySpark) | `GlueJobOperator` | Glue job name — `# TODO Fasa 2` |
| olist | Azure Databricks (ADLS) | `DatabricksRunNowOperator` | Databricks job id — `# TODO Fasa 2` |
| paysim | Databricks SQL / PySpark+Delta | `DatabricksRunNowOperator` | Databricks job id — `# TODO Fasa 2` |
| Volve | Databricks + MLflow | `DatabricksSubmitRunOperator` | Databricks job/run — `# TODO Fasa 2` |
| CIL (this repo) | DuckDB→Snowflake | bash/python trigger + `DbtCloudRunJobOperator` | bash entrypoint — `# TODO Fasa 2` |

> Values mirror `00_MASTER_SPEC §4`. If these two ever disagree, MASTER_SPEC §4 / REPO_REGISTRY win;
> fix this table to match (anti-drift — one source of truth).

## 5. Memory is a CACHE, not the transfer (binding mental model)
Per workspace, the auto-memory starts empty and does NOT ship with the repo. So:
- **Knowledge that MUST survive a fresh workspace → CLAUDE.md (§3a) + ORCHESTRATION_CONTRACT.md.**
  These are the durable transfer. They are committed; they auto-load; they cannot go stale silently.
- **Memory seeding is optional speed, not correctness.** When the owner opens a pipeline workspace
  and wants cheap resume, seed a single `orchestrated-by-control-plane` memory fact pointing at the
  two committed files. But never rely on memory to carry the contract — the committed files are the
  contract. (Same lesson as the control-plane kickoff: a new workspace = empty memory.)

## 6. How Sonnet applies this (sequencing — does NOT block control-plane Fasa 1)
This is a **separate, parallel task** from the control-plane scaffold. Two valid orders:
1. **After** control-plane Fasa 1, so `REPO_REGISTRY.md` already exists to point at (preferred — the
   pointer in §3a resolves to a real file). OR
2. Now, with the §4 table as the interim authority and a `(REPO_REGISTRY — to land Fasa 1)` note.

Per pipeline repo, the steps are mechanical:
1. Read that repo's existing `CLAUDE.md` THIS turn (read-before-touch) — append §3a, do not rewrite.
2. Add `architecture/ORCHESTRATION_CONTRACT.md` (§3b) with that repo's row.
3. Commit on a `framework/orchestration-contract` branch → PR(base=main). One PR per repo.
4. **Enumerate, don't sample:** all **5** repos get it. Re-count after: 5 CLAUDE.md sections + 5
   ORCHESTRATION_CONTRACT.md = 10 artifacts. N_before = N_after = 5 repos.

## 7. Credential hygiene (binding — applies to all 5 repos)
The PAT `GH_AIRFLOW` (Codespace secret, classic, ADMIN on all 5 repos, verified 2026-06-29) is what
makes pushing to the 4 external repos possible at all (previously blocked — the default token is
CIL-scoped). For every push:
- `GH_TOKEN=$GH_AIRFLOW gh ...` per-command, and
  `git push https://rajeluqman:${GH_AIRFLOW}@github.com/rajeluqman/<repo>.git <branch>`
- **NEVER** `gh auth login --with-token` (persists globally), **NEVER** `git push -u` with
  token-in-URL (embeds into `.git/config`). Token is never written to any file, commit, or memory.

## 8. Definition of done (this contract)
- All **5** pipeline repos carry the §3a CLAUDE.md section + §3b ORCHESTRATION_CONTRACT.md, verified
  by reading each committed file (not by trusting the build report).
- Each points back to control-plane `REPO_REGISTRY.md`; the §4 values match MASTER_SPEC §4.
- No credential, job ARN, or `.env` committed to any of the 5 repos (grep-verified).
- Reconcile checklist with per-repo `file:line` evidence; anything unverified marked "(unverified)".
