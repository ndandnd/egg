"""Focused regression battery for the frozen A6 holdout closeout."""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

from egglab import checkpoint
from egglab.a6 import (A6_K_MAX, A6_PRIORITY, A6_THETA_CERT_MULT,
                       A6_SCHEMA_VERSION, DEFAULT_CANDIDATE,
                       certified_cg_a6)
from egglab.b2a2 import (MAX_DUPLICATE_RETRIES, MAX_PRICING_ESCALATIONS,
                         PWL_TOL, RC_TOL, SCHEMA_VERSION,
                         canonicalize_pricing_solution, column_from_solution,
                         column_key, market_hash)
from egglab.b2a345 import initial_stab_state, stab_identity_params, theta_cert
from egglab.evsp import (LOAD_RECONSTRUCTION_POLICY_VERSION,
                         REPLAY_POLICY_VERSION, REPLAY_TOL_KWH, Solution)
from egglab.instance import synthetic_instance
from egglab.market import AffineMarket, make_affine_market
from egglab.records import make_record
from egglab.regimes import solve_taker
import experiments.analyze_a6_holdout as mod
import experiments.run_a6_holdout as holdout_driver
from experiments.analyze_a6_holdout import (
    A6_METHOD,
    BUDGET,
    BUDGET_EXHAUSTED_SCORE,
    EXPECTED_SELECTION_COMMIT,
    EXPECTED_SELECTION_SHA256,
    HOLDOUT_INSTANCES,
    METHODS,
    AnalysisError,
    analyze,
    assert_frozen_grid,
    classify_decision,
    exact_sign_test_p,
    score_outcome,
    validate_launch_provenance,
    validate_selection,
    validate_preflight,
)
from experiments.analyze_b2_pilot import sha256_file


MINI_INSTANCES = ((1, 4, 0.01), (3, 4, 0.05))
RUN_COMMIT = "abcdef0" + "0" * 33
SOLVER_IDENTITY = {
    "backend": "GRB", "max_mip_gap": 1e-6, "time_limit_s": None}


def fix_builder(seed, n_trips):
    return synthetic_instance(seed=seed, n_trips=n_trips, max_vehicles=2)


def selection_block():
    return {
        "path": "result/a6_pilot/20260819T005514Z/SELECTION.json",
        "sha256": EXPECTED_SELECTION_SHA256,
        "artifact_commit": EXPECTED_SELECTION_COMMIT,
        "analysis_code_commit":
            "c663fcf5b7a142db595738c8b20bb83549f1ab99",
        "analysis_code_verified": True,
        "selected_arm": A6_METHOD,
        "schema": "a6-arm-selection-v1",
        "a6_a3_wins": 2,
        "n_instances": 12,
        "win_threshold": 9,
    }


def _dump_jsonl(path: Path, rows: list) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _load_evidence(n_slots):
    return {
        "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
        "tolerance_kwh": REPLAY_TOL_KWH,
        "max_abs_residual_kwh": 0.0,
        "max_abs_residual_slot": 0,
        "raw_min_kwh": 0.0,
        "physical_min_kwh": 0.0,
        "raw_load_kwh": [0.0] * n_slots,
        "residual_kwh": [0.0] * n_slots,
    }


def _schedule_payload(inst):
    pairs = holdout_driver.constructive_zero_charge_cover(inst)
    sequences = [list(pair["trip_ids"]) for pair in pairs]
    arc_kinds = [[pair["arc_kind"]] for pair in pairs]
    trip_map = {trip.id: trip for trip in inst.trips}
    deadhead = 0.0
    for sequence, kinds in zip(sequences, arc_kinds):
        first, last = trip_map[sequence[0]], trip_map[sequence[-1]]
        deadhead += inst.dhm(inst.depot, first.start_loc)
        for k, kind in enumerate(kinds):
            left, right = trip_map[sequence[k]], trip_map[sequence[k + 1]]
            if kind == "dir":
                deadhead += inst.dhm(left.end_loc, right.start_loc)
            else:
                deadhead += inst.dhm(left.end_loc, inst.depot)
                deadhead += inst.dhm(inst.depot, right.start_loc)
        deadhead += inst.dhm(last.end_loc, inst.depot)
    ops_cost = (
        inst.vehicle_fixed_cost * len(sequences)
        + inst.dh_cost_per_min * deadhead
    )
    sol = Solution(
        sequences=sequences, arc_kinds=arc_kinds, charges=[],
        load=[0.0] * inst.n_slots, fleet=len(sequences),
    )
    return {
        "sequences": sequences,
        "arc_kinds": arc_kinds,
        "charges": [],
        "load": [0.0] * inst.n_slots,
        "fleet": len(sequences),
        "dh_min_total": deadhead,
        "energy_charged_kwh": 0.0,
        "ops_cost": ops_cost,
        "schedule_hash": sol.schedule_hash(),
        "load_hash": sol.load_hash(),
    }


def _write_launch_records(root: Path, preflight: dict,
                          instances=MINI_INSTANCES) -> None:
    lock = root / "SUBMISSION_LOCK"
    lock.mkdir()
    grid_sha = mod.canonical_grid_list_sha256(
        preflight["selection"], instances)
    n_instances = len(instances)
    n_cells = 2 * n_instances
    physical = len({(s, n) for s, n, _b in instances})
    (lock / "CLAIM.txt").write_text(
        "status=claimed-before-preflight\n"
        f"git_commit={RUN_COMMIT}\n"
        f"selection_sha256={EXPECTED_SELECTION_SHA256}\n"
        "claimed_utc=2026-08-19T01:00:00Z\n")
    (lock / "INTENT.txt").write_text(
        "status=prepared\n"
        f"git_commit={RUN_COMMIT}\n"
        f"grid_list_sha256={grid_sha}\n"
        f"selection_sha256={EXPECTED_SELECTION_SHA256}\n"
        f"preflight_sha256={preflight['sha256']}\n"
        "prepared_utc=2026-08-19T01:01:00Z\n")
    (lock / "SUBMITTED.txt").write_text(
        "status=submitted\n"
        "job_id=424242\n"
        "submitted_utc=2026-08-19T01:02:00Z\n")
    seeds = sorted({s for s, _n, _b in instances})
    seed_text = (f"{seeds[0]}-{seeds[-1]}"
                 if seeds == list(range(seeds[0], seeds[-1] + 1))
                 else "{" + ",".join(str(v) for v in seeds) + "}")
    ns = ",".join(str(v) for v in sorted({n for _s, n, _b in instances}))
    bs = ",".join(f"{v:g}" for v in sorted(
        {b for _s, _n, b in instances}))
    manifest = root / "MANIFEST-20260819T010300Z.txt"
    manifest.write_text(
        "campaign=a6-holdout (spec doc/A6_SPARSE_STABILIZATION_SPEC.md "
        "Section 6)\n"
        f"cells={n_cells} (verified: {n_instances} a2 + {n_instances} "
        "a6_a4; a6_a3 forbidden)\n"
        f"grid=seeds {seed_text} x n{{{ns}}} x b{{{bs}}}; "
        f"{n_instances} matched instances\n"
        f"grid_list_sha256={grid_sha}\n"
        f"array=0-{n_cells - 1}%12\n"
        "epsilon=1e-2; budget=240 exact oracle calls; budget exhaustion "
        "is valid and scores 241\n"
        f"audit=--expect-cg {n_cells} --expect-cg-method a2={n_instances} "
        f"--expect-cg-method a6_a4={n_instances} "
        "(NO certification-count gate)\n"
        "selection_path=result/a6_pilot/20260819T005514Z/SELECTION.json\n"
        f"selection_sha256={EXPECTED_SELECTION_SHA256}\n"
        f"selection_gate_commit={EXPECTED_SELECTION_COMMIT} "
        "(verified ancestor)\n"
        "preflight_path=runs/a6_holdout/PREFLIGHT.json\n"
        f"preflight_sha256={preflight['sha256']}\n"
        "submission_sentinel=runs/a6_holdout/SUBMISSION_LOCK "
        "(persistent; deletion requires audit/review)\n"
        f"feasibility={physical}/{physical} physical instances have exact "
        f"zero-charge covers; {n_instances} market hashes recorded before "
        "sbatch\n"
        "job_id=424242\n"
        f"git_commit={RUN_COMMIT}\n"
        "submitted_utc=2026-08-19T01:04:00Z\n")


def _event(*, method, inst, regime, call_id, trigger=False, prices=None):
    full_prices = ([0.0] * inst.n_slots if prices is None else
                   [float(value) for value in prices])
    extra = {"tag": method, "call_id": call_id}
    if trigger:
        extra.update(call_kind="clean", trigger_selected="T4",
                     triggers_fired=["T4"])
    schedule = _schedule_payload(inst)
    ops_cost = schedule["ops_cost"]
    if regime != "cg-seed":
        extra.update(
            column_key=column_key(schedule), column_novel=False,
            min_reduced_cost_ub=-0.005,
            min_reduced_cost_lb=-0.005,
        )
    return {
        "experiment": "a6-holdout", "regime": regime,
        "git_commit": RUN_COMMIT[:7], "mip_version": "1.17.6",
        "instance_name": inst.name, "instance_hash": inst.hash(),
        "n_trips": len(inst.trips), "max_vehicles": inst.max_vehicles,
        "prices": [round(value, 6) for value in full_prices],
        **schedule,
        "obj_model": ops_cost, "obj_true": ops_cost,
        "energy_cost_model": 0.0,
        "oracle_tier": "exact-milp",
        "replay_ok": True, "replay_violations": [],
        "replay_policy_version": REPLAY_POLICY_VERSION,
        "replay_tol_kwh": REPLAY_TOL_KWH,
        "extra": extra,
        "solver": {"backend": "GRB", "status": "OPTIMAL",
                   "obj": ops_cost, "bound": ops_cost, "mip_gap": 0.0,
                   "wall_s": 0.1, "lp_wall_s": 0.0,
                   "extra": {
                       "load_reconstruction": _load_evidence(inst.n_slots),
                       "pricing_objective_reconstruction": {
                           "policy_version":
                               LOAD_RECONSTRUCTION_POLICY_VERSION,
                           "prices": full_prices,
                           "model_obj": ops_cost,
                           "physical_obj": ops_cost,
                           "abs_adjustment": 0.0,
                       },
                   }},
    }


def _write_cell(root: Path, method: str, seed: int, n: int, b: float,
                cell_index: int, preflight: dict, calls: int) -> None:
    inst = fix_builder(seed, n)
    market = make_affine_market(inst, shape="duck", b_scale=b)
    dirname = f"{method}_s{seed}_n{n}_b{b:g}"
    d = root / dirname
    d.mkdir(parents=True)
    schedule = _schedule_payload(inst)
    ub = schedule["ops_cost"]
    # producer arithmetic: recorded fields DERIVE from (bound, sigma, z)
    # so the strict recovery replay's exact-equality checks hold
    sigma = ub
    bound = ub - 0.0005
    rc_lb = bound - sigma
    lb = ub + min(0.0, rc_lb)
    pricing_gap = ub - lb
    zd = ub
    identity = {
        "schema_version": SCHEMA_VERSION if method == "a2" else A6_SCHEMA_VERSION,
        "instance_hash": inst.hash(), "market_hash": market_hash(market),
        "epsilon": 0.01, "budget": 240, "pwl_tol": PWL_TOL,
        "rc_tol": RC_TOL, "solver": SOLVER_IDENTITY,
        "tol_d": 0.01, "z_d_ub": zd,
        "load_reconstruction": {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "tolerance_kwh": REPLAY_TOL_KWH,
        },
    }
    if method == A6_METHOD:
        identity.update(
            method=A6_METHOD,
            scheduler={
                "theta_cert_mult": A6_THETA_CERT_MULT,
                "theta_cert": A6_THETA_CERT_MULT * 0.01,
                "k_max": A6_K_MAX,
                "priority": list(A6_PRIORITY) + [DEFAULT_CANDIDATE],
            },
            recovery={
                "max_pricing_escalations": MAX_PRICING_ESCALATIONS,
                "max_duplicate_retries": MAX_DUPLICATE_RETRIES,
                "gap_divisor": 100.0, "gap_floor": 1e-12,
            },
            stab=stab_identity_params("a4"),
        )
    seed_event = _event(method=method, inst=inst,
                        regime="cg-seed", call_id=f"{method}-oc0",
                        prices=market.price(np.zeros(inst.n_slots)))
    clean_event = _event(
        method=method, inst=inst,
        regime="cg-pricing",
        call_id=f"{method}-oc1", trigger=method == A6_METHOD)
    clean_event["solver"]["bound"] = bound
    clean_event["extra"]["min_reduced_cost_ub"] = 0.0
    clean_event["extra"]["min_reduced_cost_lb"] = rc_lb
    for event in (seed_event, clean_event):
        event.update(
            slurm_job_id="424242",
            slurm_array_task_id=str(cell_index),
            slurm_restart_count="0",
        )
    iteration = {
        "record_kind": "cg-iteration", "phase": "clean",
        "method": method, "iteration_id": f"{method}-it1",
        "experiment": "a6-holdout", "git_commit": RUN_COMMIT[:7],
        "mip_version": "1.17.6", "terminal": False,
        "oracle_calls": 1, "pricing_solve_id": f"{method}-oc1",
        "n_columns": 1, "z_rmp_model": ub, "ub_ch": ub,
        "duals_sigma": sigma,
        "min_reduced_cost_ub": 0.0,
        "min_reduced_cost_lb": rc_lb,
        "pricing_gap_abs": pricing_gap,
        "lb_ch": lb, "lb_best": lb, "certificate_gap": ub - lb,
        "epsilon": 0.01, "pwl_tol": PWL_TOL, "rc_tol": RC_TOL,
        "n_tangent_refinements": 0,
        "column_key": clean_event["extra"]["column_key"],
        "column_novel": False,
        "master_solves": [{
            "solve_id": f"{method}-it1-rmp-r0", "backend": "GRB",
            "status": "OPTIMAL", "obj": ub, "bound": ub,
            "wall_s": 0.2, "n_int": 0,
        }],
        "slurm_job_id": "424242",
        "slurm_array_task_id": str(cell_index),
        "slurm_restart_count": "0",
    }
    if method == A6_METHOD:
        iteration.update(
            gap_at_decision=float("inf"), k_since_clean=0,
            recovery_active=False, recovery_kind=None,
            triggers_fired=["T4"], trigger_selected="T4",
            call_kind="clean", column_novel=False,
            min_reduced_cost_ub=0.0,
            pricing_max_mip_gap=SOLVER_IDENTITY.get(
                "max_mip_gap", 1e-6))
    broadcast_tv, broadcast_linf, broadcast_points = mod._price_path_metrics(
        [seed_event, clean_event],
        ("cg-seed", "cg-pricing", "cg-stab-pricing"),
    )
    outcome = {
        "type": "certified", "ub_ch": ub, "lb_best": lb,
        "gap": ub - lb, "certified": True, "oracle_calls": calls,
        "oracle_calls_clean": calls, "oracle_calls_stab": 0,
        "broadcast_tv": broadcast_tv,
        "broadcast_linf_max": broadcast_linf,
        "broadcast_points": broadcast_points,
        "uplift_interval": [(zd - 0.01) - ub, zd - lb],
    }
    if method == A6_METHOD:
        outcome["method"] = method
        outcome["trigger_selected_counts"] = {"T4": 1}
        outcome["recovery_active_at_end"] = False
    ck = {
        "identity": identity, "done": True, "outcome": outcome,
        "oracle_calls": calls, "calls_clean": calls, "calls_stab": 0,
        "lb_best": lb, "ub_history": [ub], "lb_history": [lb],
        "oracle_events": [seed_event, clean_event],
        "iteration_events": [iteration],
    }
    if method == A6_METHOD:
        # complete producer state so the shared recovery replay
        # (experiments/a6_replay.py) verifies these synthetic cells
        ck.update(
            duplicate_retries=0, refine_retries=0, pricing_escalations=0,
            pricing_max_mip_gap=SOLVER_IDENTITY.get("max_mip_gap", 1e-6),
            scheduler={"k_since_clean": 0, "n_clean_pricing": 1,
                       "last_candidate_novel": None, "recovery": None},
        )
    column = {
        key: copy.deepcopy(schedule[key])
        for key in ("sequences", "arc_kinds", "charges", "load", "fleet",
                    "ops_cost", "schedule_hash", "load_hash")
    }
    column.update(
        instance_hash=inst.hash(), replay_ok=True, replay_violations=[],
        oracle_stats=copy.deepcopy(seed_event["solver"]),
    )
    column["column_key"] = column_key(column)
    ck["columns"] = [column]
    ck["keys"] = [column["column_key"]]
    if method == A6_METHOD:
        stab_state = initial_stab_state("a4", market)
        stab_state["theta_best"] = theta_cert(
            market,
            clean_event["solver"]["extra"][
                "pricing_objective_reconstruction"]["prices"],
            clean_event["solver"]["bound"],
        )
        ck["stab"] = stab_state
    checkpoint.save(str(d / f"{method}.cg.ckpt.json"), ck)
    _dump_jsonl(d / f"{method}.oracle.jsonl", ck["oracle_events"])
    _dump_jsonl(d / f"{method}.iterations.jsonl", ck["iteration_events"])

    dictator_extra = {
        "load_reconstruction": _load_evidence(inst.n_slots),
        "adaptive_rounds": 1,
        "adaptive_lb": lb,
        "adaptive_model_obj": zd,
        "adaptive_ub": zd,
        "adaptive_gap_abs": zd - lb,
        "adaptive_tol_abs": 0.01,
        "adaptive_converged": True,
        "adaptive_total_wall_s": 0.5,
        "adaptive_solve_stats": [{
            "round": 1, "status": "OPTIMAL", "incumbent": zd,
            "bound": lb, "gap": zd - lb, "n_vars": 1, "n_int": 1,
            "n_constrs": 1, "wall_s": 0.3, "backend": "GRB",
            "threads": 4,
        }],
        "dictator_objective_reconstruction": {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "raw_true_obj": zd,
            "physical_obj": zd,
            "abs_adjustment": 0.0,
        },
    }
    drec = {
        "experiment": "a6-holdout", "regime": "dictator",
        "git_commit": RUN_COMMIT[:7], "mip_version": "1.17.6",
        "instance_name": inst.name, "instance_hash": inst.hash(),
        "n_trips": len(inst.trips), "max_vehicles": inst.max_vehicles,
        **copy.deepcopy(schedule),
        "obj_model": zd, "obj_true": zd,
        "energy_cost_model": 0.0,
        "oracle_tier": "exact-milp/dictator-adaptive",
        "replay_ok": True, "replay_violations": [],
        "replay_policy_version": REPLAY_POLICY_VERSION,
        "replay_tol_kwh": REPLAY_TOL_KWH,
        "slurm_job_id": "424242",
        "slurm_array_task_id": str(cell_index),
        "slurm_restart_count": "0",
        "solver": {"backend": "GRB", "status": "OPTIMAL",
                   "wall_s": 0.3, "lp_wall_s": 0.0,
                   "extra": copy.deepcopy(dictator_extra)},
        "extra": {"tag": dirname, "cell": [method, seed, n, b]},
    }
    dck = {
        "identity": {
            "schema_version": SCHEMA_VERSION,
            "instance_hash": inst.hash(),
            "market_hash": market_hash(market),
            "tol_d": 0.01,
            "solver": SOLVER_IDENTITY,
            "load_reconstruction": {
                "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
                "tolerance_kwh": REPLAY_TOL_KWH,
            },
        },
        "z_d_ub": zd, "tol_d": 0.01, "status": "OPTIMAL",
        "bound": lb,
        "adaptive": copy.deepcopy(dictator_extra),
        "record": drec,
    }
    checkpoint.save(str(d / "dictator.ckpt.json"), dck)
    _dump_jsonl(d / "dictator.jsonl", [drec])
    provenance = {
        "schema": "a6-holdout-cell-provenance-v1",
        "campaign": "a6-holdout", "code_commit": RUN_COMMIT,
        "cell_index": cell_index,
        "cell": {"method": method, "seed": seed, "n_trips": n, "b": b},
        "instance_hash": inst.hash(), "market_hash": market_hash(market),
        "selection": preflight["selection"],
        "preflight_path": "PREFLIGHT.json",
        "preflight_sha256": preflight["sha256"],
    }
    (d / "CELL_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n")


