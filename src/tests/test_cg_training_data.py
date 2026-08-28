"""ML warm-start training-data emission: adversarial synthetic tests (CBC).

Engineering-tier only. Fast refusal/grid tests plus a single small real
solve (n_trips=4) reused across the emission-quality checks. No cluster,
no Gurobi, no reading of runs/b3_factor_pilot or A6 paths.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

import experiments.emit_cg_training_data as em

REPO_ROOT = em.REPO_ROOT


class _Args:
    def __init__(self, out, **kw):
        self.out = str(out)
        self.mip_gap = kw.get("mip_gap", 1e-6)
        self.time_limit_s = kw.get("time_limit_s", 600.0)
        self.with_dictator = kw.get("with_dictator", True)
        self.per_cell_cpu_h_estimate = kw.get("per_cell_cpu_h_estimate", 0.09)


def _small_cell(n_trips=4):
    return {"seed": 10000, "n_trips": n_trips, "b": 0.0,
            "battery_kwh": 60.0, "charge_power_kw": 150.0,
            "tag": f"s10000_n{n_trips}_b0_bat60_chg150"}


@pytest.fixture(scope="module")
def emitted(tmp_path_factory):
    out = tmp_path_factory.mktemp("cgdata")
    cell = _small_cell()
    path = em.emit_cell(cell, _Args(out))
    record = json.loads(Path(path).read_text())
    ckpt = json.loads((out / cell["tag"] / "a2.cg.ckpt.json").read_text())
    return {"record": record, "path": Path(path), "out": out, "cell": cell,
            "ckpt": ckpt}


# --------------------------------------------------------------------------
# seed namespace
# --------------------------------------------------------------------------
def test_seed_below_floor_refused_by_name():
    for bad in (0, 15, 31, 37, 47, 9999):
        with pytest.raises(em.CGTrainingError, match="below the ML seed floor"):
            em.assert_ml_seed(bad)
    em.assert_ml_seed(10000)
    em.assert_ml_seed(12345)


def test_build_cells_and_instance_refuse_low_seed():
    with pytest.raises(em.CGTrainingError, match="seed floor"):
        em.build_cells(47, 1)
    with pytest.raises(em.CGTrainingError, match="seed floor"):
        em.build_instance({"seed": 100, "n_trips": 8, "battery_kwh": 60.0,
                           "charge_power_kw": 150.0})


def test_main_refuses_low_seed(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", [
        "emit", "--seed-base", "500", "--count", "1", "--list",
        "--out", str(tmp_path / "o")])
    with pytest.raises(em.CGTrainingError, match="seed floor"):
        em.main()


# --------------------------------------------------------------------------
# grid / ordering
# --------------------------------------------------------------------------
def test_grid_deterministic_ordering_and_counts():
    a = em.build_cells(10000, 2)
    b = em.build_cells(10000, 2)
    assert a == b
    assert em.cells_per_seed() == 108
    assert len(a) == 216
    assert a[0]["seed"] == 10000 and a[0]["n_trips"] == 8


def test_dry_run_reports_total_and_estimate(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", [
        "emit", "--seed-base", "10000", "--count", "9", "--dry-run",
        "--out", str(tmp_path / "o")])
    em.main()
    out = capsys.readouterr().out
    assert "total instances: 972" in out
    assert "estimated CPU-hours" in out


# --------------------------------------------------------------------------
# path isolation
# --------------------------------------------------------------------------
def test_refuse_a6_output(tmp_path):
    with pytest.raises(em.CGTrainingError, match="A6"):
        em.refuse_a6_paths(tmp_path / "a6_stuff")


def test_refuse_protected_output():
    with pytest.raises(em.CGTrainingError, match="protected tree"):
        em.refuse_protected_output(REPO_ROOT / "result" / "x")
    with pytest.raises(em.CGTrainingError, match="protected tree"):
        em.refuse_protected_output(REPO_ROOT / "runs" / "b3_factor_pilot" / "x")
    em.refuse_protected_output(REPO_ROOT / "runs" / "cg_training_data")  # ok


def test_default_out_is_not_under_result():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/cg_training_data")
    default = ap.parse_args([]).out
    assert "result" not in default
    assert em.build_cells  # module import sanity


def test_refuse_write_outside_output(tmp_path):
    with pytest.raises(em.CGTrainingError, match="outside the supplied"):
        em.assert_within_output(tmp_path / "out", tmp_path / "elsewhere" / "f")
    em.assert_within_output(tmp_path / "out", tmp_path / "out" / "cell" / "f")


# --------------------------------------------------------------------------
# emitted record quality (single real solve)
# --------------------------------------------------------------------------
def test_record_identity_and_schema(emitted):
    rec = emitted["record"]
    assert rec["schema"] == em.SCHEMA
    assert "engineering" in rec["evidence_tier"]
    idn = rec["identity"]
    assert idn["seed"] == 10000 and idn["n_trips"] == 4
    assert idn["epsilon"] == em.EPSILON and idn["budget"] == em.BUDGET
    assert len(idn["instance_hash"]) == 12  # Instance.hash() width
    assert len(rec["posted_prices"]) == len(rec["rmp_duals_canonical"]["pi"])


def test_reduced_costs_recompute_from_primitives(emitted):
    rec = emitted["record"]
    pi = rec["rmp_duals_canonical"]["pi"]
    sigma = rec["rmp_duals_canonical"]["sigma"]
    assert rec["columns"], "expected committed columns"
    for col in rec["columns"]:
        rc = col["ops_cost"] - float(np.dot(np.asarray(pi),
                                            np.asarray(col["load"]))) - sigma
        assert abs(rc - col["reduced_cost_final"]) < 1e-9


def test_certificate_gap_recomputes(emitted):
    cert = emitted["record"]["certificate"]
    assert cert["certified"] is True
    assert abs(cert["gap"] - (cert["ub_ch"] - cert["lb_best"])) < 1e-9
    assert cert["gap"] <= em.EPSILON + 1e-9


def test_dual_canonicalization_recorded_and_consistent(emitted):
    rec = emitted["record"]
    dc = rec["dual_canonicalization"]
    assert dc["method"] == em.DUAL_CANON_METHOD
    assert dc["n_samples"] == em.DUAL_CANON_SAMPLES == 4
    assert rec["rmp_duals_canonical"]["method"] == em.DUAL_CANON_METHOD
    # never only the last iterate: an averaged representative is emitted
    assert rec["rmp_duals_canonical"]["pi_sample_spread"] >= 0.0


def test_margins_present(emitted):
    rec = emitted["record"]
    assert "column_pool_min_margin" in rec
    for col in rec["columns"]:
        assert "margin_to_pool_min" in col and col["margin_to_pool_min"] >= -1e-9


def test_per_iteration_count_matches_oracle_calls(emitted):
    rec = emitted["record"]
    ckpt = emitted["ckpt"]
    n_events = len(ckpt["oracle_events"])
    assert rec["certificate"]["oracle_calls_total"] == n_events
    priced = [it for it in rec["iterations"] if it["pricing_solve_id"]]
    assert len(priced) == n_events - 1           # seed + one call per priced
    ids = [it["pricing_solve_id"] for it in priced]
    assert len(set(ids)) == len(ids)


def test_resume_is_byte_identical(emitted):
    first = emitted["path"].read_bytes()
    # re-emit into the SAME cell dir: certified_cg returns the committed state
    # and the record re-materializes byte-identically
    again = em.emit_cell(emitted["cell"], _Args(emitted["out"]))
    assert Path(again).read_bytes() == first


def test_dictator_certificate_recorded(emitted):
    dic = emitted["record"]["dictator"]
    assert dic is not None
    assert dic["converged"] is True
    assert abs(dic["gap"] - (dic["z_d_ub"] - dic["z_d_lb"])) < 1e-9


# --------------------------------------------------------------------------
# wall-cap marks incomplete rather than truncating
# --------------------------------------------------------------------------
def test_time_limit_marks_incomplete(tmp_path):
    cell = _small_cell()
    path = em.emit_cell(cell, _Args(tmp_path / "cap", time_limit_s=1e-4,
                                    with_dictator=False))
    rec = json.loads(Path(path).read_text())
    assert rec["incomplete"] is True
    assert rec["incomplete_reason"]
    # a record was still emitted (never silently truncated)
    assert rec["schema"] == em.SCHEMA


# --------------------------------------------------------------------------
# protected A6 files unchanged by this branch
# --------------------------------------------------------------------------
B3_BASE_COMMIT = "ed8b06f"
PROTECTED_A6_FILES = (
    "src/egglab/a6.py", "src/egglab/b2a2.py", "src/egglab/b2a345.py",
    "src/egglab/evsp.py", "src/experiments/run_a6_holdout.py",
    "src/experiments/select_a6_arm.py")


@pytest.mark.parametrize("relpath", PROTECTED_A6_FILES)
def test_protected_a6_files_zero_drift(relpath):
    committed = subprocess.check_output(
        ["git", "show", f"{B3_BASE_COMMIT}:{relpath}"], cwd=REPO_ROOT)
    assert committed == (REPO_ROOT / relpath).read_bytes()
