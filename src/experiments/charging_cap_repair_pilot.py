"""Four-cell charging-window-cap pilot; explicit profile of the energy runner."""
from __future__ import annotations

from experiments import energy_aware_repair_pilot as shared

ROOT = shared.ROOT
ATTEMPT = ROOT / "result/learning_repair/20260930-charging-cap-attempt1"
PROTOCOL = "egg-charging-cap-route-repair-development-20260930-v1"
DIAGNOSIS_FILES = shared.DIAGNOSIS_FILES + (
    "research-20260930/learning-campaign/diagnose_charging_windows.py",
    "research-20260930/learning-campaign/CHARGING_WINDOW_DIAGNOSIS.json",
    "research-20260930/learning-campaign/CHARGING_WINDOW_DIAGNOSIS.md",
)
SOURCE_FILES = tuple(dict.fromkeys(shared.SOURCE_FILES + (
    "src/experiments/charging_cap_repair_pilot.py",
    "src/tests/test_charging_cap_repair_pilot.py",
    "src/tests/test_charging_cap_cover.py",
    "src/cluster/charging_cap_repair.sbatch",
    "research-20260930/learning-campaign/PROTOCOL_CHARGING_CAP_REPAIR.md",
) + DIAGNOSIS_FILES))
PROFILE = shared.PilotProfile(
    ATTEMPT, PROTOCOL, "experiments.charging_cap_repair_pilot", "charging-cap",
    SOURCE_FILES, DIAGNOSIS_FILES, charging_caps=True)


def main(argv=None):
    return shared.main(argv, profile=PROFILE)


if __name__ == "__main__":
    raise SystemExit(main())
