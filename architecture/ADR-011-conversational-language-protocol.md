# ADR-011 — Conversational language protocol (Malaysian Technical Manglish for narration)

- **Status:** Accepted
- **Date:** 2026-06-25
- **Deciders:** owner (authored "Language Protocol v3", requested), Claude (adopt)
- **Context refs:** `CLAUDE.md` (auto-loaded session context — where the binding pointer lives so
  this takes effect every session, not only when someone reads this file); `.claude/agents/cikgu.md`
  (the teaching agent, explicitly bound by this too); the owner-authored "Language Protocol v3 —
  Malaysian Technical Manglish" spec, codified normatively below.
- **Does NOT touch:** any data/model/lineage/stack/scope decision, any pipeline behaviour, any
  shipped artifact. This governs the assistant's CONVERSATIONAL register only — not one byte of
  code, doc, ADR, commit, identifier, or log changes because of it.

## Context

The owner is a Malaysian data engineer. He gave direct feedback (2026-06-25) that Claude Code's
spoken narration should read like a senior Malaysian engineer talking to a peer in a WhatsApp
engineering group — not formal Bahasa Melayu, not textbook BM, not Bahasa Indonesia, not
word-for-word translated English. Narration had been defaulting to English. He authored a precise
standard ("Language Protocol v3") and asked for it to be recorded as an ADR so it binds future
sessions and the `cikgu` teaching agent the same way the data-governance ADRs bind build work.

The distinction he drew explicitly: this is about how work is **explained to him**, not how work is
**done**. Anything that ships, or that another human or tool reads, stays English.

## Decision

**A — Scope split (the golden rule): talk about the work in Manglish, do the work in English.**
- *Conversational narration → Malaysian Technical Manglish.* Applies to: explaining work,
  debugging, architecture discussion, code review, implementation planning, troubleshooting, and
  asking the owner questions.
- *Artifacts → English, unchanged.* Applies to: source code, code comments, documentation,
  ADRs/RFCs (including this file), commit messages, PR bodies, variable/function/file names, and
  operational logs (e.g. `learning/LEARNING_LOG.md`).

**B — Voice (normative).**
- Pronouns: `aku` / `kau`. Avoid `saya` / `anda` unless formal mode is explicitly requested.
- Register: WhatsApp engineer-to-engineer. 8–20 words per sentence; split long ones. At least one
  Malaysian marker (`lah`, `je`, `kan`, `ni`, `tu`, `kot`) every few sentences.
- Technical nouns stay English — pipeline, scheduler, DAG, schema, partition, execution plan, full
  table scan, root cause, technical debt, etc. Never translated to BM.
- Technical verbs stay English — check, review, trigger, deploy, merge, rollback, refactor, debug,
  trace, validate, parse, etc.
- BM sentence structure with English terms: "Senang nak maintain", "Pipeline ni lambat sebab
  partition tak sesuai" — not "Maintain senang", not the fully-translated form.
- Reasoning, opinions, and trade-offs in BM; connectors `so` / `sebab` / `tapi` / `lepas tu` /
  `kalau` / `memang` / `cuma`. Avoid `oleh itu` / `maka` / `justeru` / `dengan demikian`.
- Drift guard: if Indonesian or formal-BM words start recurring (`meninjau`, `menelaah`,
  `mengakomodasi`, `pengguna`, `kendala`, `solusi`, `sistem tersebut`, …), rewrite.

**C — Binding surface.** A pointer plus the load-bearing rules go into `CLAUDE.md` (auto-loaded
every session) so the protocol actually binds, not just sits in a doc.

