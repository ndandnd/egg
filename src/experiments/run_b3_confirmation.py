#!/usr/bin/env python3
"""B3 fresh-seed confirmation driver (GO-gated, outcome-blind).

Runs the frozen confirmation population of
``doc/B3_FACTOR_PILOT_SPEC_DRAFT.md`` Section 8: seeds {32..37}, S0 versus
the SELECTED factor (read from the committed GO selection artifact, never
hardcoded), n {8,12}, b {0.01,0.05} = 24 matched contrasts / 48 A2
method-cells; epsilon 0.01, tol_d 0.01, budget 240; A2 only.

STRUCTURAL GO GATE: every mode requires a committed GO ``SELECTION.json``
that validates (state == GO, named factor, analyzer-commit ancestry, the
frozen screen SHA + pilot spec hash, the frozen pilot raw-tree anchor, the
boundary disclosure — a knife-edge decision refuses — and that it is not
INVALID/HALT-derived). There is no flag, environment variable, or test
hook that bypasses the gate.

Refusals before any solve: a non-GO/boundary-adjacent/tampered selection
artifact, a non-Gurobi backend, a dirty tracked tree, a seed outside
{32..37}, an A6 path, and any path overlapping ``runs/b3_factor_pilot``
(the pilot outcomes are never read). Nothing is launched here.

Usage:
  run_b3_confirmation.py --selection-artifact SEL.json --list
  run_b3_confirmation.py --selection-artifact SEL.json --dry-run
  run_b3_confirmation.py --selection-artifact SEL.json --emit-run-manifest --out DIR
  run_b3_confirmation.py --selection-artifact SEL.json --bind-job JOBID --out DIR
  run_b3_confirmation.py --selection-artifact SEL.json --cell K --out DIR
"""
from __future__ import annotations

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import experiments.b3_confirmation as cc
from egglab import checkpoint
from egglab.b2a2 import (SCHEMA_VERSION, _atomic_write_lines, certified_cg,
                         market_hash)
from egglab.evsp import (LOAD_RECONSTRUCTION_POLICY_VERSION, REPLAY_TOL_KWH,
                         canonicalize_solution_load)
from egglab.market import make_affine_market
from egglab.records import make_record
from egglab.regimes import solve_dictator
from egglab.solver import backend

EXPERIMENT = "b3-confirmation"


def _materialize_dictator(d_state, jsonl_path):
    _atomic_write_lines(jsonl_path, [d_state["record"]])


def _dictator_stage(inst, market, out, tag, cell, kw, run):
    d_identity = {
        "schema_version": SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "instance_hash": inst.hash(),
        "market_hash": market_hash(market),
        "tol_d": cc.TOL_D,
        "solver": {"backend": backend(), **{k: kw[k] for k in sorted(kw)}},
        "screen_record_sha256": cc.FROZEN_SCREEN_RECORD_SHA256,
        "run_manifest_sha256": run["sha256"],
        "run_commit": run["manifest"]["run_commit"],
        "selection_artifact_sha256":
            run["manifest"]["selection_artifact_sha256"],
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
            raise cc.B3ConfirmationError(
                f"stale dictator checkpoint for {tag}: identity mismatch; "
                "delete the cell directory to restart")
        _materialize_dictator(d_state, d_jsonl)
        return d_state

    sol = solve_dictator(inst, market, tol_abs=cc.TOL_D, **kw)
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
        "adaptive_converged": bool(adaptive_gap <= cc.TOL_D),
        "dictator_objective_reconstruction": {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "raw_true_obj": raw_true_obj, "physical_obj": physical_obj,
            "abs_adjustment": abs(float(raw_true_obj) - physical_obj),
        },
    })
    ex = sol.stats.extra
    if sol.stats.status != "OPTIMAL":
        raise cc.B3ConfirmationError(
            f"dictator status {sol.stats.status} != OPTIMAL")
    if sol.stats.bound is None or not math.isfinite(float(sol.stats.bound)):
        raise cc.B3ConfirmationError(
            f"dictator bound nonfinite: {sol.stats.bound!r}")
    if not ex.get("adaptive_converged"):
        raise cc.B3ConfirmationError(
            f"dictator adaptive certification did not converge: gap "
            f"{ex.get('adaptive_gap_abs')} > tol {cc.TOL_D}")
    rec = make_record(EXPERIMENT, inst, sol, market=market, regime="dictator",
                      extra={"tag": tag,
                             "cell": [cell["setting"], cell["seed"],
                                      cell["n_trips"], cell["b"]],
                             "setting": cell["setting"],
                             "selection_artifact_sha256":
                                 run["manifest"]["selection_artifact_sha256"]})
    if rec["replay_ok"] is False:
        raise cc.B3ConfirmationError(
            f"dictator replay invalid: {rec['replay_violations']}")
    d_state = {"identity": d_identity, "z_d_ub": sol.obj_true,
               "z_d_lb": adaptive_lb, "tol_d": cc.TOL_D, "adaptive": ex,
               "status": sol.stats.status, "bound": sol.stats.bound,
               "record": rec}
    checkpoint.save(d_path, d_state)
    _materialize_dictator(d_state, d_jsonl)
    return d_state


