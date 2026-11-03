"""Frozen charge-response model on grouped, prespecified target tariff variants."""
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
from experiments import charge_response_campaign as charge
from experiments import computational_benchmark as base
from experiments import learning_campaign_stage2 as prior
from experiments import retrieval_comparison as retrieval

ROOT = base.ROOT
ATTEMPT = ROOT / "result/learning_campaign/20260930-tariff-response-attempt1"
ARCHIVE = charge.ATTEMPT
OLD_MODEL = charge.OLD_MODEL
PROTOCOL = "egg-frozen-charge-response-tariff-transfer-20260930-v1"
PROFILE = {2032: ("dev", 20), 2033: ("dev", 28),
           2034: ("dev", 20), 2035: ("dev", 28)}
RESERVED = (2004, 2005, 2020, 2021)
SOURCES = charge.SOURCES
VARIANTS = ("late", "day", "flat")
CHILD_SECONDS = 100
INFERENCE_SECONDS = 60
CONTROLLER_SECONDS = 5400
SOURCE_FILES = tuple(dict.fromkeys(charge.SOURCE_FILES + (
    "src/experiments/tariff_response_campaign.py",
    "src/tests/test_tariff_response_campaign.py",
    "src/cluster/tariff_response.sbatch",
    "research-20260930/learning-campaign/PROTOCOL_TARIFF_RESPONSE_TRANSFER.md",
)))
INPUT_FILES = (
    ARCHIVE / "frozen.json", ARCHIVE / "catalog.jsonl",
    ARCHIVE / "inference_receipt.json", ARCHIVE / "training_coverage.json",
    ARCHIVE / "learned/model.json", ARCHIVE / "learned/training_rows.json",
    OLD_MODEL,
)


def stages():
    return SOURCES + tuple(source + "_charge_" + variant
                           for variant in VARIANTS for source in SOURCES) + tuple(
                               "cold_" + variant for variant in VARIANTS)


def cells():
    sources = tuple((seed, source) for seed in PROFILE for source in SOURCES)
    targets = tuple((seed, stage) for seed in PROFILE for stage in stages()[2:])
    return sources + targets


def attempt(path):
    result = Path(path).resolve()
    if result != ATTEMPT.resolve():
        raise ValueError("Only the exclusive tariff-response attempt is allowed")
    return result


def case_for(seed):
    return prior.make_case(seed, profile=PROFILE)


def seed_for(name):
    return prior.seed_from_name(name, profile=PROFILE)


def folder(path, seed, stage):
    return Path(path) / case_for(seed).name / "state0" / stage


def target_market(case, variant):
    if variant not in VARIANTS:
        raise ValueError("Undeclared target tariff")
    if variant == "flat":
        prices = (41/150,)*30
    else:
        low = range(22, 26) if variant == "late" else range(10, 14)
        prices = tuple(.10 if period in low else .30 for period in range(30))
    return nh.Market(case.name + "-target-" + variant, prices, (1/900,)*30)


def market_for(case, stage):
    if stage in SOURCES:
        return prior.market(case, stage)
    variant = stage.rsplit("_", 1)[-1]
    return target_market(case, variant)


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def input_hashes():
    return {str(file.relative_to(ROOT)): base.sha(file) for file in INPUT_FILES}


