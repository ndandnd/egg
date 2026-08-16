"""Tests for experiments/analyze_closeout.py: determinism, certified
filtering, tie exclusion, and records-vs-checkpoint cross-validation."""
import filecmp
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest

from egglab import checkpoint
from experiments.analyze_closeout import (
    AnalysisError,
    analyze,
    checkpoints_digest,
    output_hashes,
    sha256_file,
)

COLS = dict(
    experiment="phase1-static", regime="taker", timestamp="t", host="h",
    git_commit="c", instance_name="syn-s0-n6", n_trips=6, fleet=2,
    replay_original_ok=True, replay_effective_ok=True, solver_status="OPTIMAL",
    solver_wall_s=1.0, solver_lp_mip_gap_abs=10.0, obj_true=100.0,
    econ_total_system=100.0, econ_total_private=100.0, econ_energy_kwh=20.0,
    x_seed=0, x_b_scale=0.01, x_alpha=1.0, x_iter=None, x_outcome_type=None,
    x_cycle_length=None, x_price_residual=None, x_sweep_slot=None,
    x_delta=None, x_idx=None,
)


def rec(**over):
    r = dict(COLS)
    r.update(over)
    return r


def _write_root(path, recs, loop_ckpts=None, sweep_ckpts=None):
    os.makedirs(path, exist_ok=True)
    df = pd.DataFrame(recs)
    df.to_csv(os.path.join(path, "records.csv"), index=False)
    raw_fail = int((df["replay_original_ok"] == False).sum())  # noqa: E712
    with open(os.path.join(path, "SUMMARY.md"), "w") as f:
        f.write(f"Total records: **{len(df)}**\n"
                f"- raw legacy replay failures: {raw_fail}\n")
    for cell, ck in (loop_ckpts or {}).items():
        checkpoint.save(os.path.join(path, "checkpoints", cell, "loop.ckpt.json"), ck)
    for cell, ck in (sweep_ckpts or {}).items():
        checkpoint.save(os.path.join(path, "checkpoints", cell, "sweep.ckpt.json"), ck)


def _loop_root(path, outcome="cycle", tamper_outcome=None, extra_recs=()):
    """One loop cell (seed 0, n6, b 0.01, alpha 0.5) with 3 iterations,
    plus static records for welfare (2 alpha draws x 4 regimes)."""
    recs = []
    for k in range(3):
        recs.append(rec(
            experiment="phase1-loop", regime="taker-iteration",
            x_alpha=0.5, x_iter=k, x_price_residual=0.1 / (k + 1),
            x_outcome_type=outcome if k == 2 else None,
            x_cycle_length=2 if (outcome == "cycle" and k == 2) else None,
        ))
    for alpha in (0.5, 1.0):
        for regime, ts in (("uncontrolled", 120.0), ("taker", 110.0),
                           ("strategic", 105.0), ("dictator", 100.0)):
            recs.append(rec(regime=regime, x_alpha=alpha, obj_true=ts,
                            econ_total_system=ts, econ_total_private=ts))
    recs.extend(extra_recs)
    ck_outcome = {"type": tamper_outcome or outcome}
    if (tamper_outcome or outcome) == "cycle":
        ck_outcome.update({"length": 2, "first_seen": 1})
    ck_outcome["iter"] = 2
    _write_root(path, recs, loop_ckpts={
        "s0_n6_duck_b0.01_a0.5": {"done": True, "iter": 3, "outcome": ck_outcome},
    })


