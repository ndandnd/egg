"""Balanced radial series-line OPF for one delivery interval.

Edges are oriented from parent to child. Positive nodal demand consumes power.
The model prices a fixed network topology. No shunts, taps or phase imbalance
are implicit in this feeder representation.
"""

from __future__ import annotations

import operator

import cvxpy as cp
import numpy as np


def _vector(value, size, name, *, allow_scalar=False, allow_infinity=False):
    values = np.asarray(value, dtype=float)
    if allow_scalar and values.ndim == 0:
        values = np.full(size, float(values))
    if values.shape != (size,):
        raise ValueError(f"{name} must have length {size}")
    if np.any(np.isnan(values)) or (not allow_infinity and not np.all(np.isfinite(values))):
        raise ValueError(f"invalid {name}")
    return values


def _index(value):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("a bus index must be an integer")
    try:
        return operator.index(value)
    except TypeError as exc:
        raise ValueError("a bus index must be an integer") from exc


def solve_radial(parent, r, x, p_mw, q_mvar, *, base_mva=1., price=50.,
                 curvature=0., hours=1., vmin=.90, vmax=1.10, imax_pu=None,
                 pwl=None, linearized=False, backup=None, root_import_cap_mw=None):
    """Return CLARABEL's status, a primal witness, balance prices and residuals.

    Buses are ordered 0..n-1. parent[j-1] is upstream of bus j. r and x are
    per-unit series impedances on base_mva. vmin and vmax bound voltage
    magnitudes. imax_pu bounds series current magnitude, with None or +inf
    denoting an absent limit. Each bound may be a scalar or a full vector.

    The slack buys signed MW at marginal price price + curvature * import_mw.
    Alternatively pwl=(break_mw, left_slope, right_slope) specifies a convex
    import offer with C(0)=0. An optional backup=(bus, pmax_mw, euro_per_mwh)
    injects active power at unity power factor. root_import_cap_mw bounds
    signed active import. The cost includes interval duration in hours.

    dlmp and dlmp_q are taken from the active and reactive balance constraints,
    in EUR/MWh and EUR/MVArh. For a fixed power factor the total sensitivity
    includes dlmp_q * dQ/dP. Pointwise conic equality alone does not establish
    that a one-sided price of the physical AC value equals either dual.
    """
    parents = [_index(value) for value in parent]
    n = len(parents) + 1
    children = [[] for _ in range(n)]
    for j, i in enumerate(parents, start=1):
        if not 0 <= i < j:
            raise ValueError(f"bus {j} must have one earlier parent")
        children[i].append(j)
    r = _vector(r, n - 1, "r")
    x = _vector(x, n - 1, "x")
    p = _vector(p_mw, n, "p_mw")
    q = _vector(q_mvar, n, "q_mvar")
    low = _vector(vmin, n, "vmin", allow_scalar=True)
    high = _vector(vmax, n, "vmax", allow_scalar=True)
    limits = _vector(np.inf if imax_pu is None else imax_pu, n - 1, "imax_pu",
                     allow_scalar=True, allow_infinity=True)
    if np.any(r < 0) or np.any(x < 0) or np.any(limits < 0):
        raise ValueError("impedances and current ratings must be nonnegative")
    if np.any(low <= 0) or np.any(low > high):
        raise ValueError("voltage bounds require 0 < vmin <= vmax")
    if not np.all(np.isfinite([base_mva, price, curvature, hours])):
        raise ValueError("base, price, curvature and duration must be finite")
    if base_mva <= 0 or hours <= 0 or curvature < 0:
        raise ValueError("base and duration must be positive and curvature nonnegative")
    if root_import_cap_mw is not None and not np.isfinite(root_import_cap_mw):
        raise ValueError("supply a finite signed root import cap or None")

    # Index 0 of each incoming vector denotes the slack injection. Entry j>0
    # denotes the sending end of the line terminating at bus j.
    incoming_p = cp.Variable(n, name="incoming_P_pu")
    incoming_q = cp.Variable(n, name="incoming_Q_pu")
    v = cp.Variable(n, name="voltage_squared")
    constraints = [v[0] == 1., v >= low**2, v <= high**2]
    import_mw = incoming_p[0] * base_mva
    if root_import_cap_mw is not None:
        constraints.append(import_mw <= root_import_cap_mw)
    if pwl is None:
        cost = price * import_mw
        if curvature:
            cost += 0.5 * curvature * cp.square(import_mw)
    else:
        knot, left, right = _vector(pwl, 3, "pwl")
        if curvature or left > right:
            raise ValueError("PWL slopes must be ordered and curvature zero")
        relative = import_mw - knot
        cost = cp.maximum(left * relative, right * relative) - max(-left * knot, -right * knot)

    backup_bus = None
    g = None
    if backup is not None:
        backup_bus, capacity, marginal_cost = backup
        backup_bus = _index(backup_bus)
        if not 0 <= backup_bus < n or not np.all(np.isfinite([capacity, marginal_cost])) or capacity < 0:
            raise ValueError("backup needs a valid bus, nonnegative finite capacity and finite cost")
        g = cp.Variable(nonneg=True, name="backup_MW")
        constraints.append(g <= capacity)
        cost += marginal_cost * g

    balance_p, balance_q = [], []
    series_current = {}
    for j in range(n):
        required_p = p[j] / base_mva + sum(incoming_p[k] for k in children[j])
        required_q = q[j] / base_mva + sum(incoming_q[k] for k in children[j])
        if j == backup_bus:
            required_p -= g / base_mva
        if j:
            edge = j - 1
            i = parents[edge]
            drop = 2 * (r[edge] * incoming_p[j] + x[edge] * incoming_q[j])
            v_child = v[i] - drop
            if not linearized and (r[edge] or x[edge]):
                ell = cp.Variable(nonneg=True, name=f"current_squared_{j}")
                series_current[j] = ell
                required_p += r[edge] * ell
                required_q += x[edge] * ell
                v_child += (r[edge]**2 + x[edge]**2) * ell
                constraints.append(cp.SOC(v[i] + ell, cp.hstack([
                    2 * incoming_p[j], 2 * incoming_q[j], v[i] - ell])))
                if np.isfinite(limits[edge]):
                    constraints.append(ell <= limits[edge]**2)
            elif np.isfinite(limits[edge]):
                # In the linearized or ideal branch, eliminate the current
                # variable but still enforce S^2 <= v_parent * Imax^2.
                constraints.append(cp.norm(cp.hstack([incoming_p[j], incoming_q[j]])) <=
                                   limits[edge] * cp.sqrt(v[i]))
            constraints.append(v[j] == v_child)
        # Required minus available makes the multipliers consumption prices.
        balance_p.append(required_p - incoming_p[j] == 0)
        balance_q.append(required_q - incoming_q[j] == 0)

    problem = cp.Problem(cp.Minimize(hours * cost), constraints + balance_p + balance_q)
    fields = ("objective", "import_mw", "import_mvar", "voltage_pu", "p_send_mw",
              "q_send_mvar", "dlmp", "dlmp_q", "loss_mw", "current_sq_pu", "backup_mw",
              "cone_abs", "cone_rel", "balance_max_pu", "voltage_eq_max_pu",
              "limit_violation_max_pu", "point_ac_residuals_pass")
    out = dict.fromkeys(fields)
    out.update(cone_rel_floor=1e-8, solver="CLARABEL", model="lindistflow" if linearized else "socp",
               point_abs_tol=1e-7, point_cone_rel_tol=1e-5, price_scope="network_model_balance_dual")
    try:
        problem.solve(solver=cp.CLARABEL, direct_solve_method="qdldl", max_iter=500,
                      tol_feas=1e-10, tol_gap_abs=1e-10, tol_gap_rel=1e-10)
    except cp.error.SolverError as exc:
        return dict(out, status="solver_error", error=str(exc))
    out["status"] = problem.status
    if problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        return out

    ps = np.asarray(incoming_p.value, dtype=float)
    qs = np.asarray(incoming_q.value, dtype=float)
    vs = np.asarray(v.value, dtype=float)
    if not np.all(np.isfinite([ps, qs, vs])) or np.any(vs <= 0):
        return dict(out, error="nonfinite powers or invalid voltage witness")
    gen = float(g.value) if g is not None else 0.
    sending_v = vs[np.asarray(parents, dtype=int)]
    apparent_sq = ps[1:]**2 + qs[1:]**2
    ell = apparent_sq / sending_v
    for j, variable in series_current.items():
        ell[j - 1] = float(variable.value)
    loss_p = np.zeros(n - 1) if linearized else r * ell
    loss_q = np.zeros(n - 1) if linearized else x * ell

    residual_p = p / base_mva - ps
    residual_q = q / base_mva - qs
    if backup_bus is not None:
        residual_p[backup_bus] -= gen / base_mva
    for j, i in enumerate(parents, start=1):
        residual_p[i] += ps[j]
        residual_q[i] += qs[j]
    residual_p[1:] += loss_p
    residual_q[1:] += loss_q
    balance_err = max(np.max(np.abs(residual_p)), np.max(np.abs(residual_q)))
    v_error = vs[1:] - sending_v + 2*(r * ps[1:] + x * qs[1:]) - r*loss_p - x*loss_q
    voltage_eq_err = max(abs(vs[0] - 1.), np.max(np.abs(v_error), initial=0.))
    vmag = np.sqrt(vs)
    # Voltage and current violations use magnitudes. Powers use per unit.
    limit_err = max(0., np.max(low - vmag), np.max(vmag - high), np.max(-ell, initial=0.),
                    np.max(np.sqrt(np.maximum(ell, 0.)) - limits, initial=0.))
    if backup_bus is not None:
        limit_err = max(limit_err, -gen / base_mva, (gen - capacity) / base_mva)
    if root_import_cap_mw is not None:
        limit_err = max(limit_err, ps[0] - root_import_cap_mw / base_mva)

    if not linearized:
        cone_error = np.abs(apparent_sq - sending_v * ell)
        out["cone_abs"] = float(np.max(cone_error, initial=0.))
        out["cone_rel"] = float(np.max(cone_error / np.maximum(sending_v * ell, out["cone_rel_floor"]),
                                       initial=0.))
        out["point_ac_residuals_pass"] = bool(problem.status == cp.OPTIMAL and
            max(balance_err, voltage_eq_err, limit_err, out["cone_abs"]) <= out["point_abs_tol"] and
            out["cone_rel"] <= out["point_cone_rel_tol"])

    dual_scale = float(hours * base_mva)
    out.update(objective=float(problem.value), import_mw=float(ps[0] * base_mva),
               import_mvar=float(qs[0] * base_mva), voltage_pu=vmag.tolist(),
               p_send_mw=(ps[1:] * base_mva).tolist(), q_send_mvar=(qs[1:] * base_mva).tolist(),
               dlmp=[float(row.dual_value) / dual_scale for row in balance_p],
               dlmp_q=[float(row.dual_value) / dual_scale for row in balance_q],
               loss_mw=float(np.sum(loss_p) * base_mva), current_sq_pu=ell.tolist(),
               backup_mw=gen, balance_max_pu=float(balance_err),
               voltage_eq_max_pu=float(voltage_eq_err), limit_violation_max_pu=float(limit_err))
    return out


