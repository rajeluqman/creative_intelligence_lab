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
    python scripts/sync_docs_to_confluence.py --homepage    # also overwrite the space homepage
                                                            # (CONFLUENCE_PARENT_PAGE_ID) with a
                                                            # hyperlinked landing page — run AFTER a
                                                            # normal sync so the pages it links to
                                                            # already exist and have real page IDs
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


# Homepage link sections, in the order a newcomer should read them. Each entry references a page
# title from PUBLISH_SET above (so the link target always matches a page that's actually published —
# no hand-typed titles to drift out of sync). One short line of "why click this" per link, written
# for a newcomer landing on the space root, not a repo contributor.
HOMEPAGE_SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    ("Start here", [
        ("Start Here", "What this project is, the five hard design problems, and the reading order below."),
    ]),
    ("Architecture", [
        ("Architecture Decisions", "Why DuckDB not Spark, content-hash identity, graph-over-star — the ADRs that matter."),
        ("Pipeline Documentation", "The flow: Drive source → S3 landing → Silver → Gold marts."),
        ("Data Contract", "Schema, types, mandatory fields, lineage/identity rules."),
        ("DATA_DICTIONARY", "What every column in the marts means."),
    ]),
    ("Operate", [
        ("Runbook", "How to rerun the pipeline on failure, with real cited incidents."),
        ("Deployment Guide", "How CI/CD and Snowflake serving actually deploy."),
        ("Known Issues", "Bugs/gaps not yet fixed."),
        ("Incident Postmortem", "Root cause records for production issues."),
    ]),
    ("Releases", [
        ("Release Notes", "What changed, most recent first."),
    ]),
]


def _homepage_html(base_url: str, space_key: str, link_ids: dict[str, str]) -> str:
    """Build the space-homepage body: an elevator pitch + a hyperlinked nav, like a real team wiki
    landing page. `link_ids` maps page title (without the PROJECT_PREFIX) -> live Confluence page id,
    so every link points at a page that actually exists today, not a guessed URL."""
    parts = [
        "<h1>Creative Intelligence Pipeline</h1>",
        "<p><em>From raw ad footage to a searchable creative feature store.</em></p>",
        "<p>Clients hand over a Google Drive folder full of near-duplicate ad video — the same campaign "
        "shot and re-cut a dozen times. This pipeline reads every clip with an LLM and turns it into "
        "structured, searchable data: every line of dialogue, the hook, the theme, the sentiment, and "
        "a 1–5 reuse score per clip (can this moment stand alone, or does it need the rest of the ad "
        "around it?).</p>",
        "<h2>How a video becomes a queryable row</h2>",
        "<ul>"
        "<li><strong>Landing (raw)</strong> — the client's video lands in S3 untouched, identified by a "
        "content hash, not a filename. Upload the same near-duplicate clip twice and it's recognized "
        "as the same asset, not reprocessed.</li>"
        "<li><strong>Bronze</strong> — an LLM (Gemini) watches each video once and its response is "
        "saved word-for-word. Kept verbatim so the data can be re-parsed later without paying to "
        "re-watch the video.</li>"
        "<li><strong>Silver</strong> — that raw response is split into one row per semantic chunk (a "
        "dialogue beat or scene, not a fixed 10-second slice), with filler removed and timestamps "
        "normalized.</li>"
        "<li><strong>Gold (marts)</strong> — the chunks become the actual feature store: fact tables "
        "per chunk, plus a graph of which chunks can coherently follow which — so a chunk doesn't get "
        "stitched next to one that breaks the message.</li>"
        "</ul>",
        "<p><strong>How marketing actually uses it:</strong> nobody touches S3 or parquet directly. "
        "Snowflake reads the Gold tables and serves them through native semantic (vector) search and "
        "Power BI — so \"find me frustrated-customer clips that stand alone\" is a search query or "
        "dashboard filter, not a script someone runs.</p>",
        "<p>This page and the docs below are generated from the project's GitHub repository and "
        "kept in sync automatically. Please make edits there, not here — anything changed directly "
        "on this page will be overwritten by the next sync.</p>",
    ]
    for section, links in HOMEPAGE_SECTIONS:
        parts.append(f"<h2>{section}</h2>")
        parts.append("<ul>")
        for title, blurb in links:
            page_id = link_ids.get(title)
            if page_id is None:
                parts.append(f"<li>{title} — <em>not yet published, run a sync first</em></li>")
                continue
            url = f"{base_url}/spaces/{space_key}/pages/{page_id}"
            parts.append(f'<li><a href="{url}">{title}</a> — {blurb}</li>')
        parts.append("</ul>")
    return "\n".join(parts)


