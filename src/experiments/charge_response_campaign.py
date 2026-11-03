"""Prospective grouped source-route charging-response learning campaign."""
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

from egglab import charge_response_model as crm
from egglab import learned_proposals as edge
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from egglab import route_fixed_repair as rr
from experiments import budget_sizing_diagnostic as sizing
from experiments import computational_benchmark as base
from experiments import learning_campaign_stage2 as prior
from experiments import retrieval_comparison as retrieval

ROOT = base.ROOT
ATTEMPT = ROOT / "result/learning_campaign/20260930-charge-response-attempt1"
PROTOCOL = "egg-charge-response-grouped-ridge-20260930-v1"
PROFILE = {2022: ("train", 12), 2023: ("train", 12),
           2024: ("train", 20), 2025: ("train", 20),
           2026: ("train", 28), 2027: ("train", 28),
           2028: ("dev", 20), 2029: ("dev", 28),
           2030: ("dev", 20), 2031: ("dev", 28)}
RESERVED = (2004, 2005, 2020, 2021)
SOURCES = ("source0", "source1")
STAGES = SOURCES + ("source0_charge", "source1_charge", "cold")
CHILD_SECONDS = 100
TRAIN_SECONDS = 60
CONTROLLER_SECONDS = 5400
OLD_MODEL = ROOT / "result/learning_campaign/20260930-stage2-attempt1/learned/model.json"
OLD_FROZEN = ROOT / "result/learning_campaign/20260930-stage2-attempt1/frozen.json"
OLD_TRAIN_RECEIPT = ROOT / "result/learning_campaign/20260930-stage2-attempt1/learning_receipt.json"
SOURCE_FILES = tuple(dict.fromkeys(prior.SOURCE_FILES + (
    "src/experiments/charge_response_campaign.py",
    "src/egglab/charge_response_model.py",
    "src/tests/test_charge_response_campaign.py",
    "src/cluster/charge_response.sbatch",
    "research-20260930/learning-campaign/PROTOCOL_CHARGE_RESPONSE_LEARNING.md",
    "src/egglab/route_fixed_repair.py",
)))


def cells():
    # The complete source pool precedes every target-charge label.
    sources = tuple((seed, source) for seed in PROFILE for source in SOURCES)
    train_lp = tuple((seed, source + "_charge") for seed in PROFILE
                     if PROFILE[seed][0] == "train" for source in SOURCES)
    dev = tuple((seed, source + "_charge") for seed in PROFILE
                if PROFILE[seed][0] == "dev" for source in SOURCES)
    cold = tuple((seed, "cold") for seed in PROFILE if PROFILE[seed][0] == "dev")
    return sources + train_lp + dev + cold


def attempt(path):
    value = Path(path).resolve()
    if value != ATTEMPT.resolve():
        raise ValueError("Only the exclusive charge-response attempt is allowed")
    return value


def case_for(seed):
    return prior.make_case(seed, profile=PROFILE)


def seed_for(name):
    return prior.seed_from_name(name, profile=PROFILE)


def folder(path, seed, stage):
    return Path(path) / case_for(seed).name / "state0" / stage


def charge_budget():
    return nr.Budget(backend="GRB", threads=1, phase_seconds=45,
                     wall_seconds=55, max_rounds=1, epsilon=1e-4)


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def input_hashes():
    return {str(path.relative_to(ROOT)): base.sha(path)
            for path in (OLD_MODEL, OLD_FROZEN, OLD_TRAIN_RECEIPT)}


