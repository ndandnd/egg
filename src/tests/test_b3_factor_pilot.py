"""Launcher-ready B3 factor pilot: frozen binding, refusals, exact-count
audit, and the preregistered decision taxonomy.

Covers the driver library (``experiments.b3_factor_pilot``), the exact-count
audit (``experiments.audit_b3_factor_pilot``), and the preregistered
analyzer (``experiments.analyze_b3_factor_pilot``) with adversarial tamper
cases, plus the protected-A6-file zero-drift gate. No optimizer is invoked
and no outcome artifact is generated: cells are synthetic fixtures.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import experiments.analyze_b3_factor_pilot as az
import experiments.audit_b3_factor_pilot as ad
import experiments.b3_factor_pilot as bp

REPO_ROOT = bp.REPO_ROOT
DRIVER = REPO_ROOT / "src" / "experiments" / "run_b3_factor_pilot.py"

# Clean base this branch integrates (origin/main tip with PR #35 merged).
B3_PILOT_BASE_COMMIT = "ac417a6"
PROTECTED_A6_FILES = (
    "src/egglab/a6.py",
    "src/egglab/b2a2.py",
    "src/egglab/b2a345.py",
    "src/egglab/evsp.py",
    "src/experiments/run_a6_holdout.py",
    "src/experiments/select_a6_arm.py",
)


@pytest.fixture(scope="module")
def screen():
    return bp.load_frozen_screen()


# --------------------------------------------------------------------------
# fixtures: synthetic sane checkpoints (no solver)
# --------------------------------------------------------------------------
RUN_COMMIT = "a" * 40
MIP_GAP = bp.MIP_GAP_DEFAULT


def _cg_ckpt(ihash, mhash, z_d_ub, ub_ch=100.0, lb_best=100.0, certified=True,
             method="a2", eps=bp.EPSILON):
    """A complete, ``_cg_sane``-passing A2 checkpoint bound to ``ihash`` /
    ``mhash`` with the CG->dictator ``z_d_ub`` recorded in identity."""
    calls = 3
    oe = [{"extra": {"call_id": f"a2-oc{i}"},
           "solver": {"status": "OPTIMAL"}, "replay_ok": True}
          for i in range(calls)]
    it = [{"iteration_id": i, "pricing_solve_id": f"a2-oc{i + 1}"}
          for i in range(calls - 1)]
    ub = [ub_ch + 2.0, ub_ch + 1.0, ub_ch]
    lb = [lb_best - 1.0, lb_best - 0.5, lb_best]
    otype = "certified" if certified else "budget_exhausted"
    return {
        "done": True,
        "identity": {"method": method, "epsilon": eps, "budget": bp.BUDGET,
                     "tol_d": bp.TOL_D, "instance_hash": ihash,
                     "market_hash": mhash, "z_d_ub": z_d_ub,
                     "solver": {"backend": "GRB", "max_mip_gap": MIP_GAP}},
        "oracle_calls": calls, "oracle_events": oe, "iteration_events": it,
        "ub_history": ub, "lb_history": lb, "lb_best": lb_best,
        "outcome": {"type": otype, "ub_ch": ub_ch, "lb_best": lb_best,
                    "gap": ub_ch - lb_best, "certified": certified,
                    "oracle_calls": calls, "method": method},
    }


def _dict_ckpt(ihash, mhash, screen_sha, setting, manifest_sha, z_d_ub, z_d_lb,
               converged=True, status="OPTIMAL"):
    return {
        "identity": {"instance_hash": ihash, "market_hash": mhash,
                     "screen_record_sha256": screen_sha,
                     "run_manifest_sha256": manifest_sha,
                     "run_commit": RUN_COMMIT, "setting": setting,
                     "tol_d": bp.TOL_D, "experiment": "b3-factor-pilot"},
        "z_d_ub": z_d_ub, "z_d_lb": z_d_lb, "tol_d": bp.TOL_D,
        "status": status,
        "adaptive": {"adaptive_converged": converged, "adaptive_lb": z_d_lb},
    }


def _write_tree(runs, screen, *, u_by_setting=None, certified_all=True):
    """Write a full 60-cell synthetic run tree bound to the frozen screen, the
    canonical run manifest, and per-cell identity sidecars.

    ``u_by_setting`` maps a setting to its (constant) certified uplift U;
    defaults to 0.5 SEK everywhere (all matched contrasts zero)."""
    runs = Path(runs)
    manifest = bp.build_run_manifest(
        screen, git_commit=RUN_COMMIT, backend_name="GRB", mip_gap=MIP_GAP)
    manifest_sha = bp.run_manifest_sha256(manifest)
    bp.write_run_manifest(runs, manifest)
    mbc = bp.market_hash_by_cell(manifest)
    for cell in bp.build_cells():
        setting = cell["setting"]
        u = 0.5 if u_by_setting is None else u_by_setting[setting]
        key3 = (setting, cell["seed"], cell["n_trips"])
        key4 = (setting, cell["seed"], cell["n_trips"], cell["b"])
        ihash = screen["instance_hashes"][key3]
        mhash = mbc[key4]
        cdir = runs / cell["tag"]
        cdir.mkdir(parents=True)
        ub_ch = lb_best = 100.0
        z_d = ub_ch + u
        (cdir / "a2.cg.ckpt.json").write_text(json.dumps(
            _cg_ckpt(ihash, mhash, z_d, ub_ch, lb_best,
                     certified=certified_all)))
        (cdir / "dictator.ckpt.json").write_text(json.dumps(
            _dict_ckpt(ihash, mhash, screen["record_sha256"], setting,
                       manifest_sha, z_d, z_d)))
        identity = bp.cell_identity(
            cell, screen, market_hash=mhash, run_manifest_sha256=manifest_sha,
            run_commit=RUN_COMMIT, mip_gap=MIP_GAP, backend_name="GRB")
        (cdir / bp.CELL_IDENTITY_FILENAME).write_bytes(
            bp.canonical_cell_identity_bytes(identity))
    return runs


def _mutate_cg(runs, tag, fn):
    p = runs / tag / "a2.cg.ckpt.json"
    ck = json.loads(p.read_text())
    fn(ck)
    p.write_text(json.dumps(ck))


def _mutate_dict(runs, tag, fn):
    p = runs / tag / "dictator.ckpt.json"
    dd = json.loads(p.read_text())
    fn(dd)
    p.write_text(json.dumps(dd))


# --------------------------------------------------------------------------
# frozen-screen binding
# --------------------------------------------------------------------------
def test_frozen_screen_loads_and_binds(screen):
    assert screen["record_sha256"] == bp.FROZEN_SCREEN_RECORD_SHA256
    assert len(screen["instance_hashes"]) == bp.N_PHYSICAL_INSTANCES
    assert bp.counts()["cells"] == 60
    cells = bp.build_cells()
    assert len(cells) == 60
    assert len({c["tag"] for c in cells}) == 60
    per_setting = {s: 0 for s in bp.SETTING_ORDER}
    for c in cells:
        per_setting[c["setting"]] += 1
    assert all(v == 12 for v in per_setting.values())


def test_factor_drift_gate_all_30(screen):
    bp.assert_no_factor_drift(screen)  # every hash matches; no raise


def _screen_copy(tmp_path, mutate=None):
    dst = tmp_path / "screen"
    dst.mkdir()
    src = Path(bp.REPO_ROOT / bp.FROZEN_SCREEN_RELDIR)
    record = json.loads((src / "SCREEN_RECORD.json").read_bytes())
    manifest = json.loads((src / "MANIFEST.json").read_bytes())
    if mutate:
        record, manifest = mutate(record, manifest)
    rb = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
    (dst / "SCREEN_RECORD.json").write_bytes(rb)
    import hashlib
    # keep the manifest hash honest unless the mutation set it explicitly
    if manifest.get("outputs", {}).get("SCREEN_RECORD.json") == \
            json.loads((src / "MANIFEST.json").read_bytes())["outputs"][
                "SCREEN_RECORD.json"]:
        manifest.setdefault("outputs", {})["SCREEN_RECORD.json"] = \
            hashlib.sha256(rb).hexdigest()
    (dst / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return dst


def test_mutated_record_manifest_hash_refused(tmp_path):
    def mutate(record, manifest):
        record["disposition"]["levels"]["S1_batt_low"] = 44.0
        # freeze the manifest hash to the ORIGINAL so it no longer matches
        return record, manifest
    dst = _screen_copy(tmp_path, mutate)
    # force a stale manifest hash by rewriting it to the original bytes' hash
    manifest = json.loads((dst / "MANIFEST.json").read_bytes())
    manifest["outputs"]["SCREEN_RECORD.json"] = "0" * 64
    (dst / "MANIFEST.json").write_text(json.dumps(manifest))
    with pytest.raises(bp.B3PilotError, match="MANIFEST output hash"):
        bp.load_frozen_screen(dst)


def test_non_frozen_disposition_refused(tmp_path):
    def mutate(record, manifest):
        record["disposition"]["state"] = "DESIGN-NOT-FROZEN"
        return record, manifest
    dst = _screen_copy(tmp_path, mutate)
    with pytest.raises(bp.B3PilotError, match="not FROZEN"):
        bp.load_frozen_screen(dst)


def test_selected_level_drift_refused(tmp_path):
    def mutate(record, manifest):
        record["selected_levels"]["S2_batt_high"] = 91.0
        record["disposition"]["levels"]["S2_batt_high"] = 91.0
        return record, manifest
    dst = _screen_copy(tmp_path, mutate)
    with pytest.raises(bp.B3PilotError, match="factor drift refused"):
        bp.load_frozen_screen(dst)


def test_screen_schema_drift_refused(tmp_path):
    def mutate(record, manifest):
        record["schema"] = "b3-factor-screen-v2"
        return record, manifest
    dst = _screen_copy(tmp_path, mutate)
    with pytest.raises(bp.B3PilotError, match="schema mismatch"):
        bp.load_frozen_screen(dst)


# --------------------------------------------------------------------------
# scientific-boundary refusals
# --------------------------------------------------------------------------
def test_development_seed_refusals():
    for seed in bp.SEEDS:
        bp.assert_development_seed(seed)
    for bad in (16, 20, 31):
        with pytest.raises(bp.B3PilotError, match="reserved band"):
            bp.assert_development_seed(bad)


def test_confirmation_seeds_refused():
    for seed in bp.CONFIRMATION_SEEDS:
        with pytest.raises(bp.B3PilotError, match="confirmation"):
            bp.assert_development_seed(seed)


def test_a6_method_and_path_refused():
    for label in ("a6", "a6_holdout", "A6-recovery"):
        with pytest.raises(bp.B3PilotError, match="A6"):
            bp.assert_no_a6(label)
    with pytest.raises(bp.B3PilotError, match="A6 path"):
        bp.assert_no_a6("runs/a6_holdout/cell0")
    with pytest.raises(bp.B3PilotError, match="A6"):
        bp.assert_method_a2("a6")


def test_method_not_a2_refused():
    with pytest.raises(bp.B3PilotError, match="not A2"):
        bp.assert_method_a2("a3")
    bp.assert_method_a2("a2")


def test_non_grb_backend_refused(monkeypatch):
    import egglab.solver as solver
    monkeypatch.setattr(solver, "backend", lambda: "CBC")
    with pytest.raises(bp.B3PilotError, match="non-GRB"):
        bp.assert_grb_backend()
    monkeypatch.setattr(solver, "backend", lambda: "GRB")
    bp.assert_grb_backend()


def test_dirty_tracked_tree_refused(monkeypatch):
    monkeypatch.setattr(bp.subprocess, "check_output",
                        lambda *a, **k: b" M src/egglab/instance.py\n")
    with pytest.raises(bp.B3PilotError, match="dirty|tracked modifications"):
        bp.assert_clean_tracked_tree()
    monkeypatch.setattr(bp.subprocess, "check_output",
                        lambda *a, **k: b"?? runs/new\n")
    bp.assert_clean_tracked_tree()  # untracked is fine


def test_cell_factor_drift_detected(screen):
    cell = {"setting": "S1_batt_low", "seed": 0, "n_trips": 8, "b": 0.01,
            "battery_kwh": 60.0, "charge_power_kw": 150.0,  # wrong (baseline)
            "tag": "x"}
    with pytest.raises(bp.B3PilotError, match="factor drift"):
        bp.make_cell_instance(cell)


# --------------------------------------------------------------------------
# driver preflight (subprocess)
# --------------------------------------------------------------------------
def _run_driver(*args):
    return subprocess.run(
        [sys.executable, str(DRIVER), *args],
        cwd=str(REPO_ROOT / "src"), capture_output=True, text=True)


def test_driver_list_reports_exactly_60():
    r = _run_driver("--list")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == "total: 60 cells"


def test_driver_dry_run_binds_and_reports():
    r = _run_driver("--dry-run")
    assert r.returncode == 0, r.stderr
    assert "factor-drift gate: PASS" in r.stdout
    assert "cells=60" in r.stdout
    assert "OK" in r.stdout


# --------------------------------------------------------------------------
# exact-count + binding audit
# --------------------------------------------------------------------------
def test_audit_passes_on_complete_bound_tree(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    result = ad.audit(runs, screen_dir=None)
    assert result["ok"], result["problems"]
    assert result["certified"] == 60 and result["dictators"] == 60


def test_audit_missing_cell_refused(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    import shutil
    shutil.rmtree(runs / bp.build_cells()[0]["tag"])
    result = ad.audit(runs, screen_dir=None)
    assert not result["ok"]
    assert any("missing" in p or "60" in p for p in result["problems"])


def test_audit_extra_dir_refused(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    (runs / "S0_baseline_s0_n99_bXX").mkdir()
    result = ad.audit(runs, screen_dir=None)
    assert not result["ok"]
    assert any("unexpected cell directory" in p for p in result["problems"])


def test_audit_a6_dir_hard_refused(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    (runs / "a6_stray").mkdir()
    with pytest.raises(bp.B3PilotError, match="A6"):
        ad.audit(runs, screen_dir=None)


def test_audit_instance_hash_drift_refused(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    ck = json.loads((runs / tag / "a2.cg.ckpt.json").read_text())
    ck["identity"]["instance_hash"] = "deadbeef"
    (runs / tag / "a2.cg.ckpt.json").write_text(json.dumps(ck))
    result = ad.audit(runs, screen_dir=None)
    assert not result["ok"]
    assert any("instance hash" in p and "drift" in p
               for p in result["problems"])


def test_audit_a6_method_hard_refused(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    ck = json.loads((runs / tag / "a2.cg.ckpt.json").read_text())
    ck["identity"]["method"] = "a6_holdout"
    (runs / tag / "a2.cg.ckpt.json").write_text(json.dumps(ck))
    with pytest.raises(bp.B3PilotError, match="A6 method"):
        ad.audit(runs, screen_dir=None)


def test_audit_uncertified_refused(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen, certified_all=False)
    result = ad.audit(runs, screen_dir=None)
    assert not result["ok"]
    assert any("not certified" in p for p in result["problems"])


# --------------------------------------------------------------------------
# exploit regressions (each was accepted before the provenance/integrity fix;
# each must now be rejected, and a clean rebuild must pass)
# --------------------------------------------------------------------------
def test_exploit_missing_market_hash(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    _mutate_cg(runs, tag, lambda ck: ck["identity"].pop("market_hash"))
    a = ad.audit(runs, screen_dir=None)
    assert not a["ok"] and any("market hash" in p for p in a["problems"])
    # repaired
    runs2 = _write_tree(tmp_path / "runs2", screen)
    assert ad.audit(runs2, screen_dir=None)["ok"]


def test_exploit_altered_outcome_lb_best(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    _mutate_cg(runs, tag,
               lambda ck: ck["outcome"].__setitem__("lb_best", 42.0))
    a = ad.audit(runs, screen_dir=None)
    assert not a["ok"]
    # analyzer independently rejects the single-field edit too
    out = az.analyze(runs, tmp_path / "out", "s1", "0" * 40,
                     screen_dir=None, verify_code_commit=False)
    man = json.loads((Path(out) / "MANIFEST.json").read_text())
    assert man["decision"]["state"] == "INVALID/HALT"


def test_exploit_altered_dictator_z_d_ub(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    _mutate_dict(runs, tag, lambda dd: dd.__setitem__("z_d_ub", 123.0))
    a = ad.audit(runs, screen_dir=None)
    assert not a["ok"]
    assert any("z_d_ub" in p for p in a["problems"])


def test_exploit_altered_dictator_z_d_lb(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    _mutate_dict(runs, tag, lambda dd: dd.__setitem__("z_d_lb", 77.0))
    a = ad.audit(runs, screen_dir=None)
    assert not a["ok"]
    assert any("z_d_lb" in p for p in a["problems"])


def test_exploit_mismatched_cg_identity_z_d_ub(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    _mutate_cg(runs, tag,
               lambda ck: ck["identity"].__setitem__("z_d_ub", 999.0))
    a = ad.audit(runs, screen_dir=None)
    assert not a["ok"]
    assert any("z_d_ub" in p for p in a["problems"])


def test_exploit_tampered_manifest(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    mpath = runs / bp.RUN_MANIFEST_FILENAME
    man = json.loads(mpath.read_text())
    man["market_hashes"][0]["market_hash"] = "0" * 64
    mpath.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
    a = ad.audit(runs, screen_dir=None)
    assert not a["ok"]
    assert any("byte-for-byte" in p or "tampered" in p for p in a["problems"])


def test_exploit_wrong_run_commit_in_sidecar(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    ipath = runs / tag / bp.CELL_IDENTITY_FILENAME
    ident = json.loads(ipath.read_text())
    ident["run_commit"] = "b" * 40
    ipath.write_bytes(bp.canonical_cell_identity_bytes(ident))
    a = ad.audit(runs, screen_dir=None)
    assert not a["ok"]
    assert any("cell-identity sidecar" in p for p in a["problems"])


def test_exploit_wrong_manifest_sha_in_dictator(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    _mutate_dict(runs, tag,
                 lambda dd: dd["identity"].__setitem__(
                     "run_manifest_sha256", "0" * 64))
    a = ad.audit(runs, screen_dir=None)
    assert not a["ok"]
    assert any("run-manifest SHA" in p for p in a["problems"])


def test_analyzer_requires_audit_pass(tmp_path, screen):
    # an analyzer run on a tree that fails audit must be INVALID/HALT, never a
    # scored decision.
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    _mutate_dict(runs, tag, lambda dd: dd.__setitem__("z_d_lb", 77.0))
    out = az.analyze(runs, tmp_path / "out", "s2", "0" * 40,
                     screen_dir=None, verify_code_commit=False)
    man = json.loads((Path(out) / "MANIFEST.json").read_text())
    assert man["decision"]["state"] == "INVALID/HALT"


# --------------------------------------------------------------------------
# run-manifest + cell-identity sidecar unit behavior
# --------------------------------------------------------------------------
def test_run_manifest_deterministic_and_bound(screen):
    m1 = bp.build_run_manifest(screen, git_commit="c" * 40,
                               backend_name="GRB", mip_gap=1e-6)
    m2 = bp.build_run_manifest(screen, git_commit="c" * 40,
                               backend_name="GRB", mip_gap=1e-6)
    assert bp.run_manifest_sha256(m1) == bp.run_manifest_sha256(m2)
    assert len(m1["instance_hashes"]) == 30 and len(m1["market_hashes"]) == 60
    assert m1["screen"]["record_sha256"] == screen["record_sha256"]
    assert m1["tolerances"]["tau_delta"] == bp.TAU_DELTA


def test_run_manifest_rejects_non_grb(screen):
    with pytest.raises(bp.B3PilotError, match="Gurobi-only|not GRB"):
        bp.build_run_manifest(screen, git_commit="c" * 40,
                              backend_name="CBC", mip_gap=1e-6)


def test_cell_identity_resume_refuses_drift(tmp_path, screen):
    cell = bp.build_cells()[0]
    m = bp.build_run_manifest(screen, git_commit=RUN_COMMIT,
                              backend_name="GRB", mip_gap=MIP_GAP)
    sha = bp.run_manifest_sha256(m)
    mbc = bp.market_hash_by_cell(m)
    key4 = (cell["setting"], cell["seed"], cell["n_trips"], cell["b"])
    ident = bp.cell_identity(cell, screen, market_hash=mbc[key4],
                             run_manifest_sha256=sha, run_commit=RUN_COMMIT,
                             mip_gap=MIP_GAP, backend_name="GRB")
    d = tmp_path / "cell"
    d.mkdir()
    bp.verify_or_write_cell_identity(d, ident)      # first write
    bp.verify_or_write_cell_identity(d, ident)      # idempotent resume
    drifted = dict(ident, run_commit="d" * 40)
    with pytest.raises(bp.B3PilotError, match="cell identity mismatch"):
        bp.verify_or_write_cell_identity(d, drifted)


def test_assert_fresh_run_dir(tmp_path, screen):
    out = tmp_path / "runs"
    bp.assert_fresh_run_dir(out)                      # missing dir is fine
    out.mkdir()
    bp.assert_fresh_run_dir(out)                      # empty dir is fine
    (out / bp.RUN_MANIFEST_FILENAME).write_text("{}")
    bp.assert_fresh_run_dir(out)                      # lone manifest reusable
    # JOB.json refuses
    (out / bp.JOB_FILENAME).write_text("{}")
    with pytest.raises(bp.B3PilotError, match="JOB.json already exists"):
        bp.assert_fresh_run_dir(out)
    (out / bp.JOB_FILENAME).unlink()
    # any extra file alongside MANIFEST.json refuses
    stray = out / "notes.txt"
    stray.write_text("x")
    with pytest.raises(bp.B3PilotError, match="unexpected entry"):
        bp.assert_fresh_run_dir(out)
    stray.unlink()
    # a cell directory refuses
    cell = out / "S0_baseline_s0_n8_b0.01"
    cell.mkdir()
    with pytest.raises(bp.B3PilotError, match="existing cell directory"):
        bp.assert_fresh_run_dir(out)
    cell.rmdir()
    # a symlink named MANIFEST.json refuses (must be a regular file)
    (out / bp.RUN_MANIFEST_FILENAME).unlink()
    target = tmp_path / "real_manifest.json"
    target.write_text("{}")
    os.symlink(target, out / bp.RUN_MANIFEST_FILENAME)
    with pytest.raises(bp.B3PilotError, match="symlink or not a regular file"):
        bp.assert_fresh_run_dir(out)


def test_job_binding_closes_provenance_gap(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    path = bp.bind_job_id(runs, "123456")
    job = json.loads(Path(path).read_text())
    assert job["job_id"] == "123456"
    assert job["run_commit"] == RUN_COMMIT
    assert job["run_manifest_sha256"] == bp.load_run_manifest(runs)["sha256"]
    with pytest.raises(bp.B3PilotError, match="already exists"):
        bp.bind_job_id(runs, "999")


# --------------------------------------------------------------------------
# preregistered decision taxonomy (analyze_population, direct)
# --------------------------------------------------------------------------
def _pop(delta_by_setting):
    """Build a valid population where every cell's U is a point; the matched
    contrast for setting f equals ``delta_by_setting[f][i]`` on market cell i."""
    market_keys = [(s, n, b) for s in bp.SEEDS for n in bp.N_TRIPS
                   for b in bp.B_SCALES]
    assert len(market_keys) == 12
    cells = {}
    for setting in bp.SETTING_ORDER:
        for i, (s, n, b) in enumerate(market_keys):
            if setting == "S0_baseline":
                u = 0.5
            else:
                u = 0.5 + delta_by_setting[setting][i]
            iv = {"U_lo_raw": u, "U_lo": max(0.0, u), "U_hi": u,
                  "width": 0.0}
            cells[(setting, s, n, b)] = {"cell": {}, "interval": iv}
    return {"cells": cells, "problems": []}


def test_decision_go(screen):
    deltas = {"S1_batt_low": [0.1] * 12, "S2_batt_high": [0.0] * 12,
              "S3_pow_low": [0.0] * 12, "S4_pow_high": [0.0] * 12}
    res = az.analyze_population(_pop(deltas))
    dec = res["decision"]
    assert dec["state"] == "GO"
    assert dec["selected_contrast"] == "S1_batt_low"
    assert dec["count"] == 12 and dec["signed_median_midpoint"] > az.TAU_DELTA


def test_decision_under_resolved():
    deltas = {k: [0.0] * 12 for k in az.FACTOR_ORDER}
    res = az.analyze_population(_pop(deltas))
    assert res["decision"]["state"] == "UNDER-RESOLVED"


def test_decision_no_go_count_short():
    # med > tau but only 7/12 zero-excluding -> NO-GO
    s1 = [0.1] * 7 + [0.0] * 5
    deltas = {"S1_batt_low": s1, "S2_batt_high": [0.0] * 12,
              "S3_pow_low": [0.0] * 12, "S4_pow_high": [0.0] * 12}
    res = az.analyze_population(_pop(deltas))
    dec = res["decision"]
    assert dec["state"] == "NO-GO"
    assert dec["selected_contrast"] == "S1_batt_low" and dec["count"] == 7


def test_decision_no_go_wrong_direction():
    # S3 (non-negative direction) but every contrast points strongly negative
    deltas = {"S1_batt_low": [0.0] * 12, "S2_batt_high": [0.0] * 12,
              "S3_pow_low": [-0.1] * 12, "S4_pow_high": [0.0] * 12}
    res = az.analyze_population(_pop(deltas))
    dec = res["decision"]
    # S3 has count 0 like the others; selection ties on count then median.
    # Its signed median is -0.1 (against direction); others are 0, so f* is a
    # zero-median setting and the state is UNDER-RESOLVED. Assert the wrong
    # direction is at least reflected in S3's signed median.
    assert res["settings"]["S3_pow_low"]["signed_median_midpoint"] < -az.TAU_DELTA
    assert dec["state"] in ("UNDER-RESOLVED", "NO-GO")


def test_decision_wrong_direction_no_go_selected():
    # Force f* = S2 while its signed median points AGAINST its non-positive
    # direction (a positive contrast), all counts tie at zero.
    deltas = {"S1_batt_low": [-0.2] * 12, "S2_batt_high": [0.1] * 12,
              "S3_pow_low": [-0.2] * 12, "S4_pow_high": [0.2] * 12}
    # signed medians: S1 -0.2, S2 -1*(+0.1)=-0.1, S3 -0.2, S4 -1*(+0.2)=-0.2.
    # All counts 0 (none direction-consistent zero-excluding). f* = the largest
    # signed median = S2 (-0.1); |med| > tau and med < 0 -> NO-GO (resolved).
    res = az.analyze_population(_pop(deltas))
    dec = res["decision"]
    assert dec["selected_contrast"] == "S2_batt_high"
    assert dec["state"] == "NO-GO" and dec["count"] == 0
    assert dec["signed_median_midpoint"] < -az.TAU_DELTA


# --------------------------------------------------------------------------
# analyzer end-to-end (file IO), INVALID and DESIGN-NOT-FROZEN
# --------------------------------------------------------------------------
def test_analyzer_go_end_to_end(tmp_path, screen):
    u = {s: 0.5 for s in bp.SETTING_ORDER}
    u["S1_batt_low"] = 0.6
    runs = _write_tree(tmp_path / "runs", screen, u_by_setting=u)
    out = az.analyze(runs, tmp_path / "out", "20260820T000000Z",
                     "0" * 40, screen_dir=None, verify_code_commit=False)
    manifest = json.loads((Path(out) / "MANIFEST.json").read_text())
    assert manifest["decision"]["state"] == "GO"
    assert manifest["decision"]["selected_contrast"] == "S1_batt_low"
    assert (Path(out) / "SUMMARY.md").exists()
    assert (Path(out) / "matched_contrasts.csv").exists()
    assert (Path(out) / "cell_intervals.csv").exists()
    assert (Path(out) / "setting_summary.csv").exists()
    assert (Path(out) / "DECISION.json").exists()
    summary = (Path(out) / "SUMMARY.md").read_text()
    assert "synthetic" in summary and "not the full B3 atlas" in summary


def test_analyzer_invalid_on_uncertified(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen, certified_all=False)
    out = az.analyze(runs, tmp_path / "out", "20260820T000001Z",
                     "0" * 40, screen_dir=None, verify_code_commit=False)
    manifest = json.loads((Path(out) / "MANIFEST.json").read_text())
    assert manifest["decision"]["state"] == "INVALID/HALT"


def test_analyzer_design_not_frozen_on_bad_screen(tmp_path):
    dst = _screen_copy(tmp_path, mutate=lambda r, m: (
        {**r, "disposition": {**r["disposition"], "state": "X"}}, m))
    runs = tmp_path / "runs"
    runs.mkdir()
    out = az.analyze(runs, tmp_path / "out", "20260820T000002Z",
                     "0" * 40, screen_dir=dst, verify_code_commit=False)
    manifest = json.loads((Path(out) / "MANIFEST.json").read_text())
    assert manifest["decision"]["state"] == "DESIGN-NOT-FROZEN"


def test_analyzer_refuses_existing_output(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    (tmp_path / "out" / "20260820T000003Z").mkdir(parents=True)
    with pytest.raises(az.B3AnalysisError, match="existing output"):
        az.analyze(runs, tmp_path / "out", "20260820T000003Z",
                   "0" * 40, screen_dir=None, verify_code_commit=False)


def test_analyzer_refuses_a6_paths(tmp_path):
    with pytest.raises(az.B3AnalysisError, match="A6"):
        az.analyze("runs/a6_holdout", tmp_path / "out", "s",
                   "0" * 40, verify_code_commit=False)


# --------------------------------------------------------------------------
# per-cell interval semantics (spec 1.1)
# --------------------------------------------------------------------------
def test_cell_interval_prefers_z_d_lb_and_cost_fraction():
    iv = az.cell_interval(ub_ch=100.0, lb_ch=99.995, z_d_ub=100.6,
                          z_d_lb=100.59, n_trips=8)
    assert iv["lo_endpoint"] == "z_D_lb"
    assert abs(iv["U_lo_raw"] - (100.59 - 100.0)) < 1e-9
    assert abs(iv["U_hi"] - (100.6 - 99.995)) < 1e-9
    assert iv["cost_fraction"] is not None
    # proxy fallback when z_D_lb missing
    iv2 = az.cell_interval(100.0, 99.995, 100.6, None, 8)
    assert iv2["lo_endpoint"] == "proxy"
    # cost fraction omitted (never approximated) when lb_CH <= 0
    iv3 = az.cell_interval(100.0, -1.0, 100.6, 100.59, 8)
    assert iv3["cost_fraction"] is None


# --------------------------------------------------------------------------
# protected A6 algorithm/grid files: zero drift vs the clean base
# --------------------------------------------------------------------------
@pytest.mark.parametrize("relpath", PROTECTED_A6_FILES)
def test_protected_a6_files_zero_drift(relpath):
    committed = subprocess.check_output(
        ["git", "show", f"{B3_PILOT_BASE_COMMIT}:{relpath}"], cwd=REPO_ROOT)
    current = (REPO_ROOT / relpath).read_bytes()
    assert committed == current, f"{relpath} drifted from the clean base"
