#!/usr/bin/env bash
#SBATCH --job-name=egg-tariff-response
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=01:40:00
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-tariff-response-%j.out
#SBATCH --error=egg-tariff-response-%j.err
if test -f /etc/profile.d/slurm.sh; then source /etc/profile.d/slurm.sh; fi
set -euo pipefail
: "${SLURM_JOB_ID:?Run only within Slurm}"
: "${SLURM_SUBMIT_DIR:?Missing checkout}"
: "${EGG_RUN_COMMIT:?Pin reviewed execution commit}"
START_UTC=$(date -u +%FT%TZ)
START_SECONDS=${SECONDS}
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1
cd src
source cluster/unicorn_env.sh
cd ..
export PYTHONPATH=src
OUT=result/learning_campaign/20260930-tariff-response-attempt1
set +e
if test ! -e "${OUT}"; then
  python -m experiments.tariff_response_campaign freeze --attempt "${OUT}"
  FREEZE_RC=$?
else
  FREEZE_RC=0
fi
PREFLIGHT_RC=not_run
CONTROLLER_RC=not_run
if test "${FREEZE_RC}" -eq 0; then
  python -m experiments.tariff_response_campaign preflight --attempt "${OUT}"
  PREFLIGHT_RC=$?
fi
if test "${FREEZE_RC}" -ne 0; then
  RC=${FREEZE_RC}
elif test "${PREFLIGHT_RC}" -ne 0; then
  RC=${PREFLIGHT_RC}
else
  timeout --signal=TERM --kill-after=10s 5700s \
    python -m experiments.tariff_response_campaign controller --attempt "${OUT}"
  CONTROLLER_RC=$?
  RC=${CONTROLLER_RC}
fi
ELAPSED=$((SECONDS-START_SECONDS))
set -e
python - "${OUT}" "${RC}" "${ELAPSED}" "${START_UTC}" \
  "${FREEZE_RC}" "${PREFLIGHT_RC}" "${CONTROLLER_RC}" <<'PY_RECEIPT'
import json, os, sys
from pathlib import Path
out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
def phase(value):
    return None if value == 'not_run' else int(value)
receipt = out.with_name(out.name + '.slurm_wrapper_receipt.' + os.environ['SLURM_JOB_ID'] + '.json')
with receipt.open('x') as stream:
    json.dump({'returncode': int(sys.argv[2]), 'elapsed_whole_seconds': int(sys.argv[3]),
               'start_utc': sys.argv[4], 'freeze_returncode': phase(sys.argv[5]),
               'preflight_returncode': phase(sys.argv[6]),
               'controller_returncode': phase(sys.argv[7]),
               'outer_shell_cap_seconds': 5700,
               'timeout_exit': phase(sys.argv[7]) in (124, 137),
               'job_id': os.environ['SLURM_JOB_ID'],
               'requested_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
               'allocated_job_cpus': os.environ.get('SLURM_JOB_CPUS_PER_NODE'),
               'allocated_memory': os.environ.get('SLURM_MEM_PER_NODE')},
              stream, indent=2, sort_keys=True)
    stream.write('\n')
PY_RECEIPT
exit "${RC}"
