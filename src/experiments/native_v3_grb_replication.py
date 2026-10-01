"""GRB-only outer supervisor for the frozen V3 physical and hull controls.

Preparation code. Importing this module never calls an optimizer. The two
stages are deliberately separate jobs, with an independently reviewed physical
admission required before the hull stage can start.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time

from experiments import native_pathflow_qualification as physical
from experiments import native_pathflow_hull_qualification as hull

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = "native-v3-grb-replication-20260927-v1"
PATHS = {
    "physical": ROOT / "result/native_pathflow_grb/20260927-attempt1",
    "hull": ROOT / "result/native_pathflow_hull_grb/20260927-attempt1",
}
CAPS = {"physical": 1320, "hull": 720}
ADMISSION = ROOT / "doc/NATIVE_V3_GRB_PHYSICAL_ADMISSION_20260927.json"
AUDIT = ROOT / "doc/NATIVE_V3_GRB_PHYSICAL_RESULT_AUDIT_20260927.md"
ADDENDUM = "doc/NATIVE_V3_GRB_REPLICATION_PROTOCOL_20260927.md"
COMMON_SOURCES = (
    "src/experiments/native_v3_grb_replication.py",
    "src/tests/test_native_v3_grb_replication.py",
    "doc/NATIVE_V3_GRB_REPLICATION_IMPLEMENTATION_REVIEW_20260927.md",
    "src/cluster/native_v3_grb_physical.sbatch",
    "src/cluster/native_v3_grb_hull.sbatch",
    "src/cluster/unicorn_env.sh",
    ADDENDUM,
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, data):
    with Path(path).open("x", encoding="utf-8") as out:
        json.dump(data, out, indent=2, sort_keys=True, allow_nan=False)
        out.write("\n")
        out.flush()
        os.fsync(out.fileno())


def source_names(stage):
    if stage not in PATHS:
        raise ValueError("Unknown GRB replication stage")
    sources = physical.SOURCES if stage == "physical" else hull.SOURCES
    extra = ("doc/NATIVE_V3_GRB_PHYSICAL_ADMISSION_20260927.json",
             "doc/NATIVE_V3_GRB_PHYSICAL_RESULT_AUDIT_20260927.md") if stage == "hull" else ()
    return tuple(dict.fromkeys(sources + COMMON_SOURCES + extra))


def source_hashes(stage):
    return {name: sha(ROOT / name) for name in source_names(stage)}


def check_path(stage, output):
    expected = PATHS[stage].resolve()
    if Path(output).resolve() != expected:
        raise ValueError(f"{stage} GRB requires exclusive {expected}")
    if expected.exists() or Path(str(expected) + ".launch").exists():
        raise FileExistsError("GRB attempt or launch sentinel already exists")
    return expected


def check_published(hashes, commit):
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if commit != actual or len(commit) != 40:
        raise ValueError("Full published source commit mismatch")
    for name, expected in hashes.items():
        blob = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=ROOT)
        if hashlib.sha256(blob).hexdigest() != expected:
            raise ValueError(f"Unpublished GRB source: {name}")


def check_physical_admission(hashes):
    """Require an independent post-run physical audit before hull starts."""
    if not ADMISSION.is_file():
        raise ValueError("Physical GRB result audit/admission is absent")
    admission = json.loads(ADMISSION.read_text())
    attempt = PATHS["physical"]
    if (admission.get("status") != "PASS" or admission.get("backend") != "GRB"
            or admission.get("attempt") != str(attempt.relative_to(ROOT))):
        raise ValueError("Physical GRB admission identity is invalid")
    pins = admission.get("pins")
    if not isinstance(pins, dict) or set(pins) != {"frozen", "summary", "receipt", "manifest", "audit"}:
        raise ValueError("Physical GRB admission pins are incomplete")
    evidence = {}
    expected_files = {"frozen": "frozen.json", "summary": "summary.json",
                      "receipt": "grb_wrapper_receipt.json", "manifest": "MANIFEST.json"}
    for key, pin in pins.items():
        if not isinstance(pin, dict) or set(pin) != {"path", "sha256"}:
            raise ValueError("Malformed physical GRB evidence pin")
        rel = Path(pin["path"])
        if (rel.is_absolute() or ".." in rel.parts or not rel.parts
                or (key != "audit" and rel != attempt.relative_to(ROOT) / expected_files[key])
                or (key == "audit" and rel != AUDIT.relative_to(ROOT))):
            raise ValueError("Physical GRB evidence pin escapes its stage")
        path = ROOT / rel
        if not path.is_file() or sha(path) != pin["sha256"]:
            raise ValueError("Physical GRB evidence pin changed")
        evidence[key] = path.read_text() if key == "audit" else json.loads(path.read_text())
    if "**PASS**" not in evidence["audit"]:
        raise ValueError("Independent physical GRB audit has not passed")
    frozen, summary, receipt, manifest = (evidence[x] for x in ("frozen", "summary", "receipt", "manifest"))
    if (frozen.get("protocol") != physical.PROTOCOL or frozen.get("budget", {}).get("backend") != "GRB"
            or frozen.get("formulation") != physical.pf.FORMULATION
            or frozen.get("extraction_policy") != physical.pf.EXTRACTION_POLICY
            or not isinstance(frozen.get("controls"), list) or len(frozen["controls"]) != 20
            or summary.get("protocol") != physical.PROTOCOL or not isinstance(summary.get("cells"), list)
            or len(summary["cells"]) != 20 or summary.get("all_pass") is not True
            or summary.get("source_hashes_unchanged") is not True
            or any(row.get("pass") is not True for row in summary["cells"])
            or receipt.get("returncode") != 0 or receipt.get("source_hashes_unchanged") is not True
            or manifest.get("protocol") != PROTOCOL):
        raise ValueError("Physical GRB qualification is incomplete")
    actual_files = {str(path.relative_to(attempt)) for path in attempt.rglob("*") if path.is_file()}
    if actual_files != set(manifest.get("files", {})) | {"MANIFEST.json"}:
        raise ValueError("Physical GRB manifest file set changed")
    for name, data in manifest["files"].items():
        path = attempt / name
        if data != {"sha256": sha(path), "bytes": path.stat().st_size}:
            raise ValueError("Physical GRB manifest content changed")
    sentinel = Path(str(attempt) + ".launch")
    completion = json.loads((sentinel / "completion.json").read_text())
    if (completion.get("receipt_sha256") != sha(attempt / "grb_wrapper_receipt.json")
            or completion.get("manifest_sha256") != sha(attempt / "MANIFEST.json")):
        raise ValueError("Physical GRB launch sentinel differs from sealed evidence")
    for name in ("src/egglab/native_recharge.py", "src/egglab/native_pathflow.py"):
        if frozen["source_hashes"].get(name) != hashes.get(name):
            raise ValueError(f"Physical GRB source differs before hull: {name}")
    return admission


def seal_manifest(attempt):
    files = {str(path.relative_to(attempt)): {"sha256": sha(path), "bytes": path.stat().st_size}
             for path in sorted(attempt.rglob("*")) if path.is_file() and path.name != "MANIFEST.json"}
    write_new(attempt / "MANIFEST.json", {"protocol": PROTOCOL, "files": files})


def stage_evidence(stage, attempt, hashes, commit):
    """Check child completion without replacing the later independent audit."""
    frozen = json.loads((attempt / "frozen.json").read_text())
    summary = json.loads((attempt / "summary.json").read_text())
    runner = physical if stage == "physical" else hull
    count = 20 if stage == "physical" else 8
    if (frozen.get("protocol") != runner.PROTOCOL or frozen.get("freeze_label") != commit
            or frozen.get("budget", {}).get("backend") != "GRB"
            or not isinstance(frozen.get("controls"), list) or len(frozen["controls"]) != count
            or summary.get("protocol") != runner.PROTOCOL
            or not isinstance(summary.get("cells"), list) or len(summary["cells"]) != count
            or summary.get("all_pass") is not True
            or summary.get("source_hashes_unchanged") is not True
            or any(row.get("pass") is not True for row in summary["cells"])):
        raise ValueError("Incomplete GRB child qualification evidence")
    for name in runner.SOURCES:
        if frozen.get("source_hashes", {}).get(name) != hashes.get(name):
            raise ValueError("Child GRB source freeze differs from wrapper")
    if stage == "physical" and (frozen.get("formulation") != physical.pf.FORMULATION
                                or frozen.get("extraction_policy") != physical.pf.EXTRACTION_POLICY):
        raise ValueError("Physical GRB formulation/extraction identity changed")
    if stage == "hull":
        supervisor = json.loads((attempt / "supervisor_receipt.json").read_text())
        if (frozen.get("pricing_oracle") != hull.compact.ORACLE_ID
                or frozen.get("extraction_policy") != hull.compact.EXTRACTION_POLICY
                or supervisor.get("protocol") != hull.PROTOCOL
                or supervisor.get("returncode") != 0
                or supervisor.get("outer_timeout") is not False):
            raise ValueError("Hull GRB oracle/extraction/supervisor identity changed")


def run(stage, output, commit):
    attempt = check_path(stage, output)
    hashes = source_hashes(stage)
    check_published(hashes, commit)
    admission = check_physical_admission(hashes) if stage == "hull" else None
    sentinel = Path(str(attempt) + ".launch")
    sentinel.mkdir(parents=True, exist_ok=False)
    cmd = [sys.executable, "-m", "experiments.native_pathflow_qualification"
           if stage == "physical" else "experiments.native_pathflow_hull_qualification",
           "--output", str(attempt), "--freeze-label", commit, "--backend", "GRB"]
    launch = {"protocol": PROTOCOL, "stage": stage, "command": cmd, "backend": "GRB",
              "source_commit": commit, "source_hashes": hashes, "outer_cap_seconds": CAPS[stage],
              "physical_admission_sha256": sha(ADMISSION) if admission else None,
              "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    write_new(sentinel / "launch.json", launch)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    started, timed_out, child_rc, launch_error = time.monotonic(), False, None, None
    with (sentinel / "stdout.txt").open("xb") as out, (sentinel / "stderr.txt").open("xb") as err:
        try:
            process = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=out, stderr=err,
                                       start_new_session=True)
            try:
                child_rc = process.wait(timeout=CAPS[stage])
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    child_rc = process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child_rc = None
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                if child_rc is None:
                    child_rc = process.wait()
        except Exception as exc:
            launch_error = repr(exc)
    attempt.mkdir(parents=True, exist_ok=True)
    write_new(attempt / "grb_wrapper_launch.json", launch)
    for stream in ("stdout", "stderr"):
        with (sentinel / f"{stream}.txt").open("rb") as source, (
                attempt / f"grb_wrapper_{stream}.txt").open("xb") as target:
            shutil.copyfileobj(source, target)
    source_error = None
    try:
        unchanged = source_hashes(stage) == hashes
    except Exception as exc:
        unchanged, source_error = False, repr(exc)
    evidence_error = None
    if child_rc == 0 and not timed_out:
        try:
            stage_evidence(stage, attempt, hashes, commit)
        except Exception as exc:
            evidence_error = repr(exc)
    rc = 124 if timed_out else child_rc if type(child_rc) is int else 1
    if rc == 0 and (not unchanged or evidence_error):
        rc = 1
    receipt = {"protocol": PROTOCOL, "stage": stage, "child_returncode": child_rc,
               "returncode": rc, "outer_timeout": timed_out, "launch_error": launch_error,
               "elapsed_seconds": time.monotonic() - started,
               "source_hashes_unchanged": unchanged, "source_check_error": source_error,
               "stage_evidence_error": evidence_error,
               "launch_sentinel": str(sentinel.relative_to(ROOT))}
    write_new(attempt / "grb_wrapper_receipt.json", receipt)
    seal_manifest(attempt)
    write_new(sentinel / "completion.json", {"attempt": str(attempt.relative_to(ROOT)),
              "receipt_sha256": sha(attempt / "grb_wrapper_receipt.json"),
              "manifest_sha256": sha(attempt / "MANIFEST.json")})
    return rc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=tuple(PATHS))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze-label", required=True)
    args = parser.parse_args(argv)
    return run(args.stage, args.output, args.freeze_label)


if __name__ == "__main__":
    raise SystemExit(main())
