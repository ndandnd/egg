"""Read-only per-route charging-window certificate for energy-aware covers."""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "result/learning_campaign/20260930-stage2-attempt1/frozen.json"
ATTEMPT = ROOT / "result/learning_repair/20260930-energy-aware-attempt1"
OUT = Path(__file__).resolve().parent
CASES = ("learning_s2016_n20", "learning_s2017_n28")
POLICIES = ("cost_only", "cost_learned")


def D(value):
    return Decimal(str(value))


def show(value):
    return format(value, "f")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_identity(case):
    value = {"schema": "egg-native-recharge-v1", "case": case}
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     allow_nan=False).encode()).hexdigest()


def window_grid_capacity(case, start, end):
    """Optimistic one-vehicle capacity, without shared-connector competition."""
    grid = Decimal(0)
    for resource in case["resources"]:
        if resource["connectors"]:
            overlap = max(Decimal(0), min(end, D(resource["end_min"]))
                          - max(start, D(resource["start_min"])))
            grid += overlap / D(60) * min(D(resource["per_bus_kw"]),
                                          D(resource["grid_kw"]))
    return grid


def analyze_route(case, route):
    trips = {trip["id"]: trip for trip in case["trips"]}
    modes = {movement["id"]: movement for movement in case["movements"]}
    B, reserve, eta = (D(case[key]) for key in
                       ("battery_kwh", "reserve_kwh", "efficiency"))
    soc = B
    first = None
    visits = []

    def check(stage, item):
        nonlocal first
        if soc < reserve and first is None:
            first = {"stage": stage, "item": item,
                     "optimistic_soc_kwh": show(soc),
                     "reserve_kwh": show(reserve),
                     "shortfall_kwh": show(reserve-soc)}

    for index, mid in enumerate(route["movements"]):
        mode = modes[mid]
        assert mode["before"] == (route["trips"][index-1] if index else None)
        assert mode["after"] == (route["trips"][index]
                                 if index < len(route["trips"]) else None)
        legs = mode["legs"]
        if mode["kind"] == "depot":
            split = mode["depot_split"]
            assert 0 < split < len(legs)
            inbound = sum((D(leg["energy_kwh"]) for leg in legs[:split]), Decimal(0))
            outbound = sum((D(leg["energy_kwh"]) for leg in legs[split:]), Decimal(0))
            soc -= inbound
            check("depot_arrival", mid)
            start = D(legs[split-1]["arrive_min"])
            end = D(legs[split]["depart_min"])
            grid_cap = window_grid_capacity(case, start, end)
            delivered_cap = eta*grid_cap
            arrival = soc
            soc = min(B, soc+delivered_cap)
            visits.append({"movement": mid, "window_start_min": show(start),
                           "window_end_min": show(end),
                           "grid_cap_kwh": show(grid_cap),
                           "delivered_cap_kwh": show(delivered_cap),
                           "optimistic_arrival_soc_kwh": show(arrival),
                           "optimistic_departure_soc_kwh": show(soc)})
            soc -= outbound
        else:
            soc -= sum((D(leg["energy_kwh"]) for leg in legs), Decimal(0))
        check("movement", mid)
        if mode["after"] is not None:
            soc -= D(trips[mode["after"]]["energy_kwh"])
            check("service", mode["after"])
    terminal = modes[route["movements"][-1]]
    assert terminal["kind"] == "pullin"
    start = max(D(terminal["legs"][-1]["arrive_min"]),
                D(case["terminal_open_min"]))
    end = D(case["recharge_deadline_min"])
    terminal_cap = eta*window_grid_capacity(case, start, end)
    terminal_shortfall = B-soc-terminal_cap
    if terminal_shortfall > 0 and first is None:
        first = {"stage": "terminal_refill", "item": terminal["id"],
                 "optimistic_soc_kwh": show(soc),
                 "reserve_kwh": show(reserve),
                 "shortfall_kwh": show(terminal_shortfall)}
    return {"vehicle": route["vehicle"], "trips": route["trips"],
            "movements": route["movements"], "depot_visits": visits,
            "optimistic_terminal_arrival_soc_kwh": show(soc),
            "terminal_delivered_cap_kwh": show(terminal_cap),
            "first_violation": first, "individually_rejected": first is not None}


