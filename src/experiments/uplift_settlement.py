"""Outcome-blind certified uplift-settlement arithmetic.

This module consumes one purpose-built endpoint certificate and nothing else.
It does not know how to read an experiment population, checkpoint, CSV, run
tree, or solver record.  Connecting certified experiment evidence to this
schema is deliberately left to a later reviewed adapter.

Accounting is at one fleet/participant block at a time.  Vehicle schedules are
evidence for that fleet's feasible action; this module never allocates a
payment among vehicles and makes no individual-rationality claim for a driver,
vehicle, or other sub-fleet actor.

Sign convention
---------------
``q`` is signed net withdrawal (demand is positive, supply is negative), so
``p*q`` is a charge to a participant.  For participant ``i``:

    assigned_value_i = c_i + p*q_i
    LOC_i = assigned_value_i - min_x(c_i(x) + p*q_i(x))

The two-part tariff charges ``p*q_i`` and pays ``LOC_i`` to the participant.
All claim-bearing arithmetic uses :class:`decimal.Decimal` with directed
outward rounding; binary floats are rejected by the programmatic API.

Normative specification: ``doc/SETTLEMENT_SPEC.md``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from decimal import (
    Decimal,
    DecimalException,
    InvalidOperation,
    ROUND_CEILING,
    ROUND_FLOOR,
    localcontext,
)
from pathlib import Path
from typing import Callable


INPUT_SCHEMA = "uplift-settlement-endpoints-v2"
OUTPUT_SCHEMA = "uplift-settlement-arithmetic-v2"
BEST_RESPONSE_EVIDENCE_SCHEMA = "uplift-best-response-evidence-v1"
GLOBAL_EXACT_ORACLE_TIER = "global-exact-oracle-certified-bound-v1"
PRIVATE_OBJECTIVE_CONVENTION = (
    "minimize-intrinsic-cost-plus-price-dot-net-withdrawal")
BEST_RESPONSE_VALIDATION_TOLERANCE = Decimal("1e-6")
DECIMAL_PRECISION = 80
PRICE_REPRESENTATION = "outer-coordinate-projections"
IDENTITY_PREMISES = (
    "complete_separable_block_coverage",
    "assignment_jointly_feasible",
    "assignment_balanced",
    "assignment_integer_optimal",
    "common_price_dual_optimal",
    "convex_hull_strong_duality",
    "best_responses_at_common_price",
)
REPO_ROOT = Path(__file__).resolve().parents[2]


class SettlementError(RuntimeError):
    """The settlement cannot be reported without weakening its certificate."""


def _canonical_zero(value: Decimal) -> Decimal:
    return Decimal(0) if value.is_zero() else value


def _decimal(value: object, label: str) -> Decimal:
    """Parse one exact decimal endpoint.

    Endpoint strings are required by the public schema.  ``Decimal`` and
    integer values are admitted only for direct unit-test/library use.  A
    Python float is never accepted because its decimal spelling would hide a
    prior binary rounding step.
    """
    if isinstance(value, bool) or isinstance(value, float):
        raise SettlementError(
            f"{label} must be an exact decimal string, not "
            f"{type(value).__name__}")
    if not isinstance(value, (str, int, Decimal)):
        raise SettlementError(
            f"{label} must be an exact decimal string")
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise SettlementError(
            f"{label} is not a valid decimal endpoint") from exc
    if not result.is_finite():
        raise SettlementError(f"{label} must be finite")
    return _canonical_zero(result)


def _directed(
    operation: Callable[[Decimal, Decimal], Decimal],
    left: Decimal,
    right: Decimal,
    rounding: str,
) -> Decimal:
    try:
        with localcontext() as context:
            context.prec = DECIMAL_PRECISION
            context.rounding = rounding
            value = operation(left, right)
    except DecimalException as exc:
        raise SettlementError(
            "decimal interval operation exceeded the supported context") from exc
    if not value.is_finite():
        raise SettlementError("decimal interval operation became non-finite")
    return _canonical_zero(value)


def _add_down(left: Decimal, right: Decimal) -> Decimal:
    return _directed(lambda x, y: x + y, left, right, ROUND_FLOOR)


def _add_up(left: Decimal, right: Decimal) -> Decimal:
    return _directed(lambda x, y: x + y, left, right, ROUND_CEILING)


def _sub_down(left: Decimal, right: Decimal) -> Decimal:
    return _directed(lambda x, y: x - y, left, right, ROUND_FLOOR)


def _sub_up(left: Decimal, right: Decimal) -> Decimal:
    return _directed(lambda x, y: x - y, left, right, ROUND_CEILING)


def _mul_down(left: Decimal, right: Decimal) -> Decimal:
    return _directed(lambda x, y: x * y, left, right, ROUND_FLOOR)


def _mul_up(left: Decimal, right: Decimal) -> Decimal:
    return _directed(lambda x, y: x * y, left, right, ROUND_CEILING)


def _decimal_text(value: Decimal) -> str:
    value = _canonical_zero(value)
    if value.is_zero():
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _canonical_json_bytes(value: object, label: str) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SettlementError(
            f"{label} is not canonical-JSON serializable") from exc


def canonical_json_sha256(value: object, label: str = "evidence") -> str:
    return hashlib.sha256(_canonical_json_bytes(value, label)).hexdigest()


def _hex_identifier(value: object, label: str, lengths=(12, 64)) -> str:
    text = _nonempty_text(value, label)
    if len(text) not in lengths or any(c not in "0123456789abcdef" for c in text):
        raise SettlementError(
            f"{label} must be lowercase hexadecimal with length "
            f"{list(lengths)}")
    return text


def canonical_price_vector(
    components: list[dict],
    label: str = "price_vector",
) -> list[dict[str, str]]:
    normalized = []
    for index, component in enumerate(components):
        item_label = f"{label}[{index}]"
        _strict_keys(component, {"component_id", "value"}, item_label)
        assert isinstance(component, dict)
        normalized.append({
            "component_id": _nonempty_text(
                component["component_id"], f"{item_label}.component_id"),
            "value": _decimal_text(
                _decimal(component["value"], f"{item_label}.value")),
        })
    return normalized


def price_vector_sha256(components: list[dict]) -> str:
    return canonical_json_sha256(
        canonical_price_vector(components), "price_vector")


def canonical_witness_payload(
    schedule: dict,
    load: list[object],
    intrinsic_cost: object,
) -> dict:
    return {
        "schedule": schedule,
        "load": [
            _decimal_text(_decimal(value, f"witness.load[{index}]"))
            for index, value in enumerate(load)
        ],
        "intrinsic_cost": _decimal_text(
            _decimal(intrinsic_cost, "witness.intrinsic_cost")),
    }


def witness_sha256(
    schedule: dict,
    load: list[object],
    intrinsic_cost: object,
) -> str:
    return canonical_json_sha256(
        canonical_witness_payload(schedule, load, intrinsic_cost),
        "best-response witness")


def load_sha256(load: list[object]) -> str:
    normalized = [
        _decimal_text(_decimal(value, f"load[{index}]"))
        for index, value in enumerate(load)
    ]
    return canonical_json_sha256(normalized, "best-response load")


@dataclass(frozen=True)
class Interval:
    """Closed finite decimal interval with outward-rounded operations."""

    lo: Decimal
    hi: Decimal

    def __post_init__(self) -> None:
        lo = _decimal(self.lo, "interval.lo")
        hi = _decimal(self.hi, "interval.hi")
        if lo > hi:
            raise SettlementError(
                f"reversed interval [{_decimal_text(lo)}, "
                f"{_decimal_text(hi)}]")
        object.__setattr__(self, "lo", lo)
        object.__setattr__(self, "hi", hi)

    @classmethod
    def from_json(cls, value: object, label: str) -> "Interval":
        _strict_keys(value, {"lo", "hi"}, label)
        assert isinstance(value, dict)
        return cls(
            _decimal(value["lo"], f"{label}.lo"),
            _decimal(value["hi"], f"{label}.hi"),
        )

    @classmethod
    def point(cls, value: object) -> "Interval":
        exact = _decimal(value, "point")
        return cls(exact, exact)

    def add(self, other: "Interval") -> "Interval":
        return Interval(
            _add_down(self.lo, other.lo),
            _add_up(self.hi, other.hi),
        )

    def subtract(self, other: "Interval") -> "Interval":
        return Interval(
            _sub_down(self.lo, other.hi),
            _sub_up(self.hi, other.lo),
        )

    def multiply(self, other: "Interval") -> "Interval":
        lower_products = (
            _mul_down(self.lo, other.lo),
            _mul_down(self.lo, other.hi),
            _mul_down(self.hi, other.lo),
            _mul_down(self.hi, other.hi),
        )
        upper_products = (
            _mul_up(self.lo, other.lo),
            _mul_up(self.lo, other.hi),
            _mul_up(self.hi, other.lo),
            _mul_up(self.hi, other.hi),
        )
        return Interval(min(lower_products), max(upper_products))

    def negate(self) -> "Interval":
        return Interval(-self.hi, -self.lo)

    def nonnegative_theorem_tightening(
        self,
        label: str,
        tolerance: Decimal = Decimal(0),
    ) -> "Interval":
        tolerance = _decimal(tolerance, f"{label}.tolerance")
        if tolerance < 0:
            raise SettlementError(f"{label}.tolerance must be nonnegative")
        if self.hi < -tolerance:
            raise SettlementError(
                f"{label} has negative upper endpoint "
                f"{_decimal_text(self.hi)}; this contradicts the certified "
                "nonnegativity theorem")
        return Interval(
            max(Decimal(0), self.lo),
            max(Decimal(0), self.hi),
        )

    def intersection(self, other: "Interval") -> "Interval | None":
        lo = max(self.lo, other.lo)
        hi = min(self.hi, other.hi)
        return None if lo > hi else Interval(lo, hi)

    def to_json(self) -> dict[str, str]:
        return {"lo": _decimal_text(self.lo), "hi": _decimal_text(self.hi)}


def interval_sum(values: list[Interval]) -> Interval:
    total = Interval.point(0)
    for value in values:
        total = total.add(value)
    return total


def interval_dot(left: list[Interval], right: list[Interval]) -> Interval:
    if len(left) != len(right):
        raise SettlementError(
            f"interval dot-product dimension mismatch: {len(left)} != "
            f"{len(right)}")
    return interval_sum([x.multiply(y) for x, y in zip(left, right)])


def _strict_keys(value: object, expected: set[str], label: str) -> None:
    if not isinstance(value, dict):
        raise SettlementError(f"{label} must be an object")
    actual = set(value)
    missing = expected - actual
    unknown = actual - expected
    if missing or unknown:
        pieces = []
        if missing:
            pieces.append(f"missing={sorted(missing)}")
        if unknown:
            pieces.append(f"unknown={sorted(unknown)}")
        raise SettlementError(
            f"{label} schema mismatch ({', '.join(pieces)})")


def _nonempty_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SettlementError(f"{label} must be a nonempty string")
    return value


def _parse_price_certificate(value: object) -> dict:
    _strict_keys(
        value,
        {"certificate_id", "status", "representation", "components"},
        "price_certificate",
    )
    assert isinstance(value, dict)
    certificate_id = _nonempty_text(
        value["certificate_id"], "price_certificate.certificate_id")
    if value["status"] != "certified":
        raise SettlementError(
            "price_certificate.status must be exactly 'certified'")
    if value["representation"] != PRICE_REPRESENTATION:
        raise SettlementError(
            "price_certificate.representation must be exactly "
            f"{PRICE_REPRESENTATION!r}; coordinate intervals are outer "
            "projections, not a Cartesian set of supporting prices")
    components_value = value["components"]
    if not isinstance(components_value, list) or not components_value:
        raise SettlementError(
            "price_certificate.components must be a nonempty list")
    components = []
    seen = set()
    for index, component in enumerate(components_value):
        label = f"price_certificate.components[{index}]"
        _strict_keys(component, {"component_id", "price"}, label)
        assert isinstance(component, dict)
        component_id = _nonempty_text(
            component["component_id"], f"{label}.component_id")
        if component_id in seen:
            raise SettlementError(
                f"duplicate price component_id {component_id!r}")
        seen.add(component_id)
        components.append({
            "component_id": component_id,
            "price": Interval.from_json(component["price"], f"{label}.price"),
        })
    return {
        "certificate_id": certificate_id,
        "components": components,
    }


def _parse_objective_certificate(value: object) -> dict:
    _strict_keys(
        value,
        {
            "certificate_id",
            "status",
            "integrated_integer_objective",
            "convex_hull_objective",
        },
        "objective_certificate",
    )
    assert isinstance(value, dict)
    if value["status"] != "certified":
        raise SettlementError(
            "objective_certificate.status must be exactly 'certified'")
    return {
        "certificate_id": _nonempty_text(
            value["certificate_id"],
            "objective_certificate.certificate_id",
        ),
        "integer": Interval.from_json(
            value["integrated_integer_objective"],
            "objective_certificate.integrated_integer_objective",
        ),
        "convex_hull": Interval.from_json(
            value["convex_hull_objective"],
            "objective_certificate.convex_hull_objective",
        ),
    }


def _parse_identity_certificate(value: object, coverage: str) -> dict | None:
    """Validate the additional premises needed for sum(LOC) == z_D - z_CH.

    Complete block coverage alone is deliberately insufficient: the assigned
    profile must also be a balanced integer optimum and every best response
    must be evaluated at one common dual-optimal price under strong duality.
    """
    if value is None:
        return None
    expected = {"certificate_id", "status", *IDENTITY_PREMISES}
    _strict_keys(value, expected, "uplift_loc_identity_certificate")
    assert isinstance(value, dict)
    if coverage != "complete":
        raise SettlementError(
            "an uplift/LOC identity certificate requires complete participant "
            "coverage")
    if value["status"] != "certified":
        raise SettlementError(
            "uplift_loc_identity_certificate.status must be exactly "
            "'certified'")
    certificate_id = _nonempty_text(
        value["certificate_id"],
        "uplift_loc_identity_certificate.certificate_id",
    )
    for premise in IDENTITY_PREMISES:
        if value[premise] is not True:
            raise SettlementError(
                "uplift_loc_identity_certificate requires certified premise "
                f"{premise}=true")
    return {
        "certificate_id": certificate_id,
        "premises": {premise: True for premise in IDENTITY_PREMISES},
    }


def _parse_schedule_witness(value: object, label: str) -> dict:
    _strict_keys(value, {"sequences", "arc_kinds", "charges", "fleet"}, label)
    assert isinstance(value, dict)
    sequences = value["sequences"]
    arc_kinds = value["arc_kinds"]
    fleet = value["fleet"]
    if (not isinstance(sequences, list) or not sequences
            or not isinstance(arc_kinds, list)
            or len(arc_kinds) != len(sequences)):
        raise SettlementError(
            f"{label} sequences/arc_kinds must be nonempty aligned lists")
    if (not isinstance(fleet, int) or isinstance(fleet, bool)
            or fleet != len(sequences) or fleet <= 0):
        raise SettlementError(
            f"{label}.fleet must equal the number of nonempty sequences")
    normalized_sequences = []
    normalized_kinds = []
    seen_trips = set()
    for vehicle, (sequence, kinds) in enumerate(zip(sequences, arc_kinds)):
        item_label = f"{label}.sequences[{vehicle}]"
        if not isinstance(sequence, list) or not sequence:
            raise SettlementError(f"{item_label} must be nonempty")
        normalized_sequence = [
            _nonempty_text(trip_id, f"{item_label}[{index}]")
            for index, trip_id in enumerate(sequence)
        ]
        if any(trip_id in seen_trips for trip_id in normalized_sequence):
            raise SettlementError(
                f"{label} trip ids must occur exactly once")
        seen_trips.update(normalized_sequence)
        if (not isinstance(kinds, list)
                or len(kinds) != len(normalized_sequence) - 1
                or any(kind not in ("dir", "dep") for kind in kinds)):
            raise SettlementError(
                f"{label}.arc_kinds[{vehicle}] has invalid shape/kind")
        normalized_sequences.append(normalized_sequence)
        normalized_kinds.append(list(kinds))

    charges = value["charges"]
    if not isinstance(charges, list):
        raise SettlementError(f"{label}.charges must be a list")
    normalized_charges = []
    charge_keys = set()
    for index, charge in enumerate(charges):
        charge_label = f"{label}.charges[{index}]"
        _strict_keys(
            charge,
            {"vehicle", "after_trip", "before_trip", "slot", "kwh"},
            charge_label,
        )
        assert isinstance(charge, dict)
        vehicle = charge["vehicle"]
        slot = charge["slot"]
        if (not isinstance(vehicle, int) or isinstance(vehicle, bool)
                or not 0 <= vehicle < fleet):
            raise SettlementError(f"{charge_label}.vehicle is invalid")
        if (not isinstance(slot, int) or isinstance(slot, bool) or slot < 0):
            raise SettlementError(f"{charge_label}.slot is invalid")
        after_trip = _nonempty_text(
            charge["after_trip"], f"{charge_label}.after_trip")
        before_trip = _nonempty_text(
            charge["before_trip"], f"{charge_label}.before_trip")
        sequence = normalized_sequences[vehicle]
        matches = [
            i for i in range(len(sequence) - 1)
            if sequence[i] == after_trip and sequence[i + 1] == before_trip
        ]
        if len(matches) != 1 \
                or normalized_kinds[vehicle][matches[0]] != "dep":
            raise SettlementError(
                f"{charge_label} is not tied to a consecutive depot arc")
        kwh = _decimal(charge["kwh"], f"{charge_label}.kwh")
        if kwh < 0:
            raise SettlementError(f"{charge_label}.kwh must be nonnegative")
        key = (vehicle, after_trip, before_trip, slot)
        if key in charge_keys:
            raise SettlementError(f"{charge_label} duplicates a charge slot")
        charge_keys.add(key)
        normalized_charges.append({
            "vehicle": vehicle,
            "after_trip": after_trip,
            "before_trip": before_trip,
            "slot": slot,
            "kwh": _decimal_text(kwh),
        })
    return {
        "sequences": normalized_sequences,
        "arc_kinds": normalized_kinds,
        "charges": normalized_charges,
        "fleet": fleet,
    }


def _parse_best_response_evidence(
    value: object,
    label: str,
    price_certificate_id: str,
    price_components: list[dict],
) -> dict:
    _strict_keys(
        value,
        {
            "schema",
            "certificate_id",
            "status",
            "evidence_tier",
            "instance_hash",
            "price_certificate_id",
            "price_vector",
            "price_vector_sha256",
            "objective_convention",
            "witness",
            "solver",
            "incumbent",
            "certified_dual_bound",
        },
        label,
    )
    assert isinstance(value, dict)
    if value["schema"] != BEST_RESPONSE_EVIDENCE_SCHEMA:
        raise SettlementError(
            f"{label}.schema must be {BEST_RESPONSE_EVIDENCE_SCHEMA!r}")
    if value["status"] != "certified":
        raise SettlementError(f"{label}.status must be exactly 'certified'")
    if value["evidence_tier"] != GLOBAL_EXACT_ORACLE_TIER:
        raise SettlementError(
            f"{label}.evidence_tier must be exactly "
            f"{GLOBAL_EXACT_ORACLE_TIER!r}; restricted-pool and heuristic "
            "evidence cannot certify a global best response")
    if value["price_certificate_id"] != price_certificate_id:
        raise SettlementError(
            f"{label}.price_certificate_id does not match the top-level "
            "price certificate")
    if value["objective_convention"] != PRIVATE_OBJECTIVE_CONVENTION:
        raise SettlementError(
            f"{label}.objective_convention must be exactly "
            f"{PRIVATE_OBJECTIVE_CONVENTION!r}")

    price_vector = canonical_price_vector(
        value["price_vector"], f"{label}.price_vector")
    component_ids = [item["component_id"] for item in price_components]
    if [item["component_id"] for item in price_vector] != component_ids:
        raise SettlementError(
            f"{label}.price_vector component order/identity does not match "
            "the top-level price certificate")
    price_hash = _hex_identifier(
        value["price_vector_sha256"],
        f"{label}.price_vector_sha256",
        lengths=(64,),
    )
    if price_hash != price_vector_sha256(price_vector):
        raise SettlementError(f"{label}.price_vector_sha256 does not recompute")
    prices = [
        _decimal(item["value"], f"{label}.price_vector[{index}].value")
        for index, item in enumerate(price_vector)
    ]
    for index, (price, component) in enumerate(zip(prices, price_components)):
        projection = component["price"]
        if not projection.lo <= price <= projection.hi:
            raise SettlementError(
                f"{label}.price_vector[{index}] lies outside the certified "
                "coordinate projection")

    witness_value = value["witness"]
    _strict_keys(
        witness_value,
        {
            "schedule",
            "load",
            "intrinsic_cost",
            "witness_sha256",
            "load_sha256",
            "certified_feasible",
            "replay_result",
        },
        f"{label}.witness",
    )
    assert isinstance(witness_value, dict)
    if witness_value["certified_feasible"] is not True:
        raise SettlementError(
            f"{label}.witness.certified_feasible must be true")
    schedule = _parse_schedule_witness(
        witness_value["schedule"], f"{label}.witness.schedule")
    load_value = witness_value["load"]
    if not isinstance(load_value, list) or len(load_value) != len(prices):
        raise SettlementError(
            f"{label}.witness.load must have {len(prices)} components")
    load = [
        _decimal(item, f"{label}.witness.load[{index}]")
        for index, item in enumerate(load_value)
    ]
    intrinsic = _decimal(
        witness_value["intrinsic_cost"],
        f"{label}.witness.intrinsic_cost")
    claimed_witness_hash = _hex_identifier(
        witness_value["witness_sha256"],
        f"{label}.witness.witness_sha256",
        lengths=(64,),
    )
    if claimed_witness_hash != witness_sha256(
            schedule, load, intrinsic):
        raise SettlementError(
            f"{label}.witness.witness_sha256 does not recompute")
    claimed_load_hash = _hex_identifier(
        witness_value["load_sha256"],
        f"{label}.witness.load_sha256",
        lengths=(64,),
    )
    if claimed_load_hash != load_sha256(load):
        raise SettlementError(
            f"{label}.witness.load_sha256 does not recompute")
    replay = witness_value["replay_result"]
    _strict_keys(
        replay, {"status", "policy", "violations"},
        f"{label}.witness.replay_result")
    assert isinstance(replay, dict)
    if replay["status"] != "passed" or replay["violations"] != []:
        raise SettlementError(
            f"{label}.witness replay must be passed with no violations")
    replay_policy = _nonempty_text(
        replay["policy"], f"{label}.witness.replay_result.policy")

    solver = value["solver"]
    _strict_keys(
        solver,
        {"backend", "solver_version", "status", "max_mip_gap"},
        f"{label}.solver",
    )
    assert isinstance(solver, dict)
    if solver["status"] != "OPTIMAL":
        raise SettlementError(f"{label}.solver.status must be 'OPTIMAL'")
    max_mip_gap = _decimal(
        solver["max_mip_gap"], f"{label}.solver.max_mip_gap")
    if max_mip_gap < 0:
        raise SettlementError(
            f"{label}.solver.max_mip_gap must be nonnegative")
    normalized_solver = {
        "backend": _nonempty_text(
            solver["backend"], f"{label}.solver.backend"),
        "solver_version": _nonempty_text(
            solver["solver_version"], f"{label}.solver.solver_version"),
        "status": "OPTIMAL",
        "max_mip_gap": _decimal_text(max_mip_gap),
    }

    incumbent = _decimal(value["incumbent"], f"{label}.incumbent")
    dual_bound = _decimal(
        value["certified_dual_bound"],
        f"{label}.certified_dual_bound")
    if dual_bound > incumbent:
        raise SettlementError(
            f"{label}.certified_dual_bound exceeds incumbent")
    witness_value_interval = Interval.point(intrinsic).add(interval_dot(
        [Interval.point(price) for price in prices],
        [Interval.point(quantity) for quantity in load],
    ))
    tolerance = BEST_RESPONSE_VALIDATION_TOLERANCE
    if (incumbent < witness_value_interval.lo - tolerance
            or incumbent > witness_value_interval.hi + tolerance):
        raise SettlementError(
            f"{label}.incumbent disagrees with the primitive witness objective")

    normalized_witness = {
        "schedule": schedule,
        "load": [_decimal_text(item) for item in load],
        "intrinsic_cost": _decimal_text(intrinsic),
        "witness_sha256": claimed_witness_hash,
        "load_sha256": claimed_load_hash,
        "certified_feasible": True,
        "replay_result": {
            "status": "passed",
            "policy": replay_policy,
            "violations": [],
        },
    }
    return {
        "schema": BEST_RESPONSE_EVIDENCE_SCHEMA,
        "certificate_id": _nonempty_text(
            value["certificate_id"], f"{label}.certificate_id"),
        "status": "certified",
        "evidence_tier": GLOBAL_EXACT_ORACLE_TIER,
        "instance_hash": _hex_identifier(
            value["instance_hash"], f"{label}.instance_hash"),
        "price_certificate_id": price_certificate_id,
        "price_vector": price_vector,
        "price_vector_sha256": price_hash,
        "prices": prices,
        "objective_convention": PRIVATE_OBJECTIVE_CONVENTION,
        "witness": normalized_witness,
        "solver": normalized_solver,
        "incumbent": incumbent,
        "certified_dual_bound": dual_bound,
        "objective": Interval(dual_bound, incumbent),
        "witness_private_cost": witness_value_interval,
    }


def _parse_participant(
    value: object,
    index: int,
    price_certificate_id: str,
    price_components: list[dict],
) -> dict:
    label = f"participants[{index}]"
    _strict_keys(
        value,
        {
            "participant_id",
            "assigned_action_id",
            "price_certificate_id",
            "assigned_action_certified_feasible",
            "assigned_intrinsic_cost",
            "assigned_net_withdrawal",
            "best_response_evidence",
        },
        label,
    )
    assert isinstance(value, dict)
    participant_id = _nonempty_text(
        value["participant_id"], f"{label}.participant_id")
    assigned_action_id = _nonempty_text(
        value["assigned_action_id"], f"{label}.assigned_action_id")
    if value["price_certificate_id"] != price_certificate_id:
        raise SettlementError(
            f"{label}.price_certificate_id does not match the top-level "
            "price certificate")
    if value["assigned_action_certified_feasible"] is not True:
        raise SettlementError(
            f"{label}.assigned_action_certified_feasible must be true")
    component_ids = [item["component_id"] for item in price_components]
    withdrawals_value = value["assigned_net_withdrawal"]
    if not isinstance(withdrawals_value, list):
        raise SettlementError(
            f"{label}.assigned_net_withdrawal must be a list")
    if len(withdrawals_value) != len(component_ids):
        raise SettlementError(
            f"{label}.assigned_net_withdrawal has {len(withdrawals_value)} "
            f"components; expected {len(component_ids)}")
    withdrawals = []
    observed_ids = []
    for slot, withdrawal in enumerate(withdrawals_value):
        item_label = f"{label}.assigned_net_withdrawal[{slot}]"
        _strict_keys(
            withdrawal, {"component_id", "quantity"}, item_label)
        assert isinstance(withdrawal, dict)
        component_id = _nonempty_text(
            withdrawal["component_id"], f"{item_label}.component_id")
        observed_ids.append(component_id)
        withdrawals.append(Interval.from_json(
            withdrawal["quantity"], f"{item_label}.quantity"))
    if observed_ids != component_ids:
        raise SettlementError(
            f"{label}.assigned_net_withdrawal component order/identity "
            f"{observed_ids!r} does not match price components "
            f"{component_ids!r}")
    best_response = _parse_best_response_evidence(
        value["best_response_evidence"],
        f"{label}.best_response_evidence",
        price_certificate_id,
        price_components,
    )
    return {
        "participant_id": participant_id,
        "assigned_action_id": assigned_action_id,
        "assigned_intrinsic_cost": Interval.from_json(
            value["assigned_intrinsic_cost"],
            f"{label}.assigned_intrinsic_cost",
        ),
        "assigned_net_withdrawal": withdrawals,
        "best_response": best_response,
    }


def _parse_document(document: object) -> dict:
    _strict_keys(
        document,
        {
            "schema",
            "case_id",
            "coverage",
            "units",
            "price_certificate",
            "objective_certificate",
            "uplift_loc_identity_certificate",
            "participants",
        },
        "endpoint certificate",
    )
    assert isinstance(document, dict)
    if document["schema"] != INPUT_SCHEMA:
        raise SettlementError(
            f"endpoint certificate schema must be {INPUT_SCHEMA!r}")
    case_id = _nonempty_text(document["case_id"], "case_id")
    coverage = document["coverage"]
    if coverage not in ("complete", "partial"):
        raise SettlementError(
            "coverage must be exactly 'complete' or 'partial'")
    _strict_keys(document["units"], {"currency", "quantity"}, "units")
    units = document["units"]
    assert isinstance(units, dict)
    parsed_units = {
        "currency": _nonempty_text(units["currency"], "units.currency"),
        "quantity": _nonempty_text(units["quantity"], "units.quantity"),
    }
    price = _parse_price_certificate(document["price_certificate"])
    component_ids = [item["component_id"] for item in price["components"]]
    objective = _parse_objective_certificate(
        document["objective_certificate"])
    identity = _parse_identity_certificate(
        document["uplift_loc_identity_certificate"], coverage)
    participant_values = document["participants"]
    if not isinstance(participant_values, list) or not participant_values:
        raise SettlementError("participants must be a nonempty list")
    participants = [
        _parse_participant(
            participant,
            index,
            price["certificate_id"],
            price["components"],
        )
        for index, participant in enumerate(participant_values)
    ]
    participant_ids = [item["participant_id"] for item in participants]
    if len(set(participant_ids)) != len(participant_ids):
        raise SettlementError("participant_id values must be unique")
    price_hashes = {
        item["best_response"]["price_vector_sha256"]
        for item in participants}
    if len(price_hashes) != 1:
        raise SettlementError(
            "all best-response records must use one identical full price "
            "vector")
    return {
        "case_id": case_id,
        "coverage": coverage,
        "units": parsed_units,
        "price": price,
        "objective": objective,
        "identity": identity,
        "participants": participants,
    }


def canonical_certificate_sha256(document: object) -> str:
    def encode_decimal(value: object) -> str:
        if isinstance(value, Decimal):
            return _decimal_text(value)
        raise TypeError(
            f"object of type {type(value).__name__} is not JSON serializable")

    try:
        payload = json.dumps(
            document,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            default=encode_decimal,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SettlementError(
            "endpoint certificate is not canonical-JSON serializable") from exc
    return hashlib.sha256(payload).hexdigest()


def _best_response_evidence_to_json(evidence: dict) -> dict:
    return {
        "schema": evidence["schema"],
        "certificate_id": evidence["certificate_id"],
        "status": evidence["status"],
        "evidence_tier": evidence["evidence_tier"],
        "instance_hash": evidence["instance_hash"],
        "price_certificate_id": evidence["price_certificate_id"],
        "price_vector": evidence["price_vector"],
        "price_vector_sha256": evidence["price_vector_sha256"],
        "objective_convention": evidence["objective_convention"],
        "witness": evidence["witness"],
        "solver": evidence["solver"],
        "incumbent": _decimal_text(evidence["incumbent"]),
        "certified_dual_bound":
            _decimal_text(evidence["certified_dual_bound"]),
        "certified_value_interval": evidence["objective"].to_json(),
        "validation_tolerance":
            _decimal_text(BEST_RESPONSE_VALIDATION_TOLERANCE),
    }


def _participant_settlement(
    participant: dict,
    prices: list[Interval],
    component_ids: list[str],
) -> tuple[dict, Interval, Interval, Interval, Interval]:
    intrinsic = participant["assigned_intrinsic_cost"]
    best_response_evidence = participant["best_response"]
    best_response = best_response_evidence["objective"]
    withdrawal = participant["assigned_net_withdrawal"]
    energy_charge = interval_dot(prices, withdrawal)
    assigned_value = intrinsic.add(energy_charge)
    raw_loc = assigned_value.subtract(best_response)
    loc = raw_loc.nonnegative_theorem_tightening(
        f"participant {participant['participant_id']!r} lost-opportunity cost",
        BEST_RESPONSE_VALIDATION_TOLERANCE)

    # A payment equal to the upper endpoint is conservative for every exact
    # value enclosed by the certificate.
    guaranteed_payment = Interval.point(loc.hi)
    guaranteed_net_charge = energy_charge.subtract(guaranteed_payment)
    guaranteed_all_in = assigned_value.subtract(guaranteed_payment)

    # At the exact minimum payment K=(c+E)-v, E-K = v-c.  Computing through
    # this identity preserves the known dependency and avoids the needless
    # widening caused by treating E and K as independent intervals.
    minimum_net_charge = best_response.subtract(intrinsic)

    evidence_prices = [
        Interval.point(value) for value in best_response_evidence["prices"]]
    target_at_evidence_price = intrinsic.add(
        interval_dot(evidence_prices, withdrawal))
    raw_regret = target_at_evidence_price.subtract(best_response)
    regret = raw_regret.nonnegative_theorem_tightening(
        f"participant {participant['participant_id']!r} "
        "price-conditioned regret",
        BEST_RESPONSE_VALIDATION_TOLERANCE)

    result = {
        "participant_id": participant["participant_id"],
        "assigned_action_id": participant["assigned_action_id"],
        "best_response_certificate_id":
            best_response_evidence["certificate_id"],
        "best_response_evidence":
            _best_response_evidence_to_json(best_response_evidence),
        "best_response_value": best_response.to_json(),
        "assigned_intrinsic_cost": intrinsic.to_json(),
        "assigned_net_withdrawal": [
            {
                "component_id": component_id,
                "quantity": quantity.to_json(),
            }
            for component_id, quantity in zip(component_ids, withdrawal)
        ],
        "volumetric_charge_to_participant": energy_charge.to_json(),
        "assigned_private_cost_before_commitment":
            assigned_value.to_json(),
        "lost_opportunity_cost_raw": raw_loc.to_json(),
        "lost_opportunity_cost": loc.to_json(),
        "target_private_cost_at_best_response_price":
            target_at_evidence_price.to_json(),
        "price_conditioned_regret_raw": raw_regret.to_json(),
        "price_conditioned_regret": regret.to_json(),
        "two_part_tariff": {
            "charge_sign_convention":
                "positive-is-charge-to-participant",
            "commitment_condition":
                "payment-contingent-on-assigned-action-performance",
            "volumetric_charge_to_participant": energy_charge.to_json(),
            "minimum_commitment_payment_to_participant": loc.to_json(),
            "fixed_charge_to_participant": loc.negate().to_json(),
            "net_charge_to_participant_at_minimum_payment":
                minimum_net_charge.to_json(),
            "assigned_all_in_cost_at_minimum_payment":
                best_response.to_json(),
            "guaranteed_commitment_payment_to_participant":
                guaranteed_payment.to_json(),
            "net_charge_to_participant_with_guaranteed_payment":
                guaranteed_net_charge.to_json(),
            "assigned_all_in_cost_with_guaranteed_payment":
                guaranteed_all_in.to_json(),
        },
    }
    return result, raw_loc, loc, raw_regret, regret


def settle(document: object) -> dict:
    """Compute a deterministic settlement from certified endpoint intervals."""
    certificate_sha = canonical_certificate_sha256(document)
    parsed = _parse_document(document)
    price_components = parsed["price"]["components"]
    component_ids = [item["component_id"] for item in price_components]
    prices = [item["price"] for item in price_components]

    participant_results = []
    raw_locs = []
    tightened_locs = []
    raw_regrets = []
    tightened_regrets = []
    for participant in parsed["participants"]:
        result, raw_loc, loc, raw_regret, regret = _participant_settlement(
            participant, prices, component_ids)
        participant_results.append(result)
        raw_locs.append(raw_loc)
        tightened_locs.append(loc)
        raw_regrets.append(raw_regret)
        tightened_regrets.append(regret)

    integer_objective = parsed["objective"]["integer"]
    convex_hull_objective = parsed["objective"]["convex_hull"]
    uplift_raw = integer_objective.subtract(convex_hull_objective)
    uplift = uplift_raw.nonnegative_theorem_tightening(
        "integrated integer-minus-convex-hull uplift")
    total_raw_loc = interval_sum(raw_locs)
    total_loc = interval_sum(tightened_locs)
    total_raw_regret = interval_sum(raw_regrets)
    total_regret = interval_sum(tightened_regrets)

    identity_asserted = parsed["identity"] is not None
    identity_intersection = None
    regret_identity_intersection = None
    identity_consistent = None
    if identity_asserted:
        identity_intersection = uplift.intersection(total_loc)
        if identity_intersection is None:
            raise SettlementError(
                "the certified uplift/LOC identity premises require total "
                "lost-opportunity cost to equal integrated uplift, but their "
                "certified intervals do not intersect")
        regret_identity_intersection = uplift.intersection(total_regret)
        if regret_identity_intersection is None:
            raise SettlementError(
                "the certified uplift/LOC identity premises require total "
                "price-conditioned regret to equal integrated uplift, but "
                "their certified intervals do not intersect")
        identity_consistent = True

    return {
        "schema": OUTPUT_SCHEMA,
        "case_id": parsed["case_id"],
        "endpoint_certificate_sha256": certificate_sha,
        "arithmetic": {
            "number_system": "decimal",
            "precision_digits": DECIMAL_PRECISION,
            "rounding": "directed-outward",
        },
        "units": parsed["units"],
        "coverage": parsed["coverage"],
        "convex_hull_price_certificate": {
            "certificate_id": parsed["price"]["certificate_id"],
            "status": "certified",
            "representation": PRICE_REPRESENTATION,
            "components": [
                {
                    "component_id": item["component_id"],
                    "price": item["price"].to_json(),
                }
                for item in price_components
            ],
        },
        "objective_certificate_id": parsed["objective"]["certificate_id"],
        "participants": participant_results,
        "system": {
            "integrated_integer_objective": integer_objective.to_json(),
            "convex_hull_objective": convex_hull_objective.to_json(),
            "uplift_raw": uplift_raw.to_json(),
            "uplift": uplift.to_json(),
        },
        "loc_aggregation": {
            "reported_participants": len(participant_results),
            "total_lost_opportunity_cost_raw": total_raw_loc.to_json(),
            "total_lost_opportunity_cost": total_loc.to_json(),
            "uplift_loc_identity_asserted": identity_asserted,
            "uplift_loc_identity_certificate_id": (
                None if parsed["identity"] is None
                else parsed["identity"]["certificate_id"]
            ),
            "uplift_loc_identity_premises": (
                None if parsed["identity"] is None
                else parsed["identity"]["premises"]
            ),
            "uplift_loc_identity_consistent": identity_consistent,
            "uplift_loc_identity_intersection": (
                None if identity_intersection is None
                else identity_intersection.to_json()
            ),
        },
        "regret_aggregation": {
            "reported_fleets": len(participant_results),
            "total_price_conditioned_regret_raw":
                total_raw_regret.to_json(),
            "total_price_conditioned_regret": total_regret.to_json(),
            "equality_with_internal_uplift_claimed": identity_asserted,
            "uplift_identity_intersection": (
                None if regret_identity_intersection is None
                else regret_identity_intersection.to_json()
            ),
            "scope": "sum-over-reported-fleet-blocks",
        },
        "boundary": {
            "endpoint_arithmetic_only": True,
            "population_adapter_included": False,
            "incentive_compatibility_claimed": False,
            "budget_balance_claimed": False,
            "coordinate_price_intervals_are_outer_projections": True,
            "arbitrary_price_box_points_claimed_supporting": False,
            "single_fleet_accounting_only": True,
            "per_vehicle_payment_allocation_included": False,
            "individual_rationality_claimed": False,
        },
    }


def canonical_result_bytes(result: dict) -> bytes:
    return (
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _assert_outside_repository_results(
    path: str | os.PathLike,
    label: str,
) -> Path:
    lexical = Path(path).expanduser().absolute()
    candidate = lexical.resolve()
    result_root = (REPO_ROOT / "result").resolve()
    if (
        lexical == result_root
        or result_root in lexical.parents
        or candidate == result_root
        or result_root in candidate.parents
    ):
        raise SettlementError(
            f"{label} path under the repository result tree is refused by "
            f"the outcome-blind boundary: {lexical}")
    return candidate


def load_endpoint_certificate(path: str | os.PathLike) -> dict:
    """Read exactly one endpoint JSON, after enforcing the path boundary."""
    source = _assert_outside_repository_results(path, "input")
    if source.is_symlink() or not source.is_file():
        raise SettlementError(
            f"input endpoint certificate is not a regular file: {source}")
    def unique_object(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise SettlementError(
                    f"endpoint certificate contains duplicate key {key!r}")
            result[key] = value
        return result

    try:
        document = json.loads(
            source.read_bytes(), object_pairs_hook=unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SettlementError(
            f"cannot read endpoint certificate {source}: {exc}") from exc
    if not isinstance(document, dict):
        raise SettlementError("endpoint certificate root must be an object")
    return document


def write_result_no_replace(
    path: str | os.PathLike,
    result: dict,
) -> str:
    """Durably publish canonical JSON without replacing any destination."""
    destination = _assert_outside_repository_results(path, "output")
    parent = destination.parent
    if not parent.is_dir():
        raise SettlementError(
            f"output parent is not an existing directory: {parent}")
    if destination.exists() or destination.is_symlink():
        raise SettlementError(
            f"refusing existing output destination: {destination}")
    payload = canonical_result_bytes(result)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=str(parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, destination, follow_symlinks=False)
        except FileExistsError as exc:
            raise SettlementError(
                f"refusing existing output destination: {destination}") from exc
        directory_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return str(destination)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compute outcome-blind convex-hull-price, best-response regret, "
            "LOC, and two-part-tariff interval arithmetic from a certified "
            "endpoint JSON."
        ))
    parser.add_argument("--input", required=True)
    parser.add_argument(
        "--output",
        help="new JSON path (refuses replacement); omit to write stdout",
    )
    args = parser.parse_args()
    try:
        result = settle(load_endpoint_certificate(args.input))
        if args.output:
            print(write_result_no_replace(args.output, result))
        else:
            sys.stdout.buffer.write(canonical_result_bytes(result))
    except SettlementError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
