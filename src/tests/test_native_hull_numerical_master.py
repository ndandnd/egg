"""Pure opt-in QP-master checks; no native optimizer or SciPy is loaded."""
import builtins
from copy import deepcopy
from fractions import Fraction
import sys
import time
from types import SimpleNamespace

import pytest

import egglab
from egglab import native_hull as hull
from egglab import native_pathflow_hull as compact
from experiments import native_hull_qualification as qualification
from test_native_hull import install_fakes, physical


def fixture():
    cell = qualification.controls()[0]
    case, initial = cell["case"], cell["market"]
    shifted = hull.Market("shifted", (0, 3.8, 0, .2), initial.b)
    return case, initial, shifted


def fake_proposal(monkeypatch, *, success=True, weights=None, pause=0):
    def propose(costs, loads, a, b, *, denominator, maxiter):
        if pause:
            time.sleep(pause)
        units = ([denominator] + [0]*(len(costs)-1) if weights is None else weights)
        return {"success": success, "solver_status": 9 if not success else 0,
                "solver_message": "fixture", "numeric_seconds": 0.0,
                "rounding_seconds": 0.0, "denominator": denominator,
                "integer_units": units,
                "weights_exact": [str(Fraction(value, denominator)) for value in units]}
    module = SimpleNamespace(propose=propose)
    monkeypatch.setitem(sys.modules, "egglab.restricted_qp_proposal", module)
    monkeypatch.setattr(egglab, "restricted_qp_proposal", module, raising=False)
    return module


def test_default_identity_and_output_stay_native_lp(monkeypatch):
    install_fakes(monkeypatch)
    case, initial, _ = fixture()
    budget = hull.Budget(pricing_calls=1)
    default = hull.state_identity(case, initial, "cold", 0, budget)
    assert default == hull.state_identity(case, initial, "cold", 0, budget,
                                          master_policy="native_lp")
    assert default != hull.state_identity(case, initial, "cold", 0, budget,
                                          master_policy="numerical_qp_proposal")
    result = hull.certify(case, initial, budget)
    assert "master_policy" not in result and "qp_proposal_calls" not in result["counts"]
    seen = {}
    def spy(*args, **kwargs):
        seen.update(kwargs)
        return {"status": "unresolved"}
    monkeypatch.setattr(compact.hull, "certify", spy)
    compact.certify(case, initial, budget, master_policy="numerical_qp_proposal", qp_maxiter=7)
    assert seen["master_policy"] == "numerical_qp_proposal" and seen["qp_maxiter"] == 7


def test_non_success_numerical_candidate_is_replayed_but_never_self_certifies(monkeypatch):
    install_fakes(monkeypatch)
    fake_proposal(monkeypatch, success=False)
    case, initial, _ = fixture()
    budget = hull.Budget(pricing_calls=2, master_calls=2, wall_seconds=60)
    events = []
    result = hull.certify(case, initial, budget, master_policy="numerical_qp_proposal",
                          record=events.append)
    assert result["master_policy"] == "numerical_qp_proposal"
    assert result["counts"]["qp_proposal_calls"] >= 1
    assert result["counts"]["qp_non_success"] == result["counts"]["qp_proposal_calls"]
    assert result["counts"]["polish_steps"] == 0
    assert result["mixture"]["simplex"]["source"] == "fixed-denominator-qp-proposal"
    assert any(e["event"] == "qp_proposal_result" and e["proposal"]["success"] is False for e in events)
    replay = next(e for e in events if e["event"] == "qp_candidate_replay")
    assert Fraction(replay["pool"]["pool_gap_exact"]) >= 0
    assert result["counts"]["pricing_requests"] >= 2
    assert result["status"] != "certified" or result["lower_certificate"]


@pytest.mark.parametrize("bad", ["negative", "wrong_sum", "not_fraction", "length"])
def test_invalid_weights_report_proposal_failed_with_prior_evidence(monkeypatch, bad):
    install_fakes(monkeypatch)
    module = fake_proposal(monkeypatch)
    case, initial, shifted = fixture()
    budget = hull.Budget(pricing_calls=1, wall_seconds=60)
    reuse = {"reuse_policy": "feasible_pool", "pricing_reserve_seconds": 10}
    prior = hull.certify(case, initial, budget, arm="retained",
                         bound_cache_policy="physical_pricing",
                         master_policy="numerical_qp_proposal", **reuse)
    assert prior["columns"] and prior["physical_pricing_evidence"]
    valid = module.propose
    def invalid(costs, loads, a, b, *, denominator, maxiter):
        proposal = valid(costs, loads, a, b, denominator=denominator, maxiter=maxiter)
        if bad == "negative":
            proposal["integer_units"] = [-1] + [denominator+1] + [0]*(len(costs)-2)
            proposal["weights_exact"] = [str(Fraction(x, denominator)) for x in proposal["integer_units"]]
        elif bad == "wrong_sum":
            proposal["integer_units"][0] -= 1
            proposal["weights_exact"][0] = str(Fraction(denominator-1, denominator))
        elif bad == "not_fraction":
            proposal["weights_exact"][0] = "bad"
        else:
            proposal["weights_exact"] = []
        return proposal
    module.propose = invalid
    events = []
    result = hull.certify(case, shifted, budget, arm="retained", state_index=1,
                          previous=prior, expected_previous=prior["state_identity"],
                          bound_cache_policy="physical_pricing", cached_from=prior,
                          expected_cached_state=prior["state_identity"],
                          master_policy="numerical_qp_proposal", record=events.append, **reuse)
    assert result["status"] == "proposal_failed" and result["reason"]
    assert result["fresh_pricing_successes"] == 0
    assert result["mixture"] and result["lower_certificate"]
    assert result["lower_certificate_origin"]["kind"] == "cached_physical_pricing"
    assert result["counts"]["qp_proposal_calls"] == 1
    assert any(e["event"] == "qp_proposal_failure" for e in events)


