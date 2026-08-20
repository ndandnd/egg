"""Acceptance battery for A6 event-triggered sparse stabilization
(doc/A6_SPARSE_STABILIZATION_SPEC.md): trigger priority, T0 recovery,
spacing/accounting invariants, certification purity, preemption,
identity, audit trigger-stream integrity, pilot grid, and the one-shot
selection pipeline."""
import copy
import itertools
import json
import os
import shutil
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

import egglab.a6 as a6_mod
import egglab.b2a2 as b2a2_mod
import egglab.b2a345 as b2a345_mod
from egglab import checkpoint
from egglab.a6 import (
    A6_K_MAX,
    A6_PRIORITY,
    CLEAN_TRIGGERS,
    DEFAULT_CANDIDATE,
    certified_cg_a6,
    select_trigger,
)
from egglab.b2a2 import B2A2Error
from egglab.enumerate_tiny import enumerated_ch
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from experiments.analyze_b2_pilot import AnalysisError
from experiments.audit_runs import audit
from experiments.run_a6_pilot import BUDGET, EPSILON, TOL_D, build_cells
from experiments.run_b2a2_pilot import _dictator_stage
from experiments.select_a6_arm import cell_score, select
from tests.test_b2a2 import (_read_jsonl, _reprice_physical_solution,
                             _strip_volatile)

MINI_INSTANCES = ((1, 4, 0.01), (3, 4, 0.05))


def fix_builder(seed, n_trips):
    return synthetic_instance(seed=seed, n_trips=n_trips, max_vehicles=2)


@pytest.fixture(scope="module")
def tiny():
    inst = fix_builder(1, 4)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    return inst, market


@pytest.fixture(scope="module")
def a6_runs(tiny, tmp_path_factory):
    inst, market = tiny
    runs = {}
    for m in ("a6_a4", "a6_a3"):
        out = str(tmp_path_factory.mktemp(m))
        state = certified_cg_a6(inst, market, method=m, epsilon=1e-2,
                                budget=120, out_dir=out, tag=m)
        runs[m] = (state, out)
    return runs


@pytest.fixture(scope="module")
def ref_a6(tiny, tmp_path_factory):
    inst, market = tiny
    out = str(tmp_path_factory.mktemp("ref"))
    state = certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                            budget=120, out_dir=out, tag="p6")
    return state, out


def _events(state):
    return [e for e in state["iteration_events"] if not e.get("terminal")]


# --------------------------------------------------------------------------
# 1. trigger-priority truth table
# --------------------------------------------------------------------------
def test_trigger_priority_truth_table():
    for combo in itertools.product([False, True], repeat=len(A6_PRIORITY)):
        fired = dict(zip(A6_PRIORITY, combo))
        expected = next((t for t in A6_PRIORITY if fired[t]),
                        DEFAULT_CANDIDATE)
        assert select_trigger(fired) == expected, fired
    assert select_trigger({}) == DEFAULT_CANDIDATE


# --------------------------------------------------------------------------
# 2. T0 recovery cannot be interrupted
# --------------------------------------------------------------------------
def test_t0_recovery_uninterruptible(tiny, tmp_path, monkeypatch):
    """Force ambiguous clean pricing forever: after recovery starts, every
    subsequent call must be a T0 clean call (no candidate ever runs), and
    the bounded escalation fails loudly."""
    inst, market = tiny
    real_solve = b2a2_mod.solve_taker
    first = {}

    def fake(_inst, prices, **kw):
        if "sol" not in first:
            first["sol"] = real_solve(_inst, prices, **kw)
            return first["sol"]
        sol = copy.deepcopy(first["sol"])
        _reprice_physical_solution(sol, prices)
        sol.stats.bound = -1e9
        return sol

    monkeypatch.setattr(a6_mod, "solve_taker", fake)
    with pytest.raises(B2A2Error, match="cannot certify exhaustion"):
        certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                        budget=60, out_dir=str(tmp_path), tag="t0")
    ck = checkpoint.load(os.path.join(str(tmp_path), "t0.cg.ckpt.json"))
    evs = [e for e in ck["iteration_events"] if not e.get("terminal")]
    assert evs[0]["trigger_selected"] == "T4"
    for e in evs[1:]:
        assert e["recovery_active"] is True
        assert e["trigger_selected"] == "T0"
        assert e["call_kind"] == "clean"
    assert ck["calls_stab"] == 0  # no candidate ever interrupted recovery


