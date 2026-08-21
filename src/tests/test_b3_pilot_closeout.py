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
_ANALYSIS_RUNS = {}


def _synthetic_anchor(runs):
    snapshot = pk.snapshot_source(runs)
    return {
        "tree_sha256": pk.canonical_tree_sha256(snapshot),
        "file_count": snapshot["file_count"],
        "directory_count": snapshot["directory_count"],
        "total_bytes": snapshot["total_bytes"],
    }


@pytest.fixture(scope="module")
def screen():
    return bp.load_frozen_screen()


def _go_tree(tmp_path, screen, name="runs"):
    u = {s: 0.5 for s in bp.SETTING_ORDER}
    u["S1_batt_low"] = 0.6  # S1 wins: GO
    return _write_tree(tmp_path / name, screen, u_by_setting=u)


def _synthetic_run_commit_ok(claimed) -> None:
    """Injected run-commit verifier for synthetic fixtures.

    Production resolves ``run_commit`` through git and requires a real
    ancestor commit; synthetic trees carry fabricated SHAs, so the fixtures
    inject this checker rather than manufacturing repository history.  It
    still asserts the recorded shape, so a fixture cannot omit the field.
    The production resolver itself is exercised directly in
    ``test_run_commit_*`` below.
    """
    if (not isinstance(claimed, str) or len(claimed) != 40
            or not all(c in "0123456789abcdef" for c in claimed)):
        raise az.evidence.EvidenceError(
            f"synthetic run_commit is malformed: {claimed!r}")


def _analyze(runs, out, stamp=STAMP, *, verified=True):
    """Analyze a synthetic tree.  ``verified=True`` produces an honestly
    verified artifact (the byte-level provenance check itself is exercised
    in test_b3_factor_pilot; it cannot pass against fixtures on a dirty
    development tree, so it is stubbed here and the manifest records
    ``analysis_code_verified: true`` through the normal code path)."""
    expected_anchor = _synthetic_anchor(runs)
    if not verified:
        artifact = az.analyze(
            runs, out, stamp, CODE, screen_dir=None,
            verify_code_commit=False, expected_raw_anchor=expected_anchor,
            run_commit_verifier=_synthetic_run_commit_ok)
    else:
        with mock.patch.object(az, "verify_analysis_code_commit",
                               return_value=True):
            artifact = az.analyze(
                runs, out, stamp, CODE, screen_dir=None,
                verify_code_commit=True, expected_raw_anchor=expected_anchor,
                run_commit_verifier=_synthetic_run_commit_ok)
    _ANALYSIS_RUNS[str(Path(artifact).resolve())] = Path(runs)
    return artifact


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
                      "u_hi_per_trip", "cost_fraction_lo",
                      "cost_fraction_hi", "dictator_gap", "ch_gap",
                      "lo_endpoint_source", "oracle_calls",
                      "solver_backend", "solver_mip_gap"):
            assert row[field] != "", field
        assert row["lo_endpoint_source"] == "z_D_lb"
        assert float(row["u_lo_tightened"]) == max(
            0.0, float(row["u_lo_raw"]))
        # spec 1.1/7 evidence: cost-fraction endpoints and BOTH
        # certificate gaps are emitted per cell
        assert float(row["dictator_gap"]) == (
            float(row["z_d_ub"]) - float(row["z_d_lb"]))
        assert float(row["ch_gap"]) == (
            float(row["ub_ch"]) - float(row["lb_ch"]))
        assert float(row["cost_fraction_lo"]) == (
            float(row["u_lo_tightened"]) / float(row["ub_ch"]))
        assert float(row["cost_fraction_hi"]) == (
            float(row["u_hi"]) / float(row["lb_ch"]))
        # the solver gap field is the run manifest's BOUND value, not an
        # unbound checkpoint field
        assert row["solver_backend"] == "GRB"
        assert float(row["solver_mip_gap"]) == bp.MIP_GAP_DEFAULT
        assert int(row["oracle_calls"]) <= bp.BUDGET
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
    assert decision["signed_median_midpoint_repr"] == repr(
        decision["signed_median_midpoint"])
    assert decision["boundary_margin"] == (
        abs(decision["signed_median_midpoint"]) - 0.04)
    assert decision["boundary_adjacent"] is False
    assert decision["boundary_adjacent_tolerance"] == 1e-9
    assert decision["analysis_code_commit"] == CODE
    assert decision["inputs"]["run_manifest_sha256"]
    manifest = json.loads((out / "MANIFEST.json").read_text())
    assert manifest["analysis_code_verified"] is True
    assert manifest["frozen_screen_verified"] is True
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
    bp.bind_job_id(runs, "424242")
    return Path(_analyze(runs, tmp_path / "out"))


