"""No-retry completion of never-launched cells after shard-0 preemption."""
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

from egglab import learned_proposals as edge
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from egglab import route_fixed_repair as rr
from experiments import budget_sizing_diagnostic as sizing
from experiments import charge_response_campaign as charge
from experiments import computational_benchmark as base
from experiments import learning_campaign_stage2 as prior
from experiments import physical_learning_campaign as original

ROOT = base.ROOT
PARENT = ROOT / "result/physical_learning/20260930-shard00-attempt1"
ATTEMPT = ROOT / "result/physical_learning/20260930-shard00-continuation-attempt1"
ACCOUNTING = ROOT / "research-20260930/learning-campaign/ACCOUNTING_703461.json"
PARENT_FILE_MANIFEST = ROOT / "research-20260930/learning-campaign/RESULT_MANIFEST_PHYSICAL_SHARD00_PREEMPTED.json"
PROTOCOL = "egg-physical-shard00-never-launched-continuation-20260930-v1"
INTERRUPTED = (10004, "source0_charge_late")
CHILD_SECONDS = 100
CONTROLLER_SECONDS = 2500
SOURCE_FILES = (
    "src/experiments/physical_learning_continuation.py",
    "src/cluster/physical_learning_continuation.sbatch",
    "src/tests/test_physical_learning_continuation.py",
    "research-20260930/learning-campaign/PROTOCOL_PHYSICAL_CONTINUATION.md",
    "src/egglab/physical_learning_cases.py", "src/experiments/physical_learning_campaign.py",
    "src/egglab/native_recharge.py", "src/egglab/native_pathflow.py",
    "src/egglab/native_hull.py", "src/egglab/route_fixed_repair.py",
    "src/egglab/learned_proposals.py",
    "src/experiments/charge_response_campaign.py",
    "src/experiments/learning_campaign_stage2.py",
    "src/experiments/computational_benchmark.py",
    "src/experiments/budget_sizing_diagnostic.py", "src/cluster/unicorn_env.sh",
)


def attempt(path=None):
    target = ATTEMPT if path is None else Path(path)
    if target.resolve() != ATTEMPT.resolve():
        raise ValueError("Only the exclusive shard-0 continuation attempt is allowed")
    return target.resolve()


def _read_json(path):
    return json.loads(Path(path).read_text())


def _rows(path):
    return [json.loads(line) for line in (Path(path) / "catalog.jsonl").read_text().splitlines()]


def _name_by_id(manifest):
    return {group["assignment"]["base_id"]: name
            for name, group in manifest["groups"].items()}


def folder(path, base_id, stage, names=None):
    names = _name_by_id(_read_json(PARENT / "manifest.json")) if names is None else names
    return Path(path) / names[base_id] / "state0" / stage


