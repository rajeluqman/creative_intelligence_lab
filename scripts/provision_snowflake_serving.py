"""Capture-as-code Snowflake serving provisioning (ADR-005 §B).

Reconstructs, as idempotent SQL, the warehouse/database/role/storage-integration/external-table
objects that were created against the live (Novartis-shared-trial) account on 2026-06-27 — see
PROJECT_STATUS.md's "Snowflake Cortex serving" item for the narrated session. Exists because that
session ran the SQL ad hoc with no checked-in artifact, which broke this repo's own "governance is
code, not vigilance" pattern. ADR-005's Cost discipline already promised "re-provision later =
re-run the capture-as-code provisioning script against the same S3 prefix" — this is that script.

Three ordered phases, because one step is a genuine human-in-the-loop handshake (a Snowflake
storage integration's IAM trust requires pasting Snowflake-generated values into the AWS console;
no API closes that loop from this side):
  1. account — CREATE WAREHOUSE/DATABASE/ROLE + GRANTs. Needs an account-admin-class role
     (ACCOUNTADMIN here — the only role with account-level CREATE WAREHOUSE/DATABASE; the scoped
     runtime role, CREATIVE_INTEL_ROLE, deliberately does not have it).
  2. storage — CREATE STORAGE INTEGRATION, then DESC it. STOP on a real run: paste the printed
     AWS IAM user ARN + external ID into the trust policy of SNOWFLAKE_S3_ROLE_ARN's AWS role
     before continuing to the tables phase.
  3. tables — CREATE STAGE + one CREATE EXTERNAL TABLE per Gold model (USING TEMPLATE +
     INFER_SCHEMA) + REFRESH + per-table GRANT SELECT to the scoped serving role (Snowflake GRANT
     takes one object per statement, not a comma list — kept literal/copy-paste-real here).

Dry-run by default: prints the SQL plan, opens no connection, needs no credentials and no
snowflake-connector import. --apply actually connects (ADR-005: "provisioning stays owner-gated" —
confirm with the owner before passing this flag) and runs it; every statement is
IF-NOT-EXISTS/idempotent, so re-running against objects that already exist is a no-op, not an
error.

Known gotcha (hit once during the original build, named here so it isn't re-discovered): the
USING TEMPLATE/INFER_SCHEMA path quotes every inferred column name, so columns land
case-sensitive lowercase in Snowflake ("asset_id", not ASSET_ID/asset_id unquoted) — any query, BI
tool, or Cortex Search build against these tables must quote column names.

Still open (not this script's job — see PROJECT_STATUS.md item 3 "Still not built"): the
chunk_embedding.embedding column infers as VARIANT here, not native VECTOR, so Cortex Search needs
an explicit cast/reshape step on top of this; a checked-in automated row-count+key reconciliation
test; COST_LOG.md; wiring Airflow's refresh_serving to an ALTER EXTERNAL TABLE ... REFRESH call.

Usage:
    python scripts/provision_snowflake_serving.py                       # dry-run, all phases
    python scripts/provision_snowflake_serving.py --phase account --apply
    python scripts/provision_snowflake_serving.py --phase storage --apply
    python scripts/provision_snowflake_serving.py --phase tables --apply
"""
from __future__ import annotations

import argparse
import os
import sys

# Gold models served as external tables: the 7 marts.core models + the BYO-embedding model
# written directly by scripts/generate_embeddings.py. All land at
# gold/<model>/<CLIENT_ID>/<model>.parquet (client-partitioned convention, ADR-005 Addendum
# 2026-06-25 #2 / macros/s3_external.sql) — the stage URL covers all of them at once.
GOLD_MODELS = [
    "dim_asset",
    "fact_chunk",
    "fact_extraction_run",
    "bridge_asset_lineage",
    "bridge_chunk_compatibility",
    "dim_keyword_bridge",
    "dim_theme_bridge",
    "chunk_embedding",
]

REQUIRED_ENV_APPLY = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]


def _cfg() -> dict:
    return {
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "CREATIVE_INTEL_WH"),
        "database": os.environ.get("SNOWFLAKE_DATABASE", "CREATIVE_INTEL_DB"),
        "role": os.environ.get("SNOWFLAKE_ROLE", "CREATIVE_INTEL_ROLE"),
        "user": os.environ.get("SNOWFLAKE_USER", "<SNOWFLAKE_USER>"),
        "bootstrap_role": os.environ.get("SNOWFLAKE_BOOTSTRAP_ROLE", "ACCOUNTADMIN"),
        "integration": os.environ.get("SNOWFLAKE_S3_INTEGRATION", "CREATIVE_INTEL_S3_INTEGRATION"),
        "stage": os.environ.get("SNOWFLAKE_STAGE", "GOLD_STAGE"),
        "s3_role_arn": os.environ.get("SNOWFLAKE_S3_ROLE_ARN", ""),
        "bucket": os.environ.get("S3_BUCKET", "creative-intel-lake"),
    }