def design():
    if len(cells()) != 44 or any(seed in PROFILE for seed in RESERVED):
        raise ValueError("Group/cell reservation changed")
    groups = {}
    for seed, (split, services) in PROFILE.items():
        case = case_for(seed)
        groups[case.name] = {"seed": seed, "split": split,
            "base_group": f"learning_s{seed}", "services": services,
            "case": asdict(case), "case_identity": case.identity(),
            "pure_witness_hash": nr.digest(prior.make_witness(case, profile=PROFILE)),
            "markets": {kind: asdict(prior.market(case, kind)) for kind in prior.MARKETS},
            "market_identities": {kind: prior.market(case, kind).identity()
                                  for kind in prior.MARKETS}}
    return {"generator": prior.GENERATOR, "profile": {str(s): [k, n]
             for s, (k, n) in PROFILE.items()}, "groups": groups,
            "cell_order": [{"seed": seed, "stage": stage} for seed, stage in cells()],
            "declared_cells": 44, "train_groups": 6, "dev_groups": 4,
            "reserved_unmaterialized": list(RESERVED),
            "source_stage_before_training": True,
            "all_dev_choices_frozen_before_dev_lp_or_cold": True,
            "response_policy": crm.POLICY, "ridge": crm.RIDGE,
            "native_budget": asdict(prior.budget()),
            "charging_budget": asdict(charge_budget()),
            "child_hard_seconds": CHILD_SECONDS, "trainer_hard_seconds": TRAIN_SECONDS,
            "controller_hard_seconds": CONTROLLER_SECONDS,
            "lp_objective": "linear target market.a, nonlinear exact cost after replay",
            "no_route_reoptimization_in_charging": True}


