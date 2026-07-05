# Incident Runbook — the 8-phase lifecycle every troubleshoot drill follows

> This is the step-by-step the owner asked for ("tengok airflow log → inform stakeholder →
> kuarantin → sampai pipeline run macam biasa"). Every T-drill is graded against these phases,
> not just against "did the bug get fixed". Phases 2, 7, 8 are what make it senior-level.

## Phase 0 — DETECT
Signal arrives: Slack failure alert / GE gate red / consumer complains ("dashboard kosong").
- Record detection time (MTTR clock starts). Note WHO detected — if a human downstream beat
  the alerting, that itself is a postmortem finding (observability gap).

## Phase 1 — TRIAGE & SEVERITY
Answer three questions in <10 minutes, evidence-first:
1. **What exactly is failing?** Airflow UI → failed task → task log (not the DAG log) →
  the actual stack trace / engine error. Never diagnose from the alert text alone.
2. **Blast radius?** Which tables/marts are stale or wrong; which consumers read them.
3. **Severity call:** P1 wrong-data-being-consumed (worst — silent lie) · P2 pipeline down,
  data stale · P3 degraded/slow · P4 cosmetic. Wrong data outranks no data.

## Phase 2 — COMMUNICATE (initial) — BEFORE fixing
Send the first notice as soon as severity is known, not when the fix is ready:
> **[P2][creative-intel] Silver build failing since 03:00 UTC.** Impact: gold marts stale as of
> yesterday 18:00; today's refresh will be late. Dashboards show yesterday's data (correct but
> old). No wrong data served. Investigating; next update 30 min.
Rules: state impact in CONSUMER terms, state what is safe to keep using, commit to the next
update time. Silence is how trust dies — a stale dashboard with a notice is an inconvenience;
a stale dashboard without one is an incident about YOU.

## Phase 3 — CONTAIN / QUARANTINE
Stop the bleeding before root-causing:
- **Pause the DAG** (and dependent DAGs) — no more bad output.
- **Quarantine, never delete:** move suspect partitions/files to `quarantine/<incident_id>/`
  (or snapshot the bad table state). This preserves evidence AND unblocks reruns.
- If wrong data already reached serving: mark/rollback the serving view (serving = view, so
  point it at the last-good snapshot) and say so in comms.

## Phase 4 — DIAGNOSE
The debugging motion (PEDAGOGY_PREFS: state → expected vs actual → business expectation → root cause):
- Bisect the failure class: **data** (source changed?) vs **code** (what deployed recently?) vs
  **infra** (quota/disk/creds?) vs **upstream** (did the provider backfill/rename?).
- Reproduce in sim/staging with the quarantined sample — never debug by re-running prod blind.
- Root cause = the sentence that explains ALL observed symptoms, not the first plausible one.

## Phase 5 — FIX
Smallest reversible change, on a branch, through the normal gates (contracts + tests). A fix
that bypasses the gates "because incident" is how the next incident gets planted.

## Phase 6 — RECOVER & VALIDATE
- Rerun idempotently (this is why skip-existing/merge-on-key exists — rerun must be safe).
- Backfill the gap window explicitly (parameterized, not hand-edited code).
- Validate with the NAMED gate: GE suite green, reconciliation counts match source
  (`row_count(gold) == row_count(source) - rejected(quarantine)` — account for every row).
- Only now unpause the DAG.

## Phase 7 — COMMUNICATE (resolution)
> **[RESOLVED][creative-intel]** Root cause: upstream added a column 03:00, strict schema gate
> rejected batches (by design). Fixed by X; backfilled 03:00–14:00; all gates green; dashboards
> current as of 14:30. No wrong data was served at any point.
State what was affected, what was corrected, and the guarantee ("no wrong data served" or
"rows X–Y were wrong between T1–T2 and have been corrected" — whichever is TRUE).

## Phase 8 — POSTMORTEM (blameless, produces an artifact)
Timeline · 5-whys to the systemic cause · and at least ONE prevention artifact merged:
a new DQ expectation, a new contract check, an alert, or an ADR addendum. An incident that
produces no new gate will repeat. Log the drill/incident in the repo's runbook + LEARNING_LOG.

---

## Worked example (CIL, T-DQ-09 class): Gemini schema drift
0. **Detect** — GE silver suite red at 03:12: `chunk_theme` null-rate 41% (threshold 2%).
1. **Triage** — Airflow task log: parse step OK; GE gate failed → build stopped BEFORE gold.
   Blast radius: gold marts stale, not wrong. Severity P2.
2. **Comms #1** — "creative feature store refresh late; yesterday's data still valid; next update 30m."
3. **Contain** — pause `creative_intel_pipeline`; move the night's raw JSON batch refs to
   `quarantine/inc-2026-07-04-01/` (raw stays append-only in landing — quarantine is a marker,
   not a rewrite of Bronze).
4. **Diagnose** — diff one quarantined response vs golden dataset: Gemini started returning
   `chunkTheme` (camelCase) after a model-version bump — parser expected `chunk_theme`.
   Root cause: prompt pinned, model version not.
5. **Fix** — parser accepts both keys + `GEMINI_MODEL` pinned explicitly; branch, gates green.
6. **Recover** — re-parse the SAME stored raw responses ($0 — this is why Bronze stores
   word-for-word); GE green; reconciliation: 100% of assets re-parsed, 0 re-billed.
7. **Comms #2** — resolved; nothing wrong ever served; refresh complete 09:40.
8. **Postmortem** — new GE expectation: response-key schema check at Bronze parse (fail fast, not
   at Silver); ADR addendum: model version pinning policy. Drill card written per CARD_FORMAT.
