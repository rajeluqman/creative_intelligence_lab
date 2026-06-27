"""Drive -> S3 landing. Tenant-scoped content-hash naming, skip-existing (idempotent).

Path A of the pipeline (architecture/STACK_AND_FLOW.md §2). Pulls every video file out of
a client's Google Drive folder and lands it write-once in S3, identified by a **tenant-scoped**
content hash: `asset_id = SHA-256(client_id ':' content_sha256)` where `content_sha256` is the
raw SHA-256 of the video bytes (ADR-006). A re-delivered/near-duplicate video FROM THE SAME
CLIENT hashes to the same asset_id and is never re-uploaded — the first cost firewall
(architecture/DRD.md §5.1). Two DIFFERENT clients delivering byte-identical footage now get
DIFFERENT asset_ids (no cross-tenant collision — ADR-006).

Auth: a Google service account, with the client's Drive folder shared to its client_email.
Set GOOGLE_APPLICATION_CREDENTIALS to the service-account JSON path (see .env.example).

Path convention (RESOLVED by ADR-006, was a flagged inconsistency): landing is
**client-partitioned** — `landing/<client_id>/video/<asset_id>.<ext>` (and Bronze likewise,
`bronze/<client_id>/asset_raw/<asset_id>.parquet`). `client_id` is REQUIRED for tenant runs;
the no-partition fallback in `_s3_key` is retained only for non-tenant/dev smoke use.

Drive folder convention (client onboarding): the client organizes their source folder into
category subfolders — e.g. `raw_video/`, `edited_video/`, `winning_video/`. _list_videos()
walks the whole tree recursively, and _infer_asset_type() classifies by the immediate parent
folder name. "winning" collapses into EDITED, NOT a third asset_type — a winning ad is
physically a finished/edited cut; "which one won" is a performance signal, a different domain
with no ratified v1 home (@data-architect ruling 2026-06-22; Clean-ERD axis-2; CLAUDE.md keeps
ad-performance OUT of v1). The asset_type *enum* (RAW|EDITED) is thus settled.

⚠️ Still open (NOT resolved here — see architecture/STTM.md "Exceptions"): populating
parent_asset_id (RAW→EDITED discovery lineage) from Drive alone has no ratified mechanism —
it is always left blank here. The folder-name sniff for asset_type is a pragmatic v1
convention, not a ratified detection mechanism; only the enum it maps onto is settled.
"""
from __future__ import annotations

import csv
import hashlib
import io
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import boto3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from env_guard import assert_safe  # noqa: E402

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
MANIFEST_PATH = Path(__file__).parent.parent / "seeds" / "asset_manifest.csv"
MANIFEST_COLUMNS = ["asset_id", "client_id", "content_sha256", "asset_name", "asset_type",
                    "parent_asset_id", "duration_sec", "source_uri", "ingested_at"]


def _drive_client():
    creds_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=DRIVE_SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _list_subfolders(drive, folder_id: str) -> list[dict]:
    """Immediate child folders of folder_id. Paginated."""
    folders, page_token = [], None
    while True:
        resp = (
            drive.files()
            .list(
                q=f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
                pageSize=100,
            )
            .execute()
        )
        folders.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            return folders


def _list_videos_in_folder(drive, folder_id: str) -> list[dict]:
    """Video files directly under folder_id (this folder only). Paginated."""
    files, page_token = [], None
    while True:
        resp = (
            drive.files()
            .list(
                q=f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false",
                fields="nextPageToken, files(id, name, mimeType, videoMediaMetadata, parents)",
                pageToken=page_token,
                pageSize=100,
            )
            .execute()
        )
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            return files


def _list_videos(drive, folder_id: str) -> list[dict]:
    """Video files under folder_id, recursing into subfolders — e.g. the client
    onboarding convention of edited_video/winning_video/raw_video category
    subfolders (see _infer_asset_type, which classifies by immediate parent
    folder name). Drive folders can nest arbitrarily; this walks the whole tree."""
    videos = list(_list_videos_in_folder(drive, folder_id))
    for sub in _list_subfolders(drive, folder_id):
        videos.extend(_list_videos(drive, sub["id"]))
    return videos


def _infer_asset_type(drive, file_meta: dict) -> str:
    """Pragmatic v1 convention — NOT a ratified rule (see module docstring).

    A file is EDITED if its immediate parent Drive folder name contains "edited",
    "winning", or "winners" (case-insensitive); otherwise RAW. parent_asset_id is
    never inferred here. "Winning" folders collapse into EDITED, not a third type —
    a winning ad IS, physically, a finished/edited cut; "which one won" is a
    performance signal, a different domain from production-status, and v1 has no
    ratified home for performance data (@data-architect ruling, 2026-06-22 —
    Clean-ERD axis-2 domain purity; CLAUDE.md keeps ad-performance ingestion OUT of v1).
    """
    parent_ids = file_meta.get("parents") or []
    for parent_id in parent_ids:
        try:
            parent = drive.files().get(fileId=parent_id, fields="name").execute()
        except Exception:
            continue
        name = parent.get("name", "").lower()
        if "edited" in name or "winning" in name or "winners" in name:
            return "EDITED"
    return "RAW"


