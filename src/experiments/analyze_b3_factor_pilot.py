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

Certificate scope: this analyzer replays the committed RMP/oracle and
dictator evidence; it does not re-solve the underlying LPs or MIPs.  The
replay proves internal consistency with recorded solver fields, so decision
integrity additionally rests on the provenance of the raw run tree and its
independent, outcome-blind pre-analysis digest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.b3_factor_pilot as bp
import experiments.b3_pilot_anchor as anchor
import experiments.b3_pilot_evidence as evidence

SCHEMA = "b3-factor-pilot-analysis-v1"
REPO_ROOT = bp.REPO_ROOT
SPEC_RELPATH = "doc/B3_FACTOR_PILOT_SPEC_DRAFT.md"
PROVENANCE_FILES = (
    "src/experiments/analyze_b3_factor_pilot.py",
    "src/experiments/audit_b3_factor_pilot.py",
    "src/experiments/b3_factor_pilot.py",
    "src/experiments/b3_pilot_anchor.py",
    "src/experiments/b3_factor_screen.py",
    "src/experiments/b3_pilot_evidence.py",
    "src/experiments/package_a6_holdout.py",
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
BOUNDARY_ADJACENT_TOL = 1e-9


class B3AnalysisError(RuntimeError):
    pass


# Provenance must not be resolvable through an attacker-controlled PATH: a
# `git` shim earlier on PATH would otherwise answer every question we ask.
_TRUSTED_PATH = "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"


def _trusted_git() -> str:
    exe = shutil.which("git", path=_TRUSTED_PATH)
    if exe is None:                                  # pragma: no cover
        raise B3AnalysisError(
            "no git executable found on the trusted path "
            f"({_TRUSTED_PATH}); provenance cannot be verified")
    return exe


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


def _load(path: Path, label: str | None = None,
          expected_sha256: str | None = None):
    """Label errors with a RUN-ROOT-RELATIVE name.

    The analyzer scores a frozen copy under a temporary directory, so an
    absolute label would leak that path into published refusal records and
    make artifact regeneration non-deterministic.
    """
    return evidence.read_json_object_once(
        path, label or path.name, expected_sha256=expected_sha256)


def load_population(runs_dir: str | os.PathLike, screen: dict,
                    market_by_cell: dict, run_manifest: dict,
                    frozen_digests: dict | None = None) -> dict:
    """Replay all 60 cells through the same primitive used by the audit.

    When ``frozen_digests`` is supplied (the analyzer always supplies it) every
    checkpoint is digest-checked against the frozen inventory in the same read
    that parses it, so evidence cannot be substituted for the duration of the
    replay and restored afterwards.
    """
    runs = Path(runs_dir)
    problems: list[str] = []
    cells: dict[tuple, dict] = {}
    manifest_solver = run_manifest.get("solver") or {}
    run_manifest_sha = bp.run_manifest_sha256(run_manifest)
    run_commit = run_manifest.get("run_commit")
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
            cg_rel = f"{tag}/a2.cg.ckpt.json"
            d_rel = f"{tag}/dictator.ckpt.json"
            if frozen_digests is not None and (
                    cg_rel not in frozen_digests
                    or d_rel not in frozen_digests):
                problems.append(
                    f"{tag}: checkpoint absent from the frozen inventory")
                continue
            digests = frozen_digests or {}
            ck = _load(cg_path, cg_rel, digests.get(cg_rel))
            dd = _load(d_path, d_rel, digests.get(d_rel))
        except evidence.EvidenceError as exc:
            problems.append(f"{tag}: {exc}")
            continue
        expected_hash = screen["instance_hashes"][
            (cell["setting"], cell["seed"], cell["n_trips"])]
        expected_market = market_by_cell.get(key)
        if expected_market is None:
            problems.append(f"{tag}: market hash missing from run manifest")
            continue
        replayed, replay_problems = evidence.replay_cell_evidence(
            ck,
            dd,
            cell=cell,
            expected_instance_hash=expected_hash,
            expected_market_hash=expected_market,
            screen_record_sha256=screen["record_sha256"],
            run_manifest_sha256=run_manifest_sha,
            run_commit=run_commit,
            manifest_solver=manifest_solver,
        )
        if replay_problems:
            problems.extend(replay_problems)
            continue
        assert replayed is not None
        interval = cell_interval(
            replayed["ub_ch"], replayed["lb_ch"],
            replayed["z_d_ub"], replayed["z_d_lb"], cell["n_trips"])
        cells[key] = {
            "cell": cell, "interval": interval,
            "instance_hash": expected_hash,
            "market_hash": expected_market,
            "oracle_calls": replayed["oracle_calls"],
            "solver_backend": replayed["solver_backend"],
            "solver_mip_gap": replayed["solver_mip_gap"],
            "dictator_gap": replayed["dictator_gap"],
            "ch_gap": replayed["ch_gap"],
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
    boundary_margin = abs(med_star) - TAU_DELTA
    return {
        "decision": {
            "state": state, "selected_contrast": f_star,
            "count": count_star, "n_cells": len(market_keys),
            "count_gate": COUNT_GATE,
            "signed_median_midpoint": med_star,
            "signed_median_midpoint_repr": repr(med_star),
            "tau_delta": TAU_DELTA,
            "boundary_margin": boundary_margin,
            "boundary_adjacent": abs(boundary_margin)
            < BOUNDARY_ADJACENT_TOL,
            "boundary_adjacent_tolerance": BOUNDARY_ADJACENT_TOL,
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
            f"{dec['signed_median_midpoint']!r} SEK "
            f"(tau_Delta = {dec['tau_delta']})",
            f"- boundary margin |median|-tau_Delta: "
            f"{dec['boundary_margin']!r}; adjacent="
            f"{dec['boundary_adjacent']} at "
            f"{dec['boundary_adjacent_tolerance']!r}",
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


def verify_run_commit(claimed, *, verifier=None) -> None:
    """The recorded ``run_commit`` must be a REAL commit object and an ancestor
    of HEAD, not merely forty hexadecimal characters.

    A shape-only check lets a manifest claim any plausible-looking SHA, so the
    code that produced a population could never be located.  ``verifier``
    exists so synthetic tests can inject a checker instead of fabricating
    repository history; production always resolves through git.
    """
    # The shape check is unconditional: an injected verifier may relax the
    # git resolution for synthetic fixtures, but it may never accept a value
    # that is not even a well-formed SHA.
    if (not isinstance(claimed, str) or len(claimed) != 40
            or not all(c in "0123456789abcdef" for c in claimed)):
        raise evidence.EvidenceError(
            "run_commit must be the full 40-character lowercase hexadecimal "
            f"SHA of a real commit; got {claimed!r}")
    if verifier is not None:
        verifier(claimed)
        return
    # A bare ``git`` inherits GIT_DIR/GIT_WORK_TREE, so an exported GIT_DIR can
    # make a commit from a FOREIGN repository resolve here.  Unlike
    # verify_analysis_code_commit there is no byte-compare backstop on this
    # value, so pin the repository explicitly and scrub the git environment.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    base = [_trusted_git(), "--git-dir", str(Path(REPO_ROOT) / ".git"),
            "--work-tree", str(REPO_ROOT)]
    try:
        resolved = subprocess.check_output(
            base + ["rev-parse", "--verify", f"{claimed}^{{commit}}"],
            cwd=REPO_ROOT, env=env,
            stderr=subprocess.DEVNULL).decode().strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        raise evidence.EvidenceError(
            f"run_commit {claimed} does not resolve to a commit object"
        ) from exc
    if resolved != claimed:
        raise evidence.EvidenceError(
            f"run_commit {claimed} resolves to {resolved}")
    if subprocess.run(
            base + ["merge-base", "--is-ancestor", claimed, "HEAD"],
            cwd=REPO_ROOT, env=env).returncode != 0:
        raise evidence.EvidenceError(
            f"run_commit {claimed} is not an ancestor of HEAD")


def _required_anchor(live_identity, *, verify_code_commit,
                     expected_raw_anchor) -> dict:
    """Resolve which anchor the raw tree must match.

    Production (``verify_code_commit=True``) always requires the frozen,
    outcome-blind pre-analysis anchor.  The relaxed form exists only so
    synthetic fixtures can be scored, and is never reachable from the CLI.
    """
    required = expected_raw_anchor
    if required is None:
        required = (anchor.FROZEN_RAW_ANCHOR if verify_code_commit
                    else live_identity)
    if (not isinstance(required, dict)
            or set(required) != set(anchor.FROZEN_RAW_ANCHOR)):
        raise evidence.EvidenceError(
            "expected pre-analysis raw anchor is malformed")
    return required


def _score_frozen_population(runs_dir, screen, screen_dir, *,
                             verify_code_commit, expected_raw_anchor,
                             run_commit_verifier):
    """Freeze the raw tree ONCE, then audit and score only that frozen copy.

    The analyzer must never audit or score bytes it does not also bind.  The
    order is therefore: snapshot the live tree, verify it against the required
    pre-analysis anchor, copy it to an immutable regular-file-only tree, verify
    the copy has the same canonical identity, and read ONLY the copy from then
    on.  A transient mutate/score/restore sequence against the live tree
    therefore cannot cause bytes other than the bound ones to be scored, and
    the live source is re-verified unchanged before the caller publishes.

    Returns ``(result, audit_sha, raw_binding, run_manifest)``.
    """
    from experiments.package_a6_holdout import (
        PackagingError as _PkgError,
        canonical_tree_sha256 as _tree_sha,
        freeze_source as _freeze,
        snapshot_source as _snapshot,
    )
    from experiments import audit_b3_factor_pilot as ad

    def _halt(problems, audit_sha=None, run_manifest=None):
        """A refusal keeps whatever provenance was already established, so an
        INVALID/HALT record still names the audited manifest and solver."""
        return ({"decision": {"state": "INVALID/HALT", "problems": problems},
                 "contrasts": [], "settings": {}, "cells": {}},
                audit_sha, None, run_manifest)

    with tempfile.TemporaryDirectory(prefix="b3-frozen-") as tmp:
        frozen_dir = Path(tmp) / "frozen"
        try:
            live = _snapshot(runs_dir)
            live_identity = anchor.snapshot_identity(live, _tree_sha(live))
            required = _required_anchor(
                live_identity, verify_code_commit=verify_code_commit,
                expected_raw_anchor=expected_raw_anchor)
            pre = anchor.anchor_disagreements(live_identity, required)
            if pre:
                raise evidence.EvidenceError(
                    "pre-analysis raw anchor mismatch: " + ", ".join(pre))
            # TMPDIR is attacker/operator controlled; the A6 boundary applies
            # to the frozen copy's location too, not just the inputs.
            refuse_a6_paths(frozen_dir.parent)
            frozen = _freeze(runs_dir, frozen_dir)
            frozen_identity = anchor.snapshot_identity(
                frozen, _tree_sha(frozen))
            drift = anchor.anchor_disagreements(frozen_identity, required)
            if drift:
                raise evidence.EvidenceError(
                    "frozen copy differs from the anchored population: "
                    + ", ".join(drift))
            # Narrow the window in which the copy could be swapped: strip
            # write permission from the tree we are about to score.  This is
            # defence in depth, NOT the guarantee -- the guarantee is the
            # post-scoring re-hash below.
            for path in sorted(frozen_dir.rglob("*"), reverse=True):
                try:
                    path.chmod(0o500 if path.is_dir() else 0o400)
                except OSError:
                    pass
        except (_PkgError, OSError, evidence.EvidenceError,
                B3AnalysisError, bp.B3PilotError) as exc:
            return _halt([f"raw tree cannot be frozen: {exc}"])

        frozen_files = {row["path"]: row["sha256"] for row in frozen["files"]}
        raw_tree_sha = frozen_identity["tree_sha256"]

        # Everything below reads the FROZEN copy only.  The audit is inside
        # the structured boundary: malformed evidence must become
        # INVALID/HALT, never an uncaught AttributeError or RecursionError
        # escaping to the caller.
        try:
            audit_result = ad.audit(frozen_dir, screen_dir)
        except (_PkgError, OSError, evidence.EvidenceError, B3AnalysisError,
                bp.B3PilotError, ValueError, KeyError, TypeError,
                AttributeError, IndexError, RecursionError) as exc:
            return _halt([f"audit could not complete: {type(exc).__name__}: "
                          f"{exc}"])
        audit_sha = audit_result.get("run_manifest_sha256")
        if not audit_result["ok"]:
            return ({"decision": {"state": "INVALID/HALT",
                                  "problems": audit_result["problems"]},
                     "contrasts": [], "settings": {}, "cells": {}},
                    audit_sha, None, None)

        run_manifest_local = None
        try:
            run_manifest = evidence.read_json_object_once(
                frozen_dir / bp.RUN_MANIFEST_FILENAME, "run MANIFEST.json",
                expected_sha256=frozen_files.get(bp.RUN_MANIFEST_FILENAME))
            run_manifest_local = run_manifest
            if verify_code_commit or run_commit_verifier is not None:
                verify_run_commit(run_manifest.get("run_commit"),
                                  verifier=run_commit_verifier)
            market_by_cell = bp.market_hash_by_cell(run_manifest)
            pop = load_population(
                frozen_dir, screen, market_by_cell, run_manifest,
                frozen_digests=frozen_files)
            result = analyze_population(pop)

            # The frozen copy was hashed BEFORE the audit and the replay.
            # Re-hash it now and require it to be unchanged, then bind to the
            # re-hashed identity: otherwise raw_binding could attest to bytes
            # other than the ones actually scored.
            rescan = _snapshot(frozen_dir)
            rescan_identity = anchor.snapshot_identity(
                rescan, _tree_sha(rescan))
            swapped = anchor.anchor_disagreements(rescan_identity, required)
            if swapped or rescan_identity != frozen_identity:
                raise evidence.EvidenceError(
                    "frozen copy changed during scoring: "
                    + ", ".join(swapped or ["identity drift"]))
            frozen_files = {row["path"]: row["sha256"]
                            for row in rescan["files"]}
            raw_binding = {
                "raw_tree_sha256": rescan_identity["tree_sha256"],
                "file_count": rescan["file_count"],
                "directory_count": rescan["directory_count"],
                "total_bytes": rescan["total_bytes"],
                "manifest_sha256": frozen_files.get(bp.RUN_MANIFEST_FILENAME),
                "job_id": None,
                "job_sha256": None,
                "pre_analysis_anchor": dict(required),
            }
            if raw_binding["manifest_sha256"] != audit_sha:
                raise evidence.EvidenceError(
                    "frozen MANIFEST.json differs from audited bytes")
            if bp.JOB_FILENAME in frozen_files:
                job_bytes = evidence.read_regular_bytes_once(
                    frozen_dir / bp.JOB_FILENAME, bp.JOB_FILENAME,
                    expected_sha256=frozen_files.get(bp.JOB_FILENAME))
                job_sha = hashlib.sha256(job_bytes).hexdigest()
                if job_sha != frozen_files[bp.JOB_FILENAME]:
                    raise evidence.EvidenceError(
                        "JOB.json changed after the raw-tree freeze")
                job_doc = evidence.strict_json_loads(
                    job_bytes, bp.JOB_FILENAME)
                if not isinstance(job_doc, dict):
                    raise evidence.EvidenceError(
                        "JOB.json root is not an object")
                job_id = job_doc.get("job_id")
                if (job_doc.get("schema") != "b3-factor-pilot-job-v1"
                        or not isinstance(job_id, str)
                        or not job_id.isdigit() or job_id.startswith("0")
                        or len(job_id) > 18):
                    raise evidence.EvidenceError(
                        "JOB.json has a noncanonical Slurm job id")
                if (job_doc.get("run_manifest_sha256") != audit_sha
                        or job_doc.get("run_commit")
                        != run_manifest.get("run_commit")):
                    raise evidence.EvidenceError(
                        "JOB.json does not bind the exact run manifest")
                raw_binding["job_id"] = job_id
                raw_binding["job_sha256"] = job_sha

            # the live source must be untouched across the whole scoring pass
            after = _snapshot(runs_dir)
            post = anchor.anchor_disagreements(
                anchor.snapshot_identity(after, _tree_sha(after)), required)
            if post:
                raise evidence.EvidenceError(
                    "live raw tree changed during scoring: "
                    + ", ".join(post))
        except (_PkgError, OSError, evidence.EvidenceError,
                B3AnalysisError, bp.B3PilotError, ValueError, KeyError) as exc:
            return _halt([f"raw tree cannot be bound: {exc}"],
                         audit_sha=audit_sha, run_manifest=run_manifest_local)

        return result, audit_sha, raw_binding, run_manifest


def analyze(runs_dir, out_base, stamp, analysis_code_commit, *,
            screen_dir=None, verify_code_commit=True,
            expected_raw_anchor=None, run_commit_verifier=None) -> str:
    refuse_a6_paths(runs_dir, out_base)
    assert_output_separation(runs_dir, out_base)
    if verify_code_commit:
        verify_analysis_code_commit(analysis_code_commit)

    audit_sha = None
    run_manifest = None
    raw_binding = None
    try:
        screen = bp.load_frozen_screen(screen_dir)
    except bp.B3PilotError as exc:
        result = {"decision": {"state": "DESIGN-NOT-FROZEN",
                               "reason": str(exc)},
                  "contrasts": [], "settings": {}, "cells": {}}
        screen = {"dir": "<unresolved>", "record_sha256": None,
                  "spec_sha256": None}
    else:
        if screen.get("record_sha256") != bp.FROZEN_SCREEN_RECORD_SHA256:
            result = {
                "decision": {
                    "state": "DESIGN-NOT-FROZEN",
                    "reason": (
                        "screen record SHA differs from the frozen canonical "
                        "screen; scoring overrides are forbidden"),
                },
                "contrasts": [], "settings": {}, "cells": {},
            }
        else:
            # Freeze the raw tree BEFORE auditing or scoring, then read only
            # the frozen copy, so the analyzer can never score bytes it does
            # not also bind.  Malformed run inputs remain a STRUCTURED
            # INVALID/HALT, never an uncaught crash.
            result, audit_sha, raw_binding, run_manifest = (
                _score_frozen_population(
                    runs_dir, screen, screen_dir,
                    verify_code_commit=verify_code_commit,
                    expected_raw_anchor=expected_raw_anchor,
                    run_commit_verifier=run_commit_verifier))

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
    # The internal screen_dir hook exists only for synthetic tests.  Any SHA
    # drift above becomes DESIGN-NOT-FROZEN and is never scored; the production
    # CLI exposes no screen override.
    frozen_screen_verified = (
        screen.get("record_sha256") == bp.FROZEN_SCREEN_RECORD_SHA256)
    manifest = {
        "schema": SCHEMA,
        "stamp": stamp,
        "analysis_code_commit": analysis_code_commit,
        "analysis_code_verified": verify_code_commit,
        # False whenever the synthetic verifier seam was used, so a fixture
        # artifact can never be mistaken for a production-verified one.
        "run_commit_verified": bool(verify_code_commit
                                    and run_commit_verifier is None),
        "frozen_screen_verified": frozen_screen_verified,
        "git_commit": _git_commit(),
        "spec": {"path": SPEC_RELPATH,
                 "sha256": sha256_file(REPO_ROOT / SPEC_RELPATH)},
        "frozen_screen": {"dir": screen_dir_recorded,
                          "record_sha256": screen.get("record_sha256")},
        "run_manifest_sha256": audit_sha,
        "raw_binding": raw_binding,
        "audit_required": True,
        "solver": (run_manifest or {}).get("solver"),
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
        "signed_median_midpoint_repr": result["decision"].get(
            "signed_median_midpoint_repr"),
        "boundary_margin": result["decision"].get("boundary_margin"),
        "boundary_adjacent": result["decision"].get("boundary_adjacent"),
        "boundary_adjacent_tolerance": result["decision"].get(
            "boundary_adjacent_tolerance"),
        "inputs": {
            "run_manifest_sha256": audit_sha,
            "screen_record_sha256": screen.get("record_sha256"),
            "spec_sha256": manifest["spec"]["sha256"],
            "raw_binding": raw_binding,
            "solver": manifest["solver"],
        },
        "frozen_screen_verified": frozen_screen_verified,
        "analysis_code_commit": analysis_code_commit,
        "problems": result["decision"].get("problems"),
        "reason": result["decision"].get("reason"),
    }
    # Two independently shaped manifest copies are intentional: the exact
    # DECISION.json document and the analyzer's internal decision record.
    # The selector requires both to equal its primitive reconstruction.
    manifest["decision_document"] = decision_document

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
    args = ap.parse_args()
    out_dir = analyze(args.runs, args.out, args.stamp,
                      args.analysis_code_commit)
    print(out_dir)


if __name__ == "__main__":
    main()
