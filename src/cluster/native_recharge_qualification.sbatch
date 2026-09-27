#!/usr/bin/env bash
#SBATCH --job-name=egg-native-qual
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=egg-native-qual-%j.out
#SBATCH --error=egg-native-qual-%j.err
set -euo pipefail

# Submit only from an isolated, published research checkout after local gate.
: "${SLURM_JOB_ID:?This qualification must run in a Slurm allocation}"
: "${SLURM_SUBMIT_DIR:?Missing submitted checkout}"
: "${EGG_RUN_COMMIT:?Declare the exact published execution commit}"
cd "${SLURM_SUBMIT_DIR}"
test "$(git rev-parse HEAD)" = "${EGG_RUN_COMMIT}"
test -z "$(git status --porcelain --untracked-files=no)"

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
cd src
source cluster/unicorn_env.sh
cd ..
export PYTHONPATH=src

# Each job has a unique immutable attempt; no requeue, retry or resume.
# The controller separately enforces 60 s per cell over the fixed 15 cells.
timeout --signal=TERM --kill-after=10s 1000s python -m experiments.native_recharge_qualification \
  --output "result/native_recharge/20260927-grb-job${SLURM_JOB_ID}-attempt1" \
  --freeze-label "${EGG_RUN_COMMIT}" --backend GRB