@pytest.fixture(scope="module")
def mini_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("a6_holdout_mini")
    preflight_path = root / "PREFLIGHT.json"
    preflight_path.write_text("{}\n")
    preflight = {
        "path": str(preflight_path.resolve()),
        "sha256": sha256_file(str(preflight_path)),
        "schema": "test-preflight", "code_commit": RUN_COMMIT,
        "physical_instances": 2, "market_instances": 2, "method_cells": 4,
        "selection": selection_block(),
    }
    _write_launch_records(root, preflight)
    cells = [(m, *i) for m in METHODS for i in MINI_INSTANCES]
    for index, (method, seed, n, b) in enumerate(cells):
        _write_cell(root, method, seed, n, b, index, preflight,
                    calls=2)
    return str(root), preflight


@pytest.fixture(scope="module")
def positive_charge_serialized_evidence(tmp_path_factory):
    """Real solver bytes for a burned-seed, holdout-scale charging case."""
    inst = synthetic_instance(seed=29, n_trips=8)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    prices = market.price(np.zeros(market.n_slots))
    sol = solve_taker(
        inst, prices, max_mip_gap=1e-6, time_limit_s=None)
    canonicalize_pricing_solution(inst, sol, prices)
    column = column_from_solution(inst, sol)
    record = make_record(
        "a6-holdout",
        inst,
        sol,
        market=market,
        prices=prices,
        regime="cg-seed",
        extra={"tag": "a2", "call_id": "a2-oc0"},
    )
    path = tmp_path_factory.mktemp(
        "positive_charge_evidence") / "checkpoint.json"
    checkpoint.save(
        str(path), {"columns": [column], "oracle_events": [record]})
    return inst, market, checkpoint.load(str(path))


@pytest.fixture(scope="module")
def a6_a4_candidate_trace(tmp_path_factory):
    """A real producer trace that exercises conditional A4 replay."""
    inst = fix_builder(1, 4)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    out = str(tmp_path_factory.mktemp("a6_a4_candidate_trace"))
    state = certified_cg_a6(
        inst, market, method=A6_METHOD, epsilon=0.01, budget=120,
        out_dir=out, tag=A6_METHOD,
    )
    assert any(
        event.get("call_kind") == "candidate"
        for event in state["iteration_events"]
    )
    return state, market


def _mini_analyze(root, preflight, out_base, stamp="TESTSTAMP"):
    rooted_preflight = dict(preflight)
    rooted_preflight["path"] = str(Path(root, "PREFLIGHT.json").resolve())
    return analyze(
        root, str(out_base), stamp, "analysis0",
        selection_path=mod.DEFAULT_SELECTION,
        instances=MINI_INSTANCES, instance_builder=fix_builder,
        verify_code_commit=False, verify_selection_git=False,
        verify_experiment_commit=False, require_frozen_grid=False,
        preflight_validator=lambda _p, instances: rooted_preflight)


def test_solver_generated_positive_charge_record_round_trips_and_replays(
        positive_charge_serialized_evidence):
    inst, market, restored = positive_charge_serialized_evidence
    column = restored["columns"][0]
    record = restored["oracle_events"][0]
    assert sum(column["load"]) > 0.0
    assert column["charges"]

    column_load, column_raw = mod._validate_physical_load_evidence(
        column,
        n_slots=market.n_slots,
        stats_field="oracle_stats",
        label="positive-charge column",
    )
    mod._validate_schedule_evidence(
        column,
        inst=inst,
        load=column_load,
        label="positive-charge column",
        record=False,
        column=True,
    )
    record_load, record_raw = mod._validate_physical_load_evidence(
        record,
        n_slots=market.n_slots,
        stats_field="solver",
        label="positive-charge record",
    )
    mod._validate_schedule_evidence(
        record,
        inst=inst,
        load=record_load,
        label="positive-charge record",
        record=True,
        column=False,
    )
    assert record_load == pytest.approx(column_load)
    assert record_raw == pytest.approx(column_raw)

    pricing = record["solver"]["extra"][
        "pricing_objective_reconstruction"]
    full_prices = pricing["prices"]
    expected_physical = record["ops_cost"] + sum(
        full_prices[t] * record_load[t] for t in range(market.n_slots))
    expected_model = record["ops_cost"] + sum(
        full_prices[t] * record_raw[t] for t in range(market.n_slots))
    assert record["obj_true"] == pytest.approx(expected_physical)
    assert pricing["physical_obj"] == pytest.approx(expected_physical)
    assert record["obj_model"] == pytest.approx(expected_model)
    assert pricing["model_obj"] == pytest.approx(expected_model)


def test_solver_generated_positive_charge_tamper_is_rejected(
        positive_charge_serialized_evidence):
    _inst, market, restored = positive_charge_serialized_evidence
    record = copy.deepcopy(restored["oracle_events"][0])
    record["charges"][0]["kwh"] += 1.0
    with pytest.raises(AnalysisError, match="summed charge events"):
        mod._validate_physical_load_evidence(
            record,
            n_slots=market.n_slots,
            stats_field="solver",
            label="tampered positive-charge record",
        )


def test_real_a6_a4_candidate_mechanism_trace_replays(
        a6_a4_candidate_trace):
    state, market = a6_a4_candidate_trace
    mod._replay_a6_a4_mechanism(state, market, "real A6-A4 trace")


def test_real_producer_retained_prefixes_have_independent_master_bounds(
        a6_a4_candidate_trace):
    state, market = a6_a4_candidate_trace
    for count in range(1, len(state["columns"]) + 1):
        bounds = mod._independent_master_bounds(
            state["columns"][:count], market,
            label=f"real A6-A4 retained prefix {count}")
        assert bounds["fw_gap"] <= mod.MASTER_FW_TOL + 1e-7
        assert bounds["lower_bound"] <= bounds["upper_bound"] + 1e-9


def test_coordinated_a6_a4_serious_counter_story_is_rejected(
        a6_a4_candidate_trace):
    original, market = a6_a4_candidate_trace
    state = copy.deepcopy(original)
    candidate = next(
        event for event in state["iteration_events"]
        if event.get("call_kind") == "candidate"
    )
    old = candidate["serious_step"]
    candidate["serious_step"] = not old
    if old:
        state["stab"]["serious_steps"] -= 1
        state["stab"]["null_steps"] += 1
    else:
        state["stab"]["null_steps"] -= 1
        state["stab"]["serious_steps"] += 1
    with pytest.raises(AnalysisError, match="serious/null classification"):
        mod._replay_a6_a4_mechanism(
            state, market, "tampered A6-A4 trace")


def test_independent_master_bounds_close_on_interior_convex_combination():
    market = AffineMarket(a=[0.0], b=[1.0], base_load=[0.0])
    columns = [
        {"ops_cost": 10.0, "load": [0.0]},
        {"ops_cost": 0.0, "load": [10.0]},
        {"ops_cost": 3.0, "load": [4.0]},
    ]
    bounds = mod._independent_master_bounds(
        columns, market, label="interior master")
    assert bounds["fw_gap"] <= mod.MASTER_FW_TOL + 1e-8
    assert bounds["lower_bound"] <= bounds["upper_bound"]
    # The optimum is genuinely fractional rather than a selected vertex.
    vertex_values = [
        column["ops_cost"] + market.system_cost_delta(column["load"])
        for column in columns
    ]
    assert bounds["upper_bound"] < min(vertex_values)


def test_multi_column_terminal_ub_is_bounded_independently():
    market = mod.make_affine_market(
        fix_builder(1, 4), shape="duck", b_scale=0.01)
    n_slots = market.n_slots
    columns = [
        {"ops_cost": 10.0, "load": [0.0] * n_slots},
        {"ops_cost": 0.0, "load": [10.0] + [0.0] * (n_slots - 1)},
    ]
    checkpoint_story = {
        "columns": columns,
        "oracle_events": [
            {},
            {"solver": {
                "bound": 10.0,
                "extra": {"pricing_objective_reconstruction": {
                    "prices": [0.0] * n_slots,
                }},
            }},
        ],
        "iteration_events": [
            {
                "terminal": False,
                "phase": "clean",
                "oracle_calls": 1,
                "n_columns": 1,
                "ub_ch": 10.0,
                "z_rmp_model": 10.0,
                "duals_sigma": 10.0,
                "lb_ch": 10.0,
                "certificate_gap": 1.0,
                "column_novel": True,
            },
            {
                "terminal": True,
                "n_columns": 2,
                "ub_ch": -1.0,
                "z_rmp_model": -1.0,
                "lb_best": 0.0,
                "certificate_gap": 1.0,
            },
        ],
    }
    certificate = {
        "outcome_type": "budget_exhausted",
        "first_certificate_call": None,
    }
    with pytest.raises(
            AnalysisError, match="below the independently bounded"):
        mod._validate_clean_bound_safety(
            checkpoint_story, market, "forged multi-column", certificate)


# -------------------------------------------------------------------------
# Exact decision partition and boundaries
# -------------------------------------------------------------------------
@pytest.mark.parametrize("ratio,wins,cell", [
    (0.80, 31, "clear-kill"),
    (0.80, 35, "discordant"),
    (0.80, 39, "adopt"),
    (0.90, 31, "clear-kill"),
    (0.90, 35, "gray"),
    (0.90, 39, "discordant"),
    (1.10, 31, "clear-kill"),
    (1.10, 35, "clear-kill"),
    (1.10, 39, "clear-kill"),
])
def test_exhaustive_nine_cell_partition(ratio, wins, cell):
    got = classify_decision(a6_certified=64, a2_certified=64,
                            ratio=ratio, wins=wins)
    assert got["decision_cell"] == cell


@pytest.mark.parametrize("ratio,wins,cell", [
    (0.85, 38, "adopt"), (0.85, 37, "discordant"),
    (1.00, 38, "clear-kill"), (0.999999, 38, "discordant"),
    (0.90, 32, "clear-kill"), (0.90, 33, "gray"),
    (0.90, 37, "gray"), (0.90, 38, "discordant"),
])
def test_partition_boundary_equalities(ratio, wins, cell):
    assert classify_decision(
        a6_certified=64, a2_certified=64, ratio=ratio,
        wins=wins)["decision_cell"] == cell


@pytest.mark.parametrize("a6_cert,a2_cert", [(60, 0), (63, 64)])
def test_certification_gate_has_absolute_precedence(a6_cert, a2_cert):
    got = classify_decision(a6_certified=a6_cert, a2_certified=a2_cert,
                            ratio=0.1, wins=64)
    assert got["decision_cell"] == "certification-shortfall"


def test_sign_test_is_exact_two_sided_and_ties_excluded():
    assert exact_sign_test_p(0, 0) == 1.0
    assert exact_sign_test_p(5, 5) == 1.0
    assert exact_sign_test_p(10, 0) == pytest.approx(2 / 2**10)


