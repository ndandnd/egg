"""Adversarial tests for guarded A6 holdout packaging and import."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.package_a6_holdout as mod
from experiments.analyze_a6_holdout import HOLDOUT_INSTANCES
from experiments.analyze_b2_pilot import sha256_file


PACKAGING_COMMIT = "a" * 40
EXPERIMENT_COMMIT = "b" * 40
SELECTION_SHA = mod.EXPECTED_SELECTION_SHA256


def _source_root(tmp_path: Path) -> Path:
    root = tmp_path / "live" / "a6_holdout"
    (root / "SUBMISSION_LOCK").mkdir(parents=True)
    (root / "PREFLIGHT.json").write_text('{"frozen":true}\n')
    (root / "MANIFEST-20260819T010300Z.txt").write_text("launch\n")
    (root / "SUBMISSION_LOCK" / "CLAIM.txt").write_text("claim\n")
    (root / "SUBMISSION_LOCK" / "INTENT.txt").write_text("intent\n")
    (root / "SUBMISSION_LOCK" / "SUBMITTED.txt").write_text("submitted\n")
    (root / "cell-a").mkdir()
    (root / "cell-a" / "checkpoint.json").write_text('{"done":true}\n')
    (root / "empty-dir").mkdir()
    return root


def _callbacks(root: Path, calls: list | None = None) -> dict:
    calls = calls if calls is not None else []

    def code_verifier(value):
        calls.append(("code", value))
        return PACKAGING_COMMIT

    def selection_validator(path, verify_git=True):
        calls.append(("selection", str(path), verify_git))
        return {
            "sha256": SELECTION_SHA,
            "selection_commit": mod.EXPECTED_SELECTION_COMMIT,
            "selected_arm": "a6_a4",
        }

    def preflight_validator(path, instances=HOLDOUT_INSTANCES):
        calls.append(("preflight", str(path)))
        return {
            "path": str(Path(path).resolve()),
            "sha256": sha256_file(str(path)),
            "code_commit": EXPERIMENT_COMMIT,
            "physical_instances": 32,
            "market_instances": 64,
            "method_cells": 128,
            "selection": {"sha256": SELECTION_SHA},
        }

    def launch_validator(run_root, preflight, selection,
                         instances=HOLDOUT_INSTANCES):
        calls.append(("launch", str(run_root)))
        run_root = Path(run_root)
        return {
            "schema": "a6-holdout-launch-provenance-v1",
            "job_id": "424242",
            "code_commit": EXPERIMENT_COMMIT,
            "selection_sha256": SELECTION_SHA,
            "preflight_sha256": preflight["sha256"],
            "grid_list_sha256": "e" * 64,
            "claimed_utc": "2026-08-19T01:00:00Z",
            "prepared_utc": "2026-08-19T01:01:00Z",
            "submitted_utc": "2026-08-19T01:02:00Z",
            "manifest_submitted_utc": "2026-08-19T01:04:00Z",
            "manifest": {
                "path": str(run_root / "MANIFEST-20260819T010300Z.txt"),
                "sha256": sha256_file(
                    str(run_root / "MANIFEST-20260819T010300Z.txt")),
            },
            "lock": {
                name: {
                    "path": str(run_root / "SUBMISSION_LOCK" / name),
                    "sha256": sha256_file(
                        str(run_root / "SUBMISSION_LOCK" / name)),
                }
                for name in ("CLAIM.txt", "INTENT.txt", "SUBMITTED.txt")
            },
        }

    def root_validator(run_root, instances=HOLDOUT_INSTANCES, preflight=None):
        calls.append(("root", str(run_root)))
        assert ".frozen-a6-holdout" in str(run_root)
        return {"validated": "paths"}

    def scientific_validator(paths, preflight, selection, packaging_commit,
                             instances=HOLDOUT_INSTANCES):
        calls.append(("scientific", paths, packaging_commit))
        return {
            "status": "PASS",
            "method_cells": 128,
            "experiment_code_commit": EXPERIMENT_COMMIT,
            "checks": ["test fixture"],
            "decision_computed": False,
        }

    def audit_fn(run_root, **kwargs):
        calls.append(("audit", str(run_root), kwargs))
        return [f"# Run summary: `{run_root}`", "", "**PASS**"], True, []

    def job_quiescence_validator(job_id):
        calls.append(("squeue", job_id))

    return {
        "selection_path": root.parent / "selection.json",
        "code_verifier": code_verifier,
        "selection_validator": selection_validator,
        "preflight_validator": preflight_validator,
        "launch_validator": launch_validator,
        "root_validator": root_validator,
        "scientific_validator": scientific_validator,
        "audit_fn": audit_fn,
        "job_quiescence_validator": job_quiescence_validator,
    }


def _package(root: Path, out: Path, calls: list | None = None, **overrides):
    kwargs = _callbacks(root, calls)
    kwargs.update(overrides)
    return mod.package_holdout(root, out, PACKAGING_COMMIT, **kwargs)


def _import(bundle: Path | str, repository: Path):
    return mod.import_bundle(
        bundle, repository,
        destination_validator=lambda _repository, _manifest: None)


def test_pack_is_deterministic_normalized_and_exact(tmp_path):
    root = _source_root(tmp_path)
    first = _package(root, tmp_path / "packages-a")
    first_bytes = Path(first["archive"]).read_bytes()

    for path in [root / "PREFLIGHT.json", root / "cell-a/checkpoint.json"]:
        os.chmod(path, 0o600)
        os.utime(path, (123456789, 123456789))
    second = _package(root, tmp_path / "packages-b")
    assert Path(second["archive"]).read_bytes() == first_bytes
    assert Path(second["sidecar"]).read_text() == (
        f"{sha256_file(second['archive'])}  {Path(second['archive']).name}\n"
    )

    external_manifest = Path(second["manifest"]).read_bytes()
    manifest = json.loads(external_manifest)
    assert manifest["audit"]["contract"] == {
        "expect_cg": 128,
        "expect_cg_method": {"a2": 64, "a6_a4": 64},
        "expect_cg_certified_method": None,
    }
    assert manifest["scope"]["excluded"]
    assert "archive_sha256" not in manifest["archive"]
    with tarfile.open(second["archive"], "r:gz") as archive:
        members = archive.getmembers()
        assert [m.name for m in members] == sorted(m.name for m in members)
        assert all(m.mtime == 0 and m.uid == 0 and m.gid == 0
                   for m in members)
        assert all(m.mode == (0o755 if m.isdir() else 0o644)
                   for m in members)
        assert archive.extractfile(
            "A6_HOLDOUT_TRANSFER/MANIFEST.json").read() == external_manifest


def test_content_change_changes_archive_and_inventory(tmp_path):
    root = _source_root(tmp_path)
    first = _package(root, tmp_path / "packages-a")
    (root / "cell-a/checkpoint.json").write_text('{"done":false}\n')
    second = _package(root, tmp_path / "packages-b")
    assert first["archive_sha256"] != second["archive_sha256"]
    first_manifest = json.loads(Path(first["manifest"]).read_text())
    second_manifest = json.loads(Path(second["manifest"]).read_text())
    assert (first_manifest["source"]["canonical_tree_sha256"]
            != second_manifest["source"]["canonical_tree_sha256"])


def test_gate_order_and_exact_audit_contract(tmp_path):
    root = _source_root(tmp_path)
    calls = []
    _package(root, tmp_path / "packages", calls)
    labels = [row[0] for row in calls]
    assert labels == [
        "code", "selection", "preflight", "launch", "squeue",
        "preflight", "launch", "root", "scientific", "audit", "squeue",
    ]
    audit_kwargs = next(row[2] for row in calls if row[0] == "audit")
    assert audit_kwargs["out_path"] == os.devnull
    assert audit_kwargs["expect_cg"] == 128
    assert audit_kwargs["expect_cg_method"] == {"a2": 64, "a6_a4": 64}
    assert audit_kwargs["expect_cg_certified_method"] is None


def test_active_job_refuses_before_outcome_validation(tmp_path):
    root = _source_root(tmp_path)
    calls = []

    def active(job_id):
        calls.append(("squeue", job_id))
        raise mod.PackagingError("still active")

    with pytest.raises(mod.PackagingError, match="still active"):
        _package(
            root, tmp_path / "packages", calls,
            job_quiescence_validator=active)
    assert not any(row[0] in ("root", "scientific", "audit") for row in calls)
    assert not (tmp_path / "packages").exists()


def test_squeue_quiescence_contract(monkeypatch):
    observed = []

    def run(command, **kwargs):
        observed.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(mod.subprocess, "run", run)
    mod.assert_job_quiescent("424242")
    assert observed[0][0] == [
        "squeue", "--noheader", "--me", "--format=%F|%T"]
    assert observed[0][1]["check"] is False

    monkeypatch.setattr(
        mod.subprocess, "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 0, stdout="111|RUNNING\n424242|COMPLETING\n", stderr=""))
    with pytest.raises(mod.PackagingError, match="still active"):
        mod.assert_job_quiescent("424242")

    monkeypatch.setattr(
        mod.subprocess, "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 1, stdout="", stderr="invalid job"))
    with pytest.raises(mod.PackagingError, match="cannot query"):
        mod.assert_job_quiescent("424242")

    monkeypatch.setattr(
        mod.subprocess, "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 0, stdout="111|RUNNING\n222|PENDING\n", stderr=""))
    mod.assert_job_quiescent("424242")

    monkeypatch.setattr(
        mod.subprocess, "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 0, stdout="malformed\n", stderr=""))
    with pytest.raises(mod.PackagingError, match="malformed squeue"):
        mod.assert_job_quiescent("424242")


def test_job_reappearing_before_publish_removes_staging(tmp_path):
    root = _source_root(tmp_path)
    checks = []

    def changes_state(job_id):
        checks.append(job_id)
        if len(checks) == 2:
            raise mod.PackagingError("job active again")

    out = tmp_path / "packages"
    with pytest.raises(mod.PackagingError, match="active again"):
        _package(
            root, out, job_quiescence_validator=changes_state)
    assert checks == ["424242", "424242"]
    assert not any(out.glob("*"))


@pytest.mark.parametrize("kind", ["file_symlink", "dir_symlink", "hardlink", "fifo"])
def test_unsafe_source_entries_refuse_without_final_bundle(tmp_path, kind):
    root = _source_root(tmp_path)
    if kind == "file_symlink":
        (root / "bad").symlink_to(root / "PREFLIGHT.json")
    elif kind == "dir_symlink":
        (root / "bad").symlink_to(root / "cell-a", target_is_directory=True)
    elif kind == "hardlink":
        os.link(root / "PREFLIGHT.json", root / "bad")
    else:
        if not hasattr(os, "mkfifo"):
            pytest.skip("FIFO unavailable")
        os.mkfifo(root / "bad")
    out = tmp_path / "packages"
    with pytest.raises(mod.PackagingError):
        _package(root, out)
    assert not any(path.name.startswith("a6_holdout-job")
                   for path in out.glob("*"))
    assert not any(".staging-" in path.name for path in out.glob("*"))


def test_symlink_root_and_unsafe_filename_refuse(tmp_path):
    root = _source_root(tmp_path)
    linked = tmp_path / "linked-root"
    linked.symlink_to(root, target_is_directory=True)
    with pytest.raises(mod.PackagingError, match="root must not be a symlink"):
        _package(linked, tmp_path / "packages-a")
    (root / "bad\\name").write_text("bad\n")
    out = tmp_path / "packages-b"
    with pytest.raises(mod.PackagingError, match="unsafe source path"):
        _package(root, out)
    assert not any(out.glob("*"))


def test_output_inside_source_and_existing_final_refuse(tmp_path):
    root = _source_root(tmp_path)
    with pytest.raises(mod.PackagingError, match="outside source"):
        _package(root, root / "packages")
    first = _package(root, tmp_path / "packages")
    before = Path(first["archive"]).read_bytes()
    with pytest.raises(mod.PackagingError, match="existing package"):
        _package(root, tmp_path / "packages")
    assert Path(first["archive"]).read_bytes() == before


def test_source_mutation_or_writer_failure_publishes_nothing(
        tmp_path, monkeypatch):
    root = _source_root(tmp_path)
    real_write = mod._write_archive

    def mutate(*args, **kwargs):
        real_write(*args, **kwargs)
        (root / "late-file").write_text("late\n")

    monkeypatch.setattr(mod, "_write_archive", mutate)
    out = tmp_path / "packages-a"
    with pytest.raises(mod.PackagingError, match="source tree changed"):
        _package(root, out)
    assert not any(out.glob("*"))

    root = _source_root(tmp_path / "second")

    def fail(*_args, **_kwargs):
        raise OSError("injected archive failure")

    monkeypatch.setattr(mod, "_write_archive", fail)
    out = tmp_path / "packages-b"
    with pytest.raises(OSError, match="injected"):
        _package(root, out)
    assert not any(out.glob("*"))


def test_audit_failure_publishes_nothing(tmp_path):
    root = _source_root(tmp_path)

    def failed_audit(*_args, **_kwargs):
        return ["failed"], False, ["missing cell"]

    out = tmp_path / "packages"
    with pytest.raises(mod.PackagingError, match="AUDIT FAILED"):
        _package(root, out, audit_fn=failed_audit)
    assert not any(out.glob("*"))


def test_scientific_validation_failure_publishes_nothing(tmp_path):
    root = _source_root(tmp_path)

    def failed_science(*_args, **_kwargs):
        raise mod.PackagingError("unscoreable population")

    out = tmp_path / "packages"
    with pytest.raises(mod.PackagingError, match="unscoreable"):
        _package(root, out, scientific_validator=failed_science)
    assert not any(out.glob("*"))


def test_scientific_population_rejects_mixed_source_commits():
    from experiments.analyze_a6_holdout import (
        AnalysisError, check_population_contract,
    )

    paths = {
        (method, seed, n_trips, b): "unused"
        for seed, n_trips, b in HOLDOUT_INSTANCES
        for method in mod.METHODS
    }
    index = {key: i for i, key in enumerate(paths)}

    def extract(_path, method, seed, n_trips, b):
        key = (method, seed, n_trips, b)
        return {
            "method": method,
            "epsilon": 0.01,
            "budget": 240,
            "tol_d": 0.01,
            "backend": "GRB",
            "solver_identity": "{}",
            "mip_version": "1.17.6",
            "source_commit": "1111111" if index[key] else "2222222",
        }

    with pytest.raises(AnalysisError, match="mixes experiment code commits"):
        mod.validate_scientific_population(
            paths,
            {"code_commit": "1" * 40},
            {"selection_commit": mod.EXPECTED_SELECTION_COMMIT},
            PACKAGING_COMMIT,
            cell_extractor=extract,
            population_validator=check_population_contract,
            provenance_validator=lambda *_args: "1" * 40,
        )


def test_import_round_trip_is_verified_atomic_and_no_overwrite(tmp_path):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    repository = tmp_path / "repo"
    (repository / ".git").mkdir(parents=True)
    (repository / "src/runs").mkdir(parents=True)

    result = _import(package["bundle_dir"], repository)
    target = Path(result["target"])
    assert mod.snapshot_source(target) == mod.snapshot_source(root)
    assert not (repository / "A6_HOLDOUT_TRANSFER").exists()
    assert not any(path.name.startswith(".a6_holdout.import-")
                   for path in (repository / "src/runs").iterdir())
    with pytest.raises(mod.PackagingError, match="existing import target"):
        _import(package["bundle_dir"], repository)


def test_import_rejects_sidecar_tamper_and_extra_file(tmp_path):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    bundle = Path(package["bundle_dir"])
    repository = tmp_path / "repo"
    (repository / ".git").mkdir(parents=True)
    (repository / "src/runs").mkdir(parents=True)

    sidecar = bundle / "ARCHIVE.sha256"
    original = sidecar.read_bytes()
    sidecar.write_text("0" * 64 + f"  {Path(package['archive']).name}\n")
    with pytest.raises(mod.PackagingError, match="sidecar does not match"):
        _import(bundle, repository)
    sidecar.write_bytes(original)
    (bundle / "extra").write_text("unexpected\n")
    with pytest.raises(mod.PackagingError, match="population differs"):
        _import(bundle, repository)


def test_import_rejects_corrupt_archive_even_with_updated_sidecar(tmp_path):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    bundle = Path(package["bundle_dir"])
    archive = Path(package["archive"])
    repository = tmp_path / "repo"
    (repository / ".git").mkdir(parents=True)
    (repository / "src").mkdir(parents=True)

    with archive.open("ab") as handle:
        handle.write(b"corrupt")
    digest = sha256_file(str(archive))
    (bundle / "ARCHIVE.sha256").write_text(
        f"{digest}  {archive.name}\n")
    with pytest.raises(mod.PackagingError, match="archive"):
        _import(bundle, repository)
    assert not (repository / "src/runs/a6_holdout").exists()


def test_import_archive_change_before_install_leaves_no_target(
        tmp_path, monkeypatch):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    archive = Path(package["archive"])
    repository = tmp_path / "repo"
    (repository / ".git").mkdir(parents=True)
    (repository / "src/runs").mkdir(parents=True)
    real_record = mod._stable_file_record
    archive_reads = 0

    def mutate_on_recheck(record_root, path):
        nonlocal archive_reads
        if Path(path) == archive:
            archive_reads += 1
            if archive_reads == 2:
                with archive.open("ab") as handle:
                    handle.write(b"late")
        return real_record(record_root, path)

    monkeypatch.setattr(mod, "_stable_file_record", mutate_on_recheck)
    with pytest.raises(mod.PackagingError, match="changed during import"):
        _import(package["bundle_dir"], repository)
    assert not (repository / "src/runs/a6_holdout").exists()
    assert not any(path.name.startswith(".a6_holdout.import-")
                   for path in (repository / "src/runs").iterdir())


def test_import_lock_and_manifest_provenance_tamper_refuse(tmp_path):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    bundle = Path(package["bundle_dir"])
    repository = tmp_path / "repo"
    (repository / ".git").mkdir(parents=True)
    (repository / "src/runs").mkdir(parents=True)
    lock = repository / "src/runs/.a6_holdout.import-lock"
    lock.mkdir()
    with pytest.raises(mod.PackagingError, match="holds"):
        _import(bundle, repository)
    lock.rmdir()

    manifest_path = bundle / "BUNDLE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["preflight"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(mod.PackagingError, match="launch identity"):
        _import(bundle, repository)


def test_import_cli_help_needs_only_standard_library(tmp_path):
    script = Path(mod.__file__).resolve()
    result = subprocess.run(
        [sys.executable, "-S", str(script), "import", "--help"],
        cwd=tmp_path, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False)
    assert result.returncode == 0, result.stderr
    assert "--bundle-dir" in result.stdout and "--repo-root" in result.stdout


def test_destination_repository_is_git_and_selection_bound(tmp_path):
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=mod.REPO_ROOT, text=True).strip()
    mod.validate_destination_repository(
        mod.REPO_ROOT, {"packaging_code_commit": head})

    fake = tmp_path / "not-egg"
    (fake / ".git").mkdir(parents=True)
    (fake / "src").mkdir()
    with pytest.raises(mod.PackagingError, match="compatible egg"):
        mod.validate_destination_repository(
            fake, {"packaging_code_commit": head})


def test_gzip_header_has_zero_mtime_and_no_filename(tmp_path):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    header = Path(package["archive"]).read_bytes()[:10]
    assert header[:2] == b"\x1f\x8b"
    assert header[3] & 0x08 == 0
    assert header[4:8] == b"\x00\x00\x00\x00"
    assert header[8:] == b"\x02\xff"
