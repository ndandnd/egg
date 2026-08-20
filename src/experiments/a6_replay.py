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

EI-025 closure: a COMPLETED trace is also closed at its terminal/final
state.  No event may follow a derived certificate or the budget terminal;
certified completion has zero terminal events and budget exhaustion has
exactly one final terminal event whose n_columns/lb_best/history entry
replay; the top-level checkpoint lb_best, column count, and history lengths
and the full outcome (type, certified, ub_ch, lb_best, gap, oracle_calls,
method, recovery-at-end) must equal the replay; and each call's
oracle-event reduced-cost/novelty evidence must agree with its iteration
event.

Oracle-call provenance (F1): oracle-event call IDs are present and unique;
replay_calls (one seed plus one per priced iteration) equals, as exact
integers, len(oracle_events), checkpoint.oracle_calls, and
outcome.oracle_calls; every priced iteration binds its chronological
oracle_calls index and the terminal event binds the total count; and the
non-seed oracle events are in one-to-one correspondence with the priced
iterations (no orphan, reused, or missing events).
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


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


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
    # oracle-call provenance: every committed oracle event carries a present,
    # unique call ID (reused or missing IDs break the one-to-one mapping)
    call_ids = [(e.get("extra") or {}).get("call_id") for e in events]
    if None in call_ids or len(set(call_ids)) != len(call_ids):
        return fail("a6 oracle events have missing or reused call IDs")
    seed_call_id = call_ids[0] if call_ids else None
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
    terminals = 0
    oracle_call = 0             # chronological index of the last priced call
    referenced_ids: set = set()  # non-seed oracle events cited by iterations

    for it in ck.get("iteration_events") or []:
        iteration = it.get("iteration_id")
        # nothing may follow a certificate or the budget terminal: the
        # producer STOPS at either (the certificate returns; the terminal
        # master is the final committed event).  A trailing event of ANY
        # kind — including a second terminal — is impossible.
        if certified:
            return fail(
                f"a6 iteration {iteration}: events continue after the "
                "certificate returned")
        if terminals:
            return fail(
                f"a6 iteration {iteration}: events continue after the "
                "terminal event")
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
            terminals += 1
            recorded_terminal_gap = it.get("certificate_gap")
            if not _pos_inf_ok(recorded_terminal_gap) or (
                    recorded_terminal_gap != derived_gap):
                return fail(
                    f"a6 iteration {iteration}: terminal certificate_gap="
                    f"{recorded_terminal_gap!r} but the derived value is "
                    f"{derived_gap!r}")
            # the terminal master commits n_columns, lb_best, and one more
            # UB/LB history entry: each must replay exactly
            if it.get("n_columns") != n_columns:
                return fail(
                    f"a6 iteration {iteration}: terminal n_columns="
                    f"{it.get('n_columns')!r} but the recomputed value is "
                    f"{n_columns}")
            if it.get("lb_best") != lb_best:
                return fail(
                    f"a6 iteration {iteration}: terminal lb_best="
                    f"{it.get('lb_best')!r} but the derived value is "
                    f"{lb_best!r}")
            if (isinstance(ub_history, list)
                    and history_index < len(ub_history)
                    and ub_history[history_index] != ub):
                return fail(
                    f"a6 iteration {iteration}: terminal ub_history "
                    "disagrees with the iteration ub_ch")
            if (isinstance(lb_history, list)
                    and history_index < len(lb_history)
                    and lb_history[history_index] != lb_best):
                return fail(
                    f"a6 iteration {iteration}: terminal lb_history "
                    "disagrees with the derived LB chain")
            # the terminal master fires at the budget: its recorded
            # oracle_calls is the total call count (seed + every priced call)
            if it.get("oracle_calls") != oracle_call + 1:
                return fail(
                    f"a6 iteration {iteration}: terminal oracle_calls="
                    f"{it.get('oracle_calls')!r} but the replayed count is "
                    f"{oracle_call + 1}")
            prev_ub = ub
            history_index += 1
            continue
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
        # each priced iteration is oracle call k (seed is call 0); bind its
        # recorded chronological index exactly
        oracle_call += 1
        if it.get("oracle_calls") != oracle_call:
            return fail(
                f"a6 iteration {iteration}: recorded "
                f"oracle_calls={it.get('oracle_calls')!r} but the "
                f"chronological index is {oracle_call}")
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
        # one-to-one: a priced iteration cites the seed or an already-cited
        # event only if the stream is forged
        if pricing_id == seed_call_id:
            return fail(
                f"a6 iteration {iteration}: priced call references the seed "
                f"oracle event {pricing_id!r}")
        if pricing_id in referenced_ids:
            return fail(
                f"a6 iteration {iteration}: oracle event {pricing_id!r} is "
                "referenced by more than one priced iteration")
        referenced_ids.add(pricing_id)
        novel = it.get("column_novel")
        if not isinstance(novel, bool):
            return fail(
                f"a6 iteration {iteration}: column_novel is not boolean")
        # oracle and iteration evidence for the SAME call may never disagree
        if extra.get("column_novel") != novel:
            return fail(
                f"a6 iteration {iteration}: oracle-event column_novel "
                "disagrees with the iteration event")
        if kind == "clean" and (
                extra.get("min_reduced_cost_ub")
                != it.get("min_reduced_cost_ub")
                or extra.get("min_reduced_cost_lb")
                != it.get("min_reduced_cost_lb")):
            return fail(
                f"a6 iteration {iteration}: oracle-event reduced-cost "
                "evidence disagrees with the iteration event")

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

    # ---- terminal / final-state / outcome closure (EI-025 closure) --------
    # A COMPLETED trace closes in exactly one way: a certificate returns
    # (zero terminal events) or the budget terminal fires as the final event
    # (exactly one).  A resumable in-flight checkpoint legitimately has
    # neither, so this closure only binds a done checkpoint.
    if ck.get("done"):
        final_gap = prev_ub - lb_best
        expected_certified = bool(_fin(final_gap) and final_gap <= epsilon)
        if terminals == 0:
            if not certified:
                errors.append(
                    "a6 final state: completed trace has neither a "
                    "certificate nor a terminal event")
                return final_state, errors
            expected_type = "certified"
        elif terminals == 1:
            if certified:
                errors.append(
                    "a6 final state: a certificate and a terminal event "
                    "cannot both close a trace")
                return final_state, errors
            iters = ck.get("iteration_events") or []
            if not (iters and isinstance(iters[-1], dict)
                    and iters[-1].get("terminal") is True):
                errors.append(
                    "a6 final state: the terminal event is not the final "
                    "iteration event")
                return final_state, errors
            expected_type = "budget_exhausted"
        else:
            errors.append(
                f"a6 final state: {terminals} terminal events (a completed "
                "trace has zero when certified, exactly one at budget)")
            return final_state, errors

        # top-level checkpoint fields must equal the replay
        if ck.get("lb_best") != lb_best:
            errors.append(
                f"a6 final state: recorded lb_best={ck.get('lb_best')!r} "
                f"but the event stream replays {lb_best!r}")
            return final_state, errors
        columns = ck.get("columns")
        if isinstance(columns, list) and len(columns) != n_columns:
            errors.append(
                f"a6 final state: recorded column count {len(columns)} but "
                f"the event stream replays {n_columns}")
            return final_state, errors
        for name, hist in (("ub_history", ub_history),
                           ("lb_history", lb_history)):
            hist_len = len(hist) if isinstance(hist, list) else None
            if hist_len != history_index:
                errors.append(
                    f"a6 final state: {name} length {hist_len} does not "
                    f"match the {history_index} replayed events")
                return final_state, errors

        rec_outcome = ck.get("outcome") or {}

        # ---- oracle-call provenance closure (F1) --------------------------
        # replay_calls = one seed call plus one call per priced iteration.
        # It must equal, as exact integers, the committed oracle-event count,
        # the checkpoint's oracle_calls, and the outcome's oracle_calls.
        replay_calls = 1 + oracle_call
        for name, value in (
                ("checkpoint.oracle_calls", ck.get("oracle_calls")),
                ("outcome.oracle_calls", rec_outcome.get("oracle_calls"))):
            if not _is_int(value):
                errors.append(
                    f"a6 final state: {name}={value!r} is not an integer")
                return final_state, errors
        if not (replay_calls == len(events) == ck.get("oracle_calls")
                == rec_outcome.get("oracle_calls")):
            errors.append(
                "a6 final state: oracle-call count mismatch — replay "
                f"{replay_calls}, oracle_events {len(events)}, "
                f"checkpoint.oracle_calls {ck.get('oracle_calls')!r}, "
                f"outcome.oracle_calls {rec_outcome.get('oracle_calls')!r}")
            return final_state, errors
        # every non-seed oracle event is cited by exactly one priced iteration
        # (no orphan events, no missing events)
        if referenced_ids != set(call_ids) - {seed_call_id}:
            errors.append(
                "a6 final state: priced iterations and non-seed oracle "
                "events are not in one-to-one correspondence")
            return final_state, errors

        # the recorded outcome must follow the replayed trace exactly
        outcome_checks = (
            ("type", rec_outcome.get("type"), expected_type),
            ("method", rec_outcome.get("method"),
             (ck.get("identity") or {}).get("method")),
            ("ub_ch", rec_outcome.get("ub_ch"), prev_ub),
            ("lb_best", rec_outcome.get("lb_best"), lb_best),
            ("gap", rec_outcome.get("gap"), final_gap),
        )
        for name, recorded, expected in outcome_checks:
            if recorded != expected:
                errors.append(
                    f"a6 final state: outcome {name}={recorded!r} but the "
                    f"event stream replays {expected!r}")
                return final_state, errors
        if rec_outcome.get("certified") is not expected_certified:
            errors.append(
                "a6 final state: outcome certified="
                f"{rec_outcome.get('certified')!r} but the event stream "
                f"replays {expected_certified!r}")
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
