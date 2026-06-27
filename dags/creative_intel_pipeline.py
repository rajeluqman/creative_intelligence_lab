"""Creative Intelligence pipeline DAG (local Airflow).

Demonstrates the orchestration patterns ratified in DATA_MODEL.md §8 / STACK_AND_FLOW.md §2,
without a synchronous per-video polling loop that would pin worker slots:

  * parameterized run     -> client_id + drive_folder_id (ad-hoc video OR new-client onboard)
  * Drive -> Landing sync  -> content-hash, skip-existing on the way in (the $-firewall, step 1)
  * dynamic task mapping  -> one mapped `extract_chunks` task per NEW asset (`.expand()`)
  * gemini_api Pool       -> caps concurrency to the QPM budget (the rate-limit guard)
  * retries + backoff     -> exponential backoff + jitter on 429
  * skip-existing         -> AirflowSkipException when no new assets (cost firewall, step 2)
  * deferrable async wait -> TimeDeltaSensorAsync frees the worker slot while Gemini processes
  * serving refresh        -> refresh the read-only veneer over the fresh Gold S3 (ADR-005)

Run model: manual trigger with config (recommended) — e.g.
  airflow dags trigger creative_intel_pipeline_v1 \
    --conf '{"client_id": "voltecx", "drive_folder_id": ""}'
Or set `schedule="@daily"` to poll while Airflow is up (Codespace = on-demand, not 24/7).

ADR-008 (2026-06-25, architecture/ADR-008-airflow-orchestration-wiring.md): this DAG runs in
its OWN isolated `venv_airflow/` (Airflow's dependency set
is notoriously strict-pinned and would otherwise collide with `venv/`'s google-genai/boto3/
dbt-duckdb/scipy stack). Task bodies below therefore shell out to `venv/bin/python <script>`
rather than importing the real scripts directly — Airflow's process never imports boto3 or
google-genai, it only invokes the already-verified-for-real CLI scripts as subprocesses. This
keeps the two dependency sets fully isolated and means wiring this DAG could never regress the
real, already-tested pipeline scripts' own dependencies.

Bodies are now wired to the real scripts (was: TODO stubs). `ge_validate` remains an honest
partial-no-op (a literal GE checkpoint doesn't exist yet — tests/GATES.md "Open" section).
`refresh_serving` is real for `SERVING_BACKEND=snowflake_cortex` (ADR-005 Addendum 2026-06-27
#5) and stays an honest no-op for the default `duckdb_vss` backend, which has no separate index
file to refresh. This DAG does not fabricate behavior for unbuilt gates.
Verify: `python -c "from airflow.models import DagBag; \
assert not DagBag('dags').import_errors, DagBag('dags').import_errors"`.

ADR-009 (2026-06-25, architecture/ADR-009-slack-alerts-and-confluence-doc-sync.md): any task
failure posts to Slack via `_notify_slack_failure` (DAG-level `on_failure_callback`, fires for
every task automatically). Uses stdlib `urllib.request` only — `venv_airflow` stays dependency-
minimal per ADR-008. Missing/empty `SLACK_WEBHOOK_URL` is a graceful no-op (logs a warning),
never a second failure stacked on the real one.
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import urllib.request
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.sensors.time_delta import TimeDeltaSensorAsync

log = logging.getLogger(__name__)

GEMINI_POOL = "gemini_api"  # create in Airflow: `airflow pools set gemini_api <QPM_budget> "..."`

REPO_DIR = Path(__file__).resolve().parent.parent
VENV_PYTHON = str(REPO_DIR / "venv" / "bin" / "python")


def _load_dotenv() -> dict[str, str]:
    """Minimal `.env` parser for the subprocess env below — intentionally not a new
    `python-dotenv` dependency (none of the real scripts use one either; PROJECT_STATUS.md's
    2026-06-24 entry already named this exact gap: `source venv/bin/activate` alone does not
    load `.env`). Airflow's own process never needs these vars; only the subprocess calls into
    `venv/`'s real scripts do."""
    env_path = REPO_DIR / ".env"
    values: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            # bash's `source .env` (the documented manual-run path, e.g. `set -a && source .env`)
            # treats an unquoted ' #' mid-line as a comment start too — .env/.env.example rely on
            # that (`GOOGLE_APPLICATION_CREDENTIALS=path   # explanation`). Found live 2026-06-27:
            # without this, this hand-rolled parser fed the literal " # explanation" suffix into
            # the subprocess env, and `service_account.Credentials.from_service_account_file`
            # FileNotFoundError'd on the resulting bogus path.
            val = re.split(r"\s+#", val.strip(), maxsplit=1)[0].strip()
            values[key.strip()] = val
    return values


