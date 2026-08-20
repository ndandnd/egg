"""B3 no-solver certified-uplift baseline battery.

Runs against the COMMITTED canonical input (read-only) plus tampered
copies; asserts the solver-free import closure, full-population
validation, uplift arithmetic, witness consistency, determinism, and
publication hygiene."""
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import experiments.analyze_b3_baseline as mod

CANONICAL = Path(mod.CANONICAL_INPUT)


def _analyze(input_dir, out, stamp="B3TEST"):
    return mod.analyze(input_dir, out, stamp, "deadbeef",
                       verify_code_commit=False)


def _tampered_copy(tmp_path, name):
    dst = tmp_path / name
    shutil.copytree(CANONICAL, dst,
                    ignore=shutil.ignore_patterns("*.png"))
    return dst


def _rewrite_cells(root, mutate):
    """Apply `mutate(rows)` and refresh the manifest hash so integrity
    passes and the semantic gate under test is what fires."""
    cells = root / "cells.csv"
    with open(cells, newline="") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames)
        rows = list(reader)
    mutate(rows)
    with open(cells, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = root / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["outputs"]["cells.csv"] = mod.sha256_file(cells)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def test_analyzer_import_closure_is_solver_free():
    """Importing and exercising the analyzer must not load egglab,
    python-mip, Gurobi/CBC bindings, or the numerical stack."""
    script = (
        "import sys, os\n"
        "sys.path.insert(0, os.getcwd())\n"
        "import experiments.analyze_b3_baseline as mod\n"
        "population = mod.load_canonical_population(mod.CANONICAL_INPUT)\n"
        "mod.analyze_population(population['rows'])\n"
        "banned = ('egglab', 'mip', 'gurobipy', 'pandas', 'numpy',"
        " 'matplotlib')\n"
        "loaded = [m for m in sys.modules"
        " if m.split('.')[0] in banned]\n"
        "assert not loaded, loaded\n"
        "print('SOLVER_FREE')\n"
    )
    out = subprocess.check_output(
        [sys.executable, "-c", script],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert b"SOLVER_FREE" in out


def test_end_to_end_baseline_on_committed_population(tmp_path):
    out_dir = Path(_analyze(CANONICAL, tmp_path / "out"))
    baseline = list(csv.DictReader(open(out_dir / "uplift_baseline.csv")))
    assert len(baseline) == 64
    assert {(r["seed"], r["n_trips"], r["b"]) for r in baseline} == {
        (str(s), str(n), b) for s in range(16)
        for n in (8, 12) for b in ("0.01", "0.05")}
    for row in baseline:
        lo, hi = float(row["uplift_lo"]), float(row["uplift_hi"])
        assert hi >= lo
        assert hi >= -mod.SERIALIZATION_TOL
        assert abs((hi - lo) - float(row["width"])) < 1e-12
        # recomputation identity from the emitted fields themselves
        assert lo == pytest.approx(
            (float(row["z_d_ub"]) - float(row["tol_d"]))
            - float(row["ub_ch"]), abs=1e-12)
        assert hi == pytest.approx(
            float(row["z_d_ub"]) - float(row["lb_best"]), abs=1e-12)
    witnesses = list(
        csv.DictReader(open(out_dir / "witness_consistency.csv")))
    assert len(witnesses) == 192
    assert all(r["intersects_a2"] == "True" for r in witnesses)
    assert all(r["z_d_ub_equal"] == "True" for r in witnesses)
    strata = list(csv.DictReader(open(out_dir / "strata_summary.csv")))
    assert [r["scope"] for r in strata] == [
        "overall", "n8_b0.01", "n8_b0.05", "n12_b0.01", "n12_b0.05"]
    assert all(r["n_negative_hi"] == "0" for r in strata)
    summary = (out_dir / "SUMMARY.md").read_text()
    assert "RETROSPECTIVE / EXPLORATORY" in summary
    manifest = json.loads((out_dir / "MANIFEST.json").read_text())
    assert manifest["schema"] == mod.SCHEMA
    assert manifest["label"] == "retrospective-exploratory"
    assert manifest["inputs"]["cells_csv"]["sha256"] == mod.sha256_file(
        CANONICAL / "cells.csv")
    assert manifest["inputs"]["b2_analysis_code_commit"] == (
        "71d4c378768a7c3a882a2236e9c2ce92d98e8b23")
    for name, sha in manifest["outputs"].items():
        assert mod.sha256_file(out_dir / name) == sha


def test_regeneration_is_byte_identical(tmp_path):
    first = Path(_analyze(CANONICAL, tmp_path / "a"))
    second = Path(_analyze(CANONICAL, tmp_path / "b"))
    names = sorted(p.name for p in first.iterdir())
    assert names == sorted(p.name for p in second.iterdir())
    for name in names:
        assert (first / name).read_bytes() == (second / name).read_bytes(), (
            name)


def test_committed_input_is_never_modified(tmp_path):
    before = {p.name: mod.sha256_file(p)
              for p in CANONICAL.iterdir() if p.is_file()}
    _analyze(CANONICAL, tmp_path / "out")
    after = {p.name: mod.sha256_file(p)
             for p in CANONICAL.iterdir() if p.is_file()}
    assert before == after


def test_existing_output_directory_refused(tmp_path):
    _analyze(CANONICAL, tmp_path / "out")
    with pytest.raises(mod.B3Error, match="refusing existing output"):
        _analyze(CANONICAL, tmp_path / "out")
    assert not list((tmp_path / "out").glob(".B3TEST.b3-staging-*"))


def test_input_hash_mismatch_rejected(tmp_path):
    bad = _tampered_copy(tmp_path, "hash-tamper")
    with open(bad / "cells.csv", "a") as handle:
        handle.write("# tampered\n")
    with pytest.raises(mod.B3Error, match="hash mismatch"):
        _analyze(bad, tmp_path / "out")


def test_row_count_and_duplicate_rejected(tmp_path):
    bad = _tampered_copy(tmp_path, "dropped-row")
    _rewrite_cells(bad, lambda rows: rows.pop())
    with pytest.raises(mod.B3Error, match="exactly 256"):
        _analyze(bad, tmp_path / "out-drop")

    bad = _tampered_copy(tmp_path, "duplicate-row")
    _rewrite_cells(bad, lambda rows: rows.__setitem__(
        1, dict(rows[0])))
    with pytest.raises(mod.B3Error, match="duplicate method-cell"):
        _analyze(bad, tmp_path / "out-dup")


def test_uncertified_row_rejected(tmp_path):
    bad = _tampered_copy(tmp_path, "uncertified")

    def flip(rows):
        rows[10]["certified"] = "False"

    _rewrite_cells(bad, flip)
    with pytest.raises(mod.B3Error, match="not certified"):
        _analyze(bad, tmp_path / "out")


def test_falsified_uplift_beyond_serialization_tol_rejected(tmp_path):
    bad = _tampered_copy(tmp_path, "uplift-tamper")

    def falsify(rows):
        rows[0]["uplift_lo"] = repr(float(rows[0]["uplift_lo"]) + 1e-6)

    _rewrite_cells(bad, falsify)
    with pytest.raises(mod.B3Error, match="serialization"):
        _analyze(bad, tmp_path / "out")


def test_dictator_evidence_divergence_rejected(tmp_path):
    bad = _tampered_copy(tmp_path, "zd-tamper")

    def diverge(rows):
        for row in rows:
            if row["method"] == "a3":
                # coordinated: keep the recorded uplifts consistent with
                # the tampered z_d_ub so only the witness gate can fire
                z = float(row["z_d_ub"]) + 0.001
                row["z_d_ub"] = repr(z)
                row["uplift_lo"] = repr(
                    (z - float(row["tol_d"])) - float(row["ub_ch"]))
                row["uplift_hi"] = repr(z - float(row["lb_best"]))
                break

    _rewrite_cells(bad, diverge)
    with pytest.raises(mod.B3Error, match="dictator evidence"):
        _analyze(bad, tmp_path / "out")


def test_witness_disjoint_interval_rejected(tmp_path):
    bad = _tampered_copy(tmp_path, "witness-tamper")

    def disjoint(rows):
        for row in rows:
            if row["method"] == "a4":
                # push the witness interval fully above a2's while keeping
                # every per-row gate satisfied: same z_d_ub, tighter bounds
                z = float(row["z_d_ub"])
                row["ub_ch"] = repr(z - 0.019)
                row["lb_best"] = repr(z - 0.0195)
                row["uplift_lo"] = repr(
                    (z - float(row["tol_d"])) - float(row["ub_ch"]))
                row["uplift_hi"] = repr(z - float(row["lb_best"]))
                break

    _rewrite_cells(bad, disjoint)
    with pytest.raises(mod.B3Error, match="does not intersect"):
        _analyze(bad, tmp_path / "out")


def test_code_commit_verification(tmp_path, monkeypatch):
    with pytest.raises(mod.B3Error, match="hexadecimal"):
        mod.verify_analysis_code_commit("NOT-HEX")

    def fake_git(args, cwd=None):
        if args[1] == "rev-parse":
            return b"abc123def4567890abc123def4567890abc123de\n"
        return b" M src/experiments/analyze_b3_baseline.py\n"

    monkeypatch.setattr(mod.subprocess, "check_output", fake_git)
    with pytest.raises(mod.B3Error, match="does not match"):
        mod.verify_analysis_code_commit("deadbee")
    with pytest.raises(mod.B3Error, match="tracked modifications"):
        mod.verify_analysis_code_commit("abc123d")
