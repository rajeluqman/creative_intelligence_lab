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
    --conf '{"client_id": "acme", "drive_folder_id": "1AbC..."}'
Or set `schedule="@daily"` to poll while Airflow is up (Codespace = on-demand, not 24/7).

Bodies are stubs (TODO) wired to the real scripts/dbt; the GRAPH + patterns are real and
parse-clean. Verify: `python -c "from airflow.models import DagBag; \
assert not DagBag('dags').import_errors, DagBag('dags').import_errors"`.
"""
from __future__ import annotations

import os
from datetime import timedelta

import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.sensors.time_delta import TimeDeltaSensorAsync

GEMINI_POOL = "gemini_api"  # create in Airflow: `airflow pools set gemini_api <QPM_budget> "..."`


@dag(
    dag_id="creative_intel_pipeline_v1",
    schedule=None,  # manual trigger w/ conf; set "@daily" to poll while Airflow is up
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    params={
        # The two "new data" entry points: ad-hoc video (existing client) + new-client onboard.
        "client_id": Param("demo_client", type="string", description="client partition under landing/"),
        "drive_folder_id": Param(
            "", type="string", description="Google Drive folder id to sync (blank = re-scan existing)"
        ),
    },
    default_args={
        "retries": 3,
        "retry_delay": timedelta(seconds=30),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(minutes=10),
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
        # TODO: scripts/ingest_drive_to_s3.py — pull `folder`, hash bytes, write
        #   s3://$S3_BUCKET/landing/<client_id>/video/<sha256>.<ext>; skip if the hash already exists.
        _ = (client_id, folder)
        return 0  # number of new assets landed this run

    @task
    def list_new_assets(**context) -> list[str]:
        """Step 2 — return only asset_ids in landing whose Bronze JSON does NOT yet exist.

        The second cost firewall — never re-call Gemini on an already-extracted asset."""
        client_id = context["params"]["client_id"]
        candidates = os.getenv("DEMO_ASSET_IDS", "rawhash001,rawhash002").split(",")
        already_processed: set[str] = set()  # TODO: query bronze_asset_raw by content hash (per client_id)
        _ = client_id
        new = [a for a in candidates if a not in already_processed]
        if not new:
            raise AirflowSkipException("no new assets — nothing to extract")
        return new

    @task(pool=GEMINI_POOL, retries=5)
    def extract_chunks(asset_id: str) -> str:
        """One Gemini extraction per asset. The pool slot is the concurrency/rate-limit guard;
        idempotent — re-running a processed asset is a no-op (skip-existing upstream)."""
        # TODO: scripts/run_gemini_extract.py — structured output, stamp model/prompt version,
        #       write verbatim to bronze_asset_raw, log tokens -> fact_extraction_run.
        return asset_id

    # Deferrable async wait: frees the worker slot while the API processes, instead of a
    # synchronous loop holding a slot for the whole upload+process duration.
    await_processing = TimeDeltaSensorAsync(
        task_id="await_gemini_processing", delta=timedelta(seconds=5)
    )

    # Silver -> Gold as external parquet on S3 (ADR-005). DuckDB compute, S3 storage.
    dbt_build = BashOperator(
        task_id="dbt_build_marts",
        bash_command="cd {{ var.value.get('repo_dir', '.') }} && dbt build -s marts.core",
    )

    @task
    def ge_validate() -> str:
        """Run the Great Expectations suites (per-layer gates). Block promotion on CRITICAL fail."""
        # TODO: run GE checkpoints over silver_chunk / fact_ad_performance / mart_chunk_perf_correlation.
        return "ge ok"

    @task
    def refresh_serving() -> str:
        """Step N — refresh the read-only serving veneer over the freshly-built Gold S3 (ADR-005).

        Gold S3 is the sole source of truth; this only refreshes the projection on top.
          * SERVING_BACKEND=snowflake_cortex -> ALTER EXTERNAL TABLE ... REFRESH + Cortex Search sync.
          * SERVING_BACKEND=duckdb_vss (default, $0) -> rebuild the VSS/HNSW index over Gold S3.
        """
        backend = os.getenv("SERVING_BACKEND", "duckdb_vss")
        # TODO: snowflake_cortex -> refresh external tables + Cortex Search service;
        #       duckdb_vss -> rebuild HNSW index over s3://$S3_BUCKET/gold/...
        return f"serving refreshed ({backend})"

    landed = sync_drive_to_landing()
    new_assets = list_new_assets()
    landed >> new_assets  # sync Drive before listing what's new
    extracted = extract_chunks.expand(asset_id=new_assets)  # dynamic mapping: 1 task per new asset
    chain(extracted, await_processing, dbt_build, ge_validate(), refresh_serving())


creative_intel_pipeline()