# --------------------------------------------------------------------------
# 3-5. spacing, certification purity, one-call accounting
# --------------------------------------------------------------------------
@pytest.mark.parametrize("method", ("a6_a4", "a6_a3"))
def test_clean_spacing_invariant(a6_runs, method):
    state, _ = a6_runs[method]
    run = 0
    for e in _events(state):
        if e["call_kind"] == "candidate":
            assert not e["recovery_active"]
            run += 1
            assert run <= A6_K_MAX, "spacing exceeded outside recovery"
        else:
            run = 0


@pytest.mark.parametrize("method", ("a6_a4", "a6_a3"))
def test_candidates_never_update_lb_or_certify(a6_runs, method):
    state, _ = a6_runs[method]
    evs = _events(state)
    lb = state["lb_history"]
    assert len(lb) == len(evs) or len(lb) == len(evs) + 1  # + terminal entry
    prev = -float("inf")
    for i, e in enumerate(evs):
        if e["call_kind"] == "candidate":
            assert lb[i] == prev, "candidate call moved LB_best"
        prev = lb[i]
    # the certifying call must be clean
    assert evs[-1]["call_kind"] == "clean"
    assert state["outcome"]["certified"]


def test_candidate_theta_injection_cannot_certify(tiny, tmp_path,
                                                  monkeypatch):
    inst, market = tiny
    monkeypatch.setattr(b2a345_mod, "theta_cert", lambda *_a, **_k: 1e12)
    state = certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                            budget=120, out_dir=str(tmp_path), tag="inj")
    oc = state["outcome"]
    assert oc["certified"] and oc["gap"] >= 0
    assert state["lb_best"] <= oc["ub_ch"] + 1e-9  # LB stayed clean-derived


@pytest.mark.parametrize("method", ("a6_a4", "a6_a3"))
def test_one_call_per_iteration_accounting(a6_runs, method):
    state, _ = a6_runs[method]
    evs = _events(state)
    # seed + exactly one oracle call per master iteration
    assert state["oracle_calls"] == 1 + len(evs)
    assert len(state["oracle_events"]) == state["oracle_calls"]
    ids = [(e.get("extra") or {}).get("call_id")
           for e in state["oracle_events"]]
    assert ids == [f"{method}-oc{i}" for i in range(len(ids))]
    oc = state["outcome"]
    assert oc["oracle_calls_clean"] + oc["oracle_calls_stab"] == \
        state["oracle_calls"]
    # every non-terminal iteration event carries exactly one pricing call
    assert all(e.get("pricing_solve_id") for e in evs)


@pytest.mark.parametrize("method", ("a6_a4", "a6_a3"))
def test_brackets_enumerated_zch(a6_runs, tiny, method):
    inst, market = tiny
    ch = enumerated_ch(inst, market)
    state, _ = a6_runs[method]
    assert state["lb_best"] <= ch["z_ch"] + 2.2e-3
    assert state["outcome"]["ub_ch"] >= ch["z_ch"] - 2.2e-3


# --------------------------------------------------------------------------
# 6. preemption at every scheduler/checkpoint boundary
# --------------------------------------------------------------------------
def _resume_and_compare(tiny, out, ref):
    inst, market = tiny
    state = certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                            budget=120, out_dir=out, tag="p6")
    ref_state, ref_out = ref
    for fn in ("p6.oracle.jsonl", "p6.iterations.jsonl"):
        got = _read_jsonl(os.path.join(out, fn))
        want = _read_jsonl(os.path.join(ref_out, fn))
        assert _strip_volatile(got) == _strip_volatile(want), fn
    ids = [r["extra"]["call_id"]
           for r in _read_jsonl(os.path.join(out, "p6.oracle.jsonl"))]
    assert len(ids) == len(set(ids))
    assert state["outcome"]["ub_ch"] == pytest.approx(
        ref_state["outcome"]["ub_ch"], abs=1e-9)


