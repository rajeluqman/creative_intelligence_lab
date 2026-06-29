#!/usr/bin/env python3
"""Repo-map generator — the NAVIGATION half of the ANTI-SHORTCUT PROTOCOL (see CLAUDE.md).

The protocol's other gates prove correctness of governed files (lineage/boundary/doc-ref).
None of them answer the cheap question "what is this file, what uses it, what does it use?"
without scanning the repo by hand — and hand-scanning from in-context memory is exactly the
shortcut that produces "missing gaps". This builds a pointer index so the answer is one cheap
read, NOT a whole-repo token burn.

Design rule (the thing that makes it safe): the map is a POINTER, never a substitute for
reading the file. It tells you WHICH file to open; you still read that file fresh before you
touch or assert about it. A pointer you trust without opening is just a bigger stale cache —
the bug, scaled up. So the map is kept *impossible to drift*:

  - It is 100% DERIVED, nothing is hand-authored. Purpose is extracted from the file itself
    (module docstring / first Markdown heading / leading SQL comment), so it lives where it
    can't fall out of sync. Edges are parsed with `ast` (.py imports) and `ref()` (.sql), not
    guessed — an LLM rewriting a docstring or moving an import shows up on regeneration.
  - The CI gate is `--check`: regenerate in memory, diff against the committed REPO_MAP.md,
    fail if they differ (same idea as `black --check` / `gofmt -l`). You cannot land a code
    or model change that shifts the dependency graph without the index moving with it. That
    is the binding answer to "an ad-hoc change quietly altered the architecture": the graph
    edge drifts, the gate goes red, the file is forced back into the index with its purpose.

Stdlib only ($0, no deps). Exit 0 = map is fresh. Exit 1 (with --check) = stale, regenerate.

Run:  python scripts/gen_repo_map.py            # (re)write architecture/REPO_MAP.md
      python scripts/gen_repo_map.py --check    # CI gate: fail if committed map is stale
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MAP_PATH = REPO / "architecture" / "REPO_MAP.md"

# Deliberately NOT mapped — config/lock/secret-template noise where an entry adds nothing.
# Stated here so the exclusion is a decision on the record, not a silent gap (cf. the
# "Enumerate, don't sample" rule: name what you leave out).
EXCLUDE = {
    ".gitignore", ".env.example", "profiles.yml.example", "package-lock.yml",
    ".user.yml", ".claude/settings.json",
    "architecture/REPO_MAP.md",  # the map never maps itself (would self-churn)
}
EXCLUDE_PREFIX = (".github/",)

# Section render order + human label. Anything unmapped-by-role falls through to "other".
ROLE_LABELS = [
    ("adr", "Architecture Decision Records"),
    ("arch-doc", "Architecture docs (record)"),
    ("dbt:staging", "dbt — staging"),
    ("dbt:intermediate", "dbt — intermediate"),
    ("dbt:mart-core", "dbt — marts/core"),
    ("dbt:mart-perf", "dbt — marts/performance"),
    ("dbt:model", "dbt — other models"),
    ("seed", "Seeds"),
    ("script", "Scripts"),
    ("dag", "Airflow DAGs"),
    ("test", "Tests / contracts"),
    ("ge", "Great Expectations suites"),
    ("hook", "Governance hooks"),
    ("agent", "Cabinet agents"),
    ("config", "Config"),
    ("analysis", "Ad-hoc analyses"),
    ("learning", "Learning"),
    ("cheatsheet", "Cheatsheets"),
    ("debate", "Debate record"),
    ("doc", "Top-level docs"),
    ("other", "Other"),
]

REF_RE = re.compile(r"\bref\(\s*['\"]([a-zA-Z0-9_]+)['\"]")


def working_set() -> list[Path]:
    """The repo as it is NOW: tracked + untracked-not-ignored, minus the stated EXCLUDE set."""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    files = []
    for raw in out.splitlines():
        rel = raw.strip()
        if not rel or rel in EXCLUDE or rel.startswith(EXCLUDE_PREFIX):
            continue
        if (REPO / rel).is_file():
            files.append(Path(rel))
    return sorted(files, key=lambda p: p.as_posix())


def role_of(rel: str) -> str:
    if rel.startswith("scripts/"):
        return "script"
    if rel.startswith("tests/"):
        return "test"
    if rel.startswith("dags/"):
        return "dag"
    if rel.startswith("models/staging/"):
        return "dbt:staging"
    if rel.startswith("models/intermediate/"):
        return "dbt:intermediate"
    if rel.startswith("models/marts/core/"):
        return "dbt:mart-core"
    if rel.startswith("models/marts/performance/"):
        return "dbt:mart-perf"
    if rel.startswith("models/"):
        return "dbt:model"
    if rel.startswith("seeds/"):
        return "seed"
    if rel.startswith("architecture/ADR-"):
        return "adr"
    if rel.startswith("architecture/"):
        return "arch-doc"
    if rel.startswith(".claude/hooks/"):
        return "hook"
    if rel.startswith(".claude/agents/"):
        return "agent"
    if rel.startswith("great_expectations/"):
        return "ge"
    if rel.startswith("learning/"):
        return "learning"
    if rel.startswith("cheatsheets/"):
        return "cheatsheet"
    if rel.startswith("debate/"):
        return "debate"
    if rel.startswith("analyses/"):
        return "analysis"
    suf = Path(rel).suffix
    if suf == ".md":
        return "doc"
    if suf in (".yml", ".yaml", ".json"):
        return "config"
    if suf == ".sh":
        return "script"
    return "other"


def _clean(text: str, limit: int = 110) -> str:
    """Plain-text, single-line, table-safe. Strip markdown that could confuse downstream gates
    (backticks/links/pipes) so an extracted heading can't masquerade as a real doc reference."""
    text = text.replace("`", "").replace("|", "/")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # [label](url) -> label
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def purpose_of(path: Path) -> str:
    """Extract the file's own one-line statement of intent — never authored here."""
    suf = path.suffix
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "—"

    if suf == ".py":
        try:
            doc = ast.get_docstring(ast.parse(text))
        except SyntaxError:
            doc = None
        if doc:
            return _clean(doc.strip().splitlines()[0])
        return "(no module docstring)"

    if suf == ".md":
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#"):
                return _clean(s.lstrip("#").strip())
            if s and not s.startswith(("<!--", ">", "---")):
                return _clean(s)
        return "—"

    if suf == ".sql":
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("--"):
                return _clean(s.lstrip("-").strip())
            if s:
                break
        return "(no leading -- comment)"

    if suf in (".yml", ".yaml"):
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#"):
                return _clean(s.lstrip("#").strip())
            if s:
                break
        return "—"

    if suf == ".csv":
        head = text.splitlines()[0] if text.strip() else ""
        return _clean(f"seed · {head}") if head else "—"

    return "—"