def train_majority():
    """Use archived six TRAIN pairs only, with complete replay/lineage checks."""
    frozen = json.loads((ARCHIVE / "frozen.json").read_text())
    coverage = json.loads((ARCHIVE / "training_coverage.json").read_text())
    receipt = json.loads((ARCHIVE / "inference_receipt.json").read_text())
    model = crm.ResponseModel.from_dict(json.loads((ARCHIVE / "learned/model.json").read_text()))
    if (receipt.get("returncode") != 0 or not coverage.get("complete_six_pairs")
            or sorted(model.training_groups) != [f"learning_s{s}" for s in range(2022, 2028)]
            or frozen.get("protocol") != charge.PROTOCOL):
        raise ValueError("Archived charge-response training lineage incomplete")
    rows = [json.loads(line) for line in (ARCHIVE / "catalog.jsonl").read_text().splitlines()]
    winners = {}
    for seed in range(2022, 2028):
        group = f"learning_s{seed}"
        found = {}
        for source in SOURCES:
            matches = [row for row in rows if (row.get("base_group") == group
                       and row.get("row_id") == f"learning_s{seed}_n{charge.PROFILE[seed][1]:02d}/{source}_charge"
                       and row.get("split") == "train")]
            if len(matches) != 1 or not matches[0]["label"].get("feasible"):
                raise ValueError("Missing archived training charge label")
            found[source] = Fraction(matches[0]["label"]["objective_exact"])
        winners[group] = min(SOURCES, key=lambda source: (found[source], SOURCES.index(source)))
    counts = {source: sum(winner == source for winner in winners.values()) for source in SOURCES}
    majority = max(SOURCES, key=lambda source: (counts[source], -SOURCES.index(source)))
    return {"majority": majority, "counts": counts, "training_group_winners": winners,
            "source": "archived 2022–2027 training LP labels only"}


