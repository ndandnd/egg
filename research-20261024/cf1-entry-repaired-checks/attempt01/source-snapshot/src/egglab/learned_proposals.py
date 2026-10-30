"""Developmental, CPU-light topology prediction with full-fleet pool proposals.

The learned movement prior ranks *saved physical plans*. It never synthesizes a
plan, changes charging, or claims native matrix feasibility. Every returned
plan is separately replayed and is still only a hint to the native solver.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import time

import numpy as np

from egglab import native_recharge as nr
from egglab import native_pathflow as pf

FEATURES = (
    "pullout", "direct", "depot", "pullin", "start_time", "end_time",
    "duration", "movement_energy", "before_energy", "after_energy",
    "charge_window", "window_price_mean", "window_price_min", "market_mean",
    "market_spread", "same_place", "intercept",
)
POLICY = "edge-logistic-route-topology-pool-projection-v1"


def case_from_dict(raw):
    """Invert dataclasses.asdict(NativeCase) without changing numeric values."""
    movements = tuple(nr.Movement(m["id"], m["kind"], m["before"], m["after"],
        tuple(nr.Leg(**leg) for leg in m["legs"]), m.get("depot_split"))
        for m in raw["movements"])
    return nr.NativeCase(raw["name"], tuple(nr.Trip(**t) for t in raw["trips"]),
        movements, tuple(nr.Resource(**r) for r in raw["resources"]),
        tuple(raw["market_edges_min"]), raw["depot"], raw["max_vehicles"],
        raw["battery_kwh"], raw["reserve_kwh"], raw["terminal_open_min"],
        raw["recharge_deadline_min"], raw["vehicle_cost"],
        raw.get("deadhead_cost_per_min", 0.0), raw.get("efficiency", 1.0),
        raw.get("graph_scope", "declared-movement-modes-only"))


def _market_arrays(row):
    market = row.get("market") or {}
    a = row.get("market_prices", market.get("a"))
    b = row.get("market_quadratic", market.get("b"))
    if a is None or b is None:
        raise ValueError("Catalog row lacks market a/b")
    return tuple(float(x) for x in a), tuple(float(x) for x in b)


def checked_row(row):
    """Rebuild and replay a catalog witness before using it as label or seed."""
    case = case_from_dict(row["case"])
    if case.identity() != row["case_identity"]:
        raise ValueError("Catalog case identity mismatch")
    nr.validate_case(case)
    a, b = _market_arrays(row)
    nr._check_market(case, a, b)
    plan = row.get("label", {}).get("plan")
    if not row.get("label", {}).get("feasible") or not isinstance(plan, dict):
        raise ValueError("Catalog row lacks a feasible full plan")
    replay = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    return case, a, b, plan, replay


def _window_prices(case, movement, prices):
    if movement.kind == "depot":
        lo = movement.legs[movement.depot_split-1].arrive_min
        hi = movement.legs[movement.depot_split].depart_min
    elif movement.kind == "pullin":
        lo = max(movement.legs[-1].arrive_min, case.terminal_open_min)
        hi = case.recharge_deadline_min
    else:
        return 0.0, float(np.mean(prices)), min(prices)
    weights = [max(0.0, min(hi, right)-max(lo, left))
        for left, right in zip(case.market_edges_min, case.market_edges_min[1:])]
    total = sum(weights)
    if total <= 0:
        return 0.0, float(np.mean(prices)), min(prices)
    return total, sum(p*w for p, w in zip(prices, weights))/total, min(
        p for p, w in zip(prices, weights) if w > 0)


def edge_features(case, prices):
    """Pure case/target-market features, with no objective or solver labels."""
    nr._check_prices(case, prices)
    trips = {t.id:t for t in case.trips}
    horizon = max(case.recharge_deadline_min, 1.0)
    battery = max(case.battery_kwh, 1.0)
    market_mean = float(np.mean(prices))
    spread = float(max(prices)-min(prices))
    rows = []
    for m in case.movements:
        first, last = m.legs[0], m.legs[-1]
        window, window_mean, window_min = _window_prices(case, m, prices)
        before = trips.get(m.before)
        after = trips.get(m.after)
        rows.append((
            float(m.kind == "pullout"), float(m.kind == "direct"),
            float(m.kind == "depot"), float(m.kind == "pullin"),
            first.depart_min/horizon, last.arrive_min/horizon,
            (last.arrive_min-first.depart_min)/horizon,
            sum(leg.energy_kwh for leg in m.legs)/battery,
            (before.energy_kwh if before else 0.0)/battery,
            (after.energy_kwh if after else 0.0)/battery,
            window/horizon, window_mean, window_min, market_mean, spread,
            float(first.origin == last.destination), 1.0,
        ))
    x = np.asarray(rows, dtype=float)
    if x.ndim != 2 or x.shape[1] != len(FEATURES) or not np.isfinite(x).all():
        raise ValueError("Invalid movement features")
    return x


def selected_vector(case, plan):
    ids = {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]}
    pf.recover_paths(case, ids)
    return np.asarray([float(m.id in ids) for m in case.movements])


@dataclass(frozen=True)
class EdgePrior:
    mean: tuple[float, ...]
    scale: tuple[float, ...]
    weights: tuple[float, ...]
    training_groups: tuple[str, ...]
    training_rows: tuple[str, ...]

    def to_dict(self):
        return {"policy": POLICY, "features": list(FEATURES), "mean": self.mean,
            "scale": self.scale, "weights": self.weights,
            "training_groups": self.training_groups, "training_rows": self.training_rows,
            "label_status": "best-known solver incumbents; provisional, not optimal labels"}

    @classmethod
    def from_dict(cls, data):
        if data.get("policy") != POLICY or tuple(data.get("features", ())) != FEATURES:
            raise ValueError("Unknown learned proposal policy/features")
        return cls(*(tuple(data[key]) for key in
            ("mean", "scale", "weights", "training_groups", "training_rows")))

    def logits(self, case, prices):
        x = edge_features(case, prices)
        return ((x-np.asarray(self.mean))/np.asarray(self.scale)) @ np.asarray(self.weights)

    def score(self, case, prices, plan):
        # Diagnostic tie breaker. This does not use the target objective.
        return float(selected_vector(case, plan) @ self.logits(case, prices)/len(case.trips))

    def propose_topology(self, case, prices):
        """Predict incoming/outgoing modes per service, prior to feasibility repair.

        This set can branch or be physically impossible; projecting onto a
        separately replayed full-fleet pool is required before solver use.
        """
        logits = self.logits(case, prices)
        chosen = set()
        for trip in case.trips:
            for side in ("after", "before"):
                choices = [j for j, m in enumerate(case.movements)
                    if getattr(m, side) == trip.id]
                if not choices:
                    raise ValueError("Service lacks declared incoming/outgoing mode")
                winner = max(choices, key=lambda j:(logits[j], -j))
                chosen.add(case.movements[winner].id)
        return tuple(sorted(chosen))


def fit(rows, *, steps=500, learning_rate=0.1, ridge=0.01):
    """Balanced logistic route prior. Only explicit train rows enter fitting."""
    samples, groups, ids = [], set(), []
    for row in rows:
        if row.get("split") != "train" or row.get("arm") not in ("source", "cold"):
            continue
        if not row.get("label", {}).get("feasible"):
            continue
        case, a, _, plan, _ = checked_row(row)
        samples.append((edge_features(case, a), selected_vector(case, plan)))
        groups.add(str(row["base_group"]))
        ids.append(str(row["row_id"]))
    if not samples:
        raise ValueError("No replayed feasible train incumbents")
    x = np.concatenate([item[0] for item in samples])
    y = np.concatenate([item[1] for item in samples])
    if not 0 < y.sum() < len(y):
        raise ValueError("Training labels lack positive/negative movements")
    mean, scale = x.mean(axis=0), x.std(axis=0)
    # Preserve the intercept, and avoid amplification of constant columns.
    mean[-1], scale[-1] = 0.0, 1.0
    scale[scale < 1e-8] = 1.0
    z = (x-mean)/scale
    w = np.zeros(z.shape[1])
    counts = np.asarray([len(label) for _, label in samples])
    per_row = np.concatenate([np.full(n, 1/(len(samples)*n)) for n in counts])
    positive = float(np.sum(per_row*y))
    negative = float(np.sum(per_row*(1-y)))
    sample_weight = per_row*np.where(y > 0, 0.5/positive, 0.5/negative)
    for _ in range(steps):
        logits = np.clip(z @ w, -35, 35)
        probability = 1/(1+np.exp(-logits))
        penalty = w.copy(); penalty[-1] = 0
        gradient = z.T @ (sample_weight*(probability-y)) + ridge*penalty
        w -= learning_rate*gradient
    return EdgePrior(tuple(mean), tuple(scale), tuple(w), tuple(sorted(groups)), tuple(ids))


def rank_candidates(model, target_row, source_rows):
    """Choose a same-case, replayed full fleet and report cold controls."""
    inference_started = time.perf_counter()
    target_case = case_from_dict(target_row["case"])
    if target_case.identity() != target_row["case_identity"]:
        raise ValueError("Target physical identity mismatch")
    a, b = _market_arrays(target_row)
    nr._check_market(target_case, a, b)
    target_group = str(target_row["base_group"])
    if target_group in model.training_groups or target_row.get("split") == "train":
        raise ValueError("Target group entered learner fit")
    proposed_topology = set(model.propose_topology(target_case, a))
    topology_seconds = time.perf_counter()-inference_started
    candidates = []
    for source in source_rows:
        if (source.get("arm") != "source" or source.get("case_identity") != target_case.identity()
                or str(source.get("base_group")) != target_group):
            continue
        try:
            _, source_a, _, plan, replay = checked_row(source)
        except (ValueError, KeyError, TypeError, IndexError):
            continue
        if nr.digest(plan) != source.get("label", {}).get("plan_hash", nr.digest(plan)):
            continue
        nearest = math.sqrt(sum((p-q)**2 for p, q in zip(a, source_a)))
        bill_exact = Fraction(replay["ops_cost"]) + sum((
            Fraction(p)*Fraction(load) + Fraction(curve)*Fraction(load)**2/2
            for p, curve, load in zip(a, b, replay["load"])), Fraction(0))
        bill = float(bill_exact)
        actual_topology = {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]}
        candidates.append({"source_row_id":source["row_id"], "score":model.score(
            target_case, a, plan), "nearest_price_distance":nearest,
            "direct_bill":bill, "direct_bill_exact":str(bill_exact),
            "_bill_exact":bill_exact,
            "topology_distance":len(actual_topology ^ proposed_topology),
            "plan":plan, "replay_ok":True,
            "source_acquisition_seconds":source["label"].get("elapsed_seconds"),
            "physical_identity":target_case.identity(),
            "source_status":source["label"].get("status"),
            "source_optimality":source["label"].get("optimality")})
    if not candidates:
        raise ValueError("No replayed same-case source fleet candidates")
    validation_seconds = time.perf_counter()-inference_started-topology_seconds
    learned = min(candidates, key=lambda c:(c["topology_distance"],
        -c["score"], c["nearest_price_distance"], c["source_row_id"]))
    first_source = candidates[0]
    nearest = min(candidates, key=lambda c:(c["nearest_price_distance"], c["source_row_id"]))
    cheapest = min(candidates, key=lambda c:(c["_bill_exact"], c["source_row_id"]))
    for candidate in candidates:
        del candidate["_bill_exact"]
    return {"policy":POLICY, "target_row_id":target_row["row_id"],
        "base_group":target_group, "case_identity":target_case.identity(),
        "proposed_topology":sorted(proposed_topology),
        "projection":"minimum symmetric-difference to replayed same-case source fleets",
        "online_timing_seconds":{"topology_prediction":topology_seconds,
            "source_validation_and_scoring":validation_seconds,
            "total":time.perf_counter()-inference_started},
        "source_pool_acquisition_seconds":sum(
            row["label"].get("elapsed_seconds") or 0 for row in source_rows
            if row.get("arm") == "source" and row.get("case_identity") == target_case.identity()),
        "chosen":learned, "controls":{"first_source":first_source["source_row_id"],
            "nearest_price":nearest["source_row_id"],
            "cheapest_bill":cheapest["source_row_id"]},
        "candidates":candidates}
