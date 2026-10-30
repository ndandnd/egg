"""Versioned synthetic physical fleet cases with explicit distance/energy assumptions."""
from __future__ import annotations

from dataclasses import asdict
import hashlib

from egglab import native_hull as nh
from egglab import native_recharge as nr

GENERATOR = "physical-fleet-learning-v2-full-factorial"
TRAIN_IDS = tuple(range(10000, 10128))
DEV_IDS = tuple(range(20000, 20032))
TEST_IDS = tuple(range(30000, 30032))
RESERVED_OLD = (2004, 2005, 2020, 2021)
PROFILES = (
    {"name": "control_80", "nameplate_kwh": 100.0,
     "upper_kwh": 100.0, "reserve_kwh": 20.0, "operating_span_kwh": 80.0},
    {"name": "soc20_80_174", "nameplate_kwh": 290.4,
     "upper_kwh": 232.32, "reserve_kwh": 58.08, "operating_span_kwh": 174.24},
    {"name": "soc10_90_232", "nameplate_kwh": 290.4,
     "upper_kwh": 261.36, "reserve_kwh": 29.04, "operating_span_kwh": 232.32},
)
CONSUMPTION_KWH_PER_KM = (1.20, 1.45, 1.70)
SPEED_KMH = 36.0
IDLE_KW = 1.2
# Direct waiting has auxiliary draw; depot dwell is engines-off with zero
# movement energy. Charging losses enter through NativeCase.efficiency.
DEPOT_DWELL_IDLE_KW = 0.0
DEADHEAD_MINUTES = {("D", "A"): 4, ("A", "D"): 4,
                    ("D", "B"): 6, ("B", "D"): 6,
                    ("A", "B"): 8, ("B", "A"): 8}
DEPOT_MIN_GAP = (0, 15, 30)
MARKET_EDGES = tuple(range(0, 1801, 60))


def split_of(base_id):
    if base_id in TRAIN_IDS:
        return "train"
    if base_id in DEV_IDS:
        return "dev"
    if base_id in TEST_IDS:
        return "test"
    raise ValueError("Unregistered physical timetable ID")


def shard_ids(index):
    if not isinstance(index, int) or not 0 <= index < 16:
        raise ValueError("Only sixteen eight-group training shards are declared")
    return TRAIN_IDS[8*index:8*(index+1)]


