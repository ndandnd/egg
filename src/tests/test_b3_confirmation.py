"""B3 confirmation stage: GO gate, committed-bytes authority, bindings,
worker self-defense, fresh-grid screen, and mandatory-artifact audit.

Adversarial synthetic tests only (no cluster, no Gurobi, no pilot outcomes
read). Selection artifacts are committed into throwaway git repositories so
the CRITICAL-1 committed-bytes control runs in full (never relaxed).
"""
import hashlib
import itertools
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import experiments.audit_b3_confirmation as ad
import experiments.b3_confirmation as cc

REPO_ROOT = cc.REPO_ROOT
DEFAULT_FACTOR = "S1_batt_low"
_counter = itertools.count()


def base_doc(factor=DEFAULT_FACTOR, **over):
    baseline = (cc.BASELINE_SETTING and
                (60.0 if factor.startswith(("S1", "S2")) else 150.0))
    d = {
        "schema": cc.SELECTION_SCHEMA, "campaign": "b3-factor-pilot",
        "state": "GO", "selected_factor": factor,
        "direction_sign": cc.DIRECTION_SIGN[factor],
        "frozen_factor_level": cc.selected_factor_level(factor),
        "baseline_level": baseline,
        "zero_excluding_count": 11, "count_gate": 9,
        "signed_median_midpoint": 0.12, "tau_delta": 0.04,
        "pilot": {
            "run_manifest_sha256": "a" * 64,
            "analysis_manifest_sha256": "b" * 64,
            "analysis_code_commit": "0" * 40,  # filled by committed_repo
            "screen_record_sha256": cc.FROZEN_SCREEN_RECORD_SHA256,
            "spec_sha256": cc.FROZEN_SPEC_SHA256,
        },
        "selection_code_commit": "0" * 40,     # filled by committed_repo
        "selection_artifact_path": "SELECTION.json",
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


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True)


def committed_repo(tmp_path, doc, *, commit_artifact=True,
                   path="SELECTION.json", fill_commits=True):
    """Create a throwaway repo, optionally commit the artifact, and return
    (repo, artifact_path_on_disk, final_doc)."""
    repo = Path(tmp_path) / f"repo{next(_counter)}"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "README").write_text("x\n")
    _git(repo, "add", "README")
    _git(repo, "commit", "-qm", "init")
    code_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    d = json.loads(json.dumps(doc))
    if fill_commits:
        d["selection_code_commit"] = code_commit
        d.setdefault("pilot", {})["analysis_code_commit"] = code_commit
        d["pilot"].setdefault("screen_record_sha256",
                              cc.FROZEN_SCREEN_RECORD_SHA256)
    d.setdefault("selection_artifact_path", path)
    art = repo / path
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    if commit_artifact:
        _git(repo, "add", path)
        _git(repo, "commit", "-qm", "selection")
    return repo, art, d


def load_ok(tmp_path, doc=None):
    doc = doc if doc is not None else base_doc()
    repo, art, _ = committed_repo(tmp_path, doc)
    return cc.load_selection_artifact(art, repo_root=repo)


def expect_refuse(tmp_path, doc, match, *, commit_artifact=True):
    repo, art, _ = committed_repo(tmp_path, doc, commit_artifact=commit_artifact)
    with pytest.raises(cc.B3ConfirmationError, match=match):
        cc.load_selection_artifact(art, repo_root=repo)


# --------------------------------------------------------------------------
# happy path
# --------------------------------------------------------------------------
def test_valid_committed_go_loads(tmp_path):
    sel = load_ok(tmp_path)
    assert sel["selected_factor"] == DEFAULT_FACTOR
    assert len(sel["sha256"]) == 64


# --------------------------------------------------------------------------
# CRITICAL 1 — uncommitted / tampered artifact refused
# --------------------------------------------------------------------------
def test_uncommitted_artifact_refused(tmp_path):
    # well-formed but NEVER committed -> not a tracked file
    repo, art, _ = committed_repo(tmp_path, base_doc(), commit_artifact=False)
    with pytest.raises(cc.B3ConfirmationError, match="not a tracked file"):
        cc.load_selection_artifact(art, repo_root=repo)


def test_committed_then_tampered_bytes_refused(tmp_path):
    repo, art, d = committed_repo(tmp_path, base_doc())
    # mutate the on-disk bytes after commit (bytes != committed blob)
    tampered = json.loads(art.read_text())
    tampered["zero_excluding_count"] = 10
    art.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n")
    with pytest.raises(cc.B3ConfirmationError,
                       match="do not equal the committed blob"):
        cc.load_selection_artifact(art, repo_root=repo)


