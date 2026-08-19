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
import experiments.analyze_a6_holdout as analysis_mod
import experiments.audit_runs as audit_mod
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

    def root_validator(run_root, instances=HOLDOUT_INSTANCES, preflight=None,
                       launch=None):
        calls.append(("root", str(run_root)))
        assert ".frozen-a6-holdout" in str(run_root)
        assert launch and launch["job_id"] == "424242"
        return {"validated": "paths"}

    def scientific_validator(paths, preflight, selection, packaging_commit,
                             instances=HOLDOUT_INSTANCES):
        calls.append(("scientific", paths, packaging_commit))
        return {
            "status": "PASS",
            "method_cells": 128,
            "experiment_code_commit": EXPERIMENT_COMMIT,
            "checks": list(mod.SCIENTIFIC_CHECKS),
            "decision_computed": False,
        }

    def audit_fn(run_root, **kwargs):
        calls.append(("audit", str(run_root), kwargs))
        return [f"# Run summary: `{run_root}`", "", "**PASS**"], True, []

    def job_quiescence_validator(job_id):
        calls.append(("squeue", job_id))

    def closeout_claimer(run_root, *, packaging_commit, preflight,
                         selection, launch, snapshot):
        calls.append(("claim", str(run_root)))
        document = {
            "schema": mod.CLOSEOUT_CLAIM_SCHEMA,
            "campaign": "a6-holdout",
            "status": "claimed-before-outcome-validation",
            "claimed_utc": "2026-08-19T02:00:00Z",
            "packaging_code_commit": packaging_commit,
            "experiment_code_commit": preflight["code_commit"],
            "selection_sha256": selection["sha256"],
            "preflight_sha256": preflight["sha256"],
            "launch_job_id": launch["job_id"],
            "grid_list_sha256": launch["grid_list_sha256"],
            "source": {
                "canonical_tree_sha256":
                    mod.canonical_tree_sha256(snapshot),
                "file_count": snapshot["file_count"],
                "directory_count": snapshot["directory_count"],
                "total_bytes": snapshot["total_bytes"],
            },
        }
        payload = (json.dumps(
            document, indent=2, sort_keys=True) + "\n").encode()
        return {
            "path": "fixture-closeout-claim",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "document": document,
        }

    def closeout_claim_validator(record):
        calls.append(("claim-check", record["sha256"]))
        assert record["document"]["status"] == (
            "claimed-before-outcome-validation")

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
        "closeout_claimer": closeout_claimer,
        "closeout_claim_validator": closeout_claim_validator,
    }


def _package(root: Path, out: Path, calls: list | None = None, **overrides):
    kwargs = _callbacks(root, calls)
    kwargs.update(overrides)
    return mod.package_holdout(root, out, PACKAGING_COMMIT, **kwargs)


def _import(bundle: Path | str, repository: Path):
    return mod.import_bundle(
        bundle, repository,
        destination_validator=lambda _repository, _manifest: None)


@pytest.mark.parametrize(
    "claimed", ("", "abcdef", "ABCDEF0", "abcdeg0", "a" * 41))
def test_packaging_commit_verifier_rejects_invalid_claim_without_git(
        claimed, monkeypatch):
    def unexpected(*_args, **_kwargs):
        raise AssertionError("invalid commit syntax must fail before Git")

    monkeypatch.setattr(mod.subprocess, "check_output", unexpected)
    with pytest.raises(mod.PackagingError, match="7-40 lowercase hexadecimal"):
        mod.verify_packaging_code_commit(claimed)


def test_packaging_commit_verifier_rejects_unresolved_claim(monkeypatch):
    def unresolved(command, **_kwargs):
        assert command[-1] == "deadbee^{commit}"
        raise subprocess.CalledProcessError(128, command)

    monkeypatch.setattr(mod.subprocess, "check_output", unresolved)
    with pytest.raises(mod.PackagingError, match="cannot resolve"):
        mod.verify_packaging_code_commit("deadbee")


