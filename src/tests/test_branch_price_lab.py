"""Acceptance battery for the tiny external branch-and-price laboratory."""
import math
import os
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab import checkpoint
from egglab.b2a2 import certified_cg
from egglab.branch_price_lab import (
    BASE_ORIGIN_MAIN_SHA,
    ExactnessLabError,
    _fractional_arc,
    arc_key,
    audit_tree,
    canonical_branch_constraints,
    gurobi_available,
    solve_node_lp,
    solve_tree,
    structural_arc,
    structural_arc_catalog,
    structural_incidence,
)
from egglab.enumerate_tiny import enumerated_ch, enumerated_dictator
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.regimes import solve_dictator


TREE_EPSILON = 1e-2
TREE_PWL_TOL = 1e-4
A2_EPSILON = 1e-2
A2_PWL_TOL = 1e-4
# The independent enumerator has a 1e-4 tangent tolerance.  This allowance
# combines that certificate with the tighter tree and A2 tolerances.
TRUTH_TOL = 2e-4


@pytest.fixture(scope="module")
def tiny():
    inst = synthetic_instance(seed=1, n_trips=4, max_vehicles=2)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    return inst, market


@pytest.fixture(scope="module")
def truth(tiny):
    inst, market = tiny
    return enumerated_ch(inst, market), enumerated_dictator(inst, market)


@pytest.fixture(scope="module")
def a2_root(tiny, tmp_path_factory):
    inst, market = tiny
    return certified_cg(
        inst,
        market,
        epsilon=A2_EPSILON,
        pwl_tol=A2_PWL_TOL,
        budget=200,
        out_dir=str(tmp_path_factory.mktemp("tiny-a2-root")),
        tag="a2",
        solver_kw={"max_mip_gap": 1e-9},
    )


@pytest.fixture(scope="module")
def tree_run(tiny, tmp_path_factory):
    inst, market = tiny
    out = str(tmp_path_factory.mktemp("tiny-branch-price"))
    state = solve_tree(
        inst,
        market,
        out,
        epsilon=TREE_EPSILON,
        pwl_tol=TREE_PWL_TOL,
    )
    return state, out


def _root_outcome(state):
    return state["nodes"]["n0000"]["lp_outcome"]


def _call_signature(node_state):
    return [
        (
            call["call_id"],
            call["solver"]["status"],
            None if call["column"] is None else call["column"]["column_key"],
            call.get("lower_bound_best"),
            call.get("upper_bound"),
        )
        for call in node_state["pricing_calls"]
    ]


