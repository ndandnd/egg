"""Handcrafted source-only scorer tests; never import the egglab package/backend."""

import ast
import builtins
import importlib.util
import sys
from fractions import Fraction
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "egglab" / "comparison_scoring.py"


def _load_source(name):
    spec = importlib.util.spec_from_file_location(name, SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


scoring = _load_source("_source_only_comparison_scoring")
K = scoring.EndpointKind


def endpoint(kind=K.VALID, bill=0, unit=1):
    return scoring.Endpoint(kind, bill if kind is K.VALID else None, unit)


def roster(kind=scoring.CohortKind.PRIMARY, unit=1):
    count = 4 if kind is scoring.CohortKind.PRIMARY else 2
    return scoring.AssignmentRoster(kind, tuple(
        scoring.PairAssignment(f"synthetic-{size}-{i}", size, seed)
        for size in (40, 80) for i in range(count) for seed in (17, 41, 73)
    ), unit)


def observation(key, a=None, c=None):
    return scoring.PairObservation(key, a or endpoint(), c or endpoint(K.ALGORITHMIC_FAILURE))


def bounds(actual, lower, upper):
    assert actual == scoring.ExactBounds(Fraction(lower), Fraction(upper))


def test_source_load_has_no_runtime_or_backend_imports(monkeypatch):
    tree = ast.parse(SOURCE.read_text())
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert imports == ["dataclasses", "enum", "fractions", "typing"]
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
    original = builtins.__import__

    def standard_library_only(name, *args, **kwargs):
        assert name.split(".")[0] in sys.stdlib_module_names, f"non-stdlib import: {name}"
        return original(name, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(builtins, "__import__", standard_library_only)
        loaded = _load_source("_guarded_source_only_comparison_scoring")
        assert loaded.Endpoint(loaded.EndpointKind.VALID, "-3/2").bill == Fraction(-3, 2)


def test_exact_input_types_and_canonical_spelling():
    for value in (0, -3, 10**500, Fraction(-3, 2), "-3/2", "0", "123"):
        assert scoring.exact_rational(value) == Fraction(value)
    for value in (True, False, 0.5, float("nan"), float("inf"), None, complex(1)):
        with pytest.raises(TypeError):
            scoring.exact_rational(value)
    for value in ("1e-2", "0.005", "2/4", "1/1", "-0", "01", "+1", " 1", "1 ", "nan", "inf", "1/0"):
        with pytest.raises(ValueError):
            scoring.exact_rational(value)


@pytest.mark.parametrize("a_bill, expected", [(Fraction(199001, 1000), 0), (199, 0), (Fraction(198999, 1000), 1)])
def test_exact_boundary_and_sign_reversal(a_bill, expected):
    a, c = endpoint(bill=a_bill), endpoint(bill=200)
    result = scoring.score_pair(a, c)
    assert result.value == expected
    assert result.tie_band == 1
    assert result.bill_difference == 200 - a_bill
    assert scoring.score_pair(c, a).value == -expected


def test_negative_bills_huge_integers_and_unit_floor():
    assert scoring.score_pair(endpoint(bill=-200), endpoint(bill=-199)).value == 0
    assert scoring.score_pair(endpoint(bill=-200), endpoint(bill="-198999/1000")).value == 1
    huge = 10**500
    result = scoring.score_pair(endpoint(bill=199 * huge), endpoint(bill=200 * huge))
    assert result.value == 0 and result.tie_band == huge
    assert scoring.score_pair(endpoint(bill=0, unit=1000), endpoint(bill=5, unit=1000)).value == 0
    assert scoring.score_pair(endpoint(bill=0, unit=1000), endpoint(bill=6, unit=1000)).value == 1


def test_healthy_failures_and_unknown_precedence_never_invent_bills():
    valid, failure = endpoint(bill=-7), endpoint(K.ALGORITHMIC_FAILURE)
    for a, c, expected in ((valid, failure, 1), (failure, valid, -1), (failure, failure, 0)):
        result = scoring.score_pair(a, c)
        assert result.value == expected
        assert result.tie_band is None and result.bill_difference is None
    for unknown_kind in (K.UNKNOWN, K.UNDISPATCHED):
        unknown = endpoint(unknown_kind)
        for other in (valid, failure, unknown):
            for a, c in ((unknown, other), (other, unknown)):
                result = scoring.score_pair(a, c)
                assert result.value is None
                bounds(result.bounds, -1, 1)
                assert result.tie_band is None and result.bill_difference is None


def test_invalid_endpoint_and_currency_inputs_are_rejected():
    for kind in ("valid", "algorithmic_failure", None):
        with pytest.raises(TypeError):
            scoring.Endpoint(kind, 0)
    with pytest.raises(ValueError):
        scoring.Endpoint(K.VALID)
    for kind in (K.ALGORITHMIC_FAILURE, K.UNKNOWN, K.UNDISPATCHED):
        with pytest.raises(ValueError):
            scoring.Endpoint(kind, 0)
    for unit in (0, -1, Fraction(-1, 2)):
        with pytest.raises(ValueError):
            endpoint(unit=unit)
    for unit in (False, 1.0):
        with pytest.raises(TypeError):
            endpoint(unit=unit)
    with pytest.raises(ValueError):
        scoring.score_pair(endpoint(unit=1), endpoint(unit=2))
    with pytest.raises(TypeError):
        scoring.score_pair("valid", endpoint())


def test_validity_difference_retains_known_opponent():
    valid, failure, unknown = endpoint(), endpoint(K.ALGORITHMIC_FAILURE), endpoint(K.UNKNOWN)
    for a, c, lower, upper in ((valid, unknown, 0, 1), (unknown, valid, -1, 0),
                              (unknown, failure, 0, 1), (failure, unknown, -1, 0),
                              (unknown, unknown, -1, 1), (failure, failure, 0, 0)):
        bounds(scoring.validity_difference_bounds(a, c), lower, upper)


def test_complete_roster_equal_seed_base_and_size_weights():
    assigned = roster()
    observations = tuple(observation(key) for key in assigned.assignments)
    result = scoring.summarize_comparison(assigned, observations)
    assert assigned.pair_weight == Fraction(1, 24)
    assert assigned.base_weight == Fraction(1, 8) and assigned.size_weight == Fraction(1, 2)
    assert len(result.per_base) == 8 and len(result.per_size) == 2
    assert result.overall.score.assigned_count == 24
    assert result.overall.score.wins == 24
    assert result.overall.score.known_component == 1 and result.overall.score.missing_mass == 0
    bounds(result.overall.score.bounds, 1, 1)
    assert all(item.summary.score.assigned_count == 3 for item in result.per_base)
    assert all(item.summary.score.assigned_count == 12 for item in result.per_size)


def test_missing_entire_size_keeps_assigned_denominators():
    assigned = roster()
    result = scoring.summarize_comparison(assigned, (
        observation(key) for key in assigned.assignments if key.size == 40))
    assert result.overall.score.known_component == Fraction(1, 2)
    assert result.overall.score.missing_mass == Fraction(1, 2)
    assert result.overall.score.unknown_pairs == 12
    bounds(result.overall.score.bounds, 0, 1)
    bounds(result.per_size[1].summary.score.bounds, -1, 1)
    for item in result.per_base:
        bounds(item.summary.score.bounds, 1 if item.size == 40 else -1, 1)


def test_mechanism_single_missing_seed_uses_twelve_assignments():
    assigned = roster(scoring.CohortKind.MECHANISM)
    result = scoring.summarize_comparison(assigned, map(observation, assigned.assignments[1:]))
    assert assigned.pair_weight == Fraction(1, 12) and assigned.base_weight == Fraction(1, 4)
    assert result.overall.score.known_component == Fraction(11, 12)
    assert result.overall.score.missing_mass == Fraction(1, 12)
    bounds(result.overall.score.bounds, Fraction(5, 6), 1)
    bounds(result.per_base[0].summary.score.bounds, Fraction(1, 3), 1)
    assert result.per_size[0].summary.score.assigned_count == 6


@pytest.mark.parametrize("kind,n", [(scoring.CohortKind.PRIMARY, 24), (scoring.CohortKind.MECHANISM, 12)])
def test_all_missing_has_full_mass_and_no_complete_case_estimate(kind, n):
    result = scoring.summarize_comparison(roster(kind))
    assert result.overall.score.assigned_count == n and result.overall.score.unknown_pairs == n
    assert result.overall.score.known_component == 0 and result.overall.score.missing_mass == 1
    bounds(result.overall.score.bounds, -1, 1)
    bounds(result.overall.arm_a_validity.bounds, 0, 1)
    bounds(result.overall.validity_difference, -1, 1)


def test_shared_unknown_does_not_erase_known_arm_validity():
    assigned = roster()
    result = scoring.summarize_comparison(assigned, (
        observation(key, endpoint(), endpoint(K.UNKNOWN)) for key in assigned.assignments))
    bounds(result.overall.score.bounds, -1, 1)
    bounds(result.overall.arm_a_validity.bounds, 1, 1)
    bounds(result.overall.arm_c_validity.bounds, 0, 1)
    bounds(result.overall.validity_difference, 0, 1)


def test_undispatched_counts_are_separate_and_validity_uses_fixed_denominator():
    assigned = roster()
    a, b, c = assigned.assignments[:3]
    result = scoring.summarize_comparison(assigned, (
        observation(a), observation(b, endpoint(K.ALGORITHMIC_FAILURE), endpoint(K.UNKNOWN)),
        observation(c, endpoint(K.UNDISPATCHED), endpoint()),
    ))
    validity = result.per_base[0].summary.arm_a_validity
    assert (validity.valid, validity.algorithmic_failures, validity.unknown, validity.undispatched) == (1, 1, 0, 1)
    bounds(validity.bounds, Fraction(1, 3), Fraction(2, 3))
    bounds(result.per_base[0].summary.validity_difference, Fraction(-1, 3), Fraction(1, 3))


def test_invalid_roster_id_size_seed_and_fixed_shape_are_rejected():
    for args in (("", 40, 17), (" padded", 40, 17), ("x", 41, 17), ("x", True, 17), ("x", 40, 18), ("x", 40, True)):
        with pytest.raises(ValueError):
            scoring.PairAssignment(*args)
    assigned = roster()
    for keys in (assigned.assignments[:-1], assigned.assignments + assigned.assignments[:1],
                 assigned.assignments[3:], tuple(
                     scoring.PairAssignment(key.base_id if key.size == 40 else key.base_id.replace("80", "40"), key.size, key.seed)
                     for key in assigned.assignments)):
        with pytest.raises(ValueError):
            scoring.AssignmentRoster(scoring.CohortKind.PRIMARY, keys)
    with pytest.raises(TypeError):
        scoring.AssignmentRoster("primary", assigned.assignments)


def test_duplicate_unlisted_and_mixed_unit_observations_are_rejected():
    assigned = roster(unit=2)
    key = assigned.assignments[0]
    good = observation(key, endpoint(unit=2), endpoint(K.UNKNOWN, unit=2))
    with pytest.raises(ValueError):
        scoring.summarize_comparison(assigned, (good, good))
    unlisted = scoring.PairAssignment("synthetic-unlisted", 40, 17)
    with pytest.raises(ValueError):
        scoring.summarize_comparison(assigned, (observation(unlisted),))
    with pytest.raises(ValueError):
        scoring.summarize_comparison(assigned, (observation(key),))
    with pytest.raises(TypeError):
        scoring.summarize_comparison(assigned, ("raw receipt",))

