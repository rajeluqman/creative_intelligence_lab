#!/usr/bin/env python3
"""Stack + scope boundary contract — deterministic gate over rejected tech & v2-backlog scope.

This is the ENFORCEMENT half of architecture/BOUNDARY_CONTRACT.md, mirroring
tests/lineage_contract.py's pattern (rules as code, not vigilance) for the two other named
governance axes in CLAUDE.md: the **stack boundary** (ADR-001/004/005, owner @data-architect)
and **v1 Scope LOCKED** (owner @scope-guardian). A doc says what's rejected; this script makes
a banned import/dependency a build failure instead of something someone has to notice in review.

Stdlib only ($0, no deps). Exit 0 = contract holds. Exit 1 = hard violation.

Rules:
  ST1  no Spark/Databricks (ADR-001 — DuckDB over Spark)
  ST2  no MinIO / S3 endpoint escape hatch (ADR-005 — unified S3, no MinIO)
  ST3  no dedicated vector DB client (ADR-001/004 + v1 scope OUT — "vector DB")
  ST4  dbt profile adapter type must be 'duckdb' only (ADR-001/005 — DuckDB is the transform engine;
       Snowflake is serving-only and must never appear as a `type:` target)
  ST5  no live ad-platform API connector SDK / Fivetran / Airbyte (ADR-004 — "Connectorized
       ingest... rejected... manual CSV->S3 until ~50+ ads/week + DA TCO sign-off")
  SC1  no RAG framework (v1 scope OUT — "RAG script generator")
  SC2  no dashboard app framework (v1 scope OUT — "creative-ops dashboard")

NOT covered here (named in the doc instead, not practically denylist-able without false
positives): "automated tagging/archiving" (v1 OUT) and "predictive ML scoring" (ADR-004
rejected) — both are behavior, not an import signature; @scope-guardian review still applies.

Run:  python tests/boundary_contract.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Executable/config surfaces only — architecture/, debate/, .claude/, cheatsheets/, README*,
# BACKLOG.md etc. legitimately discuss rejected tech BY NAME and must not trip this.
PY_GLOBS = ["scripts/*.py", "dags/*.py"]
SQL_GLOBS = ["models/**/*.sql", "analyses/*.sql"]
REQUIREMENTS_FILES = ["requirements.txt", "requirements-airflow.txt"]
PROFILE_FILES = ["profiles.yml.example", "dbt_project.yml"]
SHELL_FILES = ["setup.sh"]

IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([A-Za-z0-9_.]+)")
REQ_LINE_RE = re.compile(r"^([A-Za-z0-9_.-]+)")

# Denylist entries are dotted module / pip-package prefixes (matched whole-segment, not substring).
STACK_DENY: dict[str, str] = {
    "pyspark": "ADR-001 — DuckDB over Spark",
    "databricks": "ADR-001 — DuckDB over Spark (Databricks rejected)",
    "minio": "ADR-005 — unified S3 storage, no MinIO",
    "pinecone": "ADR-001/004 — rejected dedicated vector DB",
    "weaviate": "ADR-001/004 — rejected dedicated vector DB",
    "qdrant": "ADR-001/004 — rejected dedicated vector DB",
    "chromadb": "ADR-001/004 — rejected dedicated vector DB",
    "pymilvus": "ADR-001/004 — rejected dedicated vector DB",
    "faiss": "ADR-001/004 — rejected dedicated vector DB",
    "fivetran": "ADR-004 — connectorized ingest rejected (manual CSV->S3 until scale + DA sign-off)",
    "airbyte": "ADR-004 — connectorized ingest rejected (manual CSV->S3 until scale + DA sign-off)",
    "facebook_business": "ADR-004 — no live Meta Ads API connector (manual CSV->S3)",
    "tiktok_business": "ADR-004 — no live TikTok Ads API connector (manual CSV->S3)",
    "google.ads": "ADR-004 — no live Google Ads API connector (manual CSV->S3)",
}
SCOPE_DENY: dict[str, str] = {
    "langchain": "v1 Scope OUT — RAG script generator (v2 backlog)",
    "llama_index": "v1 Scope OUT — RAG script generator (v2 backlog)",
    "streamlit": "v1 Scope OUT — creative-ops dashboard (v2 backlog)",
    "dash": "v1 Scope OUT — creative-ops dashboard (v2 backlog)",
    "gradio": "v1 Scope OUT — creative-ops dashboard (v2 backlog)",
}
DENY = {**STACK_DENY, **SCOPE_DENY}
S3_ENDPOINT_RE = re.compile(r"^\s*S3_ENDPOINT\s*=\s*(\S+)")  # non-empty = MinIO/custom-endpoint escape hatch


def _hits_for_module(module: str) -> str | None:
    parts = module.lower().split(".")
    for i in range(1, len(parts) + 1):
        prefix = ".".join(parts[:i])
        if prefix in DENY:
            return DENY[prefix]
    return None


def _scan_python(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(REPO)
    for lineno, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
        m = IMPORT_RE.match(line)
        if not m:
            continue
        reason = _hits_for_module(m.group(1))
        if reason:
            errors.append(f"{rel}:{lineno}: banned import '{m.group(1)}' — {reason}")


def _scan_requirements(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(REPO)
    for lineno, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = REQ_LINE_RE.match(line)
        if not m:
            continue
        pkg = m.group(1).lower().replace("-", "_")
        reason = DENY.get(pkg)
        if reason:
            errors.append(f"{rel}:{lineno}: banned dependency '{m.group(1)}' — {reason}")


def _scan_shell_env(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(REPO)
    for lineno, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
        m = S3_ENDPOINT_RE.match(line)
        if m:
            errors.append(
                f"{rel}:{lineno}: S3_ENDPOINT set to non-empty value '{m.group(1)}' — "
                "ADR-005 unified S3, no MinIO/custom-endpoint escape hatch"
            )


def _scan_profile_adapter(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(REPO)
    type_re = re.compile(r"^\s*type:\s*(\S+)")
    for lineno, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
        m = type_re.match(line)
        if m and m.group(1) != "duckdb":
            errors.append(
                f"{rel}:{lineno}: dbt profile adapter type '{m.group(1)}' != 'duckdb' — "
                "ADR-001/005 DuckDB is the sole transform engine; Snowflake is serving-only"
            )


def check() -> list[str]:
    errors: list[str] = []

    for pattern in PY_GLOBS:
        for path in REPO.glob(pattern):
            _scan_python(path, errors)

    for pattern in SQL_GLOBS:
        for path in REPO.glob(pattern):
            _scan_python(path, errors)  # same import-style regex is harmless no-op on .sql

    for name in REQUIREMENTS_FILES:
        path = REPO / name
        if path.exists():
            _scan_requirements(path, errors)

    for name in SHELL_FILES:
        path = REPO / name
        if path.exists():
            _scan_shell_env(path, errors)
            _scan_requirements(path, errors)  # catches `pip install <banned>` style lines too

    for name in PROFILE_FILES:
        path = REPO / name
        if path.exists():
            _scan_profile_adapter(path, errors)

    return errors


def main() -> int:
    errors = check()
    if errors:
        print(f"\n❌ BOUNDARY CONTRACT FAILED — {len(errors)} violation(s):", file=sys.stderr)
        for e in sorted(set(errors)):
            print(f"   • {e}", file=sys.stderr)
        print(
            "\n   See architecture/BOUNDARY_CONTRACT.md + ADR-001/004/005 + CLAUDE.md v1 Scope. "
            "Fix before proceeding.",
            file=sys.stderr,
        )
        return 1
    print("✅ boundary contract OK (stack + scope)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
