"""Immutable eight-group physical-label shards; import never solves."""
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

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from egglab import route_fixed_repair as rr
from experiments import budget_sizing_diagnostic as sizing
from experiments import charge_response_campaign as charge
from experiments import computational_benchmark as base
from experiments import learning_campaign_stage2 as prior
from experiments import retrieval_comparison as retrieval

ROOT = base.ROOT
PROTOCOL = "egg-physical-learning-training-label-shard-20260930-v1"
SOURCES = ("source0", "source1")
TARIFFS = ("late", "day", "flat")
CHILD_SECONDS = 100
CONTROLLER_SECONDS = 6600
SOURCE_FILES = (
    "src/egglab/physical_learning_cases.py",
    "src/experiments/physical_learning_campaign.py",
    "src/cluster/physical_learning.sbatch",
    "src/tests/test_physical_learning_campaign.py",
    "research-20260930/learning-campaign/PROTOCOL_PHYSICAL_LEARNING.md",
    "research-20260930/learning-campaign/BATTERY_REGIMES_AND_TRAINING_DIRECTION.md",
    "src/egglab/native_recharge.py", "src/egglab/native_pathflow.py",
    "src/egglab/native_pathflow_hull.py", "src/egglab/native_hull.py",
    "src/egglab/route_fixed_repair.py", "src/egglab/restricted_qp_proposal.py",
    "src/experiments/learning_campaign_stage2.py",
    "src/experiments/charge_response_campaign.py",
    "src/experiments/retrieval_comparison.py",
    "src/experiments/computational_benchmark.py",
    "src/experiments/budget_sizing_diagnostic.py",
    "src/cluster/unicorn_env.sh",
)


def attempt(shard, path=None):
    physical.shard_ids(shard)
    expected = ROOT / f"result/physical_learning/20260930-shard{shard:02d}-attempt1"
    target = expected if path is None else Path(path)
    if target.resolve() != expected.resolve():
        raise ValueError("Only declared exclusive physical-learning shard attempt is allowed")
    return target.resolve()


def stages():
    return SOURCES + tuple(source + "_charge_" + tariff
                           for tariff in TARIFFS for source in SOURCES)


def cells(shard):
    ids = physical.shard_ids(shard)
    return tuple((base_id, source) for base_id in ids for source in SOURCES) + tuple(
        (base_id, source + "_charge_" + tariff)
        for base_id in ids for tariff in TARIFFS for source in SOURCES)


def folder(path, base_id, stage):
    return Path(path) / physical.make_case(base_id).name / "state0" / stage


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def manifest(shard):
    selected = physical.shard_ids(shard)
    if (len(selected) != 8 or len(cells(shard)) != 64
            or any(seed in physical.RESERVED_OLD for seed in selected)):
        raise ValueError("Shard or reserved IDs changed")
    groups = {physical.make_case(seed).name: physical.metadata(seed) for seed in selected}
    return {"generator": physical.GENERATOR, "shard": shard,
        "registry": {"train": [10000, 10127, 128], "dev": [20000, 20031, 32],
                     "test": [30000, 30031, 32]},
        "reserved_old_ids": list(physical.RESERVED_OLD),
        "materialized_split": "train", "selected_base_ids": list(selected),
        "battery_profiles": list(physical.PROFILES),
        "consumption_kwh_per_km": list(physical.CONSUMPTION_KWH_PER_KM),
        "kinematics": {"speed_kmh": physical.SPEED_KMH,
                       "direct_wait_idle_kw": physical.IDLE_KW,
                       "depot_dwell_idle_kw": physical.DEPOT_DWELL_IDLE_KW,
                       "deadhead_minutes": {"-".join(key): value
                           for key, value in physical.DEADHEAD_MINUTES.items()}},
        "groups": groups,
        "cell_order": [{"base_id": seed, "stage": stage} for seed, stage in cells(shard)],
        "declared_cells": 64, "native_source_cells": 16, "fixed_charge_cells": 48,
        "source_native_budget": asdict(prior.budget()),
        "target_fixed_charge_budget": asdict(charge.charge_budget()),
        "child_hard_seconds": CHILD_SECONDS,
        "controller_hard_seconds": CONTROLLER_SECONDS,
        "no_model_fit": True, "no_dev_or_test_materialization": True,
        "label_scope": "best replayed source incumbent and linear-tariff fixed-route charging outcomes; provisional"}


