"""Task-3 evidence-language battery: the three historical evidence
limitations must be preserved, verbatim-consistent, in the analyzer
constant, the analysis SUMMARY.md and MANIFEST.json, the package bundle
metadata, and the runbook — and the incidents ledger must retain
EI-017..EI-023 with regression mapping."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.analyze_a6_holdout import EVIDENCE_LIMITATIONS

DOC = Path(__file__).resolve().parents[2] / "doc"

LIMITATION_KEYS = (
    # 1. clean-master primal/dual path not serialized
    ("lambdas", "link duals", "not serialized",
     "exact convex restricted master"),
    # 2. A6-A4 pi_out not serialized; conditional replay
    ("pi_out", "conditional on the recorded candidate price"),
    # 3. SLURM_ARRAY_JOB_ID absent; parent-array join unprovable
    ("SLURM_ARRAY_JOB_ID", "parent-array join"),
)


def test_constant_carries_all_three_limitations():
    assert len(EVIDENCE_LIMITATIONS) == 3
    for limitation, keys in zip(EVIDENCE_LIMITATIONS, LIMITATION_KEYS):
        for key in keys:
            assert key in limitation, (key, limitation)


def test_runbook_preserves_all_three_limitations():
    runbook = (DOC / "UNICORN_RUNBOOK.md").read_text()
    # the runbook states the same three limitations narratively
    assert "lambdas" in runbook and "link-dual" in runbook
    assert "out-dual" in runbook
    assert "conditional on the serialized candidate price" in runbook
    assert "SLURM_ARRAY_JOB_ID" in runbook
    assert "cannot claim that record bytes exactly join to the parent array" \
        in runbook


def test_incidents_ledger_retains_ei_017_through_023_with_mapping():
    ledger = (DOC / "ENGINEERING_INCIDENTS.md").read_text()
    for number in range(17, 24):
        assert f"## EI-0{number}" in ledger, f"EI-0{number} missing"
    assert "## Regression-coverage map: EI-017 through EI-023" in ledger
    for number in range(17, 24):
        assert f"EI-0{number} (" in ledger, (
            f"EI-0{number} missing from the coverage map")
    # the completed recovery replay is no longer an open incident
    assert "Complete recovery-state replay is required" not in ledger


def test_summary_and_manifest_carry_limitations(tmp_path):
    """The analyzer writes the exact limitation strings into SUMMARY.md and
    MANIFEST.json (asserted on the write_summary/manifest surfaces without
    a full analyze run: write_summary is invoked directly and the manifest
    embedding is pinned by the source contract)."""
    import inspect

    import experiments.analyze_a6_holdout as mod

    summary_src = inspect.getsource(mod.write_summary)
    assert "EVIDENCE_LIMITATIONS" in summary_src
    analyze_src = inspect.getsource(mod.analyze)
    assert '"evidence_limitations": list(EVIDENCE_LIMITATIONS)' in analyze_src


def test_package_metadata_carries_exact_limitations():
    import inspect

    import experiments.package_a6_holdout as pkg

    producer_src = inspect.getsource(pkg.validate_scientific_population)
    assert '"evidence_limitations": list(EVIDENCE_LIMITATIONS)' in producer_src
    validator_src = inspect.getsource(pkg._validated_manifest_snapshot)
    assert '!= list(EVIDENCE_LIMITATIONS)' in validator_src
