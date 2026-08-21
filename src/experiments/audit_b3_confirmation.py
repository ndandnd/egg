#!/usr/bin/env python3
"""Exact-count + frozen-binding audit for the B3 confirmation run tree.

Mirrors the hardened pilot audit (`audit_b3_factor_pilot`) for the frozen
confirmation population: exactly 48 A2 cells + 48 matched dictators (24
matched contrasts), the run manifest proven a byte-for-byte rebuild from
the frozen generator at the recorded factor, every cell cross-bound to
the manifest / run commit / selection-artifact SHA / instance+market
hashes / GRB solver identity / matched dictator endpoints, and the full
column-generation sanity battery delegated to
``experiments.audit_runs._cg_sane``.

Refusals: any A6 dir/method, a seed outside {32..37}, a wrong cell count,
factor drift, a missing/tampered run manifest or cell-identity sidecar, a
CG/dictator z_d_ub mismatch, a non-GRB solver, a non-OPTIMAL/unconverged
dictator, an uncertified A2 cell, or any path overlapping the pilot
outcome tree.
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

import experiments.b3_confirmation as cc
from experiments.audit_runs import _cg_sane


def _load(path: Path):
    # BLOCKER D: strict JSON everywhere the audit parses — reject duplicate
    # keys and non-regular/changing files via the shared primitive
    import experiments.b3_pilot_evidence as evidence
    return evidence.strict_json_loads(
        evidence.read_regular_bytes_once(Path(path), str(path)), str(path))


def _finite(x) -> bool:
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and math.isfinite(x))


def _validate_manifest(runs: Path, problems: list) -> dict | None:
    try:
        loaded = cc.load_run_manifest(runs)
    except cc.B3ConfirmationError as exc:
        problems.append(f"run manifest: {exc}")
        return None
    manifest = loaded["manifest"]
    factor = manifest.get("selected_factor")
    if factor not in cc.DIRECTION_SIGN:
        problems.append(f"run manifest selected_factor {factor!r} invalid")
        return None
    solver = manifest.get("solver") or {}
    try:
        rebuilt = cc.build_run_manifest(
            factor,
            {"sha256": manifest.get("selection_artifact_sha256", "")},
            git_commit=manifest.get("run_commit", ""),
            backend_name=solver.get("backend", ""),
            mip_gap=solver.get("mip_gap"))
    except cc.B3ConfirmationError as exc:
        problems.append(f"run manifest not reproducible: {exc}")
        return None
    if cc.canonical_manifest_bytes(rebuilt) != cc.canonical_manifest_bytes(
            manifest):
        problems.append(
            "run manifest is not a byte-for-byte rebuild from the frozen "
            "generator at the recorded factor (tampered manifest)")
        return None
    if manifest.get("screen_record_sha256") != cc.FROZEN_SCREEN_RECORD_SHA256:
        problems.append("run manifest screen SHA != frozen screen anchor")
    if manifest.get("pilot_raw_tree_sha256") != (
            cc.FROZEN_PILOT_RAW_TREE["tree_sha256"]):
        problems.append("run manifest pilot raw-tree SHA != frozen anchor")
    if (manifest.get("spec") or {}).get("sha256") != cc.FROZEN_SPEC_SHA256:
        problems.append("run manifest spec SHA != frozen pilot spec hash")
    if manifest.get("counts") != cc.counts():
        problems.append("run manifest counts mismatch")
    return {"manifest": manifest, "sha256": loaded["sha256"],
            "market_by_cell": cc.market_hash_by_cell(manifest),
            "factor": factor}


def audit(runs_dir, *, selection_artifact=None, repo_root=cc.REPO_ROOT) -> dict:
    runs = Path(runs_dir)
    cc.refuse_pilot_runs_path(runs)
    problems: list[str] = []
    if not runs.is_dir():
        raise cc.B3ConfirmationError(f"runs dir does not exist: {runs}")

    run = _validate_manifest(runs, problems)
    if run is None:
        report = "# B3 confirmation audit\n\n- result: FAIL\n\n## Problems\n" \
            + "".join(f"- {p}\n" for p in problems)
        return {"ok": False, "problems": problems, "report": report,
                "certified": 0, "dictators": 0, "per_setting": {}}
    manifest = run["manifest"]
    manifest_sha = run["sha256"]
    market_by_cell = run["market_by_cell"]
    factor = run["factor"]
    run_commit = manifest["run_commit"]
    sel_sha = manifest["selection_artifact_sha256"]
    mip_gap = (manifest.get("solver") or {}).get("mip_gap")
    backend_name = (manifest.get("solver") or {}).get("backend")

    # HIGH 6: the GO selection artifact is MANDATORY and must revalidate under
    # the SAME gate as the driver (including the Critical-1 committed-bytes
    # check); an internally consistent run tree cannot audit clean without
    # proving its manifest came from a genuine committed GO.
    if selection_artifact is None:
        problems.append(
            "no selection artifact supplied; the confirmation audit requires "
            "the committed GO artifact that authorized the run")
    else:
        try:
            sel = cc.load_selection_artifact(selection_artifact,
                                             verify_commit=True,
                                             repo_root=repo_root)
            if sel["sha256"] != sel_sha:
                problems.append(
                    "supplied selection artifact SHA != run manifest binding")
            if sel["selected_factor"] != factor:
                problems.append(
                    "supplied selection artifact factor != run manifest factor")
        except cc.B3ConfirmationError as exc:
            problems.append(f"selection artifact failed revalidation: {exc}")

    cells = cc.build_cells(factor)
    expected = {c["tag"]: c for c in cells}
    present = {p.name for p in runs.iterdir() if p.is_dir()}
    for name in sorted(present - set(expected)):
        cc.assert_no_a6(name)
        problems.append(f"unexpected cell directory: {name}")

    per_setting: Counter = Counter()
    certified = 0
    dictators = 0
    for tag, cell in expected.items():
        cc.assert_confirmation_seed(cell["seed"])
        cc.assert_no_a6(cell["setting"], tag)
        key = f"{cell['setting']}|{cell['seed']}|{cell['n_trips']}"
        expected_hash = manifest["instance_hashes"].get(key)
        expected_market = market_by_cell.get(
            (cell["setting"], cell["seed"], cell["n_trips"], cell["b"]))
        cdir = runs / tag
        cg_path = cdir / "a2.cg.ckpt.json"
        d_path = cdir / "dictator.ckpt.json"
        id_path = cdir / cc.CELL_IDENTITY_FILENAME
        if not cg_path.is_file():
            problems.append(f"{tag}: missing A2 checkpoint")
            continue
        if not d_path.is_file():
            problems.append(f"{tag}: missing dictator checkpoint")
            continue
        if not id_path.is_file():
            problems.append(f"{tag}: missing cell-identity sidecar")
        else:
            expected_identity = cc.cell_identity(
                cell, manifest, market_hash=expected_market,
                instance_hash=expected_hash, run_manifest_sha256=manifest_sha,
                run_commit=run_commit, selection_artifact_sha256=sel_sha,
                mip_gap=mip_gap, backend_name=backend_name)
            if id_path.read_bytes() != cc.canonical_cell_identity_bytes(
                    expected_identity):
                problems.append(
                    f"{tag}: cell-identity sidecar does not match the expected "
                    "run/manifest/selection/commit binding")

        ck = _load(cg_path)
        dd = _load(d_path)
        ident = ck.get("identity") or {}
        method = ident.get("method", "a2")
        if str(method).lower().startswith("a6"):
            raise cc.B3ConfirmationError(f"{tag}: A6 method in a B3 cell")
        if method != cc.METHOD:
            problems.append(f"{tag}: method {method!r} != a2")
        if ident.get("instance_hash") != expected_hash:
            problems.append(f"{tag}: A2 instance hash != manifest (drift)")
        if ident.get("market_hash") != expected_market:
            problems.append(f"{tag}: A2 market hash != manifest")
        for k, want in (("epsilon", cc.EPSILON), ("budget", cc.BUDGET),
                        ("tol_d", cc.TOL_D)):
            if ident.get(k) != want:
                problems.append(f"{tag}: {k} {ident.get(k)} != {want}")
        if (ident.get("solver") or {}).get("backend") != "GRB":
            problems.append(f"{tag}: A2 solver backend != GRB")
        for err in _cg_sane(ck):
            problems.append(f"{tag}: {err}")

        d_ident = dd.get("identity") or {}
        z_d_ub = dd.get("z_d_ub")
        z_d_lb = dd.get("z_d_lb")
        if not _finite(ident.get("z_d_ub")) or not _finite(z_d_ub):
            problems.append(f"{tag}: nonfinite z_d_ub")
        elif abs(ident["z_d_ub"] - z_d_ub) > 1e-12:
            problems.append(f"{tag}: CG z_d_ub != dictator z_d_ub")
        if ident.get("tol_d") != d_ident.get("tol_d"):
            problems.append(f"{tag}: CG tol_d != dictator tol_d")
        if d_ident.get("instance_hash") != expected_hash:
            problems.append(f"{tag}: dictator instance hash != manifest")
        if d_ident.get("market_hash") != expected_market:
            problems.append(f"{tag}: dictator market hash != manifest")
        if d_ident.get("run_manifest_sha256") != manifest_sha:
            problems.append(f"{tag}: dictator run-manifest SHA != manifest")
        if d_ident.get("run_commit") != run_commit:
            problems.append(f"{tag}: dictator run commit != manifest")
        if d_ident.get("selection_artifact_sha256") != sel_sha:
            problems.append(f"{tag}: dictator selection SHA != manifest")
        if d_ident.get("setting") != cell["setting"]:
            problems.append(f"{tag}: dictator setting != cell setting")
        if not _finite(z_d_lb):
            problems.append(f"{tag}: dictator z_d_lb missing/nonfinite")
        else:
            adaptive_lb = (dd.get("adaptive") or {}).get("adaptive_lb")
            if not _finite(adaptive_lb) or abs(adaptive_lb - z_d_lb) > 1e-9:
                problems.append(f"{tag}: dictator z_d_lb != adaptive_lb")
        if not (dd.get("adaptive") or {}).get("adaptive_converged"):
            problems.append(f"{tag}: dictator unconverged")
        elif dd.get("status") != "OPTIMAL":
            problems.append(f"{tag}: dictator status != OPTIMAL")
        else:
            dictators += 1

        oc = ck.get("outcome") or {}
        if oc.get("type") == "certified" and oc.get("certified"):
            certified += 1
        else:
            problems.append(
                f"{tag}: A2 not certified within budget (INVALID/HALT)")
        per_setting[cell["setting"]] += 1

    complete = len([c for c in expected
                    if (runs / c / "a2.cg.ckpt.json").is_file()])
    if complete != cc.N_CELLS:
        problems.append(f"expected exactly {cc.N_CELLS} A2 cells, found {complete}")
    if certified != cc.N_CELLS:
        problems.append(f"expected {cc.N_CELLS} certified cells, found {certified}")
    if dictators != cc.N_CELLS:
        problems.append(
            f"expected {cc.N_CELLS} converged dictators, found {dictators}")
    for setting in (cc.BASELINE_SETTING, factor):
        if per_setting.get(setting, 0) != 24:
            problems.append(
                f"setting {setting}: {per_setting.get(setting, 0)} cells != 24")

    ok = not problems
    lines = [
        "# B3 confirmation audit", "",
        f"- selected factor: {factor}",
        f"- run manifest sha256: {manifest_sha}",
        f"- run commit: {run_commit}",
        f"- selection artifact sha256: {sel_sha}",
        f"- expected cells: {cc.N_CELLS} (A2) + {cc.N_CELLS} dictators "
        f"({cc.N_MATCHED_CONTRASTS} contrasts)",
        f"- certified A2 cells: {certified}/{cc.N_CELLS}",
        f"- converged dictators: {dictators}/{cc.N_CELLS}",
        f"- per-setting cells: {dict(per_setting)}",
        f"- result: {'PASS' if ok else 'FAIL'}",
    ]
    if problems:
        lines += ["", "## Problems"] + [f"- {p}" for p in problems]
    return {"ok": ok, "problems": problems, "report": "\n".join(lines) + "\n",
            "certified": certified, "dictators": dictators,
            "per_setting": dict(per_setting), "run_manifest_sha256": manifest_sha}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs/b3_confirmation")
    ap.add_argument("--selection-artifact", dest="selection_artifact",
                    default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    result = audit(args.runs, selection_artifact=args.selection_artifact)
    sys.stdout.write(result["report"])
    if args.out:
        Path(args.out).write_text(result["report"])
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
