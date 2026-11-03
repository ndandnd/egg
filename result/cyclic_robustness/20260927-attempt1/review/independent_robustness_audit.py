#!/usr/bin/env python3
"""Non-author, solver-free audit of the frozen cyclic robustness output.

Uses only the standard library. No author experiment module is read or imported.
Physical intervals are reconstructed in battery kWh. Continuous objectives are
minimized by exact three-point quadratic interpolation; the complete hull is
checked by enumerating every endpoint pair, not by the author's hull algorithm.
Only the requested report is written, with exclusive creation.
"""

import argparse
import copy
import hashlib
import itertools
import json
import math
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path
import subprocess


FROZEN_HEAD = "bd022ac32ef680446ee17bc4400843a764acb9f6"
RESULT_HASH = "3d5c20a39b2c7176b6ece22bbeb464a42ea7b3bc58498c0959e227469e25ed29"
SOURCE_HASHES = {
    "doc/CYCLIC_ROBUSTNESS_DESIGN_20260927.md": "a6d731761122ee07bc20448287efaea38345979b1fa57c0341a5047c959190cd",
    "doc/CYCLIC_ROBUSTNESS_PROTOCOL_20260927.md": "cf49a6d845a990a6644ea6a67b484d4ae31c8cd7ba26b69f2d93af534b6c9862",
    "src/experiments/cyclic_robustness.py": "d098d6d5afaf98a953a47ccad093b6ff90508453a40f38b7f05d4f699ec33922",
}


class AuditError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise AuditError(message)


def q(value):
    return Q(value["exact"])


def eq(recorded, expected, label):
    require(q(recorded) == expected, f"{label}: {q(recorded)} != {expected}")


def vector(recorded, expected, label):
    require(len(recorded) == len(expected), f"{label}: length")
    for i, (actual, wanted) in enumerate(zip(recorded, expected)):
        eq(actual, wanted, f"{label}[{i}]")


def numeric_representations(obj, counts):
    if isinstance(obj, dict):
        if "exact" in obj or "value" in obj:
            require(set(obj) == {"exact", "value"}, "Malformed rational wrapper")
            exact = Q(obj["exact"])
            require(str(exact) == obj["exact"], "Noncanonical exact rational")
            require(isinstance(obj["value"], (int, float)), "Nonnumeric display")
            require(math.isfinite(obj["value"]), "Nonfinite display")
            require(math.isclose(float(exact), obj["value"], rel_tol=0, abs_tol=1e-12),
                    "Display value disagrees with exact rational")
            counts["rational_display_pairs"] += 1
        else:
            for value in obj.values():
                numeric_representations(value, counts)
    elif isinstance(obj, list):
        for value in obj:
            numeric_representations(value, counts)


def supply(early, late):
    return 4 * early + (early * early + late * late) / 10


def gradient(early, late):
    return (4 + early / 5, late / 5)


def conjugate(price):
    # Maximize p*x - a*x - x*x/10 separately over each nonnegative load.
    pe, pl = price
    return Q(5, 2) * (max(pe - 4, 0) ** 2 + max(pl, 0) ** 2)


def quadratic_minimum(function):
    """Minimum on [0,1], derived only from f(0), f(1/2), f(1)."""
    f0, fh, f1 = function(Q(0)), function(Q(1, 2)), function(Q(1))
    aa = 2 * (f1 + f0 - 2 * fh)
    bb = f1 - f0 - aa
    require(aa >= 0, "Unexpected concave quadratic")
    candidates = [(f0, Q(0)), (f1, Q(1))]
    if aa > 0 and 0 < -bb / (2 * aa) < 1:
        location = -bb / (2 * aa)
        candidates.append((function(location), location))
    return min(candidates)


def physical_intervals(reserve, efficiency, early_power, terminal_power):
    """Eliminate charging in BATTERY units from per-bus inventory constraints.

    A's bus has 5 after its service, so early delivered energy y is in [0,15].
    B's separate bus starts full and cannot charge early. Both structures must
    recover 30 battery kWh in total. The one-bus post-B inventory is y-10.
    """
    require(0 <= reserve <= 5 and 0 < efficiency <= 1, "Outside audited family")
    lower_battery = max(Q(0), 30 - efficiency * terminal_power)
    upper_battery = min(Q(15), efficiency * early_power)
    return {
        1: (max(lower_battery, 10 + reserve) / efficiency,
            upper_battery / efficiency),
        2: (lower_battery / efficiency, upper_battery / efficiency),
    }


