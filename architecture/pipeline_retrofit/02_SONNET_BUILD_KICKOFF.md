# Sonnet Build Kickoff — Pipeline Retrofit

> Paste/route this to start the Sonnet execution session. All high-level decisions are made in
> `00_MASTER_SPEC.md` + `01_OPUS_DECISIONS.md`. You should need ZERO architecture decisions — if you
> do, that's a spec gap: record it in this folder and escalate to Opus, don't improvise.

## Your job
Retrofit the governance/framework layer onto 4 EXTERNAL repos, one at a time, in this order:
**home-credit → olist → paysim → Volve.** Each repo keeps its own data stack untouched (see
`01_OPUS_DECISIONS.md` boundary column). You add governance, not infrastructure.

## Hard constraints
1. **Read-before-touch.** Clone/fetch the target repo and read the actual file before asserting or
   editing. Never write from the master-spec summary alone — it's a map, not the territory.
2. **Stack preservation.** Never swap a tool. The new CLAUDE.md "Stack" table must mirror the repo's
   REAL stack (verify from its README + code, not from memory).
3. **No fabricated ADRs.** Volve's ADRs are reconstructed from README — tag every one
   "(reconstructed — owner confirm rationale)". Same for any decision not actually deliberated.
4. **English default** in all artifacts (ADR-011 lesson; these are public portfolio repos).
5. **Reconcile-before-done.** Each repo's retrofit is "done" only when: hook installed + targets
   correct, 3 contracts pass, CLAUDE.md stack table matches reality, roster files coherent,
   INTERVIEW_GUIDE resume-reconciliation table filled with `file:line` evidence.

## Per-repo deliverable checklist (home-credit template, then adapt)
- [ ] CLAUDE.md (CIL structure, repo's real stack, governed-file map from 01_OPUS_DECISIONS)
- [ ] .claude/agents/ — the roster count for this repo (8/10/10/9), tailored to its stack
- [ ] .claude/hooks/governance_guard.py — retargeted to this repo's governed files
- [ ] tests/doc_reference_contract.py (universal), boundary_contract.py (this repo's rejected tech),
      identity_contract.py (this repo's identity key)
- [ ] scripts/gen_repo_map.py + REPO_MAP.md
- [ ] ADRs to backfill (per 01_OPUS_DECISIONS additions #2)
- [ ] Slack: keep existing (home-credit/paysim) OR backfill from CIL `_notify_slack_failure` (olist/Volve)
- [ ] Confluence: adapt CIL `sync_docs_to_confluence.py` + 9-page set
- [ ] Logs: PROJECT_STATUS.md, COST_LOG.md, DECISION_LOG.md (+ INFRA_LIMITS_LOG.md for Volve/home-credit)
- [ ] INTERVIEW_GUIDE.md with Resume Claim ↔ Repo Evidence table (reconcile the known mismatches)
- [ ] .github/workflows/ci.yml — wire the 3 contracts + existing dbt/GE gates as static $0 gates

## Reference sources (priority: CIL first, pharma gap-fill)
- CLAUDE.md / contracts / hook / repo-map / Confluence / Slack → `creative_intelligence_lab` (this repo).
- Agent persona files → `pharma_novartis_sttm` `.claude/agents/` (filter to the approved roster).
- INTERVIEW_GUIDE shape → pharma's Phase-5 INTERVIEW_GUIDE + the resume-reconciliation requirement.

## Definition of done (all 4)
Every repo's CI green on the 3 new contracts; every resume bullet traces to evidence or is flagged.
Report back per repo with the reconcile checklist + evidence, not "done".
