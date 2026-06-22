"""Landing TTL guarded delete — hard-delete aged non-golden videos (ADR-007).

Implements the THREE binding conditions from architecture/ADR-007-landing-ttl.md. A bare S3
lifecycle rule is explicitly INSUFFICIENT (it can't do the Bronze check), so this is the
mandated guarded-delete process. For each landing object older than the client's
`landing_ttl_days` (from dim_client):
  1. GOLDEN EXEMPTION — `landing/_golden/...` is never scanned (structural: we only list each
     client's `landing/<client_id>/video/` prefix, which excludes the golden prefix entirely).
  2. BRONZE GUARD — delete only if `bronze/<client_id>/asset_raw/<asset_id>.parquet` exists.
     No Bronze => skip (deleting bytes whose extraction never completed = unrecoverable loss).
  3. NAMED CONSEQUENCE — each delete writes a frozen-asset record to
     `bronze/<client_id>/ttl_delete_log/<asset_id>_<ts>.json` (the asset is now frozen at its
     last extraction: re-parse from Bronze survives, re-extraction is permanently impossible).

⚠️ DESTRUCTIVE on the CANONICAL bucket. DRY-RUN by default — it only reports what it WOULD
delete. Pass --apply (or TTL_APPLY=1) to actually delete. Never wire --apply into a loop that
touches the Gemini boundary (irrelevant here — this only deletes landing video, never calls
the API).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).parent))
from env_guard import assert_safe  # noqa: E402

DIM_CLIENT_PATH = Path(__file__).parent.parent / "seeds" / "dim_client.csv"
GOLDEN_PREFIX = "landing/_golden/"


def _client_ttls() -> dict[str, int]:
    """client_id -> landing_ttl_days, from the dim_client seed (system of record per ADR-006)."""
    if not DIM_CLIENT_PATH.exists():
        return {}
    with DIM_CLIENT_PATH.open(newline="") as f:
        return {r["client_id"]: int(r["landing_ttl_days"]) for r in csv.DictReader(f)}


def _list_client_videos(s3, bucket: str, client_id: str):
    """Yield (key, last_modified) under landing/<client_id>/video/ — paginated. The golden
    prefix landing/_golden/ is structurally excluded (we never list it)."""
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=f"landing/{client_id}/video/"):
        for obj in page.get("Contents", []):
            yield obj["Key"], obj["LastModified"]


def _asset_id_from_key(key: str) -> str:
    return Path(key).stem  # landing/<client>/video/<asset_id>.<ext> -> <asset_id>


def _bronze_exists(s3, bucket: str, client_id: str, asset_id: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=f"bronze/{client_id}/asset_raw/{asset_id}.parquet")
        return True
    except s3.exceptions.ClientError:
        return False


def _write_frozen_log(s3, bucket: str, client_id: str, asset_id: str, landing_key: str, age_days: int) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    body = json.dumps({
        "event": "landing_ttl_delete",
        "asset_id": asset_id, "client_id": client_id, "deleted_key": landing_key,
        "age_days": age_days, "deleted_at": ts,
        "consequence": "FROZEN — re-extraction permanently impossible; re-parse from Bronze survives (ADR-007)",
    }).encode()
    s3.put_object(Bucket=bucket, Key=f"bronze/{client_id}/ttl_delete_log/{asset_id}_{ts}.json", Body=body)


def enforce_ttl(apply: bool = False, bucket: str | None = None) -> dict:
    """Returns a summary dict. apply=False (default) = dry-run (reports, deletes nothing)."""
    assert_safe()
    bucket = bucket or os.environ["S3_BUCKET"]
    s3 = boto3.client("s3")
    now = datetime.now(timezone.utc)
    summary = {"deleted": 0, "skipped_no_bronze": 0, "within_ttl": 0, "dry_run": not apply}

    for client_id, ttl_days in _client_ttls().items():
        for key, last_modified in _list_client_videos(s3, bucket, client_id):
            age_days = (now - last_modified).days
            if age_days < ttl_days:
                summary["within_ttl"] += 1
                continue
            asset_id = _asset_id_from_key(key)
            if not _bronze_exists(s3, bucket, client_id, asset_id):
                summary["skipped_no_bronze"] += 1                 # Condition 2 — no Bronze, no delete
                print(f"SKIP (no Bronze): {key} (age {age_days}d)")
                continue
            if apply:
                s3.delete_object(Bucket=bucket, Key=key)
                _write_frozen_log(s3, bucket, client_id, asset_id, key, age_days)
                print(f"DELETED (frozen): {key} (age {age_days}d)")
            else:
                print(f"WOULD DELETE: {key} (age {age_days}d, Bronze present)")
            summary["deleted"] += 1

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Landing TTL guarded delete (ADR-007).")
    parser.add_argument("--apply", action="store_true", help="actually delete (default: dry-run)")
    args = parser.parse_args()
    apply = args.apply or os.environ.get("TTL_APPLY") == "1"
    result = enforce_ttl(apply=apply)
    print(json.dumps(result))
