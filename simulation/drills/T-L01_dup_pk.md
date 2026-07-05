# Drill T-L01 — Duplicate PK (the inflated number)

> **Ladder:** Troubleshooting L1 (execute checklist — symptom = root) · **Fault:** `dq_dup_pk`
> **RBC tasks:** 13 (investigate failed stage), 16 (fix broken SQL), 83 (dedup) ·
> **Resume:** Home Credit "deduplication"; PaySim "49/49 dbt tests".
> **Run with** [@cikgu](../CIKGU_DRILL_PROTOCOL.md). **Answer is gated** in
> `../.solutions/T-L01_dup_pk.md` — do NOT open it until you've formed a hypothesis.

This is the **template drill**. It is self-contained (inline DuckDB) so you can train today without
the full sim pipeline. Later drills follow this exact shape via `inject.py <fault_id>`.

---

## 0. Pre-flight
```bash
python simulation/check_isolation.py    # PASS — safe to break the lab
```

## 1. The scenario (production framing)
> Kau on-call engineer. Subuh tadi pipeline jalan "green" — no error, no alert. Tapi marketing
> lead WhatsApp kau: **"Kenapa total clips untuk client ACME naik 2× semalam? Kita tak upload
> apa-apa baru."** Build success. Test... let's see.

## 2. Reproduce it (run this — it's isolation-safe, local DuckDB only)
```sql
-- save as /tmp/claude-1000/.../scratchpad/t_l01.sql  or paste into: duckdb
CREATE TABLE silver_chunk AS
SELECT * FROM (VALUES
  ('acme', 'asset_001', 'chunk_01', 4),
  ('acme', 'asset_001', 'chunk_02', 5),
  ('acme', 'asset_002', 'chunk_01', 3),
  ('acme', 'asset_002', 'chunk_01', 3),   -- <-- the lab injected something here
  ('acme', 'asset_003', 'chunk_01', 2)
) AS t(client_id, asset_id, chunk_id, standalone_score);

-- the mart the marketing lead is looking at:
CREATE TABLE mart_client_summary AS
SELECT client_id, COUNT(*) AS total_chunks, AVG(standalone_score) AS avg_score
FROM silver_chunk GROUP BY client_id;

SELECT * FROM mart_client_summary;   -- total_chunks looks too high
```

## 3. The gate that should have caught it
```sql
-- grain contract: (client_id, asset_id, chunk_id) must be unique in silver_chunk
SELECT client_id, asset_id, chunk_id, COUNT(*) AS n
FROM silver_chunk
GROUP BY 1,2,3
HAVING COUNT(*) > 1;     -- a uniqueness/grain test asserts this returns ZERO rows
```

## 4. Your job (think in PEDAGOGY_PREFS terms — don't jump to the fix)
Answer these BEFORE proposing a change. Cikgu will ask them one at a time:
1. **What state is wrong?** Which table, which column, which row?
2. **Expected vs actual?** What *should* `total_chunks` be for ACME? What is it?
3. **Business expectation?** What does "1 row in silver_chunk" mean in real life?
4. **Root cause?** Is the bug in the *data* (a real duplicate clip) or the *code* (a join fanning
   out)? How would you tell the two apart? (This is the L1→L3 skill seed.)
5. **The fix — and the trap.** What's the *wrong* way to make the number go down? (Hint: deleting
   rows blindly is not dedup.)

## 5. Definition of Done
1. The **named gate** (the uniqueness query in §3) returns **0 rows** after your fix — not eyeballed.
2. You can state, in one sentence, whether it was a **data** or **code** root cause and how you knew.
3. `mart_client_summary.total_chunks` for ACME is correct AND you verified it didn't *under*-count.
4. You wrote `runbook/T-L01_dup_pk.md` in [CARD_FORMAT.md](../CARD_FORMAT.md) — filling **⚠️ Junior
   mistake** and **🎤 Soundbite** yourself.
5. Logged the pass in [../../learning/LEARNING_LOG.md](../../learning/LEARNING_LOG.md).

## 6. Reset
```bash
# for the inline version: DROP TABLE silver_chunk, mart_client_summary;
# for the inject.py version (once built): python simulation/faults/reset.py
```

> When you've got a hypothesis for all 5 questions in §4 — THEN open the gated solution to check
> yourself: `../.solutions/T-L01_dup_pk.md`.
