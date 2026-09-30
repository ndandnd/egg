"""Train and evaluate the developmental native fleet-start prior from a catalog.

Usage: PYTHONPATH=src python3 -m experiments.train_fleet_proposals \
    --catalog result/learning_campaign/20260930-attempt1/catalog.jsonl \
    --output-dir result/learning_campaign/20260930-attempt1/learned
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import tempfile
import time
import traceback

import numpy as np

from egglab import learned_proposals as lp


def read_catalog(path):
    rows, seen, groups, physical_ids, names = [], set(), {}, {}, {}
    with Path(path).open() as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid catalog line {number}: {exc}") from exc
            row_id = str(row["row_id"])
            group = str(row["base_group"])
            split = row["split"]
            if row_id in seen:
                raise ValueError(f"Duplicate catalog row_id {row_id}")
            if split not in ("train", "dev", "test"):
                raise ValueError(f"Unknown split on catalog line {number}")
            if group in groups and groups[group] != split:
                raise ValueError(f"Timetable group {group} crosses splits")
            case_id = row["case_identity"]
            case_name = row["case"]["name"]
            for key, observed, label in ((case_id, physical_ids, "case identity"),
                                         (case_name, names, "case name")):
                if key in observed and observed[key] != (group, split):
                    raise ValueError(f"{label} aliases timetable groups or splits")
                observed[key] = (group, split)
            seen.add(row_id); groups[group] = split; rows.append(row)
    return rows


def _target_rows(rows, split):
    # Target incumbents may be absent/unresolved. Only target market features
    # are read at prediction time; label.plan is never passed to inference.
    return [r for r in rows if r.get("split") == split
        and r.get("arm") in ("cold", "proposal_target")]


def append_dev_design_target(rows, frozen_path):
    """Create market-only dev inference inputs from a frozen design before solves."""
    design = json.loads(Path(frozen_path).read_text())["design"]["groups"]
    extra = []
    for group in design.values():
        if group["split"] != "dev":
            continue
        market = group["markets"]["target"]
        extra.append({"row_id":group["base_group"]+"/proposal_target",
            "base_group":group["base_group"], "split":"dev",
            "case":group["case"], "case_identity":group["case_identity"],
            "market":market, "market_prices":market["a"],
            "market_quadratic":market["b"], "arm":"proposal_target",
            "label":{"feasible":False, "plan":None}})
    return [row for row in rows if row.get("split") != "dev" or row.get("arm") != "cold"] + extra


def _summary(proposal):
    chosen = proposal["chosen"]
    return {"policy":proposal["policy"], "target_row_id":proposal["target_row_id"],
        "base_group":proposal["base_group"], "case_identity":proposal["case_identity"],
        "proposed_topology":proposal["proposed_topology"],
        "projection":proposal["projection"],
        "online_timing_seconds":proposal["online_timing_seconds"],
        "source_pool_acquisition_seconds":proposal["source_pool_acquisition_seconds"],
        "source_row_id":chosen["source_row_id"], "plan":chosen["plan"],
        "replay_ok":chosen["replay_ok"], "learned_score":chosen["score"],
        "topology_distance":chosen["topology_distance"],
        "direct_bill":chosen["direct_bill"], "controls":proposal["controls"],
        "candidates":[{k:v for k,v in c.items() if k != "plan"}
            for c in proposal["candidates"]],
        "interpretation":"Physical fleet MIP-start proposal; solver acceptance and savings unverified"}


def _evaluate(rows, split, model):
    output, omitted = [], []
    for target in _target_rows(rows, split):
        source_rows = [r for r in rows if r.get("split") == split and r.get("arm") == "source"]
        try:
            proposal = lp.rank_candidates(model, target, source_rows)
        except ValueError as exc:
            omitted.append({"row_id":target["row_id"], "reason":str(exc)})
            continue
        output.append(_summary(proposal))
    return output, omitted


def run(rows):
    # Test is reserved. The first campaign only trains and assesses dev groups.
    if any(r.get("split") == "test" for r in rows):
        raise ValueError("Reserved test rows are not admitted to this developmental trainer")
    model = lp.fit(rows)
    dev, omitted = _evaluate(rows, "dev", model)
    train_groups = sorted({str(r["base_group"]) for r in rows if r.get("split") == "train"})
    cv = []
    for group in train_groups:
        subset = [r for r in rows if r.get("split") == "train" and str(r["base_group"]) != group]
        if not any(r.get("label", {}).get("feasible") and r.get("arm") in ("source", "cold") for r in subset):
            continue
        leaveout_model = lp.fit(subset)
        held = [{**r, "split":"dev"} for r in rows if str(r["base_group"]) == group]
        proposal, failed = _evaluate(held, "dev", leaveout_model)
        for item in proposal:
            cv.append({"held_out_group":group, "target_row_id":item["target_row_id"],
                "chosen_source_row_id":item["source_row_id"], "controls":item["controls"],
                "candidate_bills":{c["source_row_id"]:c["direct_bill"] for c in item["candidates"]}})
        omitted.extend({"row_id":item["row_id"], "reason":item["reason"],
            "held_out_group":group} for item in failed)
    report = {"policy":lp.POLICY, "training_groups":list(model.training_groups),
        "training_rows":list(model.training_rows), "train_group_count":len(train_groups),
        "dev_target_count":len(_target_rows(rows, "dev")),
        "dev_proposal_count":len(dev), "leave_one_group_out":cv, "omitted":omitted,
        "scientific_status":"developmental; best-known incumbent labels are provisional; no solve-time gain established",
        "controls":["first_source", "nearest_price", "cheapest_bill"],
        "test_policy":"reserved test groups excluded from fit and this evaluation"}
    return model.to_dict(), dev, report


def _write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, prefix=".tmp-", delete=False) as stream:
        temp = Path(stream.name)
        if isinstance(data, list):
            for item in data:
                stream.write(json.dumps(item, sort_keys=True, allow_nan=False)+"\n")
        else:
            json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temp, path)  # atomic create; never replace an earlier result
    finally:
        temp.unlink(missing_ok=True)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frozen", type=Path,
        help="Frozen design enables dev inference before dev target solve")
    args = parser.parse_args(argv)
    names = ("model.json", "proposals.jsonl", "report.json", "training_receipt.json")
    if any((args.output_dir / name).exists() for name in names):
        raise ValueError("Learning output already exists; immutable attempt is not overwritten")
    started = time.perf_counter()
    source_paths = (Path(__file__), Path(lp.__file__))
    receipt = {"policy":lp.POLICY, "status":"started",
        "inputs":{"catalog_sha256":_sha(args.catalog),
                  "frozen_sha256":_sha(args.frozen) if args.frozen else None},
        "sources":{str(p):_sha(p) for p in source_paths},
        "runtime":{"python":platform.python_version(), "numpy":np.__version__},
        "output_files":{}}
    try:
        rows = read_catalog(args.catalog)
        if args.frozen:
            rows = append_dev_design_target(rows, args.frozen)
        model, proposals, report = run(rows)
        _write_atomic(args.output_dir / "model.json", model)
        _write_atomic(args.output_dir / "proposals.jsonl", proposals)
        _write_atomic(args.output_dir / "report.json", report)
        receipt.update(status="complete", input_rows=len(rows),
            training_rows=len(model["training_rows"]), dev_proposals=len(proposals),
            output_files={name:_sha(args.output_dir / name) for name in
                ("model.json", "proposals.jsonl", "report.json")})
    except Exception as exc:
        receipt.update(status="failed", failure={"type":type(exc).__name__,
            "message":str(exc), "traceback":traceback.format_exc()})
        raise
    finally:
        receipt["elapsed_seconds"] = time.perf_counter()-started
        _write_atomic(args.output_dir / "training_receipt.json", receipt)
    print(json.dumps({"training_groups":report["train_group_count"],
        "dev_proposals":report["dev_proposal_count"],
        "output_dir":str(args.output_dir)}, sort_keys=True))


if __name__ == "__main__":
    main()
