"""Freeze exact TRAIN registry prefixes for grouped source-route learning curves."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from egglab import physical_learning_cases as physical
from experiments import computational_benchmark as base

ROOT = base.ROOT
POLICY = "physical-route-source-pool-prefix-v3"
OUTPUTS = {
    64: ROOT / "result/physical_learning/20260930-route-pool64-v3",
    128: ROOT / "result/physical_learning/20260930-route-pool128-v3",
}
TABLES = ("cases.jsonl", "source_inputs.jsonl")


def _read(path):
    return json.loads(Path(path).read_text())


def _rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def _dataset(index):
    return ROOT / ("result/physical_learning/20260930-shard00-composite-v2" if index == 0
                   else f"result/physical_learning/20260930-shard{index:02d}-dataset-v1")


def _admit(index, dataset):
    receipt_path = dataset / "dataset_receipt.json"
    receipt = _read(receipt_path)
    schema = "physical-learning-composite-v2" if index == 0 else "physical-learning-dataset-v1"
    if (receipt.get("schema") != schema or receipt.get("train_only") is not True
            or any(receipt.get("output_hashes", {}).get(name) != base.sha(dataset / name)
                   for name in TABLES)):
        raise ValueError(f"Shard {index} has no valid admitted TRAIN receipt/tables")
    if index and (receipt.get("status") != "complete"
                  or receipt.get("independent_training_groups") != 8
                  or len(receipt.get("shards", ())) != 1
                  or receipt["shards"][0].get("shard") != index):
        raise ValueError(f"Shard {index} is not a completed single-shard admission")
    return receipt, {"shard": index, "dataset": str(dataset.relative_to(ROOT)),
        "dataset_receipt_sha256": base.sha(receipt_path),
        "case_table_sha256": base.sha(dataset / TABLES[0]),
        "source_table_sha256": base.sha(dataset / TABLES[1]),
        "health_sha256_from_receipt": receipt.get("output_hashes", {}).get("health.json"),
        "raw_attempt_provenance": receipt.get("shards")}


def build(prefix, output=None):
    if prefix not in OUTPUTS:
        raise ValueError("Only the exact 64/128 TRAIN registry prefixes are declared")
    output = Path(output or OUTPUTS[prefix]).resolve()
    if output.exists():
        raise ValueError("Pooled training output is immutable")
    # All prefix shards must be admitted before a single row is emitted. Never
    # replace an unavailable shard by a later one that finished sooner.
    cases, sources, admitted = [], [], []
    for index in range(prefix // 8):
        dataset = _dataset(index)
        _, evidence = _admit(index, dataset)
        shard_cases, shard_sources = (_rows(dataset / name) for name in TABLES)
        expected = set(range(10000 + 8*index, 10008 + 8*index))
        if (len(shard_cases) != 8 or {r.get("base_id") for r in shard_cases} != expected
                or {r.get("base_group") for r in shard_cases} != {
                    f"physical_v2_s{i}" for i in expected}
                or any(r.get("split") != "train" or r.get("generator") != physical.GENERATOR
                       for r in shard_cases)):
            raise ValueError(f"Shard {index} does not match its eight registry cases")
        cases.extend(shard_cases); sources.extend(shard_sources); admitted.append(evidence)
    by_group = {r["base_group"]: r for r in cases}
    if len(by_group) != prefix:
        raise ValueError("Duplicate pooled timetable")
    seen = set()
    for row in sources:
        pair = (row.get("base_group"), row.get("source"))
        if (pair[0] not in by_group or pair[1] not in ("source0", "source1")
                or pair in seen or row.get("base_id") != by_group[pair[0]]["base_id"]):
            raise ValueError("Duplicate, foreign, or malformed source input")
        seen.add(pair)
    eligibility = []
    for case in cases:
        group = case["base_group"]
        observed = [s for s in ("source0", "source1") if (group, s) in seen]
        missing = [s for s in ("source0", "source1") if s not in observed]
        row = {"base_id": case["base_id"], "base_group": group,
            "intended_source_count": 2, "observed_source_count": len(observed),
            "observed_sources": observed, "missing_source_labels": missing,
            "eligible_for_observed_source_supervision": bool(observed),
            "eligible_for_full_pair_supervision": len(observed) == 2}
        if case["base_id"] == 10037 and missing == ["source0"]:
            row["registered_censor"] = {"failed_source": "source0",
                "dependent_target_censors": 3,
                "evidence": "admitted shard04 receipt and pinned health hash; no target table exported"}
        eligibility.append(row)
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in zip(TABLES, (cases, sources)):
        with (output / name).open("x") as stream:
            for row in rows:
                stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
    manifest = {"policy": POLICY, "train_only": True,
        "base_ids": list(range(10000, 10000 + prefix)),
        "independent_groups_intended": prefix,
        "groups_eligible_observed": sum(r["eligible_for_observed_source_supervision"] for r in eligibility),
        "groups_eligible_full_pair": sum(r["eligible_for_full_pair_supervision"] for r in eligibility),
        "source_fleets_intended": 2*prefix, "source_fleets_observed": len(sources),
        "group_eligibility": eligibility, "admitted_shards": admitted,
        "output_hashes": {name: base.sha(output / name) for name in TABLES},
        "feature_policy": "case/source-market numeric edge features only; no outcome table",
        "target_outcomes_not_exported": True,
        "adapter_source_hashes": {name: base.sha(ROOT / name) for name in (
            "src/experiments/pool_physical_route_training_v3.py",
            "src/experiments/physical_learning_dataset.py")}}
    base.save_new(output / "pool_manifest.json", manifest)
    return {"output": str(output), "manifest_sha256": base.sha(output / "pool_manifest.json"),
        "independent_groups_intended": prefix,
        "groups_eligible_observed": manifest["groups_eligible_observed"],
        "source_fleets_observed": len(sources)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=int, choices=tuple(OUTPUTS), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(build(args.prefix, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
