#!/usr/bin/env python3
"""B3 internal-uplift factor pilot driver: 60 A2 + matched-dictator cells.

Implements ``doc/B3_FACTOR_PILOT_SPEC_DRAFT.md`` for the development grid:
5 frozen settings x seeds {0, 11, 15} x n {8, 12} x b {0.01, 0.05} = 60
cells, method A2 only.  Each cell binds to the committed FROZEN
factor-screen artifact (its SHA-256, disposition, selected levels) and to
the exact ``Instance.hash()`` of the corresponding physical
setting-instance (see ``experiments/b3_factor_pilot``).

Per cell: solve the dictator independently (adaptive, tol_d = 1e-2;
checkpointed so a requeue never re-solves), then run certified A2 column
generation (epsilon = 1e-2, budget = 240 exact pricing calls) with the
dictator value feeding the certified uplift interval.  All state is
atomic-checkpointed per oracle call; rerunning the same command resumes
exactly (deterministic + resumable).

Refusals (fail-closed, before any solve): A6 method/code path, any seed
>= 16 (reserved holdout 16-31 and frozen confirmation 32-37), factor
drift from the frozen levels, a wrong cell count, a non-Gurobi solver
fallback, and a dirty tracked tree.

Usage:
  python experiments/run_b3_factor_pilot.py --list
  python experiments/run_b3_factor_pilot.py --dry-run
  python experiments/run_b3_factor_pilot.py --cell K --out runs/b3_factor_pilot
  python experiments/run_b3_factor_pilot.py --all  --out runs/b3_factor_pilot
"""
from __future__ import annotations

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import experiments.b3_factor_pilot as bp
from egglab import checkpoint
from egglab.b2a2 import (
    SCHEMA_VERSION,
    _atomic_write_lines,
    certified_cg,
    market_hash,
)
from egglab.evsp import (LOAD_RECONSTRUCTION_POLICY_VERSION, REPLAY_TOL_KWH,
                         canonicalize_solution_load)
from egglab.market import make_affine_market
from egglab.records import make_record
from egglab.regimes import solve_dictator
from egglab.solver import backend

EXPERIMENT = "b3-factor-pilot"


def _materialize_dictator(d_state, jsonl_path):
    _atomic_write_lines(jsonl_path, [d_state["record"]])


def _dictator_stage(inst, market, out, tag, cell, kw, screen):
    """Transactional independent dictator solve feeding the uplift interval.
    Identity-validated (including the frozen screen record SHA and the bound
    instance hash), atomically checkpointed with the complete record committed
    inside, and materialized/repaired on resume."""
    d_identity = {
        "schema_version": SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "instance_hash": inst.hash(),
        "market_hash": market_hash(market),
        "tol_d": bp.TOL_D,
        "solver": {"backend": backend(),
                   **{k: kw[k] for k in sorted(kw)}},
        "screen_record_sha256": screen["record_sha256"],
        "setting": cell["setting"],
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
            raise bp.B3PilotError(
                f"stale dictator checkpoint for {tag}: identity mismatch; "
                "delete the cell directory to restart")
        _materialize_dictator(d_state, d_jsonl)
        return d_state

    sol = solve_dictator(inst, market, tol_abs=bp.TOL_D, **kw)
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
        "adaptive_converged": bool(adaptive_gap <= bp.TOL_D),
        "dictator_objective_reconstruction": {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "raw_true_obj": raw_true_obj,
            "physical_obj": physical_obj,
            "abs_adjustment": abs(float(raw_true_obj) - physical_obj),
        },
    })
    ex = sol.stats.extra
    if sol.stats.status != "OPTIMAL":
        raise bp.B3PilotError(f"dictator status {sol.stats.status} != OPTIMAL")
    if sol.stats.bound is None or not math.isfinite(float(sol.stats.bound)):
        raise bp.B3PilotError(f"dictator bound nonfinite: {sol.stats.bound!r}")
    if not ex.get("adaptive_converged"):
        raise bp.B3PilotError(
            f"dictator adaptive certification did not converge: gap "
            f"{ex.get('adaptive_gap_abs')} > tol {bp.TOL_D}")
    rec = make_record(EXPERIMENT, inst, sol, market=market, regime="dictator",
                      extra={"tag": tag, "cell": _cell_label(cell),
                             "setting": cell["setting"],
                             "screen_record_sha256": screen["record_sha256"]})
    if rec["replay_ok"] is False:
        raise bp.B3PilotError(f"dictator replay invalid: {rec['replay_violations']}")
    d_state = {"identity": d_identity,
               "z_d_ub": sol.obj_true, "z_d_lb": adaptive_lb, "tol_d": bp.TOL_D,
               "adaptive": ex, "status": sol.stats.status,
               "bound": sol.stats.bound, "record": rec}
    checkpoint.save(d_path, d_state)
    _materialize_dictator(d_state, d_jsonl)
    return d_state


