"""Synthetic acceptance battery for outcome-blind settlement arithmetic.

Every endpoint below is invented in this file.  No experiment population,
checkpoint, run tree, or committed result artifact is opened.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.uplift_settlement as us


def _interval(lo, hi=None):
    return {"lo": str(lo), "hi": str(lo if hi is None else hi)}


def _withdrawal(t0, t1):
    return [
        {"component_id": "t0", "quantity": _interval(t0)},
        {"component_id": "t1", "quantity": _interval(t1)},
    ]


def _identity_certificate():
    return {
        "certificate_id": "invented-uplift-loc-identity-cert",
        "status": "certified",
        **{premise: True for premise in us.IDENTITY_PREMISES},
    }


def _certificate(*, coverage="complete"):
    """Exact invented case: participant LOCs 2 + 1 = system uplift 3."""
    return {
        "schema": us.INPUT_SCHEMA,
        "case_id": "invented-two-block-case",
        "coverage": coverage,
        "units": {"currency": "SEK", "quantity": "kWh"},
        "price_certificate": {
            "certificate_id": "invented-price-cert",
            "status": "certified",
            "representation": us.PRICE_REPRESENTATION,
            "components": [
                {"component_id": "t0", "price": _interval(2)},
                {"component_id": "t1", "price": _interval(3)},
            ],
        },
        "objective_certificate": {
            "certificate_id": "invented-objective-cert",
            "status": "certified",
            "integrated_integer_objective": _interval(100),
            "convex_hull_objective": _interval(97),
        },
        "uplift_loc_identity_certificate": (
            _identity_certificate() if coverage == "complete" else None
        ),
        "participants": [
            {
                "participant_id": "demand",
                "assigned_action_id": "demand-assignment",
                "price_certificate_id": "invented-price-cert",
                "assigned_action_certified_feasible": True,
                "assigned_intrinsic_cost": _interval(10),
                "assigned_net_withdrawal": _withdrawal(4, 1),
                "best_response_certificate_id": "demand-br-cert",
                "best_response_status": "certified",
                "best_response_objective": _interval(19),
            },
            {
                "participant_id": "supply",
                "assigned_action_id": "supply-assignment",
                "price_certificate_id": "invented-price-cert",
                "assigned_action_certified_feasible": True,
                "assigned_intrinsic_cost": _interval(5),
                "assigned_net_withdrawal": _withdrawal(-4, -1),
                "best_response_certificate_id": "supply-br-cert",
                "best_response_status": "certified",
                "best_response_objective": _interval(-7),
            },
        ],
    }


def _participants(result):
    return {row["participant_id"]: row for row in result["participants"]}


def test_exact_complete_settlement_and_two_part_tariff():
    result = us.settle(_certificate())
    assert result["schema"] == us.OUTPUT_SCHEMA
    assert result["coverage"] == "complete"
    assert result["system"]["uplift_raw"] == _interval(3)
    assert result["system"]["uplift"] == _interval(3)

    participants = _participants(result)
    demand = participants["demand"]
    assert demand["volumetric_charge_to_participant"] == _interval(11)
    assert demand["assigned_private_cost_before_commitment"] == _interval(21)
    assert demand["lost_opportunity_cost_raw"] == _interval(2)
    assert demand["lost_opportunity_cost"] == _interval(2)
    tariff = demand["two_part_tariff"]
    assert tariff["minimum_commitment_payment_to_participant"] == _interval(2)
    assert tariff["fixed_charge_to_participant"] == _interval(-2)
    assert tariff["commitment_condition"] == \
        "payment-contingent-on-assigned-action-performance"
    assert tariff["net_charge_to_participant_at_minimum_payment"] == _interval(9)
    assert tariff["assigned_all_in_cost_at_minimum_payment"] == _interval(19)
    assert tariff["guaranteed_commitment_payment_to_participant"] == _interval(2)

    supply = participants["supply"]
    assert supply["volumetric_charge_to_participant"] == _interval(-11)
    assert supply["lost_opportunity_cost"] == _interval(1)
    assert supply["two_part_tariff"][
        "net_charge_to_participant_at_minimum_payment"] == _interval(-12)

    aggregate = result["loc_aggregation"]
    assert aggregate["total_lost_opportunity_cost"] == _interval(3)
    assert aggregate["uplift_loc_identity_asserted"] is True
    assert aggregate["uplift_loc_identity_certificate_id"] == \
        "invented-uplift-loc-identity-cert"
    assert aggregate["uplift_loc_identity_premises"] == {
        premise: True for premise in us.IDENTITY_PREMISES
    }
    assert aggregate["uplift_loc_identity_consistent"] is True
    assert aggregate["uplift_loc_identity_intersection"] == _interval(3)
    assert result["boundary"]["budget_balance_claimed"] is False


def test_price_components_are_preserved_as_certified_intervals():
    document = _certificate(coverage="partial")
    document["price_certificate"]["components"][0]["price"] = _interval(
        "1.9", "2.1")
    result = us.settle(document)
    assert result["convex_hull_price_certificate"]["components"][0] == {
        "component_id": "t0",
        "price": _interval("1.9", "2.1"),
    }
    assert result["convex_hull_price_certificate"][
        "representation"] == us.PRICE_REPRESENTATION
    assert result["boundary"][
        "coordinate_price_intervals_are_outer_projections"] is True
    assert result["boundary"][
        "arbitrary_price_box_points_claimed_supporting"] is False
    demand = _participants(result)["demand"]
    assert demand["volumetric_charge_to_participant"] == _interval(
        "10.6", "11.4")


def test_signed_interval_products_cover_all_four_endpoint_products():
    assert us.Interval(
        Decimal("-2"), Decimal("-1")).multiply(
            us.Interval(Decimal("3"), Decimal("4"))).to_json() == \
        _interval(-8, -3)
    assert us.Interval(
        Decimal("-2"), Decimal("3")).multiply(
            us.Interval(Decimal("-4"), Decimal("5"))).to_json() == \
        _interval(-12, 15)
    assert us.interval_dot(
        [us.Interval(Decimal("-2"), Decimal("3"))],
        [us.Interval(Decimal("-4"), Decimal("5"))],
    ).to_json() == _interval(-12, 15)


def test_directed_rounding_encloses_values_beyond_working_precision():
    one = us.Interval.point("1")
    tiny = us.Interval.point("1e-90")
    enclosed_sum = one.add(tiny)
    with localcontext() as context:
        context.prec = 200
        exact_sum = Decimal(1) + Decimal("1e-90")
    assert enclosed_sum.lo <= exact_sum <= enclosed_sum.hi
    assert enclosed_sum.lo < enclosed_sum.hi

    long_value = "1." + ("2" * 100)
    enclosed_product = us.Interval.point(long_value).multiply(
        us.Interval.point(long_value))
    with localcontext() as context:
        context.prec = 300
        exact_product = Decimal(long_value) * Decimal(long_value)
    assert enclosed_product.lo <= exact_product <= enclosed_product.hi


def test_loc_raw_interval_is_preserved_and_nonnegative_theorem_tightens():
    document = _certificate(coverage="partial")
    # Assigned private cost is exactly 21; v in [19,22] gives raw [-1,2].
    document["participants"] = [document["participants"][0]]
    document["participants"][0]["best_response_objective"] = _interval(19, 22)
    result = us.settle(document)
    participant = result["participants"][0]
    assert participant["lost_opportunity_cost_raw"] == _interval(-1, 2)
    assert participant["lost_opportunity_cost"] == _interval(0, 2)
    # Dependency-safe identity v-c, not widened E-[0,2].
    assert participant["two_part_tariff"][
        "net_charge_to_participant_at_minimum_payment"] == _interval(9, 12)
    assert participant["two_part_tariff"][
        "assigned_all_in_cost_at_minimum_payment"] == _interval(19, 22)


def test_minimum_net_tariff_uses_dependency_cancellation_identity():
    document = _certificate(coverage="partial")
    document["price_certificate"]["components"] = [
        {"component_id": "t0", "price": _interval(9, 11)}
    ]
    participant = document["participants"][0]
    document["participants"] = [participant]
    participant["assigned_intrinsic_cost"] = _interval(4, 6)
    participant["assigned_net_withdrawal"] = [
        {"component_id": "t0", "quantity": _interval(1)}
    ]
    participant["best_response_objective"] = _interval(7, 8)
    result = us.settle(document)["participants"][0]
    assert result["volumetric_charge_to_participant"] == _interval(9, 11)
    assert result["lost_opportunity_cost"] == _interval(5, 10)
    # E - LOC as independent intervals would be [-1, 6].  The exact
    # dependency cancels E and gives v-c = [1, 4].
    assert result["two_part_tariff"][
        "net_charge_to_participant_at_minimum_payment"] == _interval(1, 4)


def test_uplift_raw_interval_is_preserved_and_nonnegative_theorem_tightens():
    document = _certificate(coverage="partial")
    document["objective_certificate"][
        "integrated_integer_objective"] = _interval(99, 101)
    document["objective_certificate"]["convex_hull_objective"] = _interval(100)
    result = us.settle(document)
    assert result["system"]["uplift_raw"] == _interval(-1, 1)
    assert result["system"]["uplift"] == _interval(0, 1)


def test_negative_loc_upper_endpoint_is_a_certificate_contradiction():
    document = _certificate(coverage="partial")
    document["participants"] = [document["participants"][0]]
    document["participants"][0]["best_response_objective"] = _interval(22, 23)
    with pytest.raises(us.SettlementError, match="negative upper endpoint"):
        us.settle(document)


def test_negative_uplift_upper_endpoint_is_a_certificate_contradiction():
    document = _certificate(coverage="partial")
    document["objective_certificate"][
        "integrated_integer_objective"] = _interval(95)
    document["objective_certificate"]["convex_hull_objective"] = _interval(100)
    with pytest.raises(us.SettlementError, match="negative upper endpoint"):
        us.settle(document)


def test_certified_joint_premises_require_uplift_loc_identity_intersection():
    document = _certificate()
    document["objective_certificate"][
        "integrated_integer_objective"] = _interval(101)
    with pytest.raises(us.SettlementError, match="do not intersect"):
        us.settle(document)


def test_complete_coverage_alone_makes_no_uplift_loc_identity_claim():
    document = _certificate()
    document["uplift_loc_identity_certificate"] = None
    document["objective_certificate"][
        "integrated_integer_objective"] = _interval(101)
    result = us.settle(document)
    aggregate = result["loc_aggregation"]
    assert result["coverage"] == "complete"
    assert aggregate["total_lost_opportunity_cost"] == _interval(3)
    assert result["system"]["uplift"] == _interval(4)
    assert aggregate["uplift_loc_identity_asserted"] is False
    assert aggregate["uplift_loc_identity_certificate_id"] is None
    assert aggregate["uplift_loc_identity_premises"] is None
    assert aggregate["uplift_loc_identity_consistent"] is None
    assert aggregate["uplift_loc_identity_intersection"] is None


def test_partial_coverage_makes_no_uplift_loc_identity_claim():
    document = _certificate(coverage="partial")
    document["objective_certificate"][
        "integrated_integer_objective"] = _interval(101)
    result = us.settle(document)
    aggregate = result["loc_aggregation"]
    assert aggregate["total_lost_opportunity_cost"] == _interval(3)
    assert aggregate["uplift_loc_identity_asserted"] is False
    assert aggregate["uplift_loc_identity_certificate_id"] is None
    assert aggregate["uplift_loc_identity_consistent"] is None
    assert aggregate["uplift_loc_identity_intersection"] is None
    assert result["boundary"]["budget_balance_claimed"] is False


@pytest.mark.parametrize("premise", us.IDENTITY_PREMISES)
def test_identity_certificate_requires_every_joint_premise(premise):
    document = _certificate()
    document["uplift_loc_identity_certificate"][premise] = False
    with pytest.raises(us.SettlementError, match=rf"{premise}=true"):
        us.settle(document)


@pytest.mark.parametrize(
    "mutate, match",
    [
        (
            lambda document: document.update({"outcome": "GO"}),
            "unknown=.*outcome",
        ),
        (
            lambda document: document["price_certificate"].update(
                {"status": "uncertified"}),
            "price_certificate.status",
        ),
        (
            lambda document: document["price_certificate"].update(
                {"representation": "cartesian-box"}),
            "outer-coordinate-projections",
        ),
        (
            lambda document: document["objective_certificate"].update(
                {"status": "uncertified"}),
            "objective_certificate.status",
        ),
        (
            lambda document: document["participants"][0].update(
                {"best_response_status": "uncertified"}),
            "best_response_status",
        ),
        (
            lambda document: document["participants"][0].update(
                {"assigned_action_certified_feasible": False}),
            "assigned_action_certified_feasible",
        ),
        (
            lambda document: document[
                "uplift_loc_identity_certificate"].update(
                    {"status": "uncertified"}),
            "identity_certificate.status",
        ),
        (
            lambda document: document[
                "uplift_loc_identity_certificate"].update(
                    {"assignment_integer_optimal": False}),
            "assignment_integer_optimal=true",
        ),
        (
            lambda document: document.update({"coverage": "partial"}),
            "requires complete participant coverage",
        ),
        (
            lambda document: document["participants"][0].update(
                {"price_certificate_id": "other-price"}),
            "does not match",
        ),
        (
            lambda document: document["participants"][0][
                "assigned_net_withdrawal"].reverse(),
            "component order/identity",
        ),
        (
            lambda document: document["participants"][0].update(
                {"assigned_net_withdrawal": _withdrawal(4, 1)[:1]}),
            "has 1 components",
        ),
        (
            lambda document: document["participants"].append(
                copy.deepcopy(document["participants"][0])),
            "participant_id values must be unique",
        ),
        (
            lambda document: document["price_certificate"]["components"].append(
                copy.deepcopy(
                    document["price_certificate"]["components"][0])),
            "duplicate price component_id",
        ),
    ],
)
def test_schema_identity_and_certificate_gates(mutate, match):
    document = _certificate()
    mutate(document)
    with pytest.raises(us.SettlementError, match=match):
        us.settle(document)


@pytest.mark.parametrize("bad", [0.1, float("nan"), float("inf"), True])
def test_binary_float_nonfinite_and_boolean_endpoints_are_refused(bad):
    document = _certificate()
    document["price_certificate"]["components"][0]["price"]["lo"] = bad
    with pytest.raises(us.SettlementError, match="exact decimal|finite"):
        us.settle(document)


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity", "not-a-number"])
def test_nonfinite_or_invalid_decimal_strings_are_refused(bad):
    document = _certificate()
    document["price_certificate"]["components"][0]["price"]["lo"] = bad
    with pytest.raises(us.SettlementError, match="finite|valid decimal"):
        us.settle(document)


def test_reversed_interval_is_refused():
    document = _certificate()
    document["objective_certificate"][
        "integrated_integer_objective"] = _interval(101, 100)
    with pytest.raises(us.SettlementError, match="reversed interval"):
        us.settle(document)


def test_canonical_digest_and_result_bytes_are_insertion_order_independent():
    document = _certificate()
    reordered = dict(reversed(list(document.items())))
    assert us.canonical_certificate_sha256(document) == \
        us.canonical_certificate_sha256(reordered)
    assert us.canonical_result_bytes(us.settle(document)) == \
        us.canonical_result_bytes(us.settle(reordered))


def test_no_replace_output_is_byte_deterministic(tmp_path):
    result = us.settle(_certificate())
    destination = tmp_path / "settlement.json"
    assert us.write_result_no_replace(destination, result) == str(
        destination.resolve())
    assert destination.read_bytes() == us.canonical_result_bytes(result)
    with pytest.raises(us.SettlementError, match="existing output"):
        us.write_result_no_replace(destination, result)
    assert destination.read_bytes() == us.canonical_result_bytes(result)


def test_cli_round_trip_uses_endpoint_json_only_and_refuses_overwrite(tmp_path):
    source = tmp_path / "endpoints.json"
    destination = tmp_path / "settlement.json"
    source.write_text(json.dumps(_certificate(), indent=2) + "\n")
    script = us.REPO_ROOT / "src" / "experiments" / "uplift_settlement.py"
    command = [
        sys.executable,
        str(script),
        "--input",
        str(source),
        "--output",
        str(destination),
    ]
    completed = subprocess.run(
        command, cwd=us.REPO_ROOT / "src", capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    assert json.loads(destination.read_bytes()) == us.settle(_certificate())
    repeated = subprocess.run(
        command, cwd=us.REPO_ROOT / "src", capture_output=True, text=True)
    assert repeated.returncode == 2
    assert "existing output destination" in repeated.stderr


def test_loader_refuses_duplicate_json_keys(tmp_path):
    source = tmp_path / "duplicate.json"
    source.write_text(
        '{"schema":"uplift-settlement-endpoints-v1",'
        '"schema":"uplift-settlement-endpoints-v1"}\n')
    with pytest.raises(us.SettlementError, match="duplicate key 'schema'"):
        us.load_endpoint_certificate(source)


def test_repository_result_paths_are_refused_before_content_io(monkeypatch):
    def forbidden_read(_self):
        raise AssertionError("result content must not be read")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    forbidden = us.REPO_ROOT / "result" / "never-read-endpoints.json"
    with pytest.raises(us.SettlementError, match="outcome-blind boundary"):
        us.load_endpoint_certificate(forbidden)


def test_repository_result_output_path_is_refused(tmp_path):
    forbidden = us.REPO_ROOT / "result" / "never-write-settlement.json"
    with pytest.raises(us.SettlementError, match="outcome-blind boundary"):
        us.write_result_no_replace(forbidden, us.settle(_certificate()))
    assert not forbidden.exists()


def test_symlink_alias_into_repository_results_is_refused(tmp_path):
    alias = tmp_path / "result-alias"
    alias.symlink_to(us.REPO_ROOT / "result", target_is_directory=True)
    with pytest.raises(us.SettlementError, match="outcome-blind boundary"):
        us.load_endpoint_certificate(alias / "never-read.json")


def test_import_is_stdlib_only_and_does_not_load_solver_or_numerical_stack():
    script = """
import json, sys
import experiments.uplift_settlement
blocked = sorted(
    name for name in sys.modules
    if name.split('.')[0] in {'egglab', 'mip', 'numpy', 'pandas', 'scipy'}
)
print(json.dumps(blocked))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=us.REPO_ROOT / "src",
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == []


def test_programmatic_interval_rejects_dimension_mismatch():
    with pytest.raises(us.SettlementError, match="dimension mismatch"):
        us.interval_dot([us.Interval.point(1)], [])