def run_cell(cell, args, run):
    tag = cell["tag"]
    out = os.path.join(args.out, tag)
    os.makedirs(out, exist_ok=True)
    kw = dict(max_mip_gap=args.mip_gap, time_limit_s=None)

    inst = cc.make_cell_instance(cell)
    market = make_affine_market(inst, shape="duck", b_scale=cell["b"])
    mhash = market_hash(market)
    manifest = run["manifest"]
    expected_market = cc.market_hash_by_cell(manifest).get(
        (cell["setting"], cell["seed"], cell["n_trips"], cell["b"]))
    if mhash != expected_market:
        raise cc.B3ConfirmationError(
            f"{tag}: market hash != run manifest (factor/generator drift)")

    identity = cc.cell_identity(
        cell, manifest, market_hash=mhash, instance_hash=inst.hash(),
        run_manifest_sha256=run["sha256"],
        run_commit=manifest["run_commit"],
        selection_artifact_sha256=manifest["selection_artifact_sha256"],
        mip_gap=args.mip_gap, backend_name=backend())
    cc.verify_or_write_cell_identity(out, identity)

    d_state = _dictator_stage(inst, market, out, tag, cell, kw, run)
    state = certified_cg(
        inst, market, epsilon=cc.EPSILON, budget=cc.BUDGET,
        out_dir=out, tag="a2", experiment=EXPERIMENT, solver_kw=kw,
        z_d_ub=d_state["z_d_ub"], tol_d=d_state["tol_d"], method=cc.METHOD)
    oc = state["outcome"]
    print(f"[done] {tag}: {oc['type']} gap={oc['gap']:.6f} "
          f"oracle_calls={state['oracle_calls']} columns={len(state['columns'])} "
          f"uplift={oc.get('uplift_interval')}")


