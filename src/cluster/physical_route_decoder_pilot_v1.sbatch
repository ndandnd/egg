#!/usr/bin/env bash
#SBATCH --job-name=egg-route-decode-train
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --array=0-3%4
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-route-decode-train-%A_%a.out
#SBATCH --error=egg-route-decode-train-%A_%a.err
if test -f /etc/profile.d/slurm.sh; then source /etc/profile.d/slurm.sh; fi
set -euo pipefail
: "${SLURM_ARRAY_TASK_ID:?Run only in the four-task array}"
: "${SLURM_SUBMIT_DIR:?Missing checkout}"
: "${EGG_RUN_COMMIT:?Pin reviewed source commit}"
: "${EGG_POOL32_MANIFEST_SHA256:?Pin admitted 32-group pool}"
: "${EGG_POOL64_MANIFEST_SHA256:?Pin admitted 64-group pool}"
: "${EGG_PRIOR_128_ARRAY_JOB_ID:?Pin the 128-group training array that must finish first}"
case "${SLURM_ARRAY_TASK_ID}" in 0|1|2|3) ;; *) echo "Undeclared decoder task" >&2; exit 2;; esac
if test -n "$(squeue -h -j "${EGG_PRIOR_128_ARRAY_JOB_ID}")"; then
  echo "128-group training array still active; decoder pilot waits" >&2
  exit 2
fi
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 LOKY_MAX_CPU_COUNT=1
cd src
source cluster/unicorn_env.sh
cd ..
export PYTHONPATH=src
EGG_TRAIN_PYTHON=${EGG_TRAIN_PYTHON:-/home/nc437/egg-route-training-env-20260930/bin/python}
test -x "${EGG_TRAIN_PYTHON}"
START_SECONDS=${SECONDS}
set +e
timeout --signal=TERM --kill-after=10s 1700s python \
  -m experiments.physical_route_decoder_pilot_v1 run \
  --task-id "${SLURM_ARRAY_TASK_ID}" \
  --pool32-sha "${EGG_POOL32_MANIFEST_SHA256}" \
  --pool64-sha "${EGG_POOL64_MANIFEST_SHA256}" \
  --train-python "${EGG_TRAIN_PYTHON}"
RC=$?
set -e
ELAPSED=$((SECONDS-START_SECONDS))
python - "${RC}" "${ELAPSED}" <<'PY_RECEIPT'
import json, os, sys
from pathlib import Path
root = Path(os.environ['SLURM_SUBMIT_DIR']) / 'result/physical_learning/20260930-route-decoder-train-v1'
root.mkdir(parents=True, exist_ok=True)
task = int(os.environ['SLURM_ARRAY_TASK_ID'])
path = root / f'task{task:02d}.slurm_wrapper_receipt.{os.environ["SLURM_JOB_ID"]}.json'
with path.open('x') as stream:
    json.dump({'task_id': task, 'group_id': 10036 + task,
        'job_id': os.environ['SLURM_JOB_ID'],
        'array_job_id': os.environ.get('SLURM_ARRAY_JOB_ID'),
        'returncode': int(sys.argv[1]), 'elapsed_seconds': int(sys.argv[2]),
        'timeout_exit': int(sys.argv[1]) in (124, 137),
        'pool32_manifest_sha256': os.environ['EGG_POOL32_MANIFEST_SHA256'],
        'pool64_manifest_sha256': os.environ['EGG_POOL64_MANIFEST_SHA256'],
        'requested_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
        'allocated_job_cpus': os.environ.get('SLURM_JOB_CPUS_PER_NODE'),
        'allocated_memory': os.environ.get('SLURM_MEM_PER_NODE')}, stream, indent=2, sort_keys=True)
    stream.write('\n')
PY_RECEIPT
exit "${RC}"
