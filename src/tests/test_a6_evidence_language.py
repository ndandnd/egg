"""Task-3/Task-D evidence-language battery: the three historical evidence
limitations must be preserved, verbatim-consistent, in the EMITTED
analysis SUMMARY.md and MANIFEST.json, the EMITTED package bundle
metadata, and the runbook — verified by running the miniature analyzer
and package pipelines, not by inspecting source strings.  The incidents
ledger must retain EI-017..EI-023 with index/body status agreement."""
import json
import os
import re
import sys
from pathlib import Path

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(TESTS_DIR))
sys.path.insert(0, TESTS_DIR)

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


def test_emitted_analysis_summary_and_manifest_carry_limitations(tmp_path):
    """Run the miniature analyzer pipeline end to end and inspect the
    PUBLISHED SUMMARY.md and MANIFEST.json."""
    import test_a6_holdout_analysis as TA

    root = tmp_path / "a6_holdout_mini"
    root.mkdir()
    preflight_path = root / "PREFLIGHT.json"
    preflight_path.write_text("{}\n")
    preflight = {
        "path": str(preflight_path.resolve()),
        "sha256": TA.sha256_file(str(preflight_path)),
        "schema": "test-preflight", "code_commit": TA.RUN_COMMIT,
        "physical_instances": 2, "market_instances": 2, "method_cells": 4,
        "selection": TA.selection_block(),
    }
    TA._write_launch_records(root, preflight)
    cells = [(m, *i) for m in TA.METHODS for i in TA.MINI_INSTANCES]
    for index, (method, seed, n, b) in enumerate(cells):
        TA._write_cell(root, method, seed, n, b, index, preflight, calls=2)

    out = tmp_path / "published"
    TA._mini_analyze(str(root), preflight, out)
    target = out / "TESTSTAMP"

    manifest = json.loads((target / "MANIFEST.json").read_text())
    emitted = manifest["scientific_validation"]["evidence_limitations"]
    assert emitted == list(EVIDENCE_LIMITATIONS)

    summary = (target / "SUMMARY.md").read_text()
    for limitation in EVIDENCE_LIMITATIONS:
        assert limitation in summary, limitation


def test_emitted_package_bundle_metadata_carries_limitations(tmp_path):
    """Run the miniature package pipeline end to end and inspect the
    PUBLISHED BUNDLE_MANIFEST.json."""
    import test_a6_holdout_package as TP

    root = TP._source_root(tmp_path)
    bundle = TP._package(root, tmp_path / "packages")["bundle_dir"]
    manifest = json.loads(
        (Path(bundle) / "BUNDLE_MANIFEST.json").read_text())
    emitted = manifest["scientific_validation"]["evidence_limitations"]
    assert emitted == list(EVIDENCE_LIMITATIONS)


def test_runbook_preserves_all_three_limitations():
    runbook = (DOC / "UNICORN_RUNBOOK.md").read_text()
    # the runbook states the same three limitations narratively
    assert "lambdas" in runbook and "link-dual" in runbook
    assert "out-dual" in runbook
    assert "conditional on the serialized candidate price" in runbook
    assert "SLURM_ARRAY_JOB_ID" in runbook
    assert "cannot claim that record bytes exactly join to the parent array" \
        in runbook


def _index_statuses(ledger: str) -> dict:
    statuses = {}
    for match in re.finditer(
            r"^\| (EI-\d{3}) \| [0-9-]+ \| \*\*([^|]+?)\*\* \|",
            ledger, re.MULTILINE):
        statuses[match.group(1)] = match.group(2).strip()
    return statuses


def _body_statuses(ledger: str) -> dict:
    statuses = {}
    for match in re.finditer(
            r"^## (EI-\d{3}) — .*?\*\*(?:Status: )?([A-Z][^.*]*?)[.*]",
            ledger, re.MULTILINE | re.DOTALL):
        statuses[match.group(1)] = match.group(2).strip()
    return statuses


def test_incident_index_retains_and_matches_bodies():
    ledger = (DOC / "ENGINEERING_INCIDENTS.md").read_text()
    index = _index_statuses(ledger)
    for number in range(17, 24):
        key = f"EI-0{number}"
        assert key in index, f"{key} missing from the incident index"
        assert f"## {key}" in ledger, f"{key} body missing"
    assert "## Regression-coverage map: EI-017 through EI-023" in ledger
    for number in range(17, 24):
        assert f"EI-0{number} (" in ledger, (
            f"EI-0{number} missing from the coverage map")
    # index/body status agreement for the closeout incidents
    for key in ("EI-021", "EI-022", "EI-023"):
        body = re.search(
            rf"^## {key} — .*?\*\*Status: ([A-Za-z— -]+?)[.,*]",
            ledger, re.MULTILINE | re.DOTALL)
        assert body is not None, f"{key} body has no status line"
        body_status = body.group(1).strip()
        assert index[key].split(" ")[0] == body_status.split(" ")[0], (
            key, index[key], body_status)
    # the completed recovery replay is no longer an open incident
    assert "Complete recovery-state replay is required" not in ledger
    # the absolute "no fallible step follows" claim was corrected
    assert "no fallible step follows it" not in ledger
