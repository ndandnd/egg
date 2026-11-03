"""Exact charge-only projection for heterogeneous services in two common windows.

For one bus doing A then B (zero denotes no service), early grid energy x
lies in [max(0,(A+B-C)/eta,(A+B)/eta-terminal_plug_kWh),
min(A/eta,early_plug_kWh)]. In particular the upper limit depends only on A.
The interval is empty if either service exceeds capacity or the lower end
exceeds the upper. If a singleton cannot recharge, pairing cannot save it:
removing either service from a feasible pair permits a feasible singleton.

All matchings of size k have the same upper limit on total early energy.
Thus the union of their intervals is itself an interval, witnessed in full
by the matching with smallest lower limit. Matching edge cost is the extra
lower limit relative to keeping its two singleton buses. A minimum-cost
cardinality-k matching therefore suffices. The shared terminal and early
capacities then clip this interval. Service-level intermediate energies
are attainable by monotone filling. Constant aggregate power with shared
identical plugs follows by time-sharing as in two_peak.py.

This is a constructed common-window comparison, not a schedule for the
original operator. Signed charging and within-window price response are
outside the projection.
"""
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from functools import cached_property, lru_cache
import hashlib
import json
from math import lcm
from pathlib import Path

import networkx as nx

from .two_peak import ChargeWindow, CountLayer, _amount, _count


