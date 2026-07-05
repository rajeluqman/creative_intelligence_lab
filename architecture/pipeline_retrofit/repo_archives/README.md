# repo_archives/ — full-history backups of the 4 ported repos

> Created 2026-06-29 because the `/workspaces/*-porting` clones live in an ephemeral
> codespace and can disappear (owner reported their workspaces already got deleted once).
> CIL's own repo is the durable, pushed location, so the 4 repos are archived here as
> `.tar.gz` — **each archive contains the FULL clone including `.git`**, not just a file
> snapshot, so the original commit history, branch, and `origin` remote URL all survive
> intact. This is NOT a fork/import of these repos into CIL — they stay independent;
> this is a backup location only.

## Contents

| Archive | Repo | Branch | Commit (at archive time) |
|---|---|---|---|
| `home-credit-pipeline-porting.tar.gz` | `rajeluqman/home-credit-pipeline` | `framework/governance-retrofit` | `bdc8966` |
| `olist-ecommerce-pipeline-porting.tar.gz` | `rajeluqman/olist-ecommerce-pipeline` | `framework/governance-retrofit` | `e3a48cb` |
| `paysim-fraud-pipeline-porting.tar.gz` | `rajeluqman/paysim-fraud-pipeline` | `framework/governance-retrofit` | `7c60ccb` |
| `Volve-Sensor-Production-Analytics-Pipeline-porting.tar.gz` | `rajeluqman/Volve-Sensor-Production-Analytics-Pipeline` | `framework/governance-retrofit` | `b6c99eb` |

> **Re-archived 2026-06-29** after the week-1-readability doc pass (Purpose + Business-Questions
> + Results&Evidence sections in each README + Confluence landing page). Commits above supersede
> the original retrofit commits `bef4714`/`f17e225`/`6a8aa10`/`08a12dc`.

## How to restore + push (Opus's job, per `PROJECT_STATUS.md` "Next action")

```bash
cd /workspaces   # or wherever a fresh clone target is convenient
tar xzf creative_intelligence_lab/architecture/pipeline_retrofit/repo_archives/<name>.tar.gz
cd <name>
git remote -v                         # confirm origin still points at the right GitHub repo
git push -u origin framework/governance-retrofit
gh pr create --title "..." --body "..."   # per repo, see that repo's PROJECT_STATUS.md
```

Each extracted repo is a complete, independent git clone — push/PR exactly as if it had never
left `/workspaces/`. No history was rewritten or squashed by the archive step (verified by
`git log --oneline -1` + `git branch --show-current` against each archive at creation time).

## Re-archiving after further work
If any of the 4 repos gets more commits before the push happens, re-run:
```bash
cd /workspaces
tar czf creative_intelligence_lab/architecture/pipeline_retrofit/repo_archives/<name>.tar.gz -C /workspaces <name>
```
and replace the stale archive — don't keep both versions around.
