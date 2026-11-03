#!/usr/bin/env bash
#SBATCH --job-name=egg-feasible-pool-pilot
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-feasible-pool-pilot-%j.out
#SBATCH --error=egg-feasible-pool-pilot-%j.err
if test -f /etc/profile.d/slurm.sh; then source /etc/profile.d/slurm.sh; fi
set -euo pipefail

: "${SLURM_JOB_ID:?Run only within a Slurm allocation}"
: "${SLURM_SUBMIT_DIR:?Missing checkout}"
: "${EGG_RUN_COMMIT:?Declare the published execution commit}"
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd src
source cluster/unicorn_env.sh
cd ..
export PYTHONPATH=src

OUT=result/feasible_pool_pilot/20260928-attempt1
test ! -e "${OUT}"
python -m experiments.feasible_pool_pilot freeze --attempt "${OUT}"
START_UTC=$(date -u +%FT%TZ)
START_SECONDS=${SECONDS}
set +e
timeout --signal=TERM --kill-after=10s 5500s \
  python -m experiments.feasible_pool_pilot supervise --attempt "${OUT}"
RC=$?
ELAPSED=$((SECONDS-START_SECONDS))
set -e
python - "${OUT}" "${RC}" "${ELAPSED}" "${START_UTC}" <<'PY_RECEIPT'
import json, os, sys
from pathlib import Path
out = Path(sys.argv[1])
with out.with_name(out.name + '.slurm_wrapper_receipt.json').open('x') as stream:
    json.dump({'returncode': int(sys.argv[2]), 'elapsed_whole_seconds': int(sys.argv[3]),
               'start_utc': sys.argv[4], 'outer_shell_cap_seconds': 5500,
               'timeout_exit': int(sys.argv[2]) in (124, 137),
               'job_id': os.environ.get('SLURM_JOB_ID'),
               'requested_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
               'allocated_job_cpus': os.environ.get('SLURM_JOB_CPUS_PER_NODE'),
               'allocated_memory': os.environ.get('SLURM_MEM_PER_NODE')},
              stream, indent=2, sort_keys=True)
    stream.write('\n')
PY_RECEIPT
exit "${RC}"