def test_unsafe_artifact_path_refused(tmp_path):
    d = base_doc()
    d["selection_artifact_path"] = "../escape.json"
    # committed at SELECTION.json but declares an unsafe path
    repo, art, _ = committed_repo(tmp_path, d, fill_commits=True)
    with pytest.raises(cc.B3ConfirmationError, match="not a safe"):
        cc.load_selection_artifact(art, repo_root=repo)


# --------------------------------------------------------------------------
# HIGH 5 — field presence + type validation
# --------------------------------------------------------------------------
def test_missing_campaign_refused(tmp_path):
    d = base_doc(); del d["campaign"]
    expect_refuse(tmp_path, d, "campaign")


def test_missing_baseline_level_refused(tmp_path):
    d = base_doc(); del d["baseline_level"]
    expect_refuse(tmp_path, d, "baseline_level")


def test_wrong_baseline_level_refused(tmp_path):
    expect_refuse(tmp_path, base_doc(baseline_level=61.0), "baseline_level")


def test_boolean_direction_sign_refused(tmp_path):
    # JSON true must NOT be accepted as +1 for S1
    expect_refuse(tmp_path, base_doc(direction_sign=True),
                  "direction_sign .* is not an integer sign")


def test_count_above_possible_refused(tmp_path):
    expect_refuse(tmp_path, base_doc(zero_excluding_count=999),
                  "outside the possible")
    expect_refuse(tmp_path, base_doc(zero_excluding_count=13),
                  "outside the possible")


def test_count_below_gate_refused(tmp_path):
    expect_refuse(tmp_path, base_doc(zero_excluding_count=8),
                  "below the pilot GO gate")


def test_nonfinite_boundary_fields_refused(tmp_path):
    expect_refuse(tmp_path, base_doc(boundary_margin=float("nan")),
                  "boundary_margin is not finite")
    expect_refuse(tmp_path,
                  base_doc(signed_median_full_precision=float("inf")),
                  "signed_median_full_precision is not finite")
    expect_refuse(tmp_path, base_doc(signed_median_midpoint=float("inf")),
                  "signed_median_midpoint is not finite")


# --------------------------------------------------------------------------
# preserved passing controls
# --------------------------------------------------------------------------
def test_non_go_refused(tmp_path):
    for state in ("NO-GO", "UNDER-RESOLVED", "INVALID/HALT"):
        expect_refuse(tmp_path, base_doc(state=state), "not GO")


def test_boundary_adjacent_refused(tmp_path):
    expect_refuse(tmp_path, base_doc(boundary_adjacent=True), "knife-edge")


@pytest.mark.parametrize("field,bad", [
    ("tree_sha256", "0" * 64), ("file_count", 362),
    ("directory_count", 59), ("total_bytes", 17385780)])
def test_raw_binding_mismatch_refused(tmp_path, field, bad):
    rb = dict(cc.FROZEN_PILOT_RAW_TREE); rb[field] = bad
    expect_refuse(tmp_path, base_doc(raw_binding=rb), f"raw_binding.{field}")


def test_wrong_screen_and_spec_sha_refused(tmp_path):
    d = base_doc(); d["pilot"]["screen_record_sha256"] = "c" * 64
    # committed_repo won't override screen sha (fill_commits sets only if unset)
    repo, art, _ = committed_repo(tmp_path, d)
    with pytest.raises(cc.B3ConfirmationError, match="screen_record_sha256"):
        cc.load_selection_artifact(art, repo_root=repo)


def test_population_drift_refused(tmp_path):
    d = base_doc()
    d["confirmation_population"]["seeds"] = [32, 33, 34, 35, 36, 38]
    expect_refuse(tmp_path, d, "seeds")


# --------------------------------------------------------------------------
# enumeration / seeds
# --------------------------------------------------------------------------
def test_build_cells_deterministic_and_counts():
    cells = cc.build_cells(DEFAULT_FACTOR)
    assert cells == cc.build_cells(DEFAULT_FACTOR)
    assert len(cells) == 48
    per = {}
    for c in cells:
        per[c["setting"]] = per.get(c["setting"], 0) + 1
    assert per == {"S0_baseline": 24, DEFAULT_FACTOR: 24}


def test_confirmation_seed_refusals():
    for s in cc.CONFIRMATION_SEEDS:
        cc.assert_confirmation_seed(s)
    for bad in (0, 11, 15):
        with pytest.raises(cc.B3ConfirmationError, match="development"):
            cc.assert_confirmation_seed(bad)
    for bad in (16, 31):
        with pytest.raises(cc.B3ConfirmationError, match="holdout"):
            cc.assert_confirmation_seed(bad)
    for bad in (38, 10000):
        with pytest.raises(cc.B3ConfirmationError, match="confirmation seed"):
            cc.assert_confirmation_seed(bad)


