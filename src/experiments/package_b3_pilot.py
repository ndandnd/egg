"""B3 factor-pilot transfer package (pack/import; no new publisher).

Packs the immutable raw pilot tree (`runs/b3_factor_pilot`) together with
one completed analysis artifact into a single no-replace bundle, and
imports it at a destination — REUSING the reviewed atomic-publication
helpers from ``package_a6_holdout`` (``snapshot_source``,
``canonical_tree_sha256``, ``install_tree_no_replace``,
``assert_job_quiescent``, ``sha256_file``, ``_canonical_json_bytes``,
``PackagingError``).  No publisher implementation is forked.

Refusals: symlinks and non-regular files (via ``snapshot_source``),
unexpected paths in the raw tree, mutation during packaging (the source
tree is re-digested after the copy), an active Slurm job, an existing
destination, and import overwrite.  Nothing is launched and no cell
outcome is interpreted here — the utility binds bytes and hashes only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.b3_factor_pilot as bp
from experiments.package_a6_holdout import (
    IncompletePublicationError,
    PackagingError,
    _canonical_json_bytes,
    assert_job_quiescent,
    canonical_tree_sha256,
    install_tree_no_replace,
    sha256_file,
    snapshot_source,
)

BUNDLE_SCHEMA = "b3-factor-pilot-bundle-v1"
BUNDLE_MANIFEST_FILENAME = "BUNDLE_MANIFEST.json"
REPO_ROOT = Path(__file__).resolve().parents[2]
CELL_FILES = (
    "identity.json", "dictator.ckpt.json", "dictator.jsonl",
    "a2.cg.ckpt.json", "a2.iterations.jsonl", "a2.oracle.jsonl",
)
ROOT_FILES = ("MANIFEST.json", "JOB.json")

PROVENANCE_FILES = (
    "src/experiments/package_b3_pilot.py",
    "src/experiments/b3_factor_pilot.py",
)


def verify_b3_packaging_commit(claimed: str) -> str:
    if (not claimed or len(claimed) != 40
            or not all(c in "0123456789abcdef" for c in claimed)):
        raise PackagingError(
            "packaging commit must be the full 40-character lowercase "
            "hexadecimal SHA")
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{claimed}^{{commit}}"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise PackagingError(
            f"packaging commit {claimed} does not resolve") from exc
    if resolved != claimed:
        raise PackagingError(
            f"packaging commit {claimed} resolves to {resolved}")
    if subprocess.run(
            ["git", "merge-base", "--is-ancestor", claimed, "HEAD"],
            cwd=REPO_ROOT).returncode != 0:
        raise PackagingError(
            f"packaging commit {claimed} is not an ancestor of HEAD")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT).decode()
    if [line for line in dirty.splitlines() if not line.startswith("??")]:
        raise PackagingError(
            "working tree has tracked modifications; commit before packing")
    for relpath in PROVENANCE_FILES:
        committed = subprocess.check_output(
            ["git", "show", f"{claimed}:{relpath}"], cwd=REPO_ROOT)
        if committed != (REPO_ROOT / relpath).read_bytes():
            raise PackagingError(
                f"{relpath} differs from the claimed packaging commit")
    return resolved


def validate_raw_tree(runs_dir: str | os.PathLike) -> dict:
    """Exact-population gate: MANIFEST.json + JOB.json + the 60 frozen
    cell directories, each carrying exactly the six cell files; symlinks
    and non-regular entries are refused by snapshot_source."""
    runs = Path(runs_dir)
    snapshot = snapshot_source(runs)
    expected_tags = [cell["tag"] for cell in bp.build_cells()]
    expected_dirs = sorted(expected_tags)
    if snapshot["directories"] != expected_dirs:
        raise PackagingError(
            "raw tree directory population differs from the frozen 60-cell "
            "grid")
    expected_files = sorted(
        [name for name in ROOT_FILES]
        + [f"{tag}/{name}" for tag in expected_tags for name in CELL_FILES])
    actual_files = [row["path"] for row in snapshot["files"]]
    if actual_files != expected_files:
        unexpected = sorted(set(actual_files) - set(expected_files))
        missing = sorted(set(expected_files) - set(actual_files))
        raise PackagingError(
            f"raw tree file population differs (unexpected={unexpected}, "
            f"missing={missing})")
    job = json.loads((runs / "JOB.json").read_text())
    if (job.get("schema") != "b3-factor-pilot-job-v1"
            or not job.get("job_id")
            or not job.get("run_manifest_sha256")
            or not job.get("run_commit")):
        raise PackagingError("JOB.json is missing or malformed")
    manifest_sha = sha256_file(runs / "MANIFEST.json")
    if job["run_manifest_sha256"] != manifest_sha:
        raise PackagingError(
            "JOB.json run_manifest_sha256 does not match MANIFEST.json")
    manifest = json.loads((runs / "MANIFEST.json").read_text())
    if manifest.get("run_commit") != job.get("run_commit"):
        raise PackagingError("JOB.json / MANIFEST.json run commit mismatch")
    cell_hashes = {}
    file_sha = {row["path"]: row["sha256"] for row in snapshot["files"]}
    for tag in expected_tags:
        cell_hashes[tag] = {
            name: file_sha[f"{tag}/{name}"] for name in CELL_FILES}
    return {
        "snapshot": snapshot,
        "tree_sha256": canonical_tree_sha256(snapshot),
        "manifest_sha256": manifest_sha,
        "job_sha256": sha256_file(runs / "JOB.json"),
        "job": job,
        "run_commit": job["run_commit"],
        "cell_hashes": cell_hashes,
    }


def validate_analysis_artifact(analysis_dir: str | os.PathLike) -> dict:
    """Bind the completed analysis artifact byte-for-byte: manifest
    canonical, every listed output present with its recorded hash, and no
    unexpected files."""
    base = Path(analysis_dir)
    snapshot = snapshot_source(base)
    manifest_path = base / "MANIFEST.json"
    if not manifest_path.is_file():
        raise PackagingError(f"missing analysis manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    outputs = manifest.get("outputs") or {}
    expected = sorted(list(outputs) + ["MANIFEST.json"])
    actual = [row["path"] for row in snapshot["files"]]
    if actual != expected:
        raise PackagingError(
            f"analysis artifact population differs: {actual} != {expected}")
    for name, recorded in outputs.items():
        actual_sha = sha256_file(base / name)
        if actual_sha != recorded:
            raise PackagingError(
                f"analysis output {name} hash mismatch (tampered)")
    return {
        "snapshot": snapshot,
        "tree_sha256": canonical_tree_sha256(snapshot),
        "manifest_sha256": sha256_file(manifest_path),
        "outputs": dict(outputs),
        "run_manifest_sha256": manifest.get("run_manifest_sha256"),
        "analysis_code_commit": manifest.get("analysis_code_commit"),
    }


def _copy_tree(source: Path, destination: Path) -> None:
    """Byte-exact copy of an already-validated (symlink-free) tree."""
    destination.mkdir(parents=True)
    for dirpath, dirnames, filenames in os.walk(source, followlinks=False):
        dirnames.sort()
        filenames.sort()
        rel = Path(dirpath).relative_to(source)
        for dirname in dirnames:
            (destination / rel / dirname).mkdir()
        for filename in filenames:
            data = (Path(dirpath) / filename).read_bytes()
            (destination / rel / filename).write_bytes(data)


def pack(runs_dir: str | os.PathLike, analysis_dir: str | os.PathLike,
         out_base: str | os.PathLike, packaging_commit: str, *,
         verify_commit: bool = True,
         job_quiescence_validator=assert_job_quiescent) -> dict:
    """Bundle the raw pilot tree + analysis artifact atomically."""
    if verify_commit:
        packaging_commit = verify_b3_packaging_commit(packaging_commit)
    raw = validate_raw_tree(runs_dir)
    analysis = validate_analysis_artifact(analysis_dir)
    if (analysis["run_manifest_sha256"] is not None
            and analysis["run_manifest_sha256"] != raw["manifest_sha256"]):
        raise PackagingError(
            "analysis artifact was produced from a DIFFERENT run manifest")
    # the launched job must be finished before any byte is packaged
    job_quiescence_validator(str(raw["job"]["job_id"]))

    out_path = Path(out_base)
    if out_path.is_symlink():
        raise PackagingError(f"unsafe bundle output directory: {out_path}")
    out_path.mkdir(parents=True, exist_ok=True)
    bundle_name = (
        f"b3_pilot-job{raw['job']['job_id']}-"
        f"{raw['manifest_sha256'][:12]}")
    destination = out_path / bundle_name
    if destination.exists() or destination.is_symlink():
        raise PackagingError(
            f"refusing existing bundle destination: {destination}")

    import tempfile
    staging = Path(tempfile.mkdtemp(
        prefix=f".{bundle_name}.staging-", dir=out_path))
    try:
        _copy_tree(Path(runs_dir).resolve(), staging / "runs")
        _copy_tree(Path(analysis_dir).resolve(), staging / "analysis")
        # mutation-during-packaging gate: the SOURCE trees must digest
        # identically after the copy completed
        if canonical_tree_sha256(
                snapshot_source(runs_dir)) != raw["tree_sha256"]:
            raise PackagingError(
                "raw pilot tree mutated during packaging; refusing")
        if canonical_tree_sha256(
                snapshot_source(analysis_dir)) != analysis["tree_sha256"]:
            raise PackagingError(
                "analysis artifact mutated during packaging; refusing")
        bundle_manifest = {
            "schema": BUNDLE_SCHEMA,
            "campaign": "b3-factor-pilot",
            "packaging_commit": packaging_commit,
            "run_commit": raw["run_commit"],
            "raw": {
                "tree_sha256": raw["tree_sha256"],
                "manifest_sha256": raw["manifest_sha256"],
                "job_sha256": raw["job_sha256"],
                "job_id": str(raw["job"]["job_id"]),
                "cells": raw["cell_hashes"],
                "file_count": raw["snapshot"]["file_count"],
            },
            "analysis": {
                "tree_sha256": analysis["tree_sha256"],
                "manifest_sha256": analysis["manifest_sha256"],
                "outputs": analysis["outputs"],
                "analysis_code_commit": analysis["analysis_code_commit"],
            },
        }
        (staging / BUNDLE_MANIFEST_FILENAME).write_bytes(
            _canonical_json_bytes(bundle_manifest))
        # copies must byte-match the validated sources
        copied_raw = canonical_tree_sha256(snapshot_source(staging / "runs"))
        if copied_raw != raw["tree_sha256"]:
            raise PackagingError("bundle raw copy does not match the source")
        copied_analysis = canonical_tree_sha256(
            snapshot_source(staging / "analysis"))
        if copied_analysis != analysis["tree_sha256"]:
            raise PackagingError(
                "bundle analysis copy does not match the source")
        # atomic no-replace publication via the REVIEWED shared installer
        bundle_snapshot = snapshot_source(staging)
        install_tree_no_replace(staging, destination, bundle_snapshot)
    except BaseException:
        if staging.exists():
            import shutil
            shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"bundle_dir": str(destination),
            "bundle_manifest_sha256": sha256_file(
                destination / BUNDLE_MANIFEST_FILENAME)}


def import_bundle(bundle_dir: str | os.PathLike,
                  destination_runs: str | os.PathLike) -> dict:
    """Validate a bundle byte-for-byte and install its raw tree at the
    destination without ever overwriting an existing path."""
    bundle = Path(bundle_dir)
    if bundle.is_symlink() or not bundle.is_dir():
        raise PackagingError(f"missing or unsafe bundle: {bundle}")
    manifest_path = bundle / BUNDLE_MANIFEST_FILENAME
    raw_bytes = manifest_path.read_bytes()
    manifest = json.loads(raw_bytes)
    if raw_bytes != _canonical_json_bytes(manifest):
        raise PackagingError("bundle manifest is not canonical JSON")
    if manifest.get("schema") != BUNDLE_SCHEMA:
        raise PackagingError("bundle manifest schema differs")
    raw_tree = bundle / "runs"
    analysis_tree = bundle / "analysis"
    if canonical_tree_sha256(snapshot_source(raw_tree)) != (
            manifest["raw"]["tree_sha256"]):
        raise PackagingError("bundle raw tree digest mismatch (tampered)")
    if canonical_tree_sha256(snapshot_source(analysis_tree)) != (
            manifest["analysis"]["tree_sha256"]):
        raise PackagingError(
            "bundle analysis tree digest mismatch (tampered)")
    for tag, files in manifest["raw"]["cells"].items():
        for name, sha in files.items():
            if sha256_file(raw_tree / tag / name) != sha:
                raise PackagingError(
                    f"bundle cell file {tag}/{name} hash mismatch")

    destination = Path(destination_runs)
    if destination.exists() or destination.is_symlink():
        raise PackagingError(
            f"refusing import overwrite: {destination} exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    staging = Path(tempfile.mkdtemp(
        prefix=".b3-import-staging-", dir=destination.parent))
    try:
        # _copy_tree requires a fresh directory
        import shutil
        shutil.rmtree(staging)
        _copy_tree(raw_tree.resolve(), staging)
        snapshot = snapshot_source(staging)
        if canonical_tree_sha256(snapshot) != manifest["raw"]["tree_sha256"]:
            raise PackagingError("import staging digest mismatch")
        install_tree_no_replace(staging, destination, snapshot)
    except BaseException:
        if staging.exists():
            import shutil
            shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"target": str(destination),
            "tree_sha256": manifest["raw"]["tree_sha256"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    commands = ap.add_subparsers(dest="command", required=True)
    pack_parser = commands.add_parser("pack")
    pack_parser.add_argument("--runs", default="runs/b3_factor_pilot")
    pack_parser.add_argument("--analysis-dir", required=True)
    pack_parser.add_argument("--out", required=True)
    pack_parser.add_argument("--packaging-commit", required=True)
    import_parser = commands.add_parser("import")
    import_parser.add_argument("--bundle-dir", required=True)
    import_parser.add_argument("--destination", required=True)
    args = ap.parse_args()
    if args.command == "pack":
        result = pack(args.runs, args.analysis_dir, args.out,
                      args.packaging_commit)
        print(result["bundle_dir"])
    else:
        result = import_bundle(args.bundle_dir, args.destination)
        print(result["target"])


if __name__ == "__main__":
    main()
