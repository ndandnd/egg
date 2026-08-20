#!/usr/bin/env python3
"""Freeze a reviewed GIRO-derived instance with a verifiable manifest.

The command deliberately does not choose a weekday variant, fill deadhead
links, or invent vehicle physics.  Its input instance must already use
``Instance.canonical()`` format, and ``--provenance`` must be a JSON document
with this exact top-level shape:

    {
      "schema": "egglab-giro-freeze-provenance-v1",
      "contract": "...",
      "service_day": null,
      "variant_choice": {
        "policy": "...",
        "selected": ["..."]
      },
      "trip_selection": {
        "rule": "Identifier == Regular",
        "source_rows": [123, 456],
        "trip_ids": ["..."]
      },
      "deadhead_fidelity": {
        "level": "exact-directed-base",
        "directed": true,
        "time_dependent": false,
        "same_reference_policy": "...",
        "missing_link_policy": "..."
      },
      "physics": {
        "service_energy_policy": "...",
        "instance_parameters": {...}
      }
    }

Use repeatable ``--source ROLE=PATH`` arguments to bind the artifact to raw or
derived inputs without copying confidential source bytes into the output.
Publication is deterministic, atomic, and refuses to replace any existing
destination.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.frozen import FrozenSubsetError, freeze_subset


def _source_argument(value: str) -> tuple[str, Path]:
    role, separator, path = value.partition("=")
    if not separator or not role or not path:
        raise argparse.ArgumentTypeError(
            "--source must have the form ROLE=PATH"
        )
    return role, Path(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--instance",
        "--input",
        dest="instance",
        required=True,
        help="reviewed Instance.canonical() JSON candidate",
    )
    parser.add_argument(
        "--provenance",
        required=True,
        help="reviewed GIRO provenance JSON",
    )
    parser.add_argument(
        "--out-dir",
        "--output",
        "--out",
        dest="out_dir",
        required=True,
        help="new artifact directory (must not already exist)",
    )
    parser.add_argument(
        "--source",
        action="append",
        required=True,
        type=_source_argument,
        metavar="ROLE=PATH",
        help="additional source to hash into the manifest; repeatable",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = freeze_subset(
            args.instance,
            args.provenance,
            args.out_dir,
            source_files=args.source,
        )
    except FrozenSubsetError as exc:
        print(f"freeze refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
