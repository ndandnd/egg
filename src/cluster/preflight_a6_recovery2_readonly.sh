#!/usr/bin/env bash
# Outcome-blind, read-only inspection of the Unicorn A6 recovery2 state.
# This script never creates a claim or package and never runs the analyzer.

set -uo pipefail

script_path="${BASH_SOURCE[0]}"
script_parent="${script_path%/*}"
if test "$script_parent" = "$script_path"; then
    script_parent=.
fi
script_dir="$(CDPATH= cd -- "$script_parent" && pwd -P)" || exit 1
src_dir="$(CDPATH= cd -- "${script_dir}/.." && pwd -P)" || exit 1
cd "$src_dir" || exit 1

export PYTHONDONTWRITEBYTECODE=1

egg_python=/usr/bin/python3
egg_git=/usr/bin/git
egg_squeue=/usr/local/slurm/current/bin/squeue

if test ! -x "$egg_python"; then
    printf 'INVARIANT_FAIL=trusted Python is unavailable: %s\n' "$egg_python"
    exit 1
fi

exec "$egg_python" - "$egg_git" "$egg_squeue" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

from experiments import package_a6_holdout as package


GIT = sys.argv[1]
SQUEUE = sys.argv[2]
SRC = Path.cwd()
REPO = SRC.parent
RUNS = SRC / "runs"
ROOT = RUNS / "a6_holdout"
PACKAGES = RUNS / "a6_holdout_packages"
CLOSEOUT = RUNS / package.CLOSEOUT_CLAIM_FILENAME
RECOVERY1 = RUNS / package.RECOVERY_CLAIM_FILENAME
RECOVERY2 = RUNS / package.RECOVERY2_CLAIM_FILENAME

failures: list[str] = []

GIT_ENV = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "HOME": "/nonexistent",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin",
    "XDG_CONFIG_HOME": "/nonexistent",
}

SQUEUE_ENV = {
    "HOME": os.environ.get("HOME", "/nonexistent"),
    "LANG": "C",
    "LC_ALL": "C",
    "LOGNAME": os.environ.get("LOGNAME", os.environ.get("USER", "")),
    "PATH": "/usr/bin:/bin",
    "USER": os.environ.get("USER", ""),
}


def ok(label: str, detail: object = "") -> None:
    suffix = f"={detail}" if detail != "" else ""
    print(f"OK_{label}{suffix}")


def fail(label: str, detail: object) -> None:
    failures.append(label)
    print(f"FAIL_{label}={detail}")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reject_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def strict_claim(path: Path, expected_sha256: str | None = None) -> tuple[bytes, dict]:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("not a regular single-link file")
    raw = path.read_bytes()
    document = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(document, dict):
        raise ValueError("top-level JSON value is not an object")
    if raw != package._canonical_json_bytes(document):
        raise ValueError("JSON is not canonical")
    actual = sha256_bytes(raw)
    if expected_sha256 is not None and actual != expected_sha256:
        raise ValueError(f"SHA-256 {actual}, expected {expected_sha256}")
    return raw, document


def git_output(*args: str) -> str:
    return subprocess.check_output(
        [GIT, "-C", str(REPO), *args],
        env=GIT_ENV,
        stderr=subprocess.DEVNULL,
        text=True,
    ).strip()


print("MODE=READ_ONLY_OUTCOME_BLIND")
print("AUTHORIZATION=NONE")
print(f"PYTHON={sys.executable}")
print(f"GIT={GIT}")
print(f"SQUEUE={SQUEUE}")