def test_packaging_commit_verifier_rejects_resolved_non_head(monkeypatch):
    head = "a" * 40

    def output(command, **_kwargs):
        if command[-1] == "deadbee^{commit}":
            return "b" * 40 + "\n"
        if command[-1] == "HEAD^{commit}":
            return head + "\n"
        raise AssertionError(command)

    monkeypatch.setattr(mod.subprocess, "check_output", output)
    with pytest.raises(mod.PackagingError, match="code commit mismatch"):
        mod.verify_packaging_code_commit("deadbee")


@pytest.mark.parametrize("use_full", (False, True))
def test_packaging_commit_verifier_accepts_resolved_head_and_clean_tree(
        use_full, monkeypatch):
    head = "a" * 40
    claimed = head if use_full else head[:7]
    calls = []

    def output(command, **_kwargs):
        calls.append(command)
        if command[-1] in (f"{claimed}^{{commit}}", "HEAD^{commit}"):
            return head + "\n"
        if command[1] == "status":
            return ""
        raise AssertionError(command)

    monkeypatch.setattr(mod.subprocess, "check_output", output)
    assert mod.verify_packaging_code_commit(claimed) == head
    assert calls[-1] == [
        "git", "status", "--porcelain", "--untracked-files=no"]


def test_packaging_commit_verifier_rejects_dirty_tracked_tree(monkeypatch):
    head = "a" * 40

    def output(command, **_kwargs):
        if command[1] == "rev-parse":
            return head + "\n"
        if command[1] == "status":
            return " M src/experiments/package_a6_holdout.py\n"
        raise AssertionError(command)

    monkeypatch.setattr(mod.subprocess, "check_output", output)
    with pytest.raises(mod.PackagingError, match="uncommitted tracked changes"):
        mod.verify_packaging_code_commit(head[:7])


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


def test_closeout_claim_is_part_of_archive_determinism_contract(tmp_path):
    root = _source_root(tmp_path)
    first = _package(root, tmp_path / "packages-a")
    base_claimer = _callbacks(root)["closeout_claimer"]

    def later_claim(*args, **kwargs):
        claim = base_claimer(*args, **kwargs)
        claim["document"]["claimed_utc"] = "2026-08-19T03:00:00Z"
        payload = (json.dumps(
            claim["document"], indent=2, sort_keys=True) + "\n").encode()
        claim["sha256"] = hashlib.sha256(payload).hexdigest()
        return claim

    second = _package(
        root, tmp_path / "packages-b", closeout_claimer=later_claim)
    assert Path(first["archive"]).read_bytes() != Path(
        second["archive"]).read_bytes()
    manifest = json.loads(Path(second["manifest"]).read_text())
    assert "exact closeout claim" in manifest["archive"]["byte_determinism"]


def test_gate_order_and_exact_audit_contract(tmp_path):
    root = _source_root(tmp_path)
    calls = []
    _package(root, tmp_path / "packages", calls)
    labels = [row[0] for row in calls]
    assert labels == [
        "code", "selection", "preflight", "launch", "squeue", "claim",
        "preflight", "launch", "root", "scientific", "audit", "squeue",
        "claim-check",
    ]
    audit_kwargs = next(row[2] for row in calls if row[0] == "audit")
    assert audit_kwargs["out_path"] == os.devnull
    assert audit_kwargs["expect_cg"] == 128
    assert audit_kwargs["expect_cg_method"] == {"a2": 64, "a6_a4": 64}
    assert audit_kwargs["expect_cg_certified_method"] is None


def test_source_closeout_claim_is_canonical_exclusive_and_persistent(tmp_path):
    root = _source_root(tmp_path)
    callbacks = _callbacks(root)
    selection = callbacks["selection_validator"](
        callbacks["selection_path"], verify_git=False)
    preflight = callbacks["preflight_validator"](root / "PREFLIGHT.json")
    launch = callbacks["launch_validator"](root, preflight, selection)
    snapshot = mod.snapshot_source(root)

    claim = mod.claim_closeout(
        root,
        packaging_commit=PACKAGING_COMMIT,
        preflight=preflight,
        selection=selection,
        launch=launch,
        snapshot=snapshot,
    )
    claim_path = root.parent / mod.CLOSEOUT_CLAIM_FILENAME
    assert Path(claim["path"]) == claim_path
    assert claim_path.read_bytes() == (
        json.dumps(claim["document"], indent=2, sort_keys=True) + "\n"
    ).encode()
    mod.assert_closeout_claim_unchanged(claim)

    with pytest.raises(mod.PackagingError, match="already claimed"):
        mod.claim_closeout(
            root,
            packaging_commit=PACKAGING_COMMIT,
            preflight=preflight,
            selection=selection,
            launch=launch,
            snapshot=snapshot,
        )
    assert claim_path.is_file()


