# BACKLOG — Creative Intelligence Pipeline (post-v1)

> Items deferred out of v1 scope. Nothing here is built until v1 (the queryable creative
> feature store) ships and is demo-able. See `AGENT_ROSTER_RECOMMENDATION.md` + CLAUDE.md
> "v1 Scope (LOCKED)".

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

## Other v2 items (from CLAUDE.md "v1 Scope OUT")
- AI creative search engine (app on top of the feature store)
- RAG script/brief generator
- Creative-ops analytics dashboard
- Automated tagging / asset archiving
- ROAS / ad-performance ingestion beyond the within-winners correlation layer
- Dedicated vector DB (DuckDB VSS covers v1.5 semantic search)
