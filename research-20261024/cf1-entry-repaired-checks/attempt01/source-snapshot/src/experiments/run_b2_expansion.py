#!/usr/bin/env python3
"""B2 208-cell matched expansion driver (Option B, DECISION_LOG 2026-08-17).

Purpose: give the stabilization kill decision its full preregistered
denominator. The moderate/strong-feedback matched population is

    seeds 0-15 x n_trips {8, 12} x b {0.01, 0.05} = 64 instances
    x methods {A2, A3, A4, A5}                    = 256 method-cells,

of which the certified pilots already cover the 12 instances with seeds
{0, 11, 15} (48 method-cells, result/b2_pilot/). This driver runs EXACTLY
the remaining 52 instances x 4 methods = 208 method-cells, with settings
identical to the pilots (duck market, epsilon 1e-2, budget 240 exact
oracle calls, per-cell transactional dictator stage, atomic requeue-safe
checkpoints).

This is a POPULATION-ROBUSTNESS campaign, not a scale test: n and T are
unchanged (DECISION_LOG). Certification is an OUTCOME to be measured
(acc-1 tests >= 95%), not an audit gate — budget-exhausted cells are
valid completed science.

Usage:
  python experiments/run_b2_expansion.py --list
  python experiments/run_b2_expansion.py --cell K --out runs/b2_expansion
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

METHODS = ("a2", "a3", "a4", "a5")
PILOT_SEEDS = (0, 11, 15)          # covered by result/b2_pilot (48 cells)
ALL_SEEDS = tuple(range(16))
EXPANSION_SEEDS = tuple(s for s in ALL_SEEDS if s not in PILOT_SEEDS)
N_TRIPS = (8, 12)
B_SCALES = (0.01, 0.05)
EPSILON = 1e-2
BUDGET = 240
TOL_D = 1e-2


def expansion_instances():
    return list(itertools.product(EXPANSION_SEEDS, N_TRIPS, B_SCALES))


def build_cells():
    return [(m, s, n, b) for m in METHODS
            for (s, n, b) in expansion_instances()]


def run_cell(cell, args):
    method, seed, n_trips, b = cell
    tag_dir = f"{method}_s{seed}_n{n_trips}_b{b:g}"
    out = os.path.join(args.out, tag_dir)
    os.makedirs(out, exist_ok=True)
    kw = dict(max_mip_gap=args.mip_gap, time_limit_s=None)

    inst = synthetic_instance(seed=seed, n_trips=n_trips)
    market = make_affine_market(inst, shape="duck", b_scale=b)

    d_state = _dictator_stage(inst, market, out, tag_dir, list(cell), kw)

    state = certified_cg(
        inst, market,
        epsilon=EPSILON, budget=BUDGET,
        out_dir=out, tag=method,
        experiment="b2-expansion",
        solver_kw=kw,
        z_d_ub=d_state["z_d_ub"], tol_d=d_state["tol_d"],
        method=method,
    )
    oc = state["outcome"]
    print(f"[done] {tag_dir}: {oc['type']} gap={oc['gap']:.6f} "
          f"calls={state['oracle_calls']} "
          f"(clean={oc['oracle_calls_clean']}, stab={oc['oracle_calls_stab']}) "
          f"uplift={oc.get('uplift_interval')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/b2_expansion")
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
