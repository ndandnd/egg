"""Fixed archived source fleets, target-tariff charging LP, exact target rescoring."""
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
from egglab import native_recharge as nr
from egglab import route_fixed_repair as rr
from experiments import computational_benchmark as base
from experiments import budget_sizing_diagnostic as sizing

ROOT = base.ROOT
ATTEMPT = ROOT / "result/learning_repair/20260930-fixed-source-charge-attempt1"
PROTOCOL = "egg-fixed-source-target-charging-development-20260930-v1"
ARCHIVES = {
    2016: ROOT / "result/learning_campaign/20260930-stage2-attempt1",
    2017: ROOT / "result/learning_campaign/20260930-stage2-attempt1",
    2018: ROOT / "result/learning_campaign/20260930-transfer-attempt1",
    2019: ROOT / "result/learning_campaign/20260930-transfer-attempt1",
}
NAMES = {2016: "learning_s2016_n20", 2017: "learning_s2017_n28",
         2018: "learning_s2018_n20", 2019: "learning_s2019_n28"}
SOURCES = ("source0", "source1")
CELLS = tuple((seed, source) for seed in ARCHIVES for source in SOURCES)
CHILD_SECONDS = 100
CONTROLLER_SECONDS = 1200
SOURCE_FILES = (
    "src/experiments/fixed_source_charge_campaign.py",
    "src/tests/test_fixed_source_charge_campaign.py",
    "src/cluster/fixed_source_charge.sbatch",
    "research-20260930/learning-campaign/PROTOCOL_FIXED_SOURCE_CHARGE.md",
    "src/egglab/route_fixed_repair.py", "src/egglab/native_pathflow.py",
    "src/egglab/native_recharge.py", "src/egglab/native_hull.py",
    "src/egglab/learned_proposals.py",
    "src/experiments/computational_benchmark.py",
    "src/experiments/budget_sizing_diagnostic.py",
    "src/cluster/unicorn_env.sh",
)


def attempt(path):
    value = Path(path).resolve()
    if value != ATTEMPT.resolve():
        raise ValueError("Only the exclusive fixed-source charging attempt is allowed")
    return value


def folder(path, seed, source):
    return Path(path) / NAMES[seed] / "state0" / (source + "_charge")


def budget():
    return nr.Budget(backend="GRB", threads=1, phase_seconds=45,
                     wall_seconds=55, max_rounds=1, epsilon=1e-4)


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def input_files():
    files = {}
    for label, archive in (("stage2", ARCHIVES[2016]), ("transfer", ARCHIVES[2018])):
        for name in ("frozen.json", "catalog.jsonl", "summary.json",
                     "learned/proposals.jsonl",
                     "learning_receipt.json" if label == "stage2" else "inference_receipt.json"):
            files[label + "/" + name] = archive / name
    for seed, source in CELLS:
        label = "stage2" if seed < 2018 else "transfer"
        name = NAMES[seed] + "/state0/" + source + "/receipt.json"
        files[label + "/" + name] = ARCHIVES[seed] / name
    return files


def input_hashes():
    return {name: base.sha(path) for name, path in input_files().items()}


def _catalog(archive):
    return [json.loads(line) for line in (archive / "catalog.jsonl").read_text().splitlines()]


def archived_case(seed):
    if seed not in ARCHIVES:
        raise ValueError("Undeclared or reserved timetable")
    archive = ARCHIVES[seed]
    frozen = json.loads((archive / "frozen.json").read_text())
    group = frozen["design"]["groups"].get(NAMES[seed])
    if group is None or group.get("split") != "dev":
        raise ValueError("Archived case is not a declared development group")
    case = lp.case_from_dict(group["case"])
    target = nh.Market(**group["markets"]["target"])
    if (case.name != NAMES[seed] or case.identity() != group["case_identity"]
            or target.identity() != group["market_identities"]["target"]):
        raise ValueError("Archived development case/target identity changed")
    return case, target