def _select(analysis_dir, out):
    runs = _ANALYSIS_RUNS.get(str(Path(analysis_dir).resolve()))
    if runs is None:
        runs = next(reversed(_ANALYSIS_RUNS.values()))
    return sel.select(
        runs, analysis_dir, out, CODE, verify_code_commit=False,
        expected_raw_anchor=_synthetic_anchor(runs))


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
    assert doc["signed_median_midpoint_repr"] == repr(
        doc["signed_median_midpoint"])
    assert doc["boundary_margin"] == (
        abs(doc["signed_median_midpoint"]) - 0.04)
    assert doc["boundary_adjacent"] is False
    assert doc["boundary_adjacent_tolerance"] == 1e-9
    assert doc["boundary_review_required"] is False
    assert doc["authorization_state"] == "AUTHORIZED_BY_FROZEN_RULE"
    assert doc["certificate_integrity"]["attestation"] == (
        "replayed-not-re-solved")
    assert doc["certificate_integrity"]["pre_analysis_raw_anchor"] == (
        doc["pilot"]["raw_binding"]["pre_analysis_anchor"])
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


def test_boundary_adjacent_go_requires_human_review_without_rule_change(
        tmp_path, screen):
    u = {setting: 0.5 for setting in bp.SETTING_ORDER}
    u["S1_batt_low"] = 0.5 + az.TAU_DELTA + 5e-10
    runs = _write_tree(tmp_path / "runs", screen, u_by_setting=u)
    bp.bind_job_id(runs, "424242")
    analysis = Path(_analyze(runs, tmp_path / "out"))
    decision = json.loads((analysis / "DECISION.json").read_text())
    assert decision["state"] == "GO"
    assert decision["boundary_adjacent"] is True
    assert abs(decision["boundary_margin"]) < 1e-9

    selection = Path(_select(analysis, tmp_path / "selection"))
    document = json.loads(selection.read_text())
    assert document["state"] == "GO"
    assert document["boundary_adjacent"] is True
    assert document["boundary_review_required"] is True
    assert document["authorization_state"] == "HUMAN_REVIEW_REQUIRED"
    assert "human review" in document["boundary_policy"]


def test_selection_refuses_non_go(tmp_path, screen):
    # NO-GO / UNDER-RESOLVED style: uniform uplift -> all contrasts zero
    runs = _write_tree(tmp_path / "runs", screen)
    bp.bind_job_id(runs, "424242")
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
    bp.bind_job_id(runs2, "424243")
    invalid = Path(_analyze(runs2, tmp_path / "out2"))
    with pytest.raises(
            sel.B3SelectionError, match="incomplete|solver identity"):
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
    bp.bind_job_id(runs, "424242")
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


@pytest.mark.parametrize("copy_name", ["decision", "decision_document"])
def test_selection_requires_both_manifest_decision_copies(
        tmp_path, screen, copy_name):
    analysis = _go_analysis(tmp_path, screen)

    def forge(manifest):
        if copy_name == "decision":
            manifest["decision"]["count"] = 8
        else:
            manifest["decision_document"]["state"] = "NO-GO"

    _edit_json(analysis / "MANIFEST.json", forge)
    with pytest.raises(sel.B3SelectionError, match="MANIFEST.json"):
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


