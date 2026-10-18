"""Acceptance battery for the bounded strict-two-cycle delta debugger."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import egglab.enumerate_tiny as enumerate_tiny_module
from egglab.b2a2 import B2A2Error
from egglab.cycle_minimizer import (
    TARGET_MAX_TRIPS,
    build_witness,
    canonical_witness_bytes,
    minimize_fixture,
    witness_payload_sha256,
)
from egglab.enumerate_tiny import (
    _instance_from_canonical,
    _solution_from_record,
    replay_cycle_witness,
    response_inventory_invariants,
    structure_id,
)
from egglab.evsp import validate_solution
from egglab.market import AffineMarket
from egglab.solver import backend
from experiments.minimize_strict_cycle import artifact_payloads


@pytest.fixture(scope="module")
def reduced():
    return minimize_fixture()


@pytest.fixture(scope="module")
def witness(reduced):
    return build_witness(reduced)


def test_delta_debugger_reaches_irreducible_four_trip_core(reduced):
    inst = reduced["instance"]
    assert len(inst.trips) == TARGET_MAX_TRIPS == 4
    assert sorted(t.id for t in inst.trips) == [
        "t000", "t001", "t002", "t003"]
    assert reduced["kept_feedback_slots"] == [13]
    assert inst.max_vehicles == 2
    assert any(
        event["axis"] == "trips"
        and event["accepted"]
        and "padding" in event["removed"]
        for event in reduced["reduction_trace"]
    )
    assert all(
        not trial["accepted"] for trial in reduced["irreducibility_trials"])


def test_witness_contains_complete_strict_cycle_evidence(witness):
    evidence = witness["computational_evidence"]
    cycle = evidence["cycle"]
    assert cycle["period"] == 2
    assert len(cycle["both_schedules"]) == 2
    assert len(cycle["complete_iteration_trajectory"]) == 3
    assert (
        cycle["both_schedules"][0]["structure_id"]
        != cycle["both_schedules"][1]["structure_id"]
    )

    strict = evidence["strict_best_response"]
    ceiling = witness["tolerances"]["objective_tolerance_ceiling"]
    assert strict["all_margins_clear_tolerances"]
    assert strict["minimum_global_discrete_structure_margin"] > ceiling
    assert strict["minimum_opposite_cycle_endpoint_margin"] > ceiling
    assert all(
        state["optimal_face_load_uniqueness"][
            "max_certified_load_range_upper_kwh"]
        <= witness["tolerances"]["optimal_face_load_kwh"]
        for state in strict["states"]
    )

    enumerated = evidence["exhaustive_feasible_response_enumeration"]
    assert len(enumerated["states"]) == 2
    for state in enumerated["states"]:
        assert state["n_structures"] == (
            state["n_feasible"] + state["n_infeasible"])
        assert len(state["responses"]) == state["n_structures"]
        assert all("solution" not in row for row in state["responses"])


def test_fixed_point_and_hull_claims_are_separated(witness):
    claims = witness["claims"]
    assert claims["computational_evidence"]["status"] == "pass"
    assert claims["theorem_claims"][0]["id"] == (
        "T1-fixed-point-necessary-dictator")
    assert "a+b*U" in claims["theorem_claims"][0]["statement"]
    assert "no universal" in claims["not_claimed"][0]
    assert "1-minimal-only" in (
        claims["computational_evidence"]["statements"][-1])

    absence = witness["computational_evidence"]["fixed_point_absence"]
    ceiling = witness["tolerances"]["objective_tolerance_ceiling"]
    assert absence["conclusion"] == "no_fixed_point"
    assert absence["passes_tolerance"]
    assert absence["unique_dictator_structure_margin"] > ceiling
    assert absence["profitable_deviation_margin"] > ceiling
    assert all(
        "solution" not in row
        for row in absence["enumerated_dictator"]["structures"])

    comparison = witness[
        "computational_evidence"]["convex_hull_dictator_comparison"]
    lo, hi = comparison["uplift_interval"]
    assert 0.0 < lo <= hi
    assert comparison["z_ch_lower_model"] <= (
        comparison["z_ch_upper_exact_incumbent"])
    assert "z_ch_load" not in comparison


def test_enumerate_tiny_independently_replays_every_gate(witness):
    report = replay_cycle_witness(witness)
    assert report == witness["independent_replay"]
    assert report["status"] == "pass"
    assert all(report["checks"].values())
    assert report["irreducibility_trials_replayed"] == len(
        witness["computational_evidence"]["irreducibility"]["trials"])


def test_integrity_and_tamper_detection(witness):
    assert witness["integrity"]["canonical_payload_sha256"] == (
        witness_payload_sha256(witness))
    tampered = copy.deepcopy(witness)
    tampered["instance"]["trips"][0]["energy_kwh"] += 0.1
    with pytest.raises(B2A2Error, match="payload hash mismatch"):
        replay_cycle_witness(tampered)


@pytest.fixture(scope="module")
def backend_degeneracy_fixture(reduced, witness):
    enumeration = copy.deepcopy(
        reduced["certificate"]["enumerations"][1])
    sid = (
        "663382c80031edd1b94cb3271b2ede508"
        "82466bc33893c6e51ec956d3ea43e33"
    )
    row = next(
        response for response in enumeration["responses"]
        if response["structure_id"] == sid)
    alternate = copy.deepcopy(row["solution"])
    alternate["charges"][0].update(
        after_trip="t001", before_trip="t002", slot=14)
    alternate["load"][12] = 0.0
    alternate["load"][14] = 14.5
    return {
        "enumeration": enumeration,
        "structure_id": sid,
        "recorded": row,
        "alternate": alternate,
        "instance": _instance_from_canonical(witness["instance"]),
    }


def test_degenerate_losing_response_uses_invariant_certificate(
        backend_degeneracy_fixture, witness, monkeypatch):
    fixture = backend_degeneracy_fixture
    enumeration = fixture["enumeration"]
    sid = fixture["structure_id"]
    row = fixture["recorded"]
    alternate = fixture["alternate"]
    inst = fixture["instance"]
    prices = np.asarray(enumeration["prices"], dtype=float)
    original_objective = (
        row["solution"]["ops_cost"]
        + float(np.dot(prices, row["solution"]["load"]))
    )
    alternate_objective = (
        alternate["ops_cost"]
        + float(np.dot(prices, alternate["load"]))
    )
    alternate_sol = _solution_from_record(alternate)
    assert validate_solution(inst, alternate_sol) == []
    assert structure_id(
        alternate_sol.sequences, alternate_sol.arc_kinds) == sid
    assert alternate_objective == pytest.approx(original_objective, abs=1e-9)

    before = response_inventory_invariants(enumeration)
    row["solution"] = alternate
    after = response_inventory_invariants(enumeration)
    assert before == after

    real_enumerate = enumerate_tiny_module.enumerate_price_responses

    def equivalent_backend_choice(inst_arg, posted_prices):
        result = real_enumerate(inst_arg, posted_prices)
        if np.max(np.abs(
                np.asarray(posted_prices, dtype=float) - prices)) <= 1e-12:
            backend_row = next(
                (
                    response for response in result["responses"]
                    if response["structure_id"] == sid
                ),
                None,
            )
            if backend_row is not None:
                backend_row["solution"] = copy.deepcopy(alternate)
        return result

    monkeypatch.setattr(
        enumerate_tiny_module,
        "enumerate_price_responses",
        equivalent_backend_choice,
    )
    assert replay_cycle_witness(witness)["status"] == "pass"


def test_semantic_tampering_rejected_without_hash_gate(witness):
    mutations = []

    def losing_row(candidate):
        state = candidate["computational_evidence"][
            "exhaustive_feasible_response_enumeration"]["states"][0]
        return next(
            row for row in state["responses"]
            if row.get("feasible")
            and row["structure_id"] != state["best_structure_id"])

    mutations.append(
        lambda candidate: losing_row(candidate).__setitem__(
            "objective", losing_row(candidate)["objective"] + 1.0))
    mutations.append(
        lambda candidate: losing_row(candidate).__setitem__("feasible", False))
    mutations.append(
        lambda candidate: losing_row(candidate).__setitem__(
            "structure_id", "0" * 64))

    for mutate in mutations:
        candidate = copy.deepcopy(witness)
        mutate(candidate)
        with pytest.raises(B2A2Error, match="witness replay mismatch"):
            replay_cycle_witness(candidate, verify_integrity=False)


def test_selected_response_primitives_and_face_tampering_rejected(witness):
    candidate = copy.deepcopy(witness)
    selected = candidate["computational_evidence"]["cycle"][
        "complete_iteration_trajectory"][0]["response"]
    selected["charges"][0]["kwh"] += 1.0
    with pytest.raises(B2A2Error, match="load is inconsistent"):
        replay_cycle_witness(candidate, verify_integrity=False)

    candidate = copy.deepcopy(witness)
    selected = candidate["computational_evidence"]["cycle"][
        "complete_iteration_trajectory"][0]["response"]
    selected["ops_cost"] += 5.0
    with pytest.raises(B2A2Error, match="operations cost"):
        replay_cycle_witness(candidate, verify_integrity=False)

    candidate = copy.deepcopy(witness)
    face = candidate["computational_evidence"]["strict_best_response"][
        "states"][0]["optimal_face_load_uniqueness"]
    face["max_certified_load_range_upper_kwh"] = 999.0
    with pytest.raises(B2A2Error, match="witness replay mismatch"):
        replay_cycle_witness(candidate, verify_integrity=False)


def _tamper_path(candidate, path):
    target = candidate
    for key in path[:-1]:
        target = target[key]
    key = path[-1]
    value = target[key]
    if isinstance(value, bool):
        target[key] = not value
    elif isinstance(value, (int, float)):
        target[key] = value + 1
    elif isinstance(value, str):
        target[key] = value + "-tampered"
    else:
        raise AssertionError(f"unsupported tamper value at {path}: {value!r}")


STRICT_STATE_TAMPER_PATHS = [
    (
        "computational_evidence",
        "strict_best_response",
        "states",
        state,
        field,
    )
    for state in (0, 1)
    for field in (
        "state",
        "chosen_structure_id",
        "chosen_objective",
        "runner_up_structure_id",
        "runner_up_objective",
        "global_discrete_structure_margin",
        "opposite_cycle_endpoint_margin",
    )
]
STRICT_STATE_TAMPER_PATHS += [
    (
        "computational_evidence",
        "strict_best_response",
        "states",
        state,
        "optimal_face_load_uniqueness",
        "max_certified_load_range_upper_kwh",
    )
    for state in (0, 1)
]


@pytest.mark.parametrize(
    "path",
    STRICT_STATE_TAMPER_PATHS,
    ids=[
        f"state-{path[3]}-{path[-1]}"
        for path in STRICT_STATE_TAMPER_PATHS
    ],
)
def test_complete_strict_state_summary_tampering_rejected(witness, path):
    candidate = copy.deepcopy(witness)
    _tamper_path(candidate, path)
    with pytest.raises(B2A2Error):
        replay_cycle_witness(candidate, verify_integrity=False)


STRICT_AGGREGATE_TAMPER_PATHS = [
    ("computational_evidence", "strict_best_response", "scope"),
    (
        "computational_evidence",
        "strict_best_response",
        "minimum_global_discrete_structure_margin",
    ),
    (
        "computational_evidence",
        "strict_best_response",
        "minimum_opposite_cycle_endpoint_margin",
    ),
    (
        "computational_evidence",
        "strict_best_response",
        "maximum_certified_load_range_upper_kwh",
    ),
    (
        "computational_evidence",
        "strict_best_response",
        "objective_tolerance_ceiling",
    ),
    (
        "computational_evidence",
        "strict_best_response",
        "all_margins_clear_tolerances",
    ),
]


@pytest.mark.parametrize(
    "path",
    STRICT_AGGREGATE_TAMPER_PATHS,
    ids=[path[-1] for path in STRICT_AGGREGATE_TAMPER_PATHS],
)
def test_strict_summary_aggregate_tampering_rejected(witness, path):
    candidate = copy.deepcopy(witness)
    _tamper_path(candidate, path)
    with pytest.raises(B2A2Error):
        replay_cycle_witness(candidate, verify_integrity=False)


FIXED_POINT_TAMPER_PATHS = [
    (
        "computational_evidence",
        "fixed_point_absence",
        "candidate_induced_prices",
        0,
    ),
    (
        "computational_evidence",
        "fixed_point_absence",
        "candidate_linear_objective",
    ),
    (
        "computational_evidence",
        "fixed_point_absence",
        "best_response_at_candidate_prices",
        "structure_id",
    ),
    (
        "computational_evidence",
        "fixed_point_absence",
        "best_response_at_candidate_prices",
        "objective",
    ),
    (
        "computational_evidence",
        "fixed_point_absence",
        "best_response_at_candidate_prices",
        "solution",
        "fleet",
    ),
    (
        "computational_evidence",
        "fixed_point_absence",
        "profitable_deviation_margin",
    ),
    (
        "computational_evidence",
        "fixed_point_absence",
        "passes_tolerance",
    ),
    (
        "computational_evidence",
        "fixed_point_absence",
        "conclusion",
    ),
]


@pytest.mark.parametrize(
    "path",
    FIXED_POINT_TAMPER_PATHS,
    ids=[path[-1] for path in FIXED_POINT_TAMPER_PATHS],
)
def test_fixed_point_summary_tampering_rejected(witness, path):
    candidate = copy.deepcopy(witness)
    _tamper_path(candidate, path)
    with pytest.raises(B2A2Error):
        replay_cycle_witness(candidate, verify_integrity=False)


CYCLE_SUMMARY_TAMPER_PATHS = [
    ("computational_evidence", "cycle", "alpha"),
    ("computational_evidence", "cycle", "period"),
    ("computational_evidence", "cycle", "outcome", "type"),
    ("computational_evidence", "cycle", "outcome", "length"),
    (
        "computational_evidence",
        "cycle",
        "both_schedules",
        0,
        "fleet",
    ),
    ("computational_evidence", "cycle", "loads", 0, 13),
    ("computational_evidence", "cycle", "induced_prices", 0, 13),
    (
        "computational_evidence",
        "cycle",
        "price_state_separation_inf",
    ),
    (
        "computational_evidence",
        "cycle",
        "load_state_separation_inf_kwh",
    ),
    (
        "computational_evidence",
        "cycle",
        "complete_iteration_trajectory",
        0,
        "response",
        "fleet",
    ),
]


@pytest.mark.parametrize(
    "path",
    CYCLE_SUMMARY_TAMPER_PATHS,
    ids=[
        "-".join(str(part) for part in path[2:])
        for path in CYCLE_SUMMARY_TAMPER_PATHS
    ],
)
def test_cycle_summary_and_redundant_response_tampering_rejected(
        witness, path):
    candidate = copy.deepcopy(witness)
    _tamper_path(candidate, path)
    with pytest.raises(B2A2Error):
        replay_cycle_witness(candidate, verify_integrity=False)


SELECTED_RESPONSE_TAMPER_PATHS = [
    (
        "computational_evidence",
        "cycle",
        "complete_iteration_trajectory",
        0,
        "response",
        "structure_id",
    ),
    (
        "computational_evidence",
        "cycle",
        "complete_iteration_trajectory",
        0,
        "response",
        "fleet",
    ),
    (
        "computational_evidence",
        "cycle",
        "complete_iteration_trajectory",
        0,
        "response",
        "energy_charged_kwh",
    ),
    (
        "computational_evidence",
        "cycle",
        "complete_iteration_trajectory",
        0,
        "response",
        "load",
        13,
    ),
    (
        "computational_evidence",
        "cycle",
        "complete_iteration_trajectory",
        0,
        "response",
        "arc_kinds",
        0,
        0,
    ),
    (
        "computational_evidence",
        "cycle",
        "complete_iteration_trajectory",
        0,
        "response",
        "charges",
        0,
        "slot",
    ),
]


@pytest.mark.parametrize(
    "path",
    SELECTED_RESPONSE_TAMPER_PATHS,
    ids=[path[-1] for path in SELECTED_RESPONSE_TAMPER_PATHS],
)
def test_redundant_selected_response_field_tampering_rejected(witness, path):
    candidate = copy.deepcopy(witness)
    _tamper_path(candidate, path)
    with pytest.raises(B2A2Error):
        replay_cycle_witness(candidate, verify_integrity=False)


def test_dictator_quadratic_includes_base_load_coupling():
    a = np.array([2.0])
    b = np.array([0.5])
    base_load = np.array([100.0])
    load = np.array([4.0])
    ops = 17.0
    market = AffineMarket(a, b, base_load)

    correct = ops + market.system_cost_delta(load)
    missing_base_term = (
        ops + float(np.dot(a, load))
        + 0.5 * float(np.dot(b, load * load))
    )
    assert correct == pytest.approx(229.0)
    assert missing_base_term == pytest.approx(29.0)
    assert correct - missing_base_term == pytest.approx(
        float(np.dot(b, base_load * load)))


def test_zero_base_load_normalization_preserves_price_and_dictator_map():
    raw = AffineMarket([1.0], [1.0], [10.0])
    normalized = AffineMarket(
        raw.price(np.zeros(1)), [1.0], np.zeros(1))
    for value in (0.0, 1.0, 3.0, 7.5):
        load = np.array([value])
        assert raw.price(load) == pytest.approx(normalized.price(load))
        assert raw.system_cost_delta(load) == pytest.approx(
            normalized.system_cost_delta(load))


def test_artifact_manifest_and_summary_pin_analysis_commit(witness):
    analysis_commit = "a" * 40
    payloads = artifact_payloads(
        canonical_witness_bytes(witness), analysis_commit)
    manifest = json.loads(payloads["MANIFEST.json"])
    assert manifest["analysis_code_commit"] == analysis_commit
    assert manifest["analysis_code_verified"] is True
    assert set(payloads) == {"WITNESS.json", "MANIFEST.json", "SUMMARY.md"}
    assert set(manifest["outputs"]) == {"WITNESS.json", "SUMMARY.md"}
    assert analysis_commit.encode() in payloads["SUMMARY.md"]


def test_committed_witness_bundle_is_byte_identical(witness):
    root = Path(__file__).resolve().parents[2] / "result" / "strict_two_cycle"
    manifest = json.loads((root / "MANIFEST.json").read_bytes())
    payloads = artifact_payloads(
        canonical_witness_bytes(witness),
        manifest["analysis_code_commit"],
    )
    for filename, payload in payloads.items():
        assert (root / filename).read_bytes() == payload


def test_standalone_cbc_replay_cli(witness, tmp_path):
    if backend() != "CBC":
        pytest.skip("standalone CBC replay requires the CBC backend")
    path = tmp_path / "WITNESS.json"
    path.write_bytes(canonical_witness_bytes(witness))
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "egglab.enumerate_tiny",
            "--replay",
            str(path),
            "--require-backend",
            "CBC",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout)["status"] == "pass"


def test_canonical_json_round_trip(witness):
    payload = canonical_witness_bytes(witness)
    assert canonical_witness_bytes(json.loads(payload)) == payload
