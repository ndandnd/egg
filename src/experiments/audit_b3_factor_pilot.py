#!/usr/bin/env python3
"""Exact-count + frozen-binding audit for the B3 factor pilot run tree.

Verifies, without launching or scoring anything, that a completed run
directory holds EXACTLY the 60 expected A2 cells and 60 matched dictators,
that each is bound to the committed FROZEN factor-screen artifact (record
SHA-256, selected levels, and the exact ``Instance.hash()``), and that
each A2 checkpoint is complete and sane (delegating the full column-
generation sanity battery to ``experiments.audit_runs._cg_sane``, the same
one the production B2/A2 audit uses).

Refusals (fail-closed): any A6 method or A6 directory, any seed >= 16, a
wrong cell count (missing, extra, or unknown cell directory), factor drift
(a cell instance hash that disagrees with the frozen screen), a non-A2
method, or an uncertified A2 cell (the pilot requires certification within
budget; budget exhaustion is a validity halt, not a scientific null).
"""
from __future__ import annotations

import argparse
import json
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


def audit(runs_dir: str | os.PathLike,
          screen_dir: str | os.PathLike | None = None) -> dict:
    """Return {ok, problems, report, certified, dictators, per_setting}."""
    screen = bp.load_frozen_screen(screen_dir)
    runs = Path(runs_dir)
    problems: list[str] = []
    if not runs.is_dir():
        raise bp.B3PilotError(f"runs dir does not exist: {runs}")

    cells = bp.build_cells()
    expected = {c["tag"]: c for c in cells}
    present = {p.name for p in runs.iterdir() if p.is_dir()}

    # exact-count: no unknown or A6 directories may exist
    for name in sorted(present - set(expected)):
        bp.assert_no_a6(name)          # a stray A6 dir is a hard refusal
        problems.append(f"unexpected cell directory: {name}")

    per_setting: Counter = Counter()
    certified = 0
    dictators = 0

    for tag, cell in expected.items():
        bp.assert_development_seed(cell["seed"])
        bp.assert_no_a6(cell["setting"], tag)
        expected_hash = screen["instance_hashes"][
            (cell["setting"], cell["seed"], cell["n_trips"])]
        # rebuild + hash-check the instance (factor-drift gate)
        bp.bind_cell_to_screen(cell, screen)

        cdir = runs / tag
        cg_path = cdir / "a2.cg.ckpt.json"
        d_path = cdir / "dictator.ckpt.json"
        if not cg_path.is_file():
            problems.append(f"{tag}: missing A2 checkpoint")
            continue
        if not d_path.is_file():
            problems.append(f"{tag}: missing dictator checkpoint")
            continue

        ck = _load(cg_path)
        ident = ck.get("identity") or {}
        method = ident.get("method", "a2")
        if str(method).lower().startswith("a6"):
            raise bp.B3PilotError(f"{tag}: A6 method {method!r} in a B3 cell")
        if method != bp.METHOD:
            problems.append(f"{tag}: method {method!r} != a2")
        if ident.get("instance_hash") != expected_hash:
            problems.append(
                f"{tag}: A2 instance hash {ident.get('instance_hash')} != "
                f"frozen screen {expected_hash} (factor drift)")
        for key, want in (("epsilon", bp.EPSILON), ("budget", bp.BUDGET),
                          ("tol_d", bp.TOL_D)):
            if ident.get(key) != want:
                problems.append(f"{tag}: {key} {ident.get(key)} != {want}")

        for err in _cg_sane(ck):
            problems.append(f"{tag}: {err}")

        oc = ck.get("outcome") or {}
        if oc.get("type") == "certified" and oc.get("certified"):
            certified += 1
        else:
            problems.append(
                f"{tag}: A2 not certified within budget "
                f"(type={oc.get('type')}, certified={oc.get('certified')}) "
                "-- INVALID/HALT, not a scientific null")

        dd = _load(d_path)
        d_ident = dd.get("identity") or {}
        if d_ident.get("instance_hash") != expected_hash:
            problems.append(
                f"{tag}: dictator instance hash != frozen screen (drift)")
        if d_ident.get("screen_record_sha256") != screen["record_sha256"]:
            problems.append(
                f"{tag}: dictator screen SHA != frozen screen artifact")
        if not (dd.get("adaptive") or {}).get("adaptive_converged"):
            problems.append(f"{tag}: dictator adaptive certification unconverged")
        elif dd.get("status") != "OPTIMAL":
            problems.append(f"{tag}: dictator status {dd.get('status')} != OPTIMAL")
        else:
            dictators += 1
        per_setting[cell["setting"]] += 1

    # exact-count gates
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
            "per_setting": dict(per_setting)}


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
