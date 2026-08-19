"""Coordinated-tamper battery for the shared A6 recovery replay
(experiments/a6_replay.py): a real recovery-rich producer trace replays
exactly; internally CONSISTENT tampers (trigger labels and final state
adjusted together) that exceed a retry cap or falsify the /100 gap path
are rejected by the shared helper, the audit, and the production
analyzer."""
import copy
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import egglab.b2a2 as b2a2_mod
from egglab import checkpoint
from egglab.a6 import (
    A6_K_MAX,
    A6_PRIORITY,
    A6_THETA_CERT_MULT,
    DEFAULT_CANDIDATE,
    certified_cg_a6,
)
from egglab.b2a2 import MAX_DUPLICATE_RETRIES, MAX_PRICING_ESCALATIONS
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from experiments.a6_replay import replay_a6_recovery
from experiments.audit_runs import _cg_sane


def fix_builder(seed, n_trips):
    return synthetic_instance(seed=seed, n_trips=n_trips, max_vehicles=2)


@pytest.fixture(scope="module")
def recovery_trace(tmp_path_factory):
    """A completed REAL trace containing an ambiguity episode: one clean
    call returns a duplicate with an optimistic incumbent and a weak
    certified bound, forcing a pricing-gap escalation (/100) and a T0
    recovery that later resolves and certifies."""
    inst = fix_builder(1, 4)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    out = str(tmp_path_factory.mktemp("recovery"))
    real_solve = b2a2_mod.solve_taker
    state = {"n": 0, "seed_sol": None}

    def one_ambiguous_clean(_inst, prices, **kw):
        state["n"] += 1
        sol = real_solve(_inst, prices, **kw)
        if state["n"] == 1:
            state["seed_sol"] = sol
        if state["n"] == 2:
            # the T4 clean call returns a DUPLICATE of the seed column
            # (physically-recomputed incumbent: genuinely non-improving)
            # with only the certified bound weakened -> ambiguous pricing
            bad = copy.deepcopy(state["seed_sol"])
            bad.stats.bound = -1e9
            return bad
        return sol

    import egglab.a6 as a6_mod
    orig = a6_mod.solve_taker
    a6_mod.solve_taker = one_ambiguous_clean
    try:
        ck = certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                             budget=120, out_dir=out, tag="a6_a4")
    finally:
        a6_mod.solve_taker = orig
    return ck, out


def test_recovery_trace_replays_exactly(recovery_trace):
    ck, _ = recovery_trace
    kinds = [e.get("recovery_kind") for e in ck["iteration_events"]]
    assert "ambiguous" in kinds  # the episode actually happened
    final, errors = replay_a6_recovery(ck)
    assert errors == []
    assert final["certified"] is True
    # the /100 tightening survives recovery resolution (gap never resets)
    assert final["pricing_max_mip_gap"] == pytest.approx(1e-8)
    assert ck["pricing_max_mip_gap"] == pytest.approx(1e-8)
    # counters were reset by the novel improving recovery exit
    assert final["pricing_escalations"] == ck["pricing_escalations"]
    assert final["recovery"] is None


def _tampered_gap_path(ck):
    """Coordinated /10 falsification: every post-escalation clean event's
    recorded pricing_max_mip_gap AND the final checkpoint value are
    adjusted CONSISTENTLY with each other — only the /100 producer rule is
    violated."""
    bad = json.loads(json.dumps(ck))
    changed = 0
    for it in bad["iteration_events"]:
        if it.get("terminal") or it.get("call_kind") != "clean":
            continue
        if it.get("pricing_max_mip_gap") == pytest.approx(1e-8):
            it["pricing_max_mip_gap"] = 1e-7  # claims /10, not /100
            changed += 1
    assert changed > 0
    bad["pricing_max_mip_gap"] = 1e-7  # final state matches the tamper
    return bad


def test_falsified_gap_division_rejected_by_helper(recovery_trace):
    ck, _ = recovery_trace
    bad = _tampered_gap_path(ck)
    _final, errors = replay_a6_recovery(bad)
    assert errors and "pricing_max_mip_gap" in errors[0]
    assert "replayed value is 1e-08" in errors[0]


