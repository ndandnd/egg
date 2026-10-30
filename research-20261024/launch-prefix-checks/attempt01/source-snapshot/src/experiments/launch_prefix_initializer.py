"""Publish a new recovery ledger prefix from supplied accounting metadata only.

No provenance checks, fixture/model reads, launch permission, or CLI live here.
Publication failures deliberately leave a partial namespace that blocks retry.
"""

from dataclasses import asdict
from pathlib import Path
import re

from egglab.launch_accounting import LaunchAccounting, build_launch_accounting
from experiments import recovery_qualification as q


def _metadata(value, keys, hashes, paths):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError("Malformed metadata keys")
    result = value.copy()
    for key in hashes:
        if (type(result[key]) is not str
                or re.fullmatch(r"[0-9a-f]{64}", result[key]) is None):
            raise ValueError("Malformed SHA-256 metadata: " + key)
    for key in paths:
        path = result[key]
        if (type(path) is not str or not path or "\0" in path
                or not Path(path).is_absolute()):
            raise ValueError("Reference must be a nonempty absolute path: " + key)
    return result


def initialize_new_output(output, *, accounting: LaunchAccounting,
                          binding: dict, reconciliation: dict):
    """Create once, then verify the exact prefix with the real resume consumer.

    References/hashes are supplied metadata, not verified receipt provenance.
    All metadata and exact accounting checks precede filesystem operations.
    An existing or partially published output must never be reused here.
    """
    binding = _metadata(
        binding, ("policy", "lock_sha256", "mock", "freeze_receipt",
                  "freeze_receipt_sha256"),
        ("lock_sha256", "freeze_receipt_sha256"), ("freeze_receipt",))
    if (type(binding["policy"]) is not str or binding["policy"] != q.POLICY
            or binding["mock"] is not False):
        raise ValueError("Require the real recovery campaign binding")
    reconciliation = _metadata(
        reconciliation, ("accounting_path", "accounting_sha256"),
        ("accounting_sha256",), ("accounting_path",))
    if type(accounting) is not LaunchAccounting:
        raise ValueError("Require a canonical LaunchAccounting record")
    supplied = asdict(accounting)
    if any(type(value) not in (int, float) for value in supplied.values()):
        raise ValueError("Malformed accounting scalar")
    canonical = build_launch_accounting(**{
        name: supplied[name] for name in (
            "carried_charge_s", "receipt_charged_cpu_s",
            "receipt_cumulative_charge_s", "reconciled_total_s")})
    if supplied != asdict(canonical):
        raise ValueError("Accounting record differs from canonical rebuild")
    if (canonical.canonical_base_s + canonical.external_correction_s
            != canonical.reconciled_total_s):
        raise ValueError("Canonical prefix cannot represent reconciled total exactly")

    output = Path(output)
    output.mkdir()  # Exclusive: no parent creation, cleanup, rewriting, or retry.
    q.write_new(output / "campaign.json", binding)
    q.append_ledger(output / "ledger.jsonl", {
        "event": "carry_forward", "charged_cpu_s": canonical.carried_charge_s,
        "freeze_charge_s": canonical.freeze_charge_s})
    q.append_ledger(output / "ledger.jsonl", {
        "event": "supervisor_cpu",
        "reason": "external_freeze_reconciliation_and_closure",
        "charged_cpu_s": canonical.external_correction_s, **reconciliation})
    budget_lock = {"carried_charge_s": canonical.carried_charge_s,
                   "freeze_charge_s": canonical.freeze_charge_s, "tasks": []}
    completed, total = q.resume_state(output, budget_lock, binding["lock_sha256"])
    if completed or total != canonical.reconciled_total_s:
        raise ValueError("Published prefix failed exact recovery consumer readback")
    receipt = {
        "initializer_policy": "launch-prefix-initializer-v1",
        "informational_only": True, "launch_permission": False,
        "timing_proof": False, "completed_tasks": 0, "resumed_total_s": total,
        **binding, **reconciliation, **asdict(canonical)}
    q.write_new(output / "initialization.json", receipt)
    return receipt
