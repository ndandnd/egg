#!/usr/bin/env python3
"""Build the small public evidence archive for feasible-pool pilot attempt 1.

The full attempt remains in the private collection directory. This script
checks that sealed source against MANIFEST.json, copies only an explicit
allowlist into a deterministic ZIP, and records hashes for included and
omitted source files.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


PROTOCOL = "egg-feasible-pool-public-evidence-v1"
ATTEMPT_RELATIVE_PATH = "result/feasible_pool_pilot/20260928-attempt1"
ROOT_ALLOWLIST = {
    "frozen.json",
    "summary.json",
    "supervisor_receipt.json",
    "postmortem_summary.json",
}
STAGE_ALLOWLIST = {"raw_result.json", "result.json", "receipt.json", "ineligible.json"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def default_attempt_dir() -> Path:
    # The collected full attempt lives beside, rather than inside, the Git repo.
    workspace = Path(__file__).resolve().parents[3]
    return (
        workspace
        / "research-20260928"
        / "cluster"
        / "feasible-pool-pilot-attempt1"
        / "collected"
        / "package"
        / ATTEMPT_RELATIVE_PATH
    )


def validate_relative_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or ".." in path.parts or "." in path.parts:
        raise ValueError(f"unsafe relative path in seal: {name!r}")
    return path


def omission_reason(relative_path: str) -> str:
    path = PurePosixPath(relative_path)
    name = path.name.lower()
    if relative_path == "MANIFEST.json":
        return "Original seal file is retained with the private attempt; its hash is recorded separately."
    if name.endswith(".jsonl"):
        return "Raw line-oriented data is outside the public evidence allowlist."
    if "feature" in name or "feature" in relative_path.lower():
        return "Feature and input dumps are outside the public evidence allowlist."
    if "exception" in name or "exception" in relative_path.lower():
        return "Exception diagnostics are outside the public evidence allowlist."
    if "launch" in name or "launch" in relative_path.lower():
        return "Launch metadata is outside the public evidence allowlist."
    if path.suffix.lower() in {".txt", ".log", ".stderr", ".stdout"}:
        return "Text diagnostics and logs are outside the public evidence allowlist."
    return "File is outside the explicit public evidence allowlist."


def write_exclusive_or_verify(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError(f"existing output differs; refusing to overwrite {path}")
        return
    with path.open("xb") as stream:
        stream.write(data)


def make_zip(included: list[tuple[str, Path]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_STORED) as archive:
        for relative_path, source in included:
            info = zipfile.ZipInfo(relative_path, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.flag_bits = 0
            archive.writestr(info, source.read_bytes())
    return buffer.getvalue()


def package_evidence(attempt_dir: Path, output_dir: Path) -> dict[str, Any]:
    attempt_dir = attempt_dir.resolve(strict=True)
    manifest_path = attempt_dir / "MANIFEST.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        raise ValueError("MANIFEST.json must contain a files mapping")

    expected: dict[str, dict[str, Any]] = manifest["files"]
    actual: dict[str, Path] = {}
    for path in attempt_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink in sealed attempt: {path.relative_to(attempt_dir)}")
        if path.is_file() and path != manifest_path:
            relative_path = path.relative_to(attempt_dir).as_posix()
            validate_relative_path(relative_path)
            actual[relative_path] = path

    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    mismatches: list[str] = []
    source_hashes: dict[str, dict[str, Any]] = {}
    for relative_path, entry in expected.items():
        validate_relative_path(relative_path)
        source = actual.get(relative_path)
        if source is None:
            continue
        data = source.read_bytes()
        observed = {"bytes": len(data), "sha256": sha256(data)}
        source_hashes[relative_path] = observed
        if observed["bytes"] != entry.get("bytes") or observed["sha256"] != entry.get("sha256"):
            mismatches.append(relative_path)
    if missing or unexpected or mismatches:
        raise ValueError(
            "sealed source verification failed: "
            f"missing={len(missing)} unexpected={len(unexpected)} mismatches={len(mismatches)}"
        )

    included: list[tuple[str, Path]] = []
    for relative_path, source in actual.items():
        parts = PurePosixPath(relative_path).parts
        if len(parts) == 1 and parts[0] in ROOT_ALLOWLIST:
            included.append((relative_path, source))
        elif len(parts) > 1 and parts[-1] in STAGE_ALLOWLIST:
            included.append((relative_path, source))
    included.sort(key=lambda pair: pair[0])

    required_roots = {"frozen.json", "summary.json", "supervisor_receipt.json"}
    included_roots = {name for name, _ in included if len(PurePosixPath(name).parts) == 1}
    if not required_roots.issubset(included_roots):
        raise ValueError(f"required root evidence files missing: {sorted(required_roots - included_roots)}")

    zip_bytes = make_zip(included)
    expected_members = [name for name, _ in included]
    with zipfile.ZipFile(io.BytesIO(zip_bytes), mode="r") as archive:
        if archive.namelist() != expected_members:
            raise ValueError("ZIP member list does not equal the allowlist")
        for relative_path, source in included:
            if archive.read(relative_path) != source.read_bytes():
                raise ValueError(f"ZIP bytes differ from source: {relative_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / "scientific_evidence.zip"
    write_exclusive_or_verify(zip_path, zip_bytes)
    saved_zip = zip_path.read_bytes()
    if saved_zip != zip_bytes:
        raise ValueError("saved ZIP differs from generated ZIP")
    with zipfile.ZipFile(zip_path, mode="r") as archive:
        if archive.namelist() != expected_members:
            raise ValueError("saved ZIP member list does not equal the allowlist")
        for relative_path, source in included:
            if archive.read(relative_path) != source.read_bytes():
                raise ValueError(f"saved ZIP bytes differ from source: {relative_path}")

    included_set = {name for name, _ in included}
    original_files = dict(actual)
    original_files["MANIFEST.json"] = manifest_path
    omitted = []
    for relative_path, source in sorted(original_files.items()):
        if relative_path in included_set:
            continue
        data = source.read_bytes()
        omitted.append(
            {
                "path": relative_path,
                "bytes": len(data),
                "sha256": sha256(data),
                "reason": omission_reason(relative_path),
            }
        )

    included_records = []
    for relative_path, source in included:
        data = source.read_bytes()
        included_records.append(
            {"path": relative_path, "bytes": len(data), "sha256": sha256(data)}
        )

    report = {
        "protocol": PROTOCOL,
        "source_attempt": ATTEMPT_RELATIVE_PATH,
        "seal_protocol": manifest.get("protocol"),
        "original_seal": {
            "path": "MANIFEST.json",
            "bytes": len(manifest_bytes),
            "sha256": sha256(manifest_bytes),
            "manifested_files": len(expected),
        },
        "source_verification": {
            "original_files_including_seal": len(original_files),
            "manifest_entries_verified": len(expected),
            "missing": 0,
            "unexpected": 0,
            "hash_or_size_mismatches": 0,
        },
        "evidence_zip": {
            "path": "scientific_evidence.zip",
            "bytes": len(saved_zip),
            "sha256": sha256(saved_zip),
            "member_count": len(expected_members),
            "members_match_allowlist": True,
            "member_bytes_match_source": True,
        },
        "included_files": included_records,
        "omitted_files": omitted,
    }
    report_bytes = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    write_exclusive_or_verify(output_dir / "PUBLIC_EVIDENCE_MANIFEST.json", report_bytes)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, default=default_attempt_dir())
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "results-attempt1")
    args = parser.parse_args()
    report = package_evidence(args.attempt_dir, args.output_dir)
    print(
        "verified sealed source and wrote public evidence: "
        f"included={len(report['included_files'])} omitted={len(report['omitted_files'])} "
        f"zip_sha256={report['evidence_zip']['sha256']}"
    )


if __name__ == "__main__":
    main()
