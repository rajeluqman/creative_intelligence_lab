"""List asset_ids landed for a client that do NOT yet have a Bronze extraction.

Fills the TODO named in dags/creative_intel_pipeline.py's `list_new_assets` task ("query
bronze_asset_raw by content hash (per client_id)"). Read-only — compares the landing manifest
seed against real S3 Bronze keys, never writes anything. Cost firewall #2 (never re-call
Gemini on an already-extracted asset) depends on this comparison being correct.

Usage:
    python scripts/list_unextracted_assets.py <client_id>   # prints one asset_id per line
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).parent))
from env_guard import assert_safe  # noqa: E402

MANIFEST_PATH = Path(__file__).parent.parent / "seeds" / "asset_manifest.csv"


def list_unextracted(client_id: str) -> list[str]:
    if not client_id:
        raise ValueError("client_id is required")

    with MANIFEST_PATH.open() as f:
        landed_ids = {row["asset_id"] for row in csv.DictReader(f) if row["client_id"] == client_id}

    bucket = os.environ["S3_BUCKET"]
    prefix = f"bronze/{client_id}/asset_raw/"
    s3 = boto3.client("s3")
    extracted_ids: set[str] = set()
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            stem = Path(obj["Key"]).stem  # "<asset_id>.parquet" -> "<asset_id>"
            extracted_ids.add(stem)

    return sorted(landed_ids - extracted_ids)


if __name__ == "__main__":
    assert_safe()
    if len(sys.argv) != 2:
        sys.exit("usage: list_unextracted_assets.py <client_id>")
    for asset_id in list_unextracted(sys.argv[1]):
        print(asset_id)
