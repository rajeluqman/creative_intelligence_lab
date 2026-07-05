# Card Format — drill writeups & runbook entries

> Imported from pharma's troubleshooting/optimization cheatsheet template. Every drill writeup in
> [runbook/](runbook/) uses this. The two fields that make it interview-grade are **⚠️ Junior
> mistake** and **🎤 Soundbite** — they convert a fixed bug into a STAR story.
>
> **Authoring rule (R from [faults/README.md](faults/README.md)):** drill writeups are SIMULATED.
> They live in `simulation/runbook/`, clearly labeled, and are **never** promoted into the real
> `cheatsheets/` (that gate needs a real post-v1 incident — faking it is forbidden).

---

## Troubleshooting card

```markdown
## T-L0X — <short title>            <status badge>

- **Scenario**     : kau on-call engineer. <one-line production framing>
- **Symptom**      : <what surfaces — usually far downstream, not at the root>
- **Diagnosis**    : <triage steps that confirm root cause — observability first>
- **Root cause**   : <the structural reason; round-by-round state if it helps>
- **Fix / Recovery**: <the change + how you verified the gate goes green; idempotency note>
- **Evidence**     : <file:line of the fix · gate command output · run_results.json>
- **⚠️ Junior mistake** : <the false-confidence trap a junior falls into here>
- **🎤 Soundbite**  : <one sentence you'd say in an interview / standup>
```

## Optimization card

```markdown
## O-O0X — <short title>            <status badge>

- **Scenario**     : <slow/skewed job framing>
- **Symptom**      : <where it's slow — long tail / full scan / memory>
- **Profile (before)**: <EXPLAIN ANALYZE finding + baseline timing — REAL number>
- **Hypothesis**   : <ONE hypothesis>
- **Change**       : <the ONE change · file:line>
- **Profile (after)**: <new timing · the delta "X → Y, -Z%">
- **→ Spark vocab**: <how you'd phrase this diagnosis for a Databricks interview>
- **⚠️ Junior mistake** : <e.g. "speculative tuning — changed 3 things, can't attribute">
- **🎤 Soundbite**  : "I optimize from evidence — profile first, change one thing, measure."
```

## Status badges
- `✅ PASSED` — drill completed, gate green, evidence attached, STAR row filled.
- `🟡 IN PROGRESS` — attempted, not yet green / not yet reconciled.
- `⚪ NOT STARTED` — drill exists, not attempted.

## The rule that keeps it honest
No card is `✅ PASSED` on a parse-clean or an eyeball. Run the named gate, attach the command output.
No evidence = `🟡`, not `✅`. (CLAUDE.md anti-shortcut protocol, in the lab.)
