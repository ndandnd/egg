"""Acceptance battery for A3-A5 stabilized column generation
(doc/B2_STABILIZATION_SPEC.md), sharing the tiny complete-enumeration gate
and the transactional architecture with the A2 battery."""
import copy
import json
import math
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

import egglab.b2a2 as b2a2_mod
import egglab.b2a345 as b2a345_mod
from egglab import checkpoint
from egglab.b2a2 import B2A2Error, PWL_TOL, certified_cg
from egglab.b2a345 import (
    A3_D2_OVER_D1,
    A3_ZETA1,
    A4_ALPHA_DECR,
    A4_ALPHA_INCR_FRAC,
    A4_ALPHA_MAX,
    A5_K,
    A5_T_MIN,
    a3_update,
    a4_alpha_update,
    a4_direction_signal,
    a5_hinges,
    a5_penalty_value,
    a5_update,
    initial_stab_state,
    serious_step,
    theta_cert,
)
from egglab.enumerate_tiny import (
    PWL_TOL as ENUM_TOL,
    enumerated_ch,
    enumerated_dictator,
)
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.regimes import solve_dictator
from experiments.audit_runs import audit
from experiments.run_b2a345_pilot import BUDGET, EPSILON, build_cells
from tests.test_b2a2 import _read_jsonl, _strip_volatile

TOL_D = 1e-3
SLACK = PWL_TOL + ENUM_TOL + 1e-6
METHODS = ("a3", "a4", "a5")


@pytest.fixture(scope="module")
def tiny():
    inst = synthetic_instance(seed=1, n_trips=4, max_vehicles=2)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    return inst, market


@pytest.fixture(scope="module")
def enum_truth(tiny):
    inst, market = tiny
    return enumerated_ch(inst, market), enumerated_dictator(inst, market)


@pytest.fixture(scope="module")
def dictator(tiny):
    inst, market = tiny
    return solve_dictator(inst, market, tol_abs=TOL_D)


@pytest.fixture(scope="module")
def stab_runs(tiny, dictator, tmp_path_factory):
    """One certified run per stabilized method on the tiny instance."""
    inst, market = tiny
    runs = {}
    for m in METHODS:
        out = str(tmp_path_factory.mktemp(m))
        state = certified_cg(inst, market, epsilon=1e-2, budget=120,
                             out_dir=out, tag=m, method=m,
                             z_d_ub=dictator.obj_true, tol_d=TOL_D)
        runs[m] = (state, out)
    return runs


# --------------------------------------------------------------------------
# tiny complete-enumeration gate for each stabilized method
# --------------------------------------------------------------------------
@pytest.mark.parametrize("method", METHODS)
def test_certifies_and_brackets_enumerated_zch(stab_runs, enum_truth, method):
    (state, _), (ch, _) = stab_runs[method], enum_truth
    oc = state["outcome"]
    assert oc["type"] == "certified" and oc["certified"]
    assert oc["gap"] <= 1e-2
    # final interval brackets the enumerated z_CH
    assert state["lb_best"] <= ch["z_ch"] + SLACK
    assert oc["ub_ch"] >= ch["z_ch"] - SLACK
    assert abs(oc["ub_ch"] - ch["z_ch"]) <= SLACK + 1e-2
    for lb, ub in zip(state["lb_history"], state["ub_history"]):
        assert lb <= ch["z_ch"] + SLACK
        assert ub >= ch["z_ch"] - SLACK


@pytest.mark.parametrize("method", METHODS)
def test_uplift_interval_brackets_enumerated(stab_runs, enum_truth, method):
    (state, _), (ch, dd) = stab_runs[method], enum_truth
    lo, hi = state["outcome"]["uplift_interval"]
    true_uplift = dd["z_d"] - ch["z_ch"]
    assert lo - SLACK <= true_uplift <= hi + SLACK, (lo, true_uplift, hi)


