"""Frozen-model transfer on two new, independent synthetic development timetables."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import fcntl
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from egglab import learned_proposals as lp
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from experiments import computational_benchmark as base
from experiments import learning_campaign_stage2 as prior
from experiments import route_repair_pilot as repair
from experiments import retrieval_comparison as retrieval
from experiments import train_fleet_proposals as trainer
from experiments import budget_sizing_diagnostic as sizing

ROOT = base.ROOT
ATTEMPT = ROOT / "result/learning_campaign/20260930-transfer-attempt1"
PROTOCOL = "egg-frozen-model-independent-transfer-20260930-v1"
PROFILE = {2018: ("dev", 20), 2019: ("dev", 28)}
SEEDS = tuple(PROFILE)
RESERVED_TEST_SEEDS = prior.RESERVED_TEST_SEEDS + (2020, 2021)
SOURCE_STAGES = ("source0", "source1")
TARGET_STAGES = ("cold", "retained", "nearest_price", "cheapest_bill", "learned")
REPAIR_STAGES = ("shared_cost_only", "shared_cost_learned")
STAGES = SOURCE_STAGES + TARGET_STAGES + REPAIR_STAGES
CELLS = (tuple((seed, stage) for seed in SEEDS for stage in SOURCE_STAGES)
         + tuple((seed, stage) for seed in SEEDS for stage in TARGET_STAGES + REPAIR_STAGES))
NATIVE_CHILD_SECONDS = 100
REPAIR_CHILD_SECONDS = 240
INFERENCE_SECONDS = 45
CONTROLLER_SECONDS = 3000
SOURCE_FILES = tuple(dict.fromkeys(prior.SOURCE_FILES + repair.SOURCE_FILES + (
    "src/experiments/transfer_campaign.py", "src/tests/test_transfer_campaign.py",
    "src/cluster/transfer_campaign.sbatch",
    "research-20260930/learning-campaign/PROTOCOL_TRANSFER_CAMPAIGN.md",
    "src/experiments/train_fleet_proposals.py",
    "src/experiments/energy_aware_repair_pilot.py",
    "src/experiments/shared_interval_repair_pilot.py",
    "src/tests/test_shared_charging_cover.py",
)))


def attempt(path):
    value = Path(path).resolve()
    if value != ATTEMPT.resolve():
        raise ValueError("Only the exclusive independent-transfer attempt is allowed")
    return value


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def case_for(seed):
    return prior.make_case(seed, profile=PROFILE)


def seed_for(name):
    return prior.seed_from_name(name, profile=PROFILE)


def folder(path, name, stage):
    return prior.folder(path, name, stage)


def design():
    stage2_frozen, model = repair._stage2_inputs()
    if set(PROFILE).intersection(prior.PROFILE) or set(PROFILE).intersection(RESERVED_TEST_SEEDS):
        raise ValueError("Transfer groups overlap training, prior development, or reserved tests")
    if set(model.training_groups).intersection({f"learning_s{seed}" for seed in SEEDS}):
        raise ValueError("Frozen model was trained on a transfer group")
    groups = {}
    for seed in SEEDS:
        case = case_for(seed)
        markets = {kind: prior.market(case, kind) for kind in prior.MARKETS}
        groups[case.name] = {"base_group": f"learning_s{seed}", "split": "dev",
            "case": asdict(case), "case_identity": case.identity(),
            "pure_witness_hash": nr.digest(prior.make_witness(case, profile=PROFILE)),
            "markets": {kind: asdict(m) for kind, m in markets.items()},
            "market_identities": {kind: m.identity() for kind, m in markets.items()}}
    return {"generator": prior.GENERATOR, "profile": {str(seed): {"split": "dev", "services": n}
                for seed, (_, n) in PROFILE.items()}, "groups": groups,
            "reserved_test_seeds": list(RESERVED_TEST_SEEDS),
            "new_size_matched_test_reservations": {"2020": 20, "2021": 28},
            "frozen_model_training_groups": list(model.training_groups),
            "stage2_source_commit": stage2_frozen["source_commit"],
            "stage2_input_hashes": repair.input_hashes(),
            "cell_order": [{"seed": seed, "stage": stage} for seed, stage in CELLS],
            "declared_cells": len(CELLS), "native_budget": asdict(prior.budget()),
            "repair_budget": asdict(repair.repair_budget()),
            "repair_hull_budget": asdict(repair.hull_budget()),
            "cover_seconds": 30.0, "native_child_seconds": NATIVE_CHILD_SECONDS,
            "repair_child_seconds": REPAIR_CHILD_SECONDS,
            "inference_hard_seconds": INFERENCE_SECONDS,
            "controller_seconds": CONTROLLER_SECONDS,
            "policy": prior.POLICY, "no_refit": True,
            "source_cells_before_inference": True, "inference_before_all_target_cells": True}


def freeze(path):
    target = attempt(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    spec = {"protocol": PROTOCOL, "source_commit": commit,
            "source_hashes": source_hashes(), "runtime": sizing.software_runtime(),
            "native_probe": sizing.native_probe(), "design": design(),
            "scientific_admission": "pending independent result review"}
    target.mkdir(parents=True, exist_ok=False)
    base.save_new(target / "frozen.json", spec)
    return spec


def frozen(path):
    target = attempt(path)
    spec = json.loads((target / "frozen.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if (spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit
            or spec.get("source_hashes") != source_hashes()
            or not sizing.runtime_compatible(spec.get("runtime"), sizing.software_runtime())
            or spec.get("native_probe") != sizing.native_probe()
            or base.canonical(spec.get("design")) != base.canonical(design())):
        raise ValueError("Frozen transfer source/runtime/model/inputs/design changed")
    return spec


def _catalog_rows(path):
    file = Path(path) / "catalog.jsonl"
    return [json.loads(line) for line in file.read_text().splitlines()] if file.exists() else []


def catalog_row(path, seed, stage):
    case = case_for(seed)
    market_name = stage if stage in SOURCE_STAGES else "target"
    market = prior.market(case, market_name)
    if stage in REPAIR_STAGES:
        dest = folder(path, case.name, stage)
        receipt = json.loads((dest / "receipt.json").read_text())
        result = json.loads((dest / "result.json").read_text()) if (dest / "result.json").is_file() else None
        repair_result = json.loads((dest / "repair.json").read_text())["result"] if (dest / "repair.json").is_file() else {}
        independent = (json.loads((dest / "independent_replay.json").read_text())
                       if (dest / "independent_replay.json").is_file() else None)
        candidate_kind = (independent.get("candidate_kind") if independent else
                          result.get("candidate_kind") if result else None)
        plan = (repair_result.get("plan") if candidate_kind == "repaired" else
                json.loads((dest / "fallback.json").read_text())["plan"]
                if candidate_kind == "source_fallback" else None)
        objective = None
        if plan is not None:
            if independent is None:
                raise ValueError("Repair plan lacks independent replay receipt")
            replay = nr.replay_native(case, plan)
            objective = str(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
            if (independent.get("case_identity") != case.identity()
                    or independent.get("market_identity") != market.identity()
                    or independent.get("plan_hash") != nr.digest(plan)
                    or independent.get("objective_exact") != objective
                    or (result is not None and result.get("candidate_objective_exact") != objective)):
                raise ValueError("Provisional repair candidate replay/hash/target cost changed")
        exception = (json.loads((dest / "exception.json").read_text())
                     if (dest / "exception.json").is_file() else None)
        label = {"status": "hard_timeout" if receipt["hard_timeout"] else
                 "failed" if receipt["returncode"] != 0 else "returned",
                 "receipt": receipt, "failure": exception or repair_result.get("failure"),
                 "candidate_kind": candidate_kind, "feasible": plan is not None,
                 "optimality": "unknown", "plan": plan,
                 "plan_hash": nr.digest(plan) if plan is not None else None,
                 "objective_exact": objective, "upper_exact": objective,
                 "elapsed_seconds": receipt.get("elapsed_seconds"),
                 "hull_assessment": result.get("hull_assessment") if result else None}
    else:
        label = prior.label(path, case, stage)
    return {"row_id": case.name + "/" + stage, "base_group": f"learning_s{seed}",
            "split": "dev", "case": asdict(case), "case_identity": case.identity(),
            "market": asdict(market), "market_identity": market.identity(),
            "market_name": market_name,
            "market_role": "source" if stage in SOURCE_STAGES else "target",
            "market_prices": list(market.a), "market_quadratic": list(market.b),
            "arm": "source" if stage in SOURCE_STAGES else stage, "label": label}


def _learned_candidate(path, case, available):
    receipt = json.loads((Path(path) / "inference_receipt.json").read_text())
    proposals_path = Path(path) / "learned/proposals.jsonl"
    if (receipt.get("returncode") != 0 or receipt.get("before_all_target_cells") is not True
            or receipt.get("output_hashes", {}).get("proposals.jsonl") != base.sha(proposals_path)):
        raise ValueError("No successful frozen-model inference before target solves")
    matched = [json.loads(line) for line in proposals_path.read_text().splitlines()
               if json.loads(line).get("case_identity") == case.identity()]
    if len(matched) != 1 or matched[0].get("replay_ok") is not True:
        raise ValueError("No unique replayed frozen-model proposal")
    proposed = matched[0]
    nr.replay_native(case, proposed["plan"])
    candidates = [candidate for candidate in available["candidates"]
                  if candidate["source"] == proposed["source_row_id"].rsplit("/", 1)[-1]
                  and candidate["column"]["plan"] == proposed["plan"]]
    if len(candidates) != 1:
        raise ValueError("Frozen-model proposal does not match source pool")
    return candidates, proposed


def native_worker(path, seed, stage):
    target = attempt(path)
    case = case_for(seed)
    dest = folder(target, case.name, stage)
    started = time.monotonic()
    try:
        spec = frozen(target)
        if (seed, stage) not in CELLS or stage in REPAIR_STAGES or not (dest / "launch.json").is_file():
            raise ValueError("Undeclared native cell or missing launch receipt")
        kind = stage if stage in SOURCE_STAGES else "target"
        m = prior.market(case, kind)
        group = spec["design"]["groups"][case.name]
        if case.identity() != group["case_identity"] or m.identity() != group["market_identities"][kind]:
            raise ValueError("Frozen case/market identity changed")
        if stage in TARGET_STAGES and not (target / "inference_receipt.json").is_file():
            raise ValueError("Target cell cannot start before frozen-model inference")
        previous = identity = None
        arm = "retained" if stage in SOURCE_STAGES else "cold"
        if stage in TARGET_STAGES[1:]:
            available = prior.pool(target, case)
            if not available["eligible"]:
                raise ValueError("No replayed source fleet for target retrieval")
            if stage != "retained":
                available = prior.catalog_source_pool(target, case, available)
                if not available["eligible"]:
                    raise ValueError("No matching trainer-visible source fleet")
            if stage == "learned":
                selected, learned = _learned_candidate(target, case, available)
            elif stage == "cheapest_bill":
                selected, learned = prior.select_nonlinear_cheapest(available, m), None
            elif stage == "nearest_price":
                selected, learned = prior.select_nearest_source_market(available, case, m), None
            else:
                selected, learned = retrieval.select(available, m, stage), None
            direct_started = time.monotonic()
            direct = retrieval.direct_proposals(case, m, selected)
            direct_wall = time.monotonic()-direct_started
            base.save_new(dest / "direct_proposals.json", {
                "case_identity": case.identity(), "market_identity": m.identity(),
                "selected_keys": [candidate["key"] for candidate in selected],
                "proposals": direct, "direct_replay_rescoring_wall_seconds": direct_wall})
            base.save_new(dest / "selection.json", {
                "selected_keys": [candidate["key"] for candidate in selected],
                "candidate_pool_keys": [candidate["key"] for candidate in available["candidates"]],
                "learned_proposal": {"source_row_id": learned["source_row_id"],
                    "proposed_topology": learned["proposed_topology"],
                    "projection": learned["projection"],
                    "online_timing_seconds": learned["online_timing_seconds"]} if learned else None,
                "source_paid_seconds": sum(row.get("paid_source_seconds") or 0
                                           for row in available["sources"].values()),
                "direct_replay_rescoring_wall_seconds": direct_wall,
                "lookup_elapsed_seconds": time.monotonic()-started})
            previous, identity = retrieval.import_envelope(case, m, prior.budget(), available, selected)
            base.save_new(dest / "import_envelope.json", previous)
            arm = "retained"
        result = compact.certify(case, m, prior.budget(), arm=arm,
            state_index=0 if previous is None else 1,
            previous=previous, expected_previous=identity,
            record=prior._event_writer(dest), **prior.POLICY)
        base.save_new(dest / "raw_result.json", {"result": result, "case": case.name, "stage": stage})
        assessment = retrieval.assess_hull(case, m, result)
        base.save_new(dest / "result.json", {"assessment": assessment,
                                              "elapsed_seconds": time.monotonic()-started})
        return 0
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "elapsed_seconds": time.monotonic()-started})
        return 2


def infer_worker(path):
    target = attempt(path)
    frozen(target)
    if not (target / "inference_launch.json").is_file():
        raise ValueError("Missing prospective inference launch receipt")
    rows = _catalog_rows(target)
    expected = {case_for(seed).name + "/" + source for seed in SEEDS for source in SOURCE_STAGES}
    if len(rows) != 4 or {row["row_id"] for row in rows} != expected or any(
            row.get("split") != "dev" or row.get("arm") != "source" for row in rows):
        raise ValueError("Frozen inference requires exactly four source rows and no target labels")
    _, model = repair._stage2_inputs()
    proposals = []
    for seed in SEEDS:
        case = case_for(seed)
        market = prior.market(case, "target")
        target_row = {"row_id": case.name + "/proposal_target", "base_group": f"learning_s{seed}",
            "split": "dev", "case": asdict(case), "case_identity": case.identity(),
            "market": asdict(market), "market_prices": list(market.a),
            "market_quadratic": list(market.b), "arm": "proposal_target",
            "label": {"feasible": False, "plan": None}}
        proposals.append(trainer._summary(lp.rank_candidates(model, target_row, rows)))
    trainer._write_atomic(target / "learned/proposals.jsonl", proposals)
    return 0


def infer_before_targets(path):
    target = Path(path)
    receipt_path = target / "inference_receipt.json"
    if receipt_path.exists():
        return json.loads(receipt_path.read_text())
    rows = _catalog_rows(target)
    expected = {case_for(seed).name + "/" + source for seed in SEEDS for source in SOURCE_STAGES}
    if len(rows) != 4 or {row["row_id"] for row in rows} != expected:
        raise ValueError("All four source cells must be catalogued before inference")
    if any((folder(target, case_for(seed).name, stage) / "launch.json").exists()
           for seed in SEEDS for stage in TARGET_STAGES + REPAIR_STAGES):
        raise ValueError("Frozen-model inference was not before every target launch")
    model_path = repair.STAGE2 / "learned/model.json"
    if (target / "inference_launch.json").exists() or (target / "learned").exists():
        receipt = {"status": "interrupted_unreceipted", "returncode": None,
            "before_all_target_cells": True, "catalog_sha256": base.sha(target / "catalog.jsonl"),
            "frozen_model_sha256": base.sha(model_path), "output_hashes": {}}
        base.save_new(receipt_path, receipt)
        return receipt
    command = [sys.executable, "-m", "experiments.transfer_campaign", "infer",
               "--attempt", str(target)]
    base.save_new(target / "inference_launch.json", {"command": command,
        "hard_seconds": INFERENCE_SECONDS, "catalog_sha256": base.sha(target / "catalog.jsonl"),
        "frozen_model_sha256": base.sha(model_path), "source_hashes": source_hashes()})
    started = time.monotonic()
    try:
        with (target / "inference_stdout.txt").open("xb") as stdout, \
             (target / "inference_stderr.txt").open("xb") as stderr:
            result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                    timeout=INFERENCE_SECONDS, check=False)
        rc, failure = result.returncode, None
    except subprocess.TimeoutExpired:
        rc, failure = 124, "hard_timeout"
    except Exception as exc:
        rc, failure = 1, repr(exc)
    outputs = target / "learned/proposals.jsonl"
    receipt = {"status": "complete" if rc == 0 else "failed", "returncode": rc,
        "failure": failure, "elapsed_seconds": time.monotonic()-started,
        "before_all_target_cells": True,
        "catalog_sha256": base.sha(target / "catalog.jsonl"),
        "frozen_model_sha256": base.sha(model_path),
        "runtime": sizing.software_runtime(),
        "output_hashes": {"proposals.jsonl": base.sha(outputs)} if outputs.is_file() else {}}
    base.save_new(receipt_path, receipt)
    return receipt


def source_fallback(path, case, market):
    available = prior.catalog_source_pool(path, case, prior.pool(path, case))
    selected = prior.select_nonlinear_cheapest(available, market)[0]
    plan = selected["column"]["plan"]
    replay = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
    provenance = {"source_row_id": case.name + "/" + selected["source"],
        "source_plan_hash": nr.digest(plan), "projection_key": selected["key"],
        "objective_exact": str(exact), "source_pool_acquisition_seconds": sum(
            row.get("paid_source_seconds") or 0 for row in available["sources"].values()),
        "catalog_sha256": base.sha(Path(path) / "catalog.jsonl")}
    return plan, replay, provenance


def repair_worker(path, seed, stage):
    target = attempt(path)
    case = case_for(seed)
    dest = folder(target, case.name, stage)
    started = time.monotonic()
    try:
        spec = frozen(target)
        if stage not in REPAIR_STAGES or not (dest / "launch.json").is_file():
            raise ValueError("Undeclared repair cell or missing launch receipt")
        if not (target / "inference_receipt.json").is_file():
            raise ValueError("Repair cannot start before frozen-model inference")
        market = prior.market(case, "target")
        group = spec["design"]["groups"][case.name]
        if case.identity() != group["case_identity"] or market.identity() != group["market_identities"]["target"]:
            raise ValueError("Frozen case/market identity changed")
        _, model = repair._stage2_inputs()
        controls = {}
        for arm in ("learned", "cheapest_bill"):
            matched = [row for row in _catalog_rows(target) if row["row_id"] == case.name + "/" + arm]
            if len(matched) != 1:
                raise ValueError("Missing target control: " + arm)
            label = matched[0]["label"]
            controls[arm] = {key: label.get(key) for key in (
                "status", "feasible", "objective_exact", "elapsed_seconds",
                "lower_exact", "upper_exact", "plan_hash", "native_status")}
        base.save_new(dest / "controls.json", controls)
        prior_model = model if stage == "shared_cost_learned" else None
        return repair.evaluate_case(dest, case.name, case, market, prior_model, spec,
            controls, started, cover_policy="cost_learned" if prior_model else "cost_only",
            energy_relaxation=True, charging_caps=True, shared_charging=True,
            skip_hull_for_fallback=True, path_seconds=30.0,
            fallback_provider=lambda name, c, m: source_fallback(target, c, m))
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "elapsed_seconds": time.monotonic()-started})
        return 2


def controller(path):
    target = attempt(path)
    frozen(target)
    started = time.monotonic()
    with (target / ".controller.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another transfer controller holds the run lock") from exc
        if not (target / "controller_started.json").exists():
            base.save_new(target / "controller_started.json", {"protocol": PROTOCOL,
                                                                  "utc": time.time()})
        for seed, stage in CELLS:
            case = case_for(seed)
            hard = REPAIR_CHILD_SECONDS if stage in REPAIR_STAGES else NATIVE_CHILD_SECONDS
            if time.monotonic()-started > CONTROLLER_SECONDS-hard:
                raise TimeoutError("Transfer controller budget exhausted before next cell")
            if stage == TARGET_STAGES[0] and seed == SEEDS[0]:
                infer_before_targets(target)
            dest = folder(target, case.name, stage)
            if (dest / "receipt.json").exists():
                prior.append_catalog(target, catalog_row(target, seed, stage))
                continue
            if dest.exists():
                raise ValueError("Interrupted unreceipted cell preserved: " + str(dest))
            dest.mkdir(parents=True, exist_ok=False)
            command = [sys.executable, "-m", "experiments.transfer_campaign", "worker",
                       "--attempt", str(target), "--case", case.name, "--stage", stage]
            base.launch_child(target, case.name, 0, stage, hard, command=command)
            prior.append_catalog(target, catalog_row(target, seed, stage))
        rows = _catalog_rows(target)
        if not (target / "summary.json").exists():
            base.save_new(target / "summary.json", {"protocol": PROTOCOL,
                "declared_cells": len(CELLS), "accounted_cells": len(rows),
                "feasible_cells": sum(bool(r["label"]["feasible"]) for r in rows),
                "inference_receipt": json.loads((target / "inference_receipt.json").read_text()),
                "test_groups_unobserved": True,
                "scientific_admission": "pending independent result review"})
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "controller", "worker", "infer"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case")
    parser.add_argument("--stage", choices=STAGES)
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(design(), sort_keys=True, indent=2))
        return 0
    if args.mode == "freeze":
        freeze(args.attempt); return 0
    if args.mode == "preflight":
        frozen(args.attempt)
        print(json.dumps({"runtime": sizing.software_runtime(),
                          "native_probe": sizing.native_probe()}, sort_keys=True))
        return 0
    if args.mode == "controller":
        return controller(args.attempt)
    if args.mode == "infer":
        return infer_worker(args.attempt)
    if not args.case or not args.stage:
        parser.error("worker requires --case and --stage")
    seed = seed_for(args.case)
    return repair_worker(args.attempt, seed, args.stage) if args.stage in REPAIR_STAGES else \
           native_worker(args.attempt, seed, args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