# -------------------------------------------------------------------------
# Scoring and frozen inputs
# -------------------------------------------------------------------------
def _score_ck(kind, certified, calls, gap):
    tag = "a2"
    ub = 10.0
    events = [{
        "regime": "cg-seed",
        "extra": {"tag": tag, "call_id": f"{tag}-oc0"},
    }]
    iterations = []
    ub_history = []
    lb_history = []
    lb_best = -float("inf")
    for oracle_call in range(1, calls):
        final_clean_certificate = (
            kind == "certified" and oracle_call == calls - 1)
        iter_gap = gap if final_clean_certificate else 0.02
        pricing_bound = ub
        sigma = pricing_bound + iter_gap
        min_rc = pricing_bound - sigma
        lb_ch = ub + min(0.0, min_rc)
        lb_best = max(lb_best, lb_ch)
        call_id = f"{tag}-oc{oracle_call}"
        events.append({
            "regime": "cg-pricing", "obj_true": ub,
            "solver": {"obj": ub, "bound": pricing_bound},
            "extra": {
                "tag": tag, "call_id": call_id,
                "column_key": "k", "column_novel": False,
                "min_reduced_cost_ub": min_rc,
                "min_reduced_cost_lb": min_rc,
            },
        })
        iterations.append({
            "phase": "clean", "oracle_calls": oracle_call,
            "pricing_solve_id": call_id,
            "z_rmp_model": ub, "ub_ch": ub,
            "duals_sigma": sigma,
            "min_reduced_cost_ub": min_rc,
            "min_reduced_cost_lb": min_rc,
            "pricing_gap_abs": 0.0,
            "lb_ch": lb_ch, "lb_best": lb_best,
            "certificate_gap": ub - lb_best,
            "column_key": "k", "column_novel": False,
            "n_tangent_refinements": 0,
            "master_solves": [{
                "solve_id": f"{tag}-it{oracle_call}-rmp-r0",
                "backend": "GRB", "status": "OPTIMAL",
                "obj": ub, "bound": ub, "n_int": 0,
            }],
        })
        ub_history.append(ub)
        lb_history.append(lb_best)
    if kind == "budget_exhausted":
        terminal_ub = lb_best + gap
        iterations.append({
            "terminal": True, "phase": "terminal",
            "iteration_id": f"{tag}-it{calls}-terminal",
            "oracle_calls": calls, "pricing_solve_id": None,
            "z_rmp_model": terminal_ub, "ub_ch": terminal_ub,
            "lb_best": lb_best, "certificate_gap": gap,
            "n_tangent_refinements": 0,
            "master_solves": [{
                "solve_id": f"{tag}-it{calls}-rmp-r0",
                "backend": "GRB", "status": "OPTIMAL",
                "obj": terminal_ub, "bound": terminal_ub, "n_int": 0,
            }],
        })
        ub_history.append(terminal_ub)
        lb_history.append(lb_best)
        ub = terminal_ub
    return {
        "done": True,
        "oracle_calls": calls,
        "identity": {"epsilon": 0.01, "budget": BUDGET},
        "oracle_events": events,
        "iteration_events": iterations,
        "ub_history": ub_history,
        "lb_history": lb_history,
        "lb_best": lb_best,
        "outcome": {
            "type": kind, "certified": certified,
            "oracle_calls": calls, "ub_ch": ub,
            "lb_best": lb_best, "gap": gap,
        },
    }


def test_scoring_including_terminal_budget_certificate():
    assert score_outcome(_score_ck("certified", True, 17, 0.001), "x") == 17
    assert score_outcome(
        _score_ck("budget_exhausted", True, 240, 0.001), "x") == 240
    assert score_outcome(
        _score_ck("budget_exhausted", False, 240, 0.02), "x") == 241
    with pytest.raises(AnalysisError):
        score_outcome(_score_ck("budget_exhausted", False, 239, 0.02), "x")


def _coherent_a6_score_state():
    """A fully scheduler-coherent synthetic a6 trace accepted end-to-end by
    the analyzer (shared by the candidate-bound test and the coordinated
    recovery-tamper rejections below)."""
    state = _score_ck("certified", True, 4, 0.001)
    state["identity"]["method"] = A6_METHOD
    state["identity"]["rc_tol"] = RC_TOL
    state["identity"]["solver"] = SOLVER_IDENTITY
    state["identity"]["scheduler"] = {
        "theta_cert_mult": A6_THETA_CERT_MULT,
        "theta_cert": A6_THETA_CERT_MULT * 0.01,
        "k_max": A6_K_MAX,
        "priority": list(A6_PRIORITY) + [DEFAULT_CANDIDATE],
    }
    state["identity"]["recovery"] = {
        "max_pricing_escalations": MAX_PRICING_ESCALATIONS,
        "max_duplicate_retries": MAX_DUPLICATE_RETRIES,
        "gap_divisor": 100.0, "gap_floor": 1e-12,
    }
    base_gap = SOLVER_IDENTITY.get("max_mip_gap", 1e-6)
    ub = state["outcome"]["ub_ch"]
    for call, event in enumerate(state["oracle_events"]):
        event["extra"]["tag"] = A6_METHOD
        event["extra"]["call_id"] = f"{A6_METHOD}-oc{call}"

    it1, it2, it3 = state["iteration_events"]
    oc1, oc2, oc3 = state["oracle_events"][1:]
    # all recorded bound/gap fields DERIVE from (bound, sigma, z) with the
    # producer's exact float arithmetic (the strict replay checks equality)
    sigma1, bound1 = ub + 0.2, ub
    rc1 = bound1 - sigma1
    lb1 = ub + min(0.0, rc1)
    # it1: T4 clean, novel improving column -> no recovery
    it1.update(
        pricing_solve_id=f"{A6_METHOD}-oc1", call_kind="clean",
        trigger_selected="T4", triggers_fired=["T4"],
        gap_at_decision=float("inf"), k_since_clean=0, n_columns=1,
        recovery_active=False, recovery_kind=None,
        pricing_max_mip_gap=base_gap,
        duals_sigma=sigma1, min_reduced_cost_ub=rc1,
        min_reduced_cost_lb=rc1, lb_ch=lb1, lb_best=lb1,
        certificate_gap=ub - lb1, column_key="k-novel", column_novel=True)
    it1["master_solves"][0]["solve_id"] = f"{A6_METHOD}-it1-rmp-r0"
    oc1["extra"].update(
        call_kind="clean", trigger_selected="T4", triggers_fired=["T4"],
        min_reduced_cost_ub=rc1, min_reduced_cost_lb=rc1,
        column_key="k-novel", column_novel=True)
    oc1["solver"]["bound"] = bound1
    # it2: default candidate (gap ~0.2 > theta_cert), NON-novel column;
    # its oracle event carries a bound that WOULD certify if misused
    it2.update(
        pricing_solve_id=f"{A6_METHOD}-oc2", phase="stabilized",
        call_kind="candidate", trigger_selected=DEFAULT_CANDIDATE,
        triggers_fired=[], gap_at_decision=ub - lb1, k_since_clean=0,
        n_columns=2, recovery_active=False, recovery_kind=None,
        ub_ch=ub, lb_best=lb1, certificate_gap=ub - lb1,
        column_novel=False, master_solves=[])
    oc2["regime"] = "cg-stab-pricing"
    oc2["extra"].update(
        call_kind="candidate", trigger_selected=DEFAULT_CANDIDATE,
        triggers_fired=[], column_novel=False)
    oc2["solver"]["bound"] = ub  # tempting: gap would be 0 if misused
    # it3: T3 clean (candidate stalled), certifies
    sigma3, bound3 = ub + 0.001, ub
    rc3 = bound3 - sigma3
    lb3 = ub + min(0.0, rc3)
    it3.update(
        pricing_solve_id=f"{A6_METHOD}-oc3", call_kind="clean",
        trigger_selected="T3", triggers_fired=["T3"],
        gap_at_decision=ub - lb1, k_since_clean=1, n_columns=2,
        recovery_active=False, recovery_kind=None,
        pricing_max_mip_gap=base_gap,
        duals_sigma=sigma3, min_reduced_cost_ub=rc3,
        min_reduced_cost_lb=rc3, lb_ch=lb3, lb_best=lb3,
        certificate_gap=ub - lb3, column_novel=False)
    it3["master_solves"][0]["solve_id"] = f"{A6_METHOD}-it3-rmp-r0"
    oc3["extra"].update(
        call_kind="clean", trigger_selected="T3", triggers_fired=["T3"],
        min_reduced_cost_ub=rc3, min_reduced_cost_lb=rc3,
        column_novel=False)
    oc3["solver"]["bound"] = bound3

    state["ub_history"] = [ub, ub, ub]
    state["lb_history"] = [lb1, lb1, lb3]
    state["lb_best"] = lb3
    state["outcome"].update(lb_best=lb3, gap=ub - lb3, method=A6_METHOD,
                            recovery_active_at_end=False)
    state.update(
        duplicate_retries=0, refine_retries=0, pricing_escalations=0,
        pricing_max_mip_gap=base_gap,
        scheduler={"k_since_clean": 0, "n_clean_pricing": 2,
                   "last_candidate_novel": None, "recovery": None})
    return state


def test_scoring_replays_a6_candidate_without_treating_it_as_a_bound():
    """A candidate call carrying a certificate-tempting solver bound must
    not certify; the trace is fully scheduler-coherent so the shared
    recovery replay (experiments/a6_replay.py) accepts it."""
    assert score_outcome(_coherent_a6_score_state(), "a6") == 4


def test_analyzer_rejects_coordinated_recovery_counter_tamper():
    """Coordinated final-state tamper: the checkpoint counter is adjusted
    without any supporting event — the production analyzer must reject it
    through the shared recovery replay."""
    state = copy.deepcopy(_coherent_a6_score_state())
    state["pricing_escalations"] = 1
    with pytest.raises(AnalysisError, match="event stream replays"):
        score_outcome(state, "a6")


def test_analyzer_rejects_falsified_gap_path():
    """Coordinated /100 falsification: recorded per-event pricing gaps and
    the final state agree with EACH OTHER but not with the producer's
    /100 rule — the analyzer must reject via the shared replay."""
    state = copy.deepcopy(_coherent_a6_score_state())
    for event in state["iteration_events"]:
        if event.get("call_kind") == "clean":
            event["pricing_max_mip_gap"] = 1e-7
    state["pricing_max_mip_gap"] = 1e-7
    with pytest.raises(AnalysisError, match="pricing_max_mip_gap"):
        score_outcome(state, "a6")


def test_trace_refuses_to_continue_after_first_certificate():
    state = _score_ck("certified", True, 5, 0.001)
    ub = state["outcome"]["ub_ch"]
    lb = ub - 0.001
    for call, event in enumerate(state["iteration_events"], start=1):
        oracle = state["oracle_events"][call]
        event["duals_sigma"] = ub + 0.001
        event["min_reduced_cost_ub"] = -0.001
        event["min_reduced_cost_lb"] = -0.001
        event["lb_ch"] = lb
        event["lb_best"] = lb
        event["certificate_gap"] = 0.001
        oracle["extra"]["min_reduced_cost_ub"] = -0.001
        oracle["extra"]["min_reduced_cost_lb"] = -0.001
    state["lb_history"] = [lb] * len(state["lb_history"])
    state["lb_best"] = lb
    state["outcome"]["lb_best"] = lb
    with pytest.raises(AnalysisError, match="continues after first certificate"):
        score_outcome(state, "x")


def test_frozen_grid_rejects_missing_extra_duplicate():
    assert_frozen_grid(HOLDOUT_INSTANCES)
    with pytest.raises(AnalysisError, match="64 unique"):
        assert_frozen_grid(HOLDOUT_INSTANCES[:-1])
    bad = list(HOLDOUT_INSTANCES)
    bad[-1] = bad[0]
    with pytest.raises(AnalysisError, match="64 unique"):
        assert_frozen_grid(bad)
    bad = list(HOLDOUT_INSTANCES)
    bad[-1] = (32, 12, 0.05)
    with pytest.raises(AnalysisError, match="grid tampering"):
        assert_frozen_grid(bad)


def test_selection_exact_artifact_and_tampering(tmp_path):
    got = validate_selection(mod.DEFAULT_SELECTION, verify_git=True)
    assert got["sha256"] == EXPECTED_SELECTION_SHA256
    assert got["selection_commit"] == EXPECTED_SELECTION_COMMIT
    bad = tmp_path / "SELECTION.json"
    data = json.loads(Path(mod.DEFAULT_SELECTION).read_text())
    data["selected_arm"] = "a6_a3"
    bad.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AnalysisError):
        validate_selection(bad, verify_git=False)


def test_real_driver_preflight_round_trip_and_tampering(tmp_path):
    selection = holdout_driver.load_committed_selection()
    payload = holdout_driver.build_feasibility_manifest(
        selection, "a" * 40)
    path = tmp_path / "PREFLIGHT.json"
    checkpoint.save(str(path), payload)
    got = validate_preflight(path)
    assert got["physical_instances"] == 32
    assert got["market_instances"] == 64
    assert got["method_cells"] == 128
    assert got["selection"] == selection

    changed = copy.deepcopy(payload)
    changed["physical_instances"][0]["pairs"][0][
        "soc_trace_kwh"][0]["soc_kwh"] += 0.01
    checkpoint.save(str(path), changed)
    with pytest.raises(AnalysisError, match="SOC trace replay"):
        validate_preflight(path)


def test_real_launcher_contract_round_trip(tmp_path):
    selection = holdout_driver.load_committed_selection()
    payload = holdout_driver.build_feasibility_manifest(
        selection, RUN_COMMIT)
    path = tmp_path / "PREFLIGHT.json"
    checkpoint.save(str(path), payload)
    preflight = validate_preflight(path)
    _write_launch_records(tmp_path, preflight, HOLDOUT_INSTANCES)
    selection_summary = validate_selection(
        mod.DEFAULT_SELECTION, verify_git=False)
    launch = validate_launch_provenance(
        tmp_path, preflight, selection_summary,
        instances=HOLDOUT_INSTANCES)
    assert launch["job_id"] == "424242"
    assert launch["code_commit"] == RUN_COMMIT


# -------------------------------------------------------------------------
# Strict miniature end-to-end artifact pipeline
# -------------------------------------------------------------------------
def test_mini_pipeline_artifacts_and_determinism(mini_root, tmp_path):
    root, preflight = mini_root
    first = _mini_analyze(root, preflight, tmp_path / "one")
    second = _mini_analyze(root, preflight, tmp_path / "two")
    files = sorted(p.name for p in Path(first).iterdir())
    assert "MANIFEST.json" in files and "decision_status.csv" in files
    assert files == sorted(p.name for p in Path(second).iterdir())
    for filename in files:
        assert (Path(first, filename).read_bytes()
                == Path(second, filename).read_bytes()), filename
    manifest = json.loads(Path(first, "MANIFEST.json").read_text())
    assert manifest["schema"] == mod.CLOSEOUT_SCHEMA
    assert manifest["transfer"] is None
    assert manifest["analysis_claim"] is None
    assert manifest["launch"]["job_id"] == "424242"
    assert manifest["launch"]["code_commit"] == RUN_COMMIT
    assert manifest["launch"]["manifest"]["sha256"] == sha256_file(
        str(Path(root, "MANIFEST-20260819T010300Z.txt")))


def test_launch_provenance_validates_complete_chain(mini_root):
    root, preflight = mini_root
    rooted = dict(preflight)
    rooted["path"] = str(Path(root, "PREFLIGHT.json").resolve())
    selection = validate_selection(mod.DEFAULT_SELECTION, verify_git=False)
    launch = validate_launch_provenance(
        root, rooted, selection, instances=MINI_INSTANCES)
    assert launch["job_id"] == "424242"
    assert launch["selection_sha256"] == EXPECTED_SELECTION_SHA256
    assert set(launch["lock"]) == {
        "CLAIM.txt", "INTENT.txt", "SUBMITTED.txt"}