@pytest.mark.parametrize("method", METHODS)
def test_pricing_exhaustion_closes_bound(tiny, tmp_path, method):
    inst, market = tiny
    state = certified_cg(inst, market, epsilon=5e-4, budget=200,
                         out_dir=str(tmp_path / method), tag=method,
                         method=method, pwl_tol=1e-5)
    assert state["outcome"]["type"] == "certified"
    assert state["outcome"]["gap"] <= 5e-4


@pytest.mark.parametrize("method", METHODS)
def test_clean_ub_nonincreasing(stab_runs, method):
    state, _ = stab_runs[method]
    ub = state["ub_history"]
    for a, b in zip(ub, ub[1:]):
        assert b <= a + PWL_TOL + 1e-6


# --------------------------------------------------------------------------
# certification contract: stabilization can never certify
# --------------------------------------------------------------------------
def test_stab_theta_never_enters_lb(tiny, enum_truth, tmp_path, monkeypatch):
    """Absurdly optimistic stabilized diagnostics must not move LB_best:
    if Theta_cert were folded into the certificate, LB would jump to ~1e12
    and 'certify' instantly with a negative gap."""
    inst, market = tiny
    ch, _ = enum_truth
    monkeypatch.setattr(b2a345_mod, "theta_cert", lambda *_a, **_k: 1e12)
    state = certified_cg(inst, market, epsilon=1e-2, budget=120,
                         out_dir=str(tmp_path), tag="a3", method="a3")
    oc = state["outcome"]
    assert oc["certified"] and oc["gap"] >= 0
    assert state["lb_best"] <= ch["z_ch"] + SLACK  # LB stayed clean-derived
    # stabilized calls did happen and carried the bogus diagnostic
    stab_events = [e for e in state["iteration_events"]
                   if e.get("phase") == "stabilized"]
    assert stab_events and all(e["theta_cert"] == 1e12 for e in stab_events)


def test_optimistic_incumbent_weak_bound_never_certifies(tiny, tmp_path,
                                                         monkeypatch):
    """Optimistic incumbent (rc_ub >= 0 would say 'exhausted') with a very
    weak certified bound: the corrected accounting keeps LB low and ends in
    uncertified budget exhaustion; the old incumbent formula would have
    certified within pwl_tol."""
    inst, market = tiny
    real_solve = b2a2_mod.solve_taker
    first = {}

    def fake_solve(_inst, prices, **kw):
        if "sol" not in first:
            first["sol"] = real_solve(_inst, prices, **kw)
            return first["sol"]
        sol = copy.deepcopy(first["sol"])
        sol.obj_model = 1e12
        sol.stats.bound = -1e12
        return sol

    monkeypatch.setattr(b2a2_mod, "solve_taker", fake_solve)
    state = certified_cg(inst, market, epsilon=1e-2, budget=8,
                         out_dir=str(tmp_path), tag="a3", method="a3")
    oc = state["outcome"]
    assert oc["type"] == "budget_exhausted"
    assert oc["certified"] is False
    assert state["lb_best"] < -1e6
    for it in state["iteration_events"]:
        if it.get("phase") != "clean":
            continue
        # old formula would have false-certified
        assert min(0.0, it["min_reduced_cost_ub"]) == 0.0
        assert it["ub_ch"] - it["z_rmp_model"] <= 1e-2
        assert it["certificate_gap"] > 1e-2


def test_stab_master_never_supplies_ub(stab_runs):
    """Every UB in the history is the clean RMP's exact evaluation: the
    stabilized master solves are marked and never appear in clean events."""
    for m in ("a3", "a5"):
        _, out = stab_runs[m]
        for it in _read_jsonl(os.path.join(out, f"{m}.iterations.jsonl")):
            for ms in it["master_solves"]:
                if it.get("phase") == "stabilized":
                    assert ms.get("stabilized") is True
                else:
                    assert not ms.get("stabilized")


