#!/usr/bin/env python3
"""Doc-reference contract — deterministic gate against documentation drift.

This is the ANTI-SHORTCUT PROTOCOL's machine half (see CLAUDE.md). The protocol asks
the author (human or LLM) to read-before-touch and reconcile-before-done; this script
makes one slice of that true *without depending on anyone remembering* — it proves that
every model name and repo path a Markdown doc references ACTUALLY EXISTS. Code does not
get tired, and code does not write a migration map from memory.

It catches the exact failure class that bit this repo before (a stale DATA_MODEL.md that
named a VETOED table; a MIGRATION_MAP that lists a model that was renamed): a doc claims
`fact_chunk_v2` or `models/marts/core/dim_foo.sql` and neither exists. Drift = lie = gap.

Stdlib only ($0, no deps). Exit 0 = every checked reference resolves. Exit 1 = drift.

What it checks (deliberately narrow, to keep false positives near zero):
  C1  MODEL/SEED refs — backtick-wrapped tokens shaped like a dbt object
      (prefix fact_/fct_/dim_/stg_/int_/bridge_/mart_/map_) must be a real model
      under models/**/*.sql or a real seed under seeds/*.csv (or in ALLOW below).
  C2  PATH refs — backtick tokens and []() link targets that point at a repo path
      (models/ seeds/ scripts/ architecture/ tests/ dags/ .claude/ great_expectations/)
      must exist on disk.

What it deliberately does NOT check (stated so the limit is not mistaken for coverage):
  - prose mentions outside backticks (too noisy); s3:// runtime paths (that's
    lineage_contract.py's job); external URLs; column-level existence (future work).

Run:  python tests/doc_reference_contract.py                 # default doc set
      python tests/doc_reference_contract.py path/to/FILE.md ...   # explicit files
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# dbt-object-shaped token: one of the known grain prefixes + snake_case body.
MODEL_TOKEN = re.compile(r"^(?:fact|fct|dim|stg|int|bridge|mart|map)_[a-z0-9_]+$")
# repo path roots that must resolve on disk if a doc points at them.
PATH_ROOTS = ("models/", "seeds/", "scripts/", "architecture/", "tests/", "dags/",
              ".claude/", "great_expectations/", "analyses/", "macros/")

# Intentionally-not-yet-existing or renamed names a doc may legitimately reference.
# Mirror lineage_contract.py's GRANDFATHERED pattern: name the debt, don't silence it.
# Each entry MUST carry a reason so the allowlist can't quietly rot into a dumping ground.
ALLOW: dict[str, str] = {
    "bridge_client_asset_curation": "deliberately-OUT v1.5 model, named in ERD_consolidated.md §6 "
    "per Clean-ERD doctrine ('what's OUT stays named'); not built yet by design.",
    "stg_beta__ndc": "cross-project analogy (pharma_novartis_sttm sibling repo's bug class), "
    "cited in PROJECT_STATUS.md as a precedent — never a model in THIS repo by design.",
}


def _known_objects() -> set[str]:
    """Every real dbt model (by .sql basename) + every real seed (by .csv basename)."""
    models = {p.stem for p in (REPO / "models").rglob("*.sql")}
    seeds = {p.stem for p in (REPO / "seeds").glob("*.csv")}
    return models | seeds


def _default_docs() -> list[Path]:
    """Current-state 'architecture of record' docs only.

    Deliberately EXCLUDES two genres where a missing reference is correct, not drift:
      - SPEC_*.md      — specs name FUTURE build targets that don't exist yet by design.
      - changelogs/narrative (PROJECT_STATUS.md, BACKLOG.md, README*, CLAUDE.md) — past-tense
        references to deleted/other-repo things are valid history.
    Point the tool at those explicitly (or at a MIGRATION_MAP.md) via argv when you want them.
    """
    return [p for p in sorted((REPO / "architecture").glob("*.md"))
            if not p.name.startswith("SPEC_")]


def check(docs: list[Path]) -> list[str]:
    known = _known_objects()
    errors: list[str] = []

    backtick = re.compile(r"`([^`]+)`")
    link = re.compile(r"\]\(([^)]+)\)")

    for doc in docs:
        if not doc.exists():
            errors.append(f"{doc}: doc file does not exist")
            continue
        rel = doc.relative_to(REPO)
        for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            # C1 — model/seed-shaped tokens inside backticks
            for tok in backtick.findall(line):
                tok = tok.strip()
                if MODEL_TOKEN.match(tok) and tok not in known and tok not in ALLOW:
                    errors.append(
                        f"{rel}:{lineno}  C1 model/seed `{tok}` referenced but no "
                        f"models/**/{tok}.sql or seeds/{tok}.csv exists (drift)"
                    )

            # C2 — repo paths in backticks or markdown links must exist on disk
            candidates = backtick.findall(line) + link.findall(line)
            for cand in candidates:
                cand = cand.strip().split("#", 1)[0].strip()  # drop anchors
                if cand.startswith(("http://", "https://", "s3://", "mailto:")):
                    continue
                if not cand.startswith(PATH_ROOTS):
                    continue
                if "*" in cand or "{" in cand:  # glob / template path — not a literal file
                    continue
                if not (REPO / cand).exists():
                    errors.append(f"{rel}:{lineno}  C2 path `{cand}` referenced but not found on disk")

    return errors


def main(argv: list[str]) -> int:
    docs = [Path(a) for a in argv[1:]] if len(argv) > 1 else _default_docs()
    docs = [d if d.is_absolute() else (REPO / d) for d in docs]
    errors = check(docs)
    if errors:
        print(f"DOC-REFERENCE CONTRACT: {len(errors)} drift violation(s)\n")
        for e in errors:
            print(f"  ✗ {e}")
        print("\nFix the doc or add a reasoned entry to ALLOW. Drift is a lie waiting to mislead.")
        return 1
    print(f"DOC-REFERENCE CONTRACT: OK — {len(docs)} doc(s), all model/path references resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
