"""B3 factor-screen battery: normative witness semantics (policy P1),
N-bounds with the recomputed necessity assertion, R1/R2 conservatism,
outcome-blind enumeration, baseline-first gating, deterministic
publication, refusal paths, and the solver-free import closure."""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import experiments.b3_factor_screen as mod
from egglab.instance import Instance, Trip


# --------------------------------------------------------------------------
# crafted instances for witness golden tests
# --------------------------------------------------------------------------
def _craft(trips, battery=60.0, power=150.0, max_vehicles=2,
           soc_min_frac=0.10, soc_end_frac=0.10):
    dh_min, dh_kwh = {}, {}
    for a, b, m, k in (("D", "A", 10, 2.0), ("D", "B", 12, 2.4),
                       ("A", "B", 8, 1.6)):
        dh_min[(a, b)] = m
        dh_kwh[(a, b)] = k
        dh_min[(b, a)] = m
        dh_kwh[(b, a)] = k
    return Instance(
        name="crafted", trips=trips, depot="D", dh_min=dh_min,
        dh_kwh=dh_kwh, battery_kwh=battery, soc0_kwh=battery,
        soc_min_kwh=soc_min_frac * battery,
        soc_end_kwh=soc_end_frac * battery, charge_power_kw=power,
        max_vehicles=max_vehicles)


def test_witness_terminal_soc_is_checked_at_pull_in_without_charging():
    """Policy P1: no charging after the final trip; a duty whose pull-in
    SOC lands below soc_end_kwh is infeasible even though post-day
    charging could trivially fix it."""
    # one heavy trip: 60 - (2.0 + 49 + 1.6) = 7.4 < soc_end = 12
    trips = [Trip("t000", 400, 460, "A", "B", 49.0)]
    inst = _craft(trips, battery=60.0, soc_end_frac=0.20)
    w = mod.witness(inst)
    assert w["feasible"] is False and w["reason"] == "terminal-soc"
    # the same duty passes when the terminal requirement is lower
    inst2 = _craft(trips, battery=60.0, soc_end_frac=0.10)
    w2 = mod.witness(inst2)
    assert w2["feasible"] is True
    # and no terminal charging event was created in either case
    assert all(d <= 1680 for _a, d, _k in w2["events"])


def test_witness_assignment_failure_and_round_trip_band():
    # two overlapping trips, one vehicle allowed -> assignment failure
    trips = [Trip("t000", 400, 460, "A", "B", 20.0),
             Trip("t001", 410, 470, "A", "B", 20.0)]
    w = mod.witness(_craft(trips, max_vehicles=1))
    assert w["feasible"] is False and w["reason"] == "assignment"
    # a trip whose depot round trip exceeds the usable band
    trips = [Trip("t000", 400, 460, "A", "B", 58.0)]
    w = mod.witness(_craft(trips, battery=60.0))
    assert w["feasible"] is False and w["reason"] == "round-trip-band"


def test_witness_charging_events_are_inter_trip_depot_arcs_only():
    """A vehicle serving two trips with a long depot dwell charges on the
    inter-trip arc; the event window lies inside [return, next depart]."""
    trips = [Trip("t000", 400, 450, "A", "A", 30.0),
             Trip("t001", 800, 850, "A", "A", 30.0)]
    inst = _craft(trips, battery=60.0, max_vehicles=1)
    w = mod.witness(inst)
    assert w["feasible"] is True
    assert len(w["events"]) == 1
    a, d, kwh = w["events"][0]
    assert a == 450 + 10 and d == 800 - 10  # return arrival, next depart
    assert kwh == pytest.approx(2.0 + 30.0 + 2.0)  # charge-to-full
    rel = mod.relevance(inst, w["events"])
    assert rel["r1"] and rel["r2"] and rel["ok"]


