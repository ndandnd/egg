"""Validate completed physical-label shards and freeze a train-only dataset."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from egglab import physical_learning_dataset as adapter
from experiments import computational_benchmark as base

ROOT = base.ROOT
ADAPTER_SOURCES = (
    ROOT / "src/egglab/physical_learning_dataset.py",
    ROOT / "src/experiments/physical_learning_dataset.py",
    ROOT / "research-20260930/learning-campaign/PHYSICAL_DATASET_INTERFACE.md",
)
OUTPUTS = ("cases.jsonl", "source_inputs.jsonl", "source_outcomes.jsonl",
           "target_inputs.jsonl", "target_outcomes.jsonl")


def _jsonl_new(path, rows):
    with Path(path).open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush(); os.fsync(stream.fileno())


def compile_dataset(attempts, output):
    """All-or-nothing completed train shard ingestion; no solver/model call."""
    if not attempts:
        raise ValueError("Declare at least one completed physical training shard")
    if len({str(Path(path).resolve()) for path in attempts}) != len(attempts):
        raise ValueError("Duplicate shard path")
    pieces = [adapter.ingest_attempt(path) for path in attempts]
    if len({piece["shard"] for piece in pieces}) != len(pieces):
        raise ValueError("Duplicate shard index or cross-shard attempt")
    cases = [row for piece in pieces for row in piece["cases"]]
    if len({row["base_group"] for row in cases}) != len(cases):
        raise ValueError("Cross-shard duplicate physical base group")
    dataset = {"cases": cases,
        "source_inputs": [row for piece in pieces for row in piece["source_inputs"]],
        "source_outcomes": [row for piece in pieces for row in piece["source_outcomes"]],
        "target_inputs": [row for piece in pieces for row in piece["target_inputs"]],
        "target_outcomes": [row for piece in pieces for row in piece["target_outcomes"]]}
    diagnostics = adapter.health(dataset)
    target = Path(output).resolve()
    if target.exists():
        raise ValueError("Dataset output directory already exists; immutable compile only")
    target.mkdir(parents=True, exist_ok=False)
    for name in OUTPUTS:
        _jsonl_new(target / name, dataset[name.removesuffix(".jsonl")])
    base.save_new(target / "health.json", diagnostics)
    receipt = {"schema": adapter.SCHEMA,
        "status": "complete", "train_only": True,
        "shards": [{"shard": piece["shard"], "attempt": piece["attempt"],
                    "frozen_source_commit": piece["frozen_source_commit"],
                    "frozen_source_hashes": piece["frozen_source_hashes"],
                    "input_hashes": piece["inputs"]} for piece in pieces],
        "adapter_source_hashes": {str(path.relative_to(ROOT)): base.sha(path)
                                  for path in ADAPTER_SOURCES},
        "pre_target_input_containers": {
            "case": ["physical_profile", "case"],
            "source": ["source_plan", "source_replay", "selected_movements"],
            "target": ["target_market", "direct_exact", "selected_movements"],
            "join_only_paths": ["base_id", "base_group", "key", "case_identity",
                "market_identity", "source_plan_hash", "source",
                "physical_profile.base_id", "physical_profile.split", "case.name",
                "source_plan.case_identity"],
            "future_numeric_projection_required": True,
            "excluded_from_future_fit": ["target_outcomes", "source_outcomes",
                "paid_seconds", "native_status", "bounds", "winner", "margin"]},
        "independent_training_groups": len(cases),
        "output_hashes": {name: base.sha(target / name)
                          for name in OUTPUTS + ("health.json",)}}
    base.save_new(target / "dataset_receipt.json", receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, action="append", required=True,
                        help="Explicit completed training shard; repeat for pooling")
    parser.add_argument("--output", type=Path, required=True,
                        help="New immutable output directory")
    args = parser.parse_args(argv)
    try:
        receipt = compile_dataset(args.attempt, args.output)
    except adapter.ExcludedShard as exc:
        print("Excluded incomplete/malformed shard from training dataset: " + str(exc),
              file=sys.stderr)
        return 2
    print(json.dumps({"schema": receipt["schema"],
        "independent_training_groups": receipt["independent_training_groups"],
        "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
