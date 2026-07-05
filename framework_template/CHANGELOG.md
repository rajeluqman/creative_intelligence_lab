# Framework Template — Changelog

## v1.1.0 (2026-07-04)
Security layer — see `governance/ADR/ADR-001-security-layer-mandatory.md`. Generalized from
creative_intelligence_lab's ADR-014 (2026-07-04 owner override: one real least-privilege role +
one ADR, not a security program). Contents: `journey/09_SECURITY_AND_ACCESS.md` (9th mandatory
journey doc — secrets management, data classification, RBAC role matrix, service identities,
audit/log enablement, PII handling, compliance flags, incident contacts, all individually
N/A-able), `gates/secrets_scan.py` (config-driven, stdlib-only, `--self-test` mode; detects
literal password/api_key/secret/token assignments, AWS access keys, private-key headers,
connection strings with embedded passwords), `framework.yml` `secrets_scan:` section +9th
required doc, `ci.yml.template` wired with the new gate step.

Known limitation, corrected from v1.0.0's note: the minimal YAML fallback parser in
`gates/_config.py` does not correctly parse a list nested two levels deep under a top-level key
(e.g. `paths.path_roots`, `secrets_scan.allowlist_paths`) — it flattens the child list directly
onto the top-level key and loses the intermediate key names entirely. This is broader than the
v1.0.0 note's "list-of-dicts only" claim; it affects any two-level nesting with a list at the
second level, present since v1.0.0 (`paths:` already had this shape). Not fixed here — the
documented, CI-enforced assumption (`ci.yml.template`'s first step is `pip install pyyaml`) is
that real PyYAML is always available, and every affected config key was verified to parse
correctly under real PyYAML. The fallback parser remains a best-effort degrade path, not a
guarantee, for structures beyond flat maps and single-level string lists.

## v1.0.0 (2026-07-04)
Initial extraction. Built by diffing the 4 pipeline_retrofit repos (home-credit, olist,
paysim, Volve) against CIL's original governance layer — every gate script in that retrofit was
hand-edited per repo with identical logic and different hardcoded config values. This kit
converts that config into `gates/framework.yml`, read by generalized gate scripts, so future
adoptions don't require editing Python to retarget.

Contents: 8 mandatory journey docs (full-set, owner ruling 2026-07-04), ADR-000 feature-intake
protocol (answers "how do we control ad-hoc feature scope creep"), generic role-based agent
roster (architect/scope-guardian veto-holders + build agents), config-driven gates
(journey_completeness, boundary_contract, doc_reference_contract) + governance_guard hook
skeleton + CI template.

Known limitation: the minimal YAML fallback parser in `gates/_config.py` handles flat maps and
string lists, not list-of-dicts (used by `governed_paths:` in framework.yml) — that section
needs real PyYAML installed to work; the hook degrades to a no-op without it rather than
crashing.