def test_relevance_r1_fails_without_charging():
    """When no vehicle has an inter-trip depot dwell (overlapping trips,
    one per vehicle) there is no depot-arc charging event at all: R1
    fails (the witness day is price-insensitive)."""
    trips = [Trip("t000", 400, 450, "A", "A", 10.0),
             Trip("t001", 410, 460, "A", "A", 10.0)]
    inst = _craft(trips, battery=60.0, max_vehicles=2)
    w = mod.witness(inst)
    assert w["feasible"] is True and w["events"] == []
    rel = mod.relevance(inst, w["events"])
    assert not rel["r1"] and not rel["ok"]


def test_relevance_r2_whole_slot_conservative_semantics():
    """R2 counts whole-slot contiguous placements only: a dwell spanning
    exactly n_c + 1 whole slots is timing-free; one fewer is not."""
    inst = _craft([Trip("t000", 400, 450, "A", "A", 20.0)])
    # per_slot = 150 kWh; one needed slot => k >= 2 required
    assert mod.relevance(inst, [(60, 240, 30.0)])["r2"] is True   # k = 3
    assert mod.relevance(inst, [(60, 180, 30.0)])["r2"] is True   # k = 2
    assert mod.relevance(inst, [(60, 120, 30.0)])["r2"] is False  # k = 1
    # partial-slot flexibility the model has is deliberately NOT counted
    assert mod.relevance(inst, [(90, 178, 30.0)])["r2"] is False


def test_necessity_assertion_recomputes_generator_maximum():
    inst = mod.build_instance(0, 8, 60.0, 150.0)
    necessity = mod.necessity_assertion(inst)
    assert necessity["max_saving_kwh"] == pytest.approx(4.8)  # e = s = B
    assert necessity["min_energy_kwh"] >= 14.0
    assert necessity["ok"]


def test_n_bounds_golden():
    inst = _craft([Trip("t000", 400, 460, "A", "B", 50.0)], battery=60.0)
    bounds = mod.n_bounds(inst)  # band 54: n1 ok, n2 fails (2+50+1.6)
    assert bounds["n1"] and not bounds["n2"] and not bounds["ok"]


# --------------------------------------------------------------------------
# enumeration and ordering
# --------------------------------------------------------------------------
def test_candidate_grids_exact():
    for (name, _p, lo, hi, step, start, expected) in mod.LEVELS:
        grid = mod.candidate_grid(lo, hi, step)
        assert len(grid) == expected, name
        assert grid[0] == lo and grid[-1] == hi
        assert start in grid


def test_preference_order_outcome_blind():
    order = mod.preference_order([44.0, 45.0, 46.0, 40.0], 45.0, 60.0)
    # start first; equidistant pair broken toward farther-from-baseline
    assert order == [45.0, 44.0, 46.0, 40.0]


def test_screen_is_deterministic_and_freezes_at_starting_candidates():
    record = mod.run_screen()
    assert record["disposition"]["state"] == "FROZEN"
    assert record["selected_levels"] == {
        "S1_batt_low": 45.0, "S2_batt_high": 90.0,
        "S3_pow_low": 75.0, "S4_pow_high": 300.0}
    assert len(record["baseline_gate"]) == 6
    assert all(c["ok"] for c in record["baseline_gate"])
    assert len(record["setting_instances"]) == 30
    # every level selected on its FIRST (starting) candidate
    for name, level in record["levels"].items():
        assert level["transitions"][0]["state"] == "SELECTED", name
    # 30 unique instance hashes; settings x 6 pairs
    hashes = [c["instance_hash"] for c in record["setting_instances"]]
    assert len(set(hashes)) == 30
    # byte determinism
    assert mod.canonical_bytes(record) == mod.canonical_bytes(
        mod.run_screen())


def test_baseline_gate_runs_first_and_blocks_levels(monkeypatch):
    real_eval = mod.evaluate_instance
    calls = []

    def failing_baseline(seed, n, battery, power):
        calls.append((battery, power))
        cell = real_eval(seed, n, battery, power)
        if (battery, power) == (60.0, 150.0):
            cell = dict(cell, ok=False, first_failed_gate="r2")
        return cell

    monkeypatch.setattr(mod, "evaluate_instance", failing_baseline)
    record = mod.run_screen()
    assert record["disposition"]["state"] == "DESIGN-NOT-FROZEN"
    assert record["disposition"]["reason"] == "baseline"
    # no level candidate was ever evaluated
    assert all((b, p) == (60.0, 150.0) for b, p in calls)
    assert record["levels"] == {} and record["selected_levels"] == {}