def test_preempt_during_candidate_solve(tiny, ref_a6, tmp_path, monkeypatch):
    inst, market = tiny
    out = str(tmp_path)
    real_solve = a6_mod.solve_taker
    calls = {"n": 0}

    def dying(_inst, prices, **kw):
        calls["n"] += 1
        if calls["n"] == 3:  # seed, clean (T4), then the first candidate
            raise KeyboardInterrupt("killed in-flight candidate")
        return real_solve(_inst, prices, **kw)

    monkeypatch.setattr(a6_mod, "solve_taker", dying)
    with pytest.raises(KeyboardInterrupt):
        certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                        budget=120, out_dir=out, tag="p6")
    ck = checkpoint.load(os.path.join(out, "p6.cg.ckpt.json"))
    assert ck["oracle_calls"] == 2  # in-flight candidate not committed
    monkeypatch.setattr(a6_mod, "solve_taker", real_solve)
    _resume_and_compare(tiny, out, ref_a6)


def test_preempt_after_checkpoint_before_materialization(tiny, ref_a6,
                                                         tmp_path,
                                                         monkeypatch):
    inst, market = tiny
    out = str(tmp_path)
    real_mat = a6_mod._materialize_logs
    n = {"v": 0}

    def dying(state, oc_path, it_path):
        n["v"] += 1
        if n["v"] == 4:
            raise KeyboardInterrupt("killed before materialization")
        return real_mat(state, oc_path, it_path)

    monkeypatch.setattr(a6_mod, "_materialize_logs", dying)
    with pytest.raises(KeyboardInterrupt):
        certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                        budget=120, out_dir=out, tag="p6")
    monkeypatch.setattr(a6_mod, "_materialize_logs", real_mat)
    _resume_and_compare(tiny, out, ref_a6)


def test_preempt_during_materialization(tiny, ref_a6, tmp_path, monkeypatch):
    inst, market = tiny
    out = str(tmp_path)
    real_write = b2a2_mod._atomic_write_lines
    n = {"v": 0}

    def dying(path, records):
        n["v"] += 1
        if n["v"] == 7:
            raise KeyboardInterrupt("killed mid-materialization")
        return real_write(path, records)

    monkeypatch.setattr(b2a2_mod, "_atomic_write_lines", dying)
    with pytest.raises(KeyboardInterrupt):
        certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                        budget=120, out_dir=out, tag="p6")
    monkeypatch.setattr(b2a2_mod, "_atomic_write_lines", real_write)
    _resume_and_compare(tiny, out, ref_a6)


def test_deterministic_rerun(tiny, ref_a6, tmp_path):
    inst, market = tiny
    out = str(tmp_path)
    certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                    budget=120, out_dir=out, tag="p6")
    _resume_and_compare(tiny, out, ref_a6)


# --------------------------------------------------------------------------
# 7. identity rejection for every new constant
# --------------------------------------------------------------------------
@pytest.mark.parametrize("target,attr,value", [
    ("a6", "A6_THETA_CERT_MULT", 20.0),
    ("a6", "A6_K_MAX", 6),
    ("a6", "A6_PRIORITY", ("T0", "T3", "T4", "T1", "T2")),
    ("a6", "MAX_PRICING_ESCALATIONS", 7),
    ("b2a345", "A4_ALPHA_DECR", 0.2),
])
def test_identity_rejects_changed_constants(a6_runs, tiny, monkeypatch,
                                            target, attr, value):
    inst, market = tiny
    _, out = a6_runs["a6_a4"]
    mod = a6_mod if target == "a6" else b2a345_mod
    monkeypatch.setattr(mod, attr, value)
    with pytest.raises(B2A2Error, match="identity mismatch"):
        certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                        budget=120, out_dir=out, tag="a6_a4")


