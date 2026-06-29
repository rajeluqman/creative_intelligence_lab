"""Publish the curated onboarding doc set to Confluence as living documentation.

ADR-009 (architecture/ADR-009-slack-alerts-and-confluence-doc-sync.md) + its 2026-06-27 addendum
(onboarding IA: a curated, ordered set built for a newcomer, NOT a 1:1 mirror of architecture/*.md).
Confluence Cloud REST API only (Basic Auth: email + API token). Markdown -> HTML via the `markdown`
package; posted as Confluence "storage"-representation content. An existing page is found by title
and updated (version-incremented), never duplicated.

The published set is the explicit `PUBLISH_SET` below (reading order), fronted by two curated hub
pages in `confluence/`. Deliberately EXCLUDED from Confluence: the 12 individual ADR pages (replaced
by the consolidated "Architecture Decisions" page), `REPO_MAP.md` (dev navigation, not onboarding),
and `debate/` (historical). Those stay in the repo as source of truth.

Manual run only today — NOT wired into CI or the Airflow DAG (ADR-009 "Rejected alternatives" #4).

Usage:
    python scripts/sync_docs_to_confluence.py             # real run, needs the 5 env vars
    python scripts/sync_docs_to_confluence.py --dry-run    # render + list, no API calls, no creds
    python scripts/sync_docs_to_confluence.py --prune       # also DELETE live pages no longer in the
                                                            # curated set (e.g. old per-ADR pages)
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

# Curated onboarding set, in reading order. (repo-relative path, explicit page-name or None).
# None -> the page name is the file stem (keeps idempotency with already-created pages).
# The two confluence/ hub pages get friendly names; everything else keeps its stem so a re-run
# updates the existing page instead of creating a duplicate.
PUBLISH_SET: list[tuple[str, str | None]] = [
    ("confluence/00_START_HERE.md", "Start Here"),
    # 1. Pipeline Documentation
    ("confluence/02_PIPELINE_DOCUMENTATION.md", "Pipeline Documentation"),
    ("architecture/STACK_AND_FLOW.md", None),
    ("architecture/DBT_DAG.md", None),
    ("architecture/BRD.md", None),
    ("architecture/DRD.md", None),
    ("architecture/SPEC_v1_search.md", None),
    ("architecture/SPEC_v1.5_performance_marts.md", None),
    # 2. Data Contract
    ("confluence/03_DATA_CONTRACT.md", "Data Contract"),
    ("architecture/STTM.md", None),
    ("architecture/LINEAGE_CONTRACT.md", None),
    ("architecture/BOUNDARY_CONTRACT.md", None),
    ("architecture/ERD_consolidated.md", None),
    ("architecture/DATA_MODEL.md", None),
    ("architecture/DATA_MODEL_v1.5_PERFORMANCE.md", None),
    ("architecture/DQD.md", None),
    # 3. ADR (title kept stable — already live; renaming would orphan the existing page)
    ("confluence/01_ARCHITECTURE_DECISIONS.md", "Architecture Decisions"),
    # 4. Data Dictionary (title kept stable — already live as "DATA_DICTIONARY")
    ("architecture/DATA_DICTIONARY.md", None),
    # 5. Runbook
    ("confluence/04_RUNBOOK.md", "Runbook"),
    # 6. Release Notes
    ("confluence/05_RELEASE_NOTES.md", "Release Notes"),
    # 7. Known Issues
    ("confluence/06_KNOWN_ISSUES.md", "Known Issues"),
    # 8. Incident Postmortem
    ("confluence/07_INCIDENT_POSTMORTEM.md", "Incident Postmortem"),
    # 9. Deployment Guide (added 2026-06-27 — real CI/CD + Snowflake provisioning mechanics
    # now exist and weren't covered by the original 8-page set)
    ("confluence/08_DEPLOYMENT_GUIDE.md", "Deployment Guide"),
    # Detailed build log behind Release Notes
    ("PROJECT_STATUS.md", None),
]


def _page_title(rel_path: str, name: str | None) -> str:
    stem = name if name is not None else Path(rel_path).stem
    return f"{PROJECT_PREFIX} — {stem}"


def _published() -> list[tuple[Path, str]]:
    """(absolute path, page title) for every doc in the curated set that exists on disk."""
    out: list[tuple[Path, str]] = []
    for rel, name in PUBLISH_SET:
        p = REPO_DIR / rel
        if not p.exists():
            sys.exit(f"sync_docs_to_confluence: curated doc missing on disk: {rel}")
        out.append((p, _page_title(rel, name)))
    return out


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


# Our doc pages are ALL titled "Creative Intelligence — <stem>". The bare space homepage is titled
# just "Creative Intelligence" (no separator), so the separator is what distinguishes a prunable doc
# page from the homepage/parent — match on the full prefix-with-separator, never the bare prefix.
TITLE_PREFIX = f"{PROJECT_PREFIX} — "


def _list_project_pages(base_url: str, auth, space_key: str) -> list[dict]:
    """Every page in the space that is one of OUR doc pages (prefix + ' — '), paged.

    Deliberately requires the ' — ' separator so the bare-titled space homepage/parent
    ('Creative Intelligence') can never be selected for prune."""
    pages: list[dict] = []
    start = 0
    while True:
        resp = requests.get(
            f"{base_url}/rest/api/content",
            params={"spaceKey": space_key, "type": "page", "limit": 100, "start": start},
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        pages += [p for p in results if p.get("title", "").startswith(TITLE_PREFIX)]
        if len(results) < 100:
            return pages
        start += 100


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


def _delete_page(base_url: str, auth, page_id: str) -> None:
    resp = requests.delete(f"{base_url}/rest/api/content/{page_id}", auth=auth, timeout=30)
    resp.raise_for_status()


def sync(env: dict[str, str], dry_run: bool, prune: bool) -> None:
    docs = _published()
    keep_titles = {title for _, title in docs}

    if dry_run:
        print(f"[dry-run] would publish {len(docs)} curated doc(s) — no API calls made:")
        for path, title in docs:
            html = _to_confluence_storage_html(path.read_text())
            print(f"  + {title}  ({len(html)} chars, from {path.relative_to(REPO_DIR)})")
        # Local preview only: titles the OLD glob behaviour would have published but the curated
        # set drops. This is NOT the live state (no API call here) — the real --prune diffs against
        # the actual space and deletes only pages that genuinely exist there.
        old_titles = {f"{PROJECT_PREFIX} — {p.stem}"
                      for p in [REPO_DIR / "PROJECT_STATUS.md", *sorted((REPO_DIR / "architecture").glob("*.md"))]}
        dropped = sorted(old_titles - keep_titles)
        print(f"\n[dry-run] {len(dropped)} page(s) in the old glob set but NOT the curated set "
              f"(run with --prune to delete whichever of these are actually live in Confluence):")
        for t in dropped:
            print(f"  - {t}")
        return

    _assert_env(env)
    base_url = env["CONFLUENCE_BASE_URL"].rstrip("/")
    auth = (env["CONFLUENCE_EMAIL"], env["CONFLUENCE_API_TOKEN"])
    space_key = env["CONFLUENCE_SPACE_KEY"]
    parent_id = env["CONFLUENCE_PARENT_PAGE_ID"]

    for path, title in docs:
        html = _to_confluence_storage_html(path.read_text())
        existing = _find_existing_page(base_url, auth, space_key, title)
        if existing:
            next_version = existing["version"]["number"] + 1
            _update_page(base_url, auth, existing["id"], next_version, title, html)
            print(f"updated: {title} (v{next_version})")
        else:
            page_id = _create_page(base_url, auth, space_key, parent_id, title, html)
            print(f"created: {title} (id={page_id})")

    if prune:
        live = _list_project_pages(base_url, auth, space_key)
        # Never delete the configured parent/homepage, even if a title somehow matched.
        orphans = [p for p in live if p["title"] not in keep_titles and p["id"] != parent_id]
        print(f"\n--prune: {len(orphans)} live page(s) not in the curated set — deleting:")
        for p in orphans:
            _delete_page(base_url, auth, p["id"])
            print(f"  deleted: {p['title']} (id={p['id']})")


if __name__ == "__main__":
    import os

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="render + list pages, no API calls, no credentials required"
    )
    parser.add_argument(
        "--prune", action="store_true", help="DELETE live pages (PROJECT_PREFIX) no longer in the curated set"
    )
    args = parser.parse_args()
    sync(dict(os.environ), args.dry_run, args.prune)
