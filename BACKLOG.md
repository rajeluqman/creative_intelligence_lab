# BACKLOG — Creative Intelligence Pipeline (rejected / closed items, historical record)

> v1 (the queryable creative feature store) is the **entire, permanent** scope of this project
> (owner decision 2026-06-27) — there is no future build queue anymore. This file is now a
> closed record of what was considered and rejected, not a to-do list. See
> `AGENT_ROSTER_RECOMMENDATION.md` + CLAUDE.md "v1 Scope (LOCKED)".

## Gym apparatus port — DEFERRED / PARTLY REJECTED (cabinet convene 2026-06-22)

The owner proposed porting the full pharma gym apparatus (troubleshooting + optimization
cheatsheet libraries, an incubator + sealed-rubric incident-drill loop, and 3 gym agents:
bottleneck-saboteur / incident-responder / optimization-librarian). The roster convene ruled:

| Tier | Disposition | Owner / condition |
|------|-------------|-------------------|
| **1. Cheatsheet libraries** (DuckDB-native troubleshooting + optimization) | **BACKLOG — v1.5/v2** | Gated on v1 shipping **AND** ≥1 real incident hit during the build to document. Shrunk to a single **doc, SDE-owned, no dedicated agent/workstream**. English, DuckDB-native, real `file:line` citations, zero Spark/MinIO content. Needs `ADR-005` + @scope-guardian co-sign before authored. |
| **2. Incubator + incident-drill loop** | **REJECTED** (not backlog) | Safety-cage for a production target that does not exist. If ever wanted, it is a *fresh* proposal against a shipped v1, sized to v1's real needs — not a port. |
| **3. Gym agents** (saboteur / incident-responder / optimization-librarian) | **REJECTED** (not backlog) | Re-litigates the roster decision (`AGENT_ROSTER_RECOMMENDATION.md` line 29) with no new evidence. More reviewers than builders on a single-dev build. |

**Cost guard (FinOps, if Tier 1's golden-dataset drilling ever happens):** any drill that
touches the Gemini ingestion/extraction boundary must route through a frozen Bronze fixture or
a fail-closed `GEMINI_STUB_MODE` replay flag (exact-match convention) — never live API in a
loop. Downstream (Silver/Gold/GE/orchestration) drills are cost-safe.

**Tier-1 stub ownership ruling (co-sign 2026-06-22, @senior-data-engineer + @scope-guardian):**
Tier-1 stays **index-only** — the two existing `cheatsheets/{troubleshooting,optimization}/00_INDEX.md`
files ARE the single-doc stub. Decision: do **not** scaffold the ~16 empty per-phase/per-layer
card files (premature sprawl vs the "shrink to a single doc" line above). A real card is authored
inline in the index when the gate trips (v1 ships AND a real incident/perf-finding lands, with a
real `file:line`); a phase/layer is split into its own `0N_*.md` file only at **≥3–4 real cards**
(lazy split on volume, not taxonomy). The co-sign is a single event covering all future cards —
no per-card review ritual. The pharma `INCUBATOR.md` drill-loop reference in the troubleshooting
index is now explicitly relabelled **REJECTED** (was "optional"), per Tier 2/3 above.

## Other "v2" items — REJECTED 2026-06-27 (owner decision, not deferred anymore)

These were originally framed as "v2 BACKLOG" — implying a possible future build. **Owner
decision 2026-06-27: this project is solely the data pipeline (the queryable creative feature
store). There is no v2 app horizon.** Kept named here (not deleted) per this project's own
Clean-ERD convention — "what's deliberately OUT stays named" — so a future reader sees these
were considered and rejected, not forgotten:
- AI creative search engine (app on top of the feature store)
- RAG script/brief generator
- Creative-ops analytics dashboard
- Automated tagging / asset archiving
- ROAS / ad-performance **live-connector ingestion** (note: the v1.5 performance *marts* that
  consume a hand-supplied export are NOT rejected — they're core pipeline, just waiting on real
  data; only the "build a maintained Meta/TikTok API integration" piece is rejected)
- Dedicated vector DB (DuckDB VSS / Snowflake native `VECTOR` already cover semantic search at
  this data volume — building a separately-hosted vector DB here would be over-engineering, not
  a missing feature)

## Security layer scope — REJECTED items (2026-07-04, ADR-014)

The 2026-07-04 Fable design session ruled `CREATIVE_INTEL_ANALYST_RO` (a real, minimal RBAC role)
IN — see `architecture/ADR-014-security-and-access-model.md` — but rejected building a standing
security *program* around it, same discipline as the gym-apparatus ruling above:

- **9-file security folder** (threat model, incident-response doc, access-review cadence,
  secrets-management policy, etc. as standalone top-level docs) — rejected. Redundant with the
  ADR + the saboteur `INCIDENT_RUNBOOK.md`'s 8-phase lifecycle already in this repo; more
  reviewers-of-prose than a single-dev project needs.
- **`threat_model.md` / `incident_response.md` as standalone docs** — rejected for the same
  reason; the simulated version already lives in `simulation/CIKGU_DRILL_PROTOCOL.md` +
  `INCIDENT_RUNBOOK.md`, and a real one would be written against a real incident, not
  speculatively.
- **Custom audit-log build** (a bespoke access-log table/pipeline) — rejected. Reinvents what S3
  access logging + Snowflake `ACCOUNT_USAGE` already retain natively; see ADR-014 §C.
