"""Balanced radial branch-flow OPF for one delivery interval.

Edges are oriented from parent to child. Positive nodal demand consumes power.
Fixed taps, branch pi shunts, and bus shunts are optional. Voltage angles are
free on this single-slack tree. Fixed transformer phase shifts affect recovered
angles but disappear from squared magnitudes and complex power balances.
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


def conic_options(solver):
    if solver == "CLARABEL":
        return dict(direct_solve_method="qdldl", max_iter=500, tol_feas=1e-10,
                    tol_gap_abs=1e-10, tol_gap_rel=1e-10)
    if solver == "GUROBI":
        return dict(Threads=1, QCPDual=1, BarQCPConvTol=1e-10, FeasibilityTol=1e-9,
                    OptimalityTol=1e-9, OutputFlag=0)
    raise ValueError("choose CLARABEL or GUROBI")


def solve_radial(parent, r, x, p_mw, q_mvar, *, base_mva=1., price=50.,
                 curvature=0., hours=1., vmin=.90, vmax=1.10, imax_pu=None,
                 pwl=None, linearized=False, backup=None, root_import_cap_mw=None,
                 slack_vm_pu=1., tap_ratio=1., g_from_pu=0., b_from_pu=0.,
                 g_to_pu=0., b_to_pu=0., imax_from_pu=None, imax_to_pu=None,
                 g_bus_pu=0., b_bus_pu=0., open_end_leaves=(), solver="CLARABEL"):
    """Return the conic solver's status, primal witness, balance prices and residuals.

    Buses are ordered 0..n-1. parent[j-1] is upstream of bus j. r and x are
    per-unit series impedances on base_mva. vmin and vmax bound voltage
    magnitudes. imax_pu bounds series current magnitude, with None or +inf
    denoting an absent limit. Each bound may be a scalar or a full vector.

    tap_ratio is the fixed positive turns ratio on the per-unit voltage bases,
    with transformed sending voltage W = V_parent / tap (phase omitted).
    The series impedance joins W to V_child. The from/to shunt admittances
    g + jb are attached at W and V_child respectively, so positive b injects
    reactive power. g_bus_pu and b_bus_pu are additional nodal admittances.
    imax_from_pu and imax_to_pu bound terminal currents in their respective
    bus bases, including excitation/charging current. Terminal powers are
    positive into the branch. current_sq_pu is the series squared current.
    loss_mw includes all shunt conductances in addition to series losses.
    The linearized model omits series losses and the quadratic voltage term.

    For the SOCP, open_end_leaves optionally lists downstream BUS indices of
    known passive open ends. Each marked bus must have zero external P and Q,
    no child, and no backup. Its shunts remain energized. The physical affine
    series-current identity at each such end tightens the general relaxation.
    Its demand cannot be varied in this model, so its balance price is None.

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
    marked = tuple(_index(j) for j in open_end_leaves)
    open_ends = set(marked)
    if len(open_ends) != len(marked) or (linearized and open_ends):
        raise ValueError("open ends require distinct bus indices and the SOCP model")
    for j in open_ends:
        if not 0 < j < n or children[j] or p[j] != 0. or q[j] != 0.:
            raise ValueError("each open end must be a downstream leaf with zero external P and Q")
    low = _vector(vmin, n, "vmin", allow_scalar=True)
    high = _vector(vmax, n, "vmax", allow_scalar=True)
    tap = _vector(tap_ratio, n - 1, "tap_ratio", allow_scalar=True)
    if np.any(tap <= 0) or not np.isfinite(slack_vm_pu) or slack_vm_pu <= 0:
        raise ValueError("tap ratios and slack magnitude must be finite and positive")
    g_from = _vector(g_from_pu, n - 1, "g_from_pu", allow_scalar=True)
    b_from = _vector(b_from_pu, n - 1, "b_from_pu", allow_scalar=True)
    g_to = _vector(g_to_pu, n - 1, "g_to_pu", allow_scalar=True)
    b_to = _vector(b_to_pu, n - 1, "b_to_pu", allow_scalar=True)
    # Collect the pi terminal shunts into the bus balances. The sending-side
    # shunt draws (g - jb) |V_parent|² / tap². The ideal tap consumes no power.
    shunt_g = _vector(g_bus_pu, n, "g_bus_pu", allow_scalar=True).copy()
    shunt_b = _vector(b_bus_pu, n, "b_bus_pu", allow_scalar=True).copy()
    parent_idx = np.asarray(parents, dtype=int)
    np.add.at(shunt_g, parent_idx, g_from / tap**2)
    np.add.at(shunt_b, parent_idx, b_from / tap**2)
    shunt_g[1:] += g_to
    shunt_b[1:] += b_to

    def ratings(values, name):
        values = _vector(np.inf if values is None else values, n - 1, name,
                         allow_scalar=True, allow_infinity=True)
        if np.any(values < 0):
            raise ValueError(f"{name} must be nonnegative")
        return values

    limits = ratings(imax_pu, "imax_pu")
    limits_from = ratings(imax_from_pu, "imax_from_pu")
    limits_to = ratings(imax_to_pu, "imax_to_pu")
    if np.any(r < 0) or np.any(x < 0):
        raise ValueError("series impedance components must be nonnegative")
    if np.any(low <= 0) or np.any(low > high):
        raise ValueError("voltage bounds require 0 < vmin <= vmax")
    if not np.all(np.isfinite([base_mva, price, curvature, hours])):
        raise ValueError("base, price, curvature and duration must be finite")
    if base_mva <= 0 or hours <= 0 or curvature < 0:
        raise ValueError("base and duration must be positive and curvature nonnegative")
    if root_import_cap_mw is not None and not np.isfinite(root_import_cap_mw):
        raise ValueError("supply a finite signed root import cap or None")

    # Index 0 of each incoming vector denotes the slack injection. Entry j>0
    # denotes the series-element input, excluding both terminal shunts.
    incoming_p = cp.Variable(n, name="incoming_P_pu")
    incoming_q = cp.Variable(n, name="incoming_Q_pu")
    v = cp.Variable(n, name="voltage_squared")
    constraints = [v[0] == slack_vm_pu**2, v >= low**2, v <= high**2]
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
        if backup_bus in open_ends:
            raise ValueError("a passive open end cannot have a backup source")
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
        if shunt_g[j]:
            required_p += shunt_g[j] * v[j]
        if shunt_b[j]:
            required_q -= shunt_b[j] * v[j]
        if j == backup_bus:
            required_p -= g / base_mva
        if j:
            edge = j - 1
            i = parents[edge]
            w = v[i] if tap[edge] == 1. else v[i] / tap[edge]**2
            drop = 2 * (r[edge] * incoming_p[j] + x[edge] * incoming_q[j])
            v_child = w - drop
            if not linearized and (r[edge] or x[edge] or j in open_ends):
                if j in open_ends:
                    # KCL at a passive leaf: I_series = (y_to + y_bus) V_child.
                    # Together with V_child = W - z I_series, this identity
                    # implies the series cone equality without a lifted variable.
                    ell = (shunt_g[j]**2 + shunt_b[j]**2) * v[j]
                else:
                    ell = cp.Variable(nonneg=True, name=f"current_squared_{j}")
                    constraints.append(cp.SOC(w + ell, cp.hstack([
                        2 * incoming_p[j], 2 * incoming_q[j], w - ell])))
                series_current[j] = ell
                required_p += r[edge] * ell
                required_q += x[edge] * ell
                v_child += (r[edge]**2 + x[edge]**2) * ell
                if np.isfinite(limits[edge]):
                    constraints.append(ell <= limits[edge]**2)
                # If U_child = W - zI, the terminal currents are
                # (I + y_from W)/tap and -I + y_to U_child (angle gauge).
                # Their squared norms are affine in the lifted variables.
                if np.isfinite(limits_from[edge]):
                    cross = g_from[edge] * incoming_p[j] - b_from[edge] * incoming_q[j]
                    y_sq = g_from[edge]**2 + b_from[edge]**2
                    constraints.append(ell + 2*cross + y_sq*w <=
                                       (limits_from[edge] * tap[edge])**2)
                if np.isfinite(limits_to[edge]):
                    cross = (g_to[edge] * (incoming_p[j] - r[edge]*ell)
                             - b_to[edge] * (incoming_q[j] - x[edge]*ell))
                    y_sq = g_to[edge]**2 + b_to[edge]**2
                    constraints.append(ell - 2*cross + y_sq*v[j] <= limits_to[edge]**2)
            else:
                # No free current variable for an ideal or linearized edge.
                for limit, vp, real, imag in (
                    (limits[edge], w, incoming_p[j], incoming_q[j]),
                    (limits_from[edge], v[i], incoming_p[j] + g_from[edge]*w,
                     incoming_q[j] - b_from[edge]*w),
                    (limits_to[edge], v[j], -incoming_p[j] + g_to[edge]*v[j],
                     -incoming_q[j] - b_to[edge]*v[j])):
                    if np.isfinite(limit):
                        constraints.append(cp.norm(cp.hstack([real, imag])) <= limit * cp.sqrt(vp))
            constraints.append(v[j] == v_child)
        # Required minus available makes the multipliers consumption prices.
        balance_p.append(required_p - incoming_p[j] == 0)
        balance_q.append(required_q - incoming_q[j] == 0)

    problem = cp.Problem(cp.Minimize(hours * cost), constraints + balance_p + balance_q)
    fields = ("objective", "import_mw", "import_mvar", "voltage_pu", "p_send_mw",
              "q_send_mvar", "p_to_mw", "q_to_mvar", "p_series_send_mw", "q_series_send_mvar",
              "dlmp", "dlmp_q", "loss_mw", "series_loss_mw", "shunt_loss_mw",
              "current_sq_pu", "current_from_pu", "current_to_pu", "backup_mw",
              "cone_abs", "cone_rel", "balance_max_pu", "voltage_eq_max_pu",
              "limit_violation_max_pu", "point_ac_residuals_pass")
    out = dict.fromkeys(fields)
    solver = solver.upper()
    options = conic_options(solver)
    out.update(cone_rel_floor=1e-8, solver=solver, model="lindistflow" if linearized else "socp",
               formulation="passive_open_end_reduction" if open_ends else "general",
               open_end_leaves=sorted(open_ends),
               point_abs_tol=1e-7, point_cone_rel_tol=1e-5, price_scope="network_model_balance_dual")
    try:
        problem.solve(solver=solver, **options)
    except Exception as exc:
        # CVXPY may propagate an external solver's license/initialization exception.
        return dict(out, status="solver_error", error=f"{type(exc).__name__}: {exc}")
    out["status"] = problem.status
    if problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        return out

    ps = np.asarray(incoming_p.value, dtype=float)
    qs = np.asarray(incoming_q.value, dtype=float)
    vs = np.asarray(v.value, dtype=float)
    if not np.all(np.isfinite([ps, qs, vs])) or np.any(vs <= 0):
        return dict(out, error="nonfinite powers or invalid voltage witness")
    gen = float(g.value) if g is not None else 0.
    sending_v = vs[parent_idx] / tap**2
    apparent_sq = ps[1:]**2 + qs[1:]**2
    ell = apparent_sq / sending_v
    for j, variable in series_current.items():
        ell[j - 1] = float(variable.value)
    loss_p = np.zeros(n - 1) if linearized else r * ell
    loss_q = np.zeros(n - 1) if linearized else x * ell
    p_series, q_series = ps[1:], qs[1:]
    p_from, q_from = p_series + g_from*sending_v, q_series - b_from*sending_v
    p_to, q_to = -p_series + loss_p + g_to*vs[1:], -q_series + loss_q - b_to*vs[1:]
    if linearized:
        from_sq = (p_from**2 + q_from**2) / vs[parent_idx]
        to_sq = (p_to**2 + q_to**2) / vs[1:]
    else:
        from_sq = (ell + 2*(g_from*p_series - b_from*q_series)
                   + (g_from**2 + b_from**2)*sending_v) / tap**2
        to_sq = (ell - 2*(g_to*(p_series-loss_p) - b_to*(q_series-loss_q))
                 + (g_to**2 + b_to**2)*vs[1:])
    i_from = np.sqrt(np.maximum(from_sq, 0.))
    i_to = np.sqrt(np.maximum(to_sq, 0.))

    residual_p = p / base_mva + shunt_g * vs - ps
    residual_q = q / base_mva - shunt_b * vs - qs
    if backup_bus is not None:
        residual_p[backup_bus] -= gen / base_mva
    for j, i in enumerate(parents, start=1):
        residual_p[i] += ps[j]
        residual_q[i] += qs[j]
    residual_p[1:] += loss_p
    residual_q[1:] += loss_q
    balance_err = max(np.max(np.abs(residual_p)), np.max(np.abs(residual_q)))
    v_error = vs[1:] - sending_v + 2*(r * ps[1:] + x * qs[1:]) - r*loss_p - x*loss_q
    voltage_eq_err = max(abs(vs[0] - slack_vm_pu**2), np.max(np.abs(v_error), initial=0.))
    vmag = np.sqrt(vs)
    # Voltage and current violations use magnitudes. Powers use per unit.
    limit_err = max(0., np.max(low - vmag), np.max(vmag - high), np.max(-ell, initial=0.),
                    np.max(np.sqrt(np.maximum(ell, 0.)) - limits, initial=0.),
                    np.max(-from_sq, initial=0.), np.max(-to_sq, initial=0.),
                    np.max(i_from - limits_from, initial=0.), np.max(i_to - limits_to, initial=0.))
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
               p_send_mw=(p_from * base_mva).tolist(), q_send_mvar=(q_from * base_mva).tolist(),
               p_to_mw=(p_to * base_mva).tolist(), q_to_mvar=(q_to * base_mva).tolist(),
               p_series_send_mw=(p_series * base_mva).tolist(),
               q_series_send_mvar=(q_series * base_mva).tolist(),
               dlmp=[None if j in open_ends or row.dual_value is None else float(row.dual_value) / dual_scale
                     for j, row in enumerate(balance_p)],
               dlmp_q=[None if j in open_ends or row.dual_value is None else float(row.dual_value) / dual_scale
                       for j, row in enumerate(balance_q)],
               loss_mw=float((np.sum(loss_p) + shunt_g @ vs) * base_mva),
               series_loss_mw=float(np.sum(loss_p) * base_mva),
               shunt_loss_mw=float((shunt_g @ vs) * base_mva), current_sq_pu=ell.tolist(),
               current_from_pu=i_from.tolist(), current_to_pu=i_to.tolist(),
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
    if "open_end_leaves" in network:
        marked = tuple(_index(j) for j in network["open_end_leaves"])
        for j in marked:
            if not 0 < j < p.shape[1] or j == depot or np.any(p[:, j]) or np.any(q[:, j]):
                raise ValueError("a passive open end cannot take a depot or background injection")
        network["open_end_leaves"] = marked  # also preserve one-shot iterables across solves
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
