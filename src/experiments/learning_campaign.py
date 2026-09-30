"""Bounded, resumable synthetic fleet-label campaign; import never optimizes."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from egglab import native_hull as nh
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from experiments import computational_benchmark as base
from experiments import budget_sizing_diagnostic as sizing
from experiments import retrieval_comparison as retrieval

ROOT = base.ROOT
ATTEMPT = ROOT / "result/learning_campaign/20260930-attempt1"
PROTOCOL = "egg-learning-campaign-synthetic-20260930-v1"
GENERATOR = "independent-paired-duty-timetable-v1"
# Test groups are reserved by identity before training; this first job never
# materializes their cases, prices, labels, or features.
SPLITS = {2001: "train", 2002: "train", 2003: "dev", 2004: "test_reserved", 2005: "test_reserved"}
ACTIVE = (2001, 2002, 2003)
MARKETS = ("source0", "source1", "target")
TARGET_ARMS = ("cold", "retained", "nearest_price", "cheapest_bill", "learned")
STAGES = ("source0", "source1", "cold", "retained", "nearest_price", "cheapest_bill", "learned")
CHILD_SECONDS = 100
CONTROLLER_SECONDS = 2100
POLICY = dict(reuse_policy="feasible_pool", pricing_reserve_seconds=10.0,
              master_policy="numerical_qp_proposal", bound_cache_policy="none")
SOURCE_FILES = (
    "src/experiments/learning_campaign.py", "src/tests/test_learning_campaign.py",
    "src/cluster/learning_campaign.sbatch",
    "research-20260930/learning-campaign/PROTOCOL.md",
    "research-20260930/learning-campaign/ARCHITECTURE.md",
    "research-20260930/learning-campaign/README.md",
    "src/experiments/computational_benchmark.py",
    "src/experiments/budget_sizing_diagnostic.py",
    "src/experiments/retrieval_comparison.py",
    "src/experiments/train_fleet_proposals.py",
    "src/egglab/learned_proposals.py",
    "src/tests/test_learned_proposals.py",
    "research-20260930/learning-campaign/LEARNING.md",
    "src/egglab/native_hull.py", "src/egglab/native_pathflow_hull.py",
    "src/egglab/native_pathflow.py", "src/egglab/native_recharge.py",
    "src/egglab/restricted_qp_proposal.py", "src/cluster/unicorn_env.sh",
)


def _draw(seed: int, duty: int, field: str, count: int) -> int:
    payload = f"{GENERATOR}|{seed}|{duty}|{field}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % count


def _travel(origin, destination):
    minutes = {("D", "A"): 4, ("A", "D"): 4, ("D", "B"): 6,
               ("B", "D"): 6, ("A", "B"): 8, ("B", "A"): 8}
    value = 0 if origin == destination else minutes[origin, destination]
    return value, value * 0.25


def make_case(seed):
    if seed not in ACTIVE:
        raise ValueError("Reserved test group cannot be materialized by first campaign")
    trips = []
    for duty in range(4):
        start = 360 + 25*duty + _draw(seed, duty, "offset", 9)
        first = 18 + _draw(seed, duty, "duration_ab", 15)
        wait = 5 + _draw(seed, duty, "wait_b", 26)
        second = 18 + _draw(seed, duty, "duration_ba", 15)
        trips.extend((nr.Trip(f"T{2*duty+1:02d}", start, start+first, "A", "B",
                              18 + _draw(seed, duty, "energy_ab", 1001)/100),
                      nr.Trip(f"T{2*duty+2:02d}", start+first+wait,
                              start+first+wait+second, "B", "A",
                              18 + _draw(seed, duty, "energy_ba", 1001)/100)))
    movements = []
    for trip in trips:
        out, oe = _travel("D", trip.start_place)
        back, be = _travel(trip.end_place, "D")
        movements.extend((
            nr.Movement(f"out_{trip.id}", "pullout", None, trip.id,
                        (nr.Leg("D", trip.start_place, trip.start_min-out,
                                trip.start_min, oe),)),
            nr.Movement(f"in_{trip.id}", "pullin", trip.id, None,
                        (nr.Leg(trip.end_place, "D", trip.end_min,
                                trip.end_min+back, be),))))
    for before in trips:
        for after in trips:
            if before.id == after.id:
                continue
            travel, energy = _travel(before.end_place, after.start_place)
            arrival = before.end_min + travel
            if arrival <= after.start_min:
                legs = [nr.Leg(before.end_place, after.start_place,
                               before.end_min, arrival, energy)]
                if arrival < after.start_min:
                    legs.append(nr.Leg(after.start_place, after.start_place,
                                       arrival, after.start_min,
                                       (after.start_min-arrival)*0.01))
                movements.append(nr.Movement(f"direct_{before.id}_{after.id}",
                                             "direct", before.id, after.id, tuple(legs)))
            inbound, ie = _travel(before.end_place, "D")
            outbound, oe = _travel("D", after.start_place)
            arrival = before.end_min + inbound
            departure = after.start_min - outbound
            if arrival <= departure:
                movements.append(nr.Movement(
                    f"depot_{before.id}_{after.id}", "depot", before.id, after.id,
                    (nr.Leg(before.end_place, "D", before.end_min, arrival, ie),
                     nr.Leg("D", after.start_place, departure, after.start_min, oe)), 1))
    case = nr.NativeCase(
        name=f"learning_s{seed}_n08", trips=tuple(trips), movements=tuple(movements),
        resources=(nr.Resource(0, 1800, 90.0, 90.0, 1),),
        market_edges_min=tuple(range(0, 1801, 60)), depot="D", max_vehicles=8,
        battery_kwh=100.0, reserve_kwh=20.0, terminal_open_min=1080,
        recharge_deadline_min=1800, vehicle_cost=100.0,
        deadhead_cost_per_min=0.0, efficiency=0.9)
    nr.validate_case(case)
    return case


def seed_from_name(name):
    if not isinstance(name, str) or not name.startswith("learning_s") or not name.endswith("_n08"):
        raise ValueError("Malformed case name")
    seed = int(name[len("learning_s"):-len("_n08")])
    if f"learning_s{seed}_n08" != name or seed not in ACTIVE:
        raise ValueError("Undeclared case name")
    return seed


def market(case, kind):
    if kind not in MARKETS:
        raise ValueError("Unknown market")
    if kind == "source0":
        prices = (0.20,)*30
    elif kind == "source1":
        prices = tuple(0.10 if 18 <= h < 22 else 0.30 for h in range(30))
    else:
        prices = tuple(0.10 if 22 <= h < 26 else 0.30 for h in range(30))
    return nh.Market(case.name + "-" + kind, prices, (1/900,)*30)


def budget():
    return nh.Budget(backend="GRB", threads=1, phase_seconds=55,
                     wall_seconds=70, pricing_calls=4, master_calls=6,
                     pool_cap=32, epsilon=1e-4, pool_tolerance=1e-6,
                     polish_steps=64, rational_bits=4096, polish_seconds=15)


def stages(seed):
    if seed not in ACTIVE:
        raise ValueError("Undeclared active group")
    return STAGES if SPLITS[seed] == "dev" else STAGES[:-2]


def design():
    rows = {}
    for seed in ACTIVE:
        case = make_case(seed)
        rows[case.name] = {
            "base_group": f"learning_s{seed}", "split": SPLITS[seed],
            "case": asdict(case), "case_identity": case.identity(),
            "markets": {kind: asdict(market(case, kind)) for kind in MARKETS},
            "market_identities": {kind: market(case, kind).identity() for kind in MARKETS}}
    return {"generator": GENERATOR, "groups": rows,
            "reserved_test_seeds": [seed for seed, split in SPLITS.items()
                                    if split == "test_reserved"],
            "stages": {f"learning_s{seed}": list(stages(seed)) for seed in ACTIVE},
            "declared_cells": sum(len(stages(seed)) for seed in ACTIVE),
            "budget": asdict(budget()), "policy": POLICY,
            "child_hard_seconds": CHILD_SECONDS,
            "controller_hard_seconds": CONTROLLER_SECONDS}


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def attempt(path):
    value = Path(path).resolve()
    if value != ATTEMPT.resolve():
        raise ValueError("Only the declared immutable attempt is allowed")
    return value


def freeze(path):
    target = attempt(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    spec = {"protocol": PROTOCOL, "source_commit": commit,
            "source_hashes": source_hashes(), "runtime": sizing.software_runtime(),
            "native_probe": sizing.native_probe(), "design": design(),
            "scientific_admission": "pending independent review"}
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
        raise ValueError("Frozen commit, source, runtime, native backend, or design changed")
    return spec


def folder(path, case_name, stage):
    return Path(path) / case_name / "state0" / stage


def _event_writer(dest):
    def record(event):
        with (dest / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    return record


def _source_candidates(path, case, source):
    dest = folder(path, case.name, source)
    receipt = json.loads((dest / "receipt.json").read_text())
    raw = json.loads((dest / "raw_result.json").read_text())["result"]
    m = market(case, source)
    identity = compact.state_identity(case, m, "retained", 0, budget(), **POLICY)
    if (raw.get("physical_identity") != case.identity()
            or raw.get("market_identity") != m.identity()
            or raw.get("state_identity") != identity):
        raise ValueError("Source identity differs")
    events = [json.loads(line) for line in (dest / "events.jsonl").read_text().splitlines()]
    requests = retrieval._event_index(events, "pricing_request")
    results = retrieval._event_index(events, "pricing_result")
    bounds = retrieval._event_index(events, "global_bound")
    candidates = []
    for column in raw.get("columns", []):
        call = column["source"].get("pricing_call")
        if call not in requests or call not in results or call not in bounds:
            raise ValueError("Column lacks complete pricing event lineage")
        candidate = retrieval._candidate(case, m, identity, source,
                                         requests[call], results[call], bounds[call])
        if candidate["column"] != column:
            raise ValueError("Returned source column differs from bound event")
        candidates.append(candidate)
    files = {name: base.sha(dest / name) for name in
             ("raw_result.json", "receipt.json", "events.jsonl")}
    return {"source": source, "receipt": receipt, "raw_status": raw.get("status"),
            "source_state_identity": identity, "files": files,
            "paid_source_seconds": receipt.get("elapsed_seconds")}, candidates


def pool(path, case):
    sources, candidates = {}, []
    for name in ("source0", "source1"):
        try:
            sources[name], found = _source_candidates(path, case, name)
            candidates.extend(found)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            sources[name] = {"source": name, "admission_failure": repr(exc), "files": {},
                             "source_state_identity": None}
    return {"sources": sources, "candidates": candidates, "eligible": bool(candidates)}


def catalog_source_pool(path, case, available):
    """Exactly one best replayed fleet per source market, as seen by trainer."""
    rows = [json.loads(line) for line in (Path(path) / "catalog.jsonl").read_text().splitlines()]
    selected = []
    for source in ("source0", "source1"):
        matches = [row for row in rows if row.get("row_id") == case.name + "/" + source]
        if len(matches) != 1:
            raise ValueError("Source catalog row absent or duplicated")
        label = matches[0]["label"]
        if not label.get("feasible"):
            continue
        found = [candidate for candidate in available["candidates"]
                 if candidate["source"] == source
                 and candidate["witness_hash"] == label["plan_hash"]
                 and candidate["column"]["plan"] == label["plan"]]
        if len(found) != 1:
            raise ValueError("Catalog feasible source fleet does not uniquely match native pool")
        selected.extend(found)
    return {**available, "candidates": selected, "eligible": bool(selected)}


def select_nonlinear_cheapest(available, m):
    """Compare complete fleets under the target nonlinear market objective."""
    candidates = available["candidates"]
    if not candidates:
        raise ValueError("Empty catalog source pool")
    return [min(candidates, key=lambda candidate: (
        Fraction(candidate["column"]["ops_cost"]) +
        nh.supply(m, candidate["column"]["load"]),
        ("source0", "source1").index(candidate["source"]),
        candidate["call"], candidate["key"]))]


def select_nearest_source_market(available, case, target):
    candidates = available["candidates"]
    if not candidates:
        raise ValueError("Empty catalog source pool")
    return [min(candidates, key=lambda candidate: (
        sum((Fraction(a)-Fraction(b))**2
            for a, b in zip(market(case, candidate["source"]).a, target.a)),
        ("source0", "source1").index(candidate["source"]),
        candidate["call"], candidate["key"]))]


def learned_candidate(path, case, available):
    receipt = json.loads((Path(path) / "learning_receipt.json").read_text())
    if receipt.get("returncode") != 0 or receipt.get("before_dev_cold") is not True:
        raise ValueError("No successful prospective learning receipt")
    proposals_path = Path(path) / "learned/proposals.jsonl"
    if receipt.get("output_hashes", {}).get("proposals.jsonl") != base.sha(proposals_path):
        raise ValueError("Learned proposal file changed after prospective receipt")
    proposals = [json.loads(line) for line in proposals_path.read_text().splitlines()]
    matched = [item for item in proposals if item.get("case_identity") == case.identity()]
    if len(matched) != 1 or matched[0].get("replay_ok") is not True:
        raise ValueError("No unique replayed learned proposal for development case")
    proposed = matched[0]
    plan = proposed["plan"]
    nr.replay_native(case, plan)
    source_id = proposed["source_row_id"]
    candidates = [candidate for candidate in available["candidates"]
                  if candidate["source"] == source_id.rsplit("/", 1)[-1]
                  and candidate["column"]["plan"] == plan]
    if len(candidates) != 1:
        raise ValueError("Learned complete fleet lacks unique native source column")
    return candidates, proposed


def worker(path, case_name, stage):
    target = attempt(path)
    dest = folder(target, case_name, stage)
    started = time.monotonic()
    try:
        spec = frozen(target)
        group = spec["design"]["groups"].get(case_name)
        if stage not in stages(seed_from_name(case_name)) or group is None or not (dest / "launch.json").is_file():
            raise ValueError("Undeclared cell or absent launch receipt")
        seed = seed_from_name(case_name)
        case = make_case(seed)
        kind = stage if stage in ("source0", "source1") else "target"
        m = market(case, kind)
        if (group["case_identity"] != case.identity()
                or group["market_identities"][kind] != m.identity()):
            raise ValueError("Frozen case/market differs")
        previous = identity = None
        arm = "cold"
        if stage in ("source0", "source1"):
            arm = "retained"
        elif stage != "cold":
            available = pool(target, case)
            if not available["eligible"]:
                raise ValueError("No replayed source fleets for retrieval")
            if stage != "retained":
                available = catalog_source_pool(target, case, available)
                if not available["eligible"]:
                    raise ValueError("No trainer-visible source fleets for comparison")
            if stage == "learned":
                selected, learned = learned_candidate(target, case, available)
            elif stage == "cheapest_bill":
                selected, learned = select_nonlinear_cheapest(available, m), None
            elif stage == "nearest_price":
                selected, learned = select_nearest_source_market(available, case, m), None
            else:
                selected, learned = retrieval.select(available, m, stage), None
            retrieval.direct_proposals(case, m, selected)
            base.save_new(dest / "selection.json", {
                "selected_keys": [candidate["key"] for candidate in selected],
                "candidate_pool_keys": [candidate["key"] for candidate in available["candidates"]],
                "learned_proposal": {"source_row_id": learned["source_row_id"],
                                      "proposed_topology": learned["proposed_topology"],
                                      "projection": learned["projection"],
                                      "online_timing_seconds": learned["online_timing_seconds"]} if learned else None,
                "learning_elapsed_seconds": json.loads((target / "learning_receipt.json").read_text()).get("elapsed_seconds") if learned else None,
                "source_paid_seconds": sum(row.get("paid_source_seconds") or 0
                                           for row in available["sources"].values()),
                "lookup_elapsed_seconds": time.monotonic()-started})
            previous, identity = retrieval.import_envelope(case, m, budget(), available, selected)
            base.save_new(dest / "import_envelope.json", previous)
            arm = "retained"
        result = compact.certify(case, m, budget(), arm=arm,
                                 state_index=0 if previous is None else 1,
                                 previous=previous, expected_previous=identity,
                                 record=_event_writer(dest), **POLICY)
        base.save_new(dest / "raw_result.json", {"result": result,
                                                  "case": case_name, "stage": stage})
        assessment = retrieval.assess_hull(case, m, result)
        base.save_new(dest / "result.json", {"assessment": assessment,
                                              "elapsed_seconds": time.monotonic()-started})
        return 0
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
                                                  "message": str(exc),
                                                  "traceback": traceback.format_exc(),
                                                  "elapsed_seconds": time.monotonic()-started})
        return 2


def label(path, case, stage):
    dest = folder(path, case.name, stage)
    receipt = json.loads((dest / "receipt.json").read_text())
    result_path = dest / "raw_result.json"
    failure = None
    if (dest / "exception.json").is_file():
        failure = json.loads((dest / "exception.json").read_text())
    status = "hard_timeout" if receipt.get("hard_timeout") else (
        "failed" if receipt.get("returncode") != 0 else "returned")
    row = {"status": status, "feasible": False, "optimality": "unknown",
           "plan": None, "plan_hash": None, "load": None, "ops_cost": None,
           "objective_exact": None, "lower_exact": None, "upper_exact": None,
           "elapsed_seconds": receipt.get("elapsed_seconds"), "failure": failure,
           "receipt": receipt, "native_status": None}
    if not result_path.is_file():
        return row
    raw = json.loads(result_path.read_text())["result"]
    m = market(case, stage if stage in ("source0", "source1") else "target")
    row["native_status"] = raw.get("status")
    cert, mix = raw.get("lower_certificate"), raw.get("mixture")
    assessment_path = dest / "result.json"
    assessment = (json.loads(assessment_path.read_text()).get("assessment", {})
                  if assessment_path.is_file() else {})
    row["bounds_replay"] = {
        "global_certificate_replayed": assessment.get("global_certificate_replayed") is True,
        "mixture_replayed": assessment.get("mixture_replayed") is True}
    if cert is not None and cert.get("lower_exact") is not None:
        key = ("lower_exact" if row["bounds_replay"]["global_certificate_replayed"]
               else "unverified_native_lower_exact")
        row[key] = cert["lower_exact"]
    if mix is not None and mix.get("objective_exact") is not None:
        key = ("native_mixture_upper_exact" if row["bounds_replay"]["mixture_replayed"]
               else "unverified_native_mixture_upper_exact")
        row[key] = mix["objective_exact"]
    eligible = []
    for column in raw.get("columns", []):
        replay = nh.replay_column(case, column, compact.EXTRACTION_POLICY)
        cost = Fraction(replay["ops_cost"]) + nh.supply(m, replay["load"])
        eligible.append((cost, column["key"], column, replay))
    if eligible:
        cost, _, column, replay = min(eligible, key=lambda x: (x[0], x[1]))
        row.update(feasible=True, plan=column["plan"], plan_hash=nr.digest(column["plan"]),
                   load=replay["load"], ops_cost=replay["ops_cost"],
                   objective_exact=str(cost), upper_exact=str(cost),
                   column_key=column["key"])
    return row


def catalog_row(path, seed, stage):
    case = make_case(seed)
    kind = stage if stage in ("source0", "source1") else "target"
    m = market(case, kind)
    return {"row_id": case.name + "/" + stage, "base_group": f"learning_s{seed}",
            "split": SPLITS[seed], "case": asdict(case), "case_identity": case.identity(),
            "market": asdict(m), "market_identity": m.identity(),
            "market_name": kind, "market_role": "source" if kind != "target" else "target",
            "market_prices": list(m.a), "market_quadratic": list(m.b),
            "arm": "source" if kind != "target" else stage,
            "label": label(path, case, stage)}


def train_before_dev_cold(path):
    target = Path(path)
    receipt_path = target / "learning_receipt.json"
    if receipt_path.exists():
        return json.loads(receipt_path.read_text())
    output = target / "learned"
    if output.exists() or (target / "learning_launch.json").exists():
        receipt = {"status": "interrupted_unreceipted", "returncode": None,
                   "elapsed_seconds": None, "before_dev_cold": True,
                   "catalog_sha256": base.sha(target / "catalog.jsonl"),
                   "source_hashes": {key: value for key, value in source_hashes().items()
                                     if "learned_proposals" in key or "train_fleet_proposals" in key},
                   "runtime": sizing.software_runtime(), "output_hashes": {}}
        base.save_new(receipt_path, receipt)
        return receipt
    command = [sys.executable, "-m", "experiments.train_fleet_proposals",
               "--catalog", str(target / "catalog.jsonl"),
               "--frozen", str(target / "frozen.json"),
               "--output-dir", str(output)]
    learner_hashes = {key: value for key, value in source_hashes().items()
                      if "learned_proposals" in key or "train_fleet_proposals" in key}
    base.save_new(target / "learning_launch.json", {"command": command,
                                                     "hard_seconds": 45,
                                                     "catalog_sha256": base.sha(target / "catalog.jsonl"),
                                                     "source_hashes": learner_hashes,
                                                     "runtime": sizing.software_runtime()})
    started = time.monotonic()
    try:
        with (target / "learning_stdout.txt").open("xb") as stdout, \
                (target / "learning_stderr.txt").open("xb") as stderr:
            result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                    timeout=45, check=False)
        rc, failure = result.returncode, None
    except subprocess.TimeoutExpired:
        rc, failure = 124, "hard_timeout"
    except Exception as exc:
        rc, failure = 1, repr(exc)
    receipt = {"status": "completed" if rc == 0 else "failed", "returncode": rc,
               "failure": failure, "elapsed_seconds": time.monotonic()-started,
               "before_dev_cold": True,
               "catalog_sha256": base.sha(target / "catalog.jsonl"),
               "source_hashes": learner_hashes, "runtime": sizing.software_runtime(),
               "output_hashes": {p.name: base.sha(p) for p in sorted(output.glob("*")) if p.is_file()}}
    base.save_new(receipt_path, receipt)
    return receipt


def append_catalog(path, row):
    file = Path(path) / "catalog.jsonl"
    existing = [json.loads(line) for line in file.read_text().splitlines()] if file.exists() else []
    matches = [item for item in existing if item["row_id"] == row["row_id"]]
    if matches:
        if len(matches) != 1 or base.canonical(matches[0]) != base.canonical(row):
            raise ValueError("Catalog row conflict")
        return
    with file.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def controller(path):
    target = attempt(path)
    frozen(target)
    controller_started = time.monotonic()
    with (target / ".controller.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another controller holds the exclusive run lock") from exc
        if not (target / "controller_started.json").exists():
            base.save_new(target / "controller_started.json", {"protocol": PROTOCOL,
                                                                  "utc": time.time()})
        for seed in ACTIVE:
            case = make_case(seed)
            for stage in stages(seed):
                if time.monotonic() - controller_started > CONTROLLER_SECONDS - CHILD_SECONDS:
                    raise TimeoutError("Controller budget exhausted before next cell")
                if SPLITS[seed] == "dev" and stage == "cold":
                    train_before_dev_cold(target)
                dest = folder(target, case.name, stage)
                if (dest / "receipt.json").exists():
                    append_catalog(target, catalog_row(target, seed, stage))
                    continue
                if dest.exists():
                    raise ValueError("Interrupted unreceipted cell preserved: " + str(dest))
                dest.mkdir(parents=True, exist_ok=False)
                command = [sys.executable, "-m", "experiments.learning_campaign", "worker",
                           "--attempt", str(target), "--case", case.name, "--stage", stage]
                base.launch_child(target, case.name, 0, stage, CHILD_SECONDS, command=command)
                append_catalog(target, catalog_row(target, seed, stage))
        rows = [json.loads(line) for line in (target / "catalog.jsonl").read_text().splitlines()]
        base.save_new(target / "summary.json", {"protocol": PROTOCOL,
                                                 "declared_cells": sum(len(stages(seed)) for seed in ACTIVE),
                                                 "accounted_cells": len(rows),
                                                 "feasible_cells": sum(bool(r["label"]["feasible"]) for r in rows),
                                                 "learning_receipt": json.loads((target / "learning_receipt.json").read_text()),
                                                 "test_groups_unobserved": True,
                                                 "scientific_admission": "pending independent result review"})
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case")
    parser.add_argument("--stage", choices=STAGES)
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(design(), sort_keys=True, indent=2))
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
    if not args.case or not args.stage:
        parser.error("worker needs --case and --stage")
    return worker(args.attempt, args.case, args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
