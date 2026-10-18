"""Outcome-blind acceptance battery for settlement arithmetic.

Fixtures are invented or produced by tiny local CBC solves on burned seeds
{0, 11, 15}, with at most four trips. No experiment population, checkpoint,
run tree, or committed result artifact is opened.
"""
from __future__ import annotations

import copy
import hashlib
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


def _best_response_evidence(
    certificate_id,
    lower,
    upper=None,
    *,
    prices=("2", "3"),
    load=("0", "0"),
):
    upper = lower if upper is None else upper
    price_vector = [
        {"component_id": "t0", "value": str(prices[0])},
        {"component_id": "t1", "value": str(prices[1])},
    ]
    load_values = [str(value) for value in load]
    private_energy = sum(
        Decimal(item["value"]) * Decimal(quantity)
        for item, quantity in zip(price_vector, load_values))
    intrinsic = Decimal(str(upper)) - private_energy
    schedule = {
        "sequences": [[f"{certificate_id}-trip"]],
        "arc_kinds": [[]],
        "charges": [],
        "fleet": 1,
    }
    witness = {
        "schedule": schedule,
        "load": load_values,
        "intrinsic_cost": str(intrinsic),
        "witness_sha256": us.witness_sha256(
            schedule, load_values, str(intrinsic)),
        "load_sha256": us.load_sha256(load_values),
        "certified_feasible": True,
        "replay_result": {
            "status": "passed",
            "policy": "invented-independent-replay-v1",
            "violations": [],
        },
    }
    return {
        "schema": us.BEST_RESPONSE_EVIDENCE_SCHEMA,
        "certificate_id": certificate_id,
        "status": "certified",
        "evidence_tier": us.GLOBAL_EXACT_ORACLE_TIER,
        "instance_hash": hashlib.sha256(
            certificate_id.encode()).hexdigest(),
        "price_certificate_id": "invented-price-cert",
        "price_vector": price_vector,
        "price_vector_sha256": us.price_vector_sha256(price_vector),
        "objective_convention": us.PRIVATE_OBJECTIVE_CONVENTION,
        "witness": witness,
        "solver": {
            "backend": "CBC",
            "solver_version": "invented-cbc",
            "status": "OPTIMAL",
            "max_mip_gap": "0.000001",
        },
        "incumbent": str(upper),
        "certified_dual_bound": str(lower),
    }


def _refresh_evidence_witness(evidence):
    witness = evidence["witness"]
    prices = [
        Decimal(item["value"]) for item in evidence["price_vector"]]
    load = [Decimal(item) for item in witness["load"]]
    witness["intrinsic_cost"] = str(
        Decimal(evidence["incumbent"])
        - sum(price * quantity for price, quantity in zip(prices, load)))
    witness["witness_sha256"] = us.witness_sha256(
        witness["schedule"], witness["load"], witness["intrinsic_cost"])
    witness["load_sha256"] = us.load_sha256(witness["load"])


def _set_best_response_interval(participant, lower, upper=None):
    upper = lower if upper is None else upper
    evidence = participant["best_response_evidence"]
    evidence["certified_dual_bound"] = str(lower)
    evidence["incumbent"] = str(upper)
    _refresh_evidence_witness(evidence)


def _set_evidence_prices(participant, prices):
    evidence = participant["best_response_evidence"]
    evidence["price_vector"] = [
        {"component_id": f"t{index}", "value": str(value)}
        for index, value in enumerate(prices)
    ]
    old_load = list(evidence["witness"]["load"])
    evidence["witness"]["load"] = (
        old_load[:len(prices)]
        + ["0"] * max(0, len(prices) - len(old_load)))
    evidence["price_vector_sha256"] = us.price_vector_sha256(
        evidence["price_vector"])
    _refresh_evidence_witness(evidence)


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
                "best_response_evidence": _best_response_evidence(
                    "demand-br-cert", 19),
            },
            {
                "participant_id": "supply",
                "assigned_action_id": "supply-assignment",
                "price_certificate_id": "invented-price-cert",
                "assigned_action_certified_feasible": True,
                "assigned_intrinsic_cost": _interval(5),
                "assigned_net_withdrawal": _withdrawal(-4, -1),
                "best_response_evidence": _best_response_evidence(
                    "supply-br-cert", -7),
            },
        ],
    }


