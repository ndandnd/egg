"""Bash startup fixtures only: fake profile/commands, no graph fit or probe."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys

import pytest


WRAPPER = Path(__file__).resolve().parents[1]/"cluster/physical_route_graph_context_v9.sbatch"
OUTPUT = "result/physical_learning/20261001-route-model128-graph-context-v9"


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
    copied = tmp_path/"context-fixture.sbatch"
    # Only the test copy replaces the absolute system profile. Production has
    # no profile-path override and always uses the site-owned absolute path.
    source = WRAPPER.read_text().replace("/etc/profile.d/slurm.sh", str(profile_path))
    source = source.replace("fi\nEGG_WRAPPER_PHASE=guards", "fi\nprintf 'restored-flags=%s\\n' \"$-\" >> \"$FIXTURE_CALL_LOG\"\nEGG_WRAPPER_PHASE=guards", 1)
    inventory = repo/"research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_FIT_INVENTORY.json"
    inventory.parent.mkdir(parents=True)
    feature = repo/"src/egglab/physical_context_features_v9.py"
    feature.parent.mkdir(parents=True)
    feature.write_text("# synthetic source fixture; never imported\n")
    inventory.write_text(json.dumps({"passed":True,"features":[f"feature{i}" for i in range(38)],
        "source_hashes":{"src/egglab/physical_context_features_v9.py":hashlib.sha256(feature.read_bytes()).hexdigest()}}))
    inventory_sha = hashlib.sha256(inventory.read_bytes()).hexdigest()
    # Production pin remains immutable; only this synthetic copied wrapper pin changes.
    source = source.replace('1e096c5e34edab7a142fe0afa9f43f1b5e3b24f07658894967b06f8bc3447963', inventory_sha)
    copied.write_text(source)
    executable(binaries/"squeue", """#!/usr/bin/env bash
