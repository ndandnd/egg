"""A3-A5 stabilization mathematics for B2 certified column generation.

Normative specification: doc/B2_STABILIZATION_SPEC.md. This module contains
ONLY the stabilization machinery — stabilized/smoothed candidate-price
generation and the exact serious/null-step and parameter-update rules. The
certification loop, clean RMP, transactional checkpoints, and all bound
accounting live in egglab.b2a2 and are shared verbatim with A2.

Contract reminders (enforced by the caller):
- the stabilized master's objective/solution is NEVER a bound;
- Theta_cert of stabilized calls is diagnostic only, never folded into
  LB_best;
- every candidate pricing solution passes replay validation before any
  checkpoint advances.
"""
from __future__ import annotations

import math

import mip
import numpy as np

from .market import AffineMarket
from .solver import optimize, new_model

SERIOUS_TOL = 1e-9

# prespecified parameters (doc/B2_STABILIZATION_SPEC.md; not tuned on any
# evaluation cell)
A3_D1_FRAC = 0.05
A3_D2_OVER_D1 = 10.0
A3_ZETA1 = 0.1
A3_ZETA2 = 100.0
A3_D1_MIN_FRAC = 1e-4
A4_ALPHA0 = 0.5
A4_ALPHA_MAX = 0.99
A5_T0 = 1.0
A5_T_MIN = 1e-4
A5_K = 16
A5_W_FRAC = 2.0

METHODS = ("a3", "a4", "a5")


def initial_stab_state(method: str, market: AffineMarket) -> dict:
    """Center pi_hat^0 = -(a + b U) (posted marginal price at zero fleet
    load) plus method parameters at their prespecified initial values."""
    pi0 = [-float(x) for x in (market.a + market.b * market.U)]
    st = {"center": pi0, "theta_best": None,
          "serious_steps": 0, "null_steps": 0}
    if method == "a3":
        st["d1"] = [A3_D1_FRAC * (1.0 + abs(p)) for p in pi0]
        st["d1_min"] = [A3_D1_MIN_FRAC * (1.0 + abs(p)) for p in pi0]
    elif method == "a4":
        st["alpha"] = A4_ALPHA0
    elif method == "a5":
        st["t"] = A5_T0
        st["w"] = [A5_W_FRAC * (1.0 + abs(p)) for p in pi0]
    else:
        raise ValueError(f"unknown stabilized method {method!r}")
    return st


def stab_identity_params(method: str) -> dict:
    """The prespecified constants that enter the resume identity."""
    base = {"spec": "doc/B2_STABILIZATION_SPEC.md", "serious_tol": SERIOUS_TOL}
    if method == "a3":
        base.update(d1_frac=A3_D1_FRAC, d2_over_d1=A3_D2_OVER_D1,
                    zeta1=A3_ZETA1, zeta2=A3_ZETA2, d1_min_frac=A3_D1_MIN_FRAC)
    elif method == "a4":
        base.update(alpha0=A4_ALPHA0, alpha_max=A4_ALPHA_MAX,
                    rule="pessoa-subgradient-in-out (spec Section 2)")
    elif method == "a5":
        base.update(t0=A5_T0, t_min=A5_T_MIN, pieces=A5_K, w_frac=A5_W_FRAC,
                    penalty_model="chord-pwl (spec Section 3)")
    return base


# ---------------------------------------------------------------------------
# certified Lagrangian value (weak duality; valid at ANY price vector)
# ---------------------------------------------------------------------------
def conj_true(market: AffineMarket, prices) -> float:
    """sum_t max_{L>=0} [p_t L - DeltaC_t(L)] = sum_t max(0, p_t-c1_t)^2/(2 b_t)."""
    p = np.asarray(prices, dtype=float)
    c1 = market.a + market.b * market.U
    total = 0.0
    for t in range(market.n_slots):
        excess = p[t] - c1[t]
        if excess <= 0:
            continue
        if market.b[t] <= 0:
            return float("inf")  # linear cost row: conjugate unbounded
        total += excess * excess / (2.0 * float(market.b[t]))
    return float(total)


