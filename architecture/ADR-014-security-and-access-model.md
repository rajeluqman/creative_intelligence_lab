# ADR-014 — Security & Access Model (simulation-grade)

- **Status:** Accepted
- **Date:** 2026-07-04
- **Deciders:** owner (override + ruling), Fable (design session), Sonnet (build)
- **Context refs:** `architecture/control_plane_lab/saboteur/04_SONNET_HANDOVER.md` U1 (the
  handover this ADR closes); `PROJECT_STATUS.md` ▶ RESUME HERE 2026-07-04 thread; ADR-005
  (owner-override precedent this follows — a scoped addition to the serving layer, not a
  reopening of the whole stack); ADR-006 (`dim_client` tenancy — the data-classification
  inventory below builds on its column list); ADR-013 (`CREATIVE_INTEL_ANALYST_RO` follows the
  same "dedicated, not reused" role precedent set there for CI's role).
- **Does NOT touch:** `CREATIVE_INTEL_ROLE` (the existing operating/pipeline role — unchanged
  grants, unchanged blast radius), any Bronze/Silver object, the AWS OIDC CI role (ADR-013),
  or any Gold/marts model shape (Clean-ERD doctrine untouched — this is an access-layer ADR).

## Context

The 2026-06-22 roster convene rejected porting the full pharma gym "incubator + security"
apparatus wholesale (`BACKLOG.md` Tier 2/3) — a standing security workstream/agent roster for a
single-dev portfolio pipeline was correctly called over-engineering. That ruling still holds.

What changed 2026-07-04: the RBC simulation lab (`simulation/`) now runs drills that
**simulate real on-call work** — "kau on-call engineer" framing, `INCIDENT_RUNBOOK.md`'s 8
phases, the saboteur problem bank's own `T-SEC` category (8 entries, `PROBLEM_BANK_TROUBLESHOOT.md`
lines 114-125). A drill bank that includes credential-leak and RBAC-misconfig scenarios but
has **no real least-privilege role to misconfigure** is simulating against nothing — the gap
is the drill target, not a security *program*. Owner override (same pattern as ADR-005: a
narrow, named addition overriding the default "don't build infra you don't need" instinct):
build the **one real artifact** the drills need — a genuine read-only analyst role, real
GRANT statements, one ADR — and stop there. A 9-file security folder (threat model,
incident-response doc, access-review cadence, etc. as standalone artifacts) was proposed and
**REJECTED** in the same session (see BACKLOG entry this ADR adds).

Verification note: the security posture below was cross-checked informally against a
third-party (ChatGPT) review during the 2026-07-04 design session before the owner's override
ruling — no gap was raised that changes the decision below; noted here per the anti-shortcut
protocol's "tag assumptions" rule rather than silently asserting completeness.

## Decision

### A — RBAC role matrix (real GRANTs, not prose)

Three roles now exist in the Snowflake account, each with a distinct, non-overlapping blast
radius. This is additive: `CREATIVE_INTEL_ROLE` is unchanged.

| Role | Objects | Privileges | Used by |
|---|---|---|---|
| `ACCOUNTADMIN` (bootstrap) | account-level | CREATE WAREHOUSE/DATABASE/ROLE/INTEGRATION | owner only, `--phase account\|storage --apply` (provisioning-time, human-gated) |
| `CREATIVE_INTEL_ROLE` (existing, ADR-005) | `PUBLIC` schema Gold tables + `FACT_CHUNK_VECTOR` view | USAGE+OPERATE on warehouse, USAGE on DB/schema, per-table `SELECT` (named list, no FUTURE grant — the pipeline adds new Gold models via a code change anyway) | the pipeline's own read path (`search_cli.py`, reconciliation) |
| `CREATIVE_INTEL_ANALYST_RO` (**new**, this ADR) | `PUBLIC` schema Gold tables + future tables + `FACT_CHUNK_VECTOR` view | USAGE only on warehouse (no OPERATE), USAGE on DB/schema, `SELECT` on ALL TABLES + **`SELECT` on FUTURE TABLES** in `PUBLIC` | a human analyst account, ad-hoc query only — no Bronze/Silver stage reachable (no stage GRANT exists for this role, by omission — see §B) |

