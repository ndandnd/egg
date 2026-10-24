"""Handwritten metadata and temporary outputs; no fixtures or numerical backend."""

from copy import deepcopy
from dataclasses import asdict, replace
import json

import pytest

from experiments import launch_prefix_initializer as prefix
from experiments import recovery_qualification as q


def metadata(tmp_path):
    return ({"policy": q.POLICY, "lock_sha256": "a" * 64, "mock": False,
             "freeze_receipt": str(tmp_path / "unread-freeze.json"),
             "freeze_receipt_sha256": "b" * 64},
            {"accounting_path": str(tmp_path / "unread-accounting.json"),
             "accounting_sha256": "c" * 64})


def accounting(total=1516.4011370494984):
    return prefix.build_launch_accounting(
        carried_charge_s=1512.6011370494984,
        receipt_charged_cpu_s=3.1857290000000003,
        receipt_cumulative_charge_s=1515.7868660494985,
        reconciled_total_s=total)


def budget_lock(record):
    return {"carried_charge_s": record.carried_charge_s,
            "freeze_charge_s": record.freeze_charge_s, "tasks": []}


@pytest.mark.parametrize("total", [1515.7868660494985, 1516.4011370494984])
def test_exact_cancellation_prefix_json_and_real_consumer(tmp_path, total):
    binding, reconciliation = metadata(tmp_path)
    record = accounting(total)
    before = deepcopy((asdict(record), binding, reconciliation))
    output = tmp_path / "new"
    receipt = prefix.initialize_new_output(
        output, accounting=record, binding=binding, reconciliation=reconciliation)
    # This is exactly the campaign dict comparison performed by q.run.
    assert q.read(output / "campaign.json") == binding
    assert set(q.read(output / "campaign.json")) == set(binding)
    events = q.ledger_events(output / "ledger.jsonl")
    assert len(events) == 2
    assert events[0]["freeze_charge_s"] == 3.1857290000000376
    assert events[0]["freeze_charge_s"] != record.receipt_charged_cpu_s
    assert events[1]["event"] == "supervisor_cpu"
    assert events[1]["reason"] == "external_freeze_reconciliation_and_closure"
    assert events[1]["charged_cpu_s"] == record.external_correction_s
    assert events[1]["accounting_path"] == reconciliation["accounting_path"]
    assert events[1]["accounting_sha256"] == reconciliation["accounting_sha256"]
    completed, resumed = q.resume_state(output, budget_lock(record), binding["lock_sha256"])
    assert completed == {}
    assert resumed == total
    restored = json.loads((output / "initialization.json").read_text())
    assert restored == receipt
    assert restored["freeze_charge_s"] == 3.1857290000000376
    assert restored["receipt_charged_cpu_s"] == 3.1857290000000003
    assert restored["resumed_total_s"] == total
    assert restored["completed_tasks"] == 0
    assert restored["informational_only"] is True
    assert restored["launch_permission"] is False and restored["timing_proof"] is False
    assert all(not isinstance(value, (dict, list)) for value in restored.values())
    assert (asdict(record), binding, reconciliation) == before
    assert not (tmp_path / "unread-freeze.json").exists()
    assert not (tmp_path / "unread-accounting.json").exists()


def test_old_raw_freeze_prefix_is_rejected_by_real_consumer(tmp_path):
    record = accounting()
    q.append_ledger(tmp_path / "ledger.jsonl", {
        "event": "carry_forward", "charged_cpu_s": record.carried_charge_s,
        "freeze_charge_s": record.receipt_charged_cpu_s})
    with pytest.raises(ValueError, match="carry-forward"):
        q.resume_state(tmp_path, budget_lock(record), "a" * 64)


def test_existing_namespace_refusal_preserves_every_byte(tmp_path):
    binding, reconciliation = metadata(tmp_path)
    output = tmp_path / "existing"
    output.mkdir()
    (output / "campaign.json").write_bytes(b"preexisting bytes\x00\xff")
    (output / "ledger.jsonl").write_bytes(b"untouched partial ledger\n")
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    with pytest.raises(FileExistsError):
        prefix.initialize_new_output(output, accounting=accounting(),
                                     binding=binding, reconciliation=reconciliation)
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before


@pytest.mark.parametrize("field,value", [
    ("freeze_charge_s", 3.1857290000000003), ("canonical_base_s", 0.),
    ("external_correction_s", 99.), ("external_correction_s", True),
    ("receipt_cumulative_charge_s", 1.), ("carried_charge_s", float("nan"))])
