# Learning Log — Creative Intelligence Pipeline

> @cikgu's memory + the user's progress record. Newest entries at the TOP.
> On resume, @cikgu reads the last 3 entries + the current module in `CURRICULUM.md`.

**Current score:** 100/100
**Current module:** M0 — not started
**Next step when resuming:** start M0 (the domain & the goal) — `@cikgu teach me Module 0`

---

[2026-06-27 — T-L01 PASSED]
Module: simulation/ training gym, Troubleshoot ladder L1
Concept: Duplicate PK / grain violation. Derived root-cause method unprompted (check landing
content-hash to tell data-dup vs code-dup), identified the naive-DELETE trap before being told,
fixed via ROW_NUMBER() PARTITION BY grain key, verified gate (0 rows) + mart value with real
command output (not eyeballed).
Hint level: mostly H0-H1 (nudge/narrow); one H2 (Socratic) to land the row-identity dedup concept.
Refs: simulation/drills/T-L01_dup_pk.md, simulation/runbook/T-L01_dup_pk.md,
simulation/.solutions/T-L01_dup_pk.md
Score impact: PASS (methodology — observability-first, one hypothesis at a time, evidence-gated,
reconciled before declaring done)
Next step when resuming: run O-O01_full_scan.md, or hand off T-L02..L10 + O-O02..O06 to a Sonnet
session via simulation/SONNET_KICKOFF_PROMPT.md.

[2026-06-21 — setup]
Module: —
Concept: Curriculum + cikgu apparatus created. 11 modules (M0-M10) mapped to real artifacts.
Hint level: —
Refs: learning/CURRICULUM.md, .claude/agents/cikgu.md
Score impact: 0
Next step when resuming: begin M0. The build artifacts already exist (they are the answer key);
the job is to RE-DERIVE them, not read them cold. Start by answering "what are the 3 legs of the
goal?" before opening any doc.
