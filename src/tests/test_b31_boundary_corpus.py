"""B31 boundary-corpus builder battery.

Canonical-input checks are read-only (`--validate-only` integration gate,
digest/hash/classification replication); corpus outputs are exercised
through synthetic fixtures only — no real corpus is generated in this
PR.  Fixture injection through :func:`build`'s parameters is test-only;
the production CLI is pinned to the canonical input."""
import copy
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import experiments.build_b31_boundary_corpus as mod

CANONICAL = Path(mod.CANONICAL_INPUT)
SPEC = mod.REPO_ROOT / "doc" / "B31_BOUNDARY_CORPUS_SPEC.md"


# --------------------------------------------------------------------------
# synthetic fixture: 3 sweeps (seeds 0/5/6 -> all three splits), 4 points
# --------------------------------------------------------------------------
FIX_SEEDS = (0, 5, 6)
FIX_N_TRIPS = (8,)
FIX_SLOTS = (8,)
FIX_POINTS = 4
FIX_SLOT_COUNT = 6  # load-vector length


def _point(idx, sequences, load, fleet=2, load_slot=None):
    delta = mod.DELTA_START + mod.DELTA_STEP * idx
    return {
        "idx": idx, "delta": delta,
        "schedule_hash": mod.schedule_hash(sequences),
        "load_hash": mod.load_hash(load),
        "obj": 100.0 + idx, "fleet": fleet,
        "load_slot": load[0] if load_slot is None else load_slot,
        "load": list(load),
        "sequences": [list(seq) for seq in sequences],
        "energy_total": float(sum(load)),
    }


def _sweep_points(seed):
    base_load = [0.0] * FIX_SLOT_COUNT
    seq_a = [["t0", "t1"], ["t2", "t3"]]
    seq_b = [["t0", "t2"], ["t1", "t3"]]      # different partition
    p0 = _point(0, seq_a, base_load)
    p1 = _point(1, seq_a, base_load)          # stable vs p0
    big_load = [5.0] + [0.0] * (FIX_SLOT_COUNT - 1)
    p2 = _point(2, seq_b, big_load)           # duty change vs p1 (l1 = 5)
    if seed == 0:
        # schedule-preserving degenerate: load-hash flip, same partition
        small_load = [5.0, 0.5] + [0.0] * (FIX_SLOT_COUNT - 2)
        p3 = _point(3, seq_b, small_load)
    else:
        # schedule-changing degenerate: partition flip, tiny load move
        p3 = _point(3, seq_a, big_load)
    return [p0, p1, p2, p3]


def _fixture_expected():
    return {
        "sweeps": 3, "points": 12, "intervals": 9, "stable": 3,
        "degenerate_tie": 3, "charging_only": 0, "duty_change": 3,
        "fleet_change": 0, "margin_ties": 1,
        "economic_charging_only": 0, "economic_duty_change": 2,
        "economic_fleet_change": 0, "degenerate_schedule_preserving": 1,
    }


def _build_fixture(root: Path):
    (root / "checkpoints").mkdir(parents=True)
    for seed in FIX_SEEDS:
        points = _sweep_points(seed)
        switches = []
        n_economic = 0
        counts = {kind: 0 for kind in mod.SWITCH_KINDS}
        for a, b in zip(points, points[1:]):
            sw = mod.classify_pair(a, b)
            if sw is None:
                continue
            if sw["kind"] in ("duty_change", "fleet_change"):
                # seed 5 is an economic tie; the others clear the margin
                if seed == 5:
                    sw.update(margin_b_at_a=1e-6, margin_a_at_b=2e-4,
                              tie_margin=True)
                else:
                    sw.update(margin_b_at_a=0.4, margin_a_at_b=0.3,
                              tie_margin=False)
            counts[sw["kind"]] += 1
            if sw["kind"] in ("charging_only", "duty_change",
                              "fleet_change") and not sw.get(
                                  "tie_margin", False):
                n_economic += 1
            switches.append(sw)
        state = {
            "next_idx": len(points), "points": points, "done": True,
            "margins_done": True, "switches": switches,
            "n_switches": len(switches),
            "n_economic_switches": n_economic,
            "counts_by_kind": counts,
        }
        d = root / "checkpoints" / f"s{seed}_n8_slot8"
        d.mkdir()
        (d / "sweep.ckpt.json").write_text(
            json.dumps(state, sort_keys=True) + "\n")
    return root