def test_falsified_gap_division_rejected_by_audit(recovery_trace):
    ck, _ = recovery_trace
    errs = _cg_sane(json.loads(json.dumps(ck)))
    assert errs == []  # the untampered trace is audit-sane
    errs = _cg_sane(_tampered_gap_path(ck))
    assert any("pricing_max_mip_gap" in e for e in errs)


def test_analyzer_uses_the_shared_replay(recovery_trace):
    """Single implementation: the analyzer imports and invokes the SAME
    shared helper (analyzer-path tamper rejections are exercised in
    tests/test_a6_holdout_analysis.py on analyzer-strict fixtures)."""
    import experiments.a6_replay as shared
    import experiments.analyze_a6_holdout as an
    import inspect

    source = inspect.getsource(an._replay_cg_certificate_evidence)
    assert "replay_a6_recovery" in source
    assert an.AnalysisError is not None
    assert shared.replay_a6_recovery is not None


def test_final_counter_tamper_rejected(recovery_trace):
    ck, _ = recovery_trace
    bad = json.loads(json.dumps(ck))
    bad["pricing_escalations"] = ck["pricing_escalations"] + 1
    _final, errors = replay_a6_recovery(bad)
    assert any("recorded pricing_escalations" in e for e in errors)
    assert any("event stream replays" in e for e in errors)


def test_candidate_lb_mutation_rejected(recovery_trace):
    ck, _ = recovery_trace
    bad = json.loads(json.dumps(ck))
    idx = next(i for i, e in enumerate(
        [e for e in bad["iteration_events"] if not e.get("terminal")])
        if e.get("call_kind") == "candidate")
    assert idx > 0
    bad["lb_history"][idx] = bad["lb_history"][idx - 1] + 0.5
    _final, errors = replay_a6_recovery(bad)
    assert any("candidate call mutated LB_best" in e for e in errors)


