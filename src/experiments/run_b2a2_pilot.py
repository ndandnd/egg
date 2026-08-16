#!/usr/bin/env python3
"""B2-A2 pilot driver: certified plain column generation, 12 cells exactly.

Grid (doc/MEASUREMENT_RESULTS.md Section 8, pilot spec):
  seeds {0, 11, 15} x n_trips {8, 12} x b {0.01, 0.05}; method A2 only;
  epsilon = 1e-2; budget = 240 exact pricing calls.

Per cell: solve the dictator independently (adaptive, tol 1e-2; checkpointed
so requeues do not re-solve), then run certified CG with the dictator value
feeding the uplift interval. All state is atomic-checkpointed per oracle
call; rerunning the same command resumes exactly.

Usage:
  python experiments/run_b2a2_pilot.py --list
  python experiments/run_b2a2_pilot.py --cell K --out runs/b2a2_pilot
  python experiments/run_b2a2_pilot.py --all  --out runs/b2a2_pilot
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math

from egglab import checkpoint
from egglab.b2a2 import certified_cg, market_hash
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.records import append_jsonl, make_record
from egglab.regimes import solve_dictator

SEEDS = (0, 11, 15)
N_TRIPS = (8, 12)
B_SCALES = (0.01, 0.05)
EPSILON = 1e-2
BUDGET = 240
TOL_D = 1e-2


def build_cells():
    return list(itertools.product(SEEDS, N_TRIPS, B_SCALES))


def run_cell(cell, args):
    seed, n_trips, b = cell
    tag = f"s{seed}_n{n_trips}_b{b:g}"
    out = os.path.join(args.out, tag)
    os.makedirs(out, exist_ok=True)
    kw = dict(max_mip_gap=args.mip_gap, time_limit_s=None)

    inst = synthetic_instance(seed=seed, n_trips=n_trips)
    market = make_affine_market(inst, shape="duck", b_scale=b)

    # independent dictator solve (checkpointed; feeds the uplift interval)
    d_identity = {"instance_hash": inst.hash(),
                  "market_hash": market_hash(market), "tol_d": TOL_D}
    d_path = os.path.join(out, "dictator.ckpt.json")
    d_state = checkpoint.load(d_path)
    if d_state is not None and d_state.get("identity") != d_identity:
        raise RuntimeError(
            f"stale dictator checkpoint for {tag}: identity mismatch "
            "(instance/market/tolerance changed); delete the cell directory "
            "to restart")
    if d_state is None:
        sol = solve_dictator(inst, market, tol_abs=TOL_D, **kw)
        ex = sol.stats.extra
        # gate before the checkpoint is stored: OPTIMAL status, a finite
        # certified bound, and adaptive convergence are all required
        if sol.stats.status != "OPTIMAL":
            raise RuntimeError(f"dictator status {sol.stats.status} != OPTIMAL")
        if sol.stats.bound is None or not math.isfinite(float(sol.stats.bound)):
            raise RuntimeError(f"dictator bound nonfinite: {sol.stats.bound!r}")
        if not ex.get("adaptive_converged"):
            raise RuntimeError(
                f"dictator adaptive certification did not converge: "
                f"gap {ex.get('adaptive_gap_abs')} > tol {ex.get('adaptive_tol_abs')}")
        rec = make_record("b2a2-pilot", inst, sol, market=market,
                          regime="dictator",
                          extra={"tag": tag, "cell": list(cell)})
        if rec["replay_ok"] is False:
            raise RuntimeError(f"dictator replay invalid: {rec['replay_violations']}")
        append_jsonl(os.path.join(out, "dictator.jsonl"), rec)
        d_state = {"identity": d_identity,
                   "z_d_ub": sol.obj_true, "tol_d": TOL_D,
                   "adaptive": ex, "status": sol.stats.status,
                   "bound": sol.stats.bound}
        checkpoint.save(d_path, d_state)

    state = certified_cg(
        inst, market,
        epsilon=EPSILON, budget=BUDGET,
        out_dir=out, tag="a2",
        experiment="b2a2-pilot",
        solver_kw=kw,
        z_d_ub=d_state["z_d_ub"], tol_d=d_state["tol_d"],
    )
    oc = state["outcome"]
    print(f"[done] {tag}: {oc['type']} gap={oc['gap']:.6f} "
          f"oracle_calls={state['oracle_calls']} columns={len(state['columns'])} "
          f"uplift={oc.get('uplift_interval')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/b2a2_pilot")
    ap.add_argument("--mip-gap", dest="mip_gap", type=float, default=1e-6)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    cells = build_cells()
    if args.list:
        for k, c in enumerate(cells):
            print(k, {"seed": c[0], "n_trips": c[1], "b": c[2],
                      "method": "A2", "epsilon": EPSILON, "budget": BUDGET})
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