def freeze(path):
    target = attempt(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    spec = {"protocol": PROTOCOL, "source_commit": commit,
        "source_hashes": source_hashes(), "input_hashes": input_hashes(),
        "runtime": sizing.software_runtime(), "native_probe": sizing.native_probe(),
        "design": design(), "scientific_admission": "pending independent result review"}
    target.mkdir(parents=True, exist_ok=False)
    base.save_new(target / "frozen.json", spec)
    return spec


def frozen(path):
    target = attempt(path)
    spec = json.loads((target / "frozen.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if (spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit
            or spec.get("source_hashes") != source_hashes()
            or spec.get("input_hashes") != input_hashes()
            or base.canonical(spec.get("design")) != base.canonical(design())
            or not sizing.runtime_compatible(spec.get("runtime"), sizing.software_runtime())
            or spec.get("native_probe") != sizing.native_probe()):
        raise ValueError("Frozen source, old model, runtime, or design changed")
    return spec


def _read_rows(path):
    file = Path(path) / "catalog.jsonl"
    return [json.loads(line) for line in file.read_text().splitlines()] if file.is_file() else []


def _row(path, seed, stage):
    matches = [row for row in _read_rows(path)
               if row.get("row_id") == case_for(seed).name + "/" + stage]
    if len(matches) != 1:
        raise ValueError("Expected exactly one catalog row for source/label")
    return matches[0]


def source_plan(path, seed, source):
    case = case_for(seed)
    row = _row(path, seed, source)
    label = row["label"]
    if (row.get("split") != PROFILE[seed][0] or row.get("arm") != "source"
            or row.get("case_identity") != case.identity() or not label.get("feasible")):
        raise ValueError("No replayed source plan")
    plan = label["plan"]
    replay = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    if (label.get("plan_hash") != nr.digest(plan) or label.get("load") != replay["load"]
            or label.get("ops_cost") != replay["ops_cost"]):
        raise ValueError("Source plan/replay changed")
    return row, replay


def _events(dest):
    def record(event):
        with (dest / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
            stream.flush(); os.fsync(stream.fileno())
    return record


def worker(path, seed, stage):
    target = attempt(path)
    dest = folder(target, seed, stage)
    started = time.monotonic()
    try:
        spec = frozen(target)
        if (seed, stage) not in cells() or not (dest / "launch.json").is_file():
            raise ValueError("Undeclared cell or missing launch receipt")
        case = case_for(seed)
        kind = stage if stage in SOURCES else "target"
        market = prior.market(case, kind)
        group = spec["design"]["groups"][case.name]
        if (group["case_identity"] != case.identity()
                or group["market_identities"][kind] != market.identity()):
            raise ValueError("Frozen case or market identity changed")
        if stage.endswith("_charge"):
            if PROFILE[seed][0] == "dev" and not (target / "inference_receipt.json").is_file():
                raise ValueError("Dev target LP cannot start before prospective inference")
            source = stage.removesuffix("_charge")
            source_row, original = source_plan(target, seed, source)
            direct = crm.direct_cost(case, market, original)
            base.save_new(dest / "direct_rescore.json", {"case_identity": case.identity(),
                "market_identity": market.identity(), "source_plan_hash": source_row["label"]["plan_hash"],
                "objective_exact": str(direct)})
            selected = sorted({mid for vehicle in source_row["label"]["plan"]["vehicles"]
                               for mid in vehicle["movements"]})
            charge_start = time.monotonic()
            try:
                plan, replay, native_stats = rr._solve_fixed_charge(case, market, selected,
                                                                   charge_budget(), record=_events(dest))
                charge_seconds = time.monotonic()-charge_start
                replay_start = time.monotonic()
                checked = nr.replay_native(case, plan)
                pf._checked_pricing_start(case, plan)
                if (checked != replay or {mid for vehicle in plan["vehicles"]
                        for mid in vehicle["movements"]} != set(selected)):
                    raise ValueError("Fixed source topology or replay changed")
                exact = crm.direct_cost(case, market, checked)
                base.save_new(dest / "fixed_charge.json", {"status": "replayed",
                    "case_identity": case.identity(), "market_identity": market.identity(),
                    "source_plan_hash": source_row["label"]["plan_hash"],
                    "selected_movements": selected, "plan": plan, "plan_hash": nr.digest(plan),
                    "replay": checked, "objective_exact": str(exact), "native_stats": native_stats,
                    "charge_wall_seconds": charge_seconds,
                    "independent_replay_wall_seconds": time.monotonic()-replay_start,
                    "target_optimality": "unknown; LP optimizes linear market.a only"})
                result = {"status": "replayed", "direct_exact": str(direct),
                          "post_lp_exact": str(exact), "native_status": native_stats.get("status"),
                          "charge_wall_seconds": charge_seconds,
                          "elapsed_seconds": time.monotonic()-started}
            except Exception as exc:
                telemetry = getattr(exc, "telemetry", {})
                base.save_new(dest / "fixed_charge_failure.json", {"type": type(exc).__name__,
                    "message": str(exc), "traceback": traceback.format_exc(),
                    "native_stats": telemetry.get("native_stats", locals().get("native_stats")),
                    "charge_wall_seconds": time.monotonic()-charge_start})
                result = {"status": "no_replayed_lp_plan", "direct_exact": str(direct),
                          "post_lp_exact": None, "native_status":
                          (telemetry.get("native_stats") or {}).get("status"),
                          "charge_wall_seconds": time.monotonic()-charge_start,
                          "elapsed_seconds": time.monotonic()-started}
            base.save_new(dest / "result.json", result)
        else:
            if stage == "cold" and not (target / "inference_receipt.json").is_file():
                raise ValueError("Dev cold cannot start before prospective inference")
            arm = "retained" if stage in SOURCES else "cold"
            result = compact.certify(case, market, prior.budget(), arm=arm, state_index=0,
                                     record=_events(dest), **prior.POLICY)
            base.save_new(dest / "raw_result.json", {"result": result,
                "case": case.name, "stage": stage})
            assessment = retrieval.assess_hull(case, market, result)
            base.save_new(dest / "result.json", {"assessment": assessment,
                                                  "elapsed_seconds": time.monotonic()-started})
        return 0
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "elapsed_seconds": time.monotonic()-started})
        return 2


def label(path, seed, stage):
    case = case_for(seed)
    dest = folder(path, seed, stage)
    receipt = json.loads((dest / "receipt.json").read_text())
    status = "hard_timeout" if receipt.get("hard_timeout") else (
             "failed" if receipt.get("returncode") != 0 else "returned")
    failure_file = dest / "exception.json"
    row = {"status": status, "receipt": receipt,
           "failure": json.loads(failure_file.read_text()) if failure_file.is_file() else None,
           "feasible": False, "optimality": "unknown", "plan": None, "plan_hash": None,
           "ops_cost": None, "load": None, "objective_exact": None,
           "lower_exact": None, "upper_exact": None,
           "elapsed_seconds": receipt.get("elapsed_seconds"), "native_status": None}
    market = prior.market(case, stage if stage in SOURCES else "target")
    if stage.endswith("_charge"):
        source = stage.removesuffix("_charge")
        evidence_file = dest / "fixed_charge.json"
        failure_file = dest / "fixed_charge_failure.json"
        row["failure"] = (json.loads(failure_file.read_text()) if failure_file.is_file()
                          else row["failure"])
        if evidence_file.is_file():
            evidence = json.loads(evidence_file.read_text())
            plan = evidence["plan"]
            replay = nr.replay_native(case, plan)
            source_row, _ = source_plan(path, seed, source)
            source_ids = {mid for vehicle in source_row["label"]["plan"]["vehicles"]
                          for mid in vehicle["movements"]}
            charged_ids = {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]}
            cost = str(crm.direct_cost(case, market, replay))
            if (evidence["case_identity"] != case.identity()
                    or evidence["market_identity"] != market.identity()
                    or evidence["source_plan_hash"] != source_row["label"]["plan_hash"]
                    or set(evidence["selected_movements"]) != source_ids
                    or charged_ids != source_ids or evidence["plan_hash"] != nr.digest(plan)
                    or evidence["replay"] != replay or evidence["objective_exact"] != cost):
                raise ValueError("Charged evidence identity/topology/replay mismatch")
            row.update(feasible=True, plan=plan, plan_hash=nr.digest(plan),
                       ops_cost=replay["ops_cost"], load=replay["load"],
                       objective_exact=cost, upper_exact=cost,
                       source_plan_hash=source_row["label"]["plan_hash"],
                       native_status=evidence["native_stats"].get("status"),
                       charge_wall_seconds=evidence.get("charge_wall_seconds"),
                       independent_replay_wall_seconds=evidence.get("independent_replay_wall_seconds"))
        return row
    raw_file = dest / "raw_result.json"
    if not raw_file.is_file():
        return row
    raw = json.loads(raw_file.read_text())["result"]
    row["native_status"] = raw.get("status")
    assessment_file = dest / "result.json"
    assessment = (json.loads(assessment_file.read_text()).get("assessment", {})
                  if assessment_file.is_file() else {})
    cert, mix = raw.get("lower_certificate"), raw.get("mixture")
    row["bounds_replay"] = {"global_certificate_replayed":
        assessment.get("global_certificate_replayed") is True,
        "mixture_replayed": assessment.get("mixture_replayed") is True}
    if cert and cert.get("lower_exact") is not None:
        key = "lower_exact" if row["bounds_replay"]["global_certificate_replayed"] else \
              "unverified_native_lower_exact"
        row[key] = cert["lower_exact"]
    if mix and mix.get("objective_exact") is not None:
        key = "native_mixture_upper_exact" if row["bounds_replay"]["mixture_replayed"] else \
              "unverified_native_mixture_upper_exact"
        row[key] = mix["objective_exact"]
    candidates = []
    for column in raw.get("columns", []):
        replay = nh.replay_column(case, column, compact.EXTRACTION_POLICY)
        cost = crm.direct_cost(case, market, replay)
        candidates.append((cost, column["key"], column, replay))
    if candidates:
        cost, _, column, replay = min(candidates, key=lambda item: (item[0], item[1]))
        row.update(feasible=True, plan=column["plan"], plan_hash=nr.digest(column["plan"]),
                   ops_cost=replay["ops_cost"], load=replay["load"],
                   objective_exact=str(cost), upper_exact=str(cost), column_key=column["key"])
    return row


