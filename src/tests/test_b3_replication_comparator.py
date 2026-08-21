"""Adversarial tests for the B3 replication comparator.

Written against synthetic fixtures only.  No live run tree is read,
including ``runs/b3_factor_pilot``.  No solver is imported.
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import experiments.b3_factor_pilot as bp
import experiments.compare_b3_replication as cmp
from experiments import b3_pilot_evidence as evidence

# Hand-computable certificate (SEK):
#   ub_ch=100, lb_best=99.5, z_D_lb=z_D_ub=100.5
#   U_lo_raw = 100.5 - 100 = 0.5
#   U_hi     = 100.5 - 99.5 = 1.0
UB_CH = 100.0
LB_BEST = 99.5
Z_D = 100.5
U_LO_RAW = 0.5
U_HI = 1.0


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def _identity(cell, *, run_commit: str, manifest_sha: str) -> dict:
    return {
        "schema": "b3-cell-identity-v1",
        "setting": cell["setting"],
        "seed": cell["seed"],
        "n_trips": cell["n_trips"],
        "b": cell["b"],
        "method": bp.METHOD,
        "epsilon": bp.EPSILON,
        "tol_d": bp.TOL_D,
        "budget": bp.BUDGET,
        "instance_hash": "i" * 64,
        "market_hash": "m" * 64,
        "run_commit": run_commit,
        "run_manifest_sha256": manifest_sha,
    }


def _cg(*, certified=True, ub_ch=UB_CH, lb_best=LB_BEST, z_d_ub=Z_D):
    return {
        "identity": {
            "method": bp.METHOD,
            "epsilon": bp.EPSILON,
            "tol_d": bp.TOL_D,
            "budget": bp.BUDGET,
            "instance_hash": "i" * 64,
            "market_hash": "m" * 64,
            "z_d_ub": z_d_ub,
        },
        "ub_history": [ub_ch + 1.0, ub_ch],
        "lb_history": [lb_best - 0.25, lb_best],
        "lb_best": lb_best,
        "outcome": {
            "type": "certified" if certified else "budget_exhausted",
            "certified": certified,
            "ub_ch": ub_ch,
            "lb_best": lb_best,
        },
    }


def _dictator(*, z_d_ub=Z_D, z_d_lb=Z_D):
    return {
        "identity": {"instance_hash": "i" * 64, "market_hash": "m" * 64},
        "z_d_ub": z_d_ub,
        "z_d_lb": z_d_lb,
        "tol_d": bp.TOL_D,
        "status": "OPTIMAL",
        "adaptive": {"adaptive_converged": True, "adaptive_lb": z_d_lb},
    }


def _write_cell(root: Path, cell: dict, *, run_commit: str, manifest_sha: str,
                cg=None, dictator=None) -> Path:
    cdir = root / cell["tag"]
    cdir.mkdir(parents=True, exist_ok=True)
    _dump(cdir / bp.CELL_IDENTITY_FILENAME,
          _identity(cell, run_commit=run_commit, manifest_sha=manifest_sha))
    _dump(cdir / "a2.cg.ckpt.json", cg if cg is not None else _cg())
    _dump(cdir / "dictator.ckpt.json",
          dictator if dictator is not None else _dictator())
    return cdir


def write_population(root: Path, *, run_commit: str, manifest_sha: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    # Manifest is provenance: different bytes on each side are expected.
    _dump(root / bp.RUN_MANIFEST_FILENAME, {
        "run_commit": run_commit,
        "note": "excluded from comparison",
    })
    for cell in bp.build_cells():
        _write_cell(root, cell, run_commit=run_commit, manifest_sha=manifest_sha)
    return root


def _snapshot(root: Path) -> dict[str, tuple]:
    out = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        filenames.sort()
        parent = Path(dirpath)
        for name in filenames:
            path = parent / name
            info = path.lstat()
            rel = path.relative_to(root).as_posix()
            out[rel] = (info.st_mtime_ns, info.st_size, info.st_ino)
    return out


def test_frozen_constants_match_spec_and_pilot():
    spec = (bp.REPO_ROOT / "doc" / "B3_REPLICATION_COMPARATOR_SPEC.md").read_text()
    assert cmp.N_CELLS == 60 == bp.N_CELLS
    assert cmp.REQUIRED_AGREEING_CELLS == 60
    assert cmp.ABS_TOL_SEK == bp.EPSILON == 1e-2
    assert cmp.CG_EPSILON == 1e-2
    assert cmp.DICTATOR_TOL_D == bp.TOL_D == 1e-2
    assert cmp.PHYSICAL_REPLAY_TOL_KWH == 1e-4
    assert cmp.REL_SCALE == 1e-10
    assert cmp.ORIGINAL_IS_CANONICAL is True
    assert cmp.REPLICA_MAY_SUBSTITUTE_ORIGINAL is False
    assert "REQUIRED_AGREEING_CELLS = 60" in spec
    assert "ABS_TOL_SEK = 1e-2" in spec
    assert "REPLICA_MAY_SUBSTITUTE_ORIGINAL = False" in spec
    assert set(cmp.COMPARED_NUMERIC_FIELDS) >= {
        "lb_best", "ub_ch", "U_lo_raw", "U_hi", "z_D_lb", "z_D_ub"}
    assert "certified" in cmp.COMPARED_BOOLEAN_FIELDS


def test_hand_computable_interval_and_tolerance():
    interval = __import__(
        "experiments.analyze_b3_factor_pilot", fromlist=["cell_interval"]
    ).cell_interval(UB_CH, LB_BEST, Z_D, Z_D, n_trips=8)
    assert interval["U_lo_raw"] == pytest.approx(U_LO_RAW)
    assert interval["U_hi"] == pytest.approx(U_HI)
    # 100 vs 100.005 agrees; 100 vs 100.02 does not.
    assert cmp.numbers_agree(100.0, 100.005)
    assert not cmp.numbers_agree(100.0, 100.02)
    allowance = cmp.operand_scaled_allowance(100.0, 100.005)
    assert allowance == pytest.approx(1e-2 + 1e-10 * 100.0)


def test_importable_without_solver():
    root = Path(cmp.__file__).resolve().parent
    for name in ("compare_b3_replication.py", "b3_pilot_evidence.py"):
        tree = ast.parse((root / name).read_text())
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module.split(".")[0])
        for banned in ("gurobipy", "mip", "egglab"):
            assert banned not in imported, f"{name} imports {banned}"


def test_pass_60_of_60_ignores_provenance(tmp_path):
    original = write_population(
        tmp_path / "original", run_commit="a" * 40, manifest_sha="aa" * 32)
    replica = write_population(
        tmp_path / "replica", run_commit="b" * 40, manifest_sha="bb" * 32)
    before_o, before_r = _snapshot(original), _snapshot(replica)
    verdict = cmp.compare_replications(original, replica)
    assert verdict["status"] == cmp.STATUS_AGREE
    assert verdict["agreeing_cells"] == 60
    assert verdict["required_agreeing_cells"] == 60
    assert verdict["incident"] is False
    assert verdict["original_is_canonical"] is True
    assert verdict["replica_may_substitute_original"] is False
    assert _snapshot(original) == before_o
    assert _snapshot(replica) == before_r


def test_one_cell_disagreement_is_incident(tmp_path):
    original = write_population(
        tmp_path / "original", run_commit="a" * 40, manifest_sha="aa" * 32)
    replica = write_population(
        tmp_path / "replica", run_commit="b" * 40, manifest_sha="bb" * 32)
    tag = bp.build_cells()[0]["tag"]
    _dump(replica / tag / "a2.cg.ckpt.json",
          _cg(lb_best=LB_BEST + 0.05))  # 0.05 SEK > 1e-2, interval still ordered
    verdict = cmp.compare_replications(original, replica)
    assert verdict["status"] == cmp.STATUS_INCIDENT
    assert verdict["agreeing_cells"] == 59
    assert verdict["incident"] is True
    assert len(verdict["disagreements"]) == 1
    hit = verdict["disagreements"][0]
    assert hit["tag"] == tag
    assert hit["kind"] == "field_disagreement"
    fields = {row["field"] for row in hit["fields"]}
    assert "lb_best" in fields
    # Never a license to score the replica instead.
    assert verdict["replica_may_substitute_original"] is False


def test_missing_cell_refuses_incomplete_population(tmp_path):
    original = write_population(
        tmp_path / "original", run_commit="a" * 40, manifest_sha="aa" * 32)
    replica = write_population(
        tmp_path / "replica", run_commit="b" * 40, manifest_sha="bb" * 32)
    tag = bp.build_cells()[0]["tag"]
    shutil.rmtree(replica / tag)
    verdict = cmp.compare_replications(original, replica)
    assert verdict["status"] == cmp.STATUS_INCOMPLETE
    assert verdict["incomplete_population"] is True
    assert verdict["agreeing_cells"] == 0
    assert tag in verdict["missing_replica"]
    assert verdict["disagreements"][0]["kind"] == "incomplete_population"


def test_extra_cell_refuses_incomplete_population(tmp_path):
    original = write_population(
        tmp_path / "original", run_commit="a" * 40, manifest_sha="aa" * 32)
    replica = write_population(
        tmp_path / "replica", run_commit="b" * 40, manifest_sha="bb" * 32)
    extra = replica / "not_a_b3_cell"
    extra.mkdir()
    _dump(extra / "identity.json", {"tag": "not_a_b3_cell"})
    verdict = cmp.compare_replications(original, replica)
    assert verdict["status"] == cmp.STATUS_INCOMPLETE
    assert "not_a_b3_cell" in verdict["extra_replica"]
    assert verdict["agreeing_cells"] == 0


def test_reversed_interval_is_incident(tmp_path):
    original = write_population(
        tmp_path / "original", run_commit="a" * 40, manifest_sha="aa" * 32)
    replica = write_population(
        tmp_path / "replica", run_commit="b" * 40, manifest_sha="bb" * 32)
    tag = bp.build_cells()[0]["tag"]
    # Swap raw endpoints: U_lo_raw=1.0, U_hi=0.5
    # U_lo = z_D_lb - ub_ch = 1.0  => z_D_lb = 101
    # U_hi = z_D_ub - lb_best = 0.5 => z_D_ub = 100.0  (lb_best stays 99.5)
    _dump(replica / tag / "dictator.ckpt.json",
          _dictator(z_d_lb=101.0, z_d_ub=100.0))
    _dump(replica / tag / "a2.cg.ckpt.json", _cg(z_d_ub=100.0))
    verdict = cmp.compare_replications(original, replica)
    assert verdict["status"] == cmp.STATUS_INCIDENT
    kinds = {row["kind"] for row in verdict["disagreements"]}
    assert "reversed_interval" in kinds
    row = next(r for r in verdict["disagreements"] if r["tag"] == tag)
    assert row["original"]["U_lo_raw"] == pytest.approx(U_LO_RAW)
    assert row["original"]["U_hi"] == pytest.approx(U_HI)
    assert row["replica"]["U_lo_raw"] == pytest.approx(U_HI)
    assert row["replica"]["U_hi"] == pytest.approx(U_LO_RAW)


def test_non_finite_field_is_incident(tmp_path):
    original = write_population(
        tmp_path / "original", run_commit="a" * 40, manifest_sha="aa" * 32)
    replica = write_population(
        tmp_path / "replica", run_commit="b" * 40, manifest_sha="bb" * 32)
    tag = bp.build_cells()[0]["tag"]
    ck = _cg()
    ck["lb_history"] = [float("nan"), float("nan")]
    _dump(replica / tag / "a2.cg.ckpt.json", ck)
    verdict = cmp.compare_replications(original, replica)
    assert verdict["status"] == cmp.STATUS_INCIDENT
    assert verdict["disagreements"][0]["kind"] == "non_finite_field"


def test_duplicate_json_keys_refused(tmp_path):
    original = write_population(
        tmp_path / "original", run_commit="a" * 40, manifest_sha="aa" * 32)
    replica = write_population(
        tmp_path / "replica", run_commit="b" * 40, manifest_sha="bb" * 32)
    tag = bp.build_cells()[0]["tag"]
    (replica / tag / "a2.cg.ckpt.json").write_text(
        '{"lb_best": 1, "lb_best": 2, "ub_history": [100], '
        '"lb_history": [99.5], "outcome": {"certified": true, '
        '"type": "certified"}}\n')
    with pytest.raises(evidence.DuplicateJsonKeyError):
        evidence.strict_json_loads(
            evidence.read_regular_bytes_once(replica / tag / "a2.cg.ckpt.json"))
    verdict = cmp.compare_replications(original, replica)
    assert verdict["status"] == cmp.STATUS_INCIDENT
    assert verdict["disagreements"][0]["kind"] == "duplicate_json_key"


def test_byte_identical_verdict_regeneration(tmp_path):
    original = write_population(
        tmp_path / "original", run_commit="a" * 40, manifest_sha="aa" * 32)
    replica = write_population(
        tmp_path / "replica", run_commit="b" * 40, manifest_sha="bb" * 32)
    first = cmp.verdict_bytes(cmp.compare_replications(original, replica))
    second = cmp.verdict_bytes(cmp.compare_replications(original, replica))
    assert first == second
    out_a = tmp_path / "verdict-a.json"
    out_b = tmp_path / "verdict-b.json"
    assert cmp.main([
        "--original", str(original), "--replica", str(replica),
        "--verdict", str(out_a),
    ]) == 0
    assert cmp.main([
        "--original", str(original), "--replica", str(replica),
        "--verdict", str(out_b),
    ]) == 0
    assert out_a.read_bytes() == out_b.read_bytes() == first


def test_never_writes_into_input_trees(tmp_path):
    original = write_population(
        tmp_path / "original", run_commit="a" * 40, manifest_sha="aa" * 32)
    replica = write_population(
        tmp_path / "replica", run_commit="b" * 40, manifest_sha="bb" * 32)
    before_o, before_r = _snapshot(original), _snapshot(replica)
    inside = original / "verdict.json"
    verdict = cmp.compare_replications(original, replica)
    with pytest.raises(cmp.ComparatorError, match="input directory"):
        cmp.write_verdict(verdict, inside, original, replica)
    assert not inside.exists()
    dest = tmp_path / "out" / "verdict.json"
    cmp.write_verdict(verdict, dest, original, replica)
    assert dest.is_file()
    assert _snapshot(original) == before_o
    assert _snapshot(replica) == before_r


def test_strict_json_and_regular_read_helpers(tmp_path):
    good = tmp_path / "ok.json"
    good.write_text('{"a": 1, "b": 2}\n')
    assert evidence.strict_json_loads(
        evidence.read_regular_bytes_once(good)) == {"a": 1, "b": 2}
    dup = tmp_path / "dup.json"
    dup.write_text('{"a": 1, "a": 2}\n')
    with pytest.raises(evidence.DuplicateJsonKeyError):
        evidence.strict_json_loads(evidence.read_regular_bytes_once(dup))
    # vanilla json.loads would last-win; that is the bug we refuse.
    assert json.loads(dup.read_text()) == {"a": 2}
    link = tmp_path / "link.json"
    link.symlink_to(good)
    with pytest.raises(evidence.NonRegularFileError):
        evidence.read_regular_bytes_once(link)


def test_read_regular_bytes_once_rejects_directory(tmp_path):
    with pytest.raises(evidence.NonRegularFileError):
        evidence.read_regular_bytes_once(tmp_path)
