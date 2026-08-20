"""B3 no-solver certified-uplift baseline battery.

Runs against the COMMITTED canonical input (read-only) plus tampered
copies; asserts the solver-free import closure, pinned-hash and
population validation, four-way cross-method intersection, paired-effect
arithmetic, classification, provenance verification, portable
byte-identical regeneration, A6-path refusal, and emitted claim
limitations.  Fixture injection through :func:`analyze`'s input parameter
is test-only; the production CLI is pinned to the canonical B2 input."""
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
    return mod.analyze(input_dir, out, stamp, "deadbeef" * 5,
                       verify_code_commit=False)


def _tampered_copy(tmp_path, name):
    dst = tmp_path / name
    shutil.copytree(CANONICAL, dst,
                    ignore=shutil.ignore_patterns("*.png"))
    return dst


def _rewrite_cells(root, mutate):
    """Apply `mutate(rows)` and refresh BOTH hash gates (the manifest's
    recorded hash and the module's pinned hashes) so the semantic gate
    under test is what fires.  Test-only monkeypatching of the pins."""
    cells = root / "cells.csv"
    with open(cells, newline="") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames)
        rows = list(reader)
    mutate(rows)
    with open(cells, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns,
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = root / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["outputs"]["cells.csv"] = mod.sha256_file(cells)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return cells, manifest_path


@pytest.fixture
def unpinned(monkeypatch):
    """Repoint the pinned hashes at a tampered fixture (test-only)."""

    def repin(root):
        monkeypatch.setattr(mod, "PINNED_CELLS_SHA256",
                            mod.sha256_file(root / "cells.csv"))
        monkeypatch.setattr(mod, "PINNED_B2_MANIFEST_SHA256",
                            mod.sha256_file(root / "MANIFEST.json"))

    return repin


def test_analyzer_import_closure_is_solver_free():
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
    instances = list(csv.DictReader(open(out_dir / "instance_uplift.csv")))
    assert len(instances) == 64
    assert {(r["seed"], r["n_trips"], r["b"]) for r in instances} == {
        (str(s), str(n), b) for s in range(16)
        for n in (8, 12) for b in ("0.01", "0.05")}
    classes = [r["classification"] for r in instances]
    # smoke check (recomputed, not hard-coded in the analyzer)
    assert classes.count("strictly-positive") == 38
    assert classes.count("strict-zero-crossing") == 21
    assert classes.count("exact-zero-boundary") == 5
    for row in instances:
        lo = float(row["uplift_lo_raw"])
        hi = float(row["uplift_hi_raw"])
        n = int(row["n_trips"])
        assert hi >= lo and hi >= -mod.SERIALIZATION_TOL
        assert float(row["uplift_lo_tightened"]) == max(0.0, lo)
        assert abs((hi - lo) - float(row["width"])) < 1e-12
        assert float(row["uplift_lo_per_trip"]) == lo / n
        assert float(row["uplift_hi_per_trip"]) == hi / n
        assert lo == pytest.approx(
            (float(row["z_d_ub"]) - float(row["tol_d"]))
            - float(row["ub_ch"]), abs=1e-12)
        assert hi == pytest.approx(
            float(row["z_d_ub"]) - float(row["lb_best"]), abs=1e-12)
        assert (float(row["intersection_lo"])
                <= float(row["intersection_hi"]))

    audit = list(csv.DictReader(open(out_dir / "cross_method_audit.csv")))
    assert len(audit) == 64
    assert all(r["intersection_nonempty"] == "True" for r in audit)
    assert all(r["pass"] == "True" for r in audit)
    max_spread = max(float(r["max_spread"]) for r in audit)
    assert max_spread == pytest.approx(0.00759389, abs=1e-6)

    paired = list(csv.DictReader(open(out_dir / "paired_effects.csv")))
    assert len(paired) == 64
    feedback = [r for r in paired if r["family"] == "feedback_b"]
    workload = [r for r in paired if r["family"] == "workload_n"]
    assert len(feedback) == len(workload) == 32
    fc = [r["classification"] for r in feedback]
    wc = [r["classification"] for r in workload]
    assert (fc.count("strictly-positive"), fc.count("strictly-negative"),
            fc.count("crosses-or-touches-zero")) == (23, 1, 8)
    assert (wc.count("strictly-positive"), wc.count("strictly-negative"),
            wc.count("crosses-or-touches-zero")) == (19, 6, 7)
    # deterministic ordering: feedback block first, seed-major
    assert paired[0]["family"] == "feedback_b"
    assert [r["seed"] for r in feedback] == sorted(
        (r["seed"] for r in feedback), key=int)

    strata = list(csv.DictReader(open(out_dir / "strata_summary.csv")))
    assert [r["scope"] for r in strata] == [
        "overall", "n8_b0.01", "n8_b0.05", "n12_b0.01", "n12_b0.05"]
    overall = strata[0]
    assert (int(overall["n_positive"]), int(overall["n_crossing"]),
            int(overall["n_boundary"])) == (38, 21, 5)

    manifest = json.loads((out_dir / "MANIFEST.json").read_text())
    assert manifest["schema"] == mod.SCHEMA
    assert manifest["label"] == "retrospective-exploratory"
    cells_meta = manifest["inputs"]["cells_csv"]
    assert cells_meta["path"] == f"{mod.CANONICAL_RELDIR}/cells.csv"
    assert not cells_meta["path"].startswith("/")
    assert cells_meta["sha256"] == mod.PINNED_CELLS_SHA256
    assert cells_meta["row_count"] == 256
    assert cells_meta["unknown_mip_rows"] == 12
    assert "uplift_lo" in cells_meta["csv_header"]
    assert manifest["inputs"]["b2_manifest"]["sha256"] == (
        mod.PINNED_B2_MANIFEST_SHA256)
    assert manifest["inputs"]["b2_analysis_code_commit"] == (
        "71d4c378768a7c3a882a2236e9c2ce92d98e8b23")
    for name, sha in manifest["outputs"].items():
        assert mod.sha256_file(out_dir / name) == sha


def test_emitted_summary_carries_complete_boundary(tmp_path):
    out_dir = Path(_analyze(CANONICAL, tmp_path / "out"))
    summary = (out_dir / "SUMMARY.md").read_text()
    assert "RETROSPECTIVE / EXPLORATORY" in summary
    for claim in mod.SCIENTIFIC_BOUNDARY:
        assert claim in summary, claim
    assert ("heterogeneous and descriptive rather than causal" in summary)
    assert 'mip_version == "unknown"' in summary
    assert "12 of 256" in summary
    assert "NOT the primary normalization" in summary
    manifest = json.loads((out_dir / "MANIFEST.json").read_text())
    assert manifest["scientific_boundary"] == list(mod.SCIENTIFIC_BOUNDARY)


def test_no_crlf_in_emitted_csvs(tmp_path):
    out_dir = Path(_analyze(CANONICAL, tmp_path / "out"))
    for path in out_dir.glob("*.csv"):
        assert b"\r" not in path.read_bytes(), path.name


def test_regeneration_is_byte_identical_across_roots(tmp_path):
    """Portable determinism: two different absolute input/output roots
    produce byte-identical artifacts, including MANIFEST.json."""
    root_a = _tampered_copy(tmp_path / "deep/nested/rootA", "input")
    root_b = _tampered_copy(tmp_path / "other/rootB", "input")
    first = Path(_analyze(root_a, tmp_path / "outA"))
    second = Path(_analyze(root_b, tmp_path / "outB"))
    names = sorted(p.name for p in first.iterdir())
    assert names == sorted(p.name for p in second.iterdir())
    for name in names:
        assert (first / name).read_bytes() == (second / name).read_bytes(), (
            name)
    # and both match the canonical-root run byte for byte
    third = Path(_analyze(CANONICAL, tmp_path / "outC"))
    for name in names:
        assert (first / name).read_bytes() == (third / name).read_bytes(), (
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


def test_a6_paths_refused_before_any_io(tmp_path):
    """The scientific boundary refuses A6 input/output paths BEFORE any
    read or write."""
    a6_in = tmp_path / "runs" / "a6_holdout"
    a6_in.mkdir(parents=True)
    with pytest.raises(mod.B3Error, match="refusing A6 path"):
        mod.analyze(a6_in, tmp_path / "out", "S", "x" * 40,
                    verify_code_commit=False)
    a6_out = tmp_path / "result" / "a6_pilot"
    with pytest.raises(mod.B3Error, match="refusing A6 path"):
        mod.analyze(CANONICAL, a6_out, "S", "x" * 40,
                    verify_code_commit=False)
    assert not a6_out.exists()  # nothing was created
    assert not list(a6_in.iterdir())  # nothing was read or written


def test_pinned_hash_mismatch_rejected(tmp_path):
    bad = _tampered_copy(tmp_path, "hash-tamper")
    with open(bad / "cells.csv", "a") as handle:
        handle.write("# tampered\n")
    with pytest.raises(mod.B3Error, match="hash mismatch"):
        _analyze(bad, tmp_path / "out")


def test_b2_manifest_gates(tmp_path, unpinned):
    bad = _tampered_copy(tmp_path, "schema-tamper")
    manifest_path = bad / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["schema"] = "b2-other"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    unpinned(bad)
    with pytest.raises(mod.B3Error, match="schema"):
        _analyze(bad, tmp_path / "out-schema")

    bad = _tampered_copy(tmp_path, "verified-tamper")
    manifest_path = bad / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["analysis_code_verified"] = False
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    unpinned(bad)
    with pytest.raises(mod.B3Error, match="not code-verified"):
        _analyze(bad, tmp_path / "out-verified")


def test_missing_a2_and_incomplete_population_rejected(tmp_path, unpinned):
    bad = _tampered_copy(tmp_path, "missing-a2")

    def drop_a2(rows):
        index = next(i for i, r in enumerate(rows) if r["method"] == "a2")
        rows.pop(index)

    _rewrite_cells(bad, drop_a2)
    unpinned(bad)
    with pytest.raises(mod.B3Error, match="exactly 256"):
        _analyze(bad, tmp_path / "out-drop")

    bad = _tampered_copy(tmp_path, "duplicate-row")

    def duplicate(rows):
        rows[1] = dict(rows[0])

    _rewrite_cells(bad, duplicate)
    unpinned(bad)
    with pytest.raises(mod.B3Error, match="duplicate method-cell"):
        _analyze(bad, tmp_path / "out-dup")


@pytest.mark.parametrize("field,value,message", [
    ("method", "a9", "outside the frozen"),
    ("seed", "99", "outside the frozen"),
    ("n_trips", "10", "outside the frozen"),
    ("b", "0.02", "outside the frozen"),
    ("seed", "notanint", "malformed identity"),
])
def test_unexpected_identity_rejected(tmp_path, unpinned, field, value,
                                      message):
    bad = _tampered_copy(tmp_path, f"identity-{field}-{value}")

    def mutate(rows):
        rows[0][field] = value

    _rewrite_cells(bad, mutate)
    unpinned(bad)
    with pytest.raises(mod.B3Error, match=message):
        _analyze(bad, tmp_path / "out")


@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "notanumber", ""])
def test_nonfinite_and_nonnumeric_fields_rejected(tmp_path, unpinned, value):
    bad = _tampered_copy(tmp_path, f"numeric-{value or 'empty'}")

    def mutate(rows):
        rows[5]["ub_ch"] = value

    _rewrite_cells(bad, mutate)
    unpinned(bad)
    with pytest.raises(mod.B3Error, match="not (numeric|finite)"):
        _analyze(bad, tmp_path / "out")