def _assert_nested_equal(actual, expected):
    if isinstance(expected, dict):
        assert set(actual) == set(expected)
        for key in expected:
            _assert_nested_equal(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for got, want in zip(actual, expected):
            _assert_nested_equal(got, want)
    elif isinstance(expected, float):
        assert float(actual) == pytest.approx(expected, abs=1e-9)
    else:
        assert actual == expected


def test_gurobi_is_optional_for_cbc_only_collection():
    requirements = (
        Path(__file__).resolve().parents[1] / "requirements.txt"
    ).read_text().splitlines()
    assert not any(line.strip().startswith("gurobipy") for line in requirements)
    code = """
import sys
sys.modules["gurobipy"] = None
import egglab.branch_price_lab as lab
assert not lab.gurobi_available()
try:
    lab._new_model("must-not-start")
except lab.ExactnessLabError as exc:
    assert "optional 'gurobipy'" in str(exc)
else:
    raise AssertionError("missing optional dependency did not fail locally")
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert gurobi_available()  # this test environment exercises the lab too


def test_exact_base_sha_is_recorded(tree_run):
    state, _out = tree_run
    assert BASE_ORIGIN_MAIN_SHA == (
        "5b63e725d0fd85cfb0b83f462a612016e7f4321a"
    )
    assert state["identity"]["base_origin_main_sha"] == BASE_ORIGIN_MAIN_SHA


def test_root_bounds_agree_with_certified_a2(tree_run, a2_root, truth):
    state, _out = tree_run
    root = _root_outcome(state)
    a2 = a2_root["outcome"]
    z_ch = truth[0]["z_ch"]

    assert root["certified"] and a2["certified"]
    assert root["upper_bound"] - root["lower_bound"] <= TREE_EPSILON
    assert a2["ub_ch"] - a2["lb_best"] <= A2_EPSILON
    assert max(root["lower_bound"], a2["lb_best"]) <= (
        min(root["upper_bound"], a2["ub_ch"]) + TRUTH_TOL
    )
    assert root["lower_bound"] - TRUTH_TOL <= z_ch
    assert z_ch <= root["upper_bound"] + TRUTH_TOL
    assert a2["lb_best"] - TRUTH_TOL <= z_ch
    assert z_ch <= a2["ub_ch"] + TRUTH_TOL


@pytest.mark.parametrize(
    "seed,n_trips,max_vehicles",
    [
        (0, 4, 2),
        # Seed 11 has no time-feasible path cover at n=4/max_vehicles=2.
        (11, 3, 2),
        (15, 4, 2),
    ],
)
def test_burned_seed_cross_validation(
    seed, n_trips, max_vehicles, tmp_path
):
    inst = synthetic_instance(
        seed=seed,
        n_trips=n_trips,
        max_vehicles=max_vehicles,
    )
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    enum_ch = enumerated_ch(inst, market)
    enum_d = enumerated_dictator(inst, market)
    compact = solve_dictator(
        inst, market, tol_abs=TREE_EPSILON, max_mip_gap=1e-9
    )
    a2 = certified_cg(
        inst,
        market,
        epsilon=TREE_EPSILON,
        pwl_tol=TREE_PWL_TOL,
        budget=200,
        out_dir=str(tmp_path / "a2"),
        tag="a2",
        solver_kw={"max_mip_gap": 1e-9},
    )
    tree_out = str(tmp_path / "tree")
    tree = solve_tree(
        inst,
        market,
        tree_out,
        epsilon=TREE_EPSILON,
        pwl_tol=TREE_PWL_TOL,
    )
    root = _root_outcome(tree)
    a2_outcome = a2["outcome"]

    assert max(root["lower_bound"], a2_outcome["lb_best"]) <= min(
        root["upper_bound"], a2_outcome["ub_ch"]
    ) + TRUTH_TOL
    assert root["lower_bound"] - TRUTH_TOL <= enum_ch["z_ch"]
    assert enum_ch["z_ch"] <= root["upper_bound"] + TREE_EPSILON
    compact_lower = compact.stats.extra["adaptive_lb"]
    assert compact_lower - TRUTH_TOL <= enum_d["z_d"]
    assert enum_d["z_d"] <= compact.obj_true + TRUTH_TOL
    assert tree["outcome"]["global_bound"] - TRUTH_TOL <= enum_d["z_d"]
    assert enum_d["z_d"] <= (
        tree["outcome"]["incumbent_upper_bound"] + TRUTH_TOL
    )
    assert audit_tree(inst, tree, tree_out) == []


def test_seed11_n4_is_documented_infeasible(tmp_path):
    inst = synthetic_instance(seed=11, n_trips=4, max_vehicles=2)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    tree = solve_tree(inst, market, str(tmp_path))
    assert tree["outcome"]["status"] == "infeasible"
    assert tree["nodes"]["n0000"]["lp_outcome"]["status"] == "infeasible"


def test_final_incumbent_and_global_bound_match_complete_truth(tree_run, truth):
    state, _out = tree_run
    result = state["outcome"]
    z_dictator = truth[1]["z_d"]

    assert result["status"] == "optimal"
    assert result["certified"]
    assert result["global_bound"] <= result["incumbent_upper_bound"] + 1e-9
    assert result["gap"] <= TREE_EPSILON
    assert abs(result["incumbent_objective"] - z_dictator) <= TRUTH_TOL
    assert result["global_bound"] <= z_dictator + TRUTH_TOL
    assert z_dictator <= result["incumbent_upper_bound"] + TRUTH_TOL
    assert TREE_EPSILON > (
        result["tolerance_evidence"]["accumulated_objective_allowance"]
    )


def test_genuinely_fractional_root_closes_in_one_split(tree_run):
    state, _out = tree_run
    root = state["nodes"]["n0000"]
    assert root["status"] == "branched"
    assert len(state["branch_history"]) == 1
    branch = state["branch_history"][0]
    assert 1e-3 < branch["fractional_value"] < 1.0 - 1e-3
    assert state["outcome"]["nodes"] == 3
    assert state["outcome"]["max_depth"] == 1

    children = [state["nodes"][child] for child in branch["children"]]
    assert {child["branch"]["value"] for child in children} == {0, 1}
    assert all(child["branch"]["arc"] == branch["arc"] for child in children)
    assert all(child["status"] in {"integral", "bound_pruned"} for child in children)


def test_deeper_external_tree_closes_tiny_truth(tmp_path):
    inst = synthetic_instance(seed=9, n_trips=4, max_vehicles=2)
    market = make_affine_market(inst, shape="duck", b_scale=0.2)
    enum_d = enumerated_dictator(inst, market)
    state = solve_tree(
        inst,
        market,
        str(tmp_path),
        epsilon=TREE_EPSILON,
        pwl_tol=TREE_PWL_TOL,
    )
    assert state["outcome"]["status"] == "optimal"
    assert state["outcome"]["branches"] >= 2
    assert state["outcome"]["max_depth"] >= 2
    assert state["outcome"]["global_bound"] <= enum_d["z_d"] + TRUTH_TOL
    assert enum_d["z_d"] <= (
        state["outcome"]["incumbent_upper_bound"] + TRUTH_TOL
    )


def test_all_nodes_columns_and_leaf_replay_physically(tree_run, tiny):
    state, out = tree_run
    inst, _market = tiny
    assert audit_tree(inst, state, out) == []

    recorded_calls = 0
    for node_id, node in state["nodes"].items():
        node_state = checkpoint.load(
            os.path.join(out, "nodes", node_id, "node.ckpt.json")
        )
        assert node_state["identity"]["branch_constraints"] == (
            node["branch_constraints"]
        )
        for event in node_state["pricing_calls"]:
            recorded_calls += 1
            assert event["solver"]["backend"] == "GRB"
            assert event["branch_constraints"] == node["branch_constraints"]
            if event["column"] is not None:
                assert event["replay_ok"]
                allowance = event["tolerance_evidence"][
                    "pricing_bound_allowance"
                ]
                assert event["pricing_bound"] <= (
                    event["physical_objective"] + allowance
                )
                assert event["tolerance_evidence"][
                    "pricing_bound_le_physical_plus_allowance"
                ]
                assert event["tolerance_evidence"][
                    "charge_dropped_positive_kwh"
                ] == 0.0
        for master_event in node_state["master_events"]:
            assert all(
                solve["backend"] == "GRB"
                and solve["n_int"] == 0
                and solve["status"] == "OPTIMAL"
                for solve in master_event["rmp"]["master_solves"]
            )
            tolerance = master_event["rmp"]["tolerance_evidence"]
            assert tolerance["pwl_model_slack"] <= (
                tolerance["pwl_model_limit"]
            )
    assert recorded_calls == state["outcome"]["pricing_calls"]


def test_tolerance_budget_rejects_narrow_final_gap(tiny, tmp_path):
    inst, market = tiny
    with pytest.raises(
        ExactnessLabError, match="not wider than the declared numerical"
    ):
        solve_tree(
            inst,
            market,
            str(tmp_path),
            epsilon=1e-5,
            pwl_tol=1e-6,
        )


def test_integral_leaf_is_independent_continuous_charge_average(tree_run):
    state, _out = tree_run
    leaves = [
        node for node in state["nodes"].values() if node["status"] == "integral"
    ]
    assert len(leaves) == 1
    realization = leaves[0]["realization"]
    assert realization["replay_ok"]
    assert not realization["replay_violations"]
    # This fixture genuinely uses a convex mixture of charging realizations
    # with one common structure; no arbitrary positive lambda was selected.
    assert len(realization["source_weights"]) >= 2
    assert sum(row["lambda"] for row in realization["source_weights"]) == (
        pytest.approx(1.0, abs=1e-10)
    )
    assert realization["master_load_max_abs_residual"] <= (
        realization["conversion_tolerance"]
    )
    assert realization["master_objective_abs_residual"] <= (
        realization["conversion_tolerance"]
    )


def test_label_invariant_aggregate_incidence(tiny):
    inst, _market = tiny
    trip_ids = [trip.id for trip in inst.trips]
    catalog = {arc_key(arc): arc for arc in structural_arc_catalog(inst)}
    sequences = [trip_ids[:2], trip_ids[2:]]
    kinds = []
    for sequence in sequences:
        row = []
        for tail, head in zip(sequence, sequence[1:]):
            direct = arc_key(structural_arc("dir", tail, head))
            depot = arc_key(structural_arc("dep", tail, head))
            row.append("dir" if direct in catalog else "dep")
            assert direct in catalog or depot in catalog
        kinds.append(row)
    original = structural_incidence(inst, sequences, kinds)
    relabeled = structural_incidence(
        inst, list(reversed(sequences)), list(reversed(kinds))
    )
    assert original == relabeled


def test_full_fleet_oracle_certifies_infeasible_node(tiny, tmp_path):
    inst, market = tiny
    # Every nonempty path cover has a pull-out.  Forbidding all pull-outs makes
    # the complete schedule universe empty; this is not a pool-filter claim.
    branch = [
        {
            "arc": structural_arc("out", None, trip.id),
            "value": 0,
        }
        for trip in inst.trips
    ]
    state = solve_node_lp(
        inst,
        market,
        branch,
        str(tmp_path),
        node_id="infeasible",
        epsilon=TREE_EPSILON,
        pwl_tol=TREE_PWL_TOL,
    )
    assert state["outcome"]["status"] == "infeasible"
    assert state["outcome"]["certified"] is True
    assert state["outcome"]["evidence_tier"] == "solver-attested"
    assert state["outcome"]["pricing_calls"] == 1
    assert state["outcome"]["certificate_call_id"] == "infeasible-seed"
    event = state["pricing_calls"][0]
    assert event["solver"]["status"] == "INFEASIBLE"
    assert event["solver"]["backend"] == "GRB"
    assert event["infeasibility_certified"]
    assert event["column"] is None
    assert event["branch_constraints"] == canonical_branch_constraints(
        inst, branch
    )


def test_genuinely_infeasible_child_extends_feasible_parent(tmp_path):
    inst = synthetic_instance(seed=1, n_trips=4, max_vehicles=1)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    parent_branch = [
        {
            "arc": structural_arc("out", None, inst.trips[0].id),
            "value": 1,
        }
    ]
    child_branch = parent_branch + [
        {
            "arc": structural_arc("out", None, inst.trips[1].id),
            "value": 1,
        }
    ]
    parent = solve_node_lp(
        inst,
        market,
        parent_branch,
        str(tmp_path / "parent"),
        node_id="parent",
    )
    child = solve_node_lp(
        inst,
        market,
        child_branch,
        str(tmp_path / "child"),
        node_id="child",
    )
    assert parent["outcome"]["status"] == "certified"
    assert child["outcome"]["status"] == "infeasible"
    assert child["pricing_calls"][0]["solver"]["status"] == "INFEASIBLE"
    assert child["pricing_calls"][0]["infeasibility_certified"]
    assert len(child["identity"]["branch_constraints"]) == (
        len(parent["identity"]["branch_constraints"]) + 1
    )


def test_degenerate_tied_pricing_certifies_without_false_ambiguity(tmp_path):
    inst = synthetic_instance(seed=1, n_trips=4, max_vehicles=2)
    market = make_affine_market(
        inst,
        shape="flat",
        a_level=0.0,
        a_amp=0.0,
        b_scale=0.0,
        base_load_level=0.0,
    )
    state = solve_node_lp(
        inst,
        market,
        [],
        str(tmp_path),
        node_id="tie",
    )
    final_call = state["pricing_calls"][-1]
    assert state["outcome"]["status"] == "certified"
    assert final_call["min_reduced_cost_upper"] == pytest.approx(0.0)
    assert final_call["min_reduced_cost_lower_solver"] == pytest.approx(0.0)
    assert final_call["column_novel"] is False
    assert final_call["column"]["charges"]  # charging timing is genuinely tied


def test_near_integral_branching_band_is_explicit(tiny):
    inst, _market = tiny
    catalog = structural_arc_catalog(inst)
    keys = [arc_key(arc) for arc in catalog]
    selected = catalog[0]
    key = arc_key(selected)
    tol = 1e-8

    inside_zero = {arc_key_: 0.0 for arc_key_ in keys}
    inside_zero[key] = 0.5 * tol
    assert _fractional_arc(inst, inside_zero, [], tol) is None

    outside_zero = dict(inside_zero)
    outside_zero[key] = 2.0 * tol
    branch = _fractional_arc(inst, outside_zero, [], tol)
    assert branch is not None
    assert branch[0] == selected
    assert branch[1] == pytest.approx(2.0 * tol)

    outside_one = {arc_key_: 0.0 for arc_key_ in keys}
    outside_one[key] = 1.0 - 2.0 * tol
    branch = _fractional_arc(inst, outside_one, [], tol)
    assert branch is not None
    assert branch[1] == pytest.approx(1.0 - 2.0 * tol)


def test_tree_resume_preserves_calls_frontier_and_result(
    tiny, tree_run, tmp_path
):
    inst, market = tiny
    uninterrupted, uninterrupted_out = tree_run
    paused = solve_tree(
        inst,
        market,
        str(tmp_path),
        epsilon=TREE_EPSILON,
        pwl_tol=TREE_PWL_TOL,
        max_work_items=1,
    )
    assert not paused["done"]
    assert paused["frontier"] == {
        "queued": [],
        "open_best_bound": ["n0000"],
    }
    paused_root = checkpoint.load(
        os.path.join(tmp_path, "nodes", "n0000", "node.ckpt.json")
    )
    before_calls = _call_signature(paused_root)
    before_bounds = (
        list(paused_root["lower_history"]),
        list(paused_root["upper_history"]),
    )

    resumed = solve_tree(
        inst,
        market,
        str(tmp_path),
        epsilon=TREE_EPSILON,
        pwl_tol=TREE_PWL_TOL,
    )
    resumed_root = checkpoint.load(
        os.path.join(tmp_path, "nodes", "n0000", "node.ckpt.json")
    )
    assert _call_signature(resumed_root) == before_calls
    assert (
        resumed_root["lower_history"],
        resumed_root["upper_history"],
    ) == before_bounds
    _assert_nested_equal(resumed["outcome"], uninterrupted["outcome"])
    assert [
        (record["node_id"], record["arc"], record["fractional_value"])
        for record in resumed["branch_history"]
    ] == [
        (record["node_id"], record["arc"], record["fractional_value"])
        for record in uninterrupted["branch_history"]
    ]
    assert {
        node_id: (
            node["status"],
            node["branch_constraints"],
            node["children"],
        )
        for node_id, node in resumed["nodes"].items()
    } == {
        node_id: (
            node["status"],
            node["branch_constraints"],
            node["children"],
        )
        for node_id, node in uninterrupted["nodes"].items()
    }
    assert audit_tree(inst, resumed, str(tmp_path)) == []
    assert audit_tree(inst, uninterrupted, uninterrupted_out) == []


@pytest.mark.parametrize(
    "phase,checkpoint_phase,persisted_calls",
    [
        ("seed", "seed", 0),
        ("master", "master", 1),
        ("pricing", "pricing", 1),
    ],
)
def test_node_resume_from_uncommitted_phase_solve(
    tiny, tmp_path, phase, checkpoint_phase, persisted_calls
):
    inst, market = tiny
    reference = solve_node_lp(
        inst,
        market,
        [],
        str(tmp_path / "reference"),
        node_id="phase",
    )
    interrupted_dir = tmp_path / phase
    with pytest.raises(KeyboardInterrupt, match=phase):
        solve_node_lp(
            inst,
            market,
            [],
            str(interrupted_dir),
            node_id="phase",
            _interrupt_after_solve=phase,
        )
    interrupted = checkpoint.load(interrupted_dir / "node.ckpt.json")
    assert interrupted["phase"] == checkpoint_phase
    assert len(interrupted["pricing_calls"]) == persisted_calls

    resumed = solve_node_lp(
        inst,
        market,
        [],
        str(interrupted_dir),
        node_id="phase",
    )
    _assert_nested_equal(resumed["outcome"], reference["outcome"])
    call_ids = [call["call_id"] for call in resumed["pricing_calls"]]
    assert len(call_ids) == len(set(call_ids))
    assert call_ids == [
        call["call_id"] for call in reference["pricing_calls"]
    ]


def test_rejects_non_tiny_instance_before_solving(tmp_path):
    inst = synthetic_instance(seed=1, n_trips=5, max_vehicles=3)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    with pytest.raises(ExactnessLabError, match="n <= 4"):
        solve_tree(inst, market, str(tmp_path))
    assert not (tmp_path / "tree.ckpt.json").exists()
