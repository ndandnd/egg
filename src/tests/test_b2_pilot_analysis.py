"""Regression battery for the B2 pilot-closeout pipeline
(experiments/analyze_b2_pilot.py): artifact integrity, matched-join
correctness, identity safeguards, and byte-identical determinism, exercised
on a REAL miniature pilot fixture (actual certified_cg runs + dictator
stages on tiny instances)."""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest

from egglab import checkpoint
from egglab.b2a2 import certified_cg
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from experiments.analyze_b2_pilot import (
    AnalysisError,
    analyze,
    sha256_file,
    verify_analysis_code_commit,
)
from experiments.run_b2a2_pilot import _dictator_stage

FIX_INSTANCES = ((1, 4, 0.01), (3, 4, 0.05))
METHODS = ("a2", "a3", "a4", "a5")


def fix_builder(seed, n_trips):
    return synthetic_instance(seed=seed, n_trips=n_trips, max_vehicles=2)


@pytest.fixture(scope="module")
def pilot_roots(tmp_path_factory):
    """Miniature real pilot: 2 instances x 4 methods, run with the actual
    drivers' construction (dictator stage + certified CG per cell)."""
    base = tmp_path_factory.mktemp("pilot")
    a2_root = str(base / "b2a2_pilot")
    a345_root = str(base / "b2a345_pilot")
    kw = dict(max_mip_gap=1e-6, time_limit_s=None)
    for (s, n, b) in FIX_INSTANCES:
        inst = fix_builder(s, n)
        market = make_affine_market(inst, shape="duck", b_scale=b)
        for m in METHODS:
            tag_dir = (f"s{s}_n{n}_b{b:g}" if m == "a2"
                       else f"{m}_s{s}_n{n}_b{b:g}")
            root = a2_root if m == "a2" else a345_root
            out = os.path.join(root, tag_dir)
            os.makedirs(out, exist_ok=True)
            d_state = _dictator_stage(inst, market, out, tag_dir,
                                      [m, s, n, b], kw)
            certified_cg(inst, market, epsilon=1e-2, budget=60,
                         out_dir=out, tag=m, method=m, solver_kw=kw,
                         z_d_ub=d_state["z_d_ub"], tol_d=d_state["tol_d"])
    return a2_root, a345_root


@pytest.fixture(scope="module")
def artifacts(pilot_roots, tmp_path_factory):
    a2_root, a345_root = pilot_roots
    out_base = str(tmp_path_factory.mktemp("result"))
    out_dir = analyze(a2_root, a345_root, out_base, "TESTSTAMP",
                      "codecommit0", instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)
    return out_dir


def test_all_artifacts_written(artifacts):
    for fn in ("MANIFEST.json", "cells.csv", "matched_comparison.csv",
               "method_summary.csv", "acceptance_status.csv", "SUMMARY.md",
               "F1_matched_oracle_calls.png", "F2_matched_solver_wall.png",
               "F3_broadcast_total_variation.png"):
        assert os.path.exists(os.path.join(artifacts, fn)), fn


def test_artifact_integrity_manifest_hashes(artifacts):
    man = json.load(open(os.path.join(artifacts, "MANIFEST.json")))
    assert man["analysis_code_commit"] == "codecommit0"
    assert man["outputs"], "manifest lists no outputs"
    for fn, digest in man["outputs"].items():
        assert sha256_file(os.path.join(artifacts, fn)) == digest, fn
    # input evidence hashed file-by-file
    assert man["inputs"]["b2a2_pilot"]["files"]
    assert man["inputs"]["b2a345_pilot"]["files"]
    assert man["tolerances"]["epsilon"] == [0.01]
    assert man["tolerances"]["budget"] == [60]