def design():
    if len(cells()) != 44 or any(seed in PROFILE for seed in RESERVED):
        raise ValueError("Tariff-transfer cell set changed")
    groups = {}
    for seed, (_, services) in PROFILE.items():
        case = case_for(seed)
        groups[case.name] = {"seed": seed, "split": "dev", "services": services,
            "base_group": f"learning_s{seed}", "case": asdict(case),
            "case_identity": case.identity(),
            "pure_witness_hash": nr.digest(prior.make_witness(case, profile=PROFILE)),
            "source_market_identities": {s: prior.market(case, s).identity() for s in SOURCES},
            "target_markets": {v: asdict(target_market(case, v)) for v in VARIANTS},
            "target_market_identities": {v: target_market(case, v).identity()
                                         for v in VARIANTS}}
    return {"generator": prior.GENERATOR, "profile": {str(s): n for s, (_, n) in PROFILE.items()},
        "groups": groups, "variants": list(VARIANTS),
        "tariff_mean": "41/150 nominal per period; b=1/900",
        "train_majority": train_majority(),
        "cell_order": [{"seed": seed, "stage": stage} for seed, stage in cells()],
        "declared_cells": 44, "independent_dev_groups": 4,
        "reserved_unmaterialized": list(RESERVED),
        "all_twelve_choices_before_target_outcomes": True,
        "frozen_response_policy": crm.POLICY, "frozen_old_prior_policy": edge.POLICY,
        "source_native_budget": asdict(prior.budget()),
        "fixed_charge_budget": asdict(charge.charge_budget()),
        "child_hard_seconds": CHILD_SECONDS, "inference_hard_seconds": INFERENCE_SECONDS,
        "controller_hard_seconds": CONTROLLER_SECONDS,
        "charging_objective": "linear target market.a; exact curved bill after replay",
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
        raise ValueError("Frozen tariff-transfer source/input/runtime/design changed")
    return spec


def _rows(path):
    file = Path(path) / "catalog.jsonl"
    return [json.loads(line) for line in file.read_text().splitlines()] if file.is_file() else []


def _row(path, seed, stage):
    expected = case_for(seed).name + "/" + stage
    found = [row for row in _rows(path) if row.get("row_id") == expected]
    if len(found) != 1:
        raise ValueError("Missing or duplicate catalog row: " + expected)
    return found[0]


def source_plan(path, seed, source):
    case = case_for(seed)
    row = _row(path, seed, source)
    label = row["label"]
    if (row.get("split") != "dev" or row.get("arm") != "source"
            or row.get("case_identity") != case.identity() or not label.get("feasible")):
        raise ValueError("No replayed same-case source plan")
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
        market = market_for(case, stage)
        group = spec["design"]["groups"][case.name]
        expected_market = (group["source_market_identities"][stage] if stage in SOURCES else
                           group["target_market_identities"][stage.rsplit("_", 1)[-1]])
        if case.identity() != group["case_identity"] or market.identity() != expected_market:
            raise ValueError("Frozen case or market identity changed")
        if stage not in SOURCES and not (target / "inference_receipt.json").is_file():
            raise ValueError("Target cell cannot start before all variant inference")
        if "_charge_" in stage:
            source = stage.split("_charge_", 1)[0]
            source_row, original = source_plan(target, seed, source)
            direct = crm.direct_cost(case, market, original)
            base.save_new(dest / "direct_rescore.json", {"case_identity": case.identity(),
                "market_identity": market.identity(), "source_plan_hash": source_row["label"]["plan_hash"],
                "objective_exact": str(direct)})
            selected = sorted({mid for vehicle in source_row["label"]["plan"]["vehicles"]
                               for mid in vehicle["movements"]})
            charge_started = time.monotonic()
            try:
                plan, replay, stats = rr._solve_fixed_charge(case, market, selected,
                                                            charge.charge_budget(), record=_events(dest))
                charge_seconds = time.monotonic()-charge_started
                replay_started = time.monotonic()
                checked = nr.replay_native(case, plan)
                pf._checked_pricing_start(case, plan)
                if checked != replay or {mid for v in plan["vehicles"] for mid in v["movements"]} != set(selected):
                    raise ValueError("Fixed-source route or independent replay changed")
                exact = crm.direct_cost(case, market, checked)
                base.save_new(dest / "fixed_charge.json", {"status": "replayed",
                    "case_identity": case.identity(), "market_identity": market.identity(),
                    "source_plan_hash": source_row["label"]["plan_hash"],
                    "selected_movements": selected, "plan": plan, "plan_hash": nr.digest(plan),
                    "replay": checked, "objective_exact": str(exact), "native_stats": stats,
                    "charge_wall_seconds": charge_seconds,
                    "independent_replay_wall_seconds": time.monotonic()-replay_started,
                    "target_optimality": "unknown; LP minimizes linear target tariff only"})
                result = {"status": "replayed", "direct_exact": str(direct),
                    "post_lp_exact": str(exact), "native_status": stats.get("status"),
                    "elapsed_seconds": time.monotonic()-started}
            except Exception as exc:
                telemetry = getattr(exc, "telemetry", {})
                base.save_new(dest / "fixed_charge_failure.json", {"type": type(exc).__name__,
                    "message": str(exc), "traceback": traceback.format_exc(),
                    "native_stats": telemetry.get("native_stats", locals().get("stats")),
                    "charge_wall_seconds": time.monotonic()-charge_started})
                result = {"status": "no_replayed_lp_plan", "direct_exact": str(direct),
                    "post_lp_exact": None,
                    "native_status": (telemetry.get("native_stats") or {}).get("status"),
                    "elapsed_seconds": time.monotonic()-started}
            base.save_new(dest / "result.json", result)
        else:
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
    market = market_for(case, stage)
    dest = folder(path, seed, stage)
    receipt = json.loads((dest / "receipt.json").read_text())
    exception = dest / "exception.json"
    status = "hard_timeout" if receipt.get("hard_timeout") else (
             "failed" if receipt.get("returncode") != 0 else "returned")
    result = {"status": status, "receipt": receipt,
        "failure": json.loads(exception.read_text()) if exception.is_file() else None,
        "feasible": False, "optimality": "unknown", "plan": None, "plan_hash": None,
        "ops_cost": None, "load": None, "objective_exact": None,
        "lower_exact": None, "upper_exact": None,
        "elapsed_seconds": receipt.get("elapsed_seconds"), "native_status": None}
    if "_charge_" in stage:
        source = stage.split("_charge_", 1)[0]
        evidence_file = dest / "fixed_charge.json"
        failure_file = dest / "fixed_charge_failure.json"
        if failure_file.is_file():
            result["failure"] = json.loads(failure_file.read_text())
        if evidence_file.is_file():
            evidence = json.loads(evidence_file.read_text())
            plan = evidence["plan"]
            replay = nr.replay_native(case, plan)
            source_row, _ = source_plan(path, seed, source)
            source_ids = {mid for v in source_row["label"]["plan"]["vehicles"]
                          for mid in v["movements"]}
            charged_ids = {mid for v in plan["vehicles"] for mid in v["movements"]}
            exact = str(crm.direct_cost(case, market, replay))
            if (evidence.get("status") != "replayed" or evidence.get("case_identity") != case.identity()
                    or evidence.get("market_identity") != market.identity()
                    or evidence.get("source_plan_hash") != source_row["label"]["plan_hash"]
                    or set(evidence.get("selected_movements", ())) != source_ids
                    or charged_ids != source_ids or evidence.get("plan_hash") != nr.digest(plan)
                    or evidence.get("replay") != replay or evidence.get("objective_exact") != exact):
                raise ValueError("Charged plan source/target/replay lineage changed")
            result.update(feasible=True, plan=plan, plan_hash=nr.digest(plan),
                ops_cost=replay["ops_cost"], load=replay["load"],
                objective_exact=exact, upper_exact=exact,
                source_plan_hash=source_row["label"]["plan_hash"],
                native_status=evidence["native_stats"].get("status"),
                charge_wall_seconds=evidence.get("charge_wall_seconds"),
                independent_replay_wall_seconds=evidence.get("independent_replay_wall_seconds"))
        return result
    raw_file = dest / "raw_result.json"
    if not raw_file.is_file():
        return result
    raw = json.loads(raw_file.read_text())["result"]
    result["native_status"] = raw.get("status")
    assessment_file = dest / "result.json"
    assessment = (json.loads(assessment_file.read_text()).get("assessment", {})
                  if assessment_file.is_file() else {})
    result["bounds_replay"] = {
        "global_certificate_replayed": assessment.get("global_certificate_replayed") is True,
        "mixture_replayed": assessment.get("mixture_replayed") is True}
    cert, mix = raw.get("lower_certificate"), raw.get("mixture")
    if cert and cert.get("lower_exact") is not None:
        key = "lower_exact" if result["bounds_replay"]["global_certificate_replayed"] else \
              "unverified_native_lower_exact"
        result[key] = cert["lower_exact"]
    if mix and mix.get("objective_exact") is not None:
        key = "native_mixture_upper_exact" if result["bounds_replay"]["mixture_replayed"] else \
              "unverified_native_mixture_upper_exact"
        result[key] = mix["objective_exact"]
    candidates = []
    for column in raw.get("columns", []):
        replay = nh.replay_column(case, column, compact.EXTRACTION_POLICY)
        candidates.append((crm.direct_cost(case, market, replay), column["key"], column, replay))
    if candidates:
        exact, _, column, replay = min(candidates, key=lambda item: (item[0], item[1]))
        result.update(feasible=True, plan=column["plan"], plan_hash=nr.digest(column["plan"]),
                      ops_cost=replay["ops_cost"], load=replay["load"],
                      objective_exact=str(exact), upper_exact=str(exact), column_key=column["key"])
    return result


def catalog_row(path, seed, stage):
    case = case_for(seed)
    market = market_for(case, stage)
    variant = None if stage in SOURCES else stage.rsplit("_", 1)[-1]
    return {"row_id": case.name + "/" + stage, "base_group": f"learning_s{seed}",
        "split": "dev", "case": asdict(case), "case_identity": case.identity(),
        "market": asdict(market), "market_identity": market.identity(),
        "market_name": stage if stage in SOURCES else "target_" + variant,
        "market_role": "source" if stage in SOURCES else "target",
        "tariff_variant": variant, "market_prices": list(market.a),
        "market_quadratic": list(market.b),
        "arm": "source" if stage in SOURCES else stage, "label": label(path, seed, stage)}


def choices_for(path, seed, variant, *, model=None, old=None, majority):
    case = case_for(seed)
    target = target_market(case, variant)
    candidates = []
    for source in SOURCES:
        try:
            row, replay = source_plan(path, seed, source)
        except ValueError:
            continue
        candidates.append({"source": source, "row_id": row["row_id"],
            "plan_hash": row["label"]["plan_hash"], "plan": row["label"]["plan"],
            "replay": replay, "direct_exact": str(crm.direct_cost(case, target, replay)),
            "features": crm.features(case, target, prior.market(case, source), replay, source)})
    if not candidates:
        return {"case_identity": case.identity(), "market_identity": target.identity(),
            "variant": variant, "choices": {}, "candidates": [],
            "failure": "no replayed source fleet"}
    eligible = {candidate["source"] for candidate in candidates}
    def pick(fn):
        return min(candidates, key=lambda c: (fn(c), SOURCES.index(c["source"]))) ["source"]
    choices = {"always_source0": "source0" if "source0" in eligible else None,
        "always_source1": "source1" if "source1" in eligible else None,
        "train_majority": majority if majority in eligible else None,
        "cheapest_direct": pick(lambda c: Fraction(c["direct_exact"])),
        "nearest_price": pick(lambda c: sum((float(a)-float(b))**2 for a, b in zip(
            target.a, prior.market(case, c["source"]).a)))}
    projection = None
    if old is not None:
        if f"learning_s{seed}" in old.training_groups:
            raise ValueError("Frozen old EdgePrior trained on evaluation group")
        selected, projection = charge.old_prior_choice(case, target, candidates, old)
        choices["frozen_edge_prior"] = selected["source"]
    if model is not None:
        if f"learning_s{seed}" in model.training_groups:
            raise ValueError("Frozen charge-response model trained on evaluation group")
        for candidate in candidates:
            candidate["predicted_post_lp_cost"] = model.predict_cost(
                case, target, prior.market(case, candidate["source"]),
                candidate["replay"], candidate["source"])
        choices["charge_response_ridge"] = pick(lambda c: c["predicted_post_lp_cost"])
    return {"case_identity": case.identity(), "market_identity": target.identity(),
        "variant": variant, "choices": choices, "old_prior_projection": projection,
        "candidates": [{k: v for k, v in candidate.items() if k not in ("plan", "replay")}
                       for candidate in candidates], "failure": None}


def _expected_source_rows():
    return {case_for(seed).name + "/" + source for seed in PROFILE for source in SOURCES}


def infer_worker(path):
    target = attempt(path)
    frozen(target)
    if not (target / "inference_launch.json").is_file():
        raise ValueError("Missing prospective inference launch")
    rows = _rows(target)
    if len(rows) != 8 or {row["row_id"] for row in rows} != _expected_source_rows():
        raise ValueError("Inference catalog must have exactly eight source rows, no target outcomes")
    model = crm.ResponseModel.from_dict(json.loads((ARCHIVE / "learned/model.json").read_text()))
    old = edge.EdgePrior.from_dict(json.loads(OLD_MODEL.read_text()))
    majority = train_majority()["majority"]
    proposals = {case_for(seed).name: {variant: choices_for(target, seed, variant,
        model=model, old=old, majority=majority) for variant in VARIANTS} for seed in PROFILE}
    output = target / "learned"
    output.mkdir(parents=False, exist_ok=False)
    base.save_new(output / "proposals.json", proposals)
    return 0


def infer_before_targets(path):
    target = Path(path)
    receipt_file = target / "inference_receipt.json"
    if receipt_file.is_file():
        return json.loads(receipt_file.read_text())
    rows = _rows(target)
    if len(rows) != 8 or {row["row_id"] for row in rows} != _expected_source_rows():
        raise ValueError("All eight source rows must precede frozen inference")
    if any(folder(target, seed, stage).exists() for seed in PROFILE for stage in stages()[2:]):
        raise ValueError("Target launch preceded all-variant inference")
    baseline_file = target / "baseline_choices.json"
    baseline_receipt = target / "baseline_choices_receipt.json"
    if not baseline_file.is_file() and not (target / "inference_launch.json").exists():
        started = time.monotonic()
        old = edge.EdgePrior.from_dict(json.loads(OLD_MODEL.read_text()))
        majority = train_majority()["majority"]
        baseline = {case_for(seed).name: {variant: choices_for(target, seed, variant,
            old=old, majority=majority) for variant in VARIANTS} for seed in PROFILE}
        base.save_new(baseline_file, baseline)
        base.save_new(baseline_receipt, {"before_all_target_cells": True,
            "choices_sha256": base.sha(baseline_file),
            "elapsed_seconds": time.monotonic()-started})
    inputs = {"catalog_sha256": base.sha(target / "catalog.jsonl"),
        "baseline_choices_sha256": base.sha(baseline_file) if baseline_file.is_file() else None,
        "frozen_response_model_sha256": base.sha(ARCHIVE / "learned/model.json"),
        "old_edge_prior_sha256": base.sha(OLD_MODEL)}
    if (target / "inference_launch.json").exists() or (target / "learned").exists():
        receipt = {"status": "interrupted_unreceipted", "returncode": None,
            "before_all_target_cells": True, "inputs": inputs,
            "elapsed_seconds": None, "output_hashes": {}}
        base.save_new(receipt_file, receipt)
        return receipt
    command = [sys.executable, "-m", "experiments.tariff_response_campaign", "infer",
               "--attempt", str(target)]
    base.save_new(target / "inference_launch.json", {"command": command,
        "hard_seconds": INFERENCE_SECONDS, "inputs": inputs})
    started = time.monotonic()
    try:
        with (target / "inference_stdout.txt").open("xb") as stdout, \
             (target / "inference_stderr.txt").open("xb") as stderr:
            completed = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                       timeout=INFERENCE_SECONDS, check=False)
        rc, failure = completed.returncode, None
    except subprocess.TimeoutExpired:
        rc, failure = 124, "hard_timeout"
    except Exception as exc:
        rc, failure = 1, repr(exc)
    proposals = target / "learned/proposals.json"
    receipt = {"status": "completed" if rc == 0 else "failed", "returncode": rc,
        "failure": failure, "before_all_target_cells": True,
        "inputs": inputs, "runtime": sizing.software_runtime(),
        "elapsed_seconds": time.monotonic()-started,
        "output_hashes": {"proposals.json": base.sha(proposals)} if proposals.is_file() else {}}
    base.save_new(receipt_file, receipt)
    return receipt