# --------------------------------------------------------------------------
# synthetic coordinated cap-exceed traces (internally consistent streams)
# --------------------------------------------------------------------------
def _synthetic_recovery_ck(kind: str, repeats: int, *,
                           epsilon: float = 1e-2,
                           append_terminal: bool = True,
                           identity_overrides: dict | None = None) -> dict:
    """A minimal internally consistent a6 stream of `repeats` consecutive
    recovery clean calls of one kind (ambiguous, duplicate, or
    refinement), with every per-event label, counter, bound, and gap value
    derived through the exact producer arithmetic so only the deliberate
    violation under test differs."""
    base_gap = 1e-6
    theta_cert = A6_THETA_CERT_MULT * epsilon
    identity = {
        "method": "a6_a4", "epsilon": epsilon, "rc_tol": 1e-6,
        "pwl_tol": 1e-6,
        "solver": {"backend": "CBC", "max_mip_gap": base_gap},
        "scheduler": {"theta_cert_mult": A6_THETA_CERT_MULT,
                      "theta_cert": theta_cert,
                      "k_max": A6_K_MAX,
                      "priority": list(A6_PRIORITY) + [DEFAULT_CANDIDATE]},
        "recovery": {"max_pricing_escalations": MAX_PRICING_ESCALATIONS,
                     "max_duplicate_retries": MAX_DUPLICATE_RETRIES,
                     "gap_divisor": 100.0, "gap_floor": 1e-12},
    }
    for key, value in (identity_overrides or {}).items():
        parent, _, child = key.partition(".")
        if child:
            identity[parent][child] = value
        else:
            identity[parent] = value
    ub = 10.0
    z_model = 10.0
    sigma = 12.0
    if kind == "ambiguous":
        bound, rc_ub = 11.0, 1.0
    elif kind == "duplicate":
        bound, rc_ub = 11.0, -1.0
    else:  # refinement: |rc_lb| below RC_TOL, incumbent non-improving
        bound, rc_ub = sigma - 1e-7, 1.0
    rc_lb = bound - sigma                       # producer arithmetic
    lb = z_model + min(0.0, rc_lb)
    events = [{"regime": "cg-seed",
               "extra": {"tag": "a6_a4", "call_id": "a6_a4-oc0"}}]
    iterations = []
    gap = base_gap
    escalations = 0
    duplicates = 0
    refines = 0
    lb_best = -float("inf")
    ub_history = []
    lb_history = []
    for i in range(repeats):
        call_id = f"a6_a4-oc{i + 1}"
        fired = ["T4"] if i == 0 else ["T0"]
        derived_gap = ub - lb_best              # inf on the first call
        events.append({
            "regime": "cg-pricing",
            "solver": {"bound": bound},
            "extra": {"tag": "a6_a4", "call_id": call_id,
                      "call_kind": "clean", "trigger_selected": fired[0],
                      "triggers_fired": fired,
                      "column_novel": False,
                      "min_reduced_cost_ub": rc_ub,
                      "min_reduced_cost_lb": rc_lb}})
        lb_best = max(lb_best, lb)
        iterations.append({
            "iteration_id": f"a6_a4-it{i + 1}",
            "call_kind": "clean", "trigger_selected": fired[0],
            "triggers_fired": fired,
            "gap_at_decision": derived_gap,
            "k_since_clean": 0, "n_columns": 1,
            "recovery_active": i > 0,
            "recovery_kind": None if i == 0 else kind,
            "pricing_solve_id": call_id,
            "pricing_max_mip_gap": gap,
            "ub_ch": ub, "z_rmp_model": z_model, "duals_sigma": sigma,
            "min_reduced_cost_ub": rc_ub,
            "min_reduced_cost_lb": rc_lb,
            "lb_ch": lb, "lb_best": lb_best,
            "certificate_gap": ub - lb_best,
            "column_novel": False,
        })
        ub_history.append(ub)
        lb_history.append(lb_best)
        if kind == "ambiguous":
            escalations += 1
            gap = max(gap / 100.0, 1e-12)
        elif kind == "duplicate":
            duplicates += 1
        else:
            refines += 1
    terminal_gap = ub - lb_best
    if append_terminal:
        # the budget terminal master: commits one more UB/LB history entry
        # and the final n_columns/lb_best, with no pricing solve
        iterations.append({
            "record_kind": "cg-iteration", "terminal": True,
            "phase": "terminal", "method": "a6_a4",
            "iteration_id": f"a6_a4-it{repeats + 1}-terminal",
            "oracle_calls": repeats + 1,
            "n_columns": 1, "z_rmp_model": z_model, "ub_ch": ub,
            "lb_best": lb_best, "certificate_gap": terminal_gap,
            "pricing_solve_id": None,
        })
        ub_history.append(ub)
        lb_history.append(lb_best)
    return {
        "done": True,
        "identity": identity,
        "oracle_calls": repeats + 1,
        "oracle_events": events,
        "iteration_events": iterations,
        "columns": [{"column_key": "seed"}],
        "ub_history": ub_history,
        "lb_history": lb_history,
        "lb_best": lb_best,
        "duplicate_retries": duplicates,
        "refine_retries": refines,
        "pricing_escalations": escalations,
        "pricing_max_mip_gap": gap,
        "scheduler": {"k_since_clean": 0,
                      "n_clean_pricing": repeats,
                      "last_candidate_novel": None,
                      "recovery": {"kind": kind}},
        "outcome": {"type": "budget_exhausted", "certified": False,
                    "ub_ch": ub, "lb_best": lb_best, "gap": terminal_gap,
                    "oracle_calls": repeats + 1, "method": "a6_a4",
                    "recovery_active_at_end": True},
    }


def test_within_cap_synthetic_stream_replays():
    ck = _synthetic_recovery_ck("ambiguous", MAX_PRICING_ESCALATIONS)
    final, errors = replay_a6_recovery(ck)
    assert errors == []
    assert final["pricing_escalations"] == MAX_PRICING_ESCALATIONS


def test_escalation_cap_exceeded_rejected_even_when_coordinated():
    """One more ambiguous clean call than the producer allows — every
    label, counter, and /100 gap value is internally consistent, yet the
    stream is impossible: the producer fails loudly at the cap."""
    ck = _synthetic_recovery_ck("ambiguous", MAX_PRICING_ESCALATIONS + 1)
    _final, errors = replay_a6_recovery(ck)
    assert any("exceeds the producer cap" in e for e in errors)


