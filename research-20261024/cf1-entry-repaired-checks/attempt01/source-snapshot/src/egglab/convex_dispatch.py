"""Small continuous economic dispatch with balance and ramp duals.

All periods have unit duration. Costs are linear (hence convex), outputs are
nonnegative, and there is no commitment or implicit load shedding. Infeasible
demands return a non-optimal result, not an artificial penalty dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from contextvars import ContextVar
from math import isfinite
from typing import Sequence
from time import perf_counter
import warnings

import numpy as np
from scipy.optimize import OptimizeWarning, linprog

_lp_timing_log: ContextVar[list[dict] | None] = ContextVar("lp_timing_log", default=None)


@contextmanager
def capture_lp_timings():
    """Collect per-LP elapsed wall times for a bounded local experiment."""
    entries: list[dict] = []
    token = _lp_timing_log.set(entries)
    try:
        yield entries
    finally:
        _lp_timing_log.reset(token)


def bounded_linprog(*args, **kwargs):
    """Use one HiGHS native thread and at most ten seconds per tiny LP."""
    with warnings.catch_warnings():
        # SciPy 1.13 forwards this supported HiGHS option but labels it
        # unrecognized at the SciPy wrapper boundary. Ignore only that notice.
        warnings.filterwarnings(
            "ignore",
            message=r"Unrecognized options detected: \{'threads': 1\}\. These will be passed to HiGHS verbatim\.",
            category=OptimizeWarning,
        )
        start = perf_counter()
        try:
            result = linprog(*args, method="highs", options={"threads": 1, "time_limit": 10.0}, **kwargs)
            return result
        finally:
            log = _lp_timing_log.get()
            if log is not None:
                log.append({"elapsed_seconds": perf_counter() - start})


@dataclass(frozen=True)
class Generator:
    name: str
    marginal_cost: tuple[float, ...]
    capacity: tuple[float, ...]
    ramp_up: float | tuple[float, ...]
    ramp_down: float | tuple[float, ...]
    initial_output: float | None = None


@dataclass(frozen=True)
class DispatchResult:
    status: str
    objective: float | None
    output: tuple[tuple[float, ...], ...] | None
    balance_price: tuple[float, ...] | None
    constraint_names: tuple[str, ...]
    constraint_slack: tuple[float, ...] | None
    constraint_shadow: tuple[float, ...] | None
    dual_objective: float | None
    max_primal_residual: float | None
    max_dual_violation: float | None
    max_complementarity: float | None


def dispatch_matrices(
    generators: Sequence[Generator], periods: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, tuple[str, ...]]:
    """Return ``c, Aeq, Aub, bub, names`` for the declared generator model."""
    if not generators or periods < 1:
        raise ValueError("at least one generator and period are required")
    if len({g.name for g in generators}) != len(generators):
        raise ValueError("generator names must be unique")
    n = len(generators) * periods
    c = np.zeros(n)
    eq = np.zeros((periods, n))
    rows: list[np.ndarray] = []
    rhs: list[float] = []
    names: list[str] = []

    def add(name: str, coeffs: dict[int, float], bound: float) -> None:
        row = np.zeros(n)
        for j, value in coeffs.items():
            row[j] = value
        rows.append(row)
        rhs.append(bound)
        names.append(name)

    for i, g in enumerate(generators):
        if len(g.capacity) != periods or len(g.marginal_cost) != periods:
            raise ValueError("cost/capacity length must equal demand horizon")
        up = (g.ramp_up,) * periods if isinstance(g.ramp_up, (int, float)) else g.ramp_up
        down = (g.ramp_down,) * periods if isinstance(g.ramp_down, (int, float)) else g.ramp_down
        if len(up) != periods or len(down) != periods:
            raise ValueError("ramp sequence length must equal demand horizon")
        numbers = (*g.capacity, *g.marginal_cost, *up, *down)
        if not all(isfinite(v) and v >= 0 for v in numbers):
            raise ValueError("costs, capacities and ramps must be finite nonnegative")
        if g.initial_output is not None and (
            not isfinite(g.initial_output)
            or not 0 <= g.initial_output <= g.capacity[0]
        ):
            raise ValueError("initial output must be within first-period capacity")
        for t in range(periods):
            j = i * periods + t
            c[j] = g.marginal_cost[t]
            eq[t, j] = 1
            add(f"{g.name}.capacity[{t}]", {j: 1}, g.capacity[t])
            if t == 0 and g.initial_output is not None:
                add(f"{g.name}.initial_up", {j: 1}, g.initial_output + up[t])
                add(f"{g.name}.initial_down", {j: -1}, down[t] - g.initial_output)
            if t > 0:
                prev = j - 1
                add(f"{g.name}.up[{t}]", {j: 1, prev: -1}, up[t])
                add(f"{g.name}.down[{t}]", {prev: 1, j: -1}, down[t])
    return c, eq, np.array(rows), np.array(rhs), tuple(names)


def solve_dispatch(
    generators: Sequence[Generator], demand: Sequence[float]
) -> DispatchResult:
    """Solve one small LP; balance multipliers use the demand-price sign.

    The dual uses nonnegative ``mu`` for ``Aub*g <= bub`` and satisfies
    ``Aeq.T*p - Aub.T*mu <= c``. Its objective is ``p*d - bub*mu``.
    """
    d = np.asarray(demand, dtype=float)
    if d.ndim != 1 or not len(d) or not np.all(np.isfinite(d)) or np.min(d) < 0:
        raise ValueError("demand must be a finite nonnegative vector")
    c, eq, ub, bound, names = dispatch_matrices(generators, len(d))
    result = bounded_linprog(
        c,
        A_ub=ub,
        b_ub=bound,
        A_eq=eq,
        b_eq=d,
        bounds=(0, None),
    )
    if result.status == 2:
        return DispatchResult("infeasible", None, None, None, names, None, None, None, None, None, None)
    if result.status != 0:
        raise RuntimeError(f"dispatch solver failed: {result.message}")
    x = result.x
    p = np.asarray(result.eqlin.marginals)
    mu = -np.asarray(result.ineqlin.marginals)
    slack = bound - ub @ x
    dual_slack = c - eq.T @ p + ub.T @ mu
    dual_objective = float(p @ d - bound @ mu)
    primal_residual = max(
        float(np.max(np.abs(eq @ x - d))),
        float(np.max(np.maximum(-slack, 0))),
        float(np.max(np.maximum(-x, 0))),
    )
    dual_violation = max(
        float(np.max(np.maximum(-mu, 0))),
        float(np.max(np.maximum(-dual_slack, 0))),
        abs(float(result.fun) - dual_objective),
    )
    comp = max(float(np.max(np.abs(mu * slack))), float(np.max(np.abs(x * dual_slack))))
    periods = len(d)
    return DispatchResult(
        "optimal",
        float(result.fun),
        tuple(tuple(float(v) for v in x[i * periods : (i + 1) * periods]) for i in range(len(generators))),
        tuple(float(v) for v in p),
        names,
        tuple(float(v) for v in slack),
        tuple(float(v) for v in mu),
        dual_objective,
        primal_residual,
        dual_violation,
        comp,
    )


def incremental_cost(
    generators: Sequence[Generator], background: Sequence[float], fleet_load: Sequence[float]
) -> float:
    """Compute ``H(background + fleet_load) - H(background)``.

    Both dispatches must be feasible; this checks the declared baseline instead
    of assuming that its cost is zero.
    """
    b = np.asarray(background, dtype=float)
    load = np.asarray(fleet_load, dtype=float)
    if b.shape != load.shape:
        raise ValueError("background and fleet load horizons differ")
    baseline = solve_dispatch(generators, b)
    combined = solve_dispatch(generators, b + load)
    if baseline.objective is None or combined.objective is None:
        raise ValueError("baseline or combined demand is dispatch infeasible")
    return combined.objective - baseline.objective


def optimal_price_ranges(
    generators: Sequence[Generator], demand: Sequence[float], *, tolerance: float = 1e-8
) -> tuple[tuple[float, float], ...]:
    """Project the optimal dispatch dual face onto each balance price.

    A small absolute tolerance is needed for floating LP data. At boundary
    loads the projection can be unbounded; those endpoints are returned as
    infinite floats by HiGHS, rather than implicitly clipped.
    """
    solved = solve_dispatch(generators, demand)
    if solved.objective is None:
        raise ValueError("cannot price infeasible demand")
    d = np.asarray(demand, dtype=float)
    c, eq, ub, bound, _ = dispatch_matrices(generators, len(d))
    nt = len(d)
    nrows = len(bound)
    dual_rows = np.hstack((eq.T, -ub.T))
    optimum_row = np.concatenate((-d, bound))
    dual_ub = np.vstack((dual_rows, optimum_row))
    dual_bound = np.concatenate((c, [-solved.objective + tolerance]))
    var_bounds = [(None, None)] * nt + [(0, None)] * nrows
    ranges: list[tuple[float, float]] = []
    for t in range(nt):
        objective = np.zeros(nt + nrows)
        objective[t] = 1
        endpoints: list[float] = []
        for direction in (1, -1):
            solution = bounded_linprog(
                direction * objective,
                A_ub=dual_ub,
                b_ub=dual_bound,
                bounds=var_bounds,
            )
            if solution.status == 3:
                endpoints.append(float("-inf") if direction == 1 else float("inf"))
            elif solution.status == 0:
                endpoints.append(float(solution.x[t]))
            else:
                raise RuntimeError(f"dual price-range solver failed: {solution.message}")
        ranges.append((endpoints[0], endpoints[1]))
    return tuple(ranges)
