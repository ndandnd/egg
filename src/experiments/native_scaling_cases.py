"""Five deterministic DEVELOPMENT NativeCases with full terminal replenishment.

This is a pure input generator. It never allocates a MIP or calls a solver.
The 15-seed reservation and public timetable split live outside this module.
"""
from __future__ import annotations

from collections import Counter
import hashlib

from egglab import native_recharge as nr

CELLS = ((1006, 8), (1006, 16), (1006, 24), (1012, 16), (1009, 16))
GENERATOR_VERSION = "egg-nativecase-scaling-development-v1"
TERMINAL_OPEN_MIN = 1080
DEADLINE_MIN = 1800
LOW_WINDOW_MIN = (1080, 1320)


def _draw(seed: int, duty: int, field: str, count: int) -> int:
    payload = f"{GENERATOR_VERSION}|{seed}|{duty}|{field}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % count


def _name(seed: int, services: int) -> str:
    return f"native_scale_dev_s{seed}_n{services:02d}"


def _travel(origin: str, destination: str) -> tuple[int, float]:
    minutes = {("D", "A"): 4, ("A", "D"): 4,
               ("D", "B"): 6, ("B", "D"): 6,
               ("A", "B"): 8, ("B", "A"): 8}
    duration = 0 if origin == destination else minutes[origin, destination]
    return duration, duration * 0.25


