# Security Model — banking-multisource-lakehouse (content source for journey/09)

> Decision + rationale: `01_OPUS_DECISIONS.md` **D-16**. This doc is the CONTENT SOURCE for
> `journey/09_SECURITY_AND_ACCESS.md` in the new repo — Sonnet ports these sections in and
> fills the `{{...}}` runtime values. Structure deliberately mirrors the kit's journey/09
> template (secrets · data classification · RBAC matrix · service identities · audit · PII ·
> compliance · incident) so it drops straight in. NOT a separate `security/` folder (D-16 /
> kit ADR-001 rej-alt #2 / CIL ADR-014 — "just enough, named explicitly").

## 1. Secrets management
| Secret | Used by | Stored in | Never |
|---|---|---|---|
| Postgres / MS SQL creds | watermark extractors | Databricks secret scope / `.env` (gitignored) | in code or config committed to git |
| OBP OAuth client id/secret + token | OBP API client | Databricks secret scope | in the landing path or logs |
| S3 access key (transform) | Databricks ↔ S3 | Unity Catalog storage credential / instance profile | as a long-lived key in code |
| S3 read-only key (serving) | Snowflake ext. tables | Snowflake storage integration | scoped beyond `banking/`, never write |
| `BANK_PAT` (git push) | git credential helper | Codespaces secret ($env only) | on disk / in remote URL |

Runtime origin stated, not just "we use env vars": secrets come from the Databricks secret
scope (transform) and Codespaces/`.env` (dev). Enforcement: `gates/secrets_scan.py` +
`framework.yml → secrets_scan.extra_patterns` for DB connection strings and OBP token shapes.

## 2. Data classification
| Data | Where | Classification | Handling |
|---|---|---|---|
| `birth_number` (Berka) | landing/bronze `sap_crm` | **sensitive** (national ID, encodes DOB+gender) | decode→`birth_date`+`gender` at Silver (R-12); raw dropped after decode |
| account number / `account_id` | postgres, mssql, OBP | **sensitive** (financial account) | mask to last-4 at Silver (D-07) |
| card number | mssql `cards` | **sensitive** (PCI-shaped) | mask to last-4 at Silver; never in Gold raw |
| balances, `amount`, txn value | all sources | **confidential** (financial) | aggregate-only in Gold; row-level restricted |
| name, address, district | Berka CRM | **confidential** (PII) | restricted; not exposed in marketing-facing marts |
| `isFraud` label | mssql | **confidential** (risk) | fraud-ops role only |
| currency codes, product types, dates | all | internal | unrestricted internally |

Every non-public column has a row (journey/09 rule). "Sensitive" flagged even where no regime
currently bites, so a future reader sees it was considered.

## 3. RBAC role matrix (role × layer × permission) — REAL GRANTs, Unity Catalog
| Role | Layer / objects | Permission | Used by |
|---|---|---|---|
| `pipeline_svc` | Landing, Bronze, Silver, Gold | READ + WRITE | the extractors / transforms (service identity, not a human) |
| `data_engineer` | Silver, Gold (+ Bronze read) | READ; WRITE Silver/Gold | development / debugging |
| `analyst_marketing` | **Gold only** (masked marts) | READ | BQ-01/06/09 dashboards — NEVER Landing/Bronze |
| `fraud_ops` | Gold fraud marts + `isFraud` | READ | BQ-02/03 |
| `risk` | Gold risk marts | READ | BQ-05 |
| `serving_ro` (Snowflake) | Gold external tables only | READ | Snowflake/Power BI veneer |
| `landing_admin` | Landing, Bronze (raw PII) | READ | break-glass only, audited |

The load-bearing rule: **raw layers (Landing/Bronze) hold unmasked PII → no analyst/serving
role may read them.** UC grants enforce it (D-01 Add #3 payoff); this is not prose, it's GRANTs.

## 4. Service identities
- `pipeline_svc` — one scoped identity per pipeline concern; least-privilege (an extractor can
  write its own Landing prefix + read its watermark state, nothing more).
- `serving_ro` — read-only, scoped to `s3://<bucket>/banking/gold/` only.
- Dedicated-not-reused (CIL ADR-014 rule): the CI/OIDC identity ≠ the ingestion identity ≠ the
  serving identity. No shared admin.

## 5. Audit / log enablement
Platform-native (journey/09 default — no bespoke audit pipeline): Unity Catalog **query history**
+ **table/column lineage**; S3 server access logs on the `banking/` prefix; OBP API call logs.
Answers "who deleted/read what, when" without building a custom audit store. Retention: default
platform retention is sufficient at portfolio scale (name a longer requirement only if one appears).

## 6. PII handling
Enters via: Berka CRM (birth_number, name, address), the account/card numbers across all sources.
Path: lands raw in Landing→Bronze (restricted, R-27) → **masked/decoded at Silver** (D-07, R-12)
→ Gold + serving see only masked/aggregated forms. PII never reaches the marketing/serving roles
unmasked. Leaves the system only through Gold marts, already masked.

## 7. Compliance flags
| Regime | Applies? | Note |
|---|---|---|
| GDPR | Partial (synthetic data, but modeled as if EU subjects for realism) | right-to-erasure is *tractable*: `dim_customer_xwalk` (D-04) resolves one customer across all 4 sources, so a delete request is executable end-to-end — documented as a capability |
| PDPA (Malaysia) | Modeled | same erasure path; banking-sector data-protection framing for the local market |
| PCI-DSS | Shape only | card numbers masked to last-4 (D-07); no real cardholder data (synthetic) |
| BNM / banking-secrecy | Framing | account data treated as confidential; access-restricted per RBAC matrix |

Synthetic data means nothing legally binds — but modeling the controls is the interview point.

## 8. Threat model (as a SECTION, not a folder — D-16)
| Threat | Vector | Mitigation |
|---|---|---|
| Credential leak | secret in code/config/log | `secrets_scan.py` gate; Databricks secret scopes; `BANK_PAT` env-only |
| PII exposure to wrong role | analyst reads raw Bronze | UC RBAC: raw layers deny analyst/serving roles (§3) |
| Over-privileged pipeline | shared admin identity | dedicated least-privilege service identities (§4) |
| Poisoned data | implausible values injected | DQ range/reject gates (security-as-DQ, D-16 §6) |
| Untraceable change | no audit trail | UC query history + lineage (§5) |
| Serving key abuse | write/escape from read veneer | `serving_ro` read-only, scoped to `gold/` only (§4) |

## 9. Incident contacts
Solo-owner project: owner is the single responder; failure alerts route to the pipeline's Slack
failure channel (same pattern as CIL's `_notify_slack_failure`). One person, one channel — stated
plainly per journey/09.
