"""EVSP instance model and synthetic generator.

Conventions (documented in src/README.md):
- Times are minutes from the start of the service day; values may exceed 24h.
- Energy in kWh; charging power in kW; prices in currency per kWh.
- Vehicles start the day full (soc0 = battery_kwh by default) and must end the
  day (after pull-in) with SOC >= soc_end_kwh. Terminal-energy policy is an
  explicit modeling knob (see ref/context handoffs).
- Deadhead matrix is directed and must contain every needed pair; same-location
  movement is free.
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field, asdict


@dataclass(frozen=True)
class Trip:
    id: str
    start_min: int
    end_min: int
    start_loc: str
    end_loc: str
    energy_kwh: float


@dataclass
class Instance:
    name: str
    trips: list  # list[Trip], sorted by start_min
    depot: str
    dh_min: dict  # {(a,b): minutes}
    dh_kwh: dict  # {(a,b): kWh}
    battery_kwh: float
    soc0_kwh: float
    soc_min_kwh: float
    soc_end_kwh: float
    charge_power_kw: float
    n_slots: int = 28
    slot_min: int = 60
    max_vehicles: int = 8
    vehicle_fixed_cost: float = 1000.0
    dh_cost_per_min: float = 1.0
    meta: dict = field(default_factory=dict)

    # --- deadhead lookups -------------------------------------------------
    def dhm(self, a: str, b: str) -> int:
        return 0 if a == b else self.dh_min[(a, b)]

    def dhk(self, a: str, b: str) -> float:
        return 0.0 if a == b else self.dh_kwh[(a, b)]

    # --- identity ----------------------------------------------------------
    def canonical(self) -> dict:
        d = asdict(self)
        d["trips"] = [asdict(t) for t in self.trips]
        d["dh_min"] = sorted((a, b, v) for (a, b), v in self.dh_min.items())
        d["dh_kwh"] = sorted((a, b, v) for (a, b), v in self.dh_kwh.items())
        return d

    def hash(self) -> str:
        s = json.dumps(self.canonical(), sort_keys=True)
        return hashlib.sha256(s.encode()).hexdigest()[:12]

    @property
    def horizon_min(self) -> int:
        return self.n_slots * self.slot_min


def synthetic_instance(
    seed: int = 0,
    n_trips: int = 10,
    battery_kwh: float = 60.0,
    soc_min_frac: float = 0.10,
    soc_end_frac: float = 0.10,
    charge_power_kw: float = 150.0,
    trip_energy_range=(14.0, 22.0),
    day_start_min: int = 300,
    day_end_min: int = 1320,
    max_vehicles: int | None = None,
    name: str | None = None,
) -> Instance:
    """Small two-terminal + depot instance whose charging is materially
    price-responsive: per-vehicle service energy exceeds the usable battery, so
    midday depot charging is required, and the timing of that charging is the
    price-responsive decision."""
    rng = random.Random(seed)
    depot, A, B = "D", "A", "B"
    dh_min, dh_kwh = {}, {}

    def link(a, b, m, k):
        dh_min[(a, b)] = m
        dh_kwh[(a, b)] = k
        dh_min[(b, a)] = m
        dh_kwh[(b, a)] = k

    link(depot, A, 10, 2.0)
    link(depot, B, 12, 2.4)
    link(A, B, 8, 1.6)

    trips = []
    starts = sorted(
        rng.randrange(day_start_min, day_end_min - 70, 5) for _ in range(n_trips)
    )
    for i, st in enumerate(starts):
        dur = rng.randrange(40, 65, 5)
        if rng.random() < 0.5:
            s_loc, e_loc = A, B
        else:
            s_loc, e_loc = B, A
        if rng.random() < 0.25:  # some round trips
            e_loc = s_loc
        energy = round(rng.uniform(*trip_energy_range), 1)
        trips.append(Trip(f"t{i:03d}", st, st + dur, s_loc, e_loc, energy))

    if max_vehicles is None:
        max_vehicles = max(2, n_trips // 2)
    return Instance(
        name=name or f"syn-s{seed}-n{n_trips}",
        trips=trips,
        depot=depot,
        dh_min=dh_min,
        dh_kwh=dh_kwh,
        battery_kwh=battery_kwh,
        soc0_kwh=battery_kwh,
        soc_min_kwh=soc_min_frac * battery_kwh,
        soc_end_kwh=soc_end_frac * battery_kwh,
        charge_power_kw=charge_power_kw,
        max_vehicles=max_vehicles,
        meta={"generator": "synthetic_instance", "seed": seed},
    )


def load_frozen_subset(
    path: str,
    manifest_path: str | None = None,
    *,
    expected_manifest_sha256: str | None = None,
) -> Instance:
    """Load a GIRO-derived subset only after manifest verification.

    ``path`` may name the frozen artifact directory, its ``INSTANCE.json``,
    or its ``MANIFEST.json``.  A separately supplied manifest must still be
    the paired sibling of the instance.  Pin ``expected_manifest_sha256`` when
    the caller needs an explicit trust root in addition to a tracked manifest.

    The freeze contract (variant choice, trip lineage, deadhead fidelity,
    physics, and source hashes) is implemented by
    ``experiments/freeze_giro_subset.py``.
    """
    from .frozen import load_verified_frozen_subset

    return load_verified_frozen_subset(
        path,
        manifest_path,
        expected_manifest_sha256=expected_manifest_sha256,
    )
