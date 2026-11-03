"""Independent enumeration on integer-kWh fixtures and an exact source-calibration check."""
from fractions import Fraction
from itertools import combinations, permutations, product
import json

from egglab.matched_fleets import FleetProjection, read_matched_fleet
from egglab.two_peak import ChargeWindow


def enumerate_dispatches(a, b, cap, early, terminal, eligible):
    """Simulate every small cover and integer-kWh per-bus dispatch at efficiency one."""
    attainable = {}
    for k in range(min(len(a), len(b)) + 1):
        for a_ids in combinations(range(len(a)), k):
            for b_ids in permutations(range(len(b)), k):
                pairs = tuple(zip(a_ids, b_ids))
                if not set(pairs) <= eligible:
                    continue
                duties = [(a[i], b[j]) for i, j in pairs]
                duties += [(draw, 0) for i, draw in enumerate(a) if i not in a_ids]
                duties += [(0, draw) for j, draw in enumerate(b) if j not in b_ids]
                by_bus = []
                for first, second in duties:
                    options = []
                    for x in range(early.plug_kw.numerator + 1):
                        after_am = cap - first
                        before_pm = after_am + x
                        after_pm = before_pm - second
                        y = cap - after_pm
                        if after_am >= 0 and before_pm <= cap and after_pm >= 0 and 0 <= y <= terminal.plug_kw:
                            options.append((x, y))
                    by_bus.append(options)
                for charges in product(*by_bus):
                    x = sum(c[0] for c in charges)
                    y = sum(c[1] for c in charges)
                    if x <= early.grid_limit_kwh and y <= terminal.grid_limit_kwh:
                        attainable.setdefault(k, set()).add(x)
    return attainable


def test_exact_matching_matches_all_covers_and_source_soc():
    a, b = (1, 3, 4), (1, 2, 3)
    early, late = ChargeWindow(1, 2, 3), ChargeWindow(1, 3, 3)
    all_edges = set(product(range(3), repeat=2))
    for allowed in (all_edges, all_edges - {(0, 2), (2, 0)}, {(0, 1), (1, 2)}):
        f = FleetProjection(a, b, early, late, 50, 5, 1, tuple(allowed))
        truth = enumerate_dispatches(a, b, 5, early, late, allowed)
        layers = {r.pairs: r for r in f.layers()}
        assert set(layers) == set(truth)
        for k, r in layers.items():
            assert (r.early_min_kwh, r.early_max_kwh) == (min(truth[k]), max(truth[k]))
            assert set(range(min(truth[k]), max(truth[k]) + 1)) == truth[k]
            for x in (r.early_min_kwh, (r.early_min_kwh + r.early_max_kwh) / 2, r.early_max_kwh):
                duties = f.service_witness(k, x)
                assert sorted(i for i, _, _, _ in duties if i is not None) == [0, 1, 2]
                assert sorted(j for _, j, _, _ in duties if j is not None) == [0, 1, 2]
                assert sum(t[2] for t in duties) == x
                for i, j, u, v in duties:
                    first, second = (0 if i is None else a[i]), (0 if j is None else b[j])
                    assert (i is None or j is None or (i, j) in allowed)
                    assert 0 <= 5 - first + u <= 5 and 0 <= 5 - first + u - second
                    assert 5 - first + u - second + v == 5
                    assert 0 <= u <= 3 and 0 <= v <= 3


def test_unchargeable_afternoon_and_fixed_unchargeable_tie_retained():
    w = ChargeWindow(1, 3, 3)
    blocked = FleetProjection((2,), (3,), w, w, 1, 4, Fraction(19, 20))
    assert blocked.structural_failures == (("B", 0),)
    assert blocked.layers() == () and blocked.fixed_cover_layer() is None
    # A high-energy morning and afternoon cannot share a bus here. Across the
    # two permutations of B labels the precommitted tie selects exactly one
    # such incompatible edge. Minimum-flex matching can still pair both.
    fixed = []
    for b in ((1, 3), (3, 1)):
        f = FleetProjection((1, 5), b, ChargeWindow(1, 2, 3), w, 1, 5, 1)
        assert f.strong_cover_layer().pairs == 2
        fixed.append(f.fixed_cover_layer() is not None)
    assert sorted(fixed) == [False, True]


def test_different_matching_floors_and_equal_total_control(tmp_path):
    w = ChargeWindow(1, 3, 5)
    f = FleetProjection((1, 4), (1, 4), w, w, 50, 5, 1)
    extremes = f.diagnostics()["by_count"][-1]
    assert extremes["min_floor_grid_kwh"] == 0 and extremes["max_floor_grid_kwh"] == 3
    path = tmp_path / "peak_runs.json"
    path.write_text(json.dumps({"meta": {"source": "artificial test"}, "operators": [
        {"depots": 2}, {"depots": 1, "operator": "001__Stadtverkehr_Euskirchen", "day_type": 1,
                        "n_am_trips": 4, "n_pm_trips": 3, "a_kwh": [1.1, 2.2, 3.3, 4.4],
                        "b_kwh": [1, 2, 3]}]}))
    f, info = read_matched_fleet(path, 5, w, w, 50)
    mean, meta = read_matched_fleet(path, 5, w, w, 50, homogeneous=True)
    assert info["batches"]["a_kwh"]["selected_zero_based_ranks"] == (0, 1, 2, 2, 3)
    assert info["operator_index"] == 1 and info["peak_runs_sha256"] == meta["peak_runs_sha256"]
    assert sum(f.morning_kwh) == sum(mean.morning_kwh)
    assert sum(f.afternoon_kwh) == sum(mean.afternoon_kwh)
    assert f.total_grid_kwh == mean.total_grid_kwh and len(set(mean.morning_kwh)) == 1
