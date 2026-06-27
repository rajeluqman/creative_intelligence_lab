# ADR-008 — Airflow orchestration: isolated venv + cross-venv script invocation

- **Status:** Accepted
- **Date:** 2026-06-25
- **Deciders:** @senior-data-engineer (build), owner (sign-off to install Airflow + wire stub tasks)
- **Context refs:** `DATA_MODEL.md` §8, `STACK_AND_FLOW.md` §2 (the high-level orchestration
  pattern — local Airflow, `gemini_api` Pool, dynamic task mapping, skip-existing, deferrable
  wait — was already ratified there); `dags/creative_intel_pipeline.py` (was: parse-clean TODO
  stubs; now: wired to real scripts).
- **Does NOT touch:** ADR-001 (DuckDB engine choice), ADR-002/003 (model grain), ADR-004/005
  (perf/storage/serving), ADR-006/007 (tenancy/landing-TTL). This is purely an
  orchestration-layer implementation decision — no Gold/marts model changes.

## Context

`DATA_MODEL.md` §8 / `STACK_AND_FLOW.md` §2 already ratified the *pattern* (Pool-capped Gemini
concurrency, dynamic task mapping, skip-existing short-circuit, deferrable wait instead of a
synchronous polling loop). Until 2026-06-25 the DAG was parse-clean but every task body was a
TODO stub — `python -c "DagBag(...).import_errors"` passed, but triggering the DAG did nothing
real. Two concrete implementation questions were left open by the ratified pattern, and had to
be answered before any real wiring could happen:

1. Airflow's own dependency set is strict-pinned (a constraint file per Python/Airflow version)
   and would very likely conflict with the real pipeline's deps (`google-genai`, `boto3`,
   `dbt-duckdb`, `scipy`) if installed into the same venv.
2. The TODO bodies for `ge_validate` and `refresh_serving` referenced infrastructure that
   doesn't exist yet (a literal Great Expectations checkpoint runner; a DuckDB VSS / Snowflake
   Cortex refresh) — wiring them "for real" required deciding what they honestly do *today*
   versus what they will do once those pieces exist.

## Decision

**A — Airflow installs into its own isolated `venv_airflow/`, never the shared `venv/`.** Task
bodies that need the real pipeline scripts shell out via
`subprocess.run([venv/bin/python, script, ...])` rather than importing those modules into
Airflow's own process. A small `_load_dotenv()` helper in the DAG file feeds `.env` into the
subprocess env (mirrors the `set -a && source .env` gap `PROJECT_STATUS.md` named on
2026-06-24 for manual runs — `source venv/bin/activate` alone does not export it).

**B — `ge_validate` runs the two real, already-existing governance contracts**
(`tests/lineage_contract.py`, `tests/boundary_contract.py`) — not a literal Great Expectations
checkpoint, which doesn't exist yet (named OPEN gap, `tests/GATES.md`). The task's own
docstring says so explicitly; it does not claim to be more than it is.

**C — `refresh_serving` is an honest no-op for both `SERVING_BACKEND` values today.**
`duckdb_vss`: no embedding/VSS pipeline is built yet (`SPEC_v1_search.md` §1 rules vector
search OUT of v1 — v1.5 fast-follow). `snowflake_cortex`: ADR-005's FinOps preconditions
(COST_LOG + day-25 teardown + $0 fallback proven + single-sourced embeddings) are unmet.
Neither branch fabricates a call to infrastructure that isn't real.

**D — `scripts/list_unextracted_assets.py` (new)** fills the `list_new_assets` task's named
TODO ("query `bronze_asset_raw` by content hash per `client_id`") — reads the manifest seed,
lists real S3 Bronze keys via `boto3`, diffs the two sets. Read-only; no write path.

## Rationale

1. Isolation over a shared venv is the cheapest correct fix: it costs one extra `pip install`
   into a second venv, and in exchange the already-verified-for-real pipeline scripts'
   dependency set can never regress because someone installed Airflow.
2. Subprocess invocation over direct import is the natural consequence of (A) — it is also
   exactly the same boundary `dbt_build_marts`'s `BashOperator` already crossed (shelling out
   to `dbt build`), just generalized to the Python scripts too. No new pattern invented.
3. Honest no-op over a fabricated call (B, C): CLAUDE.md's ANTI-SHORTCUT PROTOCOL
   ("reconcile-before-done... no evidence = say unverified, not done") applies as much to
   orchestration code as to a chat response — a task that returns `"ge ok"` without running
   anything real is exactly the kind of silent gap this project's governance exists to prevent.

## Rejected alternatives

1. **Install Airflow into the shared `venv/`.** Rejected: Airflow's pinned-constraint
   dependency set is a known source of conflicts; risks regressing the real scripts' own
   already-verified dependency versions for no benefit.
2. **Import the real scripts' functions directly into the DAG module.** Rejected: would
   require installing `google-genai`/`boto3`/`dbt-duckdb`/`scipy` into `venv_airflow` too,
   defeating the isolation in (1) by the back door.
3. **Wire `ge_validate`/`refresh_serving` to placeholder success strings** (`"ge ok"` /
   `"serving refreshed"`) as the original stubs did. Rejected: indistinguishable from a real
   pass in the Airflow UI/logs — a silent gap, not a documented one.

## Consequences

- **Positive:** the DAG now runs for real end-to-end (verified 2026-06-25, see
  `PROJECT_STATUS.md`) — cost firewall #2 (skip-existing on already-extracted assets) proven
  via a live `AirflowSkipException` path, not just claimed; zero risk to the real scripts'
  dependencies from installing Airflow.
- **Negative / accepted:** two venvs to maintain (`venv/`, `venv_airflow/`); `ge_validate` /
  `refresh_serving` remain partial until the GE-checkpoint and VSS/Cortex gaps they depend on
  are closed (tracked in `tests/GATES.md` "Open", not silently dropped here).
- **Bounded:** this ADR does **not** authorize literal GE checkpoint execution or VSS/Cortex
  wiring — those remain separate, named, future ADRs/work items, not retroactively claimed done
  by this one.
