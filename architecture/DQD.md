# DQD — Data Quality Document
## Creative Intelligence Pipeline

**Owner:** @data-quality-steward
**Status:** DRAFT — pending review
**Date:** 2026-06-22

> This is the narrative *why* behind the suites. `great_expectations/README.md` is the
> terse build manifest (what to bootstrap); this doc is the design reasoning + honest
> status of each gate. Per @scope-guardian's gate ruling: writing this narrative does
> **not** implement any TODO gate — open items are flagged OPEN below, not papered over.

---

## 1. The novel risk

**Silver is "unreliable narration"** — a row can be schema-valid yet semantically wrong,
because the upstream transform is a non-deterministic LLM, not a deterministic parser.
Five gates, cheapest-first (`architecture/DATA_MODEL.md` §7):

| # | Gate | Severity | Boundary | Action on failure |
|---|------|----------|----------|--------------------|
| 0 | Non-triviality / completeness-floor gate (`chunk_count >= 1`) | CRITICAL | Bronze | quarantine (warn + `store_failures`), never blocks batch |
| 1 | JSON-schema gate | CRITICAL | Bronze→Silver | quarantine, never blocks batch |
| 2 | Business-constraint gate (`1<=standalone_score<=5`, enum `sentiment`, non-empty `chunk_theme`) | CRITICAL | Silver | quarantine the row, **do not retry** — retrying non-deterministic input just burns API spend |
| 3 | Golden-dataset gate (~30–50 hand-labeled videos, pilot: 5; ≥80% Jaccard ±1 on score) | HIGH | pipeline-level | **the only gate allowed to fail a deploy** — human review, not auto-retry |
| 4 | Idempotency gate (same `asset_id` reprocessed) | MEDIUM | Silver | drift beyond tolerance is a **signal, not a block** — LLM variance is expected |

**Promotion rule:** Silver constraint-pass ≥95% before Gold build (`architecture/DATA_MODEL.md` §7).

## 2. Suites per layer

Source: `great_expectations/README.md`.

| Suite | Layer | Checks |
|-------|-------|--------|
| `bronze_asset_raw` | Bronze | Valid JSON; **chunks length ≥ 1** (catches schema-valid-but-empty LLM output — **BUILT**: `dbt_expectations.expect_column_values_to_be_between` on `chunk_count`, wired in `models/staging/_sources.yml`, `severity: warn` + `store_failures: true`; see §3) |
| `silver_chunk` | Silver | `standalone_score ∈ [1,5]`; `sentiment` enum; non-empty `chunk_theme`; `chunk_id` not-null+unique; table row-count ≥ 1 — **BUILT + RUN 2026-06-25**: `models/intermediate/_intermediate.yml` on `int_chunk_cleaned`, all 6 checks `warn`+`store_failures` (gate-2 quarantine convention) except the table row-count floor (`error` — a structural canary, not a per-row LLM-quality issue). Real run against the real 169-row Silver layer: PASS=7/7. |
| `fact_ad_performance` | Gold (v1.5) | counts/spend ≥ 0; `platform` enum; FK constrained to `EDITED`; every `ad_id` resolves to ≥1 chunk |
| `mart_chunk_perf_correlation` | Gold (v1.5) | `n_ads < 5` ⇒ BLOCK (not surfaced); `honesty_note` not null |

Full v1.5 gate list: `architecture/SPEC_v1.5_performance_marts.md` §7.

## 3. Known gaps

Honesty per Clean-ERD Doctrine rule 6 (name what is deliberately/currently out): a DQD
that claims completeness it doesn't have is worse than no DQD.