def full_hull_minimum(points, total):
    """Enumerate every chord of the endpoint set, including upper chords.

    The objective increases strictly in intrinsic cost. Its minimum over the
    two-dimensional polygon is on its lower boundary, which consists of chords
    between endpoints. Hence the minimum over ALL chords equals the complete
    polygon minimum. Strict convexity in x gives a unique optimal (x,c).
    """
    candidates = [(supply(x, total - x) + c, x, c) for x, c, _ in points]
    for left, right in itertools.combinations(points, 2):
        x0, c0, _ = left
        x1, c1, _ = right
        objective = lambda t: supply(x0 + t * (x1 - x0),
                                     total - x0 - t * (x1 - x0)) + c0 + t * (c1 - c0)
        value, weight = quadratic_minimum(objective)
        candidates.append((value, x0 + weight * (x1 - x0),
                           c0 + weight * (c1 - c0)))
    return min(candidates)


def lower_vertices(points):
    # Supporting-line definition, independently checking every point above it.
    by_x = {}
    for x, c, buses in points:
        if x not in by_x or c < by_x[x][1]:
            by_x[x] = (x, c, buses)
    reduced = list(by_x.values())
    if len(reduced) == 1:
        return reduced
    vertices = set()
    for a, b in itertools.combinations(reduced, 2):
        if a[0] > b[0]:
            a, b = b, a
        slope = (b[1] - a[1]) / (b[0] - a[0])
        if all(c >= a[1] + slope * (x - a[0]) for x, c, _ in reduced):
            vertices.update((a, b))
    ordered = sorted(vertices)
    # Drop any nonextreme point on a straight supporting edge.
    return [p for i, p in enumerate(ordered)
            if i == 0 or i == len(ordered) - 1 or
            (p[1] - ordered[i - 1][1]) * (ordered[i + 1][0] - p[0]) !=
            (ordered[i + 1][1] - p[1]) * (p[0] - ordered[i - 1][0])]


