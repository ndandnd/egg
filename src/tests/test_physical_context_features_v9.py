"""Pure input fixtures: no bank, labels, optimizer, training or reserved data."""
from dataclasses import replace
import inspect

import numpy as np
import pytest

from egglab import learned_proposals as baseline
from egglab import native_hull as nh
from egglab import native_recharge as nr
from egglab import physical_context_features_v9 as features


def tiny_case():
    trips = (nr.Trip("a", 20, 30, "P", "Q", 12.),
             nr.Trip("b", 80, 90, "P", "Q", 8.))
    movements = (
        nr.Movement("out_a", "pullout", None, "a", (nr.Leg("D", "P", 0, 10, 2.),)),
        nr.Movement("out_b", "pullout", None, "b", (nr.Leg("D", "P", 60, 70, 2.),)),
        nr.Movement("direct", "direct", "a", "b", (nr.Leg("Q", "P", 30, 80, 3.),)),
        nr.Movement("depot", "depot", "a", "b",
                    (nr.Leg("Q", "D", 30, 40, 4.), nr.Leg("D", "P", 70, 80, 5.)), 1),
        nr.Movement("in_a", "pullin", "a", None, (nr.Leg("Q", "D", 30, 40, 4.),)),
        nr.Movement("in_b", "pullin", "b", None, (nr.Leg("Q", "D", 90, 100, 4.),)),
    )
    return nr.NativeCase("tiny-input-only", trips, movements,
                         (nr.Resource(0, 50, 60., 30., 1),
                          nr.Resource(50, 60, 60., 30., 0),
                          nr.Resource(60, 120, 60., 120., 1)),
                         (0, 50, 90, 120), "D", 2, 100., 20., 100, 120, 10.,
                         efficiency=.8)


def tiny_market():
    return nh.Market("known-prospective-input", (.1, -.2, .4), (.01, .02, .03))


def column(name):
    return features.FEATURES.index(name)


def test_prefix_is_exact_and_schema_has_no_hidden_inputs():
    case, market = tiny_case(), tiny_market()
    x = features.edge_features(case, market)
    assert x.shape == (6, 38) and x.dtype == np.float64
    assert len(set(features.FEATURES)) == len(features.FEATURES)
    assert features.FEATURES[:17] == baseline.FEATURES
    assert np.array_equal(x[:, :17], baseline.edge_features(case, market.a))
    assert tuple(inspect.signature(features.edge_features).parameters) == ("case", "market")
    with pytest.raises(TypeError, match="NativeCase"):
        features.edge_features({"case": case, "label": "poison", "split": "poison"}, market)


def test_source_labels_and_identifiers_cannot_change_same_input_features():
    case, market = tiny_case(), tiny_market()
    # Different labels/plans are deliberately never passed to the API.
    sources = [{"case": case, "market": market, "label": label}
               for label in ({"plan": "poison-one"}, {"selected_edges": "poison-two"})]
    left, right = [features.edge_features(row["case"], row["market"]) for row in sources]
    assert np.array_equal(left, right)
    id_map = {trip.id: "renamed-" + trip.id for trip in case.trips}
    renamed = replace(case, name="arbitrary-other-name",
        trips=tuple(replace(trip, id=id_map[trip.id]) for trip in case.trips),
        movements=tuple(replace(movement, id="renamed-" + movement.id,
                               before=id_map.get(movement.before),
                               after=id_map.get(movement.after)) for movement in case.movements))
    assert np.array_equal(left, features.edge_features(renamed, replace(market, name="source2")))
    reordered = replace(case, movements=tuple(reversed(case.movements)))
    assert np.array_equal(left[::-1], features.edge_features(reordered, market))


def test_isolated_capacity_uses_grid_bus_connector_efficiency_and_minutes():
    x = features.edge_features(tiny_case(), tiny_market())
    row = x[3]  # depot window [40,70]: 10 min*30 + 10 min*0 + 10 min*60 kW
    assert row[column("window_isolated_stored_kwh")] == pytest.approx(12.)
    assert row[column("window_isolated_span_ratio")] == pytest.approx(.15)
    assert row[column("window_enabled_fraction")] == pytest.approx(2/3)
    assert row[column("window_connector_hours")] == pytest.approx(1/3)
    assert row[column("window_per_bus_kw_mean")] == 60.
    assert row[column("window_grid_kw_mean")] == 60.
    assert row[column("before_window_burst_over_usable")] == pytest.approx((12+4)/80)
    assert row[column("after_window_burst_over_usable")] == pytest.approx((5+8)/80)
    assert row[column("movement_and_next_trip_over_usable")] == pytest.approx((4+5+8)/80)
    assert x[0, column("before_window_burst_over_usable")] == 0.
    assert x[2, column("movement_and_next_trip_over_usable")] == pytest.approx((3+8)/80)
    assert x[4, column("before_window_burst_over_usable")] == pytest.approx((12+4)/80)


def test_zero_power_or_connectors_give_zero_capacity_not_fake_energy():
    case, market = tiny_case(), tiny_market()
    for field, value in (("connectors", 0), ("grid_kw", 0.), ("per_bus_kw", 0.)):
        changed = replace(case, resources=tuple(replace(resource, **{field: value})
                                               for resource in case.resources))
        x = features.edge_features(changed, market)
        assert np.all(x[:, column("window_isolated_stored_kwh")] == 0.)
        assert np.all(x[:, column("window_enabled_fraction")] == 0.)
        if field == "connectors":
            assert np.all(x[:, column("window_connector_hours")] == 0.)
        else:
            assert x[3, column("window_connector_hours")] > 0.  # availability != power