@dataclass(frozen=True)
class FleetProjection:
    morning_kwh: tuple
    afternoon_kwh: tuple
    early: ChargeWindow
    terminal: ChargeWindow
    bus_fee_eur: Fraction
    usable_kwh: Fraction = Fraction(320)
    efficiency: Fraction = Fraction(95, 100)
    allowed_pairs: tuple | None = None

    def __post_init__(self):
        for name in ("morning_kwh", "afternoon_kwh"):
            values = tuple(map(_amount, getattr(self, name)))
            if not values or min(values) <= 0:
                raise ValueError("both batches need positive service draws")
            object.__setattr__(self, name, values)
        for name in ("bus_fee_eur", "usable_kwh", "efficiency"):
            object.__setattr__(self, name, _amount(getattr(self, name)))
        if self.bus_fee_eur <= 0 or self.usable_kwh <= 0 or not 0 < self.efficiency <= 1:
            raise ValueError("invalid fleet fee, battery or efficiency")
        if self.allowed_pairs is not None:
            edges = tuple(sorted({(_count(i), _count(j)) for i, j in self.allowed_pairs}))
            if any(not (0 <= i < len(self.morning_kwh) and 0 <= j < len(self.afternoon_kwh))
                   for i, j in edges):
                raise ValueError("pair outside service batches")
            object.__setattr__(self, "allowed_pairs", edges)

    @cached_property
    def total_grid_kwh(self):
        return (sum(self.morning_kwh) + sum(self.afternoon_kwh)) / self.efficiency

    def _bus_bounds(self, a, b):
        total = (a + b) / self.efficiency
        low = max(Fraction(0), (a + b - self.usable_kwh) / self.efficiency,
                  total - self.terminal.hours * self.terminal.plug_kw)
        high = min(a / self.efficiency, self.early.hours * self.early.plug_kw)
        return low, high

    @cached_property
    def _singletons(self):
        return tuple(self._bus_bounds(a, 0) for a in self.morning_kwh), tuple(
            self._bus_bounds(0, b) for b in self.afternoon_kwh)

    @cached_property
    def structural_failures(self):
        out = []
        for batch, draws, bounds in zip(("A", "B"), (self.morning_kwh, self.afternoon_kwh),
                                        self._singletons):
            for i, (draw, (lo, hi)) in enumerate(zip(draws, bounds)):
                if draw > self.usable_kwh or lo > hi:
                    out.append((batch, i))
        return tuple(out)

    @cached_property
    def _edges(self):
        if self.allowed_pairs is not None:
            return self.allowed_pairs
        return tuple((i, j) for i in range(len(self.morning_kwh))
                     for j in range(len(self.afternoon_kwh)))

    @cached_property
    def _edge_costs(self):
        singles_a, singles_b = self._singletons
        costs = {}
        for i, j in self._edges:
            lo, hi = self._bus_bounds(self.morning_kwh[i], self.afternoon_kwh[j])
            if lo <= hi:
                costs[i, j] = lo - singles_a[i][0] - singles_b[j][0]
        return costs

    def _optimum_matchings(self, direction):
        """Network simplex sees integer demands, capacities and exact common-scale weights."""
        if self.structural_failures:
            return {}
        costs = self._edge_costs
        if not costs:
            return {0: ()}
        if self.allowed_pairs is None and len(costs) == len(self._edges) and len(set(costs.values())) == 1:
            size = min(len(self.morning_kwh), len(self.afternoon_kwh))
            return {k: tuple((i, i) for i in range(k)) for k in range(size + 1)}
        denom = lcm(*(c.denominator for c in costs.values()))
        graph = nx.DiGraph()
        a_size, b_size = len(self.morning_kwh), len(self.afternoon_kwh)
        source, sink = a_size + b_size, a_size + b_size + 1
        graph.add_nodes_from(range(sink + 1), demand=0)
        graph.add_edges_from(((source, i) for i in range(a_size)), capacity=1, weight=0)
        graph.add_edges_from(((a_size + j, sink) for j in range(b_size)), capacity=1, weight=0)
        for (i, j), c in costs.items():
            graph.add_edge(i, a_size + j, capacity=1, weight=direction * int(c * denom))
        result = {0: ()}
        for k in range(1, min(a_size, b_size) + 1):
            graph.nodes[source]["demand"], graph.nodes[sink]["demand"] = -k, k
            try:
                _, flow = nx.network_simplex(graph)
            except nx.NetworkXUnfeasible:
                break  # any larger cardinality would contain a matching of size k
            result[k] = tuple((i, j) for i, j in costs if flow[i][a_size + j])
        return result

    @cached_property
    def _best(self):
        return self._optimum_matchings(1)

    @cached_property
    def _worst(self):
        return self._optimum_matchings(-1)

    @cached_property
    def _fleet_limits(self):
        return self.total_grid_kwh - self.terminal.grid_limit_kwh, self.early.grid_limit_kwh

    def _bounds(self, matching):
        early_los, early_his = zip(*self._singletons[0])
        low = sum(early_los) + sum(self._edge_costs[pair] for pair in matching)
        late_floor, site_ceiling = self._fleet_limits
        return max(low, late_floor), min(sum(early_his), site_ceiling)

    def _layer(self, matching):
        if self.structural_failures or any(edge not in self._edge_costs for edge in matching):
            return None
        lo, hi = self._bounds(matching)
        k = len(matching)
        buses = len(self.morning_kwh) + len(self.afternoon_kwh) - k
        return CountLayer(k, buses, lo, hi, buses * self.bus_fee_eur) if lo <= hi else None

    @cached_property
    def _layers(self):
        candidates = (self._layer(m) for m in self._best.values())
        return tuple(row for row in candidates if row is not None)

    def layers(self):
        return self._layers

    def strong_cover_layer(self):
        """Choose fewest physically feasible buses, then most flexible interval at that count."""
        return self._layers[-1] if self._layers else None

    @cached_property
    def _fixed_matching(self):
        """Unweighted cover at the chosen count using two distinct deterministic ID orders."""
        layer = self.strong_cover_layer()
        if layer is None:
            return None
        if layer.pairs == 0:
            return ()
        def order(batch, n):
            return sorted(range(n), key=lambda i: hashlib.sha256(
                f"egg-matched-cover-v1/{batch}/{i}".encode()).digest())
        a_ids = order("A", len(self.morning_kwh))
        b_ids = order("B", len(self.afternoon_kwh))
        if self.allowed_pairs is None:
            return tuple(sorted(zip(a_ids[:layer.pairs], b_ids[:layer.pairs])))
        positions = {j: r for r, j in enumerate(b_ids)}
        adjacency = {i: [] for i in a_ids}
        for i, j in self._edges:
            adjacency[i].append(j)
        for row in adjacency.values():
            row.sort(key=positions.__getitem__)
        # Unweighted alternating paths, without using energy or pricing to choose edges.
        matched_a, matched_b = {}, {}
        for start in a_ids:
            queue, previous = [start], {}
            for i in queue:
                for j in adjacency[i]:
                    if j in previous:
                        continue
                    previous[j] = i
                    if j in matched_b:
                        queue.append(matched_b[j])
                        continue
                    while j is not None:
                        i = previous[j]
                        old = matched_a.get(i)
                        matched_a[i], matched_b[j] = j, i
                        j = old
                    break
                else:
                    continue
                break
            if len(matched_a) == layer.pairs:
                return tuple(sorted(matched_a.items()))
        raise RuntimeError("unweighted graph cannot realize physically feasible count")

    def fixed_cover_layer(self):
        """Missing means this committed unweighted tie cannot charge; no rematching."""
        return None if self._fixed_matching is None else self._layer(self._fixed_matching)

    def service_witness(self, pairs, early_kwh, *, cover="joint"):
        k, e = _count(pairs), _amount(early_kwh)
        if cover not in ("joint", "strong", "fixed"):
            raise ValueError("unknown cover")
        if cover == "joint":
            matching = self._best.get(k)
        elif cover == "strong":
            layer = self.strong_cover_layer()
            matching = None if layer is None or layer.pairs != k else self._best[k]
        else:
            matching = self._fixed_matching
        layer = None if matching is None else self._layer(matching)
        if layer is None or layer.pairs != k or not layer.early_min_kwh <= e <= layer.early_max_kwh:
            raise ValueError("requested physical dispatch outside selected cover")
        a_used, b_used = {i for i, _ in matching}, {j for _, j in matching}
        duties = list(matching)
        duties += [(i, None) for i in range(len(self.morning_kwh)) if i not in a_used]
        duties += [(None, j) for j in range(len(self.afternoon_kwh)) if j not in b_used]
        allocations = []
        for i, j in duties:
            a = 0 if i is None else self.morning_kwh[i]
            b = 0 if j is None else self.afternoon_kwh[j]
            lo, hi = self._bus_bounds(a, b)
            allocations.append((lo, hi, (a + b) / self.efficiency))
        remaining = e - sum(lo for lo, _, _ in allocations)
        result = []
        for (i, j), (lo, hi, total) in zip(duties, allocations):
            extra = min(remaining, hi - lo)
            remaining -= extra
            result.append((i, j, lo + extra, total - lo - extra))
        if remaining:
            raise ArithmeticError("witness failed to allocate all early energy")
        return tuple(result)

    def diagnostics(self):
        """Worst floor is over individually viable edges; report shared cap failure separately."""
        rows = []
        for k, best in self._best.items():
            lo, hi = self._bounds(best)
            worst_lo, _ = self._bounds(self._worst[k])
            rows.append(dict(pairs=k, min_floor_grid_kwh=float(lo),
                             max_floor_grid_kwh=float(worst_lo), common_ceiling_grid_kwh=float(hi),
                             best_chargeable=lo <= hi, worst_chargeable=worst_lo <= hi))
        return dict(impossible_singleton_ids=list(self.structural_failures), by_count=rows,
                    fixed_pairs=self._fixed_matching, fixed_cover_chargeable=self.fixed_cover_layer() is not None)


