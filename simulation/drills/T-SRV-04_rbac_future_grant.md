# Drill T-SRV-04 — New Gold model invisible to the analyst role

> **Bank entry:** `PROBLEM_BANK_TROUBLESHOOT.md` T-SRV-04 (Lvl **L1** — execute checklist) ·
> **Fault:** `sec_missing_future_grant` · **Governs:** ADR-014 (§A RBAC role matrix),
> `scripts/provision_snowflake_serving.py`.
> **Run with** [@cikgu](../CIKGU_DRILL_PROTOCOL.md). **Answer is gated** in
> `../.solutions/T-SRV-04_rbac_future_grant.md` — do NOT open it until you've formed a hypothesis.

This drill is self-contained (a Python simulation of the grant matrix, no live Snowflake needed —
same isolation-safe shape as `T-L01`). It reproduces the exact bug class the real provisioning
script fixed this session.

---

## 0. Pre-flight
```bash
python simulation/check_isolation.py    # PASS — safe to break the lab
python simulation/faults/inject.py sec_missing_future_grant   # optional: plants a grants-snapshot
                                                                # fixture mirroring §2 below
```

## 1. The scenario (production framing)
> Kau on-call engineer. The pipeline shipped a new Gold model, `bridge_asset_lineage`, last week
> — `dbt build` green, `CREATIVE_INTEL_ROLE` (the pipeline's own role) reads it fine. Today a
> human analyst on `CREATIVE_INTEL_ANALYST_RO` pings you: **"Kenapa `bridge_asset_lineage`
> cakap table doesn't exist? Yang lain boleh."**

## 2. Reproduce it (isolation-safe — pure Python, no credentials)
```python
# save as /tmp/claude-1000/.../scratchpad/t_srv_04.py  or paste into: python3
# Simulates the PRE-fix grant pattern: a per-table GRANT list, no blanket/future grant.
tables = ["dim_asset", "fact_chunk", "fact_extraction_run"]
analyst_grants = {"dim_asset", "fact_chunk", "fact_extraction_run"}  # matches today's tables

# a new Gold model ships (this is what happened last week):
tables.append("bridge_asset_lineage")

def can_select(table: str) -> bool:
    return table in analyst_grants

for t in tables:
    print(t, "OK" if can_select(t) else "ACCESS DENIED (missing grant)")
```
Run it. `bridge_asset_lineage` prints `ACCESS DENIED` — the new model was never added to the
per-table grant list, and nobody re-ran the provisioning script for that one table.

## 3. The gate that should have caught it
There wasn't one — that's the point. A per-table grant list has **no gate**; it silently drifts
every time a model is added, until an analyst hits it live. The real fix is structural (a
blanket/future grant), not a checklist to remember to re-run.

Look at the REAL code: read `scripts/provision_snowflake_serving.py`'s `table_statements()` —
the last 3 lines (the ones granting `CREATIVE_INTEL_ANALYST_RO`) are the actual fix, added under
ADR-014. Compare them to the per-table loop just above (the pattern `CREATIVE_INTEL_ROLE` still
uses) — same function, two different grant strategies, side by side.

## 4. Your job (don't jump to the fix)
1. **What state is wrong?** Which role, which object, which grant statement is missing?
2. **Expected vs actual?** What should `can_select("bridge_asset_lineage")` return? What does it?
3. **Why does this role need a DIFFERENT grant strategy than `CREATIVE_INTEL_ROLE`** (which also
   uses a per-table list, and is intentionally left that way — see ADR-014 §A)? What's different
   about who consumes each role?
4. **The fix — in Snowflake grant vocabulary, not just "add a line."** What GRANT clause makes a
   permission apply to objects that don't exist *yet*? (Doc pointer, not the syntax handed to
   you: Snowflake's access-control docs, "future grants.")

## 5. Definition of Done
1. You can name the exact GRANT clause (not just "give it access") that closes this class of bug
   permanently, not just for `bridge_asset_lineage`.
2. Verify against the REAL fix already in this repo — run:
   ```bash
   python3 scripts/provision_snowflake_serving.py --phase tables | grep "FUTURE TABLES"
   ```
   Non-empty output = the named gate, not an eyeball.
3. You can state in one sentence why `CREATIVE_INTEL_ROLE` correctly does NOT need the same fix
   (hint: who reviews code before it adds a new model?).
4. You wrote `runbook/T-SRV-04_rbac_future_grant.md` in [CARD_FORMAT.md](../CARD_FORMAT.md).
5. Logged the pass in [../../learning/LEARNING_LOG.md](../../learning/LEARNING_LOG.md).

## 6. Reset
```bash
python simulation/faults/reset.py    # clears the planted scenario note + re-checks isolation
```

> When you've got a hypothesis for all 4 questions in §4 — THEN open the gated solution:
> `../.solutions/T-SRV-04_rbac_future_grant.md`.
