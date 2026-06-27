# ADR-009 — Operational notifications: Slack failure alerts + Confluence doc sync

- **Status:** Accepted
- **Date:** 2026-06-25
- **Deciders:** owner (requested), @senior-data-engineer (build)
- **Context refs:** `README.md` P6 ("Slack alerts" was a candidate resume-stack tool, not yet
  decided into the locked stack); ADR-008 (Airflow orchestration — this hooks into the same
  DAG); `CLAUDE.md`'s locked-stack table (had no Alerting/Notification row before this).
- **Does NOT touch:** any Gold/marts model, any ADR-001..008 decision. Purely operational
  tooling (failure visibility + doc publishing) bolted onto already-ratified infrastructure.

## Context

Two gaps the owner named directly (2026-06-25): (1) a pipeline failure today is silent unless
someone is actively watching the Airflow UI or GitHub Actions tab — no push notification
exists; (2) project documentation (`PROJECT_STATUS.md`, all `architecture/*.md`) lives only as
files in the repo, with no living/browsable copy for non-repo audiences. Clarified scope
(owner, asked directly): Slack covers **Airflow task failures only** (not CI, not budget —
those are named OUT below, not silently expanded into); Confluence covers **doc publishing**
(not alerting — Slack already owns that).

## Decision

**A — Slack: `on_failure_callback` on the DAG's `default_args`, not per-task.** One function,
`_notify_slack_failure(context)`, posts a JSON message to `SLACK_WEBHOOK_URL` using stdlib
`urllib.request` — deliberately not `requests`: this callback runs inside Airflow's own
process (`venv_airflow`), and `venv_airflow` is kept deliberately minimal per ADR-008 (the
whole point of the isolated venv was not growing its dependency set casually). `requests` is
used in the Confluence script below instead, which runs via `venv/`, where it's already
available. **Missing/empty `SLACK_WEBHOOK_URL` is a graceful no-op (logs a warning, does not
raise)** — credentials are filled in later (owner's own words); the callback must not turn
"alerting isn't configured yet" into a second failure on top of the real one.

**B — Confluence: a new standalone script, `scripts/sync_docs_to_confluence.py`,** run manually
(or as a future CI/DAG step — not wired into either yet, see Consequences), not a callback.
Converts each tracked doc from Markdown to HTML (`markdown` package, new dependency — pure
text transform, not a banned framework) and PUTs/POSTs it as a Confluence "storage"-format
page via the REST API (Basic Auth: `CONFLUENCE_EMAIL` + `CONFLUENCE_API_TOKEN`, Confluence
**Cloud** convention — Server/Data Center's PAT-bearer auth is a named-out variant, not built).
Pages are created as children of `CONFLUENCE_PARENT_PAGE_ID` under `CONFLUENCE_SPACE_KEY`,
titled `"Creative Intelligence — <doc stem>"`; an existing page is looked up by title and
updated (version-incremented), not duplicated. `--dry-run` renders the page list + converted
HTML locally without calling the API at all — this is how the script gets verified before real
credentials exist.

**C — Tracked doc set is `PROJECT_STATUS.md` + every `architecture/*.md`** (23 files as of this
ADR) — the same set a human would read to understand the project, no smaller, no larger.
`debate/` is explicitly excluded (`CLAUDE.md`: "Historical, not a build target").

## Rationale

- Failure callback at the DAG level (not per-task) means one place to maintain, and it fires
  for any task's failure automatically — adding a 6th task later doesn't require remembering
  to wire its alert separately.
- Graceful no-op on missing webhook/credentials mirrors `scripts/env_guard.py`'s own
  fail-**open**-for-alerting-only stance — env_guard fails CLOSED for anything that writes real
  data (an unset `S3_BUCKET` must stop the pipeline); a notification side-channel failing
  open is the opposite-but-correct choice, because alerting being unconfigured must never be
  the thing that takes the real pipeline down.
- `--dry-run` on the Confluence script exists for exactly the situation in front of us right
  now: built before credentials exist, must be provably correct anyway (CLAUDE.md
  ANTI-SHORTCUT PROTOCOL — no evidence = unverified, not done).

## Rejected alternatives

1. **CI (GitHub Actions) failures also alert to Slack.** Rejected for this pass — owner scoped
   this explicitly to Airflow only when asked directly. Named here so it isn't silently
   expanded into later without the same explicit ask.
2. **Gemini budget/cost alerts also routed through this Slack channel.** Rejected for this pass,
   same reason — @finops-agent's domain, a separate decision if/when wanted.
3. **A markdown→Confluence converter that preserves Confluence-native macros/panels.**
   Rejected as over-engineering for v1 of this script: plain HTML rendering via `markdown` is
   good enough to be readable; macro-level fidelity is a nice-to-have, not needed to prove the
   sync works.
4. **Wiring the Confluence sync into CI or the Airflow DAG now.** Rejected until it's been run
   at least once successfully with real credentials — wiring an unverified integration into an
   automated trigger risks a noisy/broken automated job before anyone has seen it work once.

## Consequences

- **Positive:** a real Airflow task failure will reach Slack the moment `SLACK_WEBHOOK_URL` is
  filled in, with zero further code changes. Documentation becomes browsable outside the repo
  the moment Confluence credentials are filled in and the script is run once.
- **Negative / accepted:** `markdown`→Confluence-storage-format fidelity is approximate (plain
  HTML, no native Confluence macros) — acceptable for v1 of this integration, named, not hidden.
- **Bounded — explicitly not done here:** CI alerts, budget alerts, Confluence Server/DC auth,
  and wiring the Confluence sync into any automated trigger (CI/DAG). Each is a separate future
  decision, not retroactively claimed by this ADR.