def price_depot_day(parent, r, x, background_mw, reactive_mvar, depot, fleet_kwh,
                    hours, upstream_prices, *, fd_steps_mw=(0.01, 0.001),
                    pwl_surcharge=None, **network):
    """Price a day of prescribed depot energy on independent feeder intervals.

    The depot uses unity power factor. Negative energy exports to the feeder.
    Each returned central or perturbed dispatch includes its physical checks.
    A price for the AC market requires subsequent independent AC validation.
    A PWL surcharge (knot, left, right) adds marginal slopes to each period's
    upstream price. The totals are relaxed-grid outputs. This interface
    returns no finite secant for an infeasible side.
    """
    energy = np.asarray(fleet_kwh, dtype=float)
    if energy.ndim != 1 or not energy.size or not np.all(np.isfinite(energy)):
        raise ValueError("fleet_kwh must be a finite nonempty slot vector")
    periods = len(energy)
    durations = _vector(hours, periods, "hours", allow_scalar=True)
    prices = _vector(upstream_prices, periods, "upstream_prices", allow_scalar=True)
    p = np.asarray(background_mw, dtype=float)
    q = np.asarray(reactive_mvar, dtype=float)
    depot = _index(depot)
    if (p.shape != (periods, len(parent)+1) or q.shape != p.shape
            or not 0 <= depot < p.shape[1] or np.any(durations <= 0)):
        raise ValueError("invalid day dimensions, depot or slot lengths")
    if not np.isfinite(p).all() or not np.isfinite(q).all():
        raise ValueError("background powers must be finite")
    if "pwl" in network:
        raise ValueError("use pwl_surcharge to retain the period-specific upstream price")
    if pwl_surcharge is not None:
        knot, left, right = _vector(pwl_surcharge, 3, "pwl_surcharge")
        if left > right or network.get("curvature", 0):
            raise ValueError("PWL surcharge needs ordered slopes and zero curvature")
    steps = tuple(float(step) for step in fd_steps_mw)
    if not steps or not all(np.isfinite(step) and step > 0 for step in steps):
        raise ValueError("finite-difference steps must be positive")
    dispatches = []
    for i in range(periods):
        load = p[i].copy()
        load[depot] += energy[i] / (1000 * durations[i])

        offer = None if pwl_surcharge is None else (knot, prices[i] + left, prices[i] + right)

        def evaluate(shift_mw):
            shifted = load.copy()
            shifted[depot] += shift_mw
            return solve_radial(parent, r, x, shifted, q[i], price=prices[i], hours=durations[i],
                                pwl=offer, **network)

        center = evaluate(0)
        sides = []
        for step in steps:
            minus, plus = evaluate(-step), evaluate(step)
            slopes = []
            for point, direction in ((minus, -1), (plus, 1)):
                if (point["status"] != cp.OPTIMAL or center["status"] != cp.OPTIMAL
                        or point["objective"] is None or center["objective"] is None):
                    slopes.append(None)
                else:
                    slopes.append((point["objective"] - center["objective"])
                                  / (direction * step * durations[i]))
            sides.append(dict(step_mw=step, minus=minus, plus=plus, left=slopes[0], right=slopes[1]))
        dispatches.append(dict(center=center, sides=sides))
    complete = all(d["center"]["status"] == cp.OPTIMAL and d["center"]["objective"] is not None
                   and d["center"]["dlmp"] is not None for d in dispatches)
    return {"periods": dispatches, "price_scope": "network_model_balance_dual",
            "all_center_point_checks_pass": all(d["center"]["point_ac_residuals_pass"] is True
                                                for d in dispatches),
            "grid_cost": sum(d["center"]["objective"] for d in dispatches) if complete else None,
            "depot_price_per_mwh": [d["center"]["dlmp"][depot] for d in dispatches] if complete
                                   else None}
