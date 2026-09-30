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


class RepairStageFailure(ValueError):
    """A rejected proposal with solver telemetry for the fallback receipt."""
    def __init__(self, message, **telemetry):
        super().__init__(message)
        self.telemetry = telemetry


def decode_path_cover(case, logits, *, time_limit_seconds=5.0):
    """Find a binary declared-movement path cover with a vehicle count cap.

    Scores are a proposal objective only. A valid cover says nothing about
    battery, charging, connector, or terminal-energy feasibility.
    """
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import lil_matrix
    nr.validate_case(case)
    if (not nr._finite(time_limit_seconds) or time_limit_seconds <= 0
            or len(logits) != len(case.movements)
            or any(not nr._finite(float(v), -math.inf) for v in logits)):
        raise ValueError("Invalid route logits or time cap")
    started = time.perf_counter()
    n, m = len(case.trips), len(case.movements)
    trip_index = {trip.id:i for i, trip in enumerate(case.trips)}
    matrix = lil_matrix((2*n+1, m), dtype=float)
    for j, movement in enumerate(case.movements):
        if movement.after is not None:
            matrix[trip_index[movement.after], j] = 1
        if movement.before is not None:
            matrix[n+trip_index[movement.before], j] = 1
        if movement.kind == "pullout":
            matrix[2*n, j] = 1
    lower = [1.0]*(2*n)+[-math.inf]
    upper = [1.0]*(2*n)+[float(case.max_vehicles)]
    # SciPy forwards unsupported named options to HiGHS. `threads=1` is a
    # HiGHS option; suppress only SciPy's forwarding notice for that option.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Unrecognized options detected:.*threads",
                                category=RuntimeWarning)
        result = milp(c=[-float(v) for v in logits], integrality=[1]*m,
            bounds=Bounds([0.0]*m, [1.0]*m),
            constraints=LinearConstraint(matrix.tocsr(), lower, upper),
            options={"time_limit":float(time_limit_seconds), "mip_rel_gap":0.0,
                     "threads":1})
    gap, nodes = getattr(result, "mip_gap", None), getattr(result, "mip_node_count", None)
    diagnostics = {"status":int(result.status), "message":str(result.message),
        "mip_gap":float(gap) if gap is not None and math.isfinite(float(gap)) else None,
        "mip_gap_raw":repr(gap),
        "mip_node_count":int(nodes) if nodes is not None else None,
        "wall_seconds":time.perf_counter()-started}
    if result.x is None or any(not math.isfinite(float(v)) or abs(v-round(v)) > 1e-6
                               for v in result.x):
        raise RepairStageFailure("Route cover solver has no integral incumbent",
            cover={**diagnostics, "selected_movements":None, "vehicles":None})
    selected = [movement.id for movement, value in zip(case.movements, result.x)
                if value > 0.5]
    try:
        vehicles, _ = pf.recover_paths(case, selected)
    except ValueError as exc:
        raise RepairStageFailure(f"Route cover recovery failed: {exc}",
            cover={**diagnostics, "selected_movements":selected, "vehicles":None}) from exc
    return {"selected_movements":selected, "vehicles":vehicles, **diagnostics,
        "score":sum(float(v) for v, x in zip(logits, result.x) if x > 0.5),
        "meaning":"legal path cover only; battery and charging not yet checked"}


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


def repair_target(case, market, model, *, budget, path_seconds=5.0, record=None):
    """Return a replayed new fleet, or a typed fallback for the source pool.

    `market` is a native_hull.Market; `model` is a frozen EdgePrior. The caller
    must use an external hard cap around this routine and independently replay
    the returned plan before importing it into a target hull state.
    """
    started = time.perf_counter()
    stage = "input"
    stage_started = started
    result = {"policy":POLICY, "case_identity":case.identity(),
        "market_identity":market.identity(), "repair_status":"fallback",
        "raw_topology":None, "cover":None,
        "charging_subproblem":"fixed-binary native linear program",
        "timing_seconds":{}}
    try:
        if not isinstance(model, lp.EdgePrior):
            raise TypeError("Expected frozen EdgePrior")
        nh.validate_market(case, market)
        stage = "topology"
        stage_started = time.perf_counter()
        raw = model.propose_topology(case, market.a)
        logits = model.logits(case, market.a)
        result["raw_topology"] = list(raw)
        result["timing_seconds"]["topology"] = time.perf_counter()-started
        stage = "cover"
        stage_started = time.perf_counter()
        cover = decode_path_cover(case, logits, time_limit_seconds=path_seconds)
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
