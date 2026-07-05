<!-- FRAMEWORK_TEMPLATE: UNFILLED — remove this line once real project content is added below -->
# 09 — Security & Access

> If not applicable: `N/A — <reason>`. See `00_START_HERE.md`. Every section below is
> individually N/A-able with a reason — this doc does not assume every project has secrets,
> PII, or compliance exposure; it forces the same explicit check every time instead of a
> project-by-project judgment call about what to skip.

## Why this doc is mandatory (not tiered)

Added kit v1.1.0 (owner ruling): a project "simulating real work" — on-call drills, incident
runbooks, anything framed as production-representative — is a project where a leaked credential
or an RBAC misconfiguration is exactly the kind of incident the *rest* of this kit's drills teach
you to handle. A journey doc that documents the data model but not who can touch it is an
incomplete picture of the system, the same gap `08_SERVING_AND_EVIDENCE.md` closes for "what's
actually served." Case study this section is modeled on: creative_intelligence_lab's ADR-014
(2026-07-04) — a single owner override that added one real least-privilege role instead of a
speculative security *program*; see that ADR for the shape "just enough, named explicitly" takes.

## Secrets management
Where do API keys, DB passwords, service-account credentials live? (`.env` + gitignore, a secrets
manager, GitHub Actions secrets, OIDC federation with no static keys at all — cite the ADR if one
exists.) State the mechanism, not just "we use environment variables" — where do the env vars
themselves come from at runtime, and what prevents one from ever being committed.

## Data classification
| Data | Where (table/column/file) | Classification | Handling |
|---|---|---|---|
| | | public / internal / confidential / sensitive | |

Every column or file that isn't obviously public data gets a row. "Sensitive" covers biometric,
health, financial-account, or otherwise regulated data — flag it even if no regulation currently
applies, so a future reader knows it was considered.

## RBAC role matrix (role × layer × permission)
**Required table — this is the one section that must be a real table, not prose,** mirroring
"real GRANTs, not prose" (the same standard ADR-014 held itself to):

| Role | Layer / objects | Permission | Used by |
|---|---|---|---|
| | | | |

If the project has exactly one role (a solo pipeline, no serving layer, no second consumer),
write that one row and say so — a single-row table is a real answer, not a gap.

## Service identities
Which credentials belong to a service/pipeline (not a human)? How are they scoped (least
privilege — can this identity do anything beyond what its job requires)? Note any "dedicated, not
reused" precedent (a CI role should not double as the production ingestion role, etc.).

## Audit / log enablement
What native platform logging is turned on (cloud storage access logs, warehouse query history,
API access logs)? Default to **platform-native enablement over custom audit builds** — a bespoke
audit pipeline is usually solving a problem the platform already solves, unless there's a real
retention/format requirement the platform's default can't meet (name it if so).

## PII handling
What personal data does this project touch, and where does it enter/leave the system? If none:
say so plainly (mark the section N/A, reason: synthetic/aggregate data only, or similar) rather
than leaving this blank.

## Compliance flags (GDPR / PDPA / CCPA — N/A-able per row)
| Regime | Applies? | Note |
|---|---|---|
| GDPR | | |
| PDPA | | |
| CCPA | | |

Marking a row N/A with a real reason (e.g. no EU/UK data subjects) is a complete, honest answer.
A blank row is not.

## Incident contacts
Who gets paged/notified for a security-shaped incident (leaked credential, unauthorized access,
data exposure)? For a solo-owner project this may be one person/one Slack channel — state it.