def test_source_closeout_claim_tamper_blocks_publication(tmp_path):
    root = _source_root(tmp_path)
    out = tmp_path / "packages"

    def tamper_after_claim(*_args, **_kwargs):
        claim_path = root.parent / mod.CLOSEOUT_CLAIM_FILENAME
        claim_path.write_text("tampered\n")
        return {
            "status": "PASS",
            "method_cells": 128,
            "experiment_code_commit": EXPERIMENT_COMMIT,
            "checks": list(mod.SCIENTIFIC_CHECKS),
            "decision_computed": False,
        }

    with pytest.raises(mod.PackagingError, match="closeout claim"):
        _package(
            root,
            out,
            closeout_claimer=mod.claim_closeout,
            closeout_claim_validator=mod.assert_closeout_claim_unchanged,
            scientific_validator=tamper_after_claim,
        )
    assert (root.parent / mod.CLOSEOUT_CLAIM_FILENAME).is_file()
    assert not any(path.name.startswith("a6_holdout-job")
                   for path in out.glob("*"))


def test_default_production_callback_wiring_is_self_contained(
        tmp_path, monkeypatch):
    root = _source_root(tmp_path)
    calls = []
    callbacks = _callbacks(root, calls)
    monkeypatch.setattr(
        analysis_mod, "validate_selection", callbacks["selection_validator"])
    monkeypatch.setattr(
        analysis_mod, "validate_preflight", callbacks["preflight_validator"])
    monkeypatch.setattr(
        analysis_mod, "validate_launch_provenance",
        callbacks["launch_validator"])
    monkeypatch.setattr(
        analysis_mod, "validate_holdout_root", callbacks["root_validator"])
    monkeypatch.setattr(
        mod, "validate_scientific_population",
        callbacks["scientific_validator"])
    monkeypatch.setattr(audit_mod, "audit", callbacks["audit_fn"])

    result = mod.package_holdout(
        root,
        tmp_path / "packages",
        PACKAGING_COMMIT,
        selection_path=callbacks["selection_path"],
        code_verifier=callbacks["code_verifier"],
        job_quiescence_validator=callbacks["job_quiescence_validator"],
        closeout_claimer=callbacks["closeout_claimer"],
        closeout_claim_validator=callbacks["closeout_claim_validator"],
    )
    assert Path(result["manifest"]).is_file()
    assert [row[0] for row in calls] == [
        "code", "selection", "preflight", "launch", "squeue", "claim",
        "preflight", "launch", "root", "scientific", "audit", "squeue",
        "claim-check",
    ]


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


@pytest.mark.parametrize("competitor", ("file", "directory", "symlink"))
def test_package_publication_race_never_replaces_appearing_path(
        tmp_path, monkeypatch, competitor):
    root = _source_root(tmp_path)
    out = tmp_path / "packages"
    real_publish = mod.publish_flat_directory_no_replace
    planted = {}

    def inject(staging, destination, *, expected_names):
        target = Path(destination)
        if competitor == "file":
            target.write_text("preserve\n")
        elif competitor == "directory":
            target.mkdir()
            (target / "operator-owned").write_text("preserve\n")
        else:
            owner = tmp_path / "package-owner"
            owner.mkdir()
            (owner / "operator-owned").write_text("preserve\n")
            target.symlink_to(owner, target_is_directory=True)
        planted["target"] = target
        return real_publish(
            staging, destination, expected_names=expected_names)

    monkeypatch.setattr(mod, "publish_flat_directory_no_replace", inject)
    with pytest.raises(mod.PackagingError, match="existing publication path"):
        _package(root, out)
    target = planted["target"]
    if competitor == "file":
        assert target.read_text() == "preserve\n"
    else:
        assert (target / "operator-owned").read_text() == "preserve\n"
        assert target.is_symlink() is (competitor == "symlink")
    assert not any(".staging-" in path.name for path in out.iterdir())


