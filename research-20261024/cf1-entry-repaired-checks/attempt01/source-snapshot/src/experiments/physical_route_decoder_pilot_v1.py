"""Four-cell TRAIN-only route-decoder pilot; no fitting or target-outcome reads."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

from egglab import learned_proposals as edge
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from egglab import physical_route_decoder_v1 as decoder
from experiments import computational_benchmark as base
from experiments import pool_physical_route_training as pool32
from experiments import pool_physical_route_training_v3 as pool64
from experiments import route_repair_pilot as existing_repair

ROOT = base.ROOT
OUTPUT = ROOT / "result/physical_learning/20260930-route-decoder-train-v1"
POOL32 = ROOT / "result/physical_learning/20260930-route-pool32-v1"
POOL64 = pool64.OUTPUTS[64]
MODEL32 = ROOT / "result/physical_learning/20260930-route-model32-v2"
MODEL64 = ROOT / "result/physical_learning/20260930-route-model64-v3"
SHARD04 = ROOT / "result/physical_learning/20260930-shard04-dataset-v1"
SOURCE_FILES = (
    "src/egglab/physical_route_decoder_v1.py",
    "src/experiments/physical_route_decoder_pilot_v1.py",
    "src/cluster/physical_route_decoder_pilot_v1.sbatch",
    "src/tests/test_physical_route_decoder_v1.py",
    "research-20260930/learning-campaign/ROUTE_DECODER_TRAIN_PILOT_V1_PROTOCOL.md",
    "src/egglab/route_fixed_repair.py",
    "src/egglab/learned_proposals.py",
    "src/egglab/physical_learning_cases.py",
    "src/egglab/physical_route_model_v2.py",
    "src/egglab/physical_route_model_v3.py",
    "src/experiments/pool_physical_route_training.py",
    "src/experiments/pool_physical_route_training_v3.py",
    "src/experiments/retrieval_comparison.py",
    "src/egglab/native_hull.py", "src/egglab/native_pathflow_hull.py",
    "src/egglab/native_pathflow.py", "src/egglab/native_recharge.py",
    "src/experiments/route_repair_pilot.py",
)


def _rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def _validate_pool(expected_sha):
    if base.sha(POOL64 / "pool_manifest.json") != expected_sha:
        raise ValueError("64-group pool manifest changed")
    manifest = json.loads((POOL64 / "pool_manifest.json").read_text())
    if (manifest.get("policy") != pool64.POLICY or manifest.get("base_ids") != list(range(10000, 10064))
            or [x["shard"] for x in manifest["admitted_shards"]] != list(range(8))):
        raise ValueError("Unknown 64-group exact TRAIN pool")
    for name in pool64.TABLES:
        if base.sha(POOL64 / name) != manifest["output_hashes"][name]:
            raise ValueError("64-group pool input table changed")
    return manifest


def case_inputs(group_id, expected_pool64_sha):
    manifest = _validate_pool(expected_pool64_sha)
    case_rows = [r for r in _rows(POOL64 / "cases.jsonl") if r.get("base_id") == group_id]
    if len(case_rows) != 1 or case_rows[0].get("split") != "train":
        raise ValueError("Missing declared TRAIN case")
    row = case_rows[0]
    case = edge.case_from_dict(row["case"])
    if (case.identity() != row.get("case_identity")
            or case.identity() != physical.make_case(group_id).identity()
            or row.get("physical_profile") != physical.assignment(group_id)):
        raise ValueError("TRAIN case generator/identity changed")
    source_rows = [r for r in _rows(POOL64 / "source_inputs.jsonl")
                   if r.get("base_group") == row["base_group"]]
    eligibility = manifest["group_eligibility"][group_id-10000]
    if (eligibility["base_group"] != row["base_group"]
            or eligibility["observed_source_count"] != len(source_rows)):
        raise ValueError("Group eligibility/source rows changed")
    return case, physical.market(case, decoder.TARGET_KIND), source_rows, eligibility


def score_payload(group_id, expected_pool32_sha, expected_pool64_sha):
    """Run under pinned sklearn 1.7.2 interpreter; emit scores, never a fit."""
    import joblib
    import numpy
    import scipy
    import sklearn
    if (sklearn.__version__, joblib.__version__, numpy.__version__, scipy.__version__) != (
            "1.7.2", "1.5.2", "1.26.4", "1.13.1"):
        raise ValueError("Decoder scoring requires pinned sklearn/joblib/NumPy/SciPy runtime")
    if base.sha(POOL32 / "pool_manifest.json") != expected_pool32_sha:
        raise ValueError("32-group pool manifest changed")
    manifest32 = json.loads((POOL32 / "pool_manifest.json").read_text())
    if (manifest32.get("policy") != pool32.POLICY
            or manifest32.get("base_ids") != list(range(10000, 10032))
            or any(base.sha(POOL32 / name) != manifest32.get("output_hashes", {}).get(name)
                   for name in ("cases.jsonl", "source_inputs.jsonl"))):
        raise ValueError("32-group source tables changed")
    case, market, _, eligibility = case_inputs(group_id, expected_pool64_sha)
    scored = {}
    identities = {}
    model_timing = {}
    for prefix, root, sha in ((32, MODEL32, expected_pool32_sha),
                              (64, MODEL64, expected_pool64_sha)):
        for name in decoder.MODEL_NAMES:
            load_started = time.monotonic()
            model = decoder.load_scorer(root, prefix=prefix, name=name,
                group_id=group_id, expected_pool_manifest_sha256=sha)
            load_seconds = time.monotonic()-load_started
            key = f"{prefix}_{name}"
            inference_started = time.monotonic()
            scored[key] = model.logits(case, market.a).tolist()
            model_timing[key] = {"artifact_load_seconds": load_seconds,
                "score_inference_seconds": time.monotonic()-inference_started}
            identities[key] = {"prefix_groups": prefix, "model": name,
                "fold": model.fold, "seed": model.seed,
                "result_sha256": model.result_sha256,
                "tree_sha256": model.tree_sha256,
                "fit_groups": model.fit_groups,
                "inner_groups": model.inner_groups,
                "outer_groups": model.outer_groups}
    return {"policy": decoder.POLICY, "group_id": group_id,
        "case_identity": case.identity(), "market_identity": market.identity(),
        "movement_ids": [m.id for m in case.movements],
        "group_eligibility": eligibility,
        "pool32_manifest_sha256": expected_pool32_sha,
        "pool64_manifest_sha256": expected_pool64_sha,
        "model_identities": identities, "logits": scored,
        "model_timing_seconds": model_timing,
        "runtime_versions": {"sklearn": sklearn.__version__,
            "joblib": joblib.__version__, "numpy": numpy.__version__,
            "scipy": scipy.__version__}}


def _source_acquisition(group_id):
    """Post-selection accounting only; never returned to scorer or candidate choice."""
    receipt = json.loads((SHARD04 / "dataset_receipt.json").read_text())
    path = SHARD04 / "source_outcomes.jsonl"
    if (receipt.get("output_hashes", {}).get(path.name) != base.sha(path)
            or receipt.get("status") != "complete"):
        raise ValueError("Source-acquisition outcome accounting hash changed")
    rows = [r for r in _rows(path) if r.get("base_id") == group_id]
    if len(rows) != 2 or {r.get("source") for r in rows} != {"source0", "source1"}:
        raise ValueError("Missing intended source acquisition cells")
    return {"intended_source_cells": 2,
        "paid_seconds_total": sum(float(r["paid_seconds"]) for r in rows),
        "by_source": {r["source"]: {"status": r["status"],
            "paid_seconds": r["paid_seconds"], "native_status": r.get("native_status")}
            for r in rows},
        "source_outcomes_sha256": base.sha(path),
        "dataset_receipt_sha256": base.sha(SHARD04 / "dataset_receipt.json")}


def summarize_arms(results):
    """Failed proposals have no global stage; controls are never proposal wins."""
    summary = {}
    for name, row in results.items():
        proposed = row.get("proposal") or {}
        global_check = row.get("global_verification") or {}
        summary[name] = {"kind": row["kind"],
            "proposal_status": proposed.get("status"),
            "topology_novel": proposed.get("topology_novel"),
            "candidate_cost_exact": proposed.get("objective_exact"),
            "candidate_vehicle_count": len(proposed["plan"]["vehicles"])
                if proposed.get("status") == "replayed" else None,
            "failure": proposed.get("failure"),
            "global_status": global_check.get("status"),
            "global_assessment": global_check.get("assessment"),
            "candidate_timing_seconds": proposed.get("timing_seconds"),
            "pool_import_wall_seconds": global_check.get("pool_import_wall_seconds"),
            "hull_wall_seconds": global_check.get("hull_wall_seconds"),
            "global_wall_seconds": global_check.get("wall_seconds")}
    return summary


def run(task_id, pool32_sha, pool64_sha, train_python, output=OUTPUT):
    if task_id not in range(len(decoder.GROUP_IDS)):
        raise ValueError("Only four declared TRAIN pilot tasks")
    if any(len(x) != 64 or any(c not in "0123456789abcdef" for c in x)
           for x in (pool32_sha, pool64_sha)):
        raise ValueError("Explicit pinned pool manifest SHA-256 values required")
    group_id = decoder.GROUP_IDS[task_id]
    dest = Path(output).resolve() / f"task{task_id:02d}"
    if dest.exists():
        raise ValueError("Decoder pilot task output is immutable; no retry")
    dest.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    base.save_new(dest / "launch.json", {"policy": decoder.POLICY,
        "task_id": task_id, "group_id": group_id, "target_kind": decoder.TARGET_KIND,
        "pool32_manifest_sha256": pool32_sha, "pool64_manifest_sha256": pool64_sha,
        "launched_unix": time.time()})
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        hashes = {name: base.sha(ROOT / name) for name in SOURCE_FILES}
        base.save_new(dest / "source_identity.json", {"source_commit": commit,
            "source_hashes": hashes})
        score_cmd = [str(train_python), "-m", "experiments.physical_route_decoder_pilot_v1",
            "score", "--group-id", str(group_id), "--pool32-sha", pool32_sha,
            "--pool64-sha", pool64_sha]
        score_started = time.monotonic()
        try:
            child = subprocess.run(score_cmd, cwd=ROOT, text=True,
                capture_output=True, timeout=120, check=False)
        except subprocess.TimeoutExpired as exc:
            base.save_new(dest / "score_child.json", {"status": "timeout",
                "timeout_seconds": 120, "wall_seconds": time.monotonic()-score_started,
                "stdout": exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout,
                "stderr": exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr})
            raise
        score_child_wall = time.monotonic()-score_started
        base.save_new(dest / "score_child.json", {"status": "completed",
            "returncode": child.returncode, "wall_seconds": score_child_wall,
            "stdout": child.stdout, "stderr": child.stderr})
        if child.returncode != 0:
            raise RuntimeError(f"Pinned score child exited {child.returncode}; see score_child.json")
        scores = json.loads(child.stdout)
        case, market, sources, eligibility = case_inputs(group_id, pool64_sha)
        if (scores.get("case_identity") != case.identity()
                or scores.get("market_identity") != market.identity()
                or scores.get("movement_ids") != [m.id for m in case.movements]
                or scores.get("group_eligibility") != eligibility):
            raise ValueError("Score child input identity differs from native runner")
        base.save_new(dest / "scores.json", scores)
        source_validation_started = time.monotonic()
        controls = decoder.admitted_source_controls(case, market, sources)
        source_validation_wall = time.monotonic()-source_validation_started
        source_topologies = [row["topology"] for row in controls["candidates"]]
        source_plans = [row["plan"] for row in controls["candidates"]]
        base.save_new(dest / "source_controls.json", controls)
        charge_budget = existing_repair.repair_budget()
        hull_budget = existing_repair.hull_budget()
        results = {}
        for name in (*scores["logits"], "cost_only"):
            logits = scores["logits"].get(name)
            proposed = decoder.decoded_candidate(case, market, logits, source_topologies,
                cover_policy="cost_only" if name == "cost_only" else "cost_learned",
                path_seconds=5.0, charge_budget=charge_budget)
            result = {"kind": "input_only_cost_cover" if name == "cost_only" else "learned_decoder",
                "proposal": proposed, "global_verification": None}
            if proposed["status"] == "replayed":
                result["global_verification"] = decoder.verify_global(case, market,
                    [proposed["plan"]], {"pilot": decoder.POLICY, "group_id": group_id,
                        "arm": name, "plan_hash": proposed["plan_hash"]}, hull_budget)
            results[name] = result
            base.save_new(dest / f"arm_{name}.json", result)
        for name, plans in (("cold", None), ("retained_sources", source_plans)):
            result = decoder.verify_global(case, market, plans,
                {"pilot": decoder.POLICY, "group_id": group_id,
                 "arm": name, "source_plan_hashes": [nr.digest(p) for p in source_plans]},
                hull_budget)
            results[name] = {"kind": "native_control", "global_verification": result}
            base.save_new(dest / f"arm_{name}.json", results[name])
        acquisition = _source_acquisition(group_id)
        base.save_new(dest / "source_acquisition.json", acquisition)
        summary = {"policy": decoder.POLICY, "task_id": task_id,
            "group_id": group_id, "case_identity": case.identity(),
            "market_identity": market.identity(), "target_kind": decoder.TARGET_KIND,
            "group_eligibility": eligibility,
            "source_controls": {key: controls[key] for key in (
                "first_source", "nearest_price", "cheapest_exact_bill",
                "intended_sources", "observed_sources")},
            "source_acquisition": acquisition,
            "scoring_child_wall_seconds": score_child_wall,
            "source_validation_wall_seconds": source_validation_wall,
            "model_timing_seconds": scores["model_timing_seconds"],
            "arms": summarize_arms(results),
            "source_hashes": hashes, "source_commit": commit,
            "pool32_manifest_sha256": pool32_sha, "pool64_manifest_sha256": pool64_sha,
            "elapsed_seconds": time.monotonic()-started,
            "scientific_admission": "pending independent result review"}
        base.save_new(dest / "result.json", summary)
        base.save_new(dest / "receipt.json", {"policy": decoder.POLICY,
            "task_id": task_id, "group_id": group_id, "status": "completed",
            "source_commit": commit, "source_hashes": hashes,
            "result_sha256": base.sha(dest / "result.json"),
            "score_sha256": base.sha(dest / "scores.json"),
            "score_child_sha256": base.sha(dest / "score_child.json"),
            "source_controls_sha256": base.sha(dest / "source_controls.json"),
            "wall_seconds": summary["elapsed_seconds"]})
        return {"group_id": group_id, "output": str(dest),
                "wall_seconds": summary["elapsed_seconds"]}
    except BaseException as exc:
        base.save_new(dest / "failure.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "wall_seconds": time.monotonic()-started})
        base.save_new(dest / "receipt.json", {"policy": decoder.POLICY,
            "task_id": task_id, "group_id": group_id, "status": "failed",
            "failure_sha256": base.sha(dest / "failure.json")})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    score = sub.add_parser("score")
    score.add_argument("--group-id", type=int, choices=decoder.GROUP_IDS, required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--task-id", type=int, choices=range(len(decoder.GROUP_IDS)), required=True)
    run_parser.add_argument("--train-python", type=Path, required=True)
    for command in (score, run_parser):
        command.add_argument("--pool32-sha", required=True)
        command.add_argument("--pool64-sha", required=True)
    args = parser.parse_args(argv)
    if args.command == "score":
        print(json.dumps(score_payload(args.group_id, args.pool32_sha, args.pool64_sha),
                         sort_keys=True, allow_nan=False))
    else:
        print(json.dumps(run(args.task_id, args.pool32_sha, args.pool64_sha,
                             args.train_python), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