def test_missing_launch_lock_file_halts_unscored(mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "missing-lock-file"
    shutil.copytree(source, bad)
    (bad / "SUBMISSION_LOCK" / "INTENT.txt").unlink()
    out = tmp_path / "missing-lock-out"
    with pytest.raises(AnalysisError, match="must contain exactly"):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()
    assert not list(out.glob(".TESTSTAMP.staging-*"))


def test_launch_job_id_mismatch_halts_unscored(mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "job-mismatch"
    shutil.copytree(source, bad)
    path = bad / "SUBMISSION_LOCK" / "SUBMITTED.txt"
    path.write_text(path.read_text().replace("job_id=424242", "job_id=999999"))
    out = tmp_path / "job-mismatch-out"
    with pytest.raises(AnalysisError, match="job id differs"):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()
    assert not list(out.glob(".TESTSTAMP.staging-*"))


@pytest.mark.parametrize("record,old,new,match", [
    ("CLAIM.txt", EXPECTED_SELECTION_SHA256, "2" * 64,
     "selection SHA chain"),
    ("INTENT.txt",
     mod.canonical_grid_list_sha256(selection_block(), MINI_INSTANCES),
     "3" * 64, "grid-list SHA chain"),
])
def test_launch_hash_tampering_halts_unscored(
        mini_root, tmp_path, record, old, new, match):
    source, preflight = mini_root
    bad = tmp_path / f"hash-{record}"
    shutil.copytree(source, bad)
    path = bad / "SUBMISSION_LOCK" / record
    path.write_text(path.read_text().replace(old, new, 1))
    out = tmp_path / f"hash-{record}-out"
    with pytest.raises(AnalysisError, match=match):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()
    assert not list(out.glob(".TESTSTAMP.staging-*"))


def test_frozen_grid_list_bytes_match_launched_golden_digest():
    assert mod.canonical_grid_list_sha256(
        selection_block(), HOLDOUT_INSTANCES
    ) == mod.EXPECTED_GRID_LIST_SHA256


def test_coordinated_grid_hash_tampering_halts_unscored(mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "coordinated-grid-hash"
    shutil.copytree(source, bad)
    correct = mod.canonical_grid_list_sha256(
        preflight["selection"], MINI_INSTANCES)
    false = "3" * 64
    intent = bad / "SUBMISSION_LOCK" / "INTENT.txt"
    manifest = bad / "MANIFEST-20260819T010300Z.txt"
    intent.write_text(intent.read_text().replace(correct, false))
    manifest.write_text(manifest.read_text().replace(correct, false))
    out = tmp_path / "coordinated-grid-hash-out"
    with pytest.raises(AnalysisError, match="grid-list SHA chain"):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()
    assert not list(out.glob(".TESTSTAMP.staging-*"))


def test_launch_preflight_hash_tampering_halts_unscored(mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "preflight-hash"
    shutil.copytree(source, bad)
    path = bad / "SUBMISSION_LOCK" / "INTENT.txt"
    path.write_text(path.read_text().replace(
        preflight["sha256"], "4" * 64, 1))
    out = tmp_path / "preflight-hash-out"
    with pytest.raises(AnalysisError, match="preflight SHA chain"):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()
    assert not list(out.glob(".TESTSTAMP.staging-*"))


def test_duplicate_launch_manifest_halts_unscored(mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "duplicate-manifest"
    shutil.copytree(source, bad)
    shutil.copy2(
        bad / "MANIFEST-20260819T010300Z.txt",
        bad / "MANIFEST-20260819T010301Z.txt")
    out = tmp_path / "duplicate-manifest-out"
    with pytest.raises(AnalysisError, match="exactly one"):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()
    assert not list(out.glob(".TESTSTAMP.staging-*"))


def test_launch_timestamp_inversion_halts_unscored(mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "timestamp-inversion"
    shutil.copytree(source, bad)
    path = bad / "SUBMISSION_LOCK" / "CLAIM.txt"
    path.write_text(path.read_text().replace(
        "claimed_utc=2026-08-19T01:00:00Z",
        "claimed_utc=2026-08-19T02:00:00Z"))
    out = tmp_path / "timestamp-inversion-out"
    with pytest.raises(AnalysisError, match="timestamp"):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()
    assert not list(out.glob(".TESTSTAMP.staging-*"))


@pytest.mark.parametrize("suffix,match", [
    ("job_id=424242\n", "duplicate key"),
    ("malformed-line\n", "malformed line"),
])
def test_malformed_launch_record_halts_unscored(
        mini_root, tmp_path, suffix, match):
    source, preflight = mini_root
    bad = tmp_path / f"malformed-{match.replace(' ', '-')}"
    shutil.copytree(source, bad)
    path = bad / "SUBMISSION_LOCK" / "SUBMITTED.txt"
    path.write_text(path.read_text() + suffix)
    out = tmp_path / f"malformed-{match.replace(' ', '-')}-out"
    with pytest.raises(AnalysisError, match=match):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()
    assert not list(out.glob(".TESTSTAMP.staging-*"))


def test_audit_failure_halts_unscored(mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "bad-audit"
    shutil.copytree(source, bad)
    ck_path = bad / "a2_s1_n4_b0.01" / "a2.cg.ckpt.json"
    ck = checkpoint.load(str(ck_path))
    ck["oracle_events"][0]["replay_ok"] = False
    checkpoint.save(str(ck_path), ck)
    out = tmp_path / "out"
    with pytest.raises(AnalysisError, match="HALT-AND-DEBUG"):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()


def test_analysis_output_inside_raw_root_refuses_before_writing(mini_root):
    source, preflight = mini_root
    nested = Path(source) / "analysis-output"
    with pytest.raises(AnalysisError, match="outside the raw holdout root"):
        _mini_analyze(source, preflight, nested)
    assert not nested.exists()


def test_single_analysis_claim_is_persistent_and_nonoverwriting(tmp_path):
    root = tmp_path / "src/runs/a6_holdout"
    root.mkdir(parents=True)
    transfer = {
        "sha256": "a" * 64,
        "tree_snapshot": {"canonical_tree_sha256": "b" * 64},
    }
    first = mod.claim_single_analysis(
        root,
        out_dir=tmp_path / "result/a6_holdout/20260819T030000Z",
        stamp="20260819T030000Z",
        analysis_code_commit="c" * 40,
        transfer=transfer,
    )
    claim = Path(first["path"])
    raw = claim.read_bytes()
    assert raw == (json.dumps(
        json.loads(raw), indent=2, sort_keys=True) + "\n").encode()
    with pytest.raises(AnalysisError, match="already claimed"):
        mod.claim_single_analysis(
            root,
            out_dir=tmp_path / "result/a6_holdout/20260819T030001Z",
            stamp="20260819T030001Z",
            analysis_code_commit="c" * 40,
            transfer=transfer,
        )
    assert claim.read_bytes() == raw


def test_production_orchestration_claims_before_checkpoint_root_validation(
        tmp_path, monkeypatch):
    root = tmp_path / "src/runs/a6_holdout"
    root.mkdir(parents=True)
    (root / "PREFLIGHT.json").write_text("{}\n")
    out = tmp_path / "result/a6_holdout"
    calls = []
    commit = "c" * 40

    monkeypatch.setattr(
        mod, "verify_analysis_code_commit", lambda _claim: commit)
    monkeypatch.setattr(
        mod, "validate_selection",
        lambda *_args, **_kwargs: {
            "sha256": mod.EXPECTED_SELECTION_SHA256,
            "selection_commit": mod.EXPECTED_SELECTION_COMMIT,
        })

    def receipt(*_args, **_kwargs):
        calls.append("receipt")
        return {
            "sha256": "a" * 64,
            "tree_snapshot": {"canonical_tree_sha256": "b" * 64},
        }

    def claim(*_args, **_kwargs):
        calls.append("claim")
        return {"path": "unused", "sha256": "d" * 64, "document": {}}

    def root_gate(*_args, **_kwargs):
        calls.append("root")
        raise AnalysisError("stop after ordering probe")

    monkeypatch.setattr(mod, "validate_holdout_root", root_gate)
    with pytest.raises(AnalysisError, match="ordering probe"):
        analyze(
            str(root), str(out), "20260819T030000Z", commit,
            instances=HOLDOUT_INSTANCES,
            preflight_validator=lambda *_args, **_kwargs: {
                "code_commit": RUN_COMMIT, "sha256": "e" * 64},
            launch_validator=lambda *_args, **_kwargs: {
                "job_id": "424242"},
            transfer_validator=receipt,
            analysis_claimer=claim,
        )
    assert calls == ["receipt", "claim", "root"]
    assert not out.exists()


def test_identity_and_cell_provenance_tampering_halt(mini_root, tmp_path):
    source, preflight = mini_root
    bad_hash = tmp_path / "bad-hash"
    shutil.copytree(source, bad_hash)
    ck_path = bad_hash / "a2_s1_n4_b0.01" / "a2.cg.ckpt.json"
    ck = checkpoint.load(str(ck_path))
    ck["identity"]["market_hash"] = "tampered"
    checkpoint.save(str(ck_path), ck)
    with pytest.raises(AnalysisError, match="market hash mismatch"):
        _mini_analyze(str(bad_hash), preflight, tmp_path / "o1")

    bad_policy = tmp_path / "bad-load-policy"
    shutil.copytree(source, bad_policy)
    ck_path = bad_policy / "a6_a4_s1_n4_b0.01" / "a6_a4.cg.ckpt.json"
    ck = checkpoint.load(str(ck_path))
    ck["identity"]["load_reconstruction"]["policy_version"] = 0
    checkpoint.save(str(ck_path), ck)
    with pytest.raises(AnalysisError, match="load reconstruction identity"):
        _mini_analyze(str(bad_policy), preflight, tmp_path / "o-policy")

    bad_dictator_policy = tmp_path / "bad-dictator-load-policy"
    shutil.copytree(source, bad_dictator_policy)
    dck_path = (bad_dictator_policy / "a2_s1_n4_b0.01" /
                "dictator.ckpt.json")
    dck = checkpoint.load(str(dck_path))
    dck["identity"]["load_reconstruction"]["policy_version"] = 0
    checkpoint.save(str(dck_path), dck)
    with pytest.raises(
            AnalysisError, match="dictator load reconstruction identity"):
        _mini_analyze(
            str(bad_dictator_policy), preflight,
            tmp_path / "o-dictator-policy")

    bad_prov = tmp_path / "bad-prov"
    shutil.copytree(source, bad_prov)
    p = bad_prov / "a6_a4_s1_n4_b0.01" / "CELL_PROVENANCE.json"
    data = json.loads(p.read_text())
    data["cell_index"] += 1
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AnalysisError, match="cell provenance mismatch"):
        _mini_analyze(str(bad_prov), preflight, tmp_path / "o2")


def test_slurm_task_lineage_tampering_halts_unscored(mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "bad-slurm-lineage"
    shutil.copytree(source, bad)
    cell = bad / "a2_s1_n4_b0.01"
    ck_path = cell / "a2.cg.ckpt.json"
    ck = checkpoint.load(str(ck_path))
    ck["oracle_events"][0]["slurm_array_task_id"] = "99"
    checkpoint.save(str(ck_path), ck)
    _dump_jsonl(cell / "a2.oracle.jsonl", ck["oracle_events"])
    with pytest.raises(AnalysisError, match="Slurm task"):
        _mini_analyze(str(bad), preflight, tmp_path / "bad-slurm-out")


def test_future_parent_array_lineage_must_match_launch(mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "bad-parent-array-lineage"
    shutil.copytree(source, bad)
    cell = bad / "a2_s1_n4_b0.01"
    ck_path = cell / "a2.cg.ckpt.json"
    ck = checkpoint.load(str(ck_path))
    for record in [*ck["oracle_events"], *ck["iteration_events"]]:
        record["slurm_array_job_id"] = "999999"
    checkpoint.save(str(ck_path), ck)
    _dump_jsonl(cell / "a2.oracle.jsonl", ck["oracle_events"])
    _dump_jsonl(cell / "a2.iterations.jsonl", ck["iteration_events"])
    dck_path = cell / "dictator.ckpt.json"
    dck = checkpoint.load(str(dck_path))
    dck["record"]["slurm_array_job_id"] = "999999"
    checkpoint.save(str(dck_path), dck)
    _dump_jsonl(cell / "dictator.jsonl", [dck["record"]])
    with pytest.raises(AnalysisError, match="parent Slurm array IDs"):
        _mini_analyze(str(bad), preflight, tmp_path / "bad-parent-out")


def _mutate_schedule_artifact(root: Path, target: str, mutate) -> None:
    """Mutate checkpoint evidence and its materialized JSONL in lockstep."""
    cell = root / "a2_s1_n4_b0.01"
    if target in ("column", "oracle"):
        path = cell / "a2.cg.ckpt.json"
        state = checkpoint.load(str(path))
        obj = (state["columns"][0] if target == "column"
               else state["oracle_events"][0])
        mutate(obj, state)
        checkpoint.save(str(path), state)
        if target == "oracle":
            _dump_jsonl(cell / "a2.oracle.jsonl", state["oracle_events"])
        return
    if target == "dictator":
        path = cell / "dictator.ckpt.json"
        state = checkpoint.load(str(path))
        mutate(state["record"], state)
        checkpoint.save(str(path), state)
        _dump_jsonl(cell / "dictator.jsonl", [state["record"]])
        return
    raise AssertionError(target)


def _semantic_bad_root(mini_root, tmp_path, name):
    source, preflight = mini_root
    bad = tmp_path / name
    shutil.copytree(source, bad)
    return bad, preflight


def test_coordinated_checkpoint_history_and_outcome_tamper_halts(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-coordinated-summary")
    path = bad / "a2_s1_n4_b0.01" / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    delta = 0.0001
    state["ub_history"][0] += delta
    state["lb_history"][0] += delta
    state["lb_best"] += delta
    state["outcome"]["ub_ch"] += delta
    state["outcome"]["lb_best"] += delta
    state["outcome"]["uplift_interval"][0] -= delta
    state["outcome"]["uplift_interval"][1] -= delta
    checkpoint.save(str(path), state)
    with pytest.raises(AnalysisError, match="UB/LB histories do not replay"):
        _mini_analyze(str(bad), preflight, tmp_path / "out-summary-tamper")


def test_coordinated_iteration_history_outcome_tamper_still_hits_oracle_anchor(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-coordinated-certificate")
    cell = bad / "a2_s1_n4_b0.01"
    path = cell / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    delta = 0.0001
    iteration = state["iteration_events"][0]
    oracle_extra = state["oracle_events"][1]["extra"]
    iteration["min_reduced_cost_lb"] += delta
    oracle_extra["min_reduced_cost_lb"] += delta
    iteration["lb_ch"] += delta
    iteration["lb_best"] += delta
    iteration["certificate_gap"] -= delta
    state["lb_history"][0] += delta
    state["lb_best"] += delta
    state["outcome"]["lb_best"] += delta
    state["outcome"]["gap"] -= delta
    state["outcome"]["uplift_interval"][1] -= delta
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "a2.oracle.jsonl", state["oracle_events"])
    _dump_jsonl(cell / "a2.iterations.jsonl", state["iteration_events"])
    with pytest.raises(
            AnalysisError, match="min_reduced_cost_lb.*does not recompute"):
        _mini_analyze(
            str(bad), preflight, tmp_path / "out-certificate-tamper")


def test_coordinated_scheduler_gap_and_trigger_story_halts(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-scheduler-gap-story")
    cell = bad / "a6_a4_s1_n4_b0.01"
    path = cell / "a6_a4.cg.ckpt.json"
    state = checkpoint.load(str(path))
    iteration = state["iteration_events"][0]
    oracle_extra = state["oracle_events"][1]["extra"]

    # This remains internally consistent with the old scheduler audit: T4
    # still wins priority, while the forged small gap also fires T1.  Only an
    # independent link to the prior certified LB exposes the false story.
    iteration["gap_at_decision"] = 0.0
    iteration["triggers_fired"] = ["T4", "T1"]
    oracle_extra["triggers_fired"] = ["T4", "T1"]
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "a6_a4.oracle.jsonl", state["oracle_events"])
    _dump_jsonl(cell / "a6_a4.iterations.jsonl", state["iteration_events"])

    with pytest.raises(
            AnalysisError,
            match="gap_at_decision.*(does not replay|chronologically "
                  "derived)"):
        _mini_analyze(
            str(bad), preflight, tmp_path / "out-scheduler-gap-story")


def test_coordinated_seed_price_story_must_match_posted_vector(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-seed-price-story")
    cell = bad / "a2_s1_n4_b0.01"
    path = cell / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    seed = state["oracle_events"][0]

    # The fixture has zero charging, so changing every stored seed-price
    # field leaves all producer-written objective arithmetic internally
    # consistent.  The independently regenerated posted vector must still
    # reject this false initialization story.
    forged = [0.0] * len(seed["load"])
    seed["prices"] = forged
    seed["solver"]["extra"]["pricing_objective_reconstruction"][
        "prices"] = forged
    state["columns"][0]["oracle_stats"] = copy.deepcopy(seed["solver"])
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "a2.oracle.jsonl", state["oracle_events"])

    with pytest.raises(AnalysisError, match="seed prices.*posted vector"):
        _mini_analyze(
            str(bad), preflight, tmp_path / "out-seed-price-story")


def test_coordinated_dual_sigma_story_must_be_tight_on_retained_columns(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-dual-sigma-story")
    cell = bad / "a2_s1_n4_b0.01"
    path = cell / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    iteration = state["iteration_events"][0]
    oracle_extra = state["oracle_events"][1]["extra"]
    delta = 0.0001

    iteration["duals_sigma"] += delta
    for owner in (iteration, oracle_extra):
        owner["min_reduced_cost_ub"] -= delta
        owner["min_reduced_cost_lb"] -= delta
    iteration["lb_ch"] -= delta
    iteration["lb_best"] -= delta
    iteration["certificate_gap"] += delta
    state["lb_history"][0] -= delta
    state["lb_best"] -= delta
    state["outcome"]["lb_best"] -= delta
    state["outcome"]["gap"] += delta
    state["outcome"]["uplift_interval"][1] += delta
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "a2.oracle.jsonl", state["oracle_events"])
    _dump_jsonl(cell / "a2.iterations.jsonl", state["iteration_events"])

    with pytest.raises(AnalysisError, match="dual tightness"):
        _mini_analyze(str(bad), preflight, tmp_path / "out-dual-sigma-story")


def test_arbitrary_clean_price_cannot_support_false_certificate(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-clean-price-certificate")
    cell = bad / "a2_s1_n4_b0.01"
    path = cell / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    event = state["oracle_events"][1]
    market = make_affine_market(fix_builder(1, 4), shape="duck", b_scale=0.01)
    forged = [float(value + 1.0) for value in market.price(
        [0.0] * market.n_slots)]
    event["prices"] = [round(value, 6) for value in forged]
    event["solver"]["extra"]["pricing_objective_reconstruction"][
        "prices"] = forged
    tv, linf, points = mod._price_path_metrics(
        state["oracle_events"],
        ("cg-seed", "cg-pricing", "cg-stab-pricing"),
    )
    state["outcome"].update(
        broadcast_tv=tv,
        broadcast_linf_max=linf,
        broadcast_points=points,
    )
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "a2.oracle.jsonl", state["oracle_events"])

    with pytest.raises(
            AnalysisError, match="exceeds independent Lagrangian bound"):
        _mini_analyze(
            str(bad), preflight, tmp_path / "out-clean-price-certificate")


def test_one_column_master_ub_must_recompute_from_retained_column(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-one-column-ub")
    cell = bad / "a2_s1_n4_b0.01"
    path = cell / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    iteration = state["iteration_events"][0]
    delta = 0.1
    iteration["z_rmp_model"] -= delta
    iteration["ub_ch"] -= delta
    iteration["lb_ch"] -= delta
    iteration["lb_best"] -= delta
    iteration["master_solves"][0]["obj"] -= delta
    iteration["master_solves"][0]["bound"] -= delta
    state["ub_history"][0] -= delta
    state["lb_history"][0] -= delta
    state["lb_best"] -= delta
    state["outcome"]["ub_ch"] -= delta
    state["outcome"]["lb_best"] -= delta
    state["outcome"]["uplift_interval"][0] += delta
    state["outcome"]["uplift_interval"][1] += delta
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "a2.iterations.jsonl", state["iteration_events"])

    with pytest.raises(AnalysisError, match="ub_ch is below"):
        _mini_analyze(str(bad), preflight, tmp_path / "out-one-column-ub")


def test_retained_key_list_must_exactly_match_recomputed_columns(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-retained-keys")
    path = bad / "a2_s1_n4_b0.01" / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    state["keys"][0] = "0" * 64
    checkpoint.save(str(path), state)
    with pytest.raises(AnalysisError, match="key list does not exactly match"):
        _mini_analyze(str(bad), preflight, tmp_path / "out-retained-keys")


def test_valid_but_different_seed_column_must_match_seed_oracle(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-seed-column-lineage")
    path = bad / "a2_s1_n4_b0.01" / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    column = state["columns"][0]
    column["sequences"].reverse()
    column["arc_kinds"].reverse()
    sol = Solution(
        sequences=column["sequences"], arc_kinds=column["arc_kinds"],
        charges=column["charges"], load=column["load"],
        fleet=column["fleet"],
    )
    column["schedule_hash"] = sol.schedule_hash()
    column["load_hash"] = sol.load_hash()
    column["column_key"] = column_key(column)
    state["keys"] = [column["column_key"]]
    checkpoint.save(str(path), state)
    with pytest.raises(AnalysisError, match="does not equal its oracle projection"):
        _mini_analyze(
            str(bad), preflight, tmp_path / "out-seed-column-lineage")


def test_coordinated_oracle_iteration_novelty_tamper_halts(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-column-novelty")
    cell = bad / "a2_s1_n4_b0.01"
    path = cell / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    state["oracle_events"][1]["extra"]["column_novel"] = True
    state["iteration_events"][0]["column_novel"] = True
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "a2.oracle.jsonl", state["oracle_events"])
    _dump_jsonl(cell / "a2.iterations.jsonl", state["iteration_events"])
    with pytest.raises(AnalysisError, match="novelty/linkage fails"):
        _mini_analyze(str(bad), preflight, tmp_path / "out-column-novelty")


def test_certifying_novel_oracle_is_not_required_as_retained(
        mini_root, tmp_path):
    """The producer returns before appending a certificate-closing column."""
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "certifying-novel-column")
    cell = bad / "a2_s1_n4_b0.01"
    path = cell / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    inst = fix_builder(1, 4)
    sequences = [["t000", "t002"], ["t001", "t003"]]
    arc_kinds = [["dir"], ["dir"]]
    trip_map = {trip.id: trip for trip in inst.trips}
    deadhead = 0.0
    for sequence in sequences:
        first, second = (trip_map[trip_id] for trip_id in sequence)
        deadhead += inst.dhm(inst.depot, first.start_loc)
        deadhead += inst.dhm(first.end_loc, second.start_loc)
        deadhead += inst.dhm(second.end_loc, inst.depot)
    ops_cost = (
        inst.vehicle_fixed_cost * len(sequences)
        + inst.dh_cost_per_min * deadhead
    )
    sol = Solution(
        sequences=sequences, arc_kinds=arc_kinds, charges=[],
        load=[0.0] * inst.n_slots, fleet=2,
    )
    # Make the seed/retained column the cheaper alternative.  The final clean
    # pricing call remains the fixture's original, more expensive schedule,
    # so it is genuinely novel but has nonnegative reduced cost and closes the
    # one-column master certificate before the producer's append branch.
    seed = state["oracle_events"][0]
    seed.update(
        sequences=sequences, arc_kinds=arc_kinds, charges=[],
        load=[0.0] * inst.n_slots, fleet=2,
        dh_min_total=deadhead, energy_charged_kwh=0.0,
        ops_cost=ops_cost, obj_model=ops_cost, obj_true=ops_cost,
        energy_cost_model=0.0,
        schedule_hash=sol.schedule_hash(), load_hash=sol.load_hash(),
    )
    seed["solver"]["obj"] = ops_cost
    seed["solver"]["bound"] = ops_cost
    seed_pricing = seed["solver"]["extra"][
        "pricing_objective_reconstruction"]
    seed_pricing["model_obj"] = ops_cost
    seed_pricing["physical_obj"] = ops_cost

    column = {
        key: copy.deepcopy(seed[key])
        for key in ("sequences", "arc_kinds", "charges", "load", "fleet",
                    "ops_cost", "schedule_hash", "load_hash",
                    "instance_hash", "replay_ok", "replay_violations")
    }
    column["oracle_stats"] = copy.deepcopy(seed["solver"])
    column["column_key"] = column_key(column)
    state["columns"] = [column]
    state["keys"] = [column["column_key"]]

    event = state["oracle_events"][1]
    event_key = column_key(event)
    iteration = state["iteration_events"][0]
    pricing_bound = float(event["solver"]["bound"])
    pricing_incumbent = float(event["obj_true"])
    min_rc_lb = pricing_bound - ops_cost
    min_rc_ub = pricing_incumbent - ops_cost
    event["extra"].update(
        column_key=event_key, column_novel=True,
        min_reduced_cost_ub=min_rc_ub,
        min_reduced_cost_lb=min_rc_lb,
    )
    iteration.update(
        z_rmp_model=ops_cost, ub_ch=ops_cost, duals_sigma=ops_cost,
        column_key=event_key, column_novel=True,
        min_reduced_cost_ub=min_rc_ub,
        min_reduced_cost_lb=min_rc_lb,
        lb_ch=ops_cost, lb_best=ops_cost, certificate_gap=0.0,
    )
    iteration["master_solves"][0]["obj"] = ops_cost
    iteration["master_solves"][0]["bound"] = ops_cost
    state["ub_history"] = [ops_cost]
    state["lb_history"] = [ops_cost]
    state["lb_best"] = ops_cost
    state["outcome"].update(
        ub_ch=ops_cost, lb_best=ops_cost, gap=0.0,
    )
    dck = checkpoint.load(str(cell / "dictator.ckpt.json"))
    state["outcome"]["uplift_interval"] = [
        (dck["z_d_ub"] - dck["tol_d"]) - ops_cost,
        dck["z_d_ub"] - ops_cost,
    ]
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "a2.oracle.jsonl", state["oracle_events"])
    _dump_jsonl(cell / "a2.iterations.jsonl", state["iteration_events"])
    result = _mini_analyze(
        str(bad), preflight, tmp_path / "out-certifying-novel")
    assert Path(result).is_dir()


@pytest.mark.parametrize("target", ["column", "oracle", "dictator"])
def test_duplicate_and_missing_trip_halt_independent_replay(
        mini_root, tmp_path, target):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-coverage-{target}")

    def mutate(obj, _state):
        obj["sequences"][0][0] = obj["sequences"][1][0]

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match="not covered exactly once"):
        _mini_analyze(str(bad), preflight, tmp_path / f"out-coverage-{target}")


@pytest.mark.parametrize("target", ["column", "oracle", "dictator"])
def test_malformed_arc_shape_or_kind_halts_independent_replay(
        mini_root, tmp_path, target):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-arcs-{target}")

    def mutate(obj, _state):
        obj["arc_kinds"][0][0] = "teleport"

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match="arc shape/kind mismatch"):
        _mini_analyze(str(bad), preflight, tmp_path / f"out-arcs-{target}")


@pytest.mark.parametrize("target", ["column", "oracle", "dictator"])
def test_charge_vehicle_and_arc_association_is_independently_checked(
        mini_root, tmp_path, target):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-charge-association-{target}")

    def mutate(obj, _state):
        first = obj["sequences"][0]
        obj["charges"].append({
            "vehicle": 1,
            "after_trip": first[0], "before_trip": first[1],
            "slot": 0, "kwh": 0.0,
        })

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(
            AnalysisError, match="not tied to its stated vehicle"):
        _mini_analyze(
            str(bad), preflight,
            tmp_path / f"out-charge-association-{target}")


@pytest.mark.parametrize("target", ["column", "oracle", "dictator"])
def test_invalid_charge_vehicle_halts_before_replay(
        mini_root, tmp_path, target):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-charge-vehicle-{target}")

    def mutate(obj, _state):
        first = obj["sequences"][0]
        obj["charges"].append({
            "vehicle": len(obj["sequences"]),
            "after_trip": first[0], "before_trip": first[1],
            "slot": 0, "kwh": 0.0,
        })

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match="invalid vehicle"):
        _mini_analyze(
            str(bad), preflight,
            tmp_path / f"out-charge-vehicle-{target}")


def test_duplicate_charge_vehicle_arc_slot_halts(mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-duplicate-charge")

    def mutate(obj, _state):
        obj["arc_kinds"][0][0] = "dep"
        first = obj["sequences"][0]
        event = {
            "vehicle": 0,
            "after_trip": first[0], "before_trip": first[1],
            "slot": 0, "kwh": 0.0,
        }
        obj["charges"] = [dict(event), dict(event)]

    _mutate_schedule_artifact(bad, "column", mutate)
    with pytest.raises(AnalysisError, match="duplicate charge event"):
        _mini_analyze(str(bad), preflight, tmp_path / "out-duplicate-charge")


@pytest.mark.parametrize("target", ["column", "oracle", "dictator"])
@pytest.mark.parametrize("field", ["schedule_hash", "load_hash"])
def test_false_schedule_and_load_hashes_halt(
        mini_root, tmp_path, target, field):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-{field}-{target}")

    def mutate(obj, _state):
        obj[field] = "false-hash"

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match=field.replace("_", " ")):
        _mini_analyze(
            str(bad), preflight, tmp_path / f"out-{field}-{target}")


@pytest.mark.parametrize("target", ["column", "oracle", "dictator"])
def test_consistently_adjusted_ops_and_objectives_still_halt(
        mini_root, tmp_path, target):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-coherent-economics-{target}")

    def mutate(obj, _state):
        obj["ops_cost"] += 1.0
        if target == "column":
            obj["column_key"] = column_key(obj)
        elif target == "oracle":
            obj["obj_model"] += 1.0
            obj["obj_true"] += 1.0
            pricing = obj["solver"]["extra"][
                "pricing_objective_reconstruction"]
            pricing["model_obj"] += 1.0
            pricing["physical_obj"] += 1.0
        else:
            obj["obj_model"] += 1.0
            obj["obj_true"] += 1.0
            objective = obj["solver"]["extra"][
                "dictator_objective_reconstruction"]
            objective["raw_true_obj"] += 1.0
            objective["physical_obj"] += 1.0

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match="operating cost does not recompute"):
        _mini_analyze(
            str(bad), preflight,
            tmp_path / f"out-coherent-economics-{target}")


def test_false_column_key_halts(mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-column-key")

    def mutate(obj, _state):
        obj["column_key"] = "0" * 64

    _mutate_schedule_artifact(bad, "column", mutate)
    with pytest.raises(AnalysisError, match="column_key does not recompute"):
        _mini_analyze(str(bad), preflight, tmp_path / "out-column-key")


@pytest.mark.parametrize("target", ["oracle", "dictator"])
def test_record_replay_policy_metadata_halts(mini_root, tmp_path, target):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-replay-policy-{target}")

    def mutate(obj, _state):
        obj["replay_policy_version"] -= 1

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match="replay policy metadata mismatch"):
        _mini_analyze(
            str(bad), preflight, tmp_path / f"out-replay-policy-{target}")


@pytest.mark.parametrize("target", ["column", "oracle", "dictator"])
def test_embedded_instance_and_replay_claims_are_not_trusted(
        mini_root, tmp_path, target):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-embedded-claims-{target}")

    def mutate(obj, _state):
        obj["instance_hash"] = "false-instance"
        obj["replay_ok"] = True
        obj["replay_violations"] = []

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match="record instance hash mismatch"):
        _mini_analyze(
            str(bad), preflight, tmp_path / f"out-embedded-claims-{target}")


@pytest.mark.parametrize("target", ["column", "oracle", "dictator"])
def test_nonempty_stored_replay_violations_halt(
        mini_root, tmp_path, target):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-replay-violations-{target}")

    def mutate(obj, _state):
        obj["replay_violations"] = ["hidden violation"]

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match="replay_violations is not empty"):
        _mini_analyze(
            str(bad), preflight,
            tmp_path / f"out-replay-violations-{target}")


@pytest.mark.parametrize("target", ["column", "oracle", "dictator"])
def test_fleet_count_and_instance_maximum_halt(
        mini_root, tmp_path, target):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-fleet-{target}")

    def mutate(obj, _state):
        obj["fleet"] += 1

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match="fleet .* max_vehicles"):
        _mini_analyze(str(bad), preflight, tmp_path / f"out-fleet-{target}")


@pytest.mark.parametrize("target", ["oracle", "dictator"])
def test_record_max_vehicles_must_match_instance(
        mini_root, tmp_path, target):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-max-vehicles-{target}")

    def mutate(obj, _state):
        obj["max_vehicles"] += 1

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match="max_vehicles .* instance value"):
        _mini_analyze(
            str(bad), preflight, tmp_path / f"out-max-vehicles-{target}")


@pytest.mark.parametrize("case,expected", [
    ("pricing_model", "pricing model_obj mismatch"),
    ("pricing_adjustment", "pricing abs_adjustment mismatch"),
    ("dictator_raw", "dictator raw_true_obj mismatch"),
    ("dictator_adjustment", "dictator abs_adjustment mismatch"),
    ("adaptive_lb", "adaptive_lb does not recompute from bounds"),
    ("adaptive_gap", "adaptive gap arithmetic mismatch"),
    ("adaptive_tol", "adaptive tolerance mismatch"),
    ("adaptive_row_gap", "adaptive subsolve 1 gap does not recompute"),
])
def test_raw_and_adaptive_economic_scalar_tampering_halts(
        mini_root, tmp_path, case, expected):
    target = "oracle" if case.startswith("pricing") else "dictator"
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, f"bad-economic-scalar-{case}")

    def mutate(obj, state):
        extra = obj["solver"]["extra"]
        if case == "pricing_model":
            extra["pricing_objective_reconstruction"]["model_obj"] += 1.0
            obj["obj_model"] += 1.0
        elif case == "pricing_adjustment":
            extra["pricing_objective_reconstruction"]["abs_adjustment"] += 1.0
        elif case == "dictator_raw":
            extra["dictator_objective_reconstruction"]["raw_true_obj"] += 1.0
        elif case == "dictator_adjustment":
            extra["dictator_objective_reconstruction"]["abs_adjustment"] += 1.0
        elif case == "adaptive_lb":
            extra["adaptive_lb"] += 1.0
            extra["adaptive_gap_abs"] -= 1.0
            state["adaptive"]["adaptive_lb"] += 1.0
            state["adaptive"]["adaptive_gap_abs"] -= 1.0
        elif case == "adaptive_gap":
            extra["adaptive_gap_abs"] += 1.0
            state["adaptive"]["adaptive_gap_abs"] += 1.0
        elif case == "adaptive_tol":
            extra["adaptive_tol_abs"] += 1.0
            state["adaptive"]["adaptive_tol_abs"] += 1.0
        elif case == "adaptive_row_gap":
            extra["adaptive_solve_stats"][0]["gap"] += 1.0
            state["adaptive"]["adaptive_solve_stats"][0]["gap"] += 1.0
        else:
            raise AssertionError(case)

    _mutate_schedule_artifact(bad, target, mutate)
    with pytest.raises(AnalysisError, match=expected):
        _mini_analyze(
            str(bad), preflight, tmp_path / f"out-economic-scalar-{case}")