1. **5th LLM-output gate (non-triviality / completeness-floor) — RESOLVED 2026-06-25.**
   All four gates that existed in §1 previously passed a schema-valid-but-empty
   `{"chunks": []}` Gemini response untouched, because `stg_gemini_raw.sql`'s `unnest()` of
   an empty array produces zero rows — the asset silently disappears before reaching any
   Silver-layer row a later gate could test. Fix: a `dbt_expectations.expect_column_values_to_be_between`
   test (`min_value: 1`) on `bronze_asset_raw.chunk_count`, wired directly in
   `models/staging/_sources.yml` (the GE JSON spec at
   `great_expectations/expectations/bronze_asset_raw.json` line 12 already declared this
   check; this entry just confirms it is now built, not only specified). `config: {severity:
   warn, store_failures: true}` — deliberately not `error`, per this doc's own rule (§1 gate
   1 action-on-failure = "quarantine, never blocks batch"): a row failing this test is logged
   to dbt's audit-trail failures table for review, not allowed to fail `dbt build`'s exit code
   and halt the run over one bad asset. No new model or quarantine-table abstraction was
   introduced — `store_failures` is the existing dbt-native mechanism.
   Owner: @data-quality-steward. (`PROJECT_STATUS.md` finding #2 — closed by this change.)
2. **Row-count reconciliation, EDL → `bridge_ad_chunk` — DONE 2026-06-25.** An inner join can
   silently drop EDL rows whose `chunk_id` is absent from `fact_chunk`. HIGH severity.
   (`PROJECT_STATUS.md` finding #3.) Fixed by `tests/assert_edl_bridge_ad_chunk_reconciles.sql`
   (singular dbt test, anti-join idiom: `edit_decision_list LEFT JOIN fact_chunk ... WHERE
   fact_chunk.chunk_id IS NULL` — any row returned is exactly the set `bridge_ad_chunk`'s inner
   join would have silently dropped). Verified PASS against the real (currently empty)
   `edit_decision_list` seed via `dbt test`. **Honest gap:** a live red/green adversarial proof
   (inject one bad row, confirm FAIL, revert) was attempted and blocked by the harness's own
   safety classifier (treated overwriting a seed file as risky local destruction) — correctness
   rests on the anti-join pattern being a well-understood, structurally sound idiom, not on a
   live failing-then-passing demonstration. Flagging this rather than claiming more than verified.
3. **`bridge_ad_chunk` grain guard — DONE.** `unique_combination_of_columns
   [ad_id, chunk_id, position_in_ad]` + not-nulls + position-range test, added in
   `_performance.yml`. (`PROJECT_STATUS.md` finding #1 — included here for completeness,
   not as an open item.)

## 4. Reconciliation gate (serving-layer truth boundary)

The Snowflake Cortex serving veneer is read-only over Gold S3
(`architecture/ADR-005-unified-s3-and-snowflake-serving.md`). This is enforced by a
**reconciliation test**: Snowflake external-table row counts + key sets must exact-match
the DuckDB-over-S3 read of the same Gold parquet. This is not a nicety — it is the
mechanism that keeps "Gold S3 = sole source of truth" true in practice, not just on paper.
@data-architect's veto re-fires if Snowflake ever diverges (a Snowflake-only fact, a
CTAS-internal copy, a KPI persisted only in Snowflake).

## 5. Honesty gates (v1.5 — distinct from data-quality gates above)

These guard *interpretation*, not row validity — release blockers owned by
@data-quality-steward (`architecture/ADR-004-performance-veto-converted.md`):

- **G1 within-winners:** only "AMONG ads that already succeeded…" framing is honest output;
  causal/lift language is forbidden.
- **G2 within-platform:** no pooling Meta + TikTok; cross-platform = rank-direction
  agreement only.
- **G3 sample ladder:** n<5 BLOCK · 5–11 DIRECTIONAL · ≥12 (≥5/group) SUGGESTIVE.
- **G4 double-count guard:** 1 ad → N chunks; aggregate at theme/sentiment/role grain, never
  sum ad metrics across the bridge's N chunks.

## 6. Action on failure — summary

Quarantine-not-retry is the default for any row-level failure (gates 0–2, §1): retrying a
non-deterministic LLM call on the same input burns API spend for no reliability gain. The
only path that can fail a **deploy** (not a row) is the golden-dataset gate, and that
routes to human review, never auto-retry.

---

## Sign-off Gate

| Agent | Status | Reason | Date |
|-------|--------|--------|------|
| @data-architect | ✅ APPROVED (doc-gap convene) | Narrative consolidation, no new gate logic invented; open items flagged honestly | 2026-06-22 |
| @scope-guardian | ✅ APPROVED (doc-gap convene) | Documents existing/already-planned gates only; does not implement TODOs #2/#3 | 2026-06-22 |
| @data-quality-steward | ✅ APPROVED (gate 5 built) | Direct review by the suite owner, not just doc-gap drafting. 5th LLM-output gate (non-triviality / completeness-floor) implemented as a `dbt_expectations` column test on `bronze_asset_raw.chunk_count` (`models/staging/_sources.yml`), `severity: warn` + `store_failures: true` per §1 gate 1's "quarantine, never blocks batch" rule. §3 item 2 (EDL row-count reconciliation) remains OPEN and is explicitly out of scope for this sign-off — it does not block this gate's approval. | 2026-06-25 |