# --------------------------------------------------------------------------
# HIGH 4 — fresh-grid structural screen
# --------------------------------------------------------------------------
def test_fresh_screen_passes_for_all_factors():
    for f in ("S1_batt_low", "S2_batt_high", "S3_pow_low", "S4_pow_high"):
        s = cc.screen_fresh_grid(f)
        assert s["all_pass"] and len(s["results"]) == 24
        assert s["screen_record_sha256"] == cc.FROZEN_SCREEN_RECORD_SHA256


def test_fresh_screen_failure_is_design_not_frozen(monkeypatch):
    real = cc.screen_instance
    calls = {"n": 0}

    def one_fails(inst):
        calls["n"] += 1
        if calls["n"] == 3:                       # fail the third instance
            return {"ok": False, "gate": "witness"}
        return real(inst)

    monkeypatch.setattr(cc, "screen_instance", one_fails)
    with pytest.raises(cc.B3ConfirmationError, match="DESIGN-NOT-FROZEN"):
        cc.assert_fresh_screen_passes(DEFAULT_FACTOR)
    # and it is recorded in the run manifest path (build refuses too)
    calls["n"] = 0
    with pytest.raises(cc.B3ConfirmationError, match="DESIGN-NOT-FROZEN"):
        cc.build_run_manifest(DEFAULT_FACTOR, {"sha256": "e" * 64},
                              git_commit="c" * 40, backend_name="GRB")


def test_run_manifest_records_fresh_screen():
    m = cc.build_run_manifest(DEFAULT_FACTOR, {"sha256": "e" * 64},
                              git_commit="c" * 40, backend_name="GRB")
    assert m["fresh_screen"]["all_pass"] is True
    assert len(m["fresh_screen"]["results"]) == 24
    assert m["fresh_screen"]["screen_record_sha256"] == \
        cc.FROZEN_SCREEN_RECORD_SHA256


# --------------------------------------------------------------------------
# CRITICAL 3 — atomic bind + worker self-defense
# --------------------------------------------------------------------------
def _write_manifest(out, factor=DEFAULT_FACTOR, sel_sha="e" * 64):
    m = cc.build_run_manifest(factor, {"sha256": sel_sha},
                              git_commit=cc.git_head_commit(),
                              backend_name="GRB")
    cc.write_run_manifest(out, m)
    return cc.load_run_manifest(out)


def test_bind_is_atomic_and_exclusive(tmp_path):
    out = tmp_path / "runs"
    _write_manifest(out)
    cc.bind_job_id(out, "77")
    with pytest.raises(cc.B3ConfirmationError, match="already exists"):
        cc.bind_job_id(out, "78")           # second concurrent bind fails
    job = json.loads((out / cc.JOB_FILENAME).read_text())
    assert job["job_id"] == "77"


def test_worker_self_defense(tmp_path, monkeypatch):
    out = tmp_path / "runs"
    run = _write_manifest(out)
    cc.bind_job_id(out, "9001")
    # matching array job id -> authorized
    monkeypatch.setenv("SLURM_ARRAY_JOB_ID", "9001")
    cc.assert_worker_authorized(out, run)
    # mismatched array job id -> refused (stale/foreign array)
    monkeypatch.setenv("SLURM_ARRAY_JOB_ID", "9002")
    with pytest.raises(cc.B3ConfirmationError, match="!= bound job id"):
        cc.assert_worker_authorized(out, run)
    # unset -> refused (manual/direct run)
    monkeypatch.delenv("SLURM_ARRAY_JOB_ID", raising=False)
    with pytest.raises(cc.B3ConfirmationError, match="SLURM_ARRAY_JOB_ID is unset"):
        cc.assert_worker_authorized(out, run)


def test_worker_refuses_missing_job_binding(tmp_path, monkeypatch):
    out = tmp_path / "runs"
    run = _write_manifest(out)
    monkeypatch.setenv("SLURM_ARRAY_JOB_ID", "9001")
    with pytest.raises(cc.B3ConfirmationError, match="job binding missing"):
        cc.assert_worker_authorized(out, run)


# --------------------------------------------------------------------------
# audit: HIGH 6 (mandatory GO artifact) + tamper cases
# --------------------------------------------------------------------------
MIP_GAP = cc.MIP_GAP_DEFAULT