def lagrangian_L_star(market: AffineMarket, prices) -> np.ndarray:
    """argmin_L DeltaC_true(L) - p^T L  (per slot, closed form)."""
    p = np.asarray(prices, dtype=float)
    c1 = market.a + market.b * market.U
    b = np.where(market.b > 0, market.b, 1.0)
    return np.maximum(0.0, (p - c1) / b)


def theta_cert(market: AffineMarket, prices, pricing_bound: float) -> float:
    """Certified dual value Theta_cert(p) <= z_CH (spec Section 0)."""
    c = conj_true(market, prices)
    if not math.isfinite(c):
        return -float("inf")
    return float(pricing_bound) - c


# ---------------------------------------------------------------------------
# stabilized masters (A3 du Merle 5-piece; A5 chord-PWL proximal)
# ---------------------------------------------------------------------------
def _add_penalty_pair(m, link_terms, t, breakpoint_hi, breakpoint_lo, slope):
    """One +/- primal penalty pair on link row t: y+ (coeff +1, cost
    breakpoint_hi, ub slope) and y- (coeff -1, cost -breakpoint_lo, ub
    slope). LP duality turns these into dual penalty slopes `slope` beyond
    the breakpoints (spec Sections 1 and 3)."""
    yp = m.add_var(lb=0.0, ub=slope)
    ym = m.add_var(lb=0.0, ub=slope)
    link_terms[t].append(yp - ym)
    return breakpoint_hi * yp - breakpoint_lo * ym


def solve_stabilized_rmp(inst, market: AffineMarket, columns, tangent_points,
                         method: str, stab: dict, pwl_tol: float,
                         solve_id_prefix: str):
    """Solve the A3/A5 stabilized RMP; return its link duals (candidate
    duals) and full solve evidence. The objective/solution is NEVER used as
    a bound — only the duals leave this function (plus evidence)."""
    from .b2a2 import B2A2Error  # local import to avoid a cycle
    from .regimes import _l_max

    T = market.n_slots
    center = stab["center"]
    m = new_model(f"b2-{method}-stab")
    lam = [m.add_var(lb=0.0) for _ in columns]
    L = [m.add_var(lb=0.0) for _ in range(T)]
    cost = [m.add_var(lb=0.0) for _ in range(T)]
    penalty_obj = []
    link_terms = [[] for _ in range(T)]
    for t in range(T):
        if method == "a3":
            d1 = stab["d1"][t]
            d2 = A3_D2_OVER_D1 * d1
            penalty_obj.append(_add_penalty_pair(
                m, link_terms, t, center[t] + d1, center[t] - d1, A3_ZETA1))
            penalty_obj.append(_add_penalty_pair(
                m, link_terms, t, center[t] + d2, center[t] - d2, A3_ZETA2))
        else:  # a5: chord PWL of |pi - center|^2 / (2 t), K pieces per side
            h = stab["w"][t] / A5_K
            slope = h / stab["t"]  # incremental dual slope per piece
            for k in range(A5_K):
                u = k * h
                penalty_obj.append(_add_penalty_pair(
                    m, link_terms, t, center[t] + u, center[t] - u, slope))
    link = []
    for t in range(T):
        c = m.add_constr(
            mip.xsum(lam[j] * float(columns[j]["load"][t])
                     for j in range(len(columns)))
            - L[t] + mip.xsum(link_terms[t]) == 0)
        link.append(c)
    m.add_constr(mip.xsum(lam) == 1)
    l_max = _l_max(inst)
    base_segs = market.system_delta_segments(l_max, 8)
    for t in range(T):
        for (sl, ic) in base_segs[t]:
            m += cost[t] >= sl * L[t] + ic
    for tp in tangent_points:
        segs = market.system_delta_tangents_at(np.asarray(tp))
        for t in range(T):
            sl, ic = segs[t]
            m += cost[t] >= sl * L[t] + ic
    m.objective = (
        mip.xsum(lam[j] * float(columns[j]["ops_cost"])
                 for j in range(len(columns)))
        + mip.xsum(cost) + mip.xsum(penalty_obj))
    st = optimize(m, solve_lp_first=False)
    solve_rec = {
        "solve_id": solve_id_prefix,
        "stabilized": True,
        "backend": st.backend,
        "status": st.status,
        "obj": st.obj,
        "bound": st.bound,
        "mip_gap": st.mip_gap,
        "n_vars": st.n_vars,
        "n_int": st.n_int,
        "n_constrs": st.n_constrs,
        "wall_s": st.wall_s,
        "threads": st.extra.get("threads"),
    }
    if st.status != "OPTIMAL":
        raise B2A2Error(f"stabilized {method} master not OPTIMAL: {st.status}")
    pi_stab = [float(c.pi) for c in link]
    return pi_stab, solve_rec


