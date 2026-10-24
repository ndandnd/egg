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
import numpy as np

from egglab import checkpoint
from egglab.b2a2 import (
    SCHEMA_VERSION,
    _atomic_write_lines,
    certified_cg,
    market_hash,
)
from egglab.evsp import (LOAD_RECONSTRUCTION_POLICY_VERSION, REPLAY_TOL_KWH,
                         canonicalize_solution_load)
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.records import make_record
from egglab.regimes import solve_dictator
from egglab.solver import backend

SEEDS = (0, 11, 15)
N_TRIPS = (8, 12)
B_SCALES = (0.01, 0.05)
EPSILON = 1e-2
BUDGET = 240
TOL_D = 1e-2


def build_cells():
    return list(itertools.product(SEEDS, N_TRIPS, B_SCALES))


def _materialize_dictator(d_state, jsonl_path):
    """Atomically (re)build dictator.jsonl from the record committed inside
    the checkpoint. Idempotent: the checkpoint is the source of truth, so a
    kill at any point yields exactly one dictator record after resume."""
    _atomic_write_lines(jsonl_path, [d_state["record"]])


def _dictator_stage(
    inst, market, out, tag, cell, kw, *, experiment="b2a2-pilot"
):
    """Transactional independent dictator solve (feeds the uplift interval).
    Identity-validated, atomically checkpointed with the complete record
    committed inside, and materialized/repaired on resume. ``experiment``
    labels new evidence truthfully. Representation-policy changes are part of
    the identity, so evidence produced before physical-load reconstruction is
    deliberately not resumable under newer code.
    """
    d_identity = {
        "schema_version": SCHEMA_VERSION,
        "instance_hash": inst.hash(),
        "market_hash": market_hash(market),
        "tol_d": TOL_D,
        "solver": {"backend": backend(),
                   **{k: kw[k] for k in sorted(kw)}},
        "load_reconstruction": {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "tolerance_kwh": REPLAY_TOL_KWH,
        },
    }
    d_path = os.path.join(out, "dictator.ckpt.json")
    d_jsonl = os.path.join(out, "dictator.jsonl")
    d_state = checkpoint.load(d_path)
    if d_state is not None:
        if d_state.get("identity") != d_identity:
            raise RuntimeError(
                f"stale dictator checkpoint for {tag}: identity mismatch "
                "(instance/market/tolerance/solver settings changed); delete "
                "the cell directory to restart")
        stored_experiment = (d_state.get("record") or {}).get("experiment")
        if stored_experiment != experiment:
            raise RuntimeError(
                f"stale dictator checkpoint for {tag}: record experiment "
                f"mismatch ({stored_experiment!r} != requested "
                f"{experiment!r}); "
                "refusing cross-campaign resume")
        # repair/materialize the log from committed state before use
        _materialize_dictator(d_state, d_jsonl)
        return d_state

    sol = solve_dictator(inst, market, tol_abs=TOL_D, **kw)
    raw_true_obj = sol.obj_true
    canonicalize_solution_load(inst, sol)
    physical_obj = float(
        sol.ops_cost + market.system_cost_delta(np.asarray(sol.load)))
    sol.obj_true = physical_obj
    adaptive_lb = float(sol.stats.extra["adaptive_lb"])
    adaptive_gap = physical_obj - adaptive_lb
    sol.stats.extra.update({
        "adaptive_ub": physical_obj,
        "adaptive_gap_abs": adaptive_gap,
        "adaptive_converged": bool(adaptive_gap <= TOL_D),
        "dictator_objective_reconstruction": {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "raw_true_obj": raw_true_obj,
            "physical_obj": physical_obj,
            "abs_adjustment": abs(float(raw_true_obj) - physical_obj),
        },
    })
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
    rec = make_record(experiment, inst, sol, market=market,
                      regime="dictator",
                      extra={"tag": tag, "cell": list(cell)})
    if rec["replay_ok"] is False:
        raise RuntimeError(f"dictator replay invalid: {rec['replay_violations']}")
    d_state = {"identity": d_identity,
               "z_d_ub": sol.obj_true, "tol_d": TOL_D,
               "adaptive": ex, "status": sol.stats.status,
               "bound": sol.stats.bound,
               "record": rec}
    checkpoint.save(d_path, d_state)          # commit point
    _materialize_dictator(d_state, d_jsonl)   # derived from committed state
    return d_state


def run_cell(cell, args):
    seed, n_trips, b = cell
    tag = f"s{seed}_n{n_trips}_b{b:g}"
    out = os.path.join(args.out, tag)
    os.makedirs(out, exist_ok=True)
    kw = dict(max_mip_gap=args.mip_gap, time_limit_s=None)

    inst = synthetic_instance(seed=seed, n_trips=n_trips)
    market = make_affine_market(inst, shape="duck", b_scale=b)

    d_state = _dictator_stage(inst, market, out, tag, cell, kw)

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
