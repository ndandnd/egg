#!/bin/bash
# Guarded launcher for the B3 fresh-seed confirmation stage (48 cells, A2).
#
# Usage (interactive Unicorn login prompt, in src/):
#   bash cluster/launch_b3_confirmation.sh /path/to/SELECTION.json
#
# The confirmation is GO-GATED: it refuses to submit unless handed a
# committed GO selection artifact that structurally validates (state == GO,
# named factor, analyzer-commit ancestry, frozen screen SHA + pilot spec
# hash, the frozen pilot raw-tree anchor, the boundary disclosure — a
# knife-edge decision refuses — and not INVALID/HALT-derived). The driver's
# --dry-run enforces that gate before anything is submitted.
#
# Guards mirror the pilot launcher: sbatch present; Gurobi-ONLY
# (EGGLAB_REQUIRE_GRB=1 + a hard-fail backend()=='GRB' check); a clean
# tracked tree; a FRESH run dir (empty or a lone MANIFEST.json); the run
# manifest emitted atomically BEFORE submission; and --list reporting
# EXACTLY 48 cells.
#
# Post-sbatch race is closed by submitting HELD (`sbatch --hold`) and
# releasing (`scontrol release`) ONLY after JOB.json is bound. A bind
# failure scancels the exact held job and never releases (CRITICAL on
# unconfirmed cancel); a release failure scancels the bound job. Either
# preserves MANIFEST.json/JOB.json and returns nonzero. Concurrency %12.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

SEL="${1:-${EGG_SELECTION_ARTIFACT:-}}"
if [[ -z "${SEL}" ]]; then
    echo "ERROR: a committed GO SELECTION.json path is required." >&2
    echo "usage: bash cluster/launch_b3_confirmation.sh /path/to/SELECTION.json" >&2
    exit 2
fi
if [[ ! -f "${SEL}" ]]; then
    echo "ERROR: selection artifact not found: ${SEL}" >&2
    exit 2
fi

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

# CRITICAL 2 / BLOCKER B: cluster-tool and driver indirection are permitted
# ONLY when the test harness supplies a POSITIVE permission marker
# (EGG_LAUNCH_SELFTEST must name an existing regular file it created under a
# temp dir), AND no plausible scheduler is reachable.  We do not rely on
# `command -v sbatch` alone: an absolute EGG_SBATCH outside PATH previously
# reached release.  In production the launcher invokes the driver by its
# literal path with literal tools/output — no environment hook applies.
if [[ -n "${EGG_LAUNCH_SELFTEST:-}" ]]; then
    if [[ ! -f "${EGG_LAUNCH_SELFTEST}" ]]; then
        echo "ERROR: EGG_LAUNCH_SELFTEST must name an existing self-test permission marker file." >&2
        exit 1
    fi
    _sched_reachable=""
    command -v sbatch >/dev/null 2>&1 && _sched_reachable="PATH:sbatch"
    for _p in /usr/bin/sbatch /usr/local/bin/sbatch /opt/slurm/bin/sbatch \
              /share/apps/software/slurm/current/bin/sbatch \
              /usr/local/slurm/current/bin/sbatch; do
        [[ -x "${_p}" ]] && _sched_reachable="${_p}"
    done
    for _v in SLURM_CONF SLURM_CLUSTER_NAME SLURMD_NODENAME SLURM_JOB_ID; do
        [[ -n "${!_v:-}" ]] && _sched_reachable="env:${_v}"
    done
    if [[ -n "${_sched_reachable}" ]]; then
        echo "ERROR: EGG_LAUNCH_SELFTEST refused: a scheduler is reachable (${_sched_reachable}); hooks may never run on a cluster." >&2
        exit 1
    fi
    SBATCH="${EGG_SBATCH:-sbatch}"
    SCANCEL="${EGG_SCANCEL:-scancel}"
    SCONTROL="${EGG_SCONTROL:-scontrol}"
    SQUEUE="${EGG_SQUEUE:-squeue}"
    SACCT="${EGG_SACCT:-sacct}"
    PILOT="${EGG_PILOT:-python ${SRC_DIR}/experiments/run_b3_confirmation.py}"
    OUT="${EGG_RUN_OUT:-runs/b3_confirmation}"
else
    if ! command -v sbatch >/dev/null 2>&1; then
        echo "ERROR: sbatch is unavailable; run from an interactive Unicorn login prompt." >&2
        exit 127
    fi
    # literal, non-overridable tool + driver + output identities
    SBATCH="sbatch"; SCANCEL="scancel"; SCONTROL="scontrol"
    SQUEUE="squeue"; SACCT="sacct"
    PILOT="python ${SRC_DIR}/experiments/run_b3_confirmation.py"
    OUT="runs/b3_confirmation"
    export EGGLAB_REQUIRE_GRB=1
    source "${SRC_DIR}/cluster/unicorn_env.sh"
    if ! python -c "import sys; from egglab.solver import backend; sys.exit(0 if backend()=='GRB' else 1)"; then
        echo "ERROR: Gurobi (GRB) backend is not usable; refusing to launch the Gurobi-only confirmation." >&2
        exit 1
    fi
    if [[ -n "$(git -C "${REPO_DIR}" status --porcelain | grep -v '^??' || true)" ]]; then
        echo "ERROR: tracked tree is dirty; commit before launching." >&2
        exit 1
    fi