def test_qp_import_failure_retains_prior_evidence(monkeypatch):
    install_fakes(monkeypatch)
    fake_proposal(monkeypatch)
    case, initial, shifted = fixture()
    budget = hull.Budget(pricing_calls=1, wall_seconds=60)
    reuse = {"reuse_policy": "feasible_pool", "pricing_reserve_seconds": 10}
    prior = hull.certify(case, initial, budget, arm="retained",
                         bound_cache_policy="physical_pricing",
                         master_policy="numerical_qp_proposal", **reuse)
    original_import = builtins.__import__
    def missing_qp(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "egglab" and "restricted_qp_proposal" in fromlist:
            raise ImportError("SciPy unavailable")
        return original_import(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, "__import__", missing_qp)
    events = []
    result = hull.certify(case, shifted, budget, arm="retained", state_index=1,
                          previous=prior, expected_previous=prior["state_identity"],
                          bound_cache_policy="physical_pricing", cached_from=prior,
                          expected_cached_state=prior["state_identity"],
                          master_policy="numerical_qp_proposal", record=events.append, **reuse)
    assert result["status"] == "proposal_failed"
    assert "SciPy unavailable" in result["reason"]
    assert result["mixture"] and result["lower_certificate"]
    assert result["fresh_pricing_successes"] == 0
    assert result["counts"]["qp_proposal_calls"] == 1
    assert result["counts"]["qp_proposal_wall_s"] >= 0
    assert any(e["event"] == "qp_proposal_failure" and
               e["error_type"] == "ImportError" for e in events)


def test_late_proposal_keeps_accounting_and_cannot_reach_replay(monkeypatch):
    module = fake_proposal(monkeypatch, pause=.02)
    case, initial, _ = fixture()
    column = hull.native_column(case, physical(case, 2, 0), {"kind": "test"})
    budget = hull.Budget(wall_seconds=1)
    counts = {"master_calls": 0, "qp_proposal_calls": 0, "qp_non_success": 0,
              "qp_proposal_wall_s": 0.0, "qp_replay_wall_s": 0.0,
              "max_rational_bits": 0}
    events = []
    with pytest.raises(hull.LimitReached, match="before replay"):
        hull.solve_qp_rmp(case, initial, [column], budget, time.monotonic()+.01,
                          counts, events.append)
    assert counts["qp_proposal_calls"] == 1 and counts["qp_proposal_wall_s"] >= .02
    assert any(e["event"] == "qp_proposal_result" for e in events)
    assert not any(e["event"] == "qp_candidate_replay" for e in events)
    assert module.propose


def test_exact_bit_cap_is_budget_exhaustion_not_malformed_proposal(monkeypatch):
    fake_proposal(monkeypatch)
    case, initial, _ = fixture()
    column = hull.native_column(case, physical(case, 2, 0), {"kind": "test"})
    budget = hull.Budget(rational_bits=16)
    counts = {"master_calls": 0, "qp_proposal_calls": 0, "qp_non_success": 0,
              "qp_proposal_wall_s": 0.0, "qp_replay_wall_s": 0.0,
              "max_rational_bits": 0}
    with pytest.raises(hull.LimitReached, match="bit-size budget"):
        hull.solve_qp_rmp(case, initial, [column], budget, time.monotonic()+5,
                          counts, None, denominator=10)
    assert counts["max_rational_bits"] > budget.rational_bits


def test_physical_replay_failure_is_not_relabelled_as_proposal_failure(monkeypatch):
    fake_proposal(monkeypatch)
    case, initial, _ = fixture()
    column = hull.native_column(case, physical(case, 2, 0), {"kind": "test"})
    budget = hull.Budget()
    counts = {"master_calls": 0, "qp_proposal_calls": 0, "qp_non_success": 0,
              "qp_proposal_wall_s": 0.0, "qp_replay_wall_s": 0.0,
              "max_rational_bits": 0}
    original = hull.replay_column
    calls = 0
    def replay(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("physical column replay changed")
        return original(*args, **kwargs)
    monkeypatch.setattr(hull, "replay_column", replay)
    with pytest.raises(ValueError, match="physical column replay changed"):
        hull.solve_qp_rmp(case, initial, [column], budget, time.monotonic()+5,
                          counts, None)
    assert calls == 2


def test_opt_in_controls_reject_silent_native_fallback():
    case, initial, _ = fixture()
    budget = hull.Budget()
    with pytest.raises(ValueError):
        hull.state_identity(case, initial, "cold", 0, budget,
                            master_policy="native_lp", qp_maxiter=1)
    with pytest.raises(ValueError):
        hull.state_identity(case, initial, "cold", 0, budget,
                            master_policy="numerical_qp_proposal", qp_denominator=0)
