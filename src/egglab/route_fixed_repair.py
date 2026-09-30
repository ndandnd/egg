"""Developmental route cover plus bounded fixed-route charging repair.

The route decoder is a small SciPy MILP. Once all movement binaries are fixed,
the native charging/SOC subproblem has only continuous decisions and a linear
tariff objective: mathematically an LP, executed by the existing MIP backend.
No full plan is admitted without independent continuous-time physical replay.
This module is inert on import and supplies no global optimality certificate.
"""
from __future__ import annotations

import math
import time
import warnings
from fractions import Fraction

from egglab import learned_proposals as lp
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr

POLICY = "route-cover-fixed-charge-repair-v1"
COVER_POLICIES = ("score_only", "cost_only", "cost_learned")


class RepairStageFailure(ValueError):
    """A rejected proposal with solver telemetry for the fallback receipt."""
    def __init__(self, message, **telemetry):
        super().__init__(message)
        self.telemetry = telemetry


def _energy_relaxation_rows(case, compiled, charging_caps=False):
    """Necessary route-energy rows; column order is movements, then post-trip SOC."""
    if not isinstance(charging_caps, bool):
        raise ValueError("charging_caps must be a boolean")
    m = len(case.movements)
    trip_index = {trip.id:i for i,trip in enumerate(case.trips)}
    charge_caps = {}
    for interval in compiled["intervals"]:
        cap = interval["rate_kw"]*interval["hours"]*case.efficiency
        if cap > 0:
            for mid in interval["visits"]:
                charge_caps[mid] = charge_caps.get(mid, 0.0)+cap
    positive_visits = set(charge_caps)
    B, reserve = case.battery_kwh, case.reserve_kwh
    rows = []
    def add(coefficients, lo=-math.inf, hi=math.inf):
        rows.append((coefficients, lo, hi))
    for j, movement in enumerate(case.movements):
        energy = sum(leg.energy_kwh for leg in movement.legs)
        before = (m+trip_index[movement.before]
                  if movement.before is not None else None)
        after = (m+trip_index[movement.after]
                 if movement.after is not None else None)
        service = (case.trips[trip_index[movement.after]].energy_kwh
                   if after is not None else 0.0)
        # Every inactive implication is redundant over SOC bounds.
        big_m = B+energy+service
        if movement.kind == "pullout":
            # s_after <= B - pullout energy - service energy.
            add({after:1.0, j:big_m}, hi=B-energy-service+big_m)
        elif movement.kind == "pullin":
            # Arrive at the depot with reserve before terminal charging.
            add({before:1.0, j:-big_m}, lo=reserve+energy-big_m)
            if charging_caps:
                # Terminal full refill requires enough energy in this window.
                add({before:1.0, j:-big_m},
                    lo=B+energy-charge_caps.get(movement.id, 0.0)-big_m)
        elif movement.kind == "depot" and movement.id in positive_visits:
            inbound = sum(leg.energy_kwh for leg in movement.legs[:movement.depot_split])
            outbound = energy-inbound
            # Optimistic full reset; arrival must still reach the depot.
            add({before:1.0, j:-big_m}, lo=reserve+inbound-big_m)
            add({after:1.0, j:big_m}, hi=B-outbound-service+big_m)
            if charging_caps:
                # The actual SOC gain cannot exceed this visit's delivered cap.
                add({after:1.0, before:-1.0, j:big_m},
                    hi=charge_caps[movement.id]-energy-service+big_m)
        else:
            # Direct, or a depot visit at which charging is impossible.
            add({after:1.0, before:-1.0, j:big_m},
                hi=-energy-service+big_m)
    return rows