def prospective_choices(path, seed, variant):
    target = Path(path)
    receipt = json.loads((target / "inference_receipt.json").read_text())
    proposals = target / "learned/proposals.json"
    if (receipt.get("returncode") == 0 and receipt.get("before_all_target_cells") is True
            and proposals.is_file()
            and receipt.get("output_hashes", {}).get("proposals.json") == base.sha(proposals)):
        choice = json.loads(proposals.read_text())[case_for(seed).name][variant]
        model = crm.ResponseModel.from_dict(json.loads((ARCHIVE / "learned/model.json").read_text()))
        old = edge.EdgePrior.from_dict(json.loads(OLD_MODEL.read_text()))
        expected = choices_for(target, seed, variant, model=model, old=old,
                               majority=train_majority()["majority"])
        if base.canonical(choice) != base.canonical(expected):
            raise ValueError("Prospectively frozen variant choice changed")
        return choice
    baseline = target / "baseline_choices.json"
    if (baseline.is_file() and receipt.get("inputs", {}).get("baseline_choices_sha256")
            == base.sha(baseline)):
        return json.loads(baseline.read_text())[case_for(seed).name][variant]
    return {"case_identity": case_for(seed).identity(),
        "market_identity": target_market(case_for(seed), variant).identity(),
        "variant": variant, "choices": {}, "candidates": [],
        "failure": "prospective inference and baseline unavailable"}


