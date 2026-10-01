#!/usr/bin/env bash
#SBATCH --job-name=egg-route-families128-recovery1
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --array=0,1,4,5,6,7,8,9,11%4
#SBATCH --nodelist=unicorn-cpu-75
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-route-families128-recovery1-%A_%a.out
#SBATCH --error=egg-route-families128-recovery1-%A_%a.err
if test -f /etc/profile.d/slurm.sh; then source /etc/profile.d/slurm.sh; fi
set -euo pipefail
: "${SLURM_ARRAY_TASK_ID:?Run only in declared recovery array}"
: "${SLURM_SUBMIT_DIR:?Missing isolated checkout}"
: "${EGG_RUN_COMMIT:?Pin reviewed recovery source commit}"
: "${EGG_POOL_MANIFEST_SHA256:?Pin frozen exact128 pool}"
: "${EGG_ORIGINAL_ATTEMPT_ROOT:?Original immutable array720831 evidence required}"
case "${SLURM_ARRAY_TASK_ID}" in
  0|1|4|5|6|7|8|9|11) ;;
  *) echo "Undeclared recovery task" >&2; exit 2;;
esac
test "${EGG_POOL_MANIFEST_SHA256}" = d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 LOKY_MAX_CPU_COUNT=1
cd src
source cluster/unicorn_env.sh
cd ..
export PYTHONPATH=src
EGG_TRAIN_PYTHON=${EGG_TRAIN_PYTHON:-/home/nc437/egg-route-family-env-20260930/bin/python}
test -x "${EGG_TRAIN_PYTHON}"
START_SECONDS=${SECONDS}
set +e
timeout --signal=TERM --kill-after=10s 1700s "${EGG_TRAIN_PYTHON}" \
  -m experiments.recover_physical_route_model_families_v5 \
  --task-id "${SLURM_ARRAY_TASK_ID}" \
  --original-attempt-root "${EGG_ORIGINAL_ATTEMPT_ROOT}"
RC=$?
set -e
ELAPSED=$((SECONDS-START_SECONDS))
"${EGG_TRAIN_PYTHON}" - "${RC}" "${ELAPSED}" <<'PY_RECEIPT'
import json, os, sys
from pathlib import Path
root = Path(os.environ['SLURM_SUBMIT_DIR']) / 'result/physical_learning/20260930-route-model128-families-v5-recovery1'
root.mkdir(parents=True, exist_ok=True)
task = int(os.environ['SLURM_ARRAY_TASK_ID'])
path = root / f'task{task:02d}.slurm_wrapper_receipt.{os.environ["SLURM_JOB_ID"]}.json'
with path.open('x') as stream:
    json.dump({'task_id': task, 'original_array_job_id': '720831',
        'job_id': os.environ['SLURM_JOB_ID'], 'array_job_id': os.environ.get('SLURM_ARRAY_JOB_ID'),
        'returncode': int(sys.argv[1]), 'elapsed_seconds': int(sys.argv[2]),
        'timeout_exit': int(sys.argv[1]) in (124, 137),
        'pool_manifest_sha256': os.environ['EGG_POOL_MANIFEST_SHA256'],
        'requested_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
        'allocated_job_cpus': os.environ.get('SLURM_JOB_CPUS_PER_NODE'),
        'allocated_memory': os.environ.get('SLURM_MEM_PER_NODE'),
        'node_list': os.environ.get('SLURM_JOB_NODELIST')}, stream, indent=2, sort_keys=True)
    stream.write('\n')
PY_RECEIPT
exit "${RC}"
