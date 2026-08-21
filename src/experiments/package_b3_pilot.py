"""B3 factor-pilot transfer package (pack/import; no new publisher).

Packs the immutable raw pilot tree (`runs/b3_factor_pilot`) together with
one completed analysis artifact into a single no-replace bundle, and
imports it at a destination — REUSING the reviewed atomic-publication
helpers from ``package_a6_holdout`` (``snapshot_source``,
``canonical_tree_sha256``, ``install_tree_no_replace``,
``assert_job_quiescent``, ``sha256_file``, ``_canonical_json_bytes``,
``PackagingError``).  No publisher implementation is forked.

Guarantees: freeze-then-package (both trees are copied once into immutable
snapshots and every scientific validation/copy reads those snapshots); the
analysis is cross-bound to the EXACT raw
job (run-manifest SHA, raw-tree digest, and Slurm job binding — the
design manifest is shared across jobs and can never identify one);
Slurm quiescence is verified twice for the exact authenticated job and the
live sources are revalidated immediately before publication; the job id must
be canonically formed; a post-rename failure leaves the explicit incomplete
marker (which overrides any staged completion record), and import refuses
such a destination; import
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
import os
import subprocess
import sys
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re

import experiments.b3_factor_pilot as bp
import experiments.b3_pilot_anchor as anchor
import experiments.b3_pilot_evidence as evidence
import experiments.select_b3_confirmation as selector
from experiments.analyze_b3_factor_pilot import SCHEMA as ANALYSIS_SCHEMA
from experiments.package_a6_holdout import (
    IncompletePublicationError,
    PackagingError,
    _canonical_json_bytes,
    assert_job_quiescent,
    canonical_tree_sha256,
    freeze_source,
    install_tree_no_replace,
    sha256_file,
    snapshot_source,
)

BUNDLE_SCHEMA = "b3-factor-pilot-bundle-v1"
BUNDLE_MANIFEST_FILENAME = "BUNDLE_MANIFEST.json"
BUNDLE_COMPLETE_FILENAME = "BUNDLE_COMPLETE.json"
INCOMPLETE_MARKER = ".b3-bundle-incomplete"
IMPORT_INCOMPLETE_MARKER = ".b3-import-incomplete"
REPO_ROOT = Path(__file__).resolve().parents[2]
CELL_FILES = (
    "identity.json", "dictator.ckpt.json", "dictator.jsonl",
    "a2.cg.ckpt.json", "a2.iterations.jsonl", "a2.oracle.jsonl",
)
ROOT_FILES = ("MANIFEST.json", "JOB.json")
OPTIONAL_ROOT_FILES = ("AUDIT.md",)
ANALYSIS_OUTPUTS = ("DECISION.json", "SUMMARY.md", "cell_intervals.csv",
                    "matched_contrasts.csv", "setting_summary.csv")
JOB_ID_CANONICAL = re.compile(r"^[1-9][0-9]{0,17}$")

# every file whose code EXECUTES during packaging is provenance-pinned,
# including the shared a6 helpers
PROVENANCE_FILES = (
    "src/experiments/package_b3_pilot.py",
    "src/experiments/analyze_b3_factor_pilot.py",
    "src/experiments/audit_b3_factor_pilot.py",
    "src/experiments/b3_factor_pilot.py",
    "src/experiments/b3_pilot_anchor.py",
    "src/experiments/b3_factor_screen.py",
    "src/experiments/b3_pilot_evidence.py",
    "src/experiments/package_a6_holdout.py",
    "src/experiments/provenance_git.py",
    "src/experiments/select_b3_confirmation.py",
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


def _strict_json_object(raw: bytes, label: str) -> dict:
    try:
        value = evidence.strict_json_loads(raw, label)
    except evidence.EvidenceError as exc:
        raise PackagingError(str(exc)) from exc
    if not isinstance(value, dict):
        raise PackagingError(f"{label}: JSON root is not an object")
    return value


def _assert_no_unsafe_links(root: Path, snapshot: dict, label: str) -> None:
    """Reject every symlink (handled by snapshot) and every hard-linked file."""
    for row in snapshot["files"]:
        path = root / row["path"]
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise PackagingError(
                f"{label} has an unsafe linked/non-regular file: {path}")


def _safe_component(value, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value \
            or "\\" in value:
        raise PackagingError(f"unsafe bundle manifest path {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 1 \
            or path.parts[0] in (".", ".."):
        raise PackagingError(f"unsafe bundle manifest path {value!r}")
    lowered = value.lower()
    if lowered.startswith("a6") or "a6_" in lowered:
        raise PackagingError(
            f"{label} {value!r} crosses the A6 holdout boundary")
    return value


def _read_source_job_identity(runs_dir: str | os.PathLike) -> dict:
    """Authenticate the exact job bytes before creating package output."""
    runs = Path(runs_dir)
    try:
        job_bytes = evidence.read_regular_bytes_once(
            runs / bp.JOB_FILENAME, "JOB.json")
        manifest_bytes = evidence.read_regular_bytes_once(
            runs / bp.RUN_MANIFEST_FILENAME, "MANIFEST.json")
    except evidence.EvidenceError as exc:
        raise PackagingError(str(exc)) from exc
    job = _strict_json_object(job_bytes, "JOB.json")
    manifest = _strict_json_object(manifest_bytes, "MANIFEST.json")
    job_id = job.get("job_id")
    if (job.get("schema") != "b3-factor-pilot-job-v1"
            or not isinstance(job_id, str)
            or not JOB_ID_CANONICAL.fullmatch(job_id)):
        raise PackagingError("JOB.json is missing or malformed")
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    if (manifest_bytes != bp.canonical_manifest_bytes(manifest)
            or job.get("run_manifest_sha256") != manifest_sha
            or manifest.get("run_commit") != job.get("run_commit")):
        raise PackagingError(
            "JOB.json does not authenticate the exact MANIFEST.json bytes")
    return {
        "job": job,
        "job_bytes": job_bytes,
        "job_sha256": hashlib.sha256(job_bytes).hexdigest(),
        "manifest_sha256": manifest_sha,
    }


def _strict_jsonl(raw: bytes, label: str) -> list[dict]:
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise PackagingError(f"{label}: malformed UTF-8 JSONL") from exc
    rows = []
    for index, line in enumerate(lines, start=1):
        if not line:
            raise PackagingError(f"{label}: blank JSONL line {index}")
        row = _strict_json_object(line.encode(), f"{label}:{index}")
        rows.append(row)
    return rows


def verify_b3_packaging_commit(claimed: str) -> str:
    if (not claimed or len(claimed) != 40
            or not all(c in "0123456789abcdef" for c in claimed)):
        raise PackagingError(
            "packaging commit must be the full 40-character lowercase "
            "hexadecimal SHA")
    try:
        evidence.assert_no_history_rewrites(REPO_ROOT)
    except evidence.EvidenceError as exc:
        raise PackagingError(str(exc)) from exc
    try:
        resolved = subprocess.check_output(
            evidence.git_argv(REPO_ROOT, "rev-parse", "--verify",
                                   f"{claimed}^{{commit}}"),
            cwd=REPO_ROOT, env=evidence.git_env(),
            stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise PackagingError(
            f"packaging commit {claimed} does not resolve") from exc
    if resolved != claimed:
        raise PackagingError(
            f"packaging commit {claimed} resolves to {resolved}")
    if subprocess.run(
            evidence.git_argv(REPO_ROOT, "merge-base", "--is-ancestor",
                              claimed, "HEAD"),
            cwd=REPO_ROOT, env=evidence.git_env()).returncode != 0:
        raise PackagingError(
            f"packaging commit {claimed} is not an ancestor of HEAD")
    dirty = subprocess.check_output(
        evidence.git_argv(REPO_ROOT, "status", "--porcelain"),
        cwd=REPO_ROOT, env=evidence.git_env()).decode()
    if [line for line in dirty.splitlines() if not line.startswith("??")]:
        raise PackagingError(
            "working tree has tracked modifications; commit before packing")
    for relpath in PROVENANCE_FILES:
        committed = subprocess.check_output(
            evidence.git_argv(REPO_ROOT, "show",
                              f"{claimed}:{relpath}"),
            cwd=REPO_ROOT, env=evidence.git_env())
        if committed != (REPO_ROOT / relpath).read_bytes():
            raise PackagingError(
                f"{relpath} differs from the claimed packaging commit")
    return resolved


def _current_code_provenance() -> dict[str, str]:
    return {
        relpath: hashlib.sha256((REPO_ROOT / relpath).read_bytes()).hexdigest()
        for relpath in PROVENANCE_FILES
    }


def _verify_recorded_code_provenance(
    packaging_commit,
    recorded,
) -> None:
    if (not isinstance(packaging_commit, str)
            or len(packaging_commit) != 40
            or any(c not in "0123456789abcdef" for c in packaging_commit)):
        raise PackagingError("bundle packaging commit is malformed")
    if not isinstance(recorded, dict) or set(recorded) != set(PROVENANCE_FILES):
        raise PackagingError(
            "bundle code provenance does not list every executed helper")
    try:
        resolved = subprocess.check_output(
            evidence.git_argv(REPO_ROOT, "rev-parse", "--verify",
                                   f"{packaging_commit}^{{commit}}"),
            cwd=REPO_ROOT, env=evidence.git_env(),
            stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise PackagingError(
            "bundle packaging commit does not resolve") from exc
    if resolved != packaging_commit or subprocess.run(
            evidence.git_argv(REPO_ROOT, "merge-base", "--is-ancestor",
                              packaging_commit, "HEAD"),
            cwd=REPO_ROOT, env=evidence.git_env()).returncode != 0:
        raise PackagingError(
            "bundle packaging commit is not in current repository history")
    for relpath in PROVENANCE_FILES:
        try:
            committed = subprocess.check_output(
                evidence.git_argv(REPO_ROOT, "show",
                                  f"{packaging_commit}:{relpath}"),
                cwd=REPO_ROOT, env=evidence.git_env(),
                stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as exc:
            raise PackagingError(
                f"bundle packaging commit lacks helper {relpath}") from exc
        expected = hashlib.sha256(committed).hexdigest()
        if recorded.get(relpath) != expected:
            raise PackagingError(
                f"bundle code provenance mismatch for {relpath}")


def validate_raw_tree(runs_dir: str | os.PathLike) -> dict:
    """Exact-population gate: MANIFEST.json + JOB.json + the 60 frozen
    cell directories, each carrying exactly the six cell files; symlinks
    and non-regular entries are refused by snapshot_source."""
    runs = Path(runs_dir)
    snapshot = snapshot_source(runs)
    _assert_no_unsafe_links(runs.resolve(), snapshot, "raw tree")
    if not snapshot["files"]:
        raise PackagingError("empty raw tree; refusing")
    expected_tags = [cell["tag"] for cell in bp.build_cells()]
    expected_dirs = sorted(expected_tags)
    if snapshot["directories"] != expected_dirs:
        raise PackagingError(
            "raw tree directory population differs from the frozen 60-cell "
            "grid")
    required_files = sorted(
        [name for name in ROOT_FILES]
        + [f"{tag}/{name}" for tag in expected_tags for name in CELL_FILES])
    allowed_files = set(required_files) | set(OPTIONAL_ROOT_FILES)
    actual_files = [row["path"] for row in snapshot["files"]]
    unexpected = sorted(set(actual_files) - allowed_files)
    missing = sorted(set(required_files) - set(actual_files))
    if unexpected or missing:
        raise PackagingError(
            f"raw tree file population differs (unexpected={unexpected}, "
            f"missing={missing})")
    file_sha = {row["path"]: row["sha256"] for row in snapshot["files"]}
    # transactional reads bound to the frozen inventory: each root file is
    # read ONCE, its bytes must hash to the inventoried value, and the
    # SAME bytes are parsed — no live reread after inventory
    try:
        job_bytes = evidence.read_regular_bytes_once(
            runs / "JOB.json", "JOB.json")
    except evidence.EvidenceError as exc:
        raise PackagingError(str(exc)) from exc
    if hashlib.sha256(job_bytes).hexdigest() != file_sha["JOB.json"]:
        raise PackagingError(
            "JOB.json changed between inventory and read; refusing")
    job = _strict_json_object(job_bytes, "JOB.json")
    try:
        manifest_bytes = evidence.read_regular_bytes_once(
            runs / "MANIFEST.json", "MANIFEST.json")
    except evidence.EvidenceError as exc:
        raise PackagingError(str(exc)) from exc
    if hashlib.sha256(manifest_bytes).hexdigest() != (
            file_sha["MANIFEST.json"]):
        raise PackagingError(
            "MANIFEST.json changed between inventory and read; refusing")
    manifest = _strict_json_object(manifest_bytes, "MANIFEST.json")
    if manifest_bytes != bp.canonical_manifest_bytes(manifest):
        raise PackagingError("MANIFEST.json is not canonical JSON")
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
        # Every consumed byte carries its inventoried digest, so validating
        # one set of bytes and copying another (substitute during validation,
        # restore afterwards) is detected at the point of consumption rather
        # than by re-reading the path later.
        def _cell_read(name, *, as_json):
            rel = f"{tag}/{name}"
            digest = file_sha.get(rel)
            if digest is None:
                raise PackagingError(
                    f"{rel} is absent from the raw-tree inventory")
            reader = (evidence.read_json_object_once if as_json
                      else evidence.read_regular_bytes_once)
            return reader(runs / tag / name, rel, expected_sha256=digest)

        try:
            cg = _cell_read("a2.cg.ckpt.json", as_json=True)
            dictator = _cell_read("dictator.ckpt.json", as_json=True)
            oracle_rows = _strict_jsonl(
                _cell_read("a2.oracle.jsonl", as_json=False),
                f"{tag}/a2.oracle.jsonl")
            iteration_rows = _strict_jsonl(
                _cell_read("a2.iterations.jsonl", as_json=False),
                f"{tag}/a2.iterations.jsonl")
            dictator_rows = _strict_jsonl(
                _cell_read("dictator.jsonl", as_json=False),
                f"{tag}/dictator.jsonl")
        except evidence.EvidenceError as exc:
            raise PackagingError(str(exc)) from exc
        if oracle_rows != cg.get("oracle_events") \
                or iteration_rows != cg.get("iteration_events") \
                or dictator_rows != [dictator.get("record")]:
            raise PackagingError(
                f"{tag}: materialized JSONL files differ from checkpoint "
                "primitive evidence")
    from experiments import audit_b3_factor_pilot as b3_audit
    try:
        # Hand the audit the same inventory the packager validated against, so
        # the bytes it certifies are provably the bytes that get copied.
        audit_result = b3_audit.audit(runs, expected_digests=file_sha)
    except bp.B3PilotError as exc:
        raise PackagingError(f"raw tree audit failed: {exc}") from exc
    if not audit_result["ok"]:
        raise PackagingError(
            "raw tree primitive-evidence audit failed: "
            + "; ".join(audit_result["problems"]))
    tree_sha256 = canonical_tree_sha256(snapshot)
    return {
        "snapshot": snapshot,
        "tree_sha256": tree_sha256,
        "raw_identity": anchor.snapshot_identity(snapshot, tree_sha256),
        "manifest_sha256": manifest_sha,
        "job_sha256": file_sha["JOB.json"],
        "job": job,
        "run_commit": job["run_commit"],
        "cell_hashes": cell_hashes,
    }


def validate_analysis_artifact(
    analysis_dir: str | os.PathLike,
    runs_dir: str | os.PathLike,
    *,
    expected_raw_anchor: dict | None = None,
) -> dict:
    """Reapply the FULL analysis contract from the artifact itself, never
    from any wrapper's self-description: exact schema, the complete
    scoreable output set with recorded hashes and no unexpected files,
    verified provenance (analysis_code_verified AND the frozen screen),
    and a non-null raw-run binding."""
    base = Path(analysis_dir)
    snapshot = snapshot_source(base)
    _assert_no_unsafe_links(base.resolve(), snapshot, "analysis artifact")
    if not snapshot["files"]:
        raise PackagingError("empty analysis artifact; refusing")
    file_sha = {row["path"]: row["sha256"] for row in snapshot["files"]}
    if "MANIFEST.json" not in file_sha:
        raise PackagingError(
            f"missing analysis manifest: {base / 'MANIFEST.json'}")
    # transactional read bound to the frozen inventory
    try:
        manifest_bytes = evidence.read_regular_bytes_once(
            base / "MANIFEST.json", "analysis MANIFEST.json")
    except evidence.EvidenceError as exc:
        raise PackagingError(str(exc)) from exc
    if hashlib.sha256(manifest_bytes).hexdigest() != (
            file_sha["MANIFEST.json"]):
        raise PackagingError(
            "analysis MANIFEST.json changed between inventory and read")
    manifest = _strict_json_object(
        manifest_bytes, "analysis MANIFEST.json")
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
    if manifest.get("run_commit_verified") is not True:
        raise PackagingError(
            "analysis run_commit was not production-verified; not packable")
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
    try:
        verified = selector.load_analysis_artifact(
            base, runs_dir, expected_raw_anchor=expected_raw_anchor)
    except selector.B3SelectionError as exc:
        raise PackagingError(
            f"analysis artifact contract failed: {exc}") from exc
    return {
        "snapshot": snapshot,
        "tree_sha256": canonical_tree_sha256(snapshot),
        "manifest_sha256": file_sha["MANIFEST.json"],
        "outputs": dict(outputs),
        "run_manifest_sha256": manifest.get("run_manifest_sha256"),
        "analysis_code_commit": commit,
        "raw_binding": verified["raw_binding"],
    }


def _cross_bind(raw: dict, analysis: dict) -> None:
    """Bind the analysis to the EXACT raw job being packaged/imported: the
    shared design manifest SHA alone cannot identify a job, so the raw
    tree digest AND the Slurm job binding must both match."""
    if analysis["run_manifest_sha256"] != raw["manifest_sha256"]:
        raise PackagingError(
            "analysis artifact was produced from a DIFFERENT run manifest")
    binding = analysis.get("raw_binding") or {}
    for field, expected in (
            ("raw_tree_sha256", raw["tree_sha256"]),
            ("file_count", raw["snapshot"]["file_count"]),
            ("directory_count", raw["snapshot"]["directory_count"]),
            ("total_bytes", raw["snapshot"]["total_bytes"])):
        if binding.get(field) != expected:
            raise PackagingError(
                f"analysis raw binding field {field} does not match the "
                "raw tree being packaged (analysis of a DIFFERENT job)")
    if binding.get("job_id") != raw["job"]["job_id"]:
        raise PackagingError(
            "analysis job binding does not match the raw tree's Slurm job")
    if binding.get("job_sha256") != raw["job_sha256"]:
        raise PackagingError(
            "analysis JOB.json binding does not match the raw tree's "
            "JOB.json")
    if binding.get("manifest_sha256") != raw["manifest_sha256"]:
        raise PackagingError(
            "analysis MANIFEST.json binding does not match the raw tree's "
            "exact MANIFEST.json bytes")
    if binding.get("pre_analysis_anchor") != raw["raw_identity"]:
        raise PackagingError(
            "analysis raw binding field pre_analysis_anchor does not match "
            "the raw tree being packaged")


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


def _write_fsynced(path: Path, payload: bytes, mode: int = 0o644) -> None:
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def pack(runs_dir: str | os.PathLike, analysis_dir: str | os.PathLike,
         out_base: str | os.PathLike, packaging_commit: str, *,
         verify_commit: bool = True,
         job_quiescence_validator=assert_job_quiescent) -> dict:
    """Freeze, validate, and atomically publish one exact raw-job bundle."""
    # boundary refusals come BEFORE any recursive read
    _refuse_a6_paths(runs_dir, analysis_dir, out_base)
    _assert_disjoint(runs_dir, analysis_dir, "raw tree", "analysis dir")
    _assert_disjoint(out_base, runs_dir, "bundle output", "raw tree")
    _assert_disjoint(out_base, analysis_dir, "bundle output",
                     "analysis dir")
    if verify_commit:
        packaging_commit = verify_b3_packaging_commit(packaging_commit)
    # Authenticate the exact JOB/MANIFEST bytes and reject unsafe links before
    # creating any output.  Scientific validation happens only on the frozen
    # copies below.
    source_identity = _read_source_job_identity(runs_dir)
    job_id = source_identity["job"]["job_id"]
    # First production check: after reading only identity bytes, this exact
    # authenticated job must be quiescent before any outcome file is read.
    job_quiescence_validator(job_id)
    source_raw_snapshot = snapshot_source(runs_dir)
    source_analysis_snapshot = snapshot_source(analysis_dir)
    _assert_no_unsafe_links(
        Path(runs_dir).resolve(), source_raw_snapshot, "raw tree")
    _assert_no_unsafe_links(
        Path(analysis_dir).resolve(), source_analysis_snapshot,
        "analysis artifact")
    source_files = {
        row["path"]: row["sha256"] for row in source_raw_snapshot["files"]}
    if (source_files.get(bp.JOB_FILENAME) != source_identity["job_sha256"]
            or source_files.get(bp.RUN_MANIFEST_FILENAME)
            != source_identity["manifest_sha256"]):
        raise PackagingError(
            "raw JOB/MANIFEST bytes changed during job authentication")

    out_path = Path(out_base)
    if out_path.is_symlink():
        raise PackagingError(f"unsafe bundle output directory: {out_path}")
    out_preexisted = out_path.exists()
    out_path.mkdir(parents=True, exist_ok=True)
    bundle_name = (
        f"b3_pilot-job{job_id}-"
        f"{source_identity['manifest_sha256'][:12]}")
    destination = out_path / bundle_name
    if destination.exists() or destination.is_symlink():
        raise PackagingError(
            f"refusing existing bundle destination: {destination}")

    staging = Path(tempfile.mkdtemp(
        prefix=f".{bundle_name}.staging-", dir=out_path))
    renamed = False
    try:
        # The incomplete marker is durable before any other staged content.
        _write_fsynced(
            staging / INCOMPLETE_MARKER,
            _canonical_json_bytes({"state": "publication-incomplete"}),
            0o600)
        # One immutable raw snapshot is created before contract validation;
        # all subsequent validation and packaging reads use this frozen copy.
        frozen_raw_snapshot = freeze_source(runs_dir, staging / "runs")
        frozen_analysis_snapshot = freeze_source(
            analysis_dir, staging / "analysis")
        if frozen_raw_snapshot != source_raw_snapshot:
            raise PackagingError(
                "raw pilot tree mutated before immutable freeze; refusing")
        if frozen_analysis_snapshot != source_analysis_snapshot:
            raise PackagingError(
                "analysis artifact mutated before immutable freeze; refusing")
        raw = validate_raw_tree(staging / "runs")
        analysis = validate_analysis_artifact(
            staging / "analysis", staging / "runs",
            expected_raw_anchor=raw["raw_identity"])
        _cross_bind(raw, analysis)
        if (raw["job_sha256"] != source_identity["job_sha256"]
                or raw["manifest_sha256"]
                != source_identity["manifest_sha256"]
                or raw["job"]["job_id"] != job_id):
            raise PackagingError(
                "immutable snapshot does not match the authenticated job")

        bundle_manifest = {
            "schema": BUNDLE_SCHEMA,
            "campaign": "b3-factor-pilot",
            "packaging_commit": packaging_commit,
            "code_provenance": _current_code_provenance(),
            "run_commit": raw["run_commit"],
            "raw": {
                "tree_sha256": raw["tree_sha256"],
                "manifest_sha256": raw["manifest_sha256"],
                "job_sha256": raw["job_sha256"],
                "job_id": str(raw["job"]["job_id"]),
                "cells": raw["cell_hashes"],
                "file_count": raw["snapshot"]["file_count"],
                "directory_count": raw["snapshot"]["directory_count"],
                "total_bytes": raw["snapshot"]["total_bytes"],
                "pre_analysis_anchor": raw["raw_identity"],
            },
            "analysis": {
                "tree_sha256": analysis["tree_sha256"],
                "manifest_sha256": analysis["manifest_sha256"],
                "outputs": analysis["outputs"],
                "analysis_code_commit": analysis["analysis_code_commit"],
            },
        }
        manifest_bytes = _canonical_json_bytes(bundle_manifest)
        _write_fsynced(
            staging / BUNDLE_MANIFEST_FILENAME, manifest_bytes)
        bundle_manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        complete_payload = _canonical_json_bytes({
            "schema": "b3-factor-pilot-bundle-complete-v1",
            "bundle_manifest_sha256": bundle_manifest_sha,
        })
        _write_fsynced(
            staging / BUNDLE_COMPLETE_FILENAME, complete_payload)
        bundle_snapshot = snapshot_source(staging)
        _assert_no_unsafe_links(staging, bundle_snapshot, "bundle staging")

        # Second production check on the same authenticated job, followed by
        # immediate source revalidation.  No source byte is read after this
        # gate and before the exclusive publication rename.
        job_quiescence_validator(job_id)
        if snapshot_source(runs_dir) != source_raw_snapshot:
            raise PackagingError(
                "raw pilot tree mutated during packaging; refusing")
        if snapshot_source(analysis_dir) != source_analysis_snapshot:
            raise PackagingError(
                "analysis artifact mutated during packaging; refusing")
        install_tree_no_replace(staging, destination, bundle_snapshot)
        renamed = True

        # Marker removal is the sole logical commit and the final fallible
        # mutation.  Completion bytes were already durable before rename.
        flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            flags |= os.O_DIRECTORY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        destination_fd = os.open(destination, flags)
        try:
            try:
                os.unlink(INCOMPLETE_MARKER, dir_fd=destination_fd)
            except OSError as exc:
                try:
                    os.stat(
                        INCOMPLETE_MARKER, dir_fd=destination_fd,
                        follow_symlinks=False)
                except FileNotFoundError:
                    pass  # unlink committed before reporting an error
                else:
                    raise IncompletePublicationError(
                        f"bundle {destination} remains publication-incomplete",
                        renamed=True, destination=str(destination),
                        committed=False) from exc
        finally:
            try:
                os.close(destination_fd)
            except OSError:
                pass
    except BaseException as exc:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        if not renamed and not out_preexisted and out_path.exists():
            try:
                out_path.rmdir()
            except OSError:
                pass
        if renamed and (destination / INCOMPLETE_MARKER).exists():
            # Preserve the guarded destination as explicit recovery evidence.
            if isinstance(exc, IncompletePublicationError):
                raise
            raise IncompletePublicationError(
                f"bundle {destination} was renamed but remains guarded by "
                "the incomplete-publication marker",
                renamed=True, destination=str(destination),
                committed=False) from exc
        raise
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
    # Boundary/overlap/overwrite refusals come before output creation.
    _refuse_a6_paths(bundle_dir, destination_runs)
    _assert_disjoint(bundle_dir, destination_runs, "bundle",
                     "import destination")
    bundle = Path(bundle_dir)
    destination = Path(destination_runs)
    if bundle.is_symlink() or not bundle.is_dir():
        raise PackagingError(f"missing or unsafe bundle: {bundle}")
    if destination.exists() or destination.is_symlink():
        raise PackagingError(
            f"refusing import overwrite: {destination} exists")

    # Freeze the entire bundle once.  Validation and import copy only from
    # this immutable snapshot, never from a bundle that can be swapped between
    # authorization and installation.
    source_bundle_snapshot = snapshot_source(bundle)
    _assert_no_unsafe_links(
        bundle.resolve(), source_bundle_snapshot, "bundle")
    freeze_root = Path(tempfile.mkdtemp(prefix=".b3-bundle-freeze-"))
    frozen_bundle = freeze_root / "bundle"
    try:
        frozen_snapshot = freeze_source(bundle, frozen_bundle)
        if frozen_snapshot != source_bundle_snapshot:
            raise PackagingError("bundle changed during immutable freeze")
        top_level = {entry.name for entry in os.scandir(frozen_bundle)}
        expected_top = {
            "runs", "analysis", BUNDLE_MANIFEST_FILENAME,
            BUNDLE_COMPLETE_FILENAME}
        if top_level != expected_top:
            if INCOMPLETE_MARKER in top_level:
                raise PackagingError(
                    "bundle carries the incomplete-publication marker; "
                    "refusing")
            if BUNDLE_COMPLETE_FILENAME not in top_level:
                raise PackagingError(
                    f"bundle {bundle} lacks the completion marker; refusing")
            raise PackagingError(
                f"bundle top-level population differs: {sorted(top_level)}")

        try:
            manifest_bytes = evidence.read_regular_bytes_once(
                frozen_bundle / BUNDLE_MANIFEST_FILENAME,
                BUNDLE_MANIFEST_FILENAME)
            complete_bytes = evidence.read_regular_bytes_once(
                frozen_bundle / BUNDLE_COMPLETE_FILENAME,
                BUNDLE_COMPLETE_FILENAME)
        except evidence.EvidenceError as exc:
            raise PackagingError(str(exc)) from exc
        manifest = _strict_json_object(
            manifest_bytes, BUNDLE_MANIFEST_FILENAME)
        complete = _strict_json_object(
            complete_bytes, BUNDLE_COMPLETE_FILENAME)
        if manifest_bytes != _canonical_json_bytes(manifest):
            raise PackagingError("bundle manifest is not canonical JSON")
        if complete_bytes != _canonical_json_bytes(complete):
            raise PackagingError("bundle completion record is not canonical")
        if manifest.get("schema") != BUNDLE_SCHEMA:
            raise PackagingError("bundle manifest schema differs")
        _verify_recorded_code_provenance(
            manifest.get("packaging_commit"),
            manifest.get("code_provenance"))
        if complete != {
                "schema": "b3-factor-pilot-bundle-complete-v1",
                "bundle_manifest_sha256":
                    hashlib.sha256(manifest_bytes).hexdigest(),
        }:
            raise PackagingError(
                "bundle completion record does not bind the bundle manifest")

        raw_manifest = manifest.get("raw")
        analysis_manifest = manifest.get("analysis")
        if not isinstance(raw_manifest, dict) \
                or not isinstance(analysis_manifest, dict):
            raise PackagingError("bundle manifest sections are malformed")
        recorded_cells = raw_manifest.get("cells")
        if not isinstance(recorded_cells, dict) or not recorded_cells:
            raise PackagingError("bundle manifest cells are empty; refusing")
        expected_tags = {cell["tag"] for cell in bp.build_cells()}
        for tag, files in recorded_cells.items():
            _safe_component(tag, "cell tag")
            if not isinstance(files, dict):
                raise PackagingError(
                    f"bundle manifest cell {tag!r} files are malformed")
            for name in files:
                _safe_component(name, "cell file")
        if set(recorded_cells) != expected_tags:
            raise PackagingError(
                "bundle manifest cells differ from the frozen 60-cell grid")

        raw_tree = frozen_bundle / "runs"
        analysis_tree = frozen_bundle / "analysis"
        # Reapply the full raw and analysis contracts independently of the
        # wrapper's self-description.
        raw = validate_raw_tree(raw_tree)
        analysis = validate_analysis_artifact(
            analysis_tree, raw_tree,
            expected_raw_anchor=raw["raw_identity"])
        _cross_bind(raw, analysis)
        if (raw["tree_sha256"] != raw_manifest.get("tree_sha256")
                or raw["manifest_sha256"]
                != raw_manifest.get("manifest_sha256")
                or raw["job_sha256"] != raw_manifest.get("job_sha256")
                or raw["snapshot"]["file_count"]
                != raw_manifest.get("file_count")
                or raw["snapshot"]["directory_count"]
                != raw_manifest.get("directory_count")
                or raw["snapshot"]["total_bytes"]
                != raw_manifest.get("total_bytes")
                or raw["raw_identity"]
                != raw_manifest.get("pre_analysis_anchor")):
            raise PackagingError(
                "bundle raw contract differs from the independently "
                "validated tree")
        if (analysis["tree_sha256"]
                != analysis_manifest.get("tree_sha256")
                or analysis["manifest_sha256"]
                != analysis_manifest.get("manifest_sha256")
                or analysis["outputs"] != analysis_manifest.get("outputs")
                or analysis["analysis_code_commit"]
                != analysis_manifest.get("analysis_code_commit")):
            raise PackagingError(
                "bundle analysis contract differs from the independently "
                "validated artifact")
        if raw_manifest.get("job_id") != raw["job"]["job_id"]:
            raise PackagingError(
                "bundle manifest job id differs from the raw tree's JOB.json")
        if manifest.get("run_commit") != raw["run_commit"]:
            raise PackagingError(
                "bundle run commit differs from the raw tree")
        for tag, files in recorded_cells.items():
            if set(files) != set(CELL_FILES):
                raise PackagingError(
                    f"bundle manifest cell {tag} does not list the six "
                    "frozen cell files")
            for name, sha in files.items():
                if raw["cell_hashes"][tag][name] != sha:
                    raise PackagingError(
                        f"bundle cell file {tag}/{name} hash mismatch")

        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(
            prefix=".b3-import-staging-", dir=destination.parent))
        renamed = False
        try:
            shutil.rmtree(staging)
            _copy_snapshot(raw_tree, raw["snapshot"], staging)
            raw_staging_snapshot = snapshot_source(staging)
            if canonical_tree_sha256(raw_staging_snapshot) != (
                    raw_manifest["tree_sha256"]):
                raise PackagingError("import staging digest mismatch")
            _write_fsynced(
                staging / IMPORT_INCOMPLETE_MARKER,
                _canonical_json_bytes({"state": "import-incomplete"}),
                0o600)
            install_snapshot = snapshot_source(staging)

            # Immediate prepublication revalidation of the original immutable
            # source identity closes whole-bundle replacement TOCTOU.
            if snapshot_source(bundle) != source_bundle_snapshot:
                raise PackagingError(
                    "bundle changed immediately before import publication")
            install_tree_no_replace(staging, destination, install_snapshot)
            renamed = True

            flags = os.O_RDONLY
            if hasattr(os, "O_DIRECTORY"):
                flags |= os.O_DIRECTORY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            destination_fd = os.open(destination, flags)
            try:
                try:
                    os.unlink(
                        IMPORT_INCOMPLETE_MARKER, dir_fd=destination_fd)
                except OSError as exc:
                    try:
                        os.stat(
                            IMPORT_INCOMPLETE_MARKER, dir_fd=destination_fd,
                            follow_symlinks=False)
                    except FileNotFoundError:
                        pass
                    else:
                        raise IncompletePublicationError(
                            f"import {destination} remains incomplete",
                            renamed=True, destination=str(destination),
                            committed=False) from exc
            finally:
                try:
                    os.close(destination_fd)
                except OSError:
                    pass
        except BaseException as exc:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
            if renamed and (
                    destination / IMPORT_INCOMPLETE_MARKER).exists():
                if isinstance(exc, IncompletePublicationError):
                    raise
                raise IncompletePublicationError(
                    f"import {destination} was renamed but remains guarded",
                    renamed=True, destination=str(destination),
                    committed=False) from exc
            raise
        return {"target": str(destination),
                "tree_sha256": raw_manifest["tree_sha256"]}
    finally:
        shutil.rmtree(freeze_root, ignore_errors=True)


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
