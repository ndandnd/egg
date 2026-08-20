#!/usr/bin/env python3
"""Build or check the canonical bounded strict-two-cycle witness."""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.cycle_minimizer import (  # noqa: E402
    DEFAULT_MAX_ORACLE_EVALUATIONS,
    DEFAULT_MAX_WALL_SECONDS,
    build_witness,
    canonical_witness_bytes,
    minimize_fixture,
)


def generate(max_oracle_evaluations: int, max_wall_seconds: float) -> bytes:
    reduction = minimize_fixture(
        max_oracle_evaluations=max_oracle_evaluations,
        max_wall_seconds=max_wall_seconds,
    )
    return canonical_witness_bytes(build_witness(reduction))


def _atomic_write(path: Path, payload: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Deterministically minimize the closed synthetic strict-cycle "
            "fixture; no seed/grid expansion is performed"))
    parser.add_argument("--out", required=True, help="witness JSON path")
    parser.add_argument(
        "--check", action="store_true",
        help="regenerate and require byte identity without writing")
    parser.add_argument(
        "--max-oracle-evaluations", type=int,
        default=DEFAULT_MAX_ORACLE_EVALUATIONS)
    parser.add_argument(
        "--max-wall-seconds", type=float,
        default=DEFAULT_MAX_WALL_SECONDS)
    args = parser.parse_args(argv)

    path = Path(args.out)
    payload = generate(
        args.max_oracle_evaluations, args.max_wall_seconds)
    if args.check:
        if not path.is_file():
            parser.error(f"--check target does not exist: {path}")
        if path.read_bytes() != payload:
            parser.error(
                f"canonical witness differs from regenerated output: {path}")
        return
    _atomic_write(path, payload)


if __name__ == "__main__":
    main()
