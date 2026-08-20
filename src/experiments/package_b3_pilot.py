"""B3 factor-pilot transfer package (pack/import; no new publisher).

Packs the immutable raw pilot tree (`runs/b3_factor_pilot`) together with
one completed analysis artifact into a single no-replace bundle, and
imports it at a destination — REUSING the reviewed atomic-publication
helpers from ``package_a6_holdout`` (``snapshot_source``,
``canonical_tree_sha256``, ``install_tree_no_replace``,
``assert_job_quiescent``, ``sha256_file``, ``_canonical_json_bytes``,
``PackagingError``).  No publisher implementation is forked.

Guarantees: freeze-then-package (both trees are inventoried once and
copied FROM the frozen snapshots; no live reread of ``JOB.json`` or the
manifests after inventory); the analysis is cross-bound to the EXACT raw
job (run-manifest SHA, raw-tree digest, and Slurm job binding — the
design manifest is shared across jobs and can never identify one);
Slurm quiescence is verified before any byte is read AND immediately
before the publication rename; the job id must be canonically formed;
a post-rename failure leaves the explicit incomplete marker and no
completion record, and import refuses such a destination; import
reapplies the FULL frozen contract (population, analysis provenance,
cross-binding, safe manifest path keys) independent of the bundle's
self-description; A6 paths are refused before any recursive read; and
the bundle output/import destination must be disjoint from the sources
on resolved real paths.

Refusals additionally include: symlinks and non-regular files (via
``snapshot_source``), unexpected paths in the raw tree, mutation during
packaging (per-file against the frozen snapshot and by post-copy source
re-digest), an active Slurm job, an existing destination, and import
overwrite.  Nothing is launched and no cell outcome is interpreted here
— the utility binds bytes and hashes only.
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

import re

import experiments.b3_factor_pilot as bp
from experiments.analyze_b3_factor_pilot import SCHEMA as ANALYSIS_SCHEMA
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
BUNDLE_COMPLETE_FILENAME = "BUNDLE_COMPLETE.json"
INCOMPLETE_MARKER = ".b3-bundle-incomplete"
REPO_ROOT = Path(__file__).resolve().parents[2]
CELL_FILES = (
    "identity.json", "dictator.ckpt.json", "dictator.jsonl",
    "a2.cg.ckpt.json", "a2.iterations.jsonl", "a2.oracle.jsonl",
)
ROOT_FILES = ("MANIFEST.json", "JOB.json")
ANALYSIS_OUTPUTS = ("DECISION.json", "SUMMARY.md", "cell_intervals.csv",
                    "matched_contrasts.csv", "setting_summary.csv")
JOB_ID_CANONICAL = re.compile(r"^[1-9][0-9]{0,17}$")

# every file whose code EXECUTES during packaging is provenance-pinned,
# including the shared a6 helpers
PROVENANCE_FILES = (
    "src/experiments/package_b3_pilot.py",
    "src/experiments/b3_factor_pilot.py",
    "src/experiments/package_a6_holdout.py",
)


def _refuse_a6_paths(*paths: str | os.PathLike) -> None:
    """A6 boundary refusal on RESOLVED real paths, BEFORE any recursive
    read of the trees involved."""
    for path in paths:
        resolved = Path(path).resolve()
        for part in resolved.parts:
            lowered = part.lower()
            if lowered.startswith("a6") or "a6_" in lowered:
                raise PackagingError(
                    f"refusing A6 path (scientific boundary): {resolved}")


def _assert_disjoint(a: str | os.PathLike, b: str | os.PathLike,
                     label_a: str, label_b: str) -> None:
    ra = Path(a).resolve()
    rb = Path(b).resolve()
    if ra == rb or ra in rb.parents or rb in ra.parents:
        raise PackagingError(
            f"{label_a} {ra} and {label_b} {rb} must be disjoint on "
            "resolved real paths")


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
    if not snapshot["files"]:
        raise PackagingError("empty raw tree; refusing")
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
    file_sha = {row["path"]: row["sha256"] for row in snapshot["files"]}
    # transactional reads bound to the frozen inventory: each root file is
    # read ONCE, its bytes must hash to the inventoried value, and the
    # SAME bytes are parsed — no live reread after inventory
    job_bytes = (runs / "JOB.json").read_bytes()
    if hashlib.sha256(job_bytes).hexdigest() != file_sha["JOB.json"]:
        raise PackagingError(
            "JOB.json changed between inventory and read; refusing")
    job = json.loads(job_bytes)
    manifest_bytes = (runs / "MANIFEST.json").read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != (
            file_sha["MANIFEST.json"]):
        raise PackagingError(
            "MANIFEST.json changed between inventory and read; refusing")
    manifest = json.loads(manifest_bytes)
    if (job.get("schema") != "b3-factor-pilot-job-v1"
            or not job.get("job_id")
            or not job.get("run_manifest_sha256")
            or not job.get("run_commit")):
        raise PackagingError("JOB.json is missing or malformed")
    # the job id must be a canonically formed Slurm id; a substituted or
    # unauthenticated value refuses
    job_id = job["job_id"]
    if not isinstance(job_id, str) or not JOB_ID_CANONICAL.match(job_id):
        raise PackagingError(
            f"job id {job_id!r} is not a canonical Slurm job id; refusing")
    manifest_sha = file_sha["MANIFEST.json"]
    if job["run_manifest_sha256"] != manifest_sha:
        raise PackagingError(
            "JOB.json run_manifest_sha256 does not match MANIFEST.json")
    if manifest.get("run_commit") != job.get("run_commit"):
        raise PackagingError("JOB.json / MANIFEST.json run commit mismatch")
    cell_hashes = {}
    for tag in expected_tags:
        cell_hashes[tag] = {
            name: file_sha[f"{tag}/{name}"] for name in CELL_FILES}
    return {
        "snapshot": snapshot,
        "tree_sha256": canonical_tree_sha256(snapshot),
        "manifest_sha256": manifest_sha,
        "job_sha256": file_sha["JOB.json"],
        "job": job,
        "run_commit": job["run_commit"],
        "cell_hashes": cell_hashes,
    }


def validate_analysis_artifact(analysis_dir: str | os.PathLike) -> dict:
    """Reapply the FULL analysis contract from the artifact itself, never
    from any wrapper's self-description: exact schema, the complete
    scoreable output set with recorded hashes and no unexpected files,
    verified provenance (analysis_code_verified AND the frozen screen),
    and a non-null raw-run binding."""
    base = Path(analysis_dir)
    snapshot = snapshot_source(base)
    if not snapshot["files"]:
        raise PackagingError("empty analysis artifact; refusing")
    file_sha = {row["path"]: row["sha256"] for row in snapshot["files"]}
    if "MANIFEST.json" not in file_sha:
        raise PackagingError(
            f"missing analysis manifest: {base / 'MANIFEST.json'}")
    # transactional read bound to the frozen inventory
    manifest_bytes = (base / "MANIFEST.json").read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != (
            file_sha["MANIFEST.json"]):
        raise PackagingError(
            "analysis MANIFEST.json changed between inventory and read")
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != ANALYSIS_SCHEMA:
        raise PackagingError(
            f"analysis manifest schema {manifest.get('schema')!r} is not "
            f"{ANALYSIS_SCHEMA!r}")
    outputs = manifest.get("outputs") or {}
    if set(outputs) != set(ANALYSIS_OUTPUTS):
        raise PackagingError(
            "analysis manifest outputs are not the complete scoreable set: "
            f"{sorted(outputs)}")
    expected = sorted(list(outputs) + ["MANIFEST.json"])
    actual = [row["path"] for row in snapshot["files"]]
    if actual != expected:
        raise PackagingError(
            f"analysis artifact population differs: {actual} != {expected}")
    for name, recorded in outputs.items():
        if file_sha[name] != recorded:
            raise PackagingError(
                f"analysis output {name} hash mismatch (tampered)")
    if manifest.get("analysis_code_verified") is not True:
        raise PackagingError(
            "analysis was produced without code verification; not packable")
    if (manifest.get("frozen_screen") or {}).get("record_sha256") != (
            bp.FROZEN_SCREEN_RECORD_SHA256) or manifest.get(
            "frozen_screen_verified") is not True:
        raise PackagingError(
            "analysis screen binding differs from the frozen screen "
            "constant; non-scoreable analysis is not packable")
    if not manifest.get("run_manifest_sha256"):
        raise PackagingError(
            "analysis manifest carries no raw-run binding; refusing")
    commit = manifest.get("analysis_code_commit")
    if (not isinstance(commit, str) or len(commit) != 40
            or not all(c in "0123456789abcdef" for c in commit)
            or commit == "0" * 40):
        raise PackagingError(
            f"analysis code commit {commit!r} is not a real 40-hex commit")
    return {
        "snapshot": snapshot,
        "tree_sha256": canonical_tree_sha256(snapshot),
        "manifest_sha256": file_sha["MANIFEST.json"],
        "outputs": dict(outputs),
        "run_manifest_sha256": manifest.get("run_manifest_sha256"),
        "analysis_code_commit": commit,
        "raw_binding": manifest.get("raw_binding"),
    }


def _cross_bind(raw: dict, analysis: dict) -> None:
    """Bind the analysis to the EXACT raw job being packaged/imported: the
    shared design manifest SHA alone cannot identify a job, so the raw
    tree digest AND the Slurm job binding must both match."""
    if analysis["run_manifest_sha256"] != raw["manifest_sha256"]:
        raise PackagingError(
            "analysis artifact was produced from a DIFFERENT run manifest")
    binding = analysis.get("raw_binding") or {}
    if binding.get("raw_tree_sha256") != raw["tree_sha256"]:
        raise PackagingError(
            "analysis raw-tree digest does not match the raw tree being "
            "packaged (analysis of a DIFFERENT job)")
    if binding.get("job_id") != raw["job"]["job_id"]:
        raise PackagingError(
            "analysis job binding does not match the raw tree's Slurm job")
    if binding.get("job_sha256") != raw["job_sha256"]:
        raise PackagingError(
            "analysis JOB.json binding does not match the raw tree's "
            "JOB.json")


def _copy_snapshot(source: Path, snapshot: dict,
                   destination: Path) -> None:
    """Package FROM THE FROZEN SNAPSHOT: only inventoried paths are
    copied, and every file's bytes must still hash to the inventoried
    value (any interleaved mutation refuses)."""
    destination.mkdir(parents=True)
    for rel in sorted(snapshot["directories"]):
        (destination / rel).mkdir(parents=True, exist_ok=True)
    for row in snapshot["files"]:
        data = (source / row["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise PackagingError(
                f"{row['path']} mutated during packaging; refusing")
        (destination / row["path"]).write_bytes(data)


def pack(runs_dir: str | os.PathLike, analysis_dir: str | os.PathLike,
         out_base: str | os.PathLike, packaging_commit: str, *,
         verify_commit: bool = True,
         job_quiescence_validator=assert_job_quiescent) -> dict:
    """Bundle the raw pilot tree + analysis artifact atomically."""
    # boundary refusals come BEFORE any recursive read
    _refuse_a6_paths(runs_dir, analysis_dir, out_base)
    _assert_disjoint(runs_dir, analysis_dir, "raw tree", "analysis dir")
    _assert_disjoint(out_base, runs_dir, "bundle output", "raw tree")
    _assert_disjoint(out_base, analysis_dir, "bundle output",
                     "analysis dir")
    if verify_commit:
        packaging_commit = verify_b3_packaging_commit(packaging_commit)
    raw = validate_raw_tree(runs_dir)
    analysis = validate_analysis_artifact(analysis_dir)
    _cross_bind(raw, analysis)
    # the launched job must be finished before any byte is packaged
    job_quiescence_validator(raw["job"]["job_id"])

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
        # the guard marker is staged FIRST so a partially published bundle
        # can never present itself as complete
        (staging / INCOMPLETE_MARKER).write_bytes(
            _canonical_json_bytes({"state": "publication-incomplete"}))
        # freeze-then-package: both trees are copied FROM their frozen
        # snapshots; no path outside the inventory is ever read again and
        # any interleaved byte change refuses
        _copy_snapshot(Path(runs_dir).resolve(), raw["snapshot"],
                       staging / "runs")
        _copy_snapshot(Path(analysis_dir).resolve(), analysis["snapshot"],
                       staging / "analysis")
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
        manifest_bytes = _canonical_json_bytes(bundle_manifest)
        (staging / BUNDLE_MANIFEST_FILENAME).write_bytes(manifest_bytes)
        bundle_manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        # copies must byte-match the validated sources
        copied_raw = canonical_tree_sha256(snapshot_source(staging / "runs"))
        if copied_raw != raw["tree_sha256"]:
            raise PackagingError("bundle raw copy does not match the source")
        copied_analysis = canonical_tree_sha256(
            snapshot_source(staging / "analysis"))
        if copied_analysis != analysis["tree_sha256"]:
            raise PackagingError(
                "bundle analysis copy does not match the source")
        # quiescence is re-verified IMMEDIATELY before the publication
        # rename: a job resubmitted mid-packaging refuses
        job_quiescence_validator(raw["job"]["job_id"])
        # atomic no-replace publication via the REVIEWED shared installer
        bundle_snapshot = snapshot_source(staging)
        install_tree_no_replace(staging, destination, bundle_snapshot)
    except BaseException:
        if staging.exists():
            import shutil
            shutil.rmtree(staging, ignore_errors=True)
        raise
    # post-rename commit: write the completion record, THEN drop the guard
    # marker.  Any failure here leaves the explicit incomplete marker in
    # place (and no completion record), so failure can never look like
    # success; import refuses such a destination.
    try:
        complete_payload = _canonical_json_bytes({
            "schema": "b3-factor-pilot-bundle-complete-v1",
            "bundle_manifest_sha256": bundle_manifest_sha,
        })
        descriptor = os.open(
            destination / BUNDLE_COMPLETE_FILENAME,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(complete_payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.unlink(destination / INCOMPLETE_MARKER)
        directory_fd = os.open(destination, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException as exc:
        raise IncompletePublicationError(
            f"bundle {destination} was renamed but not committed; the "
            f"incomplete marker remains: {exc}") from exc
    return {"bundle_dir": str(destination),
            "bundle_manifest_sha256": bundle_manifest_sha}


def import_bundle(bundle_dir: str | os.PathLike,
                  destination_runs: str | os.PathLike) -> dict:
    """Reapply the FULL contract to a bundle — independently of its
    self-description — and install its raw tree at the destination
    without ever overwriting an existing path.

    Requirements re-proven here: the completion record and absent
    incomplete marker; canonical bundle manifest with safe (relative,
    frozen-population) tag/file keys; the exact frozen 60-cell raw
    population with matching digests and hashes; the full analysis
    contract (schema, scoreable outputs, verified provenance, non-null
    run binding); and the raw/analysis cross-binding to the exact job."""
    # boundary refusals come BEFORE any recursive read
    _refuse_a6_paths(bundle_dir, destination_runs)
    _assert_disjoint(bundle_dir, destination_runs, "bundle",
                     "import destination")
    bundle = Path(bundle_dir)
    if bundle.is_symlink() or not bundle.is_dir():
        raise PackagingError(f"missing or unsafe bundle: {bundle}")
    # failure must not look like success: a bundle still carrying the
    # incomplete marker, or lacking the completion record, refuses
    if (bundle / INCOMPLETE_MARKER).exists():
        raise PackagingError(
            f"bundle {bundle} carries the incomplete-publication marker; "
            "refusing")
    complete_path = bundle / BUNDLE_COMPLETE_FILENAME
    if not complete_path.is_file() or complete_path.is_symlink():
        raise PackagingError(
            f"bundle {bundle} lacks the completion marker; refusing")
    manifest_path = bundle / BUNDLE_MANIFEST_FILENAME
    raw_bytes = manifest_path.read_bytes()
    manifest = json.loads(raw_bytes)
    if raw_bytes != _canonical_json_bytes(manifest):
        raise PackagingError("bundle manifest is not canonical JSON")
    if manifest.get("schema") != BUNDLE_SCHEMA:
        raise PackagingError("bundle manifest schema differs")
    complete = json.loads(complete_path.read_bytes())
    if complete.get("bundle_manifest_sha256") != hashlib.sha256(
            raw_bytes).hexdigest():
        raise PackagingError(
            "bundle completion record does not bind the bundle manifest")
    recorded_cells = manifest.get("raw", {}).get("cells")
    if not recorded_cells:
        raise PackagingError("bundle manifest cells are empty; refusing")
    expected_tags = {cell["tag"] for cell in bp.build_cells()}
    for tag, files in recorded_cells.items():
        for key in (tag, *files):
            path_key = Path(key)
            if path_key.is_absolute() or ".." in path_key.parts \
                    or len(path_key.parts) != 1:
                raise PackagingError(
                    f"unsafe bundle manifest path component {key!r}")
    if set(recorded_cells) != expected_tags:
        raise PackagingError(
            "bundle manifest cells differ from the frozen 60-cell grid")
    raw_tree = bundle / "runs"
    analysis_tree = bundle / "analysis"
    # the trees must satisfy the FULL frozen contracts, not merely match
    # the bundle's own digests
    raw = validate_raw_tree(raw_tree)
    analysis = validate_analysis_artifact(analysis_tree)
    _cross_bind(raw, analysis)
    if raw["tree_sha256"] != manifest["raw"]["tree_sha256"]:
        raise PackagingError("bundle raw tree digest mismatch (tampered)")
    if analysis["tree_sha256"] != manifest["analysis"]["tree_sha256"]:
        raise PackagingError(
            "bundle analysis tree digest mismatch (tampered)")
    if manifest["raw"].get("job_id") != raw["job"]["job_id"]:
        raise PackagingError(
            "bundle manifest job id differs from the raw tree's JOB.json")
    for tag, files in recorded_cells.items():
        if set(files) != set(CELL_FILES):
            raise PackagingError(
                f"bundle manifest cell {tag} does not list the six frozen "
                "cell files")
        for name, sha in files.items():
            if raw["cell_hashes"][tag][name] != sha:
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
        # _copy_snapshot requires a fresh directory
        import shutil
        shutil.rmtree(staging)
        _copy_snapshot(raw_tree.resolve(), raw["snapshot"], staging)
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
