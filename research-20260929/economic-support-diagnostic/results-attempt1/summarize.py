"""Curate sealed scalar economic results without reading event logs or solving."""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
QP = ROOT / "research-20260929/qp-baseline-diagnostic/results-attempt1"
CASES = tuple(f"native_scale_dev_s1006_n{n:02d}" for n in (8, 16, 24))
KINDS = ("source0", "target")
CELLS = tuple((c, k) for c in CASES for k in KINDS)
STAGES = ("planner", "response")
FIELDS = ("case", "services", "market", "planner_outcome", "response_outcome",
          "D_lower_floor4", "D_upper_ceil4", "CH_lower_floor4", "CH_upper_ceil4",
          "gap_lower_floor6", "gap_upper_ceil6", "regret_lower_floor6",
          "regret_upper_ceil6", "planner_calls", "response_calls",
          "planner_child_s", "response_child_s", "planner_native_solver_s",
          "response_native_solver_s", "planner_solver_time_complete",
          "response_solver_time_complete", "planner_plan_hash",
          "D_lower_exact_sha256", "D_upper_exact_sha256",
          "CH_lower_exact_sha256", "CH_upper_exact_sha256",
          "gap_lower_exact_sha256", "gap_upper_exact_sha256",
          "regret_lower_exact_sha256", "regret_upper_exact_sha256")


