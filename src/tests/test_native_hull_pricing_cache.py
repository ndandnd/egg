"""Pure opt-in physical pricing-bound cache tests; no native optimization."""
from copy import deepcopy
from fractions import Fraction

import pytest

from egglab import native_hull as hull
from egglab import native_pathflow_hull as compact
from experiments import native_hull_qualification as qualification
from test_native_hull import install_fakes


def fixture():
    cell = qualification.controls()[0]
    case, initial = cell["case"], cell["market"]
    shifted = hull.Market("shifted", (0, 3.8, 0, .2), initial.b)
    return case, initial, shifted


def source(monkeypatch, *, calls=3, retained=False):
    install_fakes(monkeypatch)
    case, initial, shifted = fixture()
    budget = hull.Budget(pricing_calls=calls, wall_seconds=60)
    reuse = {"reuse_policy": "feasible_pool", "pricing_reserve_seconds": 10} if retained else {}
    prior = hull.certify(case, initial, budget, arm="retained" if retained else "cold",
                         bound_cache_policy="physical_pricing", **reuse)
    return case, initial, shifted, budget, prior, reuse


def target(case, shifted, budget, prior, **kwargs):
    return hull.certify(case, shifted, budget, arm=kwargs.pop("arm", "cold"), state_index=1,
                        bound_cache_policy="physical_pricing", cached_from=prior,
                        expected_cached_state=prior["state_identity"], **kwargs)


def rehash(prior):
    for item in prior["physical_pricing_evidence"]:
        item["digest"] = hull.nr.digest(item["record"])
    prior["physical_pricing_evidence_digest"] = hull.nr.digest(prior["physical_pricing_evidence"])


def test_disabled_default_identity_output_and_wrapper_forwarding(monkeypatch):
    case, initial, _ = fixture()
    budget = hull.Budget()
    default = hull.state_identity(case, initial, "cold", 0, budget)
    opt = hull.state_identity(case, initial, "cold", 0, budget,
                              bound_cache_policy="physical_pricing")
    assert default != opt
    install_fakes(monkeypatch)
    result = hull.certify(case, initial, hull.Budget(pricing_calls=1))
    assert "physical_pricing_evidence" not in result
    assert "bound_cache_policy" not in result
    assert "pricing_oracle" not in result
    seen = {}
    def spy(*args, **kwargs):
        seen.update(kwargs)
        return {"status": "unresolved"}
    monkeypatch.setattr(compact.hull, "certify", spy)
    compact.certify(case, initial, budget, bound_cache_policy="physical_pricing")
    assert seen["bound_cache_policy"] == "physical_pricing"
    assert compact.state_identity(case, initial, "cold", 0, budget,
                                  bound_cache_policy="physical_pricing") != compact.state_identity(
                                      case, initial, "cold", 0, budget)


def test_source_keeps_every_successful_physical_pricing_bound(monkeypatch):
    case, initial, shifted, budget, prior, _ = source(monkeypatch, calls=3)
    evidence = prior["physical_pricing_evidence"]
    assert len(evidence) == prior["counts"]["pricing_requests"] >= 2
    assert prior["physical_pricing_evidence_digest"] == hull.nr.digest(evidence)
    for item in evidence:
        data = item["record"]
        assert item["digest"] == hull.nr.digest(data)
        assert data["pricing_oracle"] == hull.DEFAULT_PRICING_ORACLE
        assert data["source_state_identity"] == prior["state_identity"]
        assert data["pricing_lower"] == hull.nr.admit_bound(
            data["native_stats"], data["pricing_objective"])[0]
    result = target(case, shifted, budget, prior)
    rebuilt = [hull.fenchel_bound(shifted, item["record"]["prices"],
                                 item["record"]["pricing_lower"])
               for item in evidence]
    assert [c["certificate"] for c in result["cached_lower_candidates"]] == rebuilt
    assert result["fresh_pricing_successes"] >= 1
    assert result["cache_validation_wall_s"] >= 0
    assert result["cache_source_costs"] == prior["source_costs"]
    assert result["source_costs"]["full_child_wall_s"] is None


