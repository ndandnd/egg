"""Prepare a new controller ledger from independently rooted postfreeze metadata.

The caller owns serialization and installs the matching adapter/q policy first.
This module installs no context and neither reserves resources nor launches work.
"""

import hashlib
import json
from pathlib import Path
import re

from egglab.launch_accounting import build_launch_accounting
from experiments import comparison_native_preflight as adapter
from experiments import recovery_qualification as q
from experiments.launch_prefix_initializer import initialize_new_output


def _digest(value):
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("Require an independently supplied SHA-256")
    return value


def _root(path, expected):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != _digest(expected):
        raise ValueError("Rooted metadata changed: " + str(path))
    value = json.loads(raw)
    if type(value) is not dict:
        raise ValueError("Rooted metadata must be an object")
    return path, value


def _installed(expected_policy):
    if (type(expected_policy) is not str or not expected_policy
            or expected_policy != adapter.POLICY or expected_policy != q.POLICY
            or q.verify_lock is not adapter.verify_lock
            or q.freeze_accounting is not adapter.freeze_accounting
            or q.OUTER_ALLOCATION != adapter.OUTER_S
            or q.SUPERVISOR_STOP_S != adapter.STOP_S):
        raise ValueError("Caller must install the matching serialized adapter policy")


def _account(account, lock, roots, expected_policy, expected_total):
    owned = account.get("owned_pgids")
    if (account.get("policy") != expected_policy
            or account.get("phase") != "metadata_freeze"
            or account.get("freeze_passed") is not True
            or account.get("metadata_freeze") is not True
            or account.get("native_dispatch") is not False
            or account.get("accounting_observations_complete") is not True
            or account.get("owned_groups_absent_and_reaped") is not True
            or type(owned) is not list or not owned
            or any(type(pgid) is not int or pgid <= 0 for pgid in owned)
            or len(set(owned)) != len(owned)
            or account.get("accounting_unresolved")
            or account.get("charge_is_lower_bound")
            or account.get("prior_charge_s") != lock["carried_charge_s"]
            or not q.finite(account.get("prior_charge_s"))
            or not q.finite(account.get("current_charge_s"))
            or account.get("charged_cpu_s") != expected_total
            or not q.finite(account.get("charged_cpu_s"))
            or account["prior_charge_s"] + account["current_charge_s"] != expected_total):
        raise ValueError("Require a completed reconciled postfreeze accounting record")
    limits = {"hard_total_ceiling_s": q.CEILING,
              "dispatch_stop_s": q.DISPATCH_STOP,
              "shutdown_reserve_s": q.SHUTDOWN_RESERVE}
    if (any(not q.finite(value) or type(account.get(key)) not in (int, float)
            or account[key] != value for key, value in limits.items())
            or q.DISPATCH_STOP + q.SHUTDOWN_RESERVE != q.CEILING
            or not q.finite(q.OUTER_ALLOCATION)
            or expected_total + q.OUTER_ALLOCATION > q.DISPATCH_STOP
            or expected_total + q.OUTER_ALLOCATION + q.SHUTDOWN_RESERVE > q.CEILING
            or not all(q.finite(value) for value in (
                adapter.OUTER_S, adapter.SUPERVISION_RESERVE_S,
                adapter.ANALYSIS_FINAL_RESERVE_S, adapter.PACKAGE_CAP))
            or expected_total + adapter.OUTER_S + adapter.SUPERVISION_RESERVE_S
               + adapter.ANALYSIS_FINAL_RESERVE_S > adapter.PACKAGE_CAP):
        raise ValueError("Accounting limits or next-worker funding differ from installed policy")
    evidence = account.get("evidence_hashes")
    if type(evidence) is not dict or not evidence:
        raise ValueError("Missing rooted accounting evidence closure")
    for name, digest in evidence.items():
        if (type(name) is not str or not Path(name).is_absolute()
                or str(Path(name).resolve(strict=True)) != name):
            raise ValueError("Accounting evidence paths must be canonical absolute paths")
        _digest(digest)
    if any(evidence.get(str(path)) != digest for path, digest in roots):
        raise ValueError("Accounting must bind the checked lock and freeze receipt")
    q.verify_hashes(evidence)


def prepare_new_output(output, *, lock_path, freeze_receipt_path, accounting_path,
                       expected_lock_sha256, expected_freeze_receipt_sha256,
                       expected_accounting_sha256, expected_cumulative_charge_s,
                       expected_policy):
    """Verify postfreeze bytes and publish one new prefix, without calling q.run.

    Expected hashes/total/policy must come independently from the caller, never
    from self-described receipt hashes. Input paths are resolved as q.run does.
    The checks are snapshots, not an atomic filesystem or resource reservation.
    Once publication starts any partial namespace remains and blocks reuse.
    """
    _installed(expected_policy)
    if not q.finite(expected_cumulative_charge_s):
        raise ValueError("Require a finite independently reconciled cumulative total")
    lock_path, lock = _root(lock_path, expected_lock_sha256)
    receipt_path, receipt = _root(freeze_receipt_path, expected_freeze_receipt_sha256)
    account_path, account = _root(accounting_path, expected_accounting_sha256)
    roots = ((lock_path, expected_lock_sha256),
             (receipt_path, expected_freeze_receipt_sha256))
    _account(account, lock, roots, expected_policy, expected_cumulative_charge_s)
    adapter.verify_lock(lock)
    budget_lock = adapter.freeze_accounting(lock, lock_path, receipt_path)
    canonical = build_launch_accounting(
        carried_charge_s=lock["carried_charge_s"],
        receipt_charged_cpu_s=receipt["charged_cpu_s"],
        receipt_cumulative_charge_s=receipt["cumulative_qualification_charge_s"],
        reconciled_total_s=expected_cumulative_charge_s)
    if budget_lock != {**lock, "freeze_charge_s": canonical.freeze_charge_s}:
        raise ValueError("Real freeze consumer differs from canonical accounting")
    # Recheck rooted metadata and closure after consumer reads, before mkdir.
    _installed(expected_policy)
    for path, digest in (*roots, (account_path, expected_accounting_sha256)):
        _root(path, digest)
    _account(account, lock, roots, expected_policy, expected_cumulative_charge_s)
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError("Existing or partial output namespace: " + str(output))
    return initialize_new_output(
        output.resolve(), accounting=canonical,
        binding={"policy": expected_policy, "lock_sha256": expected_lock_sha256,
                 "mock": False, "freeze_receipt": str(receipt_path),
                 "freeze_receipt_sha256": expected_freeze_receipt_sha256},
        reconciliation={"accounting_path": str(account_path),
                        "accounting_sha256": expected_accounting_sha256})