def _cg_ckpt(ihash, mhash, z_d_ub, ub_ch=100.0, lb_best=100.0, certified=True):
    calls = 3
    oe = [{"extra": {"call_id": f"a2-oc{i}"},
           "solver": {"status": "OPTIMAL"}, "replay_ok": True}
          for i in range(calls)]
    it = [{"iteration_id": i, "pricing_solve_id": f"a2-oc{i + 1}"}
          for i in range(calls - 1)]
    return {"done": True,
            "identity": {"method": "a2", "epsilon": cc.EPSILON,
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
                        "oracle_calls": calls, "method": "a2"}}


def _dict_ckpt(ihash, mhash, setting, manifest_sha, sel_sha, run_commit, z):
    return {"identity": {"instance_hash": ihash, "market_hash": mhash,
                         "screen_record_sha256": cc.FROZEN_SCREEN_RECORD_SHA256,
                         "run_manifest_sha256": manifest_sha,
                         "run_commit": run_commit,
                         "selection_artifact_sha256": sel_sha,
                         "setting": setting, "tol_d": cc.TOL_D,
                         "experiment": "b3-confirmation"},
            "z_d_ub": z, "z_d_lb": z, "tol_d": cc.TOL_D, "status": "OPTIMAL",
            "adaptive": {"adaptive_converged": True, "adaptive_lb": z}}


def build_tree(tmp_path, factor=DEFAULT_FACTOR, certified_all=True):
    """Full 48-cell run tree bound to a COMMITTED GO selection artifact."""
    repo, art, _ = committed_repo(tmp_path, base_doc(factor))
    sel = cc.load_selection_artifact(art, repo_root=repo)
    sel_sha = sel["sha256"]
    runs = Path(tmp_path) / f"runs{next(_counter)}"
    run_commit = cc.git_head_commit()
    m = cc.build_run_manifest(factor, {"sha256": sel_sha},
                              git_commit=run_commit, backend_name="GRB")
    manifest_sha = cc.run_manifest_sha256(m)
    cc.write_run_manifest(runs, m)
    mbc = cc.market_hash_by_cell(m)
    for cell in cc.build_cells(factor):
        key3 = f"{cell['setting']}|{cell['seed']}|{cell['n_trips']}"
        key4 = (cell["setting"], cell["seed"], cell["n_trips"], cell["b"])
        ih = m["instance_hashes"][key3]; mh = mbc[key4]
        cdir = runs / cell["tag"]; cdir.mkdir(parents=True)
        z = 100.5
        (cdir / "a2.cg.ckpt.json").write_text(json.dumps(
            _cg_ckpt(ih, mh, z, certified=certified_all)))
        (cdir / "dictator.ckpt.json").write_text(json.dumps(
            _dict_ckpt(ih, mh, cell["setting"], manifest_sha, sel_sha,
                       run_commit, z)))
        ident = cc.cell_identity(
            cell, m, market_hash=mh, instance_hash=ih,
            run_manifest_sha256=manifest_sha, run_commit=run_commit,
            selection_artifact_sha256=sel_sha, mip_gap=MIP_GAP,
            backend_name="GRB")
        (cdir / cc.CELL_IDENTITY_FILENAME).write_bytes(
            cc.canonical_cell_identity_bytes(ident))
    return runs, art, repo


def test_audit_requires_selection_artifact(tmp_path):
    runs, art, repo = build_tree(tmp_path)
    # HIGH 6: without the GO artifact the audit refuses
    r = ad.audit(runs)
    assert not r["ok"]
    assert any("requires the committed GO artifact" in p for p in r["problems"])


def test_audit_passes_with_committed_artifact(tmp_path):
    runs, art, repo = build_tree(tmp_path)
    r = ad.audit(runs, selection_artifact=art, repo_root=repo)
    assert r["ok"], r["problems"]
    assert r["certified"] == 48 and r["dictators"] == 48


def test_audit_refuses_uncommitted_artifact(tmp_path):
    runs, art, repo = build_tree(tmp_path)
    # tamper the committed artifact on disk -> revalidation fails
    doc = json.loads(art.read_text()); doc["zero_excluding_count"] = 10
    art.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    r = ad.audit(runs, selection_artifact=art, repo_root=repo)
    assert not r["ok"]
    assert any("failed revalidation" in p for p in r["problems"])


def test_audit_uncertified_refused(tmp_path):
    runs, art, repo = build_tree(tmp_path, certified_all=False)
    r = ad.audit(runs, selection_artifact=art, repo_root=repo)
    assert not r["ok"]
    assert any("not certified" in p for p in r["problems"])


def test_audit_refuses_pilot_runs_path():
    with pytest.raises(cc.B3ConfirmationError, match="pilot outcome tree"):
        ad.audit(REPO_ROOT / "runs" / "b3_factor_pilot")


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
