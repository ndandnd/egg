import json

import numpy as np
import pytest

from egglab import physical_route_model_v3 as model
from experiments import pool_physical_route_training_v3 as pool


@pytest.mark.parametrize("prefix,expected", [(64, (40, 8, 16)), (128, (80, 16, 32))])
def test_exact_prefix_registry_splits_remain_intact(prefix, expected):
    groups = tuple(f"physical_v2_s{i}" for i in range(10000, 10000 + prefix))
    outers = []
    for fold in range(4):
        fit, inner, outer = model.grouped_split(groups, fold)
        assert tuple(map(len, (fit, inner, outer))) == expected
        assert not (set(fit) & set(inner) or set(fit) & set(outer) or set(inner) & set(outer))
        assert outer == tuple(g for index, g in enumerate(groups) if index % 4 == fold)
        outers.append(set(outer))
    assert set.union(*outers) == set(groups)
    with pytest.raises(ValueError, match="exact sorted TRAIN prefix"):
        model.grouped_split(groups[1:] + ("physical_v2_s99999",), 0)


def test_censored_and_zero_source_groups_have_explicit_equal_group_weights():
    samples = []
    for group, sources in (("g0", ("source1",)), ("g1", ("source0", "source1"))):
        for source in sources:
            n = 3 if source == "source1" else 6
            samples.append({"group": group, "source": source,
                "x": np.ones((n, 17)), "y": np.ones(n)})
    _, _, weights = model._stack(samples)
    manifest = model._weight_manifest(samples)
    assert weights.sum() == pytest.approx(1)
    assert [r["fleet_weight"] for r in manifest] == pytest.approx([.5, .25, .25])
    assert [weights[:3].sum(), weights[3:9].sum(), weights[9:].sum()] == pytest.approx([.5, .25, .25])
    eligibility = [
        {"base_group": "g0", "observed_source_count": 1,
         "eligible_for_observed_source_supervision": True, "eligible_for_full_pair_supervision": False},
        {"base_group": "g1", "observed_source_count": 2,
         "eligible_for_observed_source_supervision": True, "eligible_for_full_pair_supervision": True},
        {"base_group": "g2", "observed_source_count": 0,
         "eligible_for_observed_source_supervision": False, "eligible_for_full_pair_supervision": False},
    ]
    counts = model._partition_eligibility(eligibility, {"g0", "g1", "g2"})
    assert counts["intended_groups"] == 3
    assert counts["eligible_observed_groups"] == 2
    assert counts["eligible_full_pair_groups"] == 1
    assert counts["intended_source_fleets"] == 6
    assert counts["observed_source_fleets"] == 3
    with pytest.raises(ValueError, match="no eligible"):
        model._stack([])


def test_primary_metric_macro_weights_singleton_timetable_equally():
    def row(ap, topk):
        return {**{key: .5 for key in model.PERFORMANCE_METRICS},
                "average_precision": ap,
                "input_trip_count_topk_recall_mean_by_fleet": topk,
                "positive_count": 1, "negative_count": 2}
    pair = model._macro_metrics([row(.2, .1), row(.6, .5)])
    singleton = model._macro_metrics([row(.8, .9)])
    outer = model._macro_metrics([pair, singleton])
    assert pair["average_precision"] == pytest.approx(.4)
    assert outer["average_precision"] == pytest.approx(.6)
    assert outer["input_trip_count_topk_recall_mean_by_fleet"] == pytest.approx(.6)
    assert outer["eligible_units"] == 2


def test_admitted_64_pool_preserves_shard04_censor_without_outcome_tables(tmp_path):
    result = pool.build(64, tmp_path / "pool64")  # Admission only; no fit or native replay.
    manifest = json.loads((tmp_path / "pool64/pool_manifest.json").read_text())
    assert result["independent_groups_intended"] == 64
    assert result["groups_eligible_observed"] == 64
    assert result["source_fleets_observed"] == 127
    assert manifest["groups_eligible_full_pair"] == 63
    assert [r["shard"] for r in manifest["admitted_shards"]] == list(range(8))
    censored = manifest["group_eligibility"][37]
    assert censored["base_group"] == "physical_v2_s10037"
    assert censored["observed_sources"] == ["source1"]
    assert censored["missing_source_labels"] == ["source0"]
    assert censored["registered_censor"]["dependent_target_censors"] == 3
    assert sorted(p.name for p in (tmp_path / "pool64").iterdir()) == [
        "cases.jsonl", "pool_manifest.json", "source_inputs.jsonl"]
    data = model.load_pool(tmp_path / "pool64",
        expected_manifest_sha256=result["manifest_sha256"], prefix=64)
    assert len(data["groups"]) == 64 and len(data["samples"]) == 127
    assert [s["source"] for s in data["samples"] if s["group"] == "physical_v2_s10037"] == ["source1"]
    with pytest.raises(ValueError, match="hash"):
        model.load_pool(tmp_path / "pool64", expected_manifest_sha256="0"*64, prefix=64)


def test_128_pool_refuses_incomplete_registry_before_creating_output(tmp_path, monkeypatch):
    original = pool._dataset
    monkeypatch.setattr(pool, "_dataset", lambda index: tmp_path / "unadmitted" if index == 9 else original(index))
    output = tmp_path / "pool128"
    with pytest.raises((FileNotFoundError, ValueError)):
        pool.build(128, output)
    assert not output.exists()
