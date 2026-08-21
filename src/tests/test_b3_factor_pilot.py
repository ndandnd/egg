"""Launcher-ready B3 factor pilot: frozen binding, refusals, exact-count
audit, and the preregistered decision taxonomy.

Covers the driver library (``experiments.b3_factor_pilot``), the exact-count
audit (``experiments.audit_b3_factor_pilot``), and the preregistered
analyzer (``experiments.analyze_b3_factor_pilot``) with adversarial tamper
cases, plus the protected-A6-file zero-drift gate. No optimizer is invoked
and no outcome artifact is generated: cells are synthetic fixtures.
"""
import copy
import json
import math
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import experiments.analyze_b3_factor_pilot as az
import experiments.audit_b3_factor_pilot as ad
import experiments.b3_factor_pilot as bp
import experiments.b3_pilot_anchor as b3_anchor

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
# A REAL commit (HEAD), so the analyzer's production run_commit
# resolution actually runs against these fixtures instead of being
# bypassed by a test seam.
RUN_COMMIT = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=bp.REPO_ROOT).decode().strip()
MIP_GAP = bp.MIP_GAP_DEFAULT


def _cg_ckpt(ihash, mhash, z_d_ub, ub_ch=100.0, lb_best=100.0, certified=True,
             method="a2", eps=bp.EPSILON):
    """A complete, ``_cg_sane``-passing, REPLAY-CONSISTENT A2 checkpoint:
    every recorded bound-history entry, ``lb_ch``, ``lb_best``, and outcome
    field is reproducible from the chronological oracle/iteration event
    evidence (``lb_ch = z_rmp + min(0, bound - sigma)``), exactly as the
    production driver commits them."""
    sigma = 10.0
    # (ub of the iteration's RMP, its z_rmp_model, the lb it certifies)
    plan = [(ub_ch + 1.0, ub_ch + 1.0, lb_best - 1.0),
            (ub_ch, ub_ch, lb_best)]
    # seed call (chronologically first, referenced by no iteration event)
    oe = [{"extra": {"call_id": "a2-oc0"},
           "solver": {"status": "OPTIMAL", "backend": "GRB"},
           "replay_ok": True, "replay_violations": []}]
    it, ub_hist, lb_hist = [], [], []
    lbb = -math.inf
    for i, (ub, z_rmp, lb_target) in enumerate(plan):
        call_id = f"a2-oc{i + 1}"
        rc = lb_target - z_rmp        # <= 0, so lb_ch == lb_target exactly
        oe.append({"extra": {"call_id": call_id,
                             "min_reduced_cost_lb": rc},
                   "solver": {"status": "OPTIMAL", "backend": "GRB",
                              "bound": sigma + rc},
                   "replay_ok": True, "replay_violations": []})
        lb_ch = z_rmp + min(0.0, rc)
        lbb = max(lbb, lb_ch)
        master = {
            "solve_id": f"a2-it{i}-rmp-r0", "backend": "GRB",
            "status": "OPTIMAL", "obj": z_rmp, "bound": z_rmp,
            "mip_gap": 0.0, "n_vars": 1, "n_int": 0, "n_constrs": 1,
            "wall_s": 0.0, "threads": 1,
        }
        it.append({"iteration_id": f"it{i}", "phase": "clean",
                   "replay_ok": True, "oracle_calls": i + 1,
                   "pricing_solve_id": call_id, "z_rmp_model": z_rmp,
                   "duals_sigma": sigma, "min_reduced_cost_lb": rc,
                   "lb_ch": lb_ch, "lb_best": lbb, "ub_ch": ub,
                   "certificate_gap": ub - lbb,
                   "epsilon": bp.EPSILON, "pwl_tol": 1e-3,
                   "master_solves": [master]})
        ub_hist.append(ub)
        lb_hist.append(lbb)
    calls = len(oe)
    otype = "certified" if certified else "budget_exhausted"
    return {
        "done": True,
        "identity": {"method": method, "epsilon": eps, "budget": bp.BUDGET,
                     "tol_d": bp.TOL_D, "instance_hash": ihash,
                     "market_hash": mhash, "z_d_ub": z_d_ub,
                     "solver": {"backend": "GRB", "max_mip_gap": MIP_GAP}},
        "oracle_calls": calls, "oracle_events": oe, "iteration_events": it,
        "ub_history": ub_hist, "lb_history": lb_hist, "lb_best": lbb,
        "outcome": {"type": otype, "ub_ch": ub_ch, "lb_best": lbb,
                    "gap": ub_ch - lbb, "certified": certified,
                    "oracle_calls": calls, "method": method,
                    "uplift_interval": [
                        (z_d_ub - bp.TOL_D) - ub_ch,
                        z_d_ub - lbb,
                    ]},
    }


