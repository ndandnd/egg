"""Exact charge-only fleet response for two common depot windows.

All morning runs draw the same battery energy, and so do all afternoon runs.
Buses start/end full, make at most one run per batch, and expend no energy or
time in transitions. A pairing must be allowed in the supplied bipartite
graph. "Usable" battery capacity excludes any reserve. No V2G, taper or
setup time is modeled. Power and assignment assumptions matter here: each bus
can accept any rate from zero to one plug's rated kW, and can pause and
migrate among identical plugs within each common window.

The whole-bus projection below uses Section 3 of the draft for homogeneous
services and adds per-bus and shared charger limits to both windows. For any
feasible individual window energies e_i, set y=sum(e_i)/h. The vector of
average powers belongs to {0<=u_i<=p, sum(u_i)=y}. Every vertex has at most
one fractional entry and therefore at most ceil(y/p) occupied plugs. Finite
time-sharing of these vertices realizes all e_i with *constant* site load y.
The site limit and number of plugs hold throughout. Monotone charging keeps
each bus within its SOC limits. This argument requires the common windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import repeat
from operator import index


def _amount(value):
    # Decimal text preserves declared kWh/fee values and price ties, including
    # externally supplied floating DLMPs at the precision actually delivered.
    return Fraction(str(value))


def _count(value):
    if isinstance(value, bool):
        raise ValueError("counts and service indices must be integers")
    try:
        return index(value)
    except TypeError as exc:
        raise ValueError("counts and service indices must be integers") from exc


@dataclass(frozen=True)
class ChargeWindow:
    hours: Fraction
    plugs: int
    plug_kw: Fraction
    site_kw: Fraction | None = None

    def __post_init__(self):
        h, plugs, kw = _amount(self.hours), _count(self.plugs), _amount(self.plug_kw)
        site = None if self.site_kw is None else _amount(self.site_kw)
        if h <= 0 or plugs < 0 or kw <= 0 or (site is not None and site < 0):
            raise ValueError("invalid window duration, plug count, power or site limit")
        for key, value in (("hours", h), ("plugs", plugs), ("plug_kw", kw), ("site_kw", site)):
            object.__setattr__(self, key, value)

    @property
    def grid_limit_kwh(self):
        kw = self.plugs * self.plug_kw
        return self.hours * (kw if self.site_kw is None else min(kw, self.site_kw))


@dataclass(frozen=True)
class CountLayer:
    pairs: int
    buses: int
    early_min_kwh: Fraction
    early_max_kwh: Fraction
    fee_eur: Fraction


@dataclass(frozen=True)
class DepotPlan:
    pairs: int
    buses: int
    fleet_kwh: tuple[Fraction, Fraction]
    fee_eur: Fraction
    posted_cost_eur: Fraction


@dataclass(frozen=True)
class TwoPeakDepot:
    n_morning: int
    n_afternoon: int
    morning_kwh: Fraction
    afternoon_kwh: Fraction
    usable_kwh: Fraction
    bus_fee_eur: Fraction
    early: ChargeWindow
    terminal: ChargeWindow
    efficiency: Fraction = Fraction(1)
    allowed_pairs: tuple[tuple[int, int], ...] | None = None  # zero-based A,B IDs
    max_buses: int | None = None

    def __post_init__(self):
        for name in ("n_morning", "n_afternoon"):
            value = _count(getattr(self, name))
            if value < 1:
                raise ValueError("both peak batches need at least one service")
            object.__setattr__(self, name, value)
        for name in ("morning_kwh", "afternoon_kwh", "usable_kwh", "bus_fee_eur", "efficiency"):
            object.__setattr__(self, name, _amount(getattr(self, name)))
        if (not 0 < self.morning_kwh <= self.usable_kwh
                or not 0 < self.afternoon_kwh <= self.usable_kwh
                or self.bus_fee_eur <= 0 or not 0 < self.efficiency <= 1):
            raise ValueError("invalid service energies, capacity, fleet fee or efficiency")
        if self.max_buses is not None:
            cap = _count(self.max_buses)
            if cap < 0:
                raise ValueError("negative fleet cap")
            object.__setattr__(self, "max_buses", cap)
        if self.allowed_pairs is not None:
            edges = tuple(sorted({(_count(i), _count(j)) for i, j in self.allowed_pairs}))
            if any(not 0 <= i < self.n_morning or not 0 <= j < self.n_afternoon for i, j in edges):
                raise ValueError("pairing references a service outside the two batches")
            object.__setattr__(self, "allowed_pairs", edges)

    @property
    def total_grid_kwh(self):
        return (self.n_morning * self.morning_kwh + self.n_afternoon * self.afternoon_kwh) / self.efficiency

    def maximum_matching(self):
        """One valid largest matching. Any prefix witnesses a smaller count."""
        size = min(self.n_morning, self.n_afternoon)
        if self.allowed_pairs is None:
            return tuple((i, i) for i in range(size))
        # Standard alternating-path augmentation. Each successful search grows
        # a matching by one. The forest starts at one unmatched morning service.
        adj = [[] for _ in range(self.n_morning)]
        for i, j in self.allowed_pairs:
            adj[i].append(j)
        a_to_b, b_to_a = {}, {}
        for start in range(self.n_morning):
            todo = [start]
            before = {}
            while todo:
                i = todo.pop()
                for j in adj[i]:
                    if j in before:
                        continue
                    before[j] = i
                    if j in b_to_a:
                        todo.append(b_to_a[j])
                        continue
                    while j is not None:
                        i = before[j]
                        old = a_to_b.get(i)
                        a_to_b[i], b_to_a[j] = j, i
                        j = old
                    todo.clear()
                    break
        return tuple(sorted(a_to_b.items()))

    def _roles(self, pairs):
        """Count, morning/afternoon battery draw, and early AC-kWh bounds by role."""
        eta = self.efficiency
        for count, a, b in ((pairs, self.morning_kwh, self.afternoon_kwh),
                            (self.n_morning - pairs, self.morning_kwh, 0),
                            (self.n_afternoon - pairs, 0, self.afternoon_kwh)):
            if count:
                lo = max(0, (a + b - self.usable_kwh) / eta,
                         (a + b) / eta - self.terminal.hours * self.terminal.plug_kw)
                hi = min(a / eta, self.early.hours * self.early.plug_kw)
                yield count, a, b, lo, hi

    def layers(self):
        """Feasible integer layers. No feasible layers means no dispatch."""
        layers = []
        for m in range(len(self.maximum_matching()) + 1):
            buses = self.n_morning + self.n_afternoon - m
            if self.max_buses is not None and buses > self.max_buses:
                continue
            roles = list(self._roles(m))
            if any(lo > hi for _, _, _, lo, hi in roles):
                continue
            low = max(sum(count * lo for count, _, _, lo, _ in roles),
                      self.total_grid_kwh - self.terminal.grid_limit_kwh)
            high = min(sum(count * hi for count, _, _, _, hi in roles),
                       self.early.grid_limit_kwh)
            if low <= high:
                layers.append(CountLayer(m, buses, low, high, self.bus_fee_eur * buses))
        return tuple(layers)

    def respond(self, prices_per_mwh, fixed_pairs=None):
        """Exact physical best response at the two supplied prices, or None.

        On a price tie choose lower early kWh, then more pairs. fixed_pairs
        gives the fixed-cover baseline for homologous buses and service draws.
        """
        early_price, late_price = map(_amount, prices_per_mwh)
        fixed = None if fixed_pairs is None else _count(fixed_pairs)
        candidates = []
        for layer in self.layers():
            if fixed is not None and layer.pairs != fixed:
                continue
            early = layer.early_min_kwh if early_price >= late_price else layer.early_max_kwh
            late = self.total_grid_kwh - early
            bill = (early_price * early + late_price * late) / 1000
            candidates.append(DepotPlan(layer.pairs, layer.buses, (early, late), layer.fee_eur,
                                        layer.fee_eur + bill))
        return min(candidates, key=lambda plan: (plan.posted_cost_eur, plan.fleet_kwh[0], -plan.pairs),
                   default=None)

    def service_witness(self, pairs, early_kwh):
        """Return (A ID or None, B ID or None, early, terminal kWh) for every bus."""
        m, e = _count(pairs), _amount(early_kwh)
        layer = next((row for row in self.layers() if row.pairs == m), None)
        if layer is None or not layer.early_min_kwh <= e <= layer.early_max_kwh:
            raise ValueError("requested dispatch lies outside the physical count layer")
        matched = self.maximum_matching()[:m]
        a_used, b_used = {i for i, _ in matched}, {j for _, j in matched}
        duties = list(matched)
        duties += [(i, None) for i in range(self.n_morning) if i not in a_used]
        duties += [(None, j) for j in range(self.n_afternoon) if j not in b_used]
        bounds = [row for count, a, b, lo, hi in self._roles(m)
                  for row in repeat((a + b, lo, hi), count)]
        extra = e - sum(lo for _, lo, _ in bounds)
        witness = []
        for (i, j), (draw, lo, hi) in zip(duties, bounds):
            add = min(extra, hi - lo)
            extra -= add
            early = lo + add
            witness.append((i, j, early, draw / self.efficiency - early))
        return tuple(witness)
