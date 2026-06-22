# Build quickstart
1. `bash setup.sh`            # scaffold + venv + deps + dbt parse
2. `cp .env.example .env`     # fill GEMINI_API_KEY, S3_BUCKET
3. `cp profiles.yml.example ~/.dbt/profiles.yml`  (or set DBT_PROFILES_DIR=.)
4. Implement the stubs marked `where 1=0` / `TODO` using architecture/SPEC_v1.5_performance_marts.md
5. `dbt seed && dbt build -s marts.core`     # v1 first
6. `dbt build -s marts.performance` + `python scripts/significance_post_step.py`   # v1.5
Architecture of record: architecture/  (DATA_MODEL*, SPEC*, ADR-00*, STACK_AND_FLOW, ERD*, DBT_DAG)
