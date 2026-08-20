#!/usr/bin/env python3
"""Exact-count + frozen-binding audit for the B3 factor pilot run tree.

Verifies, without launching or scoring anything, that a completed run
directory holds EXACTLY the 60 expected A2 cells and 60 matched dictators,
that the canonical Section-7 run manifest is authentic (a byte-for-byte
rebuild from the frozen screen at the manifest's own commit + solver
identity), and that every cell is cross-bound to that manifest, the run
commit, the frozen screen, its instance/market hashes, its solver
identity, and its matched dictator's ``z_d_ub``/``tol_d`` and recorded
endpoints.  The full column-generation sanity battery is delegated to
``experiments.audit_runs._cg_sane`` (the production B2/A2 audit).

Refusals (fail-closed): any A6 method/dir, seed >= 16, wrong cell count,
factor drift, missing/tampered run manifest or cell-identity sidecar,
missing/altered market hash, CG/dictator ``z_d_ub`` mismatch, a non-GRB
solver, a non-OPTIMAL/unconverged dictator, or an uncertified A2 cell.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.b3_factor_pilot as bp
from experiments.audit_runs import _cg_sane


def _load(path: Path):
    with open(path) as handle:
        return json.load(handle)


def _finite(x) -> bool:
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and math.isfinite(x))


def _validate_manifest(runs: Path, screen: dict, problems: list) -> dict | None:
    """Load the run manifest and prove it is authentic by rebuilding it
    byte-for-byte from the frozen screen at its declared commit + solver
    identity.  Returns {manifest, sha256, market_by_cell} or None."""
    try:
        loaded = bp.load_run_manifest(runs)
    except bp.B3PilotError as exc:
        problems.append(f"run manifest: {exc}")
        return None
    manifest = loaded["manifest"]
    solver = manifest.get("solver") or {}
    try:
        rebuilt = bp.build_run_manifest(
            screen, git_commit=manifest.get("run_commit", ""),
            backend_name=solver.get("backend", ""),
            mip_gap=solver.get("mip_gap"))
    except bp.B3PilotError as exc:
        problems.append(f"run manifest not reproducible: {exc}")
        return None
    if bp.canonical_manifest_bytes(rebuilt) != bp.canonical_manifest_bytes(
            manifest):
        problems.append(
            "run manifest is not a byte-for-byte rebuild from the frozen "
            "screen (tampered manifest)")
        return None
    if manifest["screen"]["record_sha256"] != screen["record_sha256"]:
        problems.append("run manifest screen SHA != frozen screen")
    if manifest["spec"]["sha256"] != bp.sha256_file(
            bp.REPO_ROOT / bp.SPEC_RELPATH):
        problems.append("run manifest spec SHA != committed spec")
    if manifest.get("counts") != bp.counts():
        problems.append("run manifest counts mismatch")
    return {"manifest": manifest, "sha256": loaded["sha256"],
            "market_by_cell": bp.market_hash_by_cell(manifest)}


def audit(runs_dir: str | os.PathLike,
          screen_dir: str | os.PathLike | None = None) -> dict:
    """Return {ok, problems, report, certified, dictators, per_setting}."""
    screen = bp.load_frozen_screen(screen_dir)
    runs = Path(runs_dir)
    problems: list[str] = []
    if not runs.is_dir():
        raise bp.B3PilotError(f"runs dir does not exist: {runs}")

    run = _validate_manifest(runs, screen, problems)
    market_by_cell = run["market_by_cell"] if run else {}
    manifest = run["manifest"] if run else {}
    manifest_sha = run["sha256"] if run else None
    run_commit = manifest.get("run_commit") if run else None
    mip_gap = ((manifest.get("solver") or {}).get("mip_gap")) if run else None
    backend_name = ((manifest.get("solver") or {}).get("backend")) if run \
        else None

    cells = bp.build_cells()
    expected = {c["tag"]: c for c in cells}
    present = {p.name for p in runs.iterdir() if p.is_dir()}
    for name in sorted(present - set(expected)):
        bp.assert_no_a6(name)          # a stray A6 dir is a hard refusal
        problems.append(f"unexpected cell directory: {name}")

    per_setting: Counter = Counter()
    certified = 0
    dictators = 0

    for tag, cell in expected.items():
        bp.assert_development_seed(cell["seed"])
        bp.assert_no_a6(cell["setting"], tag)
        key = (cell["setting"], cell["seed"], cell["n_trips"])
        expected_hash = screen["instance_hashes"][key]
        bp.bind_cell_to_screen(cell, screen)   # factor-drift gate
        expected_market = market_by_cell.get(
            (cell["setting"], cell["seed"], cell["n_trips"], cell["b"]))

        cdir = runs / tag
        cg_path = cdir / "a2.cg.ckpt.json"
        d_path = cdir / "dictator.ckpt.json"
        id_path = cdir / bp.CELL_IDENTITY_FILENAME
        if not cg_path.is_file():
            problems.append(f"{tag}: missing A2 checkpoint")
            continue
        if not d_path.is_file():
            problems.append(f"{tag}: missing dictator checkpoint")
            continue

        # --- cell-identity sidecar (exact run/manifest/commit binding) ------
        if not id_path.is_file():
            problems.append(f"{tag}: missing cell-identity sidecar")
        elif run is not None:
            expected_identity = bp.cell_identity(
                cell, screen, market_hash=expected_market,
                run_manifest_sha256=manifest_sha, run_commit=run_commit,
                mip_gap=mip_gap, backend_name=backend_name)
            if id_path.read_bytes() != bp.canonical_cell_identity_bytes(
                    expected_identity):
                problems.append(
                    f"{tag}: cell-identity sidecar does not match the expected "
                    "run/manifest/commit/screen/market binding")

        ck = _load(cg_path)
        dd = _load(d_path)
        ident = ck.get("identity") or {}
        method = ident.get("method", "a2")
        if str(method).lower().startswith("a6"):
            raise bp.B3PilotError(f"{tag}: A6 method {method!r} in a B3 cell")
        if method != bp.METHOD:
            problems.append(f"{tag}: method {method!r} != a2")
        if ident.get("instance_hash") != expected_hash:
            problems.append(f"{tag}: A2 instance hash != frozen screen (drift)")
        if expected_market is None:
            problems.append(f"{tag}: no market hash in run manifest")
        elif ident.get("market_hash") != expected_market:
            problems.append(
                f"{tag}: A2 market hash {ident.get('market_hash')} != manifest "
                f"{expected_market}")
        for k, want in (("epsilon", bp.EPSILON), ("budget", bp.BUDGET),
                        ("tol_d", bp.TOL_D)):
            if ident.get(k) != want:
                problems.append(f"{tag}: {k} {ident.get(k)} != {want}")
        if (ident.get("solver") or {}).get("backend") != "GRB":
            problems.append(
                f"{tag}: A2 solver backend "
                f"{(ident.get('solver') or {}).get('backend')!r} != GRB")

        for err in _cg_sane(ck):
            problems.append(f"{tag}: {err}")

        # --- CG <-> dictator cross-binding ---------------------------------
        d_ident = dd.get("identity") or {}
        z_d_ub = dd.get("z_d_ub")
        z_d_lb = dd.get("z_d_lb")
        if not _finite(ident.get("z_d_ub")) or not _finite(z_d_ub):
            problems.append(f"{tag}: nonfinite z_d_ub (CG/dictator)")
        elif abs(ident["z_d_ub"] - z_d_ub) > 1e-12:
            problems.append(
                f"{tag}: CG z_d_ub {ident['z_d_ub']} != dictator z_d_ub "
                f"{z_d_ub}")
        if ident.get("tol_d") != d_ident.get("tol_d"):
            problems.append(f"{tag}: CG tol_d != dictator tol_d")
        if d_ident.get("instance_hash") != expected_hash:
            problems.append(f"{tag}: dictator instance hash != frozen screen")
        if expected_market is not None and \
                d_ident.get("market_hash") != expected_market:
            problems.append(f"{tag}: dictator market hash != manifest")
        if d_ident.get("screen_record_sha256") != screen["record_sha256"]:
            problems.append(f"{tag}: dictator screen SHA != frozen screen")
        if run is not None and d_ident.get("run_manifest_sha256") != manifest_sha:
            problems.append(f"{tag}: dictator run-manifest SHA != run manifest")
        if run is not None and d_ident.get("run_commit") != run_commit:
            problems.append(f"{tag}: dictator run commit != run manifest")
        if d_ident.get("setting") != cell["setting"]:
            problems.append(f"{tag}: dictator setting != cell setting")

        # dictator recorded endpoints
        if not _finite(z_d_lb):
            problems.append(f"{tag}: dictator z_d_lb missing/nonfinite")
        else:
            adaptive_lb = (dd.get("adaptive") or {}).get("adaptive_lb")
            if not _finite(adaptive_lb) or abs(adaptive_lb - z_d_lb) > 1e-9:
                problems.append(
                    f"{tag}: dictator z_d_lb != recorded adaptive_lb")
        if not (dd.get("adaptive") or {}).get("adaptive_converged"):
            problems.append(f"{tag}: dictator adaptive certification unconverged")
        elif dd.get("status") != "OPTIMAL":
            problems.append(f"{tag}: dictator status {dd.get('status')} != OPTIMAL")
        else:
            dictators += 1

        oc = ck.get("outcome") or {}
        if oc.get("type") == "certified" and oc.get("certified"):
            certified += 1
        else:
            problems.append(
                f"{tag}: A2 not certified within budget "
                f"(type={oc.get('type')}, certified={oc.get('certified')}) "
                "-- INVALID/HALT, not a scientific null")
        per_setting[cell["setting"]] += 1

    complete_cells = len([c for c in expected
                          if (runs / c / "a2.cg.ckpt.json").is_file()])
    if complete_cells != bp.N_CELLS:
        problems.append(
            f"expected exactly {bp.N_CELLS} A2 cells, found {complete_cells}")
    if certified != bp.N_CELLS:
        problems.append(
            f"expected {bp.N_CELLS} certified A2 cells, found {certified}")
    if dictators != bp.N_CELLS:
        problems.append(
            f"expected {bp.N_CELLS} converged dictators, found {dictators}")
    for setting in bp.SETTING_ORDER:
        if per_setting.get(setting, 0) != 12:
            problems.append(
                f"setting {setting}: {per_setting.get(setting, 0)} cells != 12")

    ok = not problems
    report_lines = [
        "# B3 factor pilot audit",
        "",
        f"- frozen screen: {screen['dir']}",
        f"- screen record sha256: {screen['record_sha256']}",
        f"- run manifest sha256: {manifest_sha}",
        f"- run commit: {run_commit}",
        f"- expected cells: {bp.N_CELLS} (A2) + {bp.N_CELLS} dictators",
        f"- certified A2 cells: {certified}/{bp.N_CELLS}",
        f"- converged dictators: {dictators}/{bp.N_CELLS}",
        f"- per-setting cells: "
        f"{ {s: per_setting.get(s, 0) for s in bp.SETTING_ORDER} }",
        f"- result: {'PASS' if ok else 'FAIL'}",
    ]
    if problems:
        report_lines.append("")
        report_lines.append("## Problems")
        report_lines.extend(f"- {p}" for p in problems)
    report = "\n".join(report_lines) + "\n"
    return {"ok": ok, "problems": problems, "report": report,
            "certified": certified, "dictators": dictators,
            "per_setting": dict(per_setting), "run_manifest_sha256": manifest_sha}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs/b3_factor_pilot")
    ap.add_argument("--screen-dir", default=None)
    ap.add_argument("--out", default=None, help="write the report to this path")
    args = ap.parse_args()
    result = audit(args.runs, args.screen_dir)
    sys.stdout.write(result["report"])
    if args.out:
        Path(args.out).write_text(result["report"])
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
