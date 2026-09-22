"""Adversarial adapter checks; these tests do not run a native optimizer."""
import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from experiments import reuse_qualification as rq
from egglab import b2a2, regimes
from egglab.evsp import Solution, LOAD_RECONSTRUCTION_POLICY_VERSION, REPLAY_TOL_KWH
from egglab.solver import SolveStats


def solution(prices=(0.3, 1.3, 1.3, 0.3)):
    value = 10 + 5 * prices[1] + 5 * prices[2]
    return Solution(
        sequences=[["t0", "t1"]], arc_kinds=[["dep"]],
        charges=[{"vehicle": 0, "after_trip": "t0", "before_trip": "t1", "slot": t, "kwh": 5.0}
                 for t in (1, 2)], load=[0.0, 5.0, 5.0, 0.0],
        fleet=1, ops_cost=10.0, obj_model=value, obj_true=value,
        stats=SolveStats(backend="CBC", status="OPTIMAL", obj=value, bound=value,
                         extra={"load_reconstruction": {
                             "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
                             "tolerance_kwh": REPLAY_TOL_KWH}}))


def predecessor(arm="retained"):
    return {"schema": rq.SCHEMA, "config_sha256": rq.digest(rq.CONFIG),
            "arm": arm, "state_index": 0, "status": "certified",
            "instance_hash": rq.fixture().hash(),
            "market_hash": b2a2.market_hash(rq.market_for_state(0)),
            "columns": [b2a2.column_from_solution(rq.fixture(), solution())],
            "last_clean_price": [0.3, 1.3, 1.3, 0.3],
            "lower": 1e9, "tangent_points": [[999.0] * 4]}


def test_independent_continuous_truth_and_zero_shift():
    truths = [rq.analytic_solution(rq.market_for_state(i)) for i in range(4)]
    assert [v["objective"] for v in truths] == pytest.approx([18, 18, 17.8, 17.8])
    assert [v["load"][1] for v in truths] == pytest.approx([5, 5, 4, 6])
    assert rq.shifted_price([0.3, 1.3, 1.3, 0.3], rq.market_for_state(0),
                            rq.market_for_state(1)) == pytest.approx([0.3, 1.3, 1.3, 0.3])
    assert rq.shifted_price([0.3, 1.3, 1.3, 0.3], rq.market_for_state(1),
                            rq.market_for_state(2)) == pytest.approx([0.3, 1.5, 1.1, 0.3])


@pytest.mark.parametrize("field,value", [
    ("arm", "retained_shift"), ("state_index", 1),
    ("instance_hash", "different"), ("market_hash", "different"),
    ("config_sha256", "different"), ("status", "failed")])
def test_import_rejects_cross_arm_future_physics_and_uncertified_state(field, value):
    prior = predecessor()
    prior[field] = value
    with pytest.raises(ValueError, match="predecessor"):
        rq.import_previous(rq.fixture(), prior, "retained", 1)


@pytest.mark.parametrize("mutation", ["cost", "load", "charge_owner", "window", "soc", "arcs"])
def test_import_replays_evidence_despite_true_stored_flag(mutation):
    col = predecessor()["columns"][0]
    if mutation == "cost":
        col["ops_cost"] = 11.0
    elif mutation == "load":
        col["load"][1] = 4.9
    elif mutation == "charge_owner":
        col["charges"][0]["vehicle"] = 1
    elif mutation == "window":
        col["charges"][0]["kwh"] = 11.0
        col["load"][1] = 11.0
    elif mutation == "soc":
        col["charges"][0]["kwh"] = 4.0
        col["load"][1] = 4.0
    else:
        col["arc_kinds"] = [[]]
    col["column_key"] = b2a2.column_key(col)
    assert col["replay_ok"] is True
    with pytest.raises(ValueError):
        rq.replay_column(rq.fixture(), col)


def test_import_isolated_copy_and_stale_bound_not_returned():
    prior = predecessor()
    columns = rq.import_previous(rq.fixture(), prior, "retained", 1)
    assert isinstance(columns, list)
    columns[0]["charges"][0]["kwh"] = -1
    assert prior["columns"][0]["charges"][0]["kwh"] == 5


def test_certificate_ignores_stale_and_proposal_bounds(monkeypatch, tmp_path):
    prior = predecessor("retained_shift")
    calls = []

    def fake_taker(inst, prices, **kwargs):
        sol = solution(prices)
        if not calls:
            # An unhelpful proposal bound must not enter the clean certificate.
            sol.stats.bound = -99999.0
        calls.append(list(prices))
        return sol

    def fake_rmp(inst, market, columns, tangent_points, **kwargs):
        assert tangent_points == []  # Prior-state tangents were not copied.
        return {"z_model": 17.999, "ub": 18.0, "L": [0, 5, 5, 0],
                "pi": [-0.3, -1.3, -1.3, -0.3], "sigma": 23.0,
                "tangent_points": [], "master_solves": []}

    monkeypatch.setattr(regimes, "solve_taker", fake_taker)
    monkeypatch.setattr(b2a2, "solve_rmp", fake_rmp)
    result = rq.solve_state("retained_shift", 1, prior, tmp_path / "state.json")
    assert result["status"] == "certified", result.get("error")
    assert result["lower"] == pytest.approx(17.999)
    assert result["calls_proposal"] == 1
    assert result["calls_clean"] == 1
    assert len(calls) == 2
    assert result["proposal"]["used_for_lower_bound"] is False
    assert result["proposal"]["novel"] is False
    assert json.loads((tmp_path / "state.json").read_text())["status"] == "certified"
