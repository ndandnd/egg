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
import ctypes
import datetime
import errno
import gzip
import hashlib
import io
import json
import os
import platform
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import zlib
from pathlib import Path, PurePosixPath

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCHEMA = "a6-holdout-transfer-bundle-v2"
# The recovery contract is a SEPARATE, versioned manifest/receipt schema so a
# recovery bundle can never be confused with a normal one (EI-026 Task B).
SCHEMA_RECOVERY = "a6-holdout-transfer-bundle-v3-recovery"
RECEIPT_SCHEMA = "a6-holdout-transfer-receipt-v1"
RECEIPT_SCHEMA_RECOVERY = "a6-holdout-transfer-receipt-v2-recovery"
RECEIPT_FILENAME = "a6_holdout.TRANSFER_RECEIPT.json"
CLOSEOUT_CLAIM_SCHEMA = "a6-holdout-closeout-claim-v1"
CLOSEOUT_CLAIM_FILENAME = "a6_holdout.CLOSEOUT_CLAIM.json"
RECOVERY_CLAIM_SCHEMA = "a6-holdout-recovery-claim-v1"
RECOVERY_CLAIM_FILENAME = "a6_holdout.RECOVERY_CLAIM.json"
RECOVERY_INCIDENT_ID = "EI-026"
# The one packaging/claim commit the original (failed) claim was made at; the
# recovery HEAD must have this as an ancestor.
RECOVERY_BASE_COMMIT = "740ab0c1578b454268102c0bb15b1104d9ac8d9d"
# Frozen EI-026 identities (operator evidence).  A merely well-formed
# operator-supplied SHA is insufficient: the recovery gate requires these exact
# values (tests inject their own synthetic expectations via parameters).
RECOVERY_ORIGINAL_CLAIM_SHA256 = (
    "1b0acf0b8232d4b08e764564e2732fcfa9c28dd53456a1415085b77cb38f6675")
RECOVERY_ORIGINAL_PACKAGING_COMMIT = (
    "740ab0c1578b454268102c0bb15b1104d9ac8d9d")
RECOVERY_ORIGINAL_SOURCE_TREE_SHA256 = (
    "2c60b3d2feb1f313cb08541556d5e8f95bf40dc76b2c539d78149dd93ad88749")
SOURCE_ARC_ROOT = "src/runs/a6_holdout"
# The repository root; every recovery Git command is pinned here, never the
# caller's cwd (EI-026 Task B.5).
REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METADATA_ARC_ROOT = "A6_HOLDOUT_TRANSFER"
DEFAULT_OUT = "runs/a6_holdout_packages"
AUDIT_EXPECT_CG = 128
AUDIT_EXPECT_METHOD = {"a2": 64, "a6_a4": 64}
METHODS = ("a2", "a6_a4")
SCIENTIFIC_CHECKS = (
    "terminal scoreability from independently replayed CG evidence",
    "oracle, iteration, retained-column, and key lineage reconstruction",
    "clean-bound, gap, first-certificate, and terminal trace derivation",
    "independent schedule replay and physical-load reconstruction",
    "schedule, load, column-key, deadhead, and operating-cost recomputation",
    "pricing raw, model, physical, and adjustment objective recomputation",
    "dictator raw, physical, adaptive-bound, and uplift recomputation",
    "frozen Slurm task-index and per-cell job-lineage coherence",
    "oracle and wall partition coherence",
    "broadcast price-path coherence",
    "population scientific identity",
    "selection-run-packaging Git ancestry",
)
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


class IncompletePublicationError(PackagingError):
    """A no-replace publication could not be completed or rolled back.

    Carries explicit commit-state metadata so wrappers clean up the
    correct path and never mask the original failure:

    - ``renamed``: the staging tree was atomically renamed to the
      destination; evidence lives there (under the incomplete marker),
      not at the staging path.
    - ``destination``: the destination path the publication targeted.
    - ``committed``: the publication reached the committed (markerless)
      state; the destination contents are valid.
    """

    def __init__(self, message: str, *, renamed: bool = False,
                 destination: str | None = None,
                 committed: bool = False) -> None:
        super().__init__(message)
        self.renamed = renamed
        self.destination = destination
        self.committed = committed


