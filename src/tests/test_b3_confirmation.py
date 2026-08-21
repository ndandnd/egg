"""B3 fresh-seed confirmation stage: GO gate, bindings, audit, refusals.

Adversarial synthetic tests only (no cluster, no Gurobi, no pilot outcomes
read). Everything runs on CBC and asserts emitted values, not source
strings.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import experiments.b3_confirmation as cc
import experiments.audit_b3_confirmation as ad

REPO_ROOT = cc.REPO_ROOT
# HEAD is always an ancestor of itself -> passes the artifact commit-ancestry
ANCESTOR = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).decode().strip()
DEFAULT_FACTOR = "S1_batt_low"


# --------------------------------------------------------------------------
# synthetic GO selection artifact
# --------------------------------------------------------------------------
def artifact(factor=DEFAULT_FACTOR, **over):
    d = {
        "schema": cc.SELECTION_SCHEMA, "campaign": "b3-factor-pilot",
        "state": "GO", "selected_factor": factor,
        "direction_sign": cc.DIRECTION_SIGN[factor],
        "frozen_factor_level": cc.selected_factor_level(factor),
        "baseline_level": 60.0, "zero_excluding_count": 11, "count_gate": 9,
        "signed_median_midpoint": 0.12, "tau_delta": 0.04,
        "pilot": {
            "run_manifest_sha256": "a" * 64,
            "analysis_manifest_sha256": "b" * 64,
            "analysis_code_commit": ANCESTOR,
            "screen_record_sha256": cc.FROZEN_SCREEN_RECORD_SHA256,
            "spec_sha256": cc.FROZEN_SPEC_SHA256,
        },
        "selection_code_commit": ANCESTOR,
        "raw_binding": dict(cc.FROZEN_PILOT_RAW_TREE),
        "boundary_margin": 0.08, "boundary_adjacent": False,
        "signed_median_full_precision": 0.12,
        "confirmation_population": {
            "seeds": list(cc.CONFIRMATION_SEEDS),
            "settings": [cc.BASELINE_SETTING, factor],
            "n_trips": list(cc.N_TRIPS), "b_scales": list(cc.B_SCALES),
            "matched_contrasts": 24, "method_cells": 48,
            "gate": {"min_zero_excluding": 18, "of": 24,
                     "signed_median_exceeds": 0.04},
        },
    }
    d.update(over)
    return d


def write_artifact(tmp_path, doc, name="SELECTION.json"):
    p = Path(tmp_path) / name
    p.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    return p


def load(tmp_path, doc):
    return cc.load_selection_artifact(write_artifact(tmp_path, doc),
                                      verify_commit=True)


# --------------------------------------------------------------------------
# GO gate — happy path and per-field refusals
# --------------------------------------------------------------------------
def test_valid_go_loads(tmp_path):
    sel = load(tmp_path, artifact())
    assert sel["selected_factor"] == DEFAULT_FACTOR
    assert len(sel["sha256"]) == 64


def test_non_go_refused(tmp_path):
    for state in ("NO-GO", "UNDER-RESOLVED", "INVALID/HALT",
                  "DESIGN-NOT-FROZEN"):
        with pytest.raises(cc.B3ConfirmationError, match="not GO"):
            load(tmp_path, artifact(state=state))


def test_boundary_adjacent_refused(tmp_path):
    with pytest.raises(cc.B3ConfirmationError, match="knife-edge"):
        load(tmp_path, artifact(boundary_adjacent=True))


@pytest.mark.parametrize("field,bad", [
    ("tree_sha256", "0" * 64), ("file_count", 362),
    ("directory_count", 59), ("total_bytes", 17385780)])
def test_raw_binding_mismatch_refused(tmp_path, field, bad):
    rb = dict(cc.FROZEN_PILOT_RAW_TREE)
    rb[field] = bad
    with pytest.raises(cc.B3ConfirmationError, match=f"raw_binding.{field}"):
        load(tmp_path, artifact(raw_binding=rb))


@pytest.mark.parametrize("field", [
    "raw_binding", "boundary_margin", "boundary_adjacent",
    "signed_median_full_precision", "selected_factor", "state",
    "direction_sign", "signed_median_midpoint", "pilot",
    "confirmation_population", "selection_code_commit"])
def test_missing_field_refused(tmp_path, field):
    d = artifact()
    del d[field]
    with pytest.raises(cc.B3ConfirmationError, match="missing required field|not GO"):
        load(tmp_path, d)


@pytest.mark.parametrize("field", [
    "run_manifest_sha256", "analysis_manifest_sha256",
    "analysis_code_commit", "screen_record_sha256", "spec_sha256"])
def test_missing_pilot_subfield_refused(tmp_path, field):
    d = artifact()
    del d["pilot"][field]
    with pytest.raises(cc.B3ConfirmationError, match=f"pilot.{field}"):
        load(tmp_path, d)


def test_wrong_screen_sha_refused(tmp_path):
    d = artifact()
    d["pilot"]["screen_record_sha256"] = "c" * 64
    with pytest.raises(cc.B3ConfirmationError, match="screen_record_sha256"):
        load(tmp_path, d)


def test_wrong_spec_sha_refused(tmp_path):
    d = artifact()
    d["pilot"]["spec_sha256"] = "d" * 64
    with pytest.raises(cc.B3ConfirmationError, match="spec_sha256"):
        load(tmp_path, d)


def test_bad_direction_sign_refused(tmp_path):
    with pytest.raises(cc.B3ConfirmationError, match="direction_sign"):
        load(tmp_path, artifact(direction_sign=-1))  # S1 must be +1


def test_median_below_tau_refused(tmp_path):
    with pytest.raises(cc.B3ConfirmationError, match="tau_delta|not a GO"):
        load(tmp_path, artifact(signed_median_midpoint=0.02))


def test_count_below_gate_refused(tmp_path):
    with pytest.raises(cc.B3ConfirmationError, match="below the pilot GO gate"):
        load(tmp_path, artifact(zero_excluding_count=8))


def test_non_ancestor_commit_refused(tmp_path):
    d = artifact()
    d["pilot"]["analysis_code_commit"] = "f" * 40
    with pytest.raises(cc.B3ConfirmationError, match="does not resolve|ancestor"):
        load(tmp_path, d)


@pytest.mark.parametrize("mutate", [
    lambda p: p.__setitem__("seeds", [32, 33, 34, 35, 36, 38]),
    lambda p: p.__setitem__("settings", ["S0_baseline", "S2_batt_high"]),
    lambda p: p.__setitem__("n_trips", [8, 12, 16]),
    lambda p: p.__setitem__("matched_contrasts", 23),
    lambda p: p.__setitem__("method_cells", 47),
    lambda p: p["gate"].__setitem__("min_zero_excluding", 17)])
def test_population_block_drift_refused(tmp_path, mutate):
    d = artifact()   # DEFAULT_FACTOR is S1, so wrong settings pair is drift
    mutate(d["confirmation_population"])
    with pytest.raises(cc.B3ConfirmationError):
        load(tmp_path, d)


def test_no_bypass_hook_exists():
    # the gate takes only (path, verify_commit); verify_commit only softens the
    # SELECTION code-commit ancestry, never the GO/state/binding checks
    import inspect
    sig = inspect.signature(cc.load_selection_artifact)
    assert set(sig.parameters) == {"path", "verify_commit"}


# --------------------------------------------------------------------------
# enumeration / seeds
# --------------------------------------------------------------------------
def test_build_cells_deterministic_and_counts():
    cells = cc.build_cells(DEFAULT_FACTOR)
    assert cells == cc.build_cells(DEFAULT_FACTOR)         # deterministic
    assert len(cells) == 48
    per = {}
    for c in cells:
        per[c["setting"]] = per.get(c["setting"], 0) + 1
    assert per == {"S0_baseline": 24, DEFAULT_FACTOR: 24}
    assert cells[0]["tag"].startswith("S0_baseline_s32")


def test_confirmation_seed_refusals():
    for s in cc.CONFIRMATION_SEEDS:
        cc.assert_confirmation_seed(s)
    for bad in (0, 11, 15):
        with pytest.raises(cc.B3ConfirmationError, match="development"):
            cc.assert_confirmation_seed(bad)
    for bad in (16, 31):
        with pytest.raises(cc.B3ConfirmationError, match="holdout"):
            cc.assert_confirmation_seed(bad)
    for bad in (38, 47, 10000):
        with pytest.raises(cc.B3ConfirmationError, match="confirmation seed"):
            cc.assert_confirmation_seed(bad)


def test_build_instance_refuses_non_confirmation_seed():
    with pytest.raises(cc.B3ConfirmationError):
        cc.build_confirmation_instance(0, 8, 60.0, 150.0)


# --------------------------------------------------------------------------
# outcome blindness + no-launch
# --------------------------------------------------------------------------
def test_refuse_pilot_runs_path():
    with pytest.raises(cc.B3ConfirmationError, match="pilot outcome tree"):
        cc.refuse_pilot_runs_path(REPO_ROOT / "runs" / "b3_factor_pilot")
    with pytest.raises(cc.B3ConfirmationError, match="pilot outcome tree"):
        cc.refuse_pilot_runs_path(
            REPO_ROOT / "runs" / "b3_factor_pilot" / "cell0")
    cc.refuse_pilot_runs_path(REPO_ROOT / "runs" / "b3_confirmation")  # ok


def test_gate_and_manifest_never_read_pilot_runs(tmp_path, monkeypatch):
    opened = []
    real_open = open

    def spy_open(file, *a, **k):
        opened.append(str(file))
        return real_open(file, *a, **k)

    monkeypatch.setattr("builtins.open", spy_open)
    sel = load(tmp_path, artifact())
    cc.build_run_manifest(DEFAULT_FACTOR, sel, git_commit=cc.git_head_commit(),
                          backend_name="GRB")
    assert not any("runs/b3_factor_pilot" in p for p in opened)


def test_driver_list_launches_nothing(tmp_path, monkeypatch):
    sel_path = write_artifact(tmp_path, artifact())
    launch_cmds = {"sbatch", "srun", "salloc", "scancel", "scontrol"}
    seen = []
    real_run = subprocess.run
    real_co = subprocess.check_output

    def spy_run(cmd, *a, **k):
        seen.append(cmd[0] if isinstance(cmd, (list, tuple)) else cmd)
        return real_run(cmd, *a, **k)

    def spy_co(cmd, *a, **k):
        seen.append(cmd[0] if isinstance(cmd, (list, tuple)) else cmd)
        return real_co(cmd, *a, **k)

    monkeypatch.setattr(subprocess, "run", spy_run)
    monkeypatch.setattr(subprocess, "check_output", spy_co)
    import experiments.run_b3_confirmation as drv
    monkeypatch.setattr(sys, "argv",
                        ["run", "--selection-artifact", str(sel_path), "--list"])
    drv.main()
    assert not (set(seen) & launch_cmds)


# --------------------------------------------------------------------------
# synthetic run tree for the audit
# --------------------------------------------------------------------------
MIP_GAP = cc.MIP_GAP_DEFAULT


def _cg_ckpt(ihash, mhash, z_d_ub, ub_ch=100.0, lb_best=100.0,
             certified=True, method="a2"):
    calls = 3
    oe = [{"extra": {"call_id": f"a2-oc{i}"},
           "solver": {"status": "OPTIMAL"}, "replay_ok": True}
          for i in range(calls)]
    it = [{"iteration_id": i, "pricing_solve_id": f"a2-oc{i + 1}"}
          for i in range(calls - 1)]
    return {
        "done": True,
        "identity": {"method": method, "epsilon": cc.EPSILON,
                     "budget": cc.BUDGET, "tol_d": cc.TOL_D,
                     "instance_hash": ihash, "market_hash": mhash,
                     "z_d_ub": z_d_ub,
                     "solver": {"backend": "GRB", "max_mip_gap": MIP_GAP}},
        "oracle_calls": calls, "oracle_events": oe, "iteration_events": it,
        "ub_history": [ub_ch + 2, ub_ch + 1, ub_ch],
        "lb_history": [lb_best - 1, lb_best - 0.5, lb_best],
        "lb_best": lb_best,
        "outcome": {"type": "certified" if certified else "budget_exhausted",
                    "ub_ch": ub_ch, "lb_best": lb_best,
                    "gap": ub_ch - lb_best, "certified": certified,
                    "oracle_calls": calls, "method": method}}


def _dict_ckpt(ihash, mhash, setting, manifest_sha, sel_sha, run_commit,
               z_d_ub, z_d_lb, converged=True, status="OPTIMAL"):
    return {
        "identity": {"instance_hash": ihash, "market_hash": mhash,
                     "screen_record_sha256": cc.FROZEN_SCREEN_RECORD_SHA256,
                     "run_manifest_sha256": manifest_sha,
                     "run_commit": run_commit,
                     "selection_artifact_sha256": sel_sha,
                     "setting": setting, "tol_d": cc.TOL_D,
                     "experiment": "b3-confirmation"},
        "z_d_ub": z_d_ub, "z_d_lb": z_d_lb, "tol_d": cc.TOL_D,
        "status": status,
        "adaptive": {"adaptive_converged": converged, "adaptive_lb": z_d_lb}}


def build_tree(runs, factor=DEFAULT_FACTOR, sel_sha=None, certified_all=True):
    runs = Path(runs)
    run_commit = cc.git_head_commit()
    sel_sha = sel_sha or ("e" * 64)
    manifest = cc.build_run_manifest(
        factor, {"sha256": sel_sha}, git_commit=run_commit,
        backend_name="GRB", mip_gap=MIP_GAP)
    manifest_sha = cc.run_manifest_sha256(manifest)
    cc.write_run_manifest(runs, manifest)
    mbc = cc.market_hash_by_cell(manifest)
    for cell in cc.build_cells(factor):
        key3 = f"{cell['setting']}|{cell['seed']}|{cell['n_trips']}"
        key4 = (cell["setting"], cell["seed"], cell["n_trips"], cell["b"])
        ih = manifest["instance_hashes"][key3]
        mh = mbc[key4]
        cdir = runs / cell["tag"]
        cdir.mkdir(parents=True)
        z = 100.5
        (cdir / "a2.cg.ckpt.json").write_text(json.dumps(
            _cg_ckpt(ih, mh, z, certified=certified_all)))
        (cdir / "dictator.ckpt.json").write_text(json.dumps(
            _dict_ckpt(ih, mh, cell["setting"], manifest_sha, sel_sha,
                       run_commit, z, z)))
        ident = cc.cell_identity(
            cell, manifest, market_hash=mh, instance_hash=ih,
            run_manifest_sha256=manifest_sha, run_commit=run_commit,
            selection_artifact_sha256=sel_sha, mip_gap=MIP_GAP,
            backend_name="GRB")
        (cdir / cc.CELL_IDENTITY_FILENAME).write_bytes(
            cc.canonical_cell_identity_bytes(ident))
    return runs, manifest_sha, sel_sha


def _mutate_cg(runs, tag, fn):
    p = runs / tag / "a2.cg.ckpt.json"
    ck = json.loads(p.read_text()); fn(ck); p.write_text(json.dumps(ck))


def _mutate_dict(runs, tag, fn):
    p = runs / tag / "dictator.ckpt.json"
    dd = json.loads(p.read_text()); fn(dd); p.write_text(json.dumps(dd))


# --------------------------------------------------------------------------
# audit
# --------------------------------------------------------------------------
def test_audit_passes_on_complete_bound_tree(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs")
    r = ad.audit(runs)
    assert r["ok"], r["problems"]
    assert r["certified"] == 48 and r["dictators"] == 48
    assert r["per_setting"] == {"S0_baseline": 24, DEFAULT_FACTOR: 24}


def test_audit_missing_cell_refused(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs")
    import shutil
    shutil.rmtree(runs / cc.build_cells(DEFAULT_FACTOR)[0]["tag"])
    r = ad.audit(runs)
    assert not r["ok"]
    assert any("missing" in p or "48" in p for p in r["problems"])


def test_audit_extra_dir_refused(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs")
    (runs / "S0_baseline_s40_n8_b0.01").mkdir()
    r = ad.audit(runs)
    assert not r["ok"]
    assert any("unexpected cell directory" in p for p in r["problems"])


def test_audit_a6_dir_hard_refused(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs")
    (runs / "a6_stray").mkdir()
    with pytest.raises(cc.B3ConfirmationError, match="A6"):
        ad.audit(runs)


def test_audit_instance_hash_drift_refused(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs")
    tag = cc.build_cells(DEFAULT_FACTOR)[0]["tag"]
    _mutate_cg(runs, tag, lambda ck: ck["identity"].__setitem__(
        "instance_hash", "deadbeef"))
    r = ad.audit(runs)
    assert not r["ok"] and any("instance hash" in p for p in r["problems"])


def test_audit_market_hash_missing_refused(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs")
    tag = cc.build_cells(DEFAULT_FACTOR)[0]["tag"]
    _mutate_cg(runs, tag, lambda ck: ck["identity"].pop("market_hash"))
    r = ad.audit(runs)
    assert not r["ok"] and any("market hash" in p for p in r["problems"])


def test_audit_cg_dictator_zd_mismatch_refused(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs")
    tag = cc.build_cells(DEFAULT_FACTOR)[0]["tag"]
    _mutate_dict(runs, tag, lambda dd: dd.__setitem__("z_d_ub", 123.0))
    r = ad.audit(runs)
    assert not r["ok"] and any("z_d_ub" in p for p in r["problems"])


def test_audit_uncertified_refused(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs", certified_all=False)
    r = ad.audit(runs)
    assert not r["ok"] and any("not certified" in p for p in r["problems"])


def test_audit_budget_overrun_refused(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs")
    tag = cc.build_cells(DEFAULT_FACTOR)[0]["tag"]
    _mutate_cg(runs, tag, lambda ck: ck["identity"].__setitem__("budget", 999))
    r = ad.audit(runs)
    assert not r["ok"] and any("budget" in p for p in r["problems"])


def test_audit_identity_sidecar_mismatch_refused(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs")
    tag = cc.build_cells(DEFAULT_FACTOR)[0]["tag"]
    ipath = runs / tag / cc.CELL_IDENTITY_FILENAME
    ident = json.loads(ipath.read_text())
    ident["run_commit"] = "b" * 40
    ipath.write_bytes(cc.canonical_cell_identity_bytes(ident))
    r = ad.audit(runs)
    assert not r["ok"] and any("sidecar" in p for p in r["problems"])


def test_audit_tampered_manifest_refused(tmp_path):
    runs, _, _ = build_tree(tmp_path / "runs")
    mpath = runs / cc.RUN_MANIFEST_FILENAME
    man = json.loads(mpath.read_text())
    man["market_hashes"][0]["market_hash"] = "0" * 64
    mpath.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
    r = ad.audit(runs)
    assert not r["ok"]
    assert any("byte-for-byte" in p or "tampered" in p for p in r["problems"])


def test_audit_selection_sha_cross_check(tmp_path):
    sel_doc = artifact()
    sel_path = write_artifact(tmp_path, sel_doc)
    sel = cc.load_selection_artifact(sel_path, verify_commit=False)
    runs, _, _ = build_tree(tmp_path / "runs", sel_sha=sel["sha256"])
    assert ad.audit(runs, selection_artifact=sel_path)["ok"]
    # a DIFFERENT artifact SHA is refused
    other = write_artifact(tmp_path, artifact(zero_excluding_count=10),
                           name="OTHER.json")
    r = ad.audit(runs, selection_artifact=other)
    assert not r["ok"]
    assert any("selection artifact SHA" in p for p in r["problems"])


def test_audit_refuses_pilot_runs_path():
    with pytest.raises(cc.B3ConfirmationError, match="pilot outcome tree"):
        ad.audit(REPO_ROOT / "runs" / "b3_factor_pilot")


# --------------------------------------------------------------------------
# run manifest / job binding units
# --------------------------------------------------------------------------
def test_run_manifest_deterministic_and_bound(tmp_path):
    sel = load(tmp_path, artifact())
    m1 = cc.build_run_manifest(DEFAULT_FACTOR, sel,
                               git_commit="c" * 40, backend_name="GRB")
    m2 = cc.build_run_manifest(DEFAULT_FACTOR, sel,
                               git_commit="c" * 40, backend_name="GRB")
    assert cc.run_manifest_sha256(m1) == cc.run_manifest_sha256(m2)
    assert len(m1["instance_hashes"]) == 24
    assert len(m1["market_hashes"]) == 48
    assert m1["selection_artifact_sha256"] == sel["sha256"]


def test_run_manifest_rejects_non_grb(tmp_path):
    sel = load(tmp_path, artifact())
    with pytest.raises(cc.B3ConfirmationError, match="Gurobi-only|not GRB"):
        cc.build_run_manifest(DEFAULT_FACTOR, sel, git_commit="c" * 40,
                              backend_name="CBC")


def test_job_binding_closes_provenance_gap(tmp_path):
    runs, manifest_sha, sel_sha = build_tree(tmp_path / "runs")
    path = cc.bind_job_id(runs, "424242")
    job = json.loads(Path(path).read_text())
    assert job["job_id"] == "424242"
    assert job["run_manifest_sha256"] == manifest_sha
    assert job["selection_artifact_sha256"] == sel_sha
    with pytest.raises(cc.B3ConfirmationError, match="already exists"):
        cc.bind_job_id(runs, "999")


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