def catalog_row(path, seed, stage):
    case = case_for(seed)
    market_name = stage if stage in SOURCES else "target"
    market = prior.market(case, market_name)
    return {"row_id": case.name + "/" + stage, "base_group": f"learning_s{seed}",
        "split": PROFILE[seed][0], "case": asdict(case), "case_identity": case.identity(),
        "market": asdict(market), "market_identity": market.identity(),
        "market_name": market_name, "market_role": "source" if stage in SOURCES else "target",
        "market_prices": list(market.a), "market_quadratic": list(market.b),
        "arm": "source" if stage in SOURCES else stage, "label": label(path, seed, stage)}


def _source_choices(path, seed, model=None, old=None):
    case = case_for(seed)
    target = prior.market(case, "target")
    candidates = []
    for source in SOURCES:
        try:
            row, replay = source_plan(path, seed, source)
        except ValueError:
            continue
        candidates.append({"source": source, "row_id": row["row_id"],
            "plan_hash": row["label"]["plan_hash"], "replay": replay,
            "plan": row["label"]["plan"],
            "direct_exact": str(crm.direct_cost(case, target, replay)),
            "features": crm.features(case, target, prior.market(case, source), replay, source)})
    if not candidates:
        return {"case_identity": case.identity(), "market_identity": target.identity(),
                "candidates": [], "choices": {}, "failure": "no replayed source fleet"}
    def pick(fn, reverse=False):
        selected = min(candidates, key=lambda c: ((-fn(c) if reverse else fn(c)),
                                                   SOURCES.index(c["source"])))
        return selected["source"]
    choices = {"cheapest_direct": pick(lambda c: Fraction(c["direct_exact"])),
               "nearest_price": pick(lambda c: sum((float(a)-float(b))**2 for a, b in zip(
                   target.a, prior.market(case, c["source"]).a)))}
    old_projection = None
    if old is not None:
        if f"learning_s{seed}" in old.training_groups:
            raise ValueError("Old EdgePrior fitted on evaluation group")
        chosen, old_projection = old_prior_choice(case, target, candidates, old)
        choices["frozen_edge_prior"] = chosen["source"]
    if model is not None:
        if f"learning_s{seed}" in model.training_groups:
            raise ValueError("Response model fitted on evaluation group")
        for candidate in candidates:
            candidate["predicted_post_lp_cost"] = model.predict_cost(
                case, target, prior.market(case, candidate["source"]),
                candidate["replay"], candidate["source"])
        choices["charge_response_ridge"] = pick(lambda c: c["predicted_post_lp_cost"])
    return {"case_identity": case.identity(), "market_identity": target.identity(),
            "old_prior_projection": old_projection,
            "old_prior_policy": edge.POLICY if old is not None else None,
            "candidates": [{key: value for key, value in c.items() if key not in ("replay", "plan")}
                           for c in candidates], "choices": choices, "failure": None}