def _dict_ckpt(ihash, mhash, screen_sha, cell, manifest_sha, z_d_ub, z_d_lb,
               converged=True, status="OPTIMAL"):
    """A complete dictator checkpoint mirroring the production driver:
    adaptive endpoints and gap, the committed replay-valid record, and the
    manifest-bound solver identity."""
    gap = z_d_ub - z_d_lb
    solve_stats = [{
        "round": 1, "status": "OPTIMAL", "incumbent": z_d_ub,
        "bound": z_d_lb, "gap": gap, "n_vars": 1, "n_int": 1,
        "n_constrs": 1, "wall_s": 0.0, "backend": "GRB", "threads": 1,
    }]
    adaptive = {"adaptive_converged": converged,
                "adaptive_lb": z_d_lb, "adaptive_ub": z_d_ub,
                "adaptive_gap_abs": gap, "adaptive_tol_abs": bp.TOL_D,
                "adaptive_rounds": 1,
                "adaptive_solve_stats": solve_stats}
    return {
        "identity": {"instance_hash": ihash, "market_hash": mhash,
                     "screen_record_sha256": screen_sha,
                     "run_manifest_sha256": manifest_sha,
                     "run_commit": RUN_COMMIT, "setting": cell["setting"],
                     "tol_d": bp.TOL_D, "experiment": "b3-factor-pilot",
                     "solver": {"backend": "GRB", "max_mip_gap": MIP_GAP,
                                "time_limit_s": None}},
        "z_d_ub": z_d_ub, "z_d_lb": z_d_lb, "tol_d": bp.TOL_D,
        "status": status, "bound": z_d_lb, "adaptive": adaptive,
        "record": {
            "experiment": "b3-factor-pilot", "regime": "dictator",
            "instance_hash": ihash, "obj_true": z_d_ub,
            "replay_ok": True, "replay_violations": [],
            "extra": {
                "tag": cell["tag"],
                "cell": [cell["setting"], cell["seed"],
                         cell["n_trips"], cell["b"]],
                "setting": cell["setting"],
                "screen_record_sha256": screen_sha,
            },
            "solver": {
                "status": status, "backend": "GRB", "bound": z_d_lb,
                "extra": copy.deepcopy(adaptive),
            },
        },
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
            _dict_ckpt(ihash, mhash, screen["record_sha256"], cell,
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


def test_preanalysis_raw_anchor_constants_are_frozen():
    assert b3_anchor.FROZEN_RAW_TREE_SHA256 == (
        "efc5ca31dcddb21166f6a5da2cf60b4961706c99edf9dbda882f87a18a88ace4")
    assert b3_anchor.FROZEN_RAW_FILE_COUNT == 363
    assert b3_anchor.FROZEN_RAW_DIRECTORY_COUNT == 60
    assert b3_anchor.FROZEN_RAW_TOTAL_BYTES == 17385781
    assert b3_anchor.FROZEN_RUN_SPEC_SHA256 == (
        "150f4b32220b13866d2872e4bb8a29bfcc5137cca18ebb55c8ddf3d163d4275f")


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
    # Its signed median is -0.1 (against direction); others are 0, so f*
    # is the first zero-median setting in factor order (S1) and the ONE
    # preregistered answer is UNDER-RESOLVED (|med_{f*}| = 0 <= tau).
    assert res["settings"]["S3_pow_low"]["signed_median_midpoint"] < -az.TAU_DELTA
    assert dec["selected_contrast"] == "S1_batt_low"
    assert dec["signed_median_midpoint"] == 0.0
    assert dec["state"] == "UNDER-RESOLVED"


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
# evidence replay: bounds are replayed from chronological events, never
# read from stored summary fields (review-reproduction regressions)
# --------------------------------------------------------------------------
def _analyze_decision(runs, out, stamp="sX", screen_dir=None):
    outdir = az.analyze(runs, out, stamp, "0" * 40, screen_dir=screen_dir,
                        verify_code_commit=False)
    return json.loads((Path(outdir) / "MANIFEST.json").read_text())[
        "decision"]


def test_exploit_ch_history_edit_with_unchanged_solver_evidence(
        tmp_path, screen):
    """Review reproduction: fabricate a 12/12 median-0.12 GO for S1 by
    shifting the CH histories, iteration bound fields, and outcome down
    while the ORACLE SOLVER EVIDENCE is unchanged.  The one shared primitive
    replay used by audit and analyzer must refuse."""
    runs = _write_tree(tmp_path / "runs", screen)  # uniform 0.5 everywhere

    def shift(ck, d=0.12):
        ck["ub_history"] = [u - d for u in ck["ub_history"]]
        ck["lb_history"] = [x - d for x in ck["lb_history"]]
        ck["lb_best"] -= d
        ck["outcome"]["ub_ch"] -= d
        ck["outcome"]["lb_best"] -= d
        for it in ck["iteration_events"]:
            it["ub_ch"] -= d
            it["lb_ch"] -= d
            it["lb_best"] -= d
    for cell in bp.build_cells():
        if cell["setting"] == "S1_batt_low":
            _mutate_cg(runs, cell["tag"], shift)
    audit = ad.audit(runs, screen_dir=None)
    assert not audit["ok"]
    assert any(any(needle in p for needle in (
        "primitive replay", "RMP", "history edited", "does not match"))
        for p in audit["problems"])
    decision = _analyze_decision(runs, tmp_path / "out")
    assert decision["state"] == "INVALID/HALT"
    assert any("!= replayed" in p or "history edited" in p or "RMP" in p
               for p in decision["problems"])


def test_exploit_single_history_entry_edit(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    _mutate_cg(runs, tag,
               lambda ck: ck["lb_history"].__setitem__(0, 42.0))
    decision = _analyze_decision(runs, tmp_path / "out")
    assert decision["state"] == "INVALID/HALT"
    assert any("CH history edited" in p for p in decision["problems"])


def test_exploit_oracle_event_dropped_or_reordered(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tags = [c["tag"] for c in bp.build_cells()[:2]]
    _mutate_cg(runs, tags[0],
               lambda ck: ck.update(
                   oracle_events=ck["oracle_events"][:-1],
                   oracle_calls=len(ck["oracle_events"]) - 1))
    _mutate_cg(runs, tags[1],
               lambda ck: ck.update(
                   oracle_events=list(reversed(ck["oracle_events"]))))
    decision = _analyze_decision(runs, tmp_path / "out")
    assert decision["state"] == "INVALID/HALT"


@pytest.mark.parametrize("forgery,needle", [
    ("gap", "recomputed dictator gap"),
    ("gap_abs", "inconsistent with endpoints"),
    ("record_invalid", "record replay invalid"),
    ("record_missing", "record replay invalid"),
    ("violations", "replay violations"),
    ("solver", "dictator solver identity"),
])
def test_exploit_dictator_certificate_forgeries(tmp_path, screen, forgery,
                                                needle):
    """adaptive_converged alone is never trusted: the dictator certificate
    is recomputed from endpoints, the committed record must be
    replay-valid, and the solver identity must match the run manifest."""
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]

    def forge(dd):
        if forgery == "gap":
            # widen the certified gap beyond tol_d while keeping every
            # stored consistency field agreeing and the flag True
            dd["z_d_lb"] -= 0.02
            dd["adaptive"]["adaptive_lb"] = dd["z_d_lb"]
            dd["adaptive"]["adaptive_gap_abs"] = (
                dd["z_d_ub"] - dd["z_d_lb"])
            assert dd["adaptive"]["adaptive_converged"] is True
        elif forgery == "gap_abs":
            dd["adaptive"]["adaptive_gap_abs"] = 0.005
        elif forgery == "record_invalid":
            dd["record"]["replay_ok"] = False
        elif forgery == "record_missing":
            dd.pop("record")
        elif forgery == "violations":
            dd["record"]["replay_violations"] = ["load drift"]
        elif forgery == "solver":
            dd["identity"]["solver"]["backend"] = "CBC"
    _mutate_dict(runs, tag, forge)
    decision = _analyze_decision(runs, tmp_path / "out")
    assert decision["state"] == "INVALID/HALT"
    assert any(needle in p for p in decision["problems"]), decision[
        "problems"]


def test_exploit_budget_exceeded_refused(tmp_path, screen):
    """A replay-consistent event stream that exceeds the frozen oracle
    budget (240) is INVALID/HALT — never a scored cell."""
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]

    def extend(ck):
        last_it = ck["iteration_events"][-1]
        extra = (bp.BUDGET + 1) - len(ck["oracle_events"])
        for j in range(extra):
            call_id = f"a2-ocx{j}"
            event = copy.deepcopy(ck["oracle_events"][-1])
            event["extra"]["call_id"] = call_id
            ck["oracle_events"].append(event)
            it = copy.deepcopy(last_it)
            it["pricing_solve_id"] = call_id
            it["iteration_id"] = f"itx{j}"
            it["oracle_calls"] = len(ck["iteration_events"]) + 1
            it["master_solves"][0]["solve_id"] = f"a2-itx{j}-rmp-r0"
            ck["iteration_events"].append(it)
            ck["ub_history"].append(it["ub_ch"])
            ck["lb_history"].append(it["lb_best"])
        ck["oracle_calls"] = len(ck["oracle_events"])
        assert ck["oracle_calls"] == 241
        ck["outcome"]["oracle_calls"] = ck["oracle_calls"]
    _mutate_cg(runs, tag, extend)
    decision = _analyze_decision(runs, tmp_path / "out")
    assert decision["state"] == "INVALID/HALT"
    assert any("exceeds the frozen budget" in p
               for p in decision["problems"]), decision["problems"]


def test_impossible_tightened_interval_is_invalid_halt(tmp_path, screen):
    """U_hi in [-1e-6, 0): the theorem-tightened interval [0, U_hi] is
    impossible (lo > hi) and must be INVALID/HALT, never emitted."""
    u = {s: 0.5 for s in bp.SETTING_ORDER}
    u["S4_pow_high"] = -5e-7
    runs = _write_tree(tmp_path / "runs", screen, u_by_setting=u)
    decision = _analyze_decision(runs, tmp_path / "out")
    assert decision["state"] == "INVALID/HALT"
    assert any("impossible tightened interval" in p
               for p in decision["problems"]), decision["problems"]


def test_malformed_checkpoint_is_structured_invalid_halt(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    tag = bp.build_cells()[0]["tag"]
    (Path(runs) / tag / "a2.cg.ckpt.json").write_text("{not json")
    decision = _analyze_decision(runs, tmp_path / "out")  # must not raise
    assert decision["state"] == "INVALID/HALT"
    assert decision["problems"]


def test_screen_override_marks_artifact_non_scoreable(tmp_path):
    """The test-only screen hook cannot bypass production scoring: a drifted
    screen is DESIGN-NOT-FROZEN and the CLI exposes no override."""
    dst = _screen_copy(tmp_path, mutate=lambda r, m: (
        {**r, "synthetic_note": "test-only screen"}, m))
    screen2 = bp.load_frozen_screen(dst)
    assert screen2["record_sha256"] != bp.FROZEN_SCREEN_RECORD_SHA256
    u = {s: 0.5 for s in bp.SETTING_ORDER}
    u["S1_batt_low"] = 0.6
    runs = _write_tree(tmp_path / "runs", screen2, u_by_setting=u)
    from unittest import mock
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=bp.REPO_ROOT).decode().strip()
    with mock.patch.object(az, "verify_analysis_code_commit",
                           return_value=True):
        out = az.analyze(runs, tmp_path / "out", "sN", head,
                         screen_dir=dst, verify_code_commit=True)
    manifest = json.loads((Path(out) / "MANIFEST.json").read_text())
    assert manifest["decision"]["state"] == "DESIGN-NOT-FROZEN"
    assert manifest["frozen_screen_verified"] is False
    decision = json.loads((Path(out) / "DECISION.json").read_text())
    assert decision["state"] == "DESIGN-NOT-FROZEN"
    assert decision["frozen_screen_verified"] is False
    assert not (Path(out) / "cell_intervals.csv").exists()
    import experiments.select_b3_confirmation as sel
    with pytest.raises(sel.B3SelectionError, match="frozen screen"):
        sel.select(
            runs, out, tmp_path / "sel", head,
            verify_code_commit=False)
    assert not (tmp_path / "sel").exists()


def test_production_analyzer_cli_has_no_screen_override():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "src/experiments/"
                            "analyze_b3_factor_pilot.py"),
         "--runs", "synthetic-does-not-exist",
         "--out", "synthetic-does-not-exist",
         "--stamp", "x", "--analysis-code-commit", "0" * 40,
         "--screen-dir", "forged"],
        cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    assert result.returncode != 0
    assert "unrecognized arguments: --screen-dir" in result.stderr


