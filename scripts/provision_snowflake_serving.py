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
case-sensitive lowercase in Snowflake ("asset_id", not ASSET_ID/asset_id unquoted) — any query or
BI tool against these tables must quote column names.

4. search — native VECTOR similarity, NOT the managed Cortex Search Service. That managed path was
   tried and abandoned for real (ADR-005 Addenda 2026-06-27 #2/#3/#4): it needs its own embedding
   model (conflicts with BYO-Gemini-only), runs on a Dynamic Table internally (rejects
   EXTERNAL_TABLE sources outright), and its embedding step is gated off trial accounts entirely
   ("AI function EMBED_TEXT_768 is not available for trial accounts") — confirmed by three
   successive real --apply failures, not assumed. What this phase actually builds: a VIEW (Clean-ERD
   "serving = view, never a duplicated physical table") casting FACT_CHUNK.embedding (VARIANT via
   INFER_SCHEMA) to native VECTOR(FLOAT, 768), queryable with VECTOR_COSINE_SIMILARITY — zero second
   embedding surface, zero Cortex AI functions, works against an external table because it's a
   plain view+query, not a Dynamic Table.

5. refresh — ALTER EXTERNAL TABLE ... REFRESH per Gold model + a CREATE OR REPLACE VIEW resync
   of FACT_CHUNK_VECTOR. Distinct from `tables`/`search` above: those CREATE the objects
   (idempotent IF-NOT-EXISTS / always-fresh-OR-REPLACE); this phase only refreshes already-
   created ones against whatever is newest on S3 — the thing Airflow's refresh_serving task
   calls after every dbt_build_marts run (dags/creative_intel_pipeline.py). The reconciliation
   check that should follow a refresh lives separately in tests/reconcile_snowflake_serving.py
   (this script provisions/refreshes; that one verifies — kept as two files on purpose, same
   separation as `dbt build` vs. a test suite).

ADR-014 addition (2026-07-04): `account` and `tables` also provision `CREATIVE_INTEL_ANALYST_RO`,
a read-only role distinct from the operating `CREATIVE_INTEL_ROLE` above — USAGE-only on the
warehouse (no OPERATE), and `SELECT` on ALL + FUTURE TABLES in PUBLIC (the FUTURE grant is the
fix for the T-SRV-04 drill class: a per-table-only grant list means a newly added Gold model is
invisible to a role until this script is re-run for it). No stage grant exists for this role, so
it can never reach Bronze/Silver regardless of future changes here.

Usage:
    python scripts/provision_snowflake_serving.py                       # dry-run, all phases
    python scripts/provision_snowflake_serving.py --phase account --apply
    python scripts/provision_snowflake_serving.py --phase storage --apply
    python scripts/provision_snowflake_serving.py --phase tables --apply
    python scripts/provision_snowflake_serving.py --phase search --apply
    python scripts/provision_snowflake_serving.py --phase refresh --apply
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
        "analyst_role": os.environ.get("SNOWFLAKE_ANALYST_ROLE", "CREATIVE_INTEL_ANALYST_RO"),
        "analyst_user": os.environ.get("SNOWFLAKE_ANALYST_USER", ""),
        "user": os.environ.get("SNOWFLAKE_USER", "<SNOWFLAKE_USER>"),
        "bootstrap_role": os.environ.get("SNOWFLAKE_BOOTSTRAP_ROLE", "ACCOUNTADMIN"),
        "integration": os.environ.get("SNOWFLAKE_S3_INTEGRATION", "CREATIVE_INTEL_S3_INTEGRATION"),
        "stage": os.environ.get("SNOWFLAKE_STAGE", "GOLD_STAGE"),
        "s3_role_arn": os.environ.get("SNOWFLAKE_S3_ROLE_ARN", ""),
        "bucket": os.environ.get("S3_BUCKET", "creative-intel-lake"),
        "vector_view": os.environ.get("SNOWFLAKE_VECTOR_VIEW", "FACT_CHUNK_VECTOR"),
    }