def sha256_file(path: str | os.PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_packaging_code_commit(claimed: str) -> str:
    """Bind packaging output to clean tracked code at the claimed HEAD."""
    if (not isinstance(claimed, str)
            or re.fullmatch(r"[0-9a-f]{7,40}", claimed) is None):
        raise PackagingError(
            "--packaging-code-commit must be 7-40 lowercase hexadecimal "
            "characters")
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{claimed}^{{commit}}"],
            cwd=REPO_ROOT, text=True,
            stderr=subprocess.STDOUT).strip()
        head = subprocess.check_output(
            ["git", "rev-parse", "--verify", "HEAD^{commit}"],
            cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        raise PackagingError("cannot resolve packaging Git provenance") from exc
    if resolved != head:
        raise PackagingError(
            f"packaging code commit mismatch: HEAD {head[:12]} vs {claimed}")
    try:
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        raise PackagingError(
            "cannot verify packaging tree cleanliness") from exc
    if dirty:
        raise PackagingError(
            "packaging tree has uncommitted tracked changes:\n" + dirty)
    return resolved


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


def canonical_tree_sha256(snapshot: dict) -> str:
    """Hash the canonical inventory portion shared by bundle and receipt."""
    payload = json.dumps(
        {
            "directories": snapshot["directories"],
            "files": snapshot["files"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


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


def _regular_signature(info: os.stat_result) -> tuple[int, int, int, int]:
    """Ownership signature for regular files: (dev, ino, size, mtime_ns).

    (dev, ino) alone is defeated by inode recycling: an unlink immediately
    followed by a re-create can legitimately receive the SAME inode number
    (observed on tmpfs), making a foreign replacement indistinguishable and
    letting rollback destroy competitor content (EI-022). Size and mtime_ns
    change on any rewrite, closing that hole for cooperative processes.
    Hard-linking/unlinking OTHER names of the inode changes neither, so the
    receipt link dance stays valid. A malicious same-UID process could
    restore mtime via utimensat — that adversary is outside the documented
    trust boundary (see the module publication notes)."""
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def _regular_signature_error(info: os.stat_result,
                             signature: tuple) -> bool:
    return (not stat.S_ISREG(info.st_mode)
            or _regular_signature(info) != tuple(signature))


def _owned_regular_error(
    path: Path,
    signature: tuple,
    *,
    allowed_nlinks: set[int],
) -> str | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return f"owned path is missing: {path}"
    if (_regular_signature_error(info, signature)
            or info.st_nlink not in allowed_nlinks):
        return (
            f"owned regular path was replaced, rewritten, or relinked: "
            f"{path} (nlink={info.st_nlink})")
    return None


def _owned_directory_error(
    path: Path,
    signature: tuple[int, int],
) -> str | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return f"owned directory is missing: {path}"
    if (not stat.S_ISDIR(info.st_mode)
            or (info.st_dev, info.st_ino) != signature):
        return f"owned directory was replaced: {path}"
    return None


def _open_directory_nofollow(
    path: str | os.PathLike,
    *,
    dir_fd: int | None = None,
) -> int:
    """Open one directory entry without following its final component."""
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise PackagingError(
            "directory-fd no-follow support is required for publication")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    return os.open(path, flags, dir_fd=dir_fd)


def _owned_regular_error_at(
    directory_fd: int,
    name: str,
    signature: tuple,
    *,
    allowed_nlinks: set[int],
    display: Path,
) -> str | None:
    try:
        info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return f"owned path is missing: {display}"
    if (_regular_signature_error(info, signature)
            or info.st_nlink not in allowed_nlinks):
        return (
            f"owned regular path was replaced, rewritten, or relinked: "
            f"{display} (nlink={info.st_nlink})")
    return None


def _owned_directory_entry_error_at(
    directory_fd: int,
    name: str,
    signature: tuple[int, int],
    *,
    display: Path,
) -> str | None:
    try:
        info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return f"owned directory is missing: {display}"
    if (not stat.S_ISDIR(info.st_mode)
            or (info.st_dev, info.st_ino) != signature):
        return f"owned directory was replaced: {display}"
    return None


def _owned_empty_directory_errors(
    path: Path,
    signature: tuple[int, int],
) -> list[str]:
    error = _owned_directory_error(path, signature)
    if error:
        return [error]
    try:
        observed = sorted(entry.name for entry in path.iterdir())
    except OSError as exc:
        return [f"cannot enumerate owned empty directory {path}: {exc}"]
    if observed:
        return [f"owned empty directory gained entries: {path}: {observed}"]
    return []


def _ensure_blocking_regular_path(
    path: Path,
    parent_fd: int,
) -> list[str]:
    """Best-effort fail-closed lock recreation without replacing a rival."""
    if path.exists() or path.is_symlink():
        return []
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path.name, flags, 0o600, dir_fd=parent_fd)
    except FileExistsError:
        return []
    except OSError as exc:
        return [f"cannot recreate blocking path {path}: {exc}"]
    try:
        os.write(descriptor, b"interrupted import\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        os.fsync(parent_fd)
    except OSError as exc:
        return [f"cannot durably recreate blocking path {path}: {exc}"]
    return []


def _rename_directory_no_replace(source: Path, target: Path) -> None:
    """Atomically publish one directory without adopting/replacing a rival."""
    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    target_bytes = os.fsencode(target)
    if sys.platform == "darwin":
        rename_exclusive = getattr(libc, "renamex_np", None)
        if rename_exclusive is None:
            raise PackagingError(
                "exclusive directory rename is unavailable on this platform")
        rename_exclusive.argtypes = [
            ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename_exclusive.restype = ctypes.c_int
        result = rename_exclusive(
            source_bytes, target_bytes, 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux"):
        rename_no_replace = getattr(libc, "renameat2", None)
        if rename_no_replace is None:
            raise PackagingError(
                "renameat2(RENAME_NOREPLACE) is unavailable")
        rename_no_replace.argtypes = [
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
            ctypes.c_uint]
        rename_no_replace.restype = ctypes.c_int
        result = rename_no_replace(
            -100, source_bytes, -100, target_bytes,
            0x00000001)  # AT_FDCWD, RENAME_NOREPLACE
    else:
        raise PackagingError(
            "exclusive directory rename is unsupported on this platform")
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number in (errno.EEXIST, errno.ENOTEMPTY):
        raise PackagingError(
            f"refusing existing publication path: {target}")
    raise OSError(error_number, os.strerror(error_number), str(target))


def _flat_publication_errors(
    target: Path,
    *,
    target_fd: int,
    target_signature: tuple[int, int],
    file_signatures: dict[str, tuple[int, int]],
    marker_signature: tuple[int, int],
    allowed_file_nlinks: set[int],
) -> list[str]:
    errors = []
    directory_error = _owned_directory_error(target, target_signature)
    if directory_error:
        return [directory_error]
    expected = set(file_signatures) | {".publication-incomplete"}
    try:
        observed = set(os.listdir(target_fd))
    except OSError as exc:
        return [f"cannot enumerate publication reservation: {exc}"]
    if observed != expected:
        errors.append(
            "publication reservation population differs: "
            f"missing={sorted(expected - observed)}, "
            f"extra={sorted(observed - expected)}")
    for name, signature in sorted(file_signatures.items()):
        error = _owned_regular_error_at(
            target_fd, name, signature,
            allowed_nlinks=allowed_file_nlinks,
            display=target / name)
        if error:
            errors.append(error)
    marker_error = _owned_regular_error_at(
        target_fd, ".publication-incomplete", marker_signature,
        allowed_nlinks={1}, display=target / ".publication-incomplete")
    if marker_error:
        errors.append(marker_error)
    return errors


def _rollback_flat_publication(
    target: Path,
    *,
    target_fd: int,
    target_signature: tuple[int, int],
    file_signatures: dict[str, tuple[int, int]],
    marker_signature: tuple[int, int] | None,
) -> list[str]:
    """Remove only a byte-for-byte owned reservation, never a competitor."""
    if marker_signature is None:
        directory_error = _owned_directory_error(target, target_signature)
        if directory_error:
            return [directory_error]
        try:
            observed = set(os.listdir(target_fd))
        except OSError as exc:
            return [f"cannot enumerate publication rollback: {exc}"]
        if observed:
            return [f"unowned publication entries appeared: {sorted(observed)}"]
    else:
        errors = _flat_publication_errors(
            target,
            target_fd=target_fd,
            target_signature=target_signature,
            file_signatures=file_signatures,
            marker_signature=marker_signature,
            allowed_file_nlinks={1, 2},
        )
        if errors:
            return errors

    errors = []
    for name, signature in sorted(
            file_signatures.items(), reverse=True):
        path = target / name
        error = _owned_regular_error_at(
            target_fd, name, signature, allowed_nlinks={1, 2},
            display=path)
        if error:
            errors.append(error)
            break
        try:
            os.unlink(name, dir_fd=target_fd)
        except OSError as exc:
            errors.append(f"owned publication unlink failed: {path}: {exc}")
            break
    if not errors and marker_signature is not None:
        marker = target / ".publication-incomplete"
        error = _owned_regular_error_at(
            target_fd, marker.name, marker_signature,
            allowed_nlinks={1}, display=marker)
        if error:
            errors.append(error)
        else:
            try:
                os.unlink(marker.name, dir_fd=target_fd)
            except OSError as exc:
                errors.append(f"owned marker unlink failed: {exc}")
    if not errors:
        directory_error = _owned_directory_error(target, target_signature)
        if directory_error:
            errors.append(directory_error)
        else:
            try:
                target.rmdir()
            except OSError as exc:
                errors.append(f"owned publication rmdir failed: {exc}")
    return errors


def publish_flat_directory_no_replace(
    staging: str | os.PathLike,
    destination: str | os.PathLike,
    *,
    expected_names: set[str],
    revalidate=None,
) -> None:
    """Publish a flat artifact directory without ever replacing a path.

    The fully prepared staging directory is atomically renamed with the native
    no-replace primitive.  An anchored sentinel remains until a post-rename
    ownership gate proves the exact directory reached the requested path.

    ``revalidate`` (optional, no arguments) runs AFTER the final ownership
    gate, and a SECOND ownership gate runs after it, immediately before
    the marker unlink — so nothing the callback observes or triggers can
    mutate the publication unnoticed.  Any exception preserves the renamed
    destination WITH the marker (IncompletePublicationError), never a
    markerless apparently-complete directory.

    Commit states are explicit and DISTINGUISH the two ways the guard can
    vanish: ``pre-rename`` (failure cleans the owned staging marker),
    ``renamed-guarded`` (renamed and still anchored by the marker; failure
    preserves the destination), ``commit-unlink-in-flight`` (set immediately
    before the publisher's own marker unlink), and ``committed`` (the marker
    is gone; the destination is valid).  Marker absence proves commit ONLY
    from ``commit-unlink-in-flight``: if the marker disappears while
    ``renamed-guarded`` (a callback removed the guard before commit) that is
    corruption, so a blocking marker is safely restored through the anchored
    fd and the incomplete/corrupt destination is preserved — never a
    markerless apparently-complete directory.  If the publisher's own unlink
    raises but the marker is verifiably absent, the publication is
    classified committed, and descriptor-close errors after commit never
    reclassify it.

    Trust boundary (honest OS limits): the native rename protects the
    DESTINATION atomically (renamex_np/RENAME_EXCL on macOS,
    renameat2/RENAME_NOREPLACE on Linux), but portable POSIX offers no
    rename-by-open-directory-fd for the SOURCE.  The randomized,
    caller-owned staging namespace is therefore treated as
    trusted/cooperative: a malicious same-UID process swapping the staging
    directory in the instant between the pre-rename ownership gate and the
    rename syscall is outside this function's guarantees (and mtime-based
    rewrite detection can likewise be defeated by a same-UID utimensat).
    Everything a cooperative-but-buggy environment can produce — stray
    files, crashed competitors, inode recycling, fsync failures — is
    detected or preserved fail-closed.
    """
    source = Path(staging)
    target = Path(destination)
    ownership = _capture_exact_tree_ownership(
        source, expected_directories=set(), expected_files=set(expected_names))
    source_fd = _open_directory_nofollow(source)
    source_info = os.fstat(source_fd)
    if ((source_info.st_dev, source_info.st_ino) != ownership["root"]
            or not stat.S_ISDIR(source_info.st_mode)):
        os.close(source_fd)
        raise PackagingError("publication staging ownership changed")
    signatures = {
        name: record["signature"]
        for name, record in ownership["files"].items()
    }
    marker_name = ".publication-incomplete"
    marker_signature: tuple[int, int] | None = None
    state = "pre-rename"

    def _marker_absent_through_fd() -> bool:
        """Inspect marker presence through the anchored directory fd."""
        try:
            os.stat(marker_name, dir_fd=source_fd, follow_symlinks=False)
        except FileNotFoundError:
            return True
        except OSError:
            return False
        return False

    def _restore_incomplete_marker() -> str | None:
        """Re-establish a blocking incomplete marker through the anchored
        directory fd after a callback removed it before commit.  Returns None
        on success or an error string if a competitor won the name or the
        restored marker cannot be proved owned.  Never overwrites or unlinks
        a competitor-created path."""
        try:
            fd = os.open(
                marker_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600, dir_fd=source_fd)
        except FileExistsError:
            return (f"incomplete-marker restoration lost a race; a foreign "
                    f"{marker_name!r} was preserved")
        except OSError as exc:
            return f"incomplete-marker restoration failed: {exc}"
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                os.close(fd)
                return "restored incomplete-marker is not an owned regular file"
            with os.fdopen(fd, "wb") as handle:
                handle.write(b"incomplete\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            try:
                os.close(fd)
            except OSError:
                pass
            return f"incomplete-marker restoration write failed: {exc}"
        try:
            os.fsync(source_fd)
        except OSError as exc:
            return f"incomplete-marker restoration dir fsync failed: {exc}"
        return None

    try:
        marker_fd = os.open(
            marker_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600,
            dir_fd=source_fd)
        marker_info = os.fstat(marker_fd)
        if (not stat.S_ISREG(marker_info.st_mode)
                or marker_info.st_nlink != 1):
            os.close(marker_fd)
            raise PackagingError(
                "publication incomplete-marker ownership is invalid")
        with os.fdopen(marker_fd, "wb") as handle:
            handle.write(b"incomplete\n")
            handle.flush()
            os.fsync(handle.fileno())
        # signature is captured AFTER the final write: (dev, ino, size,
        # mtime_ns) must describe the finished marker
        marker_signature = _regular_signature(os.stat(
            marker_name, dir_fd=source_fd, follow_symlinks=False))
        os.fchmod(source_fd, 0o755)
        os.fsync(source_fd)
        pre_errors = _flat_publication_errors(
            source,
            target_fd=source_fd,
            target_signature=ownership["root"],
            file_signatures=signatures,
            marker_signature=marker_signature,
            allowed_file_nlinks={1},
        )
        if pre_errors:
            raise PackagingError(
                "publication staging ownership changed before rename: "
                + "; ".join(pre_errors))
        _rename_directory_no_replace(source, target)
        state = "renamed-guarded"
        _fsync_directory(target.parent)

        # This is the completion boundary.  Every operation remains anchored
        # to the directory that was prepared, even if the destination name is
        # concurrently moved or replaced.
        final_errors = _flat_publication_errors(
            target,
            target_fd=source_fd,
            target_signature=ownership["root"],
            file_signatures=signatures,
            marker_signature=marker_signature,
            allowed_file_nlinks={1},
        )
        if final_errors:
            raise PackagingError(
                "publication ownership changed before commit: "
                + "; ".join(final_errors))
        # Caller-supplied final revalidation (e.g. the analyzer's raw-tree/
        # receipt/analysis-claim recheck) runs while the marker still
        # anchors the publication; its failure preserves marker + evidence.
        if revalidate is not None:
            revalidate()
            # anything mutated during (or by) the callback must be caught
            # while the marker still anchors the publication
            post_revalidate_errors = _flat_publication_errors(
                target,
                target_fd=source_fd,
                target_signature=ownership["root"],
                file_signatures=signatures,
                marker_signature=marker_signature,
                allowed_file_nlinks={1},
            )
            if post_revalidate_errors:
                raise PackagingError(
                    "publication ownership changed during final "
                    "revalidation: " + "; ".join(post_revalidate_errors))
        # The unlink syscall is the final logical commit.  All directory and
        # rename durability barriers have completed while the marker
        # existed; a crash may conservatively retain the marker, but no
        # fallible step after this point may reclassify a markerless
        # committed publication as incomplete.  Marker absence may prove
        # commit ONLY from this state — the publisher's own unlink is the
        # sole legitimate way the guard disappears.
        state = "commit-unlink-in-flight"
        try:
            os.unlink(marker_name, dir_fd=source_fd)
        except OSError:
            # the unlink may have removed the marker before failing;
            # a verifiably absent marker means the publication committed
            if _marker_absent_through_fd():
                state = "committed"
            else:
                raise
        else:
            state = "committed"
    except BaseException as exc:
        if state == "committed":
            raise
        if state == "commit-unlink-in-flight":
            # the publisher's OWN unlink was in flight: marker absence proves
            # the publication committed and the original error propagates
            # as-is; a still-present marker means it did not commit
            if _marker_absent_through_fd():
                raise
            raise IncompletePublicationError(
                "publication failed after exclusive rename; incomplete "
                "destination preserved",
                renamed=True, destination=str(target),
                committed=False) from exc
        if state == "renamed-guarded":
            # BEFORE the publisher's own commit unlink, marker absence is
            # never commit — it is corruption (a callback removed the guard).
            # Restore a blocking marker through the anchored fd and preserve
            # every artifact and foreign entry; never treat this as committed.
            if _marker_absent_through_fd():
                restore_error = _restore_incomplete_marker()
                if restore_error is not None:
                    raise IncompletePublicationError(
                        "publication guard marker was removed before commit "
                        "and could not be safely restored (" + restore_error
                        + "); incomplete/corrupt destination preserved",
                        renamed=True, destination=str(target),
                        committed=False) from exc
                raise IncompletePublicationError(
                    "publication guard marker was removed before commit; a "
                    "blocking incomplete marker was restored and the "
                    "incomplete destination preserved",
                    renamed=True, destination=str(target),
                    committed=False) from exc
            raise IncompletePublicationError(
                "publication failed after exclusive rename; incomplete "
                "destination preserved",
                renamed=True, destination=str(target),
                committed=False) from exc
        cleanup_errors = []
        if marker_signature is not None:
            path_error = _owned_directory_error(source, ownership["root"])
            marker_error = _owned_regular_error_at(
                source_fd, marker_name, marker_signature,
                allowed_nlinks={1}, display=source / marker_name)
            if path_error or marker_error:
                cleanup_errors.extend(
                    error for error in (path_error, marker_error) if error)
            else:
                try:
                    os.unlink(marker_name, dir_fd=source_fd)
                    os.fsync(source_fd)
                except OSError as cleanup_exc:
                    cleanup_errors.append(
                        f"owned publication marker cleanup failed: "
                        f"{cleanup_exc}")
        if cleanup_errors:
            raise IncompletePublicationError(
                "publication failed and staging cleanup was incomplete: "
                + "; ".join(cleanup_errors),
                renamed=False, destination=str(target),
                committed=False) from exc
        raise
    finally:
        try:
            os.close(source_fd)
        except OSError:
            # a descriptor-close failure has no data consequence (all
            # durability barriers completed while the marker existed) and
            # must never reclassify a committed publication as incomplete
            pass


def _owned_tree_population(root: Path) -> tuple[set[str], set[str], list[str]]:
    directories: set[str] = set()
    files: set[str] = set()
    errors: list[str] = []
    try:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            dirnames.sort()
            filenames.sort()
            parent = Path(dirpath)
            for name in dirnames:
                path = parent / name
                relative = path.relative_to(root).as_posix()
                try:
                    info = path.lstat()
                except OSError as exc:
                    errors.append(f"cannot stat tree directory {path}: {exc}")
                    continue
                if not stat.S_ISDIR(info.st_mode):
                    errors.append(f"tree directory was replaced: {path}")
                else:
                    directories.add(relative)
            for name in filenames:
                path = parent / name
                relative = path.relative_to(root).as_posix()
                try:
                    info = path.lstat()
                except OSError as exc:
                    errors.append(f"cannot stat tree file {path}: {exc}")
                    continue
                if not stat.S_ISREG(info.st_mode):
                    errors.append(f"tree file was replaced: {path}")
                else:
                    files.add(relative)
    except OSError as exc:
        errors.append(f"cannot enumerate owned tree {root}: {exc}")
    return directories, files, errors


def _owned_tree_errors(root: Path, ownership: dict) -> list[str]:
    errors = []
    root_error = _owned_directory_error(root, ownership["root"])
    if root_error:
        return [root_error]
    observed_dirs, observed_files, walk_errors = _owned_tree_population(root)
    errors.extend(walk_errors)
    expected_dirs = set(ownership["directories"])
    expected_files = set(ownership["files"])
    if observed_dirs != expected_dirs:
        errors.append(
            "owned tree directory population differs: "
            f"missing={sorted(expected_dirs - observed_dirs)}, "
            f"extra={sorted(observed_dirs - expected_dirs)}")
    if observed_files != expected_files:
        errors.append(
            "owned tree file population differs: "
            f"missing={sorted(expected_files - observed_files)}, "
            f"extra={sorted(observed_files - expected_files)}")
    for relative, signature in sorted(ownership["directories"].items()):
        error = _owned_directory_error(root / relative, signature)
        if error:
            errors.append(error)
    for relative, record in sorted(ownership["files"].items()):
        error = _owned_regular_error(
            root / relative, record["signature"],
            allowed_nlinks={record["nlink"]})
        if error:
            errors.append(error)
    return errors


def _open_owned_relative_directory(
    root_fd: int,
    relative: str,
    ownership: dict,
    *,
    root: Path,
) -> int:
    """Traverse only recorded directory inodes beneath an anchored root."""
    current_fd = os.dup(root_fd)
    prefix: list[str] = []
    try:
        parts = () if not relative else PurePosixPath(relative).parts
        for part in parts:
            prefix.append(part)
            key = PurePosixPath(*prefix).as_posix()
            expected = ownership["directories"].get(key)
            if expected is None:
                raise PackagingError(
                    f"directory ownership record is missing: {root / key}")
            next_fd = _open_directory_nofollow(part, dir_fd=current_fd)
            info = os.fstat(next_fd)
            if (not stat.S_ISDIR(info.st_mode)
                    or (info.st_dev, info.st_ino) != expected):
                os.close(next_fd)
                raise PackagingError(
                    f"owned directory was replaced: {root / key}")
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except BaseException:
        os.close(current_fd)
        raise


def _capture_exact_tree_ownership(
    root: Path,
    *,
    expected_directories: set[str],
    expected_files: set[str],
) -> dict:
    """Record one exact regular tree through no-follow directory handles."""
    root_fd = _open_directory_nofollow(root)
    try:
        root_info = os.fstat(root_fd)
        path_info = root.lstat()
        if (not stat.S_ISDIR(root_info.st_mode)
                or (path_info.st_dev, path_info.st_ino)
                != (root_info.st_dev, root_info.st_ino)):
            raise PackagingError(f"tree root ownership changed: {root}")
        observed_dirs, observed_files, walk_errors = _owned_tree_population(root)
        if (walk_errors or observed_dirs != expected_directories
                or observed_files != expected_files):
            raise PackagingError(
                "tree population differs while recording ownership: "
                f"errors={walk_errors}, "
                f"missing_dirs={sorted(expected_directories - observed_dirs)}, "
                f"extra_dirs={sorted(observed_dirs - expected_directories)}, "
                f"missing_files={sorted(expected_files - observed_files)}, "
                f"extra_files={sorted(observed_files - expected_files)}")
        ownership = {
            "root": (root_info.st_dev, root_info.st_ino),
            "directories": {},
            "files": {},
        }
        for relative in sorted(
                expected_directories,
                key=lambda value: len(PurePosixPath(value).parts)):
            relative_path = PurePosixPath(relative)
            parent_relative = (
                "" if relative_path.parent == PurePosixPath(".")
                else relative_path.parent.as_posix())
            parent_fd = _open_owned_relative_directory(
                root_fd, parent_relative, ownership, root=root)
            try:
                child_fd = _open_directory_nofollow(
                    relative_path.name, dir_fd=parent_fd)
                try:
                    info = os.fstat(child_fd)
                    ownership["directories"][relative] = (
                        info.st_dev, info.st_ino)
                finally:
                    os.close(child_fd)
            finally:
                os.close(parent_fd)
        for relative in sorted(expected_files):
            relative_path = PurePosixPath(relative)
            parent_relative = (
                "" if relative_path.parent == PurePosixPath(".")
                else relative_path.parent.as_posix())
            parent_fd = _open_owned_relative_directory(
                root_fd, parent_relative, ownership, root=root)
            try:
                info = os.stat(
                    relative_path.name, dir_fd=parent_fd,
                    follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise PackagingError(
                        f"unsafe owned tree file: {root / relative}")
                ownership["files"][relative] = {
                    "signature": _regular_signature(info),
                    "nlink": 1,
                }
            finally:
                os.close(parent_fd)
        errors = _owned_tree_errors(root, ownership)
        if errors:
            raise PackagingError(
                "tree ownership changed while being recorded: "
                + "; ".join(errors))
        return ownership
    finally:
        os.close(root_fd)


def _record_owned_regular_entry(
    root: Path,
    ownership: dict,
    relative: str,
) -> None:
    """Add one newly created regular file to an anchored tree record."""
    root_fd = _open_directory_nofollow(root)
    try:
        root_info = os.fstat(root_fd)
        if ((root_info.st_dev, root_info.st_ino) != ownership["root"]
                or not stat.S_ISDIR(root_info.st_mode)):
            raise PackagingError(f"owned tree root was replaced: {root}")
        relative_path = PurePosixPath(relative)
        parent_relative = (
            "" if relative_path.parent == PurePosixPath(".")
            else relative_path.parent.as_posix())
        parent_fd = _open_owned_relative_directory(
            root_fd, parent_relative, ownership, root=root)
        try:
            info = os.stat(
                relative_path.name, dir_fd=parent_fd,
                follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise PackagingError(
                    f"unsafe newly owned regular file: {root / relative}")
            ownership["files"][relative] = {
                "signature": _regular_signature(info),
                "nlink": 1,
            }
        finally:
            os.close(parent_fd)
        errors = _owned_tree_errors(root, ownership)
        if errors:
            raise PackagingError(
                "owned tree changed while recording new file: "
                + "; ".join(errors))
    finally:
        os.close(root_fd)


def _rollback_owned_tree(root: Path, ownership: dict) -> list[str]:
    """Conservatively remove an exact owned tree, bottom-up."""
    try:
        root_fd = _open_directory_nofollow(root)
    except OSError as exc:
        return [f"cannot open owned tree root without following: {root}: {exc}"]
    try:
        root_info = os.fstat(root_fd)
        if ((root_info.st_dev, root_info.st_ino) != ownership["root"]
                or not stat.S_ISDIR(root_info.st_mode)):
            return [f"owned directory was replaced: {root}"]
        root_error = _owned_directory_error(root, ownership["root"])
        if root_error:
            return [root_error]

        errors = _owned_tree_errors(root, ownership)
        if errors:
            return errors
        for relative, record in sorted(
                ownership["files"].items(), reverse=True):
            relative_path = PurePosixPath(relative)
            parent_relative = (
                "" if relative_path.parent == PurePosixPath(".")
                else relative_path.parent.as_posix())
            path = root / relative
            try:
                parent_fd = _open_owned_relative_directory(
                    root_fd, parent_relative, ownership, root=root)
            except (OSError, PackagingError) as exc:
                return [f"cannot open owned file parent {path.parent}: {exc}"]
            try:
                error = _owned_regular_error_at(
                    parent_fd, relative_path.name, record["signature"],
                    allowed_nlinks={record["nlink"]}, display=path)
                if error:
                    return [error]
                os.unlink(relative_path.name, dir_fd=parent_fd)
            except OSError as exc:
                return [f"owned import file unlink failed: {path}: {exc}"]
            finally:
                os.close(parent_fd)
        for relative, signature in sorted(
                ownership["directories"].items(),
                key=lambda item: len(PurePosixPath(item[0]).parts),
                reverse=True):
            relative_path = PurePosixPath(relative)
            parent_relative = (
                "" if relative_path.parent == PurePosixPath(".")
                else relative_path.parent.as_posix())
            path = root / relative
            try:
                parent_fd = _open_owned_relative_directory(
                    root_fd, parent_relative, ownership, root=root)
            except (OSError, PackagingError) as exc:
                return [f"cannot open owned directory parent {path.parent}: {exc}"]
            try:
                error = _owned_directory_entry_error_at(
                    parent_fd, relative_path.name, signature, display=path)
                if error:
                    return [error]
                os.rmdir(relative_path.name, dir_fd=parent_fd)
            except OSError as exc:
                return [f"owned import directory rmdir failed: {path}: {exc}"]
            finally:
                os.close(parent_fd)
        root_error = _owned_directory_error(root, ownership["root"])
        if root_error:
            return [root_error]
        try:
            root.rmdir()
        except OSError as exc:
            return [f"owned import root rmdir failed: {root}: {exc}"]
        return []
    finally:
        os.close(root_fd)


def install_tree_no_replace(
    staging: str | os.PathLike,
    destination: str | os.PathLike,
    snapshot: dict,
) -> dict:
    """Atomically install an inventoried tree without adopting a rival root."""
    source = Path(staging)
    target = Path(destination)
    ownership = _capture_exact_tree_ownership(
        source,
        expected_directories=set(snapshot["directories"]),
        expected_files={record["path"] for record in snapshot["files"]},
    )
    source_fd = _open_directory_nofollow(source)
    renamed = False
    try:
        source_info = os.fstat(source_fd)
        if ((source_info.st_dev, source_info.st_ino) != ownership["root"]
                or not stat.S_ISDIR(source_info.st_mode)):
            raise PackagingError("import staging ownership changed")
        for relative in sorted(
                ownership["directories"],
                key=lambda value: len(PurePosixPath(value).parts),
                reverse=True):
            directory_fd = _open_owned_relative_directory(
                source_fd, relative, ownership, root=source)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        os.fsync(source_fd)
        source_errors = _owned_tree_errors(source, ownership)
        if source_errors:
            raise PackagingError(
                "import staging changed before exclusive rename: "
                + "; ".join(source_errors))
        try:
            _rename_directory_no_replace(source, target)
        except PackagingError as exc:
            raise PackagingError(
                f"refusing existing import target: {target}") from exc
        renamed = True
        ownership_errors = _owned_tree_errors(target, ownership)
        if ownership_errors:
            raise IncompletePublicationError(
                "installed tree ownership changed after exclusive rename: "
                + "; ".join(ownership_errors),
                renamed=True, destination=str(target), committed=False)
        if snapshot_source(target) != snapshot:
            raise IncompletePublicationError(
                "installed source tree differs after exclusive rename",
                renamed=True, destination=str(target), committed=False)
        _fsync_directory(target.parent)
        return ownership
    except BaseException as exc:
        if renamed and not isinstance(exc, IncompletePublicationError):
            raise IncompletePublicationError(
                "import failed after exclusive rename; installed tree and "
                "import lock preserved",
                renamed=True, destination=str(target),
                committed=False) from exc
        raise
    finally:
        # closing the read-only staging descriptor has no data consequence:
        # on success the rename, snapshot validation, and parent fsync
        # durability barriers already completed, and on failure the outcome
        # (and its ownership attribution) is already decided.  A close-only
        # OSError must never mask an active exception or reclassify the
        # result — consistent with the publisher's source_fd contract.
        try:
            os.close(source_fd)
        except OSError:
            pass


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


def claim_closeout(
    root: str | os.PathLike,
    *,
    packaging_commit: str,
    preflight: dict,
    selection: dict,
    launch: dict,
    snapshot: dict,
) -> dict:
    """Persist the sole source-side closeout claim before outcome checks."""
    root_path = Path(root).resolve()
    claim_path = root_path.parent / CLOSEOUT_CLAIM_FILENAME
    document = {
        "schema": CLOSEOUT_CLAIM_SCHEMA,
        "campaign": "a6-holdout",
        "status": "claimed-before-outcome-validation",
        "claimed_utc": datetime.datetime.now(
            datetime.timezone.utc).replace(microsecond=0).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
        "packaging_code_commit": packaging_commit,
        "experiment_code_commit": preflight["code_commit"],
        "selection_sha256": selection["sha256"],
        "preflight_sha256": preflight["sha256"],
        "launch_job_id": launch["job_id"],
        "grid_list_sha256": launch["grid_list_sha256"],
        "source": {
            "canonical_tree_sha256": canonical_tree_sha256(snapshot),
            "file_count": snapshot["file_count"],
            "directory_count": snapshot["directory_count"],
            "total_bytes": snapshot["total_bytes"],
        },
    }
    payload = _canonical_json_bytes(document)
    try:
        descriptor = os.open(
            claim_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise PackagingError(
            f"A6 closeout was already claimed: {claim_path}") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_directory(root_path.parent)
    except BaseException:
        # Partial claims remain deliberate fail-closed recovery markers.
        raise
    return {
        "path": str(claim_path),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "document": document,
    }


def assert_closeout_claim_unchanged(record: dict) -> None:
    """Require the durable source-side claim to remain byte-identical."""
    if (not isinstance(record, dict)
            or set(record) != {"path", "sha256", "document"}
            or not isinstance(record.get("path"), str)
            or not _full_hex(record.get("sha256"), 64)
            or not isinstance(record.get("document"), dict)):
        raise PackagingError("closeout claim record is invalid")
    claim_path = Path(record["path"])
    raw = _regular_bundle_file(claim_path, "source closeout claim")
    expected = _canonical_json_bytes(record["document"])
    if (raw != expected
            or hashlib.sha256(raw).hexdigest() != record["sha256"]):
        raise PackagingError("source closeout claim changed during packaging")


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


# ===========================================================================
# EI-026 one-shot claimed-incident recovery (Task B)
# ===========================================================================
def _git_output(args: list[str]) -> str:
    # every recovery Git command is pinned to REPO_ROOT, never the caller's cwd
    result = subprocess.run(
        ["git", "-C", REPO_ROOT, *args], check=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        raise PackagingError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def _resolve_head_commit() -> str:
    head = _git_output(["rev-parse", "HEAD^{commit}"])
    if not _full_hex(head, 40):
        raise PackagingError(f"HEAD did not resolve to a commit: {head!r}")
    return head


def _require_clean_tracked_tree() -> None:
    if _git_output(["status", "--porcelain", "--untracked-files=no"]):
        raise PackagingError(
            "recovery requires a clean tracked tree; refusing with "
            "uncommitted tracked changes")


def _require_commit_ancestor(ancestor: str, descendant: str) -> None:
    result = subprocess.run(
        ["git", "-C", REPO_ROOT, "merge-base", "--is-ancestor",
         ancestor, descendant],
        check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 1:
        raise PackagingError(
            f"recovery HEAD {descendant} does not have {ancestor} as an "
            "ancestor")
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        raise PackagingError(f"cannot verify commit ancestry: {detail}")


def verify_original_claim(
    root,
    *,
    original_claim_sha256: str,
    expected_sha256: str = RECOVERY_ORIGINAL_CLAIM_SHA256,
    expected_packaging_commit: str = RECOVERY_ORIGINAL_PACKAGING_COMMIT,
    expected_source_tree_sha256: str = RECOVERY_ORIGINAL_SOURCE_TREE_SHA256,
) -> dict:
    """Open the original (failed) closeout claim adjacent to the raw root as
    canonical, regular, single-link IMMUTABLE evidence and verify it against the
    FROZEN EI-026 identities.

    A merely well-formed operator-supplied SHA is insufficient: the supplied SHA
    must equal the frozen expected SHA, the file must hash to it, the document
    must have the exact canonical key set, and its packaging commit and source
    digest must equal the frozen constants.  (Tests inject synthetic
    expectations via the ``expected_*`` parameters.)
    """
    if not _full_hex(original_claim_sha256, 64):
        raise PackagingError("original claim SHA-256 must be 64 lowercase hex")
    if original_claim_sha256 != expected_sha256:
        raise PackagingError(
            "original claim SHA-256 does not equal the frozen EI-026 claim "
            "SHA-256")
    root_path = Path(root).expanduser().resolve()
    claim_path = root_path.parent / CLOSEOUT_CLAIM_FILENAME
    raw = _regular_bundle_file(claim_path, "original closeout claim")
    info = claim_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise PackagingError(
            "original closeout claim is not a regular single-link file")
    if hashlib.sha256(raw).hexdigest() != original_claim_sha256:
        raise PackagingError(
            "original closeout claim SHA-256 does not match the supplied claim")
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PackagingError(
            "original closeout claim is not valid JSON") from exc
    if raw != _canonical_json_bytes(document):
        raise PackagingError("original closeout claim is not canonical JSON")
    # exact canonical key set
    if set(document) != {
            "schema", "campaign", "status", "claimed_utc",
            "packaging_code_commit", "experiment_code_commit",
            "selection_sha256", "preflight_sha256", "launch_job_id",
            "grid_list_sha256", "source"}:
        raise PackagingError("original closeout claim key set is invalid")
    if (document.get("schema") != CLOSEOUT_CLAIM_SCHEMA
            or document.get("campaign") != "a6-holdout"
            or document.get("status") != "claimed-before-outcome-validation"):
        raise PackagingError("original closeout claim schema/status is invalid")
    if document.get("packaging_code_commit") != expected_packaging_commit:
        raise PackagingError(
            "original closeout claim packaging commit does not equal the "
            "frozen EI-026 packaging commit")
    for key in ("experiment_code_commit", "launch_job_id", "grid_list_sha256",
                "selection_sha256", "preflight_sha256"):
        if not document.get(key):
            raise PackagingError(f"original closeout claim missing {key}")
    src = document.get("source") or {}
    if set(src) != {"canonical_tree_sha256", "file_count",
                    "directory_count", "total_bytes"}:
        raise PackagingError("original closeout claim source key set is invalid")
    if not (_full_hex(src.get("canonical_tree_sha256"), 64)
            and isinstance(src.get("file_count"), int)
            and not isinstance(src.get("file_count"), bool)
            and isinstance(src.get("directory_count"), int)
            and isinstance(src.get("total_bytes"), int)):
        raise PackagingError("original closeout claim source digest is invalid")
    if src.get("canonical_tree_sha256") != expected_source_tree_sha256:
        raise PackagingError(
            "original closeout claim source-tree SHA-256 does not equal the "
            "frozen EI-026 source-tree SHA-256")
    return {"path": str(claim_path), "sha256": original_claim_sha256,
            "document": document}


def claim_recovery(root, *, original_claim: dict, recovery_commit: str,
                   failure_fingerprint: str, raw_tree_sha256: str) -> dict:
    """Exclusively create the SECOND adjacent recovery claim before any outcome
    validation.  Exactly one recovery attempt is allowed: a pre-existing
    recovery claim blocks all further attempts (fail-closed one-shot)."""
    root_path = Path(root).expanduser().resolve()
    recovery_path = root_path.parent / RECOVERY_CLAIM_FILENAME
    doc = original_claim["document"]
    document = {
        "schema": RECOVERY_CLAIM_SCHEMA,
        "campaign": "a6-holdout",
        "incident_id": RECOVERY_INCIDENT_ID,
        "status": "recovery-claimed-before-outcome-validation",
        "claimed_utc": datetime.datetime.now(
            datetime.timezone.utc).replace(microsecond=0).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
        "recovery_code_commit": recovery_commit,
        "recovery_base_commit": RECOVERY_BASE_COMMIT,
        "original_claim": {
            "sha256": original_claim["sha256"],
            "packaging_code_commit": doc["packaging_code_commit"],
            "experiment_code_commit": doc["experiment_code_commit"],
            "launch_job_id": doc["launch_job_id"],
        },
        "raw_tree_sha256": raw_tree_sha256,
        "failure_fingerprint": failure_fingerprint,
    }
    payload = _canonical_json_bytes(document)
    try:
        descriptor = os.open(
            recovery_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise PackagingError(
            "A6 recovery was already claimed; a second recovery claim blocks "
            f"all further attempts: {recovery_path}") from exc
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_directory(root_path.parent)
    return {"path": str(recovery_path),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "document": document}


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
    from experiments.analyze_a6_holdout import EVIDENCE_LIMITATIONS

    return {
        "status": "PASS",
        "method_cells": len(cells),
        "experiment_code_commit": resolved,
        "checks": list(SCIENTIFIC_CHECKS),
        "decision_computed": False,
        "evidence_limitations": list(EVIDENCE_LIMITATIONS),
    }


def _manifest_document(
    *,
    packaging_commit: str,
    selection: dict,
    preflight: dict,
    launch: dict,
    closeout_claim: dict,
    scientific: dict,
    snapshot: dict,
    audit_bytes: bytes,
    recovery: dict | None = None,
) -> dict:
    launch_manifest = launch["manifest"]
    launch_lock = launch["lock"]
    document = {
        "schema": SCHEMA_RECOVERY if recovery is not None else SCHEMA,
        "campaign": "a6-holdout",
        "packaging_code_commit": packaging_commit,
        "experiment_code_commit": preflight["code_commit"],
        "closeout_claim": {
            "sha256": closeout_claim["sha256"],
            "document": closeout_claim["document"],
        },
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
            "canonical_tree_sha256": canonical_tree_sha256(snapshot),
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
                "same source inventory, exact closeout claim, packaging "
                "commit, Python, and zlib runtime"
            ),
        },
    }
    if recovery is not None:
        # the versioned recovery contract records the ORIGINAL claim
        # commit+SHA, the recovery claim commit+SHA, the experiment commit, and
        # the actual corrected packaging/analysis commit (EI-026 Task B.9).
        document["recovery"] = recovery
    return document


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
        "scientific_validation", "selection", "source", "closeout_claim",
    }
    is_recovery = manifest.get("schema") == SCHEMA_RECOVERY
    if is_recovery:
        expected_top = expected_top | {"recovery"}
    if set(manifest) != expected_top:
        raise PackagingError("bundle manifest top-level keys differ")
    if (manifest.get("schema") not in (SCHEMA, SCHEMA_RECOVERY)
            or manifest.get("campaign") != "a6-holdout"):
        raise PackagingError("bundle manifest has wrong schema/campaign")
    if is_recovery:
        recovery = manifest.get("recovery")
        original = (recovery or {}).get("original_claim") or {}
        recovery_claim = (recovery or {}).get("recovery_claim") or {}
        rc_doc = recovery_claim.get("document")
        if (not isinstance(recovery, dict)
                or recovery.get("incident_id") != RECOVERY_INCIDENT_ID
                or not _full_hex(recovery.get("recovery_code_commit"), 40)
                or recovery.get("recovery_base_commit") != RECOVERY_BASE_COMMIT
                or not _full_hex(original.get("sha256"), 64)
                or not _full_hex(original.get("packaging_code_commit"), 40)
                or not _full_hex(recovery_claim.get("sha256"), 64)
                or not isinstance(rc_doc, dict)
                or hashlib.sha256(_canonical_json_bytes(rc_doc)).hexdigest()
                != recovery_claim.get("sha256")
                or rc_doc.get("incident_id") != RECOVERY_INCIDENT_ID
                or rc_doc.get("recovery_code_commit")
                != recovery.get("recovery_code_commit")
                or (rc_doc.get("original_claim") or {}).get("sha256")
                != original.get("sha256")
                or not _full_hex(recovery.get("experiment_code_commit"), 40)):
            raise PackagingError("bundle manifest recovery block is invalid")
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

    from experiments.analyze_a6_holdout import EVIDENCE_LIMITATIONS

    scientific = manifest.get("scientific_validation") or {}
    if (set(scientific) != {
            "status", "method_cells", "experiment_code_commit", "checks",
            "decision_computed", "evidence_limitations"}
            or scientific.get("status") != "PASS"
            or scientific.get("method_cells") != 128
            or scientific.get("experiment_code_commit") != experiment_commit
            or scientific.get("decision_computed") is not False
            or scientific.get("checks") != list(SCIENTIFIC_CHECKS)
            or scientific.get("evidence_limitations")
            != list(EVIDENCE_LIMITATIONS)):
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

    closeout_claim = manifest.get("closeout_claim") or {}
    if (set(closeout_claim) != {"sha256", "document"}
            or not _full_hex(closeout_claim.get("sha256"), 64)
            or not isinstance(closeout_claim.get("document"), dict)
            or closeout_claim["sha256"] != hashlib.sha256(
                _canonical_json_bytes(closeout_claim["document"])).hexdigest()):
        raise PackagingError("bundle closeout claim envelope is invalid")
    claim_doc = closeout_claim["document"]
    if (set(claim_doc) != {
            "schema", "campaign", "status", "claimed_utc",
            "packaging_code_commit", "experiment_code_commit",
            "selection_sha256", "preflight_sha256", "launch_job_id",
            "grid_list_sha256", "source"}
            or claim_doc.get("schema") != CLOSEOUT_CLAIM_SCHEMA
            or claim_doc.get("campaign") != "a6-holdout"
            or claim_doc.get("status")
            != "claimed-before-outcome-validation"
            or claim_doc.get("packaging_code_commit") != (
                manifest["recovery"]["original_claim"]["packaging_code_commit"]
                if is_recovery else packaging_commit)
            or claim_doc.get("experiment_code_commit") != experiment_commit
            or claim_doc.get("selection_sha256") != EXPECTED_SELECTION_SHA256
            or claim_doc.get("preflight_sha256") != preflight["sha256"]
            or claim_doc.get("launch_job_id") != launch["job_id"]
            or claim_doc.get("grid_list_sha256")
            != launch["grid_list_sha256"]):
        raise PackagingError("bundle closeout claim identity is invalid")
    claim_time = _manifest_timestamp(
        claim_doc.get("claimed_utc"), "closeout claim claimed_utc")
    if claim_time < launch_times[-1]:
        raise PackagingError("bundle closeout claim predates launch records")
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
    if source.get("canonical_tree_sha256") != canonical_tree_sha256(snapshot):
        raise PackagingError("bundle canonical tree digest is invalid")
    expected_claim_source = {
        "canonical_tree_sha256": source["canonical_tree_sha256"],
        "file_count": snapshot["file_count"],
        "directory_count": snapshot["directory_count"],
        "total_bytes": snapshot["total_bytes"],
    }
    if claim_doc.get("source") != expected_claim_source:
        raise PackagingError("bundle closeout claim source tree is invalid")

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
            "same source inventory, exact closeout claim, packaging commit, "
            "Python, and zlib runtime"
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
        head = subprocess.check_output(
            ["git", "-C", str(repository), "rev-parse", "--verify",
             "HEAD^{commit}"],
            text=True, stderr=subprocess.STDOUT).strip()
        subprocess.check_call(
            ["git", "-C", str(repository), "ls-files", "--error-unmatch",
             "--", selection_rel],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        committed_selection = subprocess.check_output(
            ["git", "-C", str(repository), "show", f"HEAD:{selection_rel}"],
            stderr=subprocess.STDOUT)
        selection_commit = subprocess.check_output(
            ["git", "-C", str(repository), "log", "-1", "--format=%H",
             "--", selection_rel],
            text=True, stderr=subprocess.STDOUT).strip()
        subprocess.check_call(
            ["git", "-C", str(repository), "merge-base", "--is-ancestor",
             EXPECTED_SELECTION_COMMIT, manifest["experiment_code_commit"]],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call(
            ["git", "-C", str(repository), "merge-base", "--is-ancestor",
             manifest["packaging_code_commit"], "HEAD"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call(
            ["git", "-C", str(repository), "merge-base", "--is-ancestor",
             manifest["experiment_code_commit"],
             manifest["packaging_code_commit"]],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as exc:
        raise PackagingError(
            "destination is not a compatible egg Git checkout") from exc
    if Path(top).resolve() != repository:
        raise PackagingError(
            f"destination is not the Git top level: {repository}")
    if head != manifest["packaging_code_commit"]:
        raise PackagingError(
            "destination HEAD must exactly equal bundle packaging commit")
    if hashlib.sha256(committed_selection).hexdigest() != EXPECTED_SELECTION_SHA256:
        raise PackagingError(
            "destination egg checkout has the wrong committed A6 selection")
    if selection_commit != EXPECTED_SELECTION_COMMIT:
        raise PackagingError(
            "destination egg checkout has the wrong selection artifact commit")


def _canonical_json_bytes(document: dict) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()


def _receipt_document(
    *,
    repository: Path,
    target: Path,
    bundle: Path,
    archive: Path,
    archive_record: dict,
    manifest: dict,
    manifest_bytes: bytes,
    audit_bytes: bytes,
    snapshot: dict,
    imported_utc: str,
) -> dict:
    recovery = manifest.get("recovery")
    document = {
        "schema": (RECEIPT_SCHEMA_RECOVERY if recovery is not None
                   else RECEIPT_SCHEMA),
        "campaign": "a6-holdout",
        "imported_utc": imported_utc,
        "destination": {
            "repository": str(repository),
            "target": str(target),
            "repository_relative_target": SOURCE_ARC_ROOT,
        },
        "bundle": {
            "path": str(bundle),
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "audit_summary_sha256": hashlib.sha256(audit_bytes).hexdigest(),
        },
        "archive": {
            "name": archive.name,
            "sha256": archive_record["sha256"],
            "size": archive_record["size"],
        },
        "source": {
            "canonical_tree_sha256": canonical_tree_sha256(snapshot),
            "file_count": snapshot["file_count"],
            "directory_count": snapshot["directory_count"],
            "total_bytes": snapshot["total_bytes"],
        },
        "closeout_claim": manifest["closeout_claim"],
        "provenance": {
            "experiment_code_commit": manifest["experiment_code_commit"],
            "packaging_code_commit": manifest["packaging_code_commit"],
            "selection_sha256": manifest["selection"]["sha256"],
            "selection_artifact_commit":
                manifest["selection"]["artifact_commit"],
            "preflight_sha256": manifest["preflight"]["sha256"],
            "launch_job_id": manifest["launch"]["job_id"],
        },
    }
    if recovery is not None:
        # the receipt records the full versioned recovery contract: original
        # claim commit+SHA, recovery claim commit+SHA, experiment commit, and
        # the corrected packaging/analysis (recovery) commit.
        document["recovery"] = recovery
    return document


def validate_transfer_receipt(
    path: str | os.PathLike,
    *,
    expected: dict | None = None,
) -> dict:
    """Validate canonical receipt bytes and, when supplied, exact content."""
    receipt_path = Path(path)
    raw = _regular_bundle_file(receipt_path, "transfer receipt")
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PackagingError("transfer receipt is not valid JSON") from exc
    if raw != _canonical_json_bytes(document):
        raise PackagingError("transfer receipt is not canonical JSON")
    base_keys = {
        "schema", "campaign", "imported_utc", "destination", "bundle",
        "archive", "source", "provenance", "closeout_claim"}
    is_recovery = document.get("schema") == RECEIPT_SCHEMA_RECOVERY
    expected_keys = base_keys | {"recovery"} if is_recovery else base_keys
    if set(document) != expected_keys:
        raise PackagingError("transfer receipt top-level keys differ")
    if (document.get("schema") not in (RECEIPT_SCHEMA, RECEIPT_SCHEMA_RECOVERY)
            or document.get("campaign") != "a6-holdout"):
        raise PackagingError("transfer receipt schema/campaign is invalid")
    if is_recovery:
        recovery = document.get("recovery") or {}
        if (recovery.get("incident_id") != RECOVERY_INCIDENT_ID
                or not _full_hex(recovery.get("recovery_code_commit"), 40)):
            raise PackagingError("transfer receipt recovery block is invalid")
    _manifest_timestamp(document.get("imported_utc"), "imported_utc")
    if expected is not None:
        comparable = dict(document)
        comparable.pop("imported_utc")
        expected_comparable = dict(expected)
        expected_comparable.pop("imported_utc")
        if comparable != expected_comparable:
            raise PackagingError("transfer receipt content differs")
    return document


def import_bundle(
    bundle_dir: str | os.PathLike,
    repo_root: str | os.PathLike,
    *,
    destination_validator=validate_destination_repository,
    recovery_head_resolver=_resolve_head_commit,
    recovery_ancestor_checker=_require_commit_ancestor,
) -> dict:
    """Verify a bundle and transactionally install raw root plus receipt."""
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

    # EI-026 recovery bundles bind the destination-side HEAD to the recovery
    # commit and verify BOTH immutable claims recorded in the manifest.
    if manifest.get("schema") == SCHEMA_RECOVERY:
        recovery = manifest.get("recovery") or {}
        head = recovery_head_resolver()
        recovery_commit = recovery.get("recovery_code_commit")
        if head != recovery_commit:
            raise PackagingError(
                "recovery import requires HEAD to equal the recovery commit "
                f"{recovery_commit!r}; HEAD is {head!r}")
        # B6. prove 740ab0c -> recovery commit.
        recovery_ancestor_checker(RECOVERY_BASE_COMMIT, recovery_commit)
        original = recovery.get("original_claim") or {}
        embedded_claim = manifest.get("closeout_claim") or {}
        rc_doc = (recovery.get("recovery_claim") or {}).get("document") or {}
        # B6. cross-bind every manifest/claim/source/experiment/packaging
        # identity: the embedded original claim, the recovery claim document,
        # and the manifest commits must all agree.
        if embedded_claim.get("sha256") != original.get("sha256"):
            raise PackagingError(
                "recovery manifest original-claim SHA does not match the "
                "embedded closeout claim")
        claim_doc = embedded_claim.get("document") or {}
        if (claim_doc.get("packaging_code_commit")
                != original.get("packaging_code_commit")):
            raise PackagingError(
                "recovery manifest original packaging commit is inconsistent")
        if (rc_doc.get("recovery_code_commit") != recovery_commit
                or (rc_doc.get("original_claim") or {}).get("sha256")
                != original.get("sha256")
                or (rc_doc.get("original_claim") or {}).get(
                    "experiment_code_commit")
                != recovery.get("experiment_code_commit")):
            raise PackagingError(
                "recovery manifest recovery-claim identities are inconsistent")
        if (manifest.get("packaging_code_commit") != recovery_commit
                or manifest.get("experiment_code_commit")
                != recovery.get("experiment_code_commit")):
            raise PackagingError(
                "recovery manifest commit identities are inconsistent")

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
    receipt_path = runs_parent / RECEIPT_FILENAME
    if target.exists() or target.is_symlink():
        raise PackagingError(f"refusing existing import target: {target}")
    if receipt_path.exists() or receipt_path.is_symlink():
        raise PackagingError(
            f"refusing existing transfer receipt: {receipt_path}")

    lock = runs_parent / ".a6_holdout.import-lock"
    runs_parent_fd = _open_directory_nofollow(runs_parent)
    runs_parent_info = os.fstat(runs_parent_fd)
    runs_parent_path_info = runs_parent.lstat()
    if ((runs_parent_info.st_dev, runs_parent_info.st_ino)
            != (runs_parent_path_info.st_dev, runs_parent_path_info.st_ino)):
        os.close(runs_parent_fd)
        raise PackagingError("destination runs directory ownership changed")
    lock_fd: int | None = None
    lock_signature: tuple[int, int] | None = None
    lock_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        lock_flags |= os.O_NOFOLLOW
    try:
        lock_fd = os.open(
            lock.name, lock_flags, 0o600, dir_fd=runs_parent_fd)
    except FileExistsError as exc:
        os.close(runs_parent_fd)
        raise PackagingError(
            f"another or interrupted A6 import holds {lock}") from exc
    try:
        lock_info = os.fstat(lock_fd)
        if not stat.S_ISREG(lock_info.st_mode) or lock_info.st_nlink != 1:
            raise PackagingError("import lock ownership is invalid at creation")
        os.write(lock_fd, b"A6 import in progress\n")
        os.fsync(lock_fd)
        os.fsync(runs_parent_fd)
        # signature after the final write: rewrite detection must not be
        # defeated by inode recycling (EI-022)
        lock_signature = _regular_signature(os.fstat(lock_fd))
    except BaseException as exc:
        if lock_fd is not None:
            os.close(lock_fd)
        os.close(runs_parent_fd)
        raise PackagingError(
            "cannot establish an owned A6 import lock; path preserved to "
            "block analysis") from exc
    staging: Path | None = None
    staging_ownership: dict | None = None
    receipt_temp: Path | None = None
    receipt_temp_signature: tuple[int, int] | None = None
    target_installed = False
    receipt_installed = False
    target_ownership: dict | None = None
    receipt_ownership: dict | None = None
    release_lock = False
    # the import is durably committed only when the target tree and receipt
    # are installed AND fsynced (set on the success path, never on rollback);
    # a descriptor-close failure after this point must not report failure
    import_committed = False
    receipt_document: dict | None = None
    try:
        staging = Path(tempfile.mkdtemp(
            prefix=".a6_holdout.import-", dir=runs_parent))
        staging_info = staging.lstat()
        staging_ownership = {
            "root": (staging_info.st_dev, staging_info.st_ino),
            "directories": {},
            "files": {},
        }
        with tarfile.open(archive, "r:gz") as source_archive:
            by_name = {member.name: member for member in source_archive.getmembers()}
            for relative in snapshot["directories"]:
                directory = staging / relative
                directory.mkdir(mode=0o700)
                info = directory.lstat()
                staging_ownership["directories"][relative] = (
                    info.st_dev, info.st_ino)
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
                info = destination.lstat()
                staging_ownership["files"][record["path"]] = {
                    "signature": _regular_signature(info),
                    "nlink": 1,
                }
        staging_errors = _owned_tree_errors(staging, staging_ownership)
        if staging_errors:
            raise PackagingError(
                "import staging ownership differs: "
                + "; ".join(staging_errors))
        if snapshot_source(staging) != snapshot:
            raise PackagingError("import staging inventory differs from manifest")
        for directory in sorted(
                [staging, *(path for path in staging.rglob("*") if path.is_dir())],
                key=lambda path: len(path.parts), reverse=True):
            _fsync_directory(directory)
        if _stable_file_record(bundle, archive) != archive_record:
            raise PackagingError("bundle archive changed during import")

        imported_utc = datetime.datetime.now(
            datetime.timezone.utc).replace(microsecond=0).strftime(
                "%Y-%m-%dT%H:%M:%SZ")
        receipt_document = _receipt_document(
            repository=repository,
            target=target,
            bundle=bundle,
            archive=archive,
            archive_record=archive_record,
            manifest=manifest,
            manifest_bytes=manifest_bytes,
            audit_bytes=audit_bytes,
            snapshot=snapshot,
            imported_utc=imported_utc,
        )
        receipt_fd, receipt_name = tempfile.mkstemp(
            prefix=".a6_holdout.receipt-", dir=runs_parent)
        receipt_temp = Path(receipt_name)
        with os.fdopen(receipt_fd, "wb") as handle:
            handle.write(_canonical_json_bytes(receipt_document))
            handle.flush()
            os.fsync(handle.fileno())
        receipt_temp_info = receipt_temp.lstat()
        if (not stat.S_ISREG(receipt_temp_info.st_mode)
                or receipt_temp_info.st_nlink != 1):
            raise PackagingError("temporary transfer receipt ownership is invalid")
        receipt_temp_signature = _regular_signature(receipt_temp_info)

        if (target.exists() or target.is_symlink()
                or receipt_path.exists() or receipt_path.is_symlink()):
            raise PackagingError(
                "A6 import target or receipt appeared during verification")
        target_ownership = install_tree_no_replace(staging, target, snapshot)
        staging = None
        target_installed = True
        try:
            os.link(receipt_temp, receipt_path)
        except FileExistsError as exc:
            raise PackagingError(
                f"refusing existing transfer receipt: {receipt_path}") from exc
        receipt_link_info = receipt_path.lstat()
        temp_link_info = receipt_temp.lstat()
        if (_regular_signature_error(receipt_link_info,
                                     receipt_temp_signature)
                or _regular_signature_error(temp_link_info,
                                            receipt_temp_signature)
                or receipt_link_info.st_nlink != 2
                or temp_link_info.st_nlink != 2):
            raise PackagingError("transfer receipt hard-link ownership is invalid")
        receipt_temp.unlink()
        receipt_temp = None
        receipt_installed = True
        receipt_info = receipt_path.lstat()
        receipt_ownership = {
            "signature": receipt_temp_signature,
            "nlink": 1,
        }
        receipt_error = _owned_regular_error(
            receipt_path, receipt_ownership["signature"],
            allowed_nlinks={receipt_ownership["nlink"]})
        if receipt_error:
            raise PackagingError(receipt_error)
        validate_transfer_receipt(
            receipt_path, expected=receipt_document)
        if snapshot_source(target) != snapshot:
            raise PackagingError(
                "installed source tree differs before import commit")
        # canonical digest is computed and RETAINED while the import lock
        # still excludes competitors; no receipt I/O happens after commit
        receipt_sha256 = sha256_file(receipt_path)
        _fsync_directory(runs_parent)
        release_lock = True
        # target + receipt are durably installed and fsynced: the import has
        # committed and only the lock release remains
        import_committed = True
    except BaseException as exc:
        rollback_errors = []
        if isinstance(exc, IncompletePublicationError):
            rollback_errors.append(str(exc))
        # Validate the complete transaction before removing either half.  A
        # competitor at one path freezes both assets and the lock for review.
        if receipt_installed:
            if receipt_ownership is None:
                rollback_errors.append("receipt ownership record is missing")
            else:
                receipt_error = _owned_regular_error(
                    receipt_path, receipt_ownership["signature"],
                    allowed_nlinks={receipt_ownership["nlink"]})
                if receipt_error:
                    rollback_errors.append(receipt_error)
        elif receipt_path.exists() or receipt_path.is_symlink():
            rollback_errors.append(
                f"unowned transfer receipt appeared: {receipt_path}")
        if target_installed:
            if target_ownership is None:
                rollback_errors.append("target ownership record is missing")
            else:
                rollback_errors.extend(
                    _owned_tree_errors(target, target_ownership))
        elif target.exists() or target.is_symlink():
            rollback_errors.append(
                f"unowned or incomplete import target appeared: {target}")

        if not rollback_errors and receipt_installed:
            receipt_error = _owned_regular_error(
                receipt_path, receipt_ownership["signature"],
                allowed_nlinks={receipt_ownership["nlink"]})
            if receipt_error:
                rollback_errors.append(receipt_error)
            else:
                try:
                    receipt_path.unlink()
                    receipt_installed = False
                except OSError as rollback_exc:
                    rollback_errors.append(
                        f"owned receipt rollback failed: {rollback_exc}")
        if not rollback_errors and target_installed:
            tree_errors = _rollback_owned_tree(target, target_ownership)
            if tree_errors:
                rollback_errors.extend(tree_errors)
            else:
                target_installed = False
        try:
            _fsync_directory(runs_parent)
        except OSError as rollback_exc:
            rollback_errors.append(f"parent fsync: {rollback_exc}")
        if rollback_errors:
            raise PackagingError(
                "A6 import failed and rollback was incomplete; import lock "
                "preserved: " + "; ".join(rollback_errors)) from exc
        release_lock = True
        raise
    finally:
        temporary_cleanup_errors = []
        if (staging is not None
                and (staging.exists() or staging.is_symlink())):
            if staging_ownership is None:
                temporary_cleanup_errors.append(
                    "staging ownership record is missing")
            else:
                temporary_cleanup_errors.extend(
                    _rollback_owned_tree(staging, staging_ownership))
        if (receipt_temp is not None
                and (receipt_temp.exists() or receipt_temp.is_symlink())):
            if receipt_temp_signature is None:
                temporary_cleanup_errors.append(
                    "temporary receipt ownership record is missing")
            else:
                receipt_temp_error = _owned_regular_error(
                    receipt_temp, receipt_temp_signature,
                    allowed_nlinks={1})
                if receipt_temp_error:
                    temporary_cleanup_errors.append(receipt_temp_error)
                else:
                    try:
                        receipt_temp.unlink()
                    except OSError as cleanup_exc:
                        temporary_cleanup_errors.append(
                            f"temporary receipt cleanup failed: {cleanup_exc}")
        if temporary_cleanup_errors:
            release_lock = False
        lock_release_errors = []
        try:
            if release_lock:
                if lock_signature is None or lock_fd is None:
                    lock_release_errors.append(
                        "import lock ownership record is missing")
                else:
                    open_info = os.fstat(lock_fd)
                    if (_regular_signature_error(open_info, lock_signature)
                            or open_info.st_nlink != 1):
                        lock_release_errors.append(
                            "open import lock ownership changed")
                    lock_error = _owned_regular_error_at(
                        runs_parent_fd, lock.name, lock_signature,
                        allowed_nlinks={1}, display=lock)
                    if lock_error:
                        lock_release_errors.append(lock_error)
                if not lock_release_errors:
                    try:
                        os.unlink(lock.name, dir_fd=runs_parent_fd)
                    except OSError as exc:
                        lock_release_errors.append(
                            f"owned import lock unlink failed: {exc}")
                    else:
                        try:
                            os.fsync(runs_parent_fd)
                        except OSError as exc:
                            lock_release_errors.append(
                                f"import lock parent fsync failed: {exc}")
                if lock_release_errors:
                    lock_release_errors.extend(
                        _ensure_blocking_regular_path(
                            lock, runs_parent_fd))
            else:
                lock_release_errors.extend(
                    _ensure_blocking_regular_path(
                        lock, runs_parent_fd))
        finally:
            close_errors = []
            for descriptor in (lock_fd, runs_parent_fd):
                if descriptor is not None:
                    try:
                        os.close(descriptor)
                    except OSError as close_exc:
                        close_errors.append(str(close_exc))
            # once the import has committed (target + receipt durable, lock
            # released and its parent fsynced), a descriptor-close failure
            # has no data consequence and must NOT report the import as
            # unsuccessful; pre-commit close failures are still surfaced.
            if close_errors and not import_committed:
                raise PackagingError(
                    "A6 import descriptor close failed before commit; import "
                    "lock preserved: " + "; ".join(close_errors))
        if lock_release_errors:
            raise PackagingError(
                "cannot safely release A6 import lock; analysis remains "
                "blocked: " + "; ".join(lock_release_errors))
        if temporary_cleanup_errors:
            raise PackagingError(
                "A6 import temporary rollback was incomplete; import lock "
                "preserved: " + "; ".join(temporary_cleanup_errors))

    if receipt_document is None:
        raise PackagingError("transfer receipt was not committed")
    return {
        "target": str(target),
        "receipt": str(receipt_path),
        # retained digest from under the lock: never reread after commit
        "receipt_sha256": receipt_sha256,
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
    scientific_validator=None,
    audit_fn=None,
    job_quiescence_validator=assert_job_quiescent,
    closeout_claimer=claim_closeout,
    closeout_claim_validator=assert_closeout_claim_unchanged,
    recovery=None,
) -> dict:
    """Validate, package, and publish one no-overwrite transfer bundle."""
    if (selection_validator is None or preflight_validator is None
            or launch_validator is None or root_validator is None
            or scientific_validator is None or audit_fn is None):
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
        scientific_validator = (
            scientific_validator or validate_scientific_population)
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
    if out_path.is_symlink() or not out_path.is_dir():
        raise PackagingError(f"unsafe package output directory: {out_path}")

    # Hashing bytes is outcome-blind.  The exclusive claim is committed before
    # any checkpoint is audited, extracted, or scored below.
    live_snapshot = snapshot_source(root_path)
    closeout_claim = closeout_claimer(
        root_path,
        packaging_commit=packaging_commit,
        preflight=live_preflight,
        selection=selection,
        launch=live_launch,
        snapshot=live_snapshot,
    )

    staging: Path | None = Path(tempfile.mkdtemp(
        prefix=f".{bundle_name}.staging-", dir=out_path))
    staging_ownership: dict | None = None
    archive_name = f"{bundle_name}.tar.gz"
    try:
        staging_ownership = _capture_exact_tree_ownership(
            staging, expected_directories=set(), expected_files=set())
        frozen_root = staging / ".frozen-a6-holdout"
        snapshot = freeze_source(root_path, frozen_root)
        frozen_ownership = _capture_exact_tree_ownership(
            frozen_root,
            expected_directories=set(snapshot["directories"]),
            expected_files={record["path"] for record in snapshot["files"]},
        )
        frozen_prefix = frozen_root.name
        staging_ownership["directories"][frozen_prefix] = (
            frozen_ownership["root"])
        for relative, signature in frozen_ownership["directories"].items():
            staging_ownership["directories"][
                f"{frozen_prefix}/{relative}"] = signature
        for relative, record in frozen_ownership["files"].items():
            staging_ownership["files"][f"{frozen_prefix}/{relative}"] = {
                **record,
            }
        staging_errors = _owned_tree_errors(staging, staging_ownership)
        if staging_errors:
            raise PackagingError(
                "package staging changed after source freeze: "
                + "; ".join(staging_errors))
        if snapshot != live_snapshot:
            raise PackagingError(
                "source tree changed after the closeout claim")

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
            str(frozen_root), instances=instances, preflight=preflight,
            launch=launch)
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
            closeout_claim=closeout_claim,
            scientific=scientific,
            snapshot=snapshot,
            audit_bytes=audit_bytes,
            recovery=recovery,
        )
        manifest_bytes = (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode()
        archive_path = staging / archive_name
        _write_archive(
            archive_path, frozen_root, snapshot, manifest_bytes, audit_bytes)
        _record_owned_regular_entry(
            staging, staging_ownership, archive_name)
        _verify_archive(
            archive_path, snapshot, manifest_bytes, audit_bytes)
        if (snapshot_source(frozen_root) != snapshot
                or snapshot_source(root_path) != snapshot):
            raise PackagingError(
                "source tree changed while the archive was being written")

        archive_sha = sha256_file(str(archive_path))
        _write_bytes(staging / "BUNDLE_MANIFEST.json", manifest_bytes)
        _record_owned_regular_entry(
            staging, staging_ownership, "BUNDLE_MANIFEST.json")
        _write_bytes(staging / "AUDIT_SUMMARY.md", audit_bytes)
        _record_owned_regular_entry(
            staging, staging_ownership, "AUDIT_SUMMARY.md")
        _write_bytes(
            staging / "ARCHIVE.sha256",
            f"{archive_sha}  {archive_name}\n".encode(),
        )
        _record_owned_regular_entry(
            staging, staging_ownership, "ARCHIVE.sha256")
        frozen_cleanup_errors = _rollback_owned_tree(
            frozen_root, frozen_ownership)
        if frozen_cleanup_errors:
            raise IncompletePublicationError(
                "frozen package staging cleanup was incomplete: "
                + "; ".join(frozen_cleanup_errors))
        staging_ownership["directories"] = {
            relative: signature
            for relative, signature in staging_ownership["directories"].items()
            if relative != frozen_prefix
            and not relative.startswith(f"{frozen_prefix}/")
        }
        staging_ownership["files"] = {
            relative: record
            for relative, record in staging_ownership["files"].items()
            if not relative.startswith(f"{frozen_prefix}/")
        }
        staging_errors = _owned_tree_errors(staging, staging_ownership)
        if staging_errors:
            raise PackagingError(
                "package staging changed after frozen-tree cleanup: "
                + "; ".join(staging_errors))
        _fsync_directory(staging)
        # These are the final gates before exclusive no-replace publication.
        job_quiescence_validator(launch["job_id"])
        if snapshot_source(root_path) != snapshot:
            raise PackagingError(
                "source tree changed immediately before publication")
        closeout_claim_validator(closeout_claim)
        try:
            publish_flat_directory_no_replace(
                staging,
                final_dir,
                expected_names={
                    archive_name,
                    "ARCHIVE.sha256",
                    "BUNDLE_MANIFEST.json",
                    "AUDIT_SUMMARY.md",
                },
            )
        except IncompletePublicationError as pub_exc:
            if pub_exc.renamed:
                # the staging tree moved: evidence is preserved at the
                # destination (anchored by the marker unless committed);
                # there is nothing to clean at the staging path
                staging = None
            raise
        staging = None
    finally:
        if staging is not None:
            # an exception is always in flight here (staging is None on
            # success); cleanup problems must never mask it
            if staging_ownership is None:
                cleanup_errors = [
                    "package staging ownership record is missing"]
            else:
                cleanup_errors = _rollback_owned_tree(
                    staging, staging_ownership)
            if cleanup_errors:
                sys.stderr.write(
                    "package staging preserved for incident review: "
                    f"{staging}: " + "; ".join(cleanup_errors) + "\n")

    return {
        "bundle_dir": str(final_dir),
        "archive": str(final_dir / archive_name),
        "sidecar": str(final_dir / "ARCHIVE.sha256"),
        "manifest": str(final_dir / "BUNDLE_MANIFEST.json"),
        "audit_summary": str(final_dir / "AUDIT_SUMMARY.md"),
        "archive_sha256": archive_sha,
    }


def recover_package_holdout(
    root: str | os.PathLike,
    out_base: str | os.PathLike,
    recovery_code_commit: str,
    *,
    incident_id: str,
    original_claim_sha256: str,
    failure_fingerprint: str,
    selection_path: str | os.PathLike = DEFAULT_SELECTION,
    instances=HOLDOUT_INSTANCES,
    require_frozen_grid: bool = True,
    verify_selection_git: bool = True,
    code_verifier=verify_packaging_code_commit,
    job_quiescence_validator=assert_job_quiescent,
    head_resolver=_resolve_head_commit,
    clean_tree_checker=_require_clean_tracked_tree,
    ancestor_checker=_require_commit_ancestor,
    original_claim_verifier=verify_original_claim,
    recovery_claimer=claim_recovery,
    expected_original_sha256: str = RECOVERY_ORIGINAL_CLAIM_SHA256,
    expected_original_packaging_commit: str = (
        RECOVERY_ORIGINAL_PACKAGING_COMMIT),
    expected_original_source_tree_sha256: str = (
        RECOVERY_ORIGINAL_SOURCE_TREE_SHA256),
    **package_kwargs,
) -> dict:
    """One-shot EI-026-only claimed-incident recovery.

    This is a SEPARATE, explicit recovery entry point, never a generic bypass:
    normal ``package_holdout`` still refuses the existing closeout claim.  The
    gates run in a fixed order and every failure is fail-closed.
    """
    # 1. incident + full original claim SHA gate.
    if incident_id != RECOVERY_INCIDENT_ID:
        raise PackagingError(
            f"recovery is restricted to {RECOVERY_INCIDENT_ID}; "
            f"got {incident_id!r}")
    if not _full_hex(original_claim_sha256, 64):
        raise PackagingError("original claim SHA-256 must be 64 lowercase hex")
    if not isinstance(failure_fingerprint, str) or not failure_fingerprint:
        raise PackagingError("recovery requires a non-empty failure fingerprint")
    # 3. clean recovery HEAD equal to the recovery commit, with 740ab0c as an
    #    ancestor.  code_verifier enforces HEAD == recovery commit and a clean
    #    tracked tree (EI-004 contract); the ancestry check is additional.
    recovery_commit = code_verifier(recovery_code_commit)
    clean_tree_checker()
    head = head_resolver()
    if head != recovery_commit:
        raise PackagingError(
            "recovery HEAD does not equal the recovery commit "
            f"({head!r} != {recovery_commit!r})")
    ancestor_checker(RECOVERY_BASE_COMMIT, head)
    # 2. open + verify the immutable original claim against the FROZEN
    #    EI-026 identities.
    original_claim = original_claim_verifier(
        root, original_claim_sha256=original_claim_sha256,
        expected_sha256=expected_original_sha256,
        expected_packaging_commit=expected_original_packaging_commit,
        expected_source_tree_sha256=expected_original_source_tree_sha256)
    doc = original_claim["document"]
    # 8. Slurm quiescence BEFORE reading any outcome.
    job_quiescence_validator(doc["launch_job_id"])
    # 4. the live raw tree must still exactly match the original claim BEFORE
    #    any outcome validation.
    root_path = Path(root).expanduser().resolve()
    live_snapshot = snapshot_source(root_path)
    src = doc["source"]
    live_tree_sha = canonical_tree_sha256(live_snapshot)
    if (live_tree_sha != src["canonical_tree_sha256"]
            or live_snapshot["file_count"] != src["file_count"]
            or live_snapshot["directory_count"] != src["directory_count"]
            or live_snapshot["total_bytes"] != src["total_bytes"]):
        raise PackagingError(
            "live raw tree no longer matches the original claim; refusing "
            "recovery before any outcome validation")
    # B2. refuse ANY existing final package with the same campaign/job/preflight
    #     prefix, regardless of packaging commit, before consuming recovery.
    out_path = Path(out_base).expanduser().resolve()
    prefix = (f"a6_holdout-job{doc['launch_job_id']}-"
              f"{doc['preflight_sha256'][:12]}-")
    if out_path.is_dir():
        for entry in out_path.iterdir():
            if entry.name.startswith(prefix):
                raise PackagingError(
                    "refusing recovery: an existing package with the same "
                    f"campaign/job/preflight prefix is present: {entry}")
    # 5. exclusively create the SECOND adjacent recovery claim before outcome
    #    validation; exactly one attempt (a pre-existing recovery claim blocks
    #    all further attempts).  6. the original claim/raw root are never
    #    modified or replaced.
    recovery_claim = recovery_claimer(
        root_path, original_claim=original_claim,
        recovery_commit=recovery_commit,
        failure_fingerprint=failure_fingerprint,
        raw_tree_sha256=live_tree_sha)
    recovery_meta = {
        "incident_id": RECOVERY_INCIDENT_ID,
        "recovery_code_commit": recovery_commit,
        "recovery_base_commit": RECOVERY_BASE_COMMIT,
        "experiment_code_commit": doc["experiment_code_commit"],
        "original_claim": {
            "sha256": original_claim["sha256"],
            "packaging_code_commit": doc["packaging_code_commit"],
        },
        # B3. embed the COMPLETE recovery claim, not only its SHA.
        "recovery_claim": {
            "sha256": recovery_claim["sha256"],
            "document": recovery_claim["document"],
        },
    }

    # 7. fresh staging only (package_holdout always mkdtemp's fresh staging).
    #    The recovery claimer below RETURNS the existing original claim so the
    #    normal exclusive CLOSEOUT_CLAIM create is never invoked here.
    def _recovery_closeout_claimer(*_args, **_kwargs):
        return original_claim

    # B3. revalidate BOTH immutable claims immediately before scientific
    #     validation/publication; any mutation fails closed.
    def _recovery_claim_validator(record):
        assert_closeout_claim_unchanged(record)          # original claim
        raw = _regular_bundle_file(
            Path(recovery_claim["path"]), "recovery claim")
        if (raw != _canonical_json_bytes(recovery_claim["document"])
                or hashlib.sha256(raw).hexdigest() != recovery_claim["sha256"]):
            raise PackagingError("recovery claim changed during recovery")

    return package_holdout(
        root, out_base, recovery_code_commit,
        selection_path=selection_path, instances=instances,
        require_frozen_grid=require_frozen_grid,
        verify_selection_git=verify_selection_git,
        code_verifier=code_verifier,
        job_quiescence_validator=job_quiescence_validator,
        closeout_claimer=_recovery_closeout_claimer,
        closeout_claim_validator=_recovery_claim_validator,
        recovery=recovery_meta,
        **package_kwargs,
    )


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
    # EI-026-only one-shot recovery: a SEPARATE, explicit command (not a
    # generic bypass). Normal `pack` still refuses the existing claim.
    recover_parser = commands.add_parser("recover-pack")
    recover_parser.add_argument("--root", default="runs/a6_holdout")
    recover_parser.add_argument("--out", default=DEFAULT_OUT)
    recover_parser.add_argument("--selection", default=str(DEFAULT_SELECTION))
    recover_parser.add_argument("--recovery-code-commit", required=True)
    recover_parser.add_argument("--incident-id", required=True)
    recover_parser.add_argument("--original-claim-sha256", required=True)
    recover_parser.add_argument("--failure-fingerprint", required=True)
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
    elif args.command == "recover-pack":
        result = recover_package_holdout(
            args.root,
            args.out,
            args.recovery_code_commit,
            incident_id=args.incident_id,
            original_claim_sha256=args.original_claim_sha256,
            failure_fingerprint=args.failure_fingerprint,
            selection_path=args.selection,
        )
        print(f"[done] recovery wrote {result['bundle_dir']}")
        print(f"archive: {result['archive']}")
        print(f"sha256:  {result['archive_sha256']}")
    else:
        result = import_bundle(args.bundle_dir, args.repo_root)
        print(f"[done] imported {result['target']}")
        print(f"receipt: {result['receipt']}")
        print(f"files:   {result['file_count']}")
        print(f"sha256:  {result['archive_sha256']}")


if __name__ == "__main__":
    main()
