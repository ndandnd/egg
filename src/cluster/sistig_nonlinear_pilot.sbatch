#!/usr/bin/env bash
#SBATCH --job-name=egg-sistig-nonlinear
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:36:00
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-sistig-nonlinear-%j.out
#SBATCH --error=egg-sistig-nonlinear-%j.err
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

OUT=result/sistig_nonlinear/20260927-attempt2
test ! -e "${OUT}"
python -m experiments.sistig_nonlinear_pilot freeze --attempt "${OUT}"
START_UTC=$(date -u +%FT%TZ)
START_SECONDS=${SECONDS}
set +e
timeout --signal=TERM --kill-after=10s 2070s \
  python -m experiments.sistig_nonlinear_pilot supervise --attempt "${OUT}"
RC=$?
ELAPSED=$((SECONDS-START_SECONDS))
set -e
python - "${OUT}" "${RC}" "${ELAPSED}" "${START_UTC}" <<'PY_RECEIPT'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
with (out / 'slurm_wrapper_receipt.json').open('x') as stream:
    json.dump({'returncode': int(sys.argv[2]), 'elapsed_whole_seconds': int(sys.argv[3]),
               'start_utc': sys.argv[4], 'outer_shell_cap_seconds': 2070,
               'timeout_exit': int(sys.argv[2]) in (124, 137)}, stream,
              indent=2, sort_keys=True)
    stream.write('\n')
PY_RECEIPT
exit "${RC}"