def test_duplicate_cap_reached_rejected_even_when_coordinated():
    ck = _synthetic_recovery_ck("duplicate", MAX_DUPLICATE_RETRIES)
    _final, errors = replay_a6_recovery(ck)
    assert any("impossible in a completed trace" in e for e in errors)


def test_duplicate_below_cap_replays():
    ck = _synthetic_recovery_ck("duplicate", MAX_DUPLICATE_RETRIES - 1)
    _final, errors = replay_a6_recovery(ck)
    assert errors == []


def test_coordinated_decision_gap_trigger_tamper_rejected(recovery_trace):
    """EI-017 closure. Original exploit (reproduced accepted before the
    fix): on a clean iteration selected by a trigger above T1 where T1 did
    not fire, lower the recorded decision gap below theta_cert and add T1
    to triggers_fired on BOTH the iteration event and the oracle metadata
    (order-consistent).  Selection is unchanged, so no other stream field
    moves.  The chronological UB/LB derivation must reject it in the
    shared helper and the audit."""
    ck, _ = recovery_trace
    bad = json.loads(json.dumps(ck))
    theta = bad["identity"]["scheduler"]["theta_cert"]
    by_id = {e["extra"]["call_id"]: e
             for e in bad["oracle_events"] if e.get("extra")}
    target = None
    for it in bad["iteration_events"]:
        if it.get("terminal") or it.get("call_kind") != "clean":
            continue
        if (it["trigger_selected"] in ("T0", "T4", "T3")
                and "T1" not in it["triggers_fired"]):
            target = it
            break
    assert target is not None
    target["gap_at_decision"] = theta / 2
    fired = [t for t in A6_PRIORITY
             if t in target["triggers_fired"] or t == "T1"]
    target["triggers_fired"] = fired
    by_id[target["pricing_solve_id"]]["extra"]["triggers_fired"] = fired

    _final, errors = replay_a6_recovery(bad)
    assert any("chronologically derived" in e for e in errors)
    errs = _cg_sane(bad)
    assert any("chronologically derived" in e for e in errs)


def test_negative_infinity_gap_rejected(recovery_trace):
    ck, _ = recovery_trace
    bad = json.loads(json.dumps(ck))
    first = next(e for e in bad["iteration_events"] if not e.get("terminal"))
    first["gap_at_decision"] = -float("inf")
    _final, errors = replay_a6_recovery(bad)
    assert any("-inf are never producible" in e or "invalid gap" in e
               for e in errors)


def test_outcome_recovery_flag_deleted_or_mistyped_rejected(recovery_trace):
    ck, _ = recovery_trace
    bad = json.loads(json.dumps(ck))
    del bad["outcome"]["recovery_active_at_end"]
    _final, errors = replay_a6_recovery(bad)
    assert any("recovery_active_at_end is missing" in e for e in errors)

    bad = json.loads(json.dumps(ck))
    truthy = bad["outcome"]["recovery_active_at_end"]
    bad["outcome"]["recovery_active_at_end"] = 1 if truthy in (
        False, True) else True
    # an int (even a truthy one matching the replayed value) is mistyped
    bad["outcome"]["recovery_active_at_end"] = int(truthy)
    _final, errors = replay_a6_recovery(bad)
    assert any("not exactly a bool" in e for e in errors)


def test_iteration_recovery_flag_mistyped_rejected():
    ck = _synthetic_recovery_ck("ambiguous", 2)
    ck["iteration_events"][1]["recovery_active"] = 1  # int, not bool
    _final, errors = replay_a6_recovery(ck)
    assert any("not exactly a bool" in e for e in errors)


def test_raised_identity_caps_rejected():
    """A stream at 5 escalations whose identity ALSO claims a raised cap
    of 5 is internally consistent — but the identity must equal the frozen
    producer constant, so the coordinated raise is rejected."""
    ck = _synthetic_recovery_ck(
        "ambiguous", MAX_PRICING_ESCALATIONS + 1,
        identity_overrides={
            "recovery.max_pricing_escalations": MAX_PRICING_ESCALATIONS + 1,
        })
    _final, errors = replay_a6_recovery(ck)
    assert any("frozen producer constant" in e for e in errors)