def make_case(seed: int, services: int) -> nr.NativeCase:
    """Construct only a prespecified development cell."""
    if (seed, services) not in CELLS:
        raise ValueError("Cell is outside the five reserved development inputs")
    trips = []
    for duty in range(services // 2):
        start = 360 + 25*duty + _draw(seed, duty, "offset", 9)
        first_duration = 18 + _draw(seed, duty, "duration_ab", 15)
        wait = 5 + _draw(seed, duty, "wait_b", 26)
        second_duration = 18 + _draw(seed, duty, "duration_ba", 15)
        first_energy = 18 + _draw(seed, duty, "energy_ab", 1001) / 100
        second_energy = 18 + _draw(seed, duty, "energy_ba", 1001) / 100
        trips.extend((
            nr.Trip(f"T{2*duty+1:02d}", start, start+first_duration,
                    "A", "B", first_energy),
            nr.Trip(f"T{2*duty+2:02d}", start+first_duration+wait,
                    start+first_duration+wait+second_duration,
                    "B", "A", second_energy),
        ))
    movements = []
    for trip in trips:
        out_minutes, out_energy = _travel("D", trip.start_place)
        in_minutes, in_energy = _travel(trip.end_place, "D")
        movements.append(nr.Movement(
            f"out_{trip.id}", "pullout", None, trip.id,
            (nr.Leg("D", trip.start_place, trip.start_min-out_minutes,
                    trip.start_min, out_energy),)))
        movements.append(nr.Movement(
            f"in_{trip.id}", "pullin", trip.id, None,
            (nr.Leg(trip.end_place, "D", trip.end_min,
                    trip.end_min+in_minutes, in_energy),)))
    for before in trips:
        for after in trips:
            if before.id == after.id:
                continue
            travel_min, travel_energy = _travel(before.end_place, after.start_place)
            arrival = before.end_min + travel_min
            if arrival <= after.start_min:
                legs = [nr.Leg(before.end_place, after.start_place,
                               before.end_min, arrival, travel_energy)]
                if arrival < after.start_min:
                    legs.append(nr.Leg(after.start_place, after.start_place,
                                       arrival, after.start_min,
                                       (after.start_min-arrival)*0.01))
                movements.append(nr.Movement(f"direct_{before.id}_{after.id}",
                                             "direct", before.id, after.id,
                                             tuple(legs)))
            inbound_min, inbound_energy = _travel(before.end_place, "D")
            outbound_min, outbound_energy = _travel("D", after.start_place)
            depot_arrival = before.end_min + inbound_min
            depot_departure = after.start_min - outbound_min
            if depot_arrival <= depot_departure:
                movements.append(nr.Movement(
                    f"depot_{before.id}_{after.id}", "depot", before.id,
                    after.id,
                    (nr.Leg(before.end_place, "D", before.end_min,
                            depot_arrival, inbound_energy),
                     nr.Leg("D", after.start_place, depot_departure,
                            after.start_min, outbound_energy)), 1))
    case = nr.NativeCase(
        name=_name(seed, services), trips=tuple(trips), movements=tuple(movements),
        resources=(nr.Resource(0, DEADLINE_MIN, 90.0, 90.0, 1),),
        market_edges_min=tuple(range(0, DEADLINE_MIN+1, 60)),
        depot="D", max_vehicles=services, battery_kwh=100.0,
        reserve_kwh=20.0, terminal_open_min=TERMINAL_OPEN_MIN,
        recharge_deadline_min=DEADLINE_MIN, vehicle_cost=100.0,
        deadhead_cost_per_min=0.0, efficiency=0.9,
    )
    nr.validate_case(case)
    return case


def cases() -> dict[str, nr.NativeCase]:
    """The frozen five development inputs, keyed by stable case name."""
    return {_name(seed, n): make_case(seed, n) for seed, n in CELLS}


def make_witness(case: nr.NativeCase) -> dict:
    """One two-service duty per bus; serial 90 kW terminal charging."""
    if case.name not in {_name(seed, n) for seed, n in CELLS}:
        raise ValueError("Witness construction is limited to reserved cells")
    modes = {m.id: m for m in case.movements}
    trips = {t.id: t for t in case.trips}
    vehicles, charges = [], []
    cursor = float(case.terminal_open_min)
    for vehicle in range(len(case.trips)//2):
        first, second = f"T{2*vehicle+1:02d}", f"T{2*vehicle+2:02d}"
        ids = [f"out_{first}", f"direct_{first}_{second}", f"in_{second}"]
        energy = sum(trips[tid].energy_kwh for tid in (first, second)) + sum(
            leg.energy_kwh for mid in ids for leg in modes[mid].legs)
        if energy > 60.5 or case.battery_kwh-energy < case.reserve_kwh:
            raise ValueError("Constructed paired duty breaches the prescribed energy bound")
        release = modes[ids[-1]].legs[-1].arrive_min
        start = max(cursor, float(release), float(case.terminal_open_min))
        grid_kwh = energy / case.efficiency
        end = start + grid_kwh*60/case.resources[0].grid_kw
        if end > case.recharge_deadline_min:
            raise ValueError("Constructed serial full-charge witness misses deadline")
        vehicles.append({"vehicle": vehicle, "trips": [first, second],
                         "movements": ids})
        charges.append({"vehicle": vehicle, "movement": ids[-1],
                        "connector": 0, "start_min": start, "end_min": end,
                        "grid_kwh": grid_kwh})
        cursor = end
    load = [0.0] * (len(case.market_edges_min)-1)
    for charge in charges:
        rate = charge["grid_kwh"]*60/(charge["end_min"]-charge["start_min"])
        for period, (lo, hi) in enumerate(zip(case.market_edges_min,
                                               case.market_edges_min[1:])):
            overlap = max(0.0, min(charge["end_min"], hi)
                          - max(charge["start_min"], lo))
            load[period] += rate*overlap/60
    plan = {"schema": nr.SCHEMA, "case_identity": case.identity(),
            "vehicles": vehicles, "charges": charges, "load": load,
            "ops_cost": len(vehicles)*case.vehicle_cost}
    nr.replay_native(case, plan)
    return plan


def witnesses() -> dict[str, dict]:
    """Replayed, complete-fleet paired-duty plans for all five cases."""
    return {name: make_witness(case) for name, case in cases().items()}


def tariffs() -> dict[str, dict[str, tuple[float, ...]]]:
    """Flat, source, and shifted-target price-only inputs for each case."""
    prices = {"flat": (0.20,)*30,
              "source_low": tuple(0.10 if 18 <= hour < 22 else 0.30
                                  for hour in range(30)),
              "target_low": tuple(0.10 if 22 <= hour < 26 else 0.30
                                  for hour in range(30))}
    return {name: prices.copy() for name in cases()}


def movement_counts(case: nr.NativeCase) -> dict[str, int]:
    return dict(Counter(m.kind for m in case.movements))


def compact_dimensions(case: nr.NativeCase, compiled: dict) -> dict[str, int]:
    """Count current compact path-flow variables/rows; allocate no MIP."""
    counts = movement_counts(case)
    services, modes = len(case.trips), len(case.movements)
    intervals = compiled["intervals"]
    charge = sum(len(interval["visits"]) for interval in intervals
                 if interval["rate_kw"] > 0)
    periods = len(case.market_edges_min)-1
    return {
        "movement_binary_variables": modes,
        "service_soc_continuous_variables": 2*services,
        "charge_interval_continuous_variables": charge,
        "market_load_continuous_variables": periods,
        "total_variables_before_objective": modes+2*services+charge+periods,
        "estimated_constraints_before_objective": (
            2+3*services+charge+len(intervals)+2*modes
            +2*counts.get("depot", 0)+counts.get("pullin", 0)+2+periods),
        "compiled_resource_intervals": len(intervals),
    }