def test_cells_table_shape_and_evidence(artifacts):
    cells = pd.read_csv(os.path.join(artifacts, "cells.csv"))
    assert len(cells) == 4 * len(FIX_INSTANCES)
    for m in METHODS:
        assert (cells["method"] == m).sum() == len(FIX_INSTANCES)
    assert cells["certified"].all()
    assert (cells["oracle_calls"] ==
            cells["oracle_calls_clean"] + cells["oracle_calls_stab"]).all()
    a2 = cells[cells["method"] == "a2"]
    assert (a2["oracle_calls_stab"] == 0).all()
    assert (cells["total_solver_wall_s"] > 0).all()
    assert (cells["dictator_wall_s"] > 0).all()
    assert cells["broadcast_tv"].notna().all()
    assert cells["uplift_hi"].notna().all()


def test_matched_join_regression(artifacts):
    cells = pd.read_csv(os.path.join(artifacts, "cells.csv"))
    matched = pd.read_csv(os.path.join(artifacts, "matched_comparison.csv"))
    assert len(matched) == 3 * len(FIX_INSTANCES)
    cix = cells.set_index(["method", "seed", "n_trips", "b"])
    for _, r in matched.iterrows():
        a2_calls = int(cix.loc[("a2", r["seed"], r["n_trips"], r["b"]),
                               "oracle_calls"])
        m_calls = int(cix.loc[(r["method"], r["seed"], r["n_trips"], r["b"]),
                              "oracle_calls"])
        assert r["a2_calls"] == a2_calls
        assert r["method_calls"] == m_calls
        assert r["calls_diff"] == m_calls - a2_calls
        assert r["calls_ratio"] == pytest.approx(m_calls / a2_calls)
        expected = ("win" if m_calls < a2_calls
                    else "tie" if m_calls == a2_calls else "loss")
        assert r["calls_result_vs_a2"] == expected


def test_method_summary_consistency(artifacts):
    summary = pd.read_csv(os.path.join(artifacts, "method_summary.csv"))
    ov = summary[summary["scope"] == "overall"].set_index("method")
    assert set(ov.index) == set(METHODS)
    for m in ("a3", "a4", "a5"):
        r = ov.loc[m]
        assert (r["wins_vs_a2"] + r["ties_vs_a2"] + r["losses_vs_a2"]
                == len(FIX_INSTANCES))
    assert (ov["cert_rate"] == 1.0).all()


def test_acceptance_status_statuses(artifacts):
    acc = pd.read_csv(os.path.join(artifacts, "acceptance_status.csv"))
    assert set(acc["status"]).issubset(
        {"pilot-supports", "pilot-rejects", "not-testable-from-pilot"})
    # full-grid criteria must not be labeled as passed from pilot cells
    a1 = acc[acc["criterion_id"] == "acc-1-cert95-b005"].iloc[0]
    assert a1["status"] == "not-testable-from-pilot"
    a4c = acc[acc["criterion_id"] == "acc-4-vs-tatonnement"].iloc[0]
    assert a4c["status"] == "not-testable-from-pilot"
    # corrected denominators (review): 64 moderate/strong instances per
    # method for the 2x criterion; 96 method-cells for the b=0.05 one
    a3c = acc[acc["criterion_id"] == "acc-3-stab-beats-a2-2x"].iloc[0]
    assert "64 moderate/strong" in a3c["denominator"]
    assert "96 method-cells" in a1["denominator"]
    # statuses must equal the recomputed rule (labels are data-derived)
    summary = pd.read_csv(os.path.join(artifacts, "method_summary.csv"))
    ov = summary[summary["scope"] == "overall"].set_index("method")
    a2_med = float(ov.loc["a2", "calls_median"])
    best = min(float(ov.loc[m, "calls_median"]) for m in ("a3", "a4", "a5"))
    speedup = a2_med / best
    cells = pd.read_csv(os.path.join(artifacts, "cells.csv"))
    a2_rate = cells[(cells.method == "a2") &
                    (cells.b == 0.05)]["certified"].mean()
    assert a3c["status"] == (
        "pilot-supports" if speedup >= 2 else "pilot-rejects")
    k1 = acc[acc["criterion_id"] == "kill-1-a2-meets-bar"].iloc[0]
    assert "32 b=0.05 A2 instances" in k1["denominator"]
    assert k1["status"] == ("pilot-supports"
                            if a2_rate >= 0.95 and speedup < 2
                            else "pilot-rejects")