def audit_witness(witness, buses, early, parameters, counts):
    reserve, efficiency, early_power, terminal_power = parameters
    total = 30 / efficiency
    require(buses in (1, 2), "Invalid used-fleet size")
    require(len(witness["buses"]) == buses, "Witness fleet count")
    vector(witness["load"], (early, total - early), "witness aggregate loads")
    eq(witness["grid_total"], total, "gross grid total")
    eq(witness["battery_delivery"], Q(30), "net battery recharge")
    services = []
    all_soc = []
    early_sum = Q(0)
    late_sum = Q(0)
    terminal_by_bus = {}
    for index, bus in enumerate(witness["buses"]):
        assigned = bus["services"]
        require(assigned and len(assigned) == len(set(assigned)), "Empty or duplicate assignment")
        require(all(service in ("A", "B") for service in assigned), "Unknown service")
        services.extend(assigned)
        e, late = q(bus["early"]), q(bus["terminal"])
        require(0 <= e <= early_power and 0 <= late, "Bus grid charging bounds")
        soc = [Q(20)]
        soc.append(soc[-1] - 15 * ("A" in assigned))
        soc.append(soc[-1] + efficiency * e)
        soc.append(soc[-1] - 15 * ("B" in assigned))
        soc.append(soc[-1] + efficiency * late)
        vector(bus["soc"], soc, "replayed bus SOC")
        require(soc[-1] == 20, "Individual bus not fully replenished")
        require(all(reserve <= amount <= 20 for amount in soc), "SOC reserve/capacity violation")
        all_soc.extend(soc)
        early_sum += e
        late_sum += late
        terminal_by_bus[index] = late
        counts["bus_replays"] += 1
        counts["soc_event_replays"] += len(soc)
    require(sorted(services) == ["A", "B"], "Mandatory service partition incomplete")
    require(early_sum == early and late_sum == total - early, "Bus/aggregate mismatch")
    require(early_sum <= early_power and late_sum <= terminal_power, "Shared power limit")

    # Replay plug occupancy and integrate power. Include every session endpoint,
    # so checking open segment midpoints proves nonoverlap for the entire hour.
    sessions = witness["terminal_sessions"]
    actual_energy = Counter()
    breakpoints = {Q(3), Q(4)}
    seen_buses = set()
    for session in sessions:
        index = session["bus"]
        require(index in terminal_by_bus and index not in seen_buses, "Terminal bus session identity")
        seen_buses.add(index)
        require(session["connector"] == 0, "More than one connector")
        start, end, power = q(session["start"]), q(session["end"]), q(session["power"])
        require(3 <= start < end <= 4, "Terminal session time interval")
        require(0 < power <= terminal_power, "Terminal connector power")
        energy = (end - start) * power
        eq(session["energy"], energy, "Integrated terminal session energy")
        require(energy == terminal_by_bus[index], "Session/bus terminal energy mismatch")
        # Monotone charging between verified initial and final SOC suffices for
        # the whole continuous session, not just a sampled occupancy replay.
        actual_energy[index] += energy
        breakpoints.update((start, end))
        counts["terminal_session_replays"] += 1
    require(dict(actual_energy) == terminal_by_bus, "Missing terminal recharge session")
    for start, end in itertools.pairwise(sorted(breakpoints)):
        mid = (start + end) / 2
        active = [s for s in sessions if q(s["start"]) <= mid < q(s["end"])]
        require(len(active) == 1, "Terminal overlap or idle gap in constant-power witness")
        require(q(active[0]["power"]) == late_sum, "Aggregate terminal power not constant")
        counts["connector_interval_replays"] += 1
    expected_margins = {
        "capacity": 20 - max(all_soc), "reserve": min(all_soc) - reserve,
        "early_power": early_power - early_sum,
        "terminal_power": terminal_power - late_sum,
    }
    require(set(witness["margins"]) == set(expected_margins), "Margin schema")
    for name, margin in expected_margins.items():
        eq(witness["margins"][name], margin, f"{name} margin")
        require(margin >= 0, "Negative physical margin")
    counts["schedule_witnesses"] += 1


