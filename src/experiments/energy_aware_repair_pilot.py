"""Four-cell energy-relaxed cover pilot on frozen stage-2 development cases."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
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
from experiments import cost_aware_repair_pilot as cost
from experiments import route_repair_pilot as common

ROOT = base.ROOT
ATTEMPT = ROOT / "result/learning_repair/20260930-energy-aware-attempt1"
PROTOCOL = "egg-energy-aware-route-repair-development-20260930-v1"
CELLS = cost.CELLS
MODES = cost.MODES
CHILD_HARD_SECONDS = 240
CONTROLLER_CAP_SECONDS = 1500
DIAGNOSIS_FILES = (
    "research-20260930/learning-campaign/RESULTS_COST_AWARE_REPAIR.md",
    "research-20260930/learning-campaign/RESULT_MANIFEST_COST_AWARE.json",
    "research-20260930/learning-campaign/diagnose_energy_feasibility.py",
    "research-20260930/learning-campaign/ENERGY_FEASIBILITY_DIAGNOSIS.json",
    "research-20260930/learning-campaign/ENERGY_FEASIBILITY_DIAGNOSIS.md",
)
SOURCE_FILES = tuple(dict.fromkeys((
    "src/experiments/energy_aware_repair_pilot.py",
    "src/tests/test_energy_aware_repair_pilot.py",
    "src/tests/test_energy_cover.py",
    "src/cluster/energy_aware_repair.sbatch",
    "research-20260930/learning-campaign/PROTOCOL_ENERGY_AWARE_REPAIR.md",
) + DIAGNOSIS_FILES + cost.SOURCE_FILES))


@dataclass(frozen=True)
class PilotProfile:
    attempt: Path
    protocol: str
    module: str
    label: str
    source_files: tuple[str, ...]
    diagnosis_files: tuple[str, ...]
    charging_caps: bool = False
    shared_charging: bool = False

    def __post_init__(self):
        if self.shared_charging and not self.charging_caps:
            raise ValueError("Shared interval charging requires individual charging caps")


ENERGY_PROFILE = PilotProfile(
    ATTEMPT, PROTOCOL, "experiments.energy_aware_repair_pilot", "energy-aware",
    SOURCE_FILES, DIAGNOSIS_FILES)


def attempt(path, profile=ENERGY_PROFILE):
    value = Path(path).resolve()
    if value != profile.attempt.resolve():
        raise ValueError("Only the declared exclusive " + profile.label + " attempt is allowed")
    return value


def folder(path, case_name, mode):
    return Path(path) / case_name / "state0" / mode


def source_hashes(profile=ENERGY_PROFILE):
    return {name: base.sha(ROOT / name) for name in profile.source_files}


def design(profile=ENERGY_PROFILE):
    baseline = cost.design()
    if [(row["case"], row["mode"]) for row in baseline["cells"]] != list(CELLS):
        raise ValueError("Crossed development cell order changed")
    design = {**baseline, "energy_relaxation": True,
            "energy_relaxation_meaning":
                "necessary segment energy only; optimistic full reset at declared depot charging opportunities",
            "diagnosis_hashes": {name: base.sha(ROOT / name) for name in profile.diagnosis_files},
            "child_hard_seconds": CHILD_HARD_SECONDS,
            "controller_cap_seconds": CONTROLLER_CAP_SECONDS,
            "skip_hull_for_replayed_source_fallback": True,
            "no_refit": True, "reserved_test_groups_unobserved": True}
    if profile.charging_caps:
        design["charging_caps"] = True
        design["energy_relaxation_meaning"] = (
            "necessary route SOC with individual depot and terminal charging-window caps; "
            "shared capacity omitted")
        design["charging_caps_meaning"] = "individual compiled charging-window energy limits"
    if profile.shared_charging:
        design["shared_charging"] = True
        design["charging_caps_meaning"] = (
            "individual and shared compiled charging-interval capacity limits")
        design["energy_relaxation_meaning"] = (
            "necessary route SOC with depot, terminal, and shared interval charging limits; "
            "native physical replay remains required")
    return design


def freeze(path, profile=ENERGY_PROFILE):
    target = attempt(path, profile)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    spec = {"protocol": profile.protocol, "source_commit": commit,
            "source_hashes": source_hashes(profile), "runtime": common.sizing.software_runtime(),
            "native_probe": common.sizing.native_probe(), "design": design(profile),
            "scientific_admission": "pending independent result review"}
    target.mkdir(parents=True, exist_ok=False)
    base.save_new(target / "frozen.json", spec)
    return spec


def frozen(path, profile=ENERGY_PROFILE):
    target = attempt(path, profile)
    spec = json.loads((target / "frozen.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if (spec.get("protocol") != profile.protocol or spec.get("source_commit") != commit
            or spec.get("source_hashes") != source_hashes(profile)
            or not common.sizing.runtime_compatible(spec.get("runtime"),
                                                     common.sizing.software_runtime())
            or spec.get("native_probe") != common.sizing.native_probe()
            or base.canonical(spec.get("design")) != base.canonical(design(profile))):
        raise ValueError("Frozen " + profile.label + " source/runtime/backend/input/design changed")
    return spec


def worker(path, case_name, mode, profile=ENERGY_PROFILE):
    target = attempt(path, profile)
    dest = folder(target, case_name, mode)
    started = time.monotonic()
    try:
        spec = frozen(target, profile)
        if (case_name, mode) not in CELLS or not (dest / "launch.json").is_file():
            raise ValueError("Undeclared energy-aware cell or missing launch receipt")
        prior_frozen, model = common._stage2_inputs()
        declared = prior_frozen["design"]["groups"][case_name]
        case = lp.case_from_dict(declared["case"])
        market = nh.Market(**declared["markets"]["target"])
        if (declared["split"] != "dev"
                or case.identity() != declared["case_identity"]
                or market.identity() != declared["market_identities"]["target"]
                or spec["design"]["stage2_input_hashes"] != common.input_hashes()):
            raise ValueError("Energy-aware case/market/model input identities changed")
        controls = common.control_rows(case_name, case, market)
        base.save_new(dest / "controls.json", controls)
        prior = model if mode == "cost_learned" else None
        kwargs = {"cover_policy": mode, "energy_relaxation": True,
                  "skip_hull_for_fallback": True}
        if profile.charging_caps:
            kwargs["charging_caps"] = True
        if profile.shared_charging:
            kwargs["shared_charging"] = True
        return common.evaluate_case(dest, case_name, case, market, prior, spec,
                                    controls, started, **kwargs)
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "elapsed_seconds": time.monotonic()-started})
        return 2


def result_row(path, case_name, mode, profile=ENERGY_PROFILE):
    dest = folder(path, case_name, mode)
    row = cost.result_row_at(dest, case_name, mode)
    if (dest / "result.json").is_file():
        result = json.loads((dest / "result.json").read_text())
        if result.get("energy_relaxation") is not True:
            raise ValueError("Result omitted declared energy relaxation")
        if profile.charging_caps and result.get("charging_caps") is not True:
            raise ValueError("Result omitted declared charging-window caps")
        if profile.shared_charging and result.get("shared_charging") is not True:
            raise ValueError("Result omitted declared shared interval charging")
    return row


def controller(path, profile=ENERGY_PROFILE):
    target = attempt(path, profile)
    frozen(target, profile)
    started = time.monotonic()
    with (target / ".controller.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another " + profile.label + " controller holds the run lock") from exc
        if not (target / "controller_started.json").exists():
            base.save_new(target / "controller_started.json", {"protocol": profile.protocol,
                                                                  "utc": time.time()})
        for name, mode in CELLS:
            if time.monotonic()-started > CONTROLLER_CAP_SECONDS-CHILD_HARD_SECONDS:
                raise TimeoutError(profile.label + " controller budget exhausted before next cell")
            dest = folder(target, name, mode)
            if (dest / "receipt.json").exists():
                continue
            if dest.exists():
                raise ValueError("Interrupted unreceipted " + profile.label + " cell preserved: " + str(dest))
            dest.mkdir(parents=True, exist_ok=False)
            command = [sys.executable, "-m", profile.module, "worker",
                       "--attempt", str(target), "--case", name, "--mode", mode]
            base.launch_child(target, name, 0, mode, CHILD_HARD_SECONDS, command=command)
        rows = [result_row(target, name, mode, profile) for name, mode in CELLS]
        if not (target / "summary.json").exists():
            base.save_new(target / "summary.json", {"protocol": profile.protocol,
                "declared_cells": len(CELLS), "accounted_cells": len(rows),
                "rows": rows, "scientific_admission": "pending independent result review",
                "matched_runtime_speedup_claim": False})
    return 0


def main(argv=None, profile=ENERGY_PROFILE):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=profile.attempt)
    parser.add_argument("--case", choices=common.CASE_NAMES)
    parser.add_argument("--mode", dest="cover_mode", choices=MODES)
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(design(profile), sort_keys=True, indent=2))
        return 0
    if args.mode == "freeze":
        freeze(args.attempt, profile)
        return 0
    if args.mode == "preflight":
        frozen(args.attempt, profile)
        print(json.dumps({"runtime": common.sizing.software_runtime(),
                          "native_probe": common.sizing.native_probe()}, sort_keys=True))
        return 0
    if args.mode == "controller":
        return controller(args.attempt, profile)
    if not args.case or not args.cover_mode:
        parser.error("worker requires --case and --mode")
    return worker(args.attempt, args.case, args.cover_mode, profile)


if __name__ == "__main__":
    raise SystemExit(main())
