"""Read-only v7 artifact/plan replay. No optimizer, scoring, fitting or retry call."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import statistics
import time

from egglab import learned_proposals as edge
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "research-20260930/learning-campaign"
RAW = ROOT / "result/physical_learning/20260930-route-proposal-train-v7"
ARMS = ("tabular_v3", "families_v5", "graph_v6", "cost_only")
POLICY = "physical-route-proposals-heldout-train-v7"
METADATA_FILES = {"receipt.json", "launch.json", "source_identity.json", "comparison.json", "source_policy.json"}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1024*1024), b""): h.update(part)
    return h.hexdigest()


def require(condition, label):
    if not condition: raise ValueError(label)


def save(path, row):
    with Path(path).open("x") as stream:
        json.dump(row, stream, indent=2, sort_keys=True, allow_nan=False); stream.write("\n")


def safe(relative):
    path = (ROOT / relative).resolve()
    require(path.is_relative_to(ROOT), "Path escape")
    return path


def verify_hashes(rows):
    require(bool(rows), "Empty file hash set")
    for path, expected in rows.items(): require(sha(safe(path)) == expected, "Changed pinned artifact: "+path)


def partition(group_id, metadata):
    fold = (group_id-10000)%4
    outer = [f"physical_v2_s{i}" for i in range(10000, 10128) if (i-10000)%4 == fold]
    training = [f"physical_v2_s{i}" for i in range(10000, 10128) if f"physical_v2_s{i}" not in outer]
    inner = training[2::6]; fit = [g for g in training if g not in inner]
    for name, expected in (("fit_groups", fit), ("inner_groups", inner), ("outer_groups", outer)):
        require(metadata[name] == expected, "Fit/inner/outer partition differs")
    require(f"physical_v2_s{group_id}" in outer, "Target is not outer-held-out")


def independently_replay(case, market, plan, *, selected, expected_replay=None, expected_bill=None, expected_plan_hash=None, source_topologies=()):
    # These APIs validate paths, every charge and continuous-time shared resources;
    # they do not optimize, import an estimator, or solve a new plan.
    replay = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    actual = sorted({mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]})
    require(actual == sorted(selected), "Selected movement set changed")
    require(replay.get("replay_ok") is True, "Physical replay not admitted")
    if expected_replay is not None: require(replay == expected_replay, "Saved physical replay differs")
    bill = Fraction(replay["ops_cost"])+nh.supply(market, replay["load"])
    if expected_bill is not None: require(bill == Fraction(expected_bill), "Exact curved bill differs")
    plan_hash = nr.digest(plan)
    if expected_plan_hash is not None: require(plan_hash == expected_plan_hash, "Saved plan hash differs")
    return {"objective_exact": str(bill), "objective": float(bill), "vehicle_count": len(plan["vehicles"]),
        "plan_hash": plan_hash, "selected_movements": actual, "topology_novel":
            all(actual != sorted(s) for s in source_topologies) if source_topologies else None,
        "physical_replay_and_pricing_start_passed": True, "exact_saved_bill_reproduced": expected_bill is not None}


def sign_pair(bill, source):
    delta = Fraction(bill)-Fraction(source)
    return {"delta_exact": str(delta), "delta": float(delta), "relative_delta_percent": float(100*delta/Fraction(source)),
            "relation": "lower" if delta < 0 else "higher" if delta > 0 else "exact_tie"}


def stats(values):
    return {"n": len(values), "sum": sum(values), "mean": statistics.mean(values) if values else None,
        "median": statistics.median(values) if values else None, "min": min(values) if values else None,
        "max": max(values) if values else None}


def replay(output, report):
    started = time.monotonic(); launch = read(DOC / "LAUNCH_728823.json")
    manifest_path = DOC / launch["input_manifest"]; manifest = read(manifest_path)
    require(sha(manifest_path) == launch["input_manifest_sha256"], "Launch/manifest binding differs")
    require(manifest["policy"] == POLICY and manifest["group_ids"] == list(range(10064,10080)), "Wrong v7 cohort")
    verify_hashes(manifest["source_hashes"])
    raw_manifest_path = DOC/"RESULT_MANIFEST_ROUTE_PROPOSAL_V7.json"
    raw_manifest = read(raw_manifest_path)
    require(raw_manifest["array_job_id"] == 728823 and raw_manifest["all_archive_members_byte_verified"] is True, "Raw archive receipt is not verified")
    actual_raw = {str(p.relative_to(ROOT)) for p in RAW.rglob("*") if p.is_file()}
    require(actual_raw == set(raw_manifest["files"]), "Raw collection file set differs from preserved manifest")
    for relative, evidence in raw_manifest["files"].items():
        path = safe(relative)
        require(sha(path) == evidence["sha256"] and path.stat().st_size == evidence["bytes"], "Raw file differs from preserved byte manifest")
    accounting_path = DOC/"ACCOUNTING_728823.json"; allocation = read(accounting_path)
    parents = [r for r in allocation["rows"] if r["job_name"] == "egg-route-proposal-v7"]
    require(allocation["array_job_id"] == 728823 and len(parents) == 16, "Wrong Slurm accounting cohort")
    require({r["job_id"] for r in parents} == {f"728823_{i}" for i in range(16)}, "Slurm parent identities differ")
    require(all(r["user"] == "nc437" and r["node"] == "unicorn-cpu-75" and r["state"] == "COMPLETED" and r["exit_code"] == "0:0" for r in parents), "Slurm scientific task identity differs")
    parent_cpu = sum(int(r["elapsed_seconds"])*int(r["allocated_cpus"]) for r in parents)
    parent_elapsed = sum(int(r["elapsed_seconds"]) for r in parents)
    require(parent_cpu == allocation["allocated_cpu_seconds"] and parent_elapsed == allocation["total_parent_elapsed_seconds"], "Slurm paid totals differ")
    for arm, entries in manifest["models"].items():
        require(set(entries) == {"0","3","6","9"}, "Wrong seed17 task set")
        for entry in entries.values(): verify_hashes(entry["files"])
    for evidence in manifest["replay_attestations"].values():
        require(sha(safe(evidence["path"])) == evidence["sha256"], "Replay attestation changed")
    pool = safe(manifest["pool_path"]); pooled = read(pool / "pool_manifest.json")
    require(sha(pool / "pool_manifest.json") == manifest["pool_manifest_sha256"], "Pool manifest changed")
    for name in ("cases.jsonl", "source_inputs.jsonl"):
        require(sha(pool/name) == pooled["output_hashes"][name], "Pool table changed")
    cases = {r["base_id"]: r for r in (json.loads(s) for s in (pool/"cases.jsonl").read_text().splitlines())}
    source_inputs = [json.loads(s) for s in (pool/"source_inputs.jsonl").read_text().splitlines()]
    wrappers = {}
    for path in RAW.glob("*.wrapper_receipt.*.json"):
        row = read(path); task = int(row["task_id"])
        require(task not in wrappers and int(row["array_job_id"]) == 728823 and row["returncode"] == 0,
                "Wrapper array/task identity or duplicate attempt")
        wrappers[task] = (path, row)
    require(set(wrappers) == set(range(16)), "Missing wrapper receipt")
    require({p.name for p in RAW.glob("task[0-9][0-9]")} == {f"task{i:02d}" for i in range(16)}, "Wrong task collection")
    tasks = []; stage_status = Counter(); scientific_status = Counter(); failures = []; skips = []; time_by_stage = defaultdict(list)
    task_wall = []; wrapper_wall = []; plan_count = 0; code_hashes = {}; scorer_counts = Counter(); source_acquisition = []
    for task in range(16):
        group = 10064+task; folder = RAW/f"task{task:02d}"
        receipt, comparison, task_launch, identity = (read(folder/name) for name in ("receipt.json","comparison.json","launch.json","source_identity.json"))
        require(receipt["task_id"] == comparison["task_id"] == task_launch["task_id"] == task, "Task identity differs")
        require(receipt["group_id"] == comparison["group_id"] == task_launch["group_id"] == group, "Group identity differs")
        require(receipt["status"] == "completed_with_preserved_stage_failures", "Missing completed scientific supervisor receipt")
        require(receipt["comparison_sha256"] == sha(folder/"comparison.json"), "Comparison hash differs")
        require(task_launch["manifest_sha256"] == identity["manifest_sha256"] == receipt["manifest_sha256"] == sha(manifest_path), "Task manifest differs")
        require(identity["source_commit"] == launch["source_commit"] and identity["source_hashes"] == manifest["source_hashes"], "Task source lineage differs")
        require(read(folder/"source_policy.json") == comparison["source_policy"], "Saved source policy differs")
        code_hashes[f"task{task:02d}"] = {name: sha(folder/name) for name in METADATA_FILES}
        task_wall.append(receipt["wall_seconds"]); wrapper_wall.append(wrappers[task][1]["elapsed_seconds"])
        stages = receipt["stage_receipts"]; require(len(stages) == 35, "Missing declared stage receipt")
        verified_stage = {}
        for key, row in stages.items():
            require(read(folder/f"{key}.receipt.json") == row, "Aggregate/individual receipt differs")
            stage_status[row["status"]] += 1
            scientific_status[str(row.get("scientific_status"))] += 1
            time_by_stage[key].append(row["wall_seconds"])
            if row["status"] == "skipped":
                require(row["attempted"] is False and row["wall_seconds"] == 0., "Skipped stage received time/attempt credit")
                skips.append({"group_id":group,"stage":key,"reason":row["reason"]}); continue
            require(row["attempted"] is True, "Native stage attempt missing")
            start = read(folder/f"{key}.start.json")
            require(start["stage_key"] == key and start["cap_seconds"] == row["cap_seconds"], "Stage start/cap differs")
            for suffix in ("stdout","stderr"):
                require(sha(folder/f"{key}.{suffix}") == row[suffix+"_sha256"], "Stage stream hash differs")
            if "failure_sha256" in row:
                require(sha(folder/f"{key}.failure.json") == row["failure_sha256"], "Typed failure hash differs")
                require(read(folder/f"{key}.failure.json") == row["failure"], "Typed failure differs")
            if row["status"] == "failed":
                failures.append({"group_id":group,"stage":key,"wall_seconds":row["wall_seconds"], "returncode":row["returncode"],
                    "timed_out":row["timed_out"],"signal":row["signal"],"failure":row.get("failure"),"error":row.get("error")})
                continue
            require(row["status"] == "completed" and row["returncode"] == 0 and not row["timed_out"] and row["signal"] is None,
                    "Completed stage returned failure")
            require(sha(folder/f"{key}.json") == row["output_sha256"], "Stage output hash differs")
            value = read(folder/f"{key}.json")
            require(value["group_id"] == group and value["case_identity"] == comparison["case_identity"] and value["market_identity"] == comparison["market_identity"], "Stage physical target identity differs")
            verified_stage[key] = value
        require(abs(sum(row["wall_seconds"] for row in stages.values())-receipt["all_attempted_stage_wall_seconds"]) <= 1e-9,
                "Spent stage time differs")
        case_row = cases[group]; case = edge.case_from_dict(case_row["case"]); market = physical.market(case,"day")
        require(case_row["split"] == "train" and case.identity() == case_row["case_identity"] == physical.make_case(group).identity() == comparison["case_identity"], "TRAIN case identity differs")
        require(market.identity() == comparison["market_identity"], "Target market identity differs")
        movement_ids = [m.id for m in case.movements]
        for key, value in verified_stage.items(): require(value["movement_ids"] == movement_ids, "Movement identity/order differs")
        scored = {}
        for arm in ARMS[:3]:
            key = "score_"+arm; value = verified_stage[key]
            model_task = str(((group-10000)%4)*3); entry = manifest["models"][arm][model_task]
            require(value["model_entry"] == entry and value["arm"] == arm and value["seed"] == 17 and value["fold"] == (group-10000)%4 and value["held_out_from_fit_and_inner"] is True,
                    "Saved scorer model/outer identity differs")
            require(len(value["logits"]) == len(movement_ids) and all(math.isfinite(v) for v in value["logits"]), "Invalid saved logits")
            model_folder = safe(entry["folder"])
            metadata = read(model_folder/"inner_progress/fit_only_preprocessing_and_groups.json") if arm == "graph_v6" else read(model_folder/"result.json")
            partition(group, metadata)
            selected = "hist_boosted" if arm == "tabular_v3" else read(model_folder/"inner_progress"/("inner_architecture_promotion.json" if arm == "graph_v6" else "inner_family_promotion.json"))["family"]
            require(value["selected_model"] == selected, "Saved inference changed inner promotion")
            versions = value["runtime_versions"]
            require(all(versions[k] == v for k,v in {"numpy":"1.26.4","scipy":"1.13.1","scikit-learn":"1.7.2","joblib":"1.5.2"}.items()), "Pinned scoring runtime differs")
            if arm == "graph_v6": require(versions["torch"] == "2.4.1+cpu", "CPU torch pin differs")
            if arm == "families_v5": require(versions["xgboost"] == "3.0.5" and versions["catboost"] == "1.2.8", "Native family pins differ")
            scorer_counts[arm] += 1
            scored[arm] = {"selected_model":selected,"fold":value["fold"],"seed":17,"output_sha256":stages[key]["output_sha256"],
                "model_hashes_verified":True,"finite_logits_and_held_out_partition_verified":True,"probabilities_not_recomputed":True,
                "load_seconds":value["artifact_load_seconds"],"inference_seconds":value["score_inference_seconds"]}
        direct = comparison["direct_source_controls"]; require(direct == verified_stage["sources"]["data"], "Source admission/comparison differs")
        candidates = direct["candidates"]; topologies = [c["topology"] for c in candidates]
        admitted_inputs = [s for s in source_inputs if s["base_id"] == group]
        require(len(candidates) == len(admitted_inputs) == direct["observed_sources"] == comparison["eligibility"]["observed_source_count"], "Source censor eligibility differs")
        direct_checks = {}; direct_choices = []
        for candidate in candidates:
            source = candidate["source"]
            source_row = next(r for r in admitted_inputs if r["source"] == source)
            require(candidate["plan"] == source_row["source_plan"] and candidate["plan_hash"] == source_row["source_plan_hash"], "Direct plan is not admitted retained source")
            require(candidate["replay"] == source_row["source_replay"] and sorted(candidate["topology"]) == sorted(source_row["selected_movements"]), "Source replay/topology differs from bank")
            source_market = physical.market(case,source)
            require(source_market.identity() == source_row["market_identity"], "Source tariff identity differs")
            distance = sum((a-b)**2 for a,b in zip(market.a,source_market.a))**.5
            require(distance == candidate["nearest_price_distance"], "Nearest-tariff distance differs")
            check = independently_replay(case, market, candidate["plan"], selected=candidate["topology"],
                expected_replay=candidate["replay"],expected_bill=candidate["direct_bill_exact"],expected_plan_hash=candidate["plan_hash"],source_topologies=topologies)
            direct_checks[source] = check; direct_choices.append((source+"_direct",Fraction(check["objective_exact"])))
            plan_count += 1
        expected_first = min(candidates,key=lambda c:c["source"])["source"]
        expected_nearest = min(candidates,key=lambda c:(c["nearest_price_distance"],c["source"]))["source"]
        expected_cheapest = min(candidates,key=lambda c:(Fraction(c["direct_bill_exact"]),c["source"]))["source"]
        require((direct["first_source"],direct["nearest_price"],direct["cheapest_exact_bill"]) == (expected_first,expected_nearest,expected_cheapest), "Retrieval controls differ")
        replay_checks = {}

        def verify_chain(arm, row, topology_stage=None):
            nonlocal plan_count
            if row is None:
                require(stages[arm+"_replay"]["status"] == "skipped", "Missing physical candidate but admitted replay")
                return None
            require(stages[arm+"_charge"]["status"] == stages[arm+"_replay"]["status"] == "completed", "No completed charging/replay chain")
            charged = verified_stage[arm+"_charge"]["data"]; saved = verified_stage[arm+"_replay"]["data"]
            require(saved == row and charged["plan"] == row["plan"] and charged["internal_charge_replay"] == row["replay"] and charged["physical_comparison_credit"] is False, "Charge/replay/comparison binding differs")
            if topology_stage:
                cover = verified_stage[topology_stage]["data"]
                require(sorted(charged["selected_movements"]) == sorted(cover["selected_movements"]), "Fixed charge changed cover")
            checked = independently_replay(case,market,row["plan"],selected=charged["selected_movements"],expected_replay=row["replay"],
                expected_bill=row["objective_exact"],expected_plan_hash=row["plan_hash"],source_topologies=topologies)
            require(checked["vehicle_count"] == row["vehicle_count"] and checked["topology_novel"] == row["topology_novel"], "Fleet/novelty differs")
            plan_count += 1; replay_checks[arm] = checked; return checked

        primary = {}
        for arm in ARMS:
            row = comparison["primary_repaired_proposals"][arm]
            primary[arm] = verify_chain(arm,row,arm+"_repair")
            if row is not None:
                repair = verified_stage[arm+"_repair"]["data"]
                require(repair["objective_policy"] == ("cost_only" if arm == "cost_only" else "cost_learned") and repair["threads"] == 1 and repair["random_seed"] == 0, "Cover policy/thread differs")
        recharged = {}
        for source in ("source0","source1"):
            name = source+"_recharged"; row = comparison["source_recharges"][name]
            check = verify_chain(source,row)
            recharged[name] = check
            if check:
                require(check["selected_movements"] == direct_checks[source]["selected_movements"], "Source recharge changed topology")
                direct_choices.append((name,Fraction(check["objective_exact"])))
        winner = min(direct_choices,key=lambda c:(c[1],c[0])); policy = comparison["source_policy"]
        require(policy["status"] == "replayed" and policy["selected_arm"] == winner[0] and Fraction(policy["objective_exact"]) == winner[1] and policy["uses_all_direct_and_attempted_source_charge_replay_stages"] is True, "Source policy not the declared minimum")
        raw = {}
        raw_checks = {}
        for arm in ARMS[:3]:
            key = arm+"_raw_decode"; decoded = verified_stage[key]["data"]
            chosen = set(); logits = verified_stage["score_"+arm]["logits"]
            for trip in case.trips:
                for side in ("after","before"):
                    choices = [i for i,m in enumerate(case.movements) if getattr(m,side) == trip.id]
                    chosen.add(case.movements[max(choices,key=lambda i:(logits[i],-i))].id)
            require(sorted(chosen) == decoded["selected_movements"], "Raw argmax/tie selection differs")
            structural = True
            try: pf.recover_paths(case,sorted(chosen))
            except ValueError: structural = False
            require(decoded["status"] == ("structurally_valid" if structural else "invalid_topology"), "Raw topology gate differs")
            raw[arm] = decoded["status"]
            raw_checks[arm] = verify_chain(arm+"_raw",comparison["raw_decode_diagnostics"][arm],key if structural else None)
        cold = comparison["cold_physical_incumbent"]
        require(cold == verified_stage["cold_planner_replay"]["data"], "Cold independent replay/comparison differs")
        planner = verified_stage["cold_planner"]["data"]
        require(planner["plan"] == cold["plan"] and planner["physical_comparison_credit"] is False, "Cold extraction/replay binding differs")
        cold_check = independently_replay(case,market,cold["plan"],selected=[m for v in cold["plan"]["vehicles"] for m in v["movements"]],
            expected_replay=cold["replay"],expected_bill=cold["objective_exact"],expected_plan_hash=cold["plan_hash"],source_topologies=topologies)
        plan_count += 1
        for name, field in (("cold_hull","cold_hull_relaxation"),("retained_hull","retained_source_hull_relaxation")):
            require(stages[name]["status"] == "failed" and comparison[field] is None, "Failed hull has result credit")
        accounting = verified_stage["accounting"]; require(accounting == receipt["source_acquisition_accounting"], "Accounting/comparison binding differs")
        dataset = safe(f"result/physical_learning/20260930-shard{(group-10000)//8:02d}-dataset-v1")
        dataset_receipt = read(dataset/"dataset_receipt.json")
        require(sha(dataset/"dataset_receipt.json") == accounting["data"]["dataset_receipt_sha256"] and sha(dataset/"source_outcomes.jsonl") == accounting["data"]["source_outcomes_sha256"] == dataset_receipt["output_hashes"]["source_outcomes.jsonl"], "Deferred acquisition hash differs")
        acquisition_rows = [json.loads(line) for line in (dataset/"source_outcomes.jsonl").read_text().splitlines()]
        acquisition_rows = [r for r in acquisition_rows if r["base_id"] == group]
        require(len(acquisition_rows) == 2 and {r["source"] for r in acquisition_rows} == {"source0","source1"}, "Missing intended source acquisition attempt")
        require(sum(float(r["paid_seconds"]) for r in acquisition_rows) == accounting["data"]["paid_seconds_total"], "Sunk source paid total differs")
        expected_accounting = {r["source"]:{"status":r["status"],"paid_seconds":r["paid_seconds"],"native_status":r.get("native_status")} for r in acquisition_rows}
        require(expected_accounting == accounting["data"]["by_source"], "Source attempt censor/status accounting differs")
        source_acquisition.append(accounting["data"]["paid_seconds_total"])
        wrapper_path,wrapper = wrappers[task]
        tasks.append({"task_id":task,"group_id":group,"case_identity":case.identity(),"market_identity":market.identity(),
            "scorer_checks":scored,"primary":primary,"source_policy":{**policy,"objective":float(winner[1])},
            "paired_primary_vs_source":{arm:sign_pair(check["objective_exact"],str(winner[1])) if check else None for arm,check in primary.items()},
            "direct_source_checks":direct_checks,"source_recharge_checks":recharged,"raw_status":raw,"raw_replay_checks":raw_checks,
            "cold_physical_check":cold_check,"cold_vs_source":sign_pair(cold_check["objective_exact"],str(winner[1])),
            "cold_planner_status":planner["status"],"cold_hull_status":"failed","retained_hull_status":"failed",
            "source_control_choices":{"first":expected_first,"nearest":expected_nearest,"cheapest_direct":expected_cheapest},
            "source_acquisition":accounting["data"],
            "charged_work_seconds": {
                "primary_by_arm":{arm:sum(stages[key]["wall_seconds"] for key in (["score_"+arm] if arm != "cost_only" else [])+[arm+"_repair",arm+"_charge",arm+"_replay"]) for arm in ARMS},
                "source_policy_all_direct_and_attempted_recharge_replay":sum(stages[key]["wall_seconds"] for key in ["sources","source0_charge","source0_replay","source1_charge","source1_replay"]),
                "raw_additional_shared_score_already_in_primary":sum(stages[arm+suffix]["wall_seconds"] for arm in ARMS[:3] for suffix in ("_raw_decode","_raw_charge","_raw_replay")),
                "cold_physical":sum(stages[key]["wall_seconds"] for key in ("cold_planner","cold_planner_replay")),
                "failed_hull_controls":sum(stages[key]["wall_seconds"] for key in ("cold_hull","retained_hull")),
                "input_and_deferred_accounting":sum(stages[key]["wall_seconds"] for key in ("inputs","accounting"))},
            "task_wall_seconds":receipt["wall_seconds"],"stage_wall_seconds":receipt["all_attempted_stage_wall_seconds"],
            "wrapper_wall_seconds":wrapper["elapsed_seconds"],"wrapper_sha256":sha(wrapper_path),"raw_metadata_hashes":code_hashes[f"task{task:02d}"]})
    summary = {}
    common = [t for t in tasks if all(t["primary"][arm] is not None for arm in ARMS)]
    for arm in ARMS:
        observed = [t for t in tasks if t["primary"][arm] is not None]
        pairs = [t["paired_primary_vs_source"][arm] for t in observed]
        summary[arm] = {"replayed_groups":len(observed),"failed_groups":[t["group_id"] for t in tasks if t["primary"][arm] is None],
            "exact_relations":dict(Counter(p["relation"] for p in pairs)),"bill_delta":stats([p["delta"] for p in pairs]),
            "relative_bill_delta_percent":stats([p["relative_delta_percent"] for p in pairs]),
            "novel_replayed_topologies":sum(t["primary"][arm]["topology_novel"] is True for t in observed),
            "fleet_counts":dict(Counter(t["primary"][arm]["vehicle_count"] for t in observed)),
            "existing_native_objective_tolerance_diagnostic": {"tolerance":nr.OBJECTIVE_TOL,
                "rule":"display/interpretation only; exact source policy and signs unchanged",
                "lower_beyond_tolerance":sum(p["delta"] < -nr.OBJECTIVE_TOL for p in pairs),
                "within_tolerance":sum(abs(p["delta"]) <= nr.OBJECTIVE_TOL for p in pairs),
                "higher_beyond_tolerance":sum(p["delta"] > nr.OBJECTIVE_TOL for p in pairs)},
            "posthoc_descriptive_bill_tolerance": {"absolute_cost_units":0.01,
                "scope":"post-hoc descriptive reporting only; exact source policy, exact signs and promotions unchanged",
                "lower":sum(p["delta"] < -0.01 for p in pairs),
                "within":sum(abs(p["delta"]) <= 0.01 for p in pairs),
                "higher":sum(p["delta"] > 0.01 for p in pairs)},
            "common15_bill_delta":stats([t["paired_primary_vs_source"][arm]["delta"] for t in common])}
    arm_time = {arm:sum(t["charged_work_seconds"]["primary_by_arm"][arm] for t in tasks) for arm in ARMS}
    source_policy_time = sum(t["charged_work_seconds"]["source_policy_all_direct_and_attempted_recharge_replay"] for t in tasks)
    charged_groups_time = {key:sum(t["charged_work_seconds"][key] for t in tasks) for key in
        ("raw_additional_shared_score_already_in_primary","cold_physical","failed_hull_controls","input_and_deferred_accounting")}
    require(abs(sum(arm_time.values())+source_policy_time+sum(charged_groups_time.values())-sum(sum(v) for v in time_by_stage.values())) <= 1e-8, "Disjoint charged work does not reconstruct all attempted time")
    ledger = {"policy":POLICY,"array_job_id":728823,"source_commit":launch["source_commit"],"input_manifest_sha256":sha(manifest_path),
        "replay_script_sha256":sha(Path(__file__)),"verified_artifact_and_physical_replay":True,"exact_saved_bills_reproduced":True,
        "scientific_campaign_complete":False,"scope_gap":"All32hull stages failed before optimization on unsupported pool_tol keyword; no hull bounds exist",
        "raw_archive_manifest_sha256":sha(raw_manifest_path),"raw_archive_file_count":raw_manifest["file_count"],
        "raw_archive_all_file_hashes_rechecked":True,"slurm_accounting_sha256":sha(accounting_path),
        "submission_timestamps":{"helper":launch["submitted_at_utc"],"parent_slurm":sorted({r["submit"] for r in parents}),
            "scope":"preserve independent timestamps; Slurm Submit is1s later than helper timestamp"},
        "saved_model_probabilities_recomputed":False,"saved_scoring_stages_hash_identity_runtime_partition_and_inner_choice_verified":True,
        "no_fit_or_scoring_or_optimizer_or_outer_promotion":True,"group_ids":manifest["group_ids"],"independent_plan_replays":plan_count,
        "stage_status_counts":dict(stage_status),"scientific_stage_status_counts":dict(scientific_status),"scoring_stage_successes":dict(scorer_counts),
        "primary_summary":summary,"common_complete_primary_groups":[t["group_id"] for t in common],
        "raw_decode_summary":{arm:dict(Counter(t["raw_status"][arm] for t in tasks)) for arm in ARMS[:3]},
        "source_policy_arm_counts":dict(Counter(t["source_policy"]["selected_arm"] for t in tasks)),
        "cold_physical_summary":{"replayed":16,"exact_relations":dict(Counter(t["cold_vs_source"]["relation"] for t in tasks)),
            "bill_delta":stats([t["cold_vs_source"]["delta"] for t in tasks]),"no_optimality_or_speedup_claim":True},
        "time":{"primary_arm_all_attempted_seconds":arm_time,"source_policy_all_direct_and_attempted_recharge_replay_seconds":source_policy_time,
            "disjoint_additional_group_seconds":charged_groups_time,"task_supervisor":stats(task_wall),"wrapper":stats(wrapper_wall),"attempted_stage_seconds":sum(sum(v) for v in time_by_stage.values()),
            "failed_stage_seconds":sum(f["wall_seconds"] for f in failures),"stage_seconds":{k:sum(v) for k,v in time_by_stage.items()},
            "sunk_source_acquisition":stats(source_acquisition),"no_matched_speedup_inference":True,"slurm_allocated_cpu_seconds":parent_cpu,"slurm_parent_elapsed_seconds":parent_elapsed,
            "slurm_peak_batch_rss_kib":allocation["peak_batch_rss_kib"],"slurm_maximum_observed_concurrency":allocation["maximum_observed_concurrent_parent_tasks"]},
        "stage_failures":failures,"stage_skips":skips,"tasks":tasks,"replay_wall_seconds":time.monotonic()-started}
    save(output,ledger)
    write_report(report,ledger)
    print(json.dumps({"verified":True,"independent_plan_replays":plan_count,"stage_status_counts":dict(stage_status),
        "common15_mean_bill_deltas":{arm:summary[arm]["common15_bill_delta"]["mean"] for arm in ARMS},
        "allocated_cpu_seconds":parent_cpu,"attempted_stage_seconds":ledger["time"]["attempted_stage_seconds"]},sort_keys=True))
    return ledger


def write_report(path, ledger):
    text = ["# Fixed TRAIN physical-proposal comparison v7\n", f"Array728823 retains usable physical results and an explicit incomplete hull-control scope. All48 saved-model scoring children passed; independent replay below reproduces{ledger['independent_plan_replays']} saved plan bills exactly. No estimator inference, fitting, optimization, new solve or retry is performed by the replay script.\n",
        "The frozen16 TRAIN timetables10064–10079 use seed17 outer-fold saved models, INNER-only family/graph promotion, and the `day` market. The primary proposals are repaired-only; source policy is the predeclared minimum of all direct and independently replayed recharged source plans, with every attempted source stage charged.\n",
        "## Stage failures and scope\n", "Both hull controls failed on all16groups (32typed TypeErrors): `nh.Budget` accepts `pool_tolerance`, while v7 passed `pool_tol`. They failed before hull optimization; no cold/retained hull bound or mixture result exists. Wrapper/Slurm0 is not full scientific success. Timetable10069 also hit the5-second HiGHS cover cap without an integral incumbent for family, graph and cost-only; tabular yielded a replayed fleet. These failures, dependent skips and spent time remain in the ledger.\n",
        "All32 source recharges and16 cold physical incumbents independently replay. Raw argmax topology is invalid in46/48 diagnostics; only tabular and family on10074 reach replay, independently of the primary repaired arms.\n",
        "## Paired physical bills\n", "Bill deltas are proposal minus matched source policy: negative is cheaper. Values below round to three decimals; exact rational bills/deltas, fleets, topologies, hashes and all failures are retained in the machine ledger. A dash is a failed cover, not a high-cost surrogate.\n",
        "| TRAIN group | Source policy bill | Δtabular | Δfamily | Δgraph | Δcost-only | Cold bill |\n|---|---:|---:|---:|---:|---:|---:|\n"]
    for task in ledger["tasks"]:
        values = [f"{task['source_policy']['objective']:.3f}"]
        values += [("0.000" if abs(task['paired_primary_vs_source'][arm]['delta']) < 0.0005 else f"{task['paired_primary_vs_source'][arm]['delta']:+.3f}") if task['paired_primary_vs_source'][arm] else "—" for arm in ARMS]
        values += [f"{task['cold_physical_check']['objective']:.3f}"]
        text.append(f"| {task['group_id']} | "+" | ".join(values)+" |\n")
    text += ["\n| Primary arm | Replayed / intended | Lower / exact tie / higher than source | Lower / within0.01 / higher (post-hoc) | Mean Δbill, available pairs | Mean Δbill, common15 | Novel topologies |\n|---|---:|---:|---:|---:|---:|---:|\n"]
    for arm in ARMS:
        row=ledger["primary_summary"][arm]; counts=row["exact_relations"]; descriptive=row["posthoc_descriptive_bill_tolerance"]
        text.append(f"| {arm} | {row['replayed_groups']}/16 | {counts.get('lower',0)}/{counts.get('exact_tie',0)}/{counts.get('higher',0)} | {descriptive['lower']}/{descriptive['within']}/{descriptive['higher']} | {row['bill_delta']['mean']:+.3f} | {row['common15_bill_delta']['mean']:+.3f} | {row['novel_replayed_topologies']} |\n")
    text += ["\nFor reader interpretation only, the extra count column applies a transparently post-hoc absolute tolerance0.01cost units: differences within±0.01 are descriptive ties. This changes neither exact bills/signs nor the predeclared exact source policy or any model promotion; it is not an inferential threshold. Exact nonzero deltas displayed as0.000 are: all learned arms on10067,−2.896330089343893e-14; graph on10068,+2.994042873709717e-14; graph on10073,−5.909557616919132e-14. All other0.000 entries are exact ties. These floating-scale differences are also below the existing native objective tolerance1e-6 and do not evidence cheaper routes. Tabular/family/graph have5/4/1 cheaper groups beyond0.01, respectively.\n",
        "Neither model promotion nor a combined best learned arm is inferred from these outcomes. The small TRAIN pilot can identify individual replayed cheaper proposals, but it does not establish a general held-out route benefit. The observed cold physical bills use a different multi-round curved planning budget; they are bounded incumbents, not certified physical optima or a matched-speedup comparison.\n",
        "## Time and limitations\n", f"All attempted stage wall time is{ledger['time']['attempted_stage_seconds']:.3f}s, including{ledger['time']['failed_stage_seconds']:.3f}s spent in failed children. Supervisor totals{ledger['time']['task_supervisor']['sum']:.3f}s; wrapper totals{ledger['time']['wrapper']['sum']:.0f}s. Prior source acquisition totals{ledger['time']['sunk_source_acquisition']['sum']:.3f}s and remains a separate sunk charge. Slurm allocated{ledger['time']['slurm_allocated_cpu_seconds']}CPU-seconds ({ledger['time']['slurm_allocated_cpu_seconds']/3600:.3f}CPUh), peak batch RSS{ledger['time']['slurm_peak_batch_rss_kib']}KiB, observed concurrency{ledger['time']['slurm_maximum_observed_concurrency']}; requested ceiling was8CPUh. No stage time is discarded because it failed.\n",
        "Disjoint per-arm work totals retain failed/capped stages and shared scoring costs in the ledger; source policy also retains all source admission/recharge/replay work. The ledger verifies complete stage hash chains, runtime pins, movement/market identities, outer-only partitions and recorded INNER choices. It verifies finite saved logits and completed scoring receipts; it does not rerun saved-model numerical prediction. All physical plans are replayed with the deterministic native replay/pricing-start APIs and exact curved cost recomputation. Source retrieval is within each timetable's admitted two-source bank. No DEV/TEST, training, optimality, matched speedup or outer-based promotion claim is made.\n"]
    import re
    rendered = "\n".join(text)
    rendered = re.sub(r"(?m)(^\|[^\n]*\n)\n+(?=\|)", r"\1", rendered)
    with Path(path).open("x") as stream: stream.write(rendered)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=DOC/"ROUTE_PROPOSAL_TRAIN_V7_REPLAY.json")
    parser.add_argument("--report",type=Path,default=DOC/"ROUTE_PROPOSAL_TRAIN_V7_RESULTS.md")
    args=parser.parse_args();replay(args.output,args.report)


if __name__ == "__main__": main()
