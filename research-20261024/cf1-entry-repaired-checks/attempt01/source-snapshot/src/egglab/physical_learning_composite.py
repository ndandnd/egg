"""Admission of preempted shard 0 plus its no-retry continuation."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path

from egglab import learned_proposals as edge
from egglab import native_hull as nh
from egglab import native_recharge as nr
from egglab import physical_learning_dataset as v1
from experiments import computational_benchmark as base
from experiments import physical_learning_campaign as old
from experiments import physical_learning_continuation as continuation

SCHEMA = "physical-learning-composite-v2"


class ExcludedComposite(ValueError):
    """The union is incomplete or contradicts saved physical evidence."""


def _read(path):
    return json.loads(Path(path).read_text())


def _catalog(path):
    return [json.loads(line) for line in (Path(path) / "catalog.jsonl").read_text().splitlines()]


def _status(receipt):
    return "hard_timeout" if receipt.get("hard_timeout") else (
        "failed" if receipt.get("returncode") != 0 else "returned")


def _topology(plan):
    return sorted(mid for vehicle in plan["vehicles"] for mid in vehicle["movements"])


def _equal(a, b):
    return base.canonical(a) == base.canonical(b)


def _wrapper(cont):
    files = sorted(cont.parent.glob(cont.name + ".slurm_wrapper_receipt.*.json"))
    if len(files) != 1:
        raise ExcludedComposite("Exactly one continuation wrapper receipt required")
    receipt = _read(files[0])
    if (files[0].name != cont.name + ".slurm_wrapper_receipt." + str(receipt.get("job_id")) + ".json"
            or receipt.get("parent_job_id") != "703461" or any(receipt.get(k) != 0 for k in (
            "returncode", "freeze_returncode", "preflight_returncode", "controller_returncode"))
            or receipt.get("signal") != "none"):
        raise ExcludedComposite("Continuation wrapper did not complete all phases")
    return files[0], receipt


def ingest(parent=None, continuation_attempt=None):
    """Validate the 40+1+23 partition; never construct a receipt for cell 41."""
    parent = continuation.PARENT if parent is None else Path(parent).resolve()
    cont = continuation.ATTEMPT if continuation_attempt is None else Path(continuation_attempt).resolve()
    if parent != continuation.PARENT.resolve() or cont != continuation.ATTEMPT.resolve():
        raise ExcludedComposite("Only frozen shard-0 parent and exclusive continuation may join")
    parent_manifest, _, parent_rows, names = continuation.parent_partition(full_file_check=True)
    design = _read(cont / "manifest.json")
    frozen = _read(cont / "frozen.json")
    summary = _read(cont / "summary.json")
    if (design != continuation.manifest()
            or design.get("protocol") != continuation.PROTOCOL
            or design.get("parent_attempt") != str(parent.relative_to(base.ROOT))
            or design.get("parent_manifest_sha256") != base.sha(parent / "manifest.json")
            or design.get("parent_catalog_sha256") != base.sha(parent / "catalog.jsonl")
            or design.get("parent_accounting_sha256") != base.sha(continuation.ACCOUNTING)
            or design.get("parent_file_inventory_sha256") != base.sha(continuation.PARENT_FILE_MANIFEST)
            or design.get("parent_input_hashes") != continuation.parent_inputs()
            or design.get("interrupted", {}).get("receipt") is not None
            or design.get("interrupted", {}).get("status") != "preempted_unreceipted_censored"
            or design.get("remaining_cells") != continuation.manifest()["remaining_cells"]
            or frozen.get("protocol") != continuation.PROTOCOL
            or frozen.get("manifest_sha256") != base.sha(cont / "manifest.json")
            or frozen.get("source_hashes") != continuation.source_hashes()
            or summary.get("protocol") != continuation.PROTOCOL
            or summary.get("new_accounted_cells") != 23
            or summary.get("parent_completed_cells") != 40
            or summary.get("parent_interrupted_cells") != 1
            or summary.get("combined_cell_accounting") != 64):
        raise ExcludedComposite("Continuation manifest/freeze/summary lineage changed")
    wrapper_file, wrapper = _wrapper(cont)
    new_rows = _catalog(cont)
    if len(new_rows) != 23 or [r.get("row_id") for r in new_rows] != [
            r["row_id"] for r in design["remaining_cells"]]:
        raise ExcludedComposite("Continuation catalog is not exact 23-cell suffix")
    if summary.get("new_feasible_cells") != sum(bool(r["label"].get("feasible")) for r in new_rows):
        raise ExcludedComposite("Continuation summary contradicts catalog")
    accounting = _read(continuation.ACCOUNTING)
    row_records = []
    inputs = [parent / f for f in ("manifest.json", "frozen.json", "catalog.jsonl")]
    inputs += [continuation.ACCOUNTING, continuation.PARENT_FILE_MANIFEST]
    inputs += [cont / f for f in ("manifest.json", "frozen.json", "catalog.jsonl", "summary.json")]
    inputs.append(wrapper_file)
    for i, (base_id, stage) in enumerate(old.cells(0)):
        name = names[base_id]
        cell_id = name + "/" + stage
        if i == 40:
            dest = continuation.folder(parent, base_id, stage, names)
            if (dest / "receipt.json").exists() or (dest / "fixed_charge.json").exists():
                raise ExcludedComposite("Interrupted cell gained receipt or replay evidence")
            inputs.append(dest / "launch.json")
            row_records.append((base_id, stage, None, parent, "703461", "preempted_unreceipted"))
            continue
        is_parent = i < 40
        origin = parent if is_parent else cont
        row = parent_rows[i] if is_parent else new_rows[i-41]
        if row.get("row_id") != cell_id:
            raise ExcludedComposite("Cross-origin row order or cell identity mismatch")
        dest = continuation.folder(origin, base_id, stage, names) if is_parent else \
            cont / name / "state0" / stage
        receipt_file = dest / "receipt.json"
        if not receipt_file.is_file() or not (dest / "launch.json").is_file():
            raise ExcludedComposite("Completed row lacks original launch/child receipt")
        receipt = _read(receipt_file)
        if row.get("label", {}).get("receipt") != receipt or row["label"].get("status") != _status(receipt):
            raise ExcludedComposite("Catalog label/receipt status differs")
        expected_row = old.catalog_row(parent, base_id, stage) if is_parent else \
            continuation.catalog_row(cont, base_id, stage)
        if not _equal(row, expected_row):
            raise ExcludedComposite("Catalog row differs from independent saved-evidence replay")
        inputs.extend((dest / "launch.json", receipt_file))
        for file in ("raw_result.json", "result.json", "fixed_charge.json", "direct_rescore.json",
                     "fixed_charge_failure.json", "exception.json"):
            if (dest / file).is_file():
                inputs.append(dest / file)
        row_records.append((base_id, stage, row, origin,
            "703461" if is_parent else wrapper["job_id"], "receipted"))
    cases, source_inputs, source_outcomes, target_inputs, target_outcomes = [], [], [], [], []
    source_bank = {}
    for base_id in old.physical.shard_ids(0):
        name = names[base_id]
        group = parent_manifest["groups"][name]
        case = edge.case_from_dict(group["case"])
        cases.append({"base_group": f"physical_v2_s{base_id}", "base_id": base_id,
            "split": "train", "generator": old.physical.GENERATOR,
            "case_identity": case.identity(), "physical_profile": group["assignment"],
            "case": group["case"], "witness_hash": group["witness_hash"]})
    for base_id, stage, row, origin, job_id, evidence_class in row_records:
        name = names[base_id]
        group = parent_manifest["groups"][name]
        case = edge.case_from_dict(group["case"])
        kind = stage if stage in old.SOURCES else stage.rsplit("_", 1)[-1]
        market = old.physical.market(case, kind)
        source = stage if stage in old.SOURCES else stage.split("_charge_", 1)[0]
        common = {"key": name + "/" + stage, "base_group": f"physical_v2_s{base_id}",
            "base_id": base_id, "case_identity": case.identity(),
            "market_identity": market.identity(), "market_kind": kind, "source": source}
        provenance = {"origin_attempt": str(origin.relative_to(base.ROOT)),
            "origin_job_id": job_id, "evidence_class": evidence_class}
        if row is None:
            label = {"status": "preempted_unreceipted_censored", "native_status": None,
                "feasible": False, "plan": None, "plan_hash": None, "objective_exact": None,
                "elapsed_seconds": None, "failure": None}
        else:
            label = row["label"]
        feasible = label.get("feasible") is True
        outcome = {**common, **provenance, "status": label.get("status"),
            "native_status": label.get("native_status"), "feasible": feasible,
            "censored": not feasible, "plan": label.get("plan"),
            "plan_hash": label.get("plan_hash"), "objective_exact": label.get("objective_exact"),
            "paid_seconds": label.get("elapsed_seconds"), "failure": label.get("failure"),
            "source_market_lower_exact": label.get("lower_exact") if stage in old.SOURCES else None,
            "source_market_upper_exact": label.get("upper_exact") if stage in old.SOURCES else None,
            "reported_objective_scope": ("source market physical incumbent" if stage in old.SOURCES
                else "curved bill of fixed-route linear-tariff LP procedure"),
            "curved_optimality_uncertified": feasible,
            "certified_for_reported_objective": False,
            "feasible_after_child_failure": bool(feasible and label.get("status") != "returned"),
            "provisional_after_native_limit": bool(feasible and (
                label.get("status") != "returned" or label.get("native_status") not in
                ("certified", "OPTIMAL", "optimal")))}
        if stage in old.SOURCES:
            source_outcomes.append(outcome)
            if feasible:
                plan = label["plan"]
                replay = nr.replay_native(case, plan)
                source_bank[(base_id, stage)] = (plan, replay, label["plan_hash"])
                source_inputs.append({**common, **provenance, "source_plan_hash": label["plan_hash"],
                    "selected_movements": _topology(plan), "source_plan": plan,
                    "source_replay": replay})
        else:
            source_entry = source_bank.get((base_id, source))
            direct = None
            if source_entry:
                direct = str(Fraction(source_entry[1]["ops_cost"]) + nh.supply(market, source_entry[1]["load"]))
            target_inputs.append({**common, **provenance, "available": source_entry is not None,
                "source_plan_hash": source_entry[2] if source_entry else None,
                "selected_movements": _topology(source_entry[0]) if source_entry else None,
                "direct_exact": direct, "target_market": row["market"] if row else
                    old.asdict(market)})
            target_outcomes.append(outcome)
    if (len(cases), len(source_outcomes), len(target_outcomes)) != (8, 16, 48):
        raise ExcludedComposite("Composite row counts changed")
    health = v1.health({"cases": cases, "source_inputs": source_inputs,
        "source_outcomes": source_outcomes, "target_inputs": target_inputs,
        "target_outcomes": target_outcomes})
    health["schema"] = SCHEMA
    health["interrupted_unreceipted_cells"] = 1
    health["parent_slurm_elapsed_seconds"] = accounting["elapsed_seconds"]
    health["parent_receipted_child_seconds"] = accounting["receipted_child_seconds"]
    health["continuation_wrapper_elapsed_seconds"] = wrapper["elapsed_whole_seconds"]
    health["continuation_receipted_child_seconds"] = sum(
        row["label"]["elapsed_seconds"] for row in new_rows
        if row["label"].get("elapsed_seconds") is not None)
    return {"schema": SCHEMA, "shard": 0, "train_only": True,
        "parent_preemption": accounting, "continuation_wrapper": wrapper,
        "input_hashes": {str(file.relative_to(base.ROOT)): base.sha(file)
                         for file in sorted(set(inputs))},
        "parent_frozen_source_commit": _read(parent / "frozen.json")["source_commit"],
        "continuation_frozen_source_commit": frozen["source_commit"],
        "cases": cases, "source_inputs": source_inputs, "source_outcomes": source_outcomes,
        "target_inputs": target_inputs, "target_outcomes": target_outcomes, "health": health}
