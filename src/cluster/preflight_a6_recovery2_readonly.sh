#!/bin/bash -p
# Outcome-blind, read-only inspection of the Unicorn A6 recovery2 state.
# This script never creates a claim or package and never runs the analyzer.
# Invoke directly or with /bin/bash -p; plain bash processes BASH_ENV before us.

set -uo pipefail

script_path="${BASH_SOURCE[0]}"
script_parent="${script_path%/*}"
if test "$script_parent" = "$script_path"; then
    script_parent=.
fi
script_dir="$(CDPATH= cd -- "$script_parent" && pwd -P)" || exit 1
src_dir="$(CDPATH= cd -- "${script_dir}/.." && pwd -P)" || exit 1
cd "$src_dir" || exit 1

egg_python=/usr/bin/python3
egg_git=/usr/bin/git
egg_squeue=/usr/local/slurm/current/bin/squeue

if test ! -x "$egg_python"; then
    printf 'INVARIANT_FAIL=trusted Python is unavailable: %s\n' "$egg_python"
    exit 1
fi

# Ignore ambient Python configuration, site hooks and bytecode writes.
# The package helper imports only the standard library on this read-only path.
exec "$egg_python" -I -S -B - "$egg_git" "$egg_squeue" <<'PY'
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

# Isolated startup deliberately omits cwd. Add only the script-derived src root
# after loading standard-library dependencies; never use PYTHONPATH/site hooks.
sys.path.insert(0, str(Path.cwd()))
from experiments import package_a6_holdout as package

if Path(package.__file__).resolve() != Path.cwd() / "experiments/package_a6_holdout.py":
    raise RuntimeError("unexpected package helper location")


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


def open_regular(path: Path):
    # Reject symlinks and special files before opening (a FIFO must not block).
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("not a regular single-link file")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("not a regular single-link file")
        return os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise


def bounded_bytes(path: Path, limit: int) -> bytes:
    with open_regular(path) as handle:
        if os.fstat(handle.fileno()).st_size > limit:
            raise ValueError("metadata exceeds size limit")
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("metadata exceeds size limit")
    return raw


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open_regular(path) as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reject_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def reject_json_constant(value):
    raise ValueError("non-JSON numeric constant")


def strict_claim(path: Path, expected_sha256: str | None = None) -> tuple[bytes, dict]:
    raw = bounded_bytes(path, 1 << 20)
    actual = sha256_bytes(raw)
    if expected_sha256 is not None and actual != expected_sha256:
        raise ValueError("claim checksum mismatch")
    document = json.loads(raw, object_pairs_hook=reject_duplicate_keys,
                          parse_constant=reject_json_constant)
    if not isinstance(document, dict):
        raise ValueError("top-level JSON value is not an object")
    if raw != package._canonical_json_bytes(document):
        raise ValueError("JSON is not canonical")
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

head = None
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
    except (OSError, ValueError, RecursionError) as exc:
        fail(label, type(exc).__name__)