def test_reversed_interval_and_endpoint_tampering_rejected(
        tmp_path, unpinned):
    bad = _tampered_copy(tmp_path, "reversed-interval")

    def reverse(rows):
        # lb_best above ub_ch + tol_d: hi < lo, a reversed interval;
        # keep recorded uplifts coordinated so the interval gate fires
        row = next(r for r in rows if r["method"] == "a2")
        z = float(row["z_d_ub"])
        row["lb_best"] = repr(float(row["ub_ch"]) + 0.02)
        row["uplift_hi"] = repr(z - float(row["lb_best"]))
        row["uplift_lo"] = repr(
            (z - float(row["tol_d"])) - float(row["ub_ch"]))

    _rewrite_cells(bad, reverse)
    unpinned(bad)
    with pytest.raises(mod.B3Error, match="empty uplift interval"):
        _analyze(bad, tmp_path / "out-rev")

    bad = _tampered_copy(tmp_path, "endpoint-tamper")

    def falsify(rows):
        rows[0]["uplift_lo"] = repr(float(rows[0]["uplift_lo"]) + 1e-6)

    _rewrite_cells(bad, falsify)
    unpinned(bad)
    with pytest.raises(mod.B3Error, match="serialization"):
        _analyze(bad, tmp_path / "out-end")


