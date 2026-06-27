# ADR-012 — Token-efficiency & session-discipline operating protocol

- **Status:** Accepted
- **Date:** 2026-06-27
- **Deciders:** owner (approved directly, 2026-06-27); Claude (adopt). Not separately convened
  through @data-architect / @scope-guardian — this governs *how the assistant and cabinet operate*
  (process), not the data model, lineage, stack, or scope, so it sits outside the data-governance
  veto lanes. Owner approval is the sign-off.
- **Context refs:** `CLAUDE.md` (auto-loaded — the binding pointer lives there); `PROJECT_STATUS.md`
  (the "▶ RESUME HERE" cheap-resume block this ADR mandates); `.claude/agents/*` (the cabinet whose
  invocation pattern this changes); [[anti-shortcut-protocol]], [[repo-map-navigation-gate]],
  [[adr-addendum-parity]] memories.
- **Does NOT touch:** any data/model/lineage/stack/scope decision or pipeline behaviour. This is an
  operating protocol for cost/time efficiency. The anti-shortcut protocol and all governance gates
  are **strengthened, never relaxed** — they are the guardrail that makes cost-cutting safe.

## Context

A measured audit of this project's own Claude Code session logs (22–26 Jun 2026, 13 sessions, all
`.jsonl` transcripts incl. subagents) established the real baseline:

- **~352.5M tokens, ~$220.** Cost drivers: **cache_read 53.9%** ($118.71), **cache_write 29.5%**
  ($65.07), output 16.3% ($35.99), fresh input 0.2%. Caching already saved ~$1,068 vs. no-cache —
  it is the saving mechanism, not the problem.
- Tokens are **~97% cache_read** = (context size × number of turns). The cost lever is therefore
  **how much context is re-read each turn**, not the cache itself.
- **Opus = ~40% of cost** (@data-architect runs Opus on every ruling).
- **243 subagent messages.** Subagent-heavy workflows cost ~7× a single thread because each
  subagent reloads its context cold.
- The longest single sessions (81–93M tokens) were the most expensive — context compounds: message
  N re-pays for all prior context every turn.

The owner's stated goal: cut cost + time **without** causing rework (the worst burn), and without
the recurring shortcut/"missing-gap" failure. Cost and accuracy are not in tension if the cut
targets *redundancy*, not guardrails.

## Decision

Adopt six operating levers. Cut redundancy; never cut the guardrails (anti-shortcut protocol, the
gates, ADR-first, single-source-of-truth content).

| # | Lever | What it does | Guardrail (no-gap) |
|---|-------|--------------|--------------------|
| 1 | **Agent** | Route model per *decision*, not per agent: @data-architect (Opus) only for the 6 Clean-ERD doctrine calls; minor rulings → @scope-guardian/Sonnet or a gate. Batch related cabinet questions into one spawn. Never spawn subagents for *coupled* work — gate-loops (e.g. SDE→DQ→SDE) stay on the main thread. | Opus stays mandatory for the 6 doctrine points; coupled-on-main is also more accurate (shared state) |
| 2 | **CLAUDE.md** | Keep it cache-stable: static governance up top, volatile state pointed-to (not inlined), so an edit doesn't invalidate the whole prefix. Trim only duplication a gate already enforces. | STOP-GATE + anti-shortcut protocol stay verbatim; cut only what a gate independently enforces |
| 3 | **Protocol** | Keep all 4 anti-shortcut rules untouched. **Rescope ADR-011** language: English-default narration, Manglish opt-in (see ADR-011 Addendum 2026-06-27) — kills the rewrite round-trips. | Anti-shortcut rules are the reason cost-cutting won't cause rework |
| 4 | **ADR** | ADR-first before building (cheap via `REPO_MAP.md` pointer) — a 5-min ADR read beats rebuilding models after a conflict. Tier [[adr-addendum-parity]]: major decision = full ADR; minor extension = addendum block on the nearest ADR. | `adr_coupling_contract` keeps ADRs linked to code |
| 5 | **Gates** | Prefer a gate-run over a context re-read for any "is this consistent?" check (deterministic, ~0 tokens vs. expensive cache_read). Cheapest-gate-first / fail-fast. Lean on the pre-edit `governance_guard` hook to block bad edits at source. | Gates are the accuracy mechanism — strengthen, never reduce |
| 6 | **Session guard + cheap resume** | Cut long sessions before context compounds. Trigger = **Claude Context Bar** (installed): yellow 50–75% = finish current unit + keep RESUME-HERE current; red >75% = checkpoint + new session (75% sits below the ~80% auto-compact). Resume = the `PROJECT_STATUS.md` "▶ RESUME HERE" block + assistant writes the next-session prompt. Assistant also gives an in-chat heads-up at long-session breakpoints. | Native hook-popup dropped — broken in the VSCode extension ([anthropics/claude-code#16114]); Context Bar + in-chat text are the reliable surfaces there |

## Projection (from the measured baseline, conservative, compounded multiplicatively)

| Scenario | Tokens | Cost | Token cut | Cost cut |
|----------|--------|------|-----------|----------|
| Pessimistic | 352.5M → 218.2M | $220 → $151 | −38% | −32% |
| **Midpoint (most likely)** | 352.5M → **188.9M** | $220 → **$136** | **−46%** | **−38%** |
| Optimistic | 352.5M → 157.1M | $220 → $120 | −55% | −45% |

Lever 6 is the dominant mover (cache_read 341.6M → ~180M at midpoint). Levers 4–5 (rework
prevention) are **not** in these numbers — their saving can't be isolated from past logs, so they
are unquantified upside. Tokens cut more than cost because cache_read is already billed cheap (10%).

## Rationale

- The audit shows the spend is a *context-size × turns* problem, addressable by session discipline
  (Lever 6) + a leaner, cache-stable CLAUDE.md (Lever 2) + fewer cold subagent reloads (Lever 1).
- Same philosophy as the rest of this repo: **machine over vigilance.** The trigger is a tool
  (Context Bar), the resume is a file block, the verification is a gate run — not "remember to."
- Repealing the Manglish-narration default removes a real, recurring rework cost (rewrite-to-English
  round-trips) at zero quality loss.

## Rejected alternatives

1. **Compress the work into 1–2 long sessions.** Rejected — backwards. Long sessions are the most
   expensive (context compounds); the fix is *more, shorter* sessions, not fewer.
2. **"Overcome" the 97% cache_read by reducing cache hits.** Rejected — caching is the saving
   ($1,068 saved already). Reduce context size/turns, not cache usage.
3. **Native hook-based popup warning in the extension.** Rejected for this owner — Notification
   hooks are broken/unreliable in the VSCode extension; the installed Context Bar is the reliable
   surface.
4. **Cut governance/gates to save tokens.** Rejected — that causes rework, the most expensive burn.
   Guardrails are explicitly out of scope for cutting.

## Consequences

- **Positive:** ~46% fewer tokens / ~38% lower cost at midpoint to rebuild equivalent scope, likely
  better once rework-prevention counts; resumes are cheap (read one block, not 729 lines).
- **Negative / accepted:** more sessions to manage; Lever 6's saving depends on the owner acting on
  the red bar — if discipline slips, spend regresses toward the pessimistic column.
- **Bounded — not done here:** an aggressive CLAUDE.md restructure/trim (Lever 2 beyond the
  cache-stable pointer change) is a careful separate pass, not bundled into this ADR; a SessionStart
  hook to auto-load RESUME-HERE is deferred until verified working in the extension.