# --------------------------------------------------------------------------
# preregistered decision-rule boundaries, pinned EXACTLY (one right
# answer per fixture; engineering gates are strict inequalities)
# --------------------------------------------------------------------------
def _pop_points(u_baseline, u_by_setting):
    """A valid population of point intervals with an arbitrary baseline
    level, so boundary contrasts can be constructed float-exactly."""
    market_keys = [(s, n, b) for s in bp.SEEDS for n in bp.N_TRIPS
                   for b in bp.B_SCALES]
    assert len(market_keys) == 12
    cells = {}
    for setting in bp.SETTING_ORDER:
        for i, key in enumerate(market_keys):
            if setting == "S0_baseline":
                u = u_baseline
            else:
                u = u_by_setting[setting][i]
            iv = {"U_lo_raw": u, "U_lo": max(0.0, u), "U_hi": u,
                  "width": 0.0}
            cells[(setting, *key)] = {"cell": {}, "interval": iv}
    return {"cells": cells, "problems": []}


def _boundary_pop(s1_values):
    zeros = [0.0] * 12
    return _pop_points(0.0, {
        "S1_batt_low": s1_values, "S2_batt_high": zeros,
        "S3_pow_low": zeros, "S4_pow_high": zeros})


def test_boundary_median_exactly_plus_tau_is_under_resolved():
    """med == +0.04 EXACTLY: GO requires med > tau strictly, so the state
    is UNDER-RESOLVED (never GO), even at a 12/12 count."""
    res = az.analyze_population(_boundary_pop([az.TAU_DELTA] * 12))
    dec = res["decision"]
    assert dec["signed_median_midpoint"] == az.TAU_DELTA
    assert dec["signed_median_midpoint_repr"] == repr(az.TAU_DELTA)
    assert dec["boundary_margin"] == 0.0
    assert dec["boundary_adjacent"] is True
    assert dec["boundary_adjacent_tolerance"] == 1e-9
    assert dec["count"] == 12
    assert dec["state"] == "UNDER-RESOLVED"


