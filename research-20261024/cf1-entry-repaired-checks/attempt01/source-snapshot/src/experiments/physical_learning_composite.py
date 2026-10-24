"""Materialize an independently hashed train-only composite after continuation completes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from egglab import physical_learning_composite as composite
from experiments import computational_benchmark as base

DEFAULT_OUTPUT = base.ROOT / "result/physical_learning/20260930-shard00-composite-v2"
POLICY_FILES = (
    "src/egglab/physical_learning_composite.py",
    "src/experiments/physical_learning_composite.py",
    "src/tests/test_physical_learning_composite.py",
    "research-20260930/learning-campaign/PHYSICAL_COMPOSITE_INTERFACE.md",
    "src/egglab/physical_learning_dataset.py",
)


def write(output=DEFAULT_OUTPUT):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Composite output is immutable and already exists")
    dataset = composite.ingest()
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in (("cases.jsonl", dataset["cases"]),
            ("source_inputs.jsonl", dataset["source_inputs"]),
            ("source_outcomes.jsonl", dataset["source_outcomes"]),
            ("target_inputs.jsonl", dataset["target_inputs"]),
            ("target_outcomes.jsonl", dataset["target_outcomes"])):
        with (output / name).open("x") as stream:
            for row in rows:
                stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
    base.save_new(output / "health.json", dataset["health"])
    receipt = {"schema": dataset["schema"], "train_only": True,
        "parent_frozen_source_commit": dataset["parent_frozen_source_commit"],
        "continuation_frozen_source_commit": dataset["continuation_frozen_source_commit"],
        "parent_preemption_job_id": dataset["parent_preemption"]["job_id"],
        "continuation_job_id": dataset["continuation_wrapper"]["job_id"],
        "input_hashes": dataset["input_hashes"],
        "adapter_policy_hashes": {name: base.sha(base.ROOT / name) for name in POLICY_FILES},
        "output_hashes": {file.name: base.sha(file) for file in output.iterdir() if file.is_file()},
        "eligible_complete_pairs": len(dataset["health"]["eligible_complete_pairs"]),
        "excluded_pairs": len(dataset["health"]["pair_exclusions"]),
        "no_model_fit": True}
    base.save_new(output / "dataset_receipt.json", receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    print(json.dumps(write(args.output), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
