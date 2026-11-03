"""A6: event-triggered sparse stabilization (doc/A6_SPARSE_STABILIZATION_SPEC.md).

A2's certified loop plus a SCHEDULER that spends the seed call and then
EXACTLY ONE oracle call per master iteration, chosen under the frozen
deterministic priority

    T0 recovery > T4 initialization > T3 candidate stall >
    T1 closable gap > T2 staleness > default candidate.

Method identities: a6_a4 (Wentges-smoothed candidates) and a6_a3
(du Merle candidates). The certification contract is IDENTICAL to A2:
UB_CH from the clean RMP over all columns every iteration (an LP — no
additional oracle call), LB_CH only from clean-dual Lasdon bounds;
candidate calls only add columns and can never update LB_CH or certify.

T0 recovery uses A2's DIRECT clean escalation/retry logic (ambiguous
pricing -> tighten pricing_max_mip_gap; certified exhaustion -> tangent
refinement; duplicate-negative-rc -> bounded retries; all with loud
failure). While recovery is active, candidates never run: T0 keeps
selecting clean calls until a novel improving column arrives, the
certificate closes, or the bounded retries fail loudly. The dense
candidate-mediated deferred escalation of A3-A5 is NOT reused here.

Terminal states: certified, budget-exhausted (valid completed outcome),
or fail-loud recovery error. This module leaves b2a2.certified_cg and the
dense A3-A5 machinery completely untouched.
"""
from __future__ import annotations

import math
import os
import time

import numpy as np

from . import b2a345, checkpoint
from .b2a2 import (
    B2A2Error,
    EPSILON_DEFAULT,
    MAX_DUPLICATE_RETRIES,
    MAX_PRICING_ESCALATIONS,
    PWL_TOL,
    RC_TOL,
    TOL_MONO,
    _finite,
    _materialize_logs,
    _update_price_path,
    canonicalize_pricing_solution,
    column_from_solution,
    market_hash,
    pricing_incumbent,
    solve_rmp,
)
from .evsp import LOAD_RECONSTRUCTION_POLICY_VERSION, REPLAY_TOL_KWH
from .instance import Instance
from .market import AffineMarket
from .records import make_record, provenance
from .regimes import solve_taker
from .solver import backend

A6_SCHEMA_VERSION = "a6-v2"
A6_THETA_CERT_MULT = 10.0          # theta_cert = mult * epsilon
A6_K_MAX = 4                       # max consecutive candidates outside T0
A6_PRIORITY = ("T0", "T4", "T3", "T1", "T2")  # then default candidate
A6_METHODS = ("a6_a4", "a6_a3")
A6_MECH = {"a6_a4": "a4", "a6_a3": "a3"}
CLEAN_TRIGGERS = set(A6_PRIORITY)
DEFAULT_CANDIDATE = "default-candidate"


def select_trigger(fired: dict) -> str:
    """Frozen deterministic selection: the highest-priority fired trigger,
    else the default candidate. `fired` maps trigger name -> bool."""
    for t in A6_PRIORITY:
        if fired.get(t):
            return t
    return DEFAULT_CANDIDATE


def a6_identity(inst, market, method, epsilon, budget, pwl_tol, solver_kw,
                tol_d, z_d_ub) -> dict:
    mech = A6_MECH[method]
    return {
        "schema_version": A6_SCHEMA_VERSION,
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
        "load_reconstruction": {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "tolerance_kwh": REPLAY_TOL_KWH,
        },
        "method": method,
        "scheduler": {
            "theta_cert_mult": A6_THETA_CERT_MULT,
            "theta_cert": A6_THETA_CERT_MULT * epsilon,
            "k_max": A6_K_MAX,
            "priority": list(A6_PRIORITY) + [DEFAULT_CANDIDATE],
        },
        "recovery": {
            "max_pricing_escalations": MAX_PRICING_ESCALATIONS,
            "max_duplicate_retries": MAX_DUPLICATE_RETRIES,
            "gap_divisor": 100.0,
            "gap_floor": 1e-12,
        },
        "stab": b2a345.stab_identity_params(mech),
    }


