#!/usr/bin/env bash
#SBATCH --job-name=egg-route-graph128
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --array=0-11%4
#SBATCH --nodelist=unicorn-cpu-75
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-route-graph128-%A_%a.out
#SBATCH --error=egg-route-graph128-%A_%a.err
if test -f /etc/profile.d/slurm.sh; then source /etc/profile.d/slurm.sh; fi
set -euo pipefail
: "${SLURM_ARRAY_TASK_ID:?Run only in declared array}"
: "${SLURM_SUBMIT_DIR:?Missing checkout}"
: "${EGG_RUN_COMMIT:?Pin reviewed source commit}"
: "${EGG_POOL_MANIFEST_SHA256:?Pin immutable exact128 pool}"
: "${EGG_GRAPH_PYTHON:?Pin isolated CPU torch interpreter}"
case "${SLURM_ARRAY_TASK_ID}" in
  0|1|2|3|4|5|6|7|8|9|10|11) ;;
  *) echo "Undeclared graph task" >&2; exit 2;;
esac
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
test -x "${EGG_GRAPH_PYTHON}"
export PYTHONNOUSERSITE=1 PYTHONPATH=src
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 LOKY_MAX_CPU_COUNT=1
EGG_GRAPH_RESULT=result/physical_learning/20260930-route-model128-graph-v6
mkdir -p "${EGG_GRAPH_RESULT}"
EGG_PROBE_RECEIPT="${EGG_GRAPH_RESULT}/task${SLURM_ARRAY_TASK_ID}.runtime_probe.${SLURM_JOB_ID}.jsonl"
START_SECONDS=${SECONDS}
set +e
# The supervisor imports only stdlib; native imports occur in isolated stages.
timeout --signal=TERM --kill-after=10s 1700s "${EGG_GRAPH_PYTHON}" \
  -m experiments.probe_physical_route_graph_v6 --python "${EGG_GRAPH_PYTHON}" \
  --output "${EGG_PROBE_RECEIPT}"
RC=$?
if test "${RC}" -eq 0; then
  REMAINING_SECONDS=$((1700-(SECONDS-START_SECONDS)))
  if test "${REMAINING_SECONDS}" -gt 0; then
    timeout --signal=TERM --kill-after=10s "${REMAINING_SECONDS}s" "${EGG_GRAPH_PYTHON}" \
      -m experiments.train_physical_route_graph_v6 --task-id "${SLURM_ARRAY_TASK_ID}" \
      --pool-manifest-sha256 "${EGG_POOL_MANIFEST_SHA256}"
    RC=$?
  else
    RC=124
  fi
fi
set -e
ELAPSED=$((SECONDS-START_SECONDS))
"${EGG_GRAPH_PYTHON}" - "${RC}" "${ELAPSED}" "${EGG_PROBE_RECEIPT}" <<'PY_RECEIPT'
import hashlib, json, os, sys
from pathlib import Path
root = Path(os.environ['SLURM_SUBMIT_DIR']) / 'result/physical_learning/20260930-route-model128-graph-v6'
root.mkdir(parents=True, exist_ok=True)
task = int(os.environ['SLURM_ARRAY_TASK_ID'])
probe = Path(sys.argv[3])
path = root / f'task{task:02d}.slurm_wrapper_receipt.{os.environ["SLURM_JOB_ID"]}.json'
with path.open('x') as stream:
    json.dump({'task_id': task, 'job_id': os.environ['SLURM_JOB_ID'],
        'array_job_id': os.environ.get('SLURM_ARRAY_JOB_ID'),
        'returncode': int(sys.argv[1]), 'elapsed_seconds': int(sys.argv[2]),
        'timeout_exit': int(sys.argv[1]) in (124, 137),
        'pool_manifest_sha256': os.environ['EGG_POOL_MANIFEST_SHA256'],
        'runtime_probe_path': str(probe),
        'runtime_probe_sha256': hashlib.sha256(probe.read_bytes()).hexdigest() if probe.exists() else None,
        'hostname': os.uname().nodename,
        'requested_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
        'allocated_job_cpus': os.environ.get('SLURM_JOB_CPUS_PER_NODE'),
        'allocated_memory': os.environ.get('SLURM_MEM_PER_NODE')}, stream, indent=2, sort_keys=True)
    stream.write('\n')
PY_RECEIPT
exit "${RC}"