# --------------------------------------------------------------------------
# serious/null-step and parameter updates match the documented equations
# --------------------------------------------------------------------------
def test_serious_step_rule():
    assert serious_step(None, -5.0) is True
    assert serious_step(1.0, 1.0 + 1e-8) is True
    assert serious_step(1.0, 1.0 + 1e-10) is False
    assert serious_step(1.0, 0.5) is False


def test_a3_update_equations(tiny):
    _, market = tiny
    stab = initial_stab_state("a3", market)
    d1_0 = list(stab["d1"])
    center0 = list(stab["center"])
    pi_new = [c + 1.0 for c in center0]
    a3_update(stab, False, pi_new)  # null: nothing moves
    assert stab["center"] == center0 and stab["d1"] == d1_0
    a3_update(stab, True, pi_new)  # serious: center moves, box halves
    assert stab["center"] == pi_new
    assert stab["d1"] == [max(dm, d / 2) for d, dm in zip(d1_0, stab["d1_min"])]
    for _ in range(60):  # floor respected
        a3_update(stab, True, pi_new)
    assert all(d == dm for d, dm in zip(stab["d1"], stab["d1_min"]))
    assert stab["serious_steps"] == 61 and stab["null_steps"] == 1


def test_a4_alpha_update_equations():
    # signal > 0: dual function rises toward out -> less smoothing
    assert a4_alpha_update(0.5, 1.0) == pytest.approx(0.5 - A4_ALPHA_DECR)
    assert a4_alpha_update(0.05, 1.0) == 0.0  # floor
    # signal <= 0: overshoot -> alpha += (1-alpha)*A4_ALPHA_INCR_FRAC
    assert a4_alpha_update(0.5, -1.0) == pytest.approx(
        0.5 + 0.5 * A4_ALPHA_INCR_FRAC)
    assert a4_alpha_update(0.0, 0.0) == pytest.approx(A4_ALPHA_INCR_FRAC)
    a = 0.98
    for _ in range(200):
        a = a4_alpha_update(a, -1.0)
    assert a <= A4_ALPHA_MAX + 1e-12  # cap


def test_a4_direction_signal_finite_difference(tiny):
    """Directional finite-difference regression (review finding 1): the
    signal computed in consistent posted-price coordinates must agree in
    sign with the true directional derivative of Theta_cert toward the out
    point, and 'dual function rises toward out' must DECREASE alpha. This
    pins the coordinates end-to-end — it would fail with the g_p vs
    (pi_out - pi_cand) mix-up, not merely invert a unit expectation."""
    from egglab.regimes import solve_taker
    inst, market = tiny

    def theta_at(p):
        return theta_cert(market, p, solve_taker(inst, p).stats.bound)

    p_hat = market.price(np.zeros(market.n_slots))
    decisive = 0
    for factor in (2.0, 0.5):
        p_out = factor * p_hat
        p_cand = 0.5 * p_hat + 0.5 * p_out  # alpha = 0.5 smoothing
        d_p = p_out - p_cand
        sol = solve_taker(inst, p_cand)
        signal = a4_direction_signal(market, p_cand, p_out, sol.load)
        s = 1e-3
        fd = (theta_at(p_cand + s * d_p) - theta_at(p_cand - s * d_p)) / (2 * s)
        if abs(fd) < 1e-6:
            continue
        decisive += 1
        assert (signal > 0) == (fd > 0), (signal, fd, factor)
        alpha_new = a4_alpha_update(0.5, signal)
        if fd > 0:  # dual function rises toward out -> less smoothing
            assert alpha_new < 0.5
        else:
            assert alpha_new > 0.5
    assert decisive >= 1  # at least one decisive direction was tested


