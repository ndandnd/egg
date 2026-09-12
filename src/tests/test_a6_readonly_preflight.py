"""Synthetic-only coverage of the production preflight body and shell startup.

No solver, real run tree, claim creation API, packager operation, or Slurm
connection is used. Constants and subprocess replies are fixture inputs only;
the production launcher exposes no executable or evidence override hooks.
"""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import types
from contextlib import redirect_stdout

import pytest


SRC = Path(__file__).resolve().parents[1]
SCRIPT = SRC / "cluster/preflight_a6_recovery2_readonly.sh"
PACKAGE = SRC / "experiments/package_a6_holdout.py"
MARKER = "SYNTHETIC_PRIVATE_CONTENT"


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    src = tmp_path / "src"
    helper = src / "experiments/package_a6_holdout.py"
    helper.parent.mkdir(parents=True)
    shutil.copyfile(PACKAGE, helper)
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.setattr(sys, "path", list(sys.path))
    spec = importlib.util.spec_from_file_location("fixture_package", helper)
    package = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(package)
    root = src / "runs/a6_holdout"
    root.mkdir(parents=True)
    (root / "synthetic.txt").write_text("synthetic fixture only\n")
    snapshot = package.snapshot_source(root)
    tree = package.canonical_tree_sha256(snapshot)
    code = "a" * 40
    closeout = {
        "source": {"canonical_tree_sha256": tree, **{key: snapshot[key] for key in
                   ("file_count", "directory_count", "total_bytes")}},
        "launch_job_id": "123", "preflight_sha256": "b" * 64,
        "packaging_code_commit": package.RECOVERY_BASE_COMMIT,
        "experiment_code_commit": "c" * 40, "claimed_utc": "2026-08-20T01:00:00Z",
    }
    recovery1 = {"recovery_code_commit": package.RECOVERY2_FIRST_RECOVERY_COMMIT,
                 "claimed_utc": "2026-08-20T02:00:00Z"}
    canonical = package._canonical_json_bytes
    for filename, document in ((package.CLOSEOUT_CLAIM_FILENAME, closeout),
                               (package.RECOVERY_CLAIM_FILENAME, recovery1)):
        (root.parent / filename).write_bytes(canonical(document))
    package.RECOVERY_ORIGINAL_CLAIM_SHA256 = hashlib.sha256(canonical(closeout)).hexdigest()
    package.RECOVERY2_FIRST_RECOVERY_CLAIM_SHA256 = hashlib.sha256(canonical(recovery1)).hexdigest()
    package.RECOVERY_ORIGINAL_SOURCE_TREE_SHA256 = tree
    selection = tmp_path / "synthetic_selection.json"
    selection.write_text("{}\n")
    package.DEFAULT_SELECTION = selection
    package.EXPECTED_SELECTION_SHA256 = hashlib.sha256(selection.read_bytes()).hexdigest()
    claim = {
        "schema": package.RECOVERY2_CLAIM_SCHEMA, "campaign": "a6-holdout",
        "incident_id": package.RECOVERY2_INCIDENT_ID,
        "status": "recovery2-claimed-before-outcome-validation",
        "claimed_utc": "2026-08-20T03:00:00Z", "recovery2_code_commit": code,
        "recovery2_base_commit": package.RECOVERY2_BASE_COMMIT,
        "first_recovery_commit": package.RECOVERY2_FIRST_RECOVERY_COMMIT,
        "original_claim": {"sha256": package.RECOVERY_ORIGINAL_CLAIM_SHA256,
                           **{key: closeout[key] for key in
                              ("packaging_code_commit", "experiment_code_commit", "launch_job_id")}},
        "first_recovery_claim": {"sha256": package.RECOVERY2_FIRST_RECOVERY_CLAIM_SHA256,
                                 "recovery_code_commit": recovery1["recovery_code_commit"]},
        "raw_tree_sha256": tree, "failure_fingerprint": "synthetic incident",
    }
    experiments = types.ModuleType("experiments")
    experiments.package_a6_holdout = package
    monkeypatch.setitem(sys.modules, "experiments", experiments)
    monkeypatch.chdir(src)
    monkeypatch.setattr(sys, "argv", ["-", "/synthetic/git", "/synthetic/squeue"])
    monkeypatch.setattr(os.path, "isfile", lambda path: True)
    monkeypatch.setattr(os, "access", lambda *args: True)
    monkeypatch.setattr(subprocess, "check_output", lambda args, **kwargs:
                        "" if "status" in args else
                        code if code + "^{commit}" in args else "d" * 40)
    calls = []

    def command(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", command)
    body = SCRIPT.read_text().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]

    def run():
        output = io.StringIO()
        with redirect_stdout(output):
            try:
                exec(compile(body, str(SCRIPT), "exec"), {"__name__": "__main__"})
            except SystemExit as exc:
                status = exc.code
            else:
                status = 0
        return status, output.getvalue()

    return types.SimpleNamespace(run=run, root=root, claim=claim, code=code,
                                 package=package, calls=calls, canonical=canonical,
                                 claim_path=root.parent / package.RECOVERY2_CLAIM_FILENAME)