def _run_real_script(args: list[str], extra_env: dict[str, str] | None = None) -> str:
    """Cross-venv invocation (see module ADR-addendum note above): shells out to
    `venv/bin/python` rather than importing — Airflow's `venv_airflow` never needs boto3/
    google-genai/dbt-duckdb, and the real scripts never need Airflow's deps."""
    env = {**os.environ, **_load_dotenv(), **(extra_env or {})}
    result = subprocess.run(
        [VENV_PYTHON, *args], cwd=str(REPO_DIR), env=env, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{args[0]} failed (exit {result.returncode}):\nSTDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    return result.stdout


def _notify_slack_failure(context: dict) -> None:
    """ADR-009 on_failure_callback — fires for ANY task failure in this DAG (wired via
    default_args below, not per-task, so a future 6th task is covered automatically).

    Graceful no-op if SLACK_WEBHOOK_URL is unset/empty (credentials filled in later, per the
    owner) — alerting being unconfigured must never raise a second failure on top of the real
    one. Uses stdlib urllib only: this runs in venv_airflow, kept dependency-minimal (ADR-008)."""
    webhook = _load_dotenv().get("SLACK_WEBHOOK_URL") or os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook:
        log.warning("SLACK_WEBHOOK_URL not set — skipping Slack alert (credentials not filled in yet)")
        return

    ti = context["task_instance"]
    text = (
        f":red_circle: *Airflow task failed*\n"
        f"*DAG:* `{ti.dag_id}`  *Task:* `{ti.task_id}`\n"
        f"*Run:* `{context['run_id']}`\n"
        f"*Client:* `{context['params'].get('client_id', '?')}`\n"
        f"<{ti.log_url}|View logs>"
    )
    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info("Slack alert sent (status %s)", resp.status)
    except Exception as e:  # noqa: BLE001 — alerting must never raise into the task's own failure handling
        log.warning("Slack alert failed to send: %s", e)


@dag(
    dag_id="creative_intel_pipeline_v1",
    schedule=None,  # manual trigger w/ conf; set "@daily" to poll while Airflow is up
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    params={
        # The two "new data" entry points: ad-hoc video (existing client) + new-client onboard.
        # No real-client default: must be supplied per run via --conf (multi-client misroute
        # guard). Empty → sync_drive_to_landing raises ValueError before any S3 write.
        "client_id": Param("", type="string", minLength=1, description="client partition under landing/ (REQUIRED, must match seeds/dim_client.csv)"),
        "drive_folder_id": Param(
            "", type="string", description="Google Drive folder id to sync (blank = re-scan existing)"
        ),
    },
    default_args={
        "retries": 3,
        "retry_delay": timedelta(seconds=30),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(minutes=10),
        "on_failure_callback": _notify_slack_failure,  # ADR-009
    },
    tags=["creative-intelligence", "v1"],
)
def creative_intel_pipeline():
    @task
    def sync_drive_to_landing(**context) -> int:
        """Step 1 — Drive -> S3 landing. SHA-256 content-hash naming, skip-existing (idempotent).

        The first cost firewall: a re-delivered / near-duplicate video hashes to the same
        asset_id and is NOT re-uploaded. Returns the count of NEW videos landed."""
        params = context["params"]
        client_id, folder = params["client_id"], params["drive_folder_id"]
        if not client_id:
            raise ValueError("client_id param is required — multi-client misroute guard")
        out = _run_real_script(
            ["scripts/ingest_drive_to_s3.py"],
            extra_env={"CLIENT_ID": client_id, "DRIVE_FOLDER_ID": folder},
        )
        print(out)
        m = re.search(r"landed (\d+) new", out)
        return int(m.group(1)) if m else 0

    @task
    def list_new_assets(**context) -> list[str]:
        """Step 2 — return only asset_ids in landing whose Bronze JSON does NOT yet exist.

        The second cost firewall — never re-call Gemini on an already-extracted asset.
        Real query (was: hardcoded DEMO_ASSET_IDS stub) via scripts/list_unextracted_assets.py
        — manifest seed minus real S3 bronze_asset_raw keys for this client_id."""
        client_id = context["params"]["client_id"]
        out = _run_real_script(
            ["scripts/list_unextracted_assets.py", client_id],
            extra_env={"CLIENT_ID": client_id},
        )
        new = [line.strip() for line in out.splitlines() if line.strip()]
        if not new:
            raise AirflowSkipException("no new assets — nothing to extract")
        return new

    @task(pool=GEMINI_POOL, retries=5)
    def extract_chunks(asset_id: str, **context) -> str:
        """One Gemini extraction per asset. The pool slot is the concurrency/rate-limit guard;
        idempotent — re-running a processed asset is a no-op (skip-existing upstream, and
        scripts/run_gemini_extract.py's own Bronze-exists check, belt-and-suspenders)."""
        client_id = context["params"]["client_id"]
        out = _run_real_script(
            ["scripts/run_gemini_extract.py", asset_id],
            extra_env={"CLIENT_ID": client_id},
        )
        print(out)
        return asset_id

    # Deferrable async wait: frees the worker slot while the API processes, instead of a
    # synchronous loop holding a slot for the whole upload+process duration.
    # trigger_rule="none_failed" (ADR-008 addendum, 2026-06-25 — see "Trigger-rule fix" entry
    # in PROJECT_STATUS.md): the default rule (all_success) means that when there is nothing
    # NEW to extract, list_new_assets's AirflowSkipException cascades and skips everything
    # downstream too — including dbt_build_marts, which has no dependency on anything being
    # newly extracted; it should refresh Gold from whatever is ALREADY in Bronze/Silver every
    # run. "none_failed" runs as long as nothing upstream actually FAILED — a skip doesn't
    # block it. This also matters for the Gemini-quota-conscious case: a run with nothing new
    # to extract still rebuilds/validates the existing real data, it doesn't just stop dead.
    await_processing = TimeDeltaSensorAsync(
        task_id="await_gemini_processing",
        delta=timedelta(seconds=5),
        trigger_rule="none_failed",
    )

    # Silver -> Gold as external parquet on S3 (ADR-005). DuckDB compute, S3 storage.
    # `set -a && source .env` is required here too (same gap PROJECT_STATUS.md named
    # 2026-06-24: `source venv/bin/activate` alone does not export S3_BUCKET etc.).
    dbt_build = BashOperator(
        task_id="dbt_build_marts",
        trigger_rule="none_failed",
        bash_command=(
            "cd {{ var.value.get('repo_dir', '" + str(REPO_DIR) + "') }} && "
            "source venv/bin/activate && set -a && source .env && set +a && "
            "dbt build -s marts.core"
        ),
    )

    @task(trigger_rule="none_failed")
    def ge_validate() -> str:
        """Per-layer quality gates, block promotion on CRITICAL fail.

        Honest scope (was: TODO calling a GE checkpoint that doesn't exist): literal Great
        Expectations checkpoint execution against real data is a named open gap
        (tests/GATES.md "Open" section — "GE suites authored but not executed against real
        data in CI"). The dbt schema tests already ran inside dbt_build_marts above (the
        5th-gate `chunk_count` check, FK/range/uniqueness tests — see _core.yml /
        _sources.yml). What THIS task adds for real: the two governance contracts that gate
        every build today. It does not fabricate a GE checkpoint call."""
        out = _run_real_script(["tests/lineage_contract.py"])
        print(out)
        out = _run_real_script(["tests/boundary_contract.py"])
        print(out)
        return "lineage + boundary contracts green (literal GE checkpoint execution remains an open gap, tests/GATES.md)"

    @task(trigger_rule="none_failed")
    def refresh_serving() -> str:
        """Step N — refresh the read-only serving veneer over the freshly-built Gold S3 (ADR-005).

        Gold S3 is the sole source of truth; this only refreshes the projection on top.
          * duckdb_vss (default, $0) — still an honest no-op: no separate VSS index file exists
            to refresh (SPEC_v1_search.md §1's `--semantic` builds an ephemeral in-memory HNSW
            index per query). v1's actual serving surface is target/dev.duckdb itself, already
            refreshed by dbt_build_marts above.
          * snowflake_cortex — REAL as of ADR-005 Addendum 2026-06-27 #5: all four FinOps
            preconditions are now met (COST_LOG.md monitoring practice in place, day-25 teardown
            lifted, $0 fallback proven 2026-06-25, embeddings stay single-sourced/BYO-Gemini).
            Shells out to `venv/bin/python` (ADR-008 cross-venv boundary — venv_airflow never
            imports snowflake-connector/duckdb directly): first
            `scripts/provision_snowflake_serving.py --phase refresh --apply` (ALTER EXTERNAL
            TABLE ... REFRESH on all 8 Gold tables + FACT_CHUNK_VECTOR view resync), then
            `tests/reconcile_snowflake_serving.py` (row-count + key-set reconciliation against
            real Gold S3). A reconciliation mismatch raises here, failing the task loud — the
            live trip-wire for ADR-005's own veto line ("re-fires if Snowflake becomes a second
            source of truth").
        """
        backend = os.getenv("SERVING_BACKEND", "duckdb_vss")
        if backend == "duckdb_vss":
            return "no-op (duckdb_vss: no separate VSS index to refresh — v1 serving = target/dev.duckdb, already refreshed by dbt_build_marts)"
        out = _run_real_script(["scripts/provision_snowflake_serving.py", "--phase", "refresh", "--apply"])
        print(out)
        out = _run_real_script(["tests/reconcile_snowflake_serving.py"])
        print(out)
        return "snowflake_cortex: refreshed 8 external tables + FACT_CHUNK_VECTOR view, reconciliation OK"

    landed = sync_drive_to_landing()
    new_assets = list_new_assets()
    landed >> new_assets  # sync Drive before listing what's new
    extracted = extract_chunks.expand(asset_id=new_assets)  # dynamic mapping: 1 task per new asset
    chain(extracted, await_processing, dbt_build, ge_validate(), refresh_serving())


creative_intel_pipeline()
