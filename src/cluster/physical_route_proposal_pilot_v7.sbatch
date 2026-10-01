#!/usr/bin/env bash
#SBATCH --job-name=egg-route-proposal-v7
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --array=0-15%4
#SBATCH --nodelist=unicorn-cpu-75
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-route-proposal-v7-%A_%a.out
#SBATCH --error=egg-route-proposal-v7-%A_%a.err
set -euo pipefail
EGG_WRAPPER_STARTED=${SECONDS}
EGG_RECEIPT_PYTHON=$(command -v python3)
# Install receipt trap before source/runtime guards; preserve every wrapper attempt.
egg_v7_receipt() {
  local egg_rc=$?
  trap - EXIT
  "${EGG_RECEIPT_PYTHON}" - "${egg_rc}" "$((SECONDS-EGG_WRAPPER_STARTED))" <<'PY'
import json, os, sys
from pathlib import Path
root = Path(os.environ.get('SLURM_SUBMIT_DIR', '.')) / 'result/physical_learning/20260930-route-proposal-train-v7'
root.mkdir(parents=True, exist_ok=True)
task = os.environ.get('SLURM_ARRAY_TASK_ID', 'unknown')
path = root / f'task{task}.wrapper_receipt.{os.environ.get("SLURM_JOB_ID", "unknown")}.json'
with path.open('x') as stream:
    json.dump({'task_id': task, 'job_id': os.environ.get('SLURM_JOB_ID'),
        'array_job_id': os.environ.get('SLURM_ARRAY_JOB_ID'), 'returncode': int(sys.argv[1]),
        'elapsed_seconds': int(sys.argv[2]), 'timeout_exit': int(sys.argv[1]) in (124, 137),
        'signal_exit': int(sys.argv[1])-128 if int(sys.argv[1]) > 128 else None,
        'source_commit': os.environ.get('EGG_RUN_COMMIT'), 'manifest_sha256': os.environ.get('EGG_V7_MANIFEST_SHA256'),
        'node': os.environ.get('SLURMD_NODENAME'), 'requested_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
        'allocated_job_cpus': os.environ.get('SLURM_JOB_CPUS_PER_NODE'),
        'allocated_memory': os.environ.get('SLURM_MEM_PER_NODE'), 'native_threads': 1,
        'family_python': os.environ.get('EGG_FAMILY_PYTHON'), 'graph_python': os.environ.get('EGG_GRAPH_PYTHON')},
        stream, indent=2, sort_keys=True)
    stream.write('\n')
PY
  exit "${egg_rc}"
}
trap egg_v7_receipt EXIT
: "${SLURM_ARRAY_TASK_ID:?Run only declared16-task array}"
: "${SLURM_SUBMIT_DIR:?Missing checkout}"
: "${EGG_RUN_COMMIT:?Pin reviewed source commit}"
: "${EGG_V7_MANIFEST:?Pin reviewed prospective manifest path}"
: "${EGG_V7_MANIFEST_SHA256:?Pin prospective manifest SHA}"
case "${SLURM_ARRAY_TASK_ID}" in [0-9]|1[0-5]) ;; *) exit 2;; esac
test "${SLURM_CPUS_PER_TASK:-}" = 1
test "${SLURMD_NODENAME:-}" = unicorn-cpu-75
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 LOKY_MAX_CPU_COUNT=1 PYTHONPATH=src
export EGG_FAMILY_PYTHON=${EGG_FAMILY_PYTHON:-/home/nc437/egg-route-family-env-20260930/bin/python}
export EGG_GRAPH_PYTHON=${EGG_GRAPH_PYTHON:-/home/nc437/egg-route-graph-env-20260930/bin/python}
test -x "${EGG_FAMILY_PYTHON}"
test -x "${EGG_GRAPH_PYTHON}"
source src/cluster/unicorn_env.sh
# Supervisor is stdlib-only; each scoring/native stage is a capped subprocess.
timeout --signal=TERM --kill-after=10s 1700s python \
  -m experiments.physical_route_proposal_pilot_v7 run \
  --task-id "${SLURM_ARRAY_TASK_ID}" --manifest "${EGG_V7_MANIFEST}" \
  --manifest-sha "${EGG_V7_MANIFEST_SHA256}" \
  --family-python "${EGG_FAMILY_PYTHON}" --graph-python "${EGG_GRAPH_PYTHON}"
