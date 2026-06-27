"""Golden-dataset fixture: one frozen Gemini-shaped Bronze response + its hand-verified answer key.

The INPUT (RAW_CHUNKS / RAW_RESPONSE) and the EXPECTED OUTPUT (EXPECTED_FACT_CHUNK) are kept as
two independently-authored tables on purpose — a golden test that derives "expected" from the
same code path as the input is just restating the input, not verifying anything (CLAUDE.md
ANTI-SHORTCUT PROTOCOL rule 3: evidence, not self-agreement).

asset_id follows the real ADR-006 formula (sha256(f"{client_id}:{content_sha256}")) purely for
fidelity to the real lineage shape — this fixture never touches seeds/ or the lineage contract.
"""

from __future__ import annotations

import hashlib
import json

CLIENT_ID = "golden_test_client"
CONTENT_SHA256 = hashlib.sha256(b"golden_test_fixture_v1_content").hexdigest()
ASSET_ID = hashlib.sha256(f"{CLIENT_ID}:{CONTENT_SHA256}".encode()).hexdigest()
MODEL_VERSION = "gemini-2.5-flash"
PROMPT_VERSION = "v1"
LOAD_TS = "2026-06-25T00:00:00+00:00"

# Three chunks, deliberately distinct values per field so a swapped column/row is detectable.
RAW_CHUNKS = [
    {
        "start_sec": 0.0, "end_sec": 4.5,
        "transcript_segment": "Korang penat tukar minyak hari-hari?",
        "chunk_theme": "Hook", "sentiment": "energetic", "standalone_score": 2,
        "next_compatible_themes": ["Problem"], "keywords": ["minyak", "penat"],
    },
    {
        "start_sec": 4.5, "end_sec": 10.0,
        "transcript_segment": "Enjin haba lepas drive lama, kereta jadi tak power.",
        "chunk_theme": "Problem", "sentiment": "frustrated", "standalone_score": 1,
        "next_compatible_themes": ["Solution"], "keywords": ["enjin", "haba"],
    },
    {
        "start_sec": 10.0, "end_sec": 16.25,
        "transcript_segment": "Beli sekarang, dapat diskaun 20 peratus!",
        "chunk_theme": "CTA", "sentiment": "urgent", "standalone_score": 5,
        "next_compatible_themes": [], "keywords": ["beli", "diskaun"],
    },
]

RAW_RESPONSE = json.dumps({"chunks": RAW_CHUNKS})

# Hand-authored answer key — what fact_chunk MUST contain after stg_gemini_raw's unnest +
# int_chunk_cleaned + fact_chunk run on the fixture above. chunk_sequence is 1-indexed
# (unnest ... WITH ORDINALITY); chunk_id = f"{asset_id}_{chunk_sequence:03d}" per stg_gemini_raw.sql.
EXPECTED_FACT_CHUNK = [
    {
        "chunk_id": f"{ASSET_ID}_001", "asset_id": ASSET_ID, "chunk_sequence": 1,
        "start_sec": 0.0, "end_sec": 4.5,
        "transcript_segment": "Korang penat tukar minyak hari-hari?",
        "chunk_theme": "Hook", "sentiment": "energetic", "standalone_score": 2,
    },
    {
        "chunk_id": f"{ASSET_ID}_002", "asset_id": ASSET_ID, "chunk_sequence": 2,
        "start_sec": 4.5, "end_sec": 10.0,
        "transcript_segment": "Enjin haba lepas drive lama, kereta jadi tak power.",
        "chunk_theme": "Problem", "sentiment": "frustrated", "standalone_score": 1,
    },
    {
        "chunk_id": f"{ASSET_ID}_003", "asset_id": ASSET_ID, "chunk_sequence": 3,
        "start_sec": 10.0, "end_sec": 16.25,
        "transcript_segment": "Beli sekarang, dapat diskaun 20 peratus!",
        "chunk_theme": "CTA", "sentiment": "urgent", "standalone_score": 5,
    },
]
