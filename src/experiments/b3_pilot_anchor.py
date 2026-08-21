"""Frozen, outcome-blind identity of the audited B3 raw pilot tree.

The operator captured this inventory before any preregistered analysis ran.
It includes the documented root ``AUDIT.md`` report, ``JOB.json``,
``MANIFEST.json``, and six required files in each of 60 cell directories.
"""
from __future__ import annotations

FROZEN_RAW_TREE_SHA256 = (
    "efc5ca31dcddb21166f6a5da2cf60b4961706c99edf9dbda882f87a18a88ace4")
FROZEN_RAW_FILE_COUNT = 363
FROZEN_RAW_DIRECTORY_COUNT = 60
FROZEN_RAW_TOTAL_BYTES = 17385781
# Exact specification identity recorded in the immutable run MANIFEST.json.
# The current document contains an outcome-blind post-run clarification of
# certificate scope, raw anchoring, and boundary diagnostics.
FROZEN_RUN_SPEC_SHA256 = (
    "150f4b32220b13866d2872e4bb8a29bfcc5137cca18ebb55c8ddf3d163d4275f")

FROZEN_RAW_ANCHOR = {
    "tree_sha256": FROZEN_RAW_TREE_SHA256,
    "file_count": FROZEN_RAW_FILE_COUNT,
    "directory_count": FROZEN_RAW_DIRECTORY_COUNT,
    "total_bytes": FROZEN_RAW_TOTAL_BYTES,
}


def snapshot_identity(snapshot: dict, tree_sha256: str) -> dict:
    """Return the four frozen inventory fields from one stable snapshot."""
    return {
        "tree_sha256": tree_sha256,
        "file_count": snapshot["file_count"],
        "directory_count": snapshot["directory_count"],
        "total_bytes": snapshot["total_bytes"],
    }


def anchor_disagreements(actual: dict, expected: dict) -> list[str]:
    """Name every anchor field whose exact value differs."""
    return [
        field for field in FROZEN_RAW_ANCHOR
        if actual.get(field) != expected.get(field)
    ]