def _participants(result):
    return {row["participant_id"]: row for row in result["participants"]}


@pytest.fixture
def uplift_regret_counterexample():
    """Two fleet blocks: target regret 2, other regret 1, internal uplift 3."""
    document = _certificate()
    document["case_id"] = "explicit-uplift-not-single-fleet-regret"
    return document


def test_internal_uplift_is_not_target_fleet_regret_at_ch_price(
        uplift_regret_counterexample):
    result = us.settle(uplift_regret_counterexample)
    fleets = _participants(result)
    target_regret = fleets["demand"]["price_conditioned_regret"]
    other_regret = fleets["supply"]["price_conditioned_regret"]
    internal_uplift = result["system"]["uplift"]

    assert target_regret == _interval(2)
    assert other_regret == _interval(1)
    assert internal_uplift == _interval(3)
    assert target_regret != internal_uplift
    # Under this fixture's explicit complete joint identity certificate, the
    # documented relation is the SUM over fleet blocks, not equality with one
    # target fleet's regret.
    assert result["regret_aggregation"][
        "total_price_conditioned_regret"] == internal_uplift
    assert result["regret_aggregation"][
        "uplift_identity_intersection"] == _interval(3)


def test_exact_complete_settlement_and_two_part_tariff():
    result = us.settle(_certificate())
    assert result["schema"] == us.OUTPUT_SCHEMA
    assert result["coverage"] == "complete"
    assert result["system"]["uplift_raw"] == _interval(3)
    assert result["system"]["uplift"] == _interval(3)

    participants = _participants(result)
    demand = participants["demand"]
    assert demand["best_response_evidence"]["schema"] == (
        us.BEST_RESPONSE_EVIDENCE_SCHEMA)
    assert demand["best_response_evidence"]["evidence_tier"] == (
        us.GLOBAL_EXACT_ORACLE_TIER)
    assert demand["best_response_value"] == _interval(19)
    assert demand["volumetric_charge_to_participant"] == _interval(11)
    assert demand["assigned_private_cost_before_commitment"] == _interval(21)
    assert demand["lost_opportunity_cost_raw"] == _interval(2)
    assert demand["lost_opportunity_cost"] == _interval(2)
    assert demand["target_private_cost_at_best_response_price"] == _interval(21)
    assert demand["price_conditioned_regret_raw"] == _interval(2)
    assert demand["price_conditioned_regret"] == _interval(2)
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
    assert result["regret_aggregation"][
        "total_price_conditioned_regret"] == _interval(3)
    assert result["regret_aggregation"][
        "uplift_identity_intersection"] == _interval(3)
    assert result["boundary"]["budget_balance_claimed"] is False
    assert result["boundary"]["single_fleet_accounting_only"] is True
    assert result["boundary"]["per_vehicle_payment_allocation_included"] is False
    assert result["boundary"]["individual_rationality_claimed"] is False
    assert result["boundary"][
        "schedule_physics_replayed_by_settlement"] is False
    assert result["boundary"]["instance_hash_verified_by_settlement"] is False
    assert result["boundary"]["oracle_re_solved_by_settlement"] is False


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
    _set_best_response_interval(document["participants"][0], 19, 22)
    result = us.settle(document)
    participant = result["participants"][0]
    assert participant["lost_opportunity_cost_raw"] == _interval(-1, 2)
    assert participant["lost_opportunity_cost"] == _interval(0, 2)
    assert participant["price_conditioned_regret_raw"] == _interval(-1, 2)
    assert participant["price_conditioned_regret"] == _interval(0, 2)
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
    _set_evidence_prices(participant, [10])
    _set_best_response_interval(participant, 7, 8)
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
    _set_best_response_interval(document["participants"][0], 22, 23)
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
            lambda document: document["participants"][0][
                "best_response_evidence"].update(
                    {"status": "uncertified"}),
            "best_response_evidence.status",
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


