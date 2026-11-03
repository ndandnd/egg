import json

import pytest

from egglab import physical_learning_composite as composite
from egglab import physical_learning_dataset as v1
from experiments import physical_learning_continuation as run


def test_incomplete_continuation_excluded_without_fabricating_parent_receipt():
    with pytest.raises((FileNotFoundError, composite.ExcludedComposite)):
        composite.ingest()
    interrupted = run.manifest()["interrupted"]
    assert interrupted["receipt"] is None
    assert interrupted["feasible"] is None


def test_wrapper_requires_one_successful_job(tmp_path):
    cont = tmp_path / "attempt"
    good = {"parent_job_id": "703461", "job_id": "900001", "signal": "none",
        "returncode": 0, "freeze_returncode": 0, "preflight_returncode": 0,
        "controller_returncode": 0, "elapsed_whole_seconds": 15}
    file = tmp_path / "attempt.slurm_wrapper_receipt.900001.json"
    file.write_text(json.dumps(good))
    assert composite._wrapper(cont)[1]["job_id"] == "900001"
    file.write_text(json.dumps({**good, "signal": "TERM", "returncode": 143}))
    with pytest.raises(composite.ExcludedComposite, match="did not complete"):
        composite._wrapper(cont)
    file.write_text(json.dumps(good))
    second = tmp_path / "attempt.slurm_wrapper_receipt.900002.json"
    second.write_text(json.dumps({**good, "job_id": "900002", "returncode": 143}))
    with pytest.raises(composite.ExcludedComposite, match="Exactly one"):
        composite._wrapper(cont)


def test_synthetic_unreceipted_censor_is_excluded_from_pairs():
    group = "physical_v2_s10000"
    case = {"base_group": group, "base_id": 10000,
        "physical_profile": {"profile": {"name": "control"}, "services": 20}}
    source_inputs = [{"base_group": group, "source": source,
        "selected_movements": [source], "source_plan_hash": source}
        for source in ("source0", "source1")]
    source_outcomes = [{"base_group": group, "source": source, "status": "returned",
        "native_status": "certified"}
        for source in ("source0", "source1")]
    targets = []
    for tariff in v1.TARIFFS:
        for source in ("source0", "source1"):
            censor = tariff == "late" and source == "source0"
            targets.append({"base_group": group, "market_kind": tariff, "source": source,
                "status": "preempted_unreceipted_censored" if censor else "returned",
                "native_status": None if censor else "OPTIMAL",
                "feasible": not censor, "censored": censor,
                "objective_exact": None if censor else "2",
                "curved_optimality_uncertified": not censor,
                "provisional_after_native_limit": False,
                "feasible_after_child_failure": False})
    health = v1.health({"cases": [case], "source_inputs": source_inputs,
        "source_outcomes": source_outcomes, "target_outcomes": targets})
    assert len(health["eligible_complete_pairs"]) == 2
    assert len(health["pair_exclusions"]) == 1
    assert health["pair_exclusions"][0]["tariff"] == "late"
    assert health["by_regime_and_size"]["control/n20"]["censored_target_labels"] == 1
