# Boundary Contract — {{PROJECT}}

> This is the human-readable doc; the enforced version is `gates/boundary_contract.py` reading
> `gates/framework.yml` → `boundary:`. Keep these in sync — if you change one, change the other.

## Locked stack (what IS allowed, and where)
| Layer | Storage | Compute/engine | Sanctioned surface (which files/dirs may use it) |
|---|---|---|---|

## Rejected tech (what is explicitly NOT allowed, and why)
| Rejected | Reason | ADR reference |
|---|---|---|

## Ingestion allowlist
Only these ingestion mechanisms are sanctioned: {{list — e.g. "vendor API X, manual CSV drop"}}.
Anything else (Fivetran/Airbyte/new connector) requires an ADR before adoption.

## Enforcement
`gates/boundary_contract.py` checks:
- No banned import appears outside its sanctioned glob (see `framework.yml` → `boundary.banned_imports`).
- Profile/adapter config files match the locked compute target.
- (Extend per-project as needed — but extend the YAML, not this doc alone.)