def archived_source(seed, source, case):
    if (seed, source) not in CELLS:
        raise ValueError("Undeclared archived source")
    matched = [row for row in _catalog(ARCHIVES[seed])
               if row.get("row_id") == NAMES[seed] + "/" + source]
    if len(matched) != 1:
        raise ValueError("Missing or duplicate archived source row")
    row = matched[0]
    label = row["label"]
    if (row.get("split") != "dev" or row.get("arm") != "source"
            or row.get("case_identity") != case.identity()
            or not label.get("feasible") or not label.get("plan")):
        raise ValueError("Archived source is not a replayed pre-target fleet")
    receipt_path = ARCHIVES[seed] / NAMES[seed] / "state0" / source / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if receipt != label.get("receipt"):
        raise ValueError("Archived source receipt differs from catalog label")
    plan = label["plan"]
    replay = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    if (nr.digest(plan) != label["plan_hash"] or replay["ops_cost"] != label["ops_cost"]
            or replay["load"] != label["load"]):
        raise ValueError("Archived source plan differs from replayed catalog label")
    return row, replay


def design():
    if len(CELLS) != 8 or len(set(CELLS)) != 8:
        raise ValueError("Fixed-source cell set changed")
    groups = {}
    for seed in ARCHIVES:
        case, target = archived_case(seed)
        groups[case.name] = {"seed": seed, "case_identity": case.identity(),
            "market_identity": target.identity(), "archive": str(ARCHIVES[seed]),
            "source_plan_hashes": {source: archived_source(seed, source, case)[0]["label"]["plan_hash"]
                                   for source in SOURCES}}
    for seed in (2004, 2005, 2020, 2021):
        if seed in ARCHIVES:
            raise ValueError("Reserved test seed entered fixed-source development attempt")
    return {"groups": groups, "cell_order": [{"seed": seed, "source": source}
            for seed, source in CELLS], "declared_cells": len(CELLS),
            "budget": asdict(budget()), "child_seconds": CHILD_SECONDS,
            "controller_seconds": CONTROLLER_SECONDS,
            "source_only_pre_target": True,
            "charging_objective": "linear market.a; exact nonlinear target scored after replay",
            "no_route_reoptimization": True, "no_fresh_hull": True,
            "test_groups_unobserved": [2004, 2005, 2020, 2021]}


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
            or not sizing.runtime_compatible(spec.get("runtime"), sizing.software_runtime())
            or spec.get("native_probe") != sizing.native_probe()
            or base.canonical(spec.get("design")) != base.canonical(design())):
        raise ValueError("Frozen source/runtime/archived inputs/design changed")
    return spec


