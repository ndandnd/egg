"""Regression battery for the full-population B2 analysis
(experiments/analyze_b2_full.py): exact 3-root union, denominator gates,
computed criteria, two-call cell handling, wall identity, and byte-identical
determinism — exercised on a real miniature 3-root fixture."""
import json
import os
import shutil
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest

from egglab import checkpoint
from egglab.b2a2 import certified_cg
from egglab.instance import synthetic_instance
from experiments.analyze_b2_full import (
    EXPANSION_INSTANCES_FULL,
    FULL_INSTANCES,
    PILOT_INSTANCES_FULL,
    acceptance_full,
    analyze,
    check_denominators,
    check_scientific_contract,
    two_call_report,
)
from experiments.analyze_b2_pilot import (
    AnalysisError,
    PILOT_INSTANCES,
    sha256_file,
)
from experiments.run_b2_expansion import expansion_instances
from experiments.run_b2a2_pilot import _dictator_stage

MINI_PILOT = ((1, 4, 0.01), (1, 4, 0.05))
MINI_EXPANSION = ((3, 4, 0.01), (3, 4, 0.05))
MINI_ALL = MINI_PILOT + MINI_EXPANSION
METHODS = ("a2", "a3", "a4", "a5")


def fix_builder(seed, n_trips):
    return synthetic_instance(seed=seed, n_trips=n_trips, max_vehicles=2)


@pytest.fixture(scope="module")
def full_roots(tmp_path_factory):
    """Miniature 3-root population mirroring the real layout: pilot roots
    (A2 unprefixed, A3-A5 prefixed) for MINI_PILOT, expansion root
    (all methods prefixed) for MINI_EXPANSION."""
    base = tmp_path_factory.mktemp("full")
    roots = {"a2_pilot": str(base / "b2a2_pilot"),
             "a345_pilot": str(base / "b2a345_pilot"),
             "expansion": str(base / "b2_expansion")}
    kw = dict(max_mip_gap=1e-6, time_limit_s=None)
    from egglab.market import make_affine_market
    for (s, n, b) in MINI_ALL:
        inst = fix_builder(s, n)
        market = make_affine_market(inst, shape="duck", b_scale=b)
        for m in METHODS:
            base_name = f"s{s}_n{n}_b{b:g}"
            if (s, n, b) in MINI_PILOT:
                if m == "a2":
                    out = os.path.join(roots["a2_pilot"], base_name)
                else:
                    out = os.path.join(roots["a345_pilot"], f"{m}_{base_name}")
            else:
                out = os.path.join(roots["expansion"], f"{m}_{base_name}")
            os.makedirs(out, exist_ok=True)
            d_state = _dictator_stage(inst, market, out, base_name,
                                      [m, s, n, b], kw)
            experiment = ("b2a2-pilot" if (s, n, b) in MINI_PILOT
                          and m == "a2" else
                          "b2a345-pilot" if (s, n, b) in MINI_PILOT else
                          "b2-expansion")
            certified_cg(inst, market, epsilon=1e-2, budget=240,
                         out_dir=out, tag=m, method=m, solver_kw=kw,
                         experiment=experiment,
                         z_d_ub=d_state["z_d_ub"], tol_d=d_state["tol_d"])
    return roots


def _run(roots, out_base, stamp="TESTSTAMP"):
    return analyze(roots, out_base, stamp, "codecommit0",
                   instances=MINI_ALL, pilot_instances=MINI_PILOT,
                   instance_builder=fix_builder, verify_code_commit=False)


@pytest.fixture(scope="module")
def artifacts(full_roots, tmp_path_factory):
    return _run(full_roots, str(tmp_path_factory.mktemp("result")))


def _clone(full_roots, tmp_path):
    out = {}
    for k, v in full_roots.items():
        dst = str(tmp_path / k)
        shutil.copytree(v, dst)
        out[k] = dst
    return out


# --------------------------------------------------------------------------
# real-grid union mathematics (the production constants)
# --------------------------------------------------------------------------
def test_real_population_union_exact():
    assert len(FULL_INSTANCES) == 64
    assert set(PILOT_INSTANCES_FULL) == set(PILOT_INSTANCES)
    assert len(PILOT_INSTANCES_FULL) == 12
    assert set(EXPANSION_INSTANCES_FULL) == set(expansion_instances())
    assert len(EXPANSION_INSTANCES_FULL) == 52
    assert set(PILOT_INSTANCES_FULL) & set(EXPANSION_INSTANCES_FULL) == set()
    assert (set(PILOT_INSTANCES_FULL) | set(EXPANSION_INSTANCES_FULL)
            == set(FULL_INSTANCES))
    assert sum(1 for i in FULL_INSTANCES if i[2] == 0.05) == 32