@pytest.mark.parametrize("table,needle", [
    ("matched_contrasts.csv", "duplicate contrast|missing contrast"),
    ("cell_intervals.csv", "duplicate cell|frozen 60-cell"),
])
def test_selection_refuses_duplicate_row_replacement(tmp_path, screen,
                                                     table, needle):
    """Coordinated SAME-CARDINALITY forgery: one data row is replaced by a
    duplicate of another (row counts and manifest hashes all consistent).
    The recomputation over the frozen grid must refuse."""
    analysis = _go_analysis(tmp_path, screen)
    path = analysis / table
    lines = path.read_text().splitlines()
    assert len(lines) > 3
    lines[1] = lines[2]
    path.write_text("\n".join(lines) + "\n")
    _rehash(analysis, table)
    with pytest.raises(sel.B3SelectionError, match=needle):
        _select(analysis, tmp_path / "sel")
    assert not (tmp_path / "sel").exists()


def test_selection_requires_verified_analysis_and_real_commit(
        tmp_path, screen):
    runs = _go_tree(tmp_path, screen)
    bp.bind_job_id(runs, "424242")
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


def test_selection_rejects_duplicate_key_json(tmp_path, screen):
    """Pre-fix reproduction: duplicate JSON keys were silently last-wins."""
    analysis = _go_analysis(tmp_path, screen)
    path = analysis / "DECISION.json"
    raw = path.read_bytes()
    needle = b'  "state": "GO",'
    assert needle in raw
    path.write_bytes(raw.replace(
        needle, needle + b'\n  "state": "GO",', 1))
    _rehash(analysis, "DECISION.json")
    with pytest.raises(sel.B3SelectionError, match="duplicate JSON key"):
        _select(analysis, tmp_path / "sel")
    assert not (tmp_path / "sel").exists()


@pytest.mark.parametrize("table, field, value, message", [
    ("cell_intervals.csv", "dictator_gap", "0.009", "does not recompute"),
    ("matched_contrasts.csv", "delta_width", "0.009", "recomputed"),
    ("setting_summary.csv", "rank", "4", "disagrees"),
])
def test_selection_reconstructs_every_derived_field(
        tmp_path, screen, table, field, value, message):
    analysis = _go_analysis(tmp_path, screen)
    path = analysis / table
    rows = list(csv.DictReader(open(path)))
    rows[0][field] = value
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    _rehash(analysis, table)
    with pytest.raises(sel.B3SelectionError, match=message):
        _select(analysis, tmp_path / "sel")
    assert not (tmp_path / "sel").exists()


def test_selection_requires_exact_raw_job_binding(tmp_path, screen):
    analysis = _go_analysis(tmp_path, screen)
    _edit_json(
        analysis / "MANIFEST.json",
        lambda manifest: manifest.update(raw_binding=None))
    with pytest.raises(sel.B3SelectionError, match="raw_binding is missing"):
        _select(analysis, tmp_path / "sel")
    assert not (tmp_path / "sel").exists()


@pytest.mark.parametrize("field,bad", [
    ("raw_tree_sha256", "0" * 64),
    ("job_id", "999999"),
    ("job_sha256", "1" * 64),
])
def test_selection_names_each_raw_binding_disagreement(
        tmp_path, screen, field, bad):
    analysis = _go_analysis(tmp_path, screen)
    decision_path = analysis / "DECISION.json"
    decision = json.loads(decision_path.read_text())
    decision["inputs"]["raw_binding"][field] = bad
    decision_path.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n")
    manifest_path = analysis / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["raw_binding"][field] = bad
    manifest["decision_document"] = decision
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _rehash(analysis, "DECISION.json")
    with pytest.raises(
            sel.B3SelectionError,
            match=rf"raw_binding mismatch for {field}"):
        _select(analysis, tmp_path / "sel")
    assert not (tmp_path / "sel").exists()


def test_selection_refuses_fabricated_go_without_matching_runs(
        tmp_path, screen):
    runs_a, analysis_a = _packable(tmp_path / "a", screen)
    with pytest.raises(
            sel.B3SelectionError, match="raw runs tree is unreadable"):
        sel.select(
            tmp_path / "no-such-runs", analysis_a,
            tmp_path / "sel-missing", CODE,
            verify_code_commit=False,
            expected_raw_anchor=_synthetic_anchor(runs_a))
    assert not (tmp_path / "sel-missing").exists()

    runs_b = Path(_go_tree(tmp_path / "b", screen))
    _materialize_jsonl(runs_b)
    bp.bind_job_id(runs_b, "999999")
    (runs_b / "AUDIT.md").write_text("# Different synthetic raw tree\n")
    with pytest.raises(
            sel.B3SelectionError,
            match="analysis raw_binding mismatch for raw_tree_sha256"):
        sel.select(
            runs_b, analysis_a, tmp_path / "sel", CODE,
            verify_code_commit=False,
            expected_raw_anchor=_synthetic_anchor(runs_b))
    assert runs_a != runs_b
    assert not (tmp_path / "sel").exists()


