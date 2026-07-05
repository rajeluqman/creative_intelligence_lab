# 🔒 GATED SOLUTION — T-L01 Duplicate PK

> **STOP.** Only open this after you've answered all 5 questions in the drill. Cikgu uses this to
> *check* you and to escalate hints (H0→H3), never to hand you the answer. Taught in
> [PEDAGOGY_PREFS](../PEDAGOGY_PREFS.md) order: mental model → ETL → bug → debug → fix.

---

## Mental model (analogi dulu)
Grain key `(client_id, asset_id, chunk_id)` ialah macam **nombor IC**. Satu orang, satu IC. Kalau
dalam buku rekod ada **dua baris dengan IC sama**, bukan dua orang — itu **satu orang tercatat dua
kali**. `COUNT(*)` tak tahu beza; dia kira baris, bukan orang. Itu sebab total naik 2×.

## ETL use case (di mana ia muncul)
This is the **grain contract** of the Silver layer (ADR-002/DATA_MODEL: row-per-semantic-chunk).
Every fact/aggregate downstream trusts that Silver is unique on its grain. Break that, and *every*
`COUNT`/`SUM`/`AVG` above it inflates — silently, because the build still succeeds.

## The bug, round-by-round
```
mart_client_summary for ACME:
  real rows:        asset_001/chunk_01, asset_001/chunk_02, asset_002/chunk_01, asset_003/chunk_01 = 4
  but silver had:   asset_002/chunk_01 TWICE
  COUNT(*)        → 5   (wrong, +1 phantom)
  AVG(score)      → pulled toward the duplicated row's value (also wrong)
```

## Debug flow (the answers to §4)
1. **Wrong state:** `silver_chunk` — a duplicate row on the grain key `(acme, asset_002, chunk_01)`.
2. **Expected vs actual:** ACME `total_chunks` should be **4**, actual **5**.
3. **Business meaning:** one Silver row = one distinct semantic chunk of one asset. A duplicate =
   the same clip counted twice → marketing over-counts available footage.
4. **Data vs code — how to tell:** run the §3 uniqueness query. If duplicates exist *in the source
   seed*, it's **data** (a real dup upstream). If the source is clean but the model fans out, it's
   **code** (a join hitting a non-unique key). Here it's a duplicate row in `silver_chunk` itself →
   **data-layer**. The split-test (rerun the transform on a known-clean sample) is the L3 skill.
5. **The trap (⚠️ junior mistake):** `DELETE` rows until the count looks right. That's not dedup —
   you might delete the *wrong* row, or a real distinct chunk. Correct dedup is **deterministic**:
   keep one row per grain key by an explicit rule.

## The fix
```sql
-- deterministic dedup: one row per grain key. ROW_NUMBER, not blind DELETE.
CREATE OR REPLACE TABLE silver_chunk AS
SELECT client_id, asset_id, chunk_id, standalone_score
FROM (
  SELECT *, ROW_NUMBER() OVER (
           PARTITION BY client_id, asset_id, chunk_id
           ORDER BY standalone_score DESC   -- explicit tie-break, not arbitrary
         ) AS rn
  FROM silver_chunk
)
WHERE rn = 1;
```

## Verify (the named gate — don't eyeball)
```sql
SELECT client_id, asset_id, chunk_id, COUNT(*) n
FROM silver_chunk GROUP BY 1,2,3 HAVING COUNT(*) > 1;   -- must return 0 rows
SELECT * FROM mart_client_summary;  -- rebuild; ACME total_chunks = 4, and NOT under-counted
```
**Prevention:** this is why the grain has a `unique` test in dbt + a GE expectation. The gate
existed conceptually; the drill is "the gate fired, now trace and fix correctly."

## Card fields (model answer)
- **⚠️ Junior mistake:** "Made the number go down with a blind DELETE" — fixes the symptom, corrupts
  the data. Or: assumed it was a join bug without checking the source was clean first.
- **🎤 Soundbite:** *"Inflated aggregate, build still green — classic grain violation. I confirmed
  it was a source duplicate, not a fan-out, then deduped deterministically with ROW_NUMBER and a
  defined tie-break, and re-ran the uniqueness gate to zero."*

## Spark vocab (for interview transfer)
Same skill in Databricks: a non-unique join key causing **fan-out / row explosion**; you'd
`dropDuplicates(subset=[...])` or a windowed `row_number().filter(rn==1)` — identical reasoning,
different engine.
