#!/usr/bin/env python3
"""Run or audit the frozen tiny local-move column-proposer laboratory."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.column_proposer import (  # noqa: E402
    CELLS,
    ColumnProposerError,
    audit_directory,
    publish,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-root",
        help="fresh raw A2/proposer run root (required for --run)",
    )
    parser.add_argument(
        "--out",
        help="fresh published artifact directory (required for --run)",
    )
    parser.add_argument(
        "--analysis-commit",
        help="full committed code SHA (defaults to HEAD)",
    )
    parser.add_argument(
        "--audit",
        help="audit one existing published artifact directory",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print the exact frozen cells without solving",
    )
    args = parser.parse_args()

    selected = sum(bool(value) for value in (
        args.list, args.audit, args.run_root or args.out))
    if selected != 1:
        parser.error("choose exactly one of --list, --audit, or --run-root/--out")

    if args.list:
        for index, (seed, n_trips, b) in enumerate(CELLS):
            print(index, json.dumps({
                "seed": seed,
                "n_trips": n_trips,
                "b": b,
            }, sort_keys=True))
        print(f"total: {len(CELLS)}")
        return

    if args.audit:
        if args.run_root or args.out or args.analysis_commit:
            parser.error("--audit cannot be combined with run arguments")
        errors = audit_directory(args.audit)
        if errors:
            for error in errors:
                print(f"FAIL: {error}", file=sys.stderr)
            raise SystemExit(1)
        print("PASS")
        return

    if not args.run_root or not args.out:
        parser.error("--run-root and --out are both required")
    try:
        result = publish(
            Path(args.run_root),
            Path(args.out),
            analysis_commit=args.analysis_commit,
        )
    except ColumnProposerError as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    print(result)


if __name__ == "__main__":
    main()