def test_identity_rejects_changed_a3_constant(a6_runs, tiny, monkeypatch):
    inst, market = tiny
    _, out = a6_runs["a6_a3"]
    monkeypatch.setattr(b2a345_mod, "A3_ZETA1", 0.7)
    with pytest.raises(B2A2Error, match="identity mismatch"):
        certified_cg_a6(inst, market, method="a6_a3", epsilon=1e-2,
                        budget=120, out_dir=out, tag="a6_a3")


def test_identity_accepts_exact_match(a6_runs, tiny):
    inst, market = tiny
    state0, out = a6_runs["a6_a4"]
    state = certified_cg_a6(inst, market, method="a6_a4", epsilon=1e-2,
                            budget=120, out_dir=out, tag="a6_a4")
    assert state["done"] and state["outcome"] == state0["outcome"]


# --------------------------------------------------------------------------
# 8. audit rejection for falsified trigger streams
# --------------------------------------------------------------------------
def _audited_copy(a6_runs, tmp_path, mutate):
    _, out = a6_runs["a6_a4"]
    root = str(tmp_path / "root")
    d = os.path.join(root, "cell")
    os.makedirs(d, exist_ok=True)
    for fn in ("a6_a4.cg.ckpt.json", "a6_a4.iterations.jsonl",
               "a6_a4.oracle.jsonl"):
        shutil.copy(os.path.join(out, fn), os.path.join(d, fn))
    p = os.path.join(d, "a6_a4.cg.ckpt.json")
    ck = checkpoint.load(p)
    mutate(ck)
    checkpoint.save(p, ck)
    return audit(root, expect_cg=1)


def test_audit_clean_run_passes(a6_runs, tmp_path):
    _, ok, problems = _audited_copy(a6_runs, tmp_path, lambda ck: None)
    assert ok, problems


def test_audit_rejects_priority_violation(a6_runs, tmp_path):
    def mutate(ck):
        ev = next(e for e in ck["iteration_events"]
                  if e.get("call_kind") == "candidate")
        ev["triggers_fired"] = ["T2"]  # fired but not selected -> violation

    _, ok, problems = _audited_copy(a6_runs, tmp_path, mutate)
    assert not ok and any("recomputed" in p for p in problems)


def test_audit_rejects_candidate_on_clean_trigger(a6_runs, tmp_path):
    def mutate(ck):
        ev = next(e for e in ck["iteration_events"]
                  if e.get("call_kind") == "candidate")
        ev["trigger_selected"] = "T0"
        ev["triggers_fired"] = ["T0"]

    _, ok, problems = _audited_copy(a6_runs, tmp_path, mutate)
    assert not ok and any("recomputed" in p for p in problems)


def test_audit_rejects_candidate_during_recovery(a6_runs, tmp_path):
    def mutate(ck):
        ev = next(e for e in ck["iteration_events"]
                  if e.get("call_kind") == "candidate")
        ev["recovery_active"] = True

    _, ok, problems = _audited_copy(a6_runs, tmp_path, mutate)
    assert not ok and any("recovery_active" in p for p in problems)


def test_audit_rejects_falsified_column_count(a6_runs, tmp_path):
    def mutate(ck):
        ev = next(e for e in ck["iteration_events"]
                  if not e.get("terminal"))
        ev["n_columns"] += 1

    _, ok, problems = _audited_copy(a6_runs, tmp_path, mutate)
    assert not ok and any("n_columns" in p for p in problems)


def test_audit_rejects_falsified_recovery_kind(a6_runs, tmp_path):
    def mutate(ck):
        ev = next(e for e in ck["iteration_events"]
                  if not e.get("terminal"))
        ev["recovery_kind"] = "ambiguous"

    _, ok, problems = _audited_copy(a6_runs, tmp_path, mutate)
    assert not ok and any("recovery_kind" in p for p in problems)


def test_audit_rejects_excess_spacing(a6_runs, tmp_path):
    def mutate(ck):
        # relabel a clean iteration as a candidate to break the spacing
        # bound (and fabricate consistent trigger fields)
        evs = [e for e in ck["iteration_events"] if not e.get("terminal")]
        for e in evs:
            if e.get("call_kind") == "clean" and e.get(
                    "trigger_selected") in ("T2", "T3"):
                e["call_kind"] = "candidate"
                e["trigger_selected"] = DEFAULT_CANDIDATE
                e["triggers_fired"] = []
                e["recovery_active"] = False

    _, ok, problems = _audited_copy(a6_runs, tmp_path, mutate)
    assert not ok and any("recomputed" in p or "k_since_clean" in p
                          for p in problems)