def test_boundary_median_just_above_tau_is_go():
    value = math.nextafter(az.TAU_DELTA, 1.0)
    res = az.analyze_population(_boundary_pop([value] * 12))
    dec = res["decision"]
    assert dec["signed_median_midpoint"] == value
    assert 0 < dec["boundary_margin"] < 1e-9
    assert dec["boundary_adjacent"] is True
    assert dec["state"] == "GO"


def _minus_boundary_pop(s1_values):
    """S1 carries the boundary values; every other factor is pushed WELL
    below so the ranking must select S1 (all counts tie at zero)."""
    low = [-0.5] * 12
    return _pop_points(0.0, {
        "S1_batt_low": s1_values, "S2_batt_high": [0.5] * 12,
        "S3_pow_low": low, "S4_pow_high": [0.5] * 12})


def test_boundary_median_exactly_minus_tau_is_under_resolved():
    res = az.analyze_population(_minus_boundary_pop([-az.TAU_DELTA] * 12))
    dec = res["decision"]
    assert dec["selected_contrast"] == "S1_batt_low"
    assert dec["signed_median_midpoint"] == -az.TAU_DELTA
    assert dec["boundary_margin"] == 0.0
    assert dec["boundary_adjacent"] is True
    assert dec["state"] == "UNDER-RESOLVED"


