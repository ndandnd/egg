"""Synthetic and public-feeder qualification. Run once under the frozen external meter."""

import json
import math
from collections import deque
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# The absolute cone gate is in squared per-unit power. Report the relative slack
# even on nearly unloaded branches, where dividing by tiny flows amplifies noise.
CONE_ABS_TOL = 2e-6
FEAS_TOL = 2e-7
AC_TOL = 1e-4
REGRESSION_TOL = 1e-3
SMOOTH_PRICE_TOL = 1e-3
SECANT_TOL = 0.05
STEPS_MW = (0.01, 0.001)


def observe(result, name, measured, target, tolerance):
    measured = float(measured)
    difference = abs(measured - target)
    result["checks"][name] = dict(value=measured if math.isfinite(measured) else str(measured),
                                  target=target, tolerance=tolerance)
    if not math.isfinite(difference) or difference > tolerance:
        result["failures"].append(name)


def solve(result, name, parent, r, x, loads, reactive, **options):
    from egglab.radial_opf import solve_radial

    point = solve_radial(parent, r, x, loads, reactive, **options)
    row = {k: point[k] for k in ("status", "objective", "import_mw", "import_mvar",
                                  "loss_mw", "cone_abs", "cone_rel", "balance_max_pu",
                                  "cone_rel_floor", "voltage_eq_max_pu", "limit_violation_max_pu",
                                  "point_ac_residuals_pass")}
    result["solves"][name] = row
    for key, value in row.items():
        if isinstance(value, float) and not math.isfinite(value):
            row[key] = str(value)
    if point["status"] != "optimal":
        raise ValueError(f"{name}: native status {point['status']}")
    for key in ("balance_max_pu", "voltage_eq_max_pu", "limit_violation_max_pu"):
        observe(result, f"{name}_{key}", point[key], 0.0, FEAS_TOL)
    if not options.get("linearized", False):
        observe(result, f"{name}_cone_abs", point["cone_abs"], 0.0, CONE_ABS_TOL)
        if point["point_ac_residuals_pass"] is not True:
            result["failures"].append(f"{name}_native_point_ac_residuals")
    for key in ("objective", "import_mw", "import_mvar", "loss_mw"):
        if not math.isfinite(point[key]):
            raise ValueError(f"{name}: nonfinite {key}")
    return point


def two_bus(result, scenario):
    # Smooth ideal fixture deliberately uses a nonunit MVA base and slot length.
    if scenario == "ideal_affine":
        point = solve(result, "center", [0], [0.0], [0.0], [0.2, 0.8], [0.0, 0.0],
                      hours=0.5, base_mva=2.0, price=40.0, curvature=12.0)
        observe(result, "price", point["dlmp"][1], 52.0, SMOOTH_PRICE_TOL)
        observe(result, "objective", point["objective"], 23.0, 1e-5)
        observe(result, "depot_voltage", point["voltage_pu"][1], 1.0, AC_TOL)
        observe(result, "source_power", point["import_mw"], 1.0, AC_TOL)
        return

    demand, hours = 1.0, 1.0
    resistance = 0.02 if scenario == "resistive_ac" else 0.0
    if scenario == "resistive_ac":
        options = dict(price=40.0, curvature=12.0)
    elif scenario == "pwl_kink":
        options = dict(pwl=(1.0, 30.0, 70.0))
    else:
        options = dict(price=30.0, root_import_cap_mw=0.75, backup=(1, 1.0, 70.0))

    def dispatch(label, load):
        point = solve(result, label, [0], [resistance], [0.0], [0.0, load], [0.0, 0.0],
                      hours=hours, **options)
        depot_price = point["dlmp"][1]
        if not math.isfinite(depot_price):
            raise ValueError(f"{label}: nonfinite depot DLMP")
        result["solves"][label]["depot_price"] = depot_price
        if scenario == "resistive_ac":
            # High-voltage AC solution of P = load + r P², with unit slack and Q=0.
            discriminant = math.sqrt(1 - 4 * resistance * load)
            power = 2 * load / (1 + discriminant)
            voltage = 0.5 * (1 + discriminant)
            cost = (40.0 * power + 6.0 * power**2) * hours
            marginal = (40.0 + 12.0 * power) / discriminant
            observe(result, label + "_ac_voltage", point["voltage_pu"][1], voltage, AC_TOL)
            observe(result, label + "_ac_source_p", point["import_mw"], power, AC_TOL)
            observe(result, label + "_ac_source_q", point["import_mvar"], 0.0, AC_TOL)
            observe(result, label + "_ac_loss", point["loss_mw"], power - load, AC_TOL)
            observe(result, label + "_analytic_dlmp", depot_price, marginal, SMOOTH_PRICE_TOL)
        elif scenario == "pwl_kink":
            cost = (30.0 * min(load, 1.0) + 70.0 * max(0.0, load - 1.0)) * hours
            if load == 1.0:
                # The analytical subgradient interval is [30,70]. Solver choice is free.
                observe(result, label + "_outside_price_interval",
                        max(0.0, 30.0 - depot_price, depot_price - 70.0), 0.0, SECANT_TOL)
            else:
                observe(result, label + "_segment_price", depot_price,
                        30.0 if load < 1.0 else 70.0, SECANT_TOL)
        else:
            # The upstream constraint stays binding in a neighborhood. The local unit
            # remains strictly between 0 and 1 MW, fixing the unique marginal price.
            cost = (0.75 * 30.0 + (load - 0.75) * 70.0) * hours
            observe(result, label + "_binding_import", point["import_mw"], 0.75, AC_TOL)
            observe(result, label + "_interior_backup", point["backup_mw"], load - 0.75, AC_TOL)
            observe(result, label + "_unique_price", depot_price, 70.0, SMOOTH_PRICE_TOL)
        observe(result, label + "_objective", point["objective"], cost, 1e-5)
        return point["objective"], cost

    center, exact = dispatch("center", demand)
    for step in STEPS_MW:
        lower, exact_lower = dispatch(f"minus_{step}", demand - step)
        upper, exact_upper = dispatch(f"plus_{step}", demand + step)
        observe(result, f"left_secant_{step}", (center - lower) / (step * hours),
                (exact - exact_lower) / (step * hours), SECANT_TOL)
        observe(result, f"right_secant_{step}", (upper - center) / (step * hours),
                (exact_upper - exact) / (step * hours), SECANT_TOL)