def decode_path_cover(case, logits=None, *, time_limit_seconds=5.0,
                      cover_policy="score_only", energy_relaxation=False,
                      charging_caps=False):
    """Find a binary declared-movement path cover with a vehicle count cap.

    ``score_only`` preserves the original logit objective. ``cost_only``
    minimizes pullouts without logits. ``cost_learned`` adds a logit term whose
    change across covers is at most 1/4, so one bus dominates at an exact optimum.
    The cost modes require positive vehicle cost and zero deadhead cost.
    With ``energy_relaxation=True``, continuous post-trip SOC variables impose
    necessary route-energy bounds. Depot departures may reset optimistically to
    full only when their frozen charging window has positive available capacity.
    ``charging_caps`` additionally bounds energy from each depot and terminal
    window. Shared connector scheduling and physical replay remain unchecked.
    """
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import lil_matrix
    nr.validate_case(case)
    if cover_policy not in COVER_POLICIES:
        raise ValueError("Unknown cover policy")
    if not isinstance(energy_relaxation, bool):
        raise ValueError("energy_relaxation must be a boolean")
    if not isinstance(charging_caps, bool) or (charging_caps and not energy_relaxation):
        raise ValueError("charging_caps requires energy_relaxation=True and a boolean flag")
    if not nr._finite(time_limit_seconds) or time_limit_seconds <= 0:
        raise ValueError("Invalid route time cap")
    if cover_policy in ("cost_only", "cost_learned") and (
            case.vehicle_cost <= 0 or case.deadhead_cost_per_min != 0):
        raise ValueError("Pullout count is not the declared positive operating cost")
    if cover_policy == "cost_only":
        values = None  # Deliberately no model or logit access.
        scale = 0.0
    else:
        if logits is None or len(logits) != len(case.movements):
            raise ValueError("Invalid route logits")
        values = [float(v) for v in logits]
        if any(not nr._finite(v, -math.inf) for v in values):
            raise ValueError("Invalid route logits")
        magnitude = sum(abs(v) for v in values)
        if not math.isfinite(magnitude):
            raise ValueError("Route logit magnitude overflows")
        scale = (0.25/max(1.0,magnitude) if cover_policy == "cost_learned" else 1.0)
    started = time.perf_counter()
    n, m = len(case.trips), len(case.movements)
    trip_index = {trip.id:i for i, trip in enumerate(case.trips)}
    rows = []
    def add(coefficients, lo=-math.inf, hi=math.inf):
        rows.append((coefficients, lo, hi))
    for trip in case.trips:
        add({j:1.0 for j,movement in enumerate(case.movements)
             if movement.after == trip.id}, 1.0, 1.0)
    for trip in case.trips:
        add({j:1.0 for j,movement in enumerate(case.movements)
             if movement.before == trip.id}, 1.0, 1.0)
    add({j:1.0 for j,movement in enumerate(case.movements)
         if movement.kind == "pullout"}, hi=float(case.max_vehicles))
    if energy_relaxation:
        rows.extend(_energy_relaxation_rows(case, nr.compile_case(case), charging_caps))
    matrix = lil_matrix((len(rows), m+(n if energy_relaxation else 0)), dtype=float)
    lower, upper = [], []
    for row, (coefficients, lo, hi) in enumerate(rows):
        for col, coefficient in coefficients.items():
            matrix[row, col] = coefficient
        lower.append(lo)
        upper.append(hi)
    if cover_policy == "score_only":
        objective = [-v for v in values]
    elif cover_policy == "cost_only":
        objective = [float(m.kind == "pullout") for m in case.movements]
    else:
        objective = [float(m.kind == "pullout")-scale*v
                     for m,v in zip(case.movements,values)]
    if energy_relaxation:
        objective += [0.0]*n
    # SciPy forwards these named options to HiGHS. Thread count and seed are
    # explicit; suppress only SciPy's forwarding notice in this scope.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Unrecognized options detected:",
                                category=RuntimeWarning)
        result = milp(c=objective, integrality=[1]*m+[0]*n if energy_relaxation else [1]*m,
            bounds=Bounds([0.0]*m+[case.reserve_kwh]*n if energy_relaxation else [0.0]*m,
                          [1.0]*m+[case.battery_kwh-trip.energy_kwh for trip in case.trips]
                          if energy_relaxation else [1.0]*m),
            constraints=LinearConstraint(matrix.tocsr(), lower, upper),
            options={"time_limit":float(time_limit_seconds), "mip_rel_gap":0.0,
                     "threads":1, "random_seed":0})
    gap, nodes = getattr(result, "mip_gap", None), getattr(result, "mip_node_count", None)
    diagnostics = {"status":int(result.status), "message":str(result.message),
        "mip_gap":float(gap) if gap is not None and math.isfinite(float(gap)) else None,
        "mip_gap_raw":repr(gap),
        "mip_node_count":int(nodes) if nodes is not None else None,
        "wall_seconds":time.perf_counter()-started,
        "objective_policy":cover_policy, "logit_scale":scale,
        "random_seed":0, "threads":1}
    if (result.x is None or len(result.x) != m+(n if energy_relaxation else 0)
            or any(not math.isfinite(float(v)) for v in result.x)
            or any(abs(v-round(v)) > 1e-6 for v in result.x[:m])
            or getattr(result, "fun", None) is None
            or not math.isfinite(float(result.fun))):
        raise RepairStageFailure("Route cover solver has no integral incumbent",
            cover={**diagnostics, "selected_movements":None, "vehicles":None})
    selected = [movement.id for movement, value in zip(case.movements, result.x[:m])
                if value > 0.5]
    try:
        vehicles, _ = pf.recover_paths(case, selected)
    except ValueError as exc:
        raise RepairStageFailure(f"Route cover recovery failed: {exc}",
            cover={**diagnostics, "selected_movements":selected, "vehicles":None}) from exc
    cover = {"selected_movements":selected, "vehicles":vehicles, **diagnostics,
        "pullout_count":sum(case.movements[j].kind == "pullout"
                            for j,x in enumerate(result.x[:m]) if x > 0.5),
        "score":(sum(v for v,x in zip(values,result.x) if x > 0.5)
                 if values is not None else None),
        "cover_objective":float(result.fun),
        "native_minimum_bus_count_reported":bool(result.status == 0 and
            cover_policy in ("cost_only", "cost_learned") and not energy_relaxation),
        "minimum_bus_count_scope":("declared energy-relaxed route covers with per-visit charging caps; shared charging omitted"
            if charging_caps else "declared energy-relaxed route covers; optimistic depot resets"
            if energy_relaxation else "declared structural route covers, ignoring charging"),
        "meaning":("legal path cover satisfying necessary energy bounds; charging schedule and physical replay not yet checked"
            if energy_relaxation else "legal path cover only; battery and charging not yet checked")}
    if energy_relaxation:
        cover.update(energy_relaxation=True,
            energy_relaxation_scope=("post-trip SOC and per-visit delivered charging upper bounds including terminal refill; shared connector competition omitted"
                if charging_caps else "post-trip SOC, no-charge propagation, reserve on depot/terminal arrival; optimistic full reset only at positive-capacity depot window; shared connector and terminal refill omitted"),
            relaxation_minimum_bus_count_reported=bool(result.status == 0 and
                cover_policy in ("cost_only", "cost_learned")),
            soc_after_trip_witness_kwh={trip.id:float(result.x[m+i])
                                        for i,trip in enumerate(case.trips)})
    if charging_caps:
        cover.update(charging_caps=True,
            charging_cap_scope="per-visit min(per_bus_kw, grid_kw) times available hours times efficiency; no shared connector scheduling")
    return cover


