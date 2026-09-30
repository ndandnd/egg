"""Two-cell prospective route-fixed repair pilot on stage-2 development inputs."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
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
from egglab import native_pathflow as pf
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from experiments import budget_sizing_diagnostic as sizing
from experiments import computational_benchmark as base
from experiments import retrieval_comparison as retrieval

ROOT = base.ROOT
STAGE2 = ROOT / "result/learning_campaign/20260930-stage2-attempt1"
ATTEMPT = ROOT / "result/learning_repair/20260930-attempt1"
PROTOCOL = "egg-route-fixed-repair-development-20260930-v1"
SEEDS = (2016, 2017)
CASE_NAMES = ("learning_s2016_n20", "learning_s2017_n28")
INPUT_FILES = (
    "frozen.json", "catalog.jsonl", "summary.json", "learning_receipt.json",
    "learned/model.json", "learned/proposals.jsonl", "learned/training_receipt.json",
    "learning_s2016_n20/state0/cheapest_bill/selection.json",
    "learning_s2017_n28/state0/cheapest_bill/selection.json",
)
SOURCE_FILES = (
    "src/experiments/route_repair_pilot.py", "src/tests/test_route_repair_pilot.py",
    "src/cluster/route_repair_pilot.sbatch",
    "research-20260930/learning-campaign/PROTOCOL_REPAIR.md",
    "research-20260930/learning-campaign/REPAIR_DESIGN.md",
    "src/egglab/route_fixed_repair.py", "src/tests/test_route_fixed_repair.py",
    "src/egglab/learned_proposals.py",
    "src/egglab/native_hull.py", "src/egglab/native_pathflow_hull.py",
    "src/egglab/native_pathflow.py", "src/egglab/native_recharge.py",
    "src/egglab/restricted_qp_proposal.py",
    "src/experiments/computational_benchmark.py",
    "src/experiments/budget_sizing_diagnostic.py",
    "src/experiments/retrieval_comparison.py", "src/cluster/unicorn_env.sh",
)
REPAIR_PATH_SECONDS = 5.0
CHILD_HARD_SECONDS = 240
CONTROLLER_CAP_SECONDS = 900
POLICY = dict(reuse_policy="feasible_pool", pricing_reserve_seconds=10.0,
              master_policy="numerical_qp_proposal", bound_cache_policy="none")


def repair_budget():
    return nr.Budget(backend="GRB", threads=1, phase_seconds=45,
                     wall_seconds=55, max_rounds=1, epsilon=1e-4)


def hull_budget():
    return nh.Budget(backend="GRB", threads=1, phase_seconds=55,
                     wall_seconds=70, pricing_calls=4, master_calls=6,
                     pool_cap=32, epsilon=1e-4, pool_tolerance=1e-6,
                     polish_steps=64, rational_bits=4096, polish_seconds=15)


def attempt(path):
    value = Path(path).resolve()
    if value != ATTEMPT.resolve():
        raise ValueError("Only the declared exclusive repair attempt is allowed")
    return value


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def input_hashes():
    return {name: base.sha(STAGE2 / name) for name in INPUT_FILES}


def _stage2_inputs():
    frozen = json.loads((STAGE2 / "frozen.json").read_text())
    summary = json.loads((STAGE2 / "summary.json").read_text())
    learning = json.loads((STAGE2 / "learning_receipt.json").read_text())
    model = json.loads((STAGE2 / "learned/model.json").read_text())
    if (frozen.get("protocol") != "egg-learning-campaign-synthetic-20260930-stage2-v1"
            or summary.get("accounted_cells") != 44
            or summary.get("declared_cells") != 44
            or learning.get("returncode") != 0
            or learning.get("before_dev_cold") is not True):
        raise ValueError("Stage-2 campaign/training did not complete as declared")
    if (set(model.get("training_groups", ())) !=
            {f"learning_s{seed}" for seed in range(2010, 2016)}):
        raise ValueError("Frozen model training groups differ from six stage-2 groups")
    prior = lp.EdgePrior.from_dict(model)
    groups = frozen["design"]["groups"]
    if (set(groups) != {f"learning_s{seed}_n{n:02d}"
                        for seed, n in ((2010, 12), (2011, 12), (2012, 20),
                                        (2013, 20), (2014, 28), (2015, 28),
                                        (2016, 20), (2017, 28))}
            or frozen["design"].get("reserved_test_seeds") != [2004, 2005]):
        raise ValueError("Stage-2 profile/test reservation differs")
    for name in CASE_NAMES:
        row = groups[name]
        case = lp.case_from_dict(row["case"])
        m = nh.Market(**row["markets"]["target"])
        if (row["split"] != "dev" or case.identity() != row["case_identity"]
                or m.identity() != row["market_identities"]["target"]):
            raise ValueError("Stage-2 development case/market identity differs")
    return frozen, prior


def design():
    frozen, _ = _stage2_inputs()
    return {"stage2_source_commit": frozen["source_commit"],
            "stage2_input_hashes": input_hashes(),
            "development_cases": [
                {"name": name, "physical_identity": frozen["design"]["groups"][name]["case_identity"],
                 "market_identity": frozen["design"]["groups"][name]["market_identities"]["target"]}
                for name in CASE_NAMES],
            "repair_budget": asdict(repair_budget()), "hull_budget": asdict(hull_budget()),
            "path_seconds": REPAIR_PATH_SECONDS,
            "child_hard_seconds": CHILD_HARD_SECONDS,
            "controller_cap_seconds": CONTROLLER_CAP_SECONDS,
            "hull_policy": POLICY, "cells": list(CASE_NAMES),
            "train": "frozen model only; no fit", "test": "reserved and unobserved"}


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
        raise ValueError("Frozen repair source/runtime/backend/input/design changed")
    return spec


def folder(path, case_name):
    return Path(path) / case_name / "state0" / "route_repair"


def _events(dest):
    def record(event):
        with (dest / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    return record


def repaired_envelope(case, market, plan, lineage):
    """Replay a newly repaired fleet as a one-column feasible predecessor."""
    nr.replay_native(case, plan)
    digest = nr.digest(lineage)
    bridge = nh.Market("route-fixed-repair-pool-" + digest, market.a, market.b)
    cfg = hull_budget()
    identity = compact.state_identity(case, bridge, "retained", 0, cfg, **POLICY)
    column = nh.native_column(case, plan,
        {"state_identity": identity, "pricing_oracle": compact.ORACLE_ID,
         "source_kind": ("archived_source_fallback" if lineage.get("kind") == "source_fallback"
                         else "route_fixed_charging_repair"), "lineage_digest": digest},
        compact.EXTRACTION_POLICY)
    nh.replay_column(case, column, compact.EXTRACTION_POLICY)
    mixture = nh.replay_mixture(case, market, [column], [1.0], compact.EXTRACTION_POLICY)
    envelope = {"schema": nh.SCHEMA, "kind": "derived_route_repair_pool_import",
                "status": "bounded", "arm": "retained", "state_index": 0,
                "state_identity": identity, "physical_identity": case.identity(),
                "market_identity": bridge.identity(), "pricing_oracle": compact.ORACLE_ID,
                "extraction_policy": compact.EXTRACTION_POLICY,
                "reuse_policy": "feasible_pool", "pricing_reserve_seconds": 10.0,
                "master_policy": "numerical_qp_proposal",
                "qp_denominator": 1_000_000_000, "qp_maxiter": 500,
                "lineage": lineage, "lineage_digest": digest,
                "columns": [column], "mixture": mixture, "upper": mixture["upper"]}
    imported = nh.import_pool(case, envelope, identity, cfg, previous_index=0,
                              extraction_policy=compact.EXTRACTION_POLICY,
                              reuse_policy="feasible_pool", oracle_id=compact.ORACLE_ID,
                              pricing_reserve_seconds=10.0)
    if len(imported) != 1 or imported[0]["key"] != column["key"]:
        raise ValueError("Repaired fleet import changed projection")
    return envelope, identity


def control_rows(case_name, case, market):
    rows = [json.loads(line) for line in (STAGE2 / "catalog.jsonl").read_text().splitlines()]
    if any(row.get("split") == "test" for row in rows):
        raise ValueError("Test row appears in stage-2 catalog")
    controls = {}
    for arm in ("learned", "cheapest_bill"):
        matched = [row for row in rows if row.get("row_id") == case_name + "/" + arm]
        if len(matched) != 1:
            raise ValueError("Missing or duplicate stage-2 control " + arm)
        row = matched[0]
        if (row.get("split") != "dev" or row.get("case_identity") != case.identity()
                or row.get("market_identity") != market.identity()):
            raise ValueError("Stage-2 control case/market differs")
        label = row["label"]
        controls[arm] = {"native_status": label.get("native_status"),
                         "status": label.get("status"), "feasible": label.get("feasible"),
                         "objective_exact": label.get("objective_exact"),
                         "elapsed_seconds": label.get("elapsed_seconds"),
                         "lower_exact": label.get("lower_exact"),
                         "upper_exact": label.get("upper_exact"),
                         "plan_hash": label.get("plan_hash")}
        if label.get("feasible"):
            replay = nr.replay_native(case, label["plan"])
            exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
            if str(exact) != label["objective_exact"] or nr.digest(label["plan"]) != label["plan_hash"]:
                raise ValueError("Stage-2 control objective/plan does not replay")
    return controls


def source_fallback(case_name, case, market):
    """Independently replay the archived stage-2 exact cheapest source fleet."""
    rows = [json.loads(line) for line in (STAGE2 / "catalog.jsonl").read_text().splitlines()]
    candidates = []
    for index, source in enumerate(("source0", "source1")):
        matched = [row for row in rows if row.get("row_id") == case_name + "/" + source]
        if len(matched) != 1:
            raise ValueError("Missing or duplicate source row for fallback")
        row = matched[0]
        if (row.get("split") != "dev" or row.get("case_identity") != case.identity()
                or row.get("arm") != "source"):
            raise ValueError("Fallback source case/split/arm differs")
        label = row["label"]
        if not label.get("feasible"):
            continue
        plan = label["plan"]
        replay = nr.replay_native(case, plan)
        pf._checked_pricing_start(case, plan)
        if nr.digest(plan) != label["plan_hash"]:
            raise ValueError("Fallback source plan hash differs")
        exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
        candidates.append((exact, index, nh.projection_key(replay["load"], replay["ops_cost"]),
                           row, plan, replay))
    if not candidates:
        raise ValueError("No replayed stage-2 source fleet for fallback")
    exact, _, key, row, plan, replay = min(candidates,
                                         key=lambda item: (item[0], item[1], item[2]))
    selection_path = STAGE2 / case_name / "state0/cheapest_bill/selection.json"
    selection = json.loads(selection_path.read_text())
    if selection.get("selected_keys") != [key]:
        raise ValueError("Rebuilt cheapest source differs from archived stage-2 selection")
    provenance = {"source_row_id": row["row_id"], "source_plan_hash": nr.digest(plan),
                  "projection_key": key, "objective_exact": str(exact),
                  "source_status": row["label"].get("status"),
                  "source_native_status": row["label"].get("native_status"),
                  "source_pool_acquisition_seconds": selection.get("source_paid_seconds"),
                  "archived_selection_sha256": base.sha(selection_path)}
    return plan, replay, provenance


def worker(path, case_name):
    target = attempt(path)
    dest = folder(target, case_name)
    started = time.monotonic()
    try:
        spec = frozen(target)
        if case_name not in CASE_NAMES or not (dest / "launch.json").is_file():
            raise ValueError("Undeclared repair cell or missing launch receipt")
        prior_frozen, prior = _stage2_inputs()
        declared = prior_frozen["design"]["groups"][case_name]
        case = lp.case_from_dict(declared["case"])
        market = nh.Market(**declared["markets"]["target"])
        if (case.identity() != declared["case_identity"]
                or market.identity() != declared["market_identities"]["target"]
                or spec["design"]["stage2_input_hashes"] != input_hashes()):
            raise ValueError("Repair cell input identities changed")
        controls = control_rows(case_name, case, market)
        base.save_new(dest / "controls.json", controls)
        return evaluate_case(dest, case_name, case, market, prior, spec, controls, started)
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "elapsed_seconds": time.monotonic()-started})
        return 2


def evaluate_case(dest, case_name, case, market, prior, spec, controls, started, *,
                  cover_policy="score_only", energy_relaxation=False,
                  skip_hull_for_fallback=False, charging_caps=False,
                  shared_charging=False, path_seconds=None):
    """Evaluate one already-validated cell; caller owns attempt and input guards."""
    from egglab import route_fixed_repair as repair
    effective_path_seconds = REPAIR_PATH_SECONDS if path_seconds is None else float(path_seconds)
    repair_started = time.monotonic()
    proposed = repair.repair_target(case, market, prior, budget=repair_budget(),
                                    path_seconds=effective_path_seconds, cover_policy=cover_policy,
                                    energy_relaxation=energy_relaxation,
                                    charging_caps=charging_caps,
                                    shared_charging=shared_charging,
                                    record=_events(dest))
    repair_wall = time.monotonic() - repair_started
    base.save_new(dest / "repair.json", {"energy_relaxation": energy_relaxation,
                                           "charging_caps": charging_caps,
                                           "shared_charging": shared_charging,
                                           "path_seconds": effective_path_seconds,
                                           "result": proposed,
                                           "repair_wall_seconds": repair_wall})
    candidate_kind = "repaired"
    fallback_provenance = None
    fallback_wall = None
    if proposed.get("repair_status") != "replayed":
        base.save_new(dest / "failure.json", {
            "cover_policy": cover_policy,
            "energy_relaxation": energy_relaxation,
            "charging_caps": charging_caps,
            "shared_charging": shared_charging,
            "path_seconds": effective_path_seconds,
            "repair_status": proposed.get("repair_status"),
            "failure": proposed.get("failure"),
            "native_stats": proposed.get("native_stats"),
            "raw_topology": proposed.get("raw_topology"),
            "cover": proposed.get("cover"),
            "timing_seconds": proposed.get("timing_seconds"),
            "repair_wall_seconds": repair_wall})
        candidate_kind = "source_fallback"
        fallback_started = time.monotonic()
        plan, _, fallback_provenance = source_fallback(case_name, case, market)
        fallback_wall = time.monotonic()-fallback_started
        base.save_new(dest / "fallback.json", {"candidate_kind": candidate_kind,
            "cover_policy": cover_policy,
            "energy_relaxation": energy_relaxation,
            "charging_caps": charging_caps,
            "shared_charging": shared_charging,
            "path_seconds": effective_path_seconds,
            "plan": plan, "provenance": fallback_provenance,
            "selection_and_replay_wall_seconds": fallback_wall})
    else:
        plan = proposed["plan"]
    replay_started = time.monotonic()
    replay = nr.replay_native(case, plan)
    if candidate_kind == "repaired" and proposed.get("replay") != replay:
        raise ValueError("Repair-reported replay differs from independent replay")
    pf._checked_pricing_start(case, plan)
    if candidate_kind == "repaired":
        selected = proposed["cover"]["selected_movements"]
        pf.recover_paths(case, selected)
        if {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]} != set(selected):
            raise ValueError("Repaired plan route differs from legal decoded cover")
    exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
    if candidate_kind == "repaired" and proposed.get("true_cost_exact") != str(exact):
        raise ValueError("Repair true target cost differs from independent exact cost")
    if candidate_kind == "source_fallback" and fallback_provenance["objective_exact"] != str(exact):
        raise ValueError("Fallback target cost differs from source selection")
    replay_wall = time.monotonic()-replay_started
    base.save_new(dest / "independent_replay.json", {
        "cover_policy": cover_policy,
        "energy_relaxation": energy_relaxation,
        "charging_caps": charging_caps,
        "shared_charging": shared_charging,
        "path_seconds": effective_path_seconds,
        "candidate_kind": candidate_kind, "fallback_provenance": fallback_provenance,
        "case_identity": case.identity(), "market_identity": market.identity(),
        "plan_hash": nr.digest(plan), "replay": replay,
        "objective_exact": str(exact), "replay_wall_seconds": replay_wall,
        "elapsed_seconds": time.monotonic()-started})
    if candidate_kind == "source_fallback" and skip_hull_for_fallback:
        reference = {arm: {"row_id": case_name + "/" + arm,
                           "lower_exact": row.get("lower_exact"),
                           "upper_exact": row.get("upper_exact"),
                           "native_status": row.get("native_status")}
                     for arm, row in controls.items()}
        reason = ("The same archived stage-2 source candidate already had target native "
                  "verification; this replay adds no new physical candidate.")
        base.save_new(dest / "hull_skipped.json", {
            "cover_policy": cover_policy, "energy_relaxation": energy_relaxation,
            "charging_caps": charging_caps,
            "shared_charging": shared_charging,
            "path_seconds": effective_path_seconds,
            "reason": reason, "historical_bounds_reference": reference,
            "fresh_bound": False, "hull_wall_seconds": 0.0})
        base.save_new(dest / "result.json", {"case": case_name,
            "outcome": "fallback_replayed_no_new_hull",
            "cover_policy": cover_policy, "energy_relaxation": energy_relaxation,
            "charging_caps": charging_caps,
            "shared_charging": shared_charging,
            "path_seconds": effective_path_seconds,
            "candidate_kind": candidate_kind, "repair_status": proposed.get("repair_status"),
            "candidate_objective_exact": str(exact), "candidate_plan_hash": nr.digest(plan),
            "fallback_provenance": fallback_provenance,
            "repair_wall_seconds": repair_wall, "independent_replay_wall_seconds": replay_wall,
            "fallback_selection_and_replay_wall_seconds": fallback_wall,
            "pool_preparation_wall_seconds": 0.0, "hull_wall_seconds": 0.0,
            "hull_assessment": {}, "hull_skipped_reason": reason,
            "historical_bounds_reference": reference, "controls": controls,
            "elapsed_seconds": time.monotonic()-started,
            "scientific_admission": "pending independent result review"})
        return 0
    lineage = {"kind": candidate_kind, "cover_policy": cover_policy,
               "energy_relaxation": energy_relaxation,
               "charging_caps": charging_caps,
               "shared_charging": shared_charging,
               "path_seconds": effective_path_seconds,
               "case_identity": case.identity(),
               "market_identity": market.identity(), "plan_hash": nr.digest(plan),
               "fallback_provenance": fallback_provenance,
               "stage2_input_hashes": spec["design"]["stage2_input_hashes"],
               "repair_source_commit": spec["source_commit"]}
    pool_started = time.monotonic()
    envelope, identity = repaired_envelope(case, market, plan, lineage)
    pool_wall = time.monotonic()-pool_started
    base.save_new(dest / "import_envelope.json", envelope)
    base.save_new(dest / "pool_preparation.json", {
        "cover_policy": cover_policy,
        "energy_relaxation": energy_relaxation,
        "charging_caps": charging_caps,
        "shared_charging": shared_charging,
        "path_seconds": effective_path_seconds,
        "candidate_kind": candidate_kind, "pool_preparation_wall_seconds": pool_wall,
        "lineage_digest": envelope["lineage_digest"],
        "column_key": envelope["columns"][0]["key"]})
    hull_started = time.monotonic()
    result = compact.certify(case, market, hull_budget(), arm="retained",
                             state_index=1, previous=envelope,
                             expected_previous=identity, record=_events(dest), **POLICY)
    hull_wall = time.monotonic()-hull_started
    base.save_new(dest / "raw_hull.json", {"result": result,
                                            "hull_wall_seconds": hull_wall})
    assessment = retrieval.assess_hull(case, market, result)
    base.save_new(dest / "result.json", {"case": case_name,
        "outcome": "candidate_and_native_hull_checked",
        "cover_policy": cover_policy,
        "energy_relaxation": energy_relaxation,
        "charging_caps": charging_caps,
        "shared_charging": shared_charging,
        "path_seconds": effective_path_seconds,
        "candidate_kind": candidate_kind, "repair_status": proposed.get("repair_status"),
        "candidate_objective_exact": str(exact), "candidate_plan_hash": nr.digest(plan),
        "fallback_provenance": fallback_provenance,
        "repair_wall_seconds": repair_wall, "independent_replay_wall_seconds": replay_wall,
        "fallback_selection_and_replay_wall_seconds": fallback_wall,
        "pool_preparation_wall_seconds": pool_wall, "hull_wall_seconds": hull_wall,
        "hull_assessment": assessment, "controls": controls,
        "elapsed_seconds": time.monotonic()-started,
        "scientific_admission": "pending independent result review"})
    return 0


def result_row(path, case_name):
    dest = folder(path, case_name)
    row = {"case": case_name, "outcome": "unstarted", "receipt": None,
           "repair_status": None, "candidate_kind": None, "hull_status": None,
           "candidate_objective_exact": None, "elapsed_seconds": None}
    if (dest / "receipt.json").is_file():
        receipt = json.loads((dest / "receipt.json").read_text())
        row.update(receipt=receipt, elapsed_seconds=receipt.get("elapsed_seconds"),
                   outcome="hard_timeout" if receipt.get("hard_timeout") else
                           "failed" if receipt.get("returncode") != 0 else "returned")
    elif dest.exists():
        row["outcome"] = "interrupted_unreceipted"
    if (dest / "result.json").is_file():
        result = json.loads((dest / "result.json").read_text())
        row.update(outcome=result["outcome"], repair_status=result["repair_status"],
                   candidate_kind=result.get("candidate_kind"),
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
            raise ValueError("Another repair controller holds the run lock") from exc
        if not (target / "controller_started.json").exists():
            base.save_new(target / "controller_started.json", {"protocol": PROTOCOL,
                                                                  "utc": time.time()})
        for name in CASE_NAMES:
            if time.monotonic()-started > CONTROLLER_CAP_SECONDS-CHILD_HARD_SECONDS:
                raise TimeoutError("Repair controller budget exhausted before next cell")
            dest = folder(target, name)
            if (dest / "receipt.json").exists():
                continue
            if dest.exists():
                raise ValueError("Interrupted unreceipted repair cell preserved: " + str(dest))
            dest.mkdir(parents=True, exist_ok=False)
            command = [sys.executable, "-m", "experiments.route_repair_pilot", "worker",
                       "--attempt", str(target), "--case", name]
            base.launch_child(target, name, 0, "route_repair", CHILD_HARD_SECONDS,
                              command=command)
        rows = [result_row(target, name) for name in CASE_NAMES]
        if not (target / "summary.json").exists():
            base.save_new(target / "summary.json", {"protocol": PROTOCOL,
                "declared_cells": len(CASE_NAMES), "accounted_cells": len(rows),
                "rows": rows, "scientific_admission": "pending independent result review"})
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case", choices=CASE_NAMES)
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(design(), indent=2, sort_keys=True))
        return 0
    if args.mode == "freeze":
        freeze(args.attempt)
        return 0
    if args.mode == "preflight":
        frozen(args.attempt)
        print(json.dumps({"runtime": sizing.software_runtime(),
                          "native_probe": sizing.native_probe()}, sort_keys=True))
        return 0
    if args.mode == "controller":
        return controller(args.attempt)
    if not args.case:
        parser.error("worker requires --case")
    return worker(args.attempt, args.case)


if __name__ == "__main__":
    raise SystemExit(main())