# --------------------------------------------------------------------------
# happy path
# --------------------------------------------------------------------------
def test_artifacts_written_and_shaped(artifacts):
    for fn in ("MANIFEST.json", "cells.csv", "matched_comparison.csv",
               "method_summary.csv", "acceptance_status.csv",
               "two_call_cells.csv", "SUMMARY.md",
               "F1_total_calls_by_method.png", "F4_clean_vs_total_calls.png"):
        assert os.path.exists(os.path.join(artifacts, fn)), fn
    cells = pd.read_csv(os.path.join(artifacts, "cells.csv"))
    assert len(cells) == 4 * len(MINI_ALL)
    for m in METHODS:
        assert (cells.method == m).sum() == len(MINI_ALL)
    matched = pd.read_csv(os.path.join(artifacts, "matched_comparison.csv"))
    assert len(matched) == 3 * len(MINI_ALL)


def test_manifest_hashes_all_inputs_and_outputs(artifacts):
    man = json.load(open(os.path.join(artifacts, "MANIFEST.json")))
    assert set(man["inputs"]) == {"a2_pilot", "a345_pilot", "expansion"}
    for key in man["inputs"]:
        assert man["inputs"][key]["files"], key
    for fn, digest in man["outputs"].items():
        assert sha256_file(os.path.join(artifacts, fn)) == digest, fn
    assert man["population"]["method_cells"] == 16


def test_wall_identity_and_a2_purity(artifacts):
    cells = pd.read_csv(os.path.join(artifacts, "cells.csv"))
    resid = (cells["wall_clean_s"] + cells["wall_stab_s"]
             - cells["total_solver_wall_s"]).abs()
    assert (resid <= 1e-6).all()
    a2 = cells[cells.method == "a2"]
    assert (a2["wall_stab_s"] == 0).all()
    assert (a2["oracle_calls_stab"] == 0).all()


def test_acceptance_statuses_computed(artifacts):
    acc = pd.read_csv(os.path.join(artifacts, "acceptance_status.csv"))
    assert set(acc["status"]).issubset({"pass", "fail", "not-testable"})
    assert acc.set_index("criterion_id").loc[
        "acc-4-vs-tatonnement", "status"] == "not-testable"
    # recompute acc-3 and kill-1 from the tables
    summary = pd.read_csv(os.path.join(artifacts, "method_summary.csv"))
    cells = pd.read_csv(os.path.join(artifacts, "cells.csv"))
    ov = summary[summary["scope"] == "overall"].set_index("method")
    speedup = float(ov.loc["a2", "calls_median"]) / min(
        float(ov.loc[m, "calls_median"]) for m in ("a3", "a4", "a5"))
    a2_rate = cells[(cells.method == "a2")
                    & (cells.b == 0.05)]["certified"].mean()
    ai = acc.set_index("criterion_id")
    assert ai.loc["acc-3-stab-beats-a2-2x", "status"] == (
        "pass" if speedup >= 2 else "fail")
    assert ai.loc["kill-1-a2-meets-bar", "status"] == (
        "pass" if (a2_rate >= 0.95 and speedup < 2) else "fail")


def test_acceptance_labels_flip_with_data(artifacts):
    cells = pd.read_csv(os.path.join(artifacts, "cells.csv"))
    summary = pd.read_csv(os.path.join(artifacts, "method_summary.csv"))
    flipped = summary.copy()
    mask = (flipped["scope"] == "overall") & (flipped["method"] == "a2")
    flipped.loc[mask, "calls_median"] *= 10
    acc = acceptance_full(cells, flipped, expected_b005=2,
                          expected_matched=4).set_index("criterion_id")
    assert acc.loc["acc-3-stab-beats-a2-2x", "status"] == "pass"
    assert acc.loc["kill-1-a2-meets-bar", "status"] == "fail"


def test_deterministic_regeneration(full_roots, artifacts, tmp_path):
    out2 = _run(full_roots, str(tmp_path))
    for fn in ("cells.csv", "matched_comparison.csv", "method_summary.csv",
               "acceptance_status.csv", "two_call_cells.csv", "SUMMARY.md"):
        assert (open(os.path.join(artifacts, fn), "rb").read()
                == open(os.path.join(out2, fn), "rb").read()), fn


# --------------------------------------------------------------------------
# denominator gates
# --------------------------------------------------------------------------
def test_denominator_gate_rejects_wrong_counts(artifacts):
    cells = pd.read_csv(os.path.join(artifacts, "cells.csv"))
    check_denominators(cells, expected_b005_per_method=2,
                       expected_matched_per_method=4)  # correct: no raise
    with pytest.raises(AnalysisError, match="denominator error"):
        check_denominators(cells, expected_b005_per_method=32,
                           expected_matched_per_method=4)
    with pytest.raises(AnalysisError, match="denominator error"):
        check_denominators(cells, expected_b005_per_method=2,
                           expected_matched_per_method=64)


