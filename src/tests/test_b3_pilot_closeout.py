"""B3 pilot closeout battery: evidence-complete analyzer artifacts,
portable byte-identical regeneration, the confirmation-selection freeze,
and the pack/import transfer utility — all on synthetic fixtures; no real
outcome is read anywhere."""
import copy
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

import experiments.analyze_b3_factor_pilot as az
import experiments.b3_factor_pilot as bp
import experiments.package_b3_pilot as pk
import experiments.select_b3_confirmation as sel
from experiments.package_a6_holdout import PackagingError
from test_b3_factor_pilot import _write_tree

STAMP = "20260820T000000Z"
# the selector resolves the analyzer commit against REAL repository
# history, so the fixtures record the actual checkout HEAD
CODE = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=bp.REPO_ROOT).decode().strip()


@pytest.fixture(scope="module")
def screen():
    return bp.load_frozen_screen()


def _go_tree(tmp_path, screen, name="runs"):
    u = {s: 0.5 for s in bp.SETTING_ORDER}
    u["S1_batt_low"] = 0.6  # S1 wins: GO
    return _write_tree(tmp_path / name, screen, u_by_setting=u)


def _analyze(runs, out, stamp=STAMP, *, verified=True):
    """Analyze a synthetic tree.  ``verified=True`` produces an honestly
    verified artifact (the byte-level provenance check itself is exercised
    in test_b3_factor_pilot; it cannot pass against fixtures on a dirty
    development tree, so it is stubbed here and the manifest records
    ``analysis_code_verified: true`` through the normal code path)."""
    if not verified:
        return az.analyze(runs, out, stamp, CODE,
                          screen_dir=None, verify_code_commit=False)
    with mock.patch.object(az, "verify_analysis_code_commit",
                           return_value=True):
        return az.analyze(runs, out, stamp, CODE,
                          screen_dir=None, verify_code_commit=True)


# --------------------------------------------------------------------------
# Task A: evidence-complete artifacts
# --------------------------------------------------------------------------
def test_artifact_contents_counts_and_cross_binding(tmp_path, screen):
    runs = _go_tree(tmp_path, screen)
    out = Path(_analyze(runs, tmp_path / "out"))
    cells = list(csv.DictReader(open(out / "cell_intervals.csv")))
    assert len(cells) == 60
    for row in cells:
        for field in ("instance_hash", "market_hash", "z_d_lb", "z_d_ub",
                      "lb_ch", "ub_ch", "u_lo_raw", "u_lo_tightened",
                      "u_hi", "width", "u_lo_raw_per_trip",
                      "u_hi_per_trip", "lo_endpoint_source",
                      "oracle_calls", "solver_backend", "solver_mip_gap"):
            assert row[field] != "", field
        assert row["lo_endpoint_source"] == "z_D_lb"
        assert float(row["u_lo_tightened"]) == max(
            0.0, float(row["u_lo_raw"]))
    contrasts = list(csv.DictReader(open(out / "matched_contrasts.csv")))
    assert len(contrasts) == 48
    summary = list(csv.DictReader(open(out / "setting_summary.csv")))
    assert len(summary) == 4
    assert [row["setting"] for row in summary] == list(az.FACTOR_ORDER)
    selected = [row for row in summary if row["selected"] == "True"]
    assert len(selected) == 1 and selected[0]["setting"] == "S1_batt_low"
    assert selected[0]["rank"] == "1"
    decision = json.loads((out / "DECISION.json").read_text())
    assert decision["schema"] == az.DECISION_SCHEMA
    assert decision["state"] == "GO"
    assert decision["selected_factor"] == "S1_batt_low"
    assert decision["direction_sign"] == 1
    assert decision["thresholds"] == {
        "count_gate": 9, "tau_delta": 0.04, "width_bound": 0.02}
    assert decision["analysis_code_commit"] == CODE
    assert decision["inputs"]["run_manifest_sha256"]
    manifest = json.loads((out / "MANIFEST.json").read_text())
    assert manifest["table_rows"] == {
        "cell_intervals.csv": 60, "matched_contrasts.csv": 48,
        "setting_summary.csv": 4}
    for name, sha in manifest["outputs"].items():
        assert sel.sha256_file(out / name) == sha
    # LF-only bytes everywhere
    for path in out.iterdir():
        assert b"\r" not in path.read_bytes(), path.name


