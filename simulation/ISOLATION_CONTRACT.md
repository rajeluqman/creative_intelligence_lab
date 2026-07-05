# Isolation Contract — RBC Simulation Lab

> **Purpose:** guarantee the sim lab can never corrupt the real ("main") pipeline. This is what makes
> deliberate fault-injection and optimization drills *safe* — break the sim all you want, main is
> untouchable. Enforced by `python simulation/check_isolation.py` (deterministic, no AWS). Run it
> before every sim session **and** before committing any sim work. PASS required.

This mirrors the repo's existing governance-as-code philosophy (lineage/boundary/doc contracts):
the rule is a script, not vigilance.

---

## The rules

**R1 — Own S3 prefix.** Everything the sim reads or writes lives under
`s3://creative-intel-staging/sim/<scenario>/...` (the staging bucket is already declared throwaway
in `.env.example`). The sim must **never** reference `s3://creative-intel-lake/...` (the canonical
lake) or the real `landing/`, `bronze/`, Silver/Gold paths. *Guard:* every `s3://` literal in a sim
file must contain `/sim/`.

**R2 — Own dbt project.** The sim has its own project at `simulation/sim_dbt/` named
`sim_creative_intel` with profile target `sim`. It must **never** share the real project name
(`creative_intelligence`) or be built from the repo root. *Guard:* sim `dbt_project.yml` `name` ≠
real `name`.

**R3 — No cross-refs.** No sim model may `ref()` a real model, and no sim file may read a real seed
by name. The sim's "legacy source" is synthetic, generated from sim seeds. *Guard:* no `ref('<real
model>')` appears in any `simulation/**/*.sql`.

**R4 — Real tree is read-only.** `models/`, `seeds/`, `architecture/`, `confluence/`, `dags/`,
`tests/`, and all ADRs are **reference-only** for the sim — read them to learn the patterns, never
edit them from a sim task. (Promoting a *finished* writeup into `confluence/` is a separate,
explicit owner decision — not part of any sim run.)

**R5 — Faults stay in the lab, and reset is total.** Fault injection happens only inside
`simulation/`. The clean state must be fully rebuildable from sim seeds (`faults/reset.py` =
re-seed + re-build sim), never hand-patched — so every drill starts from an identical baseline.

---

## What the guard checks (and what it can't)
`check_isolation.py` statically enforces R1, R2, R3 — the high-value, low-false-positive boundaries.
R4 and R5 are partly human discipline (a static check can't prove a future write won't happen), but
R3's no-cross-ref rule + R1's no-canonical-path rule make an accidental main write very hard. If you
extend the lab, keep new `s3://` paths under `/sim/` and new models inside `sim_dbt/` and the guard
stays green automatically.

## If a rule and a task conflict
STOP and surface it (same as the main project's STOP-GATE). Do not "just this once" point the sim at
the real lake or edit a real model — that's exactly the failure mode the lab exists to prevent.
