# ADR-013 — AWS OIDC role federation for real `dbt build` in CI

- **Status:** Accepted
- **Date:** 2026-06-27
- **Deciders:** owner (decision + console execution of the IAM role/policy/trust relationship),
  assistant (CI wiring)
- **Context refs:** `PROJECT_STATUS.md` "AWS OIDC for real `dbt build` in CI" (the working log this
  ADR formalizes); ADR-005 (Snowflake's `CREATIVE_INTEL_ROLE` set the "dedicated, not reused"
  precedent this follows); `.github/workflows/ci.yml`'s pre-existing `static-gates` job (unchanged,
  still $0/no-cloud).
- **Does NOT touch:** the production `creative-intel-pipeline` IAM user/scripts, `static-gates`'s
  $0/no-cloud guarantee, or any Gold/marts model.

## Context

CI has only ever run `dbt parse` + `dbt seed` against a placeholder `S3_BUCKET` — never a real
`dbt build` against real S3 — a gap named since the 2026-06-25 completion plan ("needs real AWS
credentials as GitHub Actions secrets... a genuine security/access-grant decision, not an
implementation detail... needs explicit owner sign-off"). Owner decided to close it, choosing OIDC
role federation over a static-key GitHub secret: no long-lived AWS credential is ever stored
anywhere. The owner created the IAM identity provider, role, trust policy, and permissions policy
directly in the AWS console (the existing `creative-intel-pipeline` IAM user has no IAM-admin
rights — confirmed by a real `AccessDenied` on `iam:ListOpenIDConnectProviders`, so this step
could not be done programmatically from this repo).

## Decision

**A — OIDC role federation, not a static-key secret.** GitHub Actions exchanges a short-lived
OIDC token for temporary AWS credentials via `sts:AssumeRoleWithWebIdentity` — no AWS access
key/secret is ever stored in GitHub. New, dedicated role
`arn:aws:iam::579880301047:role/creative-intel-ci-role` — not a reuse of the existing
`creative-intel-pipeline` IAM user the real ingestion/extraction scripts use (mirrors the
"dedicated, not reused" precedent already set for Snowflake's `CREATIVE_INTEL_ROLE`, ADR-005).

**B — Trust policy scoped to exactly one branch.** Built via the AWS console's native GitHub
sub-form (organization `rajeluqman`, repository `creative_intelligence_lab`, branch `main`) — only
a workflow run triggered by a push to `main` (i.e., after merge) can assume the role; a
`pull_request`-triggered run, on any branch, cannot.

**C — Least-privilege permissions policy**, read-only on Bronze, read+write on Silver/Gold only —
CI building Gold must never be able to touch Landing/Bronze (only the real ingestion/extraction
scripts write those): `s3:ListBucket` on the bucket scoped to the `bronze/*`/`silver/*`/`gold/*`
prefixes, `s3:GetObject` on `bronze/*`, `s3:{Get,Put,Delete}Object` on `silver/*` and `gold/*` only.
**(unverified — built by the owner directly in the AWS console; the IAM user this repo's scripts
use has no `iam:GetRole`/`iam:ListRolePolicies` rights to read it back and confirm independently,
same `AccessDenied` wall as the role itself. This is the design as specified and confirmed by the
owner, not re-derived from a live API read.)**

**D — New CI job (`real-build`), gated `if: github.event_name == 'push'`, never `pull_request`,**
with `permissions: id-token: write` on the job + `aws-actions/configure-aws-credentials@v4`, runs
after `static-gates` passes (`needs: static-gates`), then a real `dbt build -s +marts.core` against
the repo's own checked-in `profiles.yml` (confirmed not gitignored, no secrets in it — credentials
resolve from the OIDC-assumed role's env vars at runtime via the default AWS credential chain, the
same chain pattern the real scripts already use).

## Rationale

- Federation removes the entire "static key leaks / never rotates / sits in GitHub forever" risk
  class this repo's threat model named for a private solo repo.
- Branch-restricted trust (B) + `push`-only job gating (D) are two independent, redundant controls
  (defense in depth) keeping unreviewed PR code from ever touching real S3 with write access — even
  if one were misconfigured, the other still holds.
- Read-only Bronze / no Landing access keeps CI's blast radius matching its actual job (build Gold
  from Bronze/Silver), not broader than it needs.
- Gating the real-build job on `static-gates` passing first avoids spending a real S3 write attempt
  on code that is already known-broken at the parse/lint/golden-test stage.

## Rejected alternatives

1. **Static AWS access key as a GitHub secret.** Rejected — long-lived credential, no expiry, the
   exact risk class OIDC removes for ~zero extra setup cost the owner was already willing to pay
   (mirrors past console-driven decisions, e.g. the Snowflake storage integration over embedding a
   static key in `CREATE STAGE`, ADR-005 Addendum 2026-06-27).
2. **Reusing the existing `creative-intel-pipeline` IAM user/role for CI.** Rejected — would give CI
   the same permissions as the production ingestion path (Bronze write access CI must never have),
   and breaks the "dedicated, not reused" precedent already set for Snowflake.
3. **Running the real-build job on `pull_request` too** (for earlier feedback on PRs). Rejected —
   that is precisely the access grant to unreviewed code this ADR exists to prevent;
   `static-gates` (parse/lint/golden-test, no cloud) already gives PR-time feedback without
   touching real S3.

## Consequences

- **Positive:** CI now proves a real `dbt build -s +marts.core` succeeds against real S3 on every
  merge to `main`, not just parse/lint — closes the gap named in the 2026-06-25 completion plan.
- **Negative / accepted:** a broken Gold build is now only caught after merge (push to `main`), not
  on the PR itself. Accepted because moving real-S3 write access to PR time was the rejected,
  higher-risk alternative (#3 above).
- **Bounded:** this ADR governs ONLY the new `real-build` CI job's AWS access. It does not change
  `tests/golden/run_golden_test.py`'s $0/no-cloud guarantee (still runs in `static-gates`, still on
  every PR) and does not touch the production `creative-intel-pipeline` IAM user or its scripts.