def test_invalid_halt_emits_decision_without_tables_or_go(tmp_path, screen):
    runs = _write_tree(tmp_path / "runs", screen, certified_all=False)
    out = Path(_analyze(runs, tmp_path / "out"))
    decision = json.loads((out / "DECISION.json").read_text())
    assert decision["state"] == "INVALID/HALT"
    assert decision["selected_factor"] is None
    assert decision["problems"]  # nothing silently omitted
    assert not (out / "cell_intervals.csv").exists()
    assert not (out / "matched_contrasts.csv").exists()
    assert not (out / "setting_summary.csv").exists()


def test_regeneration_byte_identical_across_roots(tmp_path, screen):
    runs_a = _go_tree(tmp_path / "deep/rootA", screen)
    runs_b = _go_tree(tmp_path / "other/nested/rootB", screen)
    out_a = Path(_analyze(runs_a, tmp_path / "outA"))
    out_b = Path(_analyze(runs_b, tmp_path / "outB"))
    names = sorted(p.name for p in out_a.iterdir())
    assert names == sorted(p.name for p in out_b.iterdir())
    for name in names:
        assert (out_a / name).read_bytes() == (out_b / name).read_bytes(), (
            name)


def test_output_separation_including_aliases(tmp_path, screen):
    runs = _go_tree(tmp_path, screen)
    with pytest.raises(az.B3AnalysisError, match="separat|inside|overlap"):
        _analyze(runs, runs / "nested-out")
    with pytest.raises(az.B3AnalysisError, match="separat|inside|overlap"):
        _analyze(runs, runs)
    link = tmp_path / "alias"
    link.symlink_to(runs, target_is_directory=True)
    with pytest.raises(az.B3AnalysisError, match="separat|inside|overlap"):
        _analyze(runs, link / "sub")
    dotted = runs / ".." / Path(runs).name / "sub"
    with pytest.raises(az.B3AnalysisError, match="separat|inside|overlap"):
        _analyze(runs, dotted)
    assert not (Path(runs) / "sub").exists()


def test_existing_output_refused(tmp_path, screen):
    runs = _go_tree(tmp_path, screen)
    _analyze(runs, tmp_path / "out")
    with pytest.raises(az.B3AnalysisError, match="refusing existing"):
        _analyze(runs, tmp_path / "out")


# --------------------------------------------------------------------------
# Task B: confirmation-selection freeze
# --------------------------------------------------------------------------
def _go_analysis(tmp_path, screen):
    runs = _go_tree(tmp_path, screen)
    return Path(_analyze(runs, tmp_path / "out"))


def _select(analysis_dir, out):
    return sel.select(analysis_dir, out, CODE, verify_code_commit=False)