@pytest.mark.parametrize(
    "mutate, match",
    [
        (
            lambda evidence: evidence.update(
                {"evidence_tier": "restricted-pool-v1"}),
            "restricted-pool and heuristic evidence cannot certify",
        ),
        (
            lambda evidence: evidence.update(
                {"price_vector_sha256": "0" * 64}),
            "price_vector_sha256 does not recompute",
        ),
        (
            lambda evidence: evidence.update(
                {"instance_hash": "not-a-hash"}),
            "instance_hash must be lowercase hexadecimal",
        ),
        (
            lambda evidence: evidence.update(
                {"certified_dual_bound": "20", "incumbent": "19"}),
            "certified_dual_bound exceeds incumbent",
        ),
        (
            lambda evidence: evidence["witness"]["schedule"].update(
                {"fleet": 2}),
            "fleet must equal",
        ),
        (
            lambda evidence: evidence["witness"]["load"].__setitem__(0, "1"),
            "witness_sha256 does not recompute",
        ),
        (
            lambda evidence: evidence["witness"]["replay_result"].update(
                {"violations": ["tampered load"]}),
            "replay must be passed",
        ),
        (
            lambda evidence: evidence["solver"].update(
                {"status": "FEASIBLE"}),
            "solver.status must be 'OPTIMAL'",
        ),
    ],
)
def test_best_response_evidence_tampering_fails_closed(mutate, match):
    document = _certificate(coverage="partial")
    document["participants"] = [document["participants"][0]]
    evidence = document["participants"][0]["best_response_evidence"]
    mutate(evidence)
    with pytest.raises(us.SettlementError, match=match):
        us.settle(document)


def test_coordinated_witness_rehash_still_must_match_incumbent():
    document = _certificate(coverage="partial")
    document["participants"] = [document["participants"][0]]
    evidence = document["participants"][0]["best_response_evidence"]
    evidence["witness"]["load"][0] = "1"
    witness = evidence["witness"]
    witness["witness_sha256"] = us.witness_sha256(
        witness["schedule"], witness["load"], witness["intrinsic_cost"])
    witness["load_sha256"] = us.load_sha256(witness["load"])
    with pytest.raises(
            us.SettlementError, match="incumbent disagrees with"):
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
        '{"schema":"uplift-settlement-endpoints-v2",'
        '"schema":"uplift-settlement-endpoints-v2"}\n')
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


def _solver_backed_document(inst, prices, solution):
    from egglab.evsp import REPLAY_POLICY_VERSION, validate_solution

    component_ids = [f"slot-{index:02d}" for index in range(len(prices))]
    price_vector = [
        {"component_id": component_id, "value": repr(float(price))}
        for component_id, price in zip(component_ids, prices)
    ]
    schedule = {
        "sequences": [list(sequence) for sequence in solution.sequences],
        "arc_kinds": [list(kinds) for kinds in solution.arc_kinds],
        "charges": [
            {
                **{key: charge[key] for key in (
                    "vehicle", "after_trip", "before_trip", "slot")},
                "kwh": repr(float(charge["kwh"])),
            }
            for charge in solution.charges
        ],
        "fleet": solution.fleet,
    }
    load = [repr(float(value)) for value in solution.load]
    intrinsic = repr(float(solution.ops_cost))
    violations = validate_solution(inst, solution)
    assert violations == []
    evidence = {
        "schema": us.BEST_RESPONSE_EVIDENCE_SCHEMA,
        "certificate_id": f"solver-{inst.name}",
        "status": "certified",
        "evidence_tier": us.GLOBAL_EXACT_ORACLE_TIER,
        "instance_hash": inst.hash(),
        "price_certificate_id": "solver-price",
        "price_vector": price_vector,
        "price_vector_sha256": us.price_vector_sha256(price_vector),
        "objective_convention": us.PRIVATE_OBJECTIVE_CONVENTION,
        "witness": {
            "schedule": schedule,
            "load": load,
            "intrinsic_cost": intrinsic,
            "witness_sha256": us.witness_sha256(schedule, load, intrinsic),
            "load_sha256": us.load_sha256(load),
            "certified_feasible": True,
            "replay_result": {
                "status": "passed",
                "policy": f"evsp-replay-v{REPLAY_POLICY_VERSION}",
                "violations": [],
            },
        },
        "solver": {
            "backend": solution.stats.backend,
            "solver_version": "python-mip",
            "status": solution.stats.status,
            "max_mip_gap": repr(float(solution.stats.max_mip_gap)),
        },
        "incumbent": repr(float(solution.stats.obj)),
        "certified_dual_bound": repr(float(solution.stats.bound)),
    }
    return {
        "schema": us.INPUT_SCHEMA,
        "case_id": f"solver-backed-{inst.name}",
        "coverage": "partial",
        "units": {"currency": "SEK", "quantity": "kWh"},
        "price_certificate": {
            "certificate_id": "solver-price",
            "status": "certified",
            "representation": us.PRICE_REPRESENTATION,
            "components": [
                {"component_id": item["component_id"],
                 "price": _interval(item["value"])}
                for item in price_vector
            ],
        },
        "objective_certificate": {
            "certificate_id": "scope-only-system-objectives",
            "status": "certified",
            "integrated_integer_objective": _interval(0),
            "convex_hull_objective": _interval(0),
        },
        "uplift_loc_identity_certificate": None,
        "participants": [{
            "participant_id": "single-fleet",
            "assigned_action_id": "solver-incumbent",
            "price_certificate_id": "solver-price",
            "assigned_action_certified_feasible": True,
            "assigned_intrinsic_cost": _interval(intrinsic),
            "assigned_net_withdrawal": [
                {"component_id": component_id, "quantity": _interval(quantity)}
                for component_id, quantity in zip(component_ids, load)
            ],
            "best_response_evidence": evidence,
        }],
    }


