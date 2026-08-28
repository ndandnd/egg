"""Deterministic delta debugging for a strict undamped two-cycle.

The search space is intentionally closed and synthetic.  The reducer starts
from one checked-in fixture recipe, removes trips and affine-feedback features,
and stops at the four-trip target.  It never expands into a seed/grid search.

"Strict" is operational here:
* alpha is exactly one and the price state has prime period two;
* the alternating responses have different discrete structures;
* complete tiny enumeration gives a positive objective margin to every other
  discrete structure at each cycle price; and
* the selected structure has a unique aggregate load at the configured LP
  optimal-face tolerance.

Continuous charging polytopes have no positive objective gap to arbitrarily
nearby feasible points.  The witness says this explicitly instead of
mislabeling a discrete-structure margin as a margin over a continuum.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import replace

import numpy as np

from .enumerate_tiny import (
    PWL_TOL,
    canonical_number,
    canonical_solution_record,
    cycle_summary_from_trajectory,
    enumerate_price_responses,
    enumerated_ch,
    enumerated_dictator_details,
    fixed_point_absence_summary,
    response_inventory_invariants,
    strict_best_response_summary,
    structure_id,
    structure_optimal_face,
)
from .evsp import REPLAY_TOL_KWH, validate_solution
from .instance import Instance, Trip, synthetic_instance
from .market import AffineMarket, make_affine_market
from .regimes import solve_taker

WITNESS_SCHEMA = "egglab.strict-undamped-two-cycle.v2"
TARGET_MAX_TRIPS = 4
DEFAULT_MAX_ORACLE_EVALUATIONS = 128
DEFAULT_MAX_WALL_SECONDS = 24 * 60 * 60
PRICE_STATE_TOL = 1e-7
LOAD_MATCH_TOL_KWH = REPLAY_TOL_KWH
OPTIMAL_FACE_OBJECTIVE_TOL = 1e-6
OPTIMAL_FACE_LOAD_TOL_KWH = REPLAY_TOL_KWH
STRICT_MARGIN_REQUIRED = 2e-2

OBJECTIVE_TOLERANCES = {
    "compact_mip_absolute": 1e-6,
    "enumerated_pwl_absolute": PWL_TOL,
    "fixed_sequence_margin_absolute": 1e-3,
    "adaptive_dictator_absolute": 1e-2,
}


class CycleMinimizerError(RuntimeError):
    pass


class _Budget:
    def __init__(self, max_evaluations: int, max_wall_seconds: float):
        self.max_evaluations = int(max_evaluations)
        self.deadline = time.monotonic() + float(max_wall_seconds)
        self.evaluations = 0

    def take(self):
        if self.evaluations >= self.max_evaluations:
            raise CycleMinimizerError(
                "strict-cycle oracle budget exhausted; bounded search killed")
        if time.monotonic() > self.deadline:
            raise CycleMinimizerError(
                "one-agent-day wall budget exhausted; bounded search killed")
        self.evaluations += 1


def synthetic_cycling_fixture() -> tuple[Instance, AffineMarket, dict]:
    """Closed synthetic fixture recipe; no result artifact is an input."""
    core = synthetic_instance(seed=5, n_trips=4, max_vehicles=2)
    # This forced singleton is a genuine removable trip: it overlaps the whole
    # core service span and therefore adds the same constant vehicle cost to
    # both cycle endpoints.
    padding = Trip(
        id="padding",
        start_min=600,
        end_min=1320,
        start_loc="A",
        end_loc="A",
        energy_kwh=14.0,
    )
    inst = replace(
        core,
        name="synthetic-cycle-s5-n4-plus-padding",
        trips=sorted(
            [padding, *core.trips],
            key=lambda trip: (trip.start_min, trip.id),
        ),
        max_vehicles=3,
        vehicle_fixed_cost=100.0,
        dh_cost_per_min=1.0,
        meta={
            "fixture": "strict-two-cycle-source-v1",
            "generator": "synthetic_instance",
            "seed": 5,
            "generated_core_trips": 4,
            "padding_trips": 1,
        },
    )
    raw_market = make_affine_market(
        inst, shape="duck", b_scale=0.05,
        name="strict-two-cycle-source-market")
    # Exact reparameterization: c + bL where c=a+bU.  Keeping U=0 makes later
    # removal of b[t] remove feedback without accidentally changing c[t].
    zero_load_prices = raw_market.price(np.zeros(raw_market.n_slots))
    market = AffineMarket(
        zero_load_prices,
        raw_market.b.copy(),
        np.zeros(raw_market.n_slots),
        name="strict-two-cycle-normalized-market",
    )
    recipe = {
        "kind": "closed-synthetic-fixture",
        "generator": {
            "function": "egglab.instance.synthetic_instance",
            "seed": 5,
            "n_trips": 4,
            "max_vehicles": 2,
        },
        "deterministic_augmentation": {
            "padding_trip": {
                "id": padding.id,
                "start_min": padding.start_min,
                "end_min": padding.end_min,
                "start_loc": padding.start_loc,
                "end_loc": padding.end_loc,
                "energy_kwh": padding.energy_kwh,
            },
            "max_vehicles": 3,
            "vehicle_fixed_cost": 100.0,
            "dh_cost_per_min": 1.0,
        },
        "market": {
            "shape": "duck",
            "b_scale": 0.05,
            "normalization": "a <- a + b*U; U <- 0 (exact price-map identity)",
        },
    }
    return inst, market, recipe


def _market_with_feedback_slots(
    market: AffineMarket, slots: list[int], name: str
) -> AffineMarket:
    slopes = np.zeros(market.n_slots)
    for slot in slots:
        slopes[int(slot)] = float(market.b[int(slot)])
    return AffineMarket(
        market.a.copy(), slopes, np.zeros(market.n_slots), name=name)


def _canonical_market(market: AffineMarket) -> dict:
    return {
        "name": market.name,
        "formula": "price[t] = a[t] + b[t] * (base_load[t] + load[t])",
        "a": [canonical_number(value) for value in market.a],
        "b": [canonical_number(value) for value in market.b],
        "base_load": [canonical_number(value) for value in market.U],
        "zero_load_prices": [
            canonical_number(value)
            for value in market.price(np.zeros(market.n_slots))
        ],
    }


def _price_distance(left, right) -> float:
    return float(np.max(np.abs(
        np.asarray(left, dtype=float) - np.asarray(right, dtype=float))))


def _load_distance(left, right) -> float:
    return float(np.max(np.abs(
        np.asarray(left, dtype=float) - np.asarray(right, dtype=float))))


def _linear_objective(solution: dict, prices) -> float:
    return float(solution["ops_cost"]) + float(np.dot(
        np.asarray(prices, dtype=float),
        np.asarray(solution["load"], dtype=float),
    ))


def trace_undamped(
    inst: Instance,
    market: AffineMarket,
    max_iters: int = 8,
    price_tolerance: float = PRICE_STATE_TOL,
) -> dict:
    """In-memory counterpart of loops.taker_fixed_point for canonical output."""
    prices = market.price(np.zeros(market.n_slots))
    history = []
    iterations = []
    outcome = None
    for iteration in range(max_iters):
        sol = solve_taker(inst, prices, max_mip_gap=1e-9)
        if sol.stats.status != "OPTIMAL":
            raise CycleMinimizerError(
                f"taker solve status {sol.stats.status} != OPTIMAL")
        violations = validate_solution(inst, sol)
        if violations:
            raise CycleMinimizerError(
                "taker solution failed physical replay: "
                + "; ".join(violations))
        response = canonical_solution_record(sol)
        load = np.asarray(response["load"], dtype=float)
        induced = market.price(load)
        objective = _linear_objective(response, prices)
        bound = sol.stats.bound
        iterations.append({
            "iteration": iteration,
            "posted_prices": [
                canonical_number(value) for value in prices],
            "response": response,
            "objective": canonical_number(objective),
            "certified_bound": (
                canonical_number(bound) if bound is not None else None),
            "solver_optimality_gap_abs": (
                canonical_number(max(0.0, objective - float(bound)))
                if bound is not None and math.isfinite(float(bound))
                else None),
            "induced_prices": [
                canonical_number(value) for value in induced],
            "price_residual_inf": canonical_number(
                _price_distance(induced, prices)),
        })
        if _price_distance(induced, prices) <= price_tolerance:
            outcome = {
                "type": "fixed_point",
                "iteration": iteration,
            }
        else:
            for first_seen in range(max(0, len(history) - 1)):
                if _price_distance(prices, history[first_seen]) <= price_tolerance:
                    outcome = {
                        "type": "cycle",
                        "first_seen": first_seen,
                        "length": iteration - first_seen,
                        "iteration": iteration,
                    }
                    break
        if outcome is not None:
            break
        history.append(np.asarray(prices, dtype=float))
        prices = induced
    if outcome is None:
        outcome = {"type": "max_iters", "iteration": max_iters}
    return {
        "alpha": 1.0,
        "price_tolerance": price_tolerance,
        "initialization": "market.price(zero_load)",
        "iterations": iterations,
        "outcome": outcome,
    }


def certify_strict_two_cycle(
    inst: Instance,
    market: AffineMarket,
) -> dict:
    """Full strict-cycle predicate used by every accepted delta step."""
    trace = trace_undamped(inst, market)
    outcome = trace["outcome"]
    if outcome.get("type") != "cycle" or outcome.get("length") != 2:
        return {
            "ok": False,
            "reason": (
                f"outcome_{outcome.get('type')}_"
                f"period_{outcome.get('length')}"),
            "trace": trace,
        }
    first = int(outcome["first_seen"])
    orbit = trace["iterations"][first:first + 2]
    if len(orbit) != 2:
        return {"ok": False, "reason": "incomplete_orbit", "trace": trace}
    ids = [row["response"]["structure_id"] for row in orbit]
    if ids[0] == ids[1]:
        return {
            "ok": False,
            "reason": "same_discrete_structure",
            "trace": trace,
        }
    if _load_distance(
            orbit[0]["response"]["load"],
            orbit[1]["response"]["load"]) <= LOAD_MATCH_TOL_KWH:
        return {
            "ok": False,
            "reason": "cycle_loads_not_distinct",
            "trace": trace,
        }

    enumerations = []
    faces = []
    margins = []
    for state_index, row in enumerate(orbit):
        enumeration = enumerate_price_responses(
            inst, row["posted_prices"])
        if enumeration["best_structure_id"] != row["response"]["structure_id"]:
            return {
                "ok": False,
                "reason": f"enumeration_mismatch_state_{state_index}",
                "trace": trace,
            }
        best_row = next(
            candidate for candidate in enumeration["responses"]
            if candidate["structure_id"] == enumeration["best_structure_id"])
        if _load_distance(
                best_row["solution"]["load"],
                row["response"]["load"]) > LOAD_MATCH_TOL_KWH:
            return {
                "ok": False,
                "reason": f"enumerated_load_mismatch_state_{state_index}",
                "trace": trace,
            }
        margin = enumeration["strict_structure_margin"]
        if margin is None or margin <= STRICT_MARGIN_REQUIRED:
            return {
                "ok": False,
                "reason": f"non_strict_structure_margin_state_{state_index}",
                "trace": trace,
            }
        face = structure_optimal_face(
            inst,
            best_row["structure"],
            row["posted_prices"],
            objective_tolerance=OPTIMAL_FACE_OBJECTIVE_TOL,
        )
        if (
            face["max_certified_load_range_upper_kwh"]
            > OPTIMAL_FACE_LOAD_TOL_KWH
        ):
            return {
                "ok": False,
                "reason": f"nonunique_optimal_load_state_{state_index}",
                "trace": trace,
            }
        enumerations.append(enumeration)
        faces.append(face)
        margins.append(float(margin))

    price_separation = _price_distance(
        orbit[0]["posted_prices"], orbit[1]["posted_prices"])
    if price_separation <= PRICE_STATE_TOL:
        return {
            "ok": False,
            "reason": "cycle_prices_not_distinct",
            "trace": trace,
        }
    return {
        "ok": True,
        "reason": "strict_two_cycle",
        "trace": trace,
        "orbit": orbit,
        "enumerations": enumerations,
        "optimal_faces": faces,
        "minimum_structure_margin": canonical_number(min(margins)),
        "price_state_separation_inf": canonical_number(price_separation),
        "load_state_separation_inf_kwh": canonical_number(_load_distance(
            orbit[0]["response"]["load"],
            orbit[1]["response"]["load"],
        )),
    }


def _trial_summary(certificate: dict) -> dict:
    summary = {
        "accepted": bool(certificate["ok"]),
        "reason": certificate["reason"],
        "outcome": certificate["trace"]["outcome"],
    }
    if certificate["ok"]:
        summary["minimum_structure_margin"] = (
            certificate["minimum_structure_margin"])
    return summary


def _ddmin(
    items: list,
    evaluate_keep,
    axis: str,
    trace: list,
) -> list:
    """Deterministic chunk deletion followed by a 1-minimality pass."""
    kept = list(items)
    granularity = 2
    while len(kept) >= 2:
        chunk_size = int(math.ceil(len(kept) / granularity))
        accepted = False
        for start in range(0, len(kept), chunk_size):
            removed = kept[start:start + chunk_size]
            candidate = kept[:start] + kept[start + chunk_size:]
            if not candidate:
                continue
            certificate = evaluate_keep(candidate)
            event = {
                "axis": axis,
                "removed": list(removed),
                "kept_count": len(candidate),
                **_trial_summary(certificate),
            }
            trace.append(event)
            if certificate["ok"]:
                kept = candidate
                granularity = max(2, granularity - 1)
                accepted = True
                break
        if accepted:
            continue
        if granularity >= len(kept):
            break
        granularity = min(len(kept), granularity * 2)

    changed = True
    while changed:
        changed = False
        for item in list(kept):
            candidate = [value for value in kept if value != item]
            if not candidate:
                continue
            certificate = evaluate_keep(candidate)
            trace.append({
                "axis": axis,
                "removed": [item],
                "kept_count": len(candidate),
                **_trial_summary(certificate),
            })
            if certificate["ok"]:
                kept = candidate
                changed = True
                break
    return kept


def minimize_fixture(
    max_oracle_evaluations: int = DEFAULT_MAX_ORACLE_EVALUATIONS,
    max_wall_seconds: float = DEFAULT_MAX_WALL_SECONDS,
) -> dict:
    """Reduce the closed fixture and return the final in-memory certificate."""
    source_inst, source_market, recipe = synthetic_cycling_fixture()
    budget = _Budget(max_oracle_evaluations, max_wall_seconds)
    reduction_trace = []

    def certify(inst, market):
        budget.take()
        return certify_strict_two_cycle(inst, market)

    source_certificate = certify(source_inst, source_market)
    if not source_certificate["ok"]:
        raise CycleMinimizerError(
            "closed source fixture no longer has a strict two-cycle")

    current_inst = source_inst
    current_market = source_market
    trip_ids = sorted(trip.id for trip in current_inst.trips)

    def evaluate_trip_keep(kept_ids):
        candidate = replace(
            current_inst,
            trips=[
                trip for trip in current_inst.trips
                if trip.id in set(kept_ids)
            ],
        )
        return certify(candidate, current_market)

    kept_trip_ids = _ddmin(
        trip_ids, evaluate_trip_keep, "trips", reduction_trace)
    current_inst = replace(
        current_inst,
        trips=[
            trip for trip in current_inst.trips
            if trip.id in set(kept_trip_ids)
        ],
    )

    while current_inst.max_vehicles > 1:
        candidate = replace(
            current_inst, max_vehicles=current_inst.max_vehicles - 1)
        certificate = certify(candidate, current_market)
        reduction_trace.append({
            "axis": "vehicle_capacity",
            "removed": [f"vehicle_{current_inst.max_vehicles}"],
            "kept_count": candidate.max_vehicles,
            **_trial_summary(certificate),
        })
        if not certificate["ok"]:
            break
        current_inst = candidate

    feedback_slots = [
        slot for slot, slope in enumerate(current_market.b)
        if abs(float(slope)) > 0.0
    ]

    def evaluate_feedback_keep(kept_slots):
        candidate_market = _market_with_feedback_slots(
            current_market,
            kept_slots,
            name="strict-two-cycle-reduced-market",
        )
        return certify(current_inst, candidate_market)

    kept_feedback_slots = _ddmin(
        feedback_slots,
        evaluate_feedback_keep,
        "affine_feedback_slots",
        reduction_trace,
    )
    current_market = _market_with_feedback_slots(
        current_market,
        kept_feedback_slots,
        name="strict-two-cycle-reduced-market",
    )
    current_inst = replace(
        current_inst,
        name="strict-two-cycle-s5-core",
        meta={
            "fixture": "strict-two-cycle-minimized-v1",
            "generator": "synthetic_instance",
            "seed": 5,
            "source_generated_trips": 4,
        },
    )

    final_certificate = certify(current_inst, current_market)
    if not final_certificate["ok"]:
        raise CycleMinimizerError("final reduced fixture lost the strict cycle")
    if len(current_inst.trips) > TARGET_MAX_TRIPS:
        raise CycleMinimizerError(
            f"bounded target missed: {len(current_inst.trips)} trips > "
            f"{TARGET_MAX_TRIPS}; refusing broad search")

    irreducibility_trials = []
    for trip_id in sorted(trip.id for trip in current_inst.trips):
        candidate = replace(
            current_inst,
            trips=[
                trip for trip in current_inst.trips
                if trip.id != trip_id
            ],
        )
        certificate = certify(candidate, current_market)
        irreducibility_trials.append({
            "axis": "trip",
            "removed": trip_id,
            **_trial_summary(certificate),
        })
    if current_inst.max_vehicles > 1:
        candidate = replace(
            current_inst, max_vehicles=current_inst.max_vehicles - 1)
        certificate = certify(candidate, current_market)
        irreducibility_trials.append({
            "axis": "vehicle_capacity",
            "removed": f"vehicle_{current_inst.max_vehicles}",
            **_trial_summary(certificate),
        })
    for slot in kept_feedback_slots:
        candidate_market = _market_with_feedback_slots(
            current_market,
            [value for value in kept_feedback_slots if value != slot],
            name="strict-two-cycle-irreducibility-trial",
        )
        certificate = certify(current_inst, candidate_market)
        irreducibility_trials.append({
            "axis": "affine_feedback_slot",
            "removed": slot,
            **_trial_summary(certificate),
        })
    if any(trial["accepted"] for trial in irreducibility_trials):
        raise CycleMinimizerError("final fixture is not 1-minimal")

    return {
        "source_instance": source_inst,
        "source_market": source_market,
        "source_recipe": recipe,
        "source_certificate": source_certificate,
        "instance": current_inst,
        "market": current_market,
        "certificate": final_certificate,
        "reduction_trace": reduction_trace,
        "kept_feedback_slots": kept_feedback_slots,
        "irreducibility_trials": irreducibility_trials,
        "oracle_evaluations": budget.evaluations,
        "budget": {
            "target_max_trips": TARGET_MAX_TRIPS,
            "max_oracle_evaluations": max_oracle_evaluations,
            "max_wall_seconds": max_wall_seconds,
            "on_target_miss": "stop; do not expand fixture/seed search",
        },
    }


def _canonical_instance(inst: Instance) -> dict:
    # Instance.canonical uses tuples for deadhead rows; normalize through JSON
    # so the in-memory witness and a reloaded witness are identical.
    return json.loads(json.dumps(inst.canonical(), sort_keys=True))


def build_witness(reduction: dict | None = None) -> dict:
    reduction = reduction or minimize_fixture()
    inst = reduction["instance"]
    market = reduction["market"]
    certificate = reduction["certificate"]
    orbit = certificate["orbit"]
    enumerations = certificate["enumerations"]

    dictator = enumerated_dictator_details(inst, market, pwl_tol=PWL_TOL)
    dictator_load = dictator["best_response"]["load"]
    dictator_prices = market.price(dictator_load)
    dictator_responses = enumerate_price_responses(inst, dictator_prices)
    candidate_linear_objective = _linear_objective(
        dictator["best_response"], dictator_prices)
    fixed_point_deviation = (
        candidate_linear_objective
        - float(dictator_responses["best_objective"])
    )
    objective_tolerance_ceiling = max(OBJECTIVE_TOLERANCES.values())
    cycle_summary = cycle_summary_from_trajectory(
        certificate["trace"]["iterations"])
    strict_summary = strict_best_response_summary(
        orbit,
        enumerations,
        certificate["optimal_faces"],
        objective_tolerance_ceiling,
    )
    fixed_point_summary = fixed_point_absence_summary(
        dictator,
        dictator_prices,
        candidate_linear_objective,
        dictator_responses,
        fixed_point_deviation,
        objective_tolerance_ceiling,
    )
    if not fixed_point_summary["passes_tolerance"]:
        raise CycleMinimizerError(
            "enumerated fixed-point-absence certificate did not clear tolerances")

    hull = enumerated_ch(inst, market, pwl_tol=PWL_TOL)
    uplift_lower = dictator["z_d_lower"] - float(hull["z_ch"])
    uplift_upper = dictator["z_d_upper"] - float(hull["z_ch_model"])

    final_ids = sorted(trip.id for trip in inst.trips)
    source_ids = sorted(
        trip.id for trip in reduction["source_instance"].trips)
    witness = {
        "schema": WITNESS_SCHEMA,
        "claims": {
            "computational_evidence": {
                "status": "pass",
                "model_scope": (
                    "the serialized affine-market EVSP with continuous "
                    "charging and exhaustively enumerated discrete structures"),
                "statements": [
                    "the recorded undamped deterministic oracle trajectory "
                    "has strict prime period two",
                    "all feasible discrete structures were independently "
                    "enumerated at both cycle prices",
                    "the unique enumerated dictator candidate is not a best "
                    "response at its induced price",
                    "the four-trip witness is 1-minimal-only on the tested "
                    "trip/capacity/feedback deletion axes, not globally "
                    "minimal",
                ],
            },
            "theorem_claims": [{
                "id": "T1-fixed-point-necessary-dictator",
                "status": "separate-algebraic-lemma",
                "statement": (
                    "For diagonal b >= 0, every self-confirming posted-price "
                    "best response minimizes ops + (a+b*U)*L + "
                    "0.5*b*L^2.  The "
                    "identity adds 0.5*(L'-L)^T b (L'-L) to each best-response "
                    "inequality."),
                "role": (
                    "Only this implication turns the enumerated unique-"
                    "dictator/deviation evidence into absence of any fixed "
                    "point in the serialized continuous-charging model."),
            }],
            "not_claimed": [
                "no universal convergence or cycling theorem",
                "no claim about non-synthetic or live operational data",
                "no positive objective gap over arbitrarily nearby points "
                "inside a continuous charging polytope",
            ],
        },
        "tolerances": {
            "price_state_inf": PRICE_STATE_TOL,
            "load_match_and_replay_kwh": LOAD_MATCH_TOL_KWH,
            "optimal_face_objective": OPTIMAL_FACE_OBJECTIVE_TOL,
            "optimal_face_load_kwh": OPTIMAL_FACE_LOAD_TOL_KWH,
            "objective": OBJECTIVE_TOLERANCES,
            "strict_margin_required": STRICT_MARGIN_REQUIRED,
            "objective_tolerance_ceiling": objective_tolerance_ceiling,
        },
        "minimization": {
            "algorithm": (
                "deterministic chunk delta-debugging plus 1-minimal pass"),
            "source_fixture": reduction["source_recipe"],
            "source_instance_hash": reduction["source_instance"].hash(),
            "source_trip_ids": source_ids,
            "final_trip_ids": final_ids,
            "removed_trip_ids": sorted(set(source_ids) - set(final_ids)),
            "kept_affine_feedback_slots": reduction["kept_feedback_slots"],
            "trace": reduction["reduction_trace"],
            "oracle_evaluations": reduction["oracle_evaluations"],
            "kill_policy": reduction["budget"],
        },
        "instance": _canonical_instance(inst),
        "market": _canonical_market(market),
        "computational_evidence": {
            "cycle": cycle_summary,
            "strict_best_response": strict_summary,
            "exhaustive_feasible_response_enumeration": {
                "scope": (
                    "all trip partitions and direct/depot arc-kind structures; "
                    "each feasible structure's continuous charging LP is "
                    "optimized and independently physically replayed"),
                "states": [
                    {
                        "state": index,
                        **response_inventory_invariants(enumeration),
                    }
                    for index, enumeration in enumerate(enumerations)
                ],
            },
            "fixed_point_absence": fixed_point_summary,
            "convex_hull_dictator_comparison": {
                "z_ch_lower_model": canonical_number(hull["z_ch_model"]),
                "z_ch_upper_exact_incumbent": canonical_number(hull["z_ch"]),
                "z_d_lower": dictator["z_d_lower"],
                "z_d_upper": dictator["z_d_upper"],
                "uplift_interval": [
                    canonical_number(uplift_lower),
                    canonical_number(uplift_upper),
                ],
                "n_structures": hull["n_structures"],
                "pwl_tolerance": PWL_TOL,
            },
            "irreducibility": {
                "definition": (
                    "1-minimal-only on the tested deletion axes: removing any "
                    "remaining trip, the second vehicle-capacity unit, or any "
                    "remaining nonzero affine-feedback slot; no global or "
                    "seed-grid minimality claim"),
                "target_max_trips": TARGET_MAX_TRIPS,
                "n_trips": len(inst.trips),
                "trials": reduction["irreducibility_trials"],
                "irreducible": True,
            },
        },
    }

    # Imported lazily so enumerate_tiny remains independently executable and
    # does not depend on this module for its replay logic.
    from .enumerate_tiny import replay_cycle_witness
    witness["independent_replay"] = replay_cycle_witness(
        witness, verify_integrity=False)
    witness["integrity"] = {
        "canonical_payload_sha256": witness_payload_sha256(witness),
        "canonical_json": "UTF-8, sorted keys, indent=2, trailing newline",
    }
    return witness


def _payload_without_integrity(witness: dict) -> dict:
    return {key: value for key, value in witness.items() if key != "integrity"}


def witness_payload_sha256(witness: dict) -> str:
    payload = json.dumps(
        _payload_without_integrity(witness),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def canonical_witness_bytes(witness: dict) -> bytes:
    return (
        json.dumps(
            witness, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
