"""B3 factor pilot: generator-only level screen and deterministic freeze.

Implements, exactly and normatively, Sections 4 and Appendix A of the
merged `doc/B3_FACTOR_PILOT_SPEC_DRAFT.md`:

- policy P1 witness (depot-only inter-trip charging, NO terminal
  charging, terminal SOC checked at final pull-in);
- schedule-independent bounds N1-N4 with the recomputed per-instance
  N2-necessity assertion (`min_energy > max_saving`);
- relevance R1/R2 on inter-trip depot-arc events only, with R2's
  conservative whole-slot contiguous semantics;
- the exact finite candidate grids, outcome-blind lexicographic
  ordering, baseline-first gate, and DESIGN-NOT-FROZEN disposition;
- a canonical deterministic screen record with every candidate
  transition, per-instance gate results, selected levels, generator
  hashes, and the final 30 selected physical setting-instances.

NO optimizer is imported or invoked: the only egglab import is the
stdlib-only instance generator (`egglab.instance`), and a subprocess
regression proves the closure contains no solver module. Nothing is
launched; no A2 pilot driver, launcher, or confirmation work exists
here. Burned seeds {0, 11, 15} only; seeds 16-31 and 32-37 are never
generated or read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.instance import synthetic_instance

SCHEMA = "b3-factor-screen-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_RELPATH = "doc/B3_FACTOR_PILOT_SPEC_DRAFT.md"
BASE_COMMIT = "b81b15ace8ffd7301ce93f349fdb643cdefd5da6"

# frozen design (spec Sections 2-4)
BURNED_SEEDS = (0, 11, 15)
N_TRIPS = (8, 12)
BASELINE_BATTERY_KWH = 60.0
BASELINE_POWER_KW = 150.0

# level -> (parameter, band lo, band hi, step, starting candidate,
#           expected candidate count)
LEVELS = (
    ("S1_batt_low", "battery_kwh", 40.0, 55.0, 1.0, 45.0, 16),
    ("S2_batt_high", "battery_kwh", 75.0, 120.0, 1.0, 90.0, 46),
    ("S3_pow_low", "charge_power_kw", 50.0, 120.0, 5.0, 75.0, 15),
    ("S4_pow_high", "charge_power_kw", 200.0, 400.0, 5.0, 300.0, 41),
)
SETTING_ORDER = ("S0_baseline", "S1_batt_low", "S2_batt_high",
                 "S3_pow_low", "S4_pow_high")

PROVENANCE_FILES = (
    "src/experiments/b3_factor_screen.py",
    "src/tests/test_b3_factor_screen.py",
    SPEC_RELPATH,
)


class B3ScreenError(RuntimeError):
    """The screen cannot proceed without weakening its contract."""


def sha256_file(path: str | os.PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def assert_burned_seeds(seeds=BURNED_SEEDS) -> None:
    """Only the burned development seeds may ever be generated."""
    if tuple(seeds) != (0, 11, 15):
        raise B3ScreenError(
            f"unexpected seeds {tuple(seeds)!r}: the screen is frozen to "
            "burned seeds (0, 11, 15)")
    for seed in seeds:
        if seed >= 16:
            raise B3ScreenError(
                f"seed {seed} is in a reserved band (16-31 holdout, 32-37 "
                "confirmation); the screen must never generate it")


def refuse_a6_paths(*paths: str | os.PathLike) -> None:
    for path in paths:
        resolved = Path(path).resolve()
        for part in resolved.parts:
            lowered = part.lower()
            if lowered.startswith("a6") or "a6_" in lowered:
                raise B3ScreenError(
                    f"refusing A6 path (scientific boundary): {resolved}")


def assert_output_separation(out_base: str | os.PathLike) -> None:
    """The output root must not overlap the repository's code or
    documentation inputs (equal/nested in either direction), on fully
    resolved paths."""
    out = Path(out_base).resolve()
    for protected in (REPO_ROOT / "src", REPO_ROOT / "doc"):
        protected = protected.resolve()
        if out == protected or protected in out.parents \
                or out in protected.parents:
            raise B3ScreenError(
                f"output root {out} overlaps the protected input tree "
                f"{protected}")


def verify_screen_provenance(claimed: str) -> bool:
    """Full-SHA attribution for artifact generation: the claimed commit
    resolves, is an ancestor of (or equal to) HEAD, the frozen base is an
    ancestor of HEAD, the tracked tree is clean, and the screen module,
    battery, and spec are byte-identical to the claimed commit."""
    if (not claimed or len(claimed) != 40
            or not all(c in "0123456789abcdef" for c in claimed)):
        raise B3ScreenError(
            "analysis-code-commit must be the full 40-character lowercase "
            "hexadecimal SHA")
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{claimed}^{{commit}}"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise B3ScreenError(
            f"claimed commit {claimed} does not resolve") from exc
    if resolved != claimed:
        raise B3ScreenError(
            f"claimed commit {claimed} resolves to {resolved}")
    if subprocess.run(
            ["git", "merge-base", "--is-ancestor", claimed, "HEAD"],
            cwd=REPO_ROOT).returncode != 0:
        raise B3ScreenError(
            f"claimed commit {claimed} is not an ancestor of HEAD")
    if subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"],
            cwd=REPO_ROOT).returncode != 0:
        raise B3ScreenError(
            f"frozen base {BASE_COMMIT} is not an ancestor of HEAD")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT).decode()
    tracked_dirty = [
        line for line in dirty.splitlines() if not line.startswith("??")]
    if tracked_dirty:
        raise B3ScreenError(
            "working tree has tracked modifications; commit the screen "
            "before generating artifacts")
    for relpath in PROVENANCE_FILES:
        committed = subprocess.check_output(
            ["git", "show", f"{claimed}:{relpath}"], cwd=REPO_ROOT)
        if committed != (REPO_ROOT / relpath).read_bytes():
            raise B3ScreenError(
                f"{relpath} differs from the claimed commit {claimed}; "
                "artifacts would be misattributed")
    return True


# --------------------------------------------------------------------------
# frozen candidate grids and outcome-blind preference (spec 4.3)
# --------------------------------------------------------------------------
def candidate_grid(lo: float, hi: float, step: float) -> list[float]:
    count = int(round((hi - lo) / step)) + 1
    return [lo + step * i for i in range(count)]


def preference_order(candidates: list[float], start: float,
                     baseline: float) -> list[float]:
    """Outcome-blind lexicographic preference: closest to the starting
    candidate; tie -> larger distance from baseline (no further tie is
    possible for distinct values)."""
    return sorted(candidates,
                  key=lambda c: (abs(c - start), -abs(c - baseline)))


# --------------------------------------------------------------------------
# instance construction (burned grid only)
# --------------------------------------------------------------------------
def build_instance(seed: int, n_trips: int, battery_kwh: float,
                   charge_power_kw: float):
    if seed not in BURNED_SEEDS:
        raise B3ScreenError(
            f"refusing to generate seed {seed}: not a burned development "
            "seed")
    return synthetic_instance(
        seed=seed, n_trips=n_trips, battery_kwh=battery_kwh,
        charge_power_kw=charge_power_kw)


# --------------------------------------------------------------------------
# N-bounds and the recomputed N2-necessity assertion (spec 4.1)
# --------------------------------------------------------------------------
def necessity_assertion(inst) -> dict:
    """Recompute max detour saving and min trip energy; N2 is a necessary
    bound only while min_energy > max_saving."""
    locations = sorted({t.start_loc for t in inst.trips}
                       | {t.end_loc for t in inst.trips})
    max_saving = max(
        inst.dhk(e, inst.depot) + inst.dhk(inst.depot, s) - inst.dhk(e, s)
        for e in locations for s in locations)
    min_energy = min(t.energy_kwh for t in inst.trips)
    return {"max_saving_kwh": max_saving, "min_energy_kwh": min_energy,
            "ok": min_energy > max_saving}


def n_bounds(inst) -> dict:
    """N1-N4 (spec 4.1). Usable band B = battery - soc_min."""
    band = inst.battery_kwh - inst.soc_min_kwh
    n1 = all(t.energy_kwh <= band for t in inst.trips)
    n2 = all(
        inst.dhk(inst.depot, t.start_loc) + t.energy_kwh
        + inst.dhk(t.end_loc, inst.depot) <= band
        for t in inst.trips)
    n3 = inst.soc_min_kwh <= inst.soc_end_kwh <= inst.battery_kwh
    n4 = inst.charge_power_kw * inst.slot_min / 60 > 0
    return {"n1": n1, "n2": n2, "n3": n3, "n4": n4,
            "ok": n1 and n2 and n3 and n4}


# --------------------------------------------------------------------------
# policy-P1 witness (spec 4.2 / Appendix A.1) — normative arithmetic
# --------------------------------------------------------------------------
def witness(inst) -> dict:
    """Deterministic constructive-duty witness under policy P1.

    Depot-only inter-trip charging; NO charging after the final trip;
    terminal SOC checked at final pull-in (soc_arr >= soc_end_kwh)."""
    trips = sorted(inst.trips, key=lambda t: (t.start_min, t.id))
    vehicles: list[list] = []  # [soc_arr, free_at]
    events: list[tuple] = []   # (a, d, kwh) inter-trip depot-arc events
    for trip in trips:
        depart = trip.start_min - inst.dhm(inst.depot, trip.start_loc)
        need = (inst.dhk(inst.depot, trip.start_loc) + trip.energy_kwh
                + inst.dhk(trip.end_loc, inst.depot))
        chosen = None
        for v_index in range(len(vehicles)):
            soc_arr, free_at = vehicles[v_index]
            if depart < free_at:
                continue
            soc_dep = min(
                inst.battery_kwh,
                soc_arr + inst.charge_power_kw * (depart - free_at) / 60)
            if soc_dep - need < inst.soc_min_kwh:
                continue
            # earliest free_at; tie -> lowest index (first found wins)
            if chosen is None or free_at < chosen[2]:
                chosen = (v_index, soc_dep, free_at)
        if chosen is None:
            if len(vehicles) == inst.max_vehicles:
                return {"feasible": False, "reason": "assignment",
                        "trip_id": trip.id, "events": []}
            v_index = len(vehicles)
            soc_arr, free_at = inst.battery_kwh, 0
            soc_dep = min(
                inst.battery_kwh,
                soc_arr + inst.charge_power_kw * (depart - free_at) / 60)
            if depart < 0 or soc_dep - need < inst.soc_min_kwh:
                return {"feasible": False, "reason": "round-trip-band",
                        "trip_id": trip.id, "events": []}
            vehicles.append([soc_arr, free_at])
            chosen = (v_index, soc_dep, free_at)
        v_index, soc_dep, free_at = chosen
        charge = soc_dep - vehicles[v_index][0]
        if charge > 0:
            events.append((free_at, depart, charge))
        vehicles[v_index] = [
            soc_dep - need,
            trip.end_min + inst.dhm(trip.end_loc, inst.depot)]
    # terminal checks: SOC upon pull-in; NO charging after the final trip
    for soc_arr, _free_at in vehicles:
        if soc_arr < inst.soc_end_kwh:
            return {"feasible": False, "reason": "terminal-soc",
                    "trip_id": None, "events": []}
    return {"feasible": True, "reason": None, "trip_id": None,
            "n_vehicles": len(vehicles), "events": events}


def relevance(inst, events: list[tuple]) -> dict:
    """R1/R2 on inter-trip depot-arc events only (spec 4.2); R2 uses the
    conservative whole-slot contiguous semantics."""
    total = 0.0
    for _a, _d, kwh in events:
        total += kwh
    r1 = total > 0.0
    per_slot = inst.charge_power_kw * inst.slot_min / 60
    timing_free = 0
    for a, d, kwh in events:
        k = math.floor(d / inst.slot_min) - math.ceil(a / inst.slot_min)
        n_c = math.ceil(kwh / per_slot)
        if n_c >= 1 and k >= n_c + 1:
            timing_free += 1
    return {"r1": r1, "total_charge_kwh": total,
            "n_events": len(events), "n_timing_free": timing_free,
            "r2": timing_free >= 1, "ok": r1 and timing_free >= 1}


def evaluate_instance(seed: int, n_trips: int, battery_kwh: float,
                      charge_power_kw: float) -> dict:
    """All gates for one physical setting-instance; pure function."""
    inst = build_instance(seed, n_trips, battery_kwh, charge_power_kw)
    record = {
        "seed": seed, "n_trips": n_trips,
        "battery_kwh": battery_kwh, "charge_power_kw": charge_power_kw,
        "instance_hash": inst.hash(),
        "necessity": necessity_assertion(inst),
        "bounds": n_bounds(inst),
    }
    if not record["necessity"]["ok"] or not record["bounds"]["ok"]:
        record.update(witness=None, relevance=None, ok=False,
                      first_failed_gate=(
                          "necessity" if not record["necessity"]["ok"]
                          else "bounds"))
        return record
    w = witness(inst)
    record["witness"] = {k: v for k, v in w.items() if k != "events"}
    if not w["feasible"]:
        record.update(relevance=None, ok=False,
                      first_failed_gate="witness")
        return record
    rel = relevance(inst, w["events"])
    record["relevance"] = rel
    record["ok"] = rel["ok"]
    record["first_failed_gate"] = (
        None if rel["ok"] else ("r1" if not rel["r1"] else "r2"))
    return record


# --------------------------------------------------------------------------
# screen driver (spec 4.3 / Appendix A.3-A.4)
# --------------------------------------------------------------------------
def _setting_params(name: str, level_value: float | None) -> tuple:
    battery, power = BASELINE_BATTERY_KWH, BASELINE_POWER_KW
    if name == "S1_batt_low" or name == "S2_batt_high":
        battery = level_value
    elif name == "S3_pow_low" or name == "S4_pow_high":
        power = level_value
    return battery, power


def run_screen() -> dict:
    """The complete deterministic screen; returns the canonical record."""
    assert_burned_seeds()
    pairs = [(seed, n) for seed in BURNED_SEEDS for n in N_TRIPS]
    if len(pairs) != 6:
        raise B3ScreenError("expected exactly 6 (seed, n) pairs")

    record = {
        "schema": SCHEMA,
        "spec": {"path": SPEC_RELPATH,
                 "sha256": sha256_file(REPO_ROOT / SPEC_RELPATH)},
        "design": {
            "seeds": list(BURNED_SEEDS),
            "n_trips": list(N_TRIPS),
            "baseline": {"battery_kwh": BASELINE_BATTERY_KWH,
                         "charge_power_kw": BASELINE_POWER_KW},
            "levels": [{
                "name": name, "parameter": parameter,
                "band": [lo, hi], "step": step, "start": start,
                "n_candidates": expected,
            } for (name, parameter, lo, hi, step, start, expected)
                in LEVELS],
        },
        "baseline_gate": [],
        "levels": {},
        "selected_levels": {},
        "setting_instances": [],
        "disposition": None,
    }

    # baseline gate first (S0 fixed; never adjusted)
    baseline_ok = True
    for seed, n in pairs:
        cell = evaluate_instance(seed, n, BASELINE_BATTERY_KWH,
                                 BASELINE_POWER_KW)
        record["baseline_gate"].append(cell)
        baseline_ok = baseline_ok and cell["ok"]
    if not baseline_ok:
        record["disposition"] = {
            "state": "DESIGN-NOT-FROZEN", "reason": "baseline",
            "detail": "S0 failed a gate; S0 is never adjusted"}
        return record

    # levels, independently, in the frozen order
    for (name, parameter, lo, hi, step, start, expected) in LEVELS:
        grid = candidate_grid(lo, hi, step)
        if len(grid) != expected:
            raise B3ScreenError(
                f"{name}: candidate grid has {len(grid)} values, expected "
                f"{expected}")
        transitions = []
        selected = None
        for cand in preference_order(grid, start,
                                     BASELINE_BATTERY_KWH
                                     if parameter == "battery_kwh"
                                     else BASELINE_POWER_KW):
            battery, power = _setting_params(name, cand)
            cells = [evaluate_instance(seed, n, battery, power)
                     for seed, n in pairs]
            failing = next((c for c in cells if not c["ok"]), None)
            if failing is None:
                transitions.append({
                    "candidate": cand, "state": "SELECTED",
                    "cells": cells})
                selected = cand
                break
            transitions.append({
                "candidate": cand, "state": "REJECT",
                "gate": failing["first_failed_gate"],
                "first_failing_instance": {
                    "seed": failing["seed"],
                    "n_trips": failing["n_trips"]},
                "cells": cells})
        record["levels"][name] = {"transitions": transitions,
                                  "selected": selected}
        if selected is None:
            record["disposition"] = {
                "state": "DESIGN-NOT-FROZEN",
                "reason": "non-exercisable", "level": name}
            return record
        record["selected_levels"][name] = selected

    # the final 30 selected physical setting-instances
    frozen = dict(record["selected_levels"])
    for setting in SETTING_ORDER:
        level_value = frozen.get(setting)
        battery, power = _setting_params(setting, level_value)
        for seed, n in pairs:
            inst = build_instance(seed, n, battery, power)
            record["setting_instances"].append({
                "setting": setting, "seed": seed, "n_trips": n,
                "battery_kwh": battery, "charge_power_kw": power,
                "name": inst.name, "instance_hash": inst.hash(),
            })
    if len(record["setting_instances"]) != 30:
        raise B3ScreenError(
            f"expected exactly 30 setting-instances, built "
            f"{len(record['setting_instances'])}")
    record["disposition"] = {"state": "FROZEN",
                             "levels": dict(record["selected_levels"])}
    return record


def canonical_bytes(record: dict) -> bytes:
    return (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()


# --------------------------------------------------------------------------
# deterministic artifact publication
# --------------------------------------------------------------------------
def publish(out_base: str | os.PathLike, stamp: str,
            analysis_code_commit: str, *,
            verify_code_commit: bool = True) -> str:
    refuse_a6_paths(out_base)
    assert_output_separation(out_base)
    if verify_code_commit:
        verify_screen_provenance(analysis_code_commit)
    record = run_screen()
    payload = canonical_bytes(record)
    # nondeterministic-regeneration refusal: the screen must reproduce
    # itself byte-for-byte within one publication
    if canonical_bytes(run_screen()) != payload:
        raise B3ScreenError(
            "screen record did not regenerate deterministically; refusing "
            "to publish")

    out_base = Path(out_base)
    out_base.mkdir(parents=True, exist_ok=True)
    out_dir = out_base / stamp
    if out_dir.exists():
        raise B3ScreenError(f"refusing existing output directory: {out_dir}")
    staging = Path(tempfile.mkdtemp(
        prefix=f".{stamp}.b3-screen-staging-", dir=out_base))
    try:
        (staging / "SCREEN_RECORD.json").write_bytes(payload)
        manifest = {
            "schema": SCHEMA,
            "stamp": stamp,
            "analysis_code_commit": analysis_code_commit,
            "analysis_code_verified": verify_code_commit,
            "base_commit": BASE_COMMIT,
            "spec": record["spec"],
            "disposition": record["disposition"],
            "counts": {
                "settings": len(SETTING_ORDER),
                "baseline_instances": len(record["baseline_gate"]),
                "setting_instances": len(record["setting_instances"]),
                "candidate_grid_sizes": {
                    name: expected
                    for (name, _p, _lo, _hi, _s, _st, expected) in LEVELS},
            },
            "outputs": {
                "SCREEN_RECORD.json": hashlib.sha256(payload).hexdigest(),
            },
        }
        with open(staging / "MANIFEST.json", "w") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.rename(staging, out_dir)
    except BaseException:
        for entry in staging.glob("*"):
            entry.unlink()
        staging.rmdir()
        raise
    return str(out_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out", default=str(REPO_ROOT / "result" / "b3_factor_screen"))
    parser.add_argument("--stamp")
    parser.add_argument("--analysis-code-commit")
    parser.add_argument(
        "--screen-only", action="store_true",
        help="run the screen and print the record; write nothing")
    args = parser.parse_args()
    if args.screen_only:
        record = run_screen()
        sys.stdout.write(canonical_bytes(record).decode())
        return
    if not args.stamp or not args.analysis_code_commit:
        parser.error("--stamp and --analysis-code-commit are required "
                     "unless --screen-only")
    out_dir = publish(args.out, args.stamp, args.analysis_code_commit)
    print(out_dir)


if __name__ == "__main__":
    main()
