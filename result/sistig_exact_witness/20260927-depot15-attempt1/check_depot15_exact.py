#!/usr/bin/env python3
"""Exact stored-number replay of one fixed two-bus depot-15 flat witness.

Standard library only. No optimizer, search over routes, or time rescheduling.
`--build` creates one prospective candidate; default mode checks that candidate
from frozen input and the archived numerical witness.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ARCHIVE_REL = Path("result/sistig_pricing/20260927-grb-job557543-attempt1")
FROZEN_SHA = "35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b"
RESULT_SHA = "d5a767d738a02db7e68481d1995549f19bd7089fdc758d8ec28cd2a64166cc85"
CASE_ID = "1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7"
FROZEN_SOURCE = "282e00b80b6fd9457006429b089269b2a9e2be92"
CANDIDATE = HERE / "depot15_exact_candidate.json"


def need(ok, message):
    if not ok:
        raise AssertionError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fraction(value):
    need(type(value) in (int, float, str), "Non-numeric stored value")
    return Q(value)


def overlap(a, b, c, d):
    return max(Q(0), min(b, d) - max(a, c))


def read_source(repo=REPO):
    archive = Path(repo) / ARCHIVE_REL
    frozen_raw = (archive / "frozen.json").read_bytes()
    result_raw = (archive / "depot_15_flat/result.json").read_bytes()
    need(digest(frozen_raw) == FROZEN_SHA and digest(result_raw) == RESULT_SHA,
         "Pinned archive changed")
    frozen, package = json.loads(frozen_raw), json.loads(result_raw)
    need(frozen["freeze_label"] == FROZEN_SOURCE, "Archived source commit changed")
    control = next(x for x in frozen["controls"] if x["id"] == "depot_15_flat")
    case, result = control["case"], package["result"]
    identity = digest(json.dumps({"schema": "egg-native-recharge-v1", "case": case},
                                 sort_keys=True, allow_nan=False).encode())
    need(identity == CASE_ID == control["case_identity"] == result["case_identity"]
         == result["plan"]["case_identity"], "Case identity changed")
    need(len(case["trips"]) == 37 and len(result["plan"]["vehicles"]) == 2
         and len(result["plan"]["charges"]) == 19, "Not the fixed 37-service two-bus witness")
    return case, result


def route_consumption(case, routes):
    trips = {t["id"]: t for t in case["trips"]}
    modes = {m["id"]: m for m in case["movements"]}
    need([v["vehicle"] for v in routes] == [0, 1], "Vehicle numbering changed")
    covered = []
    consumption, blocked, selected = {}, {}, {}
    for vehicle in routes:
        vi, sequence, mids = vehicle["vehicle"], vehicle["trips"], vehicle["movements"]
        need(sequence and len(mids) == len(sequence) + 1, "Malformed route")
        expected = [(None, sequence[0])] + list(zip(sequence, sequence[1:])) + [(sequence[-1], None)]
        intervals, total = [], Q(0)
        for mid, pair in zip(mids, expected):
            need(mid in modes, "Unknown route movement")
            mode = modes[mid]
            need((mode["before"], mode["after"]) == pair, "Movement route adjacency changed")
            selected[(vi, mid)] = mode
            kind = "pullout" if pair[0] is None else "pullin" if pair[1] is None else None
            need(mode["kind"] == kind if kind else mode["kind"] in ("direct", "depot"),
                 "Movement kind changed")
            previous = None
            for leg in mode["legs"]:
                start, end = fraction(leg["depart_min"]), fraction(leg["arrive_min"])
                need(0 <= start <= end <= fraction(case["recharge_deadline_min"]),
                     "Movement leg time outside horizon")
                if previous is not None:
                    need(previous <= start, "Movement legs reverse time")
                previous = end
                intervals.append((start, end))
                energy = fraction(leg["energy_kwh"])
                need(energy >= 0, "Negative movement energy")
                total += energy
            if pair[0] is not None:
                need(fraction(trips[pair[0]]["end_min"]) <= fraction(mode["legs"][0]["depart_min"]),
                     "Movement departs before prior service ends")
            if pair[1] is not None:
                need(fraction(mode["legs"][-1]["arrive_min"]) <= fraction(trips[pair[1]]["start_min"]),
                     "Movement arrives after next service starts")
        for tid in sequence:
            need(tid in trips, "Unknown route service")
            trip = trips[tid]
            start, end = fraction(trip["start_min"]), fraction(trip["end_min"])
            need(0 <= start < end <= fraction(case["recharge_deadline_min"]),
                 "Service time outside horizon")
            intervals.append((start, end))
            energy = fraction(trip["energy_kwh"])
            need(energy >= 0, "Negative service energy")
            total += energy
        covered += sequence
        consumption[vi], blocked[vi] = total, intervals
    need(sorted(covered) == sorted(trips), "Mandatory services not covered exactly once")
    return consumption, blocked, selected, trips, modes


def saved_timing_and_repair(case, result):
    plan = result["plan"]
    consumption, _, selected, _, _ = route_consumption(case, plan["vehicles"])
    eta = fraction(case["efficiency"])
    sessions = []
    for index, original in enumerate(plan["charges"]):
        vi, mid = original["vehicle"], original["movement"]
        need((vi, mid) in selected and original["connector"] == 0,
             "Saved charge ownership changed")
        sessions.append({"index": index, "vehicle": vi, "movement": mid, "connector": 0,
                         "start_min": str(fraction(original["start_min"])),
                         "end_min": str(fraction(original["end_min"])),
                         "grid_kwh": str(fraction(original["grid_kwh"]))})
    repairs = []
    for vi in (0, 1):
        own = [s for s in sessions if s["vehicle"] == vi]
        last = max(own, key=lambda s: (fraction(s["end_min"]), s["index"]))
        need(selected[(vi, last["movement"])]["kind"] == "pullin",
             "Last charge is not terminal")
        previous = fraction(last["grid_kwh"])
        excess = eta * sum((fraction(s["grid_kwh"]) for s in own), Q(0)) - consumption[vi]
        need(0 < excess < Q(1, 10**6), "Repair is not a tiny positive terminal excess")
        updated = previous - excess / eta
        need(updated > 0, "Terminal repair removes the session")
        last["grid_kwh"] = str(updated)
        repairs.append({"vehicle": vi, "session_index": last["index"],
                        "removed_grid_kwh": str(excess / eta),
                        "original_grid_kwh": str(previous), "repaired_grid_kwh": str(updated)})
    need([r["session_index"] for r in repairs] == [18, 16],
         "Unexpected terminal session selection")
    return sessions, repairs


def exact_replay(case, result, sessions, repairs):
    plan = result["plan"]
    routes = plan["vehicles"]
    consumption, blocked, selected, trips, modes = route_consumption(case, routes)
    need(len(sessions) == len(plan["charges"]) == 19, "Session count changed")
    repair_ids = {r["session_index"] for r in repairs}
    need(repair_ids == {16, 18}, "Unexpected repair positions")
    resources = case["resources"]
    need(len(resources) == 1 and resources[0]["connectors"] == 1,
         "This checker covers the declared one-connector resource only")
    resource = resources[0]
    horizon = (fraction(resource["start_min"]), fraction(resource["end_min"]))
    per_bus, shared = fraction(resource["per_bus_kw"]), fraction(resource["grid_kw"])
    eta, battery, reserve = map(fraction, (case["efficiency"], case["battery_kwh"], case["reserve_kwh"]))
    market_edges = list(map(fraction, case["market_edges_min"]))
    need(len(market_edges) == 31 and market_edges[0] == horizon[0]
         and market_edges[-1] == horizon[1], "Market/resource horizon changed")
    charge_intervals, charge_by_bus = [], {0: Q(0), 1: Q(0)}
    loads = [Q(0)] * 30
    for index, (saved, session) in enumerate(zip(plan["charges"], sessions)):
        need(session["index"] == index and session["vehicle"] == saved["vehicle"]
             and session["movement"] == saved["movement"]
             and session["connector"] == saved["connector"] == 0
             and fraction(session["start_min"]) == fraction(saved["start_min"])
             and fraction(session["end_min"]) == fraction(saved["end_min"]),
             "Discrete charge assignment or saved timing changed")
        vi, mid = session["vehicle"], session["movement"]
        energy = fraction(session["grid_kwh"])
        need(energy > 0, "Nonpositive charge energy")
        if index not in repair_ids:
            need(energy == fraction(saved["grid_kwh"]), "Nonterminal charge energy changed")
        start, end = fraction(session["start_min"]), fraction(session["end_min"])
        need(start < end, "Zero-duration charge")
        mode = selected[(vi, mid)]
        if mode["kind"] == "depot":
            split = mode["depot_split"]
            lo = fraction(mode["legs"][split-1]["arrive_min"])
            hi = fraction(mode["legs"][split]["depart_min"])
        else:
            need(mode["kind"] == "pullin", "Charge on a noncharging movement")
            lo = max(fraction(mode["legs"][-1]["arrive_min"]),
                     fraction(case["terminal_open_min"]))
            hi = fraction(case["recharge_deadline_min"])
        need(horizon[0] <= lo <= start < end <= hi <= horizon[1],
             "Charge outside exact availability window")
        need(all(overlap(start, end, a, b) == 0 for a, b in blocked[vi]),
             "Charge overlaps service or movement")
        power = energy * 60 / (end-start)
        need(power <= per_bus and power <= shared, "Charge power exceeds exact cap")
        charge_intervals.append((start, end, index))
        charge_by_bus[vi] += energy
        need(sum((overlap(start, end, a, b) for a, b in zip(market_edges, market_edges[1:])), Q(0))
             == end-start, "Charge not covered by market periods")
        for t, (a, b) in enumerate(zip(market_edges, market_edges[1:])):
            loads[t] += power * overlap(start, end, a, b) / 60
    for (_, previous_end, _), (next_start, _, _) in zip(sorted(charge_intervals),
                                                         sorted(charge_intervals)[1:]):
        need(previous_end <= next_start, "One connector has overlapping sessions")
    need(all(eta * charge_by_bus[vi] == consumption[vi] for vi in (0, 1)),
         "Bus battery/grid energy is not exactly conserved")
    trajectories = []
    for vehicle in routes:
        vi = vehicle["vehicle"]
        events = []
        serial = 0
        for mid in vehicle["movements"]:
            for leg_index, leg in enumerate(modes[mid]["legs"]):
                events.append((fraction(leg["arrive_min"]), 1, serial,
                               "movement", f"{mid}:leg:{leg_index}",
                               -fraction(leg["energy_kwh"])))
                serial += 1
        for tid in vehicle["trips"]:
            trip = trips[tid]
            events.append((fraction(trip["end_min"]), 1, serial,
                           "service", tid, -fraction(trip["energy_kwh"])))
            serial += 1
        for session in sessions:
            if session["vehicle"] == vi:
                events.append((fraction(session["end_min"]), 0, serial,
                               "charge", str(session["index"]),
                               eta * fraction(session["grid_kwh"])))
                serial += 1
        soc = battery
        rows = [{"time_min": "0", "kind": "initial", "source": "battery",
                 "energy_change_kwh": "0", "soc_after_kwh": str(soc)}]
        for at, _, _, kind, source, delta in sorted(events):
            soc += delta
            need(reserve <= soc <= battery, f"Exact SOC capacity/reserve violation on bus {vi}")
            rows.append({"time_min": str(at), "kind": kind, "source": source,
                         "energy_change_kwh": str(delta), "soc_after_kwh": str(soc)})
        need(soc == battery, f"Bus {vi} is not exactly full at terminal")
        trajectories.append({"vehicle": vi, "consumption_kwh": str(consumption[vi]),
                             "grid_kwh": str(charge_by_bus[vi]), "soc_events": rows})
    need(sum(loads, Q(0)) == sum(charge_by_bus.values(), Q(0)),
         "Exact hourly grid load does not conserve charge")
    prices = list(map(fraction, result["prices"]))
    need(len(prices) == 30 and len(set(prices)) == 1, "Not the saved flat price")
    ops = fraction(case["vehicle_cost"]) * len(routes) + fraction(case["deadhead_cost_per_min"]) * sum(
        (fraction(leg["arrive_min"]) - fraction(leg["depart_min"])
         for vehicle in routes for mid in vehicle["movements"] for leg in modes[mid]["legs"]), Q(0))
    return {"classification": "Exact ideal stored-input physical candidate; independent review pending",
            "source_frozen_sha256": FROZEN_SHA, "source_result_sha256": RESULT_SHA,
            "case_identity": CASE_ID, "source_commit": FROZEN_SOURCE,
            "routes": routes, "sessions": sessions, "repairs": repairs,
            "vehicles": trajectories, "hourly_grid_kwh": [str(x) for x in loads],
            "total_grid_kwh": str(sum(loads, Q(0))), "ops_cost_exact": str(ops),
            "flat_objective_exact": str(ops + sum((p*x for p, x in zip(prices, loads)), Q(0))),
            "terminal_deadline_min": str(fraction(case["recharge_deadline_min"]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO,
                        help="repository root containing the pinned archived pilot")
    parser.add_argument("--build", action="store_true", help="write the exclusive candidate once")
    args = parser.parse_args()
    case, result = read_source(args.repo.resolve())
    sessions, repairs = saved_timing_and_repair(case, result)
    expected = exact_replay(case, result, sessions, repairs)
    if args.build:
        with CANDIDATE.open("x", encoding="utf-8") as out:
            json.dump(expected, out, indent=2, sort_keys=True)
            out.write("\n")
    candidate = json.loads(CANDIDATE.read_text())
    need(candidate == expected, "Saved rational candidate differs from exact reconstruction")
    print(json.dumps({"candidate_sha256": digest(CANDIDATE.read_bytes()),
                      "used_buses": len(candidate["vehicles"]),
                      "sessions": len(candidate["sessions"]),
                      "soc_events": sum(len(v["soc_events"]) for v in candidate["vehicles"]),
                      "hourly_periods": len(candidate["hourly_grid_kwh"]),
                      "exact_replay": "PASS", "independent_review_pending": True},
                     sort_keys=True))


if __name__ == "__main__":
    main()