def parent_partition(*, full_file_check=False):
    manifest = _read_json(PARENT / "manifest.json")
    frozen = _read_json(PARENT / "frozen.json")
    accounting = _read_json(ACCOUNTING)
    inventory = _read_json(PARENT_FILE_MANIFEST)
    if (manifest.get("generator") != physical.GENERATOR or manifest.get("shard") != 0
            or manifest.get("selected_base_ids") != list(physical.shard_ids(0))
            or frozen.get("manifest_sha256") != base.sha(PARENT / "manifest.json")
            or frozen.get("protocol") != original.PROTOCOL
            or accounting.get("job_id") != "703461" or accounting.get("state") != "PREEMPTED"
            or accounting.get("wrapper_receipt_present") is not False
            or accounting.get("summary_present") is not False
            or inventory.get("job_id") != "703461"
            or inventory.get("attempt_relative") != str(PARENT.relative_to(ROOT))):
        raise ValueError("Parent preemption/source manifest lineage changed")
    if (PARENT / "summary.json").exists() or list(PARENT.parent.glob(
            PARENT.name + ".slurm_wrapper_receipt.*.json")):
        raise ValueError("Parent is no longer the archived incomplete attempt")
    names = _name_by_id(manifest)
    if len(names) != 8:
        raise ValueError("Parent has missing or duplicate base groups")
    rows = _rows(PARENT)
    expected = [(item["base_id"], item["stage"]) for item in manifest["cell_order"]]
    if expected != list(original.cells(0)) or len(rows) != 40:
        raise ValueError("Parent schedule/catalog length changed")
    ids = [row["row_id"] for row in rows]
    if ids != [names[base_id] + "/" + stage for base_id, stage in expected[:40]]:
        raise ValueError("Parent catalog is not exact completed prefix")
    for base_id, stage in expected[:40]:
        dest = folder(PARENT, base_id, stage, names)
        if not (dest / "launch.json").is_file() or not (dest / "receipt.json").is_file():
            raise ValueError("Completed parent prefix lacks launch/receipt")
    interrupted = folder(PARENT, *INTERRUPTED, names)
    if (expected[40] != INTERRUPTED or not (interrupted / "launch.json").is_file()
            or (interrupted / "receipt.json").exists()):
        raise ValueError("Interrupted cell is not precisely an unreceipted launch")
    for base_id, stage in expected[41:]:
        if folder(PARENT, base_id, stage, names).exists():
            raise ValueError("Prospective continuation cell was already launched by parent")
    if (accounting.get("catalog_rows") != 40 or accounting.get("receipted_cells") != 40
            or accounting.get("launched_cells") != 41
            or accounting.get("never_launched_cells") != 23
            or accounting.get("interrupted_unreceipted_cells") != [
                names[INTERRUPTED[0]] + "/state0/" + INTERRUPTED[1]]):
        raise ValueError("External accounting contradicts parent partition")
    if full_file_check:
        for item in inventory["files"]:
            if not item["path"].startswith(str(PARENT.relative_to(ROOT)) + "/"):
                continue  # External Slurm diagnostics are archived separately.
            file = ROOT / item["path"]
            if not file.is_file() or base.sha(file) != item["sha256"]:
                raise ValueError("Collected parent file inventory changed: " + item["path"])
    return manifest, frozen, rows, names


def parent_inputs():
    files = [PARENT / name for name in ("manifest.json", "frozen.json", "catalog.jsonl")]
    files.extend((ACCOUNTING, PARENT_FILE_MANIFEST))
    manifest = _read_json(PARENT / "manifest.json")
    names = _name_by_id(manifest)
    for base_id, stage in original.cells(0)[:40]:
        dest = folder(PARENT, base_id, stage, names)
        files.extend((dest / "launch.json", dest / "receipt.json"))
        if stage in original.SOURCES:
            files.extend((dest / "raw_result.json", dest / "result.json"))
    files.append(folder(PARENT, *INTERRUPTED, names) / "launch.json")
    return {str(file.relative_to(ROOT)): base.sha(file) for file in files}


def manifest():
    parent, frozen, _, names = parent_partition(full_file_check=True)
    remaining = original.cells(0)[41:]
    return {"protocol": PROTOCOL, "parent_attempt": str(PARENT.relative_to(ROOT)),
        "parent_source_commit": frozen["source_commit"],
        "parent_manifest_sha256": base.sha(PARENT / "manifest.json"),
        "parent_catalog_sha256": base.sha(PARENT / "catalog.jsonl"),
        "parent_accounting_sha256": base.sha(ACCOUNTING),
        "parent_file_inventory_sha256": base.sha(PARENT_FILE_MANIFEST),
        "parent_completed_cell_ids": [names[s] + "/" + stage
                                      for s, stage in original.cells(0)[:40]],
        "interrupted": {"row_id": names[INTERRUPTED[0]] + "/" + INTERRUPTED[1],
            "base_id": INTERRUPTED[0], "stage": INTERRUPTED[1],
            "status": "preempted_unreceipted_censored",
            "launch_sha256": base.sha(folder(PARENT, *INTERRUPTED, names) / "launch.json"),
            "receipt": None, "feasible": None, "objective_exact": None,
            "elapsed_child_seconds": None,
            "parent_slurm_elapsed_seconds": _read_json(ACCOUNTING)["elapsed_seconds"]},
        "remaining_cells": [{"base_id": s, "stage": stage, "row_id": names[s] + "/" + stage}
                            for s, stage in remaining],
        "declared_new_cells": 23, "child_seconds": CHILD_SECONDS,
        "controller_seconds": CONTROLLER_SECONDS,
        "fixed_charge_budget": asdict(charge.charge_budget()),
        "train_only": True, "no_parent_mutation": True, "no_retry_of_interrupted": True,
        "no_model_fit": True, "parent_input_hashes": parent_inputs()}


