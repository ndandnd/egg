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
#   - FRESH run dir: refuse if JOB.json exists or if any cell directory,
#     checkpoint, or identity sidecar already exists (partial/result-bearing
#     state); a lone byte-identical MANIFEST.json may be reused;
#   - the driver's --dry-run must pass (binds every cell to the FROZEN
#     factor-screen artifact SHA, selected levels, and 30 instance hashes);
#   - the canonical Section-7 run manifest is emitted ATOMICALLY BEFORE
#     submission; and the driver's --list must report EXACTLY 60 cells.
#
# Post-sbatch race is closed by submitting the array HELD (`sbatch --hold`):
# the array cannot run until it is explicitly released. The job id is bound
# atomically to the manifest SHA and ONLY THEN is the hold released
# (`scontrol release`). If binding fails the exact held job is scancel'd and
# never released (and stays held even if cancellation cannot be confirmed);
# if the release itself fails the exact bound job is scancel'd. Either failure
# preserves MANIFEST.json/JOB.json as incident evidence and returns nonzero.
# Concurrency is capped at %12. Never `sbatch --wrap`.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

# Cluster tools and the pilot driver are overridable for shell-level tests;
# they default to the real tools in production.
SBATCH="${EGG_SBATCH:-sbatch}"
SCANCEL="${EGG_SCANCEL:-scancel}"
SCONTROL="${EGG_SCONTROL:-scontrol}"
SQUEUE="${EGG_SQUEUE:-squeue}"
SACCT="${EGG_SACCT:-sacct}"
PILOT="${EGG_PILOT:-python experiments/run_b3_factor_pilot.py}"
OUT="${EGG_RUN_OUT:-runs/b3_factor_pilot}"

# Verify a cancelled job has actually left the queue (squeue) or shows a
# CANCELLED state (sacct); used only on the bind-failure recovery path.
b3_verify_cancelled() {
    local job="$1" i state
    for i in 1 2 3 4 5; do
        if [[ -z "$(${SQUEUE} -h -j "${job}" 2>/dev/null)" ]]; then
            echo "[verify] job ${job} has left the queue" >&2
            return 0
        fi
        state="$(${SACCT} -n -j "${job}" -o State 2>/dev/null | head -n1 | tr -d ' ')"
        case "${state}" in
            *CANCELLED*) echo "[verify] job ${job} state ${state}" >&2; return 0 ;;
        esac
        sleep "${EGG_VERIFY_SLEEP:-2}"
    done
    echo "[verify] WARNING: could not confirm cancellation of job ${job}" >&2
    return 1
}

# --- environment preparation (skippable only for shell-level self-tests) ---
if [[ -z "${EGG_LAUNCH_SELFTEST:-}" ]]; then
    if ! command -v "${SBATCH%% *}" >/dev/null 2>&1; then
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
fi

# --- FRESH run dir: allow only an empty dir or a lone regular MANIFEST.json --
if [[ -e "${OUT}/JOB.json" ]]; then
    echo "ERROR: ${OUT}/JOB.json already exists; a job was already submitted. Refusing." >&2
    exit 1
fi
if [[ -d "${OUT}" ]]; then
    shopt -s dotglob nullglob
    _entries=("${OUT}"/*)
    shopt -u dotglob nullglob
    for _e in "${_entries[@]}"; do
        _b="$(basename "${_e}")"
        if [[ "${_b}" == "MANIFEST.json" && -f "${_e}" && ! -L "${_e}" ]]; then
            continue   # the one reusable entry
        fi
        echo "ERROR: unexpected entry in run dir (${_b}); only an empty dir or a lone MANIFEST.json may be reused. Refusing to submit." >&2
        exit 1
    done
fi

# Binding + count preflight (fails closed on factor drift / A6 / bad screen).
${PILOT} --dry-run

# Emit the canonical Section-7 run manifest ATOMICALLY before submission.
EMIT="$(${PILOT} --emit-run-manifest --out "${OUT}")"
echo "${EMIT}"
RUN_SHA="$(printf '%s\n' "${EMIT}" | sed -n 's/^RUN_MANIFEST_SHA256=//p')"
if [[ -z "${RUN_SHA}" ]]; then
    echo "ERROR: run manifest emission did not report a SHA-256." >&2
    exit 1
fi

N="$(${PILOT} --list | tail -1 | sed 's/total: \([0-9]*\) cells/\1/')"
if [[ "${N}" != "60" ]]; then
    echo "ERROR: pilot --list reports ${N} cells; expected exactly 60. Refusing to submit." >&2
    exit 1
fi
CONC=12  # concurrency capped at %12

# Submit HELD: the array cannot execute until it is explicitly released, so
# there is no window in which an unbound array could run.
JOB="$(${SBATCH} --hold --parsable --array="0-$((N - 1))%${CONC}" cluster/submit_b3_factor_pilot.sub)"

# Bind the job id to the manifest SHA. If binding fails for ANY reason, cancel
# the exact held job and NEVER release it. Because the job was submitted held,
# it cannot execute unbound even if the cancellation cannot be confirmed.
if ! ${PILOT} --bind-job "${JOB}" --out "${OUT}"; then
    echo "ERROR: --bind-job failed for job ${JOB}; cancelling the held job (never releasing)." >&2
    ${SCANCEL} "${JOB}" || true
    if ! b3_verify_cancelled "${JOB}"; then
        echo "CRITICAL: could not confirm cancellation of HELD job ${JOB}; it remains HELD and cannot execute unbound. Manual cleanup required: scancel ${JOB}" >&2
    fi
    echo "MANIFEST.json preserved as incident evidence: ${OUT}/MANIFEST.json" >&2
    exit 1
fi

# Binding succeeded -> release the hold so the bound array can run.
if ! ${SCONTROL} release "${JOB}"; then
    echo "ERROR: scontrol release failed for job ${JOB}; cancelling the still-held bound job." >&2
    ${SCANCEL} "${JOB}" || true
    b3_verify_cancelled "${JOB}" || true
    echo "MANIFEST.json/JOB.json preserved as incident evidence in ${OUT}" >&2
    exit 1
fi

echo "[submitted+released] b3 factor pilot: ${N} cells as job ${JOB}"
echo "  run manifest: ${OUT}/MANIFEST.json (sha256=${RUN_SHA})"
echo "  job binding:  ${OUT}/JOB.json"
${SQUEUE} --jobs="${JOB}"