def _download_bytes(drive, file_id: str) -> bytes:
    """Stream into memory — no temp files on disk (mirrors the project's own in-memory
    ingestion pattern; consistent with the KB-MB scale this pipeline runs at)."""
    request = drive.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()


def _extension(name: str) -> str:
    suffix = Path(name).suffix
    return suffix if suffix else ".mp4"  # fallback; Drive video uploads are near-always .mp4/.mov


def _s3_key(asset_id: str, ext: str, client_id: str) -> str:
    if client_id:
        return f"landing/{client_id}/video/{asset_id}{ext}"
    return f"landing/video/{asset_id}{ext}"  # matches STACK_AND_FLOW.md / DATA_MODEL.md when no client_id


def _s3_exists(s3, bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except s3.exceptions.ClientError:
        return False


def _existing_manifest_ids() -> set[str]:
    if not MANIFEST_PATH.exists():
        return set()
    with MANIFEST_PATH.open(newline="") as f:
        return {row["asset_id"] for row in csv.DictReader(f)}


def _append_manifest_row(row: dict) -> None:
    is_new_file = not MANIFEST_PATH.exists()
    # lineterminator="\n": csv.writer defaults to "\r\n" (RFC 4180), which mismatches an
    # LF-only header (e.g. hand-edited or written by a plain text editor) and breaks DuckDB's
    # CSV dialect sniffer on mixed line endings ("could not detect parsing dialect").
    with MANIFEST_PATH.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
        if is_new_file:
            writer.writeheader()
        writer.writerow(row)


def sync_drive_to_landing(folder_id: str, client_id: str = "", s3_bucket: str | None = None) -> int:
    """Returns the count of NEW videos landed this run (matches
    dags/creative_intel_pipeline.py's sync_drive_to_landing task contract).

    Re-delivered/near-duplicate videos hash to an asset_id already in S3 or the manifest
    and are skipped — never re-uploaded, never re-appended.
    """
    assert_safe()
    bucket = s3_bucket or os.environ["S3_BUCKET"]
    if not folder_id:
        return 0  # "blank = re-scan existing" (DAG Param) — nothing to pull from Drive
    if not client_id:
        raise ValueError(
            "client_id is required (ADR-006 tenant-scoped identity). Set CLIENT_ID and ensure a "
            "matching row exists in seeds/dim_client.csv — dim_asset.client_id has a relationships "
            "test against dim_client."
        )

    drive = _drive_client()
    s3 = boto3.client("s3")
    known_ids = _existing_manifest_ids()
    landed = 0
    ingested_at = datetime.now(timezone.utc).isoformat()  # one run = one ingestion event (@data-architect ruling)

    for file_meta in tqdm(_list_videos(drive, folder_id), desc="Drive -> S3 landing"):
        raw_bytes = _download_bytes(drive, file_meta["id"])
        content_sha256 = hashlib.sha256(raw_bytes).hexdigest()                      # raw byte hash
        asset_id = hashlib.sha256(f"{client_id}:{content_sha256}".encode()).hexdigest()  # tenant-scoped (ADR-006)
        ext = _extension(file_meta["name"])
        key = _s3_key(asset_id, ext, client_id)
        source_uri = f"s3://{bucket}/{key}"

        if not _s3_exists(s3, bucket, key):
            s3.put_object(Bucket=bucket, Key=key, Body=raw_bytes)

        # Skip-existing is client-scoped transitively: asset_id folds in client_id, so the
        # same bytes from a different client produce a different asset_id and don't collide.
        if asset_id not in known_ids:
            duration_ms = (file_meta.get("videoMediaMetadata") or {}).get("durationMillis")
            _append_manifest_row(
                {
                    "asset_id": asset_id,
                    "client_id": client_id,
                    "content_sha256": content_sha256,
                    "asset_name": file_meta["name"],
                    "asset_type": _infer_asset_type(drive, file_meta),
                    "parent_asset_id": "",  # never inferred — see module docstring
                    "duration_sec": int(duration_ms) // 1000 if duration_ms else "",
                    "source_uri": source_uri,
                    "ingested_at": ingested_at,
                }
            )
            known_ids.add(asset_id)
            landed += 1

    return landed


if __name__ == "__main__":
    n = sync_drive_to_landing(
        folder_id=os.environ.get("DRIVE_FOLDER_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
    )
    print(f"landed {n} new asset(s)")
