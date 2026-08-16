"""MILP backend wrapper: Gurobi (via python-mip) when available, else CBC.

Every solve records the statistics the project requires (root LP value, MIP
value, dual bound, gap, sizes, wall time, backend), so the LP/MIP gap — the
integrality gap that several thesis questions revolve around (B10, B37) — is
captured on every oracle call for free.
"""
from __future__ import annotations

import contextlib
import os
import time
from dataclasses import dataclass, field, asdict

import mip


@contextlib.contextmanager
def _silence_native_output():
    """CBC/CLP write directly to the C-level stdout even with verbose=0;
    redirect fd 1 to /dev/null around solves so logs stay clean."""
    saved = os.dup(1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 1)
        yield
    finally:
        os.dup2(saved, 1)
        os.close(saved)
        os.close(devnull)


def detect_backend() -> str:
    try:
        import gurobipy  # noqa: F401

        # instantiating a Model verifies the license is actually usable
        m = mip.Model(solver_name="GRB")
        del m
        return "GRB"
    except Exception as exc:
        require_grb = os.environ.get("EGGLAB_REQUIRE_GRB", "").lower()
        if require_grb in {"1", "true", "yes", "on"}:
            raise RuntimeError(
                "Gurobi is required (EGGLAB_REQUIRE_GRB is set) but could not "
                "be initialized"
            ) from exc
        return "CBC"


_BACKEND_CACHE: list = []


def backend() -> str:
    if not _BACKEND_CACHE:
        _BACKEND_CACHE.append(detect_backend())
    return _BACKEND_CACHE[0]


@dataclass
class SolveStats:
    backend: str = ""
    status: str = ""
    obj: float | None = None
    bound: float | None = None
    mip_gap: float | None = None
    lp_obj: float | None = None  # root LP relaxation value
    lp_mip_gap_abs: float | None = None  # obj - lp_obj (integrality gap witness)
    wall_s: float = 0.0
    lp_wall_s: float = 0.0
    n_vars: int = 0
    n_int: int = 0
    n_constrs: int = 0
    max_mip_gap: float = 0.0
    time_limit_s: float | None = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def new_model(name: str = "m") -> mip.Model:
    m = mip.Model(name=name, sense=mip.MINIMIZE, solver_name=backend())
    m.verbose = 0
    return m


def optimize(
    m: mip.Model,
    max_mip_gap: float = 1e-6,
    time_limit_s: float | None = None,
    solve_lp_first: bool = True,
) -> SolveStats:
    st = SolveStats(backend=backend(), max_mip_gap=max_mip_gap, time_limit_s=time_limit_s)
    st.n_vars = m.num_cols
    st.n_constrs = m.num_rows
    st.n_int = m.num_int

    # cluster resource hygiene: honor the Slurm CPU allocation so a solve
    # never silently uses the whole node; record what was applied
    cpus = os.environ.get("SLURM_CPUS_PER_TASK")
    if cpus:
        try:
            m.threads = int(cpus)
        except (TypeError, ValueError):
            pass
    st.extra["threads"] = getattr(m, "threads", None)

    if solve_lp_first:
        t0 = time.time()
        with _silence_native_output():
            lp_status = m.optimize(relax=True)
        st.lp_wall_s = time.time() - t0
        if lp_status in (mip.OptimizationStatus.OPTIMAL,):
            st.lp_obj = float(m.objective_value)

    m.max_mip_gap = max_mip_gap
    t0 = time.time()
    with _silence_native_output():
        if time_limit_s is not None:
            status = m.optimize(max_seconds=time_limit_s)
        else:
            status = m.optimize()
    st.wall_s = time.time() - t0
    st.status = status.name
    if m.num_solutions > 0:
        st.obj = float(m.objective_value)
    try:
        st.bound = float(m.objective_bound)
    except Exception:
        st.bound = None
    if st.obj is not None and st.bound is not None and abs(st.obj) > 1e-12:
        st.mip_gap = abs(st.obj - st.bound) / max(1e-12, abs(st.obj))
    if st.obj is not None and st.lp_obj is not None:
        st.lp_mip_gap_abs = st.obj - st.lp_obj
    return st
