"""Read-only replay of fleets and separate CH-mixture support in decoder tasks.

No optimizer, model fit, target outcome, development case, or sealed test read.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
import json
from pathlib import Path

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_route_decoder_v1 as decoder
from experiments import computational_benchmark as base
from experiments import physical_route_decoder_pilot_v1 as pilot
from experiments import retrieval_comparison as retrieval

ROOT = pilot.OUTPUT
OUTPUT = base.ROOT / "research-20260930/learning-campaign/ROUTE_DECODER_TRAIN_PILOT_V2_REPLAY.json"
ARMS = ("32_logistic", "32_hist_boosted", "64_logistic", "64_hist_boosted",
        "cost_only", "cold", "retained_sources")
LEARNED = ARMS[:4]


def read(path):
    return json.loads(Path(path).read_text())


def exact_bill(market, replay):
    return Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])


def verified_group(task_id):
    group_id = decoder.GROUP_IDS[task_id]
    folder = ROOT / f"task{task_id:02d}"
    launch, receipt, result = (read(folder / name) for name in
                               ("launch.json", "receipt.json", "result.json"))
    score, child, controls, acquisition = (read(folder / name) for name in
        ("scores.json", "score_child.json", "source_controls.json", "source_acquisition.json"))
    identity = read(folder / "source_identity.json")
    wrappers = list(ROOT.glob(f"task{task_id:02d}.slurm_wrapper_receipt.*.json"))
    if len(wrappers) != 1:
        raise ValueError("Missing or duplicate wrapper receipt")
    wrapper = read(wrappers[0])
    if (receipt.get("status") != "completed" or wrapper.get("returncode") != 0
            or wrapper.get("timeout_exit") is not False
            or launch.get("group_id") != group_id or result.get("group_id") != group_id
            or receipt.get("group_id") != group_id or wrapper.get("group_id") != group_id
            or receipt.get("result_sha256") != base.sha(folder / "result.json")
            or receipt.get("score_sha256") != base.sha(folder / "scores.json")
            or receipt.get("score_child_sha256") != base.sha(folder / "score_child.json")
            or receipt.get("source_controls_sha256") != base.sha(folder / "source_controls.json")
            or identity.get("source_commit") != receipt.get("source_commit")
            or identity.get("source_hashes") != receipt.get("source_hashes")
            or result.get("source_hashes") != identity.get("source_hashes")
            or child.get("returncode") != 0
            or score.get("group_id") != group_id
            or score.get("policy") != decoder.POLICY):
        raise ValueError(f"Task {task_id} receipt/identity mismatch")
    for name in pilot.SOURCE_FILES:
        if identity["source_hashes"][name] != base.sha(base.ROOT / name):
            raise ValueError(f"Execution source changed: {name}")
    sha32 = base.sha(pilot.POOL32 / "pool_manifest.json")
    sha64 = base.sha(pilot.POOL64 / "pool_manifest.json")
    if any(obj.get("pool32_manifest_sha256") != sha32 or
           obj.get("pool64_manifest_sha256") != sha64 for obj in
           (launch, result, score, wrapper)):
        raise ValueError("Pooled input manifest lineage changed")
    case, market, source_rows, eligibility = pilot.case_inputs(group_id, sha64)
    if (score["case_identity"] != case.identity()
            or score["market_identity"] != market.identity()
            or score["movement_ids"] != [m.id for m in case.movements]
            or result["group_eligibility"] != eligibility):
        raise ValueError("Case, market, or censor identity changed")
    rebuilt_controls = decoder.admitted_source_controls(case, market, source_rows)
    if rebuilt_controls != controls:
        raise ValueError("Saved source control disagrees with physical replay")
    if acquisition != pilot._source_acquisition(group_id):
        raise ValueError("Source-acquisition accounting changed")
    if result["source_acquisition"] != acquisition:
        raise ValueError("Result source-acquisition accounting changed")
    if score["runtime_versions"] != {"sklearn": "1.7.2", "joblib": "1.5.2",
                                     "numpy": "1.26.4", "scipy": "1.13.1"}:
        raise ValueError("Scoring runtime drift")
    for name, item in score["model_identities"].items():
        if (item["fold"] != (group_id-10000) % 4 or item["seed"] != 17
                or name not in LEARNED):
            raise ValueError("Unknown model/fold/seed")
        target_group = f"physical_v2_s{group_id}"
        if item["prefix_groups"] == 64:
            if (target_group not in item["outer_groups"]
                    or target_group in item["fit_groups"]
                    or target_group in item["inner_groups"]):
                raise ValueError("64-group target was not outer-held-out")
        elif item["prefix_groups"] == 32:
            if any(target_group in item[k] for k in
                   ("fit_groups", "inner_groups", "outer_groups")):
                raise ValueError("32-group bank saw out-of-bank target")
        else:
            raise ValueError("Unknown fit-bank size")
    source_bills = {row["source"]: Fraction(row["direct_bill_exact"])
                    for row in controls["candidates"]}
    cheapest = min(source_bills.values())
    if controls["cheapest_exact_bill"] != min(source_bills,
            key=lambda s: (source_bills[s], s)):
        raise ValueError("Cheapest exact source selection changed")
    source_topologies = [set(row["topology"]) for row in controls["candidates"]]
    arms = {}
    for name in ARMS:
        artifact = read(folder / f"arm_{name}.json")
        summary = result["arms"][name]
        global_check = artifact.get("global_verification")
        proposed = artifact.get("proposal")
        if name in ("cold", "retained_sources"):
            if artifact["kind"] != "native_control" or proposed is not None:
                raise ValueError("Native control credited as learned proposal")
        else:
            if (artifact["kind"] != ("input_only_cost_cover" if name == "cost_only"
                                    else "learned_decoder")
                    or proposed["status"] != summary["proposal_status"]):
                raise ValueError("Decoder arm kind/status differs")
        candidate_cost = None
        novelty = None
        if proposed is not None and proposed["status"] == "replayed":
            plan = proposed["plan"]
            replay = nr.replay_native(case, plan)
            pf._checked_pricing_start(case, plan)
            if (replay != proposed["replay"] or nr.digest(plan) != proposed["plan_hash"]
                    or {mid for v in plan["vehicles"] for mid in v["movements"]}
                    != set(proposed["cover"]["selected_movements"])):
                raise ValueError("Saved complete fleet fails independent replay/cover")
            candidate_cost = exact_bill(market, replay)
            if str(candidate_cost) != proposed["objective_exact"]:
                raise ValueError("Saved candidate target bill differs from replay")
            topology = {mid for v in plan["vehicles"] for mid in v["movements"]}
            novelty = all(topology != saved for saved in source_topologies)
            if novelty is not proposed["topology_novel"]:
                raise ValueError("Source-topology novelty changed")
            if global_check is None:
                raise ValueError("Replayed proposal lacks separate global check")
        elif proposed is not None:
            if (proposed["status"] != "failed" or "plan" in proposed
                    or proposed.get("objective_exact") is not None
                    or global_check is not None or not proposed.get("failure")):
                raise ValueError("Failed proposal acquired plan or global credit")
        bounds = None
        hull_physical = None
        if global_check is not None:
            if global_check["status"] != "checked":
                raise ValueError("Unreviewed/failed global hull in completed arm")
            reassessed = retrieval.assess_hull(case, market, global_check["raw_hull"])
            if reassessed != global_check["assessment"]:
                raise ValueError("Global hull assessment changed on read-only replay")
            bounds = reassessed["bounds"]
            if (bounds is not None and all(x is not None for x in bounds)
                    and Fraction(bounds[0]) > Fraction(bounds[1])):
                raise ValueError("Global lower bound exceeds upper bound")
            raw = global_check["raw_hull"]
            physical_columns = []
            for column in raw["columns"]:
                column_replay = nh.replay_column(case, column, column["extraction_policy"])
                physical_columns.append({"column_key": column["key"],
                    "plan_hash": nr.digest(column["plan"]),
                    "bill_exact": str(exact_bill(market, column_replay))})
            if not physical_columns:
                raise ValueError("Checked hull has no replayed physical column")
            best_column = min(physical_columns,
                key=lambda c: (Fraction(c["bill_exact"]), c["column_key"]))
            mixture = raw["mixture"]
            weights = [Fraction(x) for x in mixture["simplex"]["weights_exact"]]
            if (len(weights) != len(mixture["column_keys"])
                    or sum(weights) != 1
                    or not set(mixture["column_keys"]).issubset(
                        {c["column_key"] for c in physical_columns})):
                raise ValueError("CH mixture support differs from replayed columns")
            support_count = sum(w > 0 for w in weights)
            if support_count != mixture["simplex"]["positive_weights"]:
                raise ValueError("CH mixture support count changed")
            mix_exact = Fraction(mixture["objective_exact"])
            pure = support_count == 1
            if pure:
                sole_key = mixture["column_keys"][next(i for i,w in enumerate(weights) if w > 0)]
                sole = next(c for c in physical_columns if c["column_key"] == sole_key)
                if mix_exact != Fraction(sole["bill_exact"]):
                    raise ValueError("Purported pure CH solution differs from whole fleet")
            hull_physical = {"replayed_column_count": len(physical_columns),
                "best_single_fleet_cost_exact": best_column["bill_exact"],
                "best_single_fleet_column_key": best_column["column_key"],
                "best_single_fleet_plan_hash": best_column["plan_hash"],
                "mixture_cost_exact": str(mix_exact),
                "mixture_support_count": support_count,
                "mixture_is_single_fleet": pure,
                "single_fleet_minus_mixture_exact": str(
                    Fraction(best_column["bill_exact"])-mix_exact),
                "positive_curvature": any(Fraction(b) > 0 for b in market.b)}
        if (summary["candidate_cost_exact"] != (str(candidate_cost) if candidate_cost else None)
                or summary["topology_novel"] != novelty
                or summary["global_status"] != (global_check or {}).get("status")
                or summary["global_assessment"] != (global_check or {}).get("assessment")):
            raise ValueError("Compact result differs from full arm artifact")
        arms[name] = {"kind": artifact["kind"],
            "proposal_status": proposed["status"] if proposed else None,
            "failure": proposed.get("failure") if proposed else None,
            "cover_status": proposed.get("cover", {}).get("status") if proposed else None,
            "topology_novel": novelty,
            "candidate_cost_exact": str(candidate_cost) if candidate_cost else None,
            "delta_to_cheapest_source_exact": str(candidate_cost-cheapest) if candidate_cost else None,
            "candidate_vehicle_count": len(proposed["plan"]["vehicles"])
                if candidate_cost else None,
            "candidate_plan_hash": proposed.get("plan_hash") if proposed else None,
            "global_status": global_check["status"] if global_check else None,
            "hull_status": global_check["assessment"]["status"] if global_check else None,
            "global_bounds_exact": bounds,
            "hull_physical_vs_mixture": hull_physical,
            "global_certificate_replayed": (
                global_check["assessment"]["global_certificate_replayed"] if global_check else None),
            "timing_seconds": {"candidate": proposed.get("timing_seconds") if proposed else None,
                "pool_import": global_check.get("pool_import_wall_seconds") if global_check else None,
                "hull": global_check.get("hull_wall_seconds") if global_check else None,
                "global_total": global_check.get("wall_seconds") if global_check else None}}
    return {"group_id": group_id, "task_id": task_id,
        "result_sha256": base.sha(folder / "result.json"),
        "receipt_sha256": base.sha(folder / "receipt.json"),
        "wrapper_sha256": base.sha(wrappers[0]),
        "source_controls_sha256": base.sha(folder / "source_controls.json"),
        "score_sha256": base.sha(folder / "scores.json"),
        "case_identity": case.identity(), "market_identity": market.identity(),
        "intended_sources": eligibility["intended_source_count"],
        "observed_sources": eligibility["observed_source_count"],
        "missing_source_labels": eligibility["missing_source_labels"],
        "source_bills_exact": {k: str(v) for k, v in source_bills.items()},
        "source_control_choice": {k: controls[k] for k in
            ("first_source", "nearest_price", "cheapest_exact_bill")},
        "source_acquisition": acquisition,
        "scoring_child_wall_seconds": result["scoring_child_wall_seconds"],
        "source_validation_wall_seconds": result["source_validation_wall_seconds"],
        "model_timing_seconds": result["model_timing_seconds"],
        "task_elapsed_seconds": result["elapsed_seconds"],
        "wrapper_elapsed_seconds": wrapper["elapsed_seconds"],
        "allocated_job_cpus": wrapper.get("allocated_job_cpus"),
        "arms": arms}


def build():
    groups = [verified_group(i) for i in range(4)]
    learned = [row for g in groups for name, row in g["arms"].items() if name in LEARNED]
    counts = Counter((row["proposal_status"], row["topology_novel"]) for row in learned)
    return {"policy": decoder.POLICY, "scope": "four TRAIN groups only; no fit/optimization",
        "pool32_manifest_sha256": base.sha(pilot.POOL32 / "pool_manifest.json"),
        "pool64_manifest_sha256": base.sha(pilot.POOL64 / "pool_manifest.json"),
        "groups": groups,
        "learned_arm_counts": {f"{status}/{novelty}": count for (status, novelty), count in counts.items()},
        "independent_groups": len(groups), "learned_arms": len(learned),
        "verification_source_sha256": base.sha(Path(__file__))}


def main():
    output = build()
    base.save_new(OUTPUT, output)
    print(json.dumps({"output": str(OUTPUT),
        "independent_groups": output["independent_groups"],
        "learned_arm_counts": output["learned_arm_counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
