# Deployment Guide

> **Audience: whoever stands this pipeline up on a fresh account, or maintains CI.** Not in the
> original 8-page set — added 2026-06-27 because real deployment mechanics now exist (AWS OIDC CI
> federation, a 5-phase Snowflake provisioning script) and were only documented as scattered ADR
> prose, not one page a new maintainer could follow start to finish. Local build (`venv`, `dbt`,
> `.env`) is already covered by `README_BUILD.md` — this page is the two pieces that touch real
> cloud infrastructure: CI and Snowflake serving.

## CI/CD — what actually deploys on a push to `main`

`.github/workflows/ci.yml` has two jobs:
1. **`static-gates`** — every push and PR: ruff, `py_compile`, `dbt parse`+`seed` (placeholder env,
   $0, no cloud), GE JSON validity, no-`.env`-committed guard, the lineage/boundary/doc-reference/
   repo-map/adr-coupling contracts, the golden test. Runs everywhere, needs no secrets.
2. **`real-build`** — **`push` to `main` only, never `pull_request`** — a real `dbt build -s
   +marts.core` against real S3. Uses AWS OIDC role federation (ADR-013), not a static key:
   - GitHub issues a short-lived OIDC token → `aws-actions/configure-aws-credentials@v4` exchanges
     it for temporary credentials by assuming `creative-intel-ci-role`
     (`arn:aws:iam::579880301047:role/creative-intel-ci-role`).
   - The role's trust policy restricts assumption to this exact repo + the `main` branch — a PR
     branch can never assume it, only a run that's already merged.
   - The role's permissions policy is least-privilege: read-only on `bronze/*`, read+write on
     `silver/*`/`gold/*` only — CI building Gold can never touch Landing/Bronze.
   - **`dbt seed` (all 5, unscoped) runs before the build** — `+marts.core`'s selector doesn't pull
     in `marts.performance`-lineage seeds, but a singular test references one by raw name; skipping
     this step reproduces a real failure that happened once already (see **Runbook**).
   - **No long-lived AWS credential is stored anywhere** in this repo or GitHub's secrets — that's
     the whole point of the OIDC approach over a static-key secret.

**To verify a `real-build` run after pushing to `main`:** `gh run watch` (or the Actions tab) — a
successful `Configure AWS credentials` step is the actual proof the OIDC handshake worked, not just
that the YAML parsed.

**Setting this up on a brand-new AWS account** (one-time, console-only, not scriptable from here —
confirmed by a real `AccessDenied` when the pipeline's own IAM user tried `iam:ListOpenIDConnectProviders`):
1. IAM → Identity providers → add `token.actions.githubusercontent.com` (audience
   `sts.amazonaws.com`).
2. IAM → Roles → Create role → Web identity → same provider, restrict to your org/repo/branch.
3. Attach the least-privilege inline policy from `architecture/ADR-013-aws-oidc-ci-federation.md`
   (read Bronze, read+write Silver/Gold only).
4. Paste the new role ARN into `ci.yml`'s `role-to-assume`.

## Snowflake serving — provisioning and refresh

`scripts/provision_snowflake_serving.py` is the **capture-as-code** version of the SQL that was
first run ad hoc against the real account — re-provisioning later means re-running this script
against the same S3 prefix, not a manual backfill. Five ordered phases, each idempotent
(`IF NOT EXISTS` / `CREATE OR REPLACE`):

| Phase | What it does | Needs |
|-------|--------------|-------|
| `account` | `CREATE WAREHOUSE`/`DATABASE`/`ROLE` + grants | `ACCOUNTADMIN`-class role |
| `storage` | `CREATE STORAGE INTEGRATION` (IAM-role trust, zero static secrets) | a pre-created AWS IAM role scoped to `s3:GetObject`/`s3:ListBucket` on `gold/*` |
| `tables` | `CREATE EXTERNAL TABLE` ×8 (one per Gold model) + grants | the storage integration's IAM trust handshake completed (see below) |
| `search` | `CREATE OR REPLACE VIEW` — native `VECTOR(FLOAT,768)` cast over the BYO-embedding column | the `tables` phase done |
| `refresh` | `ALTER EXTERNAL TABLE ... REFRESH` ×8 + view resync | re-run after every `dbt_build_marts` |

**Every phase is dry-run by default** — prints the exact SQL plan, opens no connection, needs no
credentials. **`--apply` is owner-gated by design** (ADR-005: "provisioning stays owner-gated") —
confirm what the dry-run printed before adding the flag:
```
python scripts/provision_snowflake_serving.py --phase <name>            # dry-run, always do this first
python scripts/provision_snowflake_serving.py --phase <name> --apply    # real connection, real SQL
```

**The one step that can't be scripted end-to-end — `storage` is a two-way handshake:** after
`CREATE STORAGE INTEGRATION`, Snowflake generates an IAM user ARN + external ID
(`DESC STORAGE INTEGRATION` prints both). Those two values must be pasted into the trust policy of
the AWS role named in `SNOWFLAKE_S3_ROLE_ARN` **before** running `--phase tables` — no API closes
this loop from either side, it's a real console step on both ends.

**Routine operation, after this is set up once:** Airflow's `refresh_serving` task already calls
`--phase refresh --apply` then `tests/reconcile_snowflake_serving.py` automatically for
`SERVING_BACKEND=snowflake_cortex` — you don't need to run these by hand unless Airflow itself is
down (see **Runbook**). A reconciliation mismatch fails the task loud — investigate before trusting
any Snowflake read, never re-run-and-ignore.

## Why Cortex Search Service isn't part of this deployment
The managed `CREATE CORTEX SEARCH SERVICE` path was tried for real and abandoned — three genuine
blockers, the last one terminal (`EMBED_TEXT_768` is gated off trial-tier accounts entirely, a
billing wall). Don't re-attempt it on this account; see **Architecture Decisions** for the full
trail. The `search` phase above (native `VECTOR` view) is the permanent replacement, not an interim
workaround.
