"""Scaled development cases for the Claude takeover (E2 time-to-quality profile).

Same construction as ``physical_learning_cases.make_case`` (paired A->B->A duties,
pullout/pullin, direct and depot movements, hourly market edges), with two declared
changes so larger timetables stay feasible under the single-connector model:

* ``services`` (trips) is a free parameter (even, >= 4);
* the one shared connector's power scales with timetable size,
  ``power_kw = 90 * ceil(services / 28)`` (90 kW up to 28 trips, as in the bank).

The native model supports one connector per resource, so a larger fleet gets a
proportionally more powerful (stylized) connector rather than more connectors.
IDs 50000-50999 are development-only and never overlap TRAIN/DEV/TEST ids.
Physical profile, consumption and depot threshold are borrowed from the TRAIN
assignment of ``10000 + (base_id % 128)`` so the regime mix matches the bank.
"""
from __future__ import annotations

import hashlib
import math

from egglab import native_recharge as nr
from egglab import physical_learning_cases as bank

GENERATOR = "claude-scale-v1"
IDS = range(50000, 51000)


def spec(base_id, services):
    if base_id not in IDS:
        raise ValueError("claude-scale ids are 50000-50999")
    if services < 4 or services % 2:
        raise ValueError("services must be even and >= 4")
    borrowed = bank.assignment(10000 + (base_id % 128))
    return {**borrowed, "base_id": base_id, "split": "claude-dev", "services": services,
            "generator": GENERATOR, "power_kw": 90.0*math.ceil(services/28)}


def _draw(base_id, duty, field, count):
    payload = f"{GENERATOR}|{base_id}|{duty}|{field}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % count


def make_case(base_id, services):
    s = spec(base_id, services)
    consumption = s["consumption_kwh_per_km"]
    trips = []
    for duty in range(services//2):
        start = 360 + s["duty_start_stride_minutes"]*duty + _draw(base_id, duty, "offset", 9)
        first = 20 + _draw(base_id, duty, "first_duration", 12)
        wait = 6 + _draw(base_id, duty, "intertrip_wait", 20)
        second = 20 + _draw(base_id, duty, "second_duration", 12)
        trips.extend((
            nr.Trip(f"T{2*duty+1:03d}", start, start+first, "A", "B",
                    bank.drive_energy_kwh(first, consumption)),
            nr.Trip(f"T{2*duty+2:03d}", start+first+wait, start+first+wait+second, "B", "A",
                    bank.drive_energy_kwh(second, consumption))))
    movements = []
    for trip in trips:
        out, oe = bank._travel("D", trip.start_place, consumption)
        back, be = bank._travel(trip.end_place, "D", consumption)
        movements.extend((
            nr.Movement(f"out_{trip.id}", "pullout", None, trip.id,
                        (nr.Leg("D", trip.start_place, trip.start_min-out, trip.start_min, oe),)),
            nr.Movement(f"in_{trip.id}", "pullin", trip.id, None,
                        (nr.Leg(trip.end_place, "D", trip.end_min, trip.end_min+back, be),))))
    for before in trips:
        for after in trips:
            if before.id == after.id:
                continue
            travel, energy = bank._travel(before.end_place, after.start_place, consumption)
            arrival = before.end_min + travel
            if arrival <= after.start_min:
                legs = [nr.Leg(before.end_place, after.start_place, before.end_min, arrival, energy)]
                if arrival < after.start_min:
                    legs.append(nr.Leg(after.start_place, after.start_place, arrival, after.start_min,
                                       bank.IDLE_KW*(after.start_min-arrival)/60))
                movements.append(nr.Movement(f"direct_{before.id}_{after.id}", "direct",
                                             before.id, after.id, tuple(legs)))
            inbound, ie = bank._travel(before.end_place, "D", consumption)
            outbound, oe = bank._travel("D", after.start_place, consumption)
            dwell_start, dwell_end = before.end_min + inbound, after.start_min - outbound
            if dwell_end - dwell_start >= s["depot_min_gap_minutes"]:
                movements.append(nr.Movement(f"depot_{before.id}_{after.id}", "depot",
                    before.id, after.id,
                    (nr.Leg(before.end_place, "D", before.end_min, dwell_start, ie),
                     nr.Leg("D", after.start_place, dwell_end, after.start_min, oe)), 1))
    p = s["profile"]
    case = nr.NativeCase(
        name=f"claude_scale_v1_s{base_id}_n{services:03d}_{p['name']}",
        trips=tuple(trips), movements=tuple(movements),
        resources=(nr.Resource(0, 1800, s["power_kw"], s["power_kw"], 1),),
        market_edges_min=bank.MARKET_EDGES, depot="D", max_vehicles=services,
        battery_kwh=p["upper_kwh"], reserve_kwh=p["reserve_kwh"],
        terminal_open_min=1080, recharge_deadline_min=1800,
        vehicle_cost=100.0, deadhead_cost_per_min=0.0, efficiency=.9)
    nr.validate_case(case)
    return case


def market(case, kind):
    """Same tariffs as the TRAIN bank (source0, source1, late, day, flat)."""
    return bank.market(case, kind)
