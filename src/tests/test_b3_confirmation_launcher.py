"""Shell-level tests for the B3 confirmation launcher and submit file.

Cover CRITICAL 2 (env hooks only under self-test, refused when a real sbatch
exists; pre-release MANIFEST/JOB assertions) and CRITICAL 3 (the .sub threads
EGG_RUN_OUT to the worker). No cluster, no Gurobi.
"""
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "src" / "cluster" / "launch_b3_confirmation.sh"
SUBMIT = REPO_ROOT / "src" / "cluster" / "submit_b3_confirmation.sub"


def _exec(path: Path, body: str) -> None:
    path.write_text("#!/bin/bash\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _stubs(tmp_path):
    bind = tmp_path / "bin"; bind.mkdir()
    events = tmp_path / "events.log"
    out = tmp_path / "out"
    sel = tmp_path / "SELECTION.json"; sel.write_text('{"state":"GO"}\n')
    _exec(bind / "sbatch", f'echo "SBATCH $*" >> "{events}"\necho "77777"\n')
    _exec(bind / "scancel", f'echo "SCANCEL $*" >> "{events}"\nexit 0\n')
    _exec(bind / "scontrol", f'echo "RELEASE $*" >> "{events}"\nexit 0\n')
    _exec(bind / "squeue", 'exit 0\n')
    _exec(bind / "sacct", 'echo CANCELLED\n')
    sha_helper = ("python3 -c \"import hashlib,sys;"
                  "print(hashlib.sha256(open(sys.argv[1],'rb').read())"
                  ".hexdigest())\"")
    _exec(bind / "pilot", f'''
args=("$@"); mode=""; JOB=""; OUT=""
for ((i=0;i<${{#args[@]}};i++)); do
  a="${{args[$i]}}"
  case "$a" in
    --dry-run) mode=dry;;
    --list) mode=list;;
    --emit-run-manifest) mode=emit;;
    --bind-job) mode=bind; JOB="${{args[$((i+1))]}}";;
    --out) OUT="${{args[$((i+1))]}}";;
  esac
done
case "$mode" in
  dry) echo "[dry-run] OK"; exit 0;;
  list) echo "total: 48 cells"; exit 0;;
  emit) mkdir -p "$OUT"; printf '{{"schema":"m"}}\\n' > "$OUT/MANIFEST.json"
        SHA=$({sha_helper} "$OUT/MANIFEST.json")
        echo "RUN_MANIFEST=$OUT/MANIFEST.json"; echo "RUN_MANIFEST_SHA256=$SHA"
        echo "RUN_COMMIT=abc"; echo "SELECTED_FACTOR=S1_batt_low"; exit 0;;
  bind) SHA=$({sha_helper} "$OUT/MANIFEST.json")
        if [[ "${{EGG_BAD_BIND:-}}" == "1" ]]; then JOB="0"; fi
        printf '{{"schema":"b3-confirmation-job-v1","job_id":"%s","run_manifest_sha256":"%s"}}\\n' "$JOB" "$SHA" > "$OUT/JOB.json"
        exit 0;;
esac
exit 2
''')
    marker = tmp_path / "selftest.marker"
    marker.write_text("permitted\n")
    env = dict(os.environ)
    # scrub any inherited scheduler signals from the harness environment
    for _v in ("SLURM_CONF", "SLURM_CLUSTER_NAME", "SLURMD_NODENAME",
               "SLURM_JOB_ID"):
        env.pop(_v, None)
    env.update({
        "EGG_LAUNCH_SELFTEST": str(marker),   # positive permission marker file
        "EGG_SBATCH": str(bind / "sbatch"),
        "EGG_SCANCEL": str(bind / "scancel"),
        "EGG_SCONTROL": str(bind / "scontrol"),
        "EGG_SQUEUE": str(bind / "squeue"),
        "EGG_SACCT": str(bind / "sacct"),
        "EGG_PILOT": str(bind / "pilot"),
        "EGG_RUN_OUT": str(out),
        "EGG_VERIFY_SLEEP": "0",
        # keep PATH free of a real sbatch (dev VM has none)
    })
    return env, events, out, sel, bind


def _tokens(events: Path):
    if not events.exists():
        return []
    return [ln.split()[0] for ln in events.read_text().splitlines() if ln.strip()]


def _run(env, sel):
    return subprocess.run(["bash", str(LAUNCHER), str(sel)], env=env,
                          capture_output=True, text=True)


def test_selftest_refused_without_marker(tmp_path):
    env, events, out, sel, bind = _stubs(tmp_path)
    env["EGG_LAUNCH_SELFTEST"] = "1"      # not a marker file
    r = _run(env, sel)
    assert r.returncode != 0
    assert "must name an existing self-test permission marker" in r.stderr
    assert _tokens(events) == []


def test_selftest_refused_when_sbatch_on_path(tmp_path):
    env, events, out, sel, bind = _stubs(tmp_path)
    (bind / "sbatch_on_path").mkdir()
    _exec(bind / "sbatch_on_path" / "sbatch", 'echo 1\n')
    env["PATH"] = f"{bind / 'sbatch_on_path'}:{env['PATH']}"
    r = _run(env, sel)
    assert r.returncode != 0
    assert "a scheduler is reachable" in r.stderr
    assert _tokens(events) == []


def test_selftest_refused_when_slurm_env_present(tmp_path):
    env, events, out, sel, bind = _stubs(tmp_path)
    env["SLURM_CONF"] = "/etc/slurm/slurm.conf"     # a scheduler signal
    r = _run(env, sel)
    assert r.returncode != 0
    assert "a scheduler is reachable" in r.stderr
    assert _tokens(events) == []


def test_production_ignores_egg_pilot_hook(tmp_path):
    env, events, out, sel, bind = _stubs(tmp_path)
    del env["EGG_LAUNCH_SELFTEST"]        # production path
    # the dev environment has no real sbatch on PATH, so production refuses at
    # the sbatch check, proving EGG_PILOT/EGG_SBATCH hooks cannot carry it past
    # the guard (coreutils remain on PATH for the launcher header)
    r = _run(env, sel)
    assert r.returncode == 127
    assert "sbatch is unavailable" in r.stderr
    assert _tokens(events) == []


def test_success_flow_hold_bind_verify_release(tmp_path):
    env, events, out, sel, bind = _stubs(tmp_path)
    r = _run(env, sel)
    assert r.returncode == 0, r.stderr
    lines = events.read_text().splitlines()
    assert lines[0].startswith("SBATCH ") and "--hold" in lines[0]
    assert _tokens(events) == ["SBATCH", "RELEASE"]   # bind is the driver stub
    assert "SCANCEL" not in _tokens(events)
    assert (out / "JOB.json").exists() and (out / "MANIFEST.json").exists()


def test_prerelease_failure_cancels_and_never_releases(tmp_path):
    env, events, out, sel, bind = _stubs(tmp_path)
    env["EGG_BAD_BIND"] = "1"             # JOB.json names the wrong job id
    r = _run(env, sel)
    assert r.returncode != 0
    toks = _tokens(events)
    assert "SBATCH" in toks and "SCANCEL" in toks and "RELEASE" not in toks
    assert "pre-release verification failed" in r.stderr


def test_export_threads_run_out(tmp_path):
    env, events, out, sel, bind = _stubs(tmp_path)
    r = _run(env, sel)
    assert r.returncode == 0, r.stderr
    sbatch_line = [ln for ln in events.read_text().splitlines()
                   if ln.startswith("SBATCH")][0]
    assert f"EGG_RUN_OUT={out}" in sbatch_line


def test_submit_sub_threads_out_to_worker(tmp_path):
    """CRITICAL 3: the .sub must pass EGG_RUN_OUT to the worker (--out), not a
    hardcoded path; execute it with a stub python and assert the argv."""
    bind = tmp_path / "bin2"; bind.mkdir()
    argv_log = tmp_path / "argv.log"
    _exec(bind / "python", f'echo "$@" >> "{argv_log}"\nexit 0\n')
    fake_src = tmp_path / "fake_src"
    (fake_src / "experiments").mkdir(parents=True)
    (fake_src / "experiments" / "run_b3_confirmation.py").write_text("")
    (fake_src / "cluster").mkdir()
    (fake_src / "cluster" / "unicorn_env.sh").write_text(":\n")
    env = dict(os.environ)
    env["PATH"] = f"{bind}:{env['PATH']}"
    env["SLURM_SUBMIT_DIR"] = str(fake_src)
    env["SLURM_ARRAY_TASK_ID"] = "0"
    env["EGG_SELECTION_ARTIFACT"] = "/tmp/SEL.json"
    env["EGG_RUN_OUT"] = "/custom/confirm/out"
    r = subprocess.run(["bash", str(SUBMIT)], env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    argv = argv_log.read_text()
    assert "--out /custom/confirm/out" in argv
    assert "--selection-artifact /tmp/SEL.json" in argv


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
