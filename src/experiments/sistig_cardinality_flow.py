"""Prospective, separately gated exact cardinality-flow public experiment.

The public run must wait for independent code review and source publication.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

from egglab import cardinality_flow as cf
from egglab import cardinality_flow_verify as verify
from egglab import flat_energy_relaxation as er
from experiments import sistig_native_case as intake

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = "sistig-cardinality-flow-20260927-v1"
PAYLOAD = "data/public/sistig_26088190_v1/hildenbrand_native_cases.json"
REVIEW_GATE = "research-20260927/agent-notes/sistig-cardinality-flow-independent-review/REVIEW.md"
ATTEMPT = ROOT / "result/sistig_cardinality_flow/20260927-attempt1"
SOURCE_FILES = (
    "src/egglab/cardinality_flow.py", "src/egglab/cardinality_flow_verify.py",
    "src/experiments/sistig_cardinality_flow.py", "src/tests/test_cardinality_flow.py",
    "doc/SISTIG_CARDINALITY_FLOW_PROTOCOL_20260927.md",
    "src/egglab/flat_energy_relaxation.py", "src/egglab/native_recharge.py",
    "src/experiments/sistig_native_case.py", PAYLOAD,
    "doc/SISTIG_FLEET_CARDINALITY_RELAXATION_DESIGN_20260927.md",
    "doc/SISTIG_FLEET_CARDINALITY_RELAXATION_REVIEW_20260927.md",
    "doc/SISTIG_ONE_BUS_OBSTRUCTION_20260927.md",
    "research-20260927/agent-notes/sistig-one-bus-postpilot/diagnostic.py",
    "research-20260927/agent-notes/sistig-one-bus-postpilot/result.json",
    "research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md",
    "result/sistig_pricing/20260927-grb-job557543-attempt1/frozen.json",
    REVIEW_GATE,
)
PINNED = {
    PAYLOAD: verify.PAYLOAD_SHA256,
    "doc/SISTIG_ONE_BUS_OBSTRUCTION_20260927.md": "a2c4badf085d9d67c205170f8b7460e7efc1b40ac8b87aab4aa846c1815d8bdb",
    "research-20260927/agent-notes/sistig-one-bus-postpilot/diagnostic.py": "fada2a1ef1fc2b1aa0f54f8c847d0f84cfa6659f56f8638f02ed9550094d4b5f",
    "research-20260927/agent-notes/sistig-one-bus-postpilot/result.json": "cdc2603b1e53dba7fdff757e63c2f64265b0d190aef1174f4792d607ecf2b3e9",
    "research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md": "7b1d55d1d20fce676ded6aaeb6ae0965cd70fc464581290ad792f2056bce53a2",
    "result/sistig_pricing/20260927-grb-job557543-attempt1/frozen.json": "35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b",
}
COMPLETE_CAP = 120
EXTERNAL_CAP = 150
RELAXATION_CAP = 8_000_000


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def source_hashes():
    hashes = {name: sha(ROOT / name) for name in SOURCE_FILES}
    check_pins(hashes, PINNED)
    return hashes


def check_attempt(attempt):
    if attempt.resolve() != ATTEMPT.resolve():
        raise ValueError("Prospective attempt path mismatch")


def check_review_gate():
    review = (ROOT / REVIEW_GATE).read_text()
    if "**PASS**" not in review or "public-case algorithm not run" not in review:
        raise ValueError("Independent code-review gate has not passed")


def check_pins(hashes, pinned):
    if any(hashes.get(name) != expected for name, expected in pinned.items()):
        raise ValueError("Pinned input or proof hash changed")


def cases():
    variants = json.loads((ROOT / PAYLOAD).read_text())["native_cases"]
    if [v["selected_depot_id"] for v in variants] != [15, 16]:
        raise ValueError("Unexpected public case order")
    cases = [intake.native_case_from_payload(v) for v in variants]
    for case, identity in zip(cases, verify.CASE_IDENTITIES):
        er.nr.validate_case(case)
        if len(case.trips) != 37 or case.identity() != identity:
            raise ValueError("Pinned public case identity changed")
    return cases


def freeze(attempt):
    """Exclusive attempt creation, only from a published committed source tree."""
    check_attempt(attempt)
    check_review_gate()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    hashes = source_hashes()
    for name, expected in hashes.items():
        blob = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=ROOT)
        if hashlib.sha256(blob).hexdigest() != expected:
            raise ValueError(f"Uncommitted dependency: {name}")
    actual = cases()
    spec = {"protocol": PROTOCOL, "source_commit": commit, "source_hashes": hashes,
            "python": sys.version, "platform": platform.platform(),
            "price_input": .2, "price_exact": str(er.rational(.2)),
            "cases": [asdict(c) for c in actual],
            "case_identities": [c.identity() for c in actual],
            "algorithm_calls": 2, "complete_seconds_cap": COMPLETE_CAP,
            "external_process_seconds_cap": EXTERNAL_CAP,
            "relaxation_cap_per_case": RELAXATION_CAP,
            "scope": "post-pilot ideal stored-input lower bound; no native optimization"}
    attempt.mkdir(parents=True, exist_ok=False)
    write_new(attempt / "frozen.json", spec)


def _check_frozen(attempt):
    check_attempt(attempt)
    check_review_gate()
    path = attempt / "frozen.json"
    spec = json.loads(path.read_text())
    if (spec["protocol"] != PROTOCOL or spec["source_hashes"] != source_hashes()
            or spec["case_identities"] != list(verify.CASE_IDENTITIES)
            or spec["algorithm_calls"] != 2 or spec["price_input"] != .2
            or spec["price_exact"] != str(er.rational(.2))
            or spec["complete_seconds_cap"] != COMPLETE_CAP
            or spec["external_process_seconds_cap"] != EXTERNAL_CAP
            or spec["relaxation_cap_per_case"] != RELAXATION_CAP
            or spec["python"] != sys.version or spec["platform"] != platform.platform()):
        raise ValueError("Frozen execution identity or budget mismatch")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if commit != spec["source_commit"]:
        raise ValueError("Frozen source commit changed")
    actual = cases()
    if json.loads(json.dumps([asdict(c) for c in actual])) != spec["cases"]:
        raise ValueError("Frozen native input mismatch")
    return spec, actual, sha(path)


def run(attempt):
    spec, actual, frozen_hash = _check_frozen(attempt)
    start = time.monotonic()
    write_new(attempt / "STARTED.json", {"protocol": PROTOCOL, "frozen_sha256": frozen_hash,
                                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    completed = []
    for depot, case in zip((15, 16), actual):
        if time.monotonic() - start > COMPLETE_CAP:
            raise TimeoutError("Complete experiment cap reached")
        problem = er.path_cover_problem(case, .2)
        n = len(problem["trip_ids"])
        edges = {(i, j): problem["matrix"][i][j] for i, j in problem["connections"]}
        certificate = cf.solve(n, n - 2, edges, max_relaxations=RELAXATION_CAP)
        pairs = [(i, j) for i, j in sorted(edges) if certificate["flow"][f"real:{i}:{j}"]]
        incoming, outgoing = {j for _, j in pairs}, {i for i, _ in pairs}
        selected = [problem["connections"][i, j] for i, j in pairs]
        selected += [problem["pullout"][tid][1] for i, tid in enumerate(problem["trip_ids"]) if i not in incoming]
        selected += [problem["pullin"][tid][1] for i, tid in enumerate(problem["trip_ids"]) if i not in outgoing]
        result = {"protocol": PROTOCOL, "source_depot_id": depot,
                  "case_identity": case.identity(), "flat_price": str(er.rational(.2)),
                  "interpretation": "post-pilot exact ideal stored-input relaxation lower bound",
                  "lower_exact": str(problem["baseline"] + Q(certificate["network_cost"])),
                  "baseline_exact": str(problem["baseline"]),
                  "service_constant_exact": str(problem["service_constant"]),
                  "used_paths_in_relaxation": n - len(pairs),
                  "selected_movement_ids": sorted(selected), "certificate": certificate,
                  "elapsed_since_start_seconds": time.monotonic() - start}
        verify.verify_public(ROOT / PAYLOAD, result)
        write_new(attempt / f"depot_{depot}.json", result)
        completed.append(result)
        if time.monotonic() - start > COMPLETE_CAP:
            raise TimeoutError("Complete experiment cap reached")
    if source_hashes() != spec["source_hashes"] or sha(attempt / "frozen.json") != frozen_hash:
        raise ValueError("Source or frozen input changed during execution")
    write_new(attempt / "summary.json", {"protocol": PROTOCOL, "status": "completed",
              "algorithm_calls": len(completed), "elapsed_seconds": time.monotonic() - start,
              "lower_exact": [r["lower_exact"] for r in completed],
              "frozen_sha256": frozen_hash, "source_hashes_unchanged": True,
              "author_payload_verifier_passed": True,
              "native_optimizer_invoked": False,
              "physical_feasibility_or_native_matrix_optimality_claimed": False})


def supervise(attempt):
    spec, _, frozen_hash = _check_frozen(attempt)
    command = [sys.executable, "-m", "experiments.sistig_cardinality_flow",
               "run", "--attempt", str(attempt)]
    write_new(attempt / "supervisor_launch.json", {"command": command,
              "hard_cap_seconds": EXTERNAL_CAP, "frozen_sha256": frozen_hash,
              "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    start, timed_out, exit_code, error = time.monotonic(), False, None, None
    try:
        with (attempt / "stdout.txt").open("xb") as out, (attempt / "stderr.txt").open("xb") as err:
            process = subprocess.run(command, cwd=ROOT / "src", stdout=out, stderr=err,
                                     timeout=EXTERNAL_CAP, check=False)
            exit_code = process.returncode
    except subprocess.TimeoutExpired:
        timed_out, exit_code = True, 124
    except Exception as exc:
        error, exit_code = repr(exc), 1
    try:
        hashes_unchanged = source_hashes() == spec["source_hashes"]
        hash_error = None if hashes_unchanged else "Source hashes changed after child exit"
    except Exception as exc:
        hashes_unchanged, hash_error = False, repr(exc)
    child_exit_code = exit_code
    if not hashes_unchanged and exit_code == 0:
        exit_code = 1
    write_new(attempt / "supervisor_receipt.json", {"elapsed_seconds": time.monotonic() - start,
              "timed_out": timed_out, "child_exit_code": child_exit_code,
              "exit_code": exit_code, "exception": error,
              "hard_cap_seconds": EXTERNAL_CAP,
              "source_hashes_unchanged": hashes_unchanged,
              "source_hash_exception": hash_error})
    files = {str(p.relative_to(attempt)): {"bytes": p.stat().st_size, "sha256": sha(p)}
             for p in sorted(attempt.rglob("*")) if p.is_file()}
    write_new(attempt / "MANIFEST.json", {"protocol": PROTOCOL, "files": files})
    if exit_code:
        raise SystemExit(exit_code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "run", "supervise"))
    parser.add_argument("--attempt", type=Path, required=True)
    args = parser.parse_args()
    {"freeze": freeze, "run": run, "supervise": supervise}[args.mode](args.attempt.resolve())


if __name__ == "__main__":
    main()
