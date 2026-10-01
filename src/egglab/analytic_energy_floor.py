"""Scope-checked ideal stored-input energy-floor baseline for reporting only.

This module is deliberately independent of the native solver, pricing oracle,
and experiment controller. Its output must not be inserted into a native
certificate, cache, solver status, or timed method result.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path


SCHEMA = "egg-native-recharge-v1"
PHYSICAL_IDENTITIES = (
    "1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7",
    "216693551f2e58ec8aab3cba68352656ec99bab8db13c671edd028542acfeb3d",
)
PINNED = {
    "flow_frozen": ("result/sistig_cardinality_flow/20260927-attempt1/frozen.json",
                    "bce2293080c3d19d05c37aa8c6bb4a285f1afe59fbde161fa6a6b6505784d103"),
    "flow_summary": ("result/sistig_cardinality_flow/20260927-attempt1/summary.json",
                     "1ad39db219db5377b72e7355babe2debd650e857cbccfd7dc074e47e8f6bd06f"),
    "flow_review": ("result/sistig_cardinality_flow/20260927-attempt1/review/REVIEW.md",
                    "60604b3467c17ec1c833ef56a2634a7e091d6cb677aaea4ec3c684dfdec15c94"),
    "one_bus_result": ("research-20260927/agent-notes/sistig-one-bus-postpilot/result.json",
                       "cdc2603b1e53dba7fdff757e63c2f64265b0d190aef1174f4792d607ecf2b3e9"),
    "one_bus_review": ("research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md",
                       "7b1d55d1d20fce676ded6aaeb6ae0965cd70fc464581290ad792f2056bce53a2"),
}


class UnsupportedBaseline(ValueError):
    """The reviewed ideal-model certificate does not cover this input."""


def _number(value, label, *, positive=False):
    if type(value) is int:
        if value.bit_length() > 1024:
            raise UnsupportedBaseline(f"{label} exceeds the supported stored-number size")
    elif type(value) is float:
        if not math.isfinite(value):
            raise UnsupportedBaseline(f"{label} must be a finite stored number")
    else:
        raise UnsupportedBaseline(f"{label} must be a finite stored number")
    result = Fraction(value)
    if result < 0 or (positive and result <= 0):
        raise UnsupportedBaseline(f"{label} is outside the nonnegative domain")
    return result


def _lower_decimal(value, digits=15):
    """Outward decimal display without float conversion or overflow."""
    scale = 10 ** digits
    units = (value.numerator * scale) // value.denominator
    sign = "-" if units < 0 else ""
    magnitude = abs(units)
    return f"{sign}{magnitude // scale}.{magnitude % scale:0{digits}d}"


def _identity(case):
    try:
        encoded = json.dumps({"schema": SCHEMA, "case": case}, sort_keys=True,
                             allow_nan=False).encode()
    except (TypeError, ValueError) as exc:
        raise UnsupportedBaseline("physical case is not a finite JSON payload") from exc
    return hashlib.sha256(encoded).hexdigest()


def _pinned_json(repo, label):
    relative, expected = PINNED[label]
    path = repo / relative
    if not path.is_file() or path.is_symlink():
        raise UnsupportedBaseline(f"missing reviewed {label} lineage")
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected:
        raise UnsupportedBaseline(f"stale or changed reviewed {label} lineage")
    if label.endswith("review"):
        return None
    try:
        return json.loads(payload)
    except (TypeError, ValueError) as exc:
        raise UnsupportedBaseline(f"unreadable reviewed {label} lineage") from exc


def _catalog(repo):
    frozen = _pinned_json(repo, "flow_frozen")
    summary = _pinned_json(repo, "flow_summary")
    _pinned_json(repo, "flow_review")
    one_bus = _pinned_json(repo, "one_bus_result")
    _pinned_json(repo, "one_bus_review")
    if (frozen.get("case_identities") != list(PHYSICAL_IDENTITIES)
            or len(frozen.get("cases", [])) != 2
            or summary.get("status") != "completed"
            or summary.get("native_optimizer_invoked") is not False
            or len(summary.get("lower_exact", [])) != 2):
        raise UnsupportedBaseline("reviewed flow certificate has an unsupported scope")
    by_id = {row.get("case_identity"): row for row in one_bus.get("cases", [])}
    if set(by_id) != set(PHYSICAL_IDENTITIES) or any(
            by_id[key].get("one_bus_infeasible_proved") is not True
            or by_id[key].get("no_recharge_on_every_forced_transition") is not True
            or by_id[key].get("minimum_used_buses_lower") != 2
            for key in PHYSICAL_IDENTITIES):
        raise UnsupportedBaseline("reviewed one-bus obstruction has an unsupported scope")
    for identity, case in zip(PHYSICAL_IDENTITIES, frozen["cases"]):
        if _identity(case) != identity:
            raise UnsupportedBaseline("reviewed physical case identity does not reproduce")
    return frozen, summary, by_id


def evaluate(case, case_identity, market, *, repo=None):
    """Return an ideal CH lower bound, or fail closed outside the reviewed scope.

    ``case`` is the complete stored physical payload, not a label or subset.
    ``market`` supplies finite ``a`` and ``b`` arrays for the same time grid.
    The result is an ideal stored-input mathematical bound, not a native-MIP
    lower bound. Price-only market changes require no native solve.
    """
    repo = Path(repo).resolve() if repo is not None else Path(__file__).resolve().parents[2]
    if not isinstance(case, dict) or not isinstance(case_identity, str):
        raise UnsupportedBaseline("complete physical case and identity required")
    calculated_identity = _identity(case)
    if calculated_identity != case_identity or case_identity not in PHYSICAL_IDENTITIES:
        raise UnsupportedBaseline("physical case identity mismatch or unsupported case")
    frozen, summary, one_bus = _catalog(repo)
    index = PHYSICAL_IDENTITIES.index(case_identity)
    if case != frozen["cases"][index]:
        raise UnsupportedBaseline("physical payload differs from reviewed flow case")
    proof = one_bus[case_identity]
    try:
        f = _number(case["vehicle_cost"], "used-bus cost", positive=True)
        battery = _number(case["battery_kwh"], "battery", positive=True)
        reserve = _number(case["reserve_kwh"], "reserve")
        eta = _number(case["efficiency"], "efficiency", positive=True)
        monetary_travel = _number(case["deadhead_cost_per_min"], "monetary travel cost")
        service = sum((_number(t["energy_kwh"], "service energy") for t in case["trips"]), Fraction(0))
        movement_nonnegative = all(_number(leg["energy_kwh"], "movement energy") >= 0
                                   for mode in case["movements"] for leg in mode["legs"])
        period_count = len(case["market_edges_min"]) - 1
    except (KeyError, TypeError) as exc:
        raise UnsupportedBaseline("incomplete physical contract") from exc
    if (f != 100 or battery != 400 or reserve != 0 or eta != 1
            or monetary_travel != 0 or not movement_nonnegative
            or case.get("recharge_deadline_min") != 1800
            or len(case["trips"]) != 37 or period_count != 30
            or service != Fraction(proof["mandatory_service_energy"]["exact_stored_number"])
            or service <= battery):
        raise UnsupportedBaseline("physical/full-terminal energy contract unsupported")
    # The full-terminal requirement is part of the pinned ideal physical
    # certificate, not inferred from NativeCase.identity alone.
    if not isinstance(market, dict) or set(market) != {"a", "b", "name"}:
        raise UnsupportedBaseline("market must have the declared a/b/name fields")
    if not isinstance(market["name"], str) or not market["name"]:
        raise UnsupportedBaseline("market name must be nonempty text")
    if (not isinstance(market["a"], list) or not isinstance(market["b"], list)
            or len(market["a"]) != period_count or len(market["b"]) != period_count):
        raise UnsupportedBaseline("market dimension differs from physical time grid")
    a = [_number(value, "market intercept") for value in market["a"]]
    b = [_number(value, "market curvature", positive=True) for value in market["b"]]
    if len(set(b)) != 1:
        raise UnsupportedBaseline("only common positive quadratic curvature is supported")
    curvature = b[0]
    flat_a = _number(frozen["price_input"], "reviewed flat price", positive=True)
    flow_lower = Fraction(summary["lower_exact"][index])
    emin = (flow_lower - 2 * f) / flat_a
    if emin <= 0 or service > emin:
        raise UnsupportedBaseline("reviewed two-bus energy floor is invalid")
    p = sum(a, Fraction(0)) / period_count + curvature * emin / period_count
    if p <= 0 or p < max(a):
        raise UnsupportedBaseline("uniform-price conjugate has no supported interior form")
    three_bus_margin = 3 * f + p * service - (2 * f + p * emin)
    if three_bus_margin <= 0:
        raise UnsupportedBaseline("three-plus-bus cardinalities are not covered")
    conjugate = sum(((p - intercept) ** 2 / (2 * curvature) for intercept in a), Fraction(0))
    lower = 2 * f + p * emin - conjugate
    return {
        "status": "supported",
        "scope": "ideal_stored_input_CH_lower_only",
        "physical_case_identity": case_identity,
        "depot": case["depot"],
        "market_name": market["name"],
        "energy_floor_exact": str(emin),
        "service_energy_exact": str(service),
        "uniform_test_price_exact": str(p),
        "three_plus_bus_margin_exact": str(three_bus_margin),
        "ch_lower_exact": str(lower),
        "ch_lower_decimal": _lower_decimal(lower),
        "lineage_sha256": {label: value[1] for label, value in PINNED.items()},
        "qualification": "reviewed full-terminal ideal model; never a native bound, cache, status or timing",
    }