def _solve_fixed_charge(case, market, selected, budget, record=None):
    """Bounded native fixed-binary charging LP under target linear tariff a."""
    nr._check_budget(budget)
    nh.validate_market(case, market)
    expected = set(selected)
    pf.recover_paths(case, selected)
    deadline = time.monotonic()+budget.wall_seconds
    built = pf.build_feasible_model(case, budget.backend)
    if time.monotonic() >= deadline:
        raise TimeoutError("Fixed-route model build exhausted charge wall cap")
    if len(built["x"]) != len(case.movements):
        raise ValueError("Fixed-route movement mapping differs from case")
    for movement, var in zip(case.movements, built["x"]):
        if var.var_type != "B":
            raise ValueError("Unexpected nonbinary movement variable")
        fixed = int(movement.id in expected)
        var.lb = fixed
        var.ub = fixed
    pf.attach_objective(built, "linear", market.a)
    if time.monotonic() >= deadline:
        raise TimeoutError("Fixed-route objective setup exhausted charge wall cap")
    if record:
        record({"event":"fixed_route_native_start", "policy":POLICY,
            "case_identity":case.identity(), "movement_count":len(case.movements),
            "selected_count":len(expected), "backend":budget.backend,
            "mathematical_subproblem":"LP with all movement binaries fixed",
            "tariff":"market.a only; true curved bill evaluated after replay"})
    stats = pf._optimize_once(built, budget, deadline)
    if record:
        record({"event":"fixed_route_native_status", "stats":stats})
    if stats["status"] not in ("OPTIMAL", "FEASIBLE") or stats.get("incumbent") is None:
        raise RepairStageFailure(
            f"Fixed-route charging has no native incumbent: {stats['status']}",
            native_stats=stats)
    if time.monotonic() >= deadline:
        raise RepairStageFailure("Fixed-route solve exhausted charge wall cap before extraction",
            native_stats=stats)
    try:
        plan = pf._extract(case, built, record=record)
        actual = {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]}
        if actual != expected:
            raise ValueError("Extracted route differs from fixed movement choices")
        replay = nr.replay_native(case, plan)
        if replay.get("replay_ok") is not True:
            raise ValueError("Fixed-route plan did not pass independent replay")
    except Exception as exc:
        raise RepairStageFailure(f"Fixed-route extraction/replay failed: {exc}",
            native_stats=stats, cause_type=type(exc).__name__) from exc
    return plan, replay, stats


