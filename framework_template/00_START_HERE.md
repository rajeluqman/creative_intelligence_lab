# Framework Template — how to use this kit

> Portable data-engineering governance kit, extracted from creative_intelligence_lab (CIL) after
> being proven across 5 repos (CIL itself + the 4-repo pipeline_retrofit: home-credit, olist,
> paysim, Volve — see `architecture/pipeline_retrofit/` in CIL for the ground-truth diff this
> kit was built from). Regardless of domain, stack, or agent roster, the process discipline below
> applies unchanged. Version: see `CHANGELOG.md`.

## What this kit is NOT
Not a scaffold of code. Not a starter architecture. It does not pick your stack, your dataset,
or your grain. It is the **governance + journey + gate layer** that wraps around whatever
architecture you decide on — proven to be the same shape whether the compute is DuckDB, Glue,
Databricks, or Snowflake.

## Steps to adopt in a new repo

1. **Copy this whole folder** into the new repo root as e.g. `framework/` (rename freely) or
   flatten its contents directly into the repo (journey/ → docs/, governance/ → architecture/,
   gates/ → tests/ + .claude/hooks/, operating/ → .claude/ + root).
2. **Fill `gates/framework.yml`** first — this is the ONE config file every gate script reads.
   Nothing else works until this has real values (paths, banned tech, identity grain).
3. **Walk `journey/01` through `journey/09` in order, fully** — this repo's kit mandates the
   **full set, no skipping**. If a doc genuinely doesn't apply (e.g. no ML model, no external
   API), do not delete it or leave it blank — write inside it: `N/A — <reason>`, dated. A
   missing/empty journey doc is a gate failure (`gates/journey_completeness.py`); an honestly
   marked N/A is not. (`journey/09_SECURITY_AND_ACCESS.md` joined as mandatory in kit v1.1.0 —
   see `governance/ADR/ADR-001-security-layer-mandatory.md`.)
4. **Rename `operating/CLAUDE.md.template` → `CLAUDE.md`** at repo root, fill the `{{PLACEHOLDER}}`
   tokens (domain, stack table, governed-file map). Same for `PROJECT_STATUS.md.template`.
5. **Trim `operating/agents/`** to what this project needs — see `governance/ADR/ADR-000` for
   the ruling on how the roster may flex (role names may drop, but the two veto-holder roles
   — architect + scope-guardian — are NOT optional; see ADR-000 §2).
6. **Wire `gates/` into CI** — copy `gates/ci.yml.template` into `.github/workflows/ci.yml`,
   adjust paths.
7. **Run the bootstrap check**: `python gates/journey_completeness.py && python
   gates/boundary_contract.py && python gates/doc_reference_contract.py && python
   gates/secrets_scan.py` — all four must be green (or explicitly, honestly failing on real known
   gaps you've logged) before the first real commit lands.
8. **New ad-hoc feature request mid-project?** Read `governance/ADR/ADR-000-feature-intake-protocol.md`
   BEFORE writing code. That file is the answer to "how do we control scope creep on a whim."

## Why full-set-mandatory (not tiered)

Owner ruling (2026-07-04): consistency across projects matters more than per-project doc weight.
A project too small to need `STTM.md` is a project that can say so in one line inside `STTM.md`
— the discipline of writing "N/A, here's why" is itself the value (it forces the same check
every time instead of a judgment call about what to skip, which is exactly the kind of
ambiguity this framework exists to remove).

## Directory map

```
journey/       — the "idea → business question → pipeline" narrative, 8 mandatory docs
governance/    — ADRs, boundary contract *docs*, plan template, feature-intake protocol
operating/     — CLAUDE.md + PROJECT_STATUS.md templates, generic agent roster
gates/         — the executable layer: framework.yml config + contract scripts + CI template
```

## Design rule that makes this portable

Every gate script in `gates/` reads `gates/framework.yml` — NONE of them hardcode a repo's
paths, stack, or banned imports inline. This is the difference between the 4 retrofitted repos
(each contract was hand-edited text, proven working but requiring a human to retarget every
value) and this kit (edit one YAML, gates just run). If you ever catch yourself editing a
`.py` file in `gates/` to make it work for your repo, stop — that value belongs in
`framework.yml` instead, and the script should be fixed to read it from there.
