#!/usr/bin/env python3
"""One hardened git runner for every module that makes a provenance claim.

This module deliberately imports nothing from the project so that the run
PRODUCER (``b3_factor_pilot``, ``run_b3_factor_pilot``) can use exactly the
same runner as the analyzer, selector and packager.  An earlier version lived
in ``b3_pilot_evidence``, which imports ``b3_factor_pilot`` and therefore could
not be imported by it -- so the producer kept shelling a bare ``git`` and could
record a commit that did not match the code that actually ran.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path


class ProvenanceError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# provenance: ONE hardened git runner for every module in the B3 path
# --------------------------------------------------------------------------
# Provenance must not be answerable by anything the caller controls.  A `git`
# shim earlier on PATH, an exported GIT_DIR, a repository-local replacement ref
# or a legacy graft file can each make fabricated history look real.  The
# trusted path deliberately excludes user-writable prefixes such as
# /usr/local/bin and /opt/homebrew/bin: on a single-user machine those are
# owned by the operator, so a shim placed there would be "trusted".
TRUSTED_PATH = "/usr/bin:/bin"


def trusted_git() -> str:
    exe = shutil.which("git", path=TRUSTED_PATH)
    if exe is None:                                  # pragma: no cover
        raise ProvenanceError(
            f"no git executable on the trusted path ({TRUSTED_PATH}); "
            "provenance cannot be verified")
    resolved = Path(exe)
    if resolved.is_symlink():
        raise ProvenanceError(f"trusted git must not be a symlink: {exe}")
    info = resolved.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ProvenanceError(f"trusted git is not a regular file: {exe}")
    if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise ProvenanceError(f"trusted git is group/world-writable: {exe}")
    return exe


def git_argv(repo_root, *args: str) -> list:
    """A repository-pinned, replacement-free, config-inert git invocation.

    ``core.fsmonitor`` and ``core.hooksPath`` make *verification* execute
    caller-supplied programs, so they are disabled per-invocation rather than
    trusted to be absent from a repository-local config we cannot control.
    """
    return [trusted_git(),
            "--no-replace-objects",
            "-c", "core.fsmonitor=",
            "-c", "core.hooksPath=/dev/null",
            "-c", "protocol.ext.allow=never",
            "--git-dir", str(git_dir(repo_root)),
            "--work-tree", str(repo_root), *args]


def git_env() -> dict:
    """An ALLOWLISTED environment, built from scratch.

    Scrubbing ``GIT_*`` was not enough.  On macOS ``/usr/bin/git`` is an
    ``xcrun`` dispatcher, so an inherited ``DEVELOPER_DIR`` (or ``TOOLCHAINS``
    / ``SDKROOT``) can route every query to an attacker-supplied toolchain and
    fabricate commit existence, type, ancestry, cleanliness and file content.
    Anything not named here is therefore dropped, rather than enumerating the
    routing variables we happen to know about.

    ``GIT_GRAFT_FILE`` is pinned at /dev/null because ``--no-replace-objects``
    does NOT disable legacy ``.git/info/grafts``; pinning it neutralises grafts
    for every invocation instead of racing a one-shot existence check.
    """
    return {
        "PATH": TRUSTED_PATH,
        "LC_ALL": "C",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_GRAFT_FILE": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
    }


def git_dir(repo_root):
    """The real git directory, following a linked worktree's gitfile.

    A worktree's ``.git`` is a FILE pointing elsewhere, so pinning
    ``--git-dir`` to ``<root>/.git`` silently addressed the wrong repository
    and made a graft in the common directory invisible to the guard.
    """
    candidate = Path(repo_root) / ".git"
    if candidate.is_file():
        text = candidate.read_text(encoding="utf-8", errors="strict").strip()
        prefix = "gitdir:"
        if not text.startswith(prefix):
            raise ProvenanceError(f"malformed gitfile: {candidate}")
        resolved = Path(text[len(prefix):].strip())
        if not resolved.is_absolute():
            resolved = (Path(repo_root) / resolved).resolve()
        return resolved
    return candidate


def assert_no_history_rewrites(repo_root) -> None:
    """Fail closed when the repository can misrepresent its own ancestry.

    ``git replace --graft`` makes an unrelated real commit appear ancestral
    without dirtying the tracked tree, and environment scrubbing does not
    disable repository-local ``refs/replace``.
    """
    try:
        listed = subprocess.check_output(
            git_argv(repo_root, "replace", "--list"),
            cwd=repo_root, env=git_env(),
            stderr=subprocess.DEVNULL).decode().strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        raise ProvenanceError("could not enumerate replacement refs") from exc
    if listed:
        raise ProvenanceError(
            "repository has replacement refs; provenance cannot be trusted: "
            + ", ".join(listed.split()))
    # Grafts are neutralised per-invocation via GIT_GRAFT_FILE, so this is a
    # hygiene report rather than the control.  Check the COMMON directory: a
    # linked worktree's own .git is a file and holds no info/grafts.
    try:
        common = subprocess.check_output(
            git_argv(repo_root, "rev-parse", "--git-common-dir"),
            cwd=repo_root, env=git_env(),
            stderr=subprocess.DEVNULL).decode().strip()
    except (subprocess.CalledProcessError, OSError):
        common = str(git_dir(repo_root))
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = (Path(repo_root) / common_path).resolve()
    for graft in (common_path / "info" / "grafts",
                  git_dir(repo_root) / "info" / "grafts"):
        if graft.exists():
            raise ProvenanceError(f"repository has a legacy graft file: {graft}")