def test_a4_events_consistent_with_signal(stab_runs):
    """Committed A4 events: alpha updates must match the recorded signal
    per the documented map."""
    _, out = stab_runs["a4"]
    checked = 0
    for it in _read_jsonl(os.path.join(out, "a4.iterations.jsonl")):
        if it.get("phase") != "stabilized":
            continue
        a0, a1 = it["params_before"]["alpha"], it["params_after"]["alpha"]
        if it["a4_signal"] > 0:
            assert a1 == pytest.approx(max(0.0, a0 - A4_ALPHA_DECR))
        else:
            assert a1 == pytest.approx(
                min(A4_ALPHA_MAX, a0 + (1 - a0) * A4_ALPHA_INCR_FRAC))
        checked += 1
    assert checked >= 1


def test_a5_update_equations(tiny):
    _, market = tiny
    stab = initial_stab_state("a5", market)
    center0 = list(stab["center"])
    pi_new = [c - 2.0 for c in center0]
    t0 = stab["t"]
    a5_update(stab, True, pi_new)  # serious: center moves, t unchanged
    assert stab["center"] == pi_new and stab["t"] == t0
    a5_update(stab, False, pi_new)  # null: t halved
    assert stab["t"] == t0 / 2
    for _ in range(60):
        a5_update(stab, False, pi_new)
    assert stab["t"] == A5_T_MIN  # floor


def test_updates_recorded_in_iteration_events(stab_runs):
    """The committed params_before/after must obey the documented updates."""
    state, out = stab_runs["a5"]
    for it in _read_jsonl(os.path.join(out, "a5.iterations.jsonl")):
        if it.get("phase") != "stabilized":
            continue
        t_before = it["params_before"]["t"]
        t_after = it["params_after"]["t"]
        if it["serious_step"]:
            assert t_after == t_before
        else:
            assert t_after == pytest.approx(max(A5_T_MIN, t_before / 2))
    state3, out3 = stab_runs["a3"]
    for it in _read_jsonl(os.path.join(out3, "a3.iterations.jsonl")):
        if it.get("phase") != "stabilized":
            continue
        d_before = it["params_before"]["d1"]
        d_after = it["params_after"]["d1"]
        if it["serious_step"]:
            assert all(a <= b / 2 + 1e-12 or a == pytest.approx(b / 2)
                       or a < b for a, b in zip(d_after, d_before))
        else:
            assert d_after == d_before


def test_a5_chord_model_analytic():
    """Review finding 2: the hinge decomposition must be the EXACT chord
    interpolation of q(x) = x^2/(2t) — equality at every grid breakpoint,
    midpoint overestimation exactly h^2/(8t), symmetry, and tangent
    continuation slope W/t beyond W (via the final half-increment)."""
    t, w = 0.7, 3.2
    h = w / A5_K
    q = lambda x: x * x / (2 * t)
    # equality with the quadratic at every grid breakpoint
    for m in range(A5_K + 1):
        assert a5_penalty_value(m * h, t, w) == pytest.approx(q(m * h),
                                                              abs=1e-12)
        assert a5_penalty_value(-m * h, t, w) == pytest.approx(q(m * h),
                                                               abs=1e-12)
    # midpoint overestimation exactly h^2/(8t), on every piece
    for m in range(A5_K):
        x = (m + 0.5) * h
        assert a5_penalty_value(x, t, w) - q(x) == pytest.approx(
            h * h / (8 * t), abs=1e-12)
    # symmetry
    for x in (0.3, 1.234, 2.9, 5.0):
        assert a5_penalty_value(x, t, w) == pytest.approx(
            a5_penalty_value(-x, t, w), abs=1e-12)
    # continuation slope beyond W is exactly W/t (tangent continuation,
    # requires the final half-increment at the W breakpoint)
    d = 0.25
    slope = (a5_penalty_value(w + 2 * d, t, w)
             - a5_penalty_value(w + d, t, w)) / d
    assert slope == pytest.approx(w / t, abs=1e-12)
    # first chord slope is h/(2t), NOT h/t (the reviewed bug)
    assert a5_penalty_value(h, t, w) / h == pytest.approx(h / (2 * t),
                                                          abs=1e-12)
    # hinge structure: first and last carry the half-increment
    hs = a5_hinges(t, w)
    assert hs[0] == (0.0, h / (2 * t))
    assert hs[-1] == (w, h / (2 * t))
    assert all(s == pytest.approx(h / t) for _, s in hs[1:-1])