def test_selection_freeze_from_go(tmp_path, screen):
    analysis = _go_analysis(tmp_path, screen)
    path = Path(_select(analysis, tmp_path / "sel"))
    doc = json.loads(path.read_text())
    assert doc["schema"] == sel.SELECTION_SCHEMA
    assert doc["selected_factor"] == "S1_batt_low"
    assert doc["direction_sign"] == 1
    assert doc["frozen_factor_level"] == 45.0
    assert doc["baseline_level"] == 60.0
    assert doc["count_gate"] == 9 and doc["tau_delta"] == 0.04
    assert doc["pilot"]["analysis_manifest_sha256"] == sel.sha256_file(
        analysis / "MANIFEST.json")
    assert doc["pilot"]["run_manifest_sha256"]
    assert doc["pilot"]["screen_record_sha256"] == (
        bp.FROZEN_SCREEN_RECORD_SHA256)
    population = doc["confirmation_population"]
    assert population["seeds"] == [32, 33, 34, 35, 36, 37]
    assert population["settings"] == ["S0_baseline", "S1_batt_low"]
    assert population["n_trips"] == [8, 12]
    assert population["b_scales"] == [0.01, 0.05]
    assert population["matched_contrasts"] == 24
    assert population["method_cells"] == 48
    assert population["gate"] == {
        "min_zero_excluding": 18, "of": 24,
        "signed_median_exceeds": 0.04}
    assert b"\r" not in path.read_bytes()
    # deterministic: a second freeze to a fresh dir is byte-identical
    second = Path(_select(analysis, tmp_path / "sel2"))
    assert second.read_bytes() == path.read_bytes()


def test_selection_refuses_non_go(tmp_path, screen):
    # NO-GO / UNDER-RESOLVED style: uniform uplift -> all contrasts zero
    runs = _write_tree(tmp_path / "runs", screen)
    analysis = Path(_analyze(runs, tmp_path / "out"))
    state = json.loads((analysis / "DECISION.json").read_text())["state"]
    # uniform uplift -> every matched contrast is exactly zero -> the
    # preregistered rule has ONE answer: |median| <= tau is UNDER-RESOLVED
    assert state == "UNDER-RESOLVED"
    with pytest.raises(sel.B3SelectionError, match="only from GO"):
        _select(analysis, tmp_path / "sel")
    assert not (tmp_path / "sel" / "SELECTION.json").exists()

    # INVALID/HALT artifact lacks the tables entirely
    runs2 = _write_tree(tmp_path / "runs2", screen, certified_all=False)
    invalid = Path(_analyze(runs2, tmp_path / "out2"))
    with pytest.raises(sel.B3SelectionError, match="incomplete"):
        _select(invalid, tmp_path / "sel2")
    assert not (tmp_path / "sel2").exists()


