"""Strict evidence I/O for the B3 replication comparator.

The analyzer replays recorded certificates rather than re-solving them.
A replication check is only meaningful if it cannot silently accept
ambiguous JSON or a file that was swapped under the reader.  Duplicate
JSON keys have already been a real vulnerability in this repository
(launcher records in the A6 holdout analyzer): ``json.loads`` keeps the
last value and hides the collision.  This module refuses that class of
input.

Importable without a solver.  Never writes.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path


class EvidenceError(ValueError):
    """Recorded evidence cannot be read as a unique, regular file."""


class DuplicateJsonKeyError(EvidenceError):
    """A JSON object contained the same key more than once."""


class NonRegularFileError(EvidenceError):
    """The path was a symlink, a directory, or otherwise not a regular file."""


def _reject_duplicate_json_keys(pairs):
    """``object_pairs_hook`` that refuses colliding keys at every object."""
    out = {}
    for key, value in pairs:
        if key in out:
            raise DuplicateJsonKeyError(
                f"duplicate JSON key {key!r} (refusing last-wins parse)")
        out[key] = value
    return out


def strict_json_loads(payload: bytes | str):
    """Parse JSON, refusing duplicate keys at every nesting level.

    ``payload`` may be the raw bytes returned by ``read_regular_bytes_once``
    or an already-decoded UTF-8 string (used by tests).
    """
    if isinstance(payload, bytes):
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EvidenceError("evidence is not UTF-8 JSON") from exc
    elif isinstance(payload, str):
        text = payload
    else:
        raise EvidenceError(
            f"strict_json_loads expected bytes or str, got {type(payload)!r}")
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
    except DuplicateJsonKeyError:
        raise
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"malformed JSON: {exc}") from exc


def read_regular_bytes_once(path: str | os.PathLike) -> bytes:
    """Read a regular file once; refuse symlinks and mid-read replacement.

    Signature is ``(st_dev, st_ino, st_size, st_mtime_ns)`` before open,
    after ``fstat``, and after close.  A mismatch means the inode was
    replaced while we were reading it.
    """
    raw = Path(path)
    if raw.exists() and raw.is_symlink():
        raise NonRegularFileError(f"refusing symlink: {raw}")
    if not raw.is_file():
        raise NonRegularFileError(f"not a regular file: {raw}")
    before = raw.lstat()
    if not stat.S_ISREG(before.st_mode) or raw.is_symlink():
        raise NonRegularFileError(f"not a regular file: {raw}")
    signature = (before.st_dev, before.st_ino, before.st_size,
                 before.st_mtime_ns)
    try:
        with raw.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if ((opened.st_dev, opened.st_ino, opened.st_size,
                 opened.st_mtime_ns) != signature
                    or not stat.S_ISREG(opened.st_mode)):
                raise EvidenceError(
                    f"file changed before read completed: {raw}")
            payload = handle.read()
            after_read = os.fstat(handle.fileno())
    except OSError as exc:
        raise EvidenceError(f"cannot read {raw}") from exc
    after_close = raw.lstat()
    closed_sig = (after_close.st_dev, after_close.st_ino, after_close.st_size,
                  after_close.st_mtime_ns)
    if ((after_read.st_dev, after_read.st_ino, after_read.st_size,
         after_read.st_mtime_ns) != signature
            or closed_sig != signature
            or len(payload) != before.st_size):
        raise EvidenceError(f"file changed while reading: {raw}")
    return payload