def test_a5_lp_dual_penalty_matches_helper():
    """The stabilized LP's induced dual penalty must equal a5_penalty_value.
    LP duality: with hinge pairs built by _add_penalty_pair from a5_hinges,
    min { sum(costs*y) : net deviation = delta } = pi_hat*delta + psi*(delta)
    where psi* is the convex conjugate of the helper's psi. We verify the
    LP value against a numerically computed conjugate of the helper."""
    import mip as mip_mod
    from egglab.b2a345 import _add_penalty_pair
    from egglab.solver import new_model, optimize

    t, w, pi_hat = 0.7, 3.2, -1.3
    xs = np.linspace(-2 * w, 2 * w, 8001)
    psi = np.array([a5_penalty_value(float(x), t, w) for x in xs])
    for delta in (0.1, -0.6, 1.9, 3.9):  # |delta| < continuation slope W/t
        m = new_model("conj")
        link_terms = [[]]
        obj_terms = []
        for u, s in a5_hinges(t, w):
            obj_terms.append(_add_penalty_pair(
                m, link_terms, 0, pi_hat + u, pi_hat - u, s))
        m.add_constr(mip_mod.xsum(link_terms[0]) == delta)
        m.objective = mip_mod.xsum(obj_terms)
        st = optimize(m, solve_lp_first=False)
        assert st.status == "OPTIMAL"
        conj = float(np.max(delta * xs - psi))  # psi*(delta), numeric
        assert st.obj == pytest.approx(pi_hat * delta + conj, abs=1e-6)


def test_theta_cert_is_weak_duality_valid(tiny, enum_truth):
    """Theta_cert at arbitrary price vectors never exceeds enumerated z_CH."""
    inst, market = tiny
    ch, _ = enum_truth
    from egglab.regimes import solve_taker
    rng = np.random.default_rng(0)
    for _ in range(3):
        p = np.abs(rng.normal(1.0, 0.5, market.n_slots))
        sol = solve_taker(inst, p)
        th = theta_cert(market, p, sol.stats.bound)
        assert th <= ch["z_ch"] + 1e-6, (th, ch["z_ch"])


# --------------------------------------------------------------------------
# identity: changed method or stabilization settings reject resume
# --------------------------------------------------------------------------
def test_identity_rejects_changed_method(stab_runs, tiny, dictator):
    inst, market = tiny
    _, out = stab_runs["a3"]
    with pytest.raises(B2A2Error, match="identity mismatch"):
        certified_cg(inst, market, epsilon=1e-2, budget=120, out_dir=out,
                     tag="a3", method="a4",
                     z_d_ub=dictator.obj_true, tol_d=TOL_D)


def test_identity_rejects_changed_stab_settings(stab_runs, tiny, dictator,
                                                monkeypatch):
    inst, market = tiny
    _, out = stab_runs["a3"]
    monkeypatch.setattr(b2a345_mod, "A3_ZETA1", A3_ZETA1 * 2)
    with pytest.raises(B2A2Error, match="identity mismatch.*stab"):
        certified_cg(inst, market, epsilon=1e-2, budget=120, out_dir=out,
                     tag="a3", method="a3",
                     z_d_ub=dictator.obj_true, tol_d=TOL_D)