@pytest.mark.parametrize("tamper", [
    "table_bytes", "manifest_hash", "missing_table", "extra_row",
    "duplicate_row", "decision_count", "selected_factor", "threshold",
    "code_commit", "run_manifest_sha",
])
def test_selection_refuses_tampering(tmp_path, screen, tamper):
    analysis = _go_analysis(tmp_path, screen)

    if tamper == "table_bytes":
        path = analysis / "setting_summary.csv"
        path.write_bytes(path.read_bytes() + b"# tampered\n")
        message = "hash mismatch"
    elif tamper == "manifest_hash":
        manifest = json.loads((analysis / "MANIFEST.json").read_text())
        manifest["outputs"]["cell_intervals.csv"] = "0" * 64
        (analysis / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        message = "hash mismatch"
    elif tamper == "missing_table":
        (analysis / "matched_contrasts.csv").unlink()
        message = "missing analysis table"
    elif tamper in ("extra_row", "duplicate_row"):
        # coordinated: append a row AND rehash in the manifest
        path = analysis / "matched_contrasts.csv"
        lines = path.read_text().splitlines()
        lines.append(lines[-1])
        path.write_text("\n".join(lines) + "\n")
        manifest = json.loads((analysis / "MANIFEST.json").read_text())
        manifest["outputs"]["matched_contrasts.csv"] = sel.sha256_file(path)
        (analysis / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        message = "row count"
    elif tamper == "decision_count":
        decision = json.loads((analysis / "DECISION.json").read_text())
        decision["counts"]["zero_excluding_count"] = 5  # below the gate
        payload = json.dumps(decision, indent=2, sort_keys=True) + "\n"
        (analysis / "DECISION.json").write_text(payload)
        manifest = json.loads((analysis / "MANIFEST.json").read_text())
        manifest["outputs"]["DECISION.json"] = sel.sha256_file(
            analysis / "DECISION.json")
        (analysis / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        message = "disagrees with the recomputed decision"
    elif tamper == "selected_factor":
        decision = json.loads((analysis / "DECISION.json").read_text())
        decision["selected_factor"] = "S3_pow_low"
        decision["direction_sign"] = 1
        (analysis / "DECISION.json").write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n")
        manifest = json.loads((analysis / "MANIFEST.json").read_text())
        manifest["outputs"]["DECISION.json"] = sel.sha256_file(
            analysis / "DECISION.json")
        (analysis / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        message = "disagrees with the recomputed decision"
    elif tamper == "threshold":
        decision = json.loads((analysis / "DECISION.json").read_text())
        decision["thresholds"]["tau_delta"] = 0.01
        (analysis / "DECISION.json").write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n")
        manifest = json.loads((analysis / "MANIFEST.json").read_text())
        manifest["outputs"]["DECISION.json"] = sel.sha256_file(
            analysis / "DECISION.json")
        (analysis / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        message = "thresholds differ"
    elif tamper == "code_commit":
        decision = json.loads((analysis / "DECISION.json").read_text())
        decision["analysis_code_commit"] = "1" * 40
        (analysis / "DECISION.json").write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n")
        manifest = json.loads((analysis / "MANIFEST.json").read_text())
        manifest["outputs"]["DECISION.json"] = sel.sha256_file(
            analysis / "DECISION.json")
        (analysis / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        message = "analysis_code_commit mismatch"
    elif tamper == "run_manifest_sha":
        decision = json.loads((analysis / "DECISION.json").read_text())
        decision["inputs"]["run_manifest_sha256"] = "2" * 64
        (analysis / "DECISION.json").write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n")
        manifest = json.loads((analysis / "MANIFEST.json").read_text())
        manifest["outputs"]["DECISION.json"] = sel.sha256_file(
            analysis / "DECISION.json")
        (analysis / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        message = "run_manifest_sha256 mismatch"
    else:
        raise AssertionError(tamper)

    with pytest.raises(sel.B3SelectionError, match=message):
        _select(analysis, tmp_path / "sel")
    assert not (tmp_path / "sel" / "SELECTION.json").exists()


def test_selection_refuses_existing_destination(tmp_path, screen):
    analysis = _go_analysis(tmp_path, screen)
    _select(analysis, tmp_path / "sel")
    with pytest.raises(sel.B3SelectionError, match="refusing existing"):
        _select(analysis, tmp_path / "sel")


def test_selection_provenance_gates(monkeypatch):
    with pytest.raises(sel.B3SelectionError, match="full 40-character"):
        sel.verify_selection_code_commit("abc")
    with pytest.raises(sel.B3SelectionError, match="does not resolve"):
        sel.verify_selection_code_commit("f" * 40)
    import subprocess as sp
    head = sp.check_output(
        ["git", "rev-parse", "HEAD"], cwd=sel.REPO_ROOT).decode().strip()
    real_run = sel.subprocess.run

    def not_ancestor(args, cwd=None, **kwargs):
        if args[:2] == ["git", "merge-base"]:
            class R:
                returncode = 1
            return R()
        return real_run(args, cwd=cwd, **kwargs)

    monkeypatch.setattr(sel.subprocess, "run", not_ancestor)
    with pytest.raises(sel.B3SelectionError, match="not an ancestor"):
        sel.verify_selection_code_commit(head)
    monkeypatch.setattr(sel.subprocess, "run", real_run)

    real_co = sel.subprocess.check_output

    def dirty(args, cwd=None, stderr=None):
        if args[1] == "status":
            return b" M src/experiments/select_b3_confirmation.py\n"
        return real_co(args, cwd=cwd, stderr=stderr)

    monkeypatch.setattr(sel.subprocess, "check_output", dirty)
    with pytest.raises(sel.B3SelectionError, match="tracked modifications"):
        sel.verify_selection_code_commit(head)


def _edit_json(path, fn):
    doc = json.loads(Path(path).read_text())
    fn(doc)
    Path(path).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")


def _rehash(analysis, *names):
    """A coordinated attacker with full write access also rewrites the
    manifest hashes of every edited output."""
    manifest_path = Path(analysis) / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    for name in names:
        manifest["outputs"][name] = sel.sha256_file(Path(analysis) / name)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def test_selection_refuses_forged_go_from_under_resolved(tmp_path, screen):
    """Review reproduction: a non-GO analysis whose DECISION.json AND
    MANIFEST.json decision were edited to GO (count 12, median 0.1) with
    all hashes recomputed.  The selector recomputes the decision from the
    primitive tables and must refuse."""
    runs = _write_tree(tmp_path / "runs", screen)  # uniform: UNDER-RESOLVED
    analysis = Path(_analyze(runs, tmp_path / "out"))

    def forge(doc):
        doc["state"] = "GO"
        doc["counts"]["zero_excluding_count"] = 12
        doc["signed_median_midpoint"] = 0.1
        doc["selected_factor"] = "S1_batt_low"
        doc["direction_sign"] = 1
    _edit_json(analysis / "DECISION.json", forge)

    def forge_manifest(doc):
        doc["decision"].update(state="GO", count=12,
                               signed_median_midpoint=0.1,
                               selected_contrast="S1_batt_low")
    _edit_json(analysis / "MANIFEST.json", forge_manifest)
    _rehash(analysis, "DECISION.json")
    with pytest.raises(sel.B3SelectionError,
                       match="disagrees with the recomputed decision"):
        _select(analysis, tmp_path / "sel")
    assert not (tmp_path / "sel").exists()


def test_selection_refuses_factor_swap_with_csv_flag_edits(tmp_path, screen):
    """Review reproduction: swap the winning factor S1 -> S3 by editing the
    matched-contrast zero-excluding flags plus DECISION/manifest, with all
    hashes recomputed.  The flags must recompute from the cell intervals,
    so the selector refuses."""
    analysis = _go_analysis(tmp_path, screen)
    path = analysis / "matched_contrasts.csv"
    rows = list(csv.DictReader(open(path)))
    for row in rows:
        if row["setting"] == "S3_pow_low":
            row["direction_consistent_zero_excluding"] = "True"
        if row["setting"] == "S1_batt_low":
            row["direction_consistent_zero_excluding"] = "False"
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    _edit_json(analysis / "DECISION.json",
               lambda d: d.update(selected_factor="S3_pow_low"))
    _edit_json(analysis / "MANIFEST.json",
               lambda m: m["decision"].update(selected_contrast="S3_pow_low"))
    _rehash(analysis, "matched_contrasts.csv", "DECISION.json")
    with pytest.raises(sel.B3SelectionError,
                       match="does not recompute|disagrees"):
        _select(analysis, tmp_path / "sel")
    assert not (tmp_path / "sel").exists()


def test_selection_requires_verified_analysis_and_real_commit(
        tmp_path, screen):
    runs = _go_tree(tmp_path, screen)
    unverified = Path(_analyze(runs, tmp_path / "out-unverified",
                               stamp="20260820T000001Z", verified=False))
    with pytest.raises(sel.B3SelectionError,
                       match="without code verification"):
        _select(unverified, tmp_path / "sel-u")
    analysis = Path(_analyze(runs, tmp_path / "out"))
    for label, fake, message in (
            ("zeros", "0" * 40, "not a real 40-hex commit"),
            ("unresolvable", "f" * 40, "does not resolve")):
        work = tmp_path / f"work-{label}"
        shutil.copytree(analysis, work)
        _edit_json(work / "MANIFEST.json",
                   lambda m, fake=fake: m.update(analysis_code_commit=fake))
        _edit_json(work / "DECISION.json",
                   lambda d, fake=fake: d.update(analysis_code_commit=fake))
        _rehash(work, "DECISION.json")
        with pytest.raises(sel.B3SelectionError, match=message):
            _select(work, tmp_path / f"sel-{label}")


def test_selection_refuses_screen_and_spec_drift(tmp_path, screen):
    analysis = _go_analysis(tmp_path, screen)
    drift_screen = tmp_path / "screen-drift"
    shutil.copytree(analysis, drift_screen)
    _edit_json(drift_screen / "MANIFEST.json",
               lambda m: m["frozen_screen"].update(record_sha256="e" * 64))
    with pytest.raises(sel.B3SelectionError, match="frozen screen"):
        _select(drift_screen, tmp_path / "s1")
    drift_spec = tmp_path / "spec-drift"
    shutil.copytree(analysis, drift_spec)
    _edit_json(drift_spec / "MANIFEST.json",
               lambda m: m["spec"].update(sha256="d" * 64))
    with pytest.raises(sel.B3SelectionError, match="spec SHA"):
        _select(drift_spec, tmp_path / "s2")


def test_selection_publication_isolation(tmp_path, screen):
    analysis = _go_analysis(tmp_path, screen)
    with pytest.raises(sel.B3SelectionError, match="disjoint"):
        _select(analysis, analysis / "sel")
    with pytest.raises(sel.B3SelectionError, match="disjoint"):
        _select(analysis, analysis.parent)
    real = tmp_path / "sel-real"
    real.mkdir()
    link = tmp_path / "sel-alias"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(sel.B3SelectionError, match="symlinked"):
        _select(analysis, link / "sub")
    with pytest.raises(sel.B3SelectionError, match="A6"):
        _select(analysis, tmp_path / "a6_holdout" / "sel")
    assert not (tmp_path / "a6_holdout").exists()
    assert not (analysis / "sel").exists()


# --------------------------------------------------------------------------
# Task C: pack / import
# --------------------------------------------------------------------------
def _materialize_jsonl(runs: Path) -> None:
    """The synthetic fixture writes checkpoints only; real cells also
    carry the materialized JSONL logs the pack population gate expects."""
    for cell in bp.build_cells():
        cdir = runs / cell["tag"]
        ck = json.loads((cdir / "a2.cg.ckpt.json").read_text())
        dck = json.loads((cdir / "dictator.ckpt.json").read_text())
        for name, rows in (
                ("a2.oracle.jsonl", ck.get("oracle_events") or []),
                ("a2.iterations.jsonl", ck.get("iteration_events") or []),
                ("dictator.jsonl", [dck.get("record") or {}])):
            with open(cdir / name, "w") as handle:
                for row in rows:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")


def _packable(tmp_path, screen):
    runs = Path(_go_tree(tmp_path, screen))
    _materialize_jsonl(runs)
    bp.bind_job_id(runs, "424242")
    analysis = Path(_analyze(runs, tmp_path / "analysis-out"))
    return runs, analysis


def _pack(runs, analysis, out):
    return pk.pack(runs, analysis, out, CODE, verify_commit=False,
                   job_quiescence_validator=lambda j: None)


def test_pack_import_round_trip(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    result = _pack(runs, analysis, tmp_path / "bundles")
    bundle = Path(result["bundle_dir"])
    manifest = json.loads(
        (bundle / "BUNDLE_MANIFEST.json").read_text())
    assert manifest["schema"] == pk.BUNDLE_SCHEMA
    assert manifest["run_commit"] == "a" * 40
    assert len(manifest["raw"]["cells"]) == 60
    for tag, files in manifest["raw"]["cells"].items():
        assert set(files) == set(pk.CELL_FILES)
    assert manifest["analysis"]["manifest_sha256"] == pk.sha256_file(
        analysis / "MANIFEST.json")
    # import at a fresh destination
    dest = tmp_path / "imported" / "b3_factor_pilot"
    imported = pk.import_bundle(bundle, dest)
    assert imported["tree_sha256"] == manifest["raw"]["tree_sha256"]
    from experiments.package_a6_holdout import (
        canonical_tree_sha256, snapshot_source)
    assert canonical_tree_sha256(snapshot_source(dest)) == (
        manifest["raw"]["tree_sha256"])
    # import overwrite refused
    with pytest.raises(PackagingError, match="refusing import overwrite"):
        pk.import_bundle(bundle, dest)
    # existing bundle destination refused
    with pytest.raises(PackagingError, match="refusing existing bundle"):
        _pack(runs, analysis, tmp_path / "bundles")


def test_pack_refuses_unexpected_and_symlinked_paths(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    rogue = runs / "rogue.txt"
    rogue.write_text("unexpected\n")
    with pytest.raises(PackagingError, match="population differs"):
        _pack(runs, analysis, tmp_path / "b1")
    rogue.unlink()
    victim = runs / "S0_baseline_s0_n8_b0.01" / "identity.json"
    moved = tmp_path / "moved-identity.json"
    shutil.move(victim, moved)
    victim.symlink_to(moved)
    with pytest.raises(PackagingError):
        _pack(runs, analysis, tmp_path / "b2")
    victim.unlink()
    shutil.move(moved, victim)


def test_pack_refuses_active_job_and_bad_job_binding(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)

    def active(job_id):
        raise PackagingError(f"Slurm job {job_id} is still active")

    with pytest.raises(PackagingError, match="still active"):
        pk.pack(runs, analysis, tmp_path / "b1", CODE,
                verify_commit=False, job_quiescence_validator=active)
    # run-commit tamper: JOB.json vs MANIFEST.json mismatch
    job = json.loads((runs / "JOB.json").read_text())
    job["run_commit"] = "b" * 40
    (runs / "JOB.json").write_text(
        json.dumps(job, indent=2, sort_keys=True) + "\n")
    with pytest.raises(PackagingError,
                       match="run_manifest_sha256 does not match|run commit"):
        _pack(runs, analysis, tmp_path / "b2")


def test_pack_detects_mutation_during_packaging(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    victim = runs / "S0_baseline_s0_n8_b0.01" / "a2.oracle.jsonl"
    real_copy = pk._copy_tree
    state = {"mutated": False}

    def mutating_copy(source, destination):
        real_copy(source, destination)
        if not state["mutated"] and source.name != "analysis-out":
            state["mutated"] = True
            victim.write_bytes(victim.read_bytes() + b"\n")

    import types
    orig = pk._copy_tree
    pk._copy_tree = mutating_copy
    try:
        with pytest.raises(PackagingError, match="mutated during packaging"):
            _pack(runs, analysis, tmp_path / "b1")
    finally:
        pk._copy_tree = orig
    assert state["mutated"]


def test_pack_refuses_cross_run_analysis(tmp_path, screen):
    """An analysis artifact produced from a DIFFERENT run manifest is
    refused."""
    runs, analysis = _packable(tmp_path, screen)
    manifest = json.loads((analysis / "MANIFEST.json").read_text())
    manifest["run_manifest_sha256"] = "3" * 64
    (analysis / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(PackagingError, match="DIFFERENT run manifest"):
        _pack(runs, analysis, tmp_path / "b1")


def test_import_rejects_tampered_bundle(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    bundle = Path(_pack(runs, analysis, tmp_path / "bundles")["bundle_dir"])
    victim = bundle / "runs" / "S1_batt_low_s0_n8_b0.01" / "a2.cg.ckpt.json"
    # bundle trees are read-only after install; work on a copy
    work = tmp_path / "bundle-copy"
    shutil.copytree(bundle, work)
    victim = work / "runs" / "S1_batt_low_s0_n8_b0.01" / "a2.cg.ckpt.json"
    victim.write_bytes(victim.read_bytes() + b"\n")
    with pytest.raises(PackagingError, match="digest mismatch"):
        pk.import_bundle(work, tmp_path / "dest")
    assert not (tmp_path / "dest").exists()
