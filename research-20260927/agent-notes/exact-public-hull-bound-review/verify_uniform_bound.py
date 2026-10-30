#!/usr/bin/env python3
"""Independent exact audit of the uniform-price depot-15 hull bound; stdlib only."""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import subprocess

SOURCE_COMMIT = "80eb69544f568a7ed346f0d603004a10f61c481a"
CASE_ID = "1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7"
CANDIDATE_SHA = {
    "NOTE.md": "6c0b0ac69e519e3e8251e12c23cbcb235a04f0a985496e9838d00eadaf56a700",
    "RESULT.json": "7f8bc70ece82c2569c83eea90a4a046f36d161d1f0f9a993c6b1a04a6ba70bac",
    "check_uniform_bound.py": "443651df15a30fb9c1d974d8e533128035df62a5e6f3e8e0808f4aee399dcf4e",
}
INPUT_SHA = {
    "result/sistig_cardinality_flow/20260927-attempt1/frozen.json": "bce2293080c3d19d05c37aa8c6bb4a285f1afe59fbde161fa6a6b6505784d103",
    "result/sistig_cardinality_flow/20260927-attempt1/depot_15.json": "01a818211e68be38093b478308d0780d752aeac150b7959d7bd785552d6bdb39",
    "result/sistig_cardinality_flow/20260927-attempt1/review/REVIEW.md": "60604b3467c17ec1c833ef56a2634a7e091d6cb677aaea4ec3c684dfdec15c94",
    "result/sistig_cardinality_flow/20260927-attempt1/review/audit-report.json": "f4d6acdf46bd3cd6839fc727c9786b63c2b63dbb4fb507197c7336a3f3f6260f",
    "result/sistig_pricing/20260927-grb-job557543-attempt1/frozen.json": "35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b",
    "doc/SISTIG_ONE_BUS_OBSTRUCTION_20260927.md": "a2c4badf085d9d67c205170f8b7460e7efc1b40ac8b87aab4aa846c1815d8bdb",
    "research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md": "7b1d55d1d20fce676ded6aaeb6ae0965cd70fc464581290ad792f2056bce53a2",
}
BLOB_SHA = {
    "src/experiments/sistig_nonlinear_pilot.py": "36195617aa3b5b3955bea3f7fe04011a59d0c8d5458f20ad454a80944a7cb2de",
    "doc/SISTIG_NONLINEAR_PILOT_PROTOCOL_20260927.md": "5fe33d06ddf1a52b611013932107bd2a8583cae02b7f3d9ffb0394a53ec0f326",
    "src/experiments/sistig_native_case.py": "f47a7a926d102f948d73e6d450f25a46fe7ad84fc93e4ff7e877da76ffe0e3c9",
    "src/egglab/native_recharge.py": "0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3",
}


