# Runbook

> **Audience: support & ops** (in this solo project, that's still the owner — but written as if
> someone else has to do this at 2am without you). How to rerun the pipeline on failure, and the
> real failures that have actually happened during build. Every entry below cites a real
> `file:line` and a real fix that was actually applied and verified — none of this is invented.
> Source: `PROJECT_STATUS.md`'s dated checkpoints. **Status: real content as of 2026-06-27** — was
> a deliberate stub until both gates cleared: (1) v1 serving live (Snowflake + DuckDB VSS, both
> proven for real) and (2) ≥1 real rerun-after-failure had actually happened. Both are true now.

## General rerun safety
The whole pipeline is **idempotent / skip-existing by design** — re-triggering after a failure is
always safe, never duplicates work:
- `list_unextracted_assets.py` only returns assets missing a Bronze row — re-running
  `dags/creative_intel_pipeline.py` after a fix re-imports the fixed module and continues the same
  DagRun, no manual `clear` needed (proven 2026-06-27, see "DAG fails on `.env` lines with inline
  comments" below).
- `dbt build` is itself idempotent (`external` materialization overwrites, doesn't append).
- Gemini extraction is content-hash-gated — re-running never re-pays for an already-extracted asset.

## Symptom: Airflow UI / DAG not reachable at all
**Possible causes:** the `airflow standalone` background process died with the container/session
(it does not survive a restart automatically).
**Resolution:**
1. Check for a live process: `ps aux | grep airflow`.
2. Restart with `AIRFLOW_HOME` **explicitly set**:
   `AIRFLOW_HOME=/workspaces/creative_intelligence_lab/airflow_home airflow standalone`. Without
   it, Airflow silently defaults to `~/airflow` (an empty instance) and
   `creative_intel_pipeline_v1` won't appear — hit for real 2026-06-27.
3. `source venv_airflow/bin/activate` **before** running `airflow standalone`, not just
   `venv_airflow/bin/airflow standalone` — `standalone_command.py` spawns webserver/scheduler/
   triggerer as subprocesses by bare command name, so without activation every subprocess fails
   `FileNotFoundError: 'airflow'` even though the top-level process starts fine. Hit for real
   2026-06-27.
4. Confirm clean: `airflow dags list-import-errors` → should be empty.
5. Login: `admin` / see `airflow_home/standalone_admin_password.txt` (persists across restarts —
   only the dags-folder path has been lost between sessions, not the user DB).

## Symptom: `sync_drive_to_landing` task fails with a `FileNotFoundError` whose path has trailing junk
**Example real error:** `FileNotFoundError: 'secrets/gdrive-service-account.json   # path to
service-account JSON, NOT the JSON itself'`.
**Root cause:** `dags/creative_intel_pipeline.py`'s hand-rolled `_load_dotenv()` only skipped lines
*starting* with `#`, not inline `# comment` suffixes after a value — bash's `source .env` strips
those, so the gap was invisible until a non-bash parser hit it. **Fixed 2026-06-27** (strip on
`r"\s+#"` after `=`) — if you see this exact shape of error on a current checkout, you're on an old
commit; pull `main`.
**Resolution if it recurs on a *new* `.env` line:** check for any inline `# comment` after a value
that isn't being stripped — the regex fix only handles the standard `KEY=value  # comment` shape.
**Verified:** the 3rd retry on the same DagRun (no manual clear) succeeded post-fix — re-triggering
after a code fix just works, per "General rerun safety" above.

## Symptom: a script exits immediately with `missing required env var(s): ... - refusing to run`
**Root cause:** this is **not a bug** — it's `scripts/env_guard.py`'s intentional fail-closed
behavior (every script that touches S3/Snowflake/Gemini calls `assert_safe()` first). Real
examples hit during build: `S3_BUCKET unset` (fresh shell after `source venv/bin/activate` alone
— activating the venv does **not** load `.env`), `SNOWFLAKE_PASSWORD` unset before a `--apply`.
**Resolution:** `set -a && source .env && set +a` before running any pipeline script in a fresh
shell — there is no `python-dotenv` call anywhere in these scripts by design (explicit over
implicit for anything that can spend money or write to a shared cloud account).

## Symptom: Gemini extraction fails/stops with a 429 or quota error
**Two different quotas behave differently — check which one you hit:**
- `generate_content_free_tier_requests` (chunk extraction) is confirmed **HARD-DAILY** (20/day for
  `gemini-2.5-flash`) — backoff-retry does not help. **Resolution:** wait for the daily reset, then
  re-run the exact same command. Confirmed 2026-06-22→2026-06-24: zero code changes needed, the
  remaining assets picked up cleanly (content-hash-gated idempotency).
- `embed_content_free_tier_requests` (embeddings) recovers with backoff — `scripts/
  generate_embeddings.py` already retries on 429 using the API's own `retryDelay`, batched at
  `BATCH_SIZE=20`. **Resolution:** just re-run; cached/already-embedded chunks cost zero API calls.

## Symptom: Snowflake provisioning/refresh/reconciliation script fails or you need to re-run it
**Scripts:** `scripts/provision_snowflake_serving.py` (phases: `account`, `storage`, `tables`,
`search`, `refresh`) and `tests/reconcile_snowflake_serving.py`.
**Resolution:**
1. Always dry-run first (no `--apply` flag) — prints the exact SQL plan, no connection, no
   credentials needed. Compare against what you expect before spending a real `--apply`.
2. `--apply` is owner-gated by design (ADR-005) — every statement is `IF NOT EXISTS`/idempotent,
   so a re-run against existing objects is a safe no-op, not an error.
3. After any `dbt_build_marts` run where `SERVING_BACKEND=snowflake_cortex`: run
   `--phase refresh --apply` (8× `ALTER EXTERNAL TABLE ... REFRESH` + a view resync), then
   `python tests/reconcile_snowflake_serving.py`. A reconciliation mismatch means Snowflake and
   Gold S3 have diverged — **stop and investigate before trusting any Snowflake read**; this is the
   live trip-wire for ADR-005's "Gold S3 is the sole source of truth" rule, not a flaky test to retry.
   Real run, 2026-06-27: exact match on all 8 models (`fact_chunk` 169/169, etc.) — that's the
   expected, healthy result.

## Symptom: CI's `real-build` job fails on a `Catalog Error: Table ... does not exist`
**Example real error:** `Catalog Error: Table with name edit_decision_list does not exist!` on
`dbt build -s +marts.core`.
**Root cause:** the `+marts.core` node selector doesn't pull in `marts.performance`-lineage seeds,
but a singular test referenced one by raw table name instead of `ref()`/`source()`, so dbt couldn't
scope it out — only surfaced on CI's fresh ephemeral catalog (local dev's persistent
`target/dev.duckdb` already had the seed loaded). **Fixed 2026-06-27**: `.github/workflows/ci.yml`
now runs `dbt seed` (all 5, unscoped) before `dbt build -s +marts.core` in the `real-build` job.
**Resolution if a similar gap recurs:** reproduce locally first — delete `target/dev.duckdb`, run
`dbt seed` then the exact failing `dbt build` selector — before pushing a fix.

## Escalation
No real production incident has occurred yet (see **Incident Postmortem**) — every entry above was
caught and fixed *during build*, not in live operation. If something fails that isn't covered here,
that's the seed for a new entry: cite the real symptom, root cause, and fix, the same convention
every entry above follows. Routes to @senior-data-engineer (pipeline/DAG/scripts) or
@data-architect (model/lineage defect).
