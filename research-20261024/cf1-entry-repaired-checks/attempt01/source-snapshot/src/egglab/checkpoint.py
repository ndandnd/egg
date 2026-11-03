"""Atomic JSON checkpoints for preemption-safe restart.

Pattern: a driver computes work units in a deterministic order, calls
`load()` at startup, skips completed units, and `save()`s after every
completed unit. Slurm requeue (or any restart) then resumes exactly where the
job was preempted. Writes are atomic (tmp file + rename) so a kill during
save cannot corrupt the checkpoint.
"""
from __future__ import annotations

import json
import os
import tempfile


def save(path: str, obj: dict) -> None:
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)