# ---------------------------------------------------------------------------
# candidate generation
# ---------------------------------------------------------------------------
def candidate_duals(inst, market, columns, tangent_points, method, stab,
                    pi_clean, pwl_tol, solve_id_prefix):
    """Return (pi_cand, master_solves) for one stabilized candidate step."""
    if method == "a4":
        a = stab["alpha"]
        pi_cand = [a * c + (1.0 - a) * o
                   for c, o in zip(stab["center"], pi_clean)]
        return pi_cand, []
    pi_cand, solve_rec = solve_stabilized_rmp(
        inst, market, columns, tangent_points, method, stab, pwl_tol,
        solve_id_prefix)
    return pi_cand, [solve_rec]


# ---------------------------------------------------------------------------
# exact serious/null-step and parameter updates (spec Sections 1-3)
# ---------------------------------------------------------------------------
def serious_step(theta_best, theta_cand) -> bool:
    if theta_best is None:
        return True
    return theta_cand > theta_best + SERIOUS_TOL


def a3_update(stab: dict, serious: bool, pi_cand) -> dict:
    if serious:
        stab["center"] = [float(x) for x in pi_cand]
        stab["d1"] = [max(dmin, d / 2.0)
                      for d, dmin in zip(stab["d1"], stab["d1_min"])]
        stab["serious_steps"] += 1
    else:
        stab["null_steps"] += 1
    return stab


def a4_alpha_update(alpha: float, g, direction) -> float:
    """Pessoa-style automatic alpha (spec Section 2): <g, d> > 0 means the
    dual function still rises toward the out point -> less smoothing;
    otherwise the out point overshoots -> more smoothing."""
    inner = float(np.dot(np.asarray(g, dtype=float),
                         np.asarray(direction, dtype=float)))
    if inner > 0.0:
        return max(0.0, alpha - 0.1)
    return min(A4_ALPHA_MAX, alpha + (1.0 - alpha) / 10.0)


def a4_update(stab: dict, serious: bool, pi_cand, g, direction) -> dict:
    stab["alpha"] = a4_alpha_update(stab["alpha"], g, direction)
    if serious:
        stab["center"] = [float(x) for x in pi_cand]
        stab["serious_steps"] += 1
    else:
        stab["null_steps"] += 1
    return stab


def a5_update(stab: dict, serious: bool, pi_cand) -> dict:
    if serious:
        stab["center"] = [float(x) for x in pi_cand]
        stab["serious_steps"] += 1
    else:
        stab["t"] = max(A5_T_MIN, stab["t"] / 2.0)
        stab["null_steps"] += 1
    return stab


def apply_update(method: str, stab: dict, serious: bool, pi_cand,
                 g=None, direction=None) -> dict:
    if method == "a3":
        return a3_update(stab, serious, pi_cand)
    if method == "a4":
        return a4_update(stab, serious, pi_cand, g, direction)
    if method == "a5":
        return a5_update(stab, serious, pi_cand)
    raise ValueError(method)
