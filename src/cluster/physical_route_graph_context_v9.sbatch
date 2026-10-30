#!/usr/bin/env bash
#SBATCH --job-name=egg-route-graph-context128-v9
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --array=0-11%4
#SBATCH --nodelist=unicorn-cpu-75
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-route-graph-context128-v9-%A_%a.out
#SBATCH --error=egg-route-graph-context128-v9-%A_%a.err
set -euo pipefail
EGG_WRAPPER_STARTED=${SECONDS}
EGG_RECEIPT_PYTHON=${EGG_RECEIPT_PYTHON:-$(command -v python3)}
EGG_WRAPPER_PHASE=guards
EGG_WRAPPER_COMPLETE=0
export EGG_EXECUTED_WRAPPER="${BASH_SOURCE[0]}"
# Standard-library receipt trap precedes profile/source/runtime guards.
egg_v9_receipt() {
  local egg_v9_rc=$?
  # Incomplete guards/profile/probe execution can never report success.
  # Preserve genuine native/profile nonzero exit codes exactly.
  if test "${egg_v9_rc}" -eq 0 && test "${EGG_WRAPPER_COMPLETE}" -ne 1; then egg_v9_rc=1; fi
  trap - EXIT
  set +e
  "${EGG_RECEIPT_PYTHON}" - "${egg_v9_rc}" "$((SECONDS-EGG_WRAPPER_STARTED))" \
    "${EGG_PROBE_RECEIPT:-}" "${EGG_WRAPPER_PHASE}" "${EGG_WRAPPER_COMPLETE}" <<'PY_RECEIPT'
import hashlib, json, os, sys
from pathlib import Path
repository = Path(os.environ.get('SLURM_SUBMIT_DIR', '.'))
root = repository / 'result/physical_learning/20261001-route-model128-graph-context-v9'
root.mkdir(parents=True, exist_ok=True)
task = os.environ.get('SLURM_ARRAY_TASK_ID', 'unknown')
task_name = f'task{int(task):02d}' if task.isdigit() else 'taskunknown'
probe = Path(sys.argv[3]) if sys.argv[3] else None
path = root / f'{task_name}.slurm_wrapper_receipt.{os.environ.get("SLURM_JOB_ID", "unknown")}.json'
source_files = (
    'src/cluster/physical_route_graph_context_v9.sbatch',
    'src/tests/test_physical_route_graph_context_v9_wrapper.py',
    'research-20260930/learning-campaign/ROUTE_MODEL_GRAPH_CONTEXT_V9_PROTOCOL.md',
    'src/egglab/physical_route_graph_context_v9.py',
    'src/experiments/train_physical_route_graph_context_v9.py',
    'src/egglab/physical_context_features_v9.py',
    'src/experiments/probe_physical_route_graph_v6.py',
    'research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_FIT_INVENTORY.json',
    'src/egglab/physical_route_graph_budget_v8.py',
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
        'attempt': 'prospective-v9-fresh-matched38-input-fits',
        'scientific_policy': 'physical-source-movement-graph-context-exact128-v9', 'source_hashes': source_hashes,
        'executed_wrapper_sha256': hashlib.sha256(executed.read_bytes()).hexdigest() if executed.is_file() else None,
        'source_commit': os.environ.get('EGG_RUN_COMMIT'),
        'prior_v8_array_job_id': os.environ.get('EGG_PRIOR_V8_ARRAY_JOB_ID'),
        'prior_v8_guard_snapshot': os.environ.get('EGG_PRIOR_V8_GUARD_SNAPSHOT'),
        'input_inventory_sha256': os.environ.get('EGG_INPUT_INVENTORY_SHA256'),
        'wrapper_budget_seconds': 7000, 'allocated_limit_seconds': 7200,
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
  exit "${egg_v9_rc}"
}
trap egg_v9_receipt EXIT
EGG_WRAPPER_PHASE=system_profile
if test -f /etc/profile.d/slurm.sh; then
  # Site profiles can read optional variables such as INCLUDE. Match ordinary
  # shell sourcing for unset variables without modifying the site's profile.
  set +u
  source /etc/profile.d/slurm.sh
  set -euo pipefail
fi
EGG_WRAPPER_PHASE=guards
egg_v9_require() {
  if test -z "$1"; then echo "Missing required $2" >&2; exit 2; fi
}
egg_v9_require "${SLURM_ARRAY_TASK_ID:-}" SLURM_ARRAY_TASK_ID
egg_v9_require "${SLURM_SUBMIT_DIR:-}" SLURM_SUBMIT_DIR
egg_v9_require "${SLURM_JOB_ID:-}" SLURM_JOB_ID
egg_v9_require "${SLURM_ARRAY_JOB_ID:-}" SLURM_ARRAY_JOB_ID
egg_v9_require "${EGG_RUN_COMMIT:-}" EGG_RUN_COMMIT
egg_v9_require "${EGG_POOL_MANIFEST_SHA256:-}" EGG_POOL_MANIFEST_SHA256
egg_v9_require "${EGG_GRAPH_PYTHON:-}" EGG_GRAPH_PYTHON
egg_v9_require "${EGG_INPUT_INVENTORY_SHA256:-}" EGG_INPUT_INVENTORY_SHA256
egg_v9_require "${EGG_PRIOR_V8_ARRAY_JOB_ID:-}" EGG_PRIOR_V8_ARRAY_JOB_ID
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
EGG_WRAPPER_PHASE=overlap_guard
test "${EGG_PRIOR_V8_ARRAY_JOB_ID}" = 738226
# A completed parent ID may expire from Slurm. Query the current user's queue,
# retain only exact prior-parent rows, and fail closed on genuine query failure.
export EGG_PRIOR_V8_GUARD_SNAPSHOT
EGG_PRIOR_V8_GUARD_SNAPSHOT=$(squeue -h -u "$(id -un)" -o '%F|%T' | \
  awk -F '|' -v prior="${EGG_PRIOR_V8_ARRAY_JOB_ID}" '("id:" $1) == ("id:" prior) {print}')
if test -n "${EGG_PRIOR_V8_GUARD_SNAPSHOT}"; then
  echo "Prior v8 array738226 remains active; v9 cannot overlap" >&2
  exit 3
fi
EGG_WRAPPER_PHASE=input_inventory_guard
"${EGG_RECEIPT_PYTHON}" - <<'PY_INVENTORY'
import hashlib, json, os
from pathlib import Path
repository = Path(os.environ['SLURM_SUBMIT_DIR'])
path = repository/'research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_FIT_INVENTORY.json'
expected = '1e096c5e34edab7a142fe0afa9f43f1b5e3b24f07658894967b06f8bc3447963'
if os.environ['EGG_INPUT_INVENTORY_SHA256'] != expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
    raise ValueError('Pinned FIT-only physical38 inventory differs')
row = json.loads(path.read_text())
if row.get('passed') is not True or len(row.get('features', ())) != 38:
    raise ValueError('FIT-only physical38 inventory not passed')
for relative, digest in row['source_hashes'].items():
    source = (repository/relative).resolve()
    if not source.is_relative_to(repository.resolve()) or hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValueError('Frozen inventory source changed: '+relative)
PY_INVENTORY
EGG_WRAPPER_PHASE=attempt_guard
EGG_GRAPH_RESULT=result/physical_learning/20261001-route-model128-graph-context-v9
mkdir -p "${EGG_GRAPH_RESULT}"
# One attempt per declared task in this new root, including startup failures.
# Mark it before any native probe or bank read; no automatic retry or resume.
"${EGG_RECEIPT_PYTHON}" - "${EGG_GRAPH_RESULT}" "${SLURM_ARRAY_TASK_ID}" <<'PY_ATTEMPT'
import json, os, sys
from pathlib import Path
root, task = Path(sys.argv[1]), int(sys.argv[2])
name = f'task{task:02d}'
if (root/name).exists() or list(root.glob(f'{name}.slurm_wrapper_receipt.*.json')):
    raise ValueError('Immutable v9 task evidence already exists; no retry')
with (root/f'{name}.v9_attempt.json').open('x') as stream:
    json.dump({'attempt': 'v9-matched38', 'task_id': task,
               'array_job_id': os.environ['SLURM_ARRAY_JOB_ID'],
               'job_id': os.environ['SLURM_JOB_ID'],
               'source_commit': os.environ['EGG_RUN_COMMIT']}, stream, sort_keys=True)
    stream.write('\n')
PY_ATTEMPT
EGG_PROBE_RECEIPT="${EGG_GRAPH_RESULT}/task${SLURM_ARRAY_TASK_ID}.runtime_probe.${SLURM_JOB_ID}.jsonl"
EGG_WRAPPER_PHASE=native_probe
REMAINING_SECONDS=$((7000-(SECONDS-EGG_WRAPPER_STARTED)))
if test "${REMAINING_SECONDS}" -le 0; then exit 124; fi
set +e
# The shared7000second budget includes guards, native probes and training.
timeout --signal=TERM --kill-after=10s "${REMAINING_SECONDS}s" "${EGG_GRAPH_PYTHON}" \
  -m experiments.probe_physical_route_graph_v6 --python "${EGG_GRAPH_PYTHON}" \
  --output "${EGG_PROBE_RECEIPT}"
RC=$?
if test "${RC}" -eq 0; then
  EGG_WRAPPER_PHASE=training
  REMAINING_SECONDS=$((7000-(SECONDS-EGG_WRAPPER_STARTED)))
  if test "${REMAINING_SECONDS}" -gt 0; then
    timeout --signal=TERM --kill-after=10s "${REMAINING_SECONDS}s" "${EGG_GRAPH_PYTHON}" \
      -m experiments.train_physical_route_graph_context_v9 --task-id "${SLURM_ARRAY_TASK_ID}" \
      --pool-manifest-sha256 "${EGG_POOL_MANIFEST_SHA256}" --output-root "${EGG_GRAPH_RESULT}"
    RC=$?
  else
    RC=124
  fi
fi
set -e
if test "${RC}" -eq 0; then EGG_WRAPPER_COMPLETE=1; fi
exit "${RC}"