def _cell_label(cell):
    return [cell["setting"], cell["seed"], cell["n_trips"], cell["b"]]


def run_cell(cell, args, screen):
    tag = cell["tag"]
    out = os.path.join(args.out, tag)
    os.makedirs(out, exist_ok=True)
    kw = dict(max_mip_gap=args.mip_gap, time_limit_s=None)

    # bind to the frozen screen (rebuilds and hash-checks the instance)
    inst = bp.bind_cell_to_screen(cell, screen)
    market = make_affine_market(inst, shape="duck", b_scale=cell["b"])

    d_state = _dictator_stage(inst, market, out, tag, cell, kw, screen)

    state = certified_cg(
        inst, market,
        epsilon=bp.EPSILON, budget=bp.BUDGET,
        out_dir=out, tag="a2",
        experiment=EXPERIMENT,
        solver_kw=kw,
        z_d_ub=d_state["z_d_ub"], tol_d=d_state["tol_d"],
        method=bp.METHOD,
    )
    oc = state["outcome"]
    print(f"[done] {tag}: {oc['type']} gap={oc['gap']:.6f} "
          f"oracle_calls={state['oracle_calls']} columns={len(state['columns'])} "
          f"uplift={oc.get('uplift_interval')}")


def _preflight(screen):
    """Load-time binding + count + refusal checks with no solver work."""
    bp.assert_no_factor_drift(screen)
    cells = bp.build_cells()
    if len(cells) != bp.N_CELLS:
        raise bp.B3PilotError(
            f"enumerated {len(cells)} cells, expected {bp.N_CELLS}")
    seen = set()
    for cell in cells:
        bp.assert_development_seed(cell["seed"])
        bp.assert_method_a2(bp.METHOD)
        bp.assert_no_a6(cell["setting"], cell["tag"])
        bp.bind_cell_to_screen(cell, screen)
        if cell["tag"] in seen:
            raise bp.B3PilotError(f"duplicate cell tag {cell['tag']}")
        seen.add(cell["tag"])
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/b3_factor_pilot")
    ap.add_argument("--mip-gap", dest="mip_gap", type=float, default=1e-6)
    ap.add_argument("--screen-dir", default=None,
                    help="override the frozen screen dir (tests only)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="full binding/count/refusal preflight; no solve")
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    cells = bp.build_cells()

    if args.list:
        for k, c in enumerate(cells):
            print(k, {"setting": c["setting"], "seed": c["seed"],
                      "n_trips": c["n_trips"], "b": c["b"],
                      "battery_kwh": c["battery_kwh"],
                      "charge_power_kw": c["charge_power_kw"],
                      "method": bp.METHOD, "epsilon": bp.EPSILON,
                      "budget": bp.BUDGET})
        print(f"total: {len(cells)} cells")
        return

    screen = bp.load_frozen_screen(args.screen_dir)

    if args.dry_run:
        checked = _preflight(screen)
        try:
            bp.assert_grb_backend()
            grb = "GRB (ok)"
        except bp.B3PilotError as exc:
            grb = f"NON-GRB — solves would refuse: {exc}"
        print(f"[dry-run] screen={screen['record_sha256'][:16]} "
              f"cells={len(checked)} settings={bp.N_SETTINGS} "
              f"contrasts={bp.N_MATCHED_CONTRASTS}")
        print(f"[dry-run] factor-drift gate: PASS ({bp.N_PHYSICAL_INSTANCES} "
              "instance hashes match the frozen screen)")
        print(f"[dry-run] backend: {grb}")
        print("[dry-run] OK — bound to frozen screen; nothing launched")
        return

    if args.cell is None and not args.all:
        ap.error("choose --list, --dry-run, --cell K, or --all")

    # execution path: hard refusals before any solve
    bp.assert_clean_tracked_tree()
    bp.assert_grb_backend()
    _preflight(screen)

    if args.cell is not None:
        if not (0 <= args.cell < len(cells)):
            ap.error(f"--cell must be in [0, {len(cells)})")
        run_cell(cells[args.cell], args, screen)
    else:
        for c in cells:
            run_cell(c, args, screen)


if __name__ == "__main__":
    main()
