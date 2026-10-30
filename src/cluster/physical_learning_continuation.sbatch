#!/usr/bin/env bash
#SBATCH --job-name=egg-physical-continuation
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:45:00
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-physical-continuation-%j.out
#SBATCH --error=egg-physical-continuation-%j.err
if test -f /etc/profile.d/slurm.sh; then source /etc/profile.d/slurm.sh; fi
set -euo pipefail
: "${SLURM_JOB_ID:?Run only within Slurm}"
: "${SLURM_SUBMIT_DIR:?Missing checkout}"
: "${EGG_RUN_COMMIT:?Pin reviewed execution commit}"
START_UTC=$(date -u +%FT%TZ)
START_SECONDS=${SECONDS}
OUT=${SLURM_SUBMIT_DIR}/result/physical_learning/20260930-shard00-continuation-attempt1
FREEZE_RC=not_run
PREFLIGHT_RC=not_run
CONTROLLER_RC=not_run
RC=2
SIGNAL=none
write_receipt() {
  local elapsed=$((SECONDS-START_SECONDS))
  python3 - "${OUT}" "${RC}" "${elapsed}" "${START_UTC}" \
    "${FREEZE_RC}" "${PREFLIGHT_RC}" "${CONTROLLER_RC}" "${SIGNAL}" <<'PY_RECEIPT'
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
        'preflight_returncode': phase(sys.argv[6]), 'controller_returncode': phase(sys.argv[7]),
        'signal': sys.argv[8], 'outer_shell_cap_seconds': 2600,
        'timeout_exit': phase(sys.argv[7]) in (124, 137), 'job_id': os.environ['SLURM_JOB_ID'],
        'parent_job_id': '703461', 'requested_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
        'allocated_job_cpus': os.environ.get('SLURM_JOB_CPUS_PER_NODE'),
        'allocated_memory': os.environ.get('SLURM_MEM_PER_NODE')}, stream, indent=2, sort_keys=True)
    stream.write('\n')
PY_RECEIPT
}
on_exit() {
  local actual=$?
  trap - EXIT TERM INT
  if test "${RC}" -eq 2 && test "${actual}" -ne 0; then RC=${actual}; fi
  write_receipt || true
}
on_term() { SIGNAL=TERM; RC=143; exit 143; }
on_int() { SIGNAL=INT; RC=130; exit 130; }
trap on_exit EXIT
trap on_term TERM
trap on_int INT
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1
cd src
source cluster/unicorn_env.sh
cd ..
export PYTHONPATH=src
set +e
if test ! -e "${OUT}"; then
  python -m experiments.physical_learning_continuation freeze --attempt "${OUT}"
  FREEZE_RC=$?
else
  FREEZE_RC=0
fi
if test "${FREEZE_RC}" -eq 0; then
  python -m experiments.physical_learning_continuation preflight --attempt "${OUT}"
  PREFLIGHT_RC=$?
fi
if test "${FREEZE_RC}" -ne 0; then
  RC=${FREEZE_RC}
elif test "${PREFLIGHT_RC}" -ne 0; then
  RC=${PREFLIGHT_RC}
else
  timeout --signal=TERM --kill-after=10s 2600s \
    python -m experiments.physical_learning_continuation controller --attempt "${OUT}"
  CONTROLLER_RC=$?
  RC=${CONTROLLER_RC}
fi
exit "${RC}"
