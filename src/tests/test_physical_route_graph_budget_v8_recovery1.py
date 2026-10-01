"""Bash startup fixtures only: fake profile/commands, no graph fit or probe."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

import pytest


WRAPPER = Path(__file__).resolve().parents[1]/"cluster/physical_route_graph_budget_v8_recovery1.sbatch"
OUTPUT = "result/physical_learning/20261001-route-model128-graph-budget-v8-recovery1"


def executable(path, text):
    path.write_text(text)
    path.chmod(0o755)


def fixture_wrapper(tmp_path, profile=None):
    repo = tmp_path/"repository"; repo.mkdir()
    binaries = tmp_path/"bin"; binaries.mkdir()
    log = tmp_path/"calls.log"
    profile_path = tmp_path/"site-profile.sh"
    profile_path.write_text(profile or '''# Site's optional variable is deliberately absent.
if test "$INCLUDE" = enabled; then :; fi
printf 'profile-flags=%s\\n' "$-" >> "$FIXTURE_CALL_LOG"
''')
    copied = tmp_path/"recovery-fixture.sbatch"
    # Only the test copy replaces the absolute system profile. Production has
    # no profile-path override and always uses the site-owned absolute path.
    source = WRAPPER.read_text().replace("/etc/profile.d/slurm.sh", str(profile_path))
    source = source.replace("fi\nEGG_WRAPPER_PHASE=guards", "fi\nprintf 'restored-flags=%s\\n' \"$-\" >> \"$FIXTURE_CALL_LOG\"\nEGG_WRAPPER_PHASE=guards", 1)
    copied.write_text(source)
    executable(binaries/"git", '''#!/usr/bin/env bash
if test "$1" = rev-parse; then printf 'fixture-commit\\n'; else exit 0; fi
''')
    executable(binaries/"timeout", '''#!/usr/bin/env bash
printf 'timeout=%s\\n' "$3" >> "$FIXTURE_CALL_LOG"
shift 3
exec "$@"
''')
    graph = binaries/"graph-python"
    executable(graph, '''#!/usr/bin/env bash
printf 'graph=%s\\n' "$*" >> "$FIXTURE_CALL_LOG"
if test "$2" = experiments.probe_physical_route_graph_v6; then
  while test "$#" -gt 0; do
    if test "$1" = --output; then shift; printf '{"fixture_only":true}\\n' > "$1"; break; fi
    shift
  done
  exit "${FIXTURE_PROBE_RC:-0}"
fi
exit "${FIXTURE_TRAIN_RC:-0}"
''')
    environment = os.environ.copy()
    environment.update({"PATH":str(binaries)+os.pathsep+environment["PATH"],
        "SLURM_ARRAY_TASK_ID":"0", "SLURM_SUBMIT_DIR":str(repo), "SLURM_JOB_ID":"fixture-job",
        "SLURM_ARRAY_JOB_ID":"fixture-array", "SLURM_CPUS_PER_TASK":"1",
        "SLURMD_NODENAME":"unicorn-cpu-75", "EGG_RUN_COMMIT":"fixture-commit",
        "EGG_POOL_MANIFEST_SHA256":"fixture-pool", "EGG_GRAPH_PYTHON":str(graph),
        "EGG_RECEIPT_PYTHON":sys.executable, "FIXTURE_CALL_LOG":str(log)})
    environment.pop("INCLUDE", None)
    return copied, repo, log, environment


def run(copied, repo, environment):
    child = subprocess.run(["bash",str(copied)],env=environment,text=True,capture_output=True)
    path = repo/OUTPUT/f'task00.slurm_wrapper_receipt.{environment["SLURM_JOB_ID"]}.json'
    receipt = json.loads(path.read_text())
    assert receipt["returncode"] == child.returncode
    assert receipt["elapsed_seconds"] >= 0
    assert receipt["executed_wrapper_sha256"] == hashlib.sha256(copied.read_bytes()).hexdigest()
    assert receipt["original_failed_array"] == "729522"
    return child, receipt


def test_optional_profile_variable_is_safe_and_strict_mode_restored(tmp_path):
    copied, repo, log, environment = fixture_wrapper(tmp_path)
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 0, child.stderr
    rows = log.read_text().splitlines()
    profile_flags = next(row.split("=",1)[1] for row in rows if row.startswith("profile-flags="))
    restored_flags = next(row.split("=",1)[1] for row in rows if row.startswith("restored-flags="))
    assert "u" not in profile_flags and "u" in restored_flags and "e" in restored_flags
    assert receipt["wrapper_phase"] == "training" and receipt["wrapper_completed"]
    assert receipt["runtime_probe_sha256"] is not None
    assert len([row for row in rows if row.startswith("timeout=")]) == 2
    assert all(0 < int(row.split("=",1)[1][:-1]) <= 3500 for row in rows if row.startswith("timeout="))
    training = next(row for row in rows if "train_physical_route_graph_budget_v8" in row)
    assert "--output-root " + OUTPUT in training
    assert (repo/OUTPUT/"task00.recovery1_attempt.json").exists()
    assert not (repo/"result/physical_learning/20261001-route-model128-graph-budget-v8").exists()


def test_missing_required_guard_still_exits_nonzero_with_receipt(tmp_path):
    copied, repo, log, environment = fixture_wrapper(tmp_path)
    environment.pop("EGG_RUN_COMMIT")
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 2 and "Missing required EGG_RUN_COMMIT" in child.stderr
    assert receipt["wrapper_phase"] == "guards" and receipt["runtime_probe_sha256"] is None
    assert "graph=" not in log.read_text()


def test_real_profile_failure_is_preserved_by_early_trap(tmp_path):
    copied, repo, _, environment = fixture_wrapper(tmp_path, "exit 7\n")
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 7 and receipt["wrapper_phase"] == "system_profile"
    assert receipt["runtime_probe_sha256"] is None and not receipt["wrapper_completed"]


def test_premature_profile_success_cannot_mark_complete_wrapper(tmp_path):
    copied, repo, _, environment = fixture_wrapper(tmp_path, "exit 0\n")
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 1 and receipt["wrapper_phase"] == "system_profile"


@pytest.mark.parametrize("code,signal,timeout", [(132,4,False),(124,None,True),(137,9,True)])
def test_native_probe_and_timeout_exit_codes_propagate_without_training(tmp_path,code,signal,timeout):
    copied, repo, log, environment = fixture_wrapper(tmp_path)
    environment["FIXTURE_PROBE_RC"] = str(code)
    child, receipt = run(copied, repo, environment)
    assert child.returncode == code and receipt["signal_exit"] == signal and not receipt["wrapper_completed"]
    assert receipt["timeout_exit"] is timeout and receipt["wrapper_phase"] == "native_probe"
    assert "train_physical_route_graph_budget_v8" not in log.read_text()


def test_training_exit_is_preserved_and_attempt_is_never_reused(tmp_path):
    copied, repo, log, environment = fixture_wrapper(tmp_path)
    environment["FIXTURE_TRAIN_RC"] = "5"
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 5 and receipt["wrapper_phase"] == "training"
    graph_call_count = log.read_text().count("graph=")
    environment["SLURM_JOB_ID"] = "second-job"
    repeated, repeated_receipt = run(copied, repo, environment)
    assert repeated.returncode != 0 and repeated_receipt["wrapper_phase"] == "guards"
    assert "Immutable recovery1 task evidence" in repeated.stderr
    assert log.read_text().count("graph=") == graph_call_count


def test_prospective_scheduler_budget_is_fixed_and_syntax_valid():
    text = WRAPPER.read_text()
    for directive in ("--cpus-per-task=1", "--mem=8G", "--time=01:00:00", "--array=0-11%4",
                      "--nodelist=unicorn-cpu-75", "--exclude=scaglione-compute-01", "--no-requeue"):
        assert "#SBATCH " + directive in text
    assert "3500-(SECONDS-EGG_WRAPPER_STARTED)" in text
    assert "--output-root" in text and "EGG_WRAPPER_COMPLETE=1" in text
    assert subprocess.run(["bash","-n",str(WRAPPER)],capture_output=True).returncode == 0
