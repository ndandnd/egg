from pathlib import Path

import pytest

from experiments import physical_learning_continuation as run


def test_archived_partition_is_exact_never_launched_suffix():
    design = run.manifest()  # Pure hashes and saved accounting; no solver.
    assert len(design["parent_completed_cell_ids"]) == 40
    assert len(design["remaining_cells"]) == 23
    assert design["interrupted"]["base_id"] == 10004
    assert design["interrupted"]["stage"] == "source0_charge_late"
    assert design["interrupted"]["receipt"] is None
    assert design["interrupted"]["feasible"] is None
    assert design["interrupted"]["objective_exact"] is None
    assert design["interrupted"]["elapsed_child_seconds"] is None
    assert design["interrupted"]["parent_slurm_elapsed_seconds"] == 713
    assert len(set(row["row_id"] for row in design["remaining_cells"])) == 23
    assert set(design["parent_completed_cell_ids"]).isdisjoint(
        row["row_id"] for row in design["remaining_cells"])
    assert design["interrupted"]["row_id"] not in {
        row["row_id"] for row in design["remaining_cells"]}


def test_exclusive_attempt_rejects_other_paths(tmp_path):
    with pytest.raises(ValueError, match="exclusive"):
        run.attempt(tmp_path / "different-attempt")


def test_source_plan_independently_replays_archived_parent():
    case, row, replay = run.source_plan(10000, "source0")
    assert row["label"]["feasible"] is True
    assert row["case_identity"] == case.identity()
    assert row["label"]["load"] == replay["load"]


def test_wrapper_and_manifest_budget_are_bounded():
    wrapper = Path(run.ROOT / "src/cluster/physical_learning_continuation.sbatch").read_text()
    assert "--time=00:45:00" in wrapper
    assert "--cpus-per-task=1" in wrapper and "--mem=8G" in wrapper
    assert "--no-requeue" in wrapper and "--exclude=scaglione-compute-01" in wrapper
    assert "2600s" in wrapper and "trap on_term TERM" in wrapper
    assert 23 * run.CHILD_SECONDS < run.CONTROLLER_SECONDS < 2600 < 2700