def repair_target(case, market, model=None, *, budget, path_seconds=5.0,
                  cover_policy="score_only", energy_relaxation=False,
                  charging_caps=False, record=None):
    """Return a replayed new fleet, or a typed fallback for the source pool.

    `market` is a native_hull.Market; `model` is a frozen EdgePrior, except that
    `cost_only` accepts None and performs no inference. The caller
    must use an external hard cap around this routine and independently replay
    the returned plan before importing it into a target hull state.
    """
    started = time.perf_counter()
    stage = "input"
    stage_started = started
    result = {"policy":POLICY, "case_identity":case.identity(),
        "market_identity":market.identity(), "repair_status":"fallback",
        "cover_policy":cover_policy, "energy_relaxation":energy_relaxation,
        "charging_caps":charging_caps,
        "raw_topology":None, "cover":None,
        "inference_attempted":False, "inference_performed":False,
        "charging_subproblem":"fixed-binary native linear program",
        "timing_seconds":{}}
    try:
        if cover_policy not in COVER_POLICIES:
            raise ValueError("Unknown cover policy")
        nh.validate_market(case, market)
        if cover_policy == "cost_only":
            logits = None
            result["timing_seconds"]["topology"] = 0.0
        else:
            if not isinstance(model, lp.EdgePrior):
                raise TypeError("Expected frozen EdgePrior")
            stage = "topology"
            stage_started = time.perf_counter()
            result["inference_attempted"] = True
            raw = model.propose_topology(case, market.a)
            logits = model.logits(case, market.a)
            result["raw_topology"] = list(raw)
            result["inference_performed"] = True
            result["timing_seconds"]["topology"] = time.perf_counter()-started
        stage = "cover"
        stage_started = time.perf_counter()
        cover = decode_path_cover(case, logits, time_limit_seconds=path_seconds,
            cover_policy=cover_policy, energy_relaxation=energy_relaxation,
            charging_caps=charging_caps)
        result["cover"] = cover
        result["timing_seconds"]["cover"] = time.perf_counter()-started-result["timing_seconds"]["topology"]
        stage = "charging"
        stage_started = time.perf_counter()
        plan, replay, stats = _solve_fixed_charge(case, market,
            cover["selected_movements"], budget, record=record)
        result["timing_seconds"]["charging_and_replay"] = (
            time.perf_counter()-started-sum(result["timing_seconds"].values()))
        exact_cost = Fraction(replay["ops_cost"])+nh.supply(market,replay["load"])
        result.update(repair_status="replayed", plan=plan, replay=replay,
            native_stats=stats, true_cost=float(exact_cost),
            true_cost_exact=str(exact_cost))
    except Exception as exc:
        timing_key = "charging_and_replay" if stage == "charging" else stage
        result["timing_seconds"].setdefault(timing_key,
            time.perf_counter()-stage_started)
        result["failure"] = {"stage":stage, "type":type(exc).__name__,
            "message":str(exc)}
        if isinstance(exc, RepairStageFailure):
            for key in ("cover", "native_stats"):
                if key in exc.telemetry:
                    result[key] = exc.telemetry[key]
            if "cause_type" in exc.telemetry:
                result["failure"]["cause_type"] = exc.telemetry["cause_type"]
    result["timing_seconds"]["total"] = time.perf_counter()-started
    return result
