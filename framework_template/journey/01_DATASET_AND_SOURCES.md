<!-- FRAMEWORK_TEMPLATE: UNFILLED — remove this line once real project content is added below -->
# 01 — Dataset & Sources

> If not applicable: do not delete this file. Write `N/A — <reason>` under the relevant
> heading and keep the rest. See `00_START_HERE.md` "Why full-set-mandatory."

## Source inventory
| Source | Type (file dump / API / DB export / stream) | Owner/access | Licence/PII constraint | Refresh cadence |
|---|---|---|---|---|
| | | | | |

## Access mechanics
- How is this fetched today (manual download / API key / connector)? Cite the exact script/command.
- Auth: where do credentials live (never commit them — name the vault/secret manager/`.env` var).
- Rate limits / cost per pull, if any (link to `finops` notes if this project has that agent).

## Volume & shape
- Row/file count order of magnitude, size on disk, growth rate.
- Known quality issues at the source (nulls, duplicates, schema drift) — first-pass only, detail
  goes in `06_DQ_PLAN.md`.

## Decision log for this doc
- **Chosen source(s) and why rejected alternatives were rejected** — this is the part most
  worth writing; "we picked X" without "instead of Y because Z" loses the reasoning later.