def test_no_window_and_zero_length_window_have_zero_local_summaries():
    case = tiny_case()
    movement = case.movements[3]
    changed = replace(movement, legs=(movement.legs[0], replace(movement.legs[1], depart_min=40)))
    case = replace(case, terminal_open_min=120,
                   movements=case.movements[:3] + (changed,) + case.movements[4:])
    x = features.edge_features(case, tiny_market())
    local_names = features.CONTEXT_FEATURES[10:19]  # resources plus window curvature
    assert np.all(x[:, [column(name) for name in local_names]] == 0.)
    # Consumption bursts survive a zero-duration window; they are not SOC.
    assert x[3, column("before_window_burst_over_usable")] > 0.


def test_curvature_is_known_time_weighted_input_and_does_not_touch_prefix():
    case, market = tiny_case(), tiny_market()
    x = features.edge_features(case, market)
    assert x[3, column("window_curvature_mean")] == pytest.approx((.01*10 + .02*20)/30)
    assert x[3, column("window_curvature_min")] == .01
    assert np.all(x[:, column("market_curvature_mean")] == pytest.approx((.01*50+.02*40+.03*30)/120))
    assert np.all(x[:, column("market_curvature_spread")] == pytest.approx(.02))
    changed = features.edge_features(case, replace(market, b=(0., 0., 0.)))
    assert np.array_equal(x[:, :17], changed[:, :17])
    assert np.all(changed[:, [column(name) for name in features.CONTEXT_FEATURES[-4:]]] == 0.)
    # Known a can differ between source/target markets; physical context cannot.
    changed_a = features.edge_features(case, replace(market, a=(1., 2., 3.)))
    assert not np.array_equal(x[:, :17], changed_a[:, :17])
    assert np.array_equal(x[:, 17:], changed_a[:, 17:])


def test_candidate_overlap_counts_declared_mutually_exclusive_alternatives():
    case, market = tiny_case(), tiny_market()
    x = features.edge_features(case, market)
    assert x[3, column("window_other_candidate_overlap_mean")] == 0.
    assert x[4, column("window_other_candidate_overlap_mean")] == 1.
    assert x[5, column("window_other_candidate_overlap_mean")] == 1.
    duplicate_alternative = replace(case.movements[3], id="other-depot-alternative")
    changed = features.edge_features(replace(case, movements=case.movements + (duplicate_alternative,)), market)
    assert changed[3, column("window_other_candidate_overlap_mean")] == 1.
    assert changed[-1, column("window_other_candidate_overlap_mean")] == 1.
    assert np.array_equal(changed[:6, :17], x[:, :17])
    assert changed[3, column("window_isolated_stored_kwh")] == x[3, column("window_isolated_stored_kwh")]


def test_small_energy_scale_preserves_true_span_ratios_and_exact_prefix_clamp():
    case, market = tiny_case(), tiny_market()
    scale = .001
    small = replace(case, battery_kwh=case.battery_kwh*scale, reserve_kwh=case.reserve_kwh*scale,
        trips=tuple(replace(trip, energy_kwh=trip.energy_kwh*scale) for trip in case.trips),
        movements=tuple(replace(movement, legs=tuple(replace(leg, energy_kwh=leg.energy_kwh*scale)
                                                    for leg in movement.legs)) for movement in case.movements),
        resources=tuple(replace(resource, per_bus_kw=resource.per_bus_kw*scale,
                                grid_kw=resource.grid_kw*scale) for resource in case.resources))
    original, changed = features.edge_features(case, market), features.edge_features(small, market)
    assert np.array_equal(changed[:, :17], baseline.edge_features(small, market.a))
    dimensionless = ("reserve_fraction", "charging_efficiency", *features.CONTEXT_FEATURES[4:11],
                     "window_isolated_span_ratio", "window_other_candidate_overlap_mean")
    for name in dimensionless:
        assert changed[:, column(name)] == pytest.approx(original[:, column(name)])
    assert changed[3, column("window_isolated_stored_kwh")] == pytest.approx(.012)
    assert changed[3, column("usable_span_kwh")] == pytest.approx(.08)


def test_capacity_and_stress_are_unclipped_bounds_not_a_route_feasibility_label():
    case, market = tiny_case(), tiny_market()
    movement = case.movements[3]
    changed = replace(case, movements=case.movements[:3] +
        (replace(movement, legs=(replace(movement.legs[0], energy_kwh=100.), movement.legs[1])),) +
        case.movements[4:], resources=(nr.Resource(0, 120, 6000., 6000., 1),))
    row = features.edge_features(changed, market)[3]
    assert row[column("before_window_burst_over_usable")] > 1.
    assert row[column("window_isolated_span_ratio")] > 1.
    assert row[column("window_isolated_stored_kwh")] > row[column("usable_span_kwh")]


@pytest.mark.parametrize("field,value", [("reserve_kwh", 100.), ("battery_kwh", 0.),
                                           ("efficiency", 0.), ("efficiency", 1.01)])
def test_invalid_physics_is_rejected(field, value):
    with pytest.raises(ValueError, match="physics"):
        features.edge_features(replace(tiny_case(), **{field: value}), tiny_market())


def test_invalid_market_and_resource_inputs_are_rejected():
    case, market = tiny_case(), tiny_market()
    for b in ((.01,), (.01, float("nan"), .02), (.01, -.01, .02)):
        with pytest.raises(ValueError):
            features.edge_features(case, replace(market, b=b))
    with pytest.raises(ValueError):
        features.edge_features(case, replace(market, a=(.1, float("inf"), .2)))
    with pytest.raises(ValueError, match="Resources"):
        features.edge_features(replace(case, resources=(nr.Resource(0, 120, 90., 90., 2),)), market)
    with pytest.raises(ValueError, match="Resources"):
        features.edge_features(replace(case, resources=(nr.Resource(1, 120, 90., 90., 1),)), market)
