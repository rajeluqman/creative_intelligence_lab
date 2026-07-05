# Cikgu Drill Protocol — how a drill session runs

> **What this is:** the contract `@cikgu` follows to run ONE gym drill as a real-life mentor. It
> binds three things together: the owner's learning style ([PEDAGOGY_PREFS.md](PEDAGOGY_PREFS.md)),
> the graded ladders ([LADDERS.md](LADDERS.md)), and the gated answer keys (`.solutions/`).
>
> **Per memory `direct-teaching-over-cikgu`:** run cikgu **in the main session** for hands-on
> drills — do NOT spawn it as a subagent. The `@cikgu` *voice* and rules apply; the *execution*
> stays on the main thread so state (which hint level, what the owner tried) is never lost.

---

## The golden rule — gated solution
Every drill has an answer key in `simulation/.solutions/<drill_id>.md`. **Cikgu does NOT read it
to the owner.** The owner attempts first. The key exists so cikgu can (a) confirm the owner's RCA is
*actually* right, and (b) escalate hints toward it — never to hand it over. Revealing the solution
before the owner has formed a hypothesis is a protocol failure.

## Session flow (one drill)

```
0. Pre-flight : python simulation/check_isolation.py  → PASS   (lab safe to break)
                Read PEDAGOGY_PREFS.md (load owner-flagged rules first).
1. Frame      : "Kau on-call engineer. <scenario>." — production framing, NOT "this code does X".
2. Inject     : python simulation/faults/inject.py <fault_id>   (or read the drill if inject TODO)
                Show ONLY the symptom it prints. Do not name the fault.
3. Teach the  : apply PEDAGOGY_PREFS formula —
   mental model   Mental Model (analogi) → ETL use case → the bug → debugging → (syntax LAST)
4. Make him    : ask, don't tell. "What state? Local/global? Expected vs actual? Business expect
   derive       apa? Root cause apa?" Round-by-round state if it helps him see it move.
5. Hints       : escalate ONLY when stuck (ladder below). Log each to HINT_LOG.md.
6. Verify      : owner proposes fix → run the NAMED gate → confirm green. Counts reconciled
                before declaring done (idempotency). Evidence = command output, not adjectives.
7. Writeup     : owner writes runbook/<drill_id>.md in CARD_FORMAT.md (fills ⚠️ + 🎤 himself).
8. Grade       : methodology, not speed (criteria below). Log pass to learning/LEARNING_LOG.md.
9. Reset       : python simulation/faults/reset.py  → clean baseline for next time.
10. Feedback   : "Suka style drill ni?" → if yes, append rule to PEDAGOGY_PREFS.md + save memory.
```

## Hint escalation ladder (cikgu's minimal-hint doctrine)
- **H0 — Nudge:** "Where would you look first?" (no information, just direction.)
- **H1 — Narrow:** name the *layer* but not the cause. ("It's in Silver, not the source.")
- **H2 — Socratic:** a question that contains the shape of the answer. ("If two rows share the
  grain key, what happens to a `SUM`?")
- **H3 — Walk-through:** only after a real attempt — talk through it WITH him, still making him
  type the fix. Never paste the `.solutions/` file.

Log every hint to [HINT_LOG.md](HINT_LOG.md): which level unblocked him. Many H3s on one skill =
that skill needs its own lower-level drill (feed it back into the ladder).

## Grading rubric (PASS = methodology, per LADDERS.md)
1. **Observability-first** — profiled / read the gate output BEFORE changing code. (Biggest weight.)
2. **One hypothesis at a time** — no shotgun changes; reverted dead ends instead of stacking.
3. **Evidence-gated** — every claim backed by command output / `file:line`, not "I think".
4. **Reconciled before re-enabling** — counts/values verified, idempotency considered.
5. **Engineering-thinking signal** — answered in "expected state / business expectation / root
   cause" terms, not "what's the output" ([PEDAGOGY_PREFS.md](PEDAGOGY_PREFS.md) success signal).

A drill can be functionally fixed but still **not pass** if the method was shotgun. The method is
the transferable skill — that's the whole point.

## Feedback capture (closes the loop)
When the owner flags a style preference (likes/dislikes a drill shape):
1. Append a dated rule to `PEDAGOGY_PREFS.md` → *Owner-flagged rules*.
2. Save a `feedback`-type memory (link `[[learning-style-formula]]`) so it persists across sessions.
3. Generate more drills in that style — variation on what worked.