def old_prior_choice(case, target, candidates, old):
    """Exactly the saved EdgePrior topology projection ordering for this two-source pool."""
    projected = sorted(old.propose_topology(case, target.a))
    for candidate in candidates:
        selected = {mid for vehicle in candidate["plan"]["vehicles"]
                    for mid in vehicle["movements"]}
        candidate["old_topology_distance"] = len(selected ^ set(projected))
        candidate["old_score"] = old.score(case, target.a, candidate["plan"])
        candidate["old_nearest_price_distance"] = sum(
            (float(a)-float(b))**2 for a, b in zip(
                target.a, prior.market(case, candidate["source"]).a))**0.5
    return min(candidates, key=lambda c: (
        c["old_topology_distance"], -c["old_score"],
        c["old_nearest_price_distance"], c["row_id"])), projected


def training_coverage(samples):
    expected = {case_for(seed).name + "/" + source + "_charge"
                for seed in PROFILE if PROFILE[seed][0] == "train" for source in SOURCES}
    actual = {sample["row_id"] for sample in samples}
    return {"expected_rows": sorted(expected), "replayed_rows": sorted(actual),
        "missing_rows": sorted(expected-actual),
        "training_groups": sorted({sample["group"] for sample in samples}),
        "complete_six_pairs": len(samples) == len(expected) and actual == expected}


def training_samples(path):
    samples = []
    for seed in PROFILE:
        if PROFILE[seed][0] != "train":
            continue
        case = case_for(seed)
        target = prior.market(case, "target")
        for source in SOURCES:
            try:
                source_row, replay = source_plan(path, seed, source)
                charge = _row(path, seed, source + "_charge")
            except ValueError:
                continue
            label = charge["label"]
            if not label.get("feasible"):
                continue
            if (charge["split"] != "train" or charge["base_group"] != f"learning_s{seed}"
                    or label["source_plan_hash"] != source_row["label"]["plan_hash"]):
                raise ValueError("Training label/source lineage differs")
            direct = crm.direct_cost(case, target, replay)
            samples.append({"group": f"learning_s{seed}", "split": "train",
                "row_id": charge["row_id"],
                "features": crm.features(case, target, prior.market(case, source), replay, source),
                "residual_per_trip": float((Fraction(label["objective_exact"])-direct)/len(case.trips)),
                "label_plan_hash": label["plan_hash"], "source_plan_hash": label["source_plan_hash"],
                "label_status": label["status"]})
    return samples


