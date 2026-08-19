#!/usr/bin/env python3
"""Validate and deterministically package the completed A6 holdout.

This command is intentionally post-run only.  It does not launch, resume, or
modify experiment cells.  Before creating any output it validates the frozen
selection, whole-population preflight, one-shot launch chain, all 128 method
cells, and the exact 64+64 completion contract.  The source run directory is
read-only throughout.

The resulting directory contains a reproducible ``tar.gz`` archive, an
external copy of its inventory manifest and audit summary, and a SHA-256
sidecar for transfer verification.  The archive extracts from the repository
root as ``src/runs/a6_holdout`` plus ``A6_HOLDOUT_TRANSFER`` metadata.
"""
from __future__ import annotations

import argparse
import datetime
import gzip
import hashlib
import io
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zlib
from pathlib import Path, PurePosixPath

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCHEMA = "a6-holdout-transfer-bundle-v1"
SOURCE_ARC_ROOT = "src/runs/a6_holdout"
METADATA_ARC_ROOT = "A6_HOLDOUT_TRANSFER"
DEFAULT_OUT = "runs/a6_holdout_packages"
AUDIT_EXPECT_CG = 128
AUDIT_EXPECT_METHOD = {"a2": 64, "a6_a4": 64}
METHODS = ("a2", "a6_a4")
HOLDOUT_INSTANCES = tuple(
    (seed, n_trips, b)
    for seed in range(16, 32)
    for n_trips in (8, 12)
    for b in (0.01, 0.05)
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SELECTION = (
    REPO_ROOT / "result" / "a6_pilot" / "20260819T005514Z"
    / "SELECTION.json"
)
EXPECTED_SELECTION_SHA256 = (
    "026ddc38e90f9dd2e9342a50cfb5550bc52731c5f1ee67d87d53008bd6b4b507"
)
EXPECTED_SELECTION_COMMIT = (
    "8f59a905bd5e12ac5784e57aebc66a03b47a00cb"
)


class PackagingError(RuntimeError):
    """The campaign cannot be packaged without weakening its contract."""


def sha256_file(path: str | os.PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_packaging_code_commit(claimed: str) -> str:
    """Bind packaging output to clean tracked code at the claimed HEAD."""
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True,
            stderr=subprocess.STDOUT).strip()
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as exc:
        raise PackagingError("cannot resolve packaging Git provenance") from exc
    if not (head.startswith(claimed) or claimed.startswith(head)):
        raise PackagingError(
            f"packaging code commit mismatch: HEAD {head[:12]} vs {claimed}")
    if dirty:
        raise PackagingError(
            "packaging tree has uncommitted tracked changes:\n" + dirty)
    return head


def assert_frozen_grid(instances) -> None:
    got = tuple(instances)
    if len(got) != 64 or len(set(got)) != 64 or set(got) != set(
            HOLDOUT_INSTANCES):
        raise PackagingError("holdout package grid is not the frozen 64 instances")


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _stat_signature(value: os.stat_result) -> tuple:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _validate_relative_name(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    for component in relative.parts:
        if (component in ("", ".", "..") or "\\" in component
                or any(ord(char) < 32 or ord(char) == 127
                       for char in component)):
            raise PackagingError(f"unsafe source path: {relative!s}")
    return relative.as_posix()


def _stable_file_record(root: Path, path: Path) -> dict:
    """Hash one regular file while refusing replacement or mutation."""
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise PackagingError(f"source entry is not a regular file: {path}")
    if before.st_nlink != 1:
        raise PackagingError(f"source file must not be hard-linked: {path}")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if _stat_signature(opened) != _stat_signature(before):
                raise PackagingError(f"source file changed before hashing: {path}")
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
            after_read = os.fstat(handle.fileno())
    except OSError as exc:
        raise PackagingError(f"cannot read source file: {path}") from exc
    try:
        after_close = path.lstat()
    except OSError as exc:
        raise PackagingError(f"source file disappeared while hashing: {path}") from exc
    if (_stat_signature(after_read) != _stat_signature(before)
            or _stat_signature(after_close) != _stat_signature(before)):
        raise PackagingError(f"source file changed while hashing: {path}")
    return {
        "path": _validate_relative_name(path, root),
        "sha256": digest.hexdigest(),
        "size": before.st_size,
    }


def snapshot_source(root: str | os.PathLike) -> dict:
    """Inventory a source tree without following or accepting symlinks."""
    raw_root = Path(root).expanduser()
    if raw_root.is_symlink():
        raise PackagingError(f"source root must not be a symlink: {raw_root}")
    root_path = raw_root.resolve()
    if not root_path.is_dir():
        raise PackagingError(f"missing source run directory: {root_path}")

    directories = []
    files = []
    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        dirnames.sort()
        filenames.sort()
        parent = Path(dirpath)
        for dirname in dirnames:
            child = parent / dirname
            child_stat = child.lstat()
            if not stat.S_ISDIR(child_stat.st_mode):
                raise PackagingError(
                    f"source directory entry is not a regular directory: {child}")
            directories.append(_validate_relative_name(child, root_path))
        for filename in filenames:
            files.append(_stable_file_record(root_path, parent / filename))

    directories.sort()
    files.sort(key=lambda row: row["path"])
    return {
        "directories": directories,
        "files": files,
        "file_count": len(files),
        "directory_count": len(directories),
        "total_bytes": sum(row["size"] for row in files),
    }


def freeze_source(
    root: str | os.PathLike,
    destination: str | os.PathLike,
) -> dict:
    """Copy a stable, regular-file-only snapshot and verify its identity."""
    raw_root = Path(root).expanduser()
    if raw_root.is_symlink():
        raise PackagingError(f"source root must not be a symlink: {raw_root}")
    root_path = raw_root.resolve()
    if not root_path.is_dir():
        raise PackagingError(f"missing source run directory: {root_path}")
    destination_path = Path(destination)
    destination_path.mkdir(parents=True, exist_ok=False)

    directories = []
    files = []
    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        dirnames.sort()
        filenames.sort()
        parent = Path(dirpath)
        relative_parent = parent.relative_to(root_path)
        frozen_parent = destination_path / relative_parent
        for dirname in dirnames:
            source_dir = parent / dirname
            source_stat = source_dir.lstat()
            if not stat.S_ISDIR(source_stat.st_mode):
                raise PackagingError(
                    "source directory entry is not a regular directory: "
                    f"{source_dir}")
            relative = _validate_relative_name(source_dir, root_path)
            (destination_path / relative).mkdir(mode=0o700)
            directories.append(relative)

        for filename in filenames:
            source = parent / filename
            relative = _validate_relative_name(source, root_path)
            before = source.lstat()
            if not stat.S_ISREG(before.st_mode):
                raise PackagingError(
                    f"source entry is not a regular file: {source}")
            if before.st_nlink != 1:
                raise PackagingError(
                    f"source file must not be hard-linked: {source}")
            flags = os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                descriptor = os.open(source, flags)
            except OSError as exc:
                raise PackagingError(
                    f"cannot safely open source file: {source}") from exc
            digest = hashlib.sha256()
            target = frozen_parent / filename
            try:
                with os.fdopen(descriptor, "rb") as source_handle:
                    opened = os.fstat(source_handle.fileno())
                    if (_stat_signature(opened) != _stat_signature(before)
                            or not stat.S_ISREG(opened.st_mode)):
                        raise PackagingError(
                            f"source changed before snapshot copy: {source}")
                    with target.open("xb") as target_handle:
                        for chunk in iter(
                                lambda: source_handle.read(1 << 20), b""):
                            digest.update(chunk)
                            target_handle.write(chunk)
                        target_handle.flush()
                        os.fsync(target_handle.fileno())
                    after = os.fstat(source_handle.fileno())
            except OSError as exc:
                raise PackagingError(
                    f"cannot snapshot source file: {source}") from exc
            try:
                closed = source.lstat()
            except OSError as exc:
                raise PackagingError(
                    f"source disappeared during snapshot copy: {source}") from exc
            if (_stat_signature(after) != _stat_signature(before)
                    or _stat_signature(closed) != _stat_signature(before)):
                raise PackagingError(
                    f"source changed during snapshot copy: {source}")
            files.append({
                "path": relative,
                "sha256": digest.hexdigest(),
                "size": before.st_size,
            })

    directories.sort()
    files.sort(key=lambda row: row["path"])
    snapshot = {
        "directories": directories,
        "files": files,
        "file_count": len(files),
        "directory_count": len(directories),
        "total_bytes": sum(row["size"] for row in files),
    }
    if snapshot_source(root_path) != snapshot:
        raise PackagingError("source tree changed during snapshot copy")
    if snapshot_source(destination_path) != snapshot:
        raise PackagingError("frozen snapshot differs from source inventory")
    return snapshot


def _normalized_tarinfo(name: str, *, directory: bool, size: int = 0):
    info = tarfile.TarInfo(name=name + ("/" if directory else ""))
    info.type = tarfile.DIRTYPE if directory else tarfile.REGTYPE
    info.mode = 0o755 if directory else 0o644
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.size = 0 if directory else size
    return info


class _HashingReader:
    def __init__(self, handle):
        self.handle = handle
        self.digest = hashlib.sha256()

    def read(self, size=-1):
        data = self.handle.read(size)
        self.digest.update(data)
        return data


def _write_archive(
    archive_path: Path,
    root: Path,
    snapshot: dict,
    manifest_bytes: bytes,
    audit_bytes: bytes,
) -> None:
    """Write normalized archive bytes and recheck each streamed source."""
    entries = []
    source_dirs = [SOURCE_ARC_ROOT] + [
        f"{SOURCE_ARC_ROOT}/{rel}" for rel in snapshot["directories"]
    ]
    metadata_dirs = [METADATA_ARC_ROOT]
    entries.extend((name, "directory", None) for name in source_dirs)
    entries.extend((name, "directory", None) for name in metadata_dirs)
    entries.extend([
        (f"{METADATA_ARC_ROOT}/AUDIT_SUMMARY.md", "bytes", audit_bytes),
        (f"{METADATA_ARC_ROOT}/MANIFEST.json", "bytes", manifest_bytes),
    ])
    by_path = {row["path"]: row for row in snapshot["files"]}
    entries.extend(
        (f"{SOURCE_ARC_ROOT}/{rel}", "source", by_path[rel])
        for rel in sorted(by_path)
    )

    with archive_path.open("wb") as raw:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0
        ) as compressed:
            with tarfile.open(
                fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT
            ) as archive:
                for arcname, kind, payload in sorted(entries):
                    if kind == "directory":
                        archive.addfile(_normalized_tarinfo(
                            arcname, directory=True))
                        continue
                    if kind == "bytes":
                        archive.addfile(
                            _normalized_tarinfo(
                                arcname, directory=False, size=len(payload)),
                            io.BytesIO(payload),
                        )
                        continue

                    record = payload
                    source = root / record["path"]
                    before = source.lstat()
                    if (not stat.S_ISREG(before.st_mode)
                            or before.st_size != record["size"]):
                        raise PackagingError(
                            f"source changed before archive write: {source}")
                    with source.open("rb") as handle:
                        opened = os.fstat(handle.fileno())
                        if _stat_signature(opened) != _stat_signature(before):
                            raise PackagingError(
                                f"source changed before archive read: {source}")
                        reader = _HashingReader(handle)
                        archive.addfile(
                            _normalized_tarinfo(
                                arcname, directory=False,
                                size=record["size"]),
                            reader,
                        )
                        after = os.fstat(handle.fileno())
                    if (_stat_signature(after) != _stat_signature(before)
                            or reader.digest.hexdigest() != record["sha256"]):
                        raise PackagingError(
                            f"source changed during archive write: {source}")
        raw.flush()
        os.fsync(raw.fileno())


def _verify_archive(
    archive_path: Path,
    snapshot: dict,
    manifest_bytes: bytes,
    audit_bytes: bytes,
) -> None:
    """Read back every member and verify layout, metadata, and content."""
    with archive_path.open("rb") as handle:
        header = handle.read(10)
    if (len(header) != 10 or header[:3] != b"\x1f\x8b\x08"
            or header[3] != 0 or header[4:8] != b"\x00\x00\x00\x00"
            or header[8:] != b"\x02\xff"):
        raise PackagingError("archive gzip header is not canonical")
    try:
        with gzip.open(archive_path, "rb") as compressed:
            for _chunk in iter(lambda: compressed.read(1 << 20), b""):
                pass
    except (OSError, EOFError) as exc:
        raise PackagingError(
            f"archive gzip stream is corrupt: {archive_path}") from exc

    expected_files = {
        f"{SOURCE_ARC_ROOT}/{row['path']}": row
        for row in snapshot["files"]
    }
    expected_bytes = {
        f"{METADATA_ARC_ROOT}/AUDIT_SUMMARY.md": audit_bytes,
        f"{METADATA_ARC_ROOT}/MANIFEST.json": manifest_bytes,
    }
    expected_dirs = {SOURCE_ARC_ROOT, METADATA_ARC_ROOT} | {
        f"{SOURCE_ARC_ROOT}/{relative}"
        for relative in snapshot["directories"]
    }
    expected_names = sorted(
        list(expected_dirs)
        + list(expected_files) + list(expected_bytes))

    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            members = archive.getmembers()
            if [member.name for member in members] != expected_names:
                raise PackagingError("archive member population/order is invalid")
            for member in members:
                if (member.uid != 0 or member.gid != 0 or member.uname != ""
                        or member.gname != "" or member.mtime != 0):
                    raise PackagingError(
                        "archive member metadata is not normalized: "
                        f"{member.name}")
                if member.isdir():
                    if (member.mode != 0o755
                            or member.name.rstrip("/") not in expected_dirs):
                        raise PackagingError(
                            f"archive directory is invalid: {member.name}")
                    continue
                if not member.isfile() or member.mode != 0o644:
                    raise PackagingError(
                        f"archive member type/mode is invalid: {member.name}")
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise PackagingError(
                        f"cannot read archive member: {member.name}")
                digest = hashlib.sha256()
                size = 0
                chunks = [] if member.name in expected_bytes else None
                for chunk in iter(lambda: extracted.read(1 << 20), b""):
                    digest.update(chunk)
                    size += len(chunk)
                    if chunks is not None:
                        chunks.append(chunk)
                if member.name in expected_bytes:
                    if b"".join(chunks) != expected_bytes[member.name]:
                        raise PackagingError(
                            f"embedded metadata differs: {member.name}")
                else:
                    record = expected_files.get(member.name)
                    if (record is None or size != record["size"]
                            or digest.hexdigest() != record["sha256"]):
                        raise PackagingError(
                            f"archived source content differs: {member.name}")
    except PackagingError:
        raise
    except (OSError, EOFError, tarfile.TarError) as exc:
        raise PackagingError(f"archive readback failed: {archive_path}") from exc


def _write_bytes(path: Path, payload: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _canonical_audit_summary(lines: list[str]) -> bytes:
    normalized = list(lines)
    if not normalized:
        raise PackagingError("audit returned no summary")
    normalized[0] = f"# Run summary: `{SOURCE_ARC_ROOT}`"
    return ("\n".join(normalized) + "\n").encode()


def assert_job_quiescent(job_id: str) -> None:
    """Require Slurm to report no active entries for the launched job."""
    try:
        result = subprocess.run(
            ["squeue", "--noheader", "--me", "--format=%F|%T"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        raise PackagingError(
            "squeue is unavailable; package on Unicorn after the job ends") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        raise PackagingError(f"cannot query active Slurm jobs: {detail}")
    states = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.strip().split("|", 1)
        job = fields[0].strip() if fields else ""
        state = fields[1].strip() if len(fields) == 2 else ""
        if len(fields) != 2 or not job.isdigit() or not state:
            raise PackagingError(f"malformed squeue output: {line!r}")
        if job == job_id:
            states.append(state)
    if states:
        raise PackagingError(
            f"Slurm job {job_id} is still active ({', '.join(states)}); "
            "no campaign outcomes were read")


def validate_scientific_population(
    paths: dict,
    preflight: dict,
    selection: dict,
    packaging_commit: str,
    *,
    instances=HOLDOUT_INSTANCES,
    cell_extractor=None,
    population_validator=None,
    provenance_validator=None,
) -> dict:
    """Run the analyzer's non-decision scoreability/provenance gates."""
    if (cell_extractor is None or population_validator is None
            or provenance_validator is None):
        import pandas as pd
        from experiments.analyze_a6_holdout import (
            check_population_contract,
            extract_cell,
            verify_run_provenance,
        )

        cell_extractor = cell_extractor or extract_cell
        population_validator = population_validator or check_population_contract
        provenance_validator = provenance_validator or verify_run_provenance
    else:
        import pandas as pd

    rows = [
        cell_extractor(paths[(method, seed, n_trips, b)],
                       method, seed, n_trips, b)
        for seed, n_trips, b in instances
        for method in METHODS
    ]
    cells = pd.DataFrame(rows)
    population_validator(cells, len(instances))
    experiment_prefixes = set(str(value) for value in cells.source_commit)
    if len(experiment_prefixes) != 1:
        raise PackagingError("population mixes experiment code commits")
    experiment_prefix = next(iter(experiment_prefixes))
    if not preflight["code_commit"].startswith(experiment_prefix):
        raise PackagingError(
            "PREFLIGHT code commit differs from cell source commit")
    selection_commit = selection.get("selection_commit")
    if not selection_commit:
        raise PackagingError("selection artifact commit is unresolved")
    resolved = provenance_validator(
        cells, selection_commit, packaging_commit)
    if resolved != preflight["code_commit"]:
        raise PackagingError(
            "resolved experiment commit differs from PREFLIGHT code commit")
    return {
        "status": "PASS",
        "method_cells": len(cells),
        "experiment_code_commit": resolved,
        "checks": [
            "terminal scoreability",
            "oracle and wall partition coherence",
            "dictator and uplift interval coherence",
            "broadcast price-path coherence",
            "population scientific identity",
            "selection-run-packaging Git ancestry",
        ],
        "decision_computed": False,
    }


def _manifest_document(
    *,
    packaging_commit: str,
    selection: dict,
    preflight: dict,
    launch: dict,
    scientific: dict,
    snapshot: dict,
    audit_bytes: bytes,
) -> dict:
    launch_manifest = launch["manifest"]
    launch_lock = launch["lock"]
    canonical_inventory = json.dumps(
        {"directories": snapshot["directories"], "files": snapshot["files"]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return {
        "schema": SCHEMA,
        "campaign": "a6-holdout",
        "packaging_code_commit": packaging_commit,
        "experiment_code_commit": preflight["code_commit"],
        "scientific_validation": scientific,
        "selection": {
            "path": "result/a6_pilot/20260819T005514Z/SELECTION.json",
            "sha256": selection["sha256"],
            "artifact_commit": selection.get("selection_commit"),
            "selected_arm": selection["selected_arm"],
        },
        "preflight": {
            "path": f"{SOURCE_ARC_ROOT}/PREFLIGHT.json",
            "sha256": preflight["sha256"],
            "physical_instances": preflight["physical_instances"],
            "market_instances": preflight["market_instances"],
            "method_cells": preflight["method_cells"],
        },
        "launch": {
            "schema": launch["schema"],
            "job_id": launch["job_id"],
            "code_commit": launch["code_commit"],
            "selection_sha256": launch["selection_sha256"],
            "preflight_sha256": launch["preflight_sha256"],
            "grid_list_sha256": launch["grid_list_sha256"],
            "claimed_utc": launch["claimed_utc"],
            "prepared_utc": launch["prepared_utc"],
            "submitted_utc": launch["submitted_utc"],
            "manifest_submitted_utc": launch["manifest_submitted_utc"],
            "manifest": {
                "path": f"{SOURCE_ARC_ROOT}/{Path(launch_manifest['path']).name}",
                "sha256": launch_manifest["sha256"],
            },
            "lock": {
                name: {
                    "path": f"{SOURCE_ARC_ROOT}/SUBMISSION_LOCK/{name}",
                    "sha256": launch_lock[name]["sha256"],
                }
                for name in sorted(launch_lock)
            },
        },
        "audit": {
            "status": "PASS",
            "contract": {
                "expect_cg": AUDIT_EXPECT_CG,
                "expect_cg_method": AUDIT_EXPECT_METHOD,
                "expect_cg_certified_method": None,
            },
            "summary_path": f"{METADATA_ARC_ROOT}/AUDIT_SUMMARY.md",
            "summary_sha256": hashlib.sha256(audit_bytes).hexdigest(),
        },
        "source": {
            "path": SOURCE_ARC_ROOT,
            "canonical_tree_sha256": hashlib.sha256(
                canonical_inventory).hexdigest(),
            **snapshot,
        },
        "scope": {
            "included": "every directory and regular file under the campaign root",
            "excluded": [
                f"src/slurm-egg-a6-holdout-{launch['job_id']}_<task>.out "
                "operational "
                "stdout files, which Slurm writes outside the canonical "
                "campaign root"
            ],
        },
        "runtime": {
            "python": platform.python_version(),
            "zlib_build": zlib.ZLIB_VERSION,
            "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION,
        },
        "archive": {
            "format": "tar.gz",
            "tar_format": "PAX",
            "gzip_mtime": 0,
            "normalized_uid_gid": 0,
            "normalized_file_mode": "0644",
            "normalized_directory_mode": "0755",
            "archive_sha256_location": "external ARCHIVE.sha256 sidecar",
            "byte_determinism": (
                "same source inventory, packaging commit, Python, and zlib runtime"
            ),
        },
    }


def _safe_inventory_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise PackagingError(f"invalid inventory path: {value!r}")
    path = PurePosixPath(value)
    if (path.is_absolute() or value != path.as_posix()
            or any(part in ("", ".", "..") for part in path.parts)
            or "\\" in value
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise PackagingError(f"unsafe inventory path: {value!r}")
    return value


def _full_hex(value: object, length: int) -> bool:
    return (isinstance(value, str) and len(value) == length
            and all(char in "0123456789abcdef" for char in value))


def _manifest_timestamp(value: object, label: str) -> datetime.datetime:
    if not isinstance(value, str):
        raise PackagingError(f"bundle manifest {label} is invalid")
    try:
        return datetime.datetime.strptime(
            value, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.timezone.utc)
    except ValueError as exc:
        raise PackagingError(
            f"bundle manifest {label} is invalid") from exc


def _validated_manifest_snapshot(manifest: dict, audit_bytes: bytes) -> dict:
    expected_top = {
        "archive", "audit", "campaign", "experiment_code_commit", "launch",
        "packaging_code_commit", "preflight", "runtime", "schema", "scope",
        "scientific_validation", "selection", "source",
    }
    if set(manifest) != expected_top:
        raise PackagingError("bundle manifest top-level keys differ")
    if manifest.get("schema") != SCHEMA or manifest.get("campaign") != "a6-holdout":
        raise PackagingError("bundle manifest has wrong schema/campaign")
    packaging_commit = manifest.get("packaging_code_commit")
    experiment_commit = manifest.get("experiment_code_commit")
    if not _full_hex(packaging_commit, 40) or not _full_hex(
            experiment_commit, 40):
        raise PackagingError("bundle manifest commit identity is invalid")

    selection = manifest.get("selection") or {}
    expected_selection = {
        "path": "result/a6_pilot/20260819T005514Z/SELECTION.json",
        "sha256": EXPECTED_SELECTION_SHA256,
        "artifact_commit": EXPECTED_SELECTION_COMMIT,
        "selected_arm": "a6_a4",
    }
    if selection != expected_selection:
        raise PackagingError("bundle manifest selection identity is invalid")

    preflight = manifest.get("preflight") or {}
    if (set(preflight) != {
            "path", "sha256", "physical_instances", "market_instances",
            "method_cells"}
            or preflight.get("path") != f"{SOURCE_ARC_ROOT}/PREFLIGHT.json"
            or not _full_hex(preflight.get("sha256"), 64)
            or preflight.get("physical_instances") != 32
            or preflight.get("market_instances") != 64
            or preflight.get("method_cells") != 128):
        raise PackagingError("bundle manifest preflight identity is invalid")

    scientific = manifest.get("scientific_validation") or {}
    if (set(scientific) != {
            "status", "method_cells", "experiment_code_commit", "checks",
            "decision_computed"}
            or scientific.get("status") != "PASS"
            or scientific.get("method_cells") != 128
            or scientific.get("experiment_code_commit") != experiment_commit
            or scientific.get("decision_computed") is not False
            or not isinstance(scientific.get("checks"), list)
            or not scientific["checks"]
            or any(not isinstance(value, str) or not value
                   for value in scientific["checks"])):
        raise PackagingError(
            "bundle manifest scientific validation is invalid")

    launch = manifest.get("launch") or {}
    if set(launch) != {
            "schema", "job_id", "code_commit", "selection_sha256",
            "preflight_sha256", "grid_list_sha256", "claimed_utc",
            "prepared_utc", "submitted_utc", "manifest_submitted_utc",
            "manifest", "lock"}:
        raise PackagingError("bundle manifest launch keys differ")
    if (launch.get("schema") != "a6-holdout-launch-provenance-v1"
            or not isinstance(launch.get("job_id"), str)
            or not launch["job_id"].isdigit()
            or launch.get("code_commit") != experiment_commit
            or launch.get("selection_sha256") != EXPECTED_SELECTION_SHA256
            or launch.get("preflight_sha256") != preflight["sha256"]
            or not _full_hex(launch.get("grid_list_sha256"), 64)):
        raise PackagingError("bundle manifest launch identity is invalid")
    launch_times = [
        _manifest_timestamp(launch[field], field)
        for field in (
            "claimed_utc", "prepared_utc", "submitted_utc",
            "manifest_submitted_utc")
    ]
    if launch_times != sorted(launch_times):
        raise PackagingError("bundle manifest launch chronology is invalid")
    launch_manifest = launch.get("manifest") or {}
    lock = launch.get("lock") or {}
    if (set(launch_manifest) != {"path", "sha256"}
            or not isinstance(launch_manifest.get("path"), str)
            or not launch_manifest["path"].startswith(
                f"{SOURCE_ARC_ROOT}/MANIFEST-")
            or not launch_manifest["path"].endswith("Z.txt")
            or not _full_hex(launch_manifest.get("sha256"), 64)
            or set(lock) != {"CLAIM.txt", "INTENT.txt", "SUBMITTED.txt"}):
        raise PackagingError("bundle manifest launch records are invalid")
    for name, record in lock.items():
        if (not isinstance(record, dict)
                or record != {
                    "path": f"{SOURCE_ARC_ROOT}/SUBMISSION_LOCK/{name}",
                    "sha256": record.get("sha256"),
                }
                or not _full_hex(record.get("sha256"), 64)):
            raise PackagingError("bundle manifest launch lock is invalid")

    if (manifest.get("source") or {}).get("path") != SOURCE_ARC_ROOT:
        raise PackagingError("bundle manifest has wrong source path")
    expected_audit = {
        "expect_cg": AUDIT_EXPECT_CG,
        "expect_cg_method": AUDIT_EXPECT_METHOD,
        "expect_cg_certified_method": None,
    }
    audit_doc = manifest.get("audit") or {}
    if (audit_doc.get("status") != "PASS"
            or audit_doc.get("contract") != expected_audit
            or audit_doc.get("summary_path")
            != f"{METADATA_ARC_ROOT}/AUDIT_SUMMARY.md"
            or audit_doc.get("summary_sha256")
            != hashlib.sha256(audit_bytes).hexdigest()):
        raise PackagingError("bundle manifest audit contract is invalid")
    source = manifest["source"]
    directories = source.get("directories")
    files = source.get("files")
    if not isinstance(directories, list) or not isinstance(files, list):
        raise PackagingError("bundle manifest inventory is missing")
    safe_directories = [_safe_inventory_path(value) for value in directories]
    if safe_directories != sorted(set(safe_directories)):
        raise PackagingError("bundle manifest directories are not sorted/unique")

    safe_files = []
    seen_files = set()
    for record in files:
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "size"}:
            raise PackagingError("bundle manifest has malformed file record")
        relative = _safe_inventory_path(record["path"])
        digest = record["sha256"]
        size = record["size"]
        if (relative in seen_files or not isinstance(digest, str)
                or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest)
                or not isinstance(size, int) or isinstance(size, bool) or size < 0):
            raise PackagingError("bundle manifest has invalid file inventory")
        seen_files.add(relative)
        safe_files.append({"path": relative, "sha256": digest, "size": size})
    if [row["path"] for row in safe_files] != sorted(seen_files):
        raise PackagingError("bundle manifest files are not sorted")
    if seen_files & set(safe_directories):
        raise PackagingError("bundle inventory path is both file and directory")
    for relative in seen_files | set(safe_directories):
        parent = PurePosixPath(relative).parent
        while parent != PurePosixPath("."):
            if parent.as_posix() not in safe_directories:
                raise PackagingError(
                    f"bundle inventory omits parent directory {parent}")
            parent = parent.parent

    snapshot = {
        "directories": safe_directories,
        "files": safe_files,
        "file_count": len(safe_files),
        "directory_count": len(safe_directories),
        "total_bytes": sum(row["size"] for row in safe_files),
    }
    for field in ("file_count", "directory_count", "total_bytes"):
        if source.get(field) != snapshot[field]:
            raise PackagingError(f"bundle manifest {field} is inconsistent")
    canonical_inventory = json.dumps(
        {"directories": safe_directories, "files": safe_files},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    if source.get("canonical_tree_sha256") != hashlib.sha256(
            canonical_inventory).hexdigest():
        raise PackagingError("bundle canonical tree digest is invalid")

    file_map = {record["path"]: record for record in safe_files}
    evidence_hashes = {
        "PREFLIGHT.json": preflight["sha256"],
        launch_manifest["path"][len(SOURCE_ARC_ROOT) + 1:]:
            launch_manifest["sha256"],
        **{
            f"SUBMISSION_LOCK/{name}": record["sha256"]
            for name, record in lock.items()
        },
    }
    for relative, digest in evidence_hashes.items():
        if (relative not in file_map
                or file_map[relative]["sha256"] != digest):
            raise PackagingError(
                f"bundle provenance hash is not tied to inventory: {relative}")

    expected_scope = {
        "included": "every directory and regular file under the campaign root",
        "excluded": [
            f"src/slurm-egg-a6-holdout-{launch['job_id']}_<task>.out "
            "operational stdout files, which Slurm writes outside the "
            "canonical campaign root"
        ],
    }
    if manifest.get("scope") != expected_scope:
        raise PackagingError("bundle manifest scope is invalid")
    runtime = manifest.get("runtime") or {}
    if (set(runtime) != {"python", "zlib_build", "zlib_runtime"}
            or any(not isinstance(value, str) or not value
                   for value in runtime.values())):
        raise PackagingError("bundle manifest runtime is invalid")
    expected_archive = {
        "format": "tar.gz",
        "tar_format": "PAX",
        "gzip_mtime": 0,
        "normalized_uid_gid": 0,
        "normalized_file_mode": "0644",
        "normalized_directory_mode": "0755",
        "archive_sha256_location": "external ARCHIVE.sha256 sidecar",
        "byte_determinism": (
            "same source inventory, packaging commit, Python, and zlib runtime"
        ),
    }
    if manifest.get("archive") != expected_archive:
        raise PackagingError("bundle manifest archive contract is invalid")
    return snapshot


def _assert_regular_bundle_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise PackagingError(f"missing or non-regular {label}: {path}")
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise PackagingError(f"unsafe {label}: {path}")


def _regular_bundle_file(path: Path, label: str) -> bytes:
    _assert_regular_bundle_file(path, label)
    try:
        return path.read_bytes()
    except OSError as exc:
        raise PackagingError(f"cannot read {label}: {path}") from exc


def validate_destination_repository(repository: Path, manifest: dict) -> None:
    """Bind import to the intended Git repository and compatible code."""
    if repository.is_symlink() or not repository.is_dir():
        raise PackagingError(
            f"destination repository is missing or symlinked: {repository}")
    selection_rel = "result/a6_pilot/20260819T005514Z/SELECTION.json"
    try:
        top = subprocess.check_output(
            ["git", "-C", str(repository), "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.STDOUT).strip()
        subprocess.check_call(
            ["git", "-C", str(repository), "ls-files", "--error-unmatch",
             "--", selection_rel],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        committed_selection = subprocess.check_output(
            ["git", "-C", str(repository), "show", f"HEAD:{selection_rel}"],
            stderr=subprocess.STDOUT)
        subprocess.check_call(
            ["git", "-C", str(repository), "merge-base", "--is-ancestor",
             manifest["packaging_code_commit"], "HEAD"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as exc:
        raise PackagingError(
            "destination is not a compatible egg Git checkout") from exc
    if Path(top).resolve() != repository:
        raise PackagingError(
            f"destination is not the Git top level: {repository}")
    if hashlib.sha256(committed_selection).hexdigest() != EXPECTED_SELECTION_SHA256:
        raise PackagingError(
            "destination egg checkout has the wrong committed A6 selection")


def import_bundle(
    bundle_dir: str | os.PathLike,
    repo_root: str | os.PathLike,
    *,
    destination_validator=validate_destination_repository,
) -> dict:
    """Verify a downloaded bundle and atomically install only its raw root."""
    raw_bundle = Path(bundle_dir).expanduser()
    if raw_bundle.is_symlink():
        raise PackagingError(f"bundle directory must not be a symlink: {raw_bundle}")
    bundle = raw_bundle.resolve()
    if not bundle.is_dir():
        raise PackagingError(f"missing bundle directory: {bundle}")
    observed = {entry.name for entry in bundle.iterdir()}
    archives = sorted(bundle.glob("*.tar.gz"))
    if len(archives) != 1:
        raise PackagingError(
            f"bundle must contain exactly one tar.gz archive; found {len(archives)}")
    archive = archives[0]
    expected = {
        archive.name,
        "ARCHIVE.sha256",
        "BUNDLE_MANIFEST.json",
        "AUDIT_SUMMARY.md",
    }
    if observed != expected:
        raise PackagingError(
            f"bundle file population differs: got {sorted(observed)}, "
            f"expected {sorted(expected)}")

    archive_record = _stable_file_record(bundle, archive)
    manifest_bytes = _regular_bundle_file(
        bundle / "BUNDLE_MANIFEST.json", "bundle manifest")
    audit_bytes = _regular_bundle_file(
        bundle / "AUDIT_SUMMARY.md", "audit summary")
    sidecar_bytes = _regular_bundle_file(
        bundle / "ARCHIVE.sha256", "archive SHA-256 sidecar")
    try:
        manifest = json.loads(manifest_bytes)
    except json.JSONDecodeError as exc:
        raise PackagingError("bundle manifest is not valid JSON") from exc
    canonical_manifest = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    if manifest_bytes != canonical_manifest:
        raise PackagingError("bundle manifest is not canonical JSON")
    snapshot = _validated_manifest_snapshot(manifest, audit_bytes)

    expected_sidecar = (
        f"{archive_record['sha256']}  {archive.name}\n"
    ).encode()
    if sidecar_bytes != expected_sidecar:
        raise PackagingError("archive SHA-256 sidecar does not match")
    _verify_archive(archive, snapshot, manifest_bytes, audit_bytes)

    raw_repository = Path(repo_root).expanduser()
    if raw_repository.is_symlink():
        raise PackagingError(
            f"destination repository must not be a symlink: {raw_repository}")
    repository = raw_repository.resolve()
    destination_validator(repository, manifest)
    source_parent = repository / "src"
    if source_parent.is_symlink() or not source_parent.is_dir():
        raise PackagingError(f"missing destination src directory: {source_parent}")
    runs_parent = source_parent / "runs"
    if runs_parent.is_symlink():
        raise PackagingError(f"destination runs directory is symlinked: {runs_parent}")
    runs_parent.mkdir(exist_ok=True)
    target = runs_parent / "a6_holdout"
    if target.exists() or target.is_symlink():
        raise PackagingError(f"refusing existing import target: {target}")

    lock = runs_parent / ".a6_holdout.import-lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise PackagingError(
            f"another or interrupted A6 import holds {lock}") from exc
    staging: Path | None = None
    try:
        staging = Path(tempfile.mkdtemp(
            prefix=".a6_holdout.import-", dir=runs_parent))
        with tarfile.open(archive, "r:gz") as source_archive:
            by_name = {member.name: member for member in source_archive.getmembers()}
            for relative in snapshot["directories"]:
                (staging / relative).mkdir(mode=0o700)
            for record in snapshot["files"]:
                member_name = f"{SOURCE_ARC_ROOT}/{record['path']}"
                member = by_name[member_name]
                source_handle = source_archive.extractfile(member)
                if source_handle is None:
                    raise PackagingError(
                        f"cannot read source member during import: {member_name}")
                destination = staging / record["path"]
                digest = hashlib.sha256()
                size = 0
                with destination.open("xb") as target_handle:
                    for chunk in iter(lambda: source_handle.read(1 << 20), b""):
                        digest.update(chunk)
                        size += len(chunk)
                        target_handle.write(chunk)
                    target_handle.flush()
                    os.fsync(target_handle.fileno())
                if (size != record["size"]
                        or digest.hexdigest() != record["sha256"]):
                    raise PackagingError(
                        f"imported source member differs: {member_name}")
        if snapshot_source(staging) != snapshot:
            raise PackagingError("import staging inventory differs from manifest")
        for directory in sorted(
                [staging, *(path for path in staging.rglob("*") if path.is_dir())],
                key=lambda path: len(path.parts), reverse=True):
            _fsync_directory(directory)
        if _stable_file_record(bundle, archive) != archive_record:
            raise PackagingError("bundle archive changed during import")
        if target.exists() or target.is_symlink():
            raise PackagingError(f"refusing existing import target: {target}")
        os.rename(staging, target)
        staging = None
        _fsync_directory(runs_parent)
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)
        try:
            lock.rmdir()
        except FileNotFoundError:
            pass

    return {
        "target": str(target),
        "archive_sha256": archive_record["sha256"],
        "file_count": snapshot["file_count"],
        "total_bytes": snapshot["total_bytes"],
    }


def package_holdout(
    root: str | os.PathLike,
    out_base: str | os.PathLike,
    packaging_code_commit: str,
    *,
    selection_path: str | os.PathLike = DEFAULT_SELECTION,
    instances=HOLDOUT_INSTANCES,
    require_frozen_grid: bool = True,
    verify_selection_git: bool = True,
    code_verifier=verify_packaging_code_commit,
    selection_validator=None,
    preflight_validator=None,
    launch_validator=None,
    root_validator=None,
    scientific_validator=validate_scientific_population,
    audit_fn=None,
    job_quiescence_validator=assert_job_quiescent,
) -> dict:
    """Validate, package, and atomically publish one transfer bundle."""
    if (selection_validator is None or preflight_validator is None
            or launch_validator is None or root_validator is None
            or audit_fn is None):
        from experiments.analyze_a6_holdout import (
            validate_holdout_root,
            validate_launch_provenance,
            validate_preflight,
            validate_selection,
        )
        from experiments.audit_runs import audit

        selection_validator = selection_validator or validate_selection
        preflight_validator = preflight_validator or validate_preflight
        launch_validator = launch_validator or validate_launch_provenance
        root_validator = root_validator or validate_holdout_root
        audit_fn = audit_fn or audit
    if require_frozen_grid:
        assert_frozen_grid(instances)
    packaging_commit = code_verifier(packaging_code_commit)

    raw_root = Path(root).expanduser()
    if raw_root.is_symlink():
        raise PackagingError(f"source root must not be a symlink: {raw_root}")
    root_path = raw_root.resolve()
    out_path = Path(out_base).expanduser().resolve()
    if _path_is_within(out_path, root_path):
        raise PackagingError("package output directory must be outside source root")

    # Launch-only gates run before any checkpoint or outcome file is copied.
    selection = selection_validator(
        selection_path, verify_git=verify_selection_git)
    preflight_path = root_path / "PREFLIGHT.json"
    live_preflight = preflight_validator(preflight_path, instances=instances)
    live_launch = launch_validator(
        root_path, live_preflight, selection, instances=instances)
    job_quiescence_validator(live_launch["job_id"])

    bundle_name = (
        f"a6_holdout-job{live_launch['job_id']}-"
        f"{live_preflight['sha256'][:12]}-pkg{packaging_commit[:12]}"
    )
    final_dir = out_path / bundle_name
    if final_dir.exists() or final_dir.is_symlink():
        raise PackagingError(f"refusing existing package path: {final_dir}")

    out_path.mkdir(parents=True, exist_ok=True)
    staging: Path | None = Path(tempfile.mkdtemp(
        prefix=f".{bundle_name}.staging-", dir=out_path))
    archive_name = f"{bundle_name}.tar.gz"
    try:
        frozen_root = staging / ".frozen-a6-holdout"
        snapshot = freeze_source(root_path, frozen_root)

        # Every scientific and provenance check below reads the frozen bytes
        # that will be archived, never the live campaign directory.
        preflight = preflight_validator(
            frozen_root / "PREFLIGHT.json", instances=instances)
        launch = launch_validator(
            frozen_root, preflight, selection, instances=instances)
        if (preflight["sha256"] != live_preflight["sha256"]
                or launch["job_id"] != live_launch["job_id"]):
            raise PackagingError("frozen launch evidence differs from live gate")
        paths = root_validator(
            str(frozen_root), instances=instances, preflight=preflight)
        scientific = scientific_validator(
            paths, preflight, selection, packaging_commit,
            instances=instances)

        audit_lines, audit_ok, audit_problems = audit_fn(
            str(frozen_root), out_path=os.devnull,
            expect_cg=2 * len(instances),
            expect_cg_method={method: len(instances) for method in METHODS},
            expect_cg_certified_method=None,
        )
        if not audit_ok:
            raise PackagingError(
                "holdout AUDIT FAILED; no package created: "
                + "; ".join(audit_problems))
        if (2 * len(instances) != AUDIT_EXPECT_CG
                or {method: len(instances) for method in METHODS}
                != AUDIT_EXPECT_METHOD):
            raise PackagingError("production package audit denominator drifted")

        audit_bytes = _canonical_audit_summary(audit_lines)
        manifest = _manifest_document(
            packaging_commit=packaging_commit,
            selection=selection,
            preflight=preflight,
            launch=launch,
            scientific=scientific,
            snapshot=snapshot,
            audit_bytes=audit_bytes,
        )
        manifest_bytes = (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode()
        archive_path = staging / archive_name
        _write_archive(
            archive_path, frozen_root, snapshot, manifest_bytes, audit_bytes)
        _verify_archive(
            archive_path, snapshot, manifest_bytes, audit_bytes)
        if (snapshot_source(frozen_root) != snapshot
                or snapshot_source(root_path) != snapshot):
            raise PackagingError(
                "source tree changed while the archive was being written")
        job_quiescence_validator(launch["job_id"])

        archive_sha = sha256_file(str(archive_path))
        _write_bytes(staging / "BUNDLE_MANIFEST.json", manifest_bytes)
        _write_bytes(staging / "AUDIT_SUMMARY.md", audit_bytes)
        _write_bytes(
            staging / "ARCHIVE.sha256",
            f"{archive_sha}  {archive_name}\n".encode(),
        )
        shutil.rmtree(frozen_root)
        _fsync_directory(staging)
        os.replace(staging, final_dir)
        staging = None
        _fsync_directory(out_path)
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)

    return {
        "bundle_dir": str(final_dir),
        "archive": str(final_dir / archive_name),
        "sidecar": str(final_dir / "ARCHIVE.sha256"),
        "manifest": str(final_dir / "BUNDLE_MANIFEST.json"),
        "audit_summary": str(final_dir / "AUDIT_SUMMARY.md"),
        "archive_sha256": archive_sha,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    pack_parser = commands.add_parser("pack")
    pack_parser.add_argument("--root", default="runs/a6_holdout")
    pack_parser.add_argument("--out", default=DEFAULT_OUT)
    pack_parser.add_argument("--selection", default=str(DEFAULT_SELECTION))
    pack_parser.add_argument("--packaging-code-commit", required=True)
    import_parser = commands.add_parser("import")
    import_parser.add_argument("--bundle-dir", required=True)
    import_parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    if args.command == "pack":
        result = package_holdout(
            args.root,
            args.out,
            args.packaging_code_commit,
            selection_path=args.selection,
        )
        print(f"[done] wrote {result['bundle_dir']}")
        print(f"archive: {result['archive']}")
        print(f"sidecar: {result['sidecar']}")
        print(f"sha256:  {result['archive_sha256']}")
    else:
        result = import_bundle(args.bundle_dir, args.repo_root)
        print(f"[done] imported {result['target']}")
        print(f"files:   {result['file_count']}")
        print(f"sha256:  {result['archive_sha256']}")


if __name__ == "__main__":
    main()
