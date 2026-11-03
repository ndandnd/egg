#!/usr/bin/env bash
#SBATCH --job-name=egg-route-graph-budget128-r1
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --array=0-11%4
#SBATCH --nodelist=unicorn-cpu-75
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-route-graph-budget128-r1-%A_%a.out
#SBATCH --error=egg-route-graph-budget128-r1-%A_%a.err
set -euo pipefail
EGG_WRAPPER_STARTED=${SECONDS}
EGG_RECEIPT_PYTHON=${EGG_RECEIPT_PYTHON:-$(command -v python3)}
EGG_WRAPPER_PHASE=guards
EGG_WRAPPER_COMPLETE=0
export EGG_EXECUTED_WRAPPER="${BASH_SOURCE[0]}"
# Standard-library receipt trap precedes profile/source/runtime guards.
egg_v8_receipt() {
  local egg_v8_rc=$?
  # Incomplete guards/profile/probe execution can never report success.
  # Preserve genuine native/profile nonzero exit codes exactly.
  if test "${egg_v8_rc}" -eq 0 && test "${EGG_WRAPPER_COMPLETE}" -ne 1; then egg_v8_rc=1; fi
  trap - EXIT
  set +e
  "${EGG_RECEIPT_PYTHON}" - "${egg_v8_rc}" "$((SECONDS-EGG_WRAPPER_STARTED))" \
    "${EGG_PROBE_RECEIPT:-}" "${EGG_WRAPPER_PHASE}" "${EGG_WRAPPER_COMPLETE}" <<'PY_RECEIPT'
import hashlib, json, os, sys
from pathlib import Path
repository = Path(os.environ.get('SLURM_SUBMIT_DIR', '.'))
root = repository / 'result/physical_learning/20261001-route-model128-graph-budget-v8-recovery1'
root.mkdir(parents=True, exist_ok=True)
task = os.environ.get('SLURM_ARRAY_TASK_ID', 'unknown')
task_name = f'task{int(task):02d}' if task.isdigit() else 'taskunknown'
probe = Path(sys.argv[3]) if sys.argv[3] else None
path = root / f'{task_name}.slurm_wrapper_receipt.{os.environ.get("SLURM_JOB_ID", "unknown")}.json'
source_files = (
    'src/cluster/physical_route_graph_budget_v8_recovery1.sbatch',
    'src/tests/test_physical_route_graph_budget_v8_recovery1.py',
    'research-20260930/learning-campaign/ROUTE_MODEL_GRAPH_BUDGET_V8_RECOVERY1_PROTOCOL.md',
    'src/cluster/physical_route_graph_budget_v8.sbatch',
    'src/experiments/train_physical_route_graph_budget_v8.py',
    'src/egglab/physical_route_graph_budget_v8.py',
    'research-20260930/learning-campaign/LAUNCH_729522.json',
)
source_hashes = {name: hashlib.sha256((repository/name).read_bytes()).hexdigest()
                 if (repository/name).is_file() else None for name in source_files}
executed = Path(os.environ.get('EGG_EXECUTED_WRAPPER', ''))
with path.open('x') as stream:
    json.dump({'task_id': int(task) if task.isdigit() else task,
        'job_id': os.environ.get('SLURM_JOB_ID'), 'array_job_id': os.environ.get('SLURM_ARRAY_JOB_ID'),
        'returncode': int(sys.argv[1]), 'elapsed_seconds': int(sys.argv[2]),
        'timeout_exit': int(sys.argv[1]) in (124, 137),
        'signal_exit': int(sys.argv[1])-128 if int(sys.argv[1]) > 128 else None,
        'wrapper_phase': sys.argv[4], 'wrapper_completed': sys.argv[5] == '1',
        'attempt': 'manual-recovery1-after-profile-startup-failure',
        'scientific_policy': 'unchanged-v8-fresh-fits', 'source_hashes': source_hashes,
        'executed_wrapper_sha256': hashlib.sha256(executed.read_bytes()).hexdigest() if executed.is_file() else None,
        'original_failed_array': '729522', 'source_commit': os.environ.get('EGG_RUN_COMMIT'),
        'pool_manifest_sha256': os.environ.get('EGG_POOL_MANIFEST_SHA256'),
        'runtime_probe_path': str(probe) if probe else None,
        'runtime_probe_sha256': hashlib.sha256(probe.read_bytes()).hexdigest() if probe and probe.exists() else None,
        'hostname': os.uname().nodename, 'graph_python': os.environ.get('EGG_GRAPH_PYTHON'),
        'requested_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
        'allocated_job_cpus': os.environ.get('SLURM_JOB_CPUS_PER_NODE'),
        'allocated_memory': os.environ.get('SLURM_MEM_PER_NODE'), 'native_threads': 1},
        stream, indent=2, sort_keys=True)
    stream.write('\n')
PY_RECEIPT
  exit "${egg_v8_rc}"
}
trap egg_v8_receipt EXIT
EGG_WRAPPER_PHASE=system_profile
if test -f /etc/profile.d/slurm.sh; then
  # Site profiles can read optional variables such as INCLUDE. Match ordinary
  # shell sourcing for unset variables without modifying the site's profile.
  set +u
  source /etc/profile.d/slurm.sh
  set -euo pipefail
