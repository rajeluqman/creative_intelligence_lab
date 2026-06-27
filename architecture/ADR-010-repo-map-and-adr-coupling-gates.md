# ADR-010 — Navigation index (REPO_MAP) + ADR-coupling gate

- **Status:** Accepted
- **Date:** 2026-06-25
- **Deciders:** owner (requested), Claude (build)
- **Context refs:** `CLAUDE.md` ANTI-SHORTCUT PROTOCOL (read-before-touch; "code does not get
  tired, code does not write from memory"); `tests/doc_reference_contract.py` (the existing
  static doc-drift gate this is a sibling of); the standing **adr-addendum-parity** rule (an
  ad-hoc change that alters architecture deserves an ADR addendum or new ADR, not a silent commit).
- **Does NOT touch:** any Gold/marts model, any seed, any lineage/identity decision (ADR-006), any
  stack-boundary decision (ADR-001/004/005). Pure governance *tooling* over the existing repo.

## Context

The owner's root-cause framing of the recurring "missing gaps": work goes wrong when an author
(human or LLM) writes code or a claim from stale in-context memory instead of from the file as it
is NOW. Two follow-on needs were named directly (2026-06-25): (1) understand the whole repo
*cheaply* — a pointer index — without burning tokens on a full-repo scan; (2) stop an ad-hoc
change from silently altering architecture without a recorded decision. The existing gates prove
correctness of governed files (lineage/boundary) and that docs don't reference non-existent
models/paths (doc-reference), but neither answers "what is this file / what uses it" nor "did this
change move the architecture without an ADR".

## Decision

**A — `architecture/REPO_MAP.md`, a generated navigation index.** `scripts/gen_repo_map.py`
emits one row per source file (purpose · uses · used-by) for every file in the working set
(tracked + untracked-not-ignored) minus a stated EXCLUDE set (`.github/`, lockfiles, `*.example`,
secret templates, settings). It is **100% derived, nothing hand-authored**: purpose is *extracted*
from the file's own module docstring / first Markdown heading / leading SQL comment; edges are
parsed with `ast` (Python imports — so SQL embedded in a string can't pose as an import) and a
`ref()` regex (dbt). Because nothing is authored, it cannot fall out of sync. The CI gate is
`gen_repo_map.py --check` — regenerate in memory, fail if it differs from the committed file (the
`black --check` pattern). A change that shifts the import/`ref()` graph turns the gate red until
the index moves with it. **The map is a pointer, not a cache:** it says which file to open; the
reader still reads that file fresh (PROTOCOL rule 1). Trusting a row without opening the file is
the stale-cache bug at larger scale, and is called out as such in the file's own header.

**B — `tests/adr_coupling_contract.py`, structural-change → ADR coupling.** A *structural* change
to a governed file (roots `models/`, `seeds/`, `scripts/`, `dags/` — the structural subset of the
governance_guard hook) must ship with an `architecture/ADR-*.md` touch in the same change.
"Structural" is deliberately narrow to avoid the noise trap: a governed file **added or deleted**,
or **modified such that its dependency edges changed** (new/removed local import or `ref()`). A
cosmetic edit, or a new *row* in a seed, is not flagged. Escape hatch, loud and on the record:
`ADR_COUPLING_WAIVED=1` with justification in the PR. Base revision resolves via
argv > `$ADR_COUPLING_BASE` > merge-base with `origin/main`/`main`; if none resolves the gate
SKIPS rather than failing a context it can't reason about (CI checkout therefore uses
`fetch-depth: 0` so the base is reachable).

**C — Both gates are wired into CI** alongside the existing contracts, and both ship with a
self-test (`tests/test_adr_coupling_contract.py`; the repo-map's `--check` is self-verifying) per
the house "the gate is itself tested" pattern. **This ADR is itself the coupling gate's first
satisfied case** — introducing these gates is an architecture-governance decision, so it is
recorded here rather than committed silently.

## Rationale

- Derive-don't-author is the same philosophy as the other contracts: a hand-maintained map drifts
  exactly the way the stale memory it's meant to cure does; a generated one can't.
- Coupling on *structural* change only keeps the signal honest. "Every edit needs an ADR" would
  train authors to add empty ADR touches to get green — the rule would then certify nothing.
- Skip-on-no-base (not fail-on-no-base) keeps the gate from being a flaky blocker in contexts
  (detached HEAD, missing upstream) where it genuinely cannot compute a diff.

## Rejected alternatives

1. **A hand-written / LLM-written repo map.** Rejected — it is the stale-cache failure mode wearing
   a new hat. The map must be derived from ground truth or it is just more memory to go stale.
2. **Coupling that fires on ANY change to a governed file.** Rejected as the noise trap above —
   it would be gamed into meaninglessness.
3. **A per-file `governed_by: ADR-xxx` column in the map.** Rejected for now — that link is not
   present in the file itself, so it would have to be authored and would drift. Kept out until it
   can be derived.
4. **Making missing module docstrings a hard failure.** Rejected for this pass — the map surfaces
   `(no module docstring)` as a visible nudge, which is enough; a hard gate on docstrings is a
   separate style decision, not claimed here.

## Consequences

- **Positive:** "what is X / what touches X" is one cheap read; a graph-shifting change cannot land
  without the index moving with it; a structural governed change cannot land without a recorded ADR
  (or a loud waiver).
- **Negative / accepted:** the coupling gate's "structural" heuristic can miss an architecture
  change that alters *behaviour* without changing files or edges (e.g. rewriting a model's logic
  but not its `ref()`s) — named, not hidden; the governance_guard hook + reviewer still cover that.
- **Bounded — explicitly not done here:** a derived `governed_by` map column, docstring-presence
  enforcement, and coupling on within-file behaviour change. Each is a separate future decision.
