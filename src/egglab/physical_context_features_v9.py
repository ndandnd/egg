"""Input-only physical context appended to the frozen 17 movement features.

Only NativeCase and the prospective Market are accepted. Window capacity is an
isolated optimistic bound, never actual charging, fleet demand, SOC or route
feasibility. No labels, source plans, fitted transforms or solver are consulted.
"""
from __future__ import annotations

import math

import numpy as np

from egglab import learned_proposals as baseline
from egglab import native_hull as nh
from egglab import native_recharge as nr

POLICY = "physical-context-input-features-v9"
CONTEXT_FEATURES = (
    "battery_upper_kwh", "usable_span_kwh", "reserve_fraction",
    "charging_efficiency", "movement_energy_over_usable",
    "movement_and_next_trip_over_usable", "before_trip_energy_over_usable",
    "after_trip_energy_over_usable", "before_window_burst_over_usable",
    "after_window_burst_over_usable", "window_enabled_fraction",
    "window_connector_hours", "window_per_bus_kw_mean", "window_grid_kw_mean",
    "window_isolated_stored_kwh", "window_isolated_span_ratio",
    "window_other_candidate_overlap_mean", "window_curvature_mean",
    "window_curvature_min", "market_curvature_mean", "market_curvature_spread",
)
FEATURES = baseline.FEATURES + CONTEXT_FEATURES


def _overlap(lo, hi, left, right):
    return max(0., min(hi, right) - max(lo, left))


def _curvature(case, values, lo, hi):
    weighted = [(value, _overlap(lo, hi, left, right))
                for value, left, right in zip(values, case.market_edges_min,
                                               case.market_edges_min[1:])]
    active = [(value, minutes) for value, minutes in weighted if minutes > 0]
    duration = math.fsum(minutes for _, minutes in active)
    if duration <= 0:
        return 0., 0., 0.
    return (math.fsum(value * minutes for value, minutes in active) / duration,
            min(value for value, _ in active),
            max(value for value, _ in active) - min(value for value, _ in active))


def edge_features(case: nr.NativeCase, market: nh.Market) -> np.ndarray:
    """Return float64 [movement, 38], in declared movement order.

    First 17 columns exactly call the historical extractor with market.a. The
    appended ratios use the true positive usable span, without a 1-kWh clamp.
    Noncharging/zero-duration windows have zero local charging/curvature fields.
    Global curvature is time-weighted over the entire declared horizon.
    """
    if not isinstance(case, nr.NativeCase) or not isinstance(market, nh.Market):
        raise TypeError("Expected NativeCase and prospective Market only")
    nr.validate_case(case)
    nh.validate_market(case, market)
    prefix = baseline.edge_features(case, market.a)
    trips = {trip.id: trip for trip in case.trips}
    span = case.battery_kwh - case.reserve_kwh
    market_mean, _, market_spread = _curvature(
        case, market.b, 0., case.recharge_deadline_min)
    windows = [nr._window(case, movement) for movement in case.movements]
    rows = []
    for index, movement in enumerate(case.movements):
        energy = math.fsum(leg.energy_kwh for leg in movement.legs)
        before = trips[movement.before].energy_kwh if movement.before else 0.
        after = trips[movement.after].energy_kwh if movement.after else 0.
        burst_before = burst_after = 0.
        resource_fields = (0.,) * 7
        curvature_mean = curvature_min = 0.
        window = windows[index]
        if window is not None:
            # These bursts exclude charging within a verified depot visit.
            # They are local consumption context, with unknown entering SOC.
            split = movement.depot_split if movement.kind == "depot" else len(movement.legs)
            burst_before = before + math.fsum(
                leg.energy_kwh for leg in movement.legs[:split])
            burst_after = after + math.fsum(
                leg.energy_kwh for leg in movement.legs[split:])
            lo, hi = window
            duration = hi - lo
            if duration > 0:
                overlaps = [(resource, _overlap(lo, hi, resource.start_min,
                                               resource.end_min))
                            for resource in case.resources]
                enabled = math.fsum(minutes for resource, minutes in overlaps
                                    if resource.connectors and resource.per_bus_kw > 0
                                    and resource.grid_kw > 0) / duration
                connector_hours = math.fsum(resource.connectors * minutes
                                           for resource, minutes in overlaps) / 60.
                per_bus = math.fsum(resource.per_bus_kw * minutes
                                   for resource, minutes in overlaps) / duration
                grid = math.fsum(resource.grid_kw * minutes
                                for resource, minutes in overlaps) / duration
                stored = case.efficiency * math.fsum(
                    min(resource.per_bus_kw, resource.grid_kw) * minutes
                    for resource, minutes in overlaps if resource.connectors) / 60.
                # Counts declared alternatives, including mutually exclusive
                # modes. This is a structural overlap proxy, not fleet demand.
                other_candidates = math.fsum(
                    _overlap(lo, hi, other[0], other[1])
                    for other_index, other in enumerate(windows)
                    if other_index != index and other is not None) / duration
                resource_fields = (enabled, connector_hours, per_bus, grid,
                                   stored, stored / span, other_candidates)
                curvature_mean, curvature_min, _ = _curvature(case, market.b, lo, hi)
        rows.append((case.battery_kwh, span, case.reserve_kwh / case.battery_kwh,
                     case.efficiency, energy / span, (energy + after) / span,
                     before / span, after / span, burst_before / span,
                     burst_after / span, *resource_fields, curvature_mean,
                     curvature_min, market_mean, market_spread))
    context = np.asarray(rows, dtype=np.float64)
    if context.shape != (len(case.movements), len(CONTEXT_FEATURES)) or not np.isfinite(context).all():
        raise ValueError("Unrepresentable physical context feature values")
    result = np.concatenate((prefix, context), axis=1)
    if result.shape[1] != len(FEATURES) or not np.isfinite(result).all():
        raise ValueError("Invalid physical context features")
    return result