def assert_failure(result, spent=False):
    status, output = result
    assert status == 1
    assert "INVARIANTS=FAIL" in output
    assert "INVARIANTS=PASS" not in output
    assert "AUTHORIZATION=NONE" in output
    assert MARKER not in output
    if spent:
        assert "ONE_SHOT_STATE=SPENT" in output
        assert "ONE_SHOT_STATE=UNSPENT" not in output
        assert "OK_RECOVERY2_CODE_COMMIT=" not in output


def test_unspent_pass_is_read_only(evidence):
    def contents():
        return {str(p): p.read_bytes() for p in evidence.root.parent.rglob("*") if p.is_file()}
    before = contents()
    status, output = evidence.run()
    assert status == 0 and "INVARIANTS=PASS" in output
    assert "ONE_SHOT_STATE=UNSPENT" in output and "PACKAGE_STATE=NONE" in output
    assert before == contents()


def test_valid_spent_validates_provenance(evidence):
    evidence.claim_path.write_bytes(evidence.canonical(evidence.claim))
    status, output = evidence.run()
    assert status == 0 and "INVARIANTS=PASS" in output
    assert "ONE_SHOT_STATE=SPENT" in output
    assert f"OK_RECOVERY2_CODE_COMMIT={evidence.code}" in output
    assert "NEXT=DO_NOT_RUN_RECOVER2_PACK" in output
    assert any(args[-2:] == [evidence.package.RECOVERY2_BASE_COMMIT, evidence.code]
               for args in evidence.calls)
    assert any(args[-2:] == [evidence.code, "d" * 40] for args in evidence.calls)


@pytest.mark.parametrize("field,value", [
    ("claimed_utc", None), ("claimed_utc", "2026-02-30T03:00:00Z"),
    ("claimed_utc", "2026-08-19T03:00:00Z"), ("recovery2_code_commit", MARKER),
    ("first_recovery_claim", [MARKER]), ("original_claim", {}),
    ("campaign", MARKER), ("failure_fingerprint", 1),
])
def test_malformed_spent_never_passes_or_echoes(evidence, field, value):
    if value is None:
        del evidence.claim[field]
    else:
        evidence.claim[field] = value
    evidence.claim_path.write_bytes(evidence.canonical(evidence.claim))
    assert_failure(evidence.run(), spent=True)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_non_json_constants_are_rejected(evidence, token):
    # Replace an existing field so this detects the parser, not unknown-key checks.
    raw = evidence.canonical(evidence.claim).replace(b'"synthetic incident"', token.encode())
    evidence.claim_path.write_bytes(raw)
    assert_failure(evidence.run(), spent=True)


def test_duplicate_claim_keys_never_echo(evidence):
    evidence.claim_path.write_text('{"' + MARKER + '":1,"' + MARKER + '":2}')
    assert_failure(evidence.run(), spent=True)


def test_deeply_nested_claim_fails_with_spent_footer(evidence):
    evidence.claim_path.write_text('{"nested":' + '[' * 2000 + '0' + ']' * 2000 + '}')
    assert_failure(evidence.run(), spent=True)


def test_dangling_claim_is_spent(evidence):
    evidence.claim_path.symlink_to(evidence.root.parent / "absent")
    assert_failure(evidence.run(), spent=True)


def test_unresolved_spent_commit_fails(evidence, monkeypatch):
    evidence.claim_path.write_bytes(evidence.canonical(evidence.claim))
    def answer(args, **kwargs):
        if evidence.code + "^{commit}" in args:
            raise subprocess.CalledProcessError(1, args)
        return "" if "status" in args else evidence.code
    monkeypatch.setattr(subprocess, "check_output", answer)
    assert_failure(evidence.run(), spent=True)


def test_spent_commit_must_be_ancestor_of_head(evidence, monkeypatch):
    evidence.claim_path.write_bytes(evidence.canonical(evidence.claim))
    def command(args, **kwargs):
        if args[-2:] == [evidence.code, "d" * 40]:
            raise subprocess.CalledProcessError(1, args)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
    monkeypatch.setattr(subprocess, "run", command)
    assert_failure(evidence.run(), spent=True)


