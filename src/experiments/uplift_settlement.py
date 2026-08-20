"""Outcome-blind certified uplift-settlement arithmetic.

This module consumes one purpose-built endpoint certificate and nothing else.
It does not know how to read an experiment population, checkpoint, CSV, run
tree, or solver record.  Connecting certified experiment evidence to this
schema is deliberately left to a later reviewed adapter.

Sign convention
---------------
``q`` is signed net withdrawal (demand is positive, supply is negative), so
``p*q`` is a charge to a participant.  For participant ``i``:

    assigned_value_i = c_i + p*q_i
    LOC_i = assigned_value_i - min_x(c_i(x) + p*q_i(x))

The two-part tariff charges ``p*q_i`` and pays ``LOC_i`` to the participant.
All claim-bearing arithmetic uses :class:`decimal.Decimal` with directed
outward rounding; binary floats are rejected by the programmatic API.

Normative specification:
``CURSOR_HANDOFF_UPLIFT_SETTLEMENT_20260820.md``.
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


INPUT_SCHEMA = "uplift-settlement-endpoints-v1"
OUTPUT_SCHEMA = "uplift-settlement-arithmetic-v1"
DECIMAL_PRECISION = 80
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

    def nonnegative_theorem_tightening(self, label: str) -> "Interval":
        if self.hi < 0:
            raise SettlementError(
                f"{label} has negative upper endpoint "
                f"{_decimal_text(self.hi)}; this contradicts the certified "
                "nonnegativity theorem")
        return Interval(max(Decimal(0), self.lo), self.hi)

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
        {"certificate_id", "status", "components"},
        "price_certificate",
    )
    assert isinstance(value, dict)
    certificate_id = _nonempty_text(
        value["certificate_id"], "price_certificate.certificate_id")
    if value["status"] != "certified":
        raise SettlementError(
            "price_certificate.status must be exactly 'certified'")
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


def _parse_participant(
    value: object,
    index: int,
    price_certificate_id: str,
    component_ids: list[str],
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
            "best_response_certificate_id",
            "best_response_status",
            "best_response_objective",
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
    if value["best_response_status"] != "certified":
        raise SettlementError(
            f"{label}.best_response_status must be exactly 'certified'")
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
    return {
        "participant_id": participant_id,
        "assigned_action_id": assigned_action_id,
        "assigned_intrinsic_cost": Interval.from_json(
            value["assigned_intrinsic_cost"],
            f"{label}.assigned_intrinsic_cost",
        ),
        "assigned_net_withdrawal": withdrawals,
        "best_response_certificate_id": _nonempty_text(
            value["best_response_certificate_id"],
            f"{label}.best_response_certificate_id",
        ),
        "best_response_objective": Interval.from_json(
            value["best_response_objective"],
            f"{label}.best_response_objective",
        ),
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
    participant_values = document["participants"]
    if not isinstance(participant_values, list) or not participant_values:
        raise SettlementError("participants must be a nonempty list")
    participants = [
        _parse_participant(
            participant,
            index,
            price["certificate_id"],
            component_ids,
        )
        for index, participant in enumerate(participant_values)
    ]
    participant_ids = [item["participant_id"] for item in participants]
    if len(set(participant_ids)) != len(participant_ids):
        raise SettlementError("participant_id values must be unique")
    return {
        "case_id": case_id,
        "coverage": coverage,
        "units": parsed_units,
        "price": price,
        "objective": objective,
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


def _participant_settlement(
    participant: dict,
    prices: list[Interval],
    component_ids: list[str],
) -> tuple[dict, Interval, Interval]:
    intrinsic = participant["assigned_intrinsic_cost"]
    best_response = participant["best_response_objective"]
    withdrawal = participant["assigned_net_withdrawal"]
    energy_charge = interval_dot(prices, withdrawal)
    assigned_value = intrinsic.add(energy_charge)
    raw_loc = assigned_value.subtract(best_response)
    loc = raw_loc.nonnegative_theorem_tightening(
        f"participant {participant['participant_id']!r} lost-opportunity cost")

    # A payment equal to the upper endpoint is conservative for every exact
    # value enclosed by the certificate.
    guaranteed_payment = Interval.point(loc.hi)
    guaranteed_net_charge = energy_charge.subtract(guaranteed_payment)
    guaranteed_all_in = assigned_value.subtract(guaranteed_payment)

    # At the exact minimum payment K=(c+E)-v, E-K = v-c.  Computing through
    # this identity preserves the known dependency and avoids the needless
    # widening caused by treating E and K as independent intervals.
    minimum_net_charge = best_response.subtract(intrinsic)

    result = {
        "participant_id": participant["participant_id"],
        "assigned_action_id": participant["assigned_action_id"],
        "best_response_certificate_id":
            participant["best_response_certificate_id"],
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
        "two_part_tariff": {
            "charge_sign_convention":
                "positive-is-charge-to-participant",
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
    return result, raw_loc, loc


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
    for participant in parsed["participants"]:
        result, raw_loc, loc = _participant_settlement(
            participant, prices, component_ids)
        participant_results.append(result)
        raw_locs.append(raw_loc)
        tightened_locs.append(loc)

    integer_objective = parsed["objective"]["integer"]
    convex_hull_objective = parsed["objective"]["convex_hull"]
    uplift_raw = integer_objective.subtract(convex_hull_objective)
    uplift = uplift_raw.nonnegative_theorem_tightening(
        "integrated integer-minus-convex-hull uplift")
    total_raw_loc = interval_sum(raw_locs)
    total_loc = interval_sum(tightened_locs)

    identity_required = parsed["coverage"] == "complete"
    identity_intersection = None
    identity_consistent = None
    if identity_required:
        identity_intersection = uplift.intersection(total_loc)
        if identity_intersection is None:
            raise SettlementError(
                "complete participant coverage requires total "
                "lost-opportunity cost to equal integrated uplift, but the "
                "certified intervals do not intersect")
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
            "uplift_loc_identity_required": identity_required,
            "uplift_loc_identity_consistent": identity_consistent,
            "uplift_loc_identity_intersection": (
                None if identity_intersection is None
                else identity_intersection.to_json()
            ),
        },
        "boundary": {
            "endpoint_arithmetic_only": True,
            "population_adapter_included": False,
            "incentive_compatibility_claimed": False,
            "partial_coverage_budget_balance_claimed": False,
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
            "Compute outcome-blind convex-hull-price, LOC, and two-part-"
            "tariff interval arithmetic from a certified endpoint JSON."
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