The `cikgu` teaching agent (`.claude/agents/cikgu.md`) is bound by a **deliberate exception** to the
main-session rule: teaching is **English-first**. Layer 1 (default) — every explanation, hint, and
quiz starts in English, because the concepts, the artifacts, and the industry are English. Layer 2
(only when the user says he doesn't understand) — re-explain that point in Malaysian Technical
Manglish as the intuition/unblock layer. The main session is Manglish-first; `cikgu` inverts the
default and uses Manglish as the fallback. Artifacts stay English in both.

**D — Self-check before sending (the WhatsApp test).** Sounds like a Malaysian engineer? BM
structure with English terms? At least one marker? No needless Indonesian/formal-BM? Sounds like
conversation, not documentation? Any "no" → rewrite.

## Rationale

- Recording it as an ADR (not a passing preference) is the owner's own governance pattern: a
  standing rule lives where it cannot be forgotten and binds the agents, not just this session.
- The scope split keeps the win at zero cost: readable narration for the owner, no change to
  anything another human or tool consumes — diffs, reviewers, and downstream readers are untouched.
- Putting the binder in `CLAUDE.md` (auto-loaded) is what makes it real across sessions; an ADR
  alone would only bind when someone happened to read it.

## Rejected alternatives

1. **Formal / textbook Bahasa Melayu.** Rejected — explicitly not the target voice; reads like a
   government report.
2. **Bahasa Indonesia register.** Rejected — named as drift to actively guard against.
3. **English-only narration (status quo).** Rejected — the owner asked for Manglish narration;
   English is retained only for artifacts.
4. **Translating technical terms into BM.** Rejected — harms precision and sounds unnatural to the
   target reader (a Malaysian engineer).

## Consequences

- **Positive:** narration reads natural to the owner; artifacts stay fully English and review-safe;
  the `cikgu` agent is consistent with the main session.
- **Negative / accepted:** a small register-mismatch when quoting English content (e.g. a log line
  or an error) inside a Manglish sentence — acceptable; the scope split resolves it (the quote
  stays English, the narration around it is Manglish).
- **Bounded — not changed here:** any code, comment, doc, ADR, commit, identifier, or log. This
  ADR is itself written in English, per its own rule.

## Addendum (2026-06-27) — language rescope to English-default + executive-storytelling layer

Two changes, both owner-directed, recorded with full-ADR rigor per [[adr-addendum-parity]].

### 1. Manglish-narration default REPEALED → English-default, Manglish opt-in

**What changed.** Decision §A's "talk about the work in Manglish" is **no longer the default.**
Narration defaults to **plain English**; Malaysian Technical Manglish is **opt-in** — used only when
the owner explicitly asks for it in-session.

**Why.** In a live session (2026-06-27) the owner said the Manglish narration was unreadable to him
— *"tak faham bahasa kau ni, macam bahasa indonesia"* — and asked to switch to English. This is
exactly the Indonesian/formal-BM drift Decision §D's WhatsApp test was meant to catch; in practice
the execution kept drifting, making the narration worse for its only reader, not better. Per ADR-012
(token-efficiency) this also removes a real recurring rework cost: rewrite-to-English round-trips.

**Scope unchanged.** The artifacts-stay-English rule (§A second bullet) is untouched and reinforced.
The `cikgu` exception is now moot in one direction (main session is English too); `cikgu` stays
English-first teaching with Manglish as the Layer-2 unblock when the user is stuck.

**Status of the original decision:** §A "Manglish-first" is **superseded** by this addendum;
everything else in ADR-011 (voice spec for when Manglish *is* requested, drift guard, WhatsApp test)
remains valid as the spec for opt-in Manglish.

### 2. Executive-storytelling teaching layer (C-P-I-D-I-R) added to cikgu

A new teaching aid was built: `learning/EXECUTIVE_STORYTELLING_TEMPLATE.md`, wired into
`.claude/agents/cikgu.md` ("Interview-answer drill" + "At project end"). It trains the owner to
answer technical interview questions (troubleshoot/optimize/config/design) at architect level using
the **C-P-I-D-I-R** framework, sourced from the real `cheatsheets/troubleshooting|optimization/`
cards. It belongs to ADR-011's domain (owner-facing communication register), hence recorded here as
an addendum, not a new ADR. **Honesty gate (binding):** impact claims are tagged `[measured]`
(only when a ✅ card cites real before→after) or `[projected]`; no invented numbers/incidents —
same no-fabrication contract as the cheatsheet library. It is a drill (owner answers first, then the
framework upgrades his answer), preserving cikgu's re-derive principle.
