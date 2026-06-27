"""SUGGESTIVE-tier significance: DuckDB -> pandas -> scipy Mann-Whitney U + Bonferroni.

architecture/SPEC_v1.5_performance_marts.md §6 — the thin Python post-step that sits
downstream of `mart_chunk_perf_correlation`. SQL computes grouped aggregates + the G3
sample-size regime (`BLOCK` / `DIRECTIONAL` / `SUGGESTIVE`); SQL never computes a p-value.
This script is the ONLY place a p-value is computed, and it only runs for `SUGGESTIVE` rows
(n_ads >= 12, the spec's own gate) — `BLOCK`/`DIRECTIONAL` rows are statistically underpowered
by design and must never be promoted to "significant" by this step.

Test design (per spec): within each `(platform_id, metric_name, feature_dim)` family —
G2's within-platform grain carried straight through — take the SUGGESTIVE feature_value
ranked #1 by `mart_chunk_perf_correlation.rank_in_platform` ("top") and Mann-Whitney U it
against the pooled ad-level metric values of every OTHER feature_value in that same family
that also cleared SUGGESTIVE ("rest"). One test per family. Bonferroni correction is applied
across the number of families actually tested in this run (not a fixed constant) — adding
more SUGGESTIVE families in a future run correctly makes each individual test more
conservative, which is the point of the correction.

Idempotent / re-run safe: writes back by recomputing from `fct_ad_metric_chunk` (the
analysis-ready base) each run, not by mutating accumulated state — re-running this script
against an unchanged mart produces the same p-values, and a stale prior run's columns are
fully overwritten, never appended to.

Usage:
    python scripts/significance_post_step.py                # writes back into target/dev.duckdb
    python scripts/significance_post_step.py --dry-run        # prints the table, no UPDATE
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import pandas as pd
from scipy.stats import mannwhitneyu

DB_PATH = Path(__file__).parent.parent / "target" / "dev.duckdb"


def _connect(read_only: bool) -> duckdb.DuckDBPyConnection:
    if not DB_PATH.exists():
        print(
            f"error: {DB_PATH} not found — run `dbt build -s +marts.performance` first.",
            file=sys.stderr,
        )
        sys.exit(1)
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def compute_significance(con: duckdb.DuckDBPyConnection) -> tuple[pd.DataFrame, int]:
    """Returns one row per mart_chunk_perf_correlation row, with p_value/is_significant
    populated for SUGGESTIVE rows and NULL/false for everything else (never promoted)."""

    mart = con.sql(
        "select platform_id, metric_name, feature_dim, feature_value, n_ads, "
        "rank_in_platform, evidence_regime from mart_chunk_perf_correlation"
    ).df()

    # Ad-level metric values per (platform, metric, feature_dim, feature_value) — the
    # population each SUGGESTIVE feature_value's Mann-Whitney sample is drawn from.
    # Mirrors mart_chunk_perf_correlation.sql's own `base` CTE exactly (chunk_theme only,
    # as-built) so the per-ad values feeding the test are the same ones that produced
    # n_ads/median_metric in the mart.
    base = con.sql(
        "select platform_id, metric_name, 'chunk_theme' as feature_dim, "
        "chunk_theme as feature_value, ad_id, metric_value "
        "from fct_ad_metric_chunk where metric_value is not null"
    ).df()

    mart["p_value"] = pd.NA
    mart["is_significant"] = False

    suggestive = mart[mart["evidence_regime"] == "SUGGESTIVE"].copy()
    families = suggestive[["platform_id", "metric_name", "feature_dim"]].drop_duplicates()

    raw_tests: list[dict] = []  # one row per family's single top-vs-rest test, pre-Bonferroni

    for _, fam in families.iterrows():
        plat, metric, fdim = fam["platform_id"], fam["metric_name"], fam["feature_dim"]

        fam_suggestive = suggestive[
            (suggestive["platform_id"] == plat)
            & (suggestive["metric_name"] == metric)
            & (suggestive["feature_dim"] == fdim)
        ]
        if fam_suggestive.empty:
            continue

        # "Top" = the SUGGESTIVE feature_value ranked #1 within this platform x metric
        # (mart_chunk_perf_correlation.rank_in_platform is computed across ALL feature_values
        # for that platform x metric, not just SUGGESTIVE ones, so take the best-ranked
        # SUGGESTIVE row, not necessarily global rank 1).
        top_row = fam_suggestive.sort_values("rank_in_platform").iloc[0]
        top_value = top_row["feature_value"]

        fam_base = base[
            (base["platform_id"] == plat)
            & (base["metric_name"] == metric)
            & (base["feature_dim"] == fdim)
        ]
        top_vals = fam_base[fam_base["feature_value"] == top_value]["metric_value"]
        rest_vals = fam_base[fam_base["feature_value"] != top_value]["metric_value"]

        if len(top_vals) < 1 or len(rest_vals) < 1:
            # Degenerate family (e.g. only one feature_value ever existed) — cannot run a
            # two-sample test. Leave as NULL/false; do not fabricate a p-value.
            continue

        try:
            _, p_raw = mannwhitneyu(top_vals, rest_vals, alternative="two-sided")
        except ValueError:
            # All-identical values on both sides (mannwhitneyu raises) — no signal to test.
            continue

        raw_tests.append(
            {
                "platform_id": plat,
                "metric_name": metric,
                "feature_dim": fdim,
                "feature_value": top_value,
                "p_raw": p_raw,
            }
        )

    n_tests = len(raw_tests)
    for t in raw_tests:
        p_bonf = min(t["p_raw"] * n_tests, 1.0) if n_tests > 0 else t["p_raw"]
        mask = (
            (mart["platform_id"] == t["platform_id"])
            & (mart["metric_name"] == t["metric_name"])
            & (mart["feature_dim"] == t["feature_dim"])
            & (mart["feature_value"] == t["feature_value"])
        )
        mart.loc[mask, "p_value"] = p_bonf
        mart.loc[mask, "is_significant"] = bool(p_bonf < 0.05)

    return mart, n_tests


def write_back(con: duckdb.DuckDBPyConnection, scored: pd.DataFrame) -> None:
    """Adds/overwrites p_value (DOUBLE) + is_significant (BOOLEAN) on
    mart_chunk_perf_correlation. Full overwrite every run — not additive state."""
    con.execute(
        "ALTER TABLE mart_chunk_perf_correlation DROP COLUMN IF EXISTS p_value"
    )
    con.execute(
        "ALTER TABLE mart_chunk_perf_correlation DROP COLUMN IF EXISTS is_significant"
    )
    con.execute(
        "ALTER TABLE mart_chunk_perf_correlation ADD COLUMN p_value DOUBLE"
    )
    con.execute(
        "ALTER TABLE mart_chunk_perf_correlation ADD COLUMN is_significant BOOLEAN DEFAULT false"
    )
    con.register("scored_df", scored)
    con.execute(
        """
        UPDATE mart_chunk_perf_correlation m
        SET p_value = s.p_value, is_significant = s.is_significant
        FROM scored_df s
        WHERE m.platform_id = s.platform_id
          AND m.metric_name = s.metric_name
          AND m.feature_dim = s.feature_dim
          AND m.feature_value = s.feature_value
        """
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="compute and print, do not write back"
    )
    args = parser.parse_args()

    con = _connect(read_only=args.dry_run)
    scored, n_tests = compute_significance(con)

    print(f"Families tested (SUGGESTIVE, top-vs-rest Mann-Whitney U): {n_tests}")
    print(f"Bonferroni divisor (n tests in this run): {n_tests if n_tests else 1}")
    cols = [
        "platform_id", "metric_name", "feature_dim", "feature_value",
        "n_ads", "evidence_regime", "p_value", "is_significant",
    ]
    print(scored[cols].sort_values(["evidence_regime", "platform_id", "metric_name"]).to_string(index=False))

    if args.dry_run:
        print("\n--dry-run: no write-back performed.")
        return

    write_back(con, scored)
    con.close()
    print(f"\nWrote p_value/is_significant back to mart_chunk_perf_correlation in {DB_PATH}")


if __name__ == "__main__":
    main()
