"""Shared pure A6 recovery/scheduler replay (Task: one implementation).

Independently reconstructs, from a checkpoint's committed event stream,
the COMPLETE producer state — trigger stream, k_since_clean,
n_clean_pricing, last_candidate_novel, recovery kind/state, n_columns,
duplicate_retries, refine_retries, pricing_escalations, and
pricing_max_mip_gap including every /100 update and the 1e-12 floor —
enforcing the producer's exact branch order:

- a certificate returns BEFORE any recovery mutation;
- a novel improving clean call resets all recovery counters (never the
  pricing gap, which only tightens);
- a duplicate improving clean call increments duplicate_retries and can
  never reach its cap in a completed trace;
- an ambiguous clean call increments pricing_escalations (bounded by its
  cap), then tightens the requested MIP gap by /divisor with the floor;
- certified-exhaustion refinement increments its bounded retry counter;
- candidate calls never mutate certified bounds, counters, or the gap.

Every clean event's recorded pricing_max_mip_gap is validated against the
replayed value, and the final checkpoint counters/scheduler fields must
equal the replayed final state. Consumed by BOTH the audit
(experiments/audit_runs) and the production analyzer
(experiments/analyze_a6_holdout); there is deliberately no second
implementation anywhere.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.a6 import A6_PRIORITY, CLEAN_TRIGGERS, select_trigger


def _fin(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(
        value, bool) and math.isfinite(value)


def replay_a6_recovery(ck: dict) -> tuple[dict, list[str]]:
    """Return (replayed_final_state, errors). Empty errors means the full
    scheduler/recovery/counter state stream replays exactly."""
    errors: list[str] = []

    def fail(message: str) -> tuple[dict, list[str]]:
        errors.append(message)
        return {}, errors

    identity = ck.get("identity") or {}
    scheduler_ident = identity.get("scheduler") or {}
    recovery_ident = identity.get("recovery") or {}
    solver_ident = identity.get("solver") or {}
    k_max = scheduler_ident.get("k_max")
    theta_cert = scheduler_ident.get("theta_cert")
    rc_tol = identity.get("rc_tol")
    epsilon = identity.get("epsilon")
    max_escalations = recovery_ident.get("max_pricing_escalations")
    max_duplicates = recovery_ident.get("max_duplicate_retries")
    gap_divisor = recovery_ident.get("gap_divisor")
    gap_floor = recovery_ident.get("gap_floor")
    # the producer defaults an unspecified pricing gap to 1e-6
    # (solver_kw.pop("max_mip_gap", 1e-6)); the identity records it only
    # when the caller passed it explicitly — mirror that exactly
    base_gap = solver_ident.get("max_mip_gap", 1e-6)
    for name, value in (
            ("scheduler.k_max", k_max),
            ("scheduler.theta_cert", theta_cert),
            ("rc_tol", rc_tol), ("epsilon", epsilon),
            ("recovery.max_pricing_escalations", max_escalations),
            ("recovery.max_duplicate_retries", max_duplicates),
            ("recovery.gap_divisor", gap_divisor),
            ("recovery.gap_floor", gap_floor),
            ("solver.max_mip_gap", base_gap)):
        if not _fin(value):
            return fail(f"a6 identity missing finite {name}")

    events = ck.get("oracle_events") or []
    event_by_id = {
        (e.get("extra") or {}).get("call_id"): e for e in events
    }
    lb_history = ck.get("lb_history")

    # replayed producer state
    run = 0                     # k_since_clean
    n_clean = 0                 # n_clean_pricing
    n_columns = 1               # the seed column
    last_candidate_novel = None
    recovery_kind = None
    duplicate_retries = 0
    refine_retries = 0
    pricing_escalations = 0
    pricing_gap = float(base_gap)
    certified = False
    history_index = 0

    for it in ck.get("iteration_events") or []:
        if it.get("terminal"):
            continue
        iteration = it.get("iteration_id")
        if certified:
            return fail(
                f"a6 iteration {iteration}: events continue after the "
                "certificate returned")
        gap = it.get("gap_at_decision")
        # +inf is legitimate before the first clean LB refresh; only a
        # missing/NaN value is malformed
        if (not isinstance(gap, (int, float)) or isinstance(gap, bool)
                or math.isnan(gap)):
            return fail(
                f"a6 iteration {iteration}: invalid gap_at_decision")
        if it.get("k_since_clean") != run:
            return fail(
                f"a6 iteration {iteration}: recorded "
                f"k_since_clean={it.get('k_since_clean')} but recomputed "
                f"value is {run}")
        if it.get("n_columns") != n_columns:
            return fail(
                f"a6 iteration {iteration}: recorded "
                f"n_columns={it.get('n_columns')} but recomputed value "
                f"is {n_columns}")
        recovery = recovery_kind is not None
        if bool(it.get("recovery_active")) != recovery:
            return fail(
                f"a6 iteration {iteration}: recorded "
                f"recovery_active={it.get('recovery_active')} but "
                f"recomputed value is {recovery}")
        if it.get("recovery_kind") != recovery_kind:
            return fail(
                f"a6 iteration {iteration}: recorded "
                f"recovery_kind={it.get('recovery_kind')!r} but "
                f"recomputed value is {recovery_kind!r}")
        expected_fired = {
            "T0": recovery,
            "T4": n_clean == 0,
            "T3": last_candidate_novel is False,
            "T1": gap <= theta_cert,
            "T2": run >= k_max,
        }
        fired_list = [t for t in A6_PRIORITY if expected_fired[t]]
        if it.get("triggers_fired") != fired_list:
            return fail(
                f"a6 iteration {iteration}: recorded "
                f"triggers_fired={it.get('triggers_fired')} but "
                f"recomputed value is {fired_list}")
        sel = it.get("trigger_selected")
        kind = it.get("call_kind")
        expected_selected = select_trigger(expected_fired)
        if sel != expected_selected:
            return fail(
                f"a6 iteration {iteration}: selected {sel} violates "
                f"recomputed frozen-priority selection {expected_selected}")
        if sel in CLEAN_TRIGGERS and kind != "clean":
            return fail(
                f"a6 iteration {iteration}: clean trigger {sel} but "
                f"call_kind {kind}")
        if sel not in CLEAN_TRIGGERS and kind != "candidate":
            return fail(
                f"a6 iteration {iteration}: default candidate selected "
                f"but call_kind {kind}")
        if recovery and kind == "candidate":
            return fail(
                f"a6 iteration {iteration}: candidate call during active "
                "recovery (T0 violated)")
        pricing_id = it.get("pricing_solve_id")
        oracle_event = event_by_id.get(pricing_id)
        extra = (oracle_event or {}).get("extra") or {}
        if oracle_event is None or any((
                extra.get("call_kind") != kind,
                extra.get("trigger_selected") != sel,
                extra.get("triggers_fired") != fired_list)):
            return fail(
                f"a6 iteration {iteration}: oracle-event scheduler fields "
                "disagree with the iteration event")
        novel = it.get("column_novel")
        if not isinstance(novel, bool):
            return fail(
                f"a6 iteration {iteration}: column_novel is not boolean")

        if kind == "candidate":
            # candidates never touch certified bounds, counters, or gap
            if (isinstance(lb_history, list)
                    and 0 < history_index < len(lb_history)
                    and lb_history[history_index]
                    != lb_history[history_index - 1]):
                return fail(
                    f"a6 iteration {iteration}: candidate call mutated "
                    "LB_best")
            run += 1
            if run > k_max:
                return fail(
                    f"a6 iteration {iteration}: {run} consecutive "
                    f"candidates exceeds k_max={k_max}")
            last_candidate_novel = novel
            if novel:
                n_columns += 1
        else:
            recorded_gap = it.get("pricing_max_mip_gap")
            if recorded_gap != pricing_gap:
                return fail(
                    f"a6 iteration {iteration}: recorded "
                    f"pricing_max_mip_gap={recorded_gap!r} but replayed "
                    f"value is {pricing_gap!r}")
            run = 0
            n_clean += 1
            last_candidate_novel = None
            rc_ub = it.get("min_reduced_cost_ub")
            rc_lb = it.get("min_reduced_cost_lb")
            cert_gap = it.get("certificate_gap")
            if not (_fin(rc_ub) and _fin(rc_lb) and _fin(cert_gap)):
                return fail(
                    f"a6 iteration {iteration}: clean event bounds are "
                    "not finite")
            if cert_gap <= epsilon:
                # the certificate returns BEFORE any recovery mutation
                certified = True
                history_index += 1
                continue
            improving = rc_ub < -rc_tol
            if novel:
                n_columns += 1
            if novel and improving:
                duplicate_retries = 0
                refine_retries = 0
                pricing_escalations = 0
                recovery_kind = None
            elif improving:
                duplicate_retries += 1
                if duplicate_retries >= max_duplicates:
                    return fail(
                        f"a6 iteration {iteration}: duplicate_retries "
                        f"reached {duplicate_retries} — the producer fails "
                        "loudly at "
                        f"{max_duplicates}, impossible in a completed trace")
                recovery_kind = "duplicate"
            elif rc_lb < -rc_tol:
                pricing_escalations += 1
                if pricing_escalations > max_escalations:
                    return fail(
                        f"a6 iteration {iteration}: pricing_escalations "
                        f"reached {pricing_escalations} — exceeds the "
                        f"producer cap {max_escalations}")
                pricing_gap = max(pricing_gap / gap_divisor, gap_floor)
                recovery_kind = "ambiguous"
            else:
                refine_retries += 1
                if refine_retries >= max_duplicates:
                    return fail(
                        f"a6 iteration {iteration}: refine_retries reached "
                        f"{refine_retries} — the producer fails loudly at "
                        f"{max_duplicates}, impossible in a completed trace")
                recovery_kind = "refinement"
        history_index += 1

    final_state = {
        "duplicate_retries": duplicate_retries,
        "refine_retries": refine_retries,
        "pricing_escalations": pricing_escalations,
        "pricing_max_mip_gap": pricing_gap,
        "recovery": ({"kind": recovery_kind}
                     if recovery_kind is not None else None),
        "k_since_clean": run,
        "n_clean_pricing": n_clean,
        "last_candidate_novel": last_candidate_novel,
        "n_columns": n_columns,
        "certified": certified,
    }

    # final checkpoint counters/scheduler fields must equal the replay
    sched = ck.get("scheduler") or {}
    comparisons = (
        ("duplicate_retries", ck.get("duplicate_retries"),
         duplicate_retries),
        ("refine_retries", ck.get("refine_retries"), refine_retries),
        ("pricing_escalations", ck.get("pricing_escalations"),
         pricing_escalations),
        ("pricing_max_mip_gap", ck.get("pricing_max_mip_gap"), pricing_gap),
        ("scheduler.k_since_clean", sched.get("k_since_clean"), run),
        ("scheduler.n_clean_pricing", sched.get("n_clean_pricing"), n_clean),
        ("scheduler.last_candidate_novel",
         sched.get("last_candidate_novel"), last_candidate_novel),
        ("scheduler.recovery", sched.get("recovery"),
         final_state["recovery"]),
    )
    for name, recorded, replayed in comparisons:
        if recorded != replayed:
            errors.append(
                f"a6 final state: recorded {name}={recorded!r} but the "
                f"event stream replays {replayed!r}")
            return final_state, errors
    outcome = ck.get("outcome") or {}
    if "recovery_active_at_end" in outcome and (
            bool(outcome.get("recovery_active_at_end"))
            != (recovery_kind is not None)):
        errors.append(
            "a6 final state: outcome recovery_active_at_end="
            f"{outcome.get('recovery_active_at_end')!r} but the event "
            f"stream replays {recovery_kind is not None!r}")
    return final_state, errors
