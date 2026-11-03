#!/usr/bin/env bash
#SBATCH --job-name=egg-budget-sizing
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-budget-sizing-%j.out
#SBATCH --error=egg-budget-sizing-%j.err
if test -f /etc/profile.d/slurm.sh; then source /etc/profile.d/slurm.sh; fi
set -euo pipefail
START_UTC=$(date -u +%FT%TZ)
START_SECONDS=${SECONDS}
: "${SLURM_JOB_ID:?Run only within a Slurm allocation}"
: "${SLURM_SUBMIT_DIR:?Missing checkout}"
: "${EGG_RUN_COMMIT:?Declare the reviewed execution commit}"
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1
cd src
source cluster/unicorn_env.sh
cd ..
export PYTHONPATH=src
OUT=result/budget_sizing_diagnostic/20260928-attempt1
test ! -e "${OUT}"
set +e
python -m experiments.budget_sizing_diagnostic freeze --attempt "${OUT}"
FREEZE_RC=$?
PREFLIGHT_RC=not_run
SUPERVISE_RC=not_run
if test "${FREEZE_RC}" -eq 0; then
  python -m experiments.budget_sizing_diagnostic preflight --attempt "${OUT}"
  PREFLIGHT_RC=$?
fi
SETUP_SECONDS=$((SECONDS-START_SECONDS))
if test "${FREEZE_RC}" -ne 0; then
  RC=${FREEZE_RC}
elif test "${PREFLIGHT_RC}" -ne 0; then
  RC=${PREFLIGHT_RC}
else
  timeout --signal=TERM --kill-after=10s 1000s \
    python -m experiments.budget_sizing_diagnostic supervise --attempt "${OUT}"
  SUPERVISE_RC=$?
  RC=${SUPERVISE_RC}
fi
ELAPSED=$((SECONDS-START_SECONDS))
set -e
python - "${OUT}" "${RC}" "${ELAPSED}" "${SETUP_SECONDS}" "${START_UTC}" \
  "${FREEZE_RC}" "${PREFLIGHT_RC}" "${SUPERVISE_RC}" <<'PY_RECEIPT'
import json, os, sys
from pathlib import Path
out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
def phase(value):
    return None if value == 'not_run' else int(value)
with out.with_name(out.name + '.slurm_wrapper_receipt.json').open('x') as stream:
    json.dump({'returncode': int(sys.argv[2]), 'elapsed_whole_seconds': int(sys.argv[3]),
               'setup_seconds': int(sys.argv[4]), 'start_utc': sys.argv[5],
               'freeze_returncode': phase(sys.argv[6]),
               'preflight_returncode': phase(sys.argv[7]),
               'supervise_returncode': phase(sys.argv[8]),
               'outer_shell_cap_seconds': 1000,
               'timeout_exit': phase(sys.argv[8]) in (124, 137),
               'job_id': os.environ.get('SLURM_JOB_ID'),
               'requested_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
               'allocated_job_cpus': os.environ.get('SLURM_JOB_CPUS_PER_NODE'),
               'allocated_memory': os.environ.get('SLURM_MEM_PER_NODE')},
              stream, indent=2, sort_keys=True)
    stream.write('\n')
PY_RECEIPT
exit "${RC}"