try:
    head = git_output("rev-parse", "--verify", "HEAD^{commit}")
    dirty = git_output("status", "--porcelain", "--untracked-files=no")
    ok("HEAD", head)
    if dirty:
        fail("TRACKED_TREE", "dirty")
    else:
        ok("TRACKED_TREE", "clean")
    for ancestor in (
        package.RECOVERY_BASE_COMMIT,
        package.RECOVERY2_FIRST_RECOVERY_COMMIT,
        package.RECOVERY2_BASE_COMMIT,
    ):
        subprocess.run(
            [GIT, "-C", str(REPO), "merge-base", "--is-ancestor", ancestor, head],
            env=GIT_ENV,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        ok("ANCESTOR", ancestor)
except (OSError, subprocess.CalledProcessError) as exc:
    fail("GIT_PROVENANCE", type(exc).__name__)

closeout = None
recovery1 = None
recovery2 = None

for label, path, expected in (
    ("CLOSEOUT_CLAIM", CLOSEOUT, package.RECOVERY_ORIGINAL_CLAIM_SHA256),
    ("RECOVERY1_CLAIM", RECOVERY1, package.RECOVERY2_FIRST_RECOVERY_CLAIM_SHA256),
):
    try:
        raw, document = strict_claim(path, expected)
        ok(f"{label}_SHA256", sha256_bytes(raw))
        if label == "CLOSEOUT_CLAIM":
            closeout = document
        else:
            recovery1 = document
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        fail(label, str(exc))

if RECOVERY2.exists() or RECOVERY2.is_symlink():
    print("ONE_SHOT_STATE=SPENT")
    try:
        raw, recovery2 = strict_claim(RECOVERY2)
        ok("RECOVERY2_CLAIM_SHA256", sha256_bytes(raw))
        if recovery2.get("schema") != package.RECOVERY2_CLAIM_SCHEMA:
            fail("RECOVERY2_SCHEMA", recovery2.get("schema"))
        if recovery2.get("incident_id") != package.RECOVERY2_INCIDENT_ID:
            fail("RECOVERY2_INCIDENT", recovery2.get("incident_id"))
        if recovery2.get("status") != "recovery2-claimed-before-outcome-validation":
            fail("RECOVERY2_STATUS", recovery2.get("status"))
        if recovery2.get("raw_tree_sha256") != package.RECOVERY_ORIGINAL_SOURCE_TREE_SHA256:
            fail("RECOVERY2_RAW_TREE_BINDING", recovery2.get("raw_tree_sha256"))
        if (recovery2.get("original_claim") or {}).get("sha256") != package.RECOVERY_ORIGINAL_CLAIM_SHA256:
            fail("RECOVERY2_ORIGINAL_BINDING", recovery2.get("original_claim"))
        if (recovery2.get("first_recovery_claim") or {}).get("sha256") != package.RECOVERY2_FIRST_RECOVERY_CLAIM_SHA256:
            fail("RECOVERY2_RECOVERY1_BINDING", recovery2.get("first_recovery_claim"))
        ok("RECOVERY2_CODE_COMMIT", recovery2.get("recovery2_code_commit"))
        ok("RECOVERY2_CLAIMED_UTC", recovery2.get("claimed_utc"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        fail("RECOVERY2_CLAIM", str(exc))
else:
    print("ONE_SHOT_STATE=UNSPENT")

if closeout is not None:
    try:
        snapshot = package.snapshot_source(ROOT)
        live = {
            "canonical_tree_sha256": package.canonical_tree_sha256(snapshot),
            "file_count": snapshot["file_count"],
            "directory_count": snapshot["directory_count"],
            "total_bytes": snapshot["total_bytes"],
        }
        expected_source = closeout.get("source") or {}
        changed = [key for key, value in live.items() if expected_source.get(key) != value]
        if live["canonical_tree_sha256"] != package.RECOVERY_ORIGINAL_SOURCE_TREE_SHA256:
            changed.append("frozen_canonical_tree_sha256")
        if changed:
            fail("RAW_TREE", f"changed fields: {sorted(set(changed))}; live={live}")
        else:
            ok("RAW_TREE_SHA256", live["canonical_tree_sha256"])
    except (OSError, package.PackagingError) as exc:
        fail("RAW_TREE", str(exc))

    job_id = str(closeout.get("launch_job_id", ""))
    preflight_sha256 = str(closeout.get("preflight_sha256", ""))
    prefix = f"a6_holdout-job{job_id}-{preflight_sha256[:12]}-"
    ok("LAUNCH_JOB_ID", job_id)
    ok("PACKAGE_PREFIX", prefix)

    if not os.path.isfile(SQUEUE) or not os.access(SQUEUE, os.X_OK):
        fail("SQUEUE", f"not executable: {SQUEUE}")
    else:
        try:
            result = subprocess.run(
                [SQUEUE, "--noheader", "--jobs", job_id, "--format=%F|%T"],
                check=True,
                capture_output=True,
                env=SQUEUE_ENV,
                text=True,
            )
            rows = [line for line in result.stdout.splitlines() if line.strip()]
            if rows:
                fail("LAUNCH_JOB_QUIESCENCE", json.dumps(rows))
            else:
                ok("LAUNCH_JOB_QUIESCENCE", "quiescent")
        except (OSError, subprocess.CalledProcessError) as exc:
            fail("SQUEUE_QUERY", type(exc).__name__)

    related: list[Path] = []
    if PACKAGES.exists() or PACKAGES.is_symlink():
        try:
            root_info = PACKAGES.lstat()
            if not stat.S_ISDIR(root_info.st_mode):
                raise ValueError("package root is not a directory")
            related = sorted(
                (path for path in PACKAGES.iterdir() if prefix in path.name),
                key=lambda path: path.name,
            )
        except (OSError, ValueError) as exc:
            fail("PACKAGE_ROOT", str(exc))

    complete_candidates: list[str] = []
    for path in related:
        try:
            info = path.lstat()
            if not stat.S_ISDIR(info.st_mode):
                print(f"PACKAGE_ENTRY={path.name}|not-directory")
                continue
            members = sorted(child.name for child in path.iterdir())
            print(f"PACKAGE_ENTRY={path.name}|members={json.dumps(members)}")
            archives = [name for name in members if name.endswith(".tar.gz")]
            expected_members = {
                "ARCHIVE.sha256",
                "AUDIT_SUMMARY.md",
                "BUNDLE_MANIFEST.json",
                *archives,
            }
            final_name = path.name.startswith(prefix)
            complete_shape = (
                final_name
                and len(archives) == 1
                and set(members) == expected_members
                and ".publication-incomplete" not in members
            )
            if complete_shape:
                archive = path / archives[0]
                actual = sha256_file(archive)
                sidecar = (path / "ARCHIVE.sha256").read_text().strip().split()[0]
                if actual == sidecar:
                    complete_candidates.append(path.name)
                    ok("PACKAGE_ARCHIVE_SHA256", actual)
                else:
                    fail("PACKAGE_ARCHIVE_SIDECAR", f"{path.name}: {actual} != {sidecar}")
        except (OSError, IndexError) as exc:
            fail("PACKAGE_ENTRY", f"{path.name}: {exc}")

    print("RELATED_PACKAGE_ENTRIES=" + json.dumps([path.name for path in related]))
    print("COMPLETE_PACKAGE_CANDIDATES=" + json.dumps(complete_candidates))
    if complete_candidates:
        print("PACKAGE_STATE=COMPLETE_CANDIDATE_NOT_SCIENTIFICALLY_VALIDATED")
    elif related:
        print("PACKAGE_STATE=PARTIAL_OR_INCOMPLETE")
    else:
        print("PACKAGE_STATE=NONE")

selection = package.DEFAULT_SELECTION
try:
    actual_selection = sha256_file(selection)
    if actual_selection == package.EXPECTED_SELECTION_SHA256:
        ok("SELECTION_SHA256", actual_selection)
    else:
        fail("SELECTION_SHA256", actual_selection)
except OSError as exc:
    fail("SELECTION", str(exc))

if failures:
    print("INVARIANTS=FAIL")
    print("FAILED_CHECKS=" + json.dumps(failures))
    print("NEXT=STOP_AND_RECONCILE")
    raise SystemExit(1)

print("INVARIANTS=PASS")
if RECOVERY2.exists() or RECOVERY2.is_symlink():
    print("NEXT=DO_NOT_RUN_RECOVER2_PACK; INSPECT_EXISTING_PACKAGE_STATE")
else:
    print("NEXT=ONE_SHOT_REMAINS_UNSPENT; EXPLICIT_APPROVAL_STILL_REQUIRED")
PY
