"""Shell-level tests for cluster/launch_b3_factor_pilot.sh.

Drives the REAL launcher with the environment-preparation block skipped
(EGG_LAUNCH_SELFTEST=1) and every cluster tool + the pilot driver replaced
by stubs that append to a single ORDERED event log, proving:

- sbatch receives --hold (the array is submitted held);
- the successful order is sbatch-held -> bind-job -> scontrol release;
- a --bind-job failure scancels the exact held job and NEVER releases it;
- a scontrol-release failure scancels the exact bound job;
- an existing JOB.json, partial cell output, or any unknown run-root file
  refuses BEFORE sbatch;
- a lone regular MANIFEST.json is reused and submitted.
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
    """Create ordered-event-log stubs; return (env, events_log, out)."""
    bind = tmp_path / "bin"
    bind.mkdir()
    events = tmp_path / "events.log"
    out = tmp_path / "out"

    _write_exec(bind / "sbatch_stub",
                f'echo "SBATCH $*" >> "{events}"\necho "77777"\n')
    _write_exec(bind / "scancel_stub",
                f'echo "SCANCEL $*" >> "{events}"\nexit 0\n')
    _write_exec(bind / "scontrol_stub",
                f'echo "RELEASE $*" >> "{events}"\nexit ${{EGG_RELEASE_RESULT:-0}}\n')
    # squeue: empty output (job left the queue) unless EGG_SQUEUE_SHOW is set
    _write_exec(bind / "squeue_stub",
                'if [[ -n "${EGG_SQUEUE_SHOW:-}" ]]; then echo "77777 held"; fi\n')
    _write_exec(bind / "sacct_stub",
                'if [[ -n "${EGG_SACCT_STATE:-}" ]]; then echo "${EGG_SACCT_STATE}"; fi\n')

    _write_exec(bind / "pilot_stub", f'''
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
        echo "BIND $2" >> "{events}"
        printf '{{"job_id":"%s"}}\\n' "$2" > "$OUT/JOB.json"; exit 0
     else exit 7; fi ;;
esac
exit 2
''')

    env = dict(os.environ)
    env.update({
        "EGG_LAUNCH_SELFTEST": "1",
        "EGG_SBATCH": str(bind / "sbatch_stub"),
        "EGG_SCANCEL": str(bind / "scancel_stub"),
        "EGG_SCONTROL": str(bind / "scontrol_stub"),
        "EGG_SQUEUE": str(bind / "squeue_stub"),
        "EGG_SACCT": str(bind / "sacct_stub"),
        "EGG_PILOT": str(bind / "pilot_stub"),
        "EGG_RUN_OUT": str(out),
        "EGG_VERIFY_SLEEP": "0",
    })
    return env, events, out


def _run(env):
    return subprocess.run(["bash", str(LAUNCHER)], env=env,
                          capture_output=True, text=True)


def _tokens(events: Path):
    if not events.exists():
        return []
    return [ln.split()[0] for ln in events.read_text().splitlines() if ln.strip()]


# --------------------------------------------------------------------------
# pre-sbatch freshness refusals (nothing submitted)
# --------------------------------------------------------------------------
def test_existing_job_json_refuses_before_sbatch(tmp_path):
    env, events, out = _stubs(tmp_path)
    out.mkdir(parents=True)
    (out / "JOB.json").write_text('{"job_id":"old"}\n')
    r = _run(env)
    assert r.returncode != 0
    assert "JOB.json already exists" in r.stderr
    assert _tokens(events) == []                 # nothing submitted


def test_partial_cell_output_refuses_before_sbatch(tmp_path):
    env, events, out = _stubs(tmp_path)
    cell = out / "S0_baseline_s0_n8_b0.01"
    cell.mkdir(parents=True)
    (cell / "a2.cg.ckpt.json").write_text("{}")
    r = _run(env)
    assert r.returncode != 0
    assert "unexpected entry" in r.stderr
    assert _tokens(events) == []


def test_unknown_run_root_file_refuses_before_sbatch(tmp_path):
    env, events, out = _stubs(tmp_path)
    out.mkdir(parents=True)
    (out / "notes.txt").write_text("stray")
    r = _run(env)
    assert r.returncode != 0
    assert "unexpected entry" in r.stderr
    assert _tokens(events) == []


def test_lone_manifest_is_reused_and_submits(tmp_path):
    env, events, out = _stubs(tmp_path)
    out.mkdir(parents=True)
    (out / "MANIFEST.json").write_text('{"schema":"b3-factor-pilot-run-v1"}\n')
    r = _run(env)
    assert r.returncode == 0, r.stderr
    assert _tokens(events) == ["SBATCH", "BIND", "RELEASE"]


# --------------------------------------------------------------------------
# submit-held -> bind -> release ordering and failure recovery
# --------------------------------------------------------------------------
def test_success_order_hold_bind_release(tmp_path):
    env, events, out = _stubs(tmp_path)
    r = _run(env)
    assert r.returncode == 0, r.stderr
    lines = events.read_text().splitlines()
    assert lines[0].startswith("SBATCH ") and "--hold" in lines[0]
    assert _tokens(events) == ["SBATCH", "BIND", "RELEASE"]
    assert "SCANCEL" not in _tokens(events)
    assert (out / "JOB.json").exists()


def test_bind_failure_scancels_and_never_releases(tmp_path):
    env, events, out = _stubs(tmp_path)
    env["EGG_BIND_RESULT"] = "1"
    r = _run(env)
    assert r.returncode != 0
    toks = _tokens(events)
    assert toks == ["SBATCH", "SCANCEL"]         # bound? no; released? never
    assert "RELEASE" not in toks
    # scancel targeted exactly the returned job id
    scancel_line = [ln for ln in events.read_text().splitlines()
                    if ln.startswith("SCANCEL")][0]
    assert scancel_line.split()[-1] == "77777"
    assert "never releasing" in r.stderr
    assert (out / "MANIFEST.json").exists()
    assert not (out / "JOB.json").exists()


def test_bind_failure_unconfirmed_cancel_prints_critical(tmp_path):
    env, events, out = _stubs(tmp_path)
    env["EGG_BIND_RESULT"] = "1"
    env["EGG_SQUEUE_SHOW"] = "1"                  # job still shows in queue
    # sacct reports no CANCELLED state -> cancellation cannot be confirmed
    r = _run(env)
    assert r.returncode != 0
    assert "CRITICAL" in r.stderr and "77777" in r.stderr
    assert "remains HELD" in r.stderr
    assert "RELEASE" not in _tokens(events)       # never released


def test_release_failure_scancels_bound_job(tmp_path):
    env, events, out = _stubs(tmp_path)
    env["EGG_RELEASE_RESULT"] = "1"              # scontrol release fails
    r = _run(env)
    assert r.returncode != 0
    assert _tokens(events) == ["SBATCH", "BIND", "RELEASE", "SCANCEL"]
    scancel_line = [ln for ln in events.read_text().splitlines()
                    if ln.startswith("SCANCEL")][0]
    assert scancel_line.split()[-1] == "77777"
    assert (out / "JOB.json").exists()           # bound; preserved as evidence
    assert (out / "MANIFEST.json").exists()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