def test_forged_record_rejected_before_creation(tmp_path, field, value):
    binding, reconciliation = metadata(tmp_path)
    output = tmp_path / "new"
    with pytest.raises(ValueError):
        prefix.initialize_new_output(output, accounting=replace(accounting(), **{field: value}),
                                     binding=binding, reconciliation=reconciliation)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("section,field,value", [
    ("binding", "policy", "other"), ("binding", "policy", None),
    ("binding", "mock", True),
    ("binding", "mock", 0), ("binding", "lock_sha256", "A" * 64),
    ("binding", "freeze_receipt_sha256", "b" * 63),
    ("binding", "freeze_receipt", "relative.json"),
    ("binding", "freeze_receipt", ""), ("binding", "freeze_receipt", None),
    ("binding", "freeze_receipt", "/bad\0path"),
    ("reconciliation", "accounting_path", "relative.json"),
    ("reconciliation", "accounting_sha256", "g" * 64),
    ("reconciliation", "accounting_sha256", 123)])
def test_malformed_metadata_rejected_before_creation(tmp_path, section, field, value):
    binding, reconciliation = metadata(tmp_path)
    candidate = binding if section == "binding" else reconciliation
    candidate[field] = value
    before = deepcopy((binding, reconciliation))
    with pytest.raises(ValueError):
        prefix.initialize_new_output(tmp_path / "new", accounting=accounting(),
                                     binding=binding, reconciliation=reconciliation)
    assert list(tmp_path.iterdir()) == []
    assert (binding, reconciliation) == before


@pytest.mark.parametrize("section", ["binding", "reconciliation"])
@pytest.mark.parametrize("damage", ["missing", "extra", "not_dict"])
def test_metadata_requires_exact_dict_keys(tmp_path, section, damage):
    binding, reconciliation = metadata(tmp_path)
    candidate = binding if section == "binding" else reconciliation
    if damage == "missing":
        candidate.pop(next(iter(candidate)))
    elif damage == "extra":
        candidate["unexpected"] = "value"
    elif section == "binding":
        binding = []
    else:
        reconciliation = []
    with pytest.raises(ValueError):
        prefix.initialize_new_output(tmp_path / "new", accounting=accounting(),
                                     binding=binding, reconciliation=reconciliation)
    assert list(tmp_path.iterdir()) == []


def test_folded_correction_losing_one_ulp_rejected_before_creation(tmp_path):
    binding, reconciliation = metadata(tmp_path)
    target = 1. + 2. ** -52
    record = prefix.build_launch_accounting(
        carried_charge_s=0., receipt_charged_cpu_s=2. ** -53,
        receipt_cumulative_charge_s=2. ** -53, reconciled_total_s=target)
    assert record.canonical_base_s + record.external_correction_s == 1.
    assert target - (record.canonical_base_s + record.external_correction_s) == 2. ** -52
    with pytest.raises(ValueError, match="represent reconciled total exactly"):
        prefix.initialize_new_output(tmp_path / "new", accounting=record,
                                     binding=binding, reconciliation=reconciliation)
    assert list(tmp_path.iterdir()) == []


def test_non_record_rejected_before_creation(tmp_path):
    binding, reconciliation = metadata(tmp_path)
    with pytest.raises(ValueError, match="LaunchAccounting"):
        prefix.initialize_new_output(tmp_path / "new", accounting=asdict(accounting()),
                                     binding=binding, reconciliation=reconciliation)
    assert list(tmp_path.iterdir()) == []


def test_publication_failure_preserves_partial_namespace_and_blocks_retry(tmp_path, monkeypatch):
    binding, reconciliation = metadata(tmp_path)
    output = tmp_path / "partial"
    write_new = q.write_new

    def fail_receipt(path, value):
        if path.name == "initialization.json":
            raise OSError("injected publication failure")
        return write_new(path, value)

    with monkeypatch.context() as patch:
        patch.setattr(q, "write_new", fail_receipt)
        with pytest.raises(OSError, match="injected publication failure"):
            prefix.initialize_new_output(output, accounting=accounting(),
                                         binding=binding, reconciliation=reconciliation)
    assert set(path.name for path in output.iterdir()) == {"campaign.json", "ledger.jsonl"}
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    with pytest.raises(FileExistsError):
        prefix.initialize_new_output(output, accounting=accounting(),
                                     binding=binding, reconciliation=reconciliation)
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before