def append_catalog(path, row):
    prior.append_catalog(path, row)


def summary(path):
    target = Path(path)
    groups = {}
    methods = ("always_source0", "always_source1", "train_majority",
               "cheapest_direct", "nearest_price", "frozen_edge_prior", "charge_response_ridge")
    for seed in PROFILE:
        case = case_for(seed)
        source = {s: _row(target, seed, s)["label"] for s in SOURCES}
        acquisition = (sum(source[s]["elapsed_seconds"] for s in SOURCES)
            if all(source[s]["elapsed_seconds"] is not None for s in SOURCES) else None)
        variants = {}
        for variant in VARIANTS:
            labels = {s: _row(target, seed, s + "_charge_" + variant)["label"] for s in SOURCES}
            cold = _row(target, seed, "cold_" + variant)["label"]
            choice = prospective_choices(target, seed, variant)
            feasible = [(Fraction(labels[s]["objective_exact"]), s) for s in SOURCES
                        if labels[s]["feasible"]]
            best = min(feasible) if feasible else None
            method_rows = {}
            for method in methods:
                selected = choice["choices"].get(method)
                selected_label = labels[selected] if selected is not None else None
                objective = selected_label["objective_exact"] if selected_label else None
                method_rows[method] = {"source": selected,
                    "feasible": bool(selected_label and selected_label["feasible"]),
                    "post_lp_objective_exact": objective,
                    "candidate_pool_excess_exact": (str(Fraction(objective)-best[0])
                        if objective is not None and len(feasible) == 2 else None),
                    "one_lp_paid_seconds": selected_label["elapsed_seconds"] if selected_label else None,
                    "source_acquisition_plus_one_lp_seconds": (
                        acquisition + selected_label["elapsed_seconds"]
                        if acquisition is not None and selected_label is not None
                        and selected_label["elapsed_seconds"] is not None else None)}
            two_lp = (sum(labels[s]["elapsed_seconds"] for s in SOURCES)
                if all(labels[s]["elapsed_seconds"] is not None for s in SOURCES) else None)
            variants[variant] = {"prospective_choices": choice["choices"],
                "choice_failure": choice["failure"],
                "source_lp_labels": {s: {key: labels[s].get(key) for key in (
                    "status", "feasible", "objective_exact", "elapsed_seconds", "native_status")}
                    for s in SOURCES},
                "methods": method_rows,
                "paid_two_lp_best": {"source": best[1], "objective_exact": str(best[0]),
                    "two_lp_paid_seconds": two_lp} if best else None,
                "cold": {key: cold.get(key) for key in (
                    "status", "feasible", "objective_exact", "lower_exact", "upper_exact",
                    "elapsed_seconds", "native_status")}}
        switches = {method: len({variants[v]["prospective_choices"].get(method)
            for v in VARIANTS if variants[v]["prospective_choices"].get(method) is not None}) > 1
            for method in methods}
        paired_excess = {}
        for method in methods:
            values = [variants[v]["methods"][method]["candidate_pool_excess_exact"]
                      for v in VARIANTS]
            paired_excess[method] = (str(sum((Fraction(value) for value in values), Fraction(0))/3)
                                     if all(value is not None for value in values) else None)
        groups[case.name] = {"base_group": f"learning_s{seed}",
            "source_acquisition_seconds_once": acquisition,
            "source_labels": {s: {"status": source[s]["status"], "feasible": source[s]["feasible"],
                "elapsed_seconds": source[s]["elapsed_seconds"]} for s in SOURCES},
            "variants": variants, "choice_switch_across_tariffs": switches,
            "mean_paired_pool_excess_exact": paired_excess}
    return {"protocol": PROTOCOL, "declared_cells": len(cells()),
        "accounted_cells": len(_rows(target)), "independent_dev_groups": 4,
        "target_variants_per_group": 3, "groups": groups,
        "train_majority": train_majority(),
        "inference_receipt": json.loads((target / "inference_receipt.json").read_text()),
        "baseline_choices_receipt": json.loads((target / "baseline_choices_receipt.json").read_text())
            if (target / "baseline_choices_receipt.json").is_file() else None,
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
            raise ValueError("Another tariff-response controller holds this attempt") from exc
        if not (target / "controller_started.json").is_file():
            base.save_new(target / "controller_started.json", {"protocol": PROTOCOL,
                "utc": time.time()})
        for seed, stage in cells():
            if time.monotonic()-started > CONTROLLER_SECONDS-CHILD_SECONDS:
                raise TimeoutError("Tariff-response controller budget exhausted before next cell")
            if (seed, stage) == cells()[8]:
                infer_before_targets(target)
            dest = folder(target, seed, stage)
            if (dest / "receipt.json").is_file():
                append_catalog(target, catalog_row(target, seed, stage))
                continue
            if dest.exists():
                raise ValueError("Interrupted unreceipted cell preserved: " + str(dest))
            dest.mkdir(parents=True, exist_ok=False)
            command = [sys.executable, "-m", "experiments.tariff_response_campaign", "worker",
                       "--attempt", str(target), "--case", case_for(seed).name,
                       "--stage", stage]
            base.launch_child(target, case_for(seed).name, 0, stage, CHILD_SECONDS,
                              command=command)
            append_catalog(target, catalog_row(target, seed, stage))
        if not (target / "summary.json").is_file():
            base.save_new(target / "summary.json", summary(target))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "controller", "worker", "infer"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case")
    parser.add_argument("--stage", choices=stages())
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
