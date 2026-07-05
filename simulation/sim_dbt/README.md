# sim_dbt — isolated simulation dbt project

> Project name `sim_creative_intel`, profile `sim_creative_intel`, target `sim`. Writes only to the
> local sim DuckDB or `s3://creative-intel-staging/sim/...`. **Never** shares a name, profile, or
> path with the real `creative_intelligence` project (enforced by `../check_isolation.py`).

## What Sonnet builds here (per `../specs/01_SIM_migration_dryrun.md`)
1. **`seeds/`** — a synthetic "Teradata extract": a small denormalized CSV (e.g. ad-spend or
   transaction-style rows) with deliberate legacy traits (mixed types, embedded business logic).
   Pin column types in `dbt_project.yml` so `dbt seed` is stable.
2. **`models/legacy/`** — the **source-of-truth** replica: one or more models that encode the
   "Teradata SQL / BTEQ" logic *as-is* (the thing we're migrating FROM). This is the baseline every
   reconciliation compares against.
3. **`models/migrated/`** — the **target**: the same business logic re-expressed in clean
   dbt-SQL (the "Snowflake" rebuild). Must produce values that reconcile to `legacy/` to the cent.

## Run
```bash
export DBT_PROFILES_DIR=simulation/sim_dbt        # or merge profiles.sim.yml.example into ~/.dbt
cd simulation/sim_dbt
dbt seed && dbt build                              # builds legacy + migrated into target/sim.duckdb
```

## Rules
- Stays inside this folder. No `ref()` to real models. No `s3://creative-intel-lake/...`.
- Clean state is rebuildable from `seeds/` alone (so `faults/reset.py` = `dbt seed && dbt build`).
- Run `python simulation/check_isolation.py` before committing.