# --------------------------------------------------------------------------
# two-call cells: verified and reported, never filtered
# --------------------------------------------------------------------------
def _fake_row(**over):
    row = {"method": "a2", "seed": 7, "n_trips": 8, "b": 0.01,
           "outcome": "certified", "certified": True, "final_gap": 1e-3,
           "oracle_calls": 2, "oracle_calls_clean": 2,
           "oracle_calls_stab": 0, "n_columns": 2, "uplift_lo": 0.0,
           "uplift_hi": 0.02, "zd_minus_lb": 0.01, "epsilon": 0.01,
           "budget": 240, "tol_d": 0.01}
    row.update(over)
    return row


def test_two_call_cells_verified_and_reported():
    cells = pd.DataFrame([_fake_row(),
                          _fake_row(seed=8, oracle_calls=14,
                                    oracle_calls_clean=14)])
    rep = two_call_report(cells)
    assert len(rep) == 1 and rep.iloc[0]["seed"] == 7
    assert bool(rep.iloc[0]["identity_verified"])
    assert len(cells) == 2  # nothing filtered from the population


def test_two_call_uncertified_is_incoherent():
    cells = pd.DataFrame([_fake_row(certified=False,
                                    outcome="budget_exhausted")])
    with pytest.raises(AnalysisError, match="NOT certified"):
        two_call_report(cells)


def test_two_call_with_stab_calls_is_impossible():
    cells = pd.DataFrame([_fake_row(oracle_calls_stab=1,
                                    oracle_calls_clean=1)])
    with pytest.raises(AnalysisError, match="stabilized calls"):
        two_call_report(cells)


def test_one_call_cell_cannot_masquerade_as_two_call():
    cells = pd.DataFrame([_fake_row(oracle_calls=1,
                                    oracle_calls_clean=1)])
    with pytest.raises(AnalysisError, match="exactly seed"):
        two_call_report(cells)


def test_scientific_contract_rejects_mixed_settings():
    cells = pd.DataFrame([_fake_row(), _fake_row(seed=8)])
    check_scientific_contract(cells)
    cells.loc[1, "budget"] = 120
    with pytest.raises(AnalysisError, match="scientific-contract error"):
        check_scientific_contract(cells)


# --------------------------------------------------------------------------
# adversarial union failures
# --------------------------------------------------------------------------
def test_overlap_between_roots_rejected(full_roots, tmp_path):
    roots = _clone(full_roots, tmp_path)
    # the same cell served by two roots: copy an expansion cell into the
    # pilot a345 root
    shutil.copytree(os.path.join(roots["expansion"], "a3_s3_n4_b0.01"),
                    os.path.join(roots["a345_pilot"], "a3_s3_n4_b0.01"))
    with pytest.raises(AnalysisError,
                       match="audit FAILED|unexpected cg checkpoints"):
        _run(roots, str(tmp_path / "out"))


def test_gap_missing_cell_rejected(full_roots, tmp_path):
    roots = _clone(full_roots, tmp_path)
    shutil.rmtree(os.path.join(roots["expansion"], "a4_s3_n4_b0.05"))
    with pytest.raises(AnalysisError, match="audit FAILED|missing cell"):
        _run(roots, str(tmp_path / "out"))


def test_hash_mismatch_rejected(full_roots, tmp_path):
    roots = _clone(full_roots, tmp_path)
    p = os.path.join(roots["expansion"], "a5_s3_n4_b0.01",
                     "a5.cg.ckpt.json")
    ck = checkpoint.load(p)
    ck["identity"]["instance_hash"] = "tampered"
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="instance hash mismatch"):
        _run(roots, str(tmp_path / "out"))


def test_experiment_lineage_mismatch_rejected(full_roots, tmp_path):
    roots = _clone(full_roots, tmp_path)
    p = os.path.join(roots["expansion"], "a5_s3_n4_b0.01",
                     "a5.cg.ckpt.json")
    ck = checkpoint.load(p)
    for event in ck["oracle_events"]:
        event["experiment"] = "wrong-campaign"
    checkpoint.save(p, ck)
    with pytest.raises(AnalysisError, match="experiment lineage"):
        _run(roots, str(tmp_path / "out"))


def test_code_commit_verification_active(full_roots, tmp_path):
    with pytest.raises(AnalysisError, match="cannot resolve|code commit mismatch"):
        analyze(full_roots, str(tmp_path), "T",
                "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
                instances=MINI_ALL, pilot_instances=MINI_PILOT,
                instance_builder=fix_builder, verify_code_commit=True)