def test_acceptance_labels_flip_with_different_data(artifacts):
    """Feeding different results must produce different verdicts — the
    labels are calculated, not hardcoded (review finding 1)."""
    from experiments.analyze_b2_pilot import acceptance_status
    cells = pd.read_csv(os.path.join(artifacts, "cells.csv"))
    summary = pd.read_csv(os.path.join(artifacts, "method_summary.csv"))
    # counterfactual: A2 suddenly needs 10x the calls
    flipped = summary.copy()
    mask = (flipped["scope"] == "overall") & (flipped["method"] == "a2")
    flipped.loc[mask, "calls_median"] *= 10
    acc = acceptance_status(cells, flipped, len(FIX_INSTANCES))
    a3c = acc[acc["criterion_id"] == "acc-3-stab-beats-a2-2x"].iloc[0]
    k1 = acc[acc["criterion_id"] == "kill-1-a2-meets-bar"].iloc[0]
    assert a3c["status"] == "pilot-supports"   # stabilization now wins 2x
    assert k1["status"] == "pilot-rejects"     # kill signal off


def test_dictator_identity_validated(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a4_s1_n4_b0.01", "dictator.ckpt.json")
    ck = checkpoint.load(p)
    ck["identity"]["market_hash"] = "tampered"
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="dictator market hash mismatch"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_stale_dictator_pairing_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a5_s3_n4_b0.05", "dictator.ckpt.json")
    ck = checkpoint.load(p)
    ck["z_d_ub"] = ck["z_d_ub"] + 5.0  # dictator value no longer the one CG used
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="stale pairing"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_zch_dictator_contradiction_halts(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    d = os.path.join(c345, "a3_s1_n4_b0.01")
    dp = os.path.join(d, "dictator.ckpt.json")
    cp = os.path.join(d, "a3.cg.ckpt.json")
    dck = checkpoint.load(dp)
    cck = checkpoint.load(cp)
    bogus = cck["lb_best"] - 100.0  # z_D below LB_CH: impossible physics
    dck["z_d_ub"] = bogus
    cck["identity"]["z_d_ub"] = bogus  # keep the pairing consistent
    checkpoint.save(dp, dck)
    checkpoint.save(cp, cck)
    with pytest.raises(AnalysisError, match="CONTRADICTION"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_code_commit_verification_rejects_wrong_commit(pilot_roots,
                                                       tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    with pytest.raises(AnalysisError, match="cannot resolve|code commit mismatch"):
        analyze(c2, c345, str(tmp_path / "out"), "T",
                "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=True)


@pytest.mark.parametrize(
    "claimed", ("", "abcdef", "ABCDEF0", "abcdeg0", "a" * 41))
def test_analysis_commit_verifier_rejects_invalid_claim_without_git(
        claimed, monkeypatch):
    def unexpected(*_args, **_kwargs):
        raise AssertionError("invalid commit syntax must fail before Git")

    monkeypatch.setattr(subprocess, "check_output", unexpected)
    with pytest.raises(AnalysisError, match="7-40 lowercase hexadecimal"):
        verify_analysis_code_commit(claimed)


def test_analysis_commit_verifier_rejects_unresolved_claim(monkeypatch):
    def unresolved(command, **_kwargs):
        assert command[-1] == "deadbee^{commit}"
        raise subprocess.CalledProcessError(128, command)

    monkeypatch.setattr(subprocess, "check_output", unresolved)
    with pytest.raises(AnalysisError, match="cannot resolve"):
        verify_analysis_code_commit("deadbee")


def test_analysis_commit_verifier_rejects_resolved_non_head(monkeypatch):
    head = "a" * 40

    def output(command, **_kwargs):
        if command[-1] == "deadbee^{commit}":
            return "b" * 40 + "\n"
        if command[-1] == "HEAD^{commit}":
            return head + "\n"
        raise AssertionError(command)

    monkeypatch.setattr(subprocess, "check_output", output)
    with pytest.raises(AnalysisError, match="code commit mismatch"):
        verify_analysis_code_commit("deadbee")


@pytest.mark.parametrize("use_full", (False, True))
def test_analysis_commit_verifier_accepts_resolved_head_and_clean_tree(
        use_full, monkeypatch):
    head = "a" * 40
    claimed = head if use_full else head[:7]
    calls = []

    def output(command, **_kwargs):
        calls.append(command)
        if command[-1] in (f"{claimed}^{{commit}}", "HEAD^{commit}"):
            return head + "\n"
        if command[1] == "status":
            return ""
        raise AssertionError(command)

    monkeypatch.setattr(subprocess, "check_output", output)
    assert verify_analysis_code_commit(claimed) == head
    assert calls[-1] == [
        "git", "status", "--porcelain", "--untracked-files=no"]


def test_analysis_commit_verifier_rejects_dirty_tracked_tree(monkeypatch):
    head = "a" * 40

    def output(command, **_kwargs):
        if command[1] == "rev-parse":
            return head + "\n"
        if command[1] == "status":
            return " M src/experiments/analyze_b2_pilot.py\n"
        raise AssertionError(command)

    monkeypatch.setattr(subprocess, "check_output", output)
    with pytest.raises(AnalysisError, match="uncommitted tracked changes"):
        verify_analysis_code_commit(head[:7])


def test_deterministic_regeneration_byte_identical(pilot_roots, artifacts,
                                                   tmp_path):
    a2_root, a345_root = pilot_roots
    out2 = analyze(a2_root, a345_root, str(tmp_path), "TESTSTAMP",
                   "codecommit0", instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)
    for fn in ("cells.csv", "matched_comparison.csv", "method_summary.csv",
               "acceptance_status.csv", "SUMMARY.md"):
        b1 = open(os.path.join(artifacts, fn), "rb").read()
        b2 = open(os.path.join(out2, fn), "rb").read()
        assert b1 == b2, f"{fn} not byte-identical on regeneration"


def _clone_roots(pilot_roots, tmp_path):
    a2_root, a345_root = pilot_roots
    c2 = str(tmp_path / "a2")
    c345 = str(tmp_path / "a345")
    shutil.copytree(a2_root, c2)
    shutil.copytree(a345_root, c345)
    return c2, c345


def test_missing_cell_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    shutil.rmtree(os.path.join(c345, "a4_s3_n4_b0.05"))
    with pytest.raises(AnalysisError):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_unexpected_extra_cell_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    shutil.copytree(os.path.join(c345, "a3_s1_n4_b0.01"),
                    os.path.join(c345, "a3_s9_n4_b0.01"))
    # the audit's expected-count gate fires first; the dedicated extras
    # check is the backstop if counts happen to still match
    with pytest.raises(AnalysisError,
                       match="audit FAILED|unexpected cg checkpoints"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_identity_mismatch_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a5_s1_n4_b0.01", "a5.cg.ckpt.json")
    ck = checkpoint.load(p)
    ck["identity"]["instance_hash"] = "tampered"
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="instance hash mismatch"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_wall_identity_and_decomposition_columns(artifacts):
    """Review fix: solver wall is partitioned exactly once; the identity
    wall_clean + wall_stab == total holds per cell, A2 has zero stabilized
    wall/calls, and the summaries expose the clean/stab decomposition."""
    cells = pd.read_csv(os.path.join(artifacts, "cells.csv"))
    resid = (cells["wall_clean_s"] + cells["wall_stab_s"]
             - cells["total_solver_wall_s"]).abs()
    assert (resid <= 1e-6).all(), resid.max()
    a2 = cells[cells["method"] == "a2"]
    assert (a2["wall_stab_s"] == 0).all()
    assert (a2["oracle_calls_stab"] == 0).all()
    matched = pd.read_csv(os.path.join(artifacts, "matched_comparison.csv"))
    for col in ("a2_clean_calls", "method_clean_calls", "method_stab_calls",
                "clean_calls_diff", "clean_result_vs_a2"):
        assert col in matched.columns, col
    summary = pd.read_csv(os.path.join(artifacts, "method_summary.csv"))
    for col in ("clean_calls_median", "stab_calls_median",
                "clean_wall_median_s", "stab_wall_median_s",
                "clean_wins_vs_a2", "clean_losses_vs_a2"):
        assert col in summary.columns, col
    # clean W/T/L recomputed from matched rows
    ov = summary[summary["scope"] == "overall"].set_index("method")
    for m in ("a3", "a4", "a5"):
        mm = matched[matched["method"] == m]
        assert int(ov.loc[m, "clean_wins_vs_a2"]) == int(
            (mm["clean_result_vs_a2"] == "win").sum())
    assert os.path.exists(os.path.join(artifacts,
                                       "F4_clean_vs_total_calls.png"))


def test_wall_double_counted_master_solve_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a3_s1_n4_b0.01", "a3.cg.ckpt.json")
    ck = checkpoint.load(p)
    ev = next(e for e in ck["iteration_events"] if e.get("master_solves"))
    ev["master_solves"] = ev["master_solves"] + [dict(ev["master_solves"][0])]
    checkpoint.save(p, ck)
    # the audit's per-checkpoint uniqueness gate or the wall partition's
    # dedup must reject it — either way, no silent double counting
    with pytest.raises(AnalysisError, match="audit FAILED|double counted"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_omitted_oracle_event_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a4_s1_n4_b0.01", "a4.cg.ckpt.json")
    ck = checkpoint.load(p)
    ck["oracle_events"] = ck["oracle_events"][1:]  # drop the seed call
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError,
                       match="audit FAILED|omitted or duplicated"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_unknown_oracle_regime_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a5_s1_n4_b0.01", "a5.cg.ckpt.json")
    ck = checkpoint.load(p)
    ck["oracle_events"][-1]["regime"] = "cg-mystery"
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="unknown oracle regime"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_phase_misclassification_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a3_s1_n4_b0.01", "a3.cg.ckpt.json")
    ck = checkpoint.load(p)
    ev = next(e for e in ck["iteration_events"]
              if e.get("phase") == "stabilized")
    ev["phase"] = "clean"  # its wall would be misattributed to clean
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="phase misclassification"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_a2_with_stabilized_call_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c2, "s1_n4_b0.01", "a2.cg.ckpt.json")
    ck = checkpoint.load(p)
    ck["oracle_events"][-1]["regime"] = "cg-stab-pricing"
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError,
                       match="A2 cell contains stabilized"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


@pytest.mark.parametrize("field,value", [
    ("wall_s", None),
    ("lp_wall_s", float("nan")),
    ("wall_s", -0.1),
])
def test_invalid_oracle_wall_evidence_rejected(pilot_roots, tmp_path,
                                               field, value):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a4_s1_n4_b0.01", "a4.cg.ckpt.json")
    ck = checkpoint.load(p)
    ck["oracle_events"][0]["solver"][field] = value
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError,
                       match="missing or nonfinite wall|negative wall"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_invalid_master_wall_evidence_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a3_s1_n4_b0.01", "a3.cg.ckpt.json")
    ck = checkpoint.load(p)
    ev = next(e for e in ck["iteration_events"] if e.get("master_solves"))
    ev["master_solves"][0]["wall_s"] = None
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="missing or nonfinite wall"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)


def test_incomplete_root_fails_audit(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a3_s3_n4_b0.05", "a3.cg.ckpt.json")
    ck = checkpoint.load(p)
    ck["done"] = False
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="audit FAILED"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder,
                verify_code_commit=False)
