#!/bin/bash
# Submit the hardened Phase 1/2 arrays from an interactive Unicorn login shell.
# Do not invoke this through a nested non-interactive `ssh host '...'` session:
# Unicorn does not expose the Slurm client path there.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch is not available in this shell." >&2
    echo "Run this script directly at an interactive Unicorn login prompt; do not SSH from Unicorn back into itself." >&2
    exit 127
fi

if ! command -v squeue >/dev/null 2>&1; then
    echo "ERROR: squeue is not available in this shell." >&2
    exit 127
fi

source "${SRC_DIR}/cluster/unicorn_env.sh"

CELL_TOTAL="$(python experiments/run_phase1.py --list | tail -1)"
echo "[egglab] commit=$(git -C "${REPO_DIR}" rev-parse --short HEAD)"
echo "[egglab] ${CELL_TOTAL}"
if [[ "${CELL_TOTAL}" != "total: 128 cells" ]]; then
    echo "ERROR: refusing to submit Phase 1; expected the hardened 128-cell grid." >&2
    exit 1
fi

P1_ARRAY="${EGG_PHASE1_ARRAY:-0-127}"
P2_ARRAY="${EGG_PHASE2_ARRAY:-0-31}"

P1_JOB="$(sbatch --parsable --export=ALL --array="${P1_ARRAY}" cluster/submit_phase1.sub)"
P2_JOB="$(sbatch --parsable --export=ALL --array="${P2_ARRAY}" cluster/submit_phase2.sub)"

echo "Phase 1: ${P1_JOB} (array ${P1_ARRAY})"
echo "Phase 2: ${P2_JOB} (array ${P2_ARRAY})"
squeue --jobs="${P1_JOB},${P2_JOB}"