def diagnose():
    frozen = json.loads(FROZEN.read_text())
    cells = []
    for name in CASES:
        group = frozen["design"]["groups"][name]
        case = group["case"]
        assert case_identity(case) == group["case_identity"]
        for policy in POLICIES:
            repair_path = ATTEMPT / name / "state0" / policy / "repair.json"
            result = json.loads(repair_path.read_text())["result"]
            cover = result["cover"]
            assert result["case_identity"] == group["case_identity"]
            assert result["cover_policy"] == policy
            assert result["energy_relaxation"] is True
            assert cover["status"] == 0 and cover["mip_gap"] == 0
            assert result["failure"]["stage"] == "charging"
            assert "INFEASIBLE" in result["failure"]["message"]
            assert Counter(t for v in cover["vehicles"] for t in v["trips"]) == Counter(
                [t["id"] for t in case["trips"]])
            assert Counter(m for v in cover["vehicles"] for m in v["movements"]) == Counter(
                cover["selected_movements"])
            routes = [analyze_route(case, route) for route in cover["vehicles"]]
            rejected = sum(route["individually_rejected"] for route in routes)
            assert rejected >= 1
            cells.append({"case": name, "policy": policy,
                          "case_identity": group["case_identity"],
                          "repair_json": str(repair_path.relative_to(ROOT)),
                          "repair_sha256": sha(repair_path),
                          "cover_status": "OPTIMAL",
                          "fixed_charge_status": "INFEASIBLE",
                          "selected_bus_count": len(routes),
                          "individually_rejected_routes": rejected,
                          "cover_independently_rejected": True, "routes": routes})
    return {"schema": "egg-charging-window-certificate-v1",
            "frozen_json": str(FROZEN.relative_to(ROOT)),
            "frozen_sha256": sha(FROZEN),
            "method": "Starting full, sweep each selected route; each depot receives its own exclusive min(per_bus_kw,grid_kw) times window energy at efficiency, capped by battery capacity; check reserve after movement and service and full terminal refill capacity.",
            "arithmetic": "Decimal sums of serialized JSON numeric spellings, not exact binary-rational floats; no optimization",
            "scope": "Necessary per-route bound on four selected covers, ignoring shared-connector competition; no claim about alternative covers or global fleet feasibility",
            "cells": cells}


def markdown(report):
    lines = ["# Charging-window diagnosis of selected energy-aware covers", "",
             "All four energy-aware route covers were optimal in the cover MILP, then the",
             "fixed-route charging LP reported `INFEASIBLE`. A route-by-route upper bound",
             "on delivered charging energy rejects each selected cover even if every bus",
             "gets exclusive access to the charger during each depot visit.", "",
             "| Case | Cover | Individually rejected routes | First witness | Maximum SOC after service | Reserve |",
             "|---|---|---:|---|---:|---:|"]
    for cell in report["cells"]:
        witness = next(route["first_violation"] for route in cell["routes"]
                       if route["first_violation"] is not None)
        soc = D(witness["optimistic_soc_kwh"])
        lines.append(f"| {cell['case']} | {cell['policy']} | "
                     f"{cell['individually_rejected_routes']}/{cell['selected_bus_count']} | "
                     f"{witness['stage']} {witness['item']} | {soc:.2f} | 20.00 |")
    lines.extend(["", "The [JSON certificate](CHARGING_WINDOW_DIAGNOSIS.json) records every",
                  "route, depot window, optimistic charge cap, and first violated reserve",
                  "or terminal refill bound. Table values are rounded for display; the JSON",
                  "keeps sums of serialized source numbers. Reproduce with:", "",
                  "```sh", "python3 research-20260930/learning-campaign/diagnose_charging_windows.py --check", "```", "",
                  "This explains why these four selected covers fail without invoking shared",
                  "charger competition. It does not determine feasibility of other covers or",
                  "the complete fleet problem.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify output without writing")
    args = parser.parse_args()
    report = diagnose()
    outputs = {OUT / "CHARGING_WINDOW_DIAGNOSIS.json":
               json.dumps(report, indent=2, sort_keys=True) + "\n",
               OUT / "CHARGING_WINDOW_DIAGNOSIS.md": markdown(report)}
    for path, content in outputs.items():
        if args.check:
            assert path.read_text() == content, f"Outdated diagnosis: {path}"
        else:
            path.write_text(content)
    print(f"Verified {len(report['cells'])} covers; "
          f"{sum(c['individually_rejected_routes'] for c in report['cells'])} "
          "individual route certificates")


if __name__ == "__main__":
    main()