def audit_case(case, expected_parameters, counts):
    names = ("reserve", "efficiency", "early_power", "terminal_power")
    parameters = tuple(q(case[name]) for name in names)
    require(parameters == expected_parameters, "Case parameter/order mismatch")
    r, eta, power, terminal = parameters
    total = 30 / eta
    eq(case["grid_total"], total, "case gross grid total")
    intervals = physical_intervals(*parameters)
    require([b["buses"] for b in case["branches"]] == [1, 2], "Branch coverage")
    points, optima = set(), {}
    for branch in case["branches"]:
        buses = branch["buses"]
        low, high = intervals[buses]
        eq(branch["lower"], low, "branch lower")
        eq(branch["upper"], high, "branch upper")
        require(branch["feasible"] is (low <= high), "Branch feasibility")
        counts["physical_intervals"] += 1
        if low > high:
            require(set(branch) == {"buses", "feasible", "lower", "upper"},
                    "Infeasible branch contains an optimization output")
            continue
        value, t = quadratic_minimum(lambda t: 7 * buses + supply(
            low + t * (high - low), total - low - t * (high - low)))
        early = low + t * (high - low)
        optima[buses] = (value, early)
        eq(branch["early"], early, "continuous branch minimizer")
        eq(branch["objective"], value, "continuous branch objective")
        audit_witness(branch["witness"], buses, early, parameters, counts)
        points.update(((low, Q(7 * buses), buses), (high, Q(7 * buses), buses)))
    feasible = bool(optima)
    require(case["feasible"] is feasible, "Whole-model feasibility")
    if not feasible:
        require(case["classification"] == "infeasible", "Infeasibility label")
        require(all(case[name] is None for name in ("physical", "convexified", "gap")),
                "Infeasible objective reported as a number")
        return {"parameters": list(map(str, parameters)), "classification": "infeasible"}

    recorded_points = set()
    for point in case["endpoint_witnesses"]:
        x, c, buses = q(point["early"]), q(point["intrinsic_cost"]), point["buses"]
        require((x, c, buses) not in recorded_points, "Duplicate endpoint witness")
        recorded_points.add((x, c, buses))
        audit_witness(point["witness"], buses, x, parameters, counts)
    require(recorded_points == points, "Complete feasible endpoint set mismatch")
    counts["endpoint_witnesses"] += len(recorded_points)
    hull, hull_early, hull_cost = full_hull_minimum(sorted(points), total)
    physical = min(value for value, _ in optima.values())
    gap = physical - hull
    eq(case["physical"], physical, "physical optimum")
    eq(case["convexified"], hull, "complete hull optimum")
    eq(case["gap"], gap, "planning gap")
    eq(case["hull_intrinsic_cost"], hull_cost, "hull intrinsic cost")
    vector(case["hull_load"], (hull_early, total - hull_early), "hull aggregate load")
    require(case["physical_optimal_bus_counts"] == sorted(
        buses for buses, (value, _) in optima.items() if value == physical), "Physical optimizer identities")
    require(case["classification"] == ("positive" if gap > 0 else "zero"), "Gap classification")
    require(gap >= 0, "Negative relaxation gap")
    actual_vertices = [(q(x), q(c), buses) for x, c, buses in case["hull_vertices"]]
    require(actual_vertices == lower_vertices(points), "Complete lower-hull vertex set")

    weighted_early, weighted_cost, weight_sum = Q(0), Q(0), Q(0)
    for component in case["hull_components"]:
        weight = q(component["weight"])
        require(0 < weight <= 1, "Nonpositive or excessive mixture weight")
        buses = component["buses"]
        early = q(component["witness"]["load"][0])
        require((early, Q(7 * buses), buses) in points, "Mixture does not use a feasible endpoint")
        audit_witness(component["witness"], buses, early, parameters, counts)
        weighted_early += weight * early
        weighted_cost += weight * 7 * buses
        weight_sum += weight
        counts["positive_mixture_components"] += 1
    require((weight_sum, weighted_early, weighted_cost) == (1, hull_early, hull_cost),
            "Mixture does not reconstruct complete-hull minimizer")

    hull_price = gradient(hull_early, total - hull_early)
    vector(case["hull_price"], hull_price, "hull price")
    response = lambda price: min(c + price[0] * x + price[1] * (total - x)
                                 for x, c, _ in points)
    hull_response = response(hull_price)
    dual_supply = conjugate(hull_price)
    eq(case["hull_response"], hull_response, "complete fleet posted-price response")
    eq(case["hull_conjugate"], dual_supply, "global nonnegative supply conjugate")
    require(hull_response - dual_supply == hull, "Exact hull primal/dual identity")
    for branch in case["branches"]:
        if not branch["feasible"]:
            continue
        buses = branch["buses"]
        value, x = optima[buses]
        own_price = gradient(x, total - x)
        vector(branch["own_price"], own_price, "physical branch gradient price")
        regret = 7 * buses + own_price[0] * x + own_price[1] * (total - x) - response(own_price)
        fleet = 7 * buses + hull_price[0] * x + hull_price[1] * (total - x) - hull_response
        supplier = supply(x, total - x) + dual_supply - hull_price[0] * x - hull_price[1] * (total - x)
        eq(branch["own_price_regret"], regret, "own-price regret")
        eq(branch["fleet_LOC_at_hull_price"], fleet, "common-price fleet LOC")
        eq(branch["supply_LOC_at_hull_price"], supplier, "common-price supply LOC")
        require(min(regret, fleet, supplier) >= 0, "Negative opportunity cost")
        require(fleet + supplier == value - hull, "Common-price total LOC identity")
        require(regret >= gap, "Gap/own-price regret inequality")
        counts["branch_price_accounts"] += 1
    return {"parameters": list(map(str, parameters)), "classification": case["classification"],
            "physical": str(physical), "convexified": str(hull), "gap": str(gap)}