Real GRANT SQL (as emitted by `scripts/provision_snowflake_serving.py`, `--phase account` /
`--phase tables`):

```sql
-- account phase
CREATE ROLE IF NOT EXISTS CREATIVE_INTEL_ANALYST_RO;
GRANT USAGE ON WAREHOUSE CREATIVE_INTEL_WH TO ROLE CREATIVE_INTEL_ANALYST_RO;
GRANT USAGE ON DATABASE CREATIVE_INTEL_DB TO ROLE CREATIVE_INTEL_ANALYST_RO;
GRANT USAGE ON SCHEMA CREATIVE_INTEL_DB.PUBLIC TO ROLE CREATIVE_INTEL_ANALYST_RO;

-- tables phase (after the existing per-table grants to CREATIVE_INTEL_ROLE)
GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO ROLE CREATIVE_INTEL_ANALYST_RO;
GRANT SELECT ON FUTURE TABLES IN SCHEMA PUBLIC TO ROLE CREATIVE_INTEL_ANALYST_RO;

-- search phase
GRANT SELECT ON VIEW PUBLIC.FACT_CHUNK_VECTOR TO ROLE CREATIVE_INTEL_ANALYST_RO;
```

The `FUTURE TABLES` grant is deliberate and is the fix `T-SRV-04` drills: `CREATIVE_INTEL_ROLE`'s
per-table grant list means a newly added Gold model is invisible to that role until the
provisioning script is re-run for it — a real, named gap, left as-is because the pipeline's
own read path is code-reviewed every time a model is added. The analyst role has no such
review gate (a human just runs ad-hoc queries), so it gets the blanket future-table grant
instead — the two roles intentionally use different grant strategies for different reasons,
not an inconsistency.

### B — Data classification inventory

| Data | Where | Classification | Handling |
|---|---|---|---|
| `dim_client.account_support_owner` | `seeds/dim_client.csv` (ADR-006) — a seed + `ref()` FK target for `dim_asset`; **NOT** one of the 8 served `GOLD_MODELS`, and no served table carries this column (verified: no `models/**/*.sql` selects `account_support_owner`) | Internal — names/contact of internal staff, not a client secret, but not for external eyes | **Not reachable by either Snowflake role today** — `dim_client` is not served as an external table, so this column is not in either role's Snowflake blast radius. It lives only in the in-repo seed / DuckDB-side Gold. Flagged as a LATENT exposure: if `dim_client` were ever added to `GOLD_MODELS`, the analyst role's `FUTURE TABLES` grant (§A) would **auto-expose it with no review step** — so that future change must either exclude this column via a serving view or consciously accept the exposure. Not a task for this ADR (no such served table exists) |
| Talent face/voice in raw video (Bronze, `landing/<client_id>/video/`) | S3 landing, subject to ADR-007's 30-day guarded-delete TTL | Sensitive (biometric-adjacent — real people's likeness/voice) | No new handling built here (TTL already bounds retention); the DOWNSTREAM Gemini-derived transcript/theme/sentiment chunks (Silver/Gold) are text, not biometric, and are the only layer `CREATIVE_INTEL_ANALYST_RO` can read — the analyst role never reaches raw video at all (see §A, no stage grant) |
| Chunk transcript text (Silver/Gold) | S3, dbt-duckdb | Client-confidential (creative footage, not public) | Tenant-scoped via `dim_client`/`client_id` (ADR-006); RLS/per-tenant view is named OUT below, not built (single owner is the only real analyst today) |

### C — Audit: platform-native enablement (no custom audit build)