def test_divisor_identity_mutation_rejected():
    """/10 divisor with a fully coordinated stream AND identity mutation:
    per-event gaps, the final state, and identity.gap_divisor all agree on
    /10 — the frozen-constant pin still rejects it."""
    ck = _synthetic_recovery_ck(
        "ambiguous", 2,
        identity_overrides={"recovery.gap_divisor": 10.0})
    gap = 1e-6
    for it in ck["iteration_events"]:
        it["pricing_max_mip_gap"] = gap
        gap = max(gap / 10.0, 1e-12)
    ck["pricing_max_mip_gap"] = gap
    _final, errors = replay_a6_recovery(ck)
    assert any("frozen producer constant" in e for e in errors)


def test_refinement_cap_behavior():
    """Refinement retries replay below the cap and reject at it (epsilon
    small enough that a near-zero certified reduced-cost bound does not
    certify)."""
    ck = _synthetic_recovery_ck(
        "refinement", MAX_DUPLICATE_RETRIES - 1, epsilon=1e-9)
    final, errors = replay_a6_recovery(ck)
    assert errors == []
    assert final["refine_retries"] == MAX_DUPLICATE_RETRIES - 1
    assert final["recovery"] == {"kind": "refinement"}

    ck = _synthetic_recovery_ck(
        "refinement", MAX_DUPLICATE_RETRIES, epsilon=1e-9)
    _final, errors = replay_a6_recovery(ck)
    assert any("refine_retries" in e and "impossible" in e for e in errors)


def test_floor_saturation_replays_and_falsification_rejected():
    """Four ambiguous escalations drive the requested gap 1e-6 -> 1e-8 ->
    1e-10 -> 1e-12 -> floor(1e-12); the floor must saturate exactly, and
    claiming the un-floored 1e-14 must be rejected."""
    ck = _synthetic_recovery_ck("ambiguous", MAX_PRICING_ESCALATIONS)
    final, errors = replay_a6_recovery(ck)
    assert errors == []
    assert final["pricing_max_mip_gap"] == 1e-12  # floor engaged
    recorded = [it["pricing_max_mip_gap"] for it in ck["iteration_events"]
                if not it.get("terminal")]
    assert recorded == [1e-6, 1e-8, 1e-10, 1e-12]

    bad = json.loads(json.dumps(ck))
    bad["pricing_max_mip_gap"] = 1e-14  # claims no floor
    _final, errors = replay_a6_recovery(bad)
    assert any("pricing_max_mip_gap" in e for e in errors)