@pytest.mark.parametrize("method,constant", [
    ("a3", "A3_SERIOUS_SHRINK"),
    ("a4", "A4_ALPHA_DECR"),
    ("a4", "A4_ALPHA_INCR_FRAC"),
    ("a5", "A5_NULL_SHRINK"),
])
def test_identity_rejects_changed_update_constants(stab_runs, tiny, dictator,
                                                   monkeypatch, method,
                                                   constant):
    """Every numerical update constant is part of the resume identity
    (review finding 4): changing any of them rejects the checkpoint."""
    inst, market = tiny
    _, out = stab_runs[method]
    monkeypatch.setattr(b2a345_mod, constant,
                        getattr(b2a345_mod, constant) * 0.5 + 0.01)
    with pytest.raises(B2A2Error, match="identity mismatch.*stab"):
        certified_cg(inst, market, epsilon=1e-2, budget=120, out_dir=out,
                     tag=method, method=method,
                     z_d_ub=dictator.obj_true, tol_d=TOL_D)


def test_identity_accepts_exact_match(stab_runs, tiny, dictator):
    inst, market = tiny
    state0, out = stab_runs["a4"]
    state = certified_cg(inst, market, epsilon=1e-2, budget=120, out_dir=out,
                         tag="a4", method="a4",
                         z_d_ub=dictator.obj_true, tol_d=TOL_D)
    assert state["done"] and state["outcome"] == state0["outcome"]


# --------------------------------------------------------------------------
# preemption at solve/checkpoint/materialization boundaries (method a3)
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def ref_a3(tiny, tmp_path_factory):
    inst, market = tiny
    out = str(tmp_path_factory.mktemp("ref3"))
    state = certified_cg(inst, market, epsilon=1e-2, budget=120,
                         out_dir=out, tag="p3", method="a3")
    return state, out


def _resume_and_compare(tiny, out, ref):
    inst, market = tiny
    state = certified_cg(inst, market, epsilon=1e-2, budget=120,
                         out_dir=out, tag="p3", method="a3")
    ref_state, ref_out = ref
    oracle = _read_jsonl(os.path.join(out, "p3.oracle.jsonl"))
    ref_oracle = _read_jsonl(os.path.join(ref_out, "p3.oracle.jsonl"))
    ids = [r["extra"]["call_id"] for r in oracle]
    assert len(ids) == len(set(ids))  # no duplicate oracle calls
    assert ids == [r["extra"]["call_id"] for r in ref_oracle]  # none missing
    assert _strip_volatile(oracle) == _strip_volatile(ref_oracle)
    iters = _read_jsonl(os.path.join(out, "p3.iterations.jsonl"))
    ref_iters = _read_jsonl(os.path.join(ref_out, "p3.iterations.jsonl"))
    assert _strip_volatile(iters) == _strip_volatile(ref_iters)
    assert state["outcome"]["ub_ch"] == pytest.approx(
        ref_state["outcome"]["ub_ch"], abs=1e-9)


def test_interrupt_during_candidate_solve(tiny, ref_a3, tmp_path, monkeypatch):
    inst, market = tiny
    out = str(tmp_path)
    real_solve = b2a2_mod.solve_taker
    calls = {"n": 0}

    def preempting(_inst, prices, **kw):
        calls["n"] += 1
        if calls["n"] == 3:  # the first CANDIDATE call (seed, clean, cand)
            raise KeyboardInterrupt("killed during candidate solve")
        return real_solve(_inst, prices, **kw)

    monkeypatch.setattr(b2a2_mod, "solve_taker", preempting)
    with pytest.raises(KeyboardInterrupt):
        certified_cg(inst, market, epsilon=1e-2, budget=120,
                     out_dir=out, tag="p3", method="a3")
    ck = checkpoint.load(os.path.join(out, "p3.cg.ckpt.json"))
    assert ck["phase"] == "stab" and ck["oracle_calls"] == 2
    monkeypatch.setattr(b2a2_mod, "solve_taker", real_solve)
    _resume_and_compare(tiny, out, ref_a3)