def test_pairwise_overlap_but_four_way_empty_rejected(tmp_path, unpinned):
    """The insufficiency the review identified: every witness interval
    intersects A2's, yet the four-way intersection is empty."""
    bad = _tampered_copy(tmp_path, "four-way-empty")

    def split(rows):
        # A2 spans [-tol, +eps]-ish; move a3 to hug its LEFT edge and a4
        # to hug its RIGHT edge so both meet a2 but not each other
        target = {}
        for row in rows:
            if row["seed"] == "0" and row["n_trips"] == "8" \
                    and row["b"] == "0.01":
                target[row["method"]] = row
        z = float(target["a2"]["z_d_ub"])
        tol = float(target["a2"]["tol_d"])

        def set_interval(row, lo, hi):
            # lo = (z - tol) - ub  =>  ub = z - tol - lo
            # hi = z - lb         =>  lb = z - hi
            row["ub_ch"] = repr(z - tol - lo)
            row["lb_best"] = repr(z - hi)
            row["uplift_lo"] = repr(
                (z - float(row["tol_d"])) - float(row["ub_ch"]))
            row["uplift_hi"] = repr(z - float(row["lb_best"]))

        # every per-row gate passes (hi >= 0, width <= 0.02) and every
        # witness intersects a2 — yet a3 and a4 are disjoint from each
        # other, so the four-way intersection is empty
        set_interval(target["a2"], -0.005, 0.005)   # centre
        set_interval(target["a3"], -0.009, 0.0001)  # hugs left of a2
        set_interval(target["a4"], 0.004, 0.009)    # hugs right of a2
        set_interval(target["a5"], -0.005, 0.005)

    _rewrite_cells(bad, split)
    unpinned(bad)
    with pytest.raises(mod.B3Error,
                       match="four-way certified-interval intersection"):
        _analyze(bad, tmp_path / "out")


