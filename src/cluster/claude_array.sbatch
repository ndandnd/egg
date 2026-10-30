#!/usr/bin/env bash
# Generic Claude-takeover array runner: task i runs line i (0-based) of $EGG_CMDS.
# Submit from the run directory, e.g.
#   sbatch --array=0-15%4 --time=00:20:00 --job-name=egg-claude-e0 \
#     --export=ALL,EGG_CMDS=$PWD/cmds.txt,EGG_CODE=$HOME/egg-claude-20261001/current \
#     $EGG_CODE/src/cluster/claude_array.sbatch
#SBATCH --partition=default_partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --exclude=scaglione-compute-01
#SBATCH --no-requeue
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err
set -euo pipefail
: "${EGG_CMDS:?command file}"; : "${EGG_CODE:?code directory}"
line=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" "$EGG_CMDS")
[ -n "$line" ] || { echo "no command for task $SLURM_ARRAY_TASK_ID" >&2; exit 2; }
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH="$EGG_CODE/src"
source "$EGG_CODE/src/cluster/unicorn_env.sh"
echo "task=$SLURM_ARRAY_TASK_ID node=$SLURMD_NODENAME commit=$(cat "$EGG_CODE/SOURCE_COMMIT") start=$(date -u +%FT%TZ)"
echo "cmd=$line"
start=$SECONDS
set +e
bash -c "$line"
rc=$?
set -e
echo "rc=$rc elapsed=$((SECONDS-start)) end=$(date -u +%FT%TZ)"
exit $rc