@pytest.mark.parametrize("mutation", ("extra", "replacement", "missing"))
def test_flat_publication_final_ownership_gate_preserves_race_evidence(
        tmp_path, monkeypatch, mutation):
    staging = tmp_path / "staging"
    staging.mkdir()
    expected = {"A.txt", "BUNDLE_MANIFEST.json"}
    for name in expected:
        (staging / name).write_text(f"owned {name}\n")
    target = tmp_path / "published"
    real_gate = mod._flat_publication_errors
    injected = False

    def inject(path, **kwargs):
        nonlocal injected
        if not injected:
            injected = True
            if mutation == "extra":
                (path / "operator-extra").write_text("preserve extra\n")
            elif mutation == "replacement":
                victim = path / "BUNDLE_MANIFEST.json"
                victim.unlink()
                victim.write_text("preserve replacement\n")
            else:
                (path / "BUNDLE_MANIFEST.json").unlink()
        return real_gate(path, **kwargs)

    monkeypatch.setattr(mod, "_flat_publication_errors", inject)
    with pytest.raises(
            mod.IncompletePublicationError, match="cleanup was incomplete"):
        mod.publish_flat_directory_no_replace(
            staging, target, expected_names=expected)
    assert (target / ".publication-incomplete").is_file()
    if mutation == "extra":
        assert (target / "operator-extra").read_text() == "preserve extra\n"
    elif mutation == "replacement":
        assert (target / "BUNDLE_MANIFEST.json").read_text() == (
            "preserve replacement\n")
    else:
        assert not (target / "BUNDLE_MANIFEST.json").exists()


def test_flat_publication_reservation_fsync_failure_rolls_back_empty_target(
        tmp_path, monkeypatch):
    staging = tmp_path / "staging"
    staging.mkdir()
    expected = {"A.txt", "BUNDLE_MANIFEST.json"}
    for name in expected:
        (staging / name).write_text(f"owned {name}\n")
    target = tmp_path / "published"
    real_fsync = mod._fsync_directory
    injected = False

    def fail_first_parent_fsync(path):
        nonlocal injected
        if Path(path) == target.parent and not injected:
            injected = True
            raise OSError("injected reservation fsync failure")
        return real_fsync(path)

    monkeypatch.setattr(mod, "_fsync_directory", fail_first_parent_fsync)
    with pytest.raises(OSError, match="reservation fsync"):
        mod.publish_flat_directory_no_replace(
            staging, target, expected_names=expected)
    assert injected
    assert not target.exists()
    assert {path.name for path in staging.iterdir()} == expected


def test_flat_publication_reservation_race_keeps_incomplete_marker(
        tmp_path, monkeypatch):
    staging = tmp_path / "staging"
    staging.mkdir()
    expected = {"A.txt", "BUNDLE_MANIFEST.json"}
    for name in expected:
        (staging / name).write_text(f"owned {name}\n")
    target = tmp_path / "published"
    real_fsync = mod._fsync_directory
    injected = False

    def race_at_first_parent_fsync(path):
        nonlocal injected
        if Path(path) == target.parent and not injected:
            injected = True
            (target / "operator-extra").write_text("preserve extra\n")
            raise OSError("injected reservation fsync race")
        return real_fsync(path)

    monkeypatch.setattr(mod, "_fsync_directory", race_at_first_parent_fsync)
    with pytest.raises(
            mod.IncompletePublicationError, match="cleanup was incomplete"):
        mod.publish_flat_directory_no_replace(
            staging, target, expected_names=expected)
    assert injected
    assert (target / ".publication-incomplete").read_text() == "incomplete\n"
    assert (target / "operator-extra").read_text() == "preserve extra\n"
    assert {path.name for path in staging.iterdir()} == expected


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