def test_boundary_median_just_below_minus_tau_is_no_go():
    value = math.nextafter(-az.TAU_DELTA, -1.0)
    res = az.analyze_population(_minus_boundary_pop([value] * 12))
    dec = res["decision"]
    assert dec["selected_contrast"] == "S1_batt_low"
    assert dec["signed_median_midpoint"] == value
    assert dec["state"] == "NO-GO"


def test_boundary_negative_direction_median_exactly_tau():
    """S2 (non-positive direction): every contrast exactly -tau gives a
    SIGNED median of exactly +tau with a 12/12 zero-excluding count; the
    strict median gate still refuses GO."""
    zeros = [0.0] * 12
    res = az.analyze_population(_pop_points(0.0, {
        "S1_batt_low": zeros, "S2_batt_high": [-az.TAU_DELTA] * 12,
        "S3_pow_low": zeros, "S4_pow_high": zeros}))
    dec = res["decision"]
    assert dec["selected_contrast"] == "S2_batt_high"
    assert dec["count"] == 12
    assert dec["signed_median_midpoint"] == az.TAU_DELTA
    assert dec["state"] == "UNDER-RESOLVED"


def test_boundary_count_exactly_nine_is_go_eight_is_no_go():
    go = az.analyze_population(_boundary_pop([0.1] * 9 + [0.0] * 3))
    assert go["decision"]["count"] == 9
    assert go["decision"]["signed_median_midpoint"] == 0.1
    assert go["decision"]["boundary_adjacent"] is False
    assert go["decision"]["state"] == "GO"
    no_go = az.analyze_population(_boundary_pop([0.1] * 8 + [0.0] * 4))
    assert no_go["decision"]["count"] == 8
    assert no_go["decision"]["signed_median_midpoint"] == 0.1
    assert no_go["decision"]["state"] == "NO-GO"


