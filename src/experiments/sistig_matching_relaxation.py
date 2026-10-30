"""Prospectively frozen exact flat-price relaxation for both public cases."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

from egglab import flat_energy_relaxation as er
from experiments import sistig_native_case as intake

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = "sistig-matching-relaxation-20260927-v1"
PAYLOAD = "data/public/sistig_26088190_v1/hildenbrand_native_cases.json"
PAYLOAD_SHA256 = "af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6"
SOURCES = ("src/egglab/flat_energy_relaxation.py", "src/egglab/native_recharge.py",
           "src/experiments/sistig_native_case.py", "src/experiments/sistig_matching_relaxation.py",
           "src/tests/test_flat_energy_relaxation.py", "doc/SISTIG_MATCHING_PROTOCOL_20260927.md",
           "doc/SISTIG_ENERGY_RELAXATION_DESIGN_REVIEW_20260927.md",
           "doc/SISTIG_MATCHING_NUMERICAL_SCOPE_REVIEW_20260927.md", PAYLOAD)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def source_hashes():
    return {name: sha(ROOT / name) for name in SOURCES}


def cases():
    if sha(ROOT / PAYLOAD) != PAYLOAD_SHA256:
        raise ValueError("Pinned full public payload changed")
    variants = json.loads((ROOT / PAYLOAD).read_text())["native_cases"]
    if [v["selected_depot_id"] for v in variants] != [15, 16]:
        raise ValueError("Expected both public depot cases in declared order")
    result = []
    for v in variants:
        case = intake.native_case_from_payload(v)
        er.nr.validate_case(case)
        if len(case.trips) != 37 or case.identity() != v["case_identity"]:
            raise ValueError("Public case coverage or identity changed")
        result.append(case)
    return result


def freeze(attempt):
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    hashes = source_hashes()
    for name, expected in hashes.items():
        blob = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=ROOT)
        if hashlib.sha256(blob).hexdigest() != expected:
            raise ValueError(f"Uncommitted dependency: {name}")
    spec = {"protocol": PROTOCOL, "source_commit": commit, "source_hashes": hashes,
            "python": sys.version, "platform": platform.platform(),
            "price_exact": str(er.rational(.2)), "price_input": .2,
            "cases": [asdict(c) for c in cases()],
            "case_identities": [c.identity() for c in cases()],
            "algorithm_calls": 2, "complete_seconds_cap": 30,
            "external_process_seconds_cap": 45,
            "scope": "exact ideal stored-input relaxation; public pilot archives remain unchanged"}
    attempt.mkdir(parents=True, exist_ok=False)
    write_new(attempt / "frozen.json", spec)


def run(attempt):
    start = time.monotonic()
    frozen_path = attempt / "frozen.json"
    frozen_hash = sha(frozen_path)
    spec = json.loads(frozen_path.read_text())
    if (spec["protocol"] != PROTOCOL or spec["source_hashes"] != source_hashes()
            or spec["algorithm_calls"] != 2 or spec["price_input"] != .2
            or spec["price_exact"] != str(er.rational(.2))
            or spec["complete_seconds_cap"] != 30 or spec["external_process_seconds_cap"] != 45):
        raise ValueError("Frozen execution identity or budget differs")
    if spec["python"] != sys.version or spec["platform"] != platform.platform():
        raise ValueError("Frozen local runtime differs")
    actual = cases()
    if (json.loads(json.dumps([asdict(c) for c in actual])) != spec["cases"]
            or [c.identity() for c in actual] != spec["case_identities"]):
        raise ValueError("Frozen input mismatch")
    write_new(attempt / "STARTED.json", {"protocol": PROTOCOL, "frozen_sha256": frozen_hash,
                                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    completed = []
    for depot, case in zip((15, 16), actual):
        result = er.solve_relaxation(case, .2)
        result["source_depot_id"] = depot
        result["elapsed_since_start_seconds"] = time.monotonic() - start
        write_new(attempt / f"depot_{depot}.json", result)
        completed.append(result)
        if time.monotonic() - start > spec["complete_seconds_cap"]:
            raise TimeoutError("Complete matching experiment cap reached")
    if source_hashes() != spec["source_hashes"] or sha(frozen_path) != frozen_hash:
        raise ValueError("Source or frozen input changed during execution")
    write_new(attempt / "summary.json", {"protocol": PROTOCOL, "status": "completed",
              "algorithm_calls": len(completed), "elapsed_seconds": time.monotonic() - start,
              "lower_exact": [r["lower_exact"] for r in completed],
              "source_hashes_unchanged": True, "frozen_sha256": frozen_hash,
              "native_optimizer_invoked": False,
              "physical_feasibility_or_native_matrix_optimality_claimed": False})


def supervise(attempt):
    """Exclusive one-shot launch, hard timeout, immutable raw completion bundle."""
    spec = json.loads((attempt / "frozen.json").read_text())
    if spec["external_process_seconds_cap"] != 45 or spec["source_hashes"] != source_hashes():
        raise ValueError("Frozen source or supervisor cap changed")
    command = [sys.executable, "-m", "experiments.sistig_matching_relaxation",
               "run", "--attempt", str(attempt)]
    write_new(attempt / "supervisor_launch.json", {"command": command, "hard_cap_seconds": 45,
              "frozen_sha256": sha(attempt / "frozen.json"),
              "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    start, timed_out, exit_code = time.monotonic(), False, None
    error = None
    try:
        with (attempt / "stdout.txt").open("xb") as out, (attempt / "stderr.txt").open("xb") as err:
            process = subprocess.run(command, cwd=ROOT / "src", stdout=out, stderr=err,
                                     timeout=45, check=False)
            exit_code = process.returncode
    except subprocess.TimeoutExpired:
        # subprocess.run kills and waits for its only child before raising.
        timed_out, exit_code = True, 124
    except Exception as exc:
        error, exit_code = repr(exc), 1
    write_new(attempt / "supervisor_receipt.json", {"elapsed_seconds": time.monotonic() - start,
              "timed_out": timed_out, "exit_code": exit_code, "exception": error,
              "hard_cap_seconds": 45, "source_hashes_unchanged": source_hashes() == spec["source_hashes"]})
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