def assignment(base_id):
    split = split_of(base_id)
    i = base_id - (10000 if split == "train" else 20000 if split == "dev" else 30000)
    # Multiplication by seven permutes all 54 combinations before repeating:
    # 3 SOC profiles × 2 service counts × 3 consumption × 3 depot thresholds.
    j = (7*i) % 54
    profile = PROFILES[j % 3]
    services = 20 if (j // 3) % 2 == 0 else 28
    consumption = CONSUMPTION_KWH_PER_KM[(j // 6) % 3]
    depot_gap = DEPOT_MIN_GAP[(j // 18) % 3]
    stride = 25 if i % 2 == 0 else 30
    return {"base_id": base_id, "split": split, "services": services,
        "profile": dict(profile), "consumption_kwh_per_km": consumption,
        "depot_min_gap_minutes": depot_gap, "duty_start_stride_minutes": stride,
        "speed_kmh": SPEED_KMH, "idle_kw": IDLE_KW,
        "depot_dwell_idle_kw": DEPOT_DWELL_IDLE_KW,
        "resource_grid_kw": 90.0, "resource_bus_kw": 90.0,
        "terminal_open_min": 1080, "deadline_min": 1800,
        "efficiency": .9}


def _draw(base_id, duty, field, count):
    payload = f"{GENERATOR}|{base_id}|{duty}|{field}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % count


def distance_km(minutes):
    return minutes*SPEED_KMH/60


def drive_energy_kwh(minutes, consumption):
    return distance_km(minutes)*consumption


def _travel(origin, destination, consumption):
    minutes = 0 if origin == destination else DEADHEAD_MINUTES[origin, destination]
    return minutes, drive_energy_kwh(minutes, consumption)


def make_case(base_id):
    spec = assignment(base_id)
    n = spec["services"]
    consumption = spec["consumption_kwh_per_km"]
    trips = []
    for duty in range(n//2):
        start = 360 + spec["duty_start_stride_minutes"]*duty + _draw(base_id, duty, "offset", 9)
        first = 20 + _draw(base_id, duty, "first_duration", 12)
        wait = 6 + _draw(base_id, duty, "intertrip_wait", 20)
        second = 20 + _draw(base_id, duty, "second_duration", 12)
        trips.extend((
            nr.Trip(f"T{2*duty+1:02d}", start, start+first, "A", "B",
                    drive_energy_kwh(first, consumption)),
            nr.Trip(f"T{2*duty+2:02d}", start+first+wait,
                    start+first+wait+second, "B", "A",
                    drive_energy_kwh(second, consumption))))
    movements = []
    for trip in trips:
        out, oe = _travel("D", trip.start_place, consumption)
        back, be = _travel(trip.end_place, "D", consumption)
        movements.extend((
            nr.Movement(f"out_{trip.id}", "pullout", None, trip.id,
                (nr.Leg("D", trip.start_place, trip.start_min-out, trip.start_min, oe),)),
            nr.Movement(f"in_{trip.id}", "pullin", trip.id, None,
                (nr.Leg(trip.end_place, "D", trip.end_min, trip.end_min+back, be),))))
    for before in trips:
        for after in trips:
            if before.id == after.id:
                continue
            travel, energy = _travel(before.end_place, after.start_place, consumption)
            arrival = before.end_min + travel
            if arrival <= after.start_min:
                legs = [nr.Leg(before.end_place, after.start_place,
                               before.end_min, arrival, energy)]
                if arrival < after.start_min:
                    legs.append(nr.Leg(after.start_place, after.start_place, arrival,
                                       after.start_min, IDLE_KW*(after.start_min-arrival)/60))
                movements.append(nr.Movement(f"direct_{before.id}_{after.id}",
                    "direct", before.id, after.id, tuple(legs)))
            inbound, ie = _travel(before.end_place, "D", consumption)
            outbound, oe = _travel("D", after.start_place, consumption)
            dwell_start = before.end_min + inbound
            dwell_end = after.start_min - outbound
            if dwell_end-dwell_start >= spec["depot_min_gap_minutes"]:
                movements.append(nr.Movement(f"depot_{before.id}_{after.id}",
                    "depot", before.id, after.id,
                    (nr.Leg(before.end_place, "D", before.end_min, dwell_start, ie),
                     nr.Leg("D", after.start_place, dwell_end, after.start_min, oe)), 1))
    profile = spec["profile"]
    case = nr.NativeCase(
        name=f"physical_v2_s{base_id}_n{n:02d}_{profile['name']}",
        trips=tuple(trips), movements=tuple(movements),
        resources=(nr.Resource(0, 1800, 90.0, 90.0, 1),),
        market_edges_min=MARKET_EDGES, depot="D", max_vehicles=n,
        battery_kwh=profile["upper_kwh"], reserve_kwh=profile["reserve_kwh"],
        terminal_open_min=1080, recharge_deadline_min=1800,
        vehicle_cost=100.0, deadhead_cost_per_min=0.0, efficiency=.9)
    nr.validate_case(case)
    return case


def make_witness(case, base_id):
    """One two-trip vehicle per duty; terminal charging serial on one connector."""
    if case.identity() != make_case(base_id).identity():
        raise ValueError("Witness case differs from versioned physical generator")
    trips = {trip.id: trip for trip in case.trips}
    movements = {movement.id: movement for movement in case.movements}
    vehicles, charges = [], []
    cursor = float(case.terminal_open_min)
    for vehicle in range(len(case.trips)//2):
        first, second = f"T{2*vehicle+1:02d}", f"T{2*vehicle+2:02d}"
        ids = [f"out_{first}", f"direct_{first}_{second}", f"in_{second}"]
        energy = sum(trips[tid].energy_kwh for tid in (first, second)) + sum(
            leg.energy_kwh for mid in ids for leg in movements[mid].legs)
        if case.battery_kwh-energy < case.reserve_kwh:
            raise ValueError("Constructive paired duty breaches operating span")
        release = movements[ids[-1]].legs[-1].arrive_min
        start = max(cursor, float(release), float(case.terminal_open_min))
        grid = energy/case.efficiency
        end = start + grid*60/case.resources[0].grid_kw
        if end > case.recharge_deadline_min:
            raise ValueError("Constructive serial refill misses deadline")
        vehicles.append({"vehicle": vehicle, "trips": [first, second], "movements": ids})
        charges.append({"vehicle": vehicle, "movement": ids[-1], "connector": 0,
                        "start_min": start, "end_min": end, "grid_kwh": grid})
        cursor = end
    load = [0.0]*(len(case.market_edges_min)-1)
    for charge in charges:
        rate = charge["grid_kwh"]*60/(charge["end_min"]-charge["start_min"])
        for period, (left, right) in enumerate(zip(case.market_edges_min,
                                                   case.market_edges_min[1:])):
            overlap = max(0.0, min(charge["end_min"], right)-max(charge["start_min"], left))
            load[period] += rate*overlap/60
    plan = {"schema": nr.SCHEMA, "case_identity": case.identity(),
            "vehicles": vehicles, "charges": charges, "load": load,
            "ops_cost": len(vehicles)*case.vehicle_cost}
    nr.replay_native(case, plan)
    return plan


def market(case, kind):
    if kind == "source0":
        prices = (.20,)*30
    elif kind == "source1":
        prices = tuple(.10 if 18 <= h < 22 else .30 for h in range(30))
    elif kind in ("late", "day", "flat"):
        if kind == "flat":
            prices = (41/150,)*30
        else:
            cheap = range(22, 26) if kind == "late" else range(10, 14)
            prices = tuple(.10 if h in cheap else .30 for h in range(30))
    else:
        raise ValueError("Undeclared physical learning market")
    return nh.Market(case.name + "-" + kind, prices, (1/900,)*30)


def metadata(base_id):
    spec = assignment(base_id)
    case = make_case(base_id)
    witness = make_witness(case, base_id)
    return {"assignment": spec, "case": asdict(case),
            "case_identity": case.identity(), "witness_hash": nr.digest(witness),
            "market_identities": {kind: market(case, kind).identity()
                                  for kind in ("source0", "source1", "late", "day", "flat")}}