def need(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def q(value):
    if isinstance(value, bool):
        raise AssertionError("boolean is not a numeric input")
    if isinstance(value, float):
        return Q.from_float(value)
    return Q(value)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit(repo, candidate_dir):
    need((repo / ".git").exists(), "repo path is not a git checkout")
    candidate_bytes = {}
    for name, digest in CANDIDATE_SHA.items():
        raw = (candidate_dir / name).read_bytes()
        need(sha(raw) == digest, f"candidate-byte pin mismatch: {name}")
        candidate_bytes[name] = raw
    inputs = {}
    for name, digest in INPUT_SHA.items():
        raw = (repo / name).read_bytes()
        need(sha(raw) == digest, f"frozen review input mismatch: {name}")
        inputs[name] = raw
    blobs = {}
    for name, digest in BLOB_SHA.items():
        raw = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{name}"], cwd=repo)
        need(sha(raw) == digest, f"source commit blob mismatch: {name}")
        blobs[name] = raw.decode("utf-8")

    flow_frozen = json.loads(inputs["result/sistig_cardinality_flow/20260927-attempt1/frozen.json"])
    flow = json.loads(inputs["result/sistig_cardinality_flow/20260927-attempt1/depot_15.json"])
    flow_audit = json.loads(inputs["result/sistig_cardinality_flow/20260927-attempt1/review/audit-report.json"])
    flat_frozen = json.loads(inputs["result/sistig_pricing/20260927-grb-job557543-attempt1/frozen.json"])
    result = json.loads(candidate_bytes["RESULT.json"])
    case = flow_frozen["cases"][0]
    flat_control = flat_frozen["controls"][0]
    need(case == flat_control["case"], "flat and flow frozen cases differ")
    need(flow["case_identity"] == flat_control["case_identity"] == CASE_ID,
         "case identity differs across frozen inputs")
    need(flat_control["source_payload_sha256"] ==
         "af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6",
         "public case payload pin differs")
    need(flow_audit["verdict"].startswith("PASS") and
         flow_audit["cases"][0]["case_identity"] == CASE_ID and
         flow_audit["cases"][0]["lower_exact"] == flow["lower_exact"] and
         flow_audit["cases"][0]["primal_dual_equal"] is True and
         flow_audit["cases"][0]["paths_in_relaxation"] == 2 and
         flow_audit["cases"][0]["services"] == 37 and
         flow_audit["cases"][0]["gate_flow"] == 35 and
         flow_audit["cases"][0]["real_edges_selected"] == 35 and
         flow["used_paths_in_relaxation"] == 2,
         "independently reviewed two-path lower certificate is not pinned")

    source = blobs["src/experiments/sistig_nonlinear_pilot.py"]
    protocol = blobs["doc/SISTIG_NONLINEAR_PILOT_PROTOCOL_20260927.md"]
    case_source = blobs["src/experiments/sistig_native_case.py"]
    charge_source = blobs["src/egglab/native_recharge.py"]
    need("(.2,) * 30," in source and "(1 / 900,) * 30" in source,
         "pinned pilot market literals changed")
    need("F(L)=sum_t(a_t L_t + b_t L_t^2/2)" in protocol,
         "pinned nonlinear objective description changed")
    need('"initial_inventory_policy": "every used bus starts at full usable EB-3 inventory (400 kWh)"' in case_source
         and '"terminal_policy": "every used bus returns to its selected depot and must restore full usable inventory by 30:00 (1800 min); terminal opening is 00:00, so all post-pull-in time is available"' in case_source,
         "pinned full-inventory endpoint policy changed")
    need('if m.kind == "depot":' in charge_source and 'elif m.kind == "pullin":' in charge_source
         and 'raise ValueError("Charging on a noncharging movement")' in charge_source,
         "pinned charging eligibility changed")

    a, b = Q.from_float(0.2), Q.from_float(1 / 900)
    f, efficiency = q(case["vehicle_cost"]), q(case["efficiency"])
    service_energy = sum((q(t["energy_kwh"]) for t in case["trips"]), Q(0))
    need(a == q(flow["flat_price"]) == q(flow_frozen["price_input"])
         and a == Q(flow_frozen["price_exact"]) and b > 0 and f == 100 and efficiency == 1,
         "stored binary price/cost/efficiency differs")
    need(len(case["trips"]) == 37 and len(case["market_edges_min"]) == 31
         and case["market_edges_min"] == list(range(0, 1801, 60))
         and q(case["battery_kwh"]) == 400 and q(case["reserve_kwh"]) == 0
         and q(case["deadhead_cost_per_min"]) == 0,
         "depot-15 fleet/market assumptions differ")
    need(all(q(t["energy_kwh"]) >= 0 for t in case["trips"])
         and all(q(leg["energy_kwh"]) >= 0 for m in case["movements"] for leg in m["legs"]),
         "negative service or movement energy invalidates the floor argument")

    trips = sorted(case["trips"], key=lambda t: (q(t["start_min"]), q(t["end_min"]), t["id"]))
    need(len(trips) == 37 and all(q(t["start_min"]) < q(t["end_min"]) for t in trips)
         and all(q(x["end_min"]) <= q(y["start_min"]) for x, y in zip(trips, trips[1:])),
         "services do not force the unique chronological order")
    forced = []
    for before, after in zip(trips, trips[1:]):
        modes = [m for m in case["movements"] if m.get("before") == before["id"]
                 and m.get("after") == after["id"]]
        need(len(modes) == 1 and modes[0]["kind"] == "direct",
             "one-bus consecutive transition has an alternate/depot mode")
        forced.append(modes[0])
    need(len(forced) == 36 and service_energy > q(case["battery_kwh"]),
         "one-bus energy obstruction does not hold")

    movement_by_id = {m["id"]: m for m in case["movements"]}
    selected = flow["selected_movement_ids"]
    need(len(selected) == len(set(selected)) == 39 and all(mid in movement_by_id for mid in selected),
         "two-path flow movements are incomplete or duplicated")
    selected_energy = service_energy + sum((q(leg["energy_kwh"])
        for mid in selected for leg in movement_by_id[mid]["legs"]), Q(0))
    lower = Q(flow["lower_exact"])
    emin = (lower - 2 * f) / a
    need(lower == 2 * f + a * selected_energy and emin == selected_energy,
         "two-path exact flat primal energy/lower-bound equality changed")

    periods = len(case["market_edges_min"]) - 1
    uniform = a + b * emin / periods
    eservice = service_energy
    margin = 3 * f + uniform * eservice - (2 * f + uniform * emin)
    need(uniform >= a and margin > 0,
         "uniform-price three-or-more-bus comparison is not strict")
    conjugate = periods * (uniform - a) ** 2 / (2 * b)
    pricing_lower = 2 * f + uniform * emin
    ch_lower = pricing_lower - conjugate
    simplified = 2 * f + a * emin + b * emin**2 / (2 * periods)
    need(ch_lower == simplified, "Fenchel simplification mismatch")

    stated = {"a": a, "b": b, "Eservice": eservice, "Lflow": lower,
              "Emin": emin, "uniform_price": uniform,
              "three_bus_margin": margin, "conjugate": conjugate,
              "pricing_lower": pricing_lower, "CH_lower": ch_lower}
    for name, value in stated.items():
        need(result[name] == str(value), f"candidate exact value mismatch: {name}")
    need(result["CH_lower_decimal"] == format(float(ch_lower), ".12f"),
         "candidate decimal display mismatch")

    witness_dir = repo / "result/sistig_exact_witness/20260927-depot15-attempt1"
    witness = (witness_dir / "depot15_exact_candidate.json").read_bytes()
    witness_review_dir = repo / "research-20260927/agent-notes/exact-public-witness-review"
    witness_review = (witness_review_dir / "REVIEW.md").read_bytes()
    witness_report = json.loads((witness_review_dir / "audit-report-portable-20260927.json").read_text())
    need(sha(witness) == "fafb2e2721a283b0ef43b94357c497710ad113c79f85427a8aabc4211b8aa325"
         and sha(witness_review) == "831a10c42e82a15ac2936ecc67d0d7c9b2f9571cd6372adbd8b7d697377012a2"
         and witness_report["verdict"] == "PASS exact ideal depot-15 witness"
         and witness_report["candidate_sha256"] == sha(witness),
         "independently passed exact witness pin changed")
    wc = json.loads(witness)
    need(wc["case_identity"] == CASE_ID and len(wc["hourly_grid_kwh"]) == periods,
         "exact witness does not match this case and 30-hour market")
    loads = [Q(x) for x in wc["hourly_grid_kwh"]]
    witness_upper = q(wc["ops_cost_exact"]) + sum(
        (a * L + b * L**2 / 2 for L in loads), Q(0))
    need(sum(loads, Q(0)) == Q(wc["total_grid_kwh"])
         and q(wc["flat_objective_exact"]) == q(wc["ops_cost_exact"]) + a * sum(loads, Q(0))
         and ch_lower <= witness_upper,
         "separately reviewed exact witness load/objective arithmetic mismatch")

    return {
        "verdict": "PASS exact ideal stored-input uniform-price full-hull lower bound",
        "source_commit": SOURCE_COMMIT,
        "candidate_hashes": {k: CANDIDATE_SHA[k] for k in sorted(CANDIDATE_SHA)},
        "pinned_input_sha256": dict(INPUT_SHA),
        "pinned_source_blob_sha256": dict(BLOB_SHA),
        "case_identity": CASE_ID,
        "independently_recomputed": {k: str(v) for k, v in stated.items()},
        "one_bus": {"forced_unique_direct_transitions": len(forced),
                    "service_energy_exact": str(service_energy),
                    "battery_exact": str(q(case["battery_kwh"])),
                    "charging_modes_only_depot_or_pullin": True},
        "convex_mixture_logic": "all physical plans satisfy K*f+p*E >= pricing_lower; linearity preserves it under mixtures, Fenchel applies to the averaged 30-load vector",
        "separate_exact_witness_nonlinear_upper": {
            "witness_sha256": sha(witness), "objective_exact": str(witness_upper),
            "objective_decimal": format(float(witness_upper), ".13f"),
            "scope": "CH <= D <= this exact ideal feasible-plan value; no D-CH gap or optimum claim"},
        "method": "stdlib JSON/Fraction/hashlib and pinned git blob reads; no author checker or optimizer",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    candidate_dir = (args.candidate_dir.resolve() if args.candidate_dir else
        repo / "result/sistig_exact_hull_bound/20260927-uniform-price1")
    report = audit(repo, candidate_dir)
    report["independent_verifier_sha256"] = sha(Path(__file__).read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(report, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps({"verdict": report["verdict"], "case_identity": report["case_identity"],
                      "CH_lower": report["independently_recomputed"]["CH_lower"],
                      "witness_upper": report["separate_exact_witness_nonlinear_upper"]["objective_exact"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