def account_statements(cfg: dict) -> list[str]:
    stmts = [
        f"USE ROLE {cfg['bootstrap_role']};",
        f"CREATE WAREHOUSE IF NOT EXISTS {cfg['warehouse']} "
        f"WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;",
        f"CREATE DATABASE IF NOT EXISTS {cfg['database']};",
        f"CREATE ROLE IF NOT EXISTS {cfg['role']};",
        f"GRANT USAGE, OPERATE ON WAREHOUSE {cfg['warehouse']} TO ROLE {cfg['role']};",
        f"GRANT USAGE ON DATABASE {cfg['database']} TO ROLE {cfg['role']};",
        f"GRANT USAGE ON SCHEMA {cfg['database']}.PUBLIC TO ROLE {cfg['role']};",
        f"GRANT ROLE {cfg['role']} TO USER {cfg['user']};",
        # ADR-014: read-only analyst role, USAGE-only (no OPERATE) — distinct blast radius from
        # the operating role above.
        f"CREATE ROLE IF NOT EXISTS {cfg['analyst_role']};",
        f"GRANT USAGE ON WAREHOUSE {cfg['warehouse']} TO ROLE {cfg['analyst_role']};",
        f"GRANT USAGE ON DATABASE {cfg['database']} TO ROLE {cfg['analyst_role']};",
        f"GRANT USAGE ON SCHEMA {cfg['database']}.PUBLIC TO ROLE {cfg['analyst_role']};",
    ]
    if cfg["analyst_user"]:
        stmts.append(f"GRANT ROLE {cfg['analyst_role']} TO USER {cfg['analyst_user']};")
    else:
        print(
            "NOTE: SNOWFLAKE_ANALYST_USER is unset - CREATIVE_INTEL_ANALYST_RO is created but "
            "granted to no user yet. Set it before --apply to also assign the role.",
            file=sys.stderr,
        )
    return stmts


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
    # ADR-014: analyst role gets a blanket + FUTURE grant (unlike the operating role's per-table
    # list above) since ad-hoc analyst queries have no code-review gate to catch a missed model.
    stmts.append(f"GRANT USAGE ON SCHEMA PUBLIC TO ROLE {cfg['analyst_role']};")
    stmts.append(f"GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO ROLE {cfg['analyst_role']};")
    stmts.append(f"GRANT SELECT ON FUTURE TABLES IN SCHEMA PUBLIC TO ROLE {cfg['analyst_role']};")
    return stmts


def search_statements(cfg: dict) -> list[str]:
    # ADR-005 Addendum 2026-06-27 #4: the managed Cortex Search Service path (Addenda #2/#3) is
    # abandoned - trial accounts can't run its embedding step at all ("AI function EMBED_TEXT_768
    # is not available for trial accounts"), confirmed by a real failed --apply, not assumed. This
    # phase now builds a VIEW (not a copy - Clean-ERD "serving = view, never a duplicated physical
    # table") that casts FACT_CHUNK.embedding (VARIANT via INFER_SCHEMA) to native VECTOR(FLOAT,768)
    # for VECTOR_COSINE_SIMILARITY queries - zero second embedding surface, zero Cortex AI functions.
    cols = ('"chunk_id", "asset_id", "transcript_segment", "chunk_theme", "sentiment", '
            '"standalone_score"')
    return [
        f"USE ROLE {cfg['bootstrap_role']};",
        f"USE DATABASE {cfg['database']};",
        f"CREATE OR REPLACE VIEW PUBLIC.{cfg['vector_view']} AS\n"
        f"  SELECT {cols}, \"embedding\"::VECTOR(FLOAT, 768) AS \"embedding_vec\"\n"
        f'  FROM PUBLIC.FACT_CHUNK WHERE "embedding" IS NOT NULL;',
        f"GRANT SELECT ON VIEW PUBLIC.{cfg['vector_view']} TO ROLE {cfg['role']};",
        f"GRANT SELECT ON VIEW PUBLIC.{cfg['vector_view']} TO ROLE {cfg['analyst_role']};",
    ]


def refresh_statements(cfg: dict) -> list[str]:
    # ALTER EXTERNAL TABLE ... REFRESH per Gold model, then resync the FACT_CHUNK_VECTOR view by
    # reusing search_statements' own CREATE OR REPLACE VIEW / GRANT SQL (no duplicated view DDL
    # to drift out of sync with the `search` phase above).
    stmts = [
        f"USE ROLE {cfg['bootstrap_role']};",
        f"USE DATABASE {cfg['database']};",
    ]
    for model in GOLD_MODELS:
        stmts.append(f"ALTER EXTERNAL TABLE PUBLIC.{model.upper()} REFRESH;")
    stmts += [
        s for s in search_statements(cfg)
        if s.startswith(("CREATE OR REPLACE VIEW", "GRANT SELECT ON VIEW"))
    ]
    return stmts


PHASES = {
    "account": account_statements,
    "storage": storage_statements,
    "tables": table_statements,
    "search": search_statements,
    "refresh": refresh_statements,
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
