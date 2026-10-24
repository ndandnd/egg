"""Small prespecified ridge model for source-route target charging response."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np

from egglab import native_hull as nh
from egglab import native_recharge as nr

POLICY = "post-charge-direct-residual-ridge-v1"
FEATURES = ("intercept", "direct_cost_per_trip", "ops_per_trip",
            "target_linear_load_per_trip", "load_per_trip",
            "source_price_distance", "source_one", "trip_count_scaled")
RIDGE = 1.0


def direct_cost(case, target, replay):
    return Fraction(replay["ops_cost"]) + nh.supply(target, replay["load"])


def features(case, target, source_market, replay, source):
    """Pre-target-solve quantities only; no charged plan or target label."""
    if source not in ("source0", "source1"):
        raise ValueError("Unknown source market")
    n = len(case.trips)
    if n <= 0 or len(replay["load"]) != len(target.a):
        raise ValueError("Invalid source replay for feature extraction")
    direct = float(direct_cost(case, target, replay)) / n
    linear_load = sum(float(p) * float(x) for p, x in zip(target.a, replay["load"])) / n
    distance = sum((float(p)-float(q))**2 for p, q in zip(target.a, source_market.a))
    vector = (1.0, direct, float(replay["ops_cost"])/n, linear_load,
              sum(float(x) for x in replay["load"])/n, distance,
              float(source == "source1"), n/28.0)
    if len(vector) != len(FEATURES) or not all(math.isfinite(x) for x in vector):
        raise ValueError("Nonfinite response feature")
    return vector


@dataclass(frozen=True)
class ResponseModel:
    mean: tuple[float, ...]
    scale: tuple[float, ...]
    weights: tuple[float, ...]
    training_groups: tuple[str, ...]
    training_rows: tuple[str, ...]

    def to_dict(self):
        return {"policy": POLICY, "features": FEATURES, "ridge": RIDGE,
                "target": "(post_charge_exact_cost-direct_exact_cost)/trip_count",
                "mean": self.mean, "scale": self.scale, "weights": self.weights,
                "training_groups": self.training_groups, "training_rows": self.training_rows,
                "label_status": "independently replayed feasible LP incumbents; no target global optimum"}

    @classmethod
    def from_dict(cls, raw):
        if (raw.get("policy") != POLICY or tuple(raw.get("features", ())) != FEATURES
                or float(raw.get("ridge", -1)) != RIDGE):
            raise ValueError("Unknown response model policy")
        return cls(*(tuple(raw[key]) for key in
                     ("mean", "scale", "weights", "training_groups", "training_rows")))

    def predict_cost(self, case, target, source_market, replay, source):
        x = np.asarray(features(case, target, source_market, replay, source))
        if (len(self.mean) != len(FEATURES) or len(self.scale) != len(FEATURES)
                or len(self.weights) != len(FEATURES)):
            raise ValueError("Malformed response model")
        residual = float(((x-np.asarray(self.mean))/np.asarray(self.scale)) @ np.asarray(self.weights))
        predicted = float(direct_cost(case, target, replay)) + residual*len(case.trips)
        if not math.isfinite(predicted):
            raise ValueError("Nonfinite response prediction")
        return predicted


def fit(samples):
    """Samples contain pre-target features and replayed exact LP cost; fixed ridge."""
    if len(samples) < 2 or len({sample["group"] for sample in samples}) < 2:
        raise ValueError("Insufficient independent training groups")
    if len({sample["row_id"] for sample in samples}) != len(samples):
        raise ValueError("Duplicate training label")
    if any(sample.get("split") != "train" for sample in samples):
        raise ValueError("Nontraining label entered fit")
    x = np.asarray([sample["features"] for sample in samples], dtype=float)
    y = np.asarray([sample["residual_per_trip"] for sample in samples], dtype=float)
    if x.shape != (len(samples), len(FEATURES)) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Invalid training matrix")
    mean, scale = x.mean(axis=0), x.std(axis=0)
    mean[0], scale[0] = 0.0, 1.0
    scale[scale < 1e-8] = 1.0
    z = (x-mean)/scale
    penalty = np.eye(len(FEATURES))*RIDGE
    penalty[0, 0] = 0.0
    weights = np.linalg.solve(z.T @ z + penalty, z.T @ y)
    return ResponseModel(tuple(map(float, mean)), tuple(map(float, scale)),
                         tuple(map(float, weights)),
                         tuple(sorted({str(row["group"]) for row in samples})),
                         tuple(str(row["row_id"]) for row in samples))