- **S3 side:** rely on the bucket's native server access logging / CloudTrail data events
  (enable-only, not built by this repo — an account-level toggle, not application code).
- **Snowflake side:** rely on `ACCOUNT_USAGE.LOGIN_HISTORY`, `ACCOUNT_USAGE.QUERY_HISTORY`, and
  `ACCOUNT_USAGE.GRANTS_TO_ROLES` (all native, retained per Snowflake's default window) to answer
  "who read what, and does the grant matrix actually match this ADR" — queried ad hoc, not piped
  into a dashboard.
- **REJECTED:** a custom audit-log table/pipeline (a new fact-grain access-log model, a
  Lambda-on-CloudTrail shipper, etc.). Rejected as reinventing what the platform already retains natively, for a
  single-owner project with no compliance mandate requiring a custom retention/format — see the
  BACKLOG entry this ADR adds.

### D — PDPA / talent consent: named, not built

No consent-tracking mechanism exists or is built by this ADR. This project's clients are
real registered entities (`dim_client`) but the footage-owner talent-consent chain (did the
client obtain consent from the people on camera) is **out of this pipeline's scope by
construction** — this repo ingests already-delivered client footage, it does not manage the
client's own consent paperwork. Named here (not silently absent) so that if this ever became
a real multi-client SaaS onboarding flow, the answer to "where would consent tracking attach"
is: at client onboarding, alongside the `dim_client` seed row, before the first landing write
— not retrofitted onto Gold.

## Rejected alternatives

1. **9-file security folder** (threat model, incident-response doc, access-review cadence,
   secrets-management policy, etc. as standalone top-level docs) — rejected same session.
   Redundant with what already exists in ADR form + the saboteur runbook's 8-phase lifecycle;
   more reviewers-of-prose than a single-dev project needs. See BACKLOG entry.
2. **`threat_model.md` / `incident_response.md` as standalone docs** — rejected for the same
   reason; the *simulated* incident-response motion already lives in
   `simulation/CIKGU_DRILL_PROTOCOL.md` + `INCIDENT_RUNBOOK.md`, and a *real* one would be
   written against a real incident, not speculatively.
3. **Custom audit-log build** — see §C. Reinvents native platform logging.
4. **Row-level-security policy on Gold serving views, scoped per external analyst** — rejected
   for now: there is no external analyst account today, only the owner querying via
   `CREATIVE_INTEL_ANALYST_RO` for drill purposes. Building RLS ahead of a real second query
   identity is speculative; `dim_client`/`client_id` scoping (ADR-006) already exists in the
   model and is the mechanism an RLS policy would key off when a real second identity appears.
5. **Building a PDPA consent-tracking workflow now** — rejected, no real client onboarding flow
   exists yet to attach it to (v1 is the permanent scope per `CLAUDE.md`); named-not-built per §D.

## Consequences

- **Positive:** the saboteur bank's `T-SRV-04` (RBAC misconfig) and `T-SEC-01` (credential
  leak) drills now exercise a real role/grant pattern instead of a purely hypothetical one;
  `provision_snowflake_serving.py` gains idempotent grant additions, no new required env var for
  dry-run.
- **Negative / accepted:** the analyst role's `FUTURE TABLES` grant (§A) is a deliberate trade —
  it removes the per-model provisioning-drift bug at the cost of auto-exposing any future served
  Gold model with no review step. The one column flagged Internal today
  (`dim_client.account_support_owner`, §B) is **not** currently in either role's Snowflake blast
  radius (`dim_client` is a seed, not a served table), so there is no present-day exposure to
  accept; the accepted risk is purely the latent one — if `dim_client` is ever served, the future
  grant exposes that column silently unless a serving view excludes it first.
- **Bounded:** this ADR governs only the new analyst role and the audit/classification/consent
  rulings above. It does not reopen ADR-005's serving architecture, ADR-006's tenancy model, or
  ADR-013's CI federation.