@pytest.mark.parametrize("corrupt", ["case", "oracle", "policy", "source_state", "price",
                                     "lower", "record_digest", "envelope_digest", "native_status",
                                     "source_cap", "source_cost", "malformed"])
def test_corrupted_or_incompatible_cache_fails_closed(monkeypatch, corrupt):
    case, _, shifted, budget, prior, _ = source(monkeypatch, calls=1)
    changed = deepcopy(prior)
    record = changed["physical_pricing_evidence"][0]["record"]
    if corrupt == "case":
        changed["physical_identity"] = "different"
    elif corrupt == "oracle":
        changed["pricing_oracle"] = "different"
    elif corrupt == "policy":
        changed["extraction_policy"] = "different"
    elif corrupt == "source_state":
        record["source_state_identity"] = "different"
        rehash(changed)
    elif corrupt == "price":
        loaded = next(i for i, amount in enumerate(record["load"]) if amount > 0)
        record["prices"][loaded] += 1
        rehash(changed)
    elif corrupt == "lower":
        record["pricing_lower"] += 1
        rehash(changed)
    elif corrupt == "record_digest":
        changed["physical_pricing_evidence"][0]["digest"] = "wrong"
        changed["physical_pricing_evidence_digest"] = hull.nr.digest(changed["physical_pricing_evidence"])
    elif corrupt == "envelope_digest":
        changed["physical_pricing_evidence_digest"] = "wrong"
    elif corrupt == "native_status":
        record["native_stats"]["status"] = "ERROR"
        rehash(changed)
    elif corrupt == "source_cap":
        changed["source_pricing_call_cap"] = 0
    elif corrupt == "source_cost":
        changed["source_costs"]["native_pricing_solver_wall_s"] = -1
    elif corrupt == "malformed":
        changed["physical_pricing_evidence"].append({"not_json": {1, 2}})
    with pytest.raises(ValueError):
        target(case, shifted, budget, changed)


def test_cached_lower_without_fresh_target_pricing_cannot_certify(monkeypatch):
    case, _, shifted, budget, prior, reuse = source(monkeypatch, calls=1, retained=True)
    def stop_before_pricing(*args, **kwargs):
        raise hull.LimitReached("no target master")
    monkeypatch.setattr(hull, "solve_native_rmp", stop_before_pricing)
    result = target(case, shifted, budget, prior, arm="retained", previous=prior,
                    expected_previous=prior["state_identity"], **reuse)
    assert result["status"] == "budget_exhausted"
    assert result["counts"]["pricing_requests"] == 0
    assert result["fresh_pricing_successes"] == 0
    assert result["lower_certificate_origin"]["kind"] == "cached_physical_pricing"
    assert result["lower_certificate"] == max(
        (c["certificate"] for c in result["cached_lower_candidates"]),
        key=lambda c: Fraction(c["lower_exact"]))
    assert result["mixture"] and result["cache_validation_wall_s"] >= 0


def test_cache_is_independent_of_feasible_column_reuse(monkeypatch):
    case, _, shifted, budget, prior, _ = source(monkeypatch, calls=1)
    # Cold target accepts physical lower evidence without importing fleet columns.
    result = target(case, shifted, budget, prior)
    assert result["cached_lower_candidates"]
    assert result["arm"] == "cold"
    assert result["fresh_pricing_successes"] >= 1


def test_reversed_cached_lower_and_retained_upper_fails_even_without_fresh_pricing(monkeypatch):
    case, _, shifted, budget, prior, reuse = source(monkeypatch, calls=1, retained=True)
    original = hull._cached_pricing_bounds
    def corrupt_envelope(*args, **kwargs):
        candidate = deepcopy(original(*args, **kwargs)[0])
        candidate["certificate"]["lower_exact"] = "999999"
        return [candidate]
    monkeypatch.setattr(hull, "_cached_pricing_bounds", corrupt_envelope)
    def stop_before_pricing(*args, **kwargs):
        raise hull.LimitReached("no target master")
    monkeypatch.setattr(hull, "solve_native_rmp", stop_before_pricing)
    with pytest.raises(ValueError, match="reverses target feasible enclosure"):
        target(case, shifted, budget, prior, arm="retained", previous=prior,
               expected_previous=prior["state_identity"], **reuse)