def test_certification_while_recovery_active_replays():
    """The certificate returns BEFORE any recovery mutation: a T0 recovery
    clean call that certifies leaves recovery acknowledged as active at
    the end, with counters frozen at their pre-certificate values."""
    epsilon = 2.0
    theta = A6_THETA_CERT_MULT * epsilon
    ub = z = 10.0
    sigma = 12.0
    # a certified trace ends WITHOUT a terminal event; build the recovery
    # prefix without one and append the certifying clean call below
    ck = _synthetic_recovery_ck("ambiguous", 1, epsilon=epsilon,
                                append_terminal=False)
    # event0 must NOT certify at epsilon=2: widen its certified bound
    it0 = ck["iteration_events"][0]
    bound0 = 7.0
    rc0 = bound0 - sigma
    lb0 = z + min(0.0, rc0)
    ck["oracle_events"][1]["solver"]["bound"] = bound0
    ck["oracle_events"][1]["extra"]["min_reduced_cost_lb"] = rc0
    it0.update(min_reduced_cost_lb=rc0, lb_ch=lb0, lb_best=lb0,
               certificate_gap=ub - lb0)
    ck["lb_history"][0] = lb0
    # event1: T0 clean at tightened gap 1e-8; derived gap 5.0 <= theta so
    # T1 also fires; certifies (cert 1.0 <= 2.0) while recovery is active
    bound1 = 11.0
    rc1 = bound1 - sigma
    lb1 = z + min(0.0, rc1)
    assert ub - lb0 > epsilon and ub - lb1 <= epsilon
    assert ub - lb0 <= theta  # T1 fires alongside T0
    fired = ["T0", "T1"]
    ck["oracle_events"].append({
        "regime": "cg-pricing",
        "solver": {"bound": bound1},
        "extra": {"tag": "a6_a4", "call_id": "a6_a4-oc2",
                  "call_kind": "clean", "trigger_selected": "T0",
                  "triggers_fired": fired, "column_novel": False,
                  "min_reduced_cost_ub": 1.0, "min_reduced_cost_lb": rc1}})
    ck["iteration_events"].append({
        "iteration_id": "a6_a4-it2",
        "call_kind": "clean", "trigger_selected": "T0",
        "triggers_fired": fired,
        "gap_at_decision": ub - lb0,
        "k_since_clean": 0, "n_columns": 1,
        "recovery_active": True, "recovery_kind": "ambiguous",
        "pricing_solve_id": "a6_a6-oc2".replace("a6_a6", "a6_a4"),
        "pricing_max_mip_gap": 1e-8,
        "ub_ch": ub, "z_rmp_model": z, "duals_sigma": sigma,
        "min_reduced_cost_ub": 1.0, "min_reduced_cost_lb": rc1,
        "lb_ch": lb1, "lb_best": max(lb0, lb1),
        "certificate_gap": ub - max(lb0, lb1),
        "column_novel": False,
    })
    ck["ub_history"].append(ub)
    ck["lb_history"].append(max(lb0, lb1))
    ck["lb_best"] = max(lb0, lb1)
    ck["oracle_calls"] = 3
    ck["scheduler"]["n_clean_pricing"] = 2
    ck["outcome"] = {"type": "certified", "certified": True,
                     "ub_ch": ub, "lb_best": max(lb0, lb1),
                     "gap": ub - max(lb0, lb1), "oracle_calls": 3,
                     "method": "a6_a4", "recovery_active_at_end": True}
    final, errors = replay_a6_recovery(ck)
    assert errors == []
    assert final["certified"] is True
    assert final["recovery"] == {"kind": "ambiguous"}
    assert final["pricing_escalations"] == 1  # frozen, not reset

    bad = json.loads(json.dumps(ck))
    bad["outcome"]["recovery_active_at_end"] = False
    _final, errors = replay_a6_recovery(bad)
    assert any("recovery_active_at_end" in e for e in errors)


# --------------------------------------------------------------------------
# E2 (EI-025): terminal / final-state / outcome closure.  Each edit below
# was reproduced ACCEPTED by the shared helper before the closure and must
# now be rejected.  A real CERTIFIED trace is the base for the certificate
# edits; a synthetic BUDGET-exhausted trace is the base for the terminal
# edits.
# --------------------------------------------------------------------------
def _certified_ck(recovery_trace):
    ck, _ = recovery_trace
    assert ck["outcome"]["type"] == "certified"
    return json.loads(json.dumps(ck))


def test_e2_flip_outcome_certified_after_derived_certificate(recovery_trace):
    """Exploit 1: a derived-certified trace whose outcome.certified is
    flipped to False (accepted before closure)."""
    bad = _certified_ck(recovery_trace)
    bad["outcome"]["certified"] = False
    _final, errors = replay_a6_recovery(bad)
    assert any("outcome certified=" in e and "event stream replays" in e
               for e in errors)
    assert any("outcome certified=" in e for e in _cg_sane(bad))


def test_e2_coordinated_lb_gap_inflation_rejected(recovery_trace):
    """Exploit 2: top-level checkpoint lb_best and outcome LB/gap coherently
    inflated by 5e-4 (mutually consistent, accepted before closure)."""
    bad = _certified_ck(recovery_trace)
    bad["lb_best"] += 5e-4
    bad["outcome"]["lb_best"] += 5e-4
    bad["outcome"]["gap"] -= 5e-4
    _final, errors = replay_a6_recovery(bad)
    assert any("recorded lb_best=" in e and "event stream replays" in e
               for e in errors)
    assert any("lb_best" in e for e in _cg_sane(bad))


