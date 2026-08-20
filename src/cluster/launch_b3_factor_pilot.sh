#!/bin/bash
# Guarded launcher for the B3 internal-uplift factor pilot (60 cells, A2 only).
#
# Usage (interactive Unicorn login prompt, in src/):
#   bash cluster/launch_b3_factor_pilot.sh
#
# Guards:
#   - sbatch present (refuse off-cluster submission);
#   - Gurobi-ONLY: unicorn_env.sh + EGGLAB_REQUIRE_GRB=1, and a HARD-FAIL
#     check that egglab.solver.backend() == "GRB" (no CBC fallback ever);
#   - a clean tracked tree (the driver refuses a dirty tree per cell too);
#   - the driver's --dry-run must pass (binds every cell to the FROZEN
#     factor-screen artifact SHA, selected levels, and 30 instance hashes);
#   - the canonical Section-7 run manifest is emitted ATOMICALLY BEFORE
#     submission (records the pilot commit, spec SHA, screen SHA + levels,
#     held-fixed generator args, grid, tolerances, GRB/MIP-gap/load policy,
#     and all 30 instance + 60 market hashes with their invariants);
#   - the driver's --list must report EXACTLY 60 cells.
# After sbatch the job id is bound atomically to the manifest SHA (no
# post-sbatch provenance gap). Concurrency is capped at %12. Never
# `sbatch --wrap`.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch is unavailable; run from an interactive Unicorn login prompt." >&2
    exit 127
fi

# Gurobi-only: force the GRB backend and refuse a non-GRB fallback.
export EGGLAB_REQUIRE_GRB=1
source "${SRC_DIR}/cluster/unicorn_env.sh"

# HARD-FAIL unless Gurobi is actually usable in this environment.
if ! python -c "import sys; from egglab.solver import backend; sys.exit(0 if backend()=='GRB' else 1)"; then
    echo "ERROR: Gurobi (GRB) backend is not usable; refusing to launch the Gurobi-only B3 pilot." >&2
    exit 1
fi

# Refuse a dirty tracked tree before submitting anything.
if [[ -n "$(git -C "${REPO_DIR}" status --porcelain | grep -v '^??' || true)" ]]; then
    echo "ERROR: tracked tree is dirty; commit before launching the pilot." >&2
    exit 1
fi

OUT="runs/b3_factor_pilot"

# Binding + count preflight (fails closed on factor drift / A6 / bad screen).
python experiments/run_b3_factor_pilot.py --dry-run

# Emit the canonical Section-7 run manifest ATOMICALLY before submission.
EMIT="$(python experiments/run_b3_factor_pilot.py --emit-run-manifest --out "${OUT}")"
echo "${EMIT}"
RUN_SHA="$(printf '%s\n' "${EMIT}" | sed -n 's/^RUN_MANIFEST_SHA256=//p')"
if [[ -z "${RUN_SHA}" ]]; then
    echo "ERROR: run manifest emission did not report a SHA-256." >&2
    exit 1
fi

N="$(python experiments/run_b3_factor_pilot.py --list | tail -1 | sed 's/total: \([0-9]*\) cells/\1/')"
if [[ "${N}" != "60" ]]; then
    echo "ERROR: pilot --list reports ${N} cells; expected exactly 60. Refusing to submit." >&2
    exit 1
fi
CONC=12  # concurrency capped at %12

JOB="$(sbatch --parsable --array="0-$((N - 1))%${CONC}" cluster/submit_b3_factor_pilot.sub)"
# Close the post-sbatch provenance gap: bind the job id to the manifest SHA now.
python experiments/run_b3_factor_pilot.py --bind-job "${JOB}" --out "${OUT}"

echo "[submitted] b3 factor pilot: ${N} cells as job ${JOB}"
echo "  run manifest: ${OUT}/MANIFEST.json (sha256=${RUN_SHA})"
echo "  job binding:  ${OUT}/JOB.json"
squeue --jobs="${JOB}"