def account_statements(cfg: dict) -> list[str]:
    return [
        f"USE ROLE {cfg['bootstrap_role']};",
        f"CREATE WAREHOUSE IF NOT EXISTS {cfg['warehouse']} "
        f"WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;",
        f"CREATE DATABASE IF NOT EXISTS {cfg['database']};",
        f"CREATE ROLE IF NOT EXISTS {cfg['role']};",
        f"GRANT USAGE, OPERATE ON WAREHOUSE {cfg['warehouse']} TO ROLE {cfg['role']};",
        f"GRANT USAGE ON DATABASE {cfg['database']} TO ROLE {cfg['role']};",
        f"GRANT USAGE ON SCHEMA {cfg['database']}.PUBLIC TO ROLE {cfg['role']};",
        f"GRANT ROLE {cfg['role']} TO USER {cfg['user']};",
    ]


def storage_statements(cfg: dict) -> list[str]:
    role_arn = cfg["s3_role_arn"]
    if not role_arn:
        print(
            "NOTE: SNOWFLAKE_S3_ROLE_ARN is unset - the plan below uses a placeholder ARN. "
            "Set it to the real AWS IAM role ARN before --apply.",
            file=sys.stderr,
        )
        role_arn = "arn:aws:iam::<ACCOUNT_ID>:role/creative-intel-snowflake-role"
    return [
        f"USE ROLE {cfg['bootstrap_role']};",
        f"CREATE STORAGE INTEGRATION IF NOT EXISTS {cfg['integration']}\n"
        f"  TYPE = EXTERNAL_STAGE STORAGE_PROVIDER = 'S3' ENABLED = TRUE\n"
        f"  STORAGE_AWS_ROLE_ARN = '{role_arn}'\n"
        f"  STORAGE_ALLOWED_LOCATIONS = ('s3://{cfg['bucket']}/gold/');",
        f"DESC STORAGE INTEGRATION {cfg['integration']};"
        "  -- read STORAGE_AWS_IAM_USER_ARN + STORAGE_AWS_EXTERNAL_ID from the result and paste "
        "both into the AWS role's trust policy BEFORE running --phase tables.",
    ]


def table_statements(cfg: dict) -> list[str]:
    stmts = [
        f"USE ROLE {cfg['bootstrap_role']};",
        f"USE DATABASE {cfg['database']};",
        f"CREATE STAGE IF NOT EXISTS {cfg['stage']}\n"
        f"  STORAGE_INTEGRATION = {cfg['integration']}\n"
        f"  URL = 's3://{cfg['bucket']}/gold/';",
    ]
    for model in GOLD_MODELS:
        table = model.upper()
        stmts.append(
            f"CREATE EXTERNAL TABLE IF NOT EXISTS PUBLIC.{table}\n"
            f"  USING TEMPLATE (\n"
            f"    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))\n"
            f"    FROM TABLE(INFER_SCHEMA(LOCATION=>'@{cfg['stage']}/{model}/', FILE_FORMAT=>'PARQUET_FORMAT'))\n"
            f"  )\n"
            f"  LOCATION = @{cfg['stage']}/{model}/\n"
            f"  AUTO_REFRESH = FALSE\n"
            f"  FILE_FORMAT = (TYPE = PARQUET);"
        )
        stmts.append(f"ALTER EXTERNAL TABLE PUBLIC.{table} REFRESH;")
    stmts.append(f"GRANT USAGE ON SCHEMA PUBLIC TO ROLE {cfg['role']};")
    for model in GOLD_MODELS:
        stmts.append(f"GRANT SELECT ON PUBLIC.{model.upper()} TO ROLE {cfg['role']};")
    return stmts


PHASES = {
    "account": account_statements,
    "storage": storage_statements,
    "tables": table_statements,
}


def run(phase: str, apply: bool) -> None:
    cfg = _cfg()
    phases = PHASES if phase == "all" else {phase: PHASES[phase]}

    if apply:
        missing = [v for v in REQUIRED_ENV_APPLY if not os.environ.get(v)]
        if missing:
            sys.exit(
                f"provision_snowflake_serving: missing required env var(s): "
                f"{', '.join(missing)} - refusing to run --apply."
            )
        import snowflake.connector  # local import: dry-run needs no driver/creds at all

        conn = snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
        )

    try:
        for name, builder in phases.items():
            stmts = builder(cfg)
            print(f"\n--- phase: {name} ({'APPLY' if apply else 'DRY-RUN'}) ---")
            for stmt in stmts:
                print(stmt)
            if apply:
                cur = conn.cursor()
                for stmt in stmts:
                    # strip the human-readable "--" tail glued onto the DESC line above
                    cur.execute(stmt.split("  -- ")[0])
                    if stmt.strip().startswith("DESC "):
                        for row in cur.fetchall():
                            print(row)
    finally:
        if apply:
            conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Capture-as-code Snowflake serving provisioning (ADR-005)."
    )
    parser.add_argument("--phase", choices=["all", *PHASES], default="all")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="actually connect and execute (default: dry-run, prints SQL only)",
    )
    args = parser.parse_args()
    run(args.phase, args.apply)