def source_plan(base_id, source):
    parent_manifest, _, rows, names = parent_partition()
    name = names[base_id]
    group = parent_manifest["groups"][name]
    case = edge.case_from_dict(group["case"])
    matched = [row for row in rows if row["row_id"] == name + "/" + source]
    if len(matched) != 1 or not matched[0]["label"].get("feasible"):
        raise ValueError("Parent source plan is missing or not replayed")
    row = matched[0]
    plan = row["label"]["plan"]
    replay = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    if (row["case_identity"] != case.identity()
            or row["label"]["plan_hash"] != nr.digest(plan)
            or row["label"]["load"] != replay["load"]
            or row["label"]["ops_cost"] != replay["ops_cost"]):
        raise ValueError("Parent source physical replay/hash differs")
    return case, row, replay


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def freeze(path=None):
    target = attempt(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked continuation execution source is not clean")
    design = manifest()
    target.mkdir(parents=True, exist_ok=False)
    base.save_new(target / "manifest.json", design)
    base.save_new(target / "frozen.json", {"protocol": PROTOCOL,
        "source_commit": commit, "source_hashes": source_hashes(),
        "manifest_sha256": base.sha(target / "manifest.json"),
        "runtime": sizing.software_runtime(), "native_probe": sizing.native_probe()})


def frozen(path=None):
    target = attempt(path)
    parent_partition(full_file_check=True)
    spec = _read_json(target / "frozen.json")
    design = _read_json(target / "manifest.json")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if (spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit
            or spec.get("source_hashes") != source_hashes()
            or spec.get("manifest_sha256") != base.sha(target / "manifest.json")
            or design.get("parent_input_hashes") != parent_inputs()
            or not sizing.runtime_compatible(spec.get("runtime"), sizing.software_runtime())
            or spec.get("native_probe") != sizing.native_probe()):
        raise ValueError("Frozen continuation source/runtime/parent inputs changed")
    return design


def _events(dest):
    def record(event):
        with (dest / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
            stream.flush(); os.fsync(stream.fileno())
    return record


def worker(path, base_id, stage):
    target = attempt(path)
    design = frozen(target)
    selected = {(row["base_id"], row["stage"]) for row in design["remaining_cells"]}
    if (base_id, stage) not in selected:
        raise ValueError("Only never-launched parent cells may enter continuation")
    name = next(row["row_id"].rsplit("/", 1)[0] for row in design["remaining_cells"]
                if (row["base_id"], row["stage"]) == (base_id, stage))
    dest = target / name / "state0" / stage
    started = time.monotonic()
    try:
        if not (dest / "launch.json").is_file():
            raise ValueError("Missing continuation launch receipt")
        source = stage.split("_charge_", 1)[0]
        tariff = stage.rsplit("_", 1)[-1]
        case, source_row, replay = source_plan(base_id, source)
        market = physical.market(case, tariff)
        parent_group = _read_json(PARENT / "manifest.json")["groups"][name]
        if (case.identity() != parent_group["case_identity"]
                or market.identity() != parent_group["market_identities"][tariff]):
            raise ValueError("Frozen parent case/market changed")
        direct = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
        base.save_new(dest / "direct_rescore.json", {"source_row_id": source_row["row_id"],
            "source_plan_hash": source_row["label"]["plan_hash"],
            "case_identity": case.identity(), "market_identity": market.identity(),
            "objective_exact": str(direct)})
        movement_ids = sorted({mid for vehicle in source_row["label"]["plan"]["vehicles"]
                               for mid in vehicle["movements"]})
        charge_started = time.monotonic()
        try:
            plan, returned, stats = rr._solve_fixed_charge(case, market, movement_ids,
                                                           charge.charge_budget(), record=_events(dest))
            charge_seconds = time.monotonic()-charge_started
            replay_started = time.monotonic()
            checked = nr.replay_native(case, plan)
            pf._checked_pricing_start(case, plan)
            if (checked != returned or {mid for vehicle in plan["vehicles"]
                    for mid in vehicle["movements"]} != set(movement_ids)):
                raise ValueError("Continuation fixed-route replay/topology changed")
            exact = Fraction(checked["ops_cost"]) + nh.supply(market, checked["load"])
            base.save_new(dest / "fixed_charge.json", {"status": "replayed",
                "case_identity": case.identity(), "market_identity": market.identity(),
                "source_plan_hash": source_row["label"]["plan_hash"],
                "selected_movements": movement_ids, "plan": plan, "plan_hash": nr.digest(plan),
                "replay": checked, "objective_exact": str(exact), "native_stats": stats,
                "charge_wall_seconds": charge_seconds,
                "independent_replay_wall_seconds": time.monotonic()-replay_started,
                "target_optimality": "unknown; LP optimizes linear tariff only"})
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
        return 0
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "elapsed_seconds": time.monotonic()-started})
        return 2