printf 'queue=%s\\n' "$*" >> "$FIXTURE_CALL_LOG"
printf '%s' "${FIXTURE_V8_ACTIVE:-}"
exit "${FIXTURE_SQUEUE_RC:-0}"
""")
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
        "EGG_RECEIPT_PYTHON":sys.executable, "FIXTURE_CALL_LOG":str(log),
        "EGG_INPUT_INVENTORY_SHA256":inventory_sha, "EGG_PRIOR_V8_ARRAY_JOB_ID":"738226"})
    environment.pop("INCLUDE", None)
    return copied, repo, log, environment


def run(copied, repo, environment):
    child = subprocess.run(["bash",str(copied)],env=environment,text=True,capture_output=True)
    path = repo/OUTPUT/f'task00.slurm_wrapper_receipt.{environment["SLURM_JOB_ID"]}.json'
    receipt = json.loads(path.read_text())
    assert receipt["returncode"] == child.returncode
    assert receipt["elapsed_seconds"] >= 0
    assert receipt["executed_wrapper_sha256"] == hashlib.sha256(copied.read_bytes()).hexdigest()
    assert receipt["prior_v8_array_job_id"] == "738226"
    assert receipt["wrapper_budget_seconds"] == 7000 and receipt["allocated_limit_seconds"] == 7200
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
    assert all(0 < int(row.split("=",1)[1][:-1]) <= 7000 for row in rows if row.startswith("timeout="))
    training = next(row for row in rows if "train_physical_route_graph_context_v9" in row)
    assert "--output-root " + OUTPUT in training
    assert (repo/OUTPUT/"task00.v9_attempt.json").exists()
    assert not (repo/"result/physical_learning/20261001-route-model128-graph-budget-v8-recovery1").exists()


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
    assert "train_physical_route_graph_context_v9" not in log.read_text()


def test_training_exit_is_preserved_and_attempt_is_never_reused(tmp_path):
    copied, repo, log, environment = fixture_wrapper(tmp_path)
    environment["FIXTURE_TRAIN_RC"] = "5"
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 5 and receipt["wrapper_phase"] == "training"
    graph_call_count = log.read_text().count("graph=")
    environment["SLURM_JOB_ID"] = "second-job"
    repeated, repeated_receipt = run(copied, repo, environment)
    assert repeated.returncode != 0 and repeated_receipt["wrapper_phase"] == "attempt_guard"
    assert "Immutable v9 task evidence" in repeated.stderr
    assert log.read_text().count("graph=") == graph_call_count


def test_prospective_scheduler_budget_is_fixed_and_syntax_valid():
    text = WRAPPER.read_text()
    for directive in ("--cpus-per-task=1", "--mem=8G", "--time=02:00:00", "--array=0-11%4",
                      "--nodelist=unicorn-cpu-75", "--exclude=scaglione-compute-01", "--no-requeue"):
        assert "#SBATCH " + directive in text
    assert "7000-(SECONDS-EGG_WRAPPER_STARTED)" in text
    assert "--output-root" in text and "EGG_WRAPPER_COMPLETE=1" in text
    assert subprocess.run(["bash","-n",str(WRAPPER)],capture_output=True).returncode == 0


@pytest.mark.parametrize("active,query_rc", [("738226|RUNNING",0),("",1)])
def test_active_prior_v8_or_failed_query_prevents_probe_and_fit(tmp_path,active,query_rc):
    copied, repo, log, environment = fixture_wrapper(tmp_path)
    environment["FIXTURE_V8_ACTIVE"] = active
    environment["FIXTURE_SQUEUE_RC"] = str(query_rc)
    child, receipt = run(copied, repo, environment)
    assert child.returncode != 0 and receipt["wrapper_phase"] == "overlap_guard"
    assert "graph=" not in log.read_text()
    assert not (repo/OUTPUT/"task00.v9_attempt.json").exists()


@pytest.mark.parametrize("listing", ["", "882|RUNNING\n7382260|PENDING\n"])
def test_successful_user_queue_without_exact_prior_parent_allows_startup(tmp_path,listing):
    copied, repo, log, environment = fixture_wrapper(tmp_path)
    environment["FIXTURE_V8_ACTIVE"] = listing
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 0 and receipt["wrapper_completed"]
    assert receipt["prior_v8_guard_snapshot"] == ""
    query = next(row for row in log.read_text().splitlines() if row.startswith("queue="))
    assert " -u " in query and " -o %F|%T" in query and " -j " not in query


def test_only_exact_prior_rows_are_preserved_in_failed_overlap_receipt(tmp_path):
    copied, repo, _, environment = fixture_wrapper(tmp_path)
    environment["FIXTURE_V8_ACTIVE"] = "882|RUNNING\n738226|COMPLETING\n7382260|PENDING\n"
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 3 and receipt["wrapper_phase"] == "overlap_guard"
    assert receipt["prior_v8_guard_snapshot"] == "738226|COMPLETING"


def test_inventory_hash_guard_precedes_native_probe(tmp_path):
    copied, repo, log, environment = fixture_wrapper(tmp_path)
    environment["EGG_INPUT_INVENTORY_SHA256"] = "0"*64
    child, receipt = run(copied, repo, environment)
    assert child.returncode != 0 and receipt["wrapper_phase"] == "input_inventory_guard"
    assert "Pinned FIT-only physical38 inventory differs" in child.stderr
    assert "graph=" not in log.read_text()


def test_inventory_source_tamper_prevents_native_probe(tmp_path):
    copied, repo, log, environment = fixture_wrapper(tmp_path)
    (repo/"src/egglab/physical_context_features_v9.py").write_text("changed")
    child, receipt = run(copied, repo, environment)
    assert child.returncode != 0 and receipt["wrapper_phase"] == "input_inventory_guard"
    assert "Frozen inventory source changed" in child.stderr
    assert "graph=" not in log.read_text()


def test_full_startup_consumes_same_absolute_budget(tmp_path):
    copied, repo, log, environment = fixture_wrapper(tmp_path, "EGG_WRAPPER_STARTED=$((SECONDS-20))\n")
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 0
    caps = [int(row.split("=",1)[1][:-1]) for row in log.read_text().splitlines() if row.startswith("timeout=")]
    assert len(caps) == 2 and all(cap <= 6980 for cap in caps)
    assert receipt["elapsed_seconds"] >= 20


def test_startup_exhausted_budget_never_runs_native_probe(tmp_path):
    copied, repo, log, environment = fixture_wrapper(tmp_path, "EGG_WRAPPER_STARTED=$((SECONDS-7001))\n")
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 124 and receipt["timeout_exit"] and receipt["wrapper_phase"] == "native_probe"
    assert "graph=" not in log.read_text()


def test_actual_cpu_allocation_is_recorded_without_requiring_one_allocated_cpu(tmp_path):
    copied, repo, _, environment = fixture_wrapper(tmp_path)
    environment["SLURM_JOB_CPUS_PER_NODE"] = "2"
    child, receipt = run(copied, repo, environment)
    assert child.returncode == 0 and receipt["requested_cpus_per_task"] == "1" and receipt["allocated_job_cpus"] == "2"
    assert receipt["native_threads"] == 1


def test_protocol_arm_order_is_prospective_and_balanced_without_native_imports():
    policy = "physical-source-movement-graph-context-exact128-v9"
    ranked = sorted(range(12),key=lambda task:hashlib.sha256(f"{policy}:{task}".encode()).hexdigest())
    expected = [ranked.index(task)%4 for task in range(12)]
    protocol = WRAPPER.parents[2]/"research-20260930/learning-campaign/ROUTE_MODEL_GRAPH_CONTEXT_V9_PROTOCOL.md"
    rows = re.findall(r"^\| (\d+) \| (\d+) \| (17|29|43) \| (\d+) \|$",protocol.read_text(),re.M)
    assert len(rows) == 12
    assert [int(row[3]) for row in rows] == expected
    for task,fold,seed,_ in rows:
        assert int(fold) == int(task)//3 and int(seed) == (17,29,43)[int(task)%3]
    for arm in range(4):
        positions = [(arm-rotation)%4 for rotation in expected]
        assert [positions.count(position) for position in range(4)] == [3,3,3,3]