def test_import_round_trip_is_verified_transactional_and_no_overwrite(tmp_path):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    repository = tmp_path / "repo"
    (repository / ".git").mkdir(parents=True)
    (repository / "src/runs").mkdir(parents=True)

    result = _import(package["bundle_dir"], repository)
    target = Path(result["target"])
    receipt = Path(result["receipt"])
    assert mod.snapshot_source(target) == mod.snapshot_source(root)
    assert receipt == repository / "src/runs" / mod.RECEIPT_FILENAME
    receipt_doc = mod.validate_transfer_receipt(receipt)
    package_manifest = json.loads(Path(package["manifest"]).read_text())
    assert receipt_doc["archive"]["sha256"] == package["archive_sha256"]
    assert receipt_doc["source"]["canonical_tree_sha256"] == (
        package_manifest["source"]["canonical_tree_sha256"])
    assert result["receipt_sha256"] == sha256_file(receipt)
    assert not (repository / "A6_HOLDOUT_TRANSFER").exists()
    assert not any(path.name.startswith(".a6_holdout.import-")
                   for path in (repository / "src/runs").iterdir())
    with pytest.raises(mod.PackagingError, match="existing import target"):
        _import(package["bundle_dir"], repository)


def test_import_receipt_is_required_and_bound_by_analyzer(tmp_path):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    repository = tmp_path / "repo"
    (repository / ".git").mkdir(parents=True)
    (repository / "src/runs").mkdir(parents=True)
    result = _import(package["bundle_dir"], repository)
    target = Path(result["target"])
    receipt = Path(result["receipt"])
    package_manifest = json.loads(Path(package["manifest"]).read_text())

    kwargs = {
        "preflight": {
            "code_commit": EXPERIMENT_COMMIT,
            "sha256": package_manifest["preflight"]["sha256"],
        },
        "selection": {"sha256": SELECTION_SHA},
        "launch": {
            "job_id": "424242",
            "grid_list_sha256": "e" * 64,
            "manifest_submitted_utc": "2026-08-19T01:04:00Z",
        },
        "analysis_code_commit": PACKAGING_COMMIT,
        "repository": repository,
        "verify_git": False,
    }
    validated = analysis_mod.validate_transfer_receipt(target, **kwargs)
    assert validated["sha256"] == result["receipt_sha256"]

    import_lock = target.parent / analysis_mod.IMPORT_LOCK_FILENAME
    import_lock.mkdir()
    with pytest.raises(analysis_mod.AnalysisError, match="import lock"):
        analysis_mod.validate_transfer_receipt(target, **kwargs)
    import_lock.rmdir()

    original = receipt.read_bytes()
    document = json.loads(original)
    document["provenance"]["selection_sha256"] = "0" * 64
    receipt.write_bytes(
        (json.dumps(document, indent=2, sort_keys=True) + "\n").encode())
    with pytest.raises(analysis_mod.AnalysisError, match="provenance"):
        analysis_mod.validate_transfer_receipt(target, **kwargs)
    receipt.write_bytes(original)

    document = json.loads(original)
    document["closeout_claim"]["document"]["source"]["total_bytes"] += 1
    document["closeout_claim"]["sha256"] = hashlib.sha256(
        (json.dumps(
            document["closeout_claim"]["document"],
            indent=2,
            sort_keys=True,
        ) + "\n").encode()
    ).hexdigest()
    receipt.write_bytes(
        (json.dumps(document, indent=2, sort_keys=True) + "\n").encode())
    with pytest.raises(
            analysis_mod.AnalysisError, match="closeout claim source"):
        analysis_mod.validate_transfer_receipt(target, **kwargs)
    receipt.write_bytes(original)

    (target / "late-mutation").write_text("changed\n")
    with pytest.raises(analysis_mod.AnalysisError, match="installed holdout tree"):
        analysis_mod.validate_transfer_receipt(target, **kwargs)


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


def test_existing_receipt_refuses_without_modification(tmp_path):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    repository = tmp_path / "repo"
    runs = repository / "src/runs"
    (repository / ".git").mkdir(parents=True)
    runs.mkdir(parents=True)
    receipt = runs / mod.RECEIPT_FILENAME
    receipt.write_text("operator-owned\n")
    with pytest.raises(mod.PackagingError, match="existing transfer receipt"):
        _import(package["bundle_dir"], repository)
    assert receipt.read_text() == "operator-owned\n"
    assert not (runs / "a6_holdout").exists()