# --------------------------------------------------------------------------
# 9. pilot grid
# --------------------------------------------------------------------------
def test_pilot_grid_exact_24_no_holdout_seeds():
    cells = build_cells()
    assert len(cells) == 24
    assert sum(1 for c in cells if c[0] == "a6_a4") == 12
    assert sum(1 for c in cells if c[0] == "a6_a3") == 12
    assert len(set(cells)) == 24
    for (m, s, n, b) in cells:
        assert s in (0, 11, 15)
        assert s < 16, "holdout seed leaked into the pilot"
    assert EPSILON == 1e-2 and BUDGET == 240 and TOL_D == 1e-2


# --------------------------------------------------------------------------
# 10. selection pipeline: scoring and decision
# --------------------------------------------------------------------------
def _fake_ck(certified, calls, outcome_type=None):
    return {"outcome": {"certified": certified, "oracle_calls": calls,
                        "type": outcome_type or
                        ("certified" if certified else "budget_exhausted")}}


def test_cell_score_rules():
    assert cell_score(_fake_ck(True, 17), "x") == 17
    assert cell_score(_fake_ck(False, 240), "x") == 241
    with pytest.raises(AnalysisError, match="unscorable"):
        cell_score({"outcome": {"certified": False, "type": "weird",
                                "oracle_calls": 3}}, "x")


@pytest.fixture(scope="module")
def mini_pilot(tmp_path_factory):
    """Real mini pilot root: both arms on 2 tiny instances."""
    root = str(tmp_path_factory.mktemp("pilot"))
    kw = dict(max_mip_gap=1e-6, time_limit_s=None)
    for (s, n, b) in MINI_INSTANCES:
        inst = fix_builder(s, n)
        market = make_affine_market(inst, shape="duck", b_scale=b)
        for m in ("a6_a4", "a6_a3"):
            out = os.path.join(root, f"{m}_s{s}_n{n}_b{b:g}")
            os.makedirs(out, exist_ok=True)
            d_state = _dictator_stage(inst, market, out, f"{m}_{s}",
                                      [m, s, n, b], kw)
            certified_cg_a6(inst, market, method=m, epsilon=1e-2, budget=60,
                            out_dir=out, tag=m, solver_kw=kw,
                            z_d_ub=d_state["z_d_ub"], tol_d=d_state["tol_d"])
    return root


def test_selection_artifact_end_to_end(mini_pilot, tmp_path):
    out = select(mini_pilot, str(tmp_path), "TESTSTAMP", "codecommit0",
                 instances=MINI_INSTANCES, win_threshold=2,
                 instance_builder=fix_builder, verify_code_commit=False)
    sel = json.load(open(os.path.join(out, "SELECTION.json")))
    assert sel["selected_arm"] in ("a6_a4", "a6_a3")
    assert sel["n_instances"] == 2 and sel["win_threshold"] == 2
    assert len(sel["per_cell"]) == 4 and len(sel["matched"]) == 2
    assert sel["inputs"]["files"]  # input hashes present
    # recompute the decision from the artifact's own tables
    wins = sum(1 for r in sel["matched"] if r["a6_a3_wins"])
    assert wins == sel["a6_a3_wins"]
    assert sel["selected_arm"] == (
        "a6_a3" if wins >= sel["win_threshold"] else "a6_a4")
    # deterministic regeneration
    out2 = select(mini_pilot, str(tmp_path / "again"), "TESTSTAMP",
                  "codecommit0", instances=MINI_INSTANCES, win_threshold=2,
                  instance_builder=fix_builder, verify_code_commit=False)
    assert (open(os.path.join(out, "SELECTION.json"), "rb").read()
            == open(os.path.join(out2, "SELECTION.json"), "rb").read())


