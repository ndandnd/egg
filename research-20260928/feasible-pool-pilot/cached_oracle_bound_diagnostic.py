"""Posthoc algebra on saved pricing bounds; no optimizer or frozen-result edits."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from egglab import native_hull as hull

MANIFEST_SHA = "b2f3630f4229792c47f60bc2a1a60645d506fd887feaa2a3e379bd8107628e6a"
ARM = "reserve_feasible_hull"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def diagnose(attempt):
    started = time.monotonic()
    manifest_bytes = (attempt / "MANIFEST.json").read_bytes()
    if digest(manifest_bytes) != MANIFEST_SHA:
        raise ValueError("This diagnostic requires the unchanged pilot seal")
    files = json.loads(manifest_bytes)["files"]

    def verified_bytes(name):
        data = (attempt / name).read_bytes()
        expected = files[name]
        if len(data) != expected["bytes"] or digest(data) != expected["sha256"]:
            raise ValueError("Changed sealed input: " + name)
        return data

    frozen = json.loads(verified_bytes("frozen.json"))
    rows = []
    for case in ("public_depot15", "public_depot16"):
        folder0, folder1 = f"{case}/state0/{ARM}", f"{case}/state1/{ARM}"
        previous = json.loads(verified_bytes(folder0 + "/raw_result.json"))["result"]
        current = json.loads(verified_bytes(folder1 + "/raw_result.json"))["result"]
        for field in ("physical_identity", "pricing_oracle", "extraction_policy"):
            if previous[field] != current[field]:
                raise ValueError("Physical oracle changed across markets: " + field)
        if previous["physical_identity"] != frozen["cases"][case]["case_identity"]:
            raise ValueError("Physical case differs from freeze")
        saved = previous["lower_certificate"]
        matches = []
        events_name = folder0 + "/events.jsonl"
        for line in verified_bytes(events_name).splitlines():
            event = json.loads(line)
            if event.get("event") != "pricing_result":
                continue
            result = event["result"]
            if result.get("prices") != saved["prices"] or result.get("lower") != saved["pricing_lower"]:
                continue
            if (result["case_identity"] != previous["physical_identity"]
                    or result["formulation"] != previous["pricing_oracle"]
                    or result["extraction_policy"] != previous["extraction_policy"]
                    or result["status"] not in ("certified", "bounded")):
                raise ValueError("Saved physical pricing provenance differs")
            stats = {key: result["stats"].get(key) for key in
                     ("backend", "status", "incumbent", "lower_bound", "wall_s",
                      "seconds_cap", "threads", "n_vars", "n_int", "n_constraints")}
            matches.append({"call": event["call"], "status": result["status"],
                            "lower": result["lower"], "upper": result["upper"],
                            "native_stats": stats})
        if len(matches) != 1:
            raise ValueError("Expected one matching original physical pricing result")
        markets = frozen["cases"][case]["markets"]
        initial, target = (hull.Market(m["name"], tuple(m["a"]), tuple(m["b"])) for m in markets)
        if (previous["market_identity"] != initial.identity()
                or current["market_identity"] != target.identity()
                or hull.fenchel_bound(initial, saved["prices"], saved["pricing_lower"]) != saved):
            raise ValueError("Saved market identity or certificate does not replay")
        rebuilt = hull.fenchel_bound(target, saved["prices"], saved["pricing_lower"])
        # Independent stored-number evaluation, including the nonnegative-load domain.
        conjugate = sum((max(Fraction(p) - Fraction(a), 0) ** 2 / (2 * Fraction(b))
                         for p, a, b in zip(saved["prices"], target.a, target.b)), Fraction(0))
        lower = Fraction(saved["pricing_lower"]) - conjugate
        if str(lower) != rebuilt["lower_exact"]:
            raise ValueError("Independent conjugate arithmetic differs")
        gap = Fraction(current["mixture"]["objective_exact"]) - lower
        if gap < 0:
            raise ValueError("Posthoc enclosure reversed")
        rows.append({"case": case, "physical_identity": previous["physical_identity"],
                     "old_market_certificate": saved, "original_pricing_evidence": matches[0],
                     "source_events": {"path": events_name, **files[events_name]},
                     "target_market_identity": target.identity(), "rebuilt_certificate": rebuilt,
                     "original_target_lower": current["lower"],
                     "original_target_upper": current["upper"],
                     "original_target_gap": current["gap"],
                     "posthoc_gap_exact": str(gap), "posthoc_gap_upper": hull.outward(gap, True),
                     "original_target_status_unchanged": current["status"]})
    return {"kind": "posthoc physical-oracle-bound re-evaluation; outside frozen pilot",
            "source_commit": frozen["source_commit"], "sealed_manifest_sha256": MANIFEST_SHA,
            "new_optimization_calls": 0,
            "timing_scope": "diagnostic input reads and algebra; excludes imports/startup/output; not pilot timing",
            "diagnostic_elapsed_seconds": time.monotonic() - started, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.attempt)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    for row in result["rows"]:
        print(row["case"], "rebuilt lower", row["rebuilt_certificate"]["lower"],
              "posthoc gap upper", row["posthoc_gap_upper"])


if __name__ == "__main__":
    main()
