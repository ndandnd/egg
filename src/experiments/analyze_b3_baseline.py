"""B3 baseline: no-solver certified-uplift analysis (retrospective).

Restates the certified convex-hull uplift interval
``z_D - z_CH in [uplift_lo, uplift_hi]`` from the committed B2
full-population table, deduplicated to one A2 baseline row per unique
instance, with A3-A5 used only as consistency witnesses.

Specification: doc/B3_BASELINE_SPEC.md.  Stdlib only — importing this
module must never load egglab, python-mip, Gurobi/CBC bindings, or the
numerical stack; a regression enforces that.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = "b3-baseline-v1"
LABEL = "retrospective-exploratory"
REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_INPUT = REPO_ROOT / "result" / "b2_full" / "20260818T140356Z"
SERIALIZATION_TOL = 5e-8
METHODS = ("a2", "a3", "a4", "a5")
WITNESSES = ("a3", "a4", "a5")
SEEDS = tuple(range(16))
N_TRIPS = (8, 12)
B_VALUES = ("0.01", "0.05")
EPSILON = 0.01
TOL_D = 0.01
REQUIRED_COLUMNS = frozenset({
    "method", "seed", "n_trips", "b", "outcome", "certified", "epsilon",
    "tol_d", "ub_ch", "lb_best", "z_d_ub", "uplift_lo", "uplift_hi",
})


class B3Error(RuntimeError):
    """The baseline cannot be produced without weakening its contract."""


def sha256_file(path: str | os.PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _num(row: dict, field: str, label: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise B3Error(f"{label}: field {field} is not numeric") from exc
    if not math.isfinite(value):
        raise B3Error(f"{label}: field {field} is not finite")
    return value


def verify_analysis_code_commit(claimed: str) -> bool:
    """The artifacts must be attributable to the committed analyzer."""
    if not claimed or not all(c in "0123456789abcdef" for c in claimed) \
            or not 7 <= len(claimed) <= 40:
        raise B3Error(
            "analysis-code-commit must be 7-40 lowercase hexadecimal")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).decode().strip()
    if not head.startswith(claimed):
        raise B3Error(
            f"HEAD {head} does not match claimed commit {claimed}")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT).decode()
    tracked_dirty = [
        line for line in dirty.splitlines() if not line.startswith("??")]
    if tracked_dirty:
        raise B3Error(
            "working tree has tracked modifications; commit the analyzer "
            "before generating artifacts")
    return True


def load_canonical_population(input_dir: str | os.PathLike) -> dict:
    """Validate integrity and full-population structure; return rows."""
    input_dir = Path(input_dir)
    manifest_path = input_dir / "MANIFEST.json"
    cells_path = input_dir / "cells.csv"
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, ValueError) as exc:
        raise B3Error(f"cannot read canonical manifest: {exc}") from exc
    recorded_sha = (manifest.get("outputs") or {}).get("cells.csv")
    actual_sha = sha256_file(cells_path)
    if recorded_sha != actual_sha:
        raise B3Error(
            "canonical cells.csv hash mismatch: manifest records "
            f"{recorded_sha!r} but the file hashes to {actual_sha!r}")

    with open(cells_path, newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or ())
        if missing:
            raise B3Error(f"cells.csv lacks columns: {sorted(missing)}")
        rows = list(reader)
    if len(rows) != 256:
        raise B3Error(
            f"population must be exactly 256 method-cells; found "
            f"{len(rows)}")

    expected_keys = {
        (method, seed, n, b)
        for method in METHODS for seed in SEEDS
        for n in N_TRIPS for b in B_VALUES
    }
    seen = set()
    for row in rows:
        label = (f"cell method={row.get('method')} seed={row.get('seed')} "
                 f"n={row.get('n_trips')} b={row.get('b')}")
        try:
            key = (row["method"], int(row["seed"]), int(row["n_trips"]),
                   row["b"])
        except (KeyError, ValueError) as exc:
            raise B3Error(f"{label}: malformed identity") from exc
        if key not in expected_keys:
            raise B3Error(f"{label}: outside the frozen 256-cell grid")
        if key in seen:
            raise B3Error(f"{label}: duplicate method-cell")
        seen.add(key)
        if row["outcome"] != "certified" or row["certified"] != "True":
            raise B3Error(f"{label}: population row is not certified")
        if _num(row, "epsilon", label) != EPSILON:
            raise B3Error(f"{label}: epsilon differs from 0.01")
        if _num(row, "tol_d", label) != TOL_D:
            raise B3Error(f"{label}: tol_d differs from 0.01")
    if seen != expected_keys:
        raise B3Error("population does not cover the frozen grid exactly")
    return {
        "rows": rows,
        "manifest": manifest,
        "cells_sha256": actual_sha,
        "manifest_sha256": sha256_file(manifest_path),
        "cells_path": str(cells_path),
        "manifest_path": str(manifest_path),
    }


def recompute_uplift(row: dict, label: str) -> dict:
    """Recompute the certified interval from serialized fields only."""
    ub = _num(row, "ub_ch", label)
    lb = _num(row, "lb_best", label)
    z_d = _num(row, "z_d_ub", label)
    tol_d = _num(row, "tol_d", label)
    epsilon = _num(row, "epsilon", label)
    lo = (z_d - tol_d) - ub
    hi = z_d - lb
    for field, value in (("uplift_lo", lo), ("uplift_hi", hi)):
        recorded = _num(row, field, label)
        if abs(recorded - value) > SERIALIZATION_TOL:
            raise B3Error(
                f"{label}: recorded {field}={recorded!r} deviates from the "
                f"recomputed value {value!r} beyond the serialization "
                f"tolerance {SERIALIZATION_TOL}")
    if hi < lo:
        raise B3Error(f"{label}: empty uplift interval [{lo}, {hi}]")
    width = hi - lo
    if width > tol_d + epsilon + SERIALIZATION_TOL:
        raise B3Error(
            f"{label}: interval width {width} exceeds tol_d + epsilon")
    if hi < -SERIALIZATION_TOL:
        raise B3Error(
            f"{label}: uplift_hi={hi} contradicts z_D >= z_CH")
    return {"ub_ch": ub, "lb_best": lb, "z_d_ub": z_d, "tol_d": tol_d,
            "epsilon": epsilon, "uplift_lo": lo, "uplift_hi": hi,
            "width": width}


def analyze_population(rows: list[dict]) -> dict:
    """Baseline rows (A2 once per instance) + witness consistency."""
    by_instance: dict[tuple, dict[str, dict]] = {}
    values: dict[tuple, dict[str, dict]] = {}
    for row in rows:
        key = (int(row["seed"]), int(row["n_trips"]), row["b"])
        label = (f"cell method={row['method']} seed={key[0]} n={key[1]} "
                 f"b={key[2]}")
        by_instance.setdefault(key, {})[row["method"]] = row
        values.setdefault(key, {})[row["method"]] = recompute_uplift(
            row, label)

    baseline = []
    witness_rows = []
    for key in sorted(by_instance):
        seed, n, b = key
        label = f"instance seed={seed} n={n} b={b}"
        methods = values[key]
        a2 = methods["a2"]
        # the dictator stage is shared evidence: identical across methods
        for method in METHODS:
            if methods[method]["z_d_ub"] != a2["z_d_ub"] or (
                    methods[method]["tol_d"] != a2["tol_d"]):
                raise B3Error(
                    f"{label}: {method} dictator evidence (z_d_ub/tol_d) "
                    "differs from a2")
        baseline.append({
            "seed": seed, "n_trips": n, "b": b,
            "ub_ch": a2["ub_ch"], "lb_best": a2["lb_best"],
            "z_d_ub": a2["z_d_ub"], "tol_d": a2["tol_d"],
            "uplift_lo": a2["uplift_lo"], "uplift_hi": a2["uplift_hi"],
            "width": a2["width"],
            "positive_uplift_certified": a2["uplift_lo"] > 0.0,
        })
        for method in WITNESSES:
            w = methods[method]
            intersects = not (w["uplift_hi"] < a2["uplift_lo"]
                              or w["uplift_lo"] > a2["uplift_hi"])
            witness_rows.append({
                "seed": seed, "n_trips": n, "b": b, "witness": method,
                "witness_lo": w["uplift_lo"], "witness_hi": w["uplift_hi"],
                "a2_lo": a2["uplift_lo"], "a2_hi": a2["uplift_hi"],
                "intersects_a2": intersects,
                "z_d_ub_equal": w["z_d_ub"] == a2["z_d_ub"],
            })
            if not intersects:
                raise B3Error(
                    f"{label}: witness {method} interval "
                    f"[{w['uplift_lo']}, {w['uplift_hi']}] does not "
                    f"intersect the a2 interval "
                    f"[{a2['uplift_lo']}, {a2['uplift_hi']}]")
    return {"baseline": baseline, "witnesses": witness_rows}


def _stratum(rows: list[dict], scope: str) -> dict:
    los = [r["uplift_lo"] for r in rows]
    his = [r["uplift_hi"] for r in rows]
    widths = [r["width"] for r in rows]
    return {
        "scope": scope,
        "instances": len(rows),
        "uplift_lo_min": min(los), "uplift_lo_median":
            statistics.median(los), "uplift_lo_max": max(los),
        "uplift_hi_min": min(his), "uplift_hi_median":
            statistics.median(his), "uplift_hi_max": max(his),
        "width_min": min(widths), "width_median":
            statistics.median(widths), "width_max": max(widths),
        "n_positive_lo": sum(r["uplift_lo"] > 0.0 for r in rows),
        "n_negative_hi": sum(r["uplift_hi"] < 0.0 for r in rows),
    }


def summarize_strata(baseline: list[dict]) -> list[dict]:
    strata = [_stratum(baseline, "overall")]
    for n in N_TRIPS:
        for b in B_VALUES:
            rows = [r for r in baseline
                    if r["n_trips"] == n and r["b"] == b]
            strata.append(_stratum(rows, f"n{n}_b{b}"))
    return strata


def _format(value):
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_format(row[column]) for column in columns])


def write_summary(path: Path, baseline: list[dict], strata: list[dict],
                  stamp: str, analysis_code_commit: str) -> None:
    overall = strata[0]
    positive = [r for r in baseline if r["positive_uplift_certified"]]
    lines = [
        f"# B3 baseline: certified uplift intervals ({stamp})",
        "",
        "**Label: RETROSPECTIVE / EXPLORATORY.** This analysis restates "
        "already-certified evidence from the committed B2 full population "
        "(no solver was run, no new experiment was launched); it inherits "
        "every caveat of `doc/MEASUREMENT_RESULTS.md`.",
        "",
        f"- analysis_code_commit: `{analysis_code_commit}`",
        "- baseline: one **A2** row per each of the 64 unique instances; "
        "A3-A5 used only as consistency witnesses (all witness intervals "
        "intersect the A2 interval; dictator evidence identical).",
        "- certified interval per instance: `z_D - z_CH in [uplift_lo, "
        "uplift_hi]` with `uplift_lo = (z_d_ub - tol_d) - ub_ch` and "
        "`uplift_hi = z_d_ub - lb_best`, recomputed from the committed "
        "CSV fields.",
        "",
        "## Overall (64 instances)",
        "",
        f"- uplift_lo: min {overall['uplift_lo_min']:.6g}, median "
        f"{overall['uplift_lo_median']:.6g}, max "
        f"{overall['uplift_lo_max']:.6g}",
        f"- uplift_hi: min {overall['uplift_hi_min']:.6g}, median "
        f"{overall['uplift_hi_median']:.6g}, max "
        f"{overall['uplift_hi_max']:.6g}",
        f"- interval width: median {overall['width_median']:.6g}, max "
        f"{overall['width_max']:.6g} (bounded by tol_d + epsilon = 0.02)",
        f"- instances with certified strictly positive uplift "
        f"(uplift_lo > 0): {len(positive)} / 64",
        f"- instances contradicting z_D >= z_CH (uplift_hi < 0): "
        f"{overall['n_negative_hi']} (must be 0)",
        "",
        "## Strata (n_trips x b)",
        "",
        "| stratum | instances | lo median | hi median | width median | "
        "positive lo |",
        "|---|---|---|---|---|---|",
    ]
    for stratum in strata[1:]:
        lines.append(
            f"| {stratum['scope']} | {stratum['instances']} | "
            f"{stratum['uplift_lo_median']:.6g} | "
            f"{stratum['uplift_hi_median']:.6g} | "
            f"{stratum['width_median']:.6g} | "
            f"{stratum['n_positive_lo']} |")
    lines += [
        "",
        "## Caveats",
        "",
        "- With tol_d = epsilon = 0.01 the certified intervals are up to "
        "0.02 wide; `uplift_lo > 0` is the only certification of strictly "
        "positive uplift. Intervals containing 0 do NOT establish that "
        "uplift is absent — only that it is below the certification "
        "resolution.",
        "- Small synthetic instances (n_trips 8/12, T=28); this baseline "
        "is a restatement, not a new measurement, and must not be quoted "
        "as a population estimate for larger fleets.",
    ]
    path.write_text("\n".join(lines) + "\n")


def analyze(input_dir: str | os.PathLike, out_base: str | os.PathLike,
            stamp: str, analysis_code_commit: str, *,
            verify_code_commit: bool = True) -> str:
    if verify_code_commit:
        verify_analysis_code_commit(analysis_code_commit)
    population = load_canonical_population(input_dir)
    result = analyze_population(population["rows"])
    strata = summarize_strata(result["baseline"])

    out_base = Path(out_base)
    out_base.mkdir(parents=True, exist_ok=True)
    out_dir = out_base / stamp
    if out_dir.exists():
        raise B3Error(f"refusing existing output directory: {out_dir}")
    staging = Path(tempfile.mkdtemp(
        prefix=f".{stamp}.b3-staging-", dir=out_base))
    try:
        write_csv(
            staging / "uplift_baseline.csv", result["baseline"],
            ["seed", "n_trips", "b", "ub_ch", "lb_best", "z_d_ub", "tol_d",
             "uplift_lo", "uplift_hi", "width",
             "positive_uplift_certified"])
        write_csv(
            staging / "witness_consistency.csv", result["witnesses"],
            ["seed", "n_trips", "b", "witness", "witness_lo", "witness_hi",
             "a2_lo", "a2_hi", "intersects_a2", "z_d_ub_equal"])
        write_csv(
            staging / "strata_summary.csv", strata,
            ["scope", "instances",
             "uplift_lo_min", "uplift_lo_median", "uplift_lo_max",
             "uplift_hi_min", "uplift_hi_median", "uplift_hi_max",
             "width_min", "width_median", "width_max",
             "n_positive_lo", "n_negative_hi"])
        write_summary(staging / "SUMMARY.md", result["baseline"], strata,
                      stamp, analysis_code_commit)
        outputs = sorted([
            "uplift_baseline.csv", "witness_consistency.csv",
            "strata_summary.csv", "SUMMARY.md"])
        manifest = {
            "schema": SCHEMA,
            "label": LABEL,
            "stamp": stamp,
            "analysis_code_commit": analysis_code_commit,
            "analysis_code_verified": verify_code_commit,
            "inputs": {
                "cells_csv": {
                    "path": population["cells_path"],
                    "sha256": population["cells_sha256"],
                },
                "b2_manifest": {
                    "path": population["manifest_path"],
                    "sha256": population["manifest_sha256"],
                },
                "b2_analysis_code_commit":
                    population["manifest"].get("analysis_code_commit"),
            },
            "population": {
                "method_cells": 256,
                "baseline_instances": len(result["baseline"]),
                "witness_rows": len(result["witnesses"]),
                "methods": list(METHODS),
                "baseline_method": "a2",
            },
            "tolerances": {
                "serialization_tol": SERIALIZATION_TOL,
                "epsilon": EPSILON,
                "tol_d": TOL_D,
            },
            "outputs": {name: sha256_file(staging / name)
                        for name in outputs},
        }
        with open(staging / "MANIFEST.json", "w") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.rename(staging, out_dir)
    except BaseException:
        # the staging tree contains only files this run just wrote
        for entry in staging.glob("*"):
            entry.unlink()
        staging.rmdir()
        raise
    return str(out_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(CANONICAL_INPUT))
    parser.add_argument(
        "--out", default=str(REPO_ROOT / "result" / "b3_baseline"))
    parser.add_argument("--stamp", required=True)
    parser.add_argument("--analysis-code-commit", required=True)
    args = parser.parse_args()
    out_dir = analyze(args.input, args.out, args.stamp,
                      args.analysis_code_commit)
    print(out_dir)


if __name__ == "__main__":
    main()
