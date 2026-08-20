"""B3 baseline: no-solver certified-uplift analysis (retrospective).

Restates the certified convex-hull uplift interval
``z_D - z_CH in [uplift_lo, uplift_hi]`` from the committed B2
full-population table, deduplicated to one A2 baseline row per unique
instance, with A3-A5 used only as consistency witnesses whose FOUR-WAY
interval intersection must be nonempty.

Specification: doc/B3_UPLIFT_BASELINE_SPEC.md.  Stdlib only — importing
this module must never load egglab, python-mip, Gurobi/CBC bindings, or
the numerical stack; a regression enforces that.  The production CLI is
pinned to the canonical B2 input; alternate inputs exist only as
test-injection parameters of :func:`analyze`.
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

SCHEMA = "b3-uplift-baseline-v2"
LABEL = "retrospective-exploratory"
REPO_ROOT = Path(__file__).resolve().parents[2]
# repository-relative canonical input identity: any input directory whose
# files match the PINNED hashes below IS this input, so manifests record
# these portable paths regardless of the absolute checkout root
CANONICAL_RELDIR = "result/b2_full/20260818T140356Z"
CANONICAL_INPUT = REPO_ROOT / CANONICAL_RELDIR
PINNED_CELLS_SHA256 = (
    "45f946e4fabb42f01157666bd00df27c1c582b3e1d767c59ae53c25a4b6e80c6")
PINNED_B2_MANIFEST_SHA256 = (
    "d9546f4e3e040a7dec5a1b0a397753602a9e505147435994b09f384cd4c37742")
B2_SCHEMA = "b2-full-population-v1"
SERIALIZATION_TOL = 5e-8
METHODS = ("a2", "a3", "a4", "a5")
SEEDS = tuple(range(16))
N_TRIPS = (8, 12)
B_VALUES = ("0.01", "0.05")
EPSILON = 0.01
TOL_D = 0.01
BUDGET = 240
REQUIRED_COLUMNS = frozenset({
    "method", "seed", "n_trips", "b", "outcome", "certified", "epsilon",
    "tol_d", "ub_ch", "lb_best", "z_d_ub", "uplift_lo", "uplift_hi",
    "backend", "mip_version", "source_commit", "budget",
})
# byte-identity of these files against the claimed correction commit is
# part of artifact provenance
PROVENANCE_FILES = (
    "src/experiments/analyze_b3_baseline.py",
    "src/tests/test_b3_baseline_analysis.py",
    "doc/B3_UPLIFT_BASELINE_SPEC.md",
)
SCIENTIFIC_BOUNDARY = (
    "All 64 instances are synthetic (seeded generators); none is observed "
    "operator data.",
    "Battery capacity and per-vehicle charging power are fixed constants "
    "of the instance generator.",
    "There is no shared charger-count or depot-capacity constraint; "
    "vehicles charge independently.",
    "There is no V2G: energy flows only from grid to vehicle.",
    "The affine duck-shaped price environment is a stylized demand curve, "
    "not a solar-generation model.",
    "n_trips is workload/problem size, not a controlled fleet-size "
    "variable.",
    "There is no distribution network and no locational charging; prices "
    "are system-wide per slot.",
    "This is the minimal default-physics uplift slice, not the full B3 "
    "atlas.",
    "The result establishes certified synthetic signal and heterogeneity, "
    "not external validity or manuscript-grade novelty.",
)


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


def refuse_a6_paths(*paths: str | os.PathLike) -> None:
    """This analysis must never read or write any A6 input/output path."""
    for path in paths:
        resolved = Path(path).resolve()
        for part in resolved.parts:
            lowered = part.lower()
            if lowered.startswith("a6") or "a6_" in lowered:
                raise B3Error(
                    f"refusing A6 path (scientific boundary): {resolved}")


def verify_analysis_code_commit(claimed: str) -> bool:
    """Artifacts must be attributable to the exact correction commit.

    The claimed commit must be the FULL 40-character SHA, resolve in this
    repository, be an ancestor of (or equal to) HEAD, and the analyzer,
    specification, and test battery in the working tree must be
    byte-identical to that commit.  Tracked dirtiness refuses.
    """
    if (not claimed or len(claimed) != 40
            or not all(c in "0123456789abcdef" for c in claimed)):
        raise B3Error(
            "analysis-code-commit must be the full 40-character lowercase "
            "hexadecimal SHA")
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{claimed}^{{commit}}"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise B3Error(
            f"claimed commit {claimed} does not resolve") from exc
    if resolved != claimed:
        raise B3Error(
            f"claimed commit {claimed} resolves to {resolved}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", claimed, "HEAD"],
        cwd=REPO_ROOT).returncode
    if ancestor != 0:
        raise B3Error(
            f"claimed commit {claimed} is not an ancestor of HEAD")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT).decode()
    tracked_dirty = [
        line for line in dirty.splitlines() if not line.startswith("??")]
    if tracked_dirty:
        raise B3Error(
            "working tree has tracked modifications; commit the analyzer "
            "before generating artifacts")
    for relpath in PROVENANCE_FILES:
        committed = subprocess.check_output(
            ["git", "show", f"{claimed}:{relpath}"], cwd=REPO_ROOT)
        current = (REPO_ROOT / relpath).read_bytes()
        if committed != current:
            raise B3Error(
                f"{relpath} differs from the claimed correction commit "
                f"{claimed}; artifacts would be misattributed")
    return True


def load_canonical_population(input_dir: str | os.PathLike) -> dict:
    """Validate integrity and full-population structure; return rows."""
    input_dir = Path(input_dir)
    manifest_path = input_dir / "MANIFEST.json"
    cells_path = input_dir / "cells.csv"
    actual_manifest_sha = sha256_file(manifest_path)
    if actual_manifest_sha != PINNED_B2_MANIFEST_SHA256:
        raise B3Error(
            "canonical B2 manifest hash mismatch: pinned "
            f"{PINNED_B2_MANIFEST_SHA256} but the file hashes to "
            f"{actual_manifest_sha}")
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, ValueError) as exc:
        raise B3Error(f"cannot read canonical manifest: {exc}") from exc
    if manifest.get("schema") != B2_SCHEMA:
        raise B3Error(
            f"canonical manifest schema {manifest.get('schema')!r} is not "
            f"{B2_SCHEMA!r}")
    if manifest.get("analysis_code_verified") is not True:
        raise B3Error("canonical B2 population was not code-verified")
    actual_sha = sha256_file(cells_path)
    if actual_sha != PINNED_CELLS_SHA256:
        raise B3Error(
            "canonical cells.csv hash mismatch: pinned "
            f"{PINNED_CELLS_SHA256} but the file hashes to {actual_sha}")
    recorded_sha = (manifest.get("outputs") or {}).get("cells.csv")
    if recorded_sha != actual_sha:
        raise B3Error(
            "canonical cells.csv hash mismatch: manifest records "
            f"{recorded_sha!r} but the file hashes to {actual_sha!r}")
    tolerances = manifest.get("tolerances") or {}
    if (tolerances.get("epsilon") != [EPSILON]
            or tolerances.get("tol_d") != [TOL_D]
            or tolerances.get("budget") != [BUDGET]):
        raise B3Error(
            f"canonical manifest tolerances {tolerances!r} differ from the "
            "frozen population contract")
    population = manifest.get("population") or {}
    if population.get("method_cells") != 256 or (
            population.get("methods") != list(METHODS)):
        raise B3Error("canonical manifest population identity is invalid")
    declared_backends = set(
        (manifest.get("solver") or {}).get("backends") or ())
    declared_mips = set(
        (manifest.get("solver") or {}).get("mip_versions") or ())
    declared_commits = set(manifest.get("experiment_commits") or ())
    if not declared_backends or not declared_mips or not declared_commits:
        raise B3Error("canonical manifest solver/commit declarations are "
                      "missing")

    with open(cells_path, newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or ())
        missing = REQUIRED_COLUMNS - set(header)
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
    unknown_mip_rows = 0
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
        if _num(row, "budget", label) != BUDGET:
            raise B3Error(f"{label}: budget differs from 240")
        if row["backend"] not in declared_backends:
            raise B3Error(
                f"{label}: backend {row['backend']!r} is not declared in "
                "the B2 manifest")
        if row["mip_version"] not in declared_mips:
            raise B3Error(
                f"{label}: mip_version {row['mip_version']!r} is not "
                "declared in the B2 manifest")
        if row["source_commit"] not in declared_commits:
            raise B3Error(
                f"{label}: source_commit {row['source_commit']!r} is not "
                "among the B2 experiment_commits")
        if row["mip_version"] == "unknown":
            # historical rows: declared in the B2 manifest, so they are
            # preserved and DISCLOSED, never silently rejected or hidden
            unknown_mip_rows += 1
    if seen != expected_keys:
        raise B3Error("population does not cover the frozen grid exactly")
    return {
        "rows": rows,
        "manifest": manifest,
        "cells_sha256": actual_sha,
        "manifest_sha256": actual_manifest_sha,
        "csv_header": header,
        "row_count": len(rows),
        "unknown_mip_rows": unknown_mip_rows,
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


def classify_interval(lo: float, hi: float, label: str) -> str:
    if lo > 0.0:
        return "strictly-positive"
    if hi == 0.0:
        # z_d_ub == lb_best in the serialized evidence: the certified
        # interval is [-tol_d, 0] — an exact-zero upper boundary
        return "exact-zero-boundary"
    if lo < 0.0 < hi:
        return "strict-zero-crossing"
    raise B3Error(
        f"{label}: interval [{lo}, {hi}] does not fit the exhaustive "
        "classification")


def classify_contrast(lo: float, hi: float) -> str:
    if lo > 0.0:
        return "strictly-positive"
    if hi < 0.0:
        return "strictly-negative"
    return "crosses-or-touches-zero"


def analyze_population(rows: list[dict]) -> dict:
    """A2 baseline (64 rows), four-way cross-method audit, paired effects."""
    values: dict[tuple, dict[str, dict]] = {}
    meta: dict[tuple, dict[str, dict]] = {}
    for row in rows:
        key = (int(row["seed"]), int(row["n_trips"]), row["b"])
        label = (f"cell method={row['method']} seed={key[0]} n={key[1]} "
                 f"b={key[2]}")
        values.setdefault(key, {})[row["method"]] = recompute_uplift(
            row, label)
        meta.setdefault(key, {})[row["method"]] = row

    instance_rows = []
    audit_rows = []
    a2_by_key = {}
    for key in sorted(values):
        seed, n, b = key
        label = f"instance seed={seed} n={n} b={b}"
        methods = values[key]
        if set(methods) != set(METHODS):
            raise B3Error(f"{label}: methods incomplete")
        a2 = methods["a2"]
        a2_by_key[key] = a2
        dictator_shared = all(
            methods[m]["z_d_ub"] == a2["z_d_ub"]
            and methods[m]["tol_d"] == a2["tol_d"] for m in METHODS)
        if not dictator_shared:
            raise B3Error(
                f"{label}: dictator evidence (z_d_ub/tol_d) differs "
                "across methods")
        metadata_ok = all(
            methods[m]["epsilon"] == a2["epsilon"] for m in METHODS)
        if not metadata_ok:
            raise B3Error(f"{label}: per-method epsilon metadata diverges")
        los = [methods[m]["uplift_lo"] for m in METHODS]
        his = [methods[m]["uplift_hi"] for m in METHODS]
        intersection_lo = max(los)
        intersection_hi = min(his)
        if intersection_lo > intersection_hi:
            raise B3Error(
                f"{label}: four-way certified-interval intersection is "
                f"empty: [{intersection_lo}, {intersection_hi}]")
        lo_spread = max(los) - min(los)
        hi_spread = max(his) - min(his)
        max_spread = max(lo_spread, hi_spread)
        audit_rows.append({
            "seed": seed, "n_trips": n, "b": b,
            "a2_lo": methods["a2"]["uplift_lo"],
            "a2_hi": methods["a2"]["uplift_hi"],
            "a3_lo": methods["a3"]["uplift_lo"],
            "a3_hi": methods["a3"]["uplift_hi"],
            "a4_lo": methods["a4"]["uplift_lo"],
            "a4_hi": methods["a4"]["uplift_hi"],
            "a5_lo": methods["a5"]["uplift_lo"],
            "a5_hi": methods["a5"]["uplift_hi"],
            "intersection_lo": intersection_lo,
            "intersection_hi": intersection_hi,
            "intersection_nonempty": intersection_lo <= intersection_hi,
            "lo_spread": lo_spread,
            "hi_spread": hi_spread,
            "max_spread": max_spread,
            "dictator_shared": dictator_shared,
            "metadata_ok": metadata_ok,
            "pass": (intersection_lo <= intersection_hi
                     and dictator_shared and metadata_ok),
        })
        lo, hi = a2["uplift_lo"], a2["uplift_hi"]
        instance_rows.append({
            "seed": seed, "n_trips": n, "b": b,
            "z_d_ub": a2["z_d_ub"], "tol_d": a2["tol_d"],
            "lb_best": a2["lb_best"], "ub_ch": a2["ub_ch"],
            "uplift_lo_raw": lo, "uplift_hi_raw": hi,
            # theorem z_D >= z_CH tightens the lower bound; the raw
            # value stays disclosed in the adjacent column
            "uplift_lo_tightened": max(0.0, lo),
            "width": a2["width"],
            "classification": classify_interval(lo, hi, label),
            "uplift_lo_per_trip": lo / n,
            "uplift_hi_per_trip": hi / n,
            "intersection_lo": intersection_lo,
            "intersection_hi": intersection_hi,
            "lo_spread": lo_spread,
            "hi_spread": hi_spread,
        })

    # paired effects by interval subtraction on the A2 baseline
    paired_rows = []
    for seed in SEEDS:
        for n in N_TRIPS:
            low = a2_by_key[(seed, n, B_VALUES[0])]
            high = a2_by_key[(seed, n, B_VALUES[1])]
            diff_lo = high["uplift_lo"] - low["uplift_hi"]
            diff_hi = high["uplift_hi"] - low["uplift_lo"]
            paired_rows.append({
                "family": "feedback_b", "seed": seed, "n_trips": n,
                "b": "0.05-0.01",
                "low_lo": low["uplift_lo"], "low_hi": low["uplift_hi"],
                "high_lo": high["uplift_lo"], "high_hi": high["uplift_hi"],
                "diff_lo": diff_lo, "diff_hi": diff_hi,
                "classification": classify_contrast(diff_lo, diff_hi),
            })
    for seed in SEEDS:
        for b in B_VALUES:
            low = a2_by_key[(seed, N_TRIPS[0], b)]
            high = a2_by_key[(seed, N_TRIPS[1], b)]
            diff_lo = high["uplift_lo"] - low["uplift_hi"]
            diff_hi = high["uplift_hi"] - low["uplift_lo"]
            paired_rows.append({
                "family": "workload_n", "seed": seed, "n_trips": "12-8",
                "b": b,
                "low_lo": low["uplift_lo"], "low_hi": low["uplift_hi"],
                "high_lo": high["uplift_lo"], "high_hi": high["uplift_hi"],
                "diff_lo": diff_lo, "diff_hi": diff_hi,
                "classification": classify_contrast(diff_lo, diff_hi),
            })
    return {"instances": instance_rows, "audit": audit_rows,
            "paired": paired_rows}


def _stratum(rows: list[dict], scope: str) -> dict:
    los = [r["uplift_lo_raw"] for r in rows]
    his = [r["uplift_hi_raw"] for r in rows]
    widths = [r["width"] for r in rows]
    lo_pt = [r["uplift_lo_per_trip"] for r in rows]
    hi_pt = [r["uplift_hi_per_trip"] for r in rows]
    n_pos = sum(r["classification"] == "strictly-positive" for r in rows)
    n_cross = sum(
        r["classification"] == "strict-zero-crossing" for r in rows)
    n_bound = sum(
        r["classification"] == "exact-zero-boundary" for r in rows)
    count = len(rows)
    return {
        "scope": scope,
        "instances": count,
        "n_positive": n_pos, "n_crossing": n_cross, "n_boundary": n_bound,
        "share_positive": n_pos / count,
        "share_crossing": n_cross / count,
        "share_boundary": n_bound / count,
        "mean_uplift_lo": statistics.fmean(los),
        "median_uplift_lo": statistics.median(los),
        "mean_uplift_hi": statistics.fmean(his),
        "median_uplift_hi": statistics.median(his),
        "median_width": statistics.median(widths),
        "max_uplift_hi": max(his),
        "median_uplift_lo_per_trip": statistics.median(lo_pt),
        "median_uplift_hi_per_trip": statistics.median(hi_pt),
    }


def summarize_strata(instances: list[dict]) -> list[dict]:
    strata = [_stratum(instances, "overall")]
    for n in N_TRIPS:
        for b in B_VALUES:
            rows = [r for r in instances
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
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_format(row[column]) for column in columns])


def _family_counts(paired: list[dict], family: str) -> dict:
    rows = [r for r in paired if r["family"] == family]
    return {
        "total": len(rows),
        "positive": sum(
            r["classification"] == "strictly-positive" for r in rows),
        "negative": sum(
            r["classification"] == "strictly-negative" for r in rows),
        "unresolved": sum(
            r["classification"] == "crosses-or-touches-zero"
            for r in rows),
    }


def write_summary(path: Path, result: dict, strata: list[dict],
                  stamp: str, analysis_code_commit: str,
                  unknown_mip_rows: int) -> None:
    instances = result["instances"]
    audit = result["audit"]
    overall = strata[0]
    max_spread = max(r["max_spread"] for r in audit)
    feedback = _family_counts(result["paired"], "feedback_b")
    workload = _family_counts(result["paired"], "workload_n")
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
        "A3-A5 used only as consistency witnesses.",
        "- certified interval per instance: `z_D - z_CH in [uplift_lo, "
        "uplift_hi]` with `uplift_lo = (z_d_ub - tol_d) - ub_ch` and "
        "`uplift_hi = z_d_ub - lb_best`, recomputed from the committed "
        "CSV fields.",
        f"- historical rows with `mip_version == \"unknown\"`: "
        f"{unknown_mip_rows} of 256 method-cells (declared in the B2 "
        "manifest; preserved and disclosed, not rejected).",
        "",
        "## Overall (64 instances)",
        "",
        f"- classification: {overall['n_positive']} strictly positive, "
        f"{overall['n_crossing']} strict zero crossings, "
        f"{overall['n_boundary']} exact-zero boundaries",
        f"- uplift_lo (raw): mean {overall['mean_uplift_lo']:.6g}, median "
        f"{overall['median_uplift_lo']:.6g}",
        f"- uplift_hi (raw): mean {overall['mean_uplift_hi']:.6g}, median "
        f"{overall['median_uplift_hi']:.6g}, max "
        f"{overall['max_uplift_hi']:.6g}",
        f"- interval width: median {overall['median_width']:.6g} (bounded "
        "by tol_d + epsilon = 0.02)",
        f"- per-trip interval medians: [{overall['median_uplift_lo_per_trip']:.6g}, "
        f"{overall['median_uplift_hi_per_trip']:.6g}]",
        "",
        "## Cross-method audit (four-way intersection)",
        "",
        f"- nonempty four-way intersections: "
        f"{sum(r['intersection_nonempty'] for r in audit)} / {len(audit)}",
        f"- maximum cross-method endpoint spread: {max_spread:.6g}",
        "- shared dictator evidence and metadata checks pass on every "
        "instance.",
        "",
        "## Paired effects (interval subtraction; descriptive)",
        "",
        f"- feedback contrast (b=0.05 minus b=0.01, 32 pairs): "
        f"{feedback['positive']} strictly positive, "
        f"{feedback['negative']} strictly negative, "
        f"{feedback['unresolved']} crosses-or-touches zero",
        f"- workload contrast (n=12 minus n=8, 32 pairs): "
        f"{workload['positive']} strictly positive, "
        f"{workload['negative']} strictly negative, "
        f"{workload['unresolved']} crosses-or-touches zero",
        "- Stratum-level certification rates rise with n and b, but "
        "matched effects are heterogeneous and descriptive rather than "
        "causal.",
        "",
        "## Strata (n_trips x b)",
        "",
        "| stratum | instances | positive | crossing | boundary | "
        "lo median | hi median | width median |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for stratum in strata[1:]:
        lines.append(
            f"| {stratum['scope']} | {stratum['instances']} | "
            f"{stratum['n_positive']} | {stratum['n_crossing']} | "
            f"{stratum['n_boundary']} | "
            f"{stratum['median_uplift_lo']:.6g} | "
            f"{stratum['median_uplift_hi']:.6g} | "
            f"{stratum['median_width']:.6g} |")
    lines += [
        "",
        "## Scientific boundary",
        "",
    ]
    lines += [f"- {item}" for item in SCIENTIFIC_BOUNDARY]
    lines += [
        "",
        "## Caveats",
        "",
        "- With tol_d = epsilon = 0.01 the certified intervals are up to "
        "0.02 wide; `uplift_lo > 0` is the only certification of strictly "
        "positive uplift. Intervals containing 0 do NOT establish that "
        "uplift is absent — only that it is below the certification "
        "resolution.",
        "- Uplift as a percentage of total integrated cost is deliberately "
        "NOT the primary normalization; per-trip bounds are reported "
        "instead.",
    ]
    path.write_text("\n".join(lines) + "\n")


def analyze(input_dir: str | os.PathLike, out_base: str | os.PathLike,
            stamp: str, analysis_code_commit: str, *,
            verify_code_commit: bool = True) -> str:
    refuse_a6_paths(input_dir, out_base)
    if verify_code_commit:
        verify_analysis_code_commit(analysis_code_commit)
    population = load_canonical_population(input_dir)
    result = analyze_population(population["rows"])
    strata = summarize_strata(result["instances"])

    out_base = Path(out_base)
    out_base.mkdir(parents=True, exist_ok=True)
    out_dir = out_base / stamp
    if out_dir.exists():
        raise B3Error(f"refusing existing output directory: {out_dir}")
    staging = Path(tempfile.mkdtemp(
        prefix=f".{stamp}.b3-staging-", dir=out_base))
    try:
        write_csv(
            staging / "instance_uplift.csv", result["instances"],
            ["seed", "n_trips", "b", "z_d_ub", "tol_d", "lb_best", "ub_ch",
             "uplift_lo_raw", "uplift_hi_raw", "uplift_lo_tightened",
             "width", "classification",
             "uplift_lo_per_trip", "uplift_hi_per_trip",
             "intersection_lo", "intersection_hi",
             "lo_spread", "hi_spread"])
        write_csv(
            staging / "cross_method_audit.csv", result["audit"],
            ["seed", "n_trips", "b",
             "a2_lo", "a2_hi", "a3_lo", "a3_hi",
             "a4_lo", "a4_hi", "a5_lo", "a5_hi",
             "intersection_lo", "intersection_hi",
             "intersection_nonempty",
             "lo_spread", "hi_spread", "max_spread",
             "dictator_shared", "metadata_ok", "pass"])
        write_csv(
            staging / "paired_effects.csv", result["paired"],
            ["family", "seed", "n_trips", "b",
             "low_lo", "low_hi", "high_lo", "high_hi",
             "diff_lo", "diff_hi", "classification"])
        write_csv(
            staging / "strata_summary.csv", strata,
            ["scope", "instances",
             "n_positive", "n_crossing", "n_boundary",
             "share_positive", "share_crossing", "share_boundary",
             "mean_uplift_lo", "median_uplift_lo",
             "mean_uplift_hi", "median_uplift_hi",
             "median_width", "max_uplift_hi",
             "median_uplift_lo_per_trip", "median_uplift_hi_per_trip"])
        write_summary(staging / "SUMMARY.md", result, strata, stamp,
                      analysis_code_commit,
                      population["unknown_mip_rows"])
        outputs = sorted([
            "instance_uplift.csv", "cross_method_audit.csv",
            "paired_effects.csv", "strata_summary.csv", "SUMMARY.md"])
        manifest = {
            "schema": SCHEMA,
            "label": LABEL,
            "stamp": stamp,
            "analysis_code_commit": analysis_code_commit,
            "analysis_code_verified": verify_code_commit,
            "inputs": {
                "cells_csv": {
                    # repository-relative canonical identity: the pinned
                    # hash guarantees content identity at any checkout root
                    "path": f"{CANONICAL_RELDIR}/cells.csv",
                    "sha256": population["cells_sha256"],
                    "csv_header": population["csv_header"],
                    "row_count": population["row_count"],
                    "unknown_mip_rows": population["unknown_mip_rows"],
                },
                "b2_manifest": {
                    "path": f"{CANONICAL_RELDIR}/MANIFEST.json",
                    "sha256": population["manifest_sha256"],
                    "schema": B2_SCHEMA,
                },
                "b2_analysis_code_commit":
                    population["manifest"].get("analysis_code_commit"),
            },
            "population": {
                "method_cells": 256,
                "baseline_instances": len(result["instances"]),
                "audit_rows": len(result["audit"]),
                "paired_contrasts": len(result["paired"]),
                "methods": list(METHODS),
                "baseline_method": "a2",
            },
            "tolerances": {
                "serialization_tol": SERIALIZATION_TOL,
                "epsilon": EPSILON,
                "tol_d": TOL_D,
                "budget": BUDGET,
            },
            "scientific_boundary": list(SCIENTIFIC_BOUNDARY),
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
    parser.add_argument(
        "--out", default=str(REPO_ROOT / "result" / "b3_baseline"))
    parser.add_argument("--stamp", required=True)
    parser.add_argument("--analysis-code-commit", required=True)
    args = parser.parse_args()
    # the production CLI is PINNED to the canonical B2 input
    out_dir = analyze(CANONICAL_INPUT, args.out, args.stamp,
                      args.analysis_code_commit)
    print(out_dir)


if __name__ == "__main__":
    main()
