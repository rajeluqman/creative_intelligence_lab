"""Drive -> S3 landing. Content-hash (SHA-256) naming, skip-existing (idempotent).

Path A of the pipeline (architecture/STACK_AND_FLOW.md §2). Pulls every video file out of
a client's Google Drive folder, identifies it by the SHA-256 of its bytes (never a random
key — DATA_MODEL.md §4, the near-duplicate answer), and lands it write-once in S3. A
re-delivered or near-duplicate video hashes to the same asset_id and is never re-uploaded —
the first cost firewall (architecture/DRD.md §5.1).

Auth: a Google service account, with the client's Drive folder shared to its client_email.
Set GOOGLE_APPLICATION_CREDENTIALS to the service-account JSON path (see .env.example).

⚠️ Path inconsistency (flag, not silently resolved): dags/creative_intel_pipeline.py's
`client_id` Param says "client partition under landing/" (landing/<client_id>/video/...),
but architecture/STACK_AND_FLOW.md §2 and DATA_MODEL.md §3 both state `landing/video/...`
with no client partition. This script follows the DAG's contract (client_id-partitioned)
since that's the more specific, recently-written spec, but defaults to the no-partition form
when client_id is blank. Route to @data-architect to reconcile the docs either way.

⚠️ Open architectural item (NOT resolved here — see architecture/STTM.md "Exceptions"):
there is no ratified mechanism for detecting asset_type (RAW vs EDITED) or populating
parent_asset_id from Drive alone. This script uses a pragmatic v1 convention (folder-name
sniff for asset_type; parent_asset_id always left blank) — see _infer_asset_type() below.
Do not treat this convention as settled; it is a placeholder pending a real ruling.
"""
from __future__ import annotations

import csv
import hashlib
import io
import os
import sys
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
MANIFEST_COLUMNS = ["asset_id", "asset_name", "asset_type", "parent_asset_id", "duration_sec", "source_uri"]


def _drive_client():
    creds_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=DRIVE_SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _list_videos(drive, folder_id: str) -> list[dict]:
    """Non-recursive listing of video files directly under folder_id. Paginated."""
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


def _infer_asset_type(drive, file_meta: dict) -> str:
    """Pragmatic v1 convention — NOT a ratified rule (see module docstring).

    A file is EDITED if its immediate parent Drive folder name contains "edited" or
    "winners" (case-insensitive); otherwise RAW. parent_asset_id is never inferred here.
    """
    parent_ids = file_meta.get("parents") or []
    for parent_id in parent_ids:
        try:
            parent = drive.files().get(fileId=parent_id, fields="name").execute()
        except Exception:
            continue
        name = parent.get("name", "").lower()
        if "edited" in name or "winners" in name:
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
    with MANIFEST_PATH.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS)
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

    drive = _drive_client()
    s3 = boto3.client("s3")
    known_ids = _existing_manifest_ids()
    landed = 0

    for file_meta in tqdm(_list_videos(drive, folder_id), desc="Drive -> S3 landing"):
        raw_bytes = _download_bytes(drive, file_meta["id"])
        asset_id = hashlib.sha256(raw_bytes).hexdigest()
        ext = _extension(file_meta["name"])
        key = _s3_key(asset_id, ext, client_id)
        source_uri = f"s3://{bucket}/{key}"

        if not _s3_exists(s3, bucket, key):
            s3.put_object(Bucket=bucket, Key=key, Body=raw_bytes)

        if asset_id not in known_ids:
            duration_ms = (file_meta.get("videoMediaMetadata") or {}).get("durationMillis")
            _append_manifest_row(
                {
                    "asset_id": asset_id,
                    "asset_name": file_meta["name"],
                    "asset_type": _infer_asset_type(drive, file_meta),
                    "parent_asset_id": "",  # never inferred — see module docstring
                    "duration_sec": int(duration_ms) // 1000 if duration_ms else "",
                    "source_uri": source_uri,
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