def test_selector_refuses_live_tree_that_misses_preanalysis_anchor(
        tmp_path, screen):
    analysis = _go_analysis(tmp_path, screen)
    runs = _ANALYSIS_RUNS[str(analysis.resolve())]
    wrong_anchor = dict(_synthetic_anchor(runs))
    wrong_anchor["total_bytes"] += 1
    with pytest.raises(
            sel.B3SelectionError,
            match="live raw-tree anchor mismatch for total_bytes"):
        sel.select(
            runs, analysis, tmp_path / "sel", CODE,
            verify_code_commit=False,
            expected_raw_anchor=wrong_anchor)
    assert not (tmp_path / "sel").exists()


def test_selection_rejects_toctou_replacement_before_commit(
        tmp_path, screen, monkeypatch):
    analysis = _go_analysis(tmp_path, screen)
    victim = analysis / "cell_intervals.csv"
    real_publish = sel.publish_flat_directory_no_replace

    def replace_then_publish(*args, **kwargs):
        replacement = victim.with_name(".replacement")
        replacement.write_bytes(victim.read_bytes())
        os.replace(replacement, victim)  # same bytes, different opened inode
        return real_publish(*args, **kwargs)

    monkeypatch.setattr(
        sel, "publish_flat_directory_no_replace", replace_then_publish)
    with pytest.raises(sel.B3SelectionError, match="changed after immutable"):
        _select(analysis, tmp_path / "sel")
    # A post-rename refusal remains explicitly guarded, never authoritative.
    assert (tmp_path / "sel" / ".publication-incomplete").exists()


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
    (runs / "AUDIT.md").write_text(
        "# Synthetic B3 audit report\n\n- result: PASS\n")
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
    assert set(manifest["code_provenance"]) == set(pk.PROVENANCE_FILES)
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


def test_raw_tree_accepts_only_optional_audit_report(tmp_path, screen):
    runs = Path(_go_tree(tmp_path, screen))
    _materialize_jsonl(runs)
    bp.bind_job_id(runs, "424242")
    assert "AUDIT.md" not in {
        row["path"] for row in pk.validate_raw_tree(runs)["snapshot"]["files"]}

    (runs / "AUDIT.md").write_text("# Synthetic documented audit\n")
    validated = pk.validate_raw_tree(runs)
    assert "AUDIT.md" in {
        row["path"] for row in validated["snapshot"]["files"]}

    rogue = runs / "NOT_THE_AUDIT.txt"
    rogue.write_text("unexpected\n")
    with pytest.raises(
            PackagingError, match=r"unexpected=\['NOT_THE_AUDIT.txt'\]"):
        pk.validate_raw_tree(runs)
    rogue.unlink()

    required = runs / bp.build_cells()[0]["tag"] / "a2.oracle.jsonl"
    required.unlink()
    with pytest.raises(PackagingError, match="a2.oracle.jsonl"):
        pk.validate_raw_tree(runs)


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


def test_pack_refuses_hard_linked_source_files(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    victim = runs / "S0_baseline_s0_n8_b0.01" / "a2.oracle.jsonl"
    outside = tmp_path / "outside.jsonl"
    outside.write_bytes(victim.read_bytes())
    victim.unlink()
    os.link(outside, victim)
    with pytest.raises(PackagingError, match="hard-linked|unsafe linked"):
        _pack(runs, analysis, tmp_path / "bundles")
    assert not (tmp_path / "bundles").exists()


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
                       match="does not authenticate the exact MANIFEST"):
        _pack(runs, analysis, tmp_path / "b2")