def infer_worker(path):
    target = attempt(path)
    frozen(target)
    if not (target / "inference_launch.json").is_file():
        raise ValueError("Missing prospective training/inference launch")
    rows = _read_rows(target)
    expected = {case_for(seed).name + "/" + source for seed in PROFILE for source in SOURCES}
    expected |= {case_for(seed).name + "/" + source + "_charge" for seed in PROFILE
                 if PROFILE[seed][0] == "train" for source in SOURCES}
    if len(rows) != len(expected) or {row["row_id"] for row in rows} != expected:
        raise ValueError("Fit/inference catalog includes missing or target development labels")
    baseline_file = target / "baseline_choices.json"
    if not baseline_file.is_file():
        raise ValueError("Prospective baseline choices absent")
    baseline = json.loads(baseline_file.read_text())
    old = edge.EdgePrior.from_dict(json.loads(OLD_MODEL.read_text()))
    expected_baseline = {case_for(seed).name: _source_choices(target, seed, old=old)
                         for seed in PROFILE if PROFILE[seed][0] == "dev"}
    if base.canonical(baseline) != base.canonical(expected_baseline):
        raise ValueError("Prospective baseline choices changed")
    fit_started = time.monotonic()
    samples = training_samples(target)
    coverage = training_coverage(samples)
    base.save_new(target / "training_coverage.json", coverage)
    if not coverage["complete_six_pairs"]:
        raise ValueError("Incomplete six-pair replayed LP training labels")
    model = crm.fit(samples)
    fit_seconds = time.monotonic()-fit_started
    inference_started = time.monotonic()
    proposals = {}
    for seed in PROFILE:
        if PROFILE[seed][0] == "dev":
            proposals[case_for(seed).name] = _source_choices(target, seed, model=model, old=old)
    inference_seconds = time.monotonic()-inference_started
    output = target / "learned"
    output.mkdir(parents=False, exist_ok=False)
    base.save_new(output / "model.json", model.to_dict())
    base.save_new(output / "training_rows.json", samples)
    base.save_new(output / "proposals.json", proposals)
    base.save_new(output / "timing.json", {"training_fit_seconds": fit_seconds,
        "four_group_inference_seconds": inference_seconds})
    return 0


def train_before_dev(path):
    target = Path(path)
    receipt_file = target / "inference_receipt.json"
    if receipt_file.is_file():
        return json.loads(receipt_file.read_text())
    expected = {(seed, source) for seed in PROFILE for source in SOURCES}
    expected |= {(seed, source + "_charge") for seed in PROFILE
                 if PROFILE[seed][0] == "train" for source in SOURCES}
    if not all((folder(target, seed, stage) / "receipt.json").is_file()
               for seed, stage in expected):
        raise ValueError("All source and train LP cells must precede inference")
    rows = _read_rows(target)
    if len(rows) != 32 or {row["row_id"] for row in rows} != {
            case_for(seed).name + "/" + stage for seed, stage in expected}:
        raise ValueError("Prospective catalog must contain only 32 source/train labels")
    if any(folder(target, seed, stage).exists() for seed in PROFILE
           if PROFILE[seed][0] == "dev" for stage in ("source0_charge", "source1_charge", "cold")):
        raise ValueError("Development target launched before inference")
    baseline_file = target / "baseline_choices.json"
    if not baseline_file.is_file() and not (target / "inference_launch.json").exists():
        baseline_started = time.monotonic()
        old = edge.EdgePrior.from_dict(json.loads(OLD_MODEL.read_text()))
        base.save_new(baseline_file, {case_for(seed).name: _source_choices(target, seed, old=old)
            for seed in PROFILE if PROFILE[seed][0] == "dev"})
        base.save_new(target / "baseline_choices_receipt.json", {
            "before_all_dev_target_cells": True,
            "baseline_choices_sha256": base.sha(baseline_file),
            "elapsed_seconds": time.monotonic()-baseline_started})
    model_input = {"catalog_sha256": base.sha(target / "catalog.jsonl"),
                   "old_model_sha256": base.sha(OLD_MODEL),
                   "baseline_choices_sha256": base.sha(baseline_file) if baseline_file.is_file() else None,
                   "model_source_sha256": source_hashes()["src/egglab/charge_response_model.py"]}
    if (target / "inference_launch.json").exists() or (target / "learned").exists():
        receipt = {"status": "interrupted_unreceipted", "returncode": None,
            "before_all_dev_target_cells": True, "inputs": model_input, "output_hashes": {},
            "elapsed_seconds": None}
        base.save_new(receipt_file, receipt)
        return receipt
    command = [sys.executable, "-m", "experiments.charge_response_campaign", "infer",
               "--attempt", str(target)]
    base.save_new(target / "inference_launch.json", {"command": command,
        "hard_seconds": TRAIN_SECONDS, "inputs": model_input})
    started = time.monotonic()
    try:
        with (target / "inference_stdout.txt").open("xb") as stdout, \
             (target / "inference_stderr.txt").open("xb") as stderr:
            completed = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                       timeout=TRAIN_SECONDS, check=False)
        rc, failure = completed.returncode, None
    except subprocess.TimeoutExpired:
        rc, failure = 124, "hard_timeout"
    except Exception as exc:
        rc, failure = 1, repr(exc)
    output = target / "learned"
    receipt = {"status": "completed" if rc == 0 else "failed", "returncode": rc,
        "failure": failure, "before_all_dev_target_cells": True,
        "inputs": model_input, "runtime": sizing.software_runtime(),
        "elapsed_seconds": time.monotonic()-started,
        "training_coverage_sha256": (base.sha(target / "training_coverage.json")
            if (target / "training_coverage.json").is_file() else None),
        "output_hashes": {p.name: base.sha(p) for p in sorted(output.glob("*")) if p.is_file()}}
    base.save_new(receipt_file, receipt)
    return receipt