def _sweep_root(path):
    """One sweep cell with 4 points: a degenerate tie, an economic duty
    change, and a margin-tied duty change."""
    pts = [
        {"idx": 0, "delta": -0.5, "schedule_hash": "A", "load_hash": "x",
         "load": [10.0, 0.0], "fleet": 2, "load_slot": 10.0, "obj": 100.0},
        {"idx": 1, "delta": 0.0, "schedule_hash": "B", "load_hash": "x",
         "load": [10.0, 0.0], "fleet": 2, "load_slot": 10.0, "obj": 100.0},
        {"idx": 2, "delta": 0.5, "schedule_hash": "C", "load_hash": "y",
         "load": [0.0, 10.0], "fleet": 2, "load_slot": 0.0, "obj": 101.0},
        {"idx": 3, "delta": 1.0, "schedule_hash": "D", "load_hash": "z",
         "load": [5.0, 5.0], "fleet": 2, "load_slot": 5.0, "obj": 102.0},
    ]
    switches = [
        {"between_deltas": [-0.5, 0.0], "kind": "degenerate_tie", "load_l1": 0.0,
         "load_jump_slot": 0.0, "fleet_change": 0, "schedule_changed": True},
        {"between_deltas": [0.0, 0.5], "kind": "duty_change", "load_l1": 20.0,
         "load_jump_slot": -10.0, "fleet_change": 0, "schedule_changed": True,
         "tie_margin": False, "margin_b_at_a": 5.0, "margin_a_at_b": 5.0},
        {"between_deltas": [0.5, 1.0], "kind": "duty_change", "load_l1": 10.0,
         "load_jump_slot": 5.0, "fleet_change": 0, "schedule_changed": True,
         "tie_margin": True, "margin_b_at_a": 0.0, "margin_a_at_b": 0.0},
    ]
    recs = [rec(experiment="phase2", regime="taker-sweep", x_alpha=None,
                x_b_scale=None, x_sweep_slot=0, x_delta=p["delta"], x_idx=p["idx"])
            for p in pts]
    _write_root(path, recs, sweep_ckpts={
        "s0_n6_slot0": {"done": True, "margins_done": True, "points": pts,
                        "switches": switches, "n_switches": 3,
                        "n_economic_switches": 1,
                        "counts_by_kind": {"degenerate_tie": 1, "charging_only": 0,
                                           "duty_change": 2, "fleet_change": 0}},
    })


@pytest.fixture()
def roots(tmp_path):
    p1 = str(tmp_path / "p1")
    dp = str(tmp_path / "dp")
    bd = str(tmp_path / "bd")
    _loop_root(p1)
    _loop_root(dp, outcome="fixed_point")
    _sweep_root(bd)
    return p1, dp, bd


def test_end_to_end_and_determinism(roots, tmp_path):
    p1, dp, bd = roots
    out1, out2 = str(tmp_path / "o1"), str(tmp_path / "o2")
    r1 = analyze(p1, dp, bd, out1)
    analyze(p1, dp, bd, out2)
    csvs = [f for f in os.listdir(out1) if f.endswith(".csv")]
    assert csvs
    for f in csvs:
        assert filecmp.cmp(os.path.join(out1, f), os.path.join(out2, f),
                           shallow=False), f"non-deterministic output: {f}"
    # tie exclusion: only 1 economic switch (degenerate + margin-tied excluded)
    sw = r1["switches"]
    assert len(sw) == 3
    assert int(sw["economic"].sum()) == 1
    # outcome table sees both campaigns
    assert set(r1["cells"]["outcome"]) == {"cycle", "fixed_point"}


def test_certified_filter_and_raw_totals(roots, tmp_path):
    p1, dp, bd = roots
    # rebuild phase1 with one non-OPTIMAL and one effective-false record
    bad = [
        rec(regime="taker", solver_status="TIME_LIMIT", x_alpha=0.5),
        rec(regime="taker", replay_original_ok=False, replay_effective_ok=False,
            x_alpha=0.5),
    ]
    p1b = str(tmp_path / "p1b")
    _loop_root(p1b, extra_recs=bad)
    res = analyze(p1b, dp, bd, str(tmp_path / "o"))
    t = res["totals"].set_index("campaign")
    assert t.loc["phase1", "records"] == t.loc["phase1", "certified_records"] + 2
    assert t.loc["phase1", "raw_replay_failures"] == 1
    assert t.loc["phase1", "unresolved"] == 1
    assert t.loc["phase1", "non_optimal"] == 1


def test_cross_validation_catches_tampered_checkpoint(roots, tmp_path):
    _p1, dp, bd = roots
    p1t = str(tmp_path / "p1t")
    _loop_root(p1t, outcome="cycle", tamper_outcome="fixed_point")
    with pytest.raises(AnalysisError, match="terminal outcome"):
        analyze(p1t, dp, bd, str(tmp_path / "o"))


