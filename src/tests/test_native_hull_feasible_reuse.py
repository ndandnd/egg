"""Pure opt-in pool-reuse and pricing-reserve controls; no native MIP."""
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction

import pytest

from egglab import native_hull as nh
from egglab import native_pathflow_hull as compact
from experiments import native_hull_qualification as hq
from test_native_hull import install_fakes, physical


def fixture():
    cell = hq.controls()[0]
    return cell["case"], cell["market"], nh.Market("shifted", (0, 3.8, 0, .2), cell["market"].b)


def test_default_hash_and_wrapper_forwarding(monkeypatch):
    case, market, _ = fixture()
    budget = nh.Budget()
    old = nh.nr.digest({"schema": nh.SCHEMA, "case": case.identity(),
        "market": market.identity(), "arm": "cold", "state_index": 0,
        "budget": asdict(budget), "extraction_policy": nh.nr.EXTRACTION_POLICY})
    assert nh.state_identity(case, market, "cold", 0, budget) == old
    assert nh.state_identity(case, market, "cold", 0, budget,
        reuse_policy="certified_only", pricing_reserve_seconds=0) == old
    opt = nh.state_identity(case, market, "cold", 0, budget,
        reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    assert opt != old
    assert compact.state_identity(case, market, "cold", 0, budget) == nh.state_identity(
        case, market, "cold", 0, budget, compact.ORACLE_ID, compact.EXTRACTION_POLICY)
    assert compact.state_identity(case, market, "cold", 0, budget,
        reuse_policy="feasible_pool", pricing_reserve_seconds=10) != compact.state_identity(
        case, market, "cold", 0, budget)
    seen = {}
    def spy(*args, **kwargs):
        seen.update(kwargs)
        return {"status": "unresolved"}
    monkeypatch.setattr(compact.hull, "certify", spy)
    compact.certify(case, market, budget, reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    assert seen["reuse_policy"] == "feasible_pool" and seen["pricing_reserve_seconds"] == 10


def test_feasible_predecessor_replays_columns_but_not_old_weights_or_lower(monkeypatch):
    install_fakes(monkeypatch)
    case, initial, shifted = fixture()
    budget = nh.Budget(pricing_calls=1, wall_seconds=60)
    previous = nh.certify(case, initial, budget, arm="retained",
        reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    assert previous["status"] == "budget_exhausted"
    expected = nh.state_identity(case, initial, "retained", 0, budget,
        reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    assert previous["state_identity"] == expected
    poisoned = deepcopy(previous)
    poisoned["mixture"] = {"objective_exact": "-999999", "weights_exact": ["bad"]}
    poisoned["lower_certificate"] = {"lower_exact": "999999", "prices": ["bad"]}
    calls = []
    oracle = nh.nr.solve_pricing
    def counted(*args, **kwargs):
        calls.append(list(args[1]))
        return oracle(*args, **kwargs)
    monkeypatch.setattr(nh.nr, "solve_pricing", counted)
    result = nh.certify(case, shifted, budget, arm="retained", state_index=1,
        previous=poisoned, expected_previous=expected,
        reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    assert calls and result["counts"]["pricing_requests"] >= 1
    assert result["market_identity"] == shifted.identity()
    assert result["lower_certificate"]["lower_exact"] != "999999"
    assert result["mixture"]["objective_exact"] != "-999999"
    assert result["mixture"]["objective_exact"] == str(Fraction(result["mixture"]["objective_exact"]))
    assert result["status"] != "certified" or result["lower_certificate"]


def test_strict_import_and_cross_control_or_column_corruption_reject(monkeypatch):
    install_fakes(monkeypatch)
    case, initial, shifted = fixture()
    budget = nh.Budget(pricing_calls=1, wall_seconds=60)
    prior = nh.certify(case, initial, budget, arm="retained",
        reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    expected = nh.state_identity(case, initial, "retained", 0, budget,
        reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    with pytest.raises(ValueError):
        nh.import_pool(case, prior, expected, budget)  # strict certified-only default
    with pytest.raises(ValueError):
        nh.certify(case, shifted, budget, arm="retained", state_index=1,
            previous=prior, expected_previous=expected, reuse_policy="feasible_pool",
            pricing_reserve_seconds=9)
    with pytest.raises(ValueError):
        nh.certify(case, shifted, budget, arm="retained", state_index=1,
            previous=prior, expected_previous="copied-but-wrong", reuse_policy="feasible_pool",
            pricing_reserve_seconds=10)
    duplicate = deepcopy(prior)
    duplicate["columns"].append(deepcopy(duplicate["columns"][0]))
    with pytest.raises(ValueError):
        nh.import_pool(case, duplicate, expected, budget, previous_index=0,
                       reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    forged = deepcopy(prior)
    forged["columns"][0]["source"]["pricing_oracle"] = "wrong-oracle"
    with pytest.raises(ValueError):
        nh.import_pool(case, forged, expected, budget, previous_index=0,
                       reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    wrong_source_state = deepcopy(prior)
    wrong_source_state["columns"][0]["source"]["state_identity"] = "wrong-state"
    with pytest.raises(ValueError):
        nh.import_pool(case, wrong_source_state, expected, budget, previous_index=0,
                       reuse_policy="feasible_pool", pricing_reserve_seconds=10)


def test_imported_feasible_upper_without_fresh_target_pricing_is_not_certified(monkeypatch):
    install_fakes(monkeypatch)
    case, initial, shifted = fixture()
    budget = nh.Budget(pricing_calls=1, wall_seconds=60)
    prior = nh.certify(case, initial, budget, arm="retained",
        reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    expected = nh.state_identity(case, initial, "retained", 0, budget,
        reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    def no_master(*args, **kwargs):
        raise nh.LimitReached("no master before new pricing")
    monkeypatch.setattr(nh, "solve_native_rmp", no_master)
    result = nh.certify(case, shifted, budget, arm="retained", state_index=1,
        previous=prior, expected_previous=expected,
        reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    assert result["status"] == "budget_exhausted"
    assert result["counts"]["pricing_requests"] == 0
    assert result["mixture"]["upper"] == result["upper"]
    assert "lower_certificate" not in result and "lower" not in result


def test_reserve_limits_started_pricing_and_preserves_feasible_mixture(monkeypatch):
    case, market, _ = fixture()
    plans = [physical(case, 2, 0), physical(case, 1, 10)]
    clock = [0.0]
    monkeypatch.setattr(nh.time, "monotonic", lambda: clock[0])
    allowances = []
    def pricing(case, prices, budget, record=None):
        plan = plans[len(allowances)]
        allowances.append(budget.wall_seconds)
        value = plan["ops_cost"] + sum(p * e for p, e in zip(prices, plan["load"]))
        stats = {"status": "FEASIBLE", "incumbent": value,
                 "lower_bound": value-100, "wall_s": 0.0}
        lower, upper = nh.nr.admit_bound(stats, value)
        clock[0] = 10.0 if len(allowances) == 1 else 51.0
        return {"case_identity": case.identity(), "prices": list(prices), "stats": stats,
                "status": "bounded", "plan": plan, "lower": lower, "upper": upper}
    def master(case, market, columns, points, budget, deadline, counts, record,
               consider, extraction_policy=None):
        mix = nh.replay_mixture(case, market, columns,
                                [1.0] if len(columns) == 1 else [.5, .5], extraction_policy)
        consider(mix)
        counts["master_calls"] += 1
        return mix, {"prices": list(market.a)}
    monkeypatch.setattr(nh.nr, "solve_pricing", pricing)
    monkeypatch.setattr(nh, "solve_native_rmp", master)
    events = []
    result = nh.certify(case, market, nh.Budget(wall_seconds=60), record=events.append,
        reuse_policy="feasible_pool", pricing_reserve_seconds=10)
    assert allowances == [50.0, 40.0]
    assert result["status"] == "budget_exhausted"
    assert result["reason"] == "pricing reserve prevented a new request"
    assert result["counts"]["pricing_requests"] == 2
    assert result["counts"]["master_calls"] == 2
    assert len(result["columns"]) == 2
    assert result["mixture"] and result["lower_certificate"]
    assert result["mixture"]["upper"] < nh.replay_mixture(case, market, result["columns"], [1, 0])["upper"]
    assert any(event["event"] == "pricing_reserve_stop" for event in events)
    assert next(event for event in events if event["event"] == "pricing_request")[
        "pricing_wall_allowance_seconds"] == 50.0


@pytest.mark.parametrize("policy,reserve", [("unknown", 0), ("feasible_pool", -1),
                                               ("feasible_pool", 60), ("feasible_pool", float("nan"))])
def test_invalid_opt_in_controls_fail_before_oracle(policy, reserve):
    case, market, _ = fixture()
    with pytest.raises(ValueError):
        nh.state_identity(case, market, "cold", 0, nh.Budget(wall_seconds=60),
                          reuse_policy=policy, pricing_reserve_seconds=reserve)
