#!/usr/bin/env python3
"""ADR-coupling contract — a STRUCTURAL change to a governed file must ship with an ADR touch.

This closes the one gap the navigation gate (scripts/gen_repo_map.py) can't: that gate proves
the index moved WITH the code, but it can't make anyone record WHY. The project's standing rule
(adr-addendum-parity) is that an ad-hoc change which alters architecture deserves an ADR addendum
or new ADR treated as seriously as a full ADR — not a silent commit. This makes that rule binding
for the cases code can detect without guessing intent.

Deliberately narrow, to avoid the noise trap (if every typo in a model demanded an ADR, people
would game it with empty ADR touches). It fires ONLY on *structural* change to a governed file:
  - a governed file ADDED or DELETED (a new/removed entity, script, DAG — unambiguous), or
  - a governed file MODIFIED such that its dependency EDGES changed: a new/removed local import
    (.py, via `ast`) or a new/removed `ref()` (.sql). A cosmetic edit that touches no edge and
    no file set is NOT flagged.
Governed roots mirror the structural subset of .claude/hooks/governance_guard.py: models/ seeds/
scripts/ dags/. "ADR touched" = any architecture/ADR-*.md added or modified in the same change.

If structural governed change exists and NO ADR was touched → exit 1. Escape hatch (loud, on the
record): ADR_COUPLING_WAIVED=1 when a structural change genuinely isn't an architecture decision.

Base revision: argv[1] > $ADR_COUPLING_BASE > merge-base with origin/main > merge-base with main.
If none resolves (e.g. detached/no-upstream), the gate SKIPS (exit 0) rather than failing CI on a
context it can't reason about. Stdlib + git only ($0).

Run:  python tests/adr_coupling_contract.py [BASE_REF]
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

GOVERNED_ROOTS = ("models/", "seeds/", "scripts/", "dags/")
ADR_RE = re.compile(r"^architecture/ADR-[^/]+\.md$")
REF_RE = re.compile(r"\bref\(\s*['\"]([a-zA-Z0-9_]+)['\"]")


def is_governed(rel: str) -> bool:
    return rel.startswith(GOVERNED_ROOTS)


def is_adr(rel: str) -> bool:
    return bool(ADR_RE.match(rel))


def dep_names(text: str, suffix: str, local_py: set[str]) -> set[str]:
    """The set of dependency edge names in a file — local imports (.py) or ref() targets (.sql).

    Restricted to LOCAL modules for .py so adding `import json` is not mistaken for a structural
    edge change; uses `ast` so SQL embedded in a Python string can't pose as an import."""
    if suffix == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return set()
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    top = n.name.split(".")[0]
                    if top in local_py:
                        names.add(top)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                top = node.module.split(".")[0]
                if top in local_py:
                    names.add(top)
        return names
    if suffix == ".sql":
        return set(REF_RE.findall(text))
    return set()  # other suffixes carry no dependency-edge concept


def evaluate(changes: list[dict], base_text, local_py: set[str]) -> tuple[list[tuple[str, str]], bool]:
    """Pure decision core (no git I/O, so it is unit-testable).

    changes: list of {status: 'A'|'M'|'D'|'R', path: str, head_text: str|None}.
    base_text: callable(path) -> str|None giving the file's content at the base revision.
    Returns (structural changes as [(reason, path)], adr_touched)."""
    structural: list[tuple[str, str]] = []
    adr_touched = False
    for ch in changes:
        code = ch["status"][0]
        rel = ch["path"]
        if is_adr(rel) and code in ("A", "M", "R"):
            adr_touched = True
        if not is_governed(rel):
            continue
        if code == "A":
            structural.append(("added governed file", rel))
        elif code == "D":
            structural.append(("deleted governed file", rel))
        elif code == "R":
            structural.append(("renamed governed file", rel))
        elif code == "M":
            suffix = Path(rel).suffix
            if suffix in (".py", ".sql"):
                before = dep_names(base_text(rel) or "", suffix, local_py)
                after = dep_names(ch.get("head_text") or "", suffix, local_py)
                if before != after:
                    structural.append(("dependency edges changed", rel))
    return structural, adr_touched


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def _read(rel: str) -> str | None:
    try:
        return (REPO / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def resolve_base(argv: list[str]) -> str | None:
    if len(argv) > 1 and argv[1].strip():
        return argv[1].strip()
    env = os.environ.get("ADR_COUPLING_BASE")
    if env:
        return env
    for upstream in ("origin/main", "main"):
        mb = _git("merge-base", "HEAD", upstream)
        if mb.returncode == 0 and mb.stdout.strip():
            return mb.stdout.strip()
    return None


def local_py_stems() -> set[str]:
    out = _git("ls-files", "--cached", "--others", "--exclude-standard").stdout
    return {Path(line).stem for line in out.splitlines() if line.strip().endswith(".py")}


def collect_changes(base: str) -> list[dict]:
    changes: list[dict] = []
    diff = _git("diff", "--name-status", "-M", base).stdout
    for line in diff.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            new = parts[2]
            changes.append({"status": "R", "path": new, "head_text": _read(new)})
        else:
            rel = parts[1]
            code = status[0]
            changes.append({"status": code, "path": rel,
                            "head_text": None if code == "D" else _read(rel)})
    # Untracked-not-ignored files (a dirty local tree) count as Added.
    for line in _git("ls-files", "--others", "--exclude-standard").stdout.splitlines():
        rel = line.strip()
        if rel:
            changes.append({"status": "A", "path": rel, "head_text": _read(rel)})
    return changes


def make_base_text(base: str):
    def _bt(rel: str) -> str | None:
        r = _git("show", f"{base}:{rel}")
        return r.stdout if r.returncode == 0 else None
    return _bt


def main(argv: list[str]) -> int:
    if _git("rev-parse", "--git-dir").returncode != 0:
        print("ADR-COUPLING: not a git repo — skipping.")
        return 0
    if os.environ.get("ADR_COUPLING_WAIVED") == "1":
        print("ADR-COUPLING: WAIVED via ADR_COUPLING_WAIVED=1 (justification belongs in the PR).")
        return 0
    base = resolve_base(argv)
    if not base:
        print("ADR-COUPLING: no base ref (origin/main, main) resolvable — skipping (not a PR context).")
        return 0

    structural, adr_touched = evaluate(collect_changes(base), make_base_text(base), local_py_stems())

    if structural and not adr_touched:
        print(f"ADR-COUPLING: {len(structural)} structural governed change(s) since {base[:12]}, "
              "but NO architecture/ADR-*.md touched.\n")
        for reason, rel in sorted(structural):
            print(f"  ✗ {rel}  ({reason})")
        print("\nA structural change to a governed file (new/removed entity, new dependency edge) is")
        print("an architecture decision — it needs an architecture/ADR-*.md addendum or a new ADR in")
        print("the SAME change (adr-addendum-parity). Add one, or set ADR_COUPLING_WAIVED=1 with a")
        print("justification in the PR if this genuinely is not an architecture change.")
        return 1

    if structural:
        print(f"ADR-COUPLING: OK — {len(structural)} structural change(s) since {base[:12]}, "
              "ADR touched in the same change.")
    else:
        print(f"ADR-COUPLING: OK — no structural governed change since {base[:12]}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
