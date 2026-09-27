"""Adversarial frontier tests; no native optimizer is run by this module."""
import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from experiments import reuse_frontier as rf
from egglab import b2a2, regimes
from egglab.enumerate_tiny import enumerate_structures
from egglab.evsp import Solution, LOAD_RECONSTRUCTION_POLICY_VERSION, REPLAY_TOL_KWH
from egglab.solver import SolveStats


def solution(prices=None):
    inst = rf.fixture("depleted_f20")
    prices = prices or [0.3] * inst.n_slots
    load = [0.0, 6.25, 6.25, 0.0, 6.25, 6.25, 0.0]
    value = 20.0 + sum(p*e for p, e in zip(prices, load))
    return Solution(sequences=[["t0", "t1", "t2"]], arc_kinds=[["dep", "dep"]],
        charges=[{"vehicle": 0, "after_trip": "t0" if t < 3 else "t1",
                  "before_trip": "t1" if t < 3 else "t2", "slot": t, "kwh": 6.25}
                 for t in (1, 2, 4, 5)], load=load, fleet=1, ops_cost=20.0,
        obj_model=value, obj_true=value,
        stats=SolveStats(backend="CBC", status="OPTIMAL", obj=value, bound=value,
            extra={"load_reconstruction": {"policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
                                           "tolerance_kwh": REPLAY_TOL_KWH}}))


def predecessor(arm="retained"):
    name = "depleted_f20"
    inst = rf.fixture(name)
    return {"schema": rf.SCHEMA, "config_sha256": rf.digest(rf.CONFIG),
            "fixture": name, "arm": arm, "state_index": 0, "status": "certified",
            "instance_hash": inst.hash(), "market_hash": b2a2.market_hash(rf.market_for_state(name, 0)),
            "columns": [b2a2.column_from_solution(inst, solution())],
            "last_clean_price": [0.3, 1.55, 1.55, 0.3, 1.55, 1.55, 0.3],
            "lower": 1e12, "tangent_points": [[999.0] * inst.n_slots]}


def test_frozen_grid_has_competing_fleets_and_charge_opportunities():
    inst = rf.fixture("depleted_f20")
    structures = enumerate_structures(inst)
    assert {len(s["sequences"]) for s in structures} == {1, 2}
    assert len(structures) <= rf.CONFIG["reference_structure_cap"]
    # A valid one-bus realization charges in four hourly opportunities.
    col = predecessor()["columns"][0]
    assert rf.replay_column(inst, col)["load"] == [0, 6.25, 6.25, 0, 6.25, 6.25, 0]


def test_replenishment_markers_force_two_terminal_chains():
    inst = rf.fixture("replenished_two_bus")
    structures = enumerate_structures(inst)
    assert structures and len(structures) <= rf.CONFIG["reference_structure_cap"]
    assert all(len(s["sequences"]) == 2 for s in structures)
    assert all({seq[-1] for seq in s["sequences"]} == {"marker0", "marker1"} for s in structures)
    assert inst.soc_end_kwh == inst.battery_kwh == inst.soc0_kwh
    assert sum(t.energy_kwh for t in inst.trips) == 45.0


def test_fixed_paths_include_identity_reversal_and_return():
    for name in rf.FIXTURES:
        markets = [rf.market_for_state(name, i) for i in range(5)]
        assert list(markets[0].a) == list(markets[1].a) == list(markets[4].a)
        assert min(markets[2].a) > 0 and min(markets[3].a) > 0
        assert list(markets[2].a + markets[3].a) == pytest.approx(list(2*markets[0].a))


@pytest.mark.parametrize("field,value", [
    ("schema", "old"), ("fixture", "depleted_f26"), ("arm", "cold"),
    ("state_index", 1), ("status", "failed"), ("instance_hash", "wrong"),
    ("market_hash", "wrong"), ("config_sha256", "wrong")])
def test_predecessor_identity_rejection(field, value):
    prior = predecessor()
    prior[field] = value
    with pytest.raises(ValueError, match="predecessor"):
        rf.import_previous(rf.fixture("depleted_f20"), prior, "depleted_f20", "retained", 1)


def test_import_copies_physics_without_stale_bounds():
    prior = predecessor()
    cols = rf.import_previous(rf.fixture("depleted_f20"), prior, "depleted_f20", "retained", 1)
    assert isinstance(cols, list)
    cols[0]["load"][1] = -1
    assert prior["columns"][0]["load"][1] == 6.25


