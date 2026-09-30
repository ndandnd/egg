"""Four-cell crossed cost-aware route-repair ablation; import never solves."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from egglab import learned_proposals as lp
from egglab import native_hull as nh
from experiments import computational_benchmark as base
from experiments import route_repair_pilot as common

ROOT = base.ROOT
ATTEMPT = ROOT / "result/learning_repair/20260930-cost-aware-attempt1"
PROTOCOL = "egg-cost-aware-route-repair-development-20260930-v1"
CELLS = (
    ("learning_s2016_n20", "cost_only"),
    ("learning_s2016_n20", "cost_learned"),
    ("learning_s2017_n28", "cost_learned"),
    ("learning_s2017_n28", "cost_only"),
)
MODES = ("cost_only", "cost_learned")
CHILD_HARD_SECONDS = 240
CONTROLLER_CAP_SECONDS = 1500
SOURCE_FILES = tuple(dict.fromkeys((
    "src/experiments/cost_aware_repair_pilot.py",
    "src/tests/test_cost_aware_repair_pilot.py",
    "src/cluster/cost_aware_repair.sbatch",
    "research-20260930/learning-campaign/PROTOCOL_COST_AWARE_REPAIR.md",
) + common.SOURCE_FILES))


def attempt(path):
    value = Path(path).resolve()
    if value != ATTEMPT.resolve():
        raise ValueError("Only the new exclusive cost-aware attempt is allowed")
    return value


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def folder(path, case_name, mode):
    return Path(path) / case_name / "state0" / mode


def design():
    prior_frozen, prior = common._stage2_inputs()
    if tuple(prior.training_groups) != tuple(f"learning_s{seed}" for seed in range(2010, 2016)):
        raise ValueError("Frozen model training groups changed")
    return {"stage2_source_commit": prior_frozen["source_commit"],
            "stage2_input_hashes": common.input_hashes(),
            "cells": [{"case": name, "mode": mode,
                       "case_identity": prior_frozen["design"]["groups"][name]["case_identity"],
                       "market_identity": prior_frozen["design"]["groups"][name]["market_identities"]["target"]}
                      for name, mode in CELLS],
            "repair_budget": asdict(common.repair_budget()),
            "hull_budget": asdict(common.hull_budget()),
            "path_seconds": common.REPAIR_PATH_SECONDS,
            "child_hard_seconds": CHILD_HARD_SECONDS,
            "controller_cap_seconds": CONTROLLER_CAP_SECONDS,
            "hull_policy": common.POLICY,
            "no_refit": True, "reserved_test_groups_unobserved": True,
            "order_policy": "crossed case/mode order; no replication"}


def freeze(path):
    target = attempt(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    spec = {"protocol": PROTOCOL, "source_commit": commit,
            "source_hashes": source_hashes(), "runtime": common.sizing.software_runtime(),
            "native_probe": common.sizing.native_probe(), "design": design(),
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
            or not common.sizing.runtime_compatible(spec.get("runtime"),
                                                     common.sizing.software_runtime())
            or spec.get("native_probe") != common.sizing.native_probe()
            or base.canonical(spec.get("design")) != base.canonical(design())):
        raise ValueError("Frozen cost-aware repair source/runtime/backend/input/design changed")
    return spec


def worker(path, case_name, mode):
    target = attempt(path)
    dest = folder(target, case_name, mode)
    started = time.monotonic()
    try:
        spec = frozen(target)
        if (case_name, mode) not in CELLS or not (dest / "launch.json").is_file():
            raise ValueError("Undeclared cost-aware cell or missing launch receipt")
        prior_frozen, model = common._stage2_inputs()
        declared = prior_frozen["design"]["groups"][case_name]
        case = lp.case_from_dict(declared["case"])
        market = nh.Market(**declared["markets"]["target"])
        if (declared["split"] != "dev"
                or case.identity() != declared["case_identity"]
                or market.identity() != declared["market_identities"]["target"]
                or spec["design"]["stage2_input_hashes"] != common.input_hashes()):
            raise ValueError("Cost-aware case/market/model input identities changed")
        controls = common.control_rows(case_name, case, market)
        base.save_new(dest / "controls.json", controls)
        # cost_only receives no model at the repair API; it performs no logits
        # inference even though the attempt freezes the common model identity.
        prior = model if mode == "cost_learned" else None
        return common.evaluate_case(dest, case_name, case, market, prior, spec,
                                    controls, started, cover_policy=mode)
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "elapsed_seconds": time.monotonic()-started})
        return 2


def result_row(path, case_name, mode):
    dest = folder(path, case_name, mode)
    row = {"case": case_name, "mode": mode, "outcome": "unstarted",
           "receipt": None, "candidate_kind": None, "repair_status": None,
           "candidate_objective_exact": None, "hull_status": None,
           "elapsed_seconds": None}
    if (dest / "receipt.json").is_file():
        receipt = json.loads((dest / "receipt.json").read_text())
        row.update(receipt=receipt, elapsed_seconds=receipt.get("elapsed_seconds"),
                   outcome="hard_timeout" if receipt.get("hard_timeout") else
                           "failed" if receipt.get("returncode") != 0 else "returned")
    elif dest.exists():
        row["outcome"] = "interrupted_unreceipted"
    if (dest / "result.json").is_file():
        result = json.loads((dest / "result.json").read_text())
        if result.get("cover_policy") != mode:
            raise ValueError("Result mode differs from declared ablation cell")
        row.update(outcome=result["outcome"], candidate_kind=result.get("candidate_kind"),
                   repair_status=result.get("repair_status"),
                   candidate_objective_exact=result.get("candidate_objective_exact"),
                   hull_status=result.get("hull_assessment", {}).get("status"))
    return row


def controller(path):
    target = attempt(path)
    frozen(target)
    started = time.monotonic()
    with (target / ".controller.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another cost-aware controller holds the run lock") from exc
        if not (target / "controller_started.json").exists():
            base.save_new(target / "controller_started.json", {"protocol": PROTOCOL,
                                                                  "utc": time.time()})
        for name, mode in CELLS:
            if time.monotonic()-started > CONTROLLER_CAP_SECONDS-CHILD_HARD_SECONDS:
                raise TimeoutError("Cost-aware controller budget exhausted before next cell")
            dest = folder(target, name, mode)
            if (dest / "receipt.json").exists():
                continue
            if dest.exists():
                raise ValueError("Interrupted unreceipted cost-aware cell preserved: " + str(dest))
            dest.mkdir(parents=True, exist_ok=False)
            command = [sys.executable, "-m", "experiments.cost_aware_repair_pilot", "worker",
                       "--attempt", str(target), "--case", name, "--mode", mode]
            base.launch_child(target, name, 0, mode, CHILD_HARD_SECONDS, command=command)
        rows = [result_row(target, name, mode) for name, mode in CELLS]
        if not (target / "summary.json").exists():
            base.save_new(target / "summary.json", {"protocol": PROTOCOL,
                "declared_cells": len(CELLS), "accounted_cells": len(rows),
                "rows": rows, "scientific_admission": "pending independent result review",
                "matched_runtime_speedup_claim": False})
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case", choices=common.CASE_NAMES)
    parser.add_argument("--mode", dest="cover_mode", choices=MODES)
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(design(), sort_keys=True, indent=2))
        return 0
    if args.mode == "freeze":
        freeze(args.attempt)
        return 0
    if args.mode == "preflight":
        frozen(args.attempt)
        print(json.dumps({"runtime": common.sizing.software_runtime(),
                          "native_probe": common.sizing.native_probe()}, sort_keys=True))
        return 0
    if args.mode == "controller":
        return controller(args.attempt)
    if not args.case or not args.cover_mode:
        parser.error("worker requires --case and --mode")
    return worker(args.attempt, args.case, args.cover_mode)


if __name__ == "__main__":
    raise SystemExit(main())
