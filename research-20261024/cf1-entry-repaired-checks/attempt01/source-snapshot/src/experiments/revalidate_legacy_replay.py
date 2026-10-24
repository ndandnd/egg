#!/usr/bin/env python3
"""Checkpointed CLI for the legacy replay revalidation campaign.

Usage:
  python experiments/revalidate_legacy_replay.py RUNS_DIR --list
  python experiments/revalidate_legacy_replay.py RUNS_DIR --count
  python experiments/revalidate_legacy_replay.py RUNS_DIR --cell K
  python experiments/revalidate_legacy_replay.py RUNS_DIR --all

One cell = one record with stored replay_ok == false, in a deterministic
order (file path, line index). Each cell writes one atomic sidecar JSON under
RUNS_DIR/revalidation/<sha256>.json; existing sidecars are returned untouched
(idempotent), so the tool is parallel-safe and resumable — rerunning after a
preemption or with an overlapping array does no duplicate work and never
edits the original JSONL. See doc/MEASUREMENT_CLOSEOUT.md for policy.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.revalidate import (
    ACCEPTED_DISPOSITIONS,
    revalidate_record,
    scan_failures,
)


def run_cell(runs_dir: str, entry: dict, solver_kw: dict) -> str:
    sc = revalidate_record(runs_dir, entry, solver_kw=solver_kw)
    disp = sc.get("disposition")
    marker = "OK" if disp in ACCEPTED_DISPOSITIONS else "NONACCEPTED"
    print(
        f"[{marker} {disp}] {entry['file']}:{entry['line_idx']} "
        f"sha={entry['sha256'][:12]} detail={sc.get('detail','')!r} "
        f"residuals={sc.get('residuals')}"
    )
    return disp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--count", action="store_true")
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--mip-gap", dest="mip_gap", type=float, default=1e-6)
    ap.add_argument("--time-limit", dest="time_limit", type=float, default=None)
    args = ap.parse_args()

    failures = scan_failures(args.runs_dir)
    if args.count:
        print(len(failures))
        return
    if args.list:
        for k, e in enumerate(failures):
            print(k, e["file"], e["line_idx"], e["sha256"][:12])
        print(f"total: {len(failures)} cells")
        return

    solver_kw = dict(max_mip_gap=args.mip_gap, time_limit_s=args.time_limit)
    if args.cell is not None:
        disp = run_cell(args.runs_dir, failures[args.cell], solver_kw)
        if disp not in ACCEPTED_DISPOSITIONS:
            # Exit nonzero AFTER the sidecar is safely written so Slurm/email
            # flags the problem immediately. Reruns/requeues are harmless:
            # the existing sidecar short-circuits (no re-solve), so a
            # permanent materially-different verdict is not retried.
            sys.exit(
                f"NONACCEPTED disposition '{disp}' for cell {args.cell} "
                f"(sidecar written; see it for diagnostics)"
            )
    elif args.all:
        dispositions = [run_cell(args.runs_dir, e, solver_kw) for e in failures]
        n_ok = sum(1 for d in dispositions if d in ACCEPTED_DISPOSITIONS)
        print(f"revalidated {n_ok}/{len(dispositions)} accepted")
        if n_ok != len(dispositions):
            sys.exit(f"{len(dispositions) - n_ok} nonaccepted dispositions")
    else:
        ap.error("choose --list, --count, --cell K, or --all")


if __name__ == "__main__":
    main()