def audit_document(document):
    counts = Counter()
    numeric_representations(document, counts)
    grid = [(Q(r), eta, Q(p), Q(30)) for r in (0, 1)
            for eta in (Q(1), Q(19, 20)) for p in (10, 11, 12)]
    grid.extend((Q(0), Q(1), Q(10), k) for k in (Q(10), Q(20), Q(47, 2), Q(24)))
    require(len(document["cases"]) == len(grid) == 16, "Frozen grid size")
    require([[q(v) for v in row] for row in document["grid"]] == [list(p) for p in grid],
            "Frozen grid parameter inventory")
    require(document["head"] == FROZEN_HEAD, "Wrong source head")
    require(document["source_hashes"] == SOURCE_HASHES, "Wrong frozen source hashes")
    cases = [audit_case(case, parameters, counts)
             for case, parameters in zip(document["cases"], grid)]
    classes = dict(Counter(case["classification"] for case in cases))
    require(classes == {"positive": 9, "zero": 6, "infeasible": 1}, "Unexpected independently derived outcomes")
    require(document["classifications"] == classes, "Recorded classification totals")
    require(document["analytical_prediction"] == classes and document["prediction_matches"] is True,
            "Prediction/result comparison")
    return {"counts": dict(counts), "classifications": classes, "cases": cases}


def packed(value):
    value = Q(value)
    return {"exact": str(value), "value": float(value)}


def corruption_controls(document):
    """Controls run the semantic auditor without the outer input hash gate."""
    def change(path, value):
        def apply(data):
            target = data
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
        return apply

    def shift_terminal_session_earlier(data):
        session = data["cases"][11]["hull_components"][0]["witness"]["terminal_sessions"][1]
        # Preserve duration, energy and power: only continuous plug occupancy
        # should reject this overlapping session, not the integral check.
        duration = q(session["end"]) - q(session["start"])
        session["start"] = packed(3)
        session["end"] = packed(3 + duration)

    def accelerate_terminal_session(data):
        session = data["cases"][11]["hull_components"][0]["witness"]["terminal_sessions"][0]
        session["power"] = packed(31)
        session["end"] = packed(q(session["start"]) + q(session["energy"]) / 31)

    cases = [
        ("wrong_display_only", change(["cases", 0, "gap", "value"], 99.0)),
        ("joint_gap_altered", change(["cases", 11, "gap"], packed(Q(94249, 28880) + 1))),
        ("lossy_grid_total_not_grossed_up", change(["cases", 11, "grid_total"], packed(30))),
        ("reserve_lower_bound_removed", change(["cases", 6, "branches", 0, "lower"], packed(10))),
        ("infeasible_one_bus_marked_feasible", change(["cases", 9, "branches", 0, "feasible"], True)),
        ("terminal_infeasibility_hidden_as_zero", change(["cases", 12, "physical"], packed(0))),
        ("interior_branch_optimum_shifted", change(["cases", 0, "branches", 1, "early"], packed(6))),
        ("endpoint_omitted", lambda d: d["cases"][11]["endpoint_witnesses"].pop()),
        ("hull_vertex_omitted", lambda d: d["cases"][11]["hull_vertices"].pop()),
        ("mixture_weight_altered", change(["cases", 11, "hull_components", 0, "weight"], packed(Q(1, 2)))),
        ("full_replenishment_lost", change(["cases", 11, "branches", 0, "witness", "buses", 0, "soc", 4], packed(19))),
        ("battery_efficiency_ignored", change(["cases", 11, "branches", 0, "witness", "buses", 0, "soc", 2], packed(Q(5) + Q(220, 19)))),
        ("terminal_sessions_overlap", change(["cases", 11, "hull_components", 0, "witness", "terminal_sessions", 1, "start"], packed(3))),
        ("terminal_overlap_with_integrals_preserved", shift_terminal_session_earlier),
        ("terminal_power_excess_with_integral_preserved", accelerate_terminal_session),
        ("second_connector_used", change(["cases", 11, "hull_components", 0, "witness", "terminal_sessions", 1, "connector"], 1)),
        ("terminal_integral_corrupted", change(["cases", 11, "hull_components", 0, "witness", "terminal_sessions", 0, "energy"], packed(15))),
        ("own_price_regret_corrupted", change(["cases", 11, "branches", 0, "own_price_regret"], packed(0))),
        ("global_supply_conjugate_corrupted", change(["cases", 11, "hull_conjugate"], packed(0))),
        ("fleet_LOC_corrupted", change(["cases", 11, "branches", 1, "fleet_LOC_at_hull_price"], packed(0))),
        ("supply_LOC_corrupted", change(["cases", 11, "branches", 0, "supply_LOC_at_hull_price"], packed(0))),
        ("grid_case_omitted", lambda d: d["cases"].pop()),
    ]
    outcomes = []
    for name, mutate in cases:
        altered = copy.deepcopy(document)
        mutate(altered)
        try:
            audit_document(altered)
        except AuditError as error:
            outcomes.append({"control": name, "rejected": True, "reason": str(error)})
        else:
            raise AuditError(f"Corruption control not rejected: {name}")
    return outcomes


