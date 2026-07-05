# Saboteur Problem Bank — architecture (Fable design, 2026-07-04)

> The master catalog @saboteur draws from: 100 troubleshooting problems + 100 optimization
> tasks covering the ~90% of real pipeline-maintenance work, mapped across all 8 owner repos.
> Designed to be ported into `airflow_dag_running_pipeline` when the control-plane lab is built
> (Fasa per `../02_SONNET_BUILD_KICKOFF.md`); usable NOW from each repo's own `simulation/`.

## How the bank relates to what already exists
- **Bank entry ≠ drill card.** The bank is the *instructor sheet* (catalog row: symptom + root
  cause + fix direction). When a drill runs, @saboteur/[@sre-incident-commander] expands ONE
  entry into a full card per `simulation/CARD_FORMAT.md` (Scenario/Symptom/Diagnosis/…/Soundbite)
  — revealing ONLY Scenario+Symptom to the learner. Root-cause column is the answer key.
- **Pedagogy contract applies** (`simulation/PEDAGOGY_PREFS.md`): production framing first
  ("kau on-call engineer"), doc-pointer hints not handed syntax, explicit run/visual-output
  mechanics, one new concept per session, syntax last.
- **Scoring** stays the LEARNING_LOG convention (start 100, hint −5, badge on gate-green +
  evidence). No card passes on an eyeball — named gate output required.

## Where drills execute (the staging question — settled)
Two surfaces, one runbook:

1. **Drills (simulated incidents)** — ALWAYS in the isolated surface: per-repo `simulation/`
   under its ISOLATION_CONTRACT (own storage prefix e.g. `S3_STAGING_BUCKET`/sim schema, own
   compute project, no refs into real models), on a throwaway branch (`drill/<id>`), never
   `main`. In the control-plane lab: **staging env only**, enforced by
   `saboteur_containment_contract.py` (declared blast radius, reversible reset, no prod
   credential reachable from `faults/`).
2. **Real incidents (when they happen)** — the SAME runbook runs against the real pipeline, but
   containment = **quarantine, not deletion**: bad partitions/files MOVE to a
   `quarantine/<incident_id>/` prefix (append-only evidence), DAG paused, downstream marked
   stale. The drill exists so this motion is muscle memory before it's real.

**Optimization: yes, staging too** — with a stricter loop: baseline measured in sim → ONE
change → re-measure → keep/revert → only then PR to the real repo. An optimization without a
before/after number is not done (CARD_FORMAT requires the real numbers).

## Stack tags → repo mapping
| Tag | Meaning | Applies to |
|---|---|---|
| AF | Airflow orchestration | CIL, home-credit, olist, airflow_dag_running_pipeline (control-plane) |
| DBT | dbt models/incremental/snapshots | CIL, home-credit, olist, paysim, pharma_novartis_sttm |
| SPK | Spark: Databricks/Glue/PySpark/Delta | home-credit (Glue), olist, paysim, Volve (Databricks) |
| SF | Snowflake serving/warehouse | CIL, home-credit, olist, paysim |
| S3 | Object storage S3/ADLS (landing/lake) | all pipeline repos |
| DDB | DuckDB transform engine | CIL |
| GE | Great Expectations / DQ gates | CIL, home-credit, paysim |
| LLM | Gemini extraction step (non-deterministic) | CIL |
| FAB | Fabric/OneLake | migration_fiber_home_credit_risk |
| ALL | stack-agnostic (process/design problem) | all 8 |

One bank, 8 repos: a drill instantiates an entry ON a specific repo whose tags match. The same
`T-TRF-07` (SCD2 overlap) can run on olist (MERGE-expire) or home-credit (dbt snapshot) — same
mental model, different syntax layer, which is exactly the pedagogy order.

## Difficulty ladder (the road to "senior")
- **L1** — detect & read: find the failing task, read the right log, name the symptom precisely.
- **L2** — diagnose & fix: root-cause from signals, smallest reversible fix, validated rerun.
- **L3** — own the incident: L2 **plus** severity call, stakeholder comms, quarantine decision,
  backfill plan, postmortem with a prevention artifact (new gate/DQ rule/ADR addendum).

The senior claim is L3, and L3 is mostly NOT technical: the differentiator columns are the
comms + prevention phases of `INCIDENT_RUNBOOK.md`. A candidate who fixes fast but never
quarantines, never informs, never prevents recurrence is a strong mid, not a senior.

## Files
- `PROBLEM_BANK_TROUBLESHOOT.md` — 100 entries, 8 categories (T-ING/ORC/STO/TRF/DQ/SRV/SEC/INF)
- `PROBLEM_BANK_OPTIMIZATION.md` — 100 entries, 8 categories (O-LAY/QRY/SPK/DDB/WH/ORC/CST/DSN)
- `INCIDENT_RUNBOOK.md` — the 8-phase step-by-step (detect → … → postmortem) every T-drill follows

## Control-plane repo port note (per `../01_OPUS_DECISIONS.md`)
This whole `saboteur/` folder — bank + runbook + `../../../simulation/faults/catalog/`'s
CIL-injectable mapping — moves **wholesale** into `airflow_dag_running_pipeline` when its Fasa-1
build happens (it is a stack-agnostic instructor sheet, not CIL-specific content). Once it lives
there, `saboteur_containment_contract.py` must treat the bank as **read-only input**: `@saboteur`
picks entries from it to build a live drill, but never edits an answer key (Root cause / Fix
direction columns) mid-drill — that would defeat the "gated answer" pedagogy contract
(`../../../simulation/CIKGU_DRILL_PROTOCOL.md`) the same way editing a test's answer key while a
student is taking it would. Row edits happen out-of-drill, as a deliberate bank-maintenance act,
same discipline as this session's read of the bank never changing its 100+100 counts or IDs.
