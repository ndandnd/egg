#!/usr/bin/env bash
#SBATCH --job-name=egg-pricing-start
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-pricing-start-%j.out
#SBATCH --error=egg-pricing-start-%j.err
if test -f /etc/profile.d/slurm.sh; then source /etc/profile.d/slurm.sh; fi
set -euo pipefail
WRAPPER_STARTED_UTC=$(date -u +%FT%TZ)
WRAPPER_START_SECONDS=${SECONDS}

: "${SLURM_JOB_ID:?Run only within a Slurm allocation}"
: "${SLURM_SUBMIT_DIR:?Missing checkout}"
: "${EGG_RUN_COMMIT:?Declare the published execution commit}"
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1
cd src
source cluster/unicorn_env.sh
cd ..
export PYTHONPATH=src

OUT=result/pricing_start_pilot/20260928-attempt1
test -f "${OUT}/frozen.json"
test ! -e "${OUT}.slurm_wrapper_receipt.json"
set +e
python -m experiments.pricing_start_pilot preflight --attempt "${OUT}"
PREFLIGHT_RC=$?
SETUP_SECONDS=$((SECONDS-WRAPPER_START_SECONDS))
if test "${PREFLIGHT_RC}" -eq 0; then
  timeout --signal=TERM --kill-after=10s 3000s \
    python -m experiments.pricing_start_pilot supervise --attempt "${OUT}"
  PILOT_RC=$?
else
  PILOT_RC=${PREFLIGHT_RC}
fi
WRAPPER_ELAPSED=$((SECONDS-WRAPPER_START_SECONDS))
set -e
python - "${OUT}" "${PREFLIGHT_RC}" "${PILOT_RC}" "${WRAPPER_ELAPSED}" "${SETUP_SECONDS}" "${WRAPPER_STARTED_UTC}" <<'PY_RECEIPT'
import json, os, sys
from pathlib import Path
out = Path(sys.argv[1])
with out.with_name(out.name + '.slurm_wrapper_receipt.json').open('x') as stream:
    json.dump({'preflight_returncode': int(sys.argv[2]), 'returncode': int(sys.argv[3]),
               'elapsed_whole_seconds': int(sys.argv[4]), 'setup_seconds': int(sys.argv[5]),
               'start_utc': sys.argv[6], 'outer_shell_cap_seconds': 3000,
               'timeout_exit': int(sys.argv[3]) in (124, 137),
               'job_id': os.environ.get('SLURM_JOB_ID'),
               'requested_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
               'allocated_job_cpus': os.environ.get('SLURM_JOB_CPUS_PER_NODE'),
               'allocated_memory': os.environ.get('SLURM_MEM_PER_NODE')},
              stream, indent=2, sort_keys=True)
    stream.write('\n')
PY_RECEIPT
exit "${PILOT_RC}"