@pytest.fixture
def fixture_root(tmp_path, monkeypatch):
    root = _build_fixture(tmp_path / "boundary_fixture")
    digest, n = mod.checkpoints_digest(root)
    monkeypatch.setattr(mod, "PINNED_CHECKPOINTS_SHA256", digest)
    monkeypatch.setattr(mod, "SEEDS", FIX_SEEDS)
    monkeypatch.setattr(mod, "N_TRIPS", FIX_N_TRIPS)
    monkeypatch.setattr(mod, "SLOTS", FIX_SLOTS)
    monkeypatch.setattr(mod, "N_POINTS", FIX_POINTS)
    return root


def _fix_build(root, out, stamp="B31TEST"):
    return mod.build(root, out, stamp, "deadbeef" * 5,
                     verify_code_commit=False,
                     expected_totals=_fixture_expected())


def _retamper(root, mutate, monkeypatch):
    """Mutate one fixture checkpoint and re-pin the digest so the
    semantic gate under test is what fires (test-only re-pinning)."""
    path = next((root / "checkpoints").glob("*/sweep.ckpt.json"))
    state = json.loads(path.read_text())
    mutate(state)
    path.write_text(json.dumps(state, sort_keys=True) + "\n")
    digest, _ = mod.checkpoints_digest(root)
    monkeypatch.setattr(mod, "PINNED_CHECKPOINTS_SHA256", digest)


