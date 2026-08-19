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
def _synthetic_recovery_ck(kind: str, repeats: int) -> dict:
    """A minimal internally consistent a6 stream of `repeats` consecutive
    recovery clean calls of one kind (ambiguous or duplicate), with every
    per-event label, counter, and gap value coordinated with the tamper."""
    base_gap = 1e-6
    identity = {
        "method": "a6_a4", "epsilon": 1e-2, "rc_tol": 1e-6,
        "solver": {"backend": "CBC", "max_mip_gap": base_gap},
        "scheduler": {"theta_cert": A6_THETA_CERT_MULT * 1e-2,
                      "k_max": A6_K_MAX,
                      "priority": list(A6_PRIORITY) + [DEFAULT_CANDIDATE]},
        "recovery": {"max_pricing_escalations": MAX_PRICING_ESCALATIONS,
                     "max_duplicate_retries": MAX_DUPLICATE_RETRIES,
                     "gap_divisor": 100.0, "gap_floor": 1e-12},
    }
    events = [{"regime": "cg-seed",
               "extra": {"tag": "a6_a4", "call_id": "a6_a4-oc0"}}]
    iterations = []
    gap = base_gap
    escalations = 0
    duplicates = 0
    lb_history = []
    for i in range(repeats):
        call_id = f"a6_a4-oc{i + 1}"
        fired = ["T4"] if i == 0 else ["T0"]
        if kind == "ambiguous":
            rc_ub, rc_lb = 1.0, -1.0
        else:  # duplicate improving
            rc_ub, rc_lb = -1.0, -1.0
        events.append({
            "regime": "cg-pricing",
            "extra": {"tag": "a6_a4", "call_id": call_id,
                      "call_kind": "clean", "trigger_selected": fired[0],
                      "triggers_fired": fired}})
        iterations.append({
            "iteration_id": f"a6_a4-it{i + 1}",
            "call_kind": "clean", "trigger_selected": fired[0],
            "triggers_fired": fired,
            "gap_at_decision": float("inf") if i == 0 else 5.0,
            "k_since_clean": 0, "n_columns": 1,
            "recovery_active": i > 0,
            "recovery_kind": None if i == 0 else kind,
            "pricing_solve_id": call_id,
            "pricing_max_mip_gap": gap,
            "min_reduced_cost_ub": rc_ub,
            "min_reduced_cost_lb": rc_lb,
            "certificate_gap": 5.0,
            "column_novel": False,
        })
        lb_history.append(5.0)
        if kind == "ambiguous":
            escalations += 1
            gap = max(gap / 100.0, 1e-12)
        else:
            duplicates += 1
    return {
        "done": True,
        "identity": identity,
        "oracle_calls": repeats + 1,
        "oracle_events": events,
        "iteration_events": iterations,
        "lb_history": lb_history,
        "duplicate_retries": duplicates,
        "refine_retries": 0,
        "pricing_escalations": escalations,
        "pricing_max_mip_gap": gap,
        "scheduler": {"k_since_clean": 0,
                      "n_clean_pricing": repeats,
                      "last_candidate_novel": None,
                      "recovery": {"kind": kind}},
        "outcome": {"type": "budget_exhausted", "certified": False,
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