def py_deps(path: Path, local_py: dict[str, str]) -> set[str]:
    """Cross-file LOCAL imports only, via AST (so SQL-in-a-string can't pose as an import)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return set()
    deps: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                top = n.name.split(".")[0]
                if top in local_py:
                    deps.add(local_py[top])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                top = node.module.split(".")[0]
                if top in local_py:
                    deps.add(local_py[top])
    return deps


def sql_deps(path: Path, local_sql: dict[str, str]) -> set[str]:
    """dbt ref('model') edges → the referenced model's file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return set()
    deps: set[str] = set()
    for name in REF_RE.findall(text):
        if name in local_sql:
            deps.add(local_sql[name])
    return deps


def build_edges(files: list[Path]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Return (uses, used_by) keyed by rel-path. Edges derived from ground truth, not memory."""
    local_py = {p.stem: p.as_posix() for p in files if p.suffix == ".py"}
    local_sql = {p.stem: p.as_posix() for p in files if p.suffix == ".sql"}
    uses: dict[str, set[str]] = {p.as_posix(): set() for p in files}
    for p in files:
        rel = p.as_posix()
        if p.suffix == ".py":
            uses[rel] |= py_deps(p, local_py)
        elif p.suffix == ".sql":
            uses[rel] |= sql_deps(p, local_sql)
        uses[rel].discard(rel)  # never self-edge
    used_by: dict[str, set[str]] = {p.as_posix(): set() for p in files}
    for rel, targets in uses.items():
        for t in targets:
            used_by.setdefault(t, set()).add(rel)
    return uses, used_by


def _names(rels: set[str]) -> str:
    return ", ".join(sorted(Path(r).name for r in rels)) if rels else "—"


def render(files: list[Path]) -> str:
    uses, used_by = build_edges(files)
    by_role: dict[str, list[Path]] = {}
    for p in files:
        by_role.setdefault(role_of(p.as_posix()), []).append(p)

    lines: list[str] = [
        "# REPO_MAP — generated navigation index",
        "",
        "> **GENERATED — do not hand-edit.** `python scripts/gen_repo_map.py` rebuilds it from",
        "> ground truth; CI runs `--check` and fails if this file is stale. Purpose is extracted",
        "> from each file's own docstring / first heading / leading comment; *Uses* and *Used by*",
        "> are parsed (`ast` for Python, `ref()` for dbt), never authored.",
        ">",
        "> **This is a pointer, not a cache.** It tells you which file to open — then READ THAT",
        "> FILE FRESH before you edit or assert about it (ANTI-SHORTCUT PROTOCOL, CLAUDE.md). A",
        "> pointer trusted without opening the file is just a bigger stale cache.",
        ">",
        "> Not mapped (by design): `.github/`, lockfiles, `*.example`, secret templates, settings.",
        "",
        f"**{len(files)} files mapped.**",
        "",
    ]

    for role, label in ROLE_LABELS:
        group = sorted(by_role.get(role, []), key=lambda p: p.as_posix())
        if not group:
            continue
        lines += [f"## {label}", "", "| File | Purpose | Uses | Used by |", "|------|---------|------|---------|"]
        for p in group:
            rel = p.as_posix()
            lines.append(
                f"| `{rel}` | {purpose_of(p)} | {_names(uses.get(rel, set()))} "
                f"| {_names(used_by.get(rel, set()))} |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    files = working_set()
    content = render(files)

    if "--check" in argv[1:]:
        if not MAP_PATH.exists():
            print("REPO-MAP: architecture/REPO_MAP.md missing — run python scripts/gen_repo_map.py")
            return 1
        current = MAP_PATH.read_text(encoding="utf-8")
        if current != content:
            new = content.splitlines()
            old = current.splitlines()
            for i in range(max(len(new), len(old))):
                a = old[i] if i < len(old) else "<EOF>"
                b = new[i] if i < len(new) else "<EOF>"
                if a != b:
                    print("REPO-MAP: STALE — committed index does not match ground truth.")
                    print(f"  first divergence at line {i + 1}:")
                    print(f"    committed: {a}")
                    print(f"    expected:  {b}")
                    break
            print("\nRegenerate: python scripts/gen_repo_map.py")
            return 1
        print(f"REPO-MAP: OK — {len(files)} files, index matches ground truth.")
        return 0

    MAP_PATH.write_text(content, encoding="utf-8")
    print(f"REPO-MAP: wrote {MAP_PATH.relative_to(REPO)} — {len(files)} files mapped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
