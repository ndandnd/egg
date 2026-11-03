#!/usr/bin/env python3
"""B2 A3-A5 stabilization pilot driver: exactly 36 cells.

Grid (doc/B2_STABILIZATION_SPEC.md; follows the certified A2 pilot):
  methods {a3, a4, a5} x seeds {0, 11, 15} x n_trips {8, 12} x
  b {0.01, 0.05}; epsilon = 1e-2; budget = 240 exact oracle calls (clean
  certification calls and stabilized candidate calls both count).

Per cell: transactional dictator stage (shared implementation with the A2
pilot), then certified stabilized CG with the dictator value feeding the
uplift interval. Rerunning the same command resumes exactly.

Usage:
  python experiments/run_b2a345_pilot.py --list
  python experiments/run_b2a345_pilot.py --cell K --out runs/b2a345_pilot
  python experiments/run_b2a345_pilot.py --all  --out runs/b2a345_pilot
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.b2a2 import certified_cg
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from experiments.run_b2a2_pilot import _dictator_stage

METHODS = ("a3", "a4", "a5")
SEEDS = (0, 11, 15)
N_TRIPS = (8, 12)
B_SCALES = (0.01, 0.05)
EPSILON = 1e-2
BUDGET = 240
TOL_D = 1e-2


def build_cells():
    return list(itertools.product(METHODS, SEEDS, N_TRIPS, B_SCALES))


def run_cell(cell, args):
    method, seed, n_trips, b = cell
    tag = f"{method}_s{seed}_n{n_trips}_b{b:g}"
    out = os.path.join(args.out, tag)
    os.makedirs(out, exist_ok=True)
    kw = dict(max_mip_gap=args.mip_gap, time_limit_s=None)

    inst = synthetic_instance(seed=seed, n_trips=n_trips)
    market = make_affine_market(inst, shape="duck", b_scale=b)

    d_state = _dictator_stage(inst, market, out, tag, list(cell), kw)

    state = certified_cg(
        inst, market,
        epsilon=EPSILON, budget=BUDGET,
        out_dir=out, tag=method,
        experiment="b2a345-pilot",
        solver_kw=kw,
        z_d_ub=d_state["z_d_ub"], tol_d=d_state["tol_d"],
        method=method,
    )
    oc = state["outcome"]
    print(f"[done] {tag}: {oc['type']} gap={oc['gap']:.6f} "
          f"calls={state['oracle_calls']} "
          f"(clean={oc['oracle_calls_clean']}, stab={oc['oracle_calls_stab']}) "
          f"serious={state['stab']['serious_steps']} "
          f"null={state['stab']['null_steps']} "
          f"tv={oc['broadcast_tv']:.3f} uplift={oc.get('uplift_interval')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/b2a345_pilot")
    ap.add_argument("--mip-gap", dest="mip_gap", type=float, default=1e-6)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    cells = build_cells()
    if args.list:
        for k, c in enumerate(cells):
            print(k, {"method": c[0].upper(), "seed": c[1], "n_trips": c[2],
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
