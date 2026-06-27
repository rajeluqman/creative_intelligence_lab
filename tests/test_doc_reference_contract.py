#!/usr/bin/env python3
"""Self-test for tests/doc_reference_contract.py — proves the gate actually fires.

A gate you never tested is a gap waiting to happen (the exact thing the contract guards
against). This drives the real check() against two synthetic docs written under the repo:
one CLEAN (must pass), one DIRTY (must catch every planted drift). Stdlib only, no pytest.

Run:  python tests/test_doc_reference_contract.py     # exit 0 = pass, 1 = fail
"""

from __future__ import annotations

import shutil
from pathlib import Path

import doc_reference_contract as drc

REPO = drc.REPO
# Fixtures must live UNDER the repo — check() calls doc.relative_to(REPO).
FIXTURE_DIR = REPO / ".tmp_doctest_fixtures"

# A real model and a real path that must resolve cleanly.
REAL_MODEL = "fact_chunk"               # models/marts/core/fact_chunk.sql
REAL_PATH = "models/staging/stg_gemini_raw.sql"
# Planted drift that must be caught.
GHOST_MODEL = "fact_does_not_exist_xyz"  # no such .sql / .csv
GHOST_PATH = "models/marts/core/ghost_nonexistent.sql"

CLEAN_DOC = f"""# Clean fixture
Transform `{REAL_MODEL}` is wired; see `{REAL_PATH}`.
A planned-but-allowlisted name `bridge_client_asset_curation` must NOT trip (it's in ALLOW).
An external link [docs](https://example.com) and an s3 path `s3://b/landing/c/video/x.mp4`
must be ignored, not flagged.
"""

DIRTY_DOC = f"""# Dirty fixture
This references `{GHOST_MODEL}` which does not exist (C1 drift).
And points at `{GHOST_PATH}` which is not on disk (C2 drift).
"""


def _write(name: str, body: str) -> Path:
    p = FIXTURE_DIR / name
    p.write_text(body, encoding="utf-8")
    return p


def run() -> int:
    FIXTURE_DIR.mkdir(exist_ok=True)
    failures: list[str] = []
    try:
        clean = _write("clean.md", CLEAN_DOC)
        dirty = _write("dirty.md", DIRTY_DOC)

        # 1. CLEAN doc → zero errors.
        clean_errs = drc.check([clean])
        if clean_errs:
            failures.append(f"CLEAN doc should have 0 errors, got {len(clean_errs)}: {clean_errs}")

        # 2. DIRTY doc → exactly the two planted drifts, named.
        dirty_errs = drc.check([dirty])
        joined = "\n".join(dirty_errs)
        if not any(GHOST_MODEL in e and "C1" in e for e in dirty_errs):
            failures.append(f"DIRTY doc: C1 drift on {GHOST_MODEL} not caught. Got:\n{joined}")
        if not any(GHOST_PATH in e and "C2" in e for e in dirty_errs):
            failures.append(f"DIRTY doc: C2 drift on {GHOST_PATH} not caught. Got:\n{joined}")

        # 3. ALLOW + external/s3 refs in the clean doc were correctly ignored (covered by #1,
        #    but assert the allowlisted name specifically never appears as an error anywhere).
        if any("bridge_client_asset_curation" in e for e in clean_errs):
            failures.append("ALLOW-listed name was flagged — allowlist not honoured")
    finally:
        shutil.rmtree(FIXTURE_DIR, ignore_errors=True)

    if failures:
        print(f"SELF-TEST FAILED ({len(failures)}):")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    print("SELF-TEST OK — clean doc passes, both planted drifts caught, allowlist + non-repo refs ignored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