def test_interrupt_after_checkpoint_before_materialization_a3(
        tiny, ref_a3, tmp_path, monkeypatch):
    inst, market = tiny
    out = str(tmp_path)
    real_mat = b2a2_mod._materialize_logs
    n = {"v": 0}

    def dying(state, oc_path, it_path):
        n["v"] += 1
        if n["v"] == 4:  # commit following the first candidate call
            raise KeyboardInterrupt("killed before materialization")
        return real_mat(state, oc_path, it_path)

    monkeypatch.setattr(b2a2_mod, "_materialize_logs", dying)
    with pytest.raises(KeyboardInterrupt):
        certified_cg(inst, market, epsilon=1e-2, budget=120,
                     out_dir=out, tag="p3", method="a3")
    monkeypatch.setattr(b2a2_mod, "_materialize_logs", real_mat)
    _resume_and_compare(tiny, out, ref_a3)


def test_interrupt_during_materialization_a3(tiny, ref_a3, tmp_path,
                                             monkeypatch):
    inst, market = tiny
    out = str(tmp_path)
    real_write = b2a2_mod._atomic_write_lines
    n = {"v": 0}

    def dying(path, records):
        n["v"] += 1
        if n["v"] == 8:  # mid-materialization after a candidate commit
            raise KeyboardInterrupt("killed mid-materialization")
        return real_write(path, records)

    monkeypatch.setattr(b2a2_mod, "_atomic_write_lines", dying)
    with pytest.raises(KeyboardInterrupt):
        certified_cg(inst, market, epsilon=1e-2, budget=120,
                     out_dir=out, tag="p3", method="a3")
    monkeypatch.setattr(b2a2_mod, "_atomic_write_lines", real_write)
    _resume_and_compare(tiny, out, ref_a3)


def test_deterministic_rerun(tiny, ref_a3, tmp_path):
    inst, market = tiny
    out = str(tmp_path)
    certified_cg(inst, market, epsilon=1e-2, budget=120,
                 out_dir=out, tag="p3", method="a3")
    _resume_and_compare(tiny, out, ref_a3)


# --------------------------------------------------------------------------
# pilot spec and audit
# --------------------------------------------------------------------------
def test_pilot_list_is_exactly_36():
    cells = build_cells()
    assert len(cells) == 36
    assert cells == [(m, s, n, b)
                     for m in ("a3", "a4", "a5")
                     for s in (0, 11, 15)
                     for n in (8, 12)
                     for b in (0.01, 0.05)]
    assert EPSILON == 1e-2 and BUDGET == 240


def test_audit_per_method_gates(stab_runs, tmp_path):
    root = str(tmp_path / "root")
    for m in METHODS:
        _, out = stab_runs[m]
        d = os.path.join(root, f"cell_{m}")
        os.makedirs(d, exist_ok=True)
        for fn in (f"{m}.cg.ckpt.json", f"{m}.iterations.jsonl",
                   f"{m}.oracle.jsonl"):
            with open(os.path.join(out, fn)) as src, \
                    open(os.path.join(d, fn), "w") as dst:
                dst.write(src.read())
    lines, ok, problems = audit(
        root, expect_cg=3, expect_cg_method={"a3": 1, "a4": 1, "a5": 1})
    assert ok, problems
    text = "\n".join(lines)
    for m in METHODS:
        assert f"- {m}: cells 1, complete and sane 1, certified 1" in text
    # a missing method cell fails its per-method gate
    _, ok2, problems2 = audit(
        root, expect_cg=3, expect_cg_method={"a3": 2, "a4": 1, "a5": 1})
    assert not ok2 and any("cg method a3: 1/2" in p for p in problems2)


def test_audit_accepts_a4_smoothing_without_master(stab_runs, tmp_path):
    _, out = stab_runs["a4"]
    root = str(tmp_path / "root")
    d = os.path.join(root, "cell_a4")
    os.makedirs(d, exist_ok=True)
    for fn in ("a4.cg.ckpt.json", "a4.iterations.jsonl", "a4.oracle.jsonl"):
        with open(os.path.join(out, fn)) as src, \
                open(os.path.join(d, fn), "w") as dst:
            dst.write(src.read())
    _, ok, problems = audit(root, expect_cg=1)
    assert ok, problems


