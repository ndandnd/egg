#!/usr/bin/env python3
"""Copy-only integrity controls for the exact pinned public subset."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import uuid

import audit_nonlinear_v2 as audit


REPO = Path(__file__).resolve().parents[3]
PUBLIC = REPO / audit.PUBLIC_ATTEMPT_REL
RAW = REPO / audit.ATTEMPT_REL
RAW_MANIFEST_SHA = "68032692ea5c5b349115bd6bd64740f0bd799fac9a8a4dcdf09462a844901cf9"


def rejected(call):
    try:
        call()
    except (AssertionError, KeyError, TypeError, ValueError, OSError):
        return True
    return False


def main():
    with tempfile.TemporaryDirectory(prefix="v2-public-copy-", dir=audit.HERE) as tmp:
        copied = Path(tmp) / "attempt2-publication"
        copied.mkdir()
        public = json.loads((PUBLIC / "PUBLIC_MANIFEST.json").read_text())
        raw_manifest = json.loads((RAW / "MANIFEST.json").read_text())
        omitted = set(public["omitted_files"])
        assert omitted == {"hull/stdout.txt", "own_price/stdout.txt", "planner/stdout.txt"}
        for rel in public["unchanged_published_files"]:
            source = RAW / rel
            target = copied / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        shutil.copy2(RAW / "MANIFEST.json", copied / "MANIFEST.json")
        shutil.copy2(RAW / "slurm_wrapper_receipt.json", copied / "slurm_wrapper_receipt.json")
        shutil.copy2(PUBLIC / "PUBLIC_MANIFEST.json", copied / "PUBLIC_MANIFEST.json")
        shutil.copy2(PUBLIC / "README.md", copied / "README.md")
        manifest, retained_bytes = audit.verify_manifest(
            copied, RAW_MANIFEST_SHA, public_copy=True)
        assert len(manifest["files"]) == 31
        assert omitted.isdisjoint(
            str(p.relative_to(copied)) for p in copied.rglob("*") if p.is_file())
        expected_retained = sum(r["bytes"] for k, r in manifest["files"].items()
                                if k not in omitted)
        assert retained_bytes == expected_retained
        # Default mode remains strict and refuses a public subset.
        assert rejected(lambda: audit.verify_manifest(
            copied, RAW_MANIFEST_SHA, public_copy=False))
        out = audit.HERE / (".audit-report-public-test-" + uuid.uuid4().hex + ".json")
        try:
            status = audit.main([
                "--repository", str(REPO), "--attempt", str(copied),
                "--manifest-sha256", RAW_MANIFEST_SHA, "--public-copy", "--out", str(out)])
            assert status == 0
            report = json.loads(out.read_text())
        finally:
            if out.exists():
                out.unlink()
        assert report["public_copy_mode"] is True
        assert report["numerical_evidence_audit_status"] == "PASS"
        assert report["protocol_compliance_status"] == "FAIL"
        assert report["overall_status"] == "NO OVERALL PASS"
        # The exact public mode must still reject a missing scientific record.
        (copied / "planner/input.json").unlink()
        assert rejected(lambda: audit.verify_manifest(
            copied, RAW_MANIFEST_SHA, public_copy=True))
    print(json.dumps({"status": "PASS", "raw_manifest_sha256": RAW_MANIFEST_SHA,
                      "public_manifest_sha256": audit.PUBLIC_MANIFEST_SHA256,
                      "retained_scientific_files": 28,
                      "omitted_files": 3,
                      "full_mode_remains_strict": True,
                      "public_mode_full_science_audit": True,
                      "missing_science_file_rejected": True}, sort_keys=True))


if __name__ == "__main__":
    main()
