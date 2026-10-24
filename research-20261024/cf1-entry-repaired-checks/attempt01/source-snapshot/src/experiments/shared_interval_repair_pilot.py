"""Shared-interval cover pilot using the frozen repair profile runner."""
from __future__ import annotations

from experiments import charging_cap_repair_pilot as prior
from experiments import energy_aware_repair_pilot as shared

ROOT = shared.ROOT
ATTEMPT = ROOT / "result/learning_repair/20260930-shared-interval-attempt1"
PROTOCOL = "egg-shared-interval-route-repair-development-20260930-v1"
DIAGNOSIS_FILES = prior.DIAGNOSIS_FILES + (
    "research-20260930/learning-campaign/INDEPENDENT_REPLAY_CHARGING_CAP.json",
    "research-20260930/learning-campaign/CHARGING_CAP_FAILURE_DIAGNOSIS.json",
    "research-20260930/learning-campaign/CHARGING_CAP_FAILURE_DIAGNOSIS.md",
    "research-20260930/learning-campaign/diagnose_charging_cap_failures.py",
)
SOURCE_FILES = tuple(dict.fromkeys(prior.SOURCE_FILES + (
    "src/experiments/shared_interval_repair_pilot.py",
    "src/tests/test_shared_interval_repair_pilot.py",
    "src/tests/test_shared_charging_cover.py",
    "src/cluster/shared_interval_repair.sbatch",
    "research-20260930/learning-campaign/PROTOCOL_SHARED_INTERVAL_REPAIR.md",
) + DIAGNOSIS_FILES))
PROFILE = shared.PilotProfile(
    ATTEMPT, PROTOCOL, "experiments.shared_interval_repair_pilot",
    "shared-interval", SOURCE_FILES, DIAGNOSIS_FILES,
    charging_caps=True, shared_charging=True)


def main(argv=None):
    return shared.main(argv, profile=PROFILE)


if __name__ == "__main__":
    raise SystemExit(main())
