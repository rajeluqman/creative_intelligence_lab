# Pedagogy Preferences — How Luqman Learns

> **Why this file exists:** the gym adapts to the learner, not the other way round. This is the
> living profile `@cikgu` reads at the START of every drill so the teaching matches the style that
> is *proven* to work for the owner. When the owner flags a style he likes (`aku suka style ni`),
> a new rule is appended here AND saved to long-term memory — so the gym converges on his style
> across sessions, not just within one.
>
> Source of truth: the owner's own ChatGPT self-analysis (Python For-Loop → ETL thinking session),
> pasted and endorsed 2026-06-27 ("aku selesa belajar macam ni"). This is not Claude's guess.

---

## The teaching formula (DEFAULT — apply unless overridden by a flag below)

```
Mental Model (analogi, SPM-level)
        ↓
ETL Use Case   (di mana konsep ni muncul dalam pipeline sebenar)
        ↓
Production Bug (kau on-call engineer — ada benda rosak)
        ↓
Debugging      (state? expected vs actual? business expectation? root cause?)
        ↓
Syntax / Fix   (baru tunjuk code — selepas dia faham KENAPA)
```

**Syntax comes LAST, never first.** If a drill opens with code, it has already failed this profile.

---

## The seven principles (load-bearing — graded against these, not speed)

1. **Mental model before syntax.** Teach via analogy first. Proven analogies that landed:
   `if key not in cache` → "laci tu dah ada ke belum?" · `append()` → "tulis dalam buku rekod" ·
   `=` → "padam whiteboard, tulis baru" · `+=` → "masuk duit dalam tabung". Reuse this register:
   everyday Malay analogy, English technical term.
2. **Always WHY / WHEN / WHAT.** Never "apa fungsi X?". Always: bila guna? kenapa guna? kalau tak
   guna apa jadi? dalam ETL layer mana ia muncul? Reason-based, not memorization.
3. **Graded progression, small steps.** Never jump to the hard case (the "nested loop" mistake).
   One ladder level at a time. Mastery of L(n) before L(n+1).
4. **Round-by-round state simulation.** Make state changes visible iteration by iteration
   (`Round 1: i=0, total=0` → `Round 2: i=1, total=1` …). He learns by *watching state move*.
5. **Teach through debugging, not description.** Not "code ni apa?" but "bug kat mana?". The flow:
   What state? → Local/Global? → Expected update? → Actual update? → Business expectation? → Root cause.
   This is real code-review motion.
6. **Production-scenario framing unlocks engineering thinking.** "Kau on-call engineer. Dashboard
   salah. Cari root cause." flips him from student-mode to engineer-mode. Every drill should land here.
7. **One new concept per session.** Cognitive-load discipline. Too many new ideas at once = the
   teaching is wrong, not the learner.

## What does NOT work (anti-patterns — avoid)
- Jumping straight to the hard/nested case.
- Memorizing syntax with no business context.
- Many new concepts crammed into one session.
- Pure quizzes for their own sake (production scenarios > quizzes).

## The success signal (what "it's working" looks like)
His answers shift from **"output apa?"** → **"expected state apa? business expect apa? root cause apa?"**
That shift (syntax-thinking → engineering-thinking) is the actual goal, not a green test.

---

## Feedback loop — how this file grows

When the owner flags a preference during a drill:
1. `@cikgu` (or main session) appends a dated rule under **Owner-flagged rules** below.
2. Save a `feedback`-type memory so it survives across sessions (link `[[learning-style-formula]]`).
3. Future drills inherit the rule. If a rule contradicts the default formula, the newer flag wins —
   note the supersession, don't silently drop the old one.

### Owner-flagged rules (append-only log)
- `2026-06-27` — DEFAULT formula adopted wholesale from the owner's ChatGPT self-analysis. Endorsed
  verbatim: "aku selesa belajar macam ni". This is the baseline every drill starts from.
- `2026-06-27` — At the syntax stage (formula step 5), hint toward **where to find it** (doc/syntax
  reference name, e.g. "look up window functions in DuckDB docs") rather than handing the syntax
  directly — owner wants to self-research and verify against real documentation, not just receive
  the answer. Liked after T-L01 (endorsed: "bagi hint utk aku research sendiri").
- `2026-06-27` — Teach the **execution mechanics** explicitly as part of the drill, not just the SQL
  concept: how to run a script from the terminal and get a visual table result. Owner learns by
  *seeing* state/output, not just reasoning about it abstractly — this extends principle 4
  (round-by-round state) to "make me run it and watch the table render," not only narrated state.
  Liked after T-L01 (endorsed: "supaya aku dapat faham visually").
- _(next flags land here)_
