## T-L01 — Duplicate PK in silver_chunk            ✅ PASSED

- **Scenario**     : kau on-call engineer. Pipeline ran green, no alert, but marketing lead
  flagged ACME's total clip count doubled overnight with no new uploads.
- **Symptom**      : `mart_client_summary.total_chunks` for ACME showed 5, should be 4.
- **Diagnosis**    : grain-uniqueness query on `(client_id, asset_id, chunk_id)` found
  `asset_002/chunk_01` appearing twice with identical score. Checked landing layer for that
  asset — only one source content-hash object existed there.
- **Root cause**   : code-side, not data-side — one source video produced two identical rows
  in `silver_chunk`, since the duplicate's content hash at landing was singular.
- **Fix / Recovery**: deduped via `ROW_NUMBER() OVER (PARTITION BY client_id, asset_id, chunk_id)`,
  kept `rn = 1`, dropped the excess — instead of a naive `DELETE WHERE` (which would have
  matched both identical rows and zeroed out the asset entirely).
- **Evidence**     : gate query (`GROUP BY 1,2,3 HAVING COUNT(*) > 1`) → empty result, 0 rows.
  `mart_client_summary_fixed.total_chunks` for ACME → 4.
- **⚠️ Junior mistake** : simply deleting matching rows — since duplicates share identical
  metadata, the WHERE clause matches both copies and deletes the asset entirely instead of
  fixing it.
- **🎤 Soundbite**  : Identical rows can't be targeted by a WHERE clause — you need to assign
  them identity first (row_number), then delete by identity, not by content.
