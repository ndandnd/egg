"""Re-evaluate sealed whole-fleet hull columns as native physical uppers.

Reads the frozen/summary receipts through the curator and eight small hull
raw_result files. Replays each saved physical plan; never invokes a solver.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE.parent))

from egglab import native_hull as nh  # noqa: E402
from egglab import native_pathflow_hull as compact  # noqa: E402
from egglab import native_recharge as nr  # noqa: E402
from experiments import public_economic_sensitivity as public  # noqa: E402
import summarize  # noqa: E402


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate(sealed):
    sealed = Path(sealed)
    curated = summarize.curate(sealed)
    if not curated["global_integrity_ok"] or not curated["manifest_ok"]:
        raise ValueError("Sealed source is not admitted")
    frozen = summarize.read(sealed / "frozen.json")
    stage = {(r["case"], r["stage"]): r for r in curated["stage_rows"]}
    rows = []
    for summary_row in curated["rows"]:
        name, kind = summary_row["case"], summary_row["market"]
        hull_stage = stage[name, "cold_hull"]
        planner_stage = stage[name, "planner"]
        if not (hull_stage["admitted"] and planner_stage["admitted"]):
            rows.append({"case": name, "market": kind, "status": "unavailable",
                         "reason": "planner_or_hull_stage_not_admitted"})
            continue
        case, market = public.cases()[name], public.market(name, kind)
        declared = frozen["design"]["cases"][name]
        if (declared["case_identity"] != case.identity()
                or declared["market_identities"][kind] != market.identity()):
            raise ValueError("Current replay case/market differs from frozen source")
        raw_path = sealed / name / "state0" / "cold_hull" / "raw_result.json"
        raw = summarize.read(raw_path)["result"]
        if (raw.get("physical_identity") != case.identity()
                or raw.get("market_identity") != market.identity()
                or raw.get("master_policy") != "numerical_qp_proposal"
                or raw.get("arm") != "cold" or raw.get("state_index") != 0
                or raw.get("state_identity") != compact.state_identity(
                    case, market, "cold", 0, public.budget("cold_hull"),
                    pricing_reserve_seconds=public.RESERVE_SECONDS,
                    master_policy="numerical_qp_proposal",
                    qp_denominator=public.QP_DENOMINATOR,
                    qp_maxiter=public.QP_MAXITER)):
            raise ValueError("Saved hull physical/pricing state differs")
        candidates = []
        for column in raw["columns"]:
            replay = nh.replay_column(case, column, compact.EXTRACTION_POLICY)
            true_cost = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
            # Add the declared native objective guard, even though true_cost is
            # recomputed exactly from the stored binary floating-point inputs.
            guarded = true_cost + Fraction(nr.BOUND_GUARD)
            candidates.append((guarded, {
                "column_key": column["key"],
                "witness_hash": column["witness_hash"],
                "source_pricing_call": column.get("source", {}).get("pricing_call"),
                "used_buses": len(column["plan"]["vehicles"]),
                "ops_cost_exact": str(Fraction(replay["ops_cost"])),
                "supply_cost_exact": str(nh.supply(market, replay["load"])),
                "true_cost_exact": str(true_cost),
                "guarded_upper_exact": str(guarded),
                "true_cost_approx": float(true_cost),
                "guarded_upper_approx": float(guarded)}))
        if not candidates:
            raise ValueError("Admitted hull unexpectedly has no physical columns")
        best_upper, best = min(candidates, key=lambda item: (item[0], item[1]["column_key"]))
        planner_lower, planner_upper = map(Fraction, summary_row["D_raw_exact"])
        hull_lower, _ = map(Fraction, summary_row["CH_raw_exact"])
        material_gain = planner_upper - best_upper
        if material_gain <= Fraction(nr.BOUND_GUARD):
            material_gain = Fraction(0)
        tightened_upper = best_upper if material_gain > 0 else planner_upper
        if tightened_upper < planner_lower or tightened_upper < hull_lower:
            raise ValueError("Replayed physical upper conflicts with native lower")
        combined = summarize.native_combination(
            [str(planner_lower), str(tightened_upper)], summary_row["CH_raw_exact"])
        if combined is None:
            raise ValueError("Post hoc physical/hull native intervals conflict")
        rows.append({"case": name, "market": kind, "status": "native_replayed",
                     "case_identity": case.identity(), "market_identity": market.identity(),
                     "hull_raw_sha256": file_sha(raw_path), "pool_size": len(candidates),
                     "best": best,
                     "planner_stage_upper_exact": str(planner_upper),
                     "posthoc_physical_upper_exact": str(tightened_upper),
                     "posthoc_native_gap_interval_exact": combined["gap_exact"],
                     "physical_upper_improvement_exact": str(material_gain),
                     "native_replay_gates": {
                         "sealed_manifest": True, "stage_on_time_complete": True,
                         "frozen_case_market_state": True,
                         "individual_plan_replayed": True,
                         "stored_projection_matches_replay": True,
                         "objective_recomputed_on_saved_binary_inputs": True,
                         "native_objective_guard_added": str(Fraction(nr.BOUND_GUARD))},
                     "ideal_exact_feasibility_reviewed": False})
    return {"scope": "post hoc same-case native physical upper from individual replayed hull columns",
            "source_commit": frozen["source_commit"],
            "manifest_sha256": file_sha(sealed / "MANIFEST.json"),
            "native_tolerance_qualified": True, "ideal_exact_proof": False,
            "mixture_used_as_physical_fleet": False,
            "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sealed", type=Path)
    parser.add_argument("out", type=Path, nargs="?", default=HERE / "pool_candidates.json")
    args = parser.parse_args()
    args.out.write_text(json.dumps(evaluate(args.sealed), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
