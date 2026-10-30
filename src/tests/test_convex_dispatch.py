from __future__ import annotations

import pytest

from egglab.convex_dispatch import Generator, incremental_cost, optimal_price_ranges, solve_dispatch


def generators(ramp: float = 5) -> tuple[Generator, Generator]:
    return (
        Generator("A", (7, 5, 1), (10, 15, 15), (10, ramp, ramp), 30, 0),
        Generator("B", (6, 5, 5), (10, 15, 30), 30, 30, 0),
    )


def test_ramped_dispatch_baseline_duality_and_price_face() -> None:
    units = generators()
    baseline = solve_dispatch(units, (0, 15, 0))
    assert baseline.objective == pytest.approx(75)
    mean = solve_dispatch(units, (5, 15, 25))
    assert mean.objective == pytest.approx(175)
    assert mean.output is not None
    assert mean.output[0] == pytest.approx((5, 10, 15))
    assert mean.output[1] == pytest.approx((0, 5, 10))
    assert mean.dual_objective == pytest.approx(mean.objective)
    assert mean.max_primal_residual < 1e-8
    assert mean.max_dual_violation < 1e-8
    assert mean.max_complementarity < 1e-8
    for row in ("A.up[1]", "A.up[2]", "A.capacity[2]"):
        assert mean.constraint_slack[mean.constraint_names.index(row)] == pytest.approx(0)
    ranges = optimal_price_ranges(units, (5, 15, 25))
    assert ranges[0] == pytest.approx((3, 6), abs=1e-6)
    assert ranges[1] == pytest.approx((5, 5), abs=1e-6)
    assert ranges[2] == pytest.approx((5, 5), abs=1e-6)
    assert incremental_cost(units, (0, 15, 0), (5, 0, 25)) == pytest.approx(100)


def test_no_ramp_control_and_infeasible_demand() -> None:
    control = generators(30)
    assert incremental_cost(control, (0, 15, 0), (0, 0, 30)) == pytest.approx(90)
    assert incremental_cost(control, (0, 15, 0), (10, 0, 20)) == pytest.approx(100)
    assert solve_dispatch(control, (100, 15, 20)).status == "infeasible"
    with pytest.raises(ValueError, match="dispatch infeasible"):
        incremental_cost(control, (0, 15, 0), (100, 0, 20))