def test_selection_decision_thresholds(mini_pilot, tmp_path, monkeypatch):
    """Exhaustive decision tests on synthetic score patterns via the real
    pipeline.  Checkpoints stay byte-coherent (the audit — which now binds
    outcome.oracle_calls to the event stream — must pass); synthetic scores
    are injected by monkeypatching cell_score, never by corrupting evidence."""
    import re
    import experiments.select_a6_arm as sel_mod
    real_cell_score = sel_mod.cell_score

    def run_with_scores(a4_scores, a3_scores, out):
        score_map = {}
        for score_by_inst, m in ((a4_scores, "a6_a4"), (a3_scores, "a6_a3")):
            for inst, sc in score_by_inst.items():
                score_map[(m, inst)] = sc

        def fake_cell_score(ck, label):
            # label is "{method} seed={s} n={n} b={b}"; keep the audit's
            # coherence guarantee by still exercising the real scorer
            real_cell_score(ck, label)
            method = label.split()[0]
            s = int(re.search(r"seed=(\d+)", label).group(1))
            n = int(re.search(r"n=(\d+)", label).group(1))
            b = float(re.search(r"b=([0-9.]+)", label).group(1))
            return score_map[(method, (s, n, b))]

        monkeypatch.setattr(sel_mod, "cell_score", fake_cell_score)
        result = select(mini_pilot, out, "T", "c",
                        instances=MINI_INSTANCES, win_threshold=2,
                        instance_builder=fix_builder, verify_code_commit=False)
        monkeypatch.undo()
        return json.load(open(os.path.join(result, "SELECTION.json")))

    # a6_a3 strictly better on both instances -> wins 2/2 >= threshold 2
    sel = run_with_scores(
        {MINI_INSTANCES[0]: 30, MINI_INSTANCES[1]: 30},
        {MINI_INSTANCES[0]: 10, MINI_INSTANCES[1]: 10},
        str(tmp_path / "o1"))
    assert sel["selected_arm"] == "a6_a3"

    # tie on one instance (ties are non-wins) -> 1 win < 2 -> a6_a4
    sel = run_with_scores(
        {MINI_INSTANCES[0]: 10, MINI_INSTANCES[1]: 30},
        {MINI_INSTANCES[0]: 10, MINI_INSTANCES[1]: 10},
        str(tmp_path / "o2"))
    assert sel["selected_arm"] == "a6_a4"


def test_selection_aborts_on_outcome_oracle_calls_edit(mini_pilot, tmp_path):
    """End-to-end F1: a single-field outcome.oracle_calls edit in one cell
    now fails the audit (via the shared replay's oracle-call provenance) and
    aborts selection — nothing is scored."""
    dst = str(tmp_path / "edited")
    shutil.copytree(mini_pilot, dst)
    s, n, b = MINI_INSTANCES[0]
    p = os.path.join(dst, f"a6_a4_s{s}_n{n}_b{b:g}", "a6_a4.cg.ckpt.json")
    ck = checkpoint.load(p)
    ck["outcome"]["oracle_calls"] = int(ck["outcome"]["oracle_calls"]) + 1
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="selection aborted"):
        select(dst, str(tmp_path / "o"), "T", "c",
               instances=MINI_INSTANCES, win_threshold=2,
               instance_builder=fix_builder, verify_code_commit=False)


def test_selection_aborts_on_failed_audit(mini_pilot, tmp_path):
    dst = str(tmp_path / "bad")
    shutil.copytree(mini_pilot, dst)
    shutil.rmtree(os.path.join(
        dst, f"a6_a3_s{MINI_INSTANCES[0][0]}_n4_b0.01"))
    with pytest.raises(AnalysisError, match="selection aborted"):
        select(dst, str(tmp_path / "o"), "T", "c",
               instances=MINI_INSTANCES, win_threshold=2,
               instance_builder=fix_builder, verify_code_commit=False)


def test_selection_code_commit_verification(mini_pilot, tmp_path):
    with pytest.raises(AnalysisError, match="cannot resolve|code commit mismatch"):
        select(mini_pilot, str(tmp_path), "T",
               "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
               instances=MINI_INSTANCES, win_threshold=2,
               instance_builder=fix_builder, verify_code_commit=True)
