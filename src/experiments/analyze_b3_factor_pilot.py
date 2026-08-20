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


def load_population(runs_dir: str | os.PathLike, screen: dict) -> dict:
    """Read all 60 cells, validate frozen binding + certification + interval
    sanity, and return per-cell intervals.  Any failure is collected as an
    INVALID/HALT problem (no cell is ever silently dropped)."""
    runs = Path(runs_dir)
    problems: list[str] = []
    cells: dict[tuple, dict] = {}
    for cell in bp.build_cells():
        tag = cell["tag"]
        key = (cell["setting"], cell["seed"], cell["n_trips"], cell["b"])
        cdir = runs / tag
        cg_path = cdir / "a2.cg.ckpt.json"
        d_path = cdir / "dictator.ckpt.json"
        if not cg_path.is_file() or not d_path.is_file():
            problems.append(f"{tag}: missing checkpoint(s)")
            continue
        ck = _load(cg_path)
        dd = _load(d_path)
        ident = ck.get("identity") or {}
        expected_hash = screen["instance_hashes"][
            (cell["setting"], cell["seed"], cell["n_trips"])]
        if ident.get("method", "a2") != bp.METHOD:
            problems.append(f"{tag}: method {ident.get('method')!r} != a2")
        if ident.get("instance_hash") != expected_hash:
            problems.append(f"{tag}: instance-hash drift vs frozen screen")
        oc = ck.get("outcome") or {}
        if not (oc.get("type") == "certified" and oc.get("certified")):
            problems.append(
                f"{tag}: A2 not certified within budget (INVALID/HALT)")
            continue
        if not (dd.get("adaptive") or {}).get("adaptive_converged"):
            problems.append(f"{tag}: dictator not converged (INVALID/HALT)")
            continue
        ub_ch = oc.get("ub_ch"); lb_ch = oc.get("lb_best")
        z_d_ub = dd.get("z_d_ub"); z_d_lb = dd.get("z_d_lb")
        if not all(_finite(v) for v in (ub_ch, lb_ch, z_d_ub)):
            problems.append(f"{tag}: nonfinite bound(s)")
            continue
        if lb_ch > ub_ch + 1e-9:
            problems.append(f"{tag}: lb_CH {lb_ch} > ub_CH {ub_ch}")
            continue
        interval = cell_interval(ub_ch, lb_ch, z_d_ub, z_d_lb, cell["n_trips"])
        if interval["U_hi"] < interval["U_lo_raw"] - 1e-9:
            problems.append(f"{tag}: U_hi < U_lo_raw (interval inversion)")
            continue
        if interval["width"] > WIDTH_BOUND + 1e-9:
            problems.append(
                f"{tag}: width(U) {interval['width']:.6g} > tol_d+epsilon "
                f"{WIDTH_BOUND}")
            continue
        cells[key] = {"cell": cell, "interval": interval}
    if len(cells) + len(problems) != bp.N_CELLS and not problems:
        problems.append(
            f"population has {len(cells)} valid cells, expected {bp.N_CELLS}")
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
                "contrasts": [], "settings": {}}
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
                          "n_cells": len(market_keys)}

    # deterministic selection of f* (spec 6): max count; tie larger med;
    # final tie the fixed factor order.
    f_star = max(
        FACTOR_ORDER,
        key=lambda f: (per_setting[f]["count"],
                       per_setting[f]["signed_median_midpoint"],
                       -FACTOR_ORDER.index(f)))
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
    }


# --------------------------------------------------------------------------
# artifact emission (spec 7)
# --------------------------------------------------------------------------
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


def _write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    import csv
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c) for c in columns})


def analyze(runs_dir, out_base, stamp, analysis_code_commit, *,
            screen_dir=None, verify_code_commit=True) -> str:
    refuse_a6_paths(runs_dir, out_base)
    assert_output_separation(runs_dir, out_base)
    if verify_code_commit:
        verify_analysis_code_commit(analysis_code_commit)

    try:
        screen = bp.load_frozen_screen(screen_dir)
    except bp.B3PilotError as exc:
        result = {"decision": {"state": "DESIGN-NOT-FROZEN",
                               "reason": str(exc)},
                  "contrasts": [], "settings": {}}
        screen = {"dir": "<unresolved>", "record_sha256": None,
                  "spec_sha256": None}
    else:
        pop = load_population(runs_dir, screen)
        result = analyze_population(pop)

    out_base = Path(out_base)
    out_base.mkdir(parents=True, exist_ok=True)
    out_dir = out_base / stamp
    if out_dir.exists():
        raise B3AnalysisError(f"refusing existing output directory: {out_dir}")

    manifest = {
        "schema": SCHEMA,
        "stamp": stamp,
        "analysis_code_commit": analysis_code_commit,
        "analysis_code_verified": verify_code_commit,
        "git_commit": _git_commit(),
        "spec": {"path": SPEC_RELPATH,
                 "sha256": sha256_file(REPO_ROOT / SPEC_RELPATH)},
        "frozen_screen": {"dir": screen["dir"],
                          "record_sha256": screen.get("record_sha256")},
        "tolerances": {"epsilon": bp.EPSILON, "tol_d": bp.TOL_D,
                       "budget": bp.BUDGET, "tau_delta": TAU_DELTA},
        "counts": bp.counts(),
        "decision": result["decision"],
    }

    staging = out_dir.with_name(f".{stamp}.staging")
    if staging.exists():
        raise B3AnalysisError(f"refusing existing staging dir: {staging}")
    staging.mkdir(parents=True)
    try:
        (staging / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        _write_summary(staging / "SUMMARY.md", manifest, result)
        if result["contrasts"]:
            _write_csv(staging / "contrasts.csv", result["contrasts"], [
                "setting", "seed", "n_trips", "b", "direction_sign",
                "delta_lo", "delta_hi", "delta_midpoint", "delta_width",
                "direction_consistent_zero_excluding"])
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
