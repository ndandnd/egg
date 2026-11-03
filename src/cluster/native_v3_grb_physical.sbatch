#!/usr/bin/env bash
#SBATCH --job-name=egg-v3-grb-physical
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-v3-grb-physical-%j.out
#SBATCH --error=egg-v3-grb-physical-%j.err
set -euo pipefail
: "${SLURM_JOB_ID:?Slurm allocation required}"
: "${SLURM_SUBMIT_DIR:?Submitted checkout required}"
: "${EGG_RUN_COMMIT:?Full published source commit required}"
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd src
source cluster/unicorn_env.sh
cd ..
export PYTHONPATH=src
OUT=result/native_pathflow_grb/20260927-attempt1
test ! -e "${OUT}"
test ! -e "${OUT}.launch"
START_UTC=$(date -u +%FT%TZ)
START_SECONDS=${SECONDS}
set +e
timeout --signal=TERM --kill-after=10s 1370s python -m experiments.native_v3_grb_replication \
  physical --output "${OUT}" --freeze-label "${EGG_RUN_COMMIT}"
RC=$?
ELAPSED=$((SECONDS-START_SECONDS))
set -e
if test -d "${OUT}.launch"; then
  python - "${OUT}.launch/slurm_receipt.json" "${RC}" "${ELAPSED}" "${START_UTC}" "${SLURM_JOB_ID}" <<'PY_RECEIPT'
import json, sys
with open(sys.argv[1], 'x', encoding='utf-8') as out:
    json.dump({'returncode': int(sys.argv[2]), 'elapsed_whole_seconds': int(sys.argv[3]),
               'start_utc': sys.argv[4], 'job_id': sys.argv[5],
               'shell_cap_seconds': 1370, 'timeout_exit': int(sys.argv[2]) in (124, 137)},
              out, sort_keys=True, indent=2)
    out.write('\n')
PY_RECEIPT
fi
exit "${RC}"