@pytest.mark.parametrize("competitor", ("file", "directory", "symlink"))
def test_import_publication_race_never_replaces_appearing_target(
        tmp_path, monkeypatch, competitor):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    repository = tmp_path / "repo"
    runs = repository / "src/runs"
    (repository / ".git").mkdir(parents=True)
    runs.mkdir(parents=True)
    real_install = mod.install_tree_no_replace

    def inject(staging, destination, snapshot):
        target = Path(destination)
        if competitor == "file":
            target.write_text("preserve\n")
        elif competitor == "directory":
            target.mkdir()
            (target / "operator-owned").write_text("preserve\n")
        else:
            owner = tmp_path / "import-owner"
            owner.mkdir()
            (owner / "operator-owned").write_text("preserve\n")
            target.symlink_to(owner, target_is_directory=True)
        return real_install(staging, destination, snapshot)

    monkeypatch.setattr(mod, "install_tree_no_replace", inject)
    with pytest.raises(mod.PackagingError, match="rollback was incomplete"):
        _import(package["bundle_dir"], repository)
    target = runs / "a6_holdout"
    if competitor == "file":
        assert target.read_text() == "preserve\n"
    else:
        assert (target / "operator-owned").read_text() == "preserve\n"
        assert target.is_symlink() is (competitor == "symlink")
    assert not (runs / mod.RECEIPT_FILENAME).exists()
    assert (runs / ".a6_holdout.import-lock").is_dir()


def test_install_internal_file_collision_preserves_source_and_competitor(
        tmp_path, monkeypatch):
    staging = tmp_path / "staging"
    (staging / "nested").mkdir(parents=True)
    (staging / "A.txt").write_text("owned source\n")
    (staging / "nested/B.txt").write_text("owned nested source\n")
    snapshot = mod.snapshot_source(staging)
    target = tmp_path / "installed"
    collision = target / "A.txt"
    real_link = mod.os.link
    injected = False

    def collide_after_reservation(source, destination, **kwargs):
        nonlocal injected
        if Path(destination) == collision and not injected:
            injected = True
            collision.write_text("operator competitor\n")
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(mod.os, "link", collide_after_reservation)
    with pytest.raises(
            mod.IncompletePublicationError, match="rollback was incomplete"):
        mod.install_tree_no_replace(staging, target, snapshot)
    assert injected
    assert collision.read_text() == "operator competitor\n"
    assert mod.snapshot_source(staging) == snapshot
    assert (target / "nested").is_dir()


def test_receipt_publication_failure_rolls_back_target(tmp_path, monkeypatch):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    repository = tmp_path / "repo"
    runs = repository / "src/runs"
    (repository / ".git").mkdir(parents=True)
    runs.mkdir(parents=True)

    real_link = mod.os.link

    def fail_receipt(source, destination, **kwargs):
        if Path(destination) == runs / mod.RECEIPT_FILENAME:
            raise OSError("injected receipt publish failure")
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(mod.os, "link", fail_receipt)
    with pytest.raises(OSError, match="injected receipt publish failure"):
        _import(package["bundle_dir"], repository)
    assert not (runs / "a6_holdout").exists()
    assert not (runs / mod.RECEIPT_FILENAME).exists()
    assert not (runs / ".a6_holdout.import-lock").exists()


@pytest.mark.parametrize("competitor", ("file", "directory", "symlink"))
def test_receipt_publication_race_preserves_competitor_and_freezes_tree(
        tmp_path, monkeypatch, competitor):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    repository = tmp_path / "repo"
    runs = repository / "src/runs"
    (repository / ".git").mkdir(parents=True)
    runs.mkdir(parents=True)
    receipt = runs / mod.RECEIPT_FILENAME
    real_link = mod.os.link

    def inject(source, destination, **kwargs):
        destination = Path(destination)
        if destination == receipt and not destination.exists():
            if competitor == "file":
                destination.write_text("preserve\n")
            elif competitor == "directory":
                destination.mkdir()
                (destination / "operator-owned").write_text("preserve\n")
            else:
                owner = tmp_path / "receipt-owner"
                owner.mkdir()
                (owner / "operator-owned").write_text("preserve\n")
                destination.symlink_to(owner, target_is_directory=True)
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(mod.os, "link", inject)
    with pytest.raises(mod.PackagingError, match="rollback was incomplete"):
        _import(package["bundle_dir"], repository)
    assert (runs / "a6_holdout").is_dir()
    if competitor == "file":
        assert receipt.read_text() == "preserve\n"
    else:
        assert (receipt / "operator-owned").read_text() == "preserve\n"
        assert receipt.is_symlink() is (competitor == "symlink")
    assert (runs / ".a6_holdout.import-lock").is_dir()


