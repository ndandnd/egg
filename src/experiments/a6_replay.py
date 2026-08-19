"""Shared pure A6 recovery/scheduler replay (single authoritative path).

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

EI-017 closure: the decision gap is DERIVED chronologically as
``ub_i - lb_best_{i-1}``, where the LB chain is rebuilt from each clean
oracle's certified solver bound (``lb = z_rmp + min(0, bound - sigma)``)
and UB is taken from the monotone per-iteration RMP value cross-checked
against ``z_rmp_model`` within the PWL slack and against the committed
histories.  The recorded ``gap_at_decision`` is validated against the
derived value and is NEVER used to regenerate T1 or the certificate
decision.

Every clean event's recorded pricing_max_mip_gap is validated against the
replayed value, and the final checkpoint counters/scheduler fields must
equal the replayed final state.  The scheduler/recovery identity must
equal the frozen producer constants (priority order, K_MAX, derived
theta_cert, retry caps, gap divisor 100, floor 1e-12).  Consumed by BOTH
the audit (experiments/audit_runs) and the production analyzer
(experiments/analyze_a6_holdout); there is deliberately no second
implementation anywhere.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.a6 import (
    A6_K_MAX,
    A6_PRIORITY,
    A6_THETA_CERT_MULT,
    CLEAN_TRIGGERS,
    DEFAULT_CANDIDATE,
    select_trigger,
)
from egglab.b2a2 import (
    MAX_DUPLICATE_RETRIES,
    MAX_PRICING_ESCALATIONS,
    PWL_TOL,
    RC_TOL,
    TOL_MONO,
)

RECOVERY_GAP_DIVISOR = 100.0
RECOVERY_GAP_FLOOR = 1e-12


def _fin(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(
        value, bool) and math.isfinite(value)


def _pos_inf_ok(value) -> bool:
    """A number where the producer permits the initial unbounded gap:
    finite or POSITIVE infinity only; bool, NaN, and -inf are rejected."""
    return (isinstance(value, (int, float))
            and not isinstance(value, bool)
            and not math.isnan(value)
            and value != -math.inf)


def replay_a6_recovery(ck: dict) -> tuple[dict, list[str]]:
    """Return (replayed_final_state, errors). Empty errors means the full
    scheduler/recovery/counter/bound-gap state stream replays exactly."""
    errors: list[str] = []

    def fail(message: str) -> tuple[dict, list[str]]:
        errors.append(message)
        return {}, errors

    identity = ck.get("identity") or {}
    scheduler_ident = identity.get("scheduler") or {}
    recovery_ident = identity.get("recovery") or {}
    solver_ident = identity.get("solver") or {}
    epsilon = identity.get("epsilon")
    if not _fin(epsilon) or epsilon < 0:
        return fail("a6 identity missing finite epsilon")
    # the certification threshold is DERIVED from the frozen constant, and
    # the identity must agree; the recorded value never drives T1
    theta_cert = A6_THETA_CERT_MULT * epsilon
    pwl_tol = identity.get("pwl_tol")
    if pwl_tol is None:
        pwl_tol = PWL_TOL
    if not _fin(pwl_tol) or pwl_tol < 0:
        return fail("a6 identity pwl_tol is invalid")
    # scheduler/recovery identity must equal the frozen producer constants
    frozen = (
        ("scheduler.k_max", scheduler_ident.get("k_max"), A6_K_MAX),
        ("scheduler.theta_cert_mult", scheduler_ident.get("theta_cert_mult"),
         A6_THETA_CERT_MULT),
        ("scheduler.theta_cert", scheduler_ident.get("theta_cert"),
         theta_cert),
        ("scheduler.priority", scheduler_ident.get("priority"),
         list(A6_PRIORITY) + [DEFAULT_CANDIDATE]),
        ("rc_tol", identity.get("rc_tol"), RC_TOL),
        ("recovery.max_pricing_escalations",
         recovery_ident.get("max_pricing_escalations"),
         MAX_PRICING_ESCALATIONS),
        ("recovery.max_duplicate_retries",
         recovery_ident.get("max_duplicate_retries"),
         MAX_DUPLICATE_RETRIES),
        ("recovery.gap_divisor", recovery_ident.get("gap_divisor"),
         RECOVERY_GAP_DIVISOR),
        ("recovery.gap_floor", recovery_ident.get("gap_floor"),
         RECOVERY_GAP_FLOOR),
    )
    for name, recorded, expected in frozen:
        if recorded != expected:
            return fail(
                f"a6 identity {name}={recorded!r} does not equal the "
                f"frozen producer constant {expected!r}")
    base_gap = solver_ident.get("max_mip_gap", 1e-6)
    if not _fin(base_gap) or base_gap <= 0:
        return fail("a6 identity solver.max_mip_gap is invalid")

    events = ck.get("oracle_events") or []
    event_by_id = {
        (e.get("extra") or {}).get("call_id"): e for e in events
    }
    ub_history = ck.get("ub_history")
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
    lb_best = -math.inf
    prev_ub = math.inf
    history_index = 0

    for it in ck.get("iteration_events") or []:
        iteration = it.get("iteration_id")
        # ---- chronological UB / derived decision gap (EI-017 closure) ----
        ub = it.get("ub_ch")
        if not _fin(ub):
            return fail(f"a6 iteration {iteration}: ub_ch is not finite")
        if ub > prev_ub + TOL_MONO:
            return fail(
                f"a6 iteration {iteration}: ub_ch increased "
                f"{prev_ub} -> {ub}")
        derived_gap = ub - lb_best  # +inf until the first clean LB refresh
        if it.get("terminal"):
            recorded_terminal_gap = it.get("certificate_gap")
            if not _pos_inf_ok(recorded_terminal_gap) or (
                    recorded_terminal_gap != derived_gap):
                return fail(
                    f"a6 iteration {iteration}: terminal certificate_gap="
                    f"{recorded_terminal_gap!r} but the derived value is "
                    f"{derived_gap!r}")
            prev_ub = ub
            history_index += 1
            continue
        if certified:
            return fail(
                f"a6 iteration {iteration}: events continue after the "
                "certificate returned")
        gap = it.get("gap_at_decision")
        if not _pos_inf_ok(gap):
            return fail(
                f"a6 iteration {iteration}: invalid gap_at_decision "
                f"{gap!r} (bool/NaN/-inf are never producible)")
        if gap != derived_gap:
            return fail(
                f"a6 iteration {iteration}: recorded gap_at_decision="
                f"{gap!r} but the chronologically derived value is "
                f"{derived_gap!r}")
        if (isinstance(ub_history, list)
                and history_index < len(ub_history)
                and ub_history[history_index] != ub):
            return fail(
                f"a6 iteration {iteration}: ub_history disagrees with the "
                "iteration ub_ch")
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
        recorded_active = it.get("recovery_active")
        if type(recorded_active) is not bool:
            return fail(
                f"a6 iteration {iteration}: recovery_active="
                f"{recorded_active!r} is not exactly a bool")
        if recorded_active != recovery:
            return fail(
                f"a6 iteration {iteration}: recorded "
                f"recovery_active={recorded_active} but "
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
            "T1": derived_gap <= theta_cert,  # never the recorded gap
            "T2": run >= A6_K_MAX,
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
            if it.get("certificate_gap") != derived_gap:
                return fail(
                    f"a6 iteration {iteration}: candidate "
                    f"certificate_gap={it.get('certificate_gap')!r} but "
                    f"the derived decision gap is {derived_gap!r}")
            if (isinstance(lb_history, list)
                    and history_index < len(lb_history)
                    and lb_history[history_index] != lb_best):
                return fail(
                    f"a6 iteration {iteration}: candidate call mutated "
                    "LB_best")
            run += 1
            if run > A6_K_MAX:
                return fail(
                    f"a6 iteration {iteration}: {run} consecutive "
                    f"candidates exceeds k_max={A6_K_MAX}")
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
            # ---- chronological LB refresh from certified evidence ----
            z_model = it.get("z_rmp_model")
            sigma = it.get("duals_sigma")
            bound = (oracle_event.get("solver") or {}).get("bound")
            rc_ub = it.get("min_reduced_cost_ub")
            rc_lb = it.get("min_reduced_cost_lb")
            if not (_fin(z_model) and _fin(sigma) and _fin(bound)
                    and _fin(rc_ub) and _fin(rc_lb)):
                return fail(
                    f"a6 iteration {iteration}: clean event bound "
                    "evidence is not finite")
            scale = max(1.0, abs(ub), abs(z_model))
            slack = ub - z_model
            if slack < -1e-9 * scale or slack > pwl_tol + 1e-9 * scale:
                return fail(
                    f"a6 iteration {iteration}: ub_ch/z_rmp_model slack "
                    f"{slack} is outside [0, {pwl_tol}]")
            if rc_lb != bound - sigma:
                return fail(
                    f"a6 iteration {iteration}: recorded "
                    f"min_reduced_cost_lb={rc_lb!r} but the certified "
                    f"oracle bound derives {bound - sigma!r}")
            lb = z_model + min(0.0, rc_lb)
            if it.get("lb_ch") != lb:
                return fail(
                    f"a6 iteration {iteration}: recorded "
                    f"lb_ch={it.get('lb_ch')!r} but the derived value is "
                    f"{lb!r}")
            lb_best = max(lb_best, lb)
            if it.get("lb_best") != lb_best:
                return fail(
                    f"a6 iteration {iteration}: recorded "
                    f"lb_best={it.get('lb_best')!r} but the derived value "
                    f"is {lb_best!r}")
            cert_gap = ub - lb_best  # the derived certificate gap
            if it.get("certificate_gap") != cert_gap:
                return fail(
                    f"a6 iteration {iteration}: recorded "
                    f"certificate_gap={it.get('certificate_gap')!r} but "
                    f"the derived value is {cert_gap!r}")
            if (isinstance(lb_history, list)
                    and history_index < len(lb_history)
                    and lb_history[history_index] != lb_best):
                return fail(
                    f"a6 iteration {iteration}: lb_history disagrees with "
                    "the derived LB chain")
            if cert_gap <= epsilon:
                # the certificate returns BEFORE any recovery mutation
                certified = True
                prev_ub = ub
                history_index += 1
                continue
            improving = rc_ub < -RC_TOL
            if novel:
                n_columns += 1
            if novel and improving:
                duplicate_retries = 0
                refine_retries = 0
                pricing_escalations = 0
                recovery_kind = None
            elif improving:
                duplicate_retries += 1
                if duplicate_retries >= MAX_DUPLICATE_RETRIES:
                    return fail(
                        f"a6 iteration {iteration}: duplicate_retries "
                        f"reached {duplicate_retries} — the producer fails "
                        "loudly at "
                        f"{MAX_DUPLICATE_RETRIES}, impossible in a "
                        "completed trace")
                recovery_kind = "duplicate"
            elif rc_lb < -RC_TOL:
                pricing_escalations += 1
                if pricing_escalations > MAX_PRICING_ESCALATIONS:
                    return fail(
                        f"a6 iteration {iteration}: pricing_escalations "
                        f"reached {pricing_escalations} — exceeds the "
                        f"producer cap {MAX_PRICING_ESCALATIONS}")
                pricing_gap = max(pricing_gap / RECOVERY_GAP_DIVISOR,
                                  RECOVERY_GAP_FLOOR)
                recovery_kind = "ambiguous"
            else:
                refine_retries += 1
                if refine_retries >= MAX_DUPLICATE_RETRIES:
                    return fail(
                        f"a6 iteration {iteration}: refine_retries reached "
                        f"{refine_retries} — the producer fails loudly at "
                        f"{MAX_DUPLICATE_RETRIES}, impossible in a "
                        "completed trace")
                recovery_kind = "refinement"
        prev_ub = ub
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
        "lb_best": lb_best,
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
    if "recovery_active_at_end" not in outcome:
        errors.append(
            "a6 final state: outcome recovery_active_at_end is missing")
        return final_state, errors
    recorded_at_end = outcome.get("recovery_active_at_end")
    if type(recorded_at_end) is not bool:
        errors.append(
            "a6 final state: outcome recovery_active_at_end="
            f"{recorded_at_end!r} is not exactly a bool")
        return final_state, errors
    if recorded_at_end != (recovery_kind is not None):
        errors.append(
            "a6 final state: outcome recovery_active_at_end="
            f"{recorded_at_end!r} but the event stream replays "
            f"{recovery_kind is not None!r}")
    return final_state, errors