def _update_homepage(base_url: str, auth, parent_id: str, html: str) -> None:
    resp = requests.get(
        f"{base_url}/rest/api/content/{parent_id}",
        params={"expand": "version"},
        auth=auth,
        timeout=30,
    )
    resp.raise_for_status()
    page = resp.json()
    next_version = page["version"]["number"] + 1
    resp = requests.put(
        f"{base_url}/rest/api/content/{parent_id}",
        auth=auth,
        json={
            "type": "page",
            "title": page["title"],
            "version": {"number": next_version},
            "body": {"storage": {"value": html, "representation": "storage"}},
        },
        timeout=30,
    )
    resp.raise_for_status()


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


def _set_space_homepage(base_url: str, auth, space_key: str, page_id: str) -> None:
    """Point the SPACE's homepage pointer at page_id. This is a separate property on the space
    object (`space.homepage`), not part of the page's own content — writing the page body alone
    (as `_update_homepage` does) does not make Confluence treat it as the space's landing page.
    Without this call the space keeps showing "This space doesn't have a homepage"."""
    resp = requests.put(
        f"{base_url}/rest/api/space/{space_key}",
        auth=auth,
        json={"homepage": {"id": page_id}},
        timeout=30,
    )
    resp.raise_for_status()


def _delete_page(base_url: str, auth, page_id: str) -> None:
    resp = requests.delete(f"{base_url}/rest/api/content/{page_id}", auth=auth, timeout=30)
    resp.raise_for_status()


def sync(env: dict[str, str], dry_run: bool, prune: bool, homepage: bool) -> None:
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
        if homepage:
            link_ids = {title: "PLACEHOLDER_ID" for section in HOMEPAGE_SECTIONS for title, _ in section[1]}
            html = _homepage_html("https://example.atlassian.net/wiki", "CI", link_ids)
            print(f"\n[dry-run] would overwrite the space homepage ({len(html)} chars):")
            print(html)
        return

    _assert_env(env)
    base_url = env["CONFLUENCE_BASE_URL"].rstrip("/")
    auth = (env["CONFLUENCE_EMAIL"], env["CONFLUENCE_API_TOKEN"])
    space_key = env["CONFLUENCE_SPACE_KEY"]
    parent_id = env["CONFLUENCE_PARENT_PAGE_ID"]

    page_ids: dict[str, str] = {}
    for path, title in docs:
        html = _to_confluence_storage_html(path.read_text())
        existing = _find_existing_page(base_url, auth, space_key, title)
        if existing:
            next_version = existing["version"]["number"] + 1
            _update_page(base_url, auth, existing["id"], next_version, title, html)
            print(f"updated: {title} (v{next_version})")
            page_ids[title] = existing["id"]
        else:
            page_id = _create_page(base_url, auth, space_key, parent_id, title, html)
            print(f"created: {title} (id={page_id})")
            page_ids[title] = page_id

    if homepage:
        link_ids = {
            stem: page_ids.get(f"{PROJECT_PREFIX} — {stem}")
            for section in HOMEPAGE_SECTIONS for stem, _ in section[1]
        }
        missing = [stem for stem, pid in link_ids.items() if pid is None]
        if missing:
            sys.exit(f"sync_docs_to_confluence: --homepage references unpublished page(s): {missing}")
        html = _homepage_html(base_url, space_key, link_ids)
        _update_homepage(base_url, auth, parent_id, html)
        _set_space_homepage(base_url, auth, space_key, parent_id)
        print(f"updated: homepage ({parent_id}), space homepage pointer set to {parent_id}")

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
    parser.add_argument(
        "--homepage", action="store_true",
        help="also overwrite the space homepage (CONFLUENCE_PARENT_PAGE_ID) with a hyperlinked landing page"
    )
    args = parser.parse_args()
    sync(dict(os.environ), args.dry_run, args.prune, args.homepage)
