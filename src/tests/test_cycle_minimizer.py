"""Acceptance battery for the bounded strict-two-cycle delta debugger."""
import copy
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.b2a2 import B2A2Error
from egglab.cycle_minimizer import (
    TARGET_MAX_TRIPS,
    build_witness,
    canonical_witness_bytes,
    minimize_fixture,
    witness_payload_sha256,
)
from egglab.enumerate_tiny import replay_cycle_witness


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
        state["optimal_face_load_uniqueness"]["max_load_range_kwh"]
        <= witness["tolerances"]["optimal_face_load_kwh"]
        for state in strict["states"]
    )

    enumerated = evidence["exhaustive_feasible_response_enumeration"]
    assert len(enumerated["states"]) == 2
    for state in enumerated["states"]:
        assert state["n_structures"] == (
            state["n_feasible"] + state["n_infeasible"])
        assert len(state["responses"]) == state["n_structures"]


def test_fixed_point_and_hull_claims_are_separated(witness):
    claims = witness["claims"]
    assert claims["computational_evidence"]["status"] == "pass"
    assert claims["theorem_claims"][0]["id"] == (
        "T1-fixed-point-necessary-dictator")
    assert "no universal" in claims["not_claimed"][0]

    absence = witness["computational_evidence"]["fixed_point_absence"]
    ceiling = witness["tolerances"]["objective_tolerance_ceiling"]
    assert absence["conclusion"] == "no_fixed_point"
    assert absence["passes_tolerance"]
    assert absence["unique_dictator_structure_margin"] > ceiling
    assert absence["profitable_deviation_margin"] > ceiling

    comparison = witness[
        "computational_evidence"]["convex_hull_dictator_comparison"]
    lo, hi = comparison["uplift_interval"]
    assert 0.0 < lo <= hi
    assert comparison["z_ch_lower_model"] <= (
        comparison["z_ch_upper_exact_incumbent"])


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


def test_canonical_committed_witness_is_byte_identical(witness):
    path = (
        Path(__file__).resolve().parents[2]
        / "result" / "strict_two_cycle" / "WITNESS.json"
    )
    assert path.read_bytes() == canonical_witness_bytes(witness)


def test_canonical_json_round_trip(witness):
    payload = canonical_witness_bytes(witness)
    assert canonical_witness_bytes(json.loads(payload)) == payload