def test_failed_queue_is_not_quiescent(evidence, monkeypatch):
    def command(args, **kwargs):
        if "--jobs" in args:
            raise subprocess.CalledProcessError(1, args)
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(subprocess, "run", command)
    assert_failure(evidence.run())


def make_package(evidence):
    path = evidence.root.parent / ("a6_holdout_packages/a6_holdout-job123-" + "b" * 12 + "-synthetic")
    path.mkdir(parents=True)
    archive = path / "synthetic.tar.gz"
    archive.write_bytes(b"synthetic opaque archive")
    for name in ("AUDIT_SUMMARY.md", "BUNDLE_MANIFEST.json"):
        (path / name).write_text("unread synthetic metadata")
    sidecar = path / "ARCHIVE.sha256"
    sidecar.write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + "  synthetic.tar.gz\n")
    return archive, sidecar


def test_valid_package_shape(evidence):
    make_package(evidence)
    status, output = evidence.run()
    assert status == 0 and "INVARIANTS=PASS" in output
    assert "PACKAGE_STATE=COMPLETE_CANDIDATE_NOT_SCIENTIFICALLY_VALIDATED" in output


@pytest.mark.parametrize("damage", ["content", "oversize", "wrong_name", "mismatch",
                                    "sidecar_symlink", "archive_symlink", "sidecar_hardlink", "fifo"])
def test_malformed_sidecar_and_archive_fail_closed(evidence, damage):
    archive, sidecar = make_package(evidence)
    if damage == "content":
        sidecar.write_text(MARKER)
    elif damage == "oversize":
        sidecar.write_bytes(b"0" * 2048)
    elif damage == "wrong_name":
        sidecar.write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + "  other.tar.gz\n")
    elif damage == "mismatch":
        sidecar.write_text("0" * 64 + "  synthetic.tar.gz\n")
    else:
        target = archive if damage == "archive_symlink" else sidecar
        external = evidence.root.parent / "synthetic_external"
        external.write_bytes(target.read_bytes())
        target.unlink()
        if damage == "sidecar_hardlink":
            os.link(external, target)
        elif damage == "fifo":
            os.mkfifo(target)
        else:
            target.symlink_to(external)
    assert_failure(evidence.run())


@pytest.mark.parametrize("entrypoint", ["documented", "direct"])
def test_exact_shell_ignores_shell_and_python_startup(tmp_path, entrypoint):
    src = tmp_path / "src"
    cluster = src / "cluster"
    cluster.mkdir(parents=True)
    (src / "experiments").mkdir()
    script = cluster / SCRIPT.name
    shutil.copyfile(SCRIPT, script)
    script.chmod(0o755)
    shutil.copyfile(PACKAGE, src / "experiments/package_a6_holdout.py")
    startup = tmp_path / "ambient"
    startup.mkdir()
    marker = tmp_path / "startup-marker"
    hook = "from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('hook ran')\n"
    (startup / "sitecustomize.py").write_text(hook)
    (startup / "usercustomize.py").write_text(hook)
    (startup / "experiments").mkdir()
    (startup / "experiments/__init__.py").write_text(hook + "raise RuntimeError('shadow package')\n")
    shell_marker = tmp_path / "shell-startup-marker"
    shell_hook = startup / "bash_env.sh"
    shell_hook.write_text("printf '%s\\n' 'synthetic hook' > " +
                          shlex.quote(str(shell_marker)) + "\n")
    env = dict(os.environ, PYTHONPATH=str(startup), BASH_ENV=str(shell_hook))
    if entrypoint == "documented":
        runbook = SRC.parent / "agentic/A6_RECOVER2_OPERATOR_RUNBOOK_20260821.md"
        commands = [shlex.split(line.strip()) for line in runbook.read_text().splitlines()
                    if line.strip().endswith("src/cluster/" + SCRIPT.name)]
        assert len(commands) == 1
        # Exercise the actual documented shell flags, changing only the fixture path.
        command = commands[0][:-1] + [str(script)]
    else:
        command = [str(script)]
    result = subprocess.run(command, cwd=tmp_path, env=env,
                            text=True, capture_output=True, timeout=20)
    assert not shell_marker.exists()
    assert not marker.exists()
    assert "MODE=READ_ONLY_OUTCOME_BLIND" in result.stdout
    assert "AUTHORIZATION=NONE" in result.stdout
    assert "ONE_SHOT_STATE=UNSPENT" in result.stdout
    assert "INVARIANTS=FAIL" in result.stdout  # no synthetic claims in this fixture
    assert "Traceback" not in result.stderr
    assert not list(tmp_path.rglob("__pycache__"))
    assert result.returncode == 1