def dev_choices(path, seed):
    target = Path(path)
    if PROFILE[seed][0] != "dev":
        raise ValueError("Not a development group")
    receipt = json.loads((target / "inference_receipt.json").read_text())
    proposals = target / "learned/proposals.json"
    model = target / "learned/model.json"
    success = (receipt.get("returncode") == 0
               and receipt.get("before_all_dev_target_cells") is True
               and receipt.get("output_hashes", {}).get("proposals.json") == base.sha(proposals)
               and receipt.get("output_hashes", {}).get("model.json") == base.sha(model)) if (
                   proposals.is_file() and model.is_file()) else False
    if success:
        all_proposals = json.loads(proposals.read_text())
        choice = all_proposals[case_for(seed).name]
        expected = _source_choices(target, seed,
            model=crm.ResponseModel.from_dict(json.loads(model.read_text())),
            old=edge.EdgePrior.from_dict(json.loads(OLD_MODEL.read_text())))
        if base.canonical(choice) != base.canonical(expected):
            raise ValueError("Frozen prospective development choice changed")
        return choice
    # Failed fitting does not erase prospectively frozen independent controls.
    baseline_file = target / "baseline_choices.json"
    if (baseline_file.is_file() and receipt.get("inputs", {}).get("baseline_choices_sha256")
            == base.sha(baseline_file)):
        return json.loads(baseline_file.read_text())[case_for(seed).name]
    return {"case_identity": case_for(seed).identity(),
            "market_identity": prior.market(case_for(seed), "target").identity(),
            "candidates": [], "choices": {},
            "failure": "prospective baseline choice receipt unavailable"}


def append_catalog(path, row):
    prior.append_catalog(path, row)


