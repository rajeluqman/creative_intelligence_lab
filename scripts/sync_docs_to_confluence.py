"""Publish PROJECT_STATUS.md + architecture/*.md to Confluence as living documentation.

ADR-009 (architecture/ADR-009-slack-alerts-and-confluence-doc-sync.md). Confluence Cloud REST
API only (Basic Auth: email + API token) — Server/Data Center's PAT-bearer auth is a named-out
variant, not built (see ADR). Markdown -> HTML via the `markdown` package; posted as Confluence
"storage"-representation content. An existing page is found by title and updated
(version-incremented), never duplicated.

Manual run only today — NOT wired into CI or the Airflow DAG yet (ADR-009 "Rejected
alternatives" #4: an unverified integration should not be on an automated trigger until it has
run successfully at least once with real credentials).

Usage:
    python scripts/sync_docs_to_confluence.py             # real run, needs all 5 env vars below
    python scripts/sync_docs_to_confluence.py --dry-run    # render + list pages, no API calls,
                                                            # no credentials required
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import markdown
import requests

REPO_DIR = Path(__file__).resolve().parent.parent
PROJECT_PREFIX = "Creative Intelligence"

REQUIRED_ENV = [
    "CONFLUENCE_BASE_URL",  # e.g. https://yourcompany.atlassian.net/wiki
    "CONFLUENCE_EMAIL",
    "CONFLUENCE_API_TOKEN",
    "CONFLUENCE_SPACE_KEY",
    "CONFLUENCE_PARENT_PAGE_ID",
]


def _tracked_docs() -> list[Path]:
    """PROJECT_STATUS.md + every architecture/*.md, sorted — the same set a human reads to
    understand the project (ADR-009 §C). `debate/` is excluded on purpose (CLAUDE.md: historical,
    not a build target)."""
    docs = [REPO_DIR / "PROJECT_STATUS.md"]
    docs += sorted((REPO_DIR / "architecture").glob("*.md"))
    return [d for d in docs if d.exists()]


def _page_title(doc_path: Path) -> str:
    return f"{PROJECT_PREFIX} — {doc_path.stem}"


def _to_confluence_storage_html(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["tables", "fenced_code"])


def _assert_env(env: dict[str, str]) -> None:
    missing = [k for k in REQUIRED_ENV if not env.get(k)]
    if missing:
        sys.exit(
            f"sync_docs_to_confluence: missing required env var(s): {', '.join(missing)} — "
            "refusing to run. Use --dry-run to preview without credentials."
        )


def _find_existing_page(base_url: str, auth, space_key: str, title: str) -> dict | None:
    resp = requests.get(
        f"{base_url}/rest/api/content",
        params={"title": title, "spaceKey": space_key, "expand": "version"},
        auth=auth,
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def _create_page(base_url: str, auth, space_key: str, parent_id: str, title: str, html: str) -> str:
    resp = requests.post(
        f"{base_url}/rest/api/content",
        auth=auth,
        json={
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "ancestors": [{"id": parent_id}],
            "body": {"storage": {"value": html, "representation": "storage"}},
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _update_page(base_url: str, auth, page_id: str, next_version: int, title: str, html: str) -> None:
    resp = requests.put(
        f"{base_url}/rest/api/content/{page_id}",
        auth=auth,
        json={
            "type": "page",
            "title": title,
            "version": {"number": next_version},
            "body": {"storage": {"value": html, "representation": "storage"}},
        },
        timeout=30,
    )
    resp.raise_for_status()


def sync(env: dict[str, str], dry_run: bool) -> None:
    docs = _tracked_docs()

    if dry_run:
        print(f"[dry-run] would sync {len(docs)} doc(s) to Confluence — no API calls made:")
        for doc in docs:
            html = _to_confluence_storage_html(doc.read_text())
            print(f"  - {_page_title(doc)}  ({len(html)} chars of rendered HTML, from {doc.relative_to(REPO_DIR)})")
        return

    _assert_env(env)
    base_url = env["CONFLUENCE_BASE_URL"].rstrip("/")
    auth = (env["CONFLUENCE_EMAIL"], env["CONFLUENCE_API_TOKEN"])
    space_key = env["CONFLUENCE_SPACE_KEY"]
    parent_id = env["CONFLUENCE_PARENT_PAGE_ID"]

    for doc in docs:
        title = _page_title(doc)
        html = _to_confluence_storage_html(doc.read_text())
        existing = _find_existing_page(base_url, auth, space_key, title)
        if existing:
            next_version = existing["version"]["number"] + 1
            _update_page(base_url, auth, existing["id"], next_version, title, html)
            print(f"updated: {title} (v{next_version})")
        else:
            page_id = _create_page(base_url, auth, space_key, parent_id, title, html)
            print(f"created: {title} (id={page_id})")


if __name__ == "__main__":
    import os

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="render + list pages, no API calls, no credentials required"
    )
    args = parser.parse_args()
    sync(dict(os.environ), args.dry_run)