def test_post_publish_validation_failure_rolls_back_both(
        tmp_path, monkeypatch):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    repository = tmp_path / "repo"
    runs = repository / "src/runs"
    (repository / ".git").mkdir(parents=True)
    runs.mkdir(parents=True)

    monkeypatch.setattr(
        mod, "validate_transfer_receipt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            mod.PackagingError("injected post-publish failure")))
    with pytest.raises(mod.PackagingError, match="post-publish"):
        _import(package["bundle_dir"], repository)
    assert not (runs / "a6_holdout").exists()
    assert not (runs / mod.RECEIPT_FILENAME).exists()
    assert not (runs / ".a6_holdout.import-lock").exists()


def test_target_competitor_during_rollback_is_preserved_with_lock(
        tmp_path, monkeypatch):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    repository = tmp_path / "repo"
    runs = repository / "src/runs"
    (repository / ".git").mkdir(parents=True)
    runs.mkdir(parents=True)
    def replace_target_file(_receipt, **_kwargs):
        victim = runs / "a6_holdout" / "PREFLIGHT.json"
        victim.unlink()
        victim.write_text("operator replacement\n")
        raise mod.PackagingError("injected post-publish failure")

    monkeypatch.setattr(mod, "validate_transfer_receipt", replace_target_file)
    with pytest.raises(mod.PackagingError, match="rollback was incomplete"):
        _import(package["bundle_dir"], repository)
    assert (runs / "a6_holdout").exists()
    assert (runs / "a6_holdout/PREFLIGHT.json").read_text() == (
        "operator replacement\n")
    assert (runs / mod.RECEIPT_FILENAME).is_file()
    assert (runs / ".a6_holdout.import-lock").is_dir()


def test_receipt_competitor_during_rollback_is_preserved_with_lock(
        tmp_path, monkeypatch):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    repository = tmp_path / "repo"
    runs = repository / "src/runs"
    (repository / ".git").mkdir(parents=True)
    runs.mkdir(parents=True)

    def replace_receipt(receipt, **_kwargs):
        receipt = Path(receipt)
        receipt.unlink()
        receipt.write_text("operator receipt replacement\n")
        raise mod.PackagingError("injected post-publish failure")

    monkeypatch.setattr(mod, "validate_transfer_receipt", replace_receipt)
    with pytest.raises(mod.PackagingError, match="rollback was incomplete"):
        _import(package["bundle_dir"], repository)
    assert (runs / "a6_holdout").is_dir()
    assert (runs / mod.RECEIPT_FILENAME).read_text() == (
        "operator receipt replacement\n")
    assert (runs / ".a6_holdout.import-lock").is_dir()


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
        mod.REPO_ROOT, {
            "packaging_code_commit": head,
            "experiment_code_commit": head,
        })
    parent = subprocess.check_output(
        ["git", "rev-parse", "HEAD^"], cwd=mod.REPO_ROOT, text=True).strip()
    with pytest.raises(mod.PackagingError, match="HEAD must exactly equal"):
        mod.validate_destination_repository(
            mod.REPO_ROOT, {
                "packaging_code_commit": parent,
                "experiment_code_commit": parent,
            })

    fake = tmp_path / "not-egg"
    (fake / ".git").mkdir(parents=True)
    (fake / "src").mkdir()
    with pytest.raises(mod.PackagingError, match="compatible egg"):
        mod.validate_destination_repository(
            fake, {
                "packaging_code_commit": head,
                "experiment_code_commit": head,
            })


def test_gzip_header_has_zero_mtime_and_no_filename(tmp_path):
    root = _source_root(tmp_path)
    package = _package(root, tmp_path / "packages")
    header = Path(package["archive"]).read_bytes()[:10]
    assert header[:2] == b"\x1f\x8b"
    assert header[3] & 0x08 == 0
    assert header[4:8] == b"\x00\x00\x00\x00"
    assert header[8:] == b"\x02\xff"