def test_coordinated_dictator_bound_above_incumbent_halts(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-dictator-bound-order")
    cell = bad / "a2_s1_n4_b0.01"
    path = cell / "dictator.ckpt.json"
    state = checkpoint.load(str(path))
    record_extra = state["record"]["solver"]["extra"]
    adaptive = state["adaptive"]
    ub = float(record_extra["adaptive_ub"])
    for owner in (record_extra, adaptive):
        row = owner["adaptive_solve_stats"][0]
        row["incumbent"] = ub
        row["bound"] = ub + 1.0
        row["gap"] = -1.0
        owner["adaptive_lb"] = ub + 1.0
        owner["adaptive_model_obj"] = ub
        owner["adaptive_gap_abs"] = -1.0
        owner["adaptive_converged"] = True
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "dictator.jsonl", [state["record"]])
    with pytest.raises(AnalysisError, match="bound exceeds incumbent"):
        _mini_analyze(str(bad), preflight, tmp_path / "out-bound-order")


@pytest.mark.parametrize("coordinate_solver_obj", (False, True))
def test_coordinated_pricing_bound_above_incumbents_halts(
        mini_root, tmp_path, coordinate_solver_obj):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path,
        f"bad-pricing-bound-order-{coordinate_solver_obj}")
    cell = bad / "a2_s1_n4_b0.01"
    path = cell / "a2.cg.ckpt.json"
    state = checkpoint.load(str(path))
    oracle = state["oracle_events"][1]
    iteration = state["iteration_events"][0]
    ub = float(iteration["ub_ch"])
    false_bound = ub + 1.0
    if coordinate_solver_obj:
        oracle["solver"]["obj"] = false_bound
    oracle["solver"]["bound"] = false_bound
    min_rc_lb = false_bound - float(iteration["duals_sigma"])
    oracle["extra"]["min_reduced_cost_lb"] = min_rc_lb
    iteration["min_reduced_cost_lb"] = min_rc_lb
    iteration["pricing_gap_abs"] = ub - false_bound
    iteration["lb_ch"] = ub
    iteration["lb_best"] = ub
    iteration["certificate_gap"] = 0.0
    state["lb_best"] = ub
    state["lb_history"] = [ub]
    state["outcome"]["lb_best"] = ub
    state["outcome"]["gap"] = 0.0
    state["outcome"]["uplift_interval"] = [-0.01, 0.0]
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "a2.oracle.jsonl", state["oracle_events"])
    _dump_jsonl(cell / "a2.iterations.jsonl", state["iteration_events"])
    # Both variants still HALT with nothing scored, via two different
    # layers of the EI-027 contract:
    # - obj untampered: the shared physical-bridge gate rejects the bound
    #   above the MODEL incumbent beyond operand tau (audit stage);
    # - obj coordinated with the bound: the ordering gate legitimately
    #   passes (the physical allowance covers exactly the model-physical
    #   distance), but the RAW reconstruction fields are preserved exactly
    #   (EI-027 Task A), so the analyzer's pricing-objective
    #   reconstruction binding catches the tampered solver obj.
    with pytest.raises(
            AnalysisError,
            match="exceeds the model incumbent beyond the operand"
                  "|solver obj mismatch"):
        _mini_analyze(str(bad), preflight, tmp_path / "out-pricing-bound-order")