def test_pack_first_quiescence_precedes_outcome_inventory(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)

    def active(job_id):
        assert job_id == "424242"
        raise PackagingError(f"Slurm job {job_id} is still active")

    with mock.patch.object(
            pk, "snapshot_source",
            side_effect=AssertionError("outcome inventory ran too early")):
        with pytest.raises(PackagingError, match="still active"):
            pk.pack(
                runs, analysis, tmp_path / "bundles", CODE,
                verify_commit=False, job_quiescence_validator=active)
    assert not (tmp_path / "bundles").exists()


def test_pack_detects_mutation_during_packaging(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    victim = runs / "S0_baseline_s0_n8_b0.01" / "a2.oracle.jsonl"
    real_freeze = pk.freeze_source
    state = {"mutated": False}

    def mutating_freeze(source, destination):
        snapshot = real_freeze(source, destination)
        if not state["mutated"] and Path(source).resolve() == runs.resolve():
            state["mutated"] = True
            victim.write_bytes(victim.read_bytes() + b"\n")
        return snapshot

    orig = pk.freeze_source
    pk.freeze_source = mutating_freeze
    try:
        with pytest.raises(PackagingError, match="mutated during packaging"):
            _pack(runs, analysis, tmp_path / "b1")
    finally:
        pk.freeze_source = orig
    assert state["mutated"]


def test_pack_refuses_cross_run_analysis(tmp_path, screen):
    """An analysis artifact produced from a DIFFERENT run manifest is
    refused."""
    runs, analysis = _packable(tmp_path, screen)
    manifest = json.loads((analysis / "MANIFEST.json").read_text())
    manifest["run_manifest_sha256"] = "3" * 64
    (analysis / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(
            PackagingError,
            match="run_manifest_sha256 mismatch|DIFFERENT run manifest"):
        _pack(runs, analysis, tmp_path / "b1")


def test_pack_refuses_cross_job_analysis(tmp_path, screen):
    """Review reproduction (BLOCKER): the design manifest is SHARED across
    jobs, so one job's raw results packaged with another job's GO analysis
    used to pass.  The raw-tree digest and Slurm job binding recorded in
    the analysis must now match the exact raw tree being packaged."""
    runs_a = Path(_go_tree(tmp_path, screen, name="runsA"))
    _materialize_jsonl(runs_a)
    bp.bind_job_id(runs_a, "424242")
    analysis_a = Path(_analyze(runs_a, tmp_path / "analysisA"))
    runs_b = Path(_go_tree(tmp_path, screen, name="runsB"))
    _materialize_jsonl(runs_b)
    bp.bind_job_id(runs_b, "424243")
    # same design manifest => identical run-manifest SHA on both sides,
    # which is exactly why the SHA alone was insufficient
    assert pk.sha256_file(runs_a / "MANIFEST.json") == pk.sha256_file(
        runs_b / "MANIFEST.json")
    with pytest.raises(PackagingError,
                       match="raw_binding mismatch for raw_tree_sha256"):
        _pack(runs_b, analysis_a, tmp_path / "b1")
    assert not (tmp_path / "b1").exists()


def test_pack_requires_verified_scoreable_analysis(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    unverified = tmp_path / "unverified"
    shutil.copytree(analysis, unverified)
    _edit_json(unverified / "MANIFEST.json",
               lambda m: m.update(analysis_code_verified=False))
    with pytest.raises(PackagingError, match="without code verification"):
        _pack(runs, unverified, tmp_path / "b1")
    drifted = tmp_path / "drifted-screen"
    shutil.copytree(analysis, drifted)
    _edit_json(drifted / "MANIFEST.json",
               lambda m: m.update(frozen_screen_verified=False))
    with pytest.raises(PackagingError, match="non-scoreable"):
        _pack(runs, drifted, tmp_path / "b2")
    unbound = tmp_path / "unbound"
    shutil.copytree(analysis, unbound)
    _edit_json(unbound / "MANIFEST.json",
               lambda m: m.update(raw_binding=None))
    with pytest.raises(PackagingError, match="raw_binding is missing"):
        _pack(runs, unbound, tmp_path / "b3")


def test_pack_refuses_noncanonical_job_id(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    for bad in ("0042", "42; scancel", "", 424242):
        job = json.loads((runs / "JOB.json").read_text())
        job["job_id"] = bad
        (runs / "JOB.json").write_text(
            json.dumps(job, indent=2, sort_keys=True) + "\n")
        with pytest.raises(PackagingError,
                           match="canonical Slurm job id|malformed"):
            _pack(runs, analysis, tmp_path / "b1")
    assert not (tmp_path / "b1").exists()


def test_pack_reverifies_quiescence_before_rename(tmp_path, screen):
    """A job that becomes active again mid-packaging refuses at the second
    (immediately-pre-rename) quiescence gate; no bundle is published."""
    runs, analysis = _packable(tmp_path, screen)
    calls = {"n": 0}

    def flaky(job_id):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise PackagingError(f"Slurm job {job_id} is still active")

    with pytest.raises(PackagingError, match="still active"):
        pk.pack(runs, analysis, tmp_path / "b1", CODE,
                verify_commit=False, job_quiescence_validator=flaky)
    assert calls["n"] == 2
    assert not (tmp_path / "b1").exists()


def test_pack_post_rename_failure_stays_explicitly_incomplete(
        tmp_path, screen, monkeypatch):
    runs, analysis = _packable(tmp_path, screen)
    real_unlink = pk.os.unlink

    def fail_guard_unlink(path, *args, **kwargs):
        if path == pk.INCOMPLETE_MARKER:
            raise OSError("synthetic marker unlink failure")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(pk.os, "unlink", fail_guard_unlink)
    out = tmp_path / "bundles"
    with pytest.raises(PackagingError, match="incomplete|guarded"):
        _pack(runs, analysis, out)
    published = [path for path in out.iterdir() if path.is_dir()]
    assert len(published) == 1
    guarded = published[0]
    assert (guarded / pk.INCOMPLETE_MARKER).exists()
    assert (guarded / pk.BUNDLE_COMPLETE_FILENAME).exists()
    with pytest.raises(PackagingError, match="incomplete-publication"):
        pk.import_bundle(guarded, tmp_path / "dest")
    assert not (tmp_path / "dest").exists()


def test_pack_and_import_path_isolation(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    with pytest.raises(PackagingError, match="disjoint"):
        _pack(runs, analysis, runs / "bundles")
    with pytest.raises(PackagingError, match="disjoint"):
        _pack(runs, analysis, analysis / "bundles")
    # the A6 refusal fires BEFORE any recursive read: the path does not
    # even exist, so any read attempt would raise a different error
    with pytest.raises(PackagingError, match="A6"):
        pk.pack(tmp_path / "a6_holdout" / "runs", analysis,
                tmp_path / "b2", CODE, verify_commit=False,
                job_quiescence_validator=lambda j: None)
    with pytest.raises(PackagingError, match="A6"):
        _pack(runs, analysis, tmp_path / "result_a6_mirror")
    bundle = Path(_pack(runs, analysis, tmp_path / "bundles")["bundle_dir"])
    with pytest.raises(PackagingError, match="disjoint"):
        pk.import_bundle(bundle, bundle / "imported")
    with pytest.raises(PackagingError, match="A6"):
        pk.import_bundle(bundle, tmp_path / "a6_holdout" / "dest")
    assert not (tmp_path / "a6_holdout").exists()


def _rewrite_bundle_manifest(work, fn):
    """Coordinated bundle tamper: edit the manifest, keep it canonical,
    and rebind the completion record to the new manifest bytes."""
    manifest = json.loads((work / "BUNDLE_MANIFEST.json").read_bytes())
    fn(manifest)
    from experiments.package_a6_holdout import _canonical_json_bytes
    raw = _canonical_json_bytes(manifest)
    (work / "BUNDLE_MANIFEST.json").write_bytes(raw)
    import hashlib
    (work / "BUNDLE_COMPLETE.json").write_bytes(_canonical_json_bytes({
        "schema": "b3-factor-pilot-bundle-complete-v1",
        "bundle_manifest_sha256": hashlib.sha256(raw).hexdigest(),
    }))


def test_import_refuses_incomplete_or_uncommitted_bundle(tmp_path, screen):
    """Failure must not look like success: a bundle carrying the
    incomplete marker, or lacking the completion record, or with a
    completion record bound to different manifest bytes, refuses."""
    runs, analysis = _packable(tmp_path, screen)
    bundle = Path(_pack(runs, analysis, tmp_path / "bundles")["bundle_dir"])
    marked = tmp_path / "marked"
    shutil.copytree(bundle, marked)
    (marked / pk.INCOMPLETE_MARKER).write_text("{}\n")
    with pytest.raises(PackagingError, match="incomplete-publication"):
        pk.import_bundle(marked, tmp_path / "d1")
    uncommitted = tmp_path / "uncommitted"
    shutil.copytree(bundle, uncommitted)
    (uncommitted / "BUNDLE_COMPLETE.json").unlink()
    with pytest.raises(PackagingError, match="lacks the completion marker"):
        pk.import_bundle(uncommitted, tmp_path / "d2")
    unbound = tmp_path / "unbound-complete"
    shutil.copytree(bundle, unbound)
    _rewrite_bundle_manifest(unbound, lambda m: None)
    _edit_json(unbound / "BUNDLE_COMPLETE.json",
               lambda d: d.update(bundle_manifest_sha256="0" * 64))
    with pytest.raises(PackagingError, match="does not bind"):
        pk.import_bundle(unbound, tmp_path / "d3")
    for d in ("d1", "d2", "d3"):
        assert not (tmp_path / d).exists()


def test_import_rejects_duplicate_key_manifest(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    bundle = Path(_pack(runs, analysis, tmp_path / "bundles")["bundle_dir"])
    work = tmp_path / "duplicate-json"
    shutil.copytree(bundle, work)
    manifest = work / pk.BUNDLE_MANIFEST_FILENAME
    raw = manifest.read_bytes()
    needle = b'  "schema": "b3-factor-pilot-bundle-v1"'
    assert needle in raw
    manifest.write_bytes(raw.replace(
        needle, needle + b',\n  "schema": "b3-factor-pilot-bundle-v1"', 1))
    with pytest.raises(PackagingError, match="duplicate JSON key"):
        pk.import_bundle(work, tmp_path / "dest")
    assert not (tmp_path / "dest").exists()


def test_import_rejects_toctou_bundle_replacement(
        tmp_path, screen, monkeypatch):
    runs, analysis = _packable(tmp_path, screen)
    bundle = Path(_pack(runs, analysis, tmp_path / "bundles")["bundle_dir"])
    victim = bundle / pk.BUNDLE_MANIFEST_FILENAME
    real_snapshot = pk.snapshot_source
    calls = {"bundle": 0}

    def replace_on_final_revalidation(root):
        if Path(root).resolve() == bundle.resolve():
            calls["bundle"] += 1
            if calls["bundle"] == 2:
                victim.write_bytes(victim.read_bytes() + b"\n")
        return real_snapshot(root)

    monkeypatch.setattr(pk, "snapshot_source", replace_on_final_revalidation)
    with pytest.raises(PackagingError, match="changed immediately"):
        pk.import_bundle(bundle, tmp_path / "dest")
    assert calls["bundle"] == 2
    assert not (tmp_path / "dest").exists()


def test_import_post_rename_failure_stays_explicitly_incomplete(
        tmp_path, screen, monkeypatch):
    runs, analysis = _packable(tmp_path, screen)
    bundle = Path(_pack(runs, analysis, tmp_path / "bundles")["bundle_dir"])
    real_unlink = pk.os.unlink

    def fail_guard_unlink(path, *args, **kwargs):
        if path == pk.IMPORT_INCOMPLETE_MARKER:
            raise OSError("synthetic import marker unlink failure")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(pk.os, "unlink", fail_guard_unlink)
    destination = tmp_path / "dest"
    with pytest.raises(PackagingError, match="incomplete|guarded"):
        pk.import_bundle(bundle, destination)
    assert (destination / pk.IMPORT_INCOMPLETE_MARKER).exists()


def test_import_reapplies_population_and_manifest_contract(
        tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    bundle = Path(_pack(runs, analysis, tmp_path / "bundles")["bundle_dir"])

    empty_runs = tmp_path / "empty-runs"
    shutil.copytree(bundle, empty_runs)
    shutil.rmtree(empty_runs / "runs")
    (empty_runs / "runs").mkdir()
    with pytest.raises(PackagingError, match="empty raw tree"):
        pk.import_bundle(empty_runs, tmp_path / "d1")

    empty_analysis = tmp_path / "empty-analysis"
    shutil.copytree(bundle, empty_analysis)
    shutil.rmtree(empty_analysis / "analysis")
    (empty_analysis / "analysis").mkdir()
    with pytest.raises(PackagingError, match="empty analysis artifact"):
        pk.import_bundle(empty_analysis, tmp_path / "d2")

    no_cells = tmp_path / "no-cells"
    shutil.copytree(bundle, no_cells)
    _rewrite_bundle_manifest(no_cells,
                             lambda m: m["raw"].update(cells={}))
    with pytest.raises(PackagingError, match="cells are empty"):
        pk.import_bundle(no_cells, tmp_path / "d3")

    traversal = tmp_path / "traversal"
    shutil.copytree(bundle, traversal)

    def add_traversal(m):
        files = next(iter(m["raw"]["cells"].values()))
        m["raw"]["cells"]["../evil"] = dict(files)
    _rewrite_bundle_manifest(traversal, add_traversal)
    with pytest.raises(PackagingError, match="unsafe bundle manifest path"):
        pk.import_bundle(traversal, tmp_path / "d4")

    absolute = tmp_path / "absolute"
    shutil.copytree(bundle, absolute)

    def add_absolute(m):
        files = next(iter(m["raw"]["cells"].values()))
        m["raw"]["cells"]["/tmp/evil"] = dict(files)
    _rewrite_bundle_manifest(absolute, add_absolute)
    with pytest.raises(PackagingError, match="unsafe bundle manifest path"):
        pk.import_bundle(absolute, tmp_path / "d4a")

    swapped_job = tmp_path / "swapped-job"
    shutil.copytree(bundle, swapped_job)
    _rewrite_bundle_manifest(
        swapped_job, lambda m: m["raw"].update(job_id="999999"))
    with pytest.raises(PackagingError,
                       match="job id differs from the raw tree"):
        pk.import_bundle(swapped_job, tmp_path / "d5")

    swapped_job_bytes = tmp_path / "swapped-job-bytes"
    shutil.copytree(bundle, swapped_job_bytes)
    _rewrite_bundle_manifest(
        swapped_job_bytes,
        lambda m: m["raw"].update(job_sha256="0" * 64))
    with pytest.raises(PackagingError, match="raw contract differs"):
        pk.import_bundle(swapped_job_bytes, tmp_path / "d5a")

    dropped_cell = tmp_path / "dropped-cell"
    shutil.copytree(bundle, dropped_cell)
    tag = bp.build_cells()[0]["tag"]
    shutil.rmtree(dropped_cell / "runs" / tag)
    with pytest.raises(PackagingError, match="population differs"):
        pk.import_bundle(dropped_cell, tmp_path / "d6")
    for d in ("d1", "d2", "d3", "d4", "d4a", "d5", "d5a", "d6"):
        assert not (tmp_path / d).exists()


def test_import_rejects_tampered_bundle(tmp_path, screen):
    runs, analysis = _packable(tmp_path, screen)
    bundle = Path(_pack(runs, analysis, tmp_path / "bundles")["bundle_dir"])
    victim = bundle / "runs" / "S1_batt_low_s0_n8_b0.01" / "a2.cg.ckpt.json"
    # bundle trees are read-only after install; work on a copy
    work = tmp_path / "bundle-copy"
    shutil.copytree(bundle, work)
    victim = work / "runs" / "S1_batt_low_s0_n8_b0.01" / "a2.cg.ckpt.json"
    victim.write_bytes(victim.read_bytes() + b"\n")
    with pytest.raises(PackagingError, match="digest|raw_binding mismatch"):
        pk.import_bundle(work, tmp_path / "dest")
    assert not (tmp_path / "dest").exists()
