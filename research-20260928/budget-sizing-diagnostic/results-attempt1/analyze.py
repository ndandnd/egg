"""Curate the sealed eight-cell sizing summary without opening native event logs.

Reads only the frozen declaration, summary, supervisor/wrapper receipts and
per-cell receipt/assessment pairs. Never launches an optimizer.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path


EXPECTED = {(s, c, b) for s in (0, 1) for c in (4, 16) for b in (4096, 8192)}
CSV_FIELDS = ("state", "pricing_call_cap", "rational_bit_cap", "outcome",
              "stop_reason", "pricing_requests", "master_calls", "max_rational_bits",
              "lower_floor4", "upper_ceil4", "gap_ceil6", "child_wall_s",
              "pricing_solver_wall_recorded_s", "pricing_solver_wall_complete",
              "master_solver_wall_recorded_s", "master_solver_wall_complete",
              "polish_wall_s", "complete_evidence", "on_time",
              "lower_exact_sha256", "upper_exact_sha256", "gap_exact_sha256")


def read(path):
    return json.loads(Path(path).read_text())


def digest(path_or_text, *, file=False):
    payload = Path(path_or_text).read_bytes() if file else path_or_text.encode()
    return hashlib.sha256(payload).hexdigest()


def directed(value, digits, *, upper=False):
    value = Fraction(value)
    scale = 10 ** digits
    units = (-((-value.numerator * scale) // value.denominator)
             if upper else (value.numerator * scale) // value.denominator)
    sign = "-" if units < 0 else ""
    size = abs(units)
    return f"{sign}{size // scale}.{size % scale:0{digits}d}"


def collect(sealed):
    sealed = Path(sealed)
    wrapper_path = sealed.with_name(sealed.name + ".slurm_wrapper_receipt.json")
    summary_path = sealed / "summary.json"
    frozen_path = sealed / "frozen.json"
    supervisor_path = sealed / "supervisor_receipt.json"
    summary, frozen, supervisor, wrapper = (read(path) for path in
                                            (summary_path, frozen_path, supervisor_path,
                                             wrapper_path))
    if (summary.get("protocol") != frozen.get("protocol")
            or supervisor.get("protocol") != frozen.get("protocol")
            or summary.get("accounted_cells") != 8
            or summary.get("all_declared_cells_accounted") is not True
            or supervisor.get("returncode") != 0
            or supervisor.get("stable_seal") is not True
            or supervisor.get("process_group_quiescent") is not True
            or supervisor.get("source_hashes_unchanged") is not True
            or any(wrapper.get(key) != 0 for key in
                   ("returncode", "freeze_returncode", "preflight_returncode",
                    "supervise_returncode"))):
        raise ValueError("Sealed top-level accounting/integrity did not pass")
    frozen_cells = {(item["state"], item["pricing_calls"], item["rational_bits"])
                    for item in frozen["design"]["cells"]}
    rows = summary["rows"]
    keys = [(r.get("state"), r.get("pricing_call_cap"), r.get("rational_bit_cap"))
            for r in rows]
    if len(rows) != 8 or len(set(keys)) != 8 or set(keys) != EXPECTED or frozen_cells != EXPECTED:
        raise ValueError("Exactly eight declared unique matrix cells required")
    curated = []
    for row in rows:
        state, calls, bits = (row[key] for key in
                              ("state", "pricing_call_cap", "rational_bit_cap"))
        folder = sealed / "synthetic_multivisit" / f"state{state}" / f"c{calls}_b{bits}"
        receipt_path, assessment_path = folder / "receipt.json", folder / "result.json"
        receipt, result = read(receipt_path), read(assessment_path)
        assessment = result["assessment"]
        if ((result["state"], result["pricing_calls"], result["rational_bits"])
                != (state, calls, bits)
                or receipt.get("returncode") != 0 or receipt.get("hard_timeout") is not False
                or receipt.get("on_time") is not True
                or receipt.get("elapsed_seconds") != row.get("child_wall_s")
                or assessment.get("complete_evidence") is not True
                or assessment.get("status") != row.get("outcome")
                or row.get("complete_evidence") is not True
                or row.get("on_time") is not True):
            raise ValueError(f"Cell receipt/assessment mismatch: {(state, calls, bits)}")
        lo, hi, gap = (Fraction(row[key]) for key in
                       ("lower_exact", "upper_exact", "gap_exact"))
        if lo > hi or hi - lo != gap:
            raise ValueError("Global enclosure arithmetic mismatch")
        assessed_lo, assessed_hi = map(Fraction, assessment["bounds"])
        if assessed_lo > lo or assessed_hi < hi:
            raise ValueError("Assessed native enclosure does not contain exact stored endpoints")
        item = {key: row.get(key) for key in CSV_FIELDS if key in row}
        item.update(lower_floor4=directed(lo, 4), upper_ceil4=directed(hi, 4, upper=True),
                    gap_ceil6=directed(gap, 6, upper=True),
                    lower_exact_sha256=digest(row["lower_exact"]),
                    upper_exact_sha256=digest(row["upper_exact"]),
                    gap_exact_sha256=digest(row["gap_exact"]),
                    receipt_sha256=digest(receipt_path, file=True),
                    assessment_sha256=digest(assessment_path, file=True))
        curated.append(item)
    curated.sort(key=lambda r: (r["state"], r["pricing_call_cap"], r["rational_bit_cap"]))
    return {"scope": "single development multivisit case, two markets, eight cold-hull cells",
            "native_tolerance_qualified": True, "ideal_model_certificate": False,
            "source_commit": frozen["source_commit"], "protocol": frozen["protocol"],
            "job_id": wrapper["job_id"], "whole_job_elapsed_s": wrapper["elapsed_whole_seconds"],
            "setup_s": wrapper["setup_seconds"],
            "supervisor_elapsed_s": supervisor["elapsed_seconds"],
            "source_sha256": {str(path.relative_to(sealed.parent)) if path != wrapper_path
                              else path.name: digest(path, file=True)
                              for path in (summary_path, frozen_path, supervisor_path, wrapper_path)},
            "exact_fraction_policy": "SHA-256 of stored exact endpoint text; original exact text stays in sealed summary",
            "rows": curated}


def plot(rows, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Patch
    matplotlib.rcParams["svg.fonttype"] = "none"
    plt.rcParams.update({"font.size": 10, "font.family": "DejaVu Sans"})
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.25), sharey=True)
    palette = {"certified": "#c8ebe7", "budget_exhausted": "#fbe4c5"}
    by_key = {(r["state"], r["pricing_call_cap"], r["rational_bit_cap"]): r for r in rows}
    for state, axis in enumerate(axes):
        for yi, bits in enumerate((8192, 4096)):
            for xi, calls in enumerate((4, 16)):
                row = by_key[(state, calls, bits)]
                axis.add_patch(Rectangle((xi - .47, yi - .44), .94, .88,
                                         facecolor=palette[row["outcome"]],
                                         edgecolor="#60717d", linewidth=.8))
                gap = row["gap_ceil6"]
                label = (f"Certified\nwidth ≤ {gap}" if row["outcome"] == "certified"
                         else f"Stopped\nwidth ≤ {directed(gap, 3, upper=True)}")
                axis.text(xi, yi, label, ha="center", va="center", fontsize=9,
                          color="#14222e")
        axis.set_xlim(-.5, 1.5)
        axis.set_ylim(1.5, -.5)
        axis.set_xticks((0, 1), ("4", "16"))
        axis.set_yticks((0, 1), ("8192", "4096"))
        axis.set_xlabel("Pricing-call cap")
        axis.set_title(f"Market {state}", fontsize=11, weight="bold")
        for spine in axis.spines.values():
            spine.set_visible(False)
    axes[0].set_ylabel("Rational-bit cap")
    fig.suptitle("Cold-hull budget limits on one multivisit case", fontsize=12, weight="bold")
    fig.legend(handles=(Patch(facecolor=palette["certified"], label="Certified"),
                        Patch(facecolor=palette["budget_exhausted"], label="Limit reached")),
               loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(.5, -.04))
    fig.tight_layout(rect=(0, .08, 1, .9))
    fig.savefig(out / "budget_matrix.svg", bbox_inches="tight")
    svg = out / "budget_matrix.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    fig.savefig(out / "budget_matrix.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sealed", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    data = collect(args.sealed)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "rows.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    with (args.out / "rows.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in CSV_FIELDS} for row in data["rows"])
    plot(data["rows"], args.out)


if __name__ == "__main__":
    main()