fi
EGG_WRAPPER_PHASE=guards
egg_v8_require() {
  if test -z "$1"; then echo "Missing required $2" >&2; exit 2; fi
}
egg_v8_require "${SLURM_ARRAY_TASK_ID:-}" SLURM_ARRAY_TASK_ID
egg_v8_require "${SLURM_SUBMIT_DIR:-}" SLURM_SUBMIT_DIR
egg_v8_require "${SLURM_JOB_ID:-}" SLURM_JOB_ID
egg_v8_require "${SLURM_ARRAY_JOB_ID:-}" SLURM_ARRAY_JOB_ID
egg_v8_require "${EGG_RUN_COMMIT:-}" EGG_RUN_COMMIT
egg_v8_require "${EGG_POOL_MANIFEST_SHA256:-}" EGG_POOL_MANIFEST_SHA256
egg_v8_require "${EGG_GRAPH_PYTHON:-}" EGG_GRAPH_PYTHON
case "${SLURM_ARRAY_TASK_ID}" in
  0|1|2|3|4|5|6|7|8|9|10|11) ;;
  *) echo "Undeclared graph task" >&2; exit 2;;
esac
test "${SLURM_CPUS_PER_TASK:-}" = 1
test "${SLURMD_NODENAME:-}" = unicorn-cpu-75
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
test -x "${EGG_GRAPH_PYTHON}"
export PYTHONNOUSERSITE=1 PYTHONPATH=src
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 LOKY_MAX_CPU_COUNT=1
EGG_GRAPH_RESULT=result/physical_learning/20261001-route-model128-graph-budget-v8-recovery1
mkdir -p "${EGG_GRAPH_RESULT}"
# One attempt per declared task in this new root, including startup failures.
# Mark it before any native probe or bank read; no automatic retry or resume.
"${EGG_RECEIPT_PYTHON}" - "${EGG_GRAPH_RESULT}" "${SLURM_ARRAY_TASK_ID}" <<'PY_ATTEMPT'
import json, os, sys
from pathlib import Path
root, task = Path(sys.argv[1]), int(sys.argv[2])
name = f'task{task:02d}'
if (root/name).exists() or list(root.glob(f'{name}.slurm_wrapper_receipt.*.json')):
    raise ValueError('Immutable recovery1 task evidence already exists; no retry')
with (root/f'{name}.recovery1_attempt.json').open('x') as stream:
    json.dump({'attempt': 'recovery1', 'task_id': task,
               'array_job_id': os.environ['SLURM_ARRAY_JOB_ID'],
               'job_id': os.environ['SLURM_JOB_ID'],
               'source_commit': os.environ['EGG_RUN_COMMIT']}, stream, sort_keys=True)
    stream.write('\n')
PY_ATTEMPT
EGG_PROBE_RECEIPT="${EGG_GRAPH_RESULT}/task${SLURM_ARRAY_TASK_ID}.runtime_probe.${SLURM_JOB_ID}.jsonl"
EGG_WRAPPER_PHASE=native_probe
REMAINING_SECONDS=$((3500-(SECONDS-EGG_WRAPPER_STARTED)))
if test "${REMAINING_SECONDS}" -le 0; then exit 124; fi
set +e
# The shared3500second budget includes guards, native probes and training.
timeout --signal=TERM --kill-after=10s "${REMAINING_SECONDS}s" "${EGG_GRAPH_PYTHON}" \
  -m experiments.probe_physical_route_graph_v6 --python "${EGG_GRAPH_PYTHON}" \
  --output "${EGG_PROBE_RECEIPT}"
RC=$?
if test "${RC}" -eq 0; then
  EGG_WRAPPER_PHASE=training
  REMAINING_SECONDS=$((3500-(SECONDS-EGG_WRAPPER_STARTED)))
  if test "${REMAINING_SECONDS}" -gt 0; then
    timeout --signal=TERM --kill-after=10s "${REMAINING_SECONDS}s" "${EGG_GRAPH_PYTHON}" \
      -m experiments.train_physical_route_graph_budget_v8 --task-id "${SLURM_ARRAY_TASK_ID}" \
      --pool-manifest-sha256 "${EGG_POOL_MANIFEST_SHA256}" --output-root "${EGG_GRAPH_RESULT}"
    RC=$?
  else
    RC=124
  fi
fi
set -e
if test "${RC}" -eq 0; then EGG_WRAPPER_COMPLETE=1; fi
exit "${RC}"
