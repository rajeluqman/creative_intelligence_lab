# 🔒 GATED SOLUTION — O-O01 Read the Plan (full scan)

> Open only after you've profiled and formed ONE hypothesis. Taught mental-model-first.

---

## Mental model (analogi)
Bayangkan buku telefon disusun ikut **nama**. Kalau aku tanya "cari semua orang nama mula 'A'" —
senang, terus pergi bahagian A. Tapi kalau aku tanya "cari semua orang yang **huruf ke-3 nama dia
'r'**" — kau terpaksa baca **setiap muka surat**, sebab susunan buku tak membantu. Letak **fungsi
atas column** dalam `WHERE` = buat engine baca setiap baris. Itu **non-sargable** = full scan.

## The bug
```sql
WHERE CAST(split_part(standalone_score_str, '/', 1) AS INTEGER) >= 4
```
The filter wraps the column in `split_part(...) + CAST(...)`. The engine must **compute that
expression for all 2,000,000 rows** before it can decide which to keep. Nothing can be skipped —
`EXPLAIN ANALYZE` shows a full scan of 2M rows feeding the filter.

## The fix (ONE change — filter the clean column)
```sql
EXPLAIN ANALYZE
SELECT count(*) FROM silver_chunk
WHERE standalone_score >= 4;     -- sargable: bare column, no per-row function
```
The real lesson isn't "this one query" — it's the **upstream data-quality decision**: a score
should land in Silver as a clean **INTEGER** (`standalone_score`), not a string like `'4/5'` you
have to parse at query time. Parsing-on-read is the smell; fix it at the layer that produces it.

## Measure (the number is the story)
Run both `EXPLAIN ANALYZE`, record real timings on your machine, e.g.:
```
before (function on column) : ~X ms, full scan 2,000,000 rows
after  (bare column filter) : ~Y ms, filter pushed to scan
delta : X → Y  (-Z%)
```
> If your delta is small, say so honestly and revert — don't invent a number. "No gain, reverted,
> here's why" is a valid, mature result.

## Card fields (model answer)
- **⚠️ Junior mistake:** "speculative tuning" — adding an index/changing memory_limit/rewriting the
  join all at once, so you can't attribute the win. Or never running `EXPLAIN` at all and guessing.
- **🎤 Soundbite:** *"It was non-sargable — a function on the column forced a full 2M-row scan. I
  profiled with EXPLAIN ANALYZE, made the filter operate on a clean integer column, re-profiled, and
  cut it from X to Y. Root cause was upstream: the score should be typed INTEGER in Silver, not
  parsed at read time."*
- **→ Spark vocab:** same diagnosis = "predicate pushdown blocked by a UDF/expression on the
  partition/filter column; push the filter down / pre-cast so the scan can prune."

## Why this is O1 (the foundational rung)
Every higher optimization rung (pushdown, pruning, join-grain, skew) starts with the same move you
just did: **read the plan before you touch anything.** Speculative tuning is the cardinal sin —
O-O01 builds the reflex that prevents it.
