# Sim #2 — PySpark Parity (close the "no Spark" gap)

**Objective:** reproduce ONE `migrated/` dbt transform in PySpark and prove identical output —
so you can say "same business logic, two engines (dbt-SQL and Spark)", which is literally the
Teradata-SQL → Spark motion at RBC.

**RBC tasks covered:** 46 (express dbt transform in PySpark), 45/61/70 (Spark transferable).

**⚠️ BOUNDARY GUARD (do not skip — surfaced from `tests/boundary_contract.py`):**
The boundary contract bans `pyspark`/`databricks` imports in `scripts/*.py`, `dags/*.py`,
`models/**`, and root `requirements*`/shell/env. To stay green:
- The notebook/script lives in **`simulation/spark/`** only (outside the scanned globs).
- Declare `pyspark` ONLY in **`simulation/spark/requirements.txt`** — **never** root `requirements.txt`
  or `setup.sh`.
- After building, run `python tests/boundary_contract.py` and confirm it's still PASS. If it goes
  red, you put Spark somewhere the product can see it — move it back into `simulation/spark/`.

**Interview story (STAR):**
> S/T: same logic must run on Spark (RBC target). A: re-expressed migrated transform in PySpark,
> diffed vs dbt output. R: byte/value-identical → "engine-portable logic". (fill specifics)

## Sonnet steps
1. `simulation/spark/requirements.txt` → `pyspark`. Set up a local SparkSession (local[*]).
2. `simulation/spark/parity_<model>.py` — read the same sim input, reproduce ONE `migrated/`
   transform's logic in DataFrame ops.
3. Write both outputs to `s3://creative-intel-staging/sim/parity/{dbt,spark}/` (or local sim paths).
4. Diff: full anti-join both directions; assert 0 rows differ. Save `runbook/02_parity_report.md`.
5. Map the Spark concepts you used to your DuckDB optimization thinking (1 short table) — interview gold.

## Definition of Done
1. `python tests/boundary_contract.py` → PASS (Spark stayed in the sandbox).
2. `python simulation/check_isolation.py` → PASS.
3. Diff = 0 rows both directions; `runbook/02_parity_report.md` has the evidence.
4. STAR row filled.