def test_non_exercisable_level_is_design_not_frozen(monkeypatch):
    real_eval = mod.evaluate_instance

    def fail_battery_low(seed, n, battery, power):
        cell = real_eval(seed, n, battery, power)
        if battery < 60.0:  # every S1 candidate fails
            cell = dict(cell, ok=False, first_failed_gate="witness")
        return cell

    monkeypatch.setattr(mod, "evaluate_instance", fail_battery_low)
    record = mod.run_screen()
    assert record["disposition"]["state"] == "DESIGN-NOT-FROZEN"
    assert record["disposition"]["reason"] == "non-exercisable"
    assert record["disposition"]["level"] == "S1_batt_low"
    transitions = record["levels"]["S1_batt_low"]["transitions"]
    assert len(transitions) == 16  # the full grid was enumerated
    assert all(t["state"] == "REJECT" for t in transitions)


def test_grid_size_tamper_refused(monkeypatch):
    tampered = tuple(
        (name, p, lo, hi, step, start, expected + 1)
        for (name, p, lo, hi, step, start, expected) in mod.LEVELS)
    monkeypatch.setattr(mod, "LEVELS", tampered)
    with pytest.raises(mod.B3ScreenError, match="candidate grid"):
        mod.run_screen()


def test_burned_seed_guards():
    mod.assert_burned_seeds()
    with pytest.raises(mod.B3ScreenError, match="frozen to"):
        mod.assert_burned_seeds((0, 11))
    with pytest.raises(mod.B3ScreenError, match="frozen to"):
        mod.assert_burned_seeds((0, 11, 16))
    with pytest.raises(mod.B3ScreenError, match="not a burned"):
        mod.build_instance(16, 8, 60.0, 150.0)
    with pytest.raises(mod.B3ScreenError, match="not a burned"):
        mod.build_instance(32, 8, 60.0, 150.0)


# --------------------------------------------------------------------------
# publication and refusals
# --------------------------------------------------------------------------
def _publish(out, stamp="B3SCREEN"):
    return mod.publish(out, stamp, "deadbeef" * 5, verify_code_commit=False)