def test_same_solve_ids_across_cells_valid_duplicate_within_fails(
        stab_runs, tmp_path):
    _, out = stab_runs["a3"]
    root = str(tmp_path / "root")
    for cell in ("cell_x", "cell_y"):
        d = os.path.join(root, cell)
        os.makedirs(d, exist_ok=True)
        for fn in ("a3.cg.ckpt.json", "a3.iterations.jsonl", "a3.oracle.jsonl"):
            with open(os.path.join(out, fn)) as src, \
                    open(os.path.join(d, fn), "w") as dst:
                dst.write(src.read())
    _, ok, problems = audit(root, expect_cg=2)
    assert ok, problems
    # duplicate inside one cell still fails
    it_path = os.path.join(root, "cell_x", "a3.iterations.jsonl")
    recs = _read_jsonl(it_path)
    clean = [r for r in recs if r.get("phase") == "clean"][0]
    clean["master_solves"] += [dict(clean["master_solves"][0])]
    with open(it_path, "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    _, ok2, problems2 = audit(root, expect_cg=2)
    assert not ok2 and any("duplicate master solve_id" in p for p in problems2)


def test_budget_exhausted_stabilized_is_sane_not_certified(tiny, tmp_path):
    inst, market = tiny
    out = str(tmp_path / "cell")
    state = certified_cg(inst, market, epsilon=1e-2, budget=4,
                         out_dir=out, tag="a5", method="a5")
    oc = state["outcome"]
    assert oc["type"] == "budget_exhausted" and oc["certified"] is False
    assert oc["oracle_calls_clean"] + oc["oracle_calls_stab"] == 4
    lines, ok, problems = audit(out, expect_cg=1)
    assert ok, problems
    text = "\n".join(lines)
    assert "complete and sane: 1" in text
    assert "CERTIFIED (gap <= epsilon): 0" in text


def test_certification_gate_rejects_sane_budget_exhausted_pilot(tiny,
                                                                tmp_path):
    """Review finding 3: 36 sane budget-exhausted cells must PASS the
    generic completeness audit (cg=36, 12 per method) yet FAIL the pilot's
    per-method certification gate (cgcert 12 per method)."""
    inst, market = tiny
    src = str(tmp_path / "src")
    certified_cg(inst, market, epsilon=1e-2, budget=4,
                 out_dir=src, tag="a5", method="a5")
    ck = checkpoint.load(os.path.join(src, "a5.cg.ckpt.json"))
    root = str(tmp_path / "root")
    for m in METHODS:
        for i in range(12):
            d = os.path.join(root, f"{m}_cell{i}")
            os.makedirs(d, exist_ok=True)
            fab = json.loads(json.dumps(ck))
            fab["identity"]["method"] = m
            checkpoint.save(os.path.join(d, "a5.cg.ckpt.json"), fab)
            for fn in ("a5.iterations.jsonl", "a5.oracle.jsonl"):
                with open(os.path.join(src, fn)) as sf, \
                        open(os.path.join(d, fn), "w") as df:
                    df.write(sf.read())
    gates = {"a3": 12, "a4": 12, "a5": 12}
    _, ok, problems = audit(root, expect_cg=36, expect_cg_method=gates)
    assert ok, problems  # generic audit: complete and sane
    _, ok2, problems2 = audit(root, expect_cg=36, expect_cg_method=gates,
                              expect_cg_certified_method=gates)
    assert not ok2
    cert_fails = [p for p in problems2 if "certification gate" in p]
    assert len(cert_fails) == 3
    assert any("cg method a3: 0/12 CERTIFIED" in p for p in cert_fails)
