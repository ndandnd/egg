"""Read-only certificate for the four selected cost-aware repair covers.

No optimization is run. All arithmetic below uses the decimal spellings of the
frozen JSON numbers, so the certificate is reproducible from the two compact
source files named in each result cell.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "result/learning_campaign/20260930-stage2-attempt1/frozen.json"
ATTEMPT = ROOT / "result/learning_repair/20260930-cost-aware-attempt1"
OUT = Path(__file__).resolve().parent
CASES = ("learning_s2016_n20", "learning_s2017_n28")
POLICIES = ("cost_only", "cost_learned")


def number(value):
    return Decimal(str(value))


def decimal_text(value):
    return format(value, "f")


def digest_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(case):
    payload = {"schema": "egg-native-recharge-v1", "case": case}
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                     allow_nan=False).encode()).hexdigest()


def analyze_vehicle(vehicle, trips, movements, usable):
    ids = vehicle["trips"]
    mids = vehicle["movements"]
    assert len(mids) == len(ids) + 1
    assert movements[mids[0]]["kind"] == "pullout"
    assert movements[mids[-1]]["kind"] == "pullin"
    segments = []
    segment = None

    def new_segment(start):
        return {"from": start, "trips": [], "movements": [],
                "service_kwh": Decimal(0), "movement_kwh": Decimal(0)}

    def finish(end):
        nonlocal segment
        assert segment is not None
        consumption = segment.pop("service_kwh") + segment.pop("movement_kwh")
        service = sum((number(trips[t]["energy_kwh"]) for t in segment["trips"]), Decimal(0))
        movement = consumption - service
        segment.update({"to": end, "service_kwh": decimal_text(service),
                        "movement_kwh": decimal_text(movement),
                        "consumption_kwh": decimal_text(consumption),
                        "usable_battery_kwh": decimal_text(usable),
                        "excess_kwh": decimal_text(consumption - usable),
                        "violates_necessary_bound": consumption > usable})
        segments.append(segment)
        segment = None

    for index, mid in enumerate(mids):
        mode = movements[mid]
        expected_before = ids[index - 1] if index else None
        expected_after = ids[index] if index < len(ids) else None
        assert mode["before"] == expected_before and mode["after"] == expected_after
        if mode["kind"] == "pullout":
            assert index == 0 and segment is None
            segment = new_segment("initial_full_battery")
        else:
            assert segment is not None
        if mode["kind"] == "depot":
            split = mode["depot_split"]
            assert isinstance(split, int) and 0 < split < len(mode["legs"])
            segment["movements"].append(mid + ":inbound")
            segment["movement_kwh"] += sum(
                (number(leg["energy_kwh"]) for leg in mode["legs"][:split]), Decimal(0))
            finish("depot_arrival:" + mid)
            segment = new_segment("depot_departure:" + mid)
            segment["movements"].append(mid + ":outbound")
            segment["movement_kwh"] += sum(
                (number(leg["energy_kwh"]) for leg in mode["legs"][split:]), Decimal(0))
        else:
            segment["movements"].append(mid)
            segment["movement_kwh"] += sum(
                (number(leg["energy_kwh"]) for leg in mode["legs"]), Decimal(0))
        if expected_after is not None:
            assert mode["kind"] in ("pullout", "direct", "depot")
            segment["trips"].append(expected_after)
            segment["service_kwh"] += number(trips[expected_after]["energy_kwh"])
        else:
            finish("terminal_arrival_before_pullin_charge")
    return {"vehicle": vehicle["vehicle"], "route_trips": ids,
            "route_movements": mids, "segments": segments,
            "has_violating_segment": any(s["violates_necessary_bound"] for s in segments)}


def diagnosis():
    frozen = json.loads(FROZEN.read_text())
    cells = []
    for case_name in CASES:
        group = frozen["design"]["groups"][case_name]
        case = group["case"]
        assert identity(case) == group["case_identity"]
        trips = {t["id"]: t for t in case["trips"]}
        movements = {m["id"]: m for m in case["movements"]}
        usable = number(case["battery_kwh"]) - number(case["reserve_kwh"])
        for policy in POLICIES:
            repair_path = ATTEMPT / case_name / "state0" / policy / "repair.json"
            result = json.loads(repair_path.read_text())["result"]
            cover = result["cover"]
            assert result["case_identity"] == group["case_identity"]
            assert result["cover_policy"] == policy
            assert result["failure"]["stage"] == "charging"
            assert "INFEASIBLE" in result["failure"]["message"]
            assert cover["pullout_count"] == len(cover["vehicles"])
            all_trips = [t for v in cover["vehicles"] for t in v["trips"]]
            all_movements = [m for v in cover["vehicles"] for m in v["movements"]]
            assert Counter(all_trips) == Counter(list(trips))
            assert Counter(all_movements) == Counter(cover["selected_movements"])
            vehicles = [analyze_vehicle(v, trips, movements, usable)
                        for v in cover["vehicles"]]
            assert all(v["has_violating_segment"] for v in vehicles)
            cells.append({"case": case_name, "policy": policy,
                          "repair_json": str(repair_path.relative_to(ROOT)),
                          "repair_sha256": digest_file(repair_path),
                          "case_identity": group["case_identity"],
                          "reported_native_status": "INFEASIBLE",
                          "selected_bus_count": len(vehicles),
                          "battery_kwh": decimal_text(number(case["battery_kwh"])),
                          "reserve_kwh": decimal_text(number(case["reserve_kwh"])),
                          "usable_battery_kwh": decimal_text(usable),
                          "vehicles": vehicles,
                          "all_selected_routes_have_certificate": True})
    return {"schema": "egg-selected-cover-energy-certificate-v1",
            "frozen_json": str(FROZEN.relative_to(ROOT)),
            "frozen_sha256": digest_file(FROZEN),
            "bound": "Between charging opportunities, movement plus service energy must be <= battery_kwh - reserve_kwh; a depot departure is optimistically allowed a full battery.",
            "arithmetic": "Decimal sums of serialized JSON numeric spellings, not exact binary-rational float values; no rounding or optimization",
            "scope": "Only the four selected fixed path covers; no conclusion about any alternative cover or global fleet feasibility",
            "cells": cells}


def markdown(report):
    lines = ["# Selected-cover energy feasibility diagnosis", "",
             "Each selected route violates a necessary battery bound. Between charging opportunities,",
             "service plus movement energy cannot exceed battery capacity minus reserve,",
             "which is **80 kWh** in both frozen cases. I allow a full battery at every depot",
             "departure, making this check optimistic about charging time, grid power, and",
             "connector availability. Pull-in charging starts only after the final movement,",
             "so it cannot repair an earlier deficit.", "",
             "| Case | Cover | Bus | Violating segment | Energy (kWh) | Excess over 80 (kWh) |",
             "|---|---|---:|---|---:|---:|"]
    for cell in report["cells"]:
        for vehicle in cell["vehicles"]:
            for segment in vehicle["segments"]:
                if not segment["violates_necessary_bound"]:
                    continue
                label = "initial→terminal" if segment["from"] == "initial_full_battery" else "depot departure→terminal"
                energy = number(segment["consumption_kwh"])
                excess = number(segment["excess_kwh"])
                lines.append(f"| {cell['case']} | {cell['policy']} | {vehicle['vehicle']} | {label} | "
                             f"{energy:.2f} | {excess:.2f} |")
    lines.extend(["", "The [JSON certificate](ENERGY_FEASIBILITY_DIAGNOSIS.json) lists each route's",
                  "trip and movement IDs, splits at depot visits, component energy sums,",
                  "source hashes, and case identities. The table displays two decimal places;",
                  "the JSON keeps sums of the serialized numeric spellings. Recompute it with:", "",
                  "```sh", "python3 research-20260930/learning-campaign/diagnose_energy_feasibility.py --check", "```", "",
                  "The native fixed-charge LP reported `INFEASIBLE` for all four selected covers.",
                  "These route-level violations independently explain infeasibility of those",
                  "particular covers. They do not prove that the complete fleet problem or its",
                  "minimum-bus-count family is infeasible; other structural covers may differ.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify committed outputs without writing")
    args = parser.parse_args()
    report = diagnosis()
    outputs = {OUT / "ENERGY_FEASIBILITY_DIAGNOSIS.json":
               json.dumps(report, indent=2, sort_keys=True) + "\n",
               OUT / "ENERGY_FEASIBILITY_DIAGNOSIS.md": markdown(report)}
    for path, content in outputs.items():
        if args.check:
            assert path.read_text() == content, f"Outdated diagnosis: {path}"
        else:
            path.write_text(content)
    print(f"Verified {len(report['cells'])} covers, "
          f"{sum(len(c['vehicles']) for c in report['cells'])} violating routes")


if __name__ == "__main__":
    main()
