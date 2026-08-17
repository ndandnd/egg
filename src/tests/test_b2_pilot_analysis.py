"""Regression battery for the B2 pilot-closeout pipeline
(experiments/analyze_b2_pilot.py): artifact integrity, matched-join
correctness, identity safeguards, and byte-identical determinism, exercised
on a REAL miniature pilot fixture (actual certified_cg runs + dictator
stages on tiny instances)."""
import json
import os
import shutil
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
)
from experiments.run_b2a2_pilot import _dictator_stage

FIX_INSTANCES = ((1, 4, 0.01), (3, 4, 0.01))
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
                      "codecommit0", instances=FIX_INSTANCES, instance_builder=fix_builder)
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


def test_deterministic_regeneration_byte_identical(pilot_roots, artifacts,
                                                   tmp_path):
    a2_root, a345_root = pilot_roots
    out2 = analyze(a2_root, a345_root, str(tmp_path), "TESTSTAMP",
                   "codecommit0", instances=FIX_INSTANCES, instance_builder=fix_builder)
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
    shutil.rmtree(os.path.join(c345, "a4_s3_n4_b0.01"))
    with pytest.raises(AnalysisError):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder)


def test_unexpected_extra_cell_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    shutil.copytree(os.path.join(c345, "a3_s1_n4_b0.01"),
                    os.path.join(c345, "a3_s9_n4_b0.01"))
    # the audit's expected-count gate fires first; the dedicated extras
    # check is the backstop if counts happen to still match
    with pytest.raises(AnalysisError,
                       match="audit FAILED|unexpected cg checkpoints"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder)


def test_identity_mismatch_rejected(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a5_s1_n4_b0.01", "a5.cg.ckpt.json")
    ck = checkpoint.load(p)
    ck["identity"]["instance_hash"] = "tampered"
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="instance hash mismatch"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder)


def test_incomplete_root_fails_audit(pilot_roots, tmp_path):
    c2, c345 = _clone_roots(pilot_roots, tmp_path)
    p = os.path.join(c345, "a3_s3_n4_b0.01", "a3.cg.ckpt.json")
    ck = checkpoint.load(p)
    ck["done"] = False
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="audit FAILED"):
        analyze(c2, c345, str(tmp_path / "out"), "T", "c",
                instances=FIX_INSTANCES, instance_builder=fix_builder)
