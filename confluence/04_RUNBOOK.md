# Runbook

> ## 🚧 STATUS: STUB — Phase-5/post-ship gated
> **This page is intentionally empty of procedures.** Per the 2026-06-22 doc-gap convene
> (`PROJECT_STATUS.md` → "Doc-gap convene"), a Runbook was explicitly assessed and **deliberately
> NOT written yet** — it's a Phase-5/post-ship artifact, and Gold/serving are still partially stub
> (`bridge_asset_lineage`, `fact_extraction_run`; Snowflake Cortex serving not built — see **Known
> Issues**). Writing rerun procedures for a pipeline that isn't fully serving yet would mean
> inventing steps nobody has actually run, which this project's own no-fabrication convention
> rejects (same rule the troubleshooting cheatsheet enforces: every card cites a real fix, no
> invented incidents).
>
> **Gate to write this for real:** v1 fully ships to serving (Snowflake or DuckDB VSS, live) AND at
> least one real rerun-after-failure has actually happened, so the procedure can cite a real
> `file:line`/command, not a guess.
> **Owner today:** @senior-data-engineer (owns the Airflow DAG + the scripts a runbook would
> reference).

## What exists today, for reference (not a runbook, just pointers)
- Idempotent skip-existing re-run: `dags/creative_intel_pipeline.py` (the whole DAG is safe to
  re-trigger — `list_new_assets` finds only unextracted assets).
- Guarded landing-TTL delete: `scripts/enforce_landing_ttl.py`'s `--apply` flag (dry-run by default).
- Manual Confluence/Slack re-sync: `python scripts/sync_docs_to_confluence.py` (see ADR-009).

When a real "pipeline failed, here's how I fixed it" happens, that's the seed for this page — write
it from the real fix, the same rule the troubleshooting cheatsheet already follows.