@lru_cache(maxsize=2)
def _read_source(path):
    data = Path(path).read_bytes()
    source = json.loads(data, parse_float=Decimal)
    index, operator = next((i, op) for i, op in enumerate(source["operators"]) if op.get("depots") == 1)
    if operator["operator"] != "001__Stadtverkehr_Euskirchen":
        raise ValueError("first archived single-depot operator differs from registered Euskirchen")
    return source["meta"]["source"], hashlib.sha256(data).hexdigest(), index, operator


def read_matched_fleet(peak_runs, n, early, terminal, bus_fee_eur, homogeneous=False):
    """Select midpoint empirical quantiles of each original ordered batch, with repeats if n grows."""
    n = _count(n)
    if n < 1:
        raise ValueError("each scaled batch needs positive size")
    source, digest, operator_index, op = _read_source(str(Path(peak_runs).resolve()))
    samples, batch_meta = [], {}
    for label in ("a_kwh", "b_kwh"):
        source_energies = tuple(map(_amount, op[label]))
        if tuple(sorted(source_energies)) != source_energies:
            raise ValueError("archive must contain the original ascending energy order")
        ranks = tuple((2 * i + 1) * len(source_energies) // (2 * n) for i in range(n))
        draws = tuple(source_energies[r] for r in ranks)
        mean = sum(draws) / n
        samples.append((mean,) * n if homogeneous else draws)
        batch_meta[label] = dict(source_count=len(source_energies), selected_zero_based_ranks=ranks,
                                 distinct_source_ranks=len(set(ranks)), selected_mean_kwh=float(mean))
    fleet = FleetProjection(*samples, early, terminal, bus_fee_eur)
    provenance = dict(source=source, peak_runs_sha256=digest, operator=op["operator"],
                      operator_index=operator_index, selected_day_type=op["day_type"],
                      original_service_trips=(op["n_am_trips"], op["n_pm_trips"]),
                      mode="batch_mean_homogeneous" if homogeneous else "empirical_heterogeneous",
                      batches=batch_meta, allowed_pairs="all synthetic common-window cross-batch pairs",
                      cover_tie="SHA256 of egg-matched-cover-v1/{A|B}/{zero-based sampled ordinal}")
    return fleet, provenance