@pytest.mark.parametrize("seed", [0, 11, 15])
def test_burned_seed_solve_taker_certificate_is_enclosed(seed):
    import numpy as np
    from egglab.instance import synthetic_instance
    from egglab.regimes import solve_taker

    inst = synthetic_instance(seed=seed, n_trips=6)
    prices = np.linspace(0.5, 2.0, inst.n_slots)
    solution = solve_taker(
        inst, prices, max_mip_gap=1e-6, time_limit_s=None)
    assert solution.stats.backend == "CBC"
    result = us.settle(_solver_backed_document(inst, prices, solution))
    participant = result["participants"][0]
    certified = participant["best_response_value"]
    incumbent = Decimal(repr(float(solution.stats.obj)))
    tolerance = us.BEST_RESPONSE_VALIDATION_TOLERANCE
    assert Decimal(certified["lo"]) - tolerance <= incumbent
    assert incumbent <= Decimal(certified["hi"]) + tolerance
    regret = participant["price_conditioned_regret"]
    assert Decimal(regret["lo"]) == 0
    assert Decimal(regret["hi"]) >= 0


def test_complete_tiny_enumeration_agrees_with_global_certificate():
    import numpy as np
    from egglab.enumerate_tiny import enumerate_structures
    from egglab.evsp import solve_fixed_sequences
    from egglab.instance import synthetic_instance
    from egglab.regimes import solve_taker

    inst = synthetic_instance(seed=0, n_trips=4)
    prices = np.linspace(0.75, 1.75, inst.n_slots)
    global_solution = solve_taker(
        inst, prices, max_mip_gap=1e-6, time_limit_s=None)
    partitions = {
        tuple(tuple(sequence) for sequence in structure["sequences"])
        for structure in enumerate_structures(inst)
    }
    enumerated_values = []
    for partition in sorted(partitions):
        candidate = solve_fixed_sequences(
            inst, [list(sequence) for sequence in partition],
            ("linear", prices), max_mip_gap=1e-6, time_limit_s=None)
        if candidate is not None:
            enumerated_values.append(float(candidate.obj_model))
    assert enumerated_values
    enumerated_best = min(enumerated_values)

    result = us.settle(
        _solver_backed_document(inst, prices, global_solution))
    certified = result["participants"][0]["best_response_value"]
    tolerance = float(us.BEST_RESPONSE_VALIDATION_TOLERANCE) + 1e-5
    assert float(certified["lo"]) - tolerance <= enumerated_best
    assert enumerated_best <= float(certified["hi"]) + tolerance
    assert float(global_solution.stats.obj) == pytest.approx(
        enumerated_best, abs=tolerance)


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