# --------------------------------------------------------------------------
# canonical read-only gates
# --------------------------------------------------------------------------
def test_builder_import_closure_is_solver_free():
    script = (
        "import sys, os\n"
        "sys.path.insert(0, os.getcwd())\n"
        "import experiments.build_b31_boundary_corpus as mod\n"
        "banned = ('egglab', 'mip', 'gurobipy', 'pandas', 'numpy',"
        " 'matplotlib')\n"
        "loaded = [m for m in sys.modules"
        " if m.split('.')[0] in banned]\n"
        "assert not loaded, loaded\n"
        "print('SOLVER_FREE')\n"
    )
    out = subprocess.check_output(
        [sys.executable, "-c", script],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert b"SOLVER_FREE" in out


def test_canonical_validate_only_integration_gate(tmp_path):
    """Read-only CLI gate against the committed canonical input: every
    fail-closed gate runs, the exact totals print, and NOTHING is
    written."""
    before = {p.name: mod.sha256_file(p)
              for p in CANONICAL.rglob("*") if p.is_file()}
    out_base = tmp_path / "never-created"
    result = subprocess.run(
        [sys.executable, "experiments/build_b31_boundary_corpus.py",
         "--validate-only", "--out", str(out_base)],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    totals = json.loads(result.stdout)
    assert totals["sweeps"] == 64
    assert totals["points"] == 19264
    assert totals["intervals"] == 19200
    assert totals["stable"] == 16460
    assert totals["degenerate_tie"] == 2559
    assert totals["margin_ties"] == 89
    assert totals["economic_charging_only"] == 35
    assert totals["economic_duty_change"] == 57
    assert totals["economic_fleet_change"] == 0
    assert totals["degenerate_schedule_preserving"] == 1
    assert not out_base.exists()  # read-only: no file was created
    after = {p.name: mod.sha256_file(p)
             for p in CANONICAL.rglob("*") if p.is_file()}
    assert before == after


def test_pinned_digest_recipe_matches_committed_analysis():
    digest, n_files = mod.checkpoints_digest(CANONICAL)
    assert n_files == 64
    assert digest == mod.PINNED_CHECKPOINTS_SHA256
    committed = json.loads(
        (mod.REPO_ROOT / "result" / "analysis" / "20260816T190835Z"
         / "MANIFEST.json").read_text())
    assert committed["input_hashes"]["boundary"]["checkpoints_sha256"] == (
        mod.PINNED_CHECKPOINTS_SHA256)


def test_hash_replicas_match_committed_points():
    ck = json.loads(
        (CANONICAL / "checkpoints" / "s0_n8_slot8"
         / "sweep.ckpt.json").read_text())
    for point in ck["points"][:5] + ck["points"][-5:]:
        assert mod.schedule_hash(point["sequences"]) == (
            point["schedule_hash"])
        assert mod.load_hash(point["load"]) == point["load_hash"]


def test_classify_pair_replica_golden():
    base = {"schedule_hash": "aaa", "load_hash": "xxx",
            "load": [0.0, 0.0], "fleet": 2, "delta": 0.0,
            "load_slot": 0.0}
    same = dict(base, delta=0.01)
    assert mod.classify_pair(base, same) is None
    # fleet change wins precedence even with tiny load motion
    fleet = dict(base, delta=0.01, fleet=3, load_hash="yyy")
    assert mod.classify_pair(base, fleet)["kind"] == "fleet_change"
    # at exactly the tolerance the change is degenerate (<=)
    deg = dict(base, delta=0.01, load=[1.0, 0.0], load_hash="yyy")
    assert mod.classify_pair(base, deg)["kind"] == "degenerate_tie"
    # above the tolerance with a schedule flip: duty change
    duty = dict(base, delta=0.01, load=[1.5, 0.0], load_hash="yyy",
                schedule_hash="bbb")
    sw = mod.classify_pair(base, duty)
    assert sw["kind"] == "duty_change" and sw["schedule_changed"]
    assert sw["load_l1"] == 1.5
    # above the tolerance, same partition: charging-only
    charge = dict(base, delta=0.01, load=[1.5, 0.0], load_hash="yyy")
    assert mod.classify_pair(base, charge)["kind"] == "charging_only"


def test_evidence_limits_in_spec():
    text = SPEC.read_text()
    assert "HASH RESOLUTION" in text
    assert "never received the margin test" in text.lower() or (
        "NEVER received the margin test" in text)
    assert "one degenerate row does not change the route partition" \
        in text.lower()
    assert "-4.5e-13" in text
    assert "b9807ab8f8b50094e5bd4ebceb507b87eabd1c546372fb54d35906e8420ba4a1" \
        in text


# --------------------------------------------------------------------------
# fixture end-to-end and determinism
# --------------------------------------------------------------------------
def test_fixture_end_to_end_build(fixture_root, tmp_path):
    out_dir = Path(_fix_build(fixture_root, tmp_path / "out"))
    sweeps = list(csv.DictReader(open(out_dir / "sweeps.csv")))
    assert len(sweeps) == 3
    assert {s["split"] for s in sweeps} == {"train", "validation", "test"}
    intervals = list(csv.DictReader(open(out_dir / "intervals.csv")))
    assert len(intervals) == 9
    assert [r["kind"] for r in intervals
            if r["sweep_id"] == "s0_n8_slot8"] == [
        "stable", "duty_change", "degenerate_tie"]
    stable_rows = [r for r in intervals if r["stable"] == "True"]
    assert len(stable_rows) == 3
    economic = [r for r in intervals if r["economic"] == "True"]
    assert len(economic) == 2  # seed 5's duty change is a margin tie
    tie_rows = [r for r in intervals if r["tie_margin"] == "True"]
    assert len(tie_rows) == 1 and tie_rows[0]["seed"] == "5"
    # the schedule-preserving degenerate exists exactly once (seed 0)
    preserving = [r for r in intervals
                  if r["kind"] == "degenerate_tie"
                  and r["schedule_changed"] == "False"]
    assert len(preserving) == 1 and preserving[0]["seed"] == "0"
    # margins are absent (empty) outside duty/fleet rows
    for row in intervals:
        if row["kind"] in ("stable", "degenerate_tie", "charging_only"):
            assert row["margin_b_at_a"] == "" and row["tie_margin"] == ""

    schema = json.loads((out_dir / "feature_schema.json").read_text())
    assert schema["features"] == list(mod.FEATURE_COLUMNS)
    assert schema["outcomes"] == list(mod.OUTCOME_COLUMNS)
    assert schema["evidence_limits"] == list(mod.EVIDENCE_LIMITS)
    split = json.loads((out_dir / "SPLIT_MANIFEST.json").read_text())
    assert split["train"]["sweeps"] == ["s0_n8_slot8"]
    assert split["validation"]["sweeps"] == ["s5_n8_slot8"]
    assert split["test"]["sweeps"] == ["s6_n8_slot8"]
    assert sum(split[s]["n_intervals"]
               for s in ("train", "validation", "test")) == 9
    manifest = json.loads((out_dir / "MANIFEST.json").read_text())
    assert manifest["schema"] == mod.SCHEMA
    assert manifest["evidence_limits"] == list(mod.EVIDENCE_LIMITS)
    assert manifest["base_commit"] == mod.BASE_COMMIT
    assert manifest["csv_headers"]["intervals.csv"] == mod.INTERVAL_COLUMNS
    for name, sha in manifest["outputs"].items():
        assert mod.sha256_file(out_dir / name) == sha


def test_fixture_build_is_byte_identical(fixture_root, tmp_path):
    first = Path(_fix_build(fixture_root, tmp_path / "a"))
    second = Path(_fix_build(fixture_root, tmp_path / "b"))
    names = sorted(p.name for p in first.iterdir())
    assert names == sorted(p.name for p in second.iterdir())
    for name in names:
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_no_crlf_in_emitted_csvs(fixture_root, tmp_path):
    out_dir = Path(_fix_build(fixture_root, tmp_path / "out"))
    for path in out_dir.glob("*.csv"):
        assert b"\r" not in path.read_bytes(), path.name


def test_existing_output_refused_and_staging_cleaned(fixture_root,
                                                     tmp_path):
    _fix_build(fixture_root, tmp_path / "out")
    with pytest.raises(mod.B31Error, match="refusing existing output"):
        _fix_build(fixture_root, tmp_path / "out")
    assert not list((tmp_path / "out").glob(".B31TEST.b31-staging-*"))


# --------------------------------------------------------------------------
# leakage and split integrity
# --------------------------------------------------------------------------
def test_feature_leakage_guard():
    mod.assert_no_feature_leakage()  # the frozen schema is leakage-free
    with pytest.raises(mod.B31Error, match="leaks right-endpoint"):
        mod.assert_no_feature_leakage(("seed", "right_obj"))
    with pytest.raises(mod.B31Error, match="leaks right-endpoint"):
        mod.assert_no_feature_leakage(("seed", "load_l1"))
    # no feature column carries right-endpoint solution information
    for name in mod.FEATURE_COLUMNS:
        assert not name.startswith("right_")
        assert name not in mod.OUTCOME_COLUMNS


def test_split_is_whole_seed_and_exhaustive():
    assigned = [s for seeds in mod.SPLIT_BY_SEED.values() for s in seeds]
    assert sorted(assigned) == sorted(set(assigned))  # no seed twice
    assert sorted(assigned) == list(range(8))         # all seeds covered
    assert mod.SPLIT_BY_SEED["train"] == (0, 1, 2, 3, 4)
    assert mod.SPLIT_BY_SEED["validation"] == (5,)
    assert mod.SPLIT_BY_SEED["test"] == (6, 7)
    with pytest.raises(mod.B31Error, match="not assigned"):
        mod.seed_split(9)


# --------------------------------------------------------------------------
# tamper and refusal battery (fixtures)
# --------------------------------------------------------------------------
def test_digest_mismatch_refused(fixture_root, tmp_path, monkeypatch):
    path = next((fixture_root / "checkpoints").glob("*/sweep.ckpt.json"))
    path.write_text(path.read_text() + "\n")
    with pytest.raises(mod.B31Error, match="digest mismatch"):
        _fix_build(fixture_root, tmp_path / "out")


def test_input_mutation_during_build_detected(fixture_root, tmp_path,
                                              monkeypatch):
    victim = next((fixture_root / "checkpoints").glob("*/sweep.ckpt.json"))
    real_reconcile = mod._reconcile_switch
    state = {"mutated": False}

    def mutate_once(stored, recomputed, label):
        if not state["mutated"]:
            state["mutated"] = True
            victim.write_text(victim.read_text() + "\n")
        return real_reconcile(stored, recomputed, label)

    monkeypatch.setattr(mod, "_reconcile_switch", mutate_once)
    with pytest.raises(mod.B31Error, match="mutated during the build"):
        _fix_build(fixture_root, tmp_path / "out")
    assert state["mutated"]


@pytest.mark.parametrize("case,message", [
    ("kind", "stored kind"),
    ("load_l1", "deviates from recomputed"),
    ("drop_margin", "lacks margin_b_at_a"),
    ("margin_on_degenerate", "must not carry"),
    ("tie_flip", "margins replay"),
    ("counts", "counts_by_kind"),
    ("n_economic", "n_economic_switches does not replay"),
    ("not_done", "not complete"),
    ("extra_switch", "no recomputed counterpart"),
    ("missing_switch", "no stored counterpart"),
    ("negative_margin", "below the solver-noise floor"),
    ("sequences", "schedule_hash does not recompute"),
    ("off_grid_delta", "off-grid"),
    ("point_count", "expected 4 points"),
])
def test_stored_evidence_tampering_refused(fixture_root, tmp_path,
                                           monkeypatch, case, message):
    def mutate(state):
        switches = state["switches"]
        duty = next(s for s in switches if s["kind"] == "duty_change")
        degenerate = next(
            s for s in switches if s["kind"] == "degenerate_tie")
        if case == "kind":
            duty["kind"] = "charging_only"
        elif case == "load_l1":
            duty["load_l1"] += 1e-6
        elif case == "drop_margin":
            duty.pop("margin_b_at_a")
        elif case == "margin_on_degenerate":
            degenerate["tie_margin"] = False
        elif case == "tie_flip":
            duty["tie_margin"] = not duty["tie_margin"]
        elif case == "counts":
            state["counts_by_kind"]["duty_change"] += 1
        elif case == "n_economic":
            state["n_economic_switches"] += 1
        elif case == "not_done":
            state["margins_done"] = False
        elif case == "extra_switch":
            switches.append(copy.deepcopy(duty))
            state["n_switches"] += 1
        elif case == "missing_switch":
            switches.remove(degenerate)
            state["n_switches"] -= 1
        elif case == "negative_margin":
            duty["margin_b_at_a"] = -1e-6
        elif case == "sequences":
            state["points"][2]["sequences"][0].append("t9")
        elif case == "off_grid_delta":
            state["points"][1]["delta"] += 0.004
        elif case == "point_count":
            state["points"].append(dict(state["points"][-1], idx=4))
        else:
            raise AssertionError(case)

    _retamper(fixture_root, mutate, monkeypatch)
    with pytest.raises(mod.B31Error, match=message):
        _fix_build(fixture_root, tmp_path / "out")


def test_exact_total_gate_refuses(fixture_root, tmp_path):
    expected = _fixture_expected()
    expected["stable"] += 1
    with pytest.raises(mod.B31Error, match="exact-total gate failed"):
        mod.build(fixture_root, tmp_path / "out", "S", "x" * 40,
                  verify_code_commit=False, expected_totals=expected)


def test_missing_and_offgrid_sweeps_refused(fixture_root, tmp_path,
                                            monkeypatch):
    victim = fixture_root / "checkpoints" / "s6_n8_slot8"
    shutil.rmtree(victim)
    digest, _ = mod.checkpoints_digest(fixture_root)
    monkeypatch.setattr(mod, "PINNED_CHECKPOINTS_SHA256", digest)
    with pytest.raises(mod.B31Error, match="expected 3 sweep checkpoints"):
        _fix_build(fixture_root, tmp_path / "out-missing")

    rogue = fixture_root / "checkpoints" / "s9_n8_slot8"
    rogue.mkdir()
    src = fixture_root / "checkpoints" / "s0_n8_slot8" / "sweep.ckpt.json"
    (rogue / "sweep.ckpt.json").write_text(src.read_text())
    digest, _ = mod.checkpoints_digest(fixture_root)
    monkeypatch.setattr(mod, "PINNED_CHECKPOINTS_SHA256", digest)
    with pytest.raises(mod.B31Error, match="outside or duplicating"):
        _fix_build(fixture_root, tmp_path / "out-rogue")


# --------------------------------------------------------------------------
# provenance verification
# --------------------------------------------------------------------------
def test_build_provenance_verification(monkeypatch):
    with pytest.raises(mod.B31Error, match="full 40-character"):
        mod.verify_build_provenance("740ab0c")
    with pytest.raises(mod.B31Error, match="full 40-character"):
        mod.verify_build_provenance("Z" * 40)
    with pytest.raises(mod.B31Error, match="does not resolve"):
        mod.verify_build_provenance("f" * 40)

    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=mod.REPO_ROOT).decode().strip()
    real_run = mod.subprocess.run
    real_co = mod.subprocess.check_output

    def claimed_not_ancestor(args, cwd=None, **kwargs):
        if args[:2] == ["git", "merge-base"] and args[3] == head:
            class R:
                returncode = 1
            return R()
        return real_run(args, cwd=cwd, **kwargs)

    monkeypatch.setattr(mod.subprocess, "run", claimed_not_ancestor)
    with pytest.raises(mod.B31Error,
                       match=f"{head} is not an ancestor"):
        mod.verify_build_provenance(head)
    monkeypatch.setattr(mod.subprocess, "run", real_run)

    # HEAD may equal BASE_COMMIT, so discriminate by call order: the
    # first merge-base call checks the claimed commit, the second checks
    # the frozen base
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
    with pytest.raises(mod.B31Error, match="frozen base"):
        mod.verify_build_provenance(head)
    monkeypatch.setattr(mod.subprocess, "run", real_run)

    def dirty_status(args, cwd=None, stderr=None):
        if args[1] == "status":
            return b" M src/experiments/build_b31_boundary_corpus.py\n"
        return real_co(args, cwd=cwd, stderr=stderr)

    monkeypatch.setattr(mod.subprocess, "check_output", dirty_status)
    with pytest.raises(mod.B31Error, match="tracked modifications"):
        mod.verify_build_provenance(head)
    monkeypatch.setattr(mod.subprocess, "check_output", real_co)

    def stale_show(args, cwd=None, stderr=None):
        if args[1] == "status":
            return b""
        if args[1] == "show":
            return b"different bytes"
        return real_co(args, cwd=cwd, stderr=stderr)

    monkeypatch.setattr(mod.subprocess, "check_output", stale_show)
    with pytest.raises(mod.B31Error, match="differs from the claimed"):
        mod.verify_build_provenance(head)
