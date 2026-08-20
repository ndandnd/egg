#!/usr/bin/env python3
"""Preregistered analyzer for the B3 internal-uplift factor pilot.

Implements, exactly, Sections 1.1, 5, 6, and 7 of
``doc/B3_FACTOR_PILOT_SPEC_DRAFT.md``.  It is written and committed
BEFORE any development outcome exists: every threshold, direction sign,
contrast-selection rule, and decision state is frozen here, and the
analyzer refuses to score anything but a complete, valid, frozen-bound
population.

Per cell it forms the certified uplift interval
``U = [U_lo_raw, U_hi]`` with the theorem-tightened ``max(0, U_lo_raw)``,
preferring the recorded dictator lower bound ``z_D_lb`` for ``U_lo_raw``
(the ``(z_D_ub - tol_d)`` proxy is a documented fallback), the per-trip
normalization, and the cost-fraction interval only when ``lb_CH > 0``.

Per ``(seed, n, b)`` it forms the four matched factor-minus-baseline
interval contrasts ``Delta_f = U_f - U_0``, then applies the ordered,
mutually exclusive decision taxonomy: ``DESIGN-NOT-FROZEN`` (screen not
frozen / binding failure), ``INVALID/HALT`` (engineering/validity
failure), ``UNDER-RESOLVED`` (``|med_{f*}| <= tau_Delta``), ``GO``
(``med_{f*} > tau_Delta`` and ``count_{f*} >= 9/12``), or ``NO-GO``.

It launches nothing, reads no A6 path, and — until a reviewed run
exists — is exercised only on synthetic fixtures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.b3_factor_pilot as bp

SCHEMA = "b3-factor-pilot-analysis-v1"
REPO_ROOT = bp.REPO_ROOT
SPEC_RELPATH = "doc/B3_FACTOR_PILOT_SPEC_DRAFT.md"
PROVENANCE_FILES = (
    "src/experiments/analyze_b3_factor_pilot.py",
    "src/experiments/b3_factor_pilot.py",
    SPEC_RELPATH,
    "src/tests/test_b3_factor_pilot.py",
)

# frozen direction signs (spec Section 6): +1 non-negative direction, -1
# non-positive direction.  S0 is the shared baseline (no direction).
DIRECTION_SIGN = {
    "S1_batt_low": +1,
    "S2_batt_high": -1,
    "S3_pow_low": +1,
    "S4_pow_high": -1,
}
FACTOR_ORDER = ("S1_batt_low", "S2_batt_high", "S3_pow_low", "S4_pow_high")
BASELINE_SETTING = "S0_baseline"
TAU_DELTA = bp.TAU_DELTA                 # 0.04 SEK (spec 6)
COUNT_GATE = 9                           # of 12 (development engineering gate)
WIDTH_BOUND = bp.TOL_D + bp.EPSILON      # width(U) <= tol_d + epsilon


class B3AnalysisError(RuntimeError):
    pass


def sha256_file(path: str | os.PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def refuse_a6_paths(*paths: str | os.PathLike) -> None:
    for path in paths:
        resolved = Path(path).resolve()
        for part in resolved.parts:
            lowered = part.lower()
            if lowered.startswith("a6") or "a6_" in lowered:
                raise B3AnalysisError(
                    f"refusing A6 path (scientific boundary): {resolved}")


def assert_output_separation(input_dir, out_base) -> None:
    inp = Path(input_dir).resolve()
    out = Path(out_base).resolve()
    if out == inp or inp in out.parents or out in inp.parents:
        raise B3AnalysisError(
            f"output root {out} must be strictly separated from the input "
            f"root {inp}")


def verify_analysis_code_commit(claimed: str) -> bool:
    if (not claimed or len(claimed) != 40
            or not all(c in "0123456789abcdef" for c in claimed)):
        raise B3AnalysisError(
            "analysis-code-commit must be the full 40-character lowercase "
            "hexadecimal SHA")
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{claimed}^{{commit}}"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise B3AnalysisError(f"claimed commit {claimed} does not resolve") \
            from exc
    if resolved != claimed:
        raise B3AnalysisError(f"claimed commit {claimed} resolves to {resolved}")
    if subprocess.run(
            ["git", "merge-base", "--is-ancestor", claimed, "HEAD"],
            cwd=REPO_ROOT).returncode != 0:
        raise B3AnalysisError(
            f"claimed commit {claimed} is not an ancestor of HEAD")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT).decode()
    if [ln for ln in dirty.splitlines() if not ln.startswith("??")]:
        raise B3AnalysisError(
            "working tree has tracked modifications; commit the analyzer "
            "before generating artifacts")
    for relpath in PROVENANCE_FILES:
        committed = subprocess.check_output(
            ["git", "show", f"{claimed}:{relpath}"], cwd=REPO_ROOT)
        if committed != (REPO_ROOT / relpath).read_bytes():
            raise B3AnalysisError(
                f"{relpath} differs from the claimed commit {claimed}; "
                "artifacts would be misattributed")
    return True


# --------------------------------------------------------------------------
# per-cell certified uplift interval (spec 1.1)
# --------------------------------------------------------------------------
def _finite(x) -> bool:
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and math.isfinite(x))


def cell_interval(ub_ch: float, lb_ch: float, z_d_ub: float,
                  z_d_lb: float | None, n_trips: int) -> dict:
    """The certified interval U=[U_lo_raw, U_hi] with the preferred z_D_lb
    endpoint, theorem tightening, per-trip normalization, and the rigorous
    cost-fraction interval only when lb_CH > 0."""
    if z_d_lb is not None and _finite(z_d_lb):
        u_lo_raw = z_d_lb - ub_ch
        lo_endpoint = "z_D_lb"
    else:
        u_lo_raw = (z_d_ub - bp.TOL_D) - ub_ch
        lo_endpoint = "proxy"
    u_hi = z_d_ub - lb_ch
    interval = {
        "ub_ch": ub_ch, "lb_ch": lb_ch, "z_d_ub": z_d_ub, "z_d_lb": z_d_lb,
        "U_lo_raw": u_lo_raw, "U_lo": max(0.0, u_lo_raw), "U_hi": u_hi,
        "width": u_hi - u_lo_raw, "lo_endpoint": lo_endpoint,
        "U_lo_raw_per_trip": u_lo_raw / n_trips,
        "U_hi_per_trip": u_hi / n_trips,
    }
    if lb_ch > 0:
        interval["cost_fraction"] = [max(0.0, u_lo_raw) / ub_ch, u_hi / lb_ch]
    else:
        interval["cost_fraction"] = None
    return interval


def _load(path: Path):
    with open(path) as handle:
        return json.load(handle)


NUM_TOL = 1e-9
UB_MONO_TOL = 1e-9


def _replay_cg_bounds(ck: dict, tag: str) -> tuple:
    """Replay ``ub_ch``/``lb_best`` from the CHRONOLOGICAL iteration/oracle
    event logs (the standing project lesson: never trust stored summary
    labels).  Every entry of the recorded bound histories must equal the
    replayed value; every clean iteration must reference a distinct oracle
    event whose certified solver bound reproduces ``lb_ch = z_rmp +
    min(0, bound - sigma)`` exactly.

    Returns ``(ub_ch, lb_best, problems)``; the bounds are ``None`` when
    replay failed."""
    problems: list[str] = []
    events = ck.get("oracle_events") or []
    iterations = ck.get("iteration_events") or []
    ub_hist = ck.get("ub_history") or []
    lb_hist = ck.get("lb_history") or []
    seen_ids: set = set()
    for event in events:
        call_id = ((event or {}).get("extra") or {}).get("call_id")
        if not isinstance(call_id, str) or call_id in seen_ids:
            problems.append(f"{tag}: oracle event without a unique call_id")
            return None, None, problems
        seen_ids.add(call_id)
    if not iterations:
        problems.append(f"{tag}: no iteration events to replay")
        return None, None, problems
    if len(ub_hist) != len(iterations) or len(lb_hist) != len(iterations):
        problems.append(
            f"{tag}: bound history length ({len(ub_hist)}/{len(lb_hist)}) "
            f"!= iteration events ({len(iterations)}) — history edited")
        return None, None, problems
    # chronological binding: events[0] is the seed call; the k-th priced
    # iteration binds POSITIONALLY to events[k+1], whose call_id must equal
    # the iteration's pricing_solve_id (no unreferenced or reordered calls)
    priced_count = sum(1 for it in iterations
                       if not (it or {}).get("terminal"))
    if len(events) != priced_count + 1:
        problems.append(
            f"{tag}: {len(events)} committed oracle events != seed + "
            f"{priced_count} priced iterations — event log edited")
        return None, None, problems
    lb_best = -math.inf
    prev_ub = math.inf
    priced_seen = 0
    for index, it in enumerate(iterations):
        it = it or {}
        ub = it.get("ub_ch")
        if not _finite(ub):
            problems.append(f"{tag}: iteration {index}: nonfinite ub_ch")
            return None, None, problems
        if ub > prev_ub + UB_MONO_TOL:
            problems.append(
                f"{tag}: iteration {index}: UB_CH increased "
                f"{prev_ub} -> {ub}")
            return None, None, problems
        prev_ub = ub
        if it.get("terminal"):
            if index != len(iterations) - 1:
                problems.append(
                    f"{tag}: terminal iteration event is not last")
                return None, None, problems
        else:
            priced_seen += 1
            oracle = events[priced_seen]
            call_id = it.get("pricing_solve_id")
            if (not isinstance(call_id, str)
                    or ((oracle or {}).get("extra") or {}).get("call_id")
                    != call_id):
                problems.append(
                    f"{tag}: iteration {index}: pricing_solve_id "
                    f"{call_id!r} != chronological oracle event "
                    f"{priced_seen}")
                return None, None, problems
            bound = (oracle.get("solver") or {}).get("bound")
            sigma = it.get("duals_sigma")
            z_rmp = it.get("z_rmp_model")
            if not (_finite(bound) and _finite(sigma) and _finite(z_rmp)):
                problems.append(
                    f"{tag}: iteration {index}: nonfinite replay evidence "
                    "(solver bound / duals_sigma / z_rmp_model)")
                return None, None, problems
            min_rc_lb = bound - sigma
            if it.get("min_reduced_cost_lb") != min_rc_lb:
                problems.append(
                    f"{tag}: iteration {index}: min_reduced_cost_lb "
                    f"{it.get('min_reduced_cost_lb')!r} != replayed "
                    f"{min_rc_lb!r} from the oracle solver bound")
                return None, None, problems
            oracle_rc = (oracle.get("extra") or {}).get(
                "min_reduced_cost_lb")
            if oracle_rc is not None and oracle_rc != min_rc_lb:
                problems.append(
                    f"{tag}: iteration {index}: oracle-side "
                    "min_reduced_cost_lb disagrees with replay")
                return None, None, problems
            lb_ch = z_rmp + min(0.0, min_rc_lb)
            if it.get("lb_ch") != lb_ch:
                problems.append(
                    f"{tag}: iteration {index}: lb_ch {it.get('lb_ch')!r} "
                    f"!= replayed {lb_ch!r}")
                return None, None, problems
            lb_best = max(lb_best, lb_ch)
            if it.get("lb_best") != lb_best:
                problems.append(
                    f"{tag}: iteration {index}: lb_best "
                    f"{it.get('lb_best')!r} != replayed {lb_best!r}")
                return None, None, problems
        if ub_hist[index] != ub or lb_hist[index] != lb_best:
            problems.append(
                f"{tag}: iteration {index}: recorded bound history "
                f"({ub_hist[index]!r}, {lb_hist[index]!r}) != replayed "
                f"({ub!r}, {lb_best!r}) — CH history edited")
            return None, None, problems
    if not _finite(lb_best):
        problems.append(f"{tag}: replay produced no finite lb_best")
        return None, None, problems
    return prev_ub, lb_best, problems


def load_population(runs_dir: str | os.PathLike, screen: dict,
                    market_by_cell: dict, run_manifest: dict) -> dict:
    """Read all 60 cells and, rather than trusting any recorded outcome or
    history field, REPLAY the certified bounds from the chronological
    oracle/iteration event logs, recompute the dictator certificate from
    its endpoints and committed record, and cross-bind everything to the
    run manifest (market hashes AND solver identity).  Any failure is
    collected as an INVALID/HALT problem (no cell is ever silently
    dropped).

    Rejections: edits to bound histories, iteration bound fields, or
    outcome bounds (all must equal the event replay); dropped/reordered
    oracle events; CG/dictator ``z_D`` mismatch; missing or altered market
    hashes; missing/nonfinite recorded ``z_D_lb``; non-OPTIMAL, unconverged,
    or gap-violating dictator evidence (the certificate is recomputed —
    the ``adaptive_converged`` flag is never trusted); invalid or missing
    dictator replay records; solver identities differing from the run
    manifest; oracle budgets exceeding the frozen 240; malformed JSON;
    ``U_hi < 0`` beyond tolerance, interval inversion, and impossible
    theorem-tightened intervals (``lo > hi``).
    """
    runs = Path(runs_dir)
    problems: list[str] = []
    cells: dict[tuple, dict] = {}
    manifest_solver = run_manifest.get("solver") or {}
    for cell in bp.build_cells():
        tag = cell["tag"]
        key = (cell["setting"], cell["seed"], cell["n_trips"], cell["b"])
        cdir = runs / tag
        cg_path = cdir / "a2.cg.ckpt.json"
        d_path = cdir / "dictator.ckpt.json"
        if not cg_path.is_file() or not d_path.is_file():
            problems.append(f"{tag}: missing checkpoint(s)")
            continue
        # malformed inputs are a structured INVALID/HALT, never a crash
        try:
            ck = _load(cg_path)
            dd = _load(d_path)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            problems.append(f"{tag}: malformed checkpoint JSON: {exc}")
            continue
        if not isinstance(ck, dict) or not isinstance(dd, dict):
            problems.append(f"{tag}: checkpoint JSON is not an object")
            continue
        ident = ck.get("identity") or {}
        expected_hash = screen["instance_hashes"][
            (cell["setting"], cell["seed"], cell["n_trips"])]
        expected_market = market_by_cell.get(key)
        if ident.get("method", "a2") != bp.METHOD:
            problems.append(f"{tag}: method {ident.get('method')!r} != a2")
        if ident.get("instance_hash") != expected_hash:
            problems.append(f"{tag}: instance-hash drift vs frozen screen")
        # market hash must be present and match the manifest, on BOTH sides
        if expected_market is None:
            problems.append(f"{tag}: market hash missing from run manifest")
        if ident.get("market_hash") != expected_market:
            problems.append(f"{tag}: CG market hash != manifest (missing/altered)")
        if (dd.get("identity") or {}).get("market_hash") != expected_market:
            problems.append(f"{tag}: dictator market hash != manifest")

        oc = ck.get("outcome") or {}
        if not (oc.get("type") == "certified" and oc.get("certified")):
            problems.append(
                f"{tag}: A2 not certified within budget (INVALID/HALT)")
            continue

        # BLOCKER repair: replay UB/LB from the chronological oracle and
        # iteration event logs — the recorded bound histories and outcome
        # fields must all equal the replay (editing CH histories with
        # unchanged solver evidence must be impossible)
        ub_ch, lb_ch, replay_problems = _replay_cg_bounds(ck, tag)
        if replay_problems:
            problems.extend(replay_problems)
            continue
        for label, recomputed, recorded in (
                ("ub_ch", ub_ch, oc.get("ub_ch")),
                ("lb_best", lb_ch, oc.get("lb_best"))):
            if not _finite(recorded) or abs(recomputed - recorded) > NUM_TOL:
                problems.append(
                    f"{tag}: outcome {label} {recorded} != replayed "
                    f"{recomputed} (single-field edit)")
        if not _finite(oc.get("gap")) or abs(
                oc["gap"] - (ub_ch - lb_ch)) > NUM_TOL:
            problems.append(f"{tag}: outcome gap != ub_ch - lb_best")
        epsilon = ident.get("epsilon")
        if not _finite(epsilon) or epsilon != bp.EPSILON:
            problems.append(
                f"{tag}: identity epsilon {epsilon!r} != frozen "
                f"{bp.EPSILON}")
            continue
        if ub_ch - lb_ch > epsilon + NUM_TOL:
            problems.append(
                f"{tag}: replayed certificate gap {ub_ch - lb_ch:.6g} > "
                f"epsilon {epsilon} yet outcome claims certified")
            continue

        # dictator endpoints + cross-binding; a converged FLAG is never
        # trusted — the certificate is recomputed from its endpoints
        z_d_ub = dd.get("z_d_ub")
        z_d_lb = dd.get("z_d_lb")
        adaptive = dd.get("adaptive") or {}
        if dd.get("status") != "OPTIMAL":
            problems.append(f"{tag}: dictator status != OPTIMAL")
            continue
        if not adaptive.get("adaptive_converged"):
            problems.append(f"{tag}: dictator not converged (INVALID/HALT)")
            continue
        if not _finite(z_d_ub):
            problems.append(f"{tag}: nonfinite dictator z_d_ub")
            continue
        if not _finite(ident.get("z_d_ub")) or abs(
                ident["z_d_ub"] - z_d_ub) > 1e-12:
            problems.append(
                f"{tag}: CG identity z_d_ub != dictator z_d_ub (z_D mismatch)")
            continue
        if not _finite(z_d_lb):
            problems.append(
                f"{tag}: dictator z_d_lb missing/nonfinite (required)")
            continue
        adaptive_lb = adaptive.get("adaptive_lb")
        if not _finite(adaptive_lb) or abs(adaptive_lb - z_d_lb) > NUM_TOL:
            problems.append(f"{tag}: dictator z_d_lb != recorded adaptive_lb")
            continue
        adaptive_ub = adaptive.get("adaptive_ub")
        if not _finite(adaptive_ub) or abs(adaptive_ub - z_d_ub) > NUM_TOL:
            problems.append(f"{tag}: dictator z_d_ub != recorded adaptive_ub")
            continue
        dictator_gap = z_d_ub - z_d_lb
        tol_d = dd.get("tol_d")
        if tol_d != bp.TOL_D or ident.get("tol_d") != bp.TOL_D:
            problems.append(f"{tag}: tol_d differs from frozen {bp.TOL_D}")
            continue
        if dictator_gap > bp.TOL_D + NUM_TOL:
            problems.append(
                f"{tag}: recomputed dictator gap {dictator_gap:.6g} > tol_d "
                f"{bp.TOL_D} (adaptive_converged flag is not evidence)")
            continue
        adaptive_gap = adaptive.get("adaptive_gap_abs")
        if not _finite(adaptive_gap) or abs(
                adaptive_gap - dictator_gap) > NUM_TOL:
            problems.append(
                f"{tag}: recorded adaptive_gap_abs {adaptive_gap!r} "
                f"inconsistent with endpoints ({dictator_gap!r})")
            continue
        record = dd.get("record")
        if not isinstance(record, dict) or record.get("replay_ok") is not True:
            problems.append(
                f"{tag}: dictator record replay invalid or missing")
            continue
        if record.get("replay_violations"):
            problems.append(
                f"{tag}: dictator record carries replay violations")
            continue
        d_solver = (dd.get("identity") or {}).get("solver") or {}
        if d_solver.get("backend") != manifest_solver.get("backend") \
                or d_solver.get("max_mip_gap") != manifest_solver.get(
                    "mip_gap"):
            problems.append(
                f"{tag}: dictator solver identity != run manifest solver")
            continue
        if lb_ch > ub_ch + NUM_TOL:
            problems.append(f"{tag}: lb_CH {lb_ch} > ub_CH {ub_ch}")
            continue

        # certification call count is cross-checked against the committed
        # oracle events AND the frozen budget, never trusted from a summary
        # field alone
        oracle_calls = ck.get("oracle_calls")
        events = ck.get("oracle_events") or []
        if (not isinstance(oracle_calls, int)
                or isinstance(oracle_calls, bool)
                or oracle_calls != len(events)):
            problems.append(
                f"{tag}: oracle_calls {oracle_calls!r} != committed events "
                f"({len(events)})")
            continue
        if ident.get("budget") != bp.BUDGET:
            problems.append(
                f"{tag}: identity budget {ident.get('budget')!r} != frozen "
                f"{bp.BUDGET}")
            continue
        if oracle_calls > bp.BUDGET:
            problems.append(
                f"{tag}: oracle_calls {oracle_calls} exceeds the frozen "
                f"budget {bp.BUDGET}")
            continue
        # the solver identity reported per cell is the RUN MANIFEST's bound
        # solver block; the checkpoint identity must agree with it
        solver_ident = ident.get("solver") or {}
        if solver_ident.get("backend") != manifest_solver.get("backend") \
                or solver_ident.get("max_mip_gap") != manifest_solver.get(
                    "mip_gap"):
            problems.append(
                f"{tag}: CG solver identity != run manifest solver")
            continue
        interval = cell_interval(ub_ch, lb_ch, z_d_ub, z_d_lb, cell["n_trips"])
        if interval["U_hi"] < -1e-6:
            problems.append(
                f"{tag}: U_hi {interval['U_hi']:.6g} < 0 beyond tolerance "
                "(violates z_D >= z_CH)")
            continue
        if interval["U_hi"] < interval["U_lo_raw"] - NUM_TOL:
            problems.append(f"{tag}: U_hi < U_lo_raw (interval inversion)")
            continue
        if interval["U_lo"] > interval["U_hi"]:
            problems.append(
                f"{tag}: impossible tightened interval "
                f"[{interval['U_lo']:.6g}, {interval['U_hi']:.6g}] "
                "(lo > hi after theorem tightening)")
            continue
        if interval["width"] > WIDTH_BOUND + NUM_TOL:
            problems.append(
                f"{tag}: width(U) {interval['width']:.6g} > tol_d+epsilon "
                f"{WIDTH_BOUND}")
            continue
        cells[key] = {
            "cell": cell, "interval": interval,
            "instance_hash": ident.get("instance_hash"),
            "market_hash": ident.get("market_hash"),
            "oracle_calls": oracle_calls,
            "solver_backend": manifest_solver.get("backend"),
            "solver_mip_gap": manifest_solver.get("mip_gap"),
            "dictator_gap": dictator_gap,
            "ch_gap": ub_ch - lb_ch,
        }
    if len(cells) != bp.N_CELLS:
        problems.append(
            f"expected {bp.N_CELLS} valid certified cells, got {len(cells)}")
    return {"cells": cells, "problems": problems}


# --------------------------------------------------------------------------
# matched contrasts + decision taxonomy (spec 5-6)
# --------------------------------------------------------------------------
def matched_contrast(u_f: dict, u_0: dict) -> dict:
    """Delta_f = U_f - U_0 = [U_f_lo_raw - U_0_hi, U_f_hi - U_0_lo_raw]."""
    lo = u_f["U_lo_raw"] - u_0["U_hi"]
    hi = u_f["U_hi"] - u_0["U_lo_raw"]
    return {"lo": lo, "hi": hi, "midpoint": 0.5 * (lo + hi),
            "width": (u_f["width"] + u_0["width"])}


def analyze_population(pop: dict) -> dict:
    if pop["problems"]:
        return {"decision": {"state": "INVALID/HALT",
                             "problems": pop["problems"]},
                "contrasts": [], "settings": {}, "cells": {}}
    cells = pop["cells"]
    market_keys = sorted({(s, n, b) for (_setting, s, n, b) in cells})
    contrasts = []
    per_setting: dict[str, dict] = {}
    for f in FACTOR_ORDER:
        s_f = DIRECTION_SIGN[f]
        signed_mids = []
        count = 0
        for (seed, n, b) in market_keys:
            u_f = cells[(f, seed, n, b)]["interval"]
            u_0 = cells[(BASELINE_SETTING, seed, n, b)]["interval"]
            d = matched_contrast(u_f, u_0)
            zero_excluding = (d["lo"] > 0) if s_f > 0 else (d["hi"] < 0)
            if zero_excluding:
                count += 1
            signed_mids.append(s_f * d["midpoint"])
            contrasts.append({
                "setting": f, "seed": seed, "n_trips": n, "b": b,
                "direction_sign": s_f,
                "delta_lo": d["lo"], "delta_hi": d["hi"],
                "delta_midpoint": d["midpoint"], "delta_width": d["width"],
                "direction_consistent_zero_excluding": zero_excluding,
            })
        med = statistics.median(signed_mids)
        per_setting[f] = {"count": count, "signed_median_midpoint": med,
                          "n_cells": len(market_keys),
                          "direction_sign": s_f,
                          "factor_order_index": FACTOR_ORDER.index(f)}

    # deterministic selection of f* (spec 6): max count; tie larger med;
    # final tie the fixed factor order.
    ranked = sorted(
        FACTOR_ORDER,
        key=lambda f: (per_setting[f]["count"],
                       per_setting[f]["signed_median_midpoint"],
                       -FACTOR_ORDER.index(f)),
        reverse=True)
    for rank, f in enumerate(ranked, start=1):
        per_setting[f]["rank"] = rank
        per_setting[f]["selected"] = rank == 1
    f_star = ranked[0]
    med_star = per_setting[f_star]["signed_median_midpoint"]
    count_star = per_setting[f_star]["count"]

    if abs(med_star) <= TAU_DELTA:
        state = "UNDER-RESOLVED"
    elif med_star > TAU_DELTA and count_star >= COUNT_GATE:
        state = "GO"
    else:
        state = "NO-GO"
    return {
        "decision": {
            "state": state, "selected_contrast": f_star,
            "count": count_star, "n_cells": len(market_keys),
            "count_gate": COUNT_GATE,
            "signed_median_midpoint": med_star,
            "tau_delta": TAU_DELTA,
        },
        "contrasts": contrasts,
        "settings": per_setting,
        "cells": cells,
    }


# --------------------------------------------------------------------------
# artifact emission (spec 7)
# --------------------------------------------------------------------------
DECISION_SCHEMA = "b3-factor-pilot-decision-v1"


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).decode().strip()
    except subprocess.CalledProcessError:
        return None


def _write_summary(path: Path, manifest: dict, result: dict) -> None:
    dec = result["decision"]
    lines = [
        "# B3 internal-uplift factor pilot — preregistered analysis",
        "",
        "Scientific boundary (required, from the spec): all instances are "
        "synthetic; only battery capacity and per-vehicle charging power vary "
        "across the five OFAT settings; no shared charger/depot constraint; no "
        "V2G and no terminal/opportunity charging (SOC upon pull-in must reach "
        "soc_end_kwh); the affine duck price environment is not a solar model; "
        "n_trips is workload, not fleet size; no distribution network. This is "
        "a minimal two-factor slice, not the full B3 atlas, and establishes "
        "certified synthetic signal and heterogeneity only.",
        "",
        f"- schema: {manifest['schema']}",
        f"- frozen screen: {manifest['frozen_screen']['dir']}",
        f"- screen record sha256: {manifest['frozen_screen']['record_sha256']}",
        f"- spec sha256: {manifest['spec']['sha256']}",
        f"- git commit: {manifest['git_commit']}",
        f"- epsilon={bp.EPSILON}, tol_d={bp.TOL_D}, budget={bp.BUDGET}, "
        f"tau_Delta={TAU_DELTA} SEK, width(U)<={WIDTH_BOUND}",
        "",
        f"## Decision: {dec['state']}",
    ]
    if dec["state"] in ("GO", "NO-GO", "UNDER-RESOLVED"):
        lines += [
            f"- selected contrast f*: {dec['selected_contrast']}",
            f"- direction-consistent zero-excluding count: {dec['count']}/"
            f"{dec['n_cells']} (gate >= {dec['count_gate']})",
            f"- direction-signed median midpoint: "
            f"{dec['signed_median_midpoint']:.6g} SEK "
            f"(tau_Delta = {dec['tau_delta']})",
            "",
            "Confirmation (frozen, separate fresh-seed stage; NOT run here): "
            "seeds {32,33,34,35,36,37}, S0 vs S_{f*}, 24 matched contrasts, "
            "replicate iff >= 18/24 direction-consistent zero-excluding AND "
            "signed median midpoint > tau_Delta. Engineering gates, not "
            "significance levels.",
        ]
    elif dec["state"] == "INVALID/HALT":
        lines.append("Engineering/validity failure — repair and re-run; not "
                     "scientific evidence. Problems:")
        lines += [f"- {p}" for p in dec.get("problems", [])]
    elif dec["state"] == "DESIGN-NOT-FROZEN":
        lines.append(f"The Section-4 screen is not frozen / binding failed: "
                     f"{dec.get('reason')}")
    path.write_text("\n".join(lines) + "\n")


def _format_csv_value(value):
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return repr(value)
    if value is None:
        return ""
    return str(value)


def _write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    import csv
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_format_csv_value(row.get(c))
                             for c in columns])


CELL_INTERVAL_COLUMNS = [
    "setting", "seed", "n_trips", "b", "instance_hash", "market_hash",
    "z_d_lb", "z_d_ub", "lb_ch", "ub_ch",
    "u_lo_raw", "u_lo_tightened", "u_hi", "width",
    "u_lo_raw_per_trip", "u_hi_per_trip",
    "cost_fraction_lo", "cost_fraction_hi",
    "dictator_gap", "ch_gap", "lo_endpoint_source",
    "oracle_calls", "solver_backend", "solver_mip_gap",
]
MATCHED_CONTRAST_COLUMNS = [
    "setting", "seed", "n_trips", "b", "direction_sign",
    "delta_lo", "delta_hi", "delta_midpoint", "delta_width",
    "direction_consistent_zero_excluding",
]
SETTING_SUMMARY_COLUMNS = [
    "setting", "direction_sign", "zero_excluding_count", "n_cells",
    "signed_median_midpoint", "factor_order_index", "rank", "selected",
]


def _cell_interval_rows(cells: dict) -> list[dict]:
    rows = []
    for setting in bp.SETTING_ORDER:
        for seed in bp.SEEDS:
            for n in bp.N_TRIPS:
                for b in bp.B_SCALES:
                    record = cells[(setting, seed, n, b)]
                    interval = record["interval"]
                    rows.append({
                        "setting": setting, "seed": seed, "n_trips": n,
                        "b": b,
                        "instance_hash": record["instance_hash"],
                        "market_hash": record["market_hash"],
                        "z_d_lb": interval["z_d_lb"],
                        "z_d_ub": interval["z_d_ub"],
                        "lb_ch": interval["lb_ch"],
                        "ub_ch": interval["ub_ch"],
                        "u_lo_raw": interval["U_lo_raw"],
                        "u_lo_tightened": interval["U_lo"],
                        "u_hi": interval["U_hi"],
                        "width": interval["width"],
                        "u_lo_raw_per_trip": interval["U_lo_raw_per_trip"],
                        "u_hi_per_trip": interval["U_hi_per_trip"],
                        "cost_fraction_lo": (
                            interval["cost_fraction"][0]
                            if interval["cost_fraction"] else None),
                        "cost_fraction_hi": (
                            interval["cost_fraction"][1]
                            if interval["cost_fraction"] else None),
                        "dictator_gap": record["dictator_gap"],
                        "ch_gap": record["ch_gap"],
                        "lo_endpoint_source": interval["lo_endpoint"],
                        "oracle_calls": record["oracle_calls"],
                        "solver_backend": record["solver_backend"],
                        "solver_mip_gap": record["solver_mip_gap"],
                    })
    return rows


def _setting_summary_rows(settings: dict) -> list[dict]:
    return [{
        "setting": f,
        "direction_sign": settings[f]["direction_sign"],
        "zero_excluding_count": settings[f]["count"],
        "n_cells": settings[f]["n_cells"],
        "signed_median_midpoint": settings[f]["signed_median_midpoint"],
        "factor_order_index": settings[f]["factor_order_index"],
        "rank": settings[f]["rank"],
        "selected": settings[f]["selected"],
    } for f in FACTOR_ORDER]


def analyze(runs_dir, out_base, stamp, analysis_code_commit, *,
            screen_dir=None, verify_code_commit=True) -> str:
    refuse_a6_paths(runs_dir, out_base)
    assert_output_separation(runs_dir, out_base)
    if verify_code_commit:
        verify_analysis_code_commit(analysis_code_commit)

    audit_sha = None
    try:
        screen = bp.load_frozen_screen(screen_dir)
    except bp.B3PilotError as exc:
        result = {"decision": {"state": "DESIGN-NOT-FROZEN",
                               "reason": str(exc)},
                  "contrasts": [], "settings": {}, "cells": {}}
        screen = {"dir": "<unresolved>", "record_sha256": None,
                  "spec_sha256": None}
    else:
        # the exact audit MUST pass before any scoring; malformed run
        # inputs are a STRUCTURED INVALID/HALT, never an uncaught crash
        from experiments import audit_b3_factor_pilot as ad
        try:
            audit_result = ad.audit(runs_dir, screen_dir)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            audit_result = {"ok": False, "run_manifest_sha256": None,
                            "problems": [f"malformed run input: {exc}"]}
        audit_sha = audit_result.get("run_manifest_sha256")
        if not audit_result["ok"]:
            result = {"decision": {"state": "INVALID/HALT",
                                   "problems": audit_result["problems"]},
                      "contrasts": [], "settings": {}, "cells": {}}
        else:
            run = bp.load_run_manifest(runs_dir)
            market_by_cell = bp.market_hash_by_cell(run["manifest"])
            pop = load_population(runs_dir, screen, market_by_cell,
                                  run["manifest"])
            result = analyze_population(pop)

    out_base = Path(out_base)
    out_base.mkdir(parents=True, exist_ok=True)
    out_dir = out_base / stamp
    if out_dir.exists():
        raise B3AnalysisError(f"refusing existing output directory: {out_dir}")

    # repository-relative provenance paths only (portable regeneration
    # across absolute checkout/output roots)
    screen_dir_recorded = screen["dir"]
    try:
        screen_dir_recorded = str(
            Path(screen_dir_recorded).resolve().relative_to(REPO_ROOT))
    except (ValueError, OSError):
        pass
    # a --screen-dir override can never bypass the frozen screen SHA: the
    # binding is recorded and any drift marks the artifact non-scoreable
    # (the selector and packager refuse non-verified screens)
    frozen_screen_verified = (
        screen.get("record_sha256") == bp.FROZEN_SCREEN_RECORD_SHA256)
    manifest = {
        "schema": SCHEMA,
        "stamp": stamp,
        "analysis_code_commit": analysis_code_commit,
        "analysis_code_verified": verify_code_commit,
        "frozen_screen_verified": frozen_screen_verified,
        "git_commit": _git_commit(),
        "spec": {"path": SPEC_RELPATH,
                 "sha256": sha256_file(REPO_ROOT / SPEC_RELPATH)},
        "frozen_screen": {"dir": screen_dir_recorded,
                          "record_sha256": screen.get("record_sha256")},
        "run_manifest_sha256": audit_sha,
        "audit_required": True,
        "tolerances": {"epsilon": bp.EPSILON, "tol_d": bp.TOL_D,
                       "budget": bp.BUDGET, "tau_delta": TAU_DELTA},
        "counts": bp.counts(),
        "decision": result["decision"],
    }
    decision_document = {
        "schema": DECISION_SCHEMA,
        "stamp": stamp,
        "state": result["decision"]["state"],
        "selected_factor": result["decision"].get("selected_contrast"),
        "direction_sign": (
            DIRECTION_SIGN.get(result["decision"].get("selected_contrast"))
            if result["decision"].get("selected_contrast") else None),
        "thresholds": {
            "count_gate": COUNT_GATE,
            "tau_delta": TAU_DELTA,
            "width_bound": WIDTH_BOUND,
        },
        "counts": {
            "zero_excluding_count": result["decision"].get("count"),
            "n_matched_cells": result["decision"].get("n_cells"),
            "expected_cells": bp.N_CELLS,
            "expected_contrasts": bp.N_MATCHED_CONTRASTS,
        },
        "signed_median_midpoint": result["decision"].get(
            "signed_median_midpoint"),
        "inputs": {
            "run_manifest_sha256": audit_sha,
            "screen_record_sha256": screen.get("record_sha256"),
            "spec_sha256": manifest["spec"]["sha256"],
        },
        "frozen_screen_verified": frozen_screen_verified,
        "analysis_code_commit": analysis_code_commit,
        "problems": result["decision"].get("problems"),
        "reason": result["decision"].get("reason"),
    }

    valid_population = bool(result["cells"])
    staging = out_dir.with_name(f".{stamp}.staging")
    if staging.exists():
        raise B3AnalysisError(f"refusing existing staging dir: {staging}")
    staging.mkdir(parents=True)
    try:
        table_rows: dict[str, int] = {}
        if valid_population:
            cell_rows = _cell_interval_rows(result["cells"])
            if len(cell_rows) != bp.N_CELLS:
                raise B3AnalysisError(
                    f"cell_intervals must carry exactly {bp.N_CELLS} rows")
            if len(result["contrasts"]) != bp.N_MATCHED_CONTRASTS:
                raise B3AnalysisError(
                    "matched_contrasts must carry exactly "
                    f"{bp.N_MATCHED_CONTRASTS} rows")
            _write_csv(staging / "cell_intervals.csv", cell_rows,
                       CELL_INTERVAL_COLUMNS)
            _write_csv(staging / "matched_contrasts.csv",
                       result["contrasts"], MATCHED_CONTRAST_COLUMNS)
            summary_rows = _setting_summary_rows(result["settings"])
            if len(summary_rows) != len(FACTOR_ORDER):
                raise B3AnalysisError(
                    "setting_summary must carry exactly four factor rows")
            _write_csv(staging / "setting_summary.csv", summary_rows,
                       SETTING_SUMMARY_COLUMNS)
            table_rows = {
                "cell_intervals.csv": len(cell_rows),
                "matched_contrasts.csv": len(result["contrasts"]),
                "setting_summary.csv": len(summary_rows),
            }
        (staging / "DECISION.json").write_text(
            json.dumps(decision_document, indent=2, sort_keys=True) + "\n")
        _write_summary(staging / "SUMMARY.md", manifest, result)
        # the manifest is written LAST, cross-bound to every emitted
        # table's hash and row count
        outputs = sorted(
            path.name for path in staging.iterdir())
        manifest["outputs"] = {
            name: sha256_file(staging / name) for name in outputs}
        manifest["table_rows"] = table_rows
        (staging / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        os.rename(staging, out_dir)
    except BaseException:
        for entry in staging.glob("*"):
            entry.unlink()
        staging.rmdir()
        raise
    return str(out_dir)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs/b3_factor_pilot")
    ap.add_argument("--out", default=str(REPO_ROOT / "result" / "b3_factor_pilot"))
    ap.add_argument("--stamp", required=True)
    ap.add_argument("--analysis-code-commit", required=True)
    ap.add_argument("--screen-dir", default=None)
    args = ap.parse_args()
    out_dir = analyze(args.runs, args.out, args.stamp,
                      args.analysis_code_commit, screen_dir=args.screen_dir)
    print(out_dir)


if __name__ == "__main__":
    main()
