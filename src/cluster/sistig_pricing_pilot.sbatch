#!/usr/bin/env bash
#SBATCH --job-name=egg-sistig-pilot
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:12:00
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-sistig-pilot-%j.out
#SBATCH --error=egg-sistig-pilot-%j.err
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
OUT="result/sistig_pricing/20260927-grb-job${SLURM_JOB_ID}-attempt1"
test ! -e "${OUT}"
START_UTC=$(date -u +%FT%TZ)
PILOT_START_SECONDS=${SECONDS}
set +e
timeout --signal=TERM --kill-after=10s 560s python -m experiments.sistig_pricing_pilot \
  --output "${OUT}" --freeze-label "${EGG_RUN_COMMIT}" --backend GRB
PILOT_RC=$?
PILOT_ELAPSED=$((SECONDS-PILOT_START_SECONDS))
set -e
python - "${OUT}" "${PILOT_RC}" "${PILOT_ELAPSED}" "${START_UTC}" <<'PY_RECEIPT'
import json,sys
from pathlib import Path
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
receipt={'scope':'Slurm outer timeout wrapper','returncode':int(sys.argv[2]),
         'elapsed_whole_seconds':int(sys.argv[3]),'start_utc':sys.argv[4],
         'outer_cap_s':560,'kill_grace_s':10,
         'timeout_exit':int(sys.argv[2]) in (124,137)}
with (out/'supervisor_receipt.json').open('x') as stream:
    json.dump(receipt,stream,indent=2,sort_keys=True);stream.write('\n')
PY_RECEIPT
exit "${PILOT_RC}"
