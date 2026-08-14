#!/usr/bin/env python3
"""Phase 2: switch-boundary mapping sweeps on synthetic instances.

Each cell = (seed, n_trips, sweep_slot). Sweeps the price of one slot over a
delta grid around the posted price, records schedule switches. Checkpointed
at grid-point granularity; safe under preemption/requeue.

Usage mirrors run_phase1.py (--list / --cell K / --all).
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from egglab.boundary import sweep_slot
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market


def build_cells(args):
    return list(itertools.product(args.seeds, args.n_trips, args.slots))


def run_cell(cell, args):
    seed, n_trips, slot = cell
    tag = f"s{seed}_n{n_trips}_slot{slot}"
    out = os.path.join(args.out, tag)
    inst = synthetic_instance(seed=seed, n_trips=n_trips)
    market = make_affine_market(inst, shape=args.shape, b_scale=0.0)
    base = market.price(np.zeros(market.n_slots))
    deltas = np.arange(args.d_min, args.d_max + 1e-9, args.d_step)
    state = sweep_slot(
        inst,
        base,
        slot=slot,
        deltas=deltas,
        out_dir=out,
        tag="sweep",
        solver_kw=dict(max_mip_gap=args.mip_gap, time_limit_s=args.time_limit),
    )
    print(f"[done] cell {tag}: {state['n_switches']} switches")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    ap.add_argument("--n-trips", dest="n_trips", type=int, nargs="+", default=[8, 12])
    ap.add_argument("--slots", type=int, nargs="+", default=[8, 12, 16, 20])
    ap.add_argument("--shape", default="duck")
    ap.add_argument("--d-min", dest="d_min", type=float, default=-1.5)
    ap.add_argument("--d-max", dest="d_max", type=float, default=1.5)
    ap.add_argument("--d-step", dest="d_step", type=float, default=0.05)
    ap.add_argument("--mip-gap", dest="mip_gap", type=float, default=1e-6)
    ap.add_argument("--time-limit", dest="time_limit", type=float, default=None)
    ap.add_argument("--out", default="runs/phase2")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    cells = build_cells(args)
    if args.list:
        for k, c in enumerate(cells):
            print(k, c)
        print(f"total: {len(cells)} cells")
        return
    if args.cell is not None:
        run_cell(cells[args.cell], args)
    elif args.all:
        for c in cells:
            run_cell(c, args)
    else:
        ap.error("choose --list, --cell K, or --all")


if __name__ == "__main__":
    main()
