"""Isolated complete-fleet model with native recharge and one connector.

A research schema, deliberately separate from Instance/Solution and production
checkpoint/replay policies. Source-resolved directed movement modes define the
opportunity set; this module does not infer missing movements or source data.
No optimizer is initialized on import. See the prospective qualification.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import sys
import time

SCHEMA = "egg-native-recharge-v1"
ENERGY_TOL = 1e-6
TIME_TOL_MIN = 1e-7
BOUND_GUARD = 1e-6
OBJECTIVE_TOL = 1e-6


@dataclass(frozen=True)
class Trip:
    id: str
    start_min: int
    end_min: int
    start_place: str
    end_place: str
    energy_kwh: float


@dataclass(frozen=True)
class Leg:
    origin: str
    destination: str
    depart_min: int
    arrive_min: int
    energy_kwh: float


@dataclass(frozen=True)
class Movement:
    id: str
    kind: str  # pullout, direct, depot, pullin
    before: str | None
    after: str | None
    legs: tuple[Leg, ...]
    depot_split: int | None = None  # recharge gap after this many legs


@dataclass(frozen=True)
class Resource:
    start_min: int
    end_min: int
    per_bus_kw: float
    grid_kw: float
    connectors: int = 1


@dataclass(frozen=True)
class NativeCase:
    name: str
    trips: tuple[Trip, ...]
    movements: tuple[Movement, ...]
    resources: tuple[Resource, ...]
    market_edges_min: tuple[int, ...]
    depot: str
    max_vehicles: int
    battery_kwh: float
    reserve_kwh: float
    terminal_open_min: int
    recharge_deadline_min: int
    vehicle_cost: float
    deadhead_cost_per_min: float = 0.0
    efficiency: float = 1.0
    graph_scope: str = "declared-movement-modes-only"

    def identity(self):
        return digest({"schema": SCHEMA, "case": asdict(self)})


@dataclass(frozen=True)
class Budget:
    backend: str = "CBC"
    threads: int = 1
    phase_seconds: float = 10.0
    wall_seconds: float = 30.0
    max_rounds: int = 48
    epsilon: float = 1e-4


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _finite(value, lower=0.0):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= lower


def _minute(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _window(case, mode):
    if mode.kind == "depot":
        return mode.legs[mode.depot_split-1].arrive_min, mode.legs[mode.depot_split].depart_min
    if mode.kind == "pullin":
        return max(mode.legs[-1].arrive_min, case.terminal_open_min), case.recharge_deadline_min
    return None


def validate_case(case):
    """Validate the complete declared graph; never manufacture a missing leg."""
    if (not case.name or not case.depot or case.graph_scope != "declared-movement-modes-only"
            or not _minute(case.max_vehicles) or case.max_vehicles < 1
            or not _finite(case.battery_kwh) or case.battery_kwh <= 0
            or not _finite(case.reserve_kwh) or case.reserve_kwh >= case.battery_kwh
            or not _finite(case.efficiency) or not 0 < case.efficiency <= 1
            or not _finite(case.vehicle_cost) or not _finite(case.deadhead_cost_per_min)
            or not _minute(case.terminal_open_min) or not _minute(case.recharge_deadline_min)
            or not 0 <= case.terminal_open_min <= case.recharge_deadline_min):
        raise ValueError("Invalid native case policy/physics")
    edges = case.market_edges_min
    if (len(edges) < 2 or any(not _minute(t) for t in edges) or edges[0] != 0
            or edges[-1] != case.recharge_deadline_min
            or any(a >= b for a, b in zip(edges, edges[1:]))):
        raise ValueError("Invalid market-period edges")
    if not case.trips or len({t.id for t in case.trips}) != len(case.trips):
        raise ValueError("Missing or duplicate service trips")
    trips = {t.id: t for t in case.trips}
    for t in case.trips:
        if (not t.id or not t.start_place or not t.end_place
                or not _minute(t.start_min) or not _minute(t.end_min)
                or not 0 <= t.start_min < t.end_min <= case.recharge_deadline_min
                or not _finite(t.energy_kwh)
                or t.energy_kwh > case.battery_kwh-case.reserve_kwh):
            raise ValueError("Invalid individual service physics")
    end = 0
    for r in case.resources:
        if (not _minute(r.start_min) or not _minute(r.end_min) or r.start_min != end
                or r.end_min <= r.start_min or not _finite(r.per_bus_kw) or not _finite(r.grid_kw)
                or not _minute(r.connectors) or r.connectors not in (0, 1)):
            raise ValueError("Resources must cover horizon and use zero/one connector")
        end = r.end_min
    if end != case.recharge_deadline_min:
        raise ValueError("Resource horizon is incomplete")
    if not case.movements or len({m.id for m in case.movements}) != len(case.movements):
        raise ValueError("Missing or duplicate movement modes")
    for m in case.movements:
        if not m.id or m.kind not in ("pullout", "direct", "depot", "pullin") or not m.legs:
            raise ValueError("Malformed movement mode")
        if ((m.kind == "pullout" and (m.before is not None or m.after not in trips))
                or (m.kind == "pullin" and (m.before not in trips or m.after is not None))
                or (m.kind in ("direct", "depot") and
                    (m.before not in trips or m.after not in trips or m.before == m.after))):
            raise ValueError("Movement trip ownership is invalid")
        for leg in m.legs:
            if (not leg.origin or not leg.destination or not _minute(leg.depart_min)
                    or not _minute(leg.arrive_min)
                    or not 0 <= leg.depart_min <= leg.arrive_min <= case.recharge_deadline_min
                    or not _finite(leg.energy_kwh)):
                raise ValueError("Unknown/nonfinite movement time or energy")
        for left, right in zip(m.legs, m.legs[1:]):
            if left.destination != right.origin or left.arrive_min > right.depart_min:
                raise ValueError("Movement legs are not a directed chronological path")
        origin = case.depot if m.before is None else trips[m.before].end_place
        destination = case.depot if m.after is None else trips[m.after].start_place
        earliest = 0 if m.before is None else trips[m.before].end_min
        latest = case.recharge_deadline_min if m.after is None else trips[m.after].start_min
        if (m.legs[0].origin != origin or m.legs[-1].destination != destination
                or m.legs[0].depart_min < earliest or m.legs[-1].arrive_min > latest):
            raise ValueError("Movement direction or service timing is invalid")
        if m.kind == "depot":
            if (not _minute(m.depot_split) or not 1 <= m.depot_split < len(m.legs)
                    or m.legs[m.depot_split-1].destination != case.depot
                    or m.legs[m.depot_split].origin != case.depot):
                raise ValueError("Depot split does not identify a verified depot visit")
        elif m.depot_split is not None:
            raise ValueError("Only depot movements can have a depot split")
    # Path reachability is necessary, not a claim that the full fleet is feasible.
    forward = {m.after for m in case.movements if m.kind == "pullout"}
    backward = {m.before for m in case.movements if m.kind == "pullin"}
    for _ in case.trips:
        forward |= {m.after for m in case.movements if m.before in forward and m.after is not None}
        backward |= {m.before for m in case.movements if m.after in backward and m.before is not None}
    if forward != set(trips) or backward != set(trips):
        raise ValueError("Declared directed graph cannot reach/return from every service")
    return case


def compile_case(case):
    validate_case(case)
    points = set(case.market_edges_min) | {case.terminal_open_min}
    for r in case.resources:
        points.update((r.start_min, r.end_min))
    windows = {m.id: _window(case, m) for m in case.movements if _window(case, m) is not None}
    for w in windows.values():
        points.update(w)
    edges = sorted(points)
    intervals = []
    for lo, hi in zip(edges, edges[1:]):
        r = next(r for r in case.resources if r.start_min <= lo < r.end_min)
        period = next(i for i, (a, b) in enumerate(zip(case.market_edges_min, case.market_edges_min[1:]))
                      if a <= lo < b)
        rate = min(r.per_bus_kw, r.grid_kw) if r.connectors else 0.0
        intervals.append({"start": lo, "end": hi, "hours": (hi-lo)/60,
                          "rate_kw": rate, "period": period,
                          "visits": [mid for mid, (a, b) in windows.items() if a <= lo and hi <= b]})
    return {"identity": case.identity(), "windows": windows, "intervals": intervals,
            "physical_schema": SCHEMA}


def _overlap(a, b, c, d):
    return min(b, d) - max(a, c)


def replay_native(case, plan, prices=None):
    """Independent event replay: no model variables or compiled grid capacities."""
    validate_case(case)
    if plan.get("schema") != SCHEMA or plan.get("case_identity") != case.identity():
        raise ValueError("Plan physical identity mismatch")
    trips, modes = {t.id: t for t in case.trips}, {m.id: m for m in case.movements}
    vehicles = plan.get("vehicles", [])
    if (not 1 <= len(vehicles) <= case.max_vehicles
            or any(not _minute(v.get("vehicle")) for v in vehicles)
            or [v.get("vehicle") for v in vehicles] != list(range(len(vehicles)))):
        raise ValueError("Invalid used-vehicle ownership")
    covered, selected, deltas, blocked = [], {}, {}, {}
    ops = case.vehicle_cost * len(vehicles)
    for v in vehicles:
        vi, seq, ids = v["vehicle"], v["trips"], v["movements"]
        if not seq or len(ids) != len(seq)+1 or any(t not in trips for t in seq) or any(mid not in modes for mid in ids):
            raise ValueError("Malformed nonempty vehicle path")
        expected = [(None, seq[0])] + list(zip(seq, seq[1:])) + [(seq[-1], None)]
        timeline, unavailable = [], []
        for j, (mid, (before, after)) in enumerate(zip(ids, expected)):
            m = modes[mid]
            kinds = ("pullout",) if j == 0 else ("pullin",) if j == len(ids)-1 else ("direct", "depot")
            if m.kind not in kinds or (m.before, m.after) != (before, after):
                raise ValueError("Movement does not belong to its declared vehicle path")
            selected[(vi, mid)] = m
            for leg in m.legs:
                timeline.append((float(leg.arrive_min), -float(leg.energy_kwh), "movement"))
                unavailable.append((leg.depart_min, leg.arrive_min))
                ops += case.deadhead_cost_per_min * (leg.arrive_min-leg.depart_min)
        for tid in seq:
            t = trips[tid]
            timeline.append((float(t.end_min), -float(t.energy_kwh), "service"))
            unavailable.append((t.start_min, t.end_min))
        covered += seq
        deltas[vi], blocked[vi] = timeline, unavailable
    if sorted(covered) != sorted(trips):
        raise ValueError("Mandatory service coverage is not exactly once")
    loads = [0.0] * (len(case.market_edges_min)-1)
    segments = plan.get("charges", [])
    for c in segments:
        vi, mid = c.get("vehicle"), c.get("movement")
        if (not _minute(vi) or (vi, mid) not in selected
                or not _minute(c.get("connector")) or c["connector"] != 0):
            raise ValueError("Charging has invalid vehicle/movement/connector ownership")
        m = selected[(vi, mid)]
        # Re-derive availability here, without the compiler's window dictionary.
        if m.kind == "depot":
            lo, hi = m.legs[m.depot_split-1].arrive_min, m.legs[m.depot_split].depart_min
        elif m.kind == "pullin":
            lo, hi = max(m.legs[-1].arrive_min, case.terminal_open_min), case.recharge_deadline_min
        else:
            raise ValueError("Charging on a noncharging movement")
        start, end, energy = c.get("start_min"), c.get("end_min"), c.get("grid_kwh")
        if (not _finite(start) or not _finite(end) or not _finite(energy) or energy <= 0
                or end <= start or start < lo-TIME_TOL_MIN or end > hi+TIME_TOL_MIN):
            raise ValueError("Charging outside native availability or invalid energy/time")
        if any(_overlap(start, end, a, b) > TIME_TOL_MIN for a, b in blocked[vi]):
            raise ValueError("Charging overlaps its vehicle's service or movement")
        rate = energy * 60/(end-start)
        if not math.isfinite(rate):
            raise ValueError("Nonfinite charging power")
        c_periods = []
        for t, (a, b) in enumerate(zip(case.market_edges_min, case.market_edges_min[1:])):
            overlap = max(0.0, _overlap(start, end, a, b))
            if overlap:
                c_periods.append(t)
                loads[t] += rate*overlap/60
        if abs(sum(max(0.0, _overlap(start, end, a, b)) for a, b in
                       zip(case.market_edges_min, case.market_edges_min[1:])) - (end-start)) > TIME_TOL_MIN:
            raise ValueError("Charging extends beyond modeled market horizon")
        deltas[vi].append((end, case.efficiency*energy, "charge"))
    # Sweep actual sessions, not hourly totals or stored replay flags.
    endpoints = sorted({float(t) for r in case.resources for t in (r.start_min, r.end_min)}
                       | {float(c[t]) for c in segments for t in ("start_min", "end_min")})
    max_grid_kw = 0.0
    for a, b in zip(endpoints, endpoints[1:]):
        if b <= a:
            continue
        # A floating midpoint can round to an endpoint of an adjacent-float
        # session, making a positive-duration charge disappear from the sweep.
        r = next((r for r in case.resources if r.start_min <= a and b <= r.end_min), None)
        active = [c for c in segments if _overlap(a, b, c["start_min"], c["end_min"]) > 0]
        if r is None and active:
            raise ValueError("Charging outside resource horizon")
        if not active:
            continue
        if len(active) > r.connectors or len({c["vehicle"] for c in active}) != len(active):
            raise ValueError("Simultaneous charging exceeds connector/vehicle count")
        rates = [c["grid_kwh"]*60/(c["end_min"]-c["start_min"]) for c in active]
        # Compare energy over this sweep segment, using one fixed energy tolerance.
        if (any(p*(b-a)/60 > r.per_bus_kw*(b-a)/60+ENERGY_TOL for p in rates)
                or sum(rates)*(b-a)/60 > r.grid_kw*(b-a)/60+ENERGY_TOL):
            raise ValueError("Instantaneous individual/shared charging power exceeded")
        max_grid_kw = max(max_grid_kw, sum(rates))
    trajectories, total_consumption = [], 0.0
    for vi, events in deltas.items():
        soc = float(case.battery_kwh)
        trajectory = [{"time_min": 0.0, "soc_kwh": soc, "kind": "initial"}]
        # A session ending exactly when a zero-duration outbound movement
        # begins delivers its energy before that movement consumes energy.
        for at, change, kind in sorted(events, key=lambda e: (e[0], e[2] != "charge")):
            soc += change
            if kind != "charge":
                total_consumption -= change
            if not case.reserve_kwh-ENERGY_TOL <= soc <= case.battery_kwh+ENERGY_TOL:
                raise ValueError("Replayed SOC violates reserve or battery capacity")
            trajectory.append({"time_min": at, "soc_kwh": soc, "kind": kind})
        if abs(soc-case.battery_kwh) > ENERGY_TOL:
            raise ValueError("Used bus did not finish fully replenished")
        trajectories.append(trajectory)
    stored_load = plan.get("load", [])
    if (len(stored_load) != len(loads) or any(not _finite(x) or abs(x-y) > ENERGY_TOL
                                           for x, y in zip(stored_load, loads))
            or not _finite(plan.get("ops_cost")) or abs(plan["ops_cost"]-ops) > ENERGY_TOL):
        raise ValueError("Stored physical load/intrinsic cost does not replay")
    if abs(case.efficiency*sum(loads)-total_consumption) > ENERGY_TOL:
        raise ValueError("Fleet battery/grid energy conservation failed")
    out = {"replay_ok": True, "load": loads, "ops_cost": ops,
           "grid_kwh": sum(loads), "consumption_kwh": total_consumption,
           "max_grid_kw": max_grid_kw, "soc_trajectories": trajectories}
    if prices is not None:
        _check_prices(case, prices)
        out["pricing_objective"] = ops+sum(p*l for p, l in zip(prices, loads))
    return out


def _check_prices(case, prices):
    if len(prices) != len(case.market_edges_min)-1 or any(not _finite(p, -math.inf) for p in prices):
        raise ValueError("Price vector is nonfinite or has wrong dimension")


def _check_market(case, a, b):
    _check_prices(case, a)
    if len(b) != len(a) or any(not _finite(v) for v in b):
        raise ValueError("Supply curvature must be finite and nonnegative")


def true_cost(a, b, load):
    return sum(x*l+0.5*y*l*l for x, y, l in zip(a, b, load))


@lru_cache(maxsize=8)
def _file_sha(path):
    candidate = Path(path)
    return hashlib.sha256(candidate.read_bytes()).hexdigest() if candidate.is_file() else None


def _backend_identity(model, requested):
    actual = str(model.solver_name).upper()
    normalized = "GRB" if actual == "GUROBI" else actual
    module_name = type(model.solver).__module__
    expected_module = "mip.cbc" if requested == "CBC" else "mip.gurobi"
    if normalized != requested or module_name != expected_module:
        raise ValueError("Native backend mismatch/fallback: requested %s, actual %s (%s)" %
                         (requested, actual, module_name))
    module = sys.modules[module_name]
    library = getattr(module, "libfile" if requested == "CBC" else "lib_path", None)
    return {"requested": requested, "model_solver_name": actual, "solver_module": module_name,
            "solver_class": type(model.solver).__name__, "native_library_path": str(library) if library else None,
            "native_library_sha256": _file_sha(str(library)) if library else None}


def build_feasible_model(case, backend="CBC"):
    """Single common feasible set; objective attachment is separate."""
    compiled = compile_case(case)
    if backend not in ("CBC", "GRB"):
        raise ValueError("Explicit CBC/GRB backend required")
    import mip
    model = mip.Model(name="native-recharge-v1", sense=mip.MINIMIZE, solver_name=backend)
    runtime = _backend_identity(model, backend)
    model.verbose = 0
    model.threads = 1
    model.infeas_tol = 1e-8
    model.opt_tol = 1e-8
    n, V, B = len(case.trips), case.max_vehicles, case.battery_kwh
    tripidx = {t.id: i for i, t in enumerate(case.trips)}
    modeidx = {m.id: j for j, m in enumerate(case.movements)}
    used = [model.add_var(var_type=mip.BINARY) for _ in range(V)]
    u = [[model.add_var(var_type=mip.BINARY) for _ in range(n)] for _ in range(V)]
    x = [[model.add_var(var_type=mip.BINARY) for _ in case.movements] for _ in range(V)]
    sb = [[model.add_var(lb=0.0, ub=B) for _ in range(n)] for _ in range(V)]
    sa = [[model.add_var(lb=0.0, ub=B) for _ in range(n)] for _ in range(V)]
    charge = {}
    for v in range(V):
        for k, interval in enumerate(compiled["intervals"]):
            cap = interval["rate_kw"] * interval["hours"]
            for mid in interval["visits"]:
                if cap > 0:
                    charge[(v, modeidx[mid], k)] = model.add_var(lb=0.0, ub=cap)
                    model += charge[(v, modeidx[mid], k)] <= cap*x[v][modeidx[mid]]
            model += mip.xsum(x[v][modeidx[mid]] for mid in interval["visits"]) <= used[v]
    for i in range(n):
        model += mip.xsum(u[v][i] for v in range(V)) == 1
    for v in range(V):
        model += mip.xsum(x[v][j] for j, m in enumerate(case.movements) if m.kind == "pullout") == used[v]
        model += mip.xsum(x[v][j] for j, m in enumerate(case.movements) if m.kind == "pullin") == used[v]
        if v+1 < V:
            model += used[v] >= used[v+1]
        for i, t in enumerate(case.trips):
            model += mip.xsum(x[v][j] for j, m in enumerate(case.movements) if m.after == t.id) == u[v][i]
            model += mip.xsum(x[v][j] for j, m in enumerate(case.movements) if m.before == t.id) == u[v][i]
            model += sb[v][i] <= B*u[v][i]
            model += sa[v][i] <= B*u[v][i]
            model += sb[v][i] >= case.reserve_kwh*u[v][i]
            model += sa[v][i] >= case.reserve_kwh*u[v][i]
            model += sa[v][i] == sb[v][i]-t.energy_kwh*u[v][i]
        for j, m in enumerate(case.movements):
            selected = x[v][j]
            energy = sum(leg.energy_kwh for leg in m.legs)
            M = B+energy  # On inactive modes all owned charging is exactly zero.
            q = mip.xsum(var for (vv, jj, _), var in charge.items() if vv == v and jj == j)
            if m.kind == "pullout":
                residual = sb[v][tripidx[m.after]] - (B-energy)
            elif m.kind == "direct":
                residual = sb[v][tripidx[m.after]] - sa[v][tripidx[m.before]] + energy
            elif m.kind == "depot":
                inbound = sum(leg.energy_kwh for leg in m.legs[:m.depot_split])
                arrival = sa[v][tripidx[m.before]]-inbound
                model += arrival >= case.reserve_kwh-M*(1-selected)
                model += arrival+case.efficiency*q <= B+M*(1-selected)
                residual = sb[v][tripidx[m.after]]-sa[v][tripidx[m.before]]+energy-case.efficiency*q
            else:
                arrival = sa[v][tripidx[m.before]]-energy
                model += arrival >= case.reserve_kwh-M*(1-selected)
                residual = arrival+case.efficiency*q-B
            model += residual <= M*(1-selected)
            model += residual >= -M*(1-selected)
    for k, interval in enumerate(compiled["intervals"]):
        model += mip.xsum(var for (_, _, kk), var in charge.items() if kk == k) <= interval["rate_kw"]*interval["hours"]
    loads = [model.add_var(lb=0.0) for _ in range(len(case.market_edges_min)-1)]
    for t, load in enumerate(loads):
        model += load == mip.xsum(var for (_, _, k), var in charge.items() if compiled["intervals"][k]["period"] == t)
    ops = case.vehicle_cost*mip.xsum(used) + case.deadhead_cost_per_min*mip.xsum(
        x[v][j]*sum(leg.arrive_min-leg.depart_min for leg in m.legs)
        for v in range(V) for j, m in enumerate(case.movements))
    return {"model": model, "compiled": compiled, "used": used, "x": x,
            "charge": charge, "loads": loads, "ops": ops,
            "physical_identity": case.identity(), "backend": backend,
            "backend_runtime": runtime,
            "constraint_count_before_objective": model.num_rows}


def attach_objective(built, kind, payload):
    import mip
    model, loads = built["model"], built["loads"]
    if kind == "linear":
        if len(payload) != len(loads):
            raise ValueError("Wrong linear objective dimension")
        model.objective = built["ops"] + mip.xsum(float(p)*L for p, L in zip(payload, loads))
    elif kind == "tangents":
        if len(payload) != len(loads) or any(not rows for rows in payload):
            raise ValueError("Incomplete tangent objective")
        cost = [model.add_var(lb=-mip.INF) for _ in loads]
        for t, rows in enumerate(payload):
            for slope, intercept in rows:
                if not all(_finite(z, -math.inf) for z in (slope, intercept)):
                    raise ValueError("Nonfinite tangent")
                model += cost[t] >= slope*loads[t]+intercept
        model.objective = built["ops"]+mip.xsum(cost)
    else:
        raise ValueError("Unsupported native objective")


def _optimize_once(built, budget, deadline):
    remaining = deadline-time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Native remaining-time budget exhausted")
    model = built["model"]
    model.threads = budget.threads
    model.max_mip_gap = 1e-9
    model.max_seconds = min(remaining, budget.phase_seconds)
    # No hidden/unbounded LP-first phase. This is one native optimization.
    start = time.perf_counter()
    status = model.optimize(max_seconds=model.max_seconds).name
    raw_incumbent = model.objective_value if model.num_solutions else None
    incumbent = float(raw_incumbent) if raw_incumbent is not None and math.isfinite(float(raw_incumbent)) else None
    try:
        raw_lower = model.objective_bound
        lower = float(raw_lower) if raw_lower is not None and math.isfinite(float(raw_lower)) else None
    except (TypeError, ValueError):
        raw_lower = None
        lower = None
    return {"status": status, "incumbent": incumbent, "lower_bound": lower,
            "raw_incumbent_repr": repr(raw_incumbent), "raw_lower_bound_repr": repr(raw_lower),
            "wall_s": time.perf_counter()-start, "seconds_cap": model.max_seconds,
            "threads": model.threads, "backend": built["backend"],
            "backend_runtime": built["backend_runtime"],
            "n_vars": model.num_cols, "n_int": model.num_int, "n_constraints": model.num_rows,
            "physical_constraints": built["constraint_count_before_objective"]}


def decode_serial(case, compiled, energies):
    """Materialize one-connector sessions instead of assuming average power."""
    charges = []
    for k, interval in enumerate(compiled["intervals"]):
        cursor, rate = float(interval["start"]), interval["rate_kw"]
        rows = sorted((v, mid, e) for (v, mid, kk), e in energies.items() if kk == k and e != 0)
        if any(not _finite(e) for _, _, e in rows):
            raise ValueError("Negative/nonfinite extracted native charge")
        for v, mid, energy in rows:
            if mid not in interval["visits"] or rate <= 0:
                raise ValueError("Charge has no available interval/resource")
            end = cursor + energy*60/rate
            if end > interval["end"]+TIME_TOL_MIN:
                raise ValueError("Serial connector decoding exceeds interval")
            charges.append({"vehicle": v, "movement": mid, "connector": 0,
                            "start_min": cursor, "end_min": end, "grid_kwh": float(energy)})
            cursor = end
    if any(k not in range(len(compiled["intervals"])) for (_, _, k) in energies):
        raise ValueError("Charge references an unknown elementary interval")
    return charges


def _extract(case, built):
    def value(var):
        if var.x is None or not math.isfinite(float(var.x)):
            raise ValueError("Missing/nonfinite native variable")
        return float(var.x)
    vehicles, map_v, used_modes = [], {}, set()
    for v, used in enumerate(built["used"]):
        if value(used) <= 0.5:
            continue
        ids = {m.id: m for j, m in enumerate(case.movements) if value(built["x"][v][j]) > 0.5}
        starts = [m for m in ids.values() if m.kind == "pullout"]
        if len(starts) != 1:
            raise ValueError("Native extraction has invalid pull-out")
        m, seq, path = starts[0], [], []
        while True:
            if m.id in path:
                raise ValueError("Native extraction contains a cycle")
            path.append(m.id)
            if m.after is None:
                break
            seq.append(m.after)
            successors = [m2 for m2 in ids.values() if m2.before == m.after]
            if len(successors) != 1:
                raise ValueError("Native extraction has branching/incomplete path")
            m = successors[0]
        if set(path) != set(ids):
            raise ValueError("Disconnected selected movement")
        map_v[v] = len(vehicles)
        used_modes |= {(v, mid) for mid in ids}
        vehicles.append({"vehicle": len(vehicles), "trips": seq, "movements": path})
    energies = {}
    for (v, j, k), var in built["charge"].items():
        amount = value(var)
        if amount != 0:
            mid = case.movements[j].id
            if v not in map_v or (v, mid) not in used_modes:
                raise ValueError("Charging on an unused vehicle or mode")
            energies[(map_v[v], mid, k)] = amount
    charges = decode_serial(case, built["compiled"], energies)
    loads = [0.0] * (len(case.market_edges_min)-1)
    for (_, _, k), amount in energies.items():
        loads[built["compiled"]["intervals"][k]["period"]] += amount
    raw_load = [value(var) for var in built["loads"]]
    if any(abs(a-b) > ENERGY_TOL for a, b in zip(raw_load, loads)):
        raise ValueError("Raw native aggregate disagrees with physical charge")
    modes = {m.id: m for m in case.movements}
    ops = len(vehicles)*case.vehicle_cost + case.deadhead_cost_per_min*sum(
        leg.arrive_min-leg.depart_min for v in vehicles for mid in v["movements"] for leg in modes[mid].legs)
    plan = {"schema": SCHEMA, "case_identity": case.identity(), "vehicles": vehicles,
            "charges": charges, "load": loads, "ops_cost": ops, "raw_solver_load": raw_load}
    plan["replay"] = replay_native(case, plan)
    return plan


def admit_bound(stats, feasible_upper, incumbent_objective=None, allow_epigraph_slack=False):
    """Status is preserved; a time-limit incumbent is not called optimal."""
    if stats.get("status") not in ("OPTIMAL", "FEASIBLE"):
        raise ValueError("Native solve has no admissible incumbent status")
    lower = stats.get("lower_bound")
    incumbent = stats.get("incumbent")
    expected = feasible_upper if incumbent_objective is None else incumbent_objective
    if (not _finite(lower, -math.inf) or not _finite(feasible_upper, -math.inf)
            or not _finite(incumbent, -math.inf) or not _finite(expected, -math.inf)
            or lower > incumbent+BOUND_GUARD or lower > expected+BOUND_GUARD
            or expected > feasible_upper+BOUND_GUARD):
        raise ValueError("Native global bound/incumbent is absent/nonfinite/reversed")
    if (incumbent < expected-OBJECTIVE_TOL if allow_epigraph_slack
            else abs(incumbent-expected) > OBJECTIVE_TOL):
        raise ValueError("Native incumbent does not match independently evaluated objective")
    return float(lower)-BOUND_GUARD, float(feasible_upper)+BOUND_GUARD


def _check_budget(budget):
    if (budget.backend not in ("CBC", "GRB") or not _minute(budget.threads) or budget.threads != 1
            or not _finite(budget.phase_seconds) or budget.phase_seconds <= 0
            or not _finite(budget.wall_seconds) or budget.wall_seconds <= 0
            or not _minute(budget.max_rounds) or budget.max_rounds < 1
            or not _finite(budget.epsilon) or budget.epsilon <= 2*BOUND_GUARD):
        raise ValueError("Unsupported/unbounded research budget")


def solve_pricing(case, prices, budget=Budget(), record=None):
    _check_prices(case, prices)
    _check_budget(budget)
    deadline = time.monotonic()+budget.wall_seconds
    built = build_feasible_model(case, budget.backend)
    attach_objective(built, "linear", prices)
    if record:
        record({"event": "native_start", "round": 0})
    stats = _optimize_once(built, budget, deadline)
    if record:
        record({"event": "native_status", "round": 0, "stats": stats})
    result = {"case_identity": case.identity(), "objective": "complete-fleet-linear",
              "prices": list(prices), "stats": stats, "status": "unresolved"}
    if stats["status"] == "INFEASIBLE":
        return {**result, "status": "infeasible"}
    if stats["status"] not in ("OPTIMAL", "FEASIBLE") or stats.get("incumbent") is None:
        return result
    plan = _extract(case, built)
    replay = replay_native(case, plan, prices)
    lower, upper = admit_bound(stats, replay["pricing_objective"])
    result.update(plan=plan, lower=lower, upper=upper, gap=upper-lower,
                  status="certified" if upper-lower <= budget.epsilon else "bounded")
    return result


def solve_planner(case, a, b, budget=Budget(), record=None):
    _check_market(case, a, b)
    _check_budget(budget)
    deadline = time.monotonic()+budget.wall_seconds
    tangents = [[(float(aa), 0.0)] for aa in a]
    lower, upper, best, records = -math.inf, math.inf, None, []
    status = "unresolved"
    for _ in range(budget.max_rounds):
        if time.monotonic() >= deadline:
            break
        built = build_feasible_model(case, budget.backend)
        attach_objective(built, "tangents", tangents)
        snapshot = [[list(p) for p in rows] for rows in tangents]
        if record:
            record({"event": "native_start", "round": len(records), "tangents": snapshot})
        stats = _optimize_once(built, budget, deadline)
        if record:
            record({"event": "native_status", "round": len(records), "stats": stats})
        iteration = {"stats": stats, "tangents": snapshot}
        records.append(iteration)
        if stats["status"] == "INFEASIBLE":
            if best is not None:
                raise ValueError("Tangent model infeasible after a replay-valid native plan")
            return {"case_identity": case.identity(), "status": "infeasible", "rounds": records}
        if stats["status"] not in ("OPTIMAL", "FEASIBLE") or stats.get("incumbent") is None:
            break
        plan = _extract(case, built)
        true = plan["ops_cost"]+true_cost(a, b, plan["load"])
        envelope = plan["ops_cost"]+sum(max(slope*load+intercept for slope, intercept in rows)
                                        for load, rows in zip(plan["load"], snapshot))
        lo, hi = admit_bound(stats, true, envelope, allow_epigraph_slack=True)
        iteration["replayed_tangent_objective"] = envelope
        iteration["native_epigraph_slack"] = stats["incumbent"]-envelope
        iteration.update(plan=plan, lower=lo, upper=hi)
        if record:
            record({"event": "replayed_iteration", "round": len(records)-1, **iteration})
        lower = max(lower, lo)
        if hi < upper:
            upper, best = hi, plan
        if lower > upper+BOUND_GUARD:
            raise ValueError("Planner enclosure reversed")
        status = "bounded"
        if upper-lower <= budget.epsilon:
            status = "certified"
            break
        for t, load in enumerate(plan["load"]):
            tangents[t].append((float(a[t]+b[t]*load), float(-0.5*b[t]*load*load)))
    result = {"case_identity": case.identity(), "status": status, "a": list(a), "b": list(b), "rounds": records}
    if best is not None:
        result.update(plan=best, lower=lower, upper=upper, gap=upper-lower)
    return result