def certified_cg_a6(
    inst: Instance,
    market: AffineMarket,
    method: str,
    epsilon: float = EPSILON_DEFAULT,
    budget: int = 240,
    out_dir: str = "runs/a6",
    tag: str = "a6",
    experiment: str = "a6",
    pwl_tol: float = PWL_TOL,
    solver_kw: dict | None = None,
    z_d_ub: float | None = None,
    tol_d: float = 1e-2,
) -> dict:
    """Run A6 to certification (UB - LB_best <= epsilon), budget
    exhaustion, or loud recovery failure. Transactionally checkpointed
    per oracle call; resume reproduces the identical decision sequence."""
    if method not in A6_METHODS:
        raise B2A2Error(f"unknown A6 method {method!r}")
    mech = A6_MECH[method]
    solver_kw = dict(solver_kw or {})
    os.makedirs(out_dir, exist_ok=True)
    ck_path = os.path.join(out_dir, f"{tag}.cg.ckpt.json")
    it_path = os.path.join(out_dir, f"{tag}.iterations.jsonl")
    oc_path = os.path.join(out_dir, f"{tag}.oracle.jsonl")

    identity = a6_identity(inst, market, method, epsilon, budget, pwl_tol,
                           solver_kw, tol_d, z_d_ub)
    theta_cert = identity["scheduler"]["theta_cert"]
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
            "calls_clean": 0, "calls_stab": 0,
            "stab": b2a345.initial_stab_state(mech, market),
            "scheduler": {"k_since_clean": 0, "n_clean_pricing": 0,
                          "last_candidate_novel": None,
                          "recovery": None},
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
        _materialize_logs(state, oc_path, it_path)
        if state["done"]:
            return state
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
        canonicalize_pricing_solution(inst, sol, prices)
        return sol, time.time() - t0

    def finish(kind, ub, gap):
        sched = state["scheduler"]
        trig_counts = {}
        for ev in state["iteration_events"]:
            sel = ev.get("trigger_selected")
            if sel:
                trig_counts[sel] = trig_counts.get(sel, 0) + 1
        outcome = {"type": kind, "ub_ch": ub,
                   "lb_best": state["lb_best"], "gap": gap,
                   "certified": bool(gap <= epsilon),
                   "oracle_calls": state["oracle_calls"],
                   "method": method,
                   "oracle_calls_clean": state["calls_clean"],
                   "oracle_calls_stab": state["calls_stab"],
                   "trigger_selected_counts": trig_counts,
                   "recovery_active_at_end": sched["recovery"] is not None}
        pp = state.get("price_path") or {}
        outcome["broadcast_tv"] = pp.get("tv")
        outcome["broadcast_linf_max"] = pp.get("linf_max")
        outcome["broadcast_points"] = pp.get("n")
        if z_d_ub is not None:
            outcome["uplift_interval"] = [
                (z_d_ub - tol_d) - ub, z_d_ub - state["lb_best"]]
        state.update(done=True, outcome=outcome)
        commit()
        return state

    # seed column (oracle call 0, budget-counted)
    if not state["columns"]:
        posted = market.price(np.zeros(market.n_slots))
        sol, _pw = pricing_solve(posted)
        col = column_from_solution(inst, sol)
        call_id = f"{tag}-oc0"
        rec = make_record(experiment, inst, sol, market=market, prices=posted,
                          regime="cg-seed",
                          extra={"tag": tag, "call_id": call_id,
                                 "call_kind": "seed", "method": method})
        if rec["replay_ok"] is False:
            raise B2A2Error(f"seed replay invalid: {rec['replay_violations']}")
        state["oracle_events"].append(rec)
        state["columns"].append(col)
        state["keys"].append(col["column_key"])
        state["oracle_calls"] = 1
        state["calls_clean"] = 1  # the seed is a clean-side call
        _update_price_path(state, posted)
        commit()

    while True:
        oc = state["oracle_calls"]
        sched = state["scheduler"]
        rmp = solve_rmp(inst, market, state["columns"],
                        state["tangent_points"], pwl_tol=pwl_tol,
                        solve_id_prefix=f"{tag}-it{oc}-rmp")
        state["tangent_points"] = rmp["tangent_points"]
        ub = rmp["ub"]
        prev_ub = state["ub_history"][-1] if state["ub_history"] else float("inf")
        if ub > prev_ub + TOL_MONO:
            raise B2A2Error(
                f"UB_CH increased: {prev_ub} -> {ub} (tol {TOL_MONO})")
        gap_at_decision = ub - state["lb_best"]

        if oc >= state["identity"]["budget"]:
            state["ub_history"].append(ub)
            state["lb_history"].append(state["lb_best"])
            state["iteration_events"].append({
                "record_kind": "cg-iteration",
                "terminal": True, "phase": "terminal", "method": method,
                "iteration_id": f"{tag}-it{oc}-terminal",
                "experiment": experiment, "tag": tag, **provenance(),
                "instance_hash": inst.hash(),
                "oracle_calls": oc,
                "n_columns": len(state["columns"]),
                "z_rmp_model": rmp["z_model"],
                "ub_ch": ub, "lb_best": state["lb_best"],
                "certificate_gap": gap_at_decision,
                "epsilon": epsilon, "pwl_tol": pwl_tol,
                "n_tangent_refinements": rmp["n_refinements"],
                "master_wall_s": rmp["master_wall_s"],
                "master_solves": rmp["master_solves"],
                "pricing_solve_id": None,
            })
            return finish("budget_exhausted", ub, gap_at_decision)

        # --- frozen-priority scheduler --------------------------------------
        fired = {
            "T0": sched["recovery"] is not None,
            "T4": sched["n_clean_pricing"] == 0,
            "T3": sched["last_candidate_novel"] is False,
            "T1": gap_at_decision <= theta_cert,
            "T2": sched["k_since_clean"] >= A6_K_MAX,
        }
        selected = select_trigger(fired)
        call_kind = "clean" if selected in CLEAN_TRIGGERS else "candidate"
        triggers_fired = [t for t in A6_PRIORITY if fired[t]]
        sched_snapshot = {
            "triggers_fired": triggers_fired,
            "trigger_selected": selected,
            "call_kind": call_kind,
            "k_since_clean": sched["k_since_clean"],
            "gap_at_decision": gap_at_decision,
            "recovery_active": sched["recovery"] is not None,
            "recovery_kind": (sched["recovery"] or {}).get("kind"),
        }
        call_id = f"{tag}-oc{oc}"

        if call_kind == "clean":
            prices = -np.asarray(rmp["pi"])
            sol, pricing_wall = pricing_solve(prices)
            col = column_from_solution(inst, sol)
            pricing_ub = pricing_incumbent(col, sol, prices)
            pricing_lb = float(sol.stats.bound)
            if not _finite(pricing_lb):
                raise B2A2Error(f"pricing bound nonfinite: {pricing_lb!r}")
            min_rc_ub = pricing_ub - rmp["sigma"]
            min_rc_lb = pricing_lb - rmp["sigma"]
            lb = rmp["z_model"] + min(0.0, min_rc_lb)
            state["lb_best"] = max(state["lb_best"], lb)
            gap = ub - state["lb_best"]
            novel = col["column_key"] not in state["keys"]

            rec = make_record(
                experiment, inst, sol, market=market, prices=prices,
                regime="cg-pricing",
                extra={"tag": tag, "call_id": call_id, "method": method,
                       "call_kind": "clean",
                       "trigger_selected": selected,
                       "triggers_fired": triggers_fired,
                       "min_reduced_cost_ub": min_rc_ub,
                       "min_reduced_cost_lb": min_rc_lb,
                       "column_key": col["column_key"],
                       "column_novel": novel})
            if rec["replay_ok"] is False:
                raise B2A2Error(
                    f"pricing replay invalid: {rec['replay_violations']}")
            state["oracle_events"].append(rec)
            state["iteration_events"].append({
                "record_kind": "cg-iteration",
                "iteration_id": f"{tag}-it{oc}",
                "phase": "clean", "method": method,
                "experiment": experiment, "tag": tag, **provenance(),
                "instance_hash": inst.hash(),
                "oracle_calls": oc,
                "n_columns": len(state["columns"]),
                "z_rmp_model": rmp["z_model"], "ub_ch": ub,
                "min_reduced_cost_ub": min_rc_ub,
                "min_reduced_cost_lb": min_rc_lb,
                "pricing_gap_abs": pricing_ub - pricing_lb,
                "pricing_max_mip_gap": state["pricing_max_mip_gap"],
                "lb_ch": lb, "lb_best": state["lb_best"],
                "certificate_gap": gap,
                "epsilon": epsilon, "pwl_tol": pwl_tol, "rc_tol": RC_TOL,
                "n_tangent_refinements": rmp["n_refinements"],
                "master_wall_s": rmp["master_wall_s"],
                "pricing_wall_s": pricing_wall,
                "column_novel": novel, "column_key": col["column_key"],
                "master_solves": rmp["master_solves"],
                "pricing_solve_id": call_id,
                "replay_ok": True,
                "duals_sigma": rmp["sigma"],
                **sched_snapshot,
            })
            state["oracle_calls"] = oc + 1
            state["calls_clean"] += 1
            sched["n_clean_pricing"] += 1
            sched["k_since_clean"] = 0
            sched["last_candidate_novel"] = None
            state["ub_history"].append(ub)
            state["lb_history"].append(state["lb_best"])
            _update_price_path(state, prices)
            # theta_best tracks the best certified dual value at any point
            th = b2a345.theta_cert(market, prices, pricing_lb)
            tb = state["stab"].get("theta_best")
            if math.isfinite(th) and (tb is None or th > tb):
                state["stab"]["theta_best"] = th

            if gap <= epsilon:
                return finish("certified", ub, gap)

            # A2's DIRECT recovery branches (spec T0; dense deferral unused)
            improving = min_rc_ub < -RC_TOL
            if novel:
                state["columns"].append(col)
                state["keys"].append(col["column_key"])
            if novel and improving:
                state["duplicate_retries"] = 0
                state["refine_retries"] = 0
                state["pricing_escalations"] = 0
                sched["recovery"] = None  # recovery resolved
            elif (not novel) and improving:
                state["duplicate_retries"] += 1
                if state["duplicate_retries"] >= MAX_DUPLICATE_RETRIES:
                    raise B2A2Error(
                        "pricing returned a duplicate column with materially "
                        f"negative incumbent reduced cost {min_rc_ub} "
                        f"{MAX_DUPLICATE_RETRIES} times — dual/model "
                        "inconsistency; failing loudly")
                state["tangent_points"].append(list(map(float, rmp["L"])))
                sched["recovery"] = {"kind": "duplicate"}
            elif min_rc_lb < -RC_TOL:
                state["pricing_escalations"] += 1
                if state["pricing_escalations"] > MAX_PRICING_ESCALATIONS:
                    raise B2A2Error(
                        f"pricing bound stays negative (min_rc_lb={min_rc_lb}) "
                        "with no improving novel incumbent after "
                        f"{MAX_PRICING_ESCALATIONS} MIP-gap escalations — "
                        "cannot certify exhaustion; failing loudly")
                state["pricing_max_mip_gap"] = max(
                    state["pricing_max_mip_gap"] / 100.0, 1e-12)
                sched["recovery"] = {"kind": "ambiguous"}
            else:
                state["refine_retries"] += 1
                if state["refine_retries"] >= MAX_DUPLICATE_RETRIES:
                    raise B2A2Error(
                        f"pricing certifiably exhausted (min_rc_lb={min_rc_lb}) "
                        f"but gap {gap} > epsilon {epsilon}; refinement made "
                        "no progress — failing loudly")
                state["tangent_points"].append(list(map(float, rmp["L"])))
                sched["recovery"] = {"kind": "refinement"}
            commit()

        else:  # CANDIDATE call — never touches LB_CH or certification
            stab = state["stab"]
            pi_cand, stab_solves = b2a345.candidate_duals(
                inst, market, state["columns"], state["tangent_points"],
                mech, stab, rmp["pi"], pwl_tol,
                solve_id_prefix=f"{tag}-it{oc}-stabrmp")
            prices = -np.asarray(pi_cand)
            sol, pricing_wall = pricing_solve(prices)
            col = column_from_solution(inst, sol)
            pricing_lb = float(sol.stats.bound)
            if not _finite(pricing_lb):
                raise B2A2Error(
                    f"candidate pricing bound nonfinite: {pricing_lb!r}")
            theta = b2a345.theta_cert(market, prices, pricing_lb)
            serious = b2a345.serious_step(stab.get("theta_best"), theta)
            novel = col["column_key"] not in state["keys"]

            params_before = {k: (list(stab[k]) if isinstance(stab[k], list)
                                 else stab[k])
                             for k in ("alpha", "t", "d1") if k in stab}
            signal = None
            if mech == "a4":
                prices_out = -np.asarray(rmp["pi"])
                signal = b2a345.a4_direction_signal(
                    market, prices, prices_out, col["load"])
            b2a345.apply_update(mech, stab, serious, pi_cand, signal)
            tb = stab.get("theta_best")
            if math.isfinite(theta) and (tb is None or theta > tb):
                stab["theta_best"] = theta
            params_after = {k: (list(stab[k]) if isinstance(stab[k], list)
                                else stab[k])
                            for k in ("alpha", "t", "d1") if k in stab}

            rec = make_record(
                experiment, inst, sol, market=market, prices=prices,
                regime="cg-stab-pricing",
                extra={"tag": tag, "call_id": call_id, "method": method,
                       "call_kind": "candidate",
                       "trigger_selected": selected,
                       "triggers_fired": triggers_fired,
                       "theta_cert": theta, "serious_step": serious,
                       "column_key": col["column_key"],
                       "column_novel": novel})
            if rec["replay_ok"] is False:
                raise B2A2Error(
                    f"candidate replay invalid: {rec['replay_violations']}")
            state["oracle_events"].append(rec)
            state["iteration_events"].append({
                "record_kind": "cg-iteration",
                "iteration_id": f"{tag}-it{oc}-stab",
                "phase": "stabilized", "method": method,
                "experiment": experiment, "tag": tag, **provenance(),
                "instance_hash": inst.hash(),
                "oracle_calls": oc,
                "n_columns": len(state["columns"]),
                "ub_ch": ub,
                "certificate_gap": gap_at_decision,
                "epsilon": epsilon, "pwl_tol": pwl_tol,
                "theta_cert": theta,
                "theta_best": stab.get("theta_best"),
                "serious_step": serious,
                "a4_signal": signal,
                "params_before": params_before,
                "params_after": params_after,
                "pricing_wall_s": pricing_wall,
                "column_novel": novel, "column_key": col["column_key"],
                "master_solves": stab_solves,
                "pricing_solve_id": call_id,
                "replay_ok": True,
                **sched_snapshot,
            })
            state["oracle_calls"] = oc + 1
            state["calls_stab"] += 1
            sched["k_since_clean"] += 1
            sched["last_candidate_novel"] = bool(novel)
            state["ub_history"].append(ub)
            state["lb_history"].append(state["lb_best"])  # unchanged: no LB
            _update_price_path(state, prices)
            if novel:
                state["columns"].append(col)
                state["keys"].append(col["column_key"])
            commit()
