"""Isolated complete-fleet hull certificates; no native optimizer on import.

Exact arithmetic here concerns stored finite numbers and reconstructed simplex
weights. Physical witnesses and native global bounds remain tolerance-conditional.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from fractions import Fraction as Q
import math
import time

from egglab import native_recharge as nr

SCHEMA = "egg-native-hull-v2"
MASS_TOL = 1e-10
OBJECTIVE_TOL = 1e-6
DEFAULT_PRICING_ORACLE = "egg-native-recharge.solve_pricing-v1"


@dataclass(frozen=True)
class Market:
    name: str
    a: tuple[float, ...]
    b: tuple[float, ...]

    def identity(self):
        return nr.digest(asdict(self))


@dataclass(frozen=True)
class Budget:
    backend: str = "CBC"
    threads: int = 1
    phase_seconds: float = 10.0
    wall_seconds: float = 60.0
    pricing_calls: int = 16
    master_calls: int = 64
    pool_cap: int = 48
    epsilon: float = 1e-4
    pool_tolerance: float = 1e-6
    polish_steps: int = 256
    rational_bits: int = 8192
    polish_seconds: float = 5.0


class LimitReached(RuntimeError):
    pass


class PoolStalled(RuntimeError):
    pass


class ProposalFailed(RuntimeError):
    pass


def rational(value):
    if isinstance(value, Q):
        return value
    if not nr._finite(value, -math.inf):
        raise ValueError("Nonfinite or nonnumeric scalar")
    return Q.from_float(float(value))


def outward(value, up):
    value = Q(value)
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Unrepresentable finite result")
    if (Q.from_float(number) < value if up else Q.from_float(number) > value):
        number = math.nextafter(number, math.inf if up else -math.inf)
    if not math.isfinite(number):
        raise ValueError("Outward result is not finite")
    return number


def emit(record, event):
    if record:
        record(copy.deepcopy(event))


def validate_market(case, market):
    nr._check_market(case, market.a, market.b)
    if not isinstance(market.name, str) or not market.name:
        raise ValueError("Market identity requires a name")


def validate_budget(budget):
    if (budget.backend not in ("CBC", "GRB") or type(budget.threads) is not int or budget.threads != 1
            or any(type(x) is not int or x < 1 for x in (budget.pricing_calls, budget.master_calls, budget.pool_cap,
                                                       budget.polish_steps, budget.rational_bits))
            or any(not nr._finite(x) or x <= 0 for x in (budget.phase_seconds, budget.wall_seconds,
                                                        budget.epsilon, budget.pool_tolerance, budget.polish_seconds))
            or budget.epsilon <= 2*nr.BOUND_GUARD or budget.pool_tolerance >= budget.epsilon):
        raise ValueError("Invalid bounded native hull policy")


def supply(market, loads):
    if len(loads) != len(market.a):
        raise ValueError("Wrong supply dimension")
    return sum((rational(a)*rational(x)+rational(b)*rational(x)**2/2
                for a, b, x in zip(market.a, market.b, loads)), Q(0))


def conjugate(market, prices):
    if len(prices) != len(market.a):
        raise ValueError("Wrong conjugate dimension")
    total = Q(0)
    for p, a, b in zip(prices, market.a, market.b):
        excess, curvature = rational(p)-rational(a), rational(b)
        if curvature < 0:
            raise ValueError("Negative curvature")
        if excess <= 0:
            continue
        if curvature == 0:
            return None  # +infinity, explicitly outside finite dual domain.
        total += excess*excess/(2*curvature)
    return total


def projection_key(load, ops):
    return nr.digest({"schema": SCHEMA, "load": [float(x+0.0).hex() for x in load],
                      "ops_cost": float(ops+0.0).hex()})


def _extraction_policy(value):
    if value is None:
        return nr.EXTRACTION_POLICY
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError("Explicit extraction policy requires a nonempty identity")
    return value


def native_column(case, plan, source, extraction_policy=None):
    policy = _extraction_policy(extraction_policy)
    saved_policy = plan.get("extraction_policy")
    if ((extraction_policy is not None and saved_policy != policy)
            or (extraction_policy is None and saved_policy not in (None, policy))):
        raise ValueError("Native plan extraction policy mismatch")
    witness = copy.deepcopy(plan)
    replay = nr.replay_native(case, witness)
    load, ops = replay["load"], replay["ops_cost"]
    return {"schema": SCHEMA, "physical_identity": case.identity(),
            "extraction_policy": policy, "plan": witness,
            "witness_hash": nr.digest(witness), "source": copy.deepcopy(source),
            "load": load, "ops_cost": ops, "key": projection_key(load, ops)}


def replay_column(case, column, extraction_policy=None):
    policy = _extraction_policy(extraction_policy)
    if (column.get("schema") != SCHEMA or column.get("physical_identity") != case.identity()
            or column.get("extraction_policy") != policy
            or column.get("witness_hash") != nr.digest(column.get("plan"))):
        raise ValueError("Native column physical/provenance identity mismatch")
    saved_policy = column["plan"].get("extraction_policy")
    if ((extraction_policy is not None and saved_policy != policy)
            or (extraction_policy is None and saved_policy not in (None, policy))):
        raise ValueError("Native column plan extraction policy mismatch")
    replay = nr.replay_native(case, column["plan"])
    if (column.get("load") != replay["load"] or column.get("ops_cost") != replay["ops_cost"]
            or column.get("key") != projection_key(replay["load"], replay["ops_cost"])):
        raise ValueError("Native column projection does not replay")
    return replay


def simplex(raw):
    values = [rational(x) for x in raw]
    negative = sum((-x for x in values if x < 0), Q(0))
    positive = [max(Q(0), x) for x in values]
    mass = sum(positive, Q(0))
    if not values or negative > rational(MASS_TOL) or mass <= 0 or abs(mass-1) > rational(MASS_TOL):
        raise ValueError("Raw simplex exceeds fixed mass-correction policy")
    weights = [x/mass for x in positive]
    return weights, {"raw": list(raw), "negative_mass_exact": str(negative),
                     "positive_mass_exact": str(mass), "weights_exact": [str(x) for x in weights],
                     "l1_correction_exact": str(sum((abs(x-y) for x, y in zip(values, weights)), Q(0))),
                     "tolerance": MASS_TOL}


def replay_mixture(case, market, columns, raw_weights, extraction_policy=None):
    validate_market(case, market)
    if len(columns) != len(raw_weights) or not columns:
        raise ValueError("Mixture/pool size mismatch")
    projections = [replay_column(case, c, extraction_policy) for c in columns]
    weights, correction = simplex(raw_weights)
    return _project_mixture(market, columns, projections, weights, correction)


def _project_mixture(market, columns, projections, weights, correction, bit_limit=None):
    loads = [sum((w*rational(c["load"][t]) for w, c in zip(weights, projections)), Q(0))
             for t in range(len(market.a))]
    ops = sum((w*rational(c["ops_cost"]) for w, c in zip(weights, projections)), Q(0))
    cost = supply(market, loads)
    true = ops+cost
    if bit_limit is not None and _fraction_bits(loads+[ops, cost, true]) > bit_limit:
        raise LimitReached("rational polishing projected bit-size budget exhausted")
    return {"column_keys": [c["key"] for c in columns], "simplex": correction,
            "load_exact": [str(x) for x in loads], "load": [float(x) for x in loads],
            "ops_exact": str(ops), "supply_exact": str(cost), "objective_exact": str(true),
            "upper": outward(true, True), "replayed_columns": len(columns)}


def replay_exact_mixture(case, market, columns, weights, bit_limit=None, extraction_policy=None):
    """Polished weights stay rational; never materialize them through float."""
    validate_market(case, market)
    if (not columns or len(weights) != len(columns) or any(not isinstance(w, Q) or w < 0 for w in weights)
            or sum(weights, Q(0)) != 1):
        raise ValueError("Polished simplex must be exactly nonnegative with unit mass")
    projections = [replay_column(case, c, extraction_policy) for c in columns]
    return _project_mixture(market, columns, projections, weights,
        {"source": "exact-pairwise-polish", "weights_exact": [str(w) for w in weights],
         "positive_weights": sum(w > 0 for w in weights), "mass_exact": "1"}, bit_limit)


def mixture_price(market, mixture):
    return [float(rational(a)+rational(b)*Q(x))
            for a, b, x in zip(market.a, market.b, mixture["load_exact"])]


def pool_certificate(market, columns, mixture, prices):
    fstar = conjugate(market, prices)
    if fstar is None:
        raise ValueError("Price outside finite nonnegative-supply conjugate domain")
    scores = [rational(c["ops_cost"])+sum((rational(p)*rational(e) for p, e in zip(prices, c["load"])), Q(0))
              for c in columns]
    lower = min(scores)-fstar
    gap = Q(mixture["objective_exact"])-lower
    if gap < 0:
        raise ValueError("Restricted-pool Fenchel inequality reversed")
    return {"prices": list(prices), "conjugate_exact": str(fstar), "pool_min_score_exact": str(min(scores)),
            "pool_lower_exact": str(lower), "pool_gap_exact": str(gap), "pool_gap": outward(gap, True)}


def fenchel_bound(market, prices, pricing_lower):
    fstar = conjugate(market, prices)
    if fstar is None:
        raise ValueError("Price outside finite nonnegative-supply conjugate domain")
    exact = rational(pricing_lower)-fstar
    return {"prices": list(prices), "pricing_lower": pricing_lower,
            "conjugate_exact": str(fstar), "lower_exact": str(exact), "lower": outward(exact, False)}


def tangent_rows(market, points, columns):
    """Float LP lines are weakened to remain tangents on the pool load box."""
    upper = [max(rational(c["load"][t]) for c in columns) for t in range(len(market.a))]
    rows = [[] for _ in market.a]
    for point in points:
        if len(point) != len(market.a):
            raise ValueError("Tangent point dimension mismatch")
        for t, (a, b, x) in enumerate(zip(market.a, market.b, point)):
            q, aa, bb = rational(x), rational(a), rational(b)
            if q < 0:
                raise ValueError("Negative tangent point")
            slope_exact, intercept_exact = aa+bb*q, -bb*q*q/2
            slope = float(slope_exact)
            pad = max(Q(0), rational(slope)-slope_exact)*upper[t]
            intercept = outward(intercept_exact-pad, False)
            rows[t].append({"point_exact": str(q), "slope": slope, "intercept": intercept,
                "exact_slope": str(slope_exact), "exact_intercept": str(intercept_exact),
                "rounding_pad_exact": str(pad)})
    return rows


def _master_once(case, market, columns, points, budget, deadline, call_index, record):
    # Import only when the frozen scientific runner explicitly requests a solve.
    import mip
    model = mip.Model(name="native-hull-clean-master", sense=mip.MINIMIZE, solver_name=budget.backend)
    runtime = nr._backend_identity(model, budget.backend)
    model.verbose, model.threads, model.infeas_tol, model.opt_tol = 0, 1, 1e-8, 1e-8
    lam = [model.add_var(lb=0, ub=1) for _ in columns]
    load = [model.add_var(lb=0, ub=max(c["load"][t] for c in columns)) for t in range(len(market.a))]
    cost = [model.add_var(lb=-mip.INF) for _ in market.a]
    model += mip.xsum(lam) == 1
    for t, L in enumerate(load):
        model += L == mip.xsum(lam[j]*c["load"][t] for j, c in enumerate(columns))
    base_count = model.num_rows
    rows = tangent_rows(market, points, columns)
    for t, cuts in enumerate(rows):
        for row in cuts:
            model += cost[t] >= row["slope"]*load[t]+row["intercept"]
    model.objective = mip.xsum(lam[j]*c["ops_cost"] for j, c in enumerate(columns))+mip.xsum(cost)
    emit(record, {"event": "master_start", "call": call_index, "column_keys": [c["key"] for c in columns],
                  "tangent_points": points, "tangent_rows": rows})
    native_budget = nr.Budget(backend=budget.backend, threads=1, phase_seconds=budget.phase_seconds,
                              wall_seconds=budget.wall_seconds, max_rounds=1)
    stats = nr._optimize_once({"model": model, "backend": budget.backend, "backend_runtime": runtime,
                               "constraint_count_before_objective": base_count}, native_budget, deadline)
    stats["master_base_constraints"] = stats.pop("physical_constraints")
    emit(record, {"event": "master_status", "call": call_index, "stats": stats})
    def number(x):
        return {"value": float(x) if x is not None and math.isfinite(float(x)) else None, "repr": repr(x)}
    snapshot = {"variables": [{"index": v.idx, "name": v.name, "type": v.var_type,
                 "lower": number(v.lb), "upper": number(v.ub), "solution": number(v.x)} for v in model.vars],
                "mapping": {"lambda": [v.idx for v in lam], "load": [v.idx for v in load], "epigraph": [v.idx for v in cost]}}
    emit(record, {"event": "master_incumbent", "call": call_index, **snapshot})
    if stats["status"] != "OPTIMAL" or stats["n_int"] != 0:
        raise ValueError("Clean native hull master is not an OPTIMAL LP")
    def values(items):
        out = [v.x for v in items]
        if any(not nr._finite(x, -math.inf) for x in out):
            raise ValueError("Missing/nonfinite master primal")
        return [float(x) for x in out]
    return {"stats": stats, "lambda": values(lam), "load": values(load), "epigraph": values(cost),
            "tangent_rows": rows, "tangent_points": copy.deepcopy(points)}


def check_master_primal(columns, raw):
    weights, loads, epi, rows, stats = (raw[k] for k in ("lambda", "load", "epigraph", "tangent_rows", "stats"))
    if stats.get("status") != "OPTIMAL" or stats.get("n_int") != 0:
        raise ValueError("Clean native hull master is not an OPTIMAL LP")
    if (len(weights) != len(columns) or len(loads) != len(columns[0]["load"])
            or len(epi) != len(loads) or len(rows) != len(loads)):
        raise ValueError("Master primal dimensions changed")
    simplex(weights)
    for t, load in enumerate(loads):
        expected = sum(w*c["load"][t] for w, c in zip(weights, columns))
        if (not nr._finite(load, -math.inf) or not nr._finite(epi[t], -math.inf)
                or abs(expected-load) > nr.ENERGY_TOL or load < -nr.ENERGY_TOL
                or any(epi[t] < r["slope"]*load+r["intercept"]-OBJECTIVE_TOL for r in rows[t])):
            raise ValueError("Master linking/epigraph primal does not reconstruct")
    native_objective = sum(w*c["ops_cost"] for w, c in zip(weights, columns))+sum(epi)
    nr.admit_bound(stats, native_objective)
    return native_objective


def _fraction_bits(values):
    return max((max(x.numerator.bit_length(), x.denominator.bit_length()) for x in values), default=0)


def polish_pool(case, market, columns, mixture, budget, deadline, counts, record,
                consider=None, master_call=0, extraction_policy=None):
    """Bounded exact pairwise line search; acceptance still needs g_pool."""
    started = time.monotonic()
    counts.setdefault("polish_steps", 0)
    counts.setdefault("polish_checks", 0)
    counts.setdefault("polish_wall_s", 0.0)
    counts.setdefault("max_rational_bits", 0)
    available = budget.polish_seconds-counts["polish_wall_s"]
    stop = min(deadline, started+available)
    seen = set()
    initial_steps, initial_checks = counts["polish_steps"], counts["polish_checks"]
    outcome = "started"
    emit(record, {"event": "pool_polish_start", "master_call": master_call,
                  "cumulative_steps": initial_steps, "remaining_seconds": max(0.0, available)})
    def check_bits(values):
        bits = _fraction_bits(values)
        counts["max_rational_bits"] = max(counts["max_rational_bits"], bits)
        if bits > budget.rational_bits:
            raise LimitReached("rational polishing bit-size budget exhausted")
    try:
        while True:
            if time.monotonic() >= stop:
                raise LimitReached("rational polishing/time budget exhausted")
            weights = [Q(x) for x in mixture["simplex"]["weights_exact"]]
            loads = [Q(x) for x in mixture["load_exact"]]
            check_bits(weights+loads+[Q(mixture["objective_exact"])])
            if consider:
                consider(mixture)
            prices = mixture_price(market, mixture)
            pool = pool_certificate(market, columns, mixture, prices)
            counts["polish_checks"] += 1
            emit(record, {"event": "pool_polish_check", "master_call": master_call,
                "step": counts["polish_steps"], "mixture": mixture, "pool": pool,
                "elapsed_s": time.monotonic()-started})
            if time.monotonic() >= stop:
                raise LimitReached("rational polishing/time budget exhausted after pool check")
            if Q(pool["pool_gap_exact"]) <= rational(budget.pool_tolerance):
                outcome = "qualified"
                return mixture, pool
            state = tuple(weights)
            if state in seen:
                raise PoolStalled("exact pairwise simplex repeated with open pool gap")
            seen.add(state)
            if counts["polish_steps"] >= budget.polish_steps:
                raise LimitReached("rational polishing step budget exhausted")
            gradient = [rational(a)+rational(b)*x for a, b, x in zip(market.a, market.b, loads)]
            scores = [rational(c["ops_cost"])+sum((p*rational(e) for p, e in zip(gradient, c["load"])), Q(0))
                      for c in columns]
            toward = min(range(len(columns)), key=lambda j: (scores[j], j))
            away = max((j for j, w in enumerate(weights) if w > 0), key=lambda j: (scores[j], -j))
            decrease = scores[away]-scores[toward]
            direction = [rational(b)-rational(a) for a, b in zip(columns[away]["load"], columns[toward]["load"])]
            curvature = sum((rational(b)*d*d for b, d in zip(market.b, direction)), Q(0))
            check_bits(gradient+scores+direction+[decrease, curvature])
            if decrease <= 0:
                raise PoolStalled("exact pool stationary but serialized-price gap remains open")
            gamma = min(weights[away], decrease/curvature) if curvature > 0 else weights[away]
            updated = list(weights)
            updated[away] -= gamma
            updated[toward] += gamma
            check_bits(updated+[gamma])
            if gamma <= 0 or updated == weights:
                raise PoolStalled("exact pairwise polishing made no simplex progress")
            new = replay_exact_mixture(case, market, columns, updated, budget.rational_bits,
                                       extraction_policy)
            predicted = Q(mixture["objective_exact"])-gamma*decrease+curvature*gamma*gamma/2
            if Q(new["objective_exact"]) != predicted or predicted >= Q(mixture["objective_exact"]):
                raise ValueError("Exact pairwise objective equation/decrease failed")
            check_bits([Q(x) for x in new["load_exact"]]+[predicted])
            counts["polish_steps"] += 1
            emit(record, {"event": "pool_polish_step", "master_call": master_call,
                "step": counts["polish_steps"], "column_keys": [c["key"] for c in columns],
                "away": away, "toward": toward, "away_key": columns[away]["key"],
                "toward_key": columns[toward]["key"], "weights_before_exact": [str(w) for w in weights],
                "weights_after_exact": [str(w) for w in updated], "gradient_exact": [str(p) for p in gradient],
                "scores_exact": [str(s) for s in scores], "direction_exact": [str(d) for d in direction],
                "directional_decrease_exact": str(decrease), "curvature_exact": str(curvature),
                "gamma_exact": str(gamma), "objective_before_exact": mixture["objective_exact"],
                "objective_after_exact": str(predicted), "mixture": new,
                "max_rational_bits": counts["max_rational_bits"], "elapsed_s": time.monotonic()-started})
            mixture = new
            if consider:
                consider(mixture)  # Preserve this feasible UB even if the next check hits a cap.
    except Exception as exc:
        outcome = type(exc).__name__
        raise
    finally:
        elapsed = time.monotonic()-started
        counts["polish_wall_s"] += elapsed
        emit(record, {"event": "pool_polish_finish", "master_call": master_call, "outcome": outcome,
                      "elapsed_s": elapsed, "steps_completed": counts["polish_steps"]-initial_steps,
                      "checks_completed": counts["polish_checks"]-initial_checks})


def solve_native_rmp(case, market, columns, points, budget, deadline, counts, record,
                     consider=None, extraction_policy=None):
    for c in columns:
        replay_column(case, c, extraction_policy)
    if time.monotonic() >= deadline or counts["master_calls"] >= budget.master_calls:
        raise LimitReached("master/time budget exhausted")
    index = counts["master_calls"]
    counts["master_calls"] += 1
    raw = _master_once(case, market, columns, copy.deepcopy(points), budget, deadline, index, record)
    check_master_primal(columns, raw)
    mixture = replay_mixture(case, market, columns, raw["lambda"], extraction_policy)
    if consider:
        consider(mixture)
    pool = pool_certificate(market, columns, mixture, mixture_price(market, mixture))
    repeated = list(mixture["load"]) in points
    emit(record, {"event": "master_replay", "call": index, "mixture": mixture, "pool": pool,
                  "raw_tangent_objective": raw["stats"]["incumbent"], "repeated_tangent_point": repeated})
    # V2 makes one native LP call per pool. It never appends duplicate cuts and
    # repeats an identical native master to resolve a first-order pool gap.
    if extraction_policy is None:
        mixture, pool = polish_pool(case, market, columns, mixture, budget, deadline,
                                    counts, record, consider, index)
    else:
        mixture, pool = polish_pool(case, market, columns, mixture, budget, deadline,
                                    counts, record, consider, index, extraction_policy)
    point = list(mixture["load"])
    added = point not in points
    if added:
        points.append(point)
    emit(record, {"event": "master_progress", "call": index, "new_tangent_added": added,
                  "repeated_raw_tangent_point": repeated, "polished_load_exact": mixture["load_exact"]})
    return mixture, pool


def solve_qp_rmp(case, market, columns, budget, deadline, counts, record,
                 consider=None, extraction_policy=None, denominator=1_000_000_000,
                 maxiter=500):
    """Numerical pool candidate; exact replay/residual, never a global oracle."""
    if time.monotonic() >= deadline or counts["master_calls"] >= budget.master_calls:
        raise LimitReached("master/time budget exhausted")
    for column in columns:
        replay_column(case, column, extraction_policy)
    if time.monotonic() >= deadline:
        raise LimitReached("master/time budget exhausted after column replay")
    index = counts["master_calls"]
    counts["master_calls"] += 1
    counts["qp_proposal_calls"] += 1
    emit(record, {"event": "master_start", "call": index,
                  "master_policy": "numerical_qp_proposal",
                  "column_keys": [c["key"] for c in columns]})
    # Keep SciPy out of the default native-LP import path.
    started = time.monotonic()
    try:
        from egglab import restricted_qp_proposal as qp
    except Exception as exc:
        elapsed = time.monotonic()-started
        counts["qp_proposal_wall_s"] += elapsed
        emit(record, {"event": "qp_proposal_failure", "call": index,
                      "error_type": type(exc).__name__, "reason": str(exc),
                      "proposal_wall_s": elapsed})
        raise ProposalFailed("numerical QP import failed: " + str(exc)) from exc
    if time.monotonic() >= deadline:
        elapsed = time.monotonic()-started
        counts["qp_proposal_wall_s"] += elapsed
        emit(record, {"event": "qp_proposal_timeout", "call": index,
                      "reason": "QP import/setup exhausted target wall", "proposal_wall_s": elapsed})
        raise LimitReached("QP import/setup exhausted target wall")
    try:
        proposal = qp.propose([c["ops_cost"] for c in columns],
                              [c["load"] for c in columns], market.a, market.b,
                              denominator=denominator, maxiter=maxiter)
    except (TimeoutError, LimitReached):
        counts["qp_proposal_wall_s"] += time.monotonic()-started
        raise
    except Exception as exc:
        elapsed = time.monotonic()-started
        counts["qp_proposal_wall_s"] += elapsed
        emit(record, {"event": "qp_proposal_failure", "call": index,
                      "error_type": type(exc).__name__, "reason": str(exc),
                      "proposal_wall_s": elapsed})
        raise ProposalFailed("numerical QP proposal failed: " + str(exc)) from exc
    elapsed = time.monotonic()-started
    counts["qp_proposal_wall_s"] += elapsed
    emit(record, {"event": "qp_proposal_result", "call": index, "proposal": proposal,
                  "proposal_wall_s": elapsed})
    def reject(reason):
        emit(record, {"event": "qp_proposal_failure", "call": index,
                      "error_type": "InvalidProposal", "reason": reason,
                      "proposal_wall_s": elapsed})
        raise ProposalFailed(reason)
    if (not isinstance(proposal, dict) or type(proposal.get("success")) is not bool
            or proposal.get("denominator") != denominator
            or not isinstance(proposal.get("weights_exact"), list)
            or not isinstance(proposal.get("integer_units"), list)
            or len(proposal["weights_exact"]) != len(columns)
            or len(proposal["integer_units"]) != len(columns)):
        reject("Malformed QP simplex proposal")
    counts["qp_non_success"] += int(not proposal["success"])
    try:
        weights = [Q(value) if isinstance(value, str) else None
                   for value in proposal["weights_exact"]]
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        reject("Invalid exact QP weights")
    units = proposal["integer_units"]
    if (any(weight is None or weight < 0 for weight in weights)
            or sum(weights, Q(0)) != 1
            or any(type(unit) is not int or unit < 0 for unit in units)
            or sum(units) != denominator
            or any(weight*denominator != unit for weight, unit in zip(weights, units))):
        reject("QP weights violate exact simplex policy")
    counts["max_rational_bits"] = max(counts["max_rational_bits"], _fraction_bits(weights))
    if counts["max_rational_bits"] > budget.rational_bits:
        raise LimitReached("QP weight rational bit-size budget exhausted")
    if time.monotonic() >= deadline:
        raise LimitReached("QP proposal exceeded target wall before replay")
    replay_started = time.monotonic()
    try:
        mixture = replay_exact_mixture(case, market, columns, weights,
                                       extraction_policy=extraction_policy)
        mixture["simplex"]["source"] = "fixed-denominator-qp-proposal"
        counts["max_rational_bits"] = max(counts["max_rational_bits"], _fraction_bits(
            [Q(x) for x in mixture["load_exact"]] +
            [Q(mixture[key]) for key in ("ops_exact", "supply_exact", "objective_exact")]))
        if counts["max_rational_bits"] > budget.rational_bits:
            raise LimitReached("QP mixture rational bit-size budget exhausted")
        if consider:
            consider(mixture)
        pool = pool_certificate(market, columns, mixture, mixture_price(market, mixture))
        counts["max_rational_bits"] = max(counts["max_rational_bits"], _fraction_bits(
            [Q(pool["pool_lower_exact"]), Q(pool["pool_gap_exact"]), Q(pool["conjugate_exact"])]))
        if counts["max_rational_bits"] > budget.rational_bits:
            raise LimitReached("QP restricted-pool residual bit-size budget exhausted")
        qualified = Q(pool["pool_gap_exact"]) <= rational(budget.pool_tolerance)
        emit(record, {"event": "qp_candidate_replay", "call": index, "mixture": mixture,
                      "pool": pool, "pool_qualified": qualified,
                      "proposal_success": proposal["success"],
                      "replay_wall_s": time.monotonic()-replay_started})
    finally:
        counts["qp_replay_wall_s"] += time.monotonic()-replay_started
    if time.monotonic() >= deadline:
        raise LimitReached("QP replay/residual exceeded target wall")
    return mixture, pool


def import_pool(case, previous, expected_previous, budget, previous_index=None,
                extraction_policy=None, reuse_policy="certified_only", oracle_id=None,
                pricing_reserve_seconds=0.0):
    policy = _extraction_policy(extraction_policy)
    controls = _controls(reuse_policy, pricing_reserve_seconds, budget)
    allowed = ({"certified"} if reuse_policy == "certified_only" else
               {"certified", "budget_exhausted", "stalled_bounded", "bounded"})
    if (not isinstance(expected_previous, str) or not expected_previous
            or not previous or previous.get("schema") != SCHEMA or previous.get("status") not in allowed
            or previous.get("arm") != "retained"
            or (previous_index is not None and previous.get("state_index") != previous_index)
            or previous.get("state_identity") != expected_previous
            or previous.get("physical_identity") != case.identity()
            or previous.get("extraction_policy") != policy
            or any(previous.get(key) != value for key, value in controls.items())):
        raise ValueError("Invalid retained predecessor identity/status")
    columns = copy.deepcopy(previous.get("columns", []))
    if not 1 <= len(columns) <= budget.pool_cap or len({c["key"] for c in columns}) != len(columns):
        raise ValueError("Invalid retained pool size/duplicate projection")
    for c in columns:
        replay_column(case, c, extraction_policy)
        if reuse_policy == "feasible_pool":
            source = c.get("source")
            if (not isinstance(source, dict) or source.get("state_identity") != expected_previous
                    or source.get("pricing_oracle") != oracle_id):
                raise ValueError("Imported column provenance/oracle identity mismatch")
    return columns


def _controls(reuse_policy, pricing_reserve_seconds, budget):
    if reuse_policy not in ("certified_only", "feasible_pool"):
        raise ValueError("Unknown retained-pool reuse policy")
    if (not nr._finite(pricing_reserve_seconds)
            or pricing_reserve_seconds >= budget.wall_seconds):
        raise ValueError("Invalid pricing-time reserve")
    return ({} if reuse_policy == "certified_only" and pricing_reserve_seconds == 0 else
            {"reuse_policy": reuse_policy,
             "pricing_reserve_seconds": float(pricing_reserve_seconds)})


def _cache_controls(bound_cache_policy, expected_cached_state):
    if bound_cache_policy not in ("none", "physical_pricing"):
        raise ValueError("Unknown physical pricing-bound cache policy")
    if bound_cache_policy == "none":
        if expected_cached_state is not None:
            raise ValueError("Disabled cache cannot name a source state")
        return {}
    if expected_cached_state is not None and (not isinstance(expected_cached_state, str)
                                              or not expected_cached_state):
        raise ValueError("Invalid expected cached source state")
    return {"bound_cache_policy": bound_cache_policy,
            **({"cache_source_state_identity": expected_cached_state} if expected_cached_state else {})}


def _master_controls(master_policy, qp_denominator, qp_maxiter, budget):
    if master_policy == "native_lp":
        if qp_denominator != 1_000_000_000 or qp_maxiter != 500:
            raise ValueError("QP controls require the opt-in numerical master")
        return {}
    if (master_policy != "numerical_qp_proposal" or type(qp_denominator) is not int
            or qp_denominator < 1 or qp_denominator.bit_length() > budget.rational_bits
            or type(qp_maxiter) is not int or qp_maxiter < 1):
        raise ValueError("Invalid numerical restricted-master policy")
    return {"master_policy": master_policy, "qp_denominator": qp_denominator,
            "qp_maxiter": qp_maxiter}


def _cached_pricing_bounds(case, market, source, expected_state, oracle, policy):
    """Re-evaluate checked physical pricing lowers; caller owns source receipt trust."""
    if (not isinstance(source, dict) or source.get("schema") != SCHEMA
            or source.get("state_identity") != expected_state
            or source.get("physical_identity") != case.identity()
            or source.get("pricing_oracle") != oracle
            or source.get("extraction_policy") != policy
            or source.get("bound_cache_policy") != "physical_pricing"
            or not isinstance(source.get("market_identity"), str)
            or not source["market_identity"]
            or type(source.get("state_index")) is not int):
        raise ValueError("Cached source case/state/oracle/policy mismatch")
    records = source.get("physical_pricing_evidence")
    counts = source.get("counts")
    cap = source.get("source_pricing_call_cap")
    costs = source.get("source_costs")
    if (type(cap) is not int or cap < 1 or not isinstance(costs, dict)
            or not nr._finite(costs.get("source_coordinator_elapsed_s"))
            or not nr._finite(costs.get("native_pricing_solver_wall_s"))
            or costs.get("full_child_wall_s") is not None
            or costs.get("unmeasured_preparation_wall_s") is not None):
        raise ValueError("Cached source work cap/cost lineage is invalid")
    try:
        records_digest = nr.digest(records)
    except (TypeError, ValueError) as exc:
        raise ValueError("Malformed physical pricing evidence") from exc
    if (not isinstance(records, list) or not records
            or not isinstance(counts, dict)
            or type(counts.get("pricing_requests")) is not int
            or counts["pricing_requests"] > cap
            or len(records) > counts["pricing_requests"]
            or source.get("physical_pricing_evidence_digest") != records_digest):
        raise ValueError("Missing, oversized or changed physical pricing evidence")
    candidates, calls = [], set()
    for item in records:
        if not isinstance(item, dict) or set(item) != {"record", "digest"}:
            raise ValueError("Malformed cached pricing record")
        data = item["record"]
        try:
            record_digest = nr.digest(data)
        except (TypeError, ValueError) as exc:
            raise ValueError("Malformed cached pricing record") from exc
        if not isinstance(data, dict) or item["digest"] != record_digest:
            raise ValueError("Changed cached pricing record")
        call = data.get("pricing_call")
        if (type(call) is not int or call < 0 or call >= counts["pricing_requests"] or call in calls
                or data.get("source_state_identity") != expected_state
                or data.get("source_market_identity") != source["market_identity"]
                or data.get("physical_identity") != case.identity()
                or data.get("pricing_oracle") != oracle
                or data.get("extraction_policy") != policy
                or data.get("native_result_status") not in ("certified", "bounded")
                or not isinstance(data.get("prices"), list)
                or len(data["prices"]) != len(market.a)
                or any(not nr._finite(p, -math.inf) for p in data["prices"])
                or not nr._finite(data.get("pricing_objective"), -math.inf)
                or not nr._finite(data.get("pricing_lower"), -math.inf)
                or not nr._finite(data.get("pricing_upper"), -math.inf)
                or not nr._finite(data.get("ops_cost"), -math.inf)
                or not isinstance(data.get("load"), list)
                or len(data["load"]) != len(market.a)
                or any(not nr._finite(e) for e in data["load"])
                or not isinstance(data.get("column_key"), str) or not data["column_key"]
                or not isinstance(data.get("witness_hash"), str) or not data["witness_hash"]):
            raise ValueError("Incompatible cached physical pricing provenance")
        calls.add(call)
        objective = data["ops_cost"] + sum(p*e for p, e in zip(data["prices"], data["load"]))
        if (abs(objective-data["pricing_objective"]) > OBJECTIVE_TOL
                or data["column_key"] != projection_key(data["load"], data["ops_cost"])):
            raise ValueError("Cached pricing price/projection/objective mismatch")
        stats = data.get("native_stats")
        if not isinstance(stats, dict) or not nr._finite(stats.get("wall_s")):
            raise ValueError("Cached native pricing statistics incomplete")
        lower, upper = nr.admit_bound(stats, data["pricing_objective"])
        if data["pricing_lower"] != lower or data["pricing_upper"] != upper:
            raise ValueError("Cached physical pricing bound differs from native evidence")
        cert = fenchel_bound(market, data["prices"], lower)
        candidates.append({"certificate": cert, "source_state_identity": expected_state,
                           "source_market_identity": source["market_identity"],
                           "source_pricing_call": call, "source_record_digest": item["digest"],
                           "source_column_key": data["column_key"]})
    return candidates


def state_identity(case, market, arm, state_index, budget, oracle_id=None,
                   extraction_policy=None, reuse_policy="certified_only",
                   pricing_reserve_seconds=0.0, bound_cache_policy="none",
                   expected_cached_state=None, master_policy="native_lp",
                   qp_denominator=1_000_000_000, qp_maxiter=500):
    policy = _extraction_policy(extraction_policy)
    metadata = {} if oracle_id is None else {"pricing_oracle": oracle_id}
    controls = _controls(reuse_policy, pricing_reserve_seconds, budget)
    cache_controls = _cache_controls(bound_cache_policy, expected_cached_state)
    master_controls = _master_controls(master_policy, qp_denominator, qp_maxiter, budget)
    if cache_controls and oracle_id is None:
        metadata = {"pricing_oracle": DEFAULT_PRICING_ORACLE}
    if oracle_id is not None and (not isinstance(oracle_id, str) or not oracle_id.strip()):
        raise ValueError("Explicit pricing oracle requires a nonempty identity")
    return nr.digest({"schema": SCHEMA, "case": case.identity(), "market": market.identity(),
                      "arm": arm, "state_index": state_index, "budget": asdict(budget),
                      "extraction_policy": policy, **metadata, **controls, **cache_controls,
                      **master_controls})


def certify(case, market, budget=Budget(), *, arm="cold", state_index=0,
            previous=None, expected_previous=None, record=None, pricing_oracle=None,
            oracle_id=None, extraction_policy=None, reuse_policy="certified_only",
            pricing_reserve_seconds=0.0, bound_cache_policy="none", cached_from=None,
            expected_cached_state=None, master_policy="native_lp",
            qp_denominator=1_000_000_000, qp_maxiter=500):
    nr.validate_case(case)
    validate_market(case, market)
    validate_budget(budget)
    controls = _controls(reuse_policy, pricing_reserve_seconds, budget)
    cache_controls = _cache_controls(bound_cache_policy, expected_cached_state)
    master_controls = _master_controls(master_policy, qp_denominator, qp_maxiter, budget)
    if (cached_from is None) != (expected_cached_state is None):
        raise ValueError("Cached source and expected state must be supplied together")
    if cached_from is not None and bound_cache_policy != "physical_pricing":
        raise ValueError("Physical pricing-bound cache must be explicitly enabled")
    if (pricing_oracle is None) != (oracle_id is None) or (pricing_oracle is not None and not callable(pricing_oracle)):
        raise ValueError("Explicit pricing oracle requires both a callable and its identity")
    policy = _extraction_policy(extraction_policy)
    if oracle_id is None and policy != nr.EXTRACTION_POLICY:
        raise ValueError("Non-indexed extraction policy requires an explicit oracle")
    canonical_oracle = oracle_id if oracle_id is not None else DEFAULT_PRICING_ORACLE
    column_oracle = canonical_oracle if bound_cache_policy != "none" else oracle_id
    metadata = {} if column_oracle is None else {"pricing_oracle": column_oracle}
    oracle = nr.solve_pricing if pricing_oracle is None else pricing_oracle
    if arm not in ("cold", "retained") or type(state_index) is not int or state_index < 0:
        raise ValueError("Invalid hull arm/state")
    if (arm == "cold" or state_index == 0) and (previous is not None or expected_previous is not None):
        raise ValueError("Fresh state cannot import a predecessor")
    started = time.monotonic()
    deadline = started+budget.wall_seconds
    identity = state_identity(case, market, arm, state_index, budget, oracle_id, extraction_policy,
                              reuse_policy, pricing_reserve_seconds, bound_cache_policy, expected_cached_state,
                              master_policy, qp_denominator, qp_maxiter)
    if previous is not None and previous.get("pricing_oracle") != column_oracle:
        raise ValueError("Retained predecessor pricing oracle identity differs")
    columns = (import_pool(case, previous, expected_previous, budget, state_index-1,
                           extraction_policy, reuse_policy, column_oracle, pricing_reserve_seconds)
               if arm == "retained" and state_index > 0 else [])
    counts = {"pricing_requests": 0, "seed_requests": 0, "master_calls": 0,
              "polish_steps": 0, "polish_checks": 0, "polish_wall_s": 0.0, "max_rational_bits": 0}
    if master_controls:
        counts.update(qp_proposal_calls=0, qp_non_success=0,
                      qp_proposal_wall_s=0.0, qp_replay_wall_s=0.0)
    best_lower, best_mixture = None, None
    best_lower_origin = None
    fresh_best_lower, fresh_pricing_successes = None, 0
    pricing_evidence, cache_candidates = [], []
    cache_started = time.monotonic()
    if cached_from is not None:
        if (state_index < 1 or not isinstance(cached_from, dict)
                or cached_from.get("state_index") != state_index - 1):
            raise ValueError("Cached source is not the preceding state")
        cache_candidates = _cached_pricing_bounds(case, market, cached_from, expected_cached_state,
                                                   canonical_oracle, policy)
        best = max(cache_candidates, key=lambda item: Q(item["certificate"]["lower_exact"]))
        best_lower = copy.deepcopy(best["certificate"])
        best_lower_origin = {"kind": "cached_physical_pricing", **{key: value for key, value in best.items()
                              if key != "certificate"}}
    cache_validation_wall_s = time.monotonic() - cache_started if bound_cache_policy != "none" else None
    points = [[0.0]*len(market.a)]
    emit(record, {"event": "state_start", "state_identity": identity, "market_identity": market.identity(),
                  "imported_column_keys": [c["key"] for c in columns], "fresh_bounds": True,
                  **metadata, **controls, **cache_controls,
                  **master_controls,
                  **({"fresh_target_pricing_required": True,
                      "target_conjugates_rebuilt_from_cached_physical_lowers": True,
                      "cached_bound_candidates": len(cache_candidates)} if cache_controls else {})})
    if bound_cache_policy != "none":
        emit(record, {"event": "physical_pricing_cache_checked", "source_state_identity": expected_cached_state,
                      "candidate_count": len(cache_candidates), "validation_wall_s": cache_validation_wall_s,
                      "best_candidate": (max(cache_candidates, key=lambda item: Q(item["certificate"]["lower_exact"]))
                                         if cache_candidates else None)})
    def consider_mixture(mix):
        nonlocal best_mixture
        if (best_mixture is None or Q(mix["objective_exact"]) < Q(best_mixture["objective_exact"])
                or (master_controls and best_mixture is not None
                    and Q(mix["objective_exact"]) == Q(best_mixture["objective_exact"])
                    and mix["simplex"].get("source") == "fixed-denominator-qp-proposal")):
            best_mixture = copy.deepcopy(mix)
    if columns and reuse_policy == "feasible_pool":
        # Reconstruct an upper in the NEW market from physical columns only.
        # Neither old simplex weights nor old lower certificates cross states.
        for index in range(len(columns)):
            one_hot = [float(j == index) for j in range(len(columns))]
            retained_mix = replay_mixture(case, market, columns, one_hot, extraction_policy)
            if master_controls:
                retained_mix["simplex"]["source"] = "retained-column-one-hot"
            consider_mixture(retained_mix)
    def price(prices, seed=False):
        nonlocal best_lower, best_lower_origin, fresh_best_lower, fresh_pricing_successes
        now = time.monotonic()
        if pricing_reserve_seconds == 0:
            if now >= deadline or counts["pricing_requests"] >= budget.pricing_calls:
                raise LimitReached("pricing/time budget exhausted")
        else:
            if counts["pricing_requests"] >= budget.pricing_calls:
                raise LimitReached("pricing call budget exhausted")
            if deadline-now <= pricing_reserve_seconds:
                emit(record, {"event": "pricing_reserve_stop", "remaining_seconds": deadline-now,
                              "reserve_seconds": pricing_reserve_seconds})
                raise LimitReached("pricing reserve prevented a new request")
        if pricing_reserve_seconds:
            remaining = deadline-time.monotonic()-pricing_reserve_seconds
            if remaining <= 0:
                emit(record, {"event": "pricing_reserve_stop", "remaining_seconds": remaining+pricing_reserve_seconds,
                              "reserve_seconds": pricing_reserve_seconds})
                raise LimitReached("pricing reserve prevented a new request")
        index = counts["pricing_requests"]
        counts["pricing_requests"] += 1
        counts["seed_requests"] += int(seed)
        trace = ({"pricing_wall_allowance_seconds": remaining,
                  "reserve_seconds": pricing_reserve_seconds,
                  "remaining_total_seconds": remaining+pricing_reserve_seconds}
                 if pricing_reserve_seconds else {})
        emit(record, {"event": "pricing_request", "call": index, "seed": seed, "prices": prices,
                      **metadata, **trace})
        def oracle_record(event):
            emit(record, {"event": "pricing_native", "call": index, "detail": event})
        if not pricing_reserve_seconds:
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise LimitReached("time budget exhausted before pricing")
        result = oracle(case, prices,
            nr.Budget(backend=budget.backend, threads=1, phase_seconds=budget.phase_seconds,
                      wall_seconds=remaining, max_rounds=1), record=oracle_record)
        emit(record, {"event": "pricing_result", "call": index, "result": result})
        if oracle_id is not None and (result.get("formulation") != oracle_id
                or not isinstance(result.get("plan"), dict) or result["plan"].get("formulation") != oracle_id):
            raise ValueError("Explicit pricing oracle result/plan formulation mismatch")
        if extraction_policy is not None and (result.get("extraction_policy") != policy
                or result["plan"].get("extraction_policy") != policy):
            raise ValueError("Explicit pricing oracle extraction policy mismatch")
        if (result.get("status") not in ("certified", "bounded") or result.get("case_identity") != case.identity()
                or result.get("prices") != list(prices)):
            raise ValueError("Unresolved/infeasible/mismatched complete-fleet pricing result")
        column = native_column(case, result["plan"],
                               {"state_identity": identity, "pricing_call": index, **metadata},
                               extraction_policy)
        objective = column["ops_cost"]+sum(p*e for p, e in zip(prices, column["load"]))
        lower, upper = nr.admit_bound(result["stats"], objective)
        if result.get("lower") != lower or abs(result.get("upper", math.inf)-upper) > OBJECTIVE_TOL:
            raise ValueError("Pricing reported enclosure changed on physical replay")
        certificate = fenchel_bound(market, prices, lower)
        emit(record, {"event": "global_bound", "call": index, "certificate": certificate, "column": column})
        fresh_pricing_successes += 1
        if bound_cache_policy != "none":
            if not nr._finite(result["stats"].get("wall_s")):
                raise ValueError("Physical pricing solver wall time is unavailable for cache evidence")
            evidence = {"source_state_identity": identity, "source_market_identity": market.identity(),
                        "physical_identity": case.identity(), "pricing_oracle": canonical_oracle,
                        "extraction_policy": policy, "pricing_call": index, "prices": list(prices),
                        "pricing_objective": objective, "pricing_lower": lower, "pricing_upper": upper,
                        "load": list(column["load"]), "ops_cost": column["ops_cost"],
                        "native_result_status": result["status"],
                        "native_stats": {key: result["stats"].get(key) for key in
                                         ("status", "incumbent", "lower_bound", "wall_s", "backend", "threads")},
                        "column_key": column["key"], "witness_hash": column["witness_hash"]}
            pricing_evidence.append({"record": evidence, "digest": nr.digest(evidence)})
            if fresh_best_lower is None or Q(certificate["lower_exact"]) > Q(fresh_best_lower["lower_exact"]):
                fresh_best_lower = copy.deepcopy(certificate)
        if best_lower is None or Q(certificate["lower_exact"]) > Q(best_lower["lower_exact"]):
            best_lower = copy.deepcopy(certificate)
            if bound_cache_policy != "none":
                best_lower_origin = {"kind": "fresh_target_pricing", "pricing_call": index,
                                     "source_state_identity": identity}
        return column
    reason, status = None, "unresolved"
    try:
        if not columns:
            columns.append(price(list(market.a), seed=True))
            seed_mix = replay_mixture(case, market, columns, [1.0], extraction_policy)
            if master_controls:
                seed_mix["simplex"]["source"] = "fresh-seed-one-hot"
            consider_mixture(seed_mix)
        while True:
            if master_policy == "native_lp":
                mixture, pool = solve_native_rmp(case, market, columns, points, budget, deadline,
                                                 counts, record, consider_mixture, extraction_policy)
            else:
                mixture, pool = solve_qp_rmp(case, market, columns, budget, deadline, counts, record,
                                             consider_mixture, extraction_policy, qp_denominator, qp_maxiter)
            consider_mixture(mixture)
            candidate = price(pool["prices"])
            gap = Q(best_mixture["objective_exact"])-Q(best_lower["lower_exact"])
            if gap < -rational(nr.BOUND_GUARD):
                raise ValueError("Native hull global enclosure reversed")
            if gap < 0:
                raise ValueError("Negative exact stored-number certificate width")
            if gap <= rational(budget.epsilon) and (bound_cache_policy == "none" or fresh_pricing_successes > 0):
                if candidate["key"] not in {c["key"] for c in columns} and len(columns) < budget.pool_cap:
                    columns.append(candidate)
                    emit(record, {"event": "column_added", "key": candidate["key"], "size": len(columns),
                                  "after_certificate": True})
                status = "certified"
                break
            if candidate["key"] in {c["key"] for c in columns}:
                status, reason = "stalled_bounded", "duplicate pricing projection with open global gap"
                break
            if len(columns) >= budget.pool_cap:
                raise LimitReached("column pool budget exhausted")
            columns.append(candidate)
            emit(record, {"event": "column_added", "key": candidate["key"], "size": len(columns)})
    except (LimitReached, TimeoutError) as exc:
        status, reason = "budget_exhausted", str(exc)
    except PoolStalled as exc:
        status, reason = "stalled_bounded", str(exc)
    except ProposalFailed as exc:
        status, reason = "proposal_failed", str(exc)
    result = {"schema": SCHEMA, "status": status, "reason": reason, "state_identity": identity,
              "physical_identity": case.identity(), "market_identity": market.identity(),
              "extraction_policy": policy, "arm": arm, "state_index": state_index,
              "columns": columns, "counts": counts, "epsilon": budget.epsilon,
              **metadata, **controls, **cache_controls, **master_controls}
    if bound_cache_policy != "none":
        result.update(pricing_oracle=canonical_oracle, physical_pricing_evidence=pricing_evidence,
                      physical_pricing_evidence_digest=nr.digest(pricing_evidence),
                      source_pricing_call_cap=budget.pricing_calls,
                      cached_lower_candidates=cache_candidates,
                      cache_validation_wall_s=cache_validation_wall_s,
                      cache_source_costs=(copy.deepcopy(cached_from.get("source_costs")) if cached_from else None),
                      fresh_pricing_successes=fresh_pricing_successes,
                      fresh_lower_certificate=fresh_best_lower,
                      lower_certificate_origin=best_lower_origin,
                      source_costs={"source_coordinator_elapsed_s": time.monotonic()-started,
                                    "native_pricing_solver_wall_s": sum(
                                        item["record"]["native_stats"]["wall_s"] for item in pricing_evidence),
                                    "full_child_wall_s": None, "unmeasured_preparation_wall_s": None,
                                    "scope": "core certify call only; excludes runner preparation/child overhead"})
    if best_lower:
        result["lower_certificate"] = best_lower
        result["lower"] = best_lower["lower"]
    if best_mixture:
        result["mixture"] = best_mixture
        result["upper"] = best_mixture["upper"]
    if best_lower and best_mixture:
        gap = Q(best_mixture["objective_exact"])-Q(best_lower["lower_exact"])
        if (bound_cache_policy != "none" or master_controls) and gap < 0:
            raise ValueError("Cached physical bound reverses target feasible enclosure")
        result.update(gap=outward(gap, True), gap_exact=str(gap))
    emit(record, {"event": "state_finish", "result": result})
    return result
