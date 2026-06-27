# 🧠 Executive Storytelling Template — Technical Q&A → Architect-Level Answer

> **Owner:** @cikgu (teaching apparatus). **Status:** teaching aid, not a build artifact.
> **Language:** English (concepts + the industry register are English).
> **Purpose:** train the owner to answer technical interview questions (troubleshooting,
> optimization, config tuning, design) the way a Staff Engineer / Architect answers a CTO —
> outcome-first, system-level, tradeoff-aware — using the **real solutions already logged in
> `cheatsheets/troubleshooting/` and `cheatsheets/optimization/`** as the source of truth.

---

## 0. The one rule that makes this fit THIS project — the honesty gate

This converter sits on top of a library with a **no-fabrication contract** (see both cheatsheet
INDEX files: every ✅ card cites a real `file:line`; 🟡 seed cards are explicitly "target, not
work-done"). The executive-storytelling layer **must not break that contract to sound impressive.**

- **Impact is tagged, never invented.** Every impact statement is labelled `[measured]` or
  `[projected]`. `[measured]` is allowed ONLY when the source card is ✅ DONE and carries a real
  `Measured effect: before → after`. If the card is 🟡 APPLICABLE / "target", the answer says
  **"projected"** (e.g. *"this is designed to cut re-model API cost to ~$0; not yet measured in
  production"*). No card → the agent says **"no logged card for this yet"**, it does not improvise a war story.
- **No invented numbers, no invented incidents.** A polished narrative around a fabricated metric
  is worse than a plain honest answer — it fails the exact "missing-gap / shortcut" test this
  project is built to prevent.
- **Senior ≠ embellished.** Seniority comes from system framing + tradeoff honesty (including
  "here's what I did NOT do and why"), not from inflated outcomes.

This gate overrides any "always inject an impact angle" instinct below: inject the angle only if
the card supports it; otherwise name it as a projection or omit it.

---

## 1. The framework — C-P-I-D-I-R

Internal reasoning skeleton (the model thinks in this order; the user-facing answer is shaped in §3):

| Step | Meaning | Sourced from the cheatsheet card field |
|------|---------|----------------------------------------|
| **C** — Context | the system situation / environment | card layer/phase + project stack (DuckDB/dbt/Airflow/Gemini/S3) |
| **P** — Problem | the symptom, stated in system/business terms | TS `Symptom` · OPT `Why here` (the pain) |
| **I** — Investigation | how the issue was found (observability-first) | TS `Backward trace` · OPT "how the bottleneck was spotted" |
| **D** — Decision | why this solution over alternatives (the thinking layer) | the tradeoff behind `Fix` / `What` |
| **I** — Implementation | the concrete technical action | TS `Fix / guard: file:line` · OPT `Applied at: file:line` |
| **R** — Result | impact on perf / cost / reliability — **honesty-gated (§0)** | TS (incident resolved) · OPT `Measured effect` |

Mnemonic: **C-P-I-D-I-R**.

---

## 2. Input detection — which cheatsheet library to pull from

cikgu already separates these two pedagogies (`.claude/agents/cikgu.md` → "Troubleshooting vs
Optimization"). The converter follows the same split:

- **TYPE A — Troubleshooting** ("why is the DAG slow?", "pipeline failed", "Silver count dropped
  to zero") → pull from `cheatsheets/troubleshooting/`. Full C-P-I-D-I-R, observability-first
  (Investigation = the backward trace).
- **TYPE B — Optimization** ("reduce cost?", "speed up the Gemini step?") → pull from
  `cheatsheets/optimization/`. Lead with baseline → improved state; Result must carry the
  `[measured]`/`[projected]` tag (§0).
- **TYPE C — Configuration / tuning** ("why `min_file_process_interval`?", "Airflow Pool size?",
  "DuckDB `memory_limit`?") → translate the knob into system reasoning: what bottleneck it
  relieves, what breaks if mis-set, the tradeoff it encodes. Never just state the value.

If the question maps to **no logged card**, say so and (in drill mode) turn it into a
hypothesis exercise rather than inventing an answer.

---

## 3. User-facing output format (8 beats)

```
1. Executive summary   — 1–2 lines, OUTCOME FIRST. "The issue was X causing Y; resolved by Z."
2. Context             — the system/environment (this stack, this layer).
3. Problem statement   — what broke / what was inefficient, in system terms.
4. Investigation       — how it was diagnosed (the trace / the metric watched).
5. Root cause          — the actual defect or bottleneck, stated plainly.
6. Solution + logic    — what was done AND why this over the alternative (the decision).
7. Tradeoff            — what was sacrificed / deliberately left out (cite ERD §6 / ADR if relevant).
8. Impact              — perf / cost / reliability, TAGGED [measured] or [projected] per §0.
```

Optional closer (only if it adds real signal): **"If I were scaling this in production…"** — one
line of next-level architecture thinking (e.g. "at 10× video volume this moves from a single
DuckDB node to partitioned external tables; the bridge-table design already supports it").

---

## 4. Translation layer — raw config → system reasoning

The single highest-value move. Convert the knob into the bottleneck it addresses.

| ❌ Junior (states the config) | ✅ Architect (states the system effect) |
|------------------------------|------------------------------------------|
| "Changed `min_file_process_interval`." | "Cut scheduler overhead by lowering DAG re-parse frequency, so the scheduler spends cycles on task execution instead of metadata scanning — the tradeoff is a slightly staler DAG refresh." |
| "Cached the Gemini JSON in Bronze." | "Made the raw LLM response immutable in Bronze so every downstream re-model re-parses instead of re-calling the API — the API call is the only real cost cliff, so a full re-model drops from a re-pay to ~$0 `[projected]`." |
| "Added a GE expectation `chunks >= 1`." | "Closed a schema-valid-but-empty failure mode: Gemini can return valid JSON with zero segments and pass the schema gate, so a business-rule gate quarantines empties before they silently zero out Silver." |

---

## 5. Seniority signal — inject ONE angle, honestly

When the card supports it, frame the answer through at least one of: **scalability · cost ·
reliability · system-bottleneck**. Subject to §0 — if the card has no measured/real basis for the
angle, mark it `[projected]` or drop it. An honest "we haven't load-tested past N yet" is a senior
answer; a fabricated throughput number is not.

---

## 6. Two modes for cikgu (preserves the re-derive principle)

cikgu's contract is **make the user re-derive, don't hand answers** (`.claude/agents/cikgu.md`).
So this template is a **drill**, not an answer dispenser:

### Mode 1 — Interview drill (default)
1. cikgu poses a real question tied to today's module / a logged card
   (e.g. *"why DuckDB not Spark?"* → ADR-001; *"Silver count dropped to zero"* → TS-EXT-01).
2. **The user answers first.** No framework shown.
3. cikgu scores the answer against the 8 beats + the honesty gate, then **upgrades** it —
   showing where the user gave a junior (config-only) answer vs an architect (system) answer.
4. Score + `learning/LEARNING_LOG.md` entry, same mechanic as normal teaching
   (hint = −5; an answer that fabricates an impact number = flag it, that is the cardinal sin here).

### Mode 2 — Answer-key converter (reference, post-attempt only)
Given a specific logged card, emit the full 8-beat executive answer as an **answer key** — revealed
only AFTER the user has attempted (same flow as DIY "diff vs answer key"). Used to calibrate, not
to skip the attempt.

---

## 7. Worked example (from the real seed card OPT-EXT-01)

**Question (TYPE B):** *"How would you keep the Gemini extraction step from blowing up cost when
the schema changes?"*

**Junior answer:** "I'd cache the Gemini response so I don't call the API again."

**Architect answer (8 beats, honesty-gated):**
> **Summary:** The cost risk is re-calling a paid LLM on every re-model; the fix is to make the raw
> response immutable in Bronze and re-parse from there. **Context:** extraction is the only step in
> this pipeline that hits a paid external API (Gemini); everything downstream is local DuckDB. **Problem:**
> a naive design re-calls Gemini whenever the Silver schema changes, re-billing the entire video
> library. **Investigation:** cost attribution showed the API call is the single cost cliff — transform
> compute is effectively free at this data size (KB–MB). **Root cause:** coupling re-models to the API
> instead of to stored output. **Solution + logic:** persist the verbatim Gemini JSON in Bronze,
> append-only; all models read `stg_gemini_raw` off Bronze, never the API (ADR-003). **Tradeoff:** Bronze
> storage grows and we keep "ugly" raw payloads forever — accepted, because storage is cents and
> re-pay is dollars. **Impact:** a full re-model of ~500 videos targets ~$0 API vs $20–150 re-pay
> `[projected — seed card OPT-EXT-01, not yet measured in production]`.
> *Scaling closer:* at 10× library size this pattern is what makes re-models free; the cost stays
> bounded to net-new videos via content-hash skip-existing.

Note the `[projected]` tag — the seed card is 🟡, so the number is honestly flagged, not asserted.

---

## 8. Final principle

> Sound like **a senior engineer explaining to a CTO, not a developer reading docs** — but never
> buy that register with a number you can't cite. On this project, an honest "projected, not yet
> measured" beats a confident fabrication every time.
