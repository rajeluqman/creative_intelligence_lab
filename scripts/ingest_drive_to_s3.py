"""Drive -> S3 landing. Content-hash (SHA-256) naming, skip-existing (idempotent)."""
# TODO: Google Drive API pull -> hashlib.sha256(bytes) -> s3://$S3_BUCKET/landing/video/<hash>.<ext>
# Skip if the hash already exists (cost firewall). See STACK_AND_FLOW.md §2 Path A.