def _append_fake_terminal(ck):
    last = [e for e in ck["iteration_events"] if not e.get("terminal")][-1]
    ub = last["ub_ch"]
    lb_best = ck["lb_best"]
    ck["iteration_events"].append({
        "record_kind": "cg-iteration", "terminal": True, "phase": "terminal",
        "iteration_id": "a6_a4-itX-terminal", "oracle_calls": ck["oracle_calls"],
        "n_columns": last.get("n_columns"), "ub_ch": ub, "lb_best": lb_best,
        "certificate_gap": ub - lb_best, "pricing_solve_id": None,
    })
    ck["ub_history"].append(ub)
    ck["lb_history"].append(lb_best)
    return ck


def test_e2_terminal_after_certificate_rejected(recovery_trace):
    """Exploit 3: a terminal event (plus matching history) appended after a
    certificate was already derived (accepted before closure)."""
    bad = _append_fake_terminal(_certified_ck(recovery_trace))
    _final, errors = replay_a6_recovery(bad)
    assert any("events continue after the certificate returned" in e
               for e in errors)
    assert any("events continue after the certificate returned" in e
               for e in _cg_sane(bad))


def test_e2_budget_terminal_deleted_rejected():
    """A completed budget-exhausted trace with its required terminal removed
    no longer closes."""
    ck = _synthetic_recovery_ck("ambiguous", 2)
    assert ck["iteration_events"][-1].get("terminal") is True
    del ck["iteration_events"][-1]
    del ck["ub_history"][-1]
    del ck["lb_history"][-1]
    _final, errors = replay_a6_recovery(ck)
    assert any("neither a certificate nor a terminal event" in e
               for e in errors)


def test_e2_second_budget_terminal_rejected():
    """Two terminal events cannot close one trace."""
    ck = _synthetic_recovery_ck("ambiguous", 2)
    ck["iteration_events"].append(copy.deepcopy(ck["iteration_events"][-1]))
    ck["ub_history"].append(ck["ub_history"][-1])
    ck["lb_history"].append(ck["lb_history"][-1])
    _final, errors = replay_a6_recovery(ck)
    assert any("events continue after the terminal event" in e
               for e in errors)


def test_e2_falsified_terminal_lb_best_rejected():
    """The terminal master's committed lb_best must replay exactly."""
    ck = _synthetic_recovery_ck("ambiguous", 2)
    ck["iteration_events"][-1]["lb_best"] += 5e-4
    _final, errors = replay_a6_recovery(ck)
    assert any("terminal lb_best=" in e for e in errors)


def test_e2_falsified_terminal_n_columns_rejected():
    """The terminal master's committed n_columns must replay exactly."""
    ck = _synthetic_recovery_ck("ambiguous", 2)
    ck["iteration_events"][-1]["n_columns"] = 99
    _final, errors = replay_a6_recovery(ck)
    assert any("terminal n_columns=" in e for e in errors)


def test_e2_oracle_iteration_reduced_cost_disagreement_rejected():
    """Oracle and iteration reduced-cost evidence for the same clean call
    may not disagree."""
    ck = _synthetic_recovery_ck("ambiguous", 2)
    it = next(e for e in ck["iteration_events"]
              if e.get("call_kind") == "clean")
    it["min_reduced_cost_lb"] = it["min_reduced_cost_lb"] + 1.0
    _final, errors = replay_a6_recovery(ck)
    assert any("reduced-cost evidence disagrees" in e for e in errors)


def test_e2_oracle_iteration_novelty_disagreement_rejected():
    """Oracle and iteration column-novelty for the same call may not
    disagree."""
    ck = _synthetic_recovery_ck("ambiguous", 2)
    oc = next(e for e in ck["oracle_events"]
              if (e.get("extra") or {}).get("call_kind") == "clean")
    oc["extra"]["column_novel"] = True  # iteration says False
    _final, errors = replay_a6_recovery(ck)
    assert any("column_novel" in e and "disagrees" in e for e in errors)