def _events(dest):
    def record(event):
        with (dest / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
            stream.flush(); os.fsync(stream.fileno())
    return record


def worker(path, seed, source):
    target = attempt(path)
    dest = folder(target, seed, source)
    started = time.monotonic()
    try:
        spec = frozen(target)
        if (seed, source) not in CELLS or not (dest / "launch.json").is_file():
            raise ValueError("Undeclared cell or missing launch receipt")
        case, market = archived_case(seed)
        row, original = archived_source(seed, source, case)
        if (case.identity() != spec["design"]["groups"][case.name]["case_identity"]
                or market.identity() != spec["design"]["groups"][case.name]["market_identity"]
                or nr.digest(row["label"]["plan"]) != spec["design"]["groups"][case.name]["source_plan_hashes"][source]):
            raise ValueError("Frozen case, market, or source plan differs")
        direct_started = time.monotonic()
        direct_exact = Fraction(original["ops_cost"]) + nh.supply(market, original["load"])
        base.save_new(dest / "direct_rescore.json", {"source_row_id": row["row_id"],
            "source_plan_hash": row["label"]["plan_hash"], "case_identity": case.identity(),
            "market_identity": market.identity(), "objective_exact": str(direct_exact),
            "replay": original, "rescore_wall_seconds": time.monotonic()-direct_started})
        selected = sorted({mid for vehicle in row["label"]["plan"]["vehicles"]
                           for mid in vehicle["movements"]})
        charge_started = time.monotonic()
        try:
            plan, replay, stats = rr._solve_fixed_charge(case, market, selected,
                                                         budget(), record=_events(dest))
            charge_wall = time.monotonic()-charge_started
            independent_started = time.monotonic()
            checked = nr.replay_native(case, plan)
            pf._checked_pricing_start(case, plan)
            if checked != replay or {mid for vehicle in plan["vehicles"]
                                     for mid in vehicle["movements"]} != set(selected):
                raise ValueError("Fixed-source route or independent replay changed")
            exact = Fraction(checked["ops_cost"]) + nh.supply(market, checked["load"])
            replay_wall = time.monotonic()-independent_started
            base.save_new(dest / "fixed_charge.json", {"status": "replayed",
                "case_identity": case.identity(), "market_identity": market.identity(),
                "source_plan_hash": row["label"]["plan_hash"],
                "selected_movements": selected, "native_stats": stats,
                "plan": plan, "plan_hash": nr.digest(plan), "replay": checked,
                "objective_exact": str(exact), "charge_wall_seconds": charge_wall,
                "independent_replay_wall_seconds": replay_wall,
                "target_optimality": "unknown; native LP minimizes only linear market.a"})
            result = {"status": "replayed", "source": source,
                "direct_objective_exact": str(direct_exact),
                "post_lp_objective_exact": str(exact), "post_lp_plan_hash": nr.digest(plan),
                "source_paid_seconds": row["label"].get("elapsed_seconds"),
                "charge_wall_seconds": charge_wall,
                "independent_replay_wall_seconds": replay_wall,
                "native_status": stats.get("status"), "target_optimality": "unknown",
                "fresh_hull": False, "elapsed_seconds": time.monotonic()-started}
        except Exception as exc:
            charge_wall = time.monotonic()-charge_started
            telemetry = getattr(exc, "telemetry", {})
            base.save_new(dest / "fixed_charge_failure.json", {
                "type": type(exc).__name__, "message": str(exc),
                "native_stats": telemetry.get("native_stats", locals().get("stats")),
                "unverified_plan_hash": nr.digest(plan) if "plan" in locals() else None,
                "charge_wall_seconds": charge_wall,
                "traceback": traceback.format_exc()})
            result = {"status": "no_replayed_lp_plan", "source": source,
                "direct_objective_exact": str(direct_exact),
                "post_lp_objective_exact": None, "post_lp_plan_hash": None,
                "source_paid_seconds": row["label"].get("elapsed_seconds"),
                "charge_wall_seconds": charge_wall,
                "independent_replay_wall_seconds": None,
                "native_status": (telemetry.get("native_stats") or {}).get("status"),
                "failure": {"type": type(exc).__name__, "message": str(exc)},
                "target_optimality": "unknown", "fresh_hull": False,
                "elapsed_seconds": time.monotonic()-started}
        base.save_new(dest / "result.json", result)
        return 0
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "elapsed_seconds": time.monotonic()-started})
        return 2


def _learned_source(seed):
    archive = ARCHIVES[seed]
    matched = [json.loads(line) for line in (archive / "learned/proposals.jsonl").read_text().splitlines()
               if json.loads(line).get("case_identity") == archived_case(seed)[0].identity()]
    if len(matched) != 1 or matched[0].get("replay_ok") is not True:
        raise ValueError("Archived frozen-model learned source absent or ambiguous")
    source = matched[0]["source_row_id"].rsplit("/", 1)[-1]
    if source not in SOURCES:
        raise ValueError("Learned proposal source is undeclared")
    return source, matched[0]


def _controls(seed):
    rows = _catalog(ARCHIVES[seed])
    result = {}
    for arm in ("cold", "retained", "nearest_price", "cheapest_bill", "learned"):
        matched = [row for row in rows if row.get("row_id") == NAMES[seed] + "/" + arm]
        if len(matched) != 1:
            raise ValueError("Missing or duplicate archived target control " + arm)
        label = matched[0]["label"]
        result[arm] = {key: label.get(key) for key in (
            "feasible", "status", "objective_exact", "lower_exact", "upper_exact",
            "native_status", "elapsed_seconds", "plan_hash")}
    return result


