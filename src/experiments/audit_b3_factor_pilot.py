#!/usr/bin/env python3
"""Exact-count + frozen-binding audit for the B3 factor pilot run tree.

Verifies, without launching or scoring anything, that a completed run
directory holds EXACTLY the 60 expected A2 cells and 60 matched dictators,
that the canonical Section-7 run manifest is authentic (a byte-for-byte
rebuild from the frozen screen at the manifest's own commit + solver
identity), and that every cell is cross-bound to that manifest, the run
commit, the frozen screen, its instance/market hashes, its solver
identity, and its matched dictator's ``z_d_ub``/``tol_d`` and recorded
endpoints.  Audit and analyzer use the same primitive replay in
``experiments.b3_pilot_evidence``; neither trusts bound histories or outcomes.

Refusals (fail-closed): any A6 method/dir, seed >= 16, wrong cell count,
factor drift, missing/tampered run manifest or cell-identity sidecar,
missing/altered market hash, CG/dictator ``z_d_ub`` mismatch, a non-GRB
solver, a non-OPTIMAL/unconverged dictator, or an uncertified A2 cell.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.b3_factor_pilot as bp
import experiments.b3_pilot_anchor as anchor
import experiments.b3_pilot_evidence as evidence


def _load(path: Path):
    return evidence.read_json_object_once(path, str(path))


def _validate_manifest(runs: Path, screen: dict, problems: list) -> dict | None:
    """Load the run manifest and prove it is authentic by rebuilding it
    byte-for-byte from the frozen screen at its declared commit + solver
    identity.  Returns {manifest, sha256, market_by_cell} or None."""
    path = runs / bp.RUN_MANIFEST_FILENAME
    try:
        raw = evidence.read_regular_bytes_once(path, "run MANIFEST.json")
        manifest = evidence.strict_json_loads(raw, "run MANIFEST.json")
        if not isinstance(manifest, dict):
            raise evidence.EvidenceError(
                "run MANIFEST.json: JSON root is not an object")
    except evidence.EvidenceError as exc:
        problems.append(f"run manifest: {exc}")
        return None
    if raw != bp.canonical_manifest_bytes(manifest):
        problems.append(
            "run manifest is not canonical byte-for-byte JSON (tampered)")
        return None
    manifest_sha = hashlib.sha256(raw).hexdigest()
    if manifest.get("schema") != bp.RUN_MANIFEST_SCHEMA:
        problems.append("run manifest schema mismatch")
        return None
    solver = manifest.get("solver") or {}
    run_spec_sha = (manifest.get("spec") or {}).get("sha256")
    current_spec_sha = bp.sha256_file(bp.REPO_ROOT / bp.SPEC_RELPATH)
    if run_spec_sha not in {
            anchor.FROZEN_RUN_SPEC_SHA256, current_spec_sha}:
        problems.append(
            "run manifest spec SHA is neither the frozen run identity nor "
            "the current outcome-blind amendment")
        return None
    try:
        rebuilt = bp.build_run_manifest(
            screen, git_commit=manifest.get("run_commit", ""),
            backend_name=solver.get("backend", ""),
            mip_gap=solver.get("mip_gap"))
    except bp.B3PilotError as exc:
        problems.append(f"run manifest not reproducible: {exc}")
        return None
    # The immutable run predates the outcome-blind documentation amendment.
    # Preserve its exact recorded spec identity while rebuilding all other
    # manifest fields from current frozen code.
    rebuilt["spec"]["sha256"] = run_spec_sha
    if bp.canonical_manifest_bytes(rebuilt) != bp.canonical_manifest_bytes(
            manifest):
        problems.append(
            "run manifest is not a byte-for-byte rebuild from the frozen "
            "screen (tampered manifest)")
        return None
    if manifest["screen"]["record_sha256"] != screen["record_sha256"]:
        problems.append("run manifest screen SHA != frozen screen")
    if manifest.get("counts") != bp.counts():
        problems.append("run manifest counts mismatch")
    return {"manifest": manifest, "sha256": manifest_sha,
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
        if not id_path.is_file() or id_path.is_symlink():
            problems.append(f"{tag}: missing cell-identity sidecar")
        elif run is not None:
            expected_identity = bp.cell_identity(
                cell, screen, market_hash=expected_market,
                run_manifest_sha256=manifest_sha, run_commit=run_commit,
                mip_gap=mip_gap, backend_name=backend_name)
            try:
                identity_bytes = evidence.read_regular_bytes_once(
                    id_path, f"{tag}: cell-identity sidecar")
            except evidence.EvidenceError as exc:
                problems.append(str(exc))
                identity_bytes = None
            if identity_bytes != bp.canonical_cell_identity_bytes(
                    expected_identity):
                problems.append(
                    f"{tag}: cell-identity sidecar does not match the expected "
                    "run/manifest/commit/screen/market binding")

        try:
            ck = _load(cg_path)
            dd = _load(d_path)
        except evidence.EvidenceError as exc:
            problems.append(f"{tag}: {exc}")
            continue
        ident = ck.get("identity") or {}
        method = ident.get("method", "a2")
        if str(method).lower().startswith("a6"):
            raise bp.B3PilotError(f"{tag}: A6 method {method!r} in a B3 cell")
        if run is None or expected_market is None:
            problems.append(f"{tag}: no authentic run-manifest identity")
            continue
        replayed, replay_problems = evidence.replay_cell_evidence(
            ck,
            dd,
            cell=cell,
            expected_instance_hash=expected_hash,
            expected_market_hash=expected_market,
            screen_record_sha256=screen["record_sha256"],
            run_manifest_sha256=manifest_sha,
            run_commit=run_commit,
            manifest_solver=manifest.get("solver") or {},
        )
        if replay_problems:
            problems.extend(replay_problems)
        elif replayed is not None:
            certified += 1
            dictators += 1
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
