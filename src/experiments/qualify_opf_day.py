"""Check duration, export, nodal prices and the physical screen under negative import prices."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from egglab.radial_opf import price_depot_day, solve_radial


def main():
    # Same ideal connector, different settlement periods. First slot buys
    # 1 MW for half an hour, second exports 0.25 MW for one hour.
    day = price_depot_day([0], [0.], [0.], [[0., 0.], [0., 0.]], [[0., 0.], [0., 0.]],
                          1, [500., -250.], [.5, 1.], [40., 60.], curvature=12.)
    expected_price = [52., 57.]
    # Half-hour cost = 23. Second slot = -15 + .375.
    comparisons = {"day_cost": abs(day["grid_cost"] - 8.375) < 1e-6}
    sides = []
    for i, slot in enumerate(day["periods"]):
        comparisons[f"dual_{i}"] = abs(day["depot_price_per_mwh"][i] - expected_price[i]) < 1e-3
        comparisons[f"center_physics_{i}"] = slot["center"]["point_ac_residuals_pass"]
        for side in slot["sides"]:
            step = side["step_mw"]
            comparisons[f"sides_{i}_{step}"] = bool(
                side["minus"]["point_ac_residuals_pass"] and side["plus"]["point_ac_residuals_pass"]
                and abs(side["left"] - (expected_price[i] - 6*step)) < .01
                and abs(side["right"] - (expected_price[i] + 6*step)) < .01)
            sides.append([i, step, side["left"], side["right"]])
    # With a negative source price, the relaxed optimal point can intentionally
    # consume fictitious losses. An optimizer success must fail the AC point check.
    bad = solve_radial([0], [.02], [0.], [0., 1.], [0., 0.], price=-50., imax_pu=2.)
    comparisons["detect_artificial_losses"] = (bad["status"] == "optimal"
                                 and bad["point_ac_residuals_pass"] is False
                                 and bad["cone_abs"] > 1.)
    print(json.dumps(dict(checks=comparisons, grid_cost=day["grid_cost"],
                          depot_prices=day["depot_price_per_mwh"], secants=sides,
                          negative_price_control=bad), allow_nan=False))
    return int(not all(comparisons.values()))


if __name__ == "__main__":
    raise SystemExit(main())
