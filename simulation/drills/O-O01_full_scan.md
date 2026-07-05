# Drill O-O01 — Read the Plan (the full scan)

> **Ladder:** Optimization O1 (read `EXPLAIN ANALYZE` before touching anything) · **Fault:**
> `perf_full_scan` · **RBC tasks:** 7 (duration trend), 70 (map DuckDB perf-thinking → Spark) ·
> **Resume:** "Query Performance Optimisation". **Answer gated** in `../.solutions/O-O01_full_scan.md`.

The O-ladder rule: **the number is the story.** "I cut it from X to Y" beats any adjective. So you
ALWAYS profile before and after — one change, measured.

---

## 0. Pre-flight
```bash
python simulation/check_isolation.py    # PASS
```

## 1. The scenario
> Kau on-call. The nightly `mart_high_value_chunks` step that used to finish in seconds now drags.
> No new data volume. Someone "tidied up" a filter last week. Find out why it's slow — **with
> evidence, not a guess.**

## 2. Reproduce (isolation-safe, local DuckDB)
```sql
-- build a chunk table with a clean integer score and a messy string score
CREATE TABLE silver_chunk AS
SELECT i AS chunk_pk,
       (i % 5) + 1                          AS standalone_score,      -- clean: integer 1..5
       CAST((i % 5) + 1 AS VARCHAR) || '/5' AS standalone_score_str   -- messy: '1/5'..'5/5'
FROM range(2_000_000) t(i);

-- the SLOW query someone "tidied" — filters on the messy string with a function on the column:
EXPLAIN ANALYZE
SELECT count(*) FROM silver_chunk
WHERE CAST(split_part(standalone_score_str, '/', 1) AS INTEGER) >= 4;
```

## 3. Your job (O-ladder discipline)
1. **Profile BEFORE touching anything.** Run the `EXPLAIN ANALYZE`. Record: does it scan all 2M
   rows? What's the timing? (Write the real number down — that's your baseline.)
2. **Read the plan.** Why can't the engine skip rows? What is the function on the column doing to
   the filter? (This is the *sargability* idea — the O1 concept.)
3. **ONE hypothesis, ONE change.** Don't change three things. What single change lets the filter
   work on a clean column instead of a computed one?
4. **Profile AFTER.** Re-run, record the new timing, compute the delta `X → Y, -Z%`.
5. **Map to Spark vocab** for the interview (see the gated solution if stuck — but try first).

## 4. Definition of Done
1. **Before AND after** timings recorded — real numbers, same session.
2. **Exactly one** change attributed to the improvement (or honest "no gain, reverted").
3. `runbook/O-O01_full_scan.md` in [CARD_FORMAT.md](../CARD_FORMAT.md), with the `→ Spark vocab`
   line filled.
4. `check_isolation.py` PASS.

## 5. Reset
```sql
DROP TABLE silver_chunk;
```

> Hypothesis ready? Check yourself against `../.solutions/O-O01_full_scan.md`.
