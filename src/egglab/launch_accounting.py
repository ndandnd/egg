"""Pure accounting values for a separately authorized future launch ledger.

This module neither reads receipts nor grants permission to launch work.
"""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class LaunchAccounting:
    carried_charge_s: float
    receipt_charged_cpu_s: float
    receipt_cumulative_charge_s: float
    freeze_charge_s: float
    canonical_base_s: float
    reconciled_total_s: float
    external_correction_s: float


def build_launch_accounting(
    *,
    carried_charge_s: float,
    receipt_charged_cpu_s: float,
    receipt_cumulative_charge_s: float,
    reconciled_total_s: float,
) -> LaunchAccounting:
    """Match comparison_native_preflight.freeze_accounting's exact component.

    All inputs must be finite, nonnegative Python int/float scalars. The caller
    supplies an independently reconciled total; this function creates no budget.
    The generic recovery freezer's separate maximum-with-lock-floor policy is
    outside this helper's contract.
    """
    values = {
        "carried_charge_s": carried_charge_s,
        "receipt_charged_cpu_s": receipt_charged_cpu_s,
        "receipt_cumulative_charge_s": receipt_cumulative_charge_s,
        "reconciled_total_s": reconciled_total_s,
    }
    for name, value in values.items():
        try:
            valid = type(value) in (int, float) and isfinite(value) and value >= 0
        except OverflowError:
            valid = False
        if not valid:
            raise ValueError(f"{name} must be a finite nonnegative numeric scalar")
    if receipt_cumulative_charge_s != carried_charge_s + receipt_charged_cpu_s:
        raise ValueError("Receipt cumulative charge must equal carried plus raw charge")

    freeze_charge_s = receipt_cumulative_charge_s - carried_charge_s
    canonical_base_s = carried_charge_s + freeze_charge_s
    if (reconciled_total_s < canonical_base_s
            or reconciled_total_s < receipt_cumulative_charge_s):
        raise ValueError("Reconciled total must cover canonical base and receipt cumulative")
    external_correction_s = reconciled_total_s - canonical_base_s
    return LaunchAccounting(
        carried_charge_s=carried_charge_s,
        receipt_charged_cpu_s=receipt_charged_cpu_s,
        receipt_cumulative_charge_s=receipt_cumulative_charge_s,
        freeze_charge_s=freeze_charge_s,
        canonical_base_s=canonical_base_s,
        reconciled_total_s=reconciled_total_s,
        external_correction_s=external_correction_s,
    )