def test_manifest_hashes_inputs_and_outputs(roots, tmp_path):
    """Provenance: MANIFEST.json must carry verifiable SHA-256 hashes of the
    canonical inputs and of every generated output."""
    p1, dp, bd = roots
    out = str(tmp_path / "o")
    analyze(p1, dp, bd, out)
    man = json.load(open(os.path.join(out, "MANIFEST.json")))
    assert man["analysis_code_commit"]
    # inputs
    for name, root in (("phase1", p1), ("damping", dp), ("boundary", bd)):
        ih = man["input_hashes"][name]
        assert ih["records.csv"] == sha256_file(os.path.join(root, "records.csv"))
        assert ih["SUMMARY.md"] == sha256_file(os.path.join(root, "SUMMARY.md"))
        digest, n = checkpoints_digest(root)
        assert ih["checkpoints_sha256"] == digest
        assert ih["n_checkpoint_files"] == n
    # outputs: every generated file hashed, every hash correct
    oh = man["output_hashes"]
    recomputed = output_hashes(out)
    assert oh == recomputed
    assert any(k.endswith(".csv") for k in oh)
    assert any(k.startswith("figures/") for k in oh)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _repo_analysis_dirs():
    base = os.path.join(REPO_ROOT, "result", "analysis")
    if not os.path.isdir(base):
        return []
    return sorted(
        os.path.join(base, s) for s in os.listdir(base)
        if os.path.exists(os.path.join(base, s, "MANIFEST.json"))
    )


def test_committed_artifacts_match_their_manifest():
    """Integrity of committed analysis artifacts: every generated file and
    every canonical input must match the SHA-256 recorded in the artifact
    set's own MANIFEST.json. Environment-independent: verifies the committed
    files, not cross-environment regeneration."""
    dirs = [d for d in _repo_analysis_dirs()
            if "output_hashes" in json.load(open(os.path.join(d, "MANIFEST.json")))]
    if not dirs:
        pytest.skip("no committed analysis artifacts with provenance manifests")
    for d in dirs:
        man = json.load(open(os.path.join(d, "MANIFEST.json")))
        assert man["output_hashes"] == output_hashes(d), f"artifact drift in {d}"
        for name, ih in man["input_hashes"].items():
            root = ih["path"] if os.path.isabs(ih["path"]) \
                else os.path.join(REPO_ROOT, ih["path"])
            assert os.path.isdir(root), f"{d}: input root missing: {root}"
            assert ih["records.csv"] == sha256_file(os.path.join(root, "records.csv")), \
                f"input drift: {root}/records.csv"
            assert ih["SUMMARY.md"] == sha256_file(os.path.join(root, "SUMMARY.md")), \
                f"input drift: {root}/SUMMARY.md"
            digest, n = checkpoints_digest(root)
            assert ih["checkpoints_sha256"] == digest, f"input drift: {root}/checkpoints"
            assert ih["n_checkpoint_files"] == n


def test_dominance_violation_detected(roots, tmp_path):
    _p1, dp, bd = roots
    p1w = str(tmp_path / "p1w")
    # dictator strictly worse than taker in total_system
    recs = []
    for k in range(3):
        recs.append(rec(experiment="phase1-loop", regime="taker-iteration",
                        x_alpha=0.5, x_iter=k, x_price_residual=0.1,
                        x_outcome_type="cycle" if k == 2 else None,
                        x_cycle_length=2 if k == 2 else None))
    for regime, ts in (("uncontrolled", 120.0), ("taker", 90.0),
                       ("strategic", 105.0), ("dictator", 100.0)):
        recs.append(rec(regime=regime, obj_true=ts, econ_total_system=ts,
                        econ_total_private=ts, x_alpha=0.5))
    _write_root(p1w, recs, loop_ckpts={
        "s0_n6_duck_b0.01_a0.5": {"done": True, "iter": 3,
                                  "outcome": {"type": "cycle", "length": 2,
                                              "first_seen": 1, "iter": 2}},
    })
    with pytest.raises(AnalysisError, match="dictator worse"):
        analyze(p1w, dp, bd, str(tmp_path / "o"))