def select_case(path, seed):
    target = Path(path)
    case, market = archived_case(seed)
    started = time.monotonic()
    rows = []
    for source in SOURCES:
        dest = folder(target, seed, source)
        receipt = json.loads((dest / "receipt.json").read_text())
        direct_path = dest / "direct_rescore.json"
        direct = json.loads(direct_path.read_text()) if direct_path.is_file() else None
        result = json.loads((dest / "result.json").read_text()) if (dest / "result.json").is_file() else None
        source_row, original = archived_source(seed, source, case)
        expected = str(Fraction(original["ops_cost"]) + nh.supply(market, original["load"]))
        if direct is not None and (direct["objective_exact"] != expected
                or direct["source_plan_hash"] != source_row["label"]["plan_hash"]
                or direct["case_identity"] != case.identity()
                or direct["market_identity"] != market.identity()):
            raise ValueError("Direct source target rescore changed")
        post_exact = None
        evidence_path = dest / "fixed_charge.json"
        if evidence_path.is_file():
            evidence = json.loads(evidence_path.read_text())
            plan = evidence["plan"]
            replay = nr.replay_native(case, plan)
            post_exact = str(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
            source_movements = {mid for vehicle in source_row["label"]["plan"]["vehicles"]
                                for mid in vehicle["movements"]}
            repaired_movements = {mid for vehicle in plan["vehicles"]
                                  for mid in vehicle["movements"]}
            if (evidence.get("status") != "replayed"
                    or evidence.get("case_identity") != case.identity()
                    or evidence.get("market_identity") != market.identity()
                    or evidence.get("source_plan_hash") != source_row["label"]["plan_hash"]
                    or set(evidence.get("selected_movements", ())) != source_movements
                    or repaired_movements != source_movements
                    or evidence["plan_hash"] != nr.digest(plan)
                    or evidence["replay"] != replay
                    or evidence["objective_exact"] != post_exact
                    or (result is not None and (result.get("status") != "replayed"
                        or result["post_lp_objective_exact"] != post_exact))):
                raise ValueError("Recharged plan replay/hash/target cost changed")
        elif result and result.get("status") == "replayed":
            raise ValueError("Replayed LP result lacks fixed-charge plan evidence")
        failure_path = dest / "exception.json"
        lp_failure_path = dest / "fixed_charge_failure.json"
        rows.append({"source": source, "receipt": receipt,
            "original_source_plan_hash": source_row["label"]["plan_hash"],
            "direct_objective_exact": expected,
            "direct_receipt_present": direct is not None,
            "direct_rescore_status": "receipted" if direct is not None else
                                      "recomputed_from_archived_replay_after_worker_failure",
            "post_lp_objective_exact": post_exact,
            "post_lp_status": ("replayed_provisional_after_worker_failure"
                if post_exact is not None and (result is None
                    or receipt.get("returncode") != 0 or receipt.get("hard_timeout")) else
                result.get("status") if result else "worker_failed"),
            "source_paid_seconds": source_row["label"].get("elapsed_seconds"),
            "lp_paid_seconds": receipt.get("elapsed_seconds"),
            "native_status": (result.get("native_status") if result else
                evidence.get("native_stats", {}).get("status") if evidence_path.is_file() else None),
            "worker_failure": json.loads(failure_path.read_text()) if failure_path.is_file() else None,
            "lp_failure": json.loads(lp_failure_path.read_text()) if lp_failure_path.is_file() else None})
    best_direct = min(rows, key=lambda row: (Fraction(row["direct_objective_exact"]),
                                             SOURCES.index(row["source"])))
    charged = [row for row in rows if row["post_lp_objective_exact"] is not None]
    best_charged = min(charged, key=lambda row: (Fraction(row["post_lp_objective_exact"]),
                                                 SOURCES.index(row["source"]))) if charged else None
    choices = [(Fraction(row[key]), row["source"], "direct" if key.startswith("direct") else "recharged")
               for row in rows for key in ("direct_objective_exact", "post_lp_objective_exact")
               if row[key] is not None]
    best_four = min(choices, key=lambda item: (item[0], SOURCES.index(item[1]),
                                               0 if item[2] == "direct" else 1))
    learned_source, learned = _learned_source(seed)
    by_source = {row["source"]: row for row in rows}
    learned_source_row, _ = archived_source(seed, learned_source, case)
    if (learned.get("plan") != learned_source_row["label"]["plan"]
            or nr.digest(learned["plan"]) != learned_source_row["label"]["plan_hash"]):
        raise ValueError("Archived learned proposal differs from pre-target source plan")
    preparation_path = ARCHIVES[seed] / (
        "learning_receipt.json" if seed < 2018 else "inference_receipt.json")
    preparation = json.loads(preparation_path.read_text())
    total_source = (sum(row["source_paid_seconds"] for row in rows)
                    if all(row["source_paid_seconds"] is not None for row in rows) else None)
    total_lp = (sum(row["lp_paid_seconds"] for row in rows)
                if all(row["lp_paid_seconds"] is not None for row in rows) else None)
    selected = {"case": case.name, "case_identity": case.identity(),
        "market_identity": market.identity(), "candidates": rows,
        "best_direct_source": best_direct["source"],
        "best_direct_objective_exact": best_direct["direct_objective_exact"],
        "best_recharged_source": best_charged["source"] if best_charged else None,
        "best_recharged_objective_exact": best_charged["post_lp_objective_exact"] if best_charged else None,
        "best_of_four": {"source": best_four[1], "kind": best_four[2],
                         "objective_exact": str(best_four[0])},
        "single_lp_methods": {
            "pre_target_cheapest_direct": {"source": best_direct["source"],
                "post_lp_objective_exact": by_source[best_direct["source"]]["post_lp_objective_exact"],
                "lp_paid_seconds": by_source[best_direct["source"]]["lp_paid_seconds"]},
            "frozen_learned_source": {"source": learned_source,
                "post_lp_objective_exact": by_source[learned_source]["post_lp_objective_exact"],
                "inference_seconds": learned.get("online_timing_seconds", {}).get("total"),
                "lp_paid_seconds": by_source[learned_source]["lp_paid_seconds"]}},
        "historical_source_acquisition_seconds": total_source,
        "archived_model_preparation_status": preparation.get("status"),
        "archived_model_preparation_elapsed_seconds": preparation.get("elapsed_seconds"),
        "two_lp_paid_seconds": total_lp,
        "two_lp_plus_historical_acquisition_seconds": (
            total_source + total_lp if total_source is not None and total_lp is not None
            else None),
        "selection_wall_seconds": time.monotonic()-started,
        "historical_target_controls": _controls(seed),
        "fresh_global_bound": False,
        "target_optimality": "unknown: charging LP minimized only linear tariff a",
        "matched_runtime_speedup_claim": False}
    base.save_new(target / case.name / "selection.json", selected)
    return selected


def controller(path):
    target = attempt(path)
    frozen(target)
    started = time.monotonic()
    with (target / ".controller.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another fixed-source controller holds the run lock") from exc
        if not (target / "controller_started.json").exists():
            base.save_new(target / "controller_started.json", {"protocol": PROTOCOL,
                                                                  "utc": time.time()})
        for seed, source in CELLS:
            if time.monotonic()-started > CONTROLLER_SECONDS-CHILD_SECONDS:
                raise TimeoutError("Fixed-source controller budget exhausted before next cell")
            dest = folder(target, seed, source)
            if (dest / "receipt.json").exists():
                continue
            if dest.exists():
                raise ValueError("Interrupted unreceipted fixed-source cell preserved: " + str(dest))
            dest.mkdir(parents=True, exist_ok=False)
            command = [sys.executable, "-m", "experiments.fixed_source_charge_campaign", "worker",
                       "--attempt", str(target), "--case", NAMES[seed], "--source", source]
            base.launch_child(target, NAMES[seed], 0, source + "_charge", CHILD_SECONDS,
                              command=command)
        selections = {}
        for seed in ARCHIVES:
            file = target / NAMES[seed] / "selection.json"
            selections[NAMES[seed]] = json.loads(file.read_text()) if file.exists() else \
                select_case(target, seed)
        if not (target / "summary.json").exists():
            base.save_new(target / "summary.json", {"protocol": PROTOCOL,
                "declared_cells": len(CELLS), "accounted_cells": sum(
                    (folder(target, seed, source) / "receipt.json").is_file()
                    for seed, source in CELLS), "selections": selections,
                "scientific_admission": "pending independent result review"})
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case", choices=tuple(NAMES.values()))
    parser.add_argument("--source", choices=SOURCES)
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
    if not args.case or not args.source:
        parser.error("worker requires --case and --source")
    seed = next(seed for seed, name in NAMES.items() if name == args.case)
    return worker(args.attempt, seed, args.source)


if __name__ == "__main__":
    raise SystemExit(main())
