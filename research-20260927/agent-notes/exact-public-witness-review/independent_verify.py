#!/usr/bin/env python3
"""Narrow independent exact audit of the depot-15 candidate; stdlib only."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fractions import Fraction
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = None
PACKAGE = None
CANDIDATE = None
FROZEN = None
RESULT = None
PAYLOAD = "data/public/sistig_26088190_v1/hildenbrand_native_cases.json"
FLOW_REPORT = None
FLOW_REVIEW = None
FLOW_ATTEMPT = None
PINNED_CANDIDATE_SHA = "fafb2e2721a283b0ef43b94357c497710ad113c79f85427a8aabc4211b8aa325"
PINNED_COMMIT = "282e00b80b6fd9457006429b089269b2a9e2be92"
REMOVALS = {
    18: Fraction(1013, 562949953421312),
    16: Fraction(3857, 562949953421312),
}


class AuditError(AssertionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def q(value) -> Fraction:
    """Exact binary rationals for JSON floats; exact strings for candidate fractions."""
    if isinstance(value, bool):
        raise AuditError("boolean is not a numeric input")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, float):
        return Fraction.from_float(value)
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    raise AuditError(f"unsupported exact-number type: {type(value).__name__}")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_package_pins():
    manifest = read_json(PACKAGE / "MANIFEST.json")
    require(manifest["status"] == "candidate-pending-independent-review",
            "package is no longer marked as a pending candidate")
    for name, pin in manifest["files"].items():
        raw = (PACKAGE / name).read_bytes()
        require(len(raw) == pin["bytes"] and sha(raw) == pin["sha256"],
                f"package manifest mismatch: {name}")
    raw_candidate = CANDIDATE.read_bytes()
    require(sha(raw_candidate) == PINNED_CANDIDATE_SHA,
            "candidate does not match requested byte hash")
    frozen_raw, result_raw = FROZEN.read_bytes(), RESULT.read_bytes()
    require(sha(frozen_raw) == manifest["archive"]["frozen_sha256"],
            "pinned original frozen JSON hash mismatch")
    require(sha(result_raw) == manifest["archive"]["depot15_result_sha256"],
            "pinned original depot-15 result hash mismatch")
    return json.loads(raw_candidate), json.loads(frozen_raw), json.loads(result_raw), manifest


def validate_routes(candidate, case, plan):
    trips = {row["id"]: row for row in case["trips"]}
    movements = {row["id"]: row for row in case["movements"]}
    require(len(trips) == len(case["trips"]), "duplicate trip identifiers in frozen case")
    require(len(movements) == len(case["movements"]), "duplicate movement identifiers in frozen case")
    require(candidate["routes"] == [
        {"vehicle": row["vehicle"], "movements": row["movements"], "trips": row["trips"]}
        for row in plan["vehicles"]], "candidate changed an archived route")

    route_by_vehicle = {row["vehicle"]: row for row in candidate["routes"]}
    require(len(route_by_vehicle) == len(candidate["routes"]) == 2,
            "candidate must use exactly two distinct vehicles")
    covered = []
    for vehicle, route in route_by_vehicle.items():
        tids, mids = route["trips"], route["movements"]
        require(tids and len(mids) == len(tids) + 1, f"vehicle {vehicle}: route arity")
        require(all(t in trips for t in tids), f"vehicle {vehicle}: unknown trip")
        covered.extend(tids)
        first, last = movements.get(mids[0]), movements.get(mids[-1])
        require(first is not None and first["kind"] == "pullout"
                and first["before"] is None and first["after"] == tids[0],
                f"vehicle {vehicle}: invalid pullout")
        require(last is not None and last["kind"] == "pullin"
                and last["before"] == tids[-1] and last["after"] is None,
                f"vehicle {vehicle}: invalid pullin")

        ordered_trips = [trips[t] for t in tids]
        require(all(q(t["start_min"]) < q(t["end_min"]) for t in ordered_trips),
                f"vehicle {vehicle}: nonpositive service duration")
        for before, after in zip(ordered_trips, ordered_trips[1:]):
            require(q(before["end_min"]) <= q(after["start_min"]),
                    f"vehicle {vehicle}: overlapping/out-of-order services")

        require(len(first["legs"]) == 1, f"vehicle {vehicle}: unexpected pullout legs")
        leg = first["legs"][0]
        require(leg["origin"] == case["depot"]
                and leg["destination"] == ordered_trips[0]["start_place"]
                and q(leg["depart_min"]) <= q(leg["arrive_min"])
                and q(leg["depart_min"]) >= q(case["terminal_open_min"])
                and q(leg["arrive_min"]) <= q(ordered_trips[0]["start_min"]),
                f"vehicle {vehicle}: pullout does not reach first service in time")

        for i, mid in enumerate(mids[1:-1]):
            movement = movements.get(mid)
            before, after = ordered_trips[i], ordered_trips[i + 1]
            require(movement is not None and movement["before"] == before["id"]
                    and movement["after"] == after["id"],
                    f"vehicle {vehicle}: internal movement does not join adjacent trips")
            legs = movement["legs"]
            require(bool(legs), f"vehicle {vehicle}: empty movement")
            require(legs[0]["origin"] == before["end_place"]
                    and legs[-1]["destination"] == after["start_place"],
                    f"vehicle {vehicle}: connection endpoints do not match trips")
            for j, current in enumerate(legs):
                dep, arr = q(current["depart_min"]), q(current["arrive_min"])
                require(dep <= arr and dep >= q(before["end_min"])
                        and arr <= q(after["start_min"]),
                        f"vehicle {vehicle}: connection leg outside service gap")
                if j:
                    previous = legs[j - 1]
                    require(previous["destination"] == current["origin"]
                            and q(previous["arrive_min"]) <= dep,
                            f"vehicle {vehicle}: discontinuous connection legs")
            if movement["kind"] == "depot":
                require(len(legs) == 2 and movement["depot_split"] == 1
                        and legs[0]["destination"] == case["depot"]
                        and legs[1]["origin"] == case["depot"],
                        f"vehicle {vehicle}: invalid depot split")
            else:
                require(movement["kind"] == "direct" and movement["depot_split"] is None,
                        f"vehicle {vehicle}: unknown internal mode")

        pullin = last["legs"]
        require(len(pullin) == 1, f"vehicle {vehicle}: unexpected pullin legs")
        leg = pullin[0]
        require(leg["origin"] == ordered_trips[-1]["end_place"]
                and leg["destination"] == case["depot"]
                and q(leg["depart_min"]) <= q(leg["arrive_min"])
                and q(leg["depart_min"]) >= q(ordered_trips[-1]["end_min"])
                and q(leg["arrive_min"]) <= q(case["recharge_deadline_min"]),
                f"vehicle {vehicle}: pullin misses depot/deadline")

    require(Counter(covered) == Counter(trips.keys()), "routes do not cover every service exactly once")
    for record in candidate["vehicles"]:
        vehicle = record["vehicle"]
        route = route_by_vehicle.get(vehicle)
        require(route is not None, f"vehicle {vehicle}: SOC record has no candidate route")
    return trips, movements, route_by_vehicle


def validate_sessions(candidate, case, plan, movements, route_by_vehicle):
    sessions = candidate["sessions"]
    charges = plan["charges"]
    require(len(sessions) == len(charges) == 19, "expected 19 archived charging sessions")
    require([s["index"] for s in sessions] == list(range(len(sessions))),
            "session indices/order changed")
    repairs = {int(r["session_index"]): r for r in candidate["repairs"]}
    require(len(repairs) == len(candidate["repairs"]) == 2 and set(repairs) == {16, 18},
            "candidate must contain only the two terminal repairs")
    require(q(repairs[18]["removed_grid_kwh"]) == REMOVALS[18]
            and q(repairs[16]["removed_grid_kwh"]) == REMOVALS[16],
            "terminal repair amounts differ from the declared exact corrections")

    resources = case["resources"]
    require(len(resources) == 1, "unexpected resource-window structure")
    resource = resources[0]
    intervals = []
    charge_by_vehicle = {v: [] for v in route_by_vehicle}
    for i, (session, saved) in enumerate(zip(sessions, charges)):
        require(session["vehicle"] == saved["vehicle"]
                and session["connector"] == saved["connector"]
                and session["movement"] == saved["movement"],
                f"session {i}: owner/connector differs from archived source")
        start, end = q(session["start_min"]), q(session["end_min"])
        require(start == q(saved["start_min"]) and end == q(saved["end_min"]),
                f"session {i}: fixed timing changed")
        require(start < end and start >= q(resource["start_min"])
                and end <= q(resource["end_min"])
                and end <= q(case["recharge_deadline_min"]),
                f"session {i}: outside resource/deadline window")
        original = q(saved["grid_kwh"])
        if i in repairs:
            repair = repairs[i]
            require(repair["vehicle"] == session["vehicle"]
                    and q(repair["original_grid_kwh"]) == original
                    and q(repair["repaired_grid_kwh"]) == q(session["grid_kwh"]),
                    f"session {i}: repair ledger does not reconcile")
            expected_energy = original - REMOVALS[i]
        else:
            expected_energy = original
        energy = q(session["grid_kwh"])
        require(energy == expected_energy and energy > 0,
                f"session {i}: energy differs from exact archived amount/repair")
        require(type(session["connector"]) is int
                and 0 <= session["connector"] < resource["connectors"],
                f"session {i}: invalid connector")
        mode = movements.get(session["movement"])
        require(mode is not None and session["vehicle"] in route_by_vehicle
                and session["movement"] in route_by_vehicle[session["vehicle"]]["movements"],
                f"session {i}: owner movement is not on that vehicle's route")
        if mode["kind"] == "depot":
            lo, hi = q(mode["legs"][0]["arrive_min"]), q(mode["legs"][1]["depart_min"])
            require(mode["legs"][0]["destination"] == case["depot"]
                    and mode["legs"][1]["origin"] == case["depot"],
                    f"session {i}: depot dwell does not occur at the depot")
        elif mode["kind"] == "pullin":
            lo, hi = q(mode["legs"][0]["arrive_min"]), q(case["recharge_deadline_min"])
            require(mode["legs"][0]["destination"] == case["depot"],
                    f"session {i}: pullin does not reach the depot")
        else:
            raise AuditError(f"session {i}: charging assigned to nonstationary mode")
        require(start >= lo and end <= hi, f"session {i}: outside its depot dwell")
        rate = energy * 60 / (end - start)
        require(rate <= q(resource["per_bus_kw"])
                and rate <= q(resource["grid_kw"]),
                f"session {i}: exceeds per-bus/shared power cap")
        intervals.append((start, end, session["connector"], rate, i))
        charge_by_vehicle[session["vehicle"]].append(session)

    intervals.sort()
    for left, right in zip(intervals, intervals[1:]):
        require(left[2] != right[2] or left[1] <= right[0],
                f"sessions {left[4]} and {right[4]} overlap on connector {left[2]}")
    # Sweep exact half-open intervals to certify total instantaneous grid power.
    points = sorted({t for row in intervals for t in row[:2]})
    max_power = Fraction(0)
    for lo, hi in zip(points, points[1:]):
        active = [row for row in intervals if row[0] <= lo and hi <= row[1]]
        total = sum((row[3] for row in active), Fraction(0))
        require(len(active) <= resource["connectors"], "connector count exceeded")
        require(total <= q(resource["grid_kw"]), "shared instantaneous grid cap exceeded")
        max_power = max(max_power, total)
    return charge_by_vehicle, intervals, max_power


def validate_soc(candidate, case, trips, movements, route_by_vehicle, charge_by_vehicle):
    battery, reserve, efficiency = q(case["battery_kwh"]), q(case["reserve_kwh"]), q(case["efficiency"])
    observed = {v["vehicle"]: v for v in candidate["vehicles"]}
    require(len(candidate["vehicles"]) == len(observed) == 2
            and set(observed) == set(route_by_vehicle),
            "vehicle SOC records do not match the two routes")
    min_soc = battery
    totals = {}
    for vehicle, route in route_by_vehicle.items():
        expected = Counter()
        exact_energy = {}
        expected[("initial", "battery", Fraction(0))] += 1
        exact_energy[("initial", "battery", Fraction(0))] = Fraction(0)
        movement_energy = Fraction(0)
        service_energy = Fraction(0)
        for mid in route["movements"]:
            movement = movements[mid]
            for i, leg in enumerate(movement["legs"]):
                key = ("movement", f"{mid}:leg:{i}", q(leg["arrive_min"]))
                expected[key] += 1
                e = q(leg["energy_kwh"])
                exact_energy[key] = -e
                movement_energy += e
        for tid in route["trips"]:
            trip = trips[tid]
            key = ("service", tid, q(trip["end_min"]))
            expected[key] += 1
            e = q(trip["energy_kwh"])
            exact_energy[key] = -e
            service_energy += e
        grid_energy = Fraction(0)
        for session in charge_by_vehicle[vehicle]:
            key = ("charge", str(session["index"]), q(session["end_min"]))
            expected[key] += 1
            e = q(session["grid_kwh"]) * efficiency
            exact_energy[key] = e
            grid_energy += q(session["grid_kwh"])

        events = observed[vehicle]["soc_events"]
        actual = Counter((e["kind"], e["source"], q(e["time_min"])) for e in events)
        require(actual == expected, f"vehicle {vehicle}: SOC event set differs from reconstructed route")
        times = [q(e["time_min"]) for e in events]
        require(times == sorted(times), f"vehicle {vehicle}: SOC events are not chronological")
        # A simultaneous charge/discharge tie has order-dependent extrema; none is present.
        at_time = {}
        soc = battery
        for event in events:
            key = (event["kind"], event["source"], q(event["time_min"]))
            delta = exact_energy[key]
            require(q(event["energy_change_kwh"]) == delta,
                    f"vehicle {vehicle}: event energy differs from frozen input")
            sign = (delta > 0) - (delta < 0)
            at_time.setdefault(key[2], set()).add(sign)
            soc += delta
            require(q(event["soc_after_kwh"]) == soc,
                    f"vehicle {vehicle}: saved SOC does not equal exact event sum")
            require(reserve <= soc <= battery,
                    f"vehicle {vehicle}: exact SOC outside reserve/capacity")
            min_soc = min(min_soc, soc)
        require(all(not ({-1, 1} <= signs) for signs in at_time.values()),
                f"vehicle {vehicle}: tied charge/discharge event needs a finer ordering proof")
        require(times[-1] <= q(case["recharge_deadline_min"]) and soc == battery,
                f"vehicle {vehicle}: not exactly full by 30-hour deadline")
        require(q(observed[vehicle]["consumption_kwh"]) == movement_energy + service_energy,
                f"vehicle {vehicle}: consumption total differs from frozen inputs")
        require(q(observed[vehicle]["grid_kwh"]) == grid_energy
                and grid_energy * efficiency == movement_energy + service_energy,
                f"vehicle {vehicle}: charging does not balance exact consumption")
        totals[vehicle] = {"movement_kwh": movement_energy, "service_kwh": service_energy,
                           "consumption_kwh": movement_energy + service_energy,
                           "grid_kwh": grid_energy, "terminal_soc_kwh": soc}
    return totals, min_soc


def validate_loads_and_cost(candidate, case, control, route_by_vehicle, intervals, totals):
    edges = [q(x) for x in case["market_edges_min"]]
    require(len(edges) == 31 and edges[0] == 0 and edges[-1] == 1800,
            "expected 30 consecutive full-hour periods over 30:00")
    calculated = []
    for lo, hi in zip(edges, edges[1:]):
        load = Fraction(0)
        for session in candidate["sessions"]:
            start, end = q(session["start_min"]), q(session["end_min"])
            overlap = max(Fraction(0), min(end, hi) - max(start, lo))
            if overlap:
                load += q(session["grid_kwh"]) * overlap / (end - start)
        require(load <= q(case["resources"][0]["grid_kw"]), "hourly energy exceeds grid cap")
        calculated.append(load)
    saved = [q(x) for x in candidate["hourly_grid_kwh"]]
    require(len(saved) == 30 and saved == calculated,
            "one or more of the 30 exact hourly loads differs from reconstructed sessions")
    total = sum(calculated, Fraction(0))
    require(total == q(candidate["total_grid_kwh"])
            and total == sum((x["grid_kwh"] for x in totals.values()), Fraction(0)),
            "total charging energy does not equal 30-hour loads and per-vehicle sums")
    ops = q(case["vehicle_cost"]) * len(route_by_vehicle)
    prices = [q(p) for p in control["prices"]]
    require(len(prices) == 30, "flat market does not have 30 prices")
    objective = ops + sum((p * load for p, load in zip(prices, calculated)), Fraction(0))
    require(q(candidate["ops_cost_exact"]) == ops
            and q(candidate["flat_objective_exact"]) == objective,
            "exact flat objective does not reconcile to ops cost and hourly prices")
    return calculated, total, ops, objective


def validate_candidate(candidate, frozen, result):
    control = next(c for c in frozen["controls"] if c["id"] == "depot_15_flat")
    plan = result["result"]["plan"]
    case = control["case"]
    require(candidate["source_commit"] == frozen["freeze_label"] == PINNED_COMMIT,
            "candidate source commit differs from archived freeze")
    require(candidate["source_frozen_sha256"] == sha(FROZEN.read_bytes())
            and candidate["source_result_sha256"] == sha(RESULT.read_bytes()),
            "candidate source byte pins do not match")
    require(candidate["case_identity"] == control["case_identity"]
            == result["result"]["case_identity"] == plan["case_identity"],
            "candidate and archived case identities differ")
    require(case["depot"] == "P15" and case["graph_scope"] == "declared-movement-modes-only"
            and q(case["battery_kwh"]) == 400 and q(case["efficiency"]) == 1
            and len(candidate["routes"]) <= case["max_vehicles"]
            and q(candidate["terminal_deadline_min"]) == q(case["recharge_deadline_min"]),
            "candidate does not refer to the declared depot-15 ideal case")
    require(result["cell"] == "depot_15_flat"
            and len(result["result"]["prices"]) == len(control["prices"])
            and all(q(a) == q(b) for a, b in zip(result["result"]["prices"], control["prices"])),
            "archived result does not match the frozen flat-price control")
    trips, movements, route_by_vehicle = validate_routes(candidate, case, plan)
    charge_by_vehicle, intervals, max_power = validate_sessions(
        candidate, case, plan, movements, route_by_vehicle)
    totals, min_soc = validate_soc(candidate, case, trips, movements,
                                   route_by_vehicle, charge_by_vehicle)
    loads, total_grid, ops, objective = validate_loads_and_cost(
        candidate, case, control, route_by_vehicle, intervals, totals)
    return {"services": len(trips), "vehicles": len(route_by_vehicle),
            "route_movement_counts": {str(v): len(r["movements"])
                                      for v, r in route_by_vehicle.items()},
            "sessions": len(candidate["sessions"]),
            "soc_events": sum(len(v["soc_events"]) for v in candidate["vehicles"]),
            "hourly_periods": len(loads), "min_soc_kwh": str(min_soc),
            "max_power_kw": str(max_power), "total_grid_kwh": str(total_grid),
            "ops_cost": str(ops), "flat_objective_exact": str(objective),
            "vehicle_totals": {str(v): {k: str(x) for k, x in row.items()}
                               for v, row in totals.items()}}


def verify_one_bus_obstruction(case):
    trips = sorted(case["trips"], key=lambda t: (q(t["start_min"]), q(t["end_min"]), t["id"]))
    require(len(trips) == 37, "one-bus obstruction expects all 37 services")
    for before, after in zip(trips, trips[1:]):
        require(q(before["end_min"]) <= q(after["start_min"]),
                "chronological service order is not nonoverlapping")
    movements = case["movements"]
    forced = []
    for before, after in zip(trips, trips[1:]):
        modes = [m for m in movements if m["before"] == before["id"]
                 and m["after"] == after["id"]]
        require(len(modes) == 1 and modes[0]["kind"] == "direct",
                f"not exactly one direct-only transition: {before['id']} -> {after['id']}")
        mode = modes[0]
        legs = mode["legs"]
        require(bool(legs) and legs[0]["origin"] == before["end_place"]
                and legs[-1]["destination"] == after["start_place"],
                f"invalid forced direct endpoints: {before['id']} -> {after['id']}")
        for i, leg in enumerate(legs):
            require(q(leg["depart_min"]) <= q(leg["arrive_min"])
                    and q(leg["depart_min"]) >= q(before["end_min"])
                    and q(leg["arrive_min"]) <= q(after["start_min"]),
                    f"invalid forced direct timing: {before['id']} -> {after['id']}")
            if i:
                previous = legs[i - 1]
                require(previous["destination"] == leg["origin"]
                        and q(previous["arrive_min"]) <= q(leg["depart_min"]),
                        f"discontinuous forced direct legs: {before['id']} -> {after['id']}")
        forced.append(mode)
    service_energy = sum((q(t["energy_kwh"]) for t in trips), Fraction(0))
    require(service_energy > q(case["battery_kwh"]),
            "service-only energy does not exceed one-bus inventory")
    return {"forced_direct_transitions": len(forced),
            "service_energy_kwh": str(service_energy),
            "battery_kwh": str(q(case["battery_kwh"]))}


def flow_enclosure(candidate, frozen, objective):
    for manifest_path in (FLOW_ATTEMPT / "MANIFEST.json",
                          FLOW_ATTEMPT / "review/MANIFEST.json"):
        manifest = read_json(manifest_path)
        for name, pin in manifest["files"].items():
            raw = (manifest_path.parent / name).read_bytes()
            require(len(raw) == pin["bytes"] and sha(raw) == pin["sha256"],
                    f"prior flow audit manifest mismatch: {manifest_path.parent / name}")
    flow = read_json(FLOW_REPORT)
    depot15 = next(row for row in flow["cases"] if row["depot"] == 15)
    control = next(c for c in frozen["controls"] if c["id"] == "depot_15_flat")
    require("Verdict: PASS" in FLOW_REVIEW.read_text(encoding="utf-8"),
            "previous independent flow certificate review is not PASS")
    require(flow["verdict"] == "PASS independent exact certificate and provenance audit"
            and depot15["case_identity"] == candidate["case_identity"]
            and q(flow["flat_price_exact"]) == q(control["prices"][0])
            and depot15["services"] == 37 and depot15["paths_in_relaxation"] == 2
            and depot15["gate_flow"] == depot15["real_edges_selected"] == 35
            and depot15["primal_dual_equal"] is True,
            "flow lower bound is not pinned to the same depot-15 case and flat price")
    lower = q(depot15["lower_exact"])
    require(lower < objective, "candidate exact objective does not exceed exact flow lower bound")
    return {"lower_exact": str(lower), "lower_decimal": depot15["lower_decimal_display"],
            "candidate_upper_exact": str(objective),
            "candidate_upper_decimal": float(objective),
            "same_case_identity": depot15["case_identity"],
            "flow_review_sha256": sha(FLOW_REVIEW.read_bytes()),
            "flow_audit_sha256": sha(FLOW_REPORT.read_bytes())}


def run_corruption_controls(candidate, frozen, result):
    controls = []
    mutations = [
        ("missing-service", lambda x: x["routes"][0]["trips"].pop()),
        ("charge-energy-plus-2^-40", lambda x: x["sessions"][0].__setitem__(
            "grid_kwh", str(q(x["sessions"][0]["grid_kwh"]) + Fraction(1, 2**40)))),
        ("hour-bin-plus-2^-40", lambda x: x["hourly_grid_kwh"].__setitem__(
            0, str(q(x["hourly_grid_kwh"][0]) + Fraction(1, 2**40)))),
        ("invalid-connector", lambda x: x["sessions"][0].__setitem__("connector", 1)),
    ]
    for name, mutate in mutations:
        altered = deepcopy(candidate)
        mutate(altered)
        try:
            validate_candidate(altered, frozen, result)
        except (AuditError, KeyError, ValueError, StopIteration):
            controls.append({"control": name, "rejected": True})
        else:
            raise AuditError(f"corruption control was admitted: {name}")
    return controls


def configure_repo(repo_arg):
    """Resolve the scientific repo explicitly or from this copied review's location."""
    global ROOT, PACKAGE, CANDIDATE, FROZEN, RESULT, FLOW_REPORT, FLOW_REVIEW, FLOW_ATTEMPT
    if repo_arg:
        root = Path(repo_arg).resolve()
    else:
        here = Path(__file__).resolve()
        candidates = []
        for ancestor in (here.parent, *here.parents):
            candidates.append(ancestor)
            candidates.append(ancestor.parent / "journal-research-work")
        root = next((p for p in candidates
                     if (p / "result/sistig_exact_witness/20260927-depot15-attempt1/MANIFEST.json").is_file()), None)
        if root is None:
            raise AuditError("cannot locate repo; pass --repo PATH")
    require((root / ".git").exists(), "--repo does not identify a git working tree")
    ROOT = root
    PACKAGE = ROOT / "result/sistig_exact_witness/20260927-depot15-attempt1"
    CANDIDATE = PACKAGE / "depot15_exact_candidate.json"
    FROZEN = ROOT / "result/sistig_pricing/20260927-grb-job557543-attempt1/frozen.json"
    RESULT = ROOT / "result/sistig_pricing/20260927-grb-job557543-attempt1/depot_15_flat/result.json"
    FLOW_ATTEMPT = ROOT / "result/sistig_cardinality_flow/20260927-attempt1"
    FLOW_REPORT = FLOW_ATTEMPT / "review/audit-report.json"
    FLOW_REVIEW = FLOW_ATTEMPT / "review/REVIEW.md"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="path to the frozen journal-research-work checkout")
    parser.add_argument("--output", help="write JSON report to this path instead of stdout")
    args = parser.parse_args(argv)
    configure_repo(args.repo)
    candidate, frozen, result, manifest = verify_package_pins()
    case = next(c["case"] for c in frozen["controls"] if c["id"] == "depot_15_flat")
    blob = subprocess.check_output(["git", "show", f"{PINNED_COMMIT}:{PAYLOAD}"], cwd=ROOT)
    require(sha(blob) == frozen["source_hashes"][PAYLOAD],
            "archived source commit payload hash differs from frozen source pin")
    summary = validate_candidate(candidate, frozen, result)
    obstruction = verify_one_bus_obstruction(case)
    enclosure = flow_enclosure(candidate, frozen, q(candidate["flat_objective_exact"]))
    corruptions = run_corruption_controls(candidate, frozen, result)
    native_upper = result["result"]["upper"]
    report = {"verdict": "PASS exact ideal depot-15 witness", "candidate_sha256": sha(CANDIDATE.read_bytes()),
            "independent_verifier_sha256": sha(Path(__file__).read_bytes()),
            "frozen_sha256": sha(FROZEN.read_bytes()), "saved_result_sha256": sha(RESULT.read_bytes()),
            "source_commit": PINNED_COMMIT, "manifest_files_verified": len(manifest["files"]),
            "candidate": summary, "one_bus_obstruction": obstruction,
            "ideal_flat_objective_enclosure": enclosure, "corruption_controls": corruptions,
            "separate_prior_native_numerical_upper": native_upper,
            "method": "stdlib JSON/Fraction/hashlib/subprocess only; no optimizer or author checker"}
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
