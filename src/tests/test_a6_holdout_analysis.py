"""Focused regression battery for the frozen A6 holdout closeout."""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from egglab import checkpoint
from egglab.a6 import (A6_K_MAX, A6_PRIORITY, A6_THETA_CERT_MULT,
                       A6_SCHEMA_VERSION, DEFAULT_CANDIDATE)
from egglab.b2a2 import (MAX_DUPLICATE_RETRIES, MAX_PRICING_ESCALATIONS,
                         PWL_TOL, RC_TOL, SCHEMA_VERSION, market_hash)
from egglab.b2a345 import stab_identity_params
from egglab.evsp import LOAD_RECONSTRUCTION_POLICY_VERSION, REPLAY_TOL_KWH
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
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


def _event(*, method, inst_hash, n_slots, regime, call_id, trigger=False):
    extra = {"tag": method, "call_id": call_id}
    if trigger:
        extra.update(call_kind="clean", trigger_selected="T4",
                     triggers_fired=["T4"])
    return {
        "experiment": "a6-holdout", "regime": regime,
        "git_commit": RUN_COMMIT[:7], "mip_version": "1.17.6",
        "instance_hash": inst_hash, "prices": [0.0] * n_slots,
        "load": [0.0] * n_slots, "charges": [],
        "energy_charged_kwh": 0.0, "ops_cost": 10.0,
        "obj_model": 10.0, "obj_true": 10.0,
        "replay_ok": True, "extra": extra,
        "solver": {"backend": "GRB", "status": "OPTIMAL",
                   "wall_s": 0.1, "lp_wall_s": 0.0,
                   "extra": {
                       "load_reconstruction": _load_evidence(n_slots),
                       "pricing_objective_reconstruction": {
                           "policy_version":
                               LOAD_RECONSTRUCTION_POLICY_VERSION,
                           "prices": [0.0] * n_slots,
                           "model_obj": 10.0,
                           "physical_obj": 10.0,
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
    zd = 11.0
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
    seed_event = _event(method=method, inst_hash=inst.hash(),
                        n_slots=inst.n_slots,
                        regime="cg-seed", call_id=f"{method}-oc0")
    clean_event = _event(
        method=method, inst_hash=inst.hash(), n_slots=inst.n_slots,
        regime="cg-pricing",
        call_id=f"{method}-oc1", trigger=method == A6_METHOD)
    iteration = {
        "record_kind": "cg-iteration", "phase": "clean",
        "method": method, "iteration_id": f"{method}-it1",
        "experiment": "a6-holdout", "git_commit": RUN_COMMIT[:7],
        "mip_version": "1.17.6", "terminal": False,
        "pricing_solve_id": f"{method}-oc1", "certificate_gap": 0.005,
        "master_solves": [{
            "solve_id": f"{method}-rmp1", "status": "OPTIMAL",
            "obj": 10.0, "bound": 10.0, "wall_s": 0.2, "n_int": 0,
        }],
    }
    if method == A6_METHOD:
        iteration.update(
            gap_at_decision=1.0, k_since_clean=0, recovery_active=False,
            triggers_fired=["T4"], trigger_selected="T4",
            call_kind="clean", column_novel=True,
            min_reduced_cost_ub=-1.0)
    outcome = {
        "type": "certified", "ub_ch": 10.0, "lb_best": 9.995,
        "gap": 0.005, "certified": True, "oracle_calls": calls,
        "oracle_calls_clean": calls, "oracle_calls_stab": 0,
        "broadcast_tv": 0.0, "broadcast_linf_max": 0.0,
        "broadcast_points": 2,
        "uplift_interval": [0.99, 1.005],
    }
    if method == A6_METHOD:
        outcome["method"] = method
        outcome["trigger_selected_counts"] = {"T4": 1}
    ck = {
        "identity": identity, "done": True, "outcome": outcome,
        "oracle_calls": calls, "calls_clean": calls, "calls_stab": 0,
        "lb_best": 9.995, "ub_history": [10.0], "lb_history": [9.995],
        "columns": [{
            "column_key": "x", "load": [0.0] * inst.n_slots,
            "charges": [], "energy_charged_kwh": 0.0,
            "ops_cost": 10.0, "oracle_stats": seed_event["solver"],
        }],
        "oracle_events": [seed_event, clean_event],
        "iteration_events": [iteration],
    }
    if method == A6_METHOD:
        ck["stab"] = {"serious_steps": 0, "null_steps": 0}
    checkpoint.save(str(d / f"{method}.cg.ckpt.json"), ck)
    _dump_jsonl(d / f"{method}.oracle.jsonl", ck["oracle_events"])
    _dump_jsonl(d / f"{method}.iterations.jsonl", ck["iteration_events"])

    drec = {
        "experiment": "a6-holdout", "regime": "dictator",
        "git_commit": RUN_COMMIT[:7], "mip_version": "1.17.6",
        "instance_hash": inst.hash(), "replay_ok": True,
        "load": [0.0] * inst.n_slots, "charges": [],
        "energy_charged_kwh": 0.0, "ops_cost": zd,
        "obj_model": zd, "obj_true": zd,
        "solver": {"backend": "GRB", "status": "OPTIMAL",
                   "wall_s": 0.3, "lp_wall_s": 0.0,
                   "extra": {
                       "load_reconstruction": _load_evidence(inst.n_slots),
                       "dictator_objective_reconstruction": {
                           "policy_version":
                               LOAD_RECONSTRUCTION_POLICY_VERSION,
                           "raw_true_obj": zd,
                           "physical_obj": zd,
                           "abs_adjustment": 0.0,
                       },
                   }},
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
        "bound": 10.99,
        "adaptive": {"adaptive_total_wall_s": 0.5,
                     "adaptive_converged": True},
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
    cells = [(m, *i) for m in METHODS for i in MINI_INSTANCES]
    for index, (method, seed, n, b) in enumerate(cells):
        _write_cell(root, method, seed, n, b, index, preflight,
                    calls=2)
    return str(root), preflight


def _mini_analyze(root, preflight, out_base, stamp="TESTSTAMP"):
    return analyze(
        root, str(out_base), stamp, "analysis0",
        selection_path=mod.DEFAULT_SELECTION,
        instances=MINI_INSTANCES, instance_builder=fix_builder,
        verify_code_commit=False, verify_selection_git=False,
        verify_experiment_commit=False, require_frozen_grid=False,
        preflight_validator=lambda _p, instances: preflight)


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
    return {"oracle_calls": calls, "identity": {"epsilon": 0.01},
            "outcome": {"type": kind, "certified": certified,
                        "oracle_calls": calls, "gap": gap}}


def test_scoring_including_terminal_budget_certificate():
    assert score_outcome(_score_ck("certified", True, 17, 0.001), "x") == 17
    assert score_outcome(
        _score_ck("budget_exhausted", True, 240, 0.001), "x") == 240
    assert score_outcome(
        _score_ck("budget_exhausted", False, 240, 0.02), "x") == 241
    with pytest.raises(AnalysisError):
        score_outcome(_score_ck("budget_exhausted", False, 239, 0.02), "x")


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