def summary(path):
    target = Path(path)
    cases = {}
    for seed in PROFILE:
        case = case_for(seed)
        labels = {stage: _row(target, seed, stage)["label"] for s, stage in cells() if s == seed}
        report = {"split": PROFILE[seed][0], "source_acquisition_seconds": (
            sum(labels[s]["elapsed_seconds"] for s in SOURCES)
            if all(labels[s]["elapsed_seconds"] is not None for s in SOURCES) else None),
            "source_labels": {s: {"status": labels[s]["status"],
                "feasible": labels[s]["feasible"], "objective_exact": labels[s]["objective_exact"]}
                for s in SOURCES},
            "charged_labels": {s: {"status": labels[s + "_charge"]["status"],
                "feasible": labels[s + "_charge"]["feasible"],
                "objective_exact": labels[s + "_charge"]["objective_exact"],
                "lp_paid_seconds": labels[s + "_charge"]["elapsed_seconds"]} for s in SOURCES}}
        if PROFILE[seed][0] == "dev":
            choices = dev_choices(target, seed)
            report["prospective_choices"] = choices["choices"]
            report["inference_failure"] = choices["failure"] if not choices["choices"].get(
                "charge_response_ridge") else None
            report["single_lp_methods"] = {method: {
                "source": selected,
                "post_lp_objective_exact": labels[selected + "_charge"]["objective_exact"],
                "lp_paid_seconds": labels[selected + "_charge"]["elapsed_seconds"],
                "source_acquisition_plus_lp_paid_seconds": (
                    report["source_acquisition_seconds"] + labels[selected + "_charge"]["elapsed_seconds"]
                    if report["source_acquisition_seconds"] is not None
                    and labels[selected + "_charge"]["elapsed_seconds"] is not None else None)}
                for method, selected in choices["choices"].items()}
            feasible = [(Fraction(labels[s + "_charge"]["objective_exact"]), s)
                        for s in SOURCES if labels[s + "_charge"]["feasible"]]
            report["paid_two_lp_best"] = ({"source": min(feasible)[1],
                "objective_exact": str(min(feasible)[0]),
                "lp_paid_seconds": (sum(labels[s + "_charge"]["elapsed_seconds"] for s in SOURCES)
                    if all(labels[s + "_charge"]["elapsed_seconds"] is not None for s in SOURCES)
                    else None)} if feasible else None)
            for method in report["single_lp_methods"].values():
                objective = method["post_lp_objective_exact"]
                method["excess_over_best_two_lp_exact"] = (
                    str(Fraction(objective)-min(feasible)[0])
                    if objective is not None and len(feasible) == 2 else None)
            report["cold"] = {key: labels["cold"].get(key) for key in (
                "status", "feasible", "objective_exact", "lower_exact", "upper_exact",
                "elapsed_seconds", "native_status")}
        cases[case.name] = report
    return {"protocol": PROTOCOL, "declared_cells": len(cells()),
        "accounted_cells": len(_read_rows(target)), "cases": cases,
        "inference_receipt": json.loads((target / "inference_receipt.json").read_text()),
        "baseline_choices_receipt": json.loads((target / "baseline_choices_receipt.json").read_text())
            if (target / "baseline_choices_receipt.json").is_file() else None,
        "training_inference_timing": json.loads((target / "learned/timing.json").read_text())
            if (target / "learned/timing.json").is_file() else None,
        "test_groups_unobserved": True,
        "scientific_admission": "pending independent result review"}


def controller(path):
    target = attempt(path)
    frozen(target)
    started = time.monotonic()
    with (target / ".controller.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another charge-response controller holds this attempt") from exc
        if not (target / "controller_started.json").exists():
            base.save_new(target / "controller_started.json", {"protocol": PROTOCOL,
                "utc": time.time()})
        for seed, stage in cells():
            if time.monotonic()-started > CONTROLLER_SECONDS-CHILD_SECONDS:
                raise TimeoutError("Charge-response controller budget exhausted before next cell")
            if PROFILE[seed][0] == "dev" and stage == "source0_charge":
                train_before_dev(target)
            dest = folder(target, seed, stage)
            if (dest / "receipt.json").is_file():
                append_catalog(target, catalog_row(target, seed, stage))
                continue
            if dest.exists():
                raise ValueError("Interrupted unreceipted cell preserved: " + str(dest))
            dest.mkdir(parents=True, exist_ok=False)
            command = [sys.executable, "-m", "experiments.charge_response_campaign", "worker",
                "--attempt", str(target), "--case", case_for(seed).name, "--stage", stage]
            base.launch_child(target, case_for(seed).name, 0, stage, CHILD_SECONDS,
                              command=command)
            append_catalog(target, catalog_row(target, seed, stage))
        if not (target / "summary.json").exists():
            base.save_new(target / "summary.json", summary(target))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "controller", "worker", "infer"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case")
    parser.add_argument("--stage", choices=STAGES)
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(design(), sort_keys=True, indent=2)); return 0
    if args.mode == "freeze":
        freeze(args.attempt); return 0
    if args.mode == "preflight":
        frozen(args.attempt)
        print(json.dumps({"runtime": sizing.software_runtime(),
            "native_probe": sizing.native_probe()}, sort_keys=True)); return 0
    if args.mode == "controller":
        return controller(args.attempt)
    if args.mode == "infer":
        return infer_worker(args.attempt)
    if not args.case or not args.stage:
        parser.error("worker requires --case and --stage")
    return worker(args.attempt, seed_for(args.case), args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
