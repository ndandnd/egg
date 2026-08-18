#!/usr/bin/env python3
"""A6 burned-seed pilot driver: EXACTLY 24 cells
(doc/A6_SPARSE_STABILIZATION_SPEC.md Section 7).

Grid: methods {a6_a4, a6_a3} x BURNED seeds {0, 11, 15} x n_trips {8, 12}
x b {0.01, 0.05}. Settings identical to the A2-A5 campaigns (epsilon
1e-2, budget 240, duck market, per-cell transactional dictator stage).
The pilot gates IMPLEMENTATION correctness and feeds the one-shot arm
selection (experiments/select_a6_arm.py); its results are dev-only and
may never be cited as evaluation evidence. The holdout (seeds 16-31) is
NOT part of this driver and must not be generated before the selection
artifact is committed.

Usage:
  python experiments/run_a6_pilot.py --list
  python experiments/run_a6_pilot.py --cell K --out runs/a6_pilot
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.a6 import A6_METHODS, certified_cg_a6
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from experiments.run_b2a2_pilot import _dictator_stage

SEEDS = (0, 11, 15)   # BURNED pilot seeds; holdout seeds 16-31 excluded
N_TRIPS = (8, 12)
B_SCALES = (0.01, 0.05)
EPSILON = 1e-2
BUDGET = 240
TOL_D = 1e-2


def build_cells():
    return [(m, s, n, b) for m in A6_METHODS
            for (s, n, b) in itertools.product(SEEDS, N_TRIPS, B_SCALES)]


def run_cell(cell, args):
    method, seed, n_trips, b = cell
    tag_dir = f"{method}_s{seed}_n{n_trips}_b{b:g}"
    out = os.path.join(args.out, tag_dir)
    os.makedirs(out, exist_ok=True)
    kw = dict(max_mip_gap=args.mip_gap, time_limit_s=None)

    inst = synthetic_instance(seed=seed, n_trips=n_trips)
    market = make_affine_market(inst, shape="duck", b_scale=b)

    d_state = _dictator_stage(inst, market, out, tag_dir, list(cell), kw)

    state = certified_cg_a6(
        inst, market, method=method,
        epsilon=EPSILON, budget=BUDGET,
        out_dir=out, tag=method,
        experiment="a6-pilot",
        solver_kw=kw,
        z_d_ub=d_state["z_d_ub"], tol_d=d_state["tol_d"],
    )
    oc = state["outcome"]
    print(f"[done] {tag_dir}: {oc['type']} gap={oc['gap']:.6f} "
          f"calls={state['oracle_calls']} "
          f"(clean={oc['oracle_calls_clean']}, cand={oc['oracle_calls_stab']}) "
          f"triggers={oc['trigger_selected_counts']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/a6_pilot")
    ap.add_argument("--mip-gap", dest="mip_gap", type=float, default=1e-6)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    cells = build_cells()
    if args.list:
        for k, c in enumerate(cells):
            print(k, {"method": c[0], "seed": c[1], "n_trips": c[2],
                      "b": c[3], "epsilon": EPSILON, "budget": BUDGET})
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
