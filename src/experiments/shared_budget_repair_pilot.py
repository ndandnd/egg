"""Two-cell 30-second shared-cover study on the frozen 28-service dev case."""
from __future__ import annotations

from experiments import energy_aware_repair_pilot as shared
from experiments import shared_interval_repair_pilot as prior

ROOT = shared.ROOT
ATTEMPT = ROOT / "result/learning_repair/20260930-shared-budget-attempt1"
PROTOCOL = "egg-shared-interval-cover-budget-development-20260930-v1"
CELLS = (
    ("learning_s2017_n28", "cost_learned"),
    ("learning_s2017_n28", "cost_only"),
)
PATH_SECONDS = 30.0
SOURCE_FILES = tuple(dict.fromkeys(prior.SOURCE_FILES + (
    "src/experiments/shared_budget_repair_pilot.py",
    "src/tests/test_shared_budget_repair_pilot.py",
    "src/cluster/shared_budget_repair.sbatch",
    "research-20260930/learning-campaign/PROTOCOL_SHARED_BUDGET_REPAIR.md",
    "research-20260930/learning-campaign/RESULT_MANIFEST_SHARED_INTERVAL.json",
    "research-20260930/learning-campaign/SHARED_INTERVAL_REPAIR_CELLS.csv",
)))
PROFILE = shared.PilotProfile(
    ATTEMPT, PROTOCOL, "experiments.shared_budget_repair_pilot",
    "shared-budget", SOURCE_FILES, prior.DIAGNOSIS_FILES,
    charging_caps=True, shared_charging=True,
    cells=CELLS, path_seconds=PATH_SECONDS)


def main(argv=None):
    return shared.main(argv, profile=PROFILE)


if __name__ == "__main__":
    raise SystemExit(main())
