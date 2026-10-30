"""Curate six sealed scalar rows; never read events or invoke an optimizer."""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path


CASES = tuple(f"native_scale_dev_s1006_n{n:02d}" for n in (8, 16, 24))
KINDS = ("source0", "target")
EXPECTED = {(case, kind) for case in CASES for kind in KINDS}
FIELDS = ("case", "market", "outcome", "stop_reason", "pricing_requests",
          "master_calls", "max_rational_bits", "lower_floor4", "upper_ceil4",
          "gap_ceil6", "child_wall_s", "pricing_solver_wall_recorded_s",
          "pricing_solver_wall_complete", "master_solver_wall_recorded_s",
          "master_solver_wall_complete", "polish_wall_s", "model_construction_s",
          "complete_evidence", "on_time", "lower_exact_sha256",
          "upper_exact_sha256", "gap_exact_sha256")


def read(path):
    return json.loads(Path(path).read_text())


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def directed(value, digits, *, upper=False):
    value = Fraction(value)
    scale = 10 ** digits
    units = (-((-value.numerator * scale) // value.denominator)
             if upper else (value.numerator * scale) // value.denominator)
    sign = "-" if units < 0 else ""
    absolute = abs(units)
    return f"{sign}{absolute // scale}.{absolute % scale:0{digits}d}"


def collect(sealed):
    sealed = Path(sealed)
    summary = read(sealed / "summary.json")
    frozen = read(sealed / "frozen.json")
    supervisor = read(sealed / "supervisor_receipt.json")
    wrapper = read(sealed.with_name(sealed.name + ".slurm_wrapper_receipt.json"))
    if (summary.get("protocol") != frozen.get("protocol")
            or supervisor.get("protocol") != frozen.get("protocol")
            or summary.get("accounted_cells") != 6
            or summary.get("all_declared_cells_accounted") is not True
            or supervisor.get("returncode") != 0
            or supervisor.get("stable_seal") is not True
            or supervisor.get("process_group_quiescent") is not True
            or supervisor.get("source_hashes_unchanged") is not True
            or any(wrapper.get(key) != 0 for key in
                   ("returncode", "freeze_returncode", "preflight_returncode",
                    "supervise_returncode"))):
        raise ValueError("Top-level accounting or source/process integrity failed")
    raw_rows = summary["rows"]
    keys = [(r.get("case"), r.get("market")) for r in raw_rows]
    if len(raw_rows) != 6 or len(set(keys)) != 6 or set(keys) != EXPECTED:
        raise ValueError("Expected exactly six unique declared development cells")
    rows = []
    for row in raw_rows:
        name, kind = row["case"], row["market"]
        state = 0 if kind == "source0" else 1
        cell = sealed / name / f"state{state}" / "cold_hull"
        receipt = read(cell / "receipt.json")
        result = read(cell / "result.json")
        assessment = result["assessment"]
        if ((result.get("case"), result.get("market")) != (name, kind)
                or receipt.get("returncode") != 0
                or receipt.get("hard_timeout") is not False
                or receipt.get("on_time") is not True
                or receipt.get("elapsed_seconds") != row.get("child_wall_s")
                or assessment.get("complete_evidence") is not True
                or assessment.get("status") != row.get("outcome")
                or row.get("complete_evidence") is not True
                or row.get("on_time") is not True):
            raise ValueError(f"Cell receipt/assessment mismatch: {name}/{kind}")
        lo, hi, gap = (Fraction(row[key]) for key in
                       ("lower_exact", "upper_exact", "gap_exact"))
        if lo > hi or hi - lo != gap:
            raise ValueError("Stored global enclosure arithmetic differs")
        assessed_lo, assessed_hi = map(Fraction, assessment["bounds"])
        if assessed_lo > lo or assessed_hi < hi:
            raise ValueError("Assessed enclosure does not contain stored endpoints")
        compact = {key: row.get(key) for key in FIELDS if key in row}
        compact.update(lower_floor4=directed(lo, 4),
                       upper_ceil4=directed(hi, 4, upper=True),
                       gap_ceil6=directed(gap, 6, upper=True),
                       lower_exact_sha256=sha(row["lower_exact"]),
                       upper_exact_sha256=sha(row["upper_exact"]),
                       gap_exact_sha256=sha(row["gap_exact"]))
        rows.append(compact)
    rows.sort(key=lambda r: (CASES.index(r["case"]), KINDS.index(r["market"])))
    return {"scope": "one seed-1006 synthetic development family; six cold-hull cells",
            "protocol": frozen["protocol"], "source_commit": frozen["source_commit"],
            "job_id": wrapper["job_id"], "wrapper_elapsed_s": wrapper["elapsed_whole_seconds"],
            "setup_s": wrapper["setup_seconds"],
            "supervisor_elapsed_s": supervisor["elapsed_seconds"],
            "native_tolerance_qualified": True, "exact_ideal_proof": False,
            "exact_fraction_policy": "endpoint text hashes refer to sealed summary.json",
            "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sealed", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    data = collect(args.sealed)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "compactrows.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    with (args.out / "compactrows.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in FIELDS} for row in data["rows"])


if __name__ == "__main__":
    main()