fi

# FRESH run dir: allow only an empty dir or a lone regular MANIFEST.json
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
            continue
        fi
        echo "ERROR: unexpected entry in run dir (${_b}); only an empty dir or a lone MANIFEST.json may be reused. Refusing." >&2
        exit 1
    done
fi

# GO-gate + binding preflight (fails closed on a non-GO/tampered artifact).
${PILOT} --selection-artifact "${SEL}" --dry-run

EMIT="$(${PILOT} --selection-artifact "${SEL}" --emit-run-manifest --out "${OUT}")"
echo "${EMIT}"
RUN_SHA="$(printf '%s\n' "${EMIT}" | sed -n 's/^RUN_MANIFEST_SHA256=//p')"
if [[ -z "${RUN_SHA}" ]]; then
    echo "ERROR: run manifest emission did not report a SHA-256." >&2
    exit 1
fi

N="$(${PILOT} --selection-artifact "${SEL}" --list | tail -1 | sed 's/total: \([0-9]*\) cells/\1/')"
if [[ "${N}" != "48" ]]; then
    echo "ERROR: --list reports ${N} cells; expected exactly 48. Refusing." >&2
    exit 1
fi
CONC=12

# submit HELD; thread the output dir to the worker so the launcher's binding
# and the worker's evidence always target the SAME directory (CRITICAL 3)
JOB="$(${SBATCH} --hold --parsable --array="0-$((N - 1))%${CONC}" \
    --export="ALL,EGG_SELECTION_ARTIFACT=${SEL},EGG_RUN_OUT=${OUT}" \
    cluster/submit_b3_confirmation.sub)"

if ! ${PILOT} --selection-artifact "${SEL}" --bind-job "${JOB}" --out "${OUT}"; then
    echo "ERROR: --bind-job failed for job ${JOB}; cancelling the held job (never releasing)." >&2
    ${SCANCEL} "${JOB}" || true
    if ! b3_verify_cancelled "${JOB}"; then
        echo "CRITICAL: could not confirm cancellation of HELD job ${JOB}; it remains HELD and cannot execute unbound. Manual cleanup required: scancel ${JOB}" >&2
    fi
    echo "MANIFEST.json preserved as incident evidence: ${OUT}/MANIFEST.json" >&2
    exit 1
fi

# CRITICAL 2: before releasing the hold, assert the bind is real on disk:
# MANIFEST.json and JOB.json exist, JOB.json names the EXACT submitted job id,
# and its recorded run-manifest SHA equals the manifest file's hash and the
# emitted SHA. Any failure cancels the held job and never releases it.
if ! python3 - "${OUT}" "${JOB}" "${RUN_SHA}" <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
out, job, run_sha = sys.argv[1], sys.argv[2], sys.argv[3]
man = Path(out) / "MANIFEST.json"
jb = Path(out) / "JOB.json"
if not man.is_file() or not jb.is_file():
    sys.exit(11)
try:
    doc = json.loads(jb.read_bytes())
except Exception:
    sys.exit(12)
if str(doc.get("job_id")) != str(job):
    sys.exit(13)
actual = hashlib.sha256(man.read_bytes()).hexdigest()
if doc.get("run_manifest_sha256") != actual or actual != run_sha:
    sys.exit(14)
sys.exit(0)
PYEOF
then
    echo "ERROR: pre-release verification failed for job ${JOB}; cancelling the held job (never releasing)." >&2
    ${SCANCEL} "${JOB}" || true
    b3_verify_cancelled "${JOB}" || true
    echo "MANIFEST.json/JOB.json preserved as incident evidence in ${OUT}" >&2
    exit 1
fi

if ! ${SCONTROL} release "${JOB}"; then
    echo "ERROR: scontrol release failed for job ${JOB}; cancelling the still-held bound job." >&2
    ${SCANCEL} "${JOB}" || true
    b3_verify_cancelled "${JOB}" || true
    echo "MANIFEST.json/JOB.json preserved as incident evidence in ${OUT}" >&2
    exit 1
fi

echo "[submitted+released] b3 confirmation: ${N} cells as job ${JOB}"
echo "  run manifest: ${OUT}/MANIFEST.json (sha256=${RUN_SHA})"
echo "  job binding:  ${OUT}/JOB.json"
${SQUEUE} --jobs="${JOB}"