def freeze(shard, path=None):
    target = attempt(shard, path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    design = manifest(shard)  # Pure witness creation and independent replay.
    spec = {"protocol": PROTOCOL, "source_commit": commit,
        "source_hashes": source_hashes(), "runtime": sizing.software_runtime(),
        "native_probe": sizing.native_probe(),
        "scientific_admission": "pending independent result review"}
    target.mkdir(parents=True, exist_ok=False)
    base.save_new(target / "manifest.json", design)
    spec["manifest_sha256"] = base.sha(target / "manifest.json")
    base.save_new(target / "frozen.json", spec)
    return spec


def frozen(shard, path=None):
    target = attempt(shard, path)
    spec = json.loads((target / "frozen.json").read_text())
    saved_manifest = json.loads((target / "manifest.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if (spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit
            or spec.get("source_hashes") != source_hashes()
            or spec.get("manifest_sha256") != base.sha(target / "manifest.json")
            or base.canonical(saved_manifest) != base.canonical(manifest(shard))
            or not sizing.runtime_compatible(spec.get("runtime"), sizing.software_runtime())
            or spec.get("native_probe") != sizing.native_probe()):
        raise ValueError("Frozen shard source/runtime/manifest changed")
    return spec, saved_manifest


def _rows(path):
    file = Path(path) / "catalog.jsonl"
    return [json.loads(line) for line in file.read_text().splitlines()] if file.is_file() else []


def _row(path, base_id, stage):
    key = physical.make_case(base_id).name + "/" + stage
    matched = [row for row in _rows(path) if row.get("row_id") == key]
    if len(matched) != 1:
        raise ValueError("Missing or duplicate source catalog row: " + key)
    return matched[0]


def source_plan(path, base_id, source):
    case = physical.make_case(base_id)
    row = _row(path, base_id, source)
    label = row["label"]
    if (row.get("base_group") != f"physical_v2_s{base_id}" or row.get("split") != "train"
            or row.get("arm") != "source" or row.get("case_identity") != case.identity()
            or not label.get("feasible")):
        raise ValueError("No replayed same-base source plan")
    plan = label["plan"]
    replay = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    if (label.get("plan_hash") != nr.digest(plan) or label.get("ops_cost") != replay["ops_cost"]
            or label.get("load") != replay["load"]):
        raise ValueError("Saved source plan and independent replay differ")
    return row, replay


def _events(dest):
    def record(event):
        with (dest / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
            stream.flush(); os.fsync(stream.fileno())
    return record


def worker(shard, path, base_id, stage):
    target = attempt(shard, path)
    if (base_id, stage) not in cells(shard):
        raise ValueError("Case/stage is outside the selected training shard")
    dest = folder(target, base_id, stage)
    started = time.monotonic()
    try:
        _, design = frozen(shard, target)
        if not (dest / "launch.json").is_file():
            raise ValueError("Undeclared cell or missing launch receipt")
        case = physical.make_case(base_id)
        kind = stage if stage in SOURCES else stage.rsplit("_", 1)[-1]
        market = physical.market(case, kind)
        group = design["groups"][case.name]
        if (case.identity() != group["case_identity"]
                or market.identity() != group["market_identities"][kind]):
            raise ValueError("Frozen case/market identity changed")
        if stage in SOURCES:
            result = compact.certify(case, market, prior.budget(), arm="retained", state_index=0,
                                     record=_events(dest), **prior.POLICY)
            base.save_new(dest / "raw_result.json", {"result": result,
                "case": case.name, "stage": stage})
            assessment = retrieval.assess_hull(case, market, result)
            base.save_new(dest / "result.json", {"assessment": assessment,
                "elapsed_seconds": time.monotonic()-started})
        else:
            source = stage.split("_charge_", 1)[0]
            source_row, replay = source_plan(target, base_id, source)
            direct = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
            base.save_new(dest / "direct_rescore.json", {"source_row_id": source_row["row_id"],
                "source_plan_hash": source_row["label"]["plan_hash"],
                "case_identity": case.identity(), "market_identity": market.identity(),
                "objective_exact": str(direct)})
            selected = sorted({mid for vehicle in source_row["label"]["plan"]["vehicles"]
                               for mid in vehicle["movements"]})
            charging_started = time.monotonic()
            try:
                plan, returned_replay, stats = rr._solve_fixed_charge(case, market, selected,
                    charge.charge_budget(), record=_events(dest))
                charge_seconds = time.monotonic()-charging_started
                independent_started = time.monotonic()
                checked = nr.replay_native(case, plan)
                pf._checked_pricing_start(case, plan)
                if (checked != returned_replay or {mid for v in plan["vehicles"]
                        for mid in v["movements"]} != set(selected)):
                    raise ValueError("Fixed source movement set or replay changed")
                exact = Fraction(checked["ops_cost"]) + nh.supply(market, checked["load"])
                base.save_new(dest / "fixed_charge.json", {"status": "replayed",
                    "case_identity": case.identity(), "market_identity": market.identity(),
                    "source_plan_hash": source_row["label"]["plan_hash"],
                    "selected_movements": selected, "plan": plan, "plan_hash": nr.digest(plan),
                    "replay": checked, "objective_exact": str(exact), "native_stats": stats,
                    "charge_wall_seconds": charge_seconds,
                    "independent_replay_wall_seconds": time.monotonic()-independent_started,
                    "curved_cost_optimality": "unknown; LP minimized linear market.a"})
                result = {"status": "replayed", "direct_exact": str(direct),
                    "post_lp_exact": str(exact), "native_status": stats.get("status"),
                    "elapsed_seconds": time.monotonic()-started}
            except Exception as exc:
                telemetry = getattr(exc, "telemetry", {})
                base.save_new(dest / "fixed_charge_failure.json", {"type": type(exc).__name__,
                    "message": str(exc), "traceback": traceback.format_exc(),
                    "native_stats": telemetry.get("native_stats", locals().get("stats")),
                    "charge_wall_seconds": time.monotonic()-charging_started})
                result = {"status": "no_replayed_lp_plan", "direct_exact": str(direct),
                    "post_lp_exact": None,
                    "native_status": (telemetry.get("native_stats") or {}).get("status"),
                    "elapsed_seconds": time.monotonic()-started}
            base.save_new(dest / "result.json", result)
        return 0
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "elapsed_seconds": time.monotonic()-started})
        return 2


def label(path, base_id, stage):
    case = physical.make_case(base_id)
    market = physical.market(case, stage if stage in SOURCES else stage.rsplit("_", 1)[-1])
    dest = folder(path, base_id, stage)
    receipt = json.loads((dest / "receipt.json").read_text())
    exception = dest / "exception.json"
    result = {"status": "hard_timeout" if receipt.get("hard_timeout") else
              "failed" if receipt.get("returncode") != 0 else "returned",
        "receipt": receipt,
        "failure": json.loads(exception.read_text()) if exception.is_file() else None,
        "feasible": False, "optimality": "unknown", "plan": None, "plan_hash": None,
        "ops_cost": None, "load": None, "objective_exact": None,
        "lower_exact": None, "upper_exact": None,
        "elapsed_seconds": receipt.get("elapsed_seconds"), "native_status": None}
    if stage not in SOURCES:
        source = stage.split("_charge_", 1)[0]
        evidence_file = dest / "fixed_charge.json"
        failure_file = dest / "fixed_charge_failure.json"
        if failure_file.is_file():
            result["failure"] = json.loads(failure_file.read_text())
        if evidence_file.is_file():
            evidence = json.loads(evidence_file.read_text())
            plan = evidence["plan"]
            replay = nr.replay_native(case, plan)
            source_row, _ = source_plan(path, base_id, source)
            source_ids = {mid for v in source_row["label"]["plan"]["vehicles"]
                          for mid in v["movements"]}
            charged_ids = {mid for v in plan["vehicles"] for mid in v["movements"]}
            exact = str(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
            if (evidence.get("status") != "replayed"
                    or evidence.get("case_identity") != case.identity()
                    or evidence.get("market_identity") != market.identity()
                    or evidence.get("source_plan_hash") != source_row["label"]["plan_hash"]
                    or set(evidence.get("selected_movements", ())) != source_ids
                    or charged_ids != source_ids or evidence.get("plan_hash") != nr.digest(plan)
                    or evidence.get("replay") != replay or evidence.get("objective_exact") != exact):
                raise ValueError("Charged plan physical/source/market lineage changed")
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
        exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
        candidates.append((exact, column["key"], column, replay))
    if candidates:
        exact, _, column, replay = min(candidates, key=lambda item: (item[0], item[1]))
        result.update(feasible=True, plan=column["plan"], plan_hash=nr.digest(column["plan"]),
            ops_cost=replay["ops_cost"], load=replay["load"],
            objective_exact=str(exact), upper_exact=str(exact), column_key=column["key"])
    return result


def catalog_row(path, base_id, stage):
    case = physical.make_case(base_id)
    kind = stage if stage in SOURCES else stage.rsplit("_", 1)[-1]
    market = physical.market(case, kind)
    return {"row_id": case.name + "/" + stage,
        "base_group": f"physical_v2_s{base_id}", "base_id": base_id,
        "split": "train", "physical_profile": physical.assignment(base_id),
        "case": asdict(case), "case_identity": case.identity(),
        "market": asdict(market), "market_identity": market.identity(),
        "market_name": kind, "market_role": "source" if stage in SOURCES else "target",
        "market_prices": list(market.a), "market_quadratic": list(market.b),
        "arm": "source" if stage in SOURCES else "fixed_source_charge",
        "source_market": stage.split("_charge_", 1)[0] if stage not in SOURCES else None,
        "label": label(path, base_id, stage)}


def summary(path, shard):
    target = Path(path)
    groups = {}
    for base_id in physical.shard_ids(shard):
        case = physical.make_case(base_id)
        rows = {stage: _row(target, base_id, stage)["label"] for _, stage in cells(shard)
                if _ == base_id}
        groups[case.name] = {"base_id": base_id, "profile": physical.assignment(base_id)["profile"],
            "source_acquisition_seconds": (sum(rows[s]["elapsed_seconds"] for s in SOURCES)
                if all(rows[s]["elapsed_seconds"] is not None for s in SOURCES) else None),
            "cells": {stage: {key: row.get(key) for key in (
                "status", "feasible", "optimality", "objective_exact", "lower_exact",
                "upper_exact", "elapsed_seconds", "native_status", "plan_hash", "source_plan_hash")}
                for stage, row in rows.items()}}
    return {"protocol": PROTOCOL, "shard": shard, "declared_cells": 64,
        "accounted_cells": len(_rows(target)), "feasible_cells": sum(
            bool(row["label"]["feasible"]) for row in _rows(target)),
        "groups": groups, "no_model_fit": True, "dev_test_unmaterialized": True,
        "scientific_admission": "pending independent result review"}


def controller(shard, path=None):
    target = attempt(shard, path)
    frozen(shard, target)
    started = time.monotonic()
    with (target / ".controller.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another physical-label controller holds this shard") from exc
        if not (target / "controller_started.json").is_file():
            base.save_new(target / "controller_started.json", {"protocol": PROTOCOL,
                "shard": shard, "utc": time.time()})
        for base_id, stage in cells(shard):
            if time.monotonic()-started > CONTROLLER_SECONDS-CHILD_SECONDS:
                raise TimeoutError("Physical-label controller cap exhausted before next cell")
            dest = folder(target, base_id, stage)
            if (dest / "receipt.json").is_file():
                prior.append_catalog(target, catalog_row(target, base_id, stage))
                continue
            if dest.exists():
                raise ValueError("Interrupted unreceipted cell preserved: " + str(dest))
            dest.mkdir(parents=True, exist_ok=False)
            command = [sys.executable, "-m", "experiments.physical_learning_campaign", "worker",
                "--shard", str(shard), "--attempt", str(target),
                "--case", physical.make_case(base_id).name, "--stage", stage]
            base.launch_child(target, physical.make_case(base_id).name, 0, stage,
                              CHILD_SECONDS, command=command)
            prior.append_catalog(target, catalog_row(target, base_id, stage))
        if not (target / "summary.json").is_file():
            base.save_new(target / "summary.json", summary(target, shard))
    return 0


def base_id_from_name(name, shard):
    matches = [base_id for base_id in physical.shard_ids(shard)
               if physical.make_case(base_id).name == name]
    if len(matches) != 1:
        raise ValueError("Case is not in selected training shard")
    return matches[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "controller", "worker"))
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--attempt", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--stage", choices=stages())
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(manifest(args.shard), sort_keys=True, indent=2)); return 0
    if args.mode == "freeze":
        freeze(args.shard, args.attempt); return 0
    if args.mode == "preflight":
        frozen(args.shard, args.attempt)
        print(json.dumps({"runtime": sizing.software_runtime(),
            "native_probe": sizing.native_probe()}, sort_keys=True)); return 0
    if args.mode == "controller":
        return controller(args.shard, args.attempt)
    if not args.case or not args.stage:
        parser.error("worker requires --case and --stage")
    return worker(args.shard, args.attempt, base_id_from_name(args.case, args.shard), args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
