"""Shared, pure replay of B3 pilot primitive evidence.

The audit and analyzer both call this module.  Stored histories, outcome
labels, convergence flags, and summary bounds are consistency witnesses only;
the certified CH bounds are rebuilt from chronological RMP/oracle events and
the dictator certificate is rebuilt from its recorded subsolve bounds.
"""
from __future__ import annotations

import json
import hashlib
import math
import os
import shutil
import stat
import subprocess
import os
import stat
from pathlib import Path

import experiments.b3_factor_pilot as bp

NUM_TOL = 1e-9
UB_MONO_TOL = 2e-3


class EvidenceError(ValueError):
    """Primitive evidence is malformed, incomplete, or contradictory."""


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def strict_json_loads(raw: bytes, label: str) -> object:
    """Decode UTF-8 JSON while refusing duplicate object keys."""
    try:
        text = raw.decode("utf-8")
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, EvidenceError) as exc:
        raise EvidenceError(f"{label}: malformed JSON: {exc}") from exc


def read_regular_bytes_with_signature(
    path: Path,
    label: str,
) -> tuple[bytes, tuple[int, int, int, int, int]]:
    """Read once and return the stable opened inode's identity signature."""
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise EvidenceError(f"{label}: unreadable regular file: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise EvidenceError(f"{label}: not a regular file")
        # O_NONBLOCK exists only so that a transiently substituted FIFO cannot
        # block the open forever.  Once the descriptor is known to be a regular
        # file, clear it: a non-blocking read can legally return None, which
        # would surface as a TypeError instead of a clean refusal.
        if hasattr(os, "O_NONBLOCK"):
            import fcntl
            fcntl.fcntl(descriptor, fcntl.F_SETFL,
                        fcntl.fcntl(descriptor, fcntl.F_GETFL)
                        & ~os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            raw = handle.read()
        after = os.fstat(descriptor)
        signature = lambda info: (
            info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_nlink)
        if signature(before) != signature(after) or len(raw) != before.st_size:
            raise EvidenceError(f"{label}: changed while being read")
        return raw, signature(after)
    finally:
        os.close(descriptor)


# --------------------------------------------------------------------------
# provenance: re-exported from the dependency-free runner so that the run
# producer can share it (see experiments/provenance_git.py)
# --------------------------------------------------------------------------
from experiments.provenance_git import (          # noqa: E402
    assert_no_history_rewrites as _pg_assert_no_history_rewrites,
    TRUSTED_PATH,
    ProvenanceError,
    git_argv,
    git_dir,
    git_env,
    trusted_git,
)


def assert_no_history_rewrites(repo_root) -> None:
    """See provenance_git; re-raised as EvidenceError for callers here."""
    try:
        _pg_assert_no_history_rewrites(repo_root)
    except ProvenanceError as exc:
        raise EvidenceError(str(exc)) from exc



def read_regular_bytes_once(path: Path, label: str, *,
                            expected_sha256: str | None = None) -> bytes:
    """Read one stable regular file through a no-follow descriptor exactly once.

    ``expected_sha256`` makes the read TOCTOU-proof AT THE POINT OF
    CONSUMPTION: the bytes that are hashed are the same buffer that is
    returned and parsed, so substituting the file and restoring it afterwards
    cannot change what was consumed without being detected here.  Verifying a
    path again later cannot achieve this -- a swap-and-restore defeats it.
    """
    data = read_regular_bytes_with_signature(path, label)[0]
    if expected_sha256 is not None:
        seen = hashlib.sha256(data).hexdigest()
        if seen != expected_sha256:
            raise EvidenceError(
                f"{label}: consumed content digest {seen} does not match the "
                f"frozen inventory digest {expected_sha256}")
    return data


def read_json_object_once(path: Path, label: str, *,
                          expected_sha256: str | None = None) -> dict:
    value = strict_json_loads(
        read_regular_bytes_once(path, label, expected_sha256=expected_sha256),
        label)
    if not isinstance(value, dict):
        raise EvidenceError(f"{label}: JSON root is not an object")
    return value


def _finite(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _close(actual, expected, tolerance: float = NUM_TOL) -> bool:
    return (_finite(actual) and _finite(expected)
            and abs(float(actual) - float(expected)) <= tolerance)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def replay_ch_bounds(
    checkpoint: dict,
    *,
    tag: str,
    expected_instance_hash: str,
    expected_market_hash: str,
    manifest_solver: dict,
) -> dict:
    """Rebuild CH bounds from chronological RMP/oracle evidence."""
    _require(isinstance(checkpoint, dict), "A2 checkpoint is not an object")
    _require(checkpoint.get("done") is True, "A2 checkpoint is not done")
    identity = checkpoint.get("identity")
    _require(isinstance(identity, dict), "A2 identity is missing")
    method = identity.get("method", bp.METHOD)
    bp.assert_no_a6(method)
    _require(method == bp.METHOD, f"method {method!r} != a2")
    _require(identity.get("instance_hash") == expected_instance_hash,
             "A2 instance hash drift vs frozen screen")
    _require(identity.get("market_hash") == expected_market_hash,
             "A2 market hash != run manifest (missing/altered)")
    _require(identity.get("epsilon") == bp.EPSILON,
             f"identity epsilon {identity.get('epsilon')!r} != frozen "
             f"{bp.EPSILON}")
    _require(identity.get("budget") == bp.BUDGET,
             f"identity budget {identity.get('budget')!r} != frozen "
             f"{bp.BUDGET}")
    _require(identity.get("tol_d") == bp.TOL_D,
             f"identity tol_d {identity.get('tol_d')!r} != frozen "
             f"{bp.TOL_D}")
    solver_identity = identity.get("solver")
    _require(isinstance(solver_identity, dict),
             "A2 solver identity is missing")
    _require(
        solver_identity.get("backend") == manifest_solver.get("backend")
        and solver_identity.get("max_mip_gap") == manifest_solver.get(
            "mip_gap"),
        "CG solver identity != run manifest solver")

    events = checkpoint.get("oracle_events")
    iterations = checkpoint.get("iteration_events")
    ub_history = checkpoint.get("ub_history")
    lb_history = checkpoint.get("lb_history")
    _require(isinstance(events, list) and events,
             "committed oracle events are missing")
    _require(isinstance(iterations, list) and iterations,
             "iteration events are missing")
    _require(isinstance(ub_history, list) and isinstance(lb_history, list),
             "bound histories are missing")
    _require(len(ub_history) == len(iterations)
             and len(lb_history) == len(iterations),
             "bound history length differs from iteration evidence")
    _require(len(events) == len(iterations) + 1,
             f"{len(events)} committed oracle events != seed + "
             f"{len(iterations)} priced iterations")

    seen_oracle_ids = set()
    for index, event in enumerate(events):
        _require(isinstance(event, dict),
                 f"oracle event {index} is malformed")
        call_id = (event.get("extra") or {}).get("call_id")
        _require(isinstance(call_id, str) and call_id
                 and call_id not in seen_oracle_ids,
                 "oracle event without a unique call_id")
        seen_oracle_ids.add(call_id)
        solver = event.get("solver")
        _require(isinstance(solver, dict),
                 f"oracle event {call_id} solver evidence is missing")
        _require(solver.get("status") == "OPTIMAL",
                 f"oracle event {call_id} status "
                 f"{solver.get('status')!r} != OPTIMAL")
        _require(solver.get("backend") == manifest_solver.get("backend"),
                 f"oracle event {call_id} solver identity != run manifest")
        _require(event.get("replay_ok") is True,
                 f"oracle event {call_id} replay_ok is not true")
        _require(event.get("replay_violations") in (None, []),
                 f"oracle event {call_id} carries replay violations")

    lb_best = -math.inf
    previous_ub = math.inf
    seen_master_ids = set()
    for index, iteration in enumerate(iterations):
        _require(isinstance(iteration, dict),
                 f"iteration {index} is malformed")
        _require(not iteration.get("terminal"),
                 f"iteration {index} is terminal in a certified checkpoint")
        _require(iteration.get("phase") == "clean",
                 f"iteration {index} is not clean A2 evidence")
        _require(iteration.get("replay_ok") is True,
                 f"iteration {index} replay_ok is not true")
        _require(iteration.get("oracle_calls") == index + 1,
                 f"iteration {index} oracle-call index is inconsistent")

        z_rmp = iteration.get("z_rmp_model")
        ub_ch = iteration.get("ub_ch")
        sigma = iteration.get("duals_sigma")
        _require(_finite(z_rmp) and _finite(ub_ch) and _finite(sigma),
                 f"iteration {index}: nonfinite RMP evidence")
        _require(ub_ch <= previous_ub + UB_MONO_TOL,
                 f"iteration {index}: UB_CH increased "
                 f"{previous_ub} -> {ub_ch}")
        previous_ub = float(ub_ch)

        master_solves = iteration.get("master_solves")
        _require(isinstance(master_solves, list) and master_solves,
                 f"iteration {index}: RMP solve evidence is missing")
        for solve in master_solves:
            _require(isinstance(solve, dict),
                     f"iteration {index}: malformed RMP solve evidence")
            solve_id = solve.get("solve_id")
            _require(isinstance(solve_id, str) and solve_id
                     and solve_id not in seen_master_ids,
                     f"iteration {index}: duplicate/missing RMP solve_id")
            seen_master_ids.add(solve_id)
            _require(solve.get("backend") == manifest_solver.get("backend")
                     and solve.get("status") == "OPTIMAL",
                     f"iteration {index}: RMP solver identity/status mismatch")
            _require(solve.get("n_int") == 0,
                     f"iteration {index}: RMP evidence is not an LP")
        final_master = master_solves[-1]
        _require(_close(final_master.get("obj"), z_rmp),
                 f"iteration {index}: z_rmp_model does not match final RMP "
                 "solver objective")
        _require(_close(final_master.get("bound"), z_rmp),
                 f"iteration {index}: final RMP solver bound does not match "
                 "z_rmp_model")
        pwl_tol = iteration.get("pwl_tol")
        _require(_finite(pwl_tol) and pwl_tol >= 0,
                 f"iteration {index}: RMP PWL tolerance is missing")
        _require(float(ub_ch) + NUM_TOL >= float(z_rmp)
                 and float(ub_ch) - float(z_rmp)
                 <= float(pwl_tol) + NUM_TOL,
                 f"iteration {index}: ub_ch is not certified by the RMP "
                 "objective/PWL evidence")
        _require(iteration.get("epsilon") == bp.EPSILON,
                 f"iteration {index}: epsilon differs from the frozen design")

        oracle = events[index + 1]
        call_id = iteration.get("pricing_solve_id")
        _require(isinstance(call_id, str)
                 and (oracle.get("extra") or {}).get("call_id") == call_id,
                 f"iteration {index}: pricing_solve_id does not match the "
                 "chronological oracle event")
        oracle_bound = (oracle.get("solver") or {}).get("bound")
        _require(_finite(oracle_bound),
                 f"iteration {index}: oracle solver bound is nonfinite")
        min_reduced_cost_lb = float(oracle_bound) - float(sigma)
        _require(_close(iteration.get("min_reduced_cost_lb"),
                        min_reduced_cost_lb),
                 f"iteration {index}: min_reduced_cost_lb does not replay "
                 "from oracle bound - duals_sigma")
        oracle_rc = (oracle.get("extra") or {}).get(
            "min_reduced_cost_lb")
        _require(_close(oracle_rc, min_reduced_cost_lb),
                 f"iteration {index}: oracle-side min_reduced_cost_lb "
                 "does not replay")
        lb_ch = float(z_rmp) + min(0.0, min_reduced_cost_lb)
        _require(_close(iteration.get("lb_ch"), lb_ch),
                 f"iteration {index}: lb_ch != replayed RMP/oracle bound")
        lb_best = max(lb_best, lb_ch)
        _require(_close(iteration.get("lb_best"), lb_best),
                 f"iteration {index}: lb_best != replayed bound")
        _require(_close(iteration.get("certificate_gap"),
                        float(ub_ch) - lb_best),
                 f"iteration {index}: certificate gap does not replay")
        _require(_close(ub_history[index], ub_ch)
                 and _close(lb_history[index], lb_best),
                 f"iteration {index}: CH history edited; recorded bounds "
                 "differ from primitive replay")

    _require(_finite(lb_best), "primitive replay produced no finite lb_CH")
    _require(_close(checkpoint.get("lb_best"), lb_best),
             "checkpoint lb_best != primitive replay")
    oracle_calls = checkpoint.get("oracle_calls")
    _require(isinstance(oracle_calls, int)
             and not isinstance(oracle_calls, bool)
             and oracle_calls == len(events),
             f"oracle_calls {oracle_calls!r} != committed events "
             f"({len(events)})")
    _require(oracle_calls <= bp.BUDGET,
             f"oracle_calls {oracle_calls} exceeds the frozen budget "
             f"{bp.BUDGET}")

    outcome = checkpoint.get("outcome")
    _require(isinstance(outcome, dict), "A2 outcome is missing")
    _require(outcome.get("type") == "certified"
             and outcome.get("certified") is True,
             "A2 not certified within budget (INVALID/HALT)")
    _require(outcome.get("method") == bp.METHOD,
             "A2 outcome method differs from a2")
    _require(outcome.get("oracle_calls") == oracle_calls,
             "A2 outcome oracle_calls differs from committed events")
    _require(_close(outcome.get("ub_ch"), previous_ub)
             and _close(outcome.get("lb_best"), lb_best),
             "A2 outcome bounds != primitive replay")
    ch_gap = previous_ub - lb_best
    _require(_close(outcome.get("gap"), ch_gap),
             "A2 outcome gap != primitive replay")
    _require(ch_gap <= bp.EPSILON + NUM_TOL,
             f"replayed certificate gap {ch_gap:.6g} > epsilon "
             f"{bp.EPSILON}")
    _require(lb_best <= previous_ub + NUM_TOL,
             f"lb_CH {lb_best} > ub_CH {previous_ub}")
    return {
        "ub_ch": previous_ub,
        "lb_ch": lb_best,
        "ch_gap": ch_gap,
        "oracle_calls": oracle_calls,
        "solver_backend": manifest_solver.get("backend"),
        "solver_mip_gap": manifest_solver.get("mip_gap"),
    }


def replay_dictator(
    checkpoint: dict,
    *,
    cell: dict,
    expected_instance_hash: str,
    expected_market_hash: str,
    screen_record_sha256: str,
    run_manifest_sha256: str,
    run_commit: str,
    manifest_solver: dict,
) -> dict:
    """Rebuild the dictator bound certificate from committed subsolves."""
    _require(isinstance(checkpoint, dict),
             "dictator checkpoint is not an object")
    identity = checkpoint.get("identity")
    _require(isinstance(identity, dict), "dictator identity is missing")
    expected_identity = {
        "instance_hash": expected_instance_hash,
        "market_hash": expected_market_hash,
        "screen_record_sha256": screen_record_sha256,
        "run_manifest_sha256": run_manifest_sha256,
        "run_commit": run_commit,
        "setting": cell["setting"],
        "tol_d": bp.TOL_D,
        "experiment": "b3-factor-pilot",
    }
    identity_labels = {
        "run_manifest_sha256": "run-manifest SHA",
        "screen_record_sha256": "screen SHA",
        "instance_hash": "instance hash",
        "market_hash": "market hash",
        "run_commit": "run commit",
        "tol_d": "tol_d",
        "experiment": "experiment",
        "setting": "setting",
    }
    for field, expected in expected_identity.items():
        _require(identity.get(field) == expected,
                 f"dictator {identity_labels[field]} identity mismatch")
    solver_identity = identity.get("solver")
    _require(isinstance(solver_identity, dict)
             and solver_identity.get("backend")
             == manifest_solver.get("backend")
             and solver_identity.get("max_mip_gap")
             == manifest_solver.get("mip_gap"),
             "dictator solver identity != run manifest solver")

    _require(checkpoint.get("status") == "OPTIMAL",
             f"dictator status {checkpoint.get('status')!r} != OPTIMAL")
    _require(checkpoint.get("tol_d") == bp.TOL_D,
             f"dictator tol_d differs from frozen {bp.TOL_D}")
    z_d_ub = checkpoint.get("z_d_ub")
    z_d_lb = checkpoint.get("z_d_lb")
    _require(_finite(z_d_ub), "dictator z_d_ub missing/nonfinite")
    _require(_finite(z_d_lb), "dictator z_d_lb missing/nonfinite")
    _require(float(z_d_lb) <= float(z_d_ub) + NUM_TOL,
             "dictator z_d_lb > z_d_ub")

    adaptive = checkpoint.get("adaptive")
    _require(isinstance(adaptive, dict),
             "dictator adaptive evidence is missing")
    _require(_close(adaptive.get("adaptive_ub"), z_d_ub),
             "dictator z_d_ub != recorded adaptive_ub")
    _require(_close(adaptive.get("adaptive_lb"), z_d_lb),
             "dictator z_d_lb != recorded adaptive_lb")
    dictator_gap = float(z_d_ub) - float(z_d_lb)
    _require(_close(adaptive.get("adaptive_gap_abs"), dictator_gap),
             "dictator adaptive_gap_abs inconsistent with endpoints")
    _require(adaptive.get("adaptive_tol_abs") == bp.TOL_D,
             "dictator adaptive tolerance differs from tol_d")
    _require(adaptive.get("adaptive_converged") is True,
             "dictator adaptive certification unconverged")
    _require(dictator_gap <= bp.TOL_D + NUM_TOL,
             f"recomputed dictator gap {dictator_gap:.6g} > tol_d "
             f"{bp.TOL_D}")

    rounds = adaptive.get("adaptive_rounds")
    solve_stats = adaptive.get("adaptive_solve_stats")
    _require(isinstance(rounds, int) and not isinstance(rounds, bool)
             and rounds > 0 and isinstance(solve_stats, list)
             and rounds == len(solve_stats),
             "dictator adaptive subsolve history is malformed")
    certified_bounds = []
    for index, solve in enumerate(solve_stats, start=1):
        _require(isinstance(solve, dict) and solve.get("round") == index,
                 f"dictator adaptive subsolve {index} is malformed")
        _require(solve.get("status") == "OPTIMAL"
                 and solve.get("backend") == manifest_solver.get("backend"),
                 f"dictator adaptive subsolve {index} solver identity/status "
                 "mismatch")
        bound = solve.get("bound")
        incumbent = solve.get("incumbent")
        _require(_finite(bound) and _finite(incumbent),
                 f"dictator adaptive subsolve {index} has nonfinite bounds")
        _require(float(bound) <= float(incumbent) + NUM_TOL,
                 f"dictator adaptive subsolve {index} bound > incumbent")
        _require(_close(solve.get("gap"),
                        float(incumbent) - float(bound)),
                 f"dictator adaptive subsolve {index} gap does not replay")
        certified_bounds.append(float(bound))
    _require(_close(max(certified_bounds), z_d_lb),
             "dictator z_d_lb does not replay from adaptive subsolve bounds")

    record = checkpoint.get("record")
    _require(isinstance(record, dict),
             "dictator record replay invalid or missing")
    _require(record.get("replay_ok") is True,
             "dictator record replay invalid: replay_ok is not true")
    _require(record.get("replay_violations") == [],
             "dictator record carries replay violations")
    _require(record.get("experiment") == "b3-factor-pilot"
             and record.get("regime") == "dictator",
             "dictator record experiment/regime mismatch")
    _require(record.get("instance_hash") == expected_instance_hash,
             "dictator record instance hash mismatch")
    _require(_close(record.get("obj_true"), z_d_ub),
             "dictator record obj_true != z_d_ub")
    record_extra = record.get("extra")
    _require(isinstance(record_extra, dict)
             and record_extra.get("tag") == cell["tag"]
             and record_extra.get("cell") == [
                 cell["setting"], cell["seed"], cell["n_trips"], cell["b"]]
             and record_extra.get("setting") == cell["setting"]
             and record_extra.get("screen_record_sha256")
             == screen_record_sha256,
             "dictator record cell/screen identity mismatch")
    record_solver = record.get("solver")
    _require(isinstance(record_solver, dict)
             and record_solver.get("status") == "OPTIMAL"
             and record_solver.get("backend") == manifest_solver.get("backend"),
             "dictator record solver identity/status mismatch")
    _require(_finite(record_solver.get("bound")),
             "dictator record solver bound missing/nonfinite")
    record_adaptive = record_solver.get("extra")
    _require(isinstance(record_adaptive, dict),
             "dictator record adaptive evidence is missing")
    for field in (
            "adaptive_ub", "adaptive_lb", "adaptive_gap_abs",
            "adaptive_tol_abs", "adaptive_rounds", "adaptive_solve_stats",
            "adaptive_converged"):
        _require(record_adaptive.get(field) == adaptive.get(field),
                 f"dictator checkpoint/record {field} mismatch")
    _require(_close(checkpoint.get("bound"), record_solver.get("bound")),
             "dictator checkpoint/record solver bound mismatch")
    return {
        "z_d_ub": float(z_d_ub),
        "z_d_lb": float(z_d_lb),
        "dictator_gap": dictator_gap,
    }


def replay_cell_evidence(
    cg_checkpoint: dict,
    dictator_checkpoint: dict,
    *,
    cell: dict,
    expected_instance_hash: str,
    expected_market_hash: str,
    screen_record_sha256: str,
    run_manifest_sha256: str,
    run_commit: str,
    manifest_solver: dict,
) -> tuple[dict | None, list[str]]:
    """Replay one cell and return normalized primitive evidence or problems."""
    tag = cell["tag"]
    try:
        ch = replay_ch_bounds(
            cg_checkpoint,
            tag=tag,
            expected_instance_hash=expected_instance_hash,
            expected_market_hash=expected_market_hash,
            manifest_solver=manifest_solver,
        )
        dictator = replay_dictator(
            dictator_checkpoint,
            cell=cell,
            expected_instance_hash=expected_instance_hash,
            expected_market_hash=expected_market_hash,
            screen_record_sha256=screen_record_sha256,
            run_manifest_sha256=run_manifest_sha256,
            run_commit=run_commit,
            manifest_solver=manifest_solver,
        )
        cg_z_d_ub = (cg_checkpoint.get("identity") or {}).get("z_d_ub")
        _require(_close(cg_z_d_ub, dictator["z_d_ub"], 1e-12),
                 "CG identity z_d_ub != dictator z_d_ub")

        u_lo_raw = dictator["z_d_lb"] - ch["ub_ch"]
        u_lo = max(0.0, u_lo_raw)
        u_hi = dictator["z_d_ub"] - ch["lb_ch"]
        width = u_hi - u_lo_raw
        _require(u_hi >= -1e-6,
                 f"U_hi {u_hi:.6g} < 0 beyond tolerance")
        _require(u_hi >= u_lo_raw - NUM_TOL,
                 "U_hi < U_lo_raw (interval inversion)")
        _require(u_lo <= u_hi,
                 f"impossible tightened interval [{u_lo:.6g}, "
                 f"{u_hi:.6g}] (lo > hi)")
        _require(width <= bp.TOL_D + bp.EPSILON + NUM_TOL,
                 f"width(U) {width:.6g} > tol_d+epsilon "
                 f"{bp.TOL_D + bp.EPSILON}")
        return {
            **ch,
            **dictator,
            "u_lo_raw": u_lo_raw,
            "u_lo": u_lo,
            "u_hi": u_hi,
            "width": width,
        }, []
    except (EvidenceError, KeyError, TypeError, ValueError) as exc:
        return None, [f"{tag}: {exc}"]