def test_dictator_and_provenance_divergence_rejected(tmp_path, unpinned):
    bad = _tampered_copy(tmp_path, "zd-tamper")

    def diverge(rows):
        for row in rows:
            if row["method"] == "a3":
                z = float(row["z_d_ub"]) + 0.001
                row["z_d_ub"] = repr(z)
                row["uplift_lo"] = repr(
                    (z - float(row["tol_d"])) - float(row["ub_ch"]))
                row["uplift_hi"] = repr(z - float(row["lb_best"]))
                break

    _rewrite_cells(bad, diverge)
    unpinned(bad)
    with pytest.raises(mod.B3Error, match="dictator evidence"):
        _analyze(bad, tmp_path / "out-zd")

    for field, message in (
            ("backend", "not declared"),
            ("mip_version", "not declared"),
            ("source_commit", "not among")):
        bad = _tampered_copy(tmp_path, f"prov-{field}")

        def mutate(rows, field=field):
            rows[3][field] = "rogue"

        _rewrite_cells(bad, mutate)
        unpinned(bad)
        with pytest.raises(mod.B3Error, match=message):
            _analyze(bad, tmp_path / f"out-{field}")


def test_method_rows_never_counted_as_independent_observations(tmp_path):
    """The baseline is 64 instances, never 256 method-cells."""
    out_dir = Path(_analyze(CANONICAL, tmp_path / "out"))
    instances = list(csv.DictReader(open(out_dir / "instance_uplift.csv")))
    assert len(instances) == 64
    strata = list(csv.DictReader(open(out_dir / "strata_summary.csv")))
    assert int(strata[0]["instances"]) == 64
    assert sum(int(r["instances"]) for r in strata[1:]) == 64
    manifest = json.loads((out_dir / "MANIFEST.json").read_text())
    assert manifest["population"]["baseline_instances"] == 64
    assert manifest["population"]["method_cells"] == 256  # disclosed input


def test_known_paired_interval_arithmetic():
    """Golden check of the interval-subtraction rule."""
    # [1, 2] minus [0.2, 0.5] = [1 - 0.5, 2 - 0.2] = [0.5, 1.8]
    assert mod.classify_contrast(1 - 0.5, 2 - 0.2) == "strictly-positive"
    # [0.1, 0.2] minus [0.3, 0.6] = [-0.5, -0.1]
    assert mod.classify_contrast(0.1 - 0.6, 0.2 - 0.3) == \
        "strictly-negative"
    # [0.0, 0.4] minus [0.1, 0.3] = [-0.3, 0.3]
    assert mod.classify_contrast(0.0 - 0.3, 0.4 - 0.1) == \
        "crosses-or-touches-zero"
    # touching zero is unresolved, not positive
    assert mod.classify_contrast(0.0, 0.5) == "crosses-or-touches-zero"


def test_interval_classification_exhaustive_over_valid_intervals():
    """Exhaustive over lo <= hi: every zero-touching interval is a
    boundary case, never invalid."""
    assert mod.classify_interval(0.5, 0.6, "x") == "strictly-positive"
    assert mod.classify_interval(-0.6, -0.5, "x") == "strictly-negative"
    assert mod.classify_interval(-0.01, 0.0, "x") == "exact-zero-boundary"
    assert mod.classify_interval(0.0, 0.5, "x") == "exact-zero-boundary"
    assert mod.classify_interval(0.0, 0.0, "x") == "exact-zero-boundary"
    assert mod.classify_interval(-0.005, 0.005, "x") == \
        "strict-zero-crossing"
    # only invalid intervals raise
    with pytest.raises(mod.B3Error, match="not a valid"):
        mod.classify_interval(0.5, 0.4, "x")
    with pytest.raises(mod.B3Error, match="not a valid"):
        mod.classify_interval(float("nan"), 0.4, "x")