def test_coordinated_dictator_lb_above_physical_ub_halts(
        mini_root, tmp_path):
    bad, preflight = _semantic_bad_root(
        mini_root, tmp_path, "bad-dictator-lb-vs-physical")
    cell = bad / "a2_s1_n4_b0.01"
    path = cell / "dictator.ckpt.json"
    state = checkpoint.load(str(path))
    record_extra = state["record"]["solver"]["extra"]
    adaptive = state["adaptive"]
    ub = float(record_extra["adaptive_ub"])
    for owner in (record_extra, adaptive):
        row = owner["adaptive_solve_stats"][0]
        row["incumbent"] = ub + 2.0
        row["bound"] = ub + 1.0
        row["gap"] = 1.0
        owner["adaptive_lb"] = ub + 1.0
        owner["adaptive_model_obj"] = ub + 2.0
        owner["adaptive_gap_abs"] = -1.0
        owner["adaptive_converged"] = True
    checkpoint.save(str(path), state)
    _dump_jsonl(cell / "dictator.jsonl", [state["record"]])
    with pytest.raises(
            AnalysisError, match="lower bound exceeds independently"):
        _mini_analyze(str(bad), preflight, tmp_path / "out-lb-vs-physical")


@pytest.mark.parametrize("case,expected", [
    ("column_load", "canonical load does not equal summed charge events"),
    ("oracle_load", "canonical load does not equal summed charge events"),
    ("oracle_raw", "recorded load residual was tampered"),
    ("oracle_objective", "record obj_true mismatch"),
    ("dictator_objective", "dictator record obj_true mismatch"),
])
def test_numeric_reconstruction_tampering_halts_unscored(
        mini_root, tmp_path, case, expected):
    source, preflight = mini_root
    bad = tmp_path / f"bad-numeric-{case}"
    shutil.copytree(source, bad)
    cell = bad / "a2_s1_n4_b0.01"
    ck_path = cell / "a2.cg.ckpt.json"
    ck = checkpoint.load(str(ck_path))

    if case == "column_load":
        ck["columns"][0]["load"][0] = 1e-6
    elif case == "oracle_load":
        ck["oracle_events"][0]["load"][0] = 1e-6
    elif case == "oracle_raw":
        lr = ck["oracle_events"][0]["solver"]["extra"][
            "load_reconstruction"]
        lr["raw_load_kwh"][0] = 1e-6
    elif case == "oracle_objective":
        ck["oracle_events"][0]["obj_true"] += 1.0
    checkpoint.save(str(ck_path), ck)
    _dump_jsonl(cell / "a2.oracle.jsonl", ck["oracle_events"])

    if case == "dictator_objective":
        dck_path = cell / "dictator.ckpt.json"
        dck = checkpoint.load(str(dck_path))
        dck["record"]["obj_true"] += 1.0
        checkpoint.save(str(dck_path), dck)
        _dump_jsonl(cell / "dictator.jsonl", [dck["record"]])

    out = tmp_path / f"out-{case}"
    with pytest.raises(AnalysisError, match=expected):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()


