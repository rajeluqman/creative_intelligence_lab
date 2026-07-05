<!-- FRAMEWORK_TEMPLATE: UNFILLED — remove this line once real project content is added below -->
# 05 — Source-to-Target Mapping (STTM)

> If not applicable: `N/A — <reason>`. See `00_START_HERE.md`.

## Mapping table (repeat block per target table)

### Target: `<layer>.<table_name>`
| Target column | Type | Source | Source column | Transform rule | Nullable? | Notes |
|---|---|---|---|---|---|---|

## Transform conventions used project-wide
- Naming convention (snake_case, prefixing, etc.)
- Null handling default (explicit `NULL` vs sentinel value — pick one, state it)
- Timezone/date normalization rule
- Currency/unit normalization rule, if applicable

## Drift check
This doc is what `gates/doc_reference_contract.py` (or an STTM-specific variant) can validate
against real model files — every target table named above should resolve to an actual model on
disk. If it doesn't yet, that's expected pre-build; note the target ship date.
