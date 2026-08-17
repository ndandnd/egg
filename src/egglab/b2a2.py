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

PRICING: RIGOROUS MILP-BOUND ACCOUNTING
=======================================
Duals are taken from the clean RMP LP written EXACTLY as above
(link_t:  sum_j lambda_j e_{jt} - L_t = 0, dual pi_t; conv: dual sigma).
The reduced cost of a candidate column S is

    rc(S) = ops(S) - sum_t pi_t e_t(S) - sigma,

so exact pricing is the certified taker EVSP oracle at ORACLE PRICES

    p_t := -pi_t        (sign convention: oracle price = MINUS link dual).

A MILP pricing solve returns TWO values, and they play different roles:

    pricing_ub = sol.obj_model     (feasible incumbent value; its schedule
                                    is the candidate column)
    pricing_lb = sol.stats.bound   (certified dual bound on the exact
                                    pricing optimum; <= pricing_ub)

    min_rc_ub = pricing_ub - sigma   -> improvement/novelty decisions ONLY
    min_rc_lb = pricing_lb - sigma   -> the ONLY value allowed inside LB_CH

With ONE convexity block, the Lasdon bound requires a lower bound on the
TRUE pricing optimum, hence

    LB_CH = z_model + min(0, min_rc_lb),

never min_rc_ub (the incumbent may sit above the true optimum by up to the
solver's MIP gap, which would overstate LB_CH and could FALSELY certify).
The absolute/relative pricing gap (pricing_ub - pricing_lb) is logged on
every call, and a missing or nonfinite bound fails loudly. Validity chain:
LB_CH <= z_CH^pwl <= z_CH <= UB_CH (tangent model <= true).

If min_rc_lb < -rc_tol but pricing produced no improving novel incumbent
(duplicate, or min_rc_ub >= -rc_tol), exhaustion is NOT declared: the
pricing MIP gap is tightened (state["pricing_max_mip_gap"] /= 100, floor
1e-12) and pricing continues; after MAX_PRICING_ESCALATIONS unproductive
tightenings the run fails loudly. Pricing exhaustion — the precondition for
LB_CH ~= z_model — requires min_rc_lb >= -rc_tol, i.e. a CERTIFIED
statement that no improving column exists.

CERTIFICATION AND INVARIANTS
============================
- certified termination iff  UB_CH - LB_best <= epsilon (default 1e-2);
- LB_best is the running maximum of valid lower bounds (monotone up);
- UB_CH is nonincreasing after every valid column addition + clean-RMP
  reoptimization within tol_mono = pwl_tol + 1e-6 (enforced, loud failure);
- every oracle solve must be OPTIMAL, replay-valid, and carry a finite
  certified bound (loud failure otherwise);
- duplicate columns are never added; a duplicate incumbent claiming an
  improving min_rc_ub raises after MAX_DUPLICATE_RETRIES (dual/model
  inconsistency);
- checkpoint identity (schema version, instance hash, market hash over
  a/b/U, epsilon, budget, pwl_tol, rc_tol, solver settings, dictator
  provenance) is validated at resume; any mismatch rejects the checkpoint.

TRANSACTIONAL LOGGING (EXACTLY-ONCE)
====================================
The atomic checkpoint is the single source of truth. Every oracle record and
iteration record is committed INSIDE the checkpoint (state["oracle_events"],
state["iteration_events"], each with a stable unique id), and the JSONL logs
are materialized atomically (tmp + rename) FROM committed state — after each
checkpoint save and again at startup before a done checkpoint is returned.
A kill at any point (after the solve, after the checkpoint, during or after
materialization) therefore yields, on resume, logs that are byte-derived
from committed state: one completed oracle call appears exactly once, and at
most the single in-flight solve is repeated.

B3 UPLIFT INTERVAL
==================
With the dictator solved independently (obj_true = z_D_ub, tolerance tol_D):
    uplift = z_D - z_CH  in  [ (z_D_ub - tol_D) - UB_CH,  z_D_ub - LB_best ].
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
import time

import mip
import numpy as np

from . import checkpoint
from .evsp import validate_solution
from .instance import Instance
from .market import AffineMarket
from .records import make_record, provenance
from .regimes import _l_max, solve_taker
from .solver import backend, new_model, optimize

SCHEMA_VERSION = "b2a2-v2"
EPSILON_DEFAULT = 1e-2
PWL_TOL = 1e-3
RC_TOL = 1e-6
MAX_DUPLICATE_RETRIES = 3
MAX_PRICING_ESCALATIONS = 4
TOL_MONO = PWL_TOL + 1e-6


class B2A2Error(RuntimeError):
    pass


def _finite(x) -> bool:
    return x is not None and math.isfinite(float(x))


def market_hash(market: AffineMarket) -> str:
    """Identity of the price model: full-precision a, b, U."""
    payload = json.dumps({
        "a": [f"{float(x):.17g}" for x in market.a],
        "b": [f"{float(x):.17g}" for x in market.b],
        "U": [f"{float(x):.17g}" for x in market.U],
    })
    return hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# schedule columns
# ---------------------------------------------------------------------------
def column_key(col: dict) -> str:
    """Master-column identity: the FULL projected master vector — the
    full-precision normalized load AND the operating cost — hashed with full
    SHA-256. Identical loads with different operating costs never collide
    (the cheaper one is a distinct, novel column). Structural evidence
    (sequences, arc kinds, hashes) stays in the column dict as diagnostics
    but does not define master identity."""
    payload = json.dumps({
        "v": "b2a2-col-v2",
        "load": [f"{float(x) + 0.0:.17g}" for x in col["load"]],
        "ops_cost": f"{float(col['ops_cost']) + 0.0:.17g}",
    })
    return hashlib.sha256(payload.encode()).hexdigest()


def column_from_solution(inst: Instance, sol) -> dict:
    """Schedule column: complete feasible schedule + load + cost + hashes +
    replay evidence. Fails loudly on replay violations, non-OPTIMAL status,
    or a missing/nonfinite certified bound."""
    violations = validate_solution(inst, sol)
    if violations:
        raise B2A2Error(f"oracle produced replay-invalid column: {violations}")
    if sol.stats is None or sol.stats.status != "OPTIMAL":
        raise B2A2Error(
            f"oracle status {'missing' if sol.stats is None else sol.stats.status}"
            " != OPTIMAL")
    if not _finite(sol.stats.bound):
        raise B2A2Error(
            f"oracle returned no finite certified bound: {sol.stats.bound!r}")
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


# ---------------------------------------------------------------------------
# transactional log materialization (checkpoint is the source of truth)
# ---------------------------------------------------------------------------
def _atomic_write_lines(path: str, records: list) -> None:
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _materialize_logs(state: dict, oc_path: str, it_path: str) -> None:
    """Rebuild both JSONL logs atomically from COMMITTED state. Idempotent:
    running it any number of times, from any interruption point, yields the
    same files — one committed oracle call appears exactly once."""
    _atomic_write_lines(oc_path, state["oracle_events"])
    _atomic_write_lines(it_path, state["iteration_events"])


# ---------------------------------------------------------------------------
# clean restricted master (pure LP; UB via exact evaluation)
# ---------------------------------------------------------------------------
def solve_rmp(inst: Instance, market: AffineMarket, columns: list,
              tangent_points: list, pwl_tol: float = PWL_TOL,
              solve_id_prefix: str = "rmp"):
    """Solve the clean unstabilized RMP with inner tangent refinement.
    Returns z_model, ub (exact evaluation), lambdas, L, duals pi/sigma, the
    possibly-extended tangent_points, and Phase-0 evidence for EVERY actual
    master solve (stable solve ids, backend, status, objective, bound,
    sizes, wall time).

    Solve ids are CELL-LOCAL: they are derived from the tag and iteration
    counter, so different cell directories (which all run the same driver
    with the same tag) legitimately contain identical ids. Uniqueness is
    guaranteed, and audited, only within one cell directory / checkpoint."""
    if not columns:
        raise B2A2Error("RMP requires at least one column")
    T = market.n_slots
    l_max = _l_max(inst)
    tangent_points = [list(map(float, tp)) for tp in tangent_points]
    solves = []
    wall = 0.0
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
        st = optimize(m, solve_lp_first=False)
        wall += st.wall_s
        solves.append({
            "solve_id": f"{solve_id_prefix}-r{_refine}",
            "backend": st.backend,
            "status": st.status,
            "obj": st.obj,
            "bound": st.bound,
            "mip_gap": st.mip_gap,
            "n_vars": st.n_vars,
            "n_int": st.n_int,  # zero is meaningful: the clean RMP is an LP
            "n_constrs": st.n_constrs,
            "wall_s": st.wall_s,
            "threads": st.extra.get("threads"),
        })
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
                "n_refinements": _refine, "master_solves": solves,
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
    exhaustion. Transactionally checkpointed per oracle call; resumable
    with full identity validation; invariant-enforced."""
    solver_kw = dict(solver_kw or {})
    os.makedirs(out_dir, exist_ok=True)
    ck_path = os.path.join(out_dir, f"{tag}.cg.ckpt.json")
    it_path = os.path.join(out_dir, f"{tag}.iterations.jsonl")
    oc_path = os.path.join(out_dir, f"{tag}.oracle.jsonl")

    identity = {
        "schema_version": SCHEMA_VERSION,
        "instance_hash": inst.hash(),
        "market_hash": market_hash(market),
        "epsilon": epsilon,
        "budget": budget,
        "pwl_tol": pwl_tol,
        "rc_tol": RC_TOL,
        "solver": {"backend": backend(),
                   **{k: solver_kw[k] for k in sorted(solver_kw)}},
        "tol_d": tol_d,
        "z_d_ub": z_d_ub,
    }
    base_pricing_gap = float(solver_kw.pop("max_mip_gap", 1e-6))

    state = checkpoint.load(ck_path)
    if state is None:
        state = {
            "identity": identity,
            "columns": [], "keys": [], "tangent_points": [],
            "oracle_calls": 0, "lb_best": -float("inf"),
            "ub_history": [], "lb_history": [],
            "oracle_events": [], "iteration_events": [],
            "duplicate_retries": 0, "refine_retries": 0,
            "pricing_escalations": 0,
            "pricing_max_mip_gap": base_pricing_gap,
            "done": False, "outcome": None,
        }
    else:
        stored = state.get("identity")
        if stored != identity:
            diffs = sorted(
                k for k in set(identity) | set(stored or {})
                if (stored or {}).get(k) != identity.get(k))
            raise B2A2Error(
                f"checkpoint identity mismatch (fields: {diffs}); refusing "
                "to resume — delete the cell directory to restart")
        # repair/materialize logs from committed state BEFORE anything else
        _materialize_logs(state, oc_path, it_path)
        if state["done"]:
            return state
        # resume sanity: stored bounds must be consistent
        if state["ub_history"] and state["lb_best"] > min(
                state["ub_history"]) + TOL_MONO + epsilon:
            raise B2A2Error(
                f"corrupt checkpoint: LB_best {state['lb_best']} exceeds "
                f"best UB {min(state['ub_history'])}")

    def commit():
        checkpoint.save(ck_path, state)
        _materialize_logs(state, oc_path, it_path)

    def pricing_solve(prices):
        t0 = time.time()
        sol = solve_taker(inst, prices,
                          max_mip_gap=state["pricing_max_mip_gap"],
                          **solver_kw)
        return sol, time.time() - t0

    # seed column: taker at posted prices (oracle call 0, budget-counted)
    if not state["columns"]:
        posted = market.price(np.zeros(market.n_slots))
        sol, _pw = pricing_solve(posted)
        col = column_from_solution(inst, sol)
        call_id = f"{tag}-oc0"
        rec = make_record(experiment, inst, sol, market=market, prices=posted,
                          regime="cg-seed",
                          extra={"tag": tag, "call_id": call_id})
        if rec["replay_ok"] is False:
            raise B2A2Error(f"seed replay invalid: {rec['replay_violations']}")
        state["oracle_events"].append(rec)
        state["columns"].append(col)
        state["keys"].append(col["column_key"])
        state["oracle_calls"] = 1
        commit()

    while True:
        oc = state["oracle_calls"]
        rmp = solve_rmp(inst, market, state["columns"],
                        state["tangent_points"], pwl_tol=pwl_tol,
                        solve_id_prefix=f"{tag}-it{oc}-rmp")
        state["tangent_points"] = rmp["tangent_points"]
        ub = rmp["ub"]
        # invariant: UB nonincreasing within tolerance
        prev_ub = state["ub_history"][-1] if state["ub_history"] else float("inf")
        if ub > prev_ub + TOL_MONO:
            raise B2A2Error(
                f"UB_CH increased: {prev_ub} -> {ub} (tol {TOL_MONO})")

        if oc >= state["identity"]["budget"]:
            gap = ub - state["lb_best"]
            state["ub_history"].append(ub)
            state["lb_history"].append(state["lb_best"])
            # the terminal clean RMP is a real solve: commit its evidence as
            # a master-only iteration event (no pricing solve to reference)
            state["iteration_events"].append({
                "record_kind": "cg-iteration",
                "terminal": True,
                "iteration_id": f"{tag}-it{oc}-terminal",
                "experiment": experiment, "tag": tag, **provenance(),
                "instance_hash": inst.hash(),
                "oracle_calls": oc,
                "n_columns": len(state["columns"]),
                "z_rmp_model": rmp["z_model"],
                "ub_ch": ub,
                "lb_best": state["lb_best"],
                "certificate_gap": gap,
                "epsilon": epsilon,
                "pwl_tol": pwl_tol,
                "n_tangent_refinements": rmp["n_refinements"],
                "master_wall_s": rmp["master_wall_s"],
                "master_solves": rmp["master_solves"],
                "pricing_solve_id": None,
            })
            outcome = {"type": "budget_exhausted", "ub_ch": ub,
                       "lb_best": state["lb_best"], "gap": gap,
                       "certified": bool(gap <= epsilon),
                       "oracle_calls": oc}
            if z_d_ub is not None:
                outcome["uplift_interval"] = [
                    (z_d_ub - tol_d) - ub, z_d_ub - state["lb_best"]]
            state.update(done=True, outcome=outcome)
            commit()
            return state

        # exact pricing at oracle prices p = -pi
        prices = -np.asarray(rmp["pi"])
        sol, pricing_wall = pricing_solve(prices)
        col = column_from_solution(inst, sol)
        pricing_ub = float(sol.obj_model)          # feasible incumbent
        pricing_lb = float(sol.stats.bound)        # certified dual bound
        if not _finite(pricing_lb):
            raise B2A2Error(f"pricing bound nonfinite: {pricing_lb!r}")
        min_rc_ub = pricing_ub - rmp["sigma"]      # improvement/novelty only
        min_rc_lb = pricing_lb - rmp["sigma"]      # the ONLY value in LB_CH
        lb = rmp["z_model"] + min(0.0, min_rc_lb)
        state["lb_best"] = max(state["lb_best"], lb)
        gap = ub - state["lb_best"]
        novel = col["column_key"] not in state["keys"]
        call_id = f"{tag}-oc{oc}"

        rec = make_record(experiment, inst, sol, market=market, prices=prices,
                          regime="cg-pricing",
                          extra={"tag": tag, "call_id": call_id,
                                 "min_reduced_cost_ub": min_rc_ub,
                                 "min_reduced_cost_lb": min_rc_lb,
                                 "column_key": col["column_key"],
                                 "column_novel": novel})
        if rec["replay_ok"] is False:
            raise B2A2Error(f"pricing replay invalid: {rec['replay_violations']}")
        state["oracle_events"].append(rec)
        state["iteration_events"].append({
            "record_kind": "cg-iteration",
            "iteration_id": f"{tag}-it{oc}",
            "experiment": experiment, "tag": tag, **provenance(),
            "instance_hash": inst.hash(),
            "oracle_calls": oc,
            "n_columns": len(state["columns"]),
            "z_rmp_model": rmp["z_model"],
            "ub_ch": ub,
            "min_reduced_cost_ub": min_rc_ub,
            "min_reduced_cost_lb": min_rc_lb,
            "pricing_gap_abs": pricing_ub - pricing_lb,
            "pricing_gap_rel": (pricing_ub - pricing_lb) / max(1e-12, abs(pricing_ub)),
            "pricing_max_mip_gap": state["pricing_max_mip_gap"],
            "lb_ch": lb,
            "lb_best": state["lb_best"],
            "certificate_gap": gap,
            "epsilon": epsilon,
            "pwl_tol": pwl_tol,
            "rc_tol": RC_TOL,
            "n_tangent_refinements": rmp["n_refinements"],
            "master_wall_s": rmp["master_wall_s"],
            "pricing_wall_s": pricing_wall,
            "column_novel": novel,
            "column_key": col["column_key"],
            # every ACTUAL master solve, individually evidenced; the pricing
            # solve is referenced by id (full record in the oracle log) so
            # solve counts are never inflated by double-counting
            "master_solves": rmp["master_solves"],
            "pricing_solve_id": call_id,
            "replay_ok": True,
            "duals_sigma": rmp["sigma"],
            "oracle_prices_min": float(np.min(prices)) + 0.0,
            "oracle_prices_max": float(np.max(prices)) + 0.0,
        })
        state["oracle_calls"] = oc + 1
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
            commit()
            return state

        improving = min_rc_ub < -RC_TOL
        if novel:
            # retain every generated unique column (improving or not)
            state["columns"].append(col)
            state["keys"].append(col["column_key"])
        if novel and improving:
            state["duplicate_retries"] = 0
            state["refine_retries"] = 0
            state["pricing_escalations"] = 0
        elif (not novel) and improving:
            # a duplicate of a retained column cannot have rc < 0 at the RMP
            # optimum: dual/model inconsistency — refine, retry, then fail
            state["duplicate_retries"] += 1
            if state["duplicate_retries"] >= MAX_DUPLICATE_RETRIES:
                raise B2A2Error(
                    "pricing returned a duplicate column with materially "
                    f"negative incumbent reduced cost {min_rc_ub} "
                    f"{MAX_DUPLICATE_RETRIES} times — dual/model "
                    "inconsistency; failing loudly")
            state["tangent_points"].append(list(map(float, rmp["L"])))
        elif min_rc_lb < -RC_TOL:
            # no improving novel incumbent, but the CERTIFIED bound says an
            # improving column may still exist: NOT exhaustion — tighten the
            # pricing MIP gap and continue
            state["pricing_escalations"] += 1
            if state["pricing_escalations"] > MAX_PRICING_ESCALATIONS:
                raise B2A2Error(
                    f"pricing bound stays negative (min_rc_lb={min_rc_lb}) "
                    "with no improving novel incumbent after "
                    f"{MAX_PRICING_ESCALATIONS} MIP-gap escalations — "
                    "cannot certify exhaustion; failing loudly")
            state["pricing_max_mip_gap"] = max(
                state["pricing_max_mip_gap"] / 100.0, 1e-12)
        else:
            # certified exhaustion (min_rc_lb >= -rc_tol) but gap > epsilon:
            # only PWL slack remains — force refinement until it closes
            state["refine_retries"] += 1
            if state["refine_retries"] >= MAX_DUPLICATE_RETRIES:
                raise B2A2Error(
                    f"pricing certifiably exhausted (min_rc_lb={min_rc_lb}) "
                    f"but gap {gap} > epsilon {epsilon}; refinement made no "
                    "progress — failing loudly")
            state["tangent_points"].append(list(map(float, rmp["L"])))
        commit()