def read(path):
    return json.loads(Path(path).read_text())


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def directed(value, digits, *, upper=False):
    number = Fraction(value)
    scale = 10 ** digits
    units = (-((-number.numerator * scale) // number.denominator)
             if upper else (number.numerator * scale) // number.denominator)
    sign = "-" if units < 0 else ""
    absolute = abs(units)
    return f"{sign}{absolute // scale}.{absolute % scale:0{digits}d}"


def bounds(raw, label):
    if not isinstance(raw, list) or len(raw) != 2:
        raise ValueError(f"Missing {label} interval")
    lo, hi = map(Fraction, raw)
    if lo > hi:
        raise ValueError(f"Reversed {label} interval")
    return lo, hi


def stage_key(row):
    return row.get("case"), row.get("market"), row.get("stage")


def collect(sealed):
    sealed = Path(sealed)
    summary, frozen = read(sealed / "summary.json"), read(sealed / "frozen.json")
    supervisor = read(sealed / "supervisor_receipt.json")
    wrapper = read(sealed.with_name(sealed.name + ".slurm_wrapper_receipt.json"))
    if (summary.get("protocol") != frozen.get("protocol")
            or supervisor.get("protocol") != frozen.get("protocol")
            or summary.get("declared_cells") != 6 or summary.get("accounted_cells") != 6
            or summary.get("declared_stages") != 12 or summary.get("accounted_stages") != 12
            or summary.get("all_declared_stages_accounted") is not True
            or supervisor.get("returncode") != 0 or supervisor.get("stable_seal") is not True
            or supervisor.get("process_group_quiescent") is not True
            or supervisor.get("source_hashes_unchanged") is not True
            or any(wrapper.get(k) != 0 for k in
                   ("returncode", "freeze_returncode", "preflight_returncode",
                    "supervise_returncode"))):
        raise ValueError("Economic attempt top-level accounting/integrity failed")
    qp_receipt, qp_frozen, qp_summary = (read(QP / name) for name in
                                         ("COLLECTION_RECEIPT.json", "frozen_identity.json",
                                          "summary.json"))
    for name in ("frozen_identity.json", "summary.json"):
        if qp_receipt["curated_file_sha256"].get(name) != file_sha(QP / name):
            raise ValueError("Pinned QP source hash differs")
    if (qp_receipt.get("source_commit") != qp_frozen.get("source_commit")
            or qp_receipt.get("job_id") != "595105"):
        raise ValueError("QP source lineage differs")
    declared = frozen["design"]
    if (len(declared.get("order", [])) != 6 or set(declared.get("cases", {})) != set(CASES)
            or len(declared.get("hull_source", {})) != 6):
        raise ValueError("Economic design omitted case/source")
    for case in CASES:
        a, b = declared["cases"][case], qp_frozen["design"]["cases"][case]
        if (a["case_identity"] != b["case_identity"]
                or a["market_identities"] != b["market_identities"]):
            raise ValueError("Physical/market identity differs from QP source")
    qp_rows = {(r["case"], r["market"]): r for r in qp_summary["rows"]}
    if len(qp_rows) != 6 or set(qp_rows) != set(CELLS):
        raise ValueError("QP source lacks six cells")
    rows = summary["rows"]
    by_stage = {stage_key(row): row for row in rows}
    if len(rows) != 12 or len(by_stage) != 12 or set(by_stage) != {
            (c, k, s) for c, k in CELLS for s in STAGES}:
        raise ValueError("Economic attempt lacks twelve unique stages")
    expected_order = [(d["case"], d["market"], stage)
                      for d in declared["order"] for stage in STAGES]
    if [stage_key(row) for row in rows] != expected_order:
        raise ValueError("Economic stage order differs")
    comparisons = {(r["case"], r["market"]): r for r in summary["comparisons"]}
    if len(comparisons) != 6 or set(comparisons) != set(CELLS):
        raise ValueError("Six paired comparisons missing")
    compact_stages = []
    compact_rows = []
    for case, market in CELLS:
        pair = {}
        for stage in STAGES:
            row = by_stage[case, market, stage]
            receipt = read(sealed / case / f"state{KINDS.index(market)}" / stage / "receipt.json")
            saved = read(sealed / case / f"state{KINDS.index(market)}" / stage / "result.json")
            assessment = saved["assessment"]
            if ((saved.get("case"), saved.get("market"), saved.get("stage")) !=
                    (case, market, stage)
                    or receipt.get("returncode") != 0 or receipt.get("hard_timeout") is not False
                    or receipt.get("on_time") is not True
                    or receipt.get("elapsed_seconds") != row.get("child_wall_s")
                    or row.get("on_time") is not True or row.get("complete_evidence") is not True
                    or row.get("outcome") != "certified"
                    or assessment.get("status") != row.get("outcome")
                    or assessment.get("bounds") != [row.get("lower_exact"), row.get("upper_exact")]
                    or assessment.get("plan_hash") != row.get("plan_hash")):
                raise ValueError(f"Stage receipt/assessment mismatch: {case}/{market}/{stage}")
            bounds(assessment["bounds"], stage)
            pair[stage] = row
            compact_stages.append({k: row.get(k) for k in
                                   ("case", "market", "stage", "outcome", "native_status",
                                    "complete_evidence", "on_time", "child_wall_s", "native_calls",
                                    "native_solver_wall_recorded_s", "native_solver_wall_complete",
                                    "model_construction_s", "plan_hash", "planner_plan_hash")})
        p, r, joint = pair["planner"], pair["response"], comparisons[case, market]
        source = declared["hull_source"][f"{case}/{market}"]
        qps = qp_rows[case, market]
        if (source["source_job_id"] != "595105"
                or source["source_commit"] != qp_receipt["source_commit"]
                or source["case_identity"] != declared["cases"][case]["case_identity"]
                or source["market_identity"] != declared["cases"][case]["market_identities"][market]
                or source["lower_exact"] != qps["lower_exact"]
                or source["upper_exact"] != qps["upper_exact"]
                or qps.get("complete_evidence") is not True or qps.get("on_time") is not True
                or qps.get("outcome") != "certified"):
            raise ValueError("Imported CH source mismatch")
        d_lo, d_hi = bounds(joint["D_interval_exact"], "D")
        ch_lo, ch_hi = bounds(joint["CH_interval_exact"], "CH")
        gap_lo, gap_hi = bounds(joint["D_minus_CH_interval_exact"], "gap")
        reg_lo, reg_hi = bounds(joint["incumbent_own_price_regret_interval_exact"], "regret")
        if (joint["D_interval_exact"] != [p["lower_exact"], p["upper_exact"]]
                or joint["CH_interval_exact"] != [source["lower_exact"], source["upper_exact"]]
                or joint["incumbent_plan_hash"] != p["plan_hash"]
                or r["planner_plan_hash"] != p["plan_hash"]
                or joint["incumbent_own_price_regret_interval_exact"] !=
                   [r["regret_lower_exact"], r["regret_upper_exact"]]
                or joint["combined_D_interval_exact"] !=
                   [str(max(d_lo, ch_lo)), str(d_hi)]
                or joint["combined_CH_interval_exact"] !=
                   [str(ch_lo), str(min(ch_hi, d_hi))]
                or (gap_lo, gap_hi) !=
                   (max(Fraction(0), max(d_lo, ch_lo)-min(ch_hi, d_hi)), d_hi-ch_lo)
                or d_hi < ch_lo or reg_lo < 0):
            raise ValueError("Paired interval or named-incumbent arithmetic differs")
        response_assessment = read(sealed / case / f"state{KINDS.index(market)}" /
                                   "response" / "result.json")["assessment"]
        bill = Fraction(r["own_price_bill_exact"])
        v_lo, v_hi = map(Fraction, response_assessment["bounds"])
        if (response_assessment.get("planner_own_price_bill_exact") != r["own_price_bill_exact"]
                or response_assessment.get("own_price_regret_interval_exact") !=
                   [r["regret_lower_exact"], r["regret_upper_exact"]]
                or (reg_lo, reg_hi) !=
                   (max(Fraction(0), bill - v_hi), bill - v_lo)):
            raise ValueError("Named-incumbent response arithmetic differs")
        row = {"case": case, "services": int(case[-2:]), "market": market,
               "planner_outcome": p["outcome"], "response_outcome": r["outcome"],
               "D_lower_floor4": directed(d_lo, 4),
               "D_upper_ceil4": directed(d_hi, 4, upper=True),
               "CH_lower_floor4": directed(ch_lo, 4),
               "CH_upper_ceil4": directed(ch_hi, 4, upper=True),
               "gap_lower_floor6": directed(gap_lo, 6),
               "gap_upper_ceil6": directed(gap_hi, 6, upper=True),
               "regret_lower_floor6": directed(reg_lo, 6),
               "regret_upper_ceil6": directed(reg_hi, 6, upper=True),
               "planner_calls": p["native_calls"], "response_calls": r["native_calls"],
               "planner_child_s": p["child_wall_s"], "response_child_s": r["child_wall_s"],
               "planner_native_solver_s": p["native_solver_wall_recorded_s"],
               "response_native_solver_s": r["native_solver_wall_recorded_s"],
               "planner_solver_time_complete": p["native_solver_wall_complete"],
               "response_solver_time_complete": r["native_solver_wall_complete"],
               "planner_plan_hash": p["plan_hash"]}
        for prefix, values in (("D", joint["D_interval_exact"]),
                               ("CH", joint["CH_interval_exact"]),
                               ("gap", joint["D_minus_CH_interval_exact"]),
                               ("regret", joint["incumbent_own_price_regret_interval_exact"])):
            row[f"{prefix}_lower_exact_sha256"] = sha(values[0])
            row[f"{prefix}_upper_exact_sha256"] = sha(values[1])
        compact_rows.append(row)
    return {"scope": "six matched seed-1006 development cells; native tolerance-qualified",
            "protocol": frozen["protocol"], "source_commit": frozen["source_commit"],
            "job_id": str(wrapper["job_id"]), "qp_hull_source_job_id": "595105",
            "qp_hull_source_commit": qp_receipt["source_commit"],
            "qp_hull_job_elapsed_s": 107,
            "wrapper_elapsed_s": wrapper["elapsed_whole_seconds"],
            "setup_s": wrapper["setup_seconds"],
            "supervisor_elapsed_s": supervisor["elapsed_seconds"],
            "declared_stages": 12, "accounted_stages": len(compact_stages),
            "matched_physical_market_identities": True,
            "native_tolerance_qualified": True, "exact_ideal_proof": False,
            "fraction_policy": "endpoint hashes refer to sealed summary.json text",
            "stage_rows": compact_stages, "rows": compact_rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sealed", type=Path)
    parser.add_argument("out", type=Path, nargs="?", default=HERE)
    args = parser.parse_args()
    data = collect(args.sealed)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "compactrows.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    with (args.out / "compactrows.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({k: row.get(k) for k in FIELDS} for row in data["rows"])


if __name__ == "__main__":
    main()