def _preflight(selection, factor):
    """Binding + count + refusal preflight; no solve, no run-dir read."""
    cells = cc.build_cells(factor)
    if len(cells) != cc.N_CELLS:
        raise cc.B3ConfirmationError(
            f"enumerated {len(cells)} cells, expected {cc.N_CELLS}")
    seen = set()
    for cell in cells:
        cc.assert_confirmation_seed(cell["seed"])
        cc.assert_method_a2(cc.METHOD)
        cc.assert_no_a6(cell["setting"], cell["tag"])
        if cell["tag"] in seen:
            raise cc.B3ConfirmationError(f"duplicate cell tag {cell['tag']}")
        seen.add(cell["tag"])
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selection-artifact", dest="selection_artifact",
                    required=True,
                    help="committed GO SELECTION.json (structural gate)")
    ap.add_argument("--out", default="runs/b3_confirmation")
    ap.add_argument("--mip-gap", dest="mip_gap", type=float, default=1e-6)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--emit-run-manifest", action="store_true")
    ap.add_argument("--bind-job", default=None)
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    # outcome blindness + boundary refusals apply to every path
    cc.refuse_pilot_runs_path(args.out, args.selection_artifact)
    cc.assert_no_a6(args.out, args.selection_artifact)

    # STRUCTURAL GO GATE — no bypass; enforced in every mode
    selection = cc.load_selection_artifact(args.selection_artifact)
    factor = selection["selected_factor"]

    if args.list:
        for k, c in enumerate(cc.build_cells(factor)):
            print(k, {"setting": c["setting"], "seed": c["seed"],
                      "n_trips": c["n_trips"], "b": c["b"],
                      "battery_kwh": c["battery_kwh"],
                      "charge_power_kw": c["charge_power_kw"],
                      "method": cc.METHOD, "epsilon": cc.EPSILON,
                      "budget": cc.BUDGET})
        print(f"total: {len(cc.build_cells(factor))} cells")
        return

    if args.bind_job is not None:
        print(f"JOB_BOUND={cc.bind_job_id(args.out, args.bind_job)}")
        return

    if args.emit_run_manifest:
        cc.assert_clean_tracked_tree()
        cc.assert_grb_backend()
        cc.assert_fresh_run_dir(args.out)
        _preflight(selection, factor)
        manifest = cc.build_run_manifest(
            factor, selection, git_commit=cc.git_head_commit(),
            backend_name=backend(), mip_gap=args.mip_gap)
        path = cc.write_run_manifest(args.out, manifest)
        print(f"RUN_MANIFEST={path}")
        print(f"RUN_MANIFEST_SHA256={cc.run_manifest_sha256(manifest)}")
        print(f"RUN_COMMIT={manifest['run_commit']}")
        print(f"SELECTION_ARTIFACT_SHA256={selection['sha256']}")
        print(f"SELECTED_FACTOR={factor}")
        return

    if args.dry_run:
        _preflight(selection, factor)
        # recompute the manifest (hash invariants) but write nothing
        manifest = cc.build_run_manifest(
            factor, selection, git_commit=cc.git_head_commit(),
            backend_name="GRB", mip_gap=args.mip_gap)
        try:
            cc.assert_grb_backend()
            grb = "GRB (ok)"
        except cc.B3ConfirmationError as exc:
            grb = f"NON-GRB — solves would refuse: {exc}"
        print(f"[dry-run] selected_factor={factor} "
              f"selection_sha={selection['sha256'][:16]} cells={cc.N_CELLS} "
              f"contrasts={cc.N_MATCHED_CONTRASTS}")
        print(f"[dry-run] manifest_sha={cc.run_manifest_sha256(manifest)[:16]} "
              f"instances={len(manifest['instance_hashes'])}")
        print(f"[dry-run] backend: {grb}")
        print("[dry-run] OK — GO-gated; nothing launched; pilot outcomes "
              "never read")
        return

    if args.cell is None and not args.all:
        ap.error("choose --list, --dry-run, --emit-run-manifest, --bind-job, "
                 "--cell K, or --all")

    # execution path: hard refusals before any solve
    cc.assert_clean_tracked_tree()
    cc.assert_grb_backend()
    cells = _preflight(selection, factor)
    run = cc.load_run_manifest(args.out)
    if run["manifest"]["run_commit"] != cc.git_head_commit():
        raise cc.B3ConfirmationError(
            "run manifest commit != current HEAD; refusing to execute a cell "
            "under a different code commit than the manifest was emitted for")
    if run["manifest"]["selection_artifact_sha256"] != selection["sha256"]:
        raise cc.B3ConfirmationError(
            "run manifest selection-artifact SHA != the supplied selection "
            "artifact; refusing")
    if run["manifest"]["selected_factor"] != factor:
        raise cc.B3ConfirmationError(
            "run manifest selected factor != selection artifact factor")
    # CRITICAL 3: worker self-defense — prove this task belongs to the bound,
    # released array before producing any evidence (a directly-submitted or
    # stale array, or a manual run, refuses here without writing anything)
    cc.assert_worker_authorized(args.out, run)

    if args.cell is not None:
        if not (0 <= args.cell < len(cells)):
            ap.error(f"--cell must be in [0, {len(cells)})")
        run_cell(cells[args.cell], args, run)
    else:
        for c in cells:
            run_cell(c, args, run)


if __name__ == "__main__":
    main()
