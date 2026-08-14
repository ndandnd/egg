#!/bin/bash
# Shared Unicorn runtime for the egg Slurm jobs.
#
# The cluster's working setup is a conda prefix with Python 3.12 and
# gurobipy installed, plus the shared Gurobi license.  Do not set GUROBI_HOME
# here: the personal Gurobi 11 installation can override the native library
# shipped with the active gurobipy package.

set -euo pipefail

CONDA_BASE="${EGG_CONDA_BASE:-/share/apps/software/anaconda3}"
CONDA_ENV="${EGG_CONDA_ENV:-${HOME}/evsp_env}"
CONDA_SH="${CONDA_BASE}/etc/profile.d/conda.sh"

[[ -r "${CONDA_SH}" ]] || {
    echo "ERROR: conda initialization script not found: ${CONDA_SH}" >&2
    exit 1
}
source "${CONDA_SH}"
conda activate "${CONDA_ENV}"

# Avoid stale packages installed earlier into ~/.local.
export PYTHONNOUSERSITE=1

# Unicorn's shared academic Gurobi license.  Use a project-specific override
# only when deliberately supplied; do not inherit stale GRB_LICENSE_FILE values
# from older EVSP shells.
export GRB_LICENSE_FILE="${EGG_GRB_LICENSE_FILE:-/share/apps/software/gurobi/gurobi.lic}"
[[ -r "${GRB_LICENSE_FILE}" ]] || {
    echo "ERROR: Gurobi license is not readable: ${GRB_LICENSE_FILE}" >&2
    exit 1
}

# Use the native library associated with the active gurobipy package.
unset GUROBI_HOME

# Remove a stale personal Gurobi 11 library path if the submitting shell
# exported one, while preserving unrelated library paths.
if [[ -n "${LD_LIBRARY_PATH:-}" ]]; then
    IFS=: read -r -a _egg_ld_parts <<< "${LD_LIBRARY_PATH}"
    _egg_ld_keep=()
    for _egg_ld_part in "${_egg_ld_parts[@]}"; do
        [[ -z "${_egg_ld_part}" ]] && continue
        case "${_egg_ld_part}" in
            */gurobi1102/*) ;;
            *) _egg_ld_keep+=("${_egg_ld_part}") ;;
        esac
    done
    if ((${#_egg_ld_keep[@]})); then
        _egg_old_ifs="${IFS}"
        IFS=:
        export LD_LIBRARY_PATH="${_egg_ld_keep[*]}"
        IFS="${_egg_old_ifs}"
    else
        unset LD_LIBRARY_PATH
    fi
    unset _egg_ld_parts _egg_ld_keep _egg_ld_part _egg_old_ifs
fi

# A cluster run must never silently fall back to CBC.
export EGGLAB_REQUIRE_GRB=1

# Fail at job start with the real backend/license error instead of spending an
# array slot on a CBC fallback.
python - <<'PY'
from egglab.solver import backend

active = backend()
print(f"[egglab] backend={active}")
if active != "GRB":
    raise SystemExit("ERROR: Unicorn job requires the Gurobi backend")
PY