def test_publish_end_to_end_and_byte_identical(tmp_path):
    first = Path(_publish(tmp_path / "a"))
    second = Path(_publish(tmp_path / "b"))
    for name in ("SCREEN_RECORD.json", "MANIFEST.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    manifest = json.loads((first / "MANIFEST.json").read_text())
    assert manifest["disposition"]["state"] == "FROZEN"
    assert manifest["counts"]["setting_instances"] == 30
    assert manifest["counts"]["baseline_instances"] == 6
    assert manifest["counts"]["candidate_grid_sizes"] == {
        "S1_batt_low": 16, "S2_batt_high": 46,
        "S3_pow_low": 15, "S4_pow_high": 41}
    record = json.loads((first / "SCREEN_RECORD.json").read_text())
    payload = mod.canonical_bytes(record)
    import hashlib
    assert manifest["outputs"]["SCREEN_RECORD.json"] == (
        hashlib.sha256(payload).hexdigest())
    assert record["spec"]["sha256"] == mod.sha256_file(
        mod.REPO_ROOT / mod.SPEC_RELPATH)


def test_existing_output_refused(tmp_path):
    _publish(tmp_path / "out")
    with pytest.raises(mod.B3ScreenError, match="refusing existing"):
        _publish(tmp_path / "out")
    assert not list((tmp_path / "out").glob(".B3SCREEN.*staging*"))


def test_a6_and_overlap_refusals(tmp_path):
    with pytest.raises(mod.B3ScreenError, match="refusing A6 path"):
        _publish(tmp_path / "a6_pilot")
    for overlap in (mod.REPO_ROOT / "src",
                    mod.REPO_ROOT / "doc" / "nested",
                    mod.REPO_ROOT.parent):
        with pytest.raises(mod.B3ScreenError, match="overlaps"):
            _publish(overlap)
    assert not (mod.REPO_ROOT / "doc" / "nested").exists()


def test_nondeterministic_regeneration_refused(tmp_path, monkeypatch):
    real_run = mod.run_screen
    state = {"n": 0}

    def flaky():
        state["n"] += 1
        record = real_run()
        record["_noise"] = state["n"]
        return record

    monkeypatch.setattr(mod, "run_screen", flaky)
    with pytest.raises(mod.B3ScreenError, match="deterministically"):
        _publish(tmp_path / "out")
    assert not (tmp_path / "out" / "B3SCREEN").exists()


def test_screen_provenance_verification(monkeypatch):
    with pytest.raises(mod.B3ScreenError, match="full 40-character"):
        mod.verify_screen_provenance("b81b15a")
    with pytest.raises(mod.B3ScreenError, match="does not resolve"):
        mod.verify_screen_provenance("f" * 40)
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=mod.REPO_ROOT).decode().strip()
    real_run = mod.subprocess.run
    real_co = mod.subprocess.check_output
    merge_base_calls = {"n": 0}

    def base_not_ancestor(args, cwd=None, **kwargs):
        if args[:2] == ["git", "merge-base"]:
            merge_base_calls["n"] += 1
            if merge_base_calls["n"] == 2:
                class R:
                    returncode = 1
                return R()
        return real_run(args, cwd=cwd, **kwargs)

    monkeypatch.setattr(mod.subprocess, "run", base_not_ancestor)
    with pytest.raises(mod.B3ScreenError, match="frozen base"):
        mod.verify_screen_provenance(head)
    monkeypatch.setattr(mod.subprocess, "run", real_run)

    def dirty_status(args, cwd=None, stderr=None):
        if args[1] == "status":
            return b" M src/experiments/b3_factor_screen.py\n"
        return real_co(args, cwd=cwd, stderr=stderr)

    monkeypatch.setattr(mod.subprocess, "check_output", dirty_status)
    with pytest.raises(mod.B3ScreenError, match="tracked modifications"):
        mod.verify_screen_provenance(head)
    monkeypatch.setattr(mod.subprocess, "check_output", real_co)

    def stale_show(args, cwd=None, stderr=None):
        if args[1] == "status":
            return b""
        if args[1] == "show":
            return b"different bytes"
        return real_co(args, cwd=cwd, stderr=stderr)

    monkeypatch.setattr(mod.subprocess, "check_output", stale_show)
    with pytest.raises(mod.B3ScreenError, match="differs from the claimed"):
        mod.verify_screen_provenance(head)


def test_import_closure_is_solver_free():
    """Importing AND running the full screen must not load any solver,
    optimizer, or numerical-stack module."""
    script = (
        "import sys, os\n"
        "sys.path.insert(0, os.getcwd())\n"
        "import experiments.b3_factor_screen as mod\n"
        "record = mod.run_screen()\n"
        "assert record['disposition']['state'] == 'FROZEN'\n"
        "banned_roots = ('mip', 'gurobipy', 'numpy', 'pandas',"
        " 'matplotlib')\n"
        "banned_modules = {'egglab.evsp', 'egglab.solver',"
        " 'egglab.regimes', 'egglab.b2a2', 'egglab.b2a345', 'egglab.a6',"
        " 'egglab.boundary', 'egglab.loops'}\n"
        "loaded = [m for m in sys.modules\n"
        "          if m.split('.')[0] in banned_roots"
        " or m in banned_modules]\n"
        "assert not loaded, loaded\n"
        "print('SOLVER_FREE')\n"
    )
    out = subprocess.check_output(
        [sys.executable, "-c", script],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert b"SOLVER_FREE" in out
