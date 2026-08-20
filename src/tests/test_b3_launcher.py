"""Shell-level tests for cluster/launch_b3_factor_pilot.sh.

Drives the REAL launcher with the environment-preparation block skipped
(EGG_LAUNCH_SELFTEST=1) and every cluster tool + the pilot driver replaced
by recording stubs, proving:

- an existing JOB.json refuses before sbatch;
- partial cell output refuses before sbatch;
- a --bind-job failure scancels exactly the returned job id, then exits
  nonzero (never leaving an unbound live array);
- a successful binding submits exactly once and never calls scancel.
"""
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "src" / "cluster" / "launch_b3_factor_pilot.sh"


def _write_exec(path: Path, body: str) -> None:
    path.write_text("#!/bin/bash\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _stubs(tmp_path: Path):
    """Create recording stubs; return (env, sbatch_log, scancel_log)."""
    bind = tmp_path / "bin"
    bind.mkdir()
    sbatch_log = tmp_path / "sbatch.log"
    scancel_log = tmp_path / "scancel.log"
    out = tmp_path / "out"

    sbatch = bind / "sbatch_stub"
    _write_exec(sbatch, f'echo "$@" >> "{sbatch_log}"\necho "77777"\n')
    scancel = bind / "scancel_stub"
    _write_exec(scancel, f'echo "$@" >> "{scancel_log}"\nexit 0\n')
    squeue = bind / "squeue_stub"
    _write_exec(squeue, 'exit 0\n')            # prints nothing -> left queue
    sacct = bind / "sacct_stub"
    _write_exec(sacct, 'echo CANCELLED\n')

    pilot = bind / "pilot_stub"
    _write_exec(pilot, f'''
sub="$1"
OUT=""
args=("$@")
for ((i=0;i<${{#args[@]}};i++)); do
    if [[ "${{args[$i]}}" == "--out" ]]; then OUT="${{args[$((i+1))]}}"; fi
done
case "$sub" in
  --dry-run) echo "[dry-run] OK"; exit 0 ;;
  --list) for k in $(seq 0 59); do echo "$k {{}}"; done; echo "total: 60 cells"; exit 0 ;;
  --emit-run-manifest)
     mkdir -p "$OUT"
     printf '{{"schema":"b3-factor-pilot-run-v1"}}\\n' > "$OUT/MANIFEST.json"
     echo "RUN_MANIFEST=$OUT/MANIFEST.json"
     echo "RUN_MANIFEST_SHA256=deadbeefdeadbeef"
     echo "RUN_COMMIT=abcabcabc"
     exit 0 ;;
  --bind-job)
     if [[ "${{EGG_BIND_RESULT:-0}} " == "0 " ]]; then
        printf '{{"job_id":"%s"}}\\n' "$2" > "$OUT/JOB.json"; exit 0
     else exit 7; fi ;;
esac
exit 2
''')

    env = dict(os.environ)
    env.update({
        "EGG_LAUNCH_SELFTEST": "1",
        "EGG_SBATCH": str(sbatch),
        "EGG_SCANCEL": str(scancel),
        "EGG_SQUEUE": str(squeue),
        "EGG_SACCT": str(sacct),
        "EGG_PILOT": str(pilot),
        "EGG_RUN_OUT": str(out),
    })
    return env, sbatch_log, scancel_log, out


def _run(env):
    return subprocess.run(["bash", str(LAUNCHER)], env=env,
                          capture_output=True, text=True)


def test_existing_job_json_refuses_before_sbatch(tmp_path):
    env, sbatch_log, scancel_log, out = _stubs(tmp_path)
    out.mkdir(parents=True)
    (out / "JOB.json").write_text('{"job_id":"old"}\n')
    r = _run(env)
    assert r.returncode != 0
    assert "JOB.json already exists" in r.stderr
    assert not sbatch_log.exists()            # sbatch never called
    assert not scancel_log.exists()


def test_partial_cell_output_refuses_before_sbatch(tmp_path):
    env, sbatch_log, scancel_log, out = _stubs(tmp_path)
    cell = out / "S0_baseline_s0_n8_b0.01"
    cell.mkdir(parents=True)
    (cell / "a2.cg.ckpt.json").write_text("{}")
    r = _run(env)
    assert r.returncode != 0
    assert "partial/result-bearing state" in r.stderr
    assert not sbatch_log.exists()


def test_lone_manifest_is_reused_and_submits(tmp_path):
    env, sbatch_log, scancel_log, out = _stubs(tmp_path)
    out.mkdir(parents=True)
    (out / "MANIFEST.json").write_text('{"schema":"b3-factor-pilot-run-v1"}\n')
    r = _run(env)
    assert r.returncode == 0, r.stderr
    assert sbatch_log.read_text().count("\n") == 1   # submitted exactly once
    assert not scancel_log.exists()


def test_bind_failure_scancels_exact_job_and_fails(tmp_path):
    env, sbatch_log, scancel_log, out = _stubs(tmp_path)
    env["EGG_BIND_RESULT"] = "1"
    r = _run(env)
    assert r.returncode != 0
    assert sbatch_log.read_text().count("\n") == 1   # submitted exactly once
    assert scancel_log.exists()
    assert scancel_log.read_text().strip() == "77777"  # cancelled exact job
    assert "cancelling the newly submitted job" in r.stderr
    assert "incident evidence" in r.stderr
    assert (out / "MANIFEST.json").exists()          # preserved as evidence
    assert not (out / "JOB.json").exists()           # never bound


def test_successful_binding_submits_once_no_scancel(tmp_path):
    env, sbatch_log, scancel_log, out = _stubs(tmp_path)
    env["EGG_BIND_RESULT"] = "0"
    r = _run(env)
    assert r.returncode == 0, r.stderr
    assert sbatch_log.read_text().count("\n") == 1   # submitted exactly once
    assert not scancel_log.exists()                  # no cancellation
    assert (out / "JOB.json").exists()               # bound


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