def test_dictator_campaign_provenance_tampering_halts_unscored(
        mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "bad-dictator-lineage"
    shutil.copytree(source, bad)
    d = bad / "a2_s1_n4_b0.01"
    path = d / "dictator.ckpt.json"
    dck = checkpoint.load(str(path))
    dck["record"]["experiment"] = "b2a2-pilot"
    checkpoint.save(str(path), dck)
    _dump_jsonl(d / "dictator.jsonl", [dck["record"]])
    out = tmp_path / "dictator-out"
    with pytest.raises(AnalysisError, match="dictator provenance mismatch"):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()


def test_a6_broadcast_summary_tampering_halts_unscored(mini_root, tmp_path):
    source, preflight = mini_root
    bad = tmp_path / "bad-broadcast"
    shutil.copytree(source, bad)
    path = bad / "a6_a4_s1_n4_b0.01" / "a6_a4.cg.ckpt.json"
    ck = checkpoint.load(str(path))
    ck["outcome"]["broadcast_tv"] = 1.0
    checkpoint.save(str(path), ck)
    out = tmp_path / "broadcast-out"
    with pytest.raises(AnalysisError, match="broadcast path summary mismatch"):
        _mini_analyze(str(bad), preflight, out)
    assert not (out / "TESTSTAMP").exists()


def test_atomic_output_failure_leaves_no_final_or_staging(
        mini_root, tmp_path, monkeypatch):
    root, preflight = mini_root
    out = tmp_path / "atomic"

    def fail(*_args, **_kwargs):
        raise RuntimeError("figure failure")

    monkeypatch.setattr(mod, "make_figures", fail)
    with pytest.raises(RuntimeError, match="figure failure"):
        _mini_analyze(root, preflight, out)
    assert not (out / "TESTSTAMP").exists()
    assert not list(out.glob(".TESTSTAMP.staging-*"))


def test_unmanifested_analysis_artifact_blocks_publication(
        mini_root, tmp_path, monkeypatch):
    root, preflight = mini_root
    out = tmp_path / "unmanifested"
    real_figures = mod.make_figures

    def add_unmanifested(*args, **kwargs):
        made = real_figures(*args, **kwargs)
        Path(args[3], "unexpected.bin").write_bytes(b"unexpected")
        return made

    monkeypatch.setattr(mod, "make_figures", add_unmanifested)
    with pytest.raises(AnalysisError, match="staging is incomplete"):
        _mini_analyze(root, preflight, out)
    assert not (out / "TESTSTAMP").exists()
    # the unmanifested entry cannot be proven analysis-owned: the staging
    # tree is PRESERVED for incident review (never blindly removed), with
    # the foreign artifact intact as evidence
    preserved = list(out.glob(".TESTSTAMP.staging-*"))
    assert len(preserved) == 1
    assert (preserved[0] / "unexpected.bin").read_bytes() == b"unexpected"


@pytest.mark.parametrize("competitor", ("file", "directory", "symlink"))
def test_output_publication_race_never_replaces_appearing_path(
        mini_root, tmp_path, monkeypatch, competitor):
    root, preflight = mini_root
    out = tmp_path / "publication-race"
    real_publish = mod.publish_flat_directory_no_replace

    def inject(staging, destination, *, expected_names, revalidate=None):
        target = Path(destination)
        if competitor == "file":
            target.write_text("preserve\n")
        elif competitor == "directory":
            target.mkdir()
            (target / "operator-owned").write_text("preserve\n")
        else:
            owner = tmp_path / "analysis-owner"
            owner.mkdir()
            (owner / "operator-owned").write_text("preserve\n")
            target.symlink_to(owner, target_is_directory=True)
        return real_publish(
            staging, destination, expected_names=expected_names,
            revalidate=revalidate)

    monkeypatch.setattr(
        mod, "publish_flat_directory_no_replace", inject)
    with pytest.raises(AnalysisError,
                       match="refusing existing publication path"):
        _mini_analyze(root, preflight, out)
    target = out / "TESTSTAMP"
    if competitor == "file":
        assert target.read_text() == "preserve\n"
    else:
        assert (target / "operator-owned").read_text() == "preserve\n"
        assert target.is_symlink() is (competitor == "symlink")
    assert not list(out.glob(".TESTSTAMP.staging-*"))


@pytest.mark.parametrize("mutation", ("extra", "replace"))
def test_output_publication_post_rename_mutation_fails_closed(
        mini_root, tmp_path, monkeypatch, mutation):
    """A mutation striking the published destination between the exclusive
    rename and the final gate must freeze the publication: incomplete
    marker retained, competitor evidence preserved, owned artifacts left
    in place under the marker (rename-first: there is no reservation
    phase and no owned-link teardown)."""
    import experiments.package_a6_holdout as pkg
    root, preflight = mini_root
    out = tmp_path / f"post-rename-{mutation}"
    real_gate = pkg._flat_publication_errors
    calls = {"n": 0}

    def inject(path, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:  # the post-rename destination gate
            if mutation == "extra":
                (path / "operator-owned").write_text("preserve\n")
            else:
                victim = path / "MANIFEST.json"
                victim.unlink()
                victim.write_text("preserve\n")
        return real_gate(path, **kwargs)

    monkeypatch.setattr(pkg, "_flat_publication_errors", inject)
    with pytest.raises(AnalysisError,
                       match="incomplete destination preserved"):
        _mini_analyze(root, preflight, out)
    assert calls["n"] >= 2

    target = out / "TESTSTAMP"
    competitor = (target / "operator-owned" if mutation == "extra"
                  else target / "MANIFEST.json")
    assert competitor.read_text() == "preserve\n"
    assert (target / ".publication-incomplete").read_text() == "incomplete\n"
    assert (target / "cells.csv").is_file()  # owned artifacts preserved
    assert (target / "SUMMARY.md").is_file()
    assert not list(out.glob(".TESTSTAMP.staging-*"))  # tree moved


def test_analyzer_publication_parity_with_package(mini_root, tmp_path,
                                                  monkeypatch):
    """The analyzer publishes through the ONE shared package
    implementation (no analyzer-local fork), passing a final revalidation
    callback that the publisher runs immediately before marker removal."""
    import experiments.package_a6_holdout as pkg
    assert mod.publish_flat_directory_no_replace \
        is pkg.publish_flat_directory_no_replace
    root, preflight = mini_root
    out = tmp_path / "parity"
    seen = {}
    real_publish = pkg.publish_flat_directory_no_replace

    def spy(staging, destination, *, expected_names, revalidate=None):
        seen["revalidate"] = revalidate
        return real_publish(staging, destination,
                            expected_names=expected_names,
                            revalidate=revalidate)

    monkeypatch.setattr(mod, "publish_flat_directory_no_replace", spy)
    _mini_analyze(root, preflight, out)
    assert callable(seen["revalidate"])  # the pre-commit veto is wired
    assert (out / "TESTSTAMP" / "MANIFEST.json").is_file()
    assert not (out / "TESTSTAMP" / ".publication-incomplete").exists()


def test_analyzer_revalidation_failure_preserves_marker(mini_root, tmp_path,
                                                        monkeypatch):
    """If the final revalidation callback rejects, the destination stays
    anchored by the incomplete marker — never markerless."""
    root, preflight = mini_root
    out = tmp_path / "revalidate-veto"
    real_publish = mod.publish_flat_directory_no_replace

    def veto_wrapper(staging, destination, *, expected_names,
                     revalidate=None):
        def veto():
            if revalidate is not None:
                revalidate()
            raise AnalysisError("injected final revalidation veto")

        return real_publish(staging, destination,
                            expected_names=expected_names, revalidate=veto)

    monkeypatch.setattr(mod, "publish_flat_directory_no_replace",
                        veto_wrapper)
    with pytest.raises(AnalysisError,
                       match="incomplete destination preserved"):
        _mini_analyze(root, preflight, out)
    target = out / "TESTSTAMP"
    assert (target / ".publication-incomplete").read_text() == "incomplete\n"
    assert (target / "MANIFEST.json").is_file()


def test_analyzer_pre_rename_cleanup_failure_never_masks(
        mini_root, tmp_path, monkeypatch, capsys):
    """Wrapper-level: a pre-rename publication refusal whose staging
    cleanup ALSO fails must surface the ORIGINAL refusal; the staging tree
    is preserved with a stderr note, never a masking exception."""
    import experiments.package_a6_holdout as pkg
    root, preflight = mini_root
    out = tmp_path / "wrapper-pre-rename"

    def refuse_publication(*_args, **_kwargs):
        raise pkg.PackagingError("refusing existing publication path: X")

    def failing_rollback(_root, _ownership):
        return ["injected analyzer rollback failure"]

    monkeypatch.setattr(
        mod, "publish_flat_directory_no_replace", refuse_publication)
    monkeypatch.setattr(mod, "_rollback_owned_tree", failing_rollback)
    with pytest.raises(AnalysisError,
                       match="refusing existing publication path"):
        _mini_analyze(root, preflight, out)
    err = capsys.readouterr().err
    assert "analysis staging preserved for incident review" in err
    assert "injected analyzer rollback failure" in err
    preserved = list(out.glob(".TESTSTAMP.staging-*"))
    assert len(preserved) == 1  # frozen for review, not blindly removed


def test_analyzer_post_rename_fsync_failure_skips_staging_cleanup(
        mini_root, tmp_path, monkeypatch):
    """Wrapper-level: after the exclusive rename the staging tree MOVED;
    a parent-fsync failure must preserve the marker-anchored destination,
    and the analyzer must not attempt cleanup at the stale staging path."""
    import experiments.package_a6_holdout as pkg
    root, preflight = mini_root
    out = tmp_path / "wrapper-post-rename"
    real_fsync = pkg._fsync_directory
    injected = {"done": False}
    rollbacks = []
    real_rollback = mod._rollback_owned_tree

    def fail_parent_fsync(path):
        if Path(path) == out and not injected["done"]:
            injected["done"] = True
            raise OSError("injected wrapper parent fsync failure")
        return real_fsync(path)

    def spying_rollback(root_path, ownership):
        rollbacks.append(str(root_path))
        return real_rollback(root_path, ownership)

    monkeypatch.setattr(pkg, "_fsync_directory", fail_parent_fsync)
    monkeypatch.setattr(mod, "_rollback_owned_tree", spying_rollback)
    with pytest.raises(AnalysisError,
                       match="incomplete destination preserved"):
        _mini_analyze(root, preflight, out)
    assert injected["done"]
    target = out / "TESTSTAMP"
    assert (target / ".publication-incomplete").read_text() == "incomplete\n"
    assert (target / "MANIFEST.json").is_file()
    assert rollbacks == []  # nothing to clean: the tree moved
    assert not list(out.glob(".TESTSTAMP.staging-*"))


# ==========================================================================
# EI-026: operand-scaled pricing-order tolerance and conservative safety chain
# ==========================================================================
EI026_BOUND = 3255.503129856506
EI026_MODEL_INCUMBENT = 3255.503129876505
EI026_PHYS_INCUMBENT = 3255.503129796989


def _pricing_order_ck(bound, model_incumbent, phys_incumbent, *,
                      sigma=None, z_model=None, epsilon=0.01, budget=240):
    """A minimal but fully valid single-clean-iteration certified A2 checkpoint
    that reaches the pricing-order gate in _replay_cg_certificate_evidence,
    parameterized by the pricing bound and the two incumbents."""
    tag = "a2"
    if z_model is None:
        z_model = phys_incumbent
    ub = z_model
    if sigma is None:
        sigma = bound                       # min_rc_lb = 0 -> certifies
    min_rc_lb = bound - sigma
    min_rc_ub = phys_incumbent - sigma
    lb_ch = ub + min(0.0, min_rc_lb)
    lb_best = lb_ch
    cert_gap = ub - lb_best
    raw_gap = phys_incumbent - bound
    events = [
        {"regime": "cg-seed", "replay_ok": True,
         "solver": {"status": "OPTIMAL"},
         "extra": {"tag": tag, "call_id": f"{tag}-oc0"}},
        {"regime": "cg-pricing", "obj_true": phys_incumbent, "replay_ok": True,
         "solver": {"obj": model_incumbent, "bound": bound,
                    "status": "OPTIMAL"},
         "extra": {"tag": tag, "call_id": f"{tag}-oc1",
                   "column_key": "k", "column_novel": False,
                   "min_reduced_cost_lb": min_rc_lb,
                   "min_reduced_cost_ub": min_rc_ub}},
    ]
    it = {
        "phase": "clean", "oracle_calls": 1, "pricing_solve_id": f"{tag}-oc1",
        "z_rmp_model": z_model, "ub_ch": ub, "duals_sigma": sigma,
        "min_reduced_cost_lb": min_rc_lb, "min_reduced_cost_ub": min_rc_ub,
        "pricing_gap_abs": raw_gap,
        "pricing_gap_rel": raw_gap / max(1e-12, abs(phys_incumbent)),
        "lb_ch": lb_ch, "lb_best": lb_best, "certificate_gap": cert_gap,
        "column_key": "k", "column_novel": False, "n_tangent_refinements": 0,
        "master_solves": [{"solve_id": f"{tag}-it1-rmp-r0",
                           "backend": mod.REQUIRED_BACKEND, "status": "OPTIMAL",
                           "obj": ub, "bound": ub, "n_int": 0}],
    }
    return {
        "done": True, "oracle_calls": 2,
        "identity": {"epsilon": epsilon, "budget": budget},
        "oracle_events": events, "iteration_events": [it],
        "ub_history": [ub], "lb_history": [lb_best], "lb_best": lb_best,
        "outcome": {"type": "certified", "certified": True, "oracle_calls": 2,
                    "ub_ch": ub, "lb_best": lb_best, "gap": cert_gap},
    }


def test_ei026_exact_scalar_case_passes_as_numerical_equality():
    """The exact supplied EI-026 scalars are admitted (the raw negative gap is
    within the operand-scaled tolerance derived from the SAME operands)."""
    ck = _pricing_order_ck(
        EI026_BOUND, EI026_MODEL_INCUMBENT, EI026_PHYS_INCUMBENT)
    cert = mod._replay_cg_certificate_evidence(ck, "ei026")
    assert cert["certified"] is True
    # raw gap preserved exactly; diagnostic normalized to zero
    assert cert["min_raw_pricing_gap"] == pytest.approx(
        EI026_PHYS_INCUMBENT - EI026_BOUND, abs=0, rel=0)
    assert cert["min_pricing_gap_diag"] == 0.0
    # conservative safety certificate holds (does not depend on the slack)
    assert cert["safe_certificate_gap"] <= 0.01 + 1e-9


def test_ei026_ordering_tolerance_scales_with_operands():
    tau_small = mod._ordering_tolerance(1.0, 1.0)
    tau_large = mod._ordering_tolerance(EI026_BOUND, EI026_PHYS_INCUMBENT)
    assert tau_small == 1e-10
    assert tau_large == pytest.approx(1e-10 * EI026_BOUND)


@pytest.mark.parametrize("scale", [1.0, 3255.503129856506, 1.0e6])
def test_ei026_just_inside_and_outside_tolerance_at_scales(scale):
    """Operand-tolerance behavior at small and large objective scales,
    under the EI-027 physical-bridge contract:

    - a physical incumbent below a MODEL-consistent bound is admitted
      (the exact reconstruction adjustment explains it — the EI-027
      pattern), with the claim-bearing safe chain absorbing the full
      allowance;
    - a bound above the MODEL incumbent beyond operand tau is rejected."""
    bound = scale
    tau = 1e-10 * max(1.0, abs(bound))
    # inside: physical below bound by 0.5*tau (raw gap -0.5*tau)
    inside = _pricing_order_ck(bound, bound, bound - 0.5 * tau)
    cert = mod._replay_cg_certificate_evidence(inside, "inside")
    assert cert["certified"] is True
    # EI-027 pattern: physical 2*tau below a model-consistent bound is now
    # ADMITTED (allowance = tau + 2*tau covers it) — verify via the gate
    gate = mod.pricing_order_gate(bound, bound, bound - 2.0 * tau)
    assert gate["errors"] == []
    assert gate["physical_bridge_allowance"] == pytest.approx(3.0 * tau)
    # model-side violation is still rejected at every scale
    with pytest.raises(AnalysisError,
                       match="exceeds the model incumbent"):
        mod._replay_cg_certificate_evidence(
            _pricing_order_ck(bound + 2.0 * tau, bound, bound), "outside")


def test_ei026_raw_recorded_gap_is_checked_exactly():
    """The recorded raw pricing_gap_abs must still recompute exactly."""
    ck = _pricing_order_ck(
        EI026_BOUND, EI026_MODEL_INCUMBENT, EI026_PHYS_INCUMBENT)
    ck["iteration_events"][0]["pricing_gap_abs"] = (
        ck["iteration_events"][0]["pricing_gap_abs"] + 1e-6)
    with pytest.raises(AnalysisError, match="pricing_gap_abs"):
        mod._replay_cg_certificate_evidence(ck, "raw")


def test_ei026_full_raw_model_physical_reconstruction():
    """model - bound, physical - model, and the raw gap all reconstruct with
    the supplied signs and magnitudes; bound<=model and the near-equality with
    the physical incumbent are both accepted."""
    ck = _pricing_order_ck(
        EI026_BOUND, EI026_MODEL_INCUMBENT, EI026_PHYS_INCUMBENT)
    cert = mod._replay_cg_certificate_evidence(ck, "recon")
    assert EI026_MODEL_INCUMBENT - EI026_BOUND > 0            # +2e-8
    assert EI026_PHYS_INCUMBENT - EI026_MODEL_INCUMBENT < 0   # -7.95e-8
    assert cert["min_raw_pricing_gap"] < 0                    # -5.95e-8 raw
    assert cert["min_raw_pricing_gap"] >= -mod._ordering_tolerance(
        EI026_BOUND, EI026_PHYS_INCUMBENT)


def test_ei026_conservative_safe_chain_certifies_or_fails_honestly():
    """The conservative (reduced-bound) chain certifies for a genuinely
    slack certificate and fails honestly for a certificate that only holds
    within the operand-scale slack at the epsilon boundary."""
    # genuine margin: gap far below epsilon -> safe chain certifies
    ck = _pricing_order_ck(100.0, 100.0, 100.0, sigma=100.0, z_model=100.0,
                           epsilon=0.01)
    cert = mod._replay_cg_certificate_evidence(ck, "safe-ok")
    assert cert["certified"] is True
    assert cert["safe_certificate_gap"] <= 0.01 + 1e-9
    # boundary: raw gap == epsilon exactly, so the reduced bound pushes the
    # conservative gap over epsilon -> raw and conservative chains disagree on
    # certification, a hard rejection (no CONSERVATIVE_CERT_TOL slack).
    scale = 1.0e7
    bound = scale
    ck2 = _pricing_order_ck(bound, bound, bound, sigma=bound + 0.01,
                            z_model=bound, epsilon=0.01)
    with pytest.raises(AnalysisError, match="disagree on certification"):
        mod._replay_cg_certificate_evidence(ck2, "safe-boundary")


def test_ei026_audit_analyzer_parity_generic_pricing_order():
    """Audit (_cg_sane) and analyzer (_replay_cg_certificate_evidence) judge
    the SAME generic pricing-order evidence identically via the one shared
    operand-scaled helper: within tolerance both accept, beyond tolerance both
    reject."""
    import experiments.audit_runs as audit_mod
    # within operand tolerance (the EI-026 near-equality): both accept
    ok = _pricing_order_ck(
        EI026_BOUND, EI026_MODEL_INCUMBENT, EI026_PHYS_INCUMBENT)
    assert audit_mod._cg_sane(json.loads(json.dumps(ok))) == []
    cert = mod._replay_cg_certificate_evidence(ok, "parity-ok")
    assert cert["certified"] is True
    # beyond operand tolerance: both reject with a pricing-bound/incumbent error
    bound = 100.0
    tau = 1e-10 * 100.0
    bad = _pricing_order_ck(bound + 100.0 * tau, bound, bound)
    audit_errs = audit_mod._cg_sane(json.loads(json.dumps(bad)))
    assert any("exceeds the model incumbent beyond the operand" in e
               for e in audit_errs)
    with pytest.raises(
            AnalysisError,
            match="exceeds the (model|physical) incumbent"):
        mod._replay_cg_certificate_evidence(bad, "parity-bad")


def test_ei026_inflated_bound_beyond_tolerance_still_rejected():
    """A coordinated bound inflated ABOVE both incumbents beyond the operand
    tolerance is still rejected (existing tamper protection preserved)."""
    bound = 100.0
    tau = 1e-10 * 100.0
    # bound exceeds both incumbents by 100*tau
    ck = _pricing_order_ck(bound + 100.0 * tau, bound, bound)
    with pytest.raises(AnalysisError,
                       match="exceeds the (model|physical) incumbent"):
        mod._replay_cg_certificate_evidence(ck, "inflated")


def _raw_only_ck(scale, epsilon=0.01):
    """A certificate that holds on the RAW bound but not on the reduced bound:
    raw gap just under epsilon by less than tau, so the conservative gap crosses
    epsilon (an EI-026 raw-only certificate)."""
    tau = 1e-10 * scale
    bound = scale
    sigma = bound + epsilon - 0.4 * tau      # raw gap = epsilon - 0.4*tau
    return _pricing_order_ck(bound, bound, bound, sigma=sigma, z_model=bound,
                             epsilon=epsilon)


def test_ei026_raw_only_certificate_rejected_scale5():
    """scale=5: raw gap <= epsilon but conservative gap > epsilon must reject."""
    ck = _raw_only_ck(5.0)
    with pytest.raises(AnalysisError, match="disagree on certification"):
        mod._replay_cg_certificate_evidence(ck, "raw-only-5")


def test_ei026_raw_only_certificate_rejected_audit_and_analyzer_scale1e7():
    """scale=1e7: the audit and analyzer must BOTH reject the same raw-only
    certificate via the one shared conservative replay."""
    import experiments.audit_runs as audit_mod
    ck = _raw_only_ck(1.0e7)
    errs = audit_mod._cg_sane(json.loads(json.dumps(ck)))
    assert any("disagree on certification" in e for e in errs)
    with pytest.raises(AnalysisError, match="disagree on certification"):
        mod._replay_cg_certificate_evidence(ck, "raw-only-1e7")


def test_ei026_csv_uses_conservative_claim_bearing_values(mini_root, tmp_path):
    """Claim-bearing CSV fields use the conservative values while raw_* fields
    preserve the producer history."""
    import csv as _csv
    source, preflight = mini_root
    out = tmp_path / "claim-out"
    _mini_analyze(str(source), preflight, out)
    rows = list(_csv.DictReader(open(out / "TESTSTAMP" / "cells.csv")))
    assert rows
    for r in rows:
        for col in ("raw_lb_best", "raw_final_gap", "raw_uplift_lo",
                    "raw_uplift_hi", "raw_uplift_width", "raw_zd_minus_lb"):
            assert col in r, col
        # claim-bearing lb_best is the conservative (<= raw) lower bound
        assert float(r["lb_best"]) <= float(r["raw_lb_best"]) + 1e-12
        # conservative uplift_hi / final_gap are >= their raw counterparts
        assert float(r["uplift_hi"]) >= float(r["raw_uplift_hi"]) - 1e-12
        assert float(r["final_gap"]) >= float(r["raw_final_gap"]) - 1e-12
        # zd_minus_lb uses the smaller conservative LB, so it is >= raw
        assert float(r["zd_minus_lb"]) >= float(r["raw_zd_minus_lb"]) - 1e-12


# ---------------------------------------------------------------------------
# EI-027: physical-bridge allowance (frozen incident scalars)
# ---------------------------------------------------------------------------
EI027_BOUND = 2417.583855389641
EI027_MODEL_INCUMBENT = 2417.583855389641   # bound == model incumbent
EI027_PHYS_INCUMBENT = 2417.583844628412
EI027_OPERAND_TAU = 2.4175838553896413e-07
EI027_ADJUSTMENT = 1.0761229077616008e-05


def test_ei027_frozen_scalars_accepted_with_exact_gate_values():
    """The exact EI-027 evidence (cell a2 seed=22 n=12 b=0.01 iteration
    24) must pass the shared gate with the exact frozen intermediate
    scalars, and both the analyzer and the audit must certify it."""
    gate = mod.pricing_order_gate(
        EI027_BOUND, EI027_MODEL_INCUMBENT, EI027_PHYS_INCUMBENT)
    assert gate["operand_tau"] == EI027_OPERAND_TAU
    assert gate["reconstruction_adjustment"] == EI027_ADJUSTMENT
    assert gate["physical_bridge_allowance"] == (
        EI027_OPERAND_TAU + EI027_ADJUSTMENT)
    assert gate["safe_bound"] == EI027_BOUND - (
        EI027_OPERAND_TAU + EI027_ADJUSTMENT)
    assert gate["errors"] == []

    ck = _pricing_order_ck(
        EI027_BOUND, EI027_MODEL_INCUMBENT, EI027_PHYS_INCUMBENT)
    cert = mod._replay_cg_certificate_evidence(ck, "ei027")
    assert cert["certified"] is True
    # raw pricing gap preserved exactly (negative by the adjustment)
    assert cert["min_raw_pricing_gap"] == (
        EI027_PHYS_INCUMBENT - EI027_BOUND)
    # audit/analyzer parity through the one shared implementation
    import experiments.audit_runs as audit_mod
    assert audit_mod._cg_sane(json.loads(json.dumps(ck))) == []


def test_ei027_safe_chain_subtracts_full_allowance():
    """Claim-bearing safe bounds use bound - physical_bridge_allowance."""
    ck = _pricing_order_ck(
        EI027_BOUND, EI027_MODEL_INCUMBENT, EI027_PHYS_INCUMBENT)
    conservative = mod.conservative_certificate(ck)
    assert conservative["errors"] == [] and conservative["evaluable"]
    allowance = EI027_OPERAND_TAU + EI027_ADJUSTMENT
    z_model = ck["iteration_events"][0]["z_rmp_model"]
    sigma = ck["iteration_events"][0]["duals_sigma"]
    expected_safe_lb = z_model + min(
        0.0, (EI027_BOUND - allowance) - sigma)
    assert conservative["safe"]["lb_best"] == expected_safe_lb
    # raw chain unchanged: raw lb uses the untouched bound
    expected_raw_lb = z_model + min(0.0, EI027_BOUND - sigma)
    assert conservative["raw"]["lb_best"] == expected_raw_lb


def test_ei027_bridge_never_covers_model_side_inflation():
    """The physical bridge is one-sided: a bound above the MODEL incumbent
    beyond operand tau is rejected regardless of the physical distance."""
    gate = mod.pricing_order_gate(
        EI027_BOUND + 1e-4, EI027_BOUND, EI027_PHYS_INCUMBENT)
    assert any("model incumbent" in e for e in gate["errors"])
    # and a physical incumbent ABOVE the model gains no extra allowance
    # beyond the reconstruction distance itself
    gate = mod.pricing_order_gate(100.0 + 1e-6, 100.0, 100.0 + 2e-7)
    assert any("model incumbent" in e for e in gate["errors"])


def test_ei027_audit_analyzer_parity_on_rejection():
    """Beyond-allowance evidence is rejected identically by the audit and
    the analyzer through the one shared gate."""
    import experiments.audit_runs as audit_mod
    bad = _pricing_order_ck(
        EI027_BOUND + 1e-3, EI027_MODEL_INCUMBENT, EI027_PHYS_INCUMBENT)
    errs = audit_mod._cg_sane(json.loads(json.dumps(bad)))
    assert any("exceeds the model incumbent" in e for e in errs)
    with pytest.raises(AnalysisError,
                       match="exceeds the model incumbent"):
        mod._replay_cg_certificate_evidence(bad, "ei027-bad")


# ---------------------------------------------------------------------------
# EI-027 P1: the FULL-CELL numeric validation must apply the same
# physical-bridge policy as the audit and the certificate replay
# ---------------------------------------------------------------------------
def _frozen_incident_cell():
    """A cell whose cg-pricing event carries the EXACT frozen EI-027
    scalars, with real load-evidence, reconstruction, certificate, and
    dictator consistency at that scale.  The single-price-slot
    construction makes the recomputed model/physical objectives land on
    the frozen doubles exactly (asserted)."""
    inst = fix_builder(1, 4)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    n = market.n_slots
    zeros = [0.0] * n

    def load_evidence(raw, load):
        residual = [raw[t] - load[t] for t in range(n)]
        max_slot = max(range(n), key=lambda t: abs(residual[t]))
        return {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "tolerance_kwh": REPLAY_TOL_KWH,
            "raw_load_kwh": list(raw),
            "residual_kwh": residual,
            "max_abs_residual_kwh": max(abs(x) for x in residual),
            "max_abs_residual_slot": max_slot,
            "raw_min_kwh": min(raw),
            "physical_min_kwh": min(load),
        }

    ck = _pricing_order_ck(
        EI027_BOUND, EI027_MODEL_INCUMBENT, EI027_PHYS_INCUMBENT)
    seed_rec, price_rec = ck["oracle_events"]

    # seed event: posted prices, no charging, trivially ordered
    posted = [float(x) for x in market.price(zeros)]
    seed_rec.update(
        prices=[round(x, 6) for x in posted],
        ops_cost=EI027_PHYS_INCUMBENT, obj_true=EI027_PHYS_INCUMBENT,
        obj_model=EI027_PHYS_INCUMBENT, load=list(zeros), charges=[],
        energy_charged_kwh=0.0)
    seed_rec["solver"].update(
        obj=EI027_PHYS_INCUMBENT, bound=EI027_PHYS_INCUMBENT)
    seed_rec["solver"]["extra"] = {
        "load_reconstruction": load_evidence(zeros, zeros),
        "pricing_objective_reconstruction": {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "prices": posted, "model_obj": EI027_PHYS_INCUMBENT,
            "physical_obj": EI027_PHYS_INCUMBENT, "abs_adjustment": 0.0,
        },
    }

    # frozen pricing event: exact doubles through exact float arithmetic
    ops = 2400.0
    phys_slot = EI027_PHYS_INCUMBENT - ops
    model_slot = EI027_BOUND - ops
    assert ops + phys_slot == EI027_PHYS_INCUMBENT      # exact
    assert ops + model_slot == EI027_BOUND              # exact
    prices = [1.0] + [0.0] * (n - 1)
    load = [phys_slot] + [0.0] * (n - 1)
    raw = [model_slot] + [0.0] * (n - 1)
    price_rec.update(
        prices=[round(x, 6) for x in prices],
        ops_cost=ops, obj_true=EI027_PHYS_INCUMBENT,
        obj_model=EI027_BOUND, load=load,
        charges=[{"slot": 0, "kwh": phys_slot}],
        energy_charged_kwh=phys_slot)
    price_rec["solver"].update(obj=EI027_BOUND, bound=EI027_BOUND)
    price_rec["solver"]["extra"] = dict(
        price_rec["solver"].get("extra") or {},
        load_reconstruction=load_evidence(raw, load),
        pricing_objective_reconstruction={
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "prices": prices, "model_obj": EI027_BOUND,
            "physical_obj": EI027_PHYS_INCUMBENT,
            "abs_adjustment": EI027_ADJUSTMENT,
        })
    assert abs(EI027_BOUND - EI027_PHYS_INCUMBENT) == EI027_ADJUSTMENT

    ck["columns"] = [{
        "load": list(zeros), "charges": [],
        "oracle_stats": {"extra": {
            "load_reconstruction": load_evidence(zeros, zeros)}},
    }]

    # dictator at the same scale: zero load, exact reconstruction
    zd = EI027_PHYS_INCUMBENT + 5.0
    lb_d = zd - 0.005
    dictator_extra = {
        "load_reconstruction": load_evidence(zeros, zeros),
        "adaptive_rounds": 1, "adaptive_lb": lb_d,
        "adaptive_model_obj": zd, "adaptive_ub": zd,
        "adaptive_gap_abs": zd - lb_d, "adaptive_tol_abs": 0.01,
        "adaptive_converged": True, "adaptive_total_wall_s": 0.5,
        "adaptive_solve_stats": [{
            "round": 1, "status": "OPTIMAL", "incumbent": zd,
            "bound": lb_d, "gap": zd - lb_d, "n_vars": 1, "n_int": 1,
            "n_constrs": 1, "wall_s": 0.3, "backend": "GRB",
            "threads": 4}],
        "dictator_objective_reconstruction": {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "raw_true_obj": zd, "physical_obj": zd,
            "abs_adjustment": 0.0},
    }
    drec = {
        "ops_cost": zd, "obj_true": zd, "obj_model": zd,
        "load": list(zeros), "charges": [], "energy_charged_kwh": 0.0,
        "solver": {"backend": "GRB", "status": "OPTIMAL",
                   "extra": dictator_extra},
    }
    dck = {"record": drec, "z_d_ub": zd, "tol_d": 0.01,
           "adaptive": copy.deepcopy(dictator_extra)}
    return ck, dck, inst, market


def _run_frozen_incident_cell(monkeypatch):
    """Drive the REAL _validate_cell_numeric_evidence on the frozen
    incident.  The independent schedule-physics replay and the
    certificate-side safety helpers (covered by their own batteries) are
    stubbed; every numeric gate — load evidence, reconstruction
    bindings, the pricing-order policy, the certificate replay, and the
    dictator block — runs for real."""
    ck, dck, inst, market = _frozen_incident_cell()
    monkeypatch.setattr(mod, "_validate_schedule_evidence",
                        lambda *a, **k: None)
    monkeypatch.setattr(mod, "_validate_retained_column_lineage",
                        lambda *a, **k: None)
    monkeypatch.setattr(mod, "_validate_clean_bound_safety",
                        lambda *a, **k: None)
    monkeypatch.setattr(mod, "_replay_a6_a4_mechanism",
                        lambda *a, **k: None)
    return ck, dck, inst, market


def test_ei027_frozen_incident_passes_full_cell_numeric_evidence(
        monkeypatch):
    """P1 regression: the exact frozen incident must survive the FULL
    cell numeric validation, not merely pricing_order_gate or the
    certificate replay."""
    ck, dck, inst, market = _run_frozen_incident_cell(monkeypatch)
    mod._validate_cell_numeric_evidence(ck, dck, inst, market, "ei027")


def test_ei027_full_cell_rejects_just_beyond_model_tolerance(monkeypatch):
    """Just beyond the model tolerance the full-cell validation still
    rejects (with the reconstruction fields coordinated so only the
    ordering gate can fire)."""
    ck, dck, inst, market = _run_frozen_incident_cell(monkeypatch)
    rec = ck["oracle_events"][1]
    tau = mod._ordering_tolerance(
        EI027_BOUND, EI027_MODEL_INCUMBENT, EI027_PHYS_INCUMBENT)
    inflated = EI027_BOUND + 3.0 * tau
    rec["solver"]["bound"] = inflated
    with pytest.raises(AnalysisError,
                       match="exceeds the model incumbent"):
        mod._validate_cell_numeric_evidence(ck, dck, inst, market, "ei027")


def test_ei027_full_cell_rejects_just_beyond_bridge_allowance(monkeypatch):
    """Just beyond the physical-bridge allowance: with the model incumbent
    raised alongside the bound (so the model gate passes), a bound above
    physical + allowance is impossible without also exceeding the model
    gate; the coordinated variant is caught by the exact
    reconstruction-field bindings instead. Both layers are asserted."""
    # layer 1: bound raised beyond phys + allowance ALSO breaks the model
    # gate (the mathematical implication documented in the incident)
    gate = mod.pricing_order_gate(
        EI027_BOUND + 2e-5, EI027_MODEL_INCUMBENT, EI027_PHYS_INCUMBENT)
    assert any("model incumbent" in e for e in gate["errors"])
    # layer 2: coordinating solver obj/bound together breaks the exact
    # model-objective reconstruction binding in the full-cell path
    ck, dck, inst, market = _run_frozen_incident_cell(monkeypatch)
    rec = ck["oracle_events"][1]
    lifted = EI027_BOUND + 2e-5
    rec["solver"]["bound"] = lifted
    rec["solver"]["obj"] = lifted
    with pytest.raises(AnalysisError, match="solver obj mismatch"):
        mod._validate_cell_numeric_evidence(ck, dck, inst, market, "ei027")
