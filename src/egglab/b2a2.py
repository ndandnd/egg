"""B2-A2: certified plain column generation on the schedule-column master.

MATHEMATICAL FORMULATION
========================
The dictator problem is  z_D = min_S  ops(S) + DeltaC(e(S))  over complete
feasible fleet schedules S, where e(S) is the hourly charging-load vector and
DeltaC(L) = sum_t [ (a_t + b_t U_t) L_t + b_t L_t^2 / 2 ]  is the convex
separable true system-cost increment (identical to regimes.solve_dictator).

Schedule-column convex-hull master (one fleet convexity block):

    z_CH = min   sum_j  lambda_j c_j  +  DeltaC(L)
           s.t.  sum_j  lambda_j e_{jt}  -  L_t  =  0      (link_t, dual pi_t)
                 sum_j  lambda_j              =  1          (conv,  dual sigma)
                 lambda_j >= 0,  L_t >= 0,

where column j is a complete feasible fleet schedule with operating cost c_j
and load vector e_j. z_CH <= z_D (the integer optimum picks lambda integral),
and z_D - z_CH is the B3 uplift.

CONVEX-COST REPRESENTATION AND TOLERANCE PROPAGATION
====================================================
DeltaC is represented in the LP by tangent epigraph cuts (a convex LOWER
model). Therefore the solved RMP's LP value z_model under-estimates the true
restricted value. After each solve we evaluate the TRUE quadratic at the RMP
solution (lambda*, L*):

    UB_CH := sum_j lambda*_j c_j + DeltaC_true(L*)          (exact evaluation)

which is a valid upper bound on z_CH because (lambda*, L*) is feasible for
the true master. An inner refinement loop adds tangents at L* and re-solves
(no oracle calls) until UB_CH - z_model <= pwl_tol (default 1e-3), so the
model slack is explicitly bounded and propagated into the certificate.

UB_CH is always the objective of the ORDINARY, UNSTABILIZED restricted
master over all generated columns, with exact cost evaluation — never a
penalized, proximal, smoothed, or box surrogate.

LOWER BOUND AND REDUCED-COST SIGN CONVENTION
============================================
Duals are taken from the clean RMP LP written EXACTLY as above
(link_t:  sum_j lambda_j e_{jt} - L_t = 0, dual pi_t; conv: dual sigma).
The reduced cost of a candidate column S is

    rc(S) = ops(S) - sum_t pi_t e_t(S) - sigma.

Hence exact pricing is the certified taker EVSP oracle at ORACLE PRICES

    p_t := -pi_t        (sign convention: oracle price = MINUS link dual)

because  min_S [ops(S) + sum_t p_t e_t(S)] = min_S [ops(S) - sum_t pi_t e_t(S)],
so  min_rc = oracle_optimal_objective - sigma. At the RMP optimum the LP's
own L_t variables price out to  pi_t = dDeltaC_model/dL_t >= 0 (marginal
model cost)... NOTE the orientation: with the constraint written
(sum lambda e) - L = 0, increasing L relaxes nothing by itself; python-mip
returns pi such that p = -pi equals the model marginal cost of load, which
is nonnegative at optimality (numerically verified in the tiny-enumeration
tests; transient CG duals may wander).

With ONE convexity block, the Lasdon bound gives, for the solved LP,

    LB_CH = z_model + min(0, min_rc)

valid for the PWL master and hence (tangent model <= true) for z_CH itself:
LB_CH <= z_CH^pwl <= z_CH <= UB_CH.

CERTIFICATION AND INVARIANTS
============================
- certified termination iff  UB_CH - LB_best <= epsilon (default 1e-2);
- LB_best is the running maximum of valid lower bounds (monotone up);
- UB_CH is nonincreasing after every valid column addition + clean-RMP
  reoptimization within tol_mono = pwl_tol + 1e-6 (enforced, loud failure);
- every oracle solve must be OPTIMAL and replay-valid (loud failure);
- duplicate columns are never added; a duplicate with materially negative
  reduced cost after refinement raises after MAX_DUPLICATE retries;
- atomic per-oracle-call checkpoints; resume re-solves at most the one
  in-flight oracle call, never loses columns, and re-validates stored
  bounds (LB_best <= UB + tol) before continuing.

B3 UPLIFT INTERVAL
==================
With the dictator solved independently (obj_true = z_D_ub, tolerance tol_D):
    uplift = z_D - z_CH  in  [ (z_D_ub - tol_D) - UB_CH,  z_D_ub - LB_best ].
"""
from __future__ import annotations