def standard_feeder(result):
    import pandapower as pp
    from pandapower.networks import case33bw

    net = case33bw()
    result["pandapower_version"] = pp.__version__
    if (len(net.bus) != 33 or not net.bus.in_service.all() or len(net.ext_grid) != 1
            or len(net.switch) or any(len(net[k]) for k in ("trafo", "trafo3w", "gen", "sgen", "shunt"))):
        raise ValueError("unsupported case33bw topology or devices")
    root = int(net.ext_grid.bus.iloc[0])
    if root != 0 or net.ext_grid.vm_pu.iloc[0] != 1.0:
        raise ValueError("unrecognized slack")
    edges = net.line.loc[net.line.in_service]
    if len(edges) != 32:
        raise ValueError("case33bw must contain 32 in-service series lines")
    adjacency = {int(bus): [] for bus in net.bus.index}
    for line_id, line in edges.iterrows():
        if line.c_nf_per_km != 0 or line.g_us_per_km != 0 or line.parallel != 1:
            raise ValueError("unsupported line shunt or parallel circuit")
        i, j = int(line.from_bus), int(line.to_bus)
        adjacency[i].append((j, line_id))
        adjacency[j].append((i, line_id))
    order, indices, edge_ids = [root], {root: 0}, []
    parent, r, x = [], [], []
    pending = deque([root])
    while pending:
        i = pending.popleft()
        for j, edge_id in sorted(adjacency[i]):
            if j in indices:
                continue
            indices[j] = len(order)
            order.append(j)
            pending.append(j)
            edge_ids.append(edge_id)
            parent.append(indices[i])
            if net.bus.vn_kv.at[i] != net.bus.vn_kv.at[j]:
                raise ValueError("different nominal voltages on one series line")
            zbase = net.bus.vn_kv.at[i] ** 2 / net.sn_mva  # kV²/MVA = ohms
            line = edges.loc[edge_id]
            r.append(float(line.r_ohm_per_km * line.length_km / zbase))
            x.append(float(line.x_ohm_per_km * line.length_km / zbase))
    if len(order) != len(net.bus):
        raise ValueError("case33bw is disconnected")
    p, q = [0.0] * len(order), [0.0] * len(order)
    for load in net.load.loc[net.load.in_service].itertuples():
        if load.const_z_percent != 0 or load.const_i_percent != 0:
            raise ValueError("expected constant-power load")
        p[indices[load.bus]] += load.p_mw * load.scaling
        q[indices[load.bus]] += load.q_mvar * load.scaling
    # MATPOWER uses one-based IDs, pandapower uses zero-based bus indices here.
    result["matpower_bus_ids_in_solver_order"] = [i + 1 for i in order]
    result["pandapower_line_ids_in_solver_order"] = [int(i) for i in edge_ids]
    result["base_mva"] = float(net.sn_mva)
    # In the injection convention all downstream real/reactive upper injections
    # are nonpositive here. Gan's positive-part path matrices reduce to identity.
    # The no-loss voltage envelope with these loads lies below slack voltage.
    result["passive_path_conditions"] = dict(
        positive_series_impedances=all(y > 0 for y in r + x),
        nonnegative_fixed_loads=all(y >= 0 for y in p + q),
        root_voltage_within_upper_bound=1.0 < 1.10,
        positive_upstream_marginal_cost=True,
        branch_current_limits_imposed=False,
    )
    if not all((all(y > 0 for y in r + x), all(y >= 0 for y in p + q))):
        raise ValueError("expected a passive positive-impedance case33bw benchmark")
    pp.runpp(net, algorithm="nr", init="flat", calculate_voltage_angles=True,
             tolerance_mva=1e-9, numba=False)
    if not net.converged:
        raise ValueError("independent AC Newton PF failed")
    ref_voltage = [float(net.res_bus.vm_pu.at[i]) for i in order]
    ref_p, ref_q = [], []
    for edge_id, i in zip(edge_ids, parent):
        side = "from" if edges.from_bus.at[edge_id] == order[i] else "to"
        ref_p.append(float(net.res_line.at[edge_id, f"p_{side}_mw"]))
        ref_q.append(float(net.res_line.at[edge_id, f"q_{side}_mvar"]))
    ac = dict(import_mw=float(net.res_ext_grid.p_mw.iloc[0]),
              import_mvar=float(net.res_ext_grid.q_mvar.iloc[0]),
              loss_mw=float(net.res_line.pl_mw.sum()), minimum_voltage=min(ref_voltage),
              minimum_matpower_bus=order[ref_voltage.index(min(ref_voltage))] + 1)
    result["independent_ac"] = ac
    observe(result, "benchmark_loss", ac["loss_mw"], 0.2027, REGRESSION_TOL)
    observe(result, "benchmark_min_voltage", ac["minimum_voltage"], 0.9131, REGRESSION_TOL)
    observe(result, "benchmark_min_bus", ac["minimum_matpower_bus"], 18, 0)
    for name, linearized in (("socp", False), ("lindistflow", True)):
        point = solve(result, name, parent, r, x, p, q, base_mva=float(net.sn_mva),
                      price=50.0, vmin=0.90, vmax=1.10, linearized=linearized)
        deviations = {k: abs(point[k] - ac[k]) for k in ("import_mw", "import_mvar", "loss_mw")}
        for key, reference in (("voltage_pu", ref_voltage), ("p_send_mw", ref_p), ("q_send_mvar", ref_q)):
            if len(point[key]) != len(reference):
                raise ValueError(f"{name}: wrong length {key}")
            if not all(math.isfinite(y) and math.isfinite(z) for y, z in zip(point[key], reference)):
                raise ValueError(f"{name}: nonfinite {key}")
            deviations[key] = max(abs(y - z) for y, z in zip(point[key], reference))
        result["solves"][name]["max_ac_deviations"] = deviations
        if not linearized:
            for key, error in deviations.items():
                observe(result, "socp_vs_ac_" + key, error, 0.0, AC_TOL)
        else:
            observe(result, "lindistflow_lossless", point["loss_mw"], 0.0, AC_TOL)


def main():
    report = {}
    for name in ("ideal_affine", "resistive_ac", "pwl_kink", "binding_unique", "case33bw"):
        result = dict(checks={}, solves={}, failures=[])
        report[name] = result
        try:
            if name == "case33bw":
                standard_feeder(result)
            else:
                two_bus(result, name)
        except Exception as exc:
            result["failures"].append(f"{type(exc).__name__}: {exc}")
    success = all(not row["failures"] for row in report.values())
    print(json.dumps(dict(success=success, cases=report), allow_nan=False, separators=(",", ":")))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