def analytical_crosschecks():
    # Independently substitute the strict sufficient conditions at the joint
    # point. Continuity, not a sampled parameter sweep, yields the neighborhood.
    r, eta, power, terminal = Q(1), Q(19, 20), Q(12), Q(30)
    intervals = physical_intervals(r, eta, power, terminal)
    h, u = intervals[1]
    ell = intervals[2][0]
    total = 30 / eta
    m = (total - 20) / 2
    d = h - ell
    threshold = Q(2, 5) * d * (h - m)
    require(0 < r < 5 and 0 < eta < 1 and ell < m < h < u and Q(7) < threshold,
            "Joint strict-neighborhood hypotheses fail")
    xstar = m + Q(35, 2) / d
    independent_gap = min((h - xstar) ** 2 / 5,
                          7 * (m - ell) / d + Q(245, 4) / d ** 2)
    require(independent_gap == Q(94249, 28880), "Joint analytical gap")
    require(u - h == Q(8, 19), "Joint early headroom")
    # For K=20+d, 0<d<=10: upper-edge derivative = 2-7/d.
    # The left derivative is 2-(2/5)d-7/d<0; multiplying by
    # -5d gives 2d^2-10d+35, whose discriminant is -180<0.
    require((-10) ** 2 - 4 * 2 * 35 < 0, "Threshold left-derivative proof")
    threshold_power = 20 + Q(7, 2)
    require(threshold_power == Q(47, 2), "Terminal threshold")
    for k, expected in ((Q(20), Q(0)), (Q(47, 2), Q(0)),
                        (Q(24), Q(5, 64)), (Q(30), Q(169, 80))):
        calculated = Q(0) if k <= threshold_power else (5 - Q(35, 2) / (k - 20)) ** 2 / 5
        require(calculated == expected, "Terminal threshold substitution")
    return {
        "joint_early_headroom_grid_kWh": str(u - h),
        "joint_strict_fleet_cost_upper_threshold": str(threshold),
        "joint_gap": str(independent_gap),
        "terminal_power_positive_gap_threshold_kW": str(threshold_power),
        "left_derivative_polynomial_discriminant": -180,
        "scope": "Analytical continuity and one-dimensional threshold proof; no extra experiment cases",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    raw = args.result.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == RESULT_HASH, "Raw result hash mismatch")
    manifest_path = args.result.parent / "MANIFEST.json"
    manifest_before = manifest_path.read_bytes()
    manifest = json.loads(manifest_before)
    require(manifest["algorithm"] == "sha256" and manifest["files"] == {"results.json": RESULT_HASH},
            "Immutable raw manifest mismatch")
    for relative, wanted in SOURCE_HASHES.items():
        frozen_bytes = subprocess.check_output(["git", "show", f"{FROZEN_HEAD}:{relative}"], cwd=args.repo)
        require(hashlib.sha256(frozen_bytes).hexdigest() == wanted, f"Frozen Git object mismatch: {relative}")
    document = json.loads(raw)
    report = audit_document(document)
    report.update({
        "verdict": "PASS",
        "independence": "Non-author auditor; standard library only; no author code imports or solver",
        "frozen_head": FROZEN_HEAD, "result_sha256": RESULT_HASH,
        "raw_manifest_sha256": hashlib.sha256(manifest_before).hexdigest(),
        "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "analytical_crosschecks": analytical_crosschecks(),
        "corruption_controls": corruption_controls(document),
    })
    require(args.result.read_bytes() == raw and manifest_path.read_bytes() == manifest_before,
            "Input artifact changed during audit")
    with args.report.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"verdict": report["verdict"], "classifications": report["classifications"],
                      "counts": report["counts"], "rejected_corruption_controls": len(report["corruption_controls"]),
                      "report": str(args.report)}, indent=2))


if __name__ == "__main__":
    main()