import hashlib
import json
import os
import time

import mip
import numpy as np

from . import checkpoint
from .evsp import validate_solution
from .instance import Instance
from .market import AffineMarket
from .records import append_jsonl, make_record, provenance
from .regimes import _l_max, solve_taker
from .solver import SolveStats, new_model, optimize

EPSILON_DEFAULT = 1e-2
PWL_TOL = 1e-3
RC_TOL = 1e-6
MAX_DUPLICATE_RETRIES = 3
TOL_MONO = PWL_TOL + 1e-6


class B2A2Error(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# schedule columns
# ---------------------------------------------------------------------------
def column_from_solution(inst: Instance, sol) -> dict:
    """Schedule column: complete feasible schedule + load + cost + hashes +
    replay evidence (requirement 1)."""
    violations = validate_solution(inst, sol)
    if violations:
        raise B2A2Error(f"oracle produced replay-invalid column: {violations}")
    if sol.stats is None or sol.stats.status != "OPTIMAL":
        raise B2A2Error(
            f"oracle status {'missing' if sol.stats is None else sol.stats.status}"
            " != OPTIMAL")
    col = {
        "sequences": [list(s) for s in sol.sequences],
        "arc_kinds": [list(k) for k in sol.arc_kinds],
        "charges": sol.charges,
        "load": [float(x) for x in sol.load],
        "ops_cost": float(sol.ops_cost),
        "fleet": int(sol.fleet),
        "schedule_hash": sol.schedule_hash(),
        "load_hash": sol.load_hash(),
        "instance_hash": inst.hash(),
        "replay_ok": True,
        "replay_violations": [],
        "oracle_stats": sol.stats.to_dict(),
    }
    col["column_key"] = column_key(col)
    return col


def column_key(col: dict) -> str:
    canon = json.dumps(
        [sorted(tuple(s) for s in col["sequences"]),
         [round(x, 6) for x in col["load"]]])
    return hashlib.sha256(canon.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# clean restricted master (pure LP; UB via exact evaluation)
# ---------------------------------------------------------------------------
def solve_rmp(inst: Instance, market: AffineMarket, columns: list,
              tangent_points: list, pwl_tol: float = PWL_TOL):
    """Solve the clean unstabilized RMP with inner tangent refinement.
    Returns dict with z_model, ub (exact evaluation), lambdas, L, duals pi,
    sigma, wall time, and possibly-extended tangent_points."""
    if not columns:
        raise B2A2Error("RMP requires at least one column")
    T = market.n_slots
    l_max = _l_max(inst)
    wall = 0.0
    tangent_points = [list(map(float, tp)) for tp in tangent_points]
    for _refine in range(200):
        m = new_model("b2a2-rmp")
        lam = [m.add_var(lb=0.0) for _ in columns]
        L = [m.add_var(lb=0.0) for _ in range(T)]
        cost = [m.add_var(lb=0.0) for _ in range(T)]
        link = []
        for t in range(T):
            c = m.add_constr(
                mip.xsum(lam[j] * float(columns[j]["load"][t])
                         for j in range(len(columns))) - L[t] == 0)
            link.append(c)
        conv = m.add_constr(mip.xsum(lam) == 1)
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
            + mip.xsum(cost))
        t0 = time.time()
        st = optimize(m, solve_lp_first=False)
        wall += time.time() - t0
        if st.status != "OPTIMAL":
            raise B2A2Error(f"clean RMP not OPTIMAL: {st.status}")
        z_model = float(st.obj)
        lam_v = [float(v.x or 0.0) for v in lam]
        L_v = np.array([float(v.x or 0.0) for v in L])
        ops_part = sum(lam_v[j] * float(columns[j]["ops_cost"])
                       for j in range(len(columns)))
        ub = ops_part + market.system_delta_true(L_v)  # exact evaluation
        if ub - z_model <= pwl_tol:
            pi = [float(c.pi) for c in link]
            sigma = float(conv.pi)
            return {
                "z_model": z_model, "ub": ub, "lambdas": lam_v,
                "L": [float(x) for x in L_v], "pi": pi, "sigma": sigma,
                "master_wall_s": wall, "tangent_points": tangent_points,
                "n_refinements": _refine,
            }
        tangent_points.append([float(x) for x in L_v])
    raise B2A2Error("tangent refinement failed to close the PWL slack")


# ---------------------------------------------------------------------------
# certified plain CG (A2)
# ---------------------------------------------------------------------------
def certified_cg(
    inst: Instance,
    market: AffineMarket,
    epsilon: float = EPSILON_DEFAULT,
    budget: int = 240,
    out_dir: str = "runs/b2a2",
    tag: str = "cg",
    experiment: str = "b2a2",
    pwl_tol: float = PWL_TOL,
    solver_kw: dict | None = None,
    z_d_ub: float | None = None,
    tol_d: float = 1e-2,
) -> dict:
    """Run A2 to certification (UB_CH - LB_best <= epsilon) or budget
    exhaustion. Checkpointed per oracle call; resumable; invariant-enforced."""
    solver_kw = solver_kw or {}
    os.makedirs(out_dir, exist_ok=True)
    ck_path = os.path.join(out_dir, f"{tag}.cg.ckpt.json")
    it_path = os.path.join(out_dir, f"{tag}.iterations.jsonl")
    oc_path = os.path.join(out_dir, f"{tag}.oracle.jsonl")

    state = checkpoint.load(ck_path, default={
        "columns": [], "keys": [], "tangent_points": [],
        "oracle_calls": 0, "lb_best": -float("inf"),
        "ub_history": [], "lb_history": [],
        "duplicate_retries": 0, "done": False, "outcome": None,
        "epsilon": epsilon, "budget": budget, "pwl_tol": pwl_tol,
        "instance_hash": inst.hash(),
    })
    if state["done"]:
        return state
    if state["instance_hash"] != inst.hash():
        raise B2A2Error("checkpoint/instance hash mismatch")
    # resume sanity: stored bounds must be consistent
    if state["ub_history"] and state["lb_best"] > min(
            u for u in state["ub_history"]) + TOL_MONO + epsilon:
        raise B2A2Error(
            f"corrupt checkpoint: LB_best {state['lb_best']} exceeds "
            f"best UB {min(state['ub_history'])}")

    def record_iteration(rmp, min_rc, lb, gap, novel, key, pricing_wall, oc_stats):
        rec = {
            "experiment": experiment, "tag": tag, **provenance(),
            "instance_hash": inst.hash(),
            "oracle_calls": state["oracle_calls"],
            "n_columns": len(state["columns"]),
            "z_rmp_model": rmp["z_model"],
            "ub_ch": rmp["ub"],
            "min_reduced_cost": min_rc,
            "lb_ch": lb,
            "lb_best": state["lb_best"],
            "certificate_gap": gap,
            "epsilon": epsilon,
            "pwl_tol": pwl_tol,
            "n_tangent_refinements": rmp["n_refinements"],
            "master_wall_s": rmp["master_wall_s"],
            "pricing_wall_s": pricing_wall,
            "column_novel": novel,
            "column_key": key,
            # the pricing solve backing this iteration (audit contract:
            # every record line carries an OPTIMAL solver block); its replay
            # was enforced in column_from_solution + make_record before this
            # line is written
            "solver": oc_stats,
            "replay_ok": True,
            "duals_sigma": rmp["sigma"],
            "oracle_prices_min": float(np.min(-np.asarray(rmp["pi"]))) + 0.0,
            "oracle_prices_max": float(np.max(-np.asarray(rmp["pi"]))) + 0.0,
        }
        append_jsonl(it_path, rec)

    # seed column: taker at posted prices (oracle call, budget-counted)
    if not state["columns"]:
        posted = market.price(np.zeros(market.n_slots))
        t0 = time.time()
        sol = solve_taker(inst, posted, **solver_kw)
        pricing_wall = time.time() - t0
        col = column_from_solution(inst, sol)
        rec = make_record(experiment, inst, sol, market=market, prices=posted,
                          regime="cg-seed", extra={"tag": tag, "oracle_call": 0})
        if rec["replay_ok"] is False:
            raise B2A2Error(f"seed replay invalid: {rec['replay_violations']}")
        append_jsonl(oc_path, rec)
        state["columns"].append(col)
        state["keys"].append(col["column_key"])
        state["oracle_calls"] = 1
        checkpoint.save(ck_path, state)

    prev_ub = float("inf") if not state["ub_history"] else state["ub_history"][-1]

    while True:
        rmp = solve_rmp(inst, market, state["columns"],
                        state["tangent_points"], pwl_tol=pwl_tol)
        state["tangent_points"] = rmp["tangent_points"]
        ub = rmp["ub"]
        # invariant: UB nonincreasing within tolerance
        if ub > prev_ub + TOL_MONO:
            raise B2A2Error(
                f"UB_CH increased: {prev_ub} -> {ub} (tol {TOL_MONO})")
        prev_ub = ub

        if state["oracle_calls"] >= state["budget"]:
            gap = ub - state["lb_best"]
            outcome = {"type": "budget_exhausted", "ub_ch": ub,
                       "lb_best": state["lb_best"], "gap": gap,
                       "certified": bool(gap <= epsilon)}
            state.update(done=True, outcome=outcome)
            state["ub_history"].append(ub)
            checkpoint.save(ck_path, state)
            return state

        # exact pricing at oracle prices p = -pi
        prices = -np.asarray(rmp["pi"])
        t0 = time.time()
        sol = solve_taker(inst, prices, **solver_kw)
        pricing_wall = time.time() - t0
        col = column_from_solution(inst, sol)
        min_rc = float(sol.obj_model - rmp["sigma"])
        lb = rmp["z_model"] + min(0.0, min_rc)
        state["lb_best"] = max(state["lb_best"], lb)
        gap = ub - state["lb_best"]
        novel = col["column_key"] not in state["keys"]

        rec = make_record(experiment, inst, sol, market=market, prices=prices,
                          regime="cg-pricing",
                          extra={"tag": tag,
                                 "oracle_call": state["oracle_calls"],
                                 "min_reduced_cost": min_rc,
                                 "column_key": col["column_key"],
                                 "column_novel": novel})
        if rec["replay_ok"] is False:
            raise B2A2Error(f"pricing replay invalid: {rec['replay_violations']}")
        append_jsonl(oc_path, rec)
        state["oracle_calls"] += 1
        record_iteration(rmp, min_rc, lb, gap, novel, col["column_key"],
                         pricing_wall, col["oracle_stats"])
        state["ub_history"].append(ub)
        state["lb_history"].append(state["lb_best"])

        if gap <= epsilon:
            outcome = {"type": "certified", "ub_ch": ub,
                       "lb_best": state["lb_best"], "gap": gap,
                       "certified": True,
                       "oracle_calls": state["oracle_calls"]}
            if z_d_ub is not None:
                outcome["uplift_interval"] = [
                    (z_d_ub - tol_d) - ub, z_d_ub - state["lb_best"]]
            state.update(done=True, outcome=outcome)
            checkpoint.save(ck_path, state)
            return state

        if novel:
            state["columns"].append(col)
            state["keys"].append(col["column_key"])
            state["duplicate_retries"] = 0
        else:
            if min_rc < -RC_TOL:
                state["duplicate_retries"] += 1
                if state["duplicate_retries"] >= MAX_DUPLICATE_RETRIES:
                    raise B2A2Error(
                        "pricing returned a duplicate column with materially "
                        f"negative reduced cost {min_rc} "
                        f"{MAX_DUPLICATE_RETRIES} times — dual/model "
                        "inconsistency; failing loudly")
                # tighten the PWL model and retry pricing
                state["tangent_points"].append(list(map(float, rmp["L"])))
            else:
                # pricing exhausted: LB ~= z_model; force refinement until
                # the certificate closes or no progress is possible
                if gap > epsilon:
                    state["duplicate_retries"] += 1
                    if state["duplicate_retries"] >= MAX_DUPLICATE_RETRIES:
                        raise B2A2Error(
                            f"pricing exhausted (min_rc={min_rc}) but gap "
                            f"{gap} > epsilon {epsilon}; refinement made no "
                            "progress — failing loudly")
                    state["tangent_points"].append(list(map(float, rmp["L"])))
        checkpoint.save(ck_path, state)