def label(path, base_id, stage):
    target = Path(path)
    design = _read_json(target / "manifest.json")
    entry = next(row for row in design["remaining_cells"]
                 if (row["base_id"], row["stage"]) == (base_id, stage))
    name = entry["row_id"].rsplit("/", 1)[0]
    dest = target / name / "state0" / stage
    receipt = _read_json(dest / "receipt.json")
    status = "hard_timeout" if receipt.get("hard_timeout") else (
        "failed" if receipt.get("returncode") != 0 else "returned")
    failure_file = dest / "fixed_charge_failure.json"
    exception = dest / "exception.json"
    result = {"status": status, "receipt": receipt,
        "failure": (_read_json(failure_file) if failure_file.is_file() else
                    _read_json(exception) if exception.is_file() else None),
        "feasible": False, "optimality": "unknown", "plan": None, "plan_hash": None,
        "ops_cost": None, "load": None, "objective_exact": None,
        "lower_exact": None, "upper_exact": None,
        "elapsed_seconds": receipt.get("elapsed_seconds"), "native_status": None}
    evidence_file = dest / "fixed_charge.json"
    if not evidence_file.is_file():
        return result
    evidence = _read_json(evidence_file)
    source = stage.split("_charge_", 1)[0]
    tariff = stage.rsplit("_", 1)[-1]
    case, source_row, _ = source_plan(base_id, source)
    market = physical.market(case, tariff)
    plan = evidence["plan"]
    replay = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    source_ids = {mid for v in source_row["label"]["plan"]["vehicles"]
                  for mid in v["movements"]}
    exact = str(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
    if (evidence.get("status") != "replayed" or evidence.get("case_identity") != case.identity()
            or evidence.get("market_identity") != market.identity()
            or evidence.get("source_plan_hash") != source_row["label"]["plan_hash"]
            or set(evidence.get("selected_movements", ())) != source_ids
            or {mid for v in plan["vehicles"] for mid in v["movements"]} != source_ids
            or evidence.get("plan_hash") != nr.digest(plan) or evidence.get("replay") != replay
            or evidence.get("objective_exact") != exact):
        raise ValueError("Continuation plan/source/market replay lineage changed")
    result.update(feasible=True, plan=plan, plan_hash=nr.digest(plan),
        ops_cost=replay["ops_cost"], load=replay["load"], objective_exact=exact,
        upper_exact=exact, source_plan_hash=source_row["label"]["plan_hash"],
        native_status=evidence["native_stats"].get("status"),
        charge_wall_seconds=evidence.get("charge_wall_seconds"),
        independent_replay_wall_seconds=evidence.get("independent_replay_wall_seconds"))
    return result


def catalog_row(path, base_id, stage):
    design = _read_json(Path(path) / "manifest.json")
    entry = next(row for row in design["remaining_cells"]
                 if (row["base_id"], row["stage"]) == (base_id, stage))
    name = entry["row_id"].rsplit("/", 1)[0]
    parent_group = _read_json(PARENT / "manifest.json")["groups"][name]
    case = edge.case_from_dict(parent_group["case"])
    tariff = stage.rsplit("_", 1)[-1]
    market = physical.market(case, tariff)
    return {"row_id": entry["row_id"], "base_group": f"physical_v2_s{base_id}",
        "base_id": base_id, "split": "train", "physical_profile": parent_group["assignment"],
        "case": parent_group["case"], "case_identity": case.identity(),
        "market": asdict(market), "market_identity": market.identity(),
        "market_name": tariff, "market_role": "target", "market_prices": list(market.a),
        "market_quadratic": list(market.b), "arm": "fixed_source_charge",
        "source_market": stage.split("_charge_", 1)[0],
        "parent_source_plan_origin": str(PARENT.relative_to(ROOT)),
        "label": label(path, base_id, stage)}


def controller(path=None):
    target = attempt(path)
    design = frozen(target)
    started = time.monotonic()
    with (target / ".controller.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another continuation controller holds this attempt") from exc
        if not (target / "controller_started.json").is_file():
            base.save_new(target / "controller_started.json", {"protocol": PROTOCOL,
                "utc": time.time(), "parent_job_id": "703461"})
        for entry in design["remaining_cells"]:
            if time.monotonic()-started > CONTROLLER_SECONDS-CHILD_SECONDS:
                raise TimeoutError("Continuation controller cap exhausted before next cell")
            base_id, stage = entry["base_id"], entry["stage"]
            name = entry["row_id"].rsplit("/", 1)[0]
            dest = target / name / "state0" / stage
            if (dest / "receipt.json").is_file():
                prior.append_catalog(target, catalog_row(target, base_id, stage))
                continue
            if dest.exists():
                raise ValueError("Unreceipted continuation cell preserved without retry")
            dest.mkdir(parents=True, exist_ok=False)
            command = [sys.executable, "-m", "experiments.physical_learning_continuation", "worker",
                "--attempt", str(target), "--case", name, "--stage", stage]
            base.launch_child(target, name, 0, stage, CHILD_SECONDS, command=command)
            prior.append_catalog(target, catalog_row(target, base_id, stage))
        rows = _rows(target)
        if len(rows) != 23 or {r["row_id"] for r in rows} != {
                entry["row_id"] for entry in design["remaining_cells"]}:
            raise ValueError("Continuation catalog does not cover exactly 23 new cells")
        if not (target / "summary.json").is_file():
            base.save_new(target / "summary.json", {"protocol": PROTOCOL,
                "new_declared_cells": 23, "new_accounted_cells": 23,
                "new_feasible_cells": sum(bool(r["label"]["feasible"]) for r in rows),
                "parent_completed_cells": 40, "parent_interrupted_cells": 1,
                "interrupted": design["interrupted"],
                "combined_cell_accounting": 64,
                "scientific_admission": "pending independent composite review"})
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "controller", "worker"))
    parser.add_argument("--attempt", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--stage", choices=original.stages())
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(manifest(), sort_keys=True, indent=2)); return 0
    if args.mode == "freeze":
        freeze(args.attempt); return 0
    if args.mode == "preflight":
        frozen(args.attempt)
        print(json.dumps({"runtime": sizing.software_runtime(),
            "native_probe": sizing.native_probe()}, sort_keys=True)); return 0
    if args.mode == "controller":
        return controller(args.attempt)
    if not args.case or not args.stage:
        parser.error("worker requires --case and --stage")
    design = _read_json(attempt(args.attempt) / "manifest.json")
    match = [row for row in design["remaining_cells"]
             if row["row_id"] == args.case + "/" + args.stage]
    if len(match) != 1:
        raise ValueError("Worker case/stage is not a never-launched cell")
    return worker(args.attempt, match[0]["base_id"], args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
