"""Freeze exactly 32 admitted TRAIN groups for a source-route scoring study."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from egglab import physical_learning_cases as physical
from experiments import computational_benchmark as base

ROOT = base.ROOT
SHARD0 = ROOT / "result/physical_learning/20260930-shard00-composite-v2"
DATASETS = tuple(ROOT / f"result/physical_learning/20260930-shard{i:02d}-dataset-v1"
                 for i in (1, 2, 3))
OUTPUT = ROOT / "result/physical_learning/20260930-route-pool32-v1"
POLICY = "physical-route-source-pool32-admitted-train-v1"


def _read(path):
    return json.loads(Path(path).read_text())


def _rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def build(output=OUTPUT):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Pooled training output is immutable")
    receipt0 = _read(SHARD0 / "dataset_receipt.json")
    if (receipt0.get("schema") != "physical-learning-composite-v2"
            or receipt0.get("train_only") is not True
            or receipt0.get("output_hashes", {}).get("cases.jsonl") != base.sha(SHARD0 / "cases.jsonl")
            or receipt0.get("output_hashes", {}).get("source_inputs.jsonl") != base.sha(SHARD0 / "source_inputs.jsonl")):
        raise ValueError("Shard-0 composite admission/hash changed")
    cases = _rows(SHARD0 / "cases.jsonl")
    sources = _rows(SHARD0 / "source_inputs.jsonl")
    admitted = [{"shard": 0, "kind": "preempted-parent-plus-no-retry-continuation",
        "dataset_receipt_sha256": base.sha(SHARD0 / "dataset_receipt.json"),
        "case_table_sha256": base.sha(SHARD0 / "cases.jsonl"),
        "source_table_sha256": base.sha(SHARD0 / "source_inputs.jsonl")}]
    for index, dataset in enumerate(DATASETS, start=1):
        receipt = _read(dataset / "dataset_receipt.json")
        if (receipt.get("schema") != "physical-learning-dataset-v1"
                or receipt.get("status") != "complete" or receipt.get("train_only") is not True
                or receipt.get("independent_training_groups") != 8
                or len(receipt.get("shards", ())) != 1
                or receipt["shards"][0].get("shard") != index
                or any(receipt.get("output_hashes", {}).get(name) != base.sha(dataset / name)
                       for name in ("cases.jsonl", "source_inputs.jsonl"))):
            raise ValueError("Unadmitted or changed source training dataset")
        cases.extend(_rows(dataset / "cases.jsonl"))
        sources.extend(_rows(dataset / "source_inputs.jsonl"))
        admitted.append({"shard": index, "kind": "completed-single-attempt",
            "dataset": str(dataset.relative_to(ROOT)),
            "dataset_receipt_sha256": base.sha(dataset / "dataset_receipt.json"),
            "case_table_sha256": base.sha(dataset / "cases.jsonl"),
            "source_table_sha256": base.sha(dataset / "source_inputs.jsonl"),
            "raw_attempt_provenance": receipt["shards"][0]})
    expected_ids = set(range(10000, 10032))
    if (len(cases) != 32 or len(sources) != 64
            or {c.get("base_id") for c in cases} != expected_ids
            or {c.get("base_group") for c in cases} != {
                f"physical_v2_s{i}" for i in expected_ids}
            or any(c.get("split") != "train" or c.get("generator") != physical.GENERATOR
                   for c in cases)):
        raise ValueError("Pooled case registry is not exactly the 32-group TRAIN prefix")
    pairs = {(s.get("base_group"), s.get("source")) for s in sources}
    if len(pairs) != 64 or pairs != {(f"physical_v2_s{i}", source)
            for i in expected_ids for source in ("source0", "source1")}:
        raise ValueError("Pooled source fleets lack exact grouped pairs")
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in (("cases.jsonl", cases), ("source_inputs.jsonl", sources)):
        with (output / name).open("x") as stream:
            for row in rows:
                stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
    manifest = {"policy": POLICY, "train_only": True, "base_ids": list(range(10000, 10032)),
        "independent_groups": 32, "source_fleets": 64,
        "admitted_shards": admitted,
        "output_hashes": {name: base.sha(output / name)
                          for name in ("cases.jsonl", "source_inputs.jsonl")},
        "feature_policy": "case/source-market numeric edge features only; no outcome table",
        "target_outcomes_not_exported": True,
        "adapter_source_hashes": {name: base.sha(ROOT / name) for name in (
            "src/experiments/pool_physical_route_training.py",
            "src/experiments/physical_learning_dataset.py")}}
    base.save_new(output / "pool_manifest.json", manifest)
    return {"output": str(output), "manifest_sha256": base.sha(output / "pool_manifest.json"),
        "independent_groups": 32, "source_fleets": 64}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    print(json.dumps(build(args.output), sort_keys=True))


if __name__ == "__main__":
    main()