# Presence consumes the attempt even if the document is malformed or a dangling
# symlink. Validation must never downgrade this state to UNSPENT.
spent = RECOVERY2.exists() or RECOVERY2.is_symlink()
if spent:
    print("ONE_SHOT_STATE=SPENT")
    try:
        raw, recovery2 = strict_claim(RECOVERY2)
        ok("RECOVERY2_CLAIM_SHA256", sha256_bytes(raw))
        expected_keys = {
            "schema", "campaign", "incident_id", "status", "claimed_utc",
            "recovery2_code_commit", "recovery2_base_commit",
            "first_recovery_commit", "original_claim", "first_recovery_claim",
            "raw_tree_sha256", "failure_fingerprint",
        }
        if set(recovery2) != expected_keys:
            raise ValueError("invalid recovery2 claim fields")
        expected_values = {
            "schema": package.RECOVERY2_CLAIM_SCHEMA,
            "campaign": "a6-holdout",
            "incident_id": package.RECOVERY2_INCIDENT_ID,
            "status": "recovery2-claimed-before-outcome-validation",
            "recovery2_base_commit": package.RECOVERY2_BASE_COMMIT,
            "first_recovery_commit": package.RECOVERY2_FIRST_RECOVERY_COMMIT,
            "raw_tree_sha256": package.RECOVERY_ORIGINAL_SOURCE_TREE_SHA256,
        }
        if any(recovery2[key] != value for key, value in expected_values.items()):
            raise ValueError("invalid recovery2 claim bindings")
        if closeout is None or recovery1 is None:
            raise ValueError("prior claim unavailable")
        if recovery2["original_claim"] != {
            "sha256": package.RECOVERY_ORIGINAL_CLAIM_SHA256,
            **{key: closeout[key] for key in (
                "packaging_code_commit", "experiment_code_commit", "launch_job_id")},
        } or recovery2["first_recovery_claim"] != {
            "sha256": package.RECOVERY2_FIRST_RECOVERY_CLAIM_SHA256,
            "recovery_code_commit": recovery1["recovery_code_commit"],
        }:
            raise ValueError("invalid recovery2 prior-claim bindings")
        fingerprint = recovery2["failure_fingerprint"]
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ValueError("invalid recovery2 fingerprint")
        times = []
        for claim in (closeout, recovery1, recovery2):
            timestamp = claim["claimed_utc"]
            if not isinstance(timestamp, str) or not re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", timestamp):
                raise ValueError("invalid claim timestamp")
            times.append(datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ"))
        if not times[0] <= times[1] <= times[2]:
            raise ValueError("invalid claim chronology")
        code = recovery2["recovery2_code_commit"]
        if not isinstance(code, str) or not re.fullmatch(r"[0-9a-f]{40}", code):
            raise ValueError("invalid recovery2 commit")
        if git_output("rev-parse", "--verify", code + "^{commit}") != code:
            raise ValueError("recovery2 commit does not resolve")
        for ancestor, descendant in ((package.RECOVERY2_BASE_COMMIT, code), (code, head)):
            subprocess.run(
                [GIT, "-C", str(REPO), "merge-base", "--is-ancestor", ancestor, descendant],
                env=GIT_ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=True,
            )
        ok("RECOVERY2_CODE_COMMIT", code)
        ok("RECOVERY2_CLAIMED_UTC", recovery2["claimed_utc"])
    except (OSError, ValueError, KeyError, TypeError, RecursionError, subprocess.CalledProcessError) as exc:
        # Never echo untrusted fields, keys, parse excerpts, or fingerprint text.
        fail("RECOVERY2_CLAIM", type(exc).__name__)
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
                sidecar = bounded_bytes(path / "ARCHIVE.sha256", 1024)
                # Match the exact writer contract, including this archive basename.
                match = re.fullmatch(rb"([0-9a-f]{64})  " + re.escape(
                    archives[0].encode("utf-8")) + rb"\n", sidecar)
                if match is None:
                    raise ValueError("invalid archive sidecar format")
                actual = sha256_file(archive)
                if actual == match.group(1).decode("ascii"):
                    complete_candidates.append(path.name)
                    ok("PACKAGE_ARCHIVE_SHA256", actual)
                else:
                    fail("PACKAGE_ARCHIVE_SIDECAR", "checksum mismatch")
        except (OSError, ValueError) as exc:
            fail("PACKAGE_ENTRY", type(exc).__name__)

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
except (OSError, ValueError) as exc:
    fail("SELECTION", type(exc).__name__)

if failures:
    print("INVARIANTS=FAIL")
    print("FAILED_CHECKS=" + json.dumps(failures))
    print("NEXT=STOP_AND_RECONCILE")
    raise SystemExit(1)

print("INVARIANTS=PASS")
if spent:
    print("NEXT=DO_NOT_RUN_RECOVER2_PACK; INSPECT_EXISTING_PACKAGE_STATE")
else:
    print("NEXT=ONE_SHOT_REMAINS_UNSPENT; EXPLICIT_APPROVAL_STILL_REQUIRED")
PY
