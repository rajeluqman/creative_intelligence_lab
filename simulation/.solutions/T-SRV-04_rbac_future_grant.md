# 🔒 GATED SOLUTION — T-SRV-04 RBAC Future Grant

> **STOP.** Only open this after you've answered all 4 questions in the drill. Taught in
> [PEDAGOGY_PREFS](../PEDAGOGY_PREFS.md) order: mental model → real code → debug → fix.

---

## Mental model (analogi dulu)
A per-object GRANT list is macam **senarai tetamu untuk satu majlis sahaja** — kalau ada majlis
baru (table baru), nama kena ditambah manual dalam senarai tu. Kalau lupa tambah, tetamu tu
`ACCESS DENIED` kat pintu, walaupun dia sepatutnya boleh masuk. A FUTURE grant is a **standing
policy** ("anyone on this list gets into every future event of this type"), not a per-event
guest list — the object doesn't need to exist yet for the grant to apply to it later.

## Where it lives in the real code
`scripts/provision_snowflake_serving.py::table_statements()` — two roles, two strategies,
side by side:
```python
for model in GOLD_MODELS:
    stmts.append(f"GRANT SELECT ON PUBLIC.{model.upper()} TO ROLE {cfg['role']};")   # per-table list
...
stmts.append(f"GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO ROLE {cfg['analyst_role']};")
stmts.append(f"GRANT SELECT ON FUTURE TABLES IN SCHEMA PUBLIC TO ROLE {cfg['analyst_role']};")
```

## The answers to §4
1. **Wrong state:** the analyst role's grant set is missing an entry for `bridge_asset_lineage`
   — not a code bug, a **drift** bug: the grant list and the model list fell out of sync.
2. **Expected vs actual:** `can_select("bridge_asset_lineage")` should be `True` (any Gold model
   is analyst-readable by design, ADR-014 §A); it returns `False`.
3. **Why the two roles differ:** `CREATIVE_INTEL_ROLE` is the pipeline's OWN role — every time a
   new Gold model is added, the same PR/commit that adds the model also has to touch the
   `GOLD_MODELS` list and (by extension) this script, so there's a natural code-review gate
   forcing the grant to be added in the same change. An ad-hoc human analyst has no such
   review step — they just run queries whenever — so their access can't depend on someone
   remembering to re-run a provisioning script for every new model.
4. **The fix, in Snowflake vocabulary:** `GRANT SELECT ON FUTURE TABLES IN SCHEMA <schema> TO ROLE
   <role>;` — a **future grant**. It attaches the privilege to the schema/role pairing itself,
   so Snowflake auto-applies it to any object created in that schema from then on, no matter
   when. `GRANT ... ON ALL TABLES ...` is needed too, once, to cover objects that already
   existed before the future grant was declared (future grants are NOT retroactive).

## Verify (the named gate — don't eyeball)
```bash
python3 scripts/provision_snowflake_serving.py --phase tables | grep "FUTURE TABLES"
# GRANT SELECT ON FUTURE TABLES IN SCHEMA PUBLIC TO ROLE CREATIVE_INTEL_ANALYST_RO;
```
Non-empty = the fix is real, not described. In a live account you'd additionally confirm via
`SHOW FUTURE GRANTS IN SCHEMA PUBLIC;` — not run here (dry-run only, no live Snowflake needed for
this drill).

## Card fields (model answer)
- **⚠️ Junior mistake:** "just add the missing GRANT for this one table and move on" — fixes
  today's ticket, guarantees the exact same page next time a model ships. The senior fix changes
  the grant *strategy*, not the grant *list*.
- **🎤 Soundbite:** *"A per-object grant list for a human-facing role is a drift bug waiting to
  happen — I replaced it with a future grant so a new Gold model is analyst-visible the moment
  it's created, with zero incremental provisioning step."*

## Cloud vocab (for interview transfer)
Same concept in AWS: an IAM policy with `Resource: "arn:aws:s3:::bucket/*"` (wildcard, effectively
"future" objects under that prefix) vs one listing every object ARN explicitly — the wildcard
form is the one that doesn't drift as new objects land.