def test_boundary_contrast_endpoint_exactly_zero_not_zero_excluding():
    """A contrast endpoint of EXACTLY zero is not zero-excluding (strict
    inequality), so nine 0.1-cells plus three exact-zero cells count 9."""
    res = az.analyze_population(_boundary_pop([0.1] * 9 + [0.0] * 3))
    s1_rows = [row for row in res["contrasts"]
               if row["setting"] == "S1_batt_low"]
    zero_rows = [row for row in s1_rows if row["delta_lo"] == 0.0]
    assert len(zero_rows) == 3
    assert all(row["direction_consistent_zero_excluding"] is False
               for row in zero_rows)
    assert res["settings"]["S1_batt_low"]["count"] == 9


def test_boundary_count_beats_median_in_ranking():
    """f* selection is count-first: S1 (count 10, med 0.05) outranks S3
    (count 9, med 0.9)."""
    zeros = [0.0] * 12
    res = az.analyze_population(_pop_points(0.0, {
        "S1_batt_low": [0.05] * 10 + [0.0] * 2,
        "S2_batt_high": zeros,
        "S3_pow_low": [0.9] * 9 + [0.0] * 3,
        "S4_pow_high": zeros}))
    dec = res["decision"]
    assert res["settings"]["S1_batt_low"]["count"] == 10
    assert res["settings"]["S3_pow_low"]["count"] == 9
    assert res["settings"]["S3_pow_low"]["signed_median_midpoint"] == 0.9
    assert dec["selected_contrast"] == "S1_batt_low"
    assert dec["count"] == 10
    assert dec["signed_median_midpoint"] == 0.05
    assert dec["state"] == "GO"


def test_boundary_exact_factor_order_tie():
    """An EXACT tie on (count, signed median) resolves by the frozen
    factor order: S1 before S3."""
    zeros = [0.0] * 12
    res = az.analyze_population(_pop_points(0.0, {
        "S1_batt_low": [0.1] * 12, "S2_batt_high": zeros,
        "S3_pow_low": [0.1] * 12, "S4_pow_high": zeros}))
    dec = res["decision"]
    s1 = res["settings"]["S1_batt_low"]
    s3 = res["settings"]["S3_pow_low"]
    assert (s1["count"], s1["signed_median_midpoint"]) == (
        s3["count"], s3["signed_median_midpoint"])
    assert dec["selected_contrast"] == "S1_batt_low"
    assert s1["rank"] == 1 and s3["rank"] == 2
    assert dec["state"] == "GO"


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


def test_analyzer_refuses_preanalysis_anchor_drift(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen)
    out = az.analyze(
        runs, tmp_path / "out", "anchor-drift", "0" * 40,
        screen_dir=None, verify_code_commit=False,
        expected_raw_anchor=dict(b3_anchor.FROZEN_RAW_ANCHOR))
    decision = json.loads((Path(out) / "DECISION.json").read_text())
    assert decision["state"] == "INVALID/HALT"
    assert any("pre-analysis raw anchor mismatch" in problem
               and "tree_sha256" in problem
               for problem in decision["problems"])


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