def test_projection_novelty_reports_roundoff_as_same():
    col = predecessor()["columns"][0]
    near = copy.deepcopy(col)
    near["load"][1] += 1e-12
    assert not rf.projection_novel(near, [col])
    near["load"][1] += 1e-3
    assert rf.projection_novel(near, [col])


def fake_master(inst, market, columns, tangent_points, **kwargs):
    assert tangent_points == []
    return {"z_model": 43.124, "ub": 43.125, "L": [0, 6.25, 6.25, 0, 6.25, 6.25, 0],
            "lambdas": [1.0], "pi": [-0.3, -1.55, -1.55, -0.3, -1.55, -1.55, -0.3],
            "sigma": 58.75, "tangent_points": [], "master_solves": []}


def test_clean_bound_ignores_proposal_bound(monkeypatch, tmp_path):
    calls = []
    def fake_taker(inst, prices, **kwargs):
        sol = solution(list(prices))
        if not calls:
            sol.stats.bound = -1e9
        calls.append(prices)
        return sol
    monkeypatch.setattr(regimes, "solve_taker", fake_taker)
    monkeypatch.setattr(b2a2, "solve_rmp", fake_master)
    result = rf.solve_state("depleted_f20", "retained_shift", 1,
                            predecessor("retained_shift"), tmp_path / "state.json")
    assert result["status"] == "certified", result.get("error")
    assert result["lower"] == pytest.approx(43.124)
    assert result["calls_proposal"] == result["calls_clean"] == 1
    assert result["proposal"]["used_for_lower_bound"] is False
    assert result["proposal"]["projection_novel"] is False
    assert result["reference_validation"] == "pending separate reference phase"


def test_failed_pricing_attempt_is_preserved_and_counted(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise RuntimeError("deliberate fake failure")
    monkeypatch.setattr(regimes, "solve_taker", fail)
    result = rf.solve_state("depleted_f20", "cold", 0, None, tmp_path / "state.json")
    assert result["status"] == "failed"
    assert result["oracle_calls"] == result["calls_seed"] == 1
    assert result["oracle_events"][0]["status"] == "started"
    assert "deliberate fake failure" in result["error"]


@pytest.mark.parametrize("mutation", ["weight", "load", "upper", "lower"])
def test_master_replay_rejects_bad_upper_bound(mutation):
    inst = rf.fixture("depleted_f20")
    market = rf.market_for_state("depleted_f20", 0)
    col = predecessor()["columns"][0]
    rmp = fake_master(inst, market, [col], [])
    if mutation == "weight":
        rmp["lambdas"] = [0.5]
    elif mutation == "load":
        rmp["L"][1] += 1
    elif mutation == "upper":
        rmp["ub"] += 1
    else:
        rmp["z_model"] += 1
    with pytest.raises(ValueError):
        rf.replay_master(inst, market, [col], rmp)


def reference_pair():
    name = "depleted_f20"
    m = rf.market_for_state(name, 0)
    shared = {"fixture": name, "state_index": 0, "instance_hash": rf.fixture(name).hash(),
              "config_sha256": rf.digest(rf.CONFIG),
              "market": {"a": list(m.a), "b": list(m.b), "U": list(m.U)}}
    state = {**shared, "status": "certified", "lower": 40.0, "upper": 40.005,
             "market_hash": b2a2.market_hash(m)}
    ref = {**shared, "status": "reference_complete", "ch": {"lower": 40.001, "upper": 40.002}}
    return state, ref


def test_reference_accepts_overlapping_independent_intervals():
    state, ref = reference_pair()
    assert rf.check_reference(state, ref)["intervals_overlap_with_guard"]


@pytest.mark.parametrize("mutation", ["fixture", "state", "instance", "tariff", "disjoint", "wide", "nan"])
def test_reference_rejects_mismatch_or_invalid_interval(mutation):
    state, ref = reference_pair()
    if mutation == "fixture":
        ref["fixture"] = "depleted_f26"
    elif mutation == "state":
        ref["state_index"] = 1
    elif mutation == "instance":
        ref["instance_hash"] = "other"
    elif mutation == "tariff":
        ref["market"] = {"a": [3]}
    elif mutation == "disjoint":
        ref["ch"] = {"lower": 41, "upper": 41.001}
    elif mutation == "wide":
        state["upper"] = 41
    else:
        ref["ch"]["lower"] = float("nan")
    with pytest.raises(ValueError):
        rf.check_reference(state, ref)