def test_output_separation_gate(tmp_path):
    """--out must be strictly separated from the canonical input root in
    both directions; symlink/relative aliases cannot bypass; refusal
    happens BEFORE any input/output mutation."""
    before = {p.name: mod.sha256_file(p)
              for p in CANONICAL.iterdir() if p.is_file()}

    # out == input
    with pytest.raises(mod.B3Error, match="strictly separated"):
        mod.analyze(CANONICAL, CANONICAL, "S", "x" * 40,
                    verify_code_commit=False)
    # out inside input
    inside = CANONICAL / "nested-out"
    with pytest.raises(mod.B3Error, match="strictly separated"):
        mod.analyze(CANONICAL, inside, "S", "x" * 40,
                    verify_code_commit=False)
    assert not inside.exists()  # refused before creation
    # input inside out (out contains the input root)
    isolated = _tampered_copy(tmp_path / "container" / "deep", "input")
    with pytest.raises(mod.B3Error, match="strictly separated"):
        mod.analyze(isolated, tmp_path / "container", "S", "x" * 40,
                    verify_code_commit=False)
    assert not list((tmp_path / "container").glob(".S.b3-staging-*"))
    # symlink alias resolving into the input root
    link = tmp_path / "alias"
    link.symlink_to(CANONICAL, target_is_directory=True)
    with pytest.raises(mod.B3Error, match="strictly separated"):
        mod.analyze(CANONICAL, link / "sub", "S", "x" * 40,
                    verify_code_commit=False)
    assert not (CANONICAL / "sub").exists()
    # relative alias resolving into the input root
    dotted = CANONICAL / ".." / CANONICAL.name / "sub"
    with pytest.raises(mod.B3Error, match="strictly separated"):
        mod.analyze(CANONICAL, dotted, "S", "x" * 40,
                    verify_code_commit=False)
    assert not (CANONICAL / "sub").exists()

    # the canonical input was never mutated by any refusal
    after = {p.name: mod.sha256_file(p)
             for p in CANONICAL.iterdir() if p.is_file()}
    assert before == after


def test_code_commit_verification(monkeypatch):
    # short and non-hex SHAs refuse before any Git call
    with pytest.raises(mod.B3Error, match="full 40-character"):
        mod.verify_analysis_code_commit("a9db21f")
    with pytest.raises(mod.B3Error, match="full 40-character"):
        mod.verify_analysis_code_commit("Z" * 40)

    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=mod.REPO_ROOT).decode().strip()
    # a well-formed SHA that does not resolve
    with pytest.raises(mod.B3Error, match="does not resolve"):
        mod.verify_analysis_code_commit("f" * 40)

    calls = {}
    real_run = mod.subprocess.run
    real_co = mod.subprocess.check_output

    def fake_run(args, cwd=None, **kwargs):
        if args[:2] == ["git", "merge-base"]:
            calls["ancestor"] = True

            class R:
                returncode = 1
            return R()
        return real_run(args, cwd=cwd, **kwargs)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    with pytest.raises(mod.B3Error, match="not an ancestor"):
        mod.verify_analysis_code_commit(head)
    assert calls["ancestor"]
    monkeypatch.setattr(mod.subprocess, "run", real_run)

    def dirty_status(args, cwd=None, stderr=None):
        if args[1] == "status":
            return b" M src/experiments/analyze_b3_baseline.py\n"
        return real_co(args, cwd=cwd, stderr=stderr)

    monkeypatch.setattr(mod.subprocess, "check_output", dirty_status)
    with pytest.raises(mod.B3Error, match="tracked modifications"):
        mod.verify_analysis_code_commit(head)
    monkeypatch.setattr(mod.subprocess, "check_output", real_co)

    def stale_show(args, cwd=None, stderr=None):
        if args[1] == "status":
            return b""  # clean tree so the byte-identity gate is reached
        if args[1] == "show":
            return b"different bytes"
        return real_co(args, cwd=cwd, stderr=stderr)

    monkeypatch.setattr(mod.subprocess, "check_output", stale_show)
    with pytest.raises(mod.B3Error, match="differs from the claimed"):
        mod.verify_analysis_code_commit(head)
