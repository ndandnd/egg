"""Independent native AC reference for the fixed SimBench MV1 static snapshot.

Convert only the named static CSV members with the official SimBench converter.
No time series or archived voltage results enter the Newton power flow. Sources
and terminal outputs retain their SimBench identifiers and orientation.
"""
import argparse
import csv
import json
import math
import platform
import tempfile
from collections import Counter, defaultdict
from importlib.metadata import version
from pathlib import Path
from zipfile import ZipFile

import pandapower as pp
import simbench as sb
from pandapower.pypower.idx_brch import F_BUS, T_BUS
from pandapower.pypower.idx_bus import VM


GRID = "1-MV-rural--0-sw"
STATIC = ("Coordinates", "ExternalNet", "Line", "LineType", "Load",
          "Measurement", "Node", "RES", "Substation", "Switch", "Transformer",
          "TransformerType")
AC_OPTIONS = dict(algorithm="nr", calculate_voltage_angles=True, init="dc",
                  run_control=False, numba=False, trafo_model="t",
                  trafo_loading="current", tolerance_mva=1e-9,
                  check_connectivity=True, voltage_depend_loads=False)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_network(archive):
    require(archive.name == GRID + ".zip", "unexpected grid archive")
    tables = {}
    with tempfile.TemporaryDirectory(prefix="simbench-static-") as tmp, ZipFile(archive) as z:
        for table in STATIC:
            member = f"{GRID}/{table}.csv"
            dest = Path(tmp, table + ".csv")
            dest.write_bytes(z.read(member))
            with dest.open(newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f, delimiter=";"))
            tables[table] = {r["id"]: r for r in rows}
            require(len(tables[table]) == len(rows), f"duplicate IDs in {table}")
        net = sb.csv2pp(tmp, sep=";", no_generic_coord=True)
    return net, tables


def native_ids(table):
    mapping = {str(row["name"]): i for i, row in table.iterrows()}
    require(len(mapping) == len(table), "official converter returned duplicate device names")
    return mapping


def same(a, b):
    return math.isclose(float(a), float(b), abs_tol=1e-9, rel_tol=1e-12)


def check_inputs(net, tables):
    for source, converted, columns in (
        ("Load", net.load, {"pLoad": "p_mw", "qLoad": "q_mvar"}),
        ("RES", net.sgen, {"pRES": "p_mw", "qRES": "q_mvar"}),
        ("Transformer", net.trafo, {"tappos": "tap_pos"}),
        ("Switch", net.switch, {"cond": "closed"}),
    ):
        lookup = native_ids(converted)
        require(lookup.keys() == tables[source].keys(), f"{source} IDs differ from raw CSV")
        for name, row in tables[source].items():
            converted_row = converted.loc[lookup[name]]
            for raw, parsed in columns.items():
                require(same(row[raw], converted_row[parsed]), f"{source} {name} differs on {raw}")
            if "scaling" in converted.columns:
                require(same(converted_row.scaling, 1), f"unexpected {source} scaling")
            if "in_service" in converted.columns:
                require(bool(converted_row.in_service), f"inactive {source} {name}")
    require(len(net.ext_grid) == 1 and same(net.ext_grid.iloc[0].vm_pu, 1.025),
            "expected one native 1.025 pu external source")


def source_results(net, tables):
    bus_ids = native_ids(net.bus)
    voltages = {name: float(net.res_bus.at[i, "vm_pu"]) for name, i in bus_ids.items()}
    adjacent_switch = defaultdict(set)
    for s in tables["Switch"].values():
        adjacent_switch[s["nodeA"]].add(s["nodeB"])
        adjacent_switch[s["nodeB"]].add(s["nodeA"])

    def matches(raw, index):
        pp_name = str(net.bus.at[index, "name"])
        return raw == pp_name or pp_name in adjacent_switch[raw]

    def record_voltage(raw, ppc_row):
        vm = float(net._ppc["bus"][int(ppc_row.real), VM].real)
        require(raw not in voltages or same(vm, voltages[raw]), f"inconsistent voltage of {raw}")
        voltages[raw] = vm

    elements = {}
    overload = {}
    for label, key, raw_name, ends, fields in (
        ("lines", "line", "Line", ("nodeA", "nodeB"), ("from", "to")),
        ("transformers", "trafo", "Transformer", ("nodeHV", "nodeLV"), ("hv", "lv")),
    ):
        table, result = net[key], net["res_" + key]
        ids = native_ids(table)
        require(ids.keys() == tables[raw_name].keys(), f"incomplete {key} mapping")
        begin, end = net._pd2ppc_lookups["branch"][key]
        require(end - begin == len(table), f"unexpected {key} branch allocation")
        branch_rows = {idx: row for row, idx in enumerate(table.index, start=begin)}
        equipment = {}
        for name, row in tables[raw_name].items():
            i = ids[name]
            branch = net._ppc["branch"][branch_rows[i]]
            desc = {}
            for field, end_name, pp_end, ppc_end in zip(("a", "b"), ends, fields, (F_BUS, T_BUS)):
                raw_bus = row[end_name]
                require(matches(raw_bus, table.at[i, pp_end + "_bus"]), f"orientation mismatch for {name}")
                record_voltage(raw_bus, branch[ppc_end])
                for quantity, unit in (("p", "mw"), ("q", "mvar"), ("i", "ka")):
                    desc[f"{quantity}_{field}_{unit}"] = float(result.at[i, f"{quantity}_{pp_end}_{unit}"])
            desc["loading_percent"] = float(result.at[i, "loading_percent"])
            require(same(row["loadingMax"], table.at[i, "max_loading_percent"]), "loading limit differs")
            overload[name] = max(0.0, desc["loading_percent"] - float(row["loadingMax"]))
            equipment[name] = desc
        elements[label] = equipment

    require(voltages.keys() == tables["Node"].keys(), "not all original Node IDs accounted for")
    for s in tables["Switch"].values():
        if s["cond"] == "1":
            require(same(voltages[s["nodeA"]], voltages[s["nodeB"]]), "voltage differs across closed switch")
    require(all(math.isfinite(v) and v > 0 for v in voltages.values()), "nonphysical or missing voltage")
    v_limits = {}
    for n, v in voltages.items():
        row = tables["Node"][n]
        v_limits[n] = max(0., float(row["vmMin"]) - v, v - float(row["vmMax"]))
    source_mw = float(net.res_ext_grid.p_mw.sum())
    source_mvar = float(net.res_ext_grid.q_mvar.sum())
    loss_mw = float(net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum())
    loss_mvar = float(net.res_line.ql_mvar.sum() + net.res_trafo.ql_mvar.sum())
    sums = {name: float(net["res_" + name.split("_")[0]][name.split("_", 1)[1]].sum())
            for name in ("load_p_mw", "load_q_mvar", "sgen_p_mw", "sgen_q_mvar")}
    balances = {"mw": source_mw + sums["sgen_p_mw"] - sums["load_p_mw"] - loss_mw,
                "mvar": source_mvar + sums["sgen_q_mvar"] - sums["load_q_mvar"] - loss_mvar}
    require(max(map(abs, balances.values())) < 1e-7, "native power balance residual exceeds 1e-7")
    return {
        "status": "AC_CONVERGED", "converged": True,
        "within_native_limits": max(v_limits.values()) <= 1e-8 and max(overload.values()) <= 1e-8,
        "grid": GRID, "scope": "unscaled static operating point, no depot or controls",
        "versions": {"python": platform.python_version(), "simbench": sb.__version__,
                     "pandapower_distribution": version("pandapower"), "pandapower_module": pp.__version__,
                     "numpy": version("numpy"), "scipy": version("scipy"), "pandas": version("pandas")},
        "runpp": AC_OPTIONS, "slack_vm_pu": float(net.ext_grid.iloc[0].vm_pu), "source_injections": sums,
        "csv2pp": {"sep": ";", "no_generic_coord": True, "static_tables": list(STATIC)},
        "import_mw": source_mw, "import_mvar": source_mvar, "loss_mw": loss_mw, "net_absorption_mvar": loss_mvar,
        "balance_residual": balances, "voltage_pu": voltages, **elements,
        "coverage": {"original_nodes": len(tables["Node"]), "official_pp_buses": len(bus_ids),
                     "recovered_branch_terminal_nodes": len(voltages) - len(bus_ids),
                     "original_switch_states": dict(Counter(s["cond"] for s in tables["Switch"].values())),
                     "fixed_tap_position_by_transformer": dict(zip(net.trafo.name, map(float, net.trafo.tap_pos)))},
        "native_limits": {"voltage_min_pu": min(voltages.values()), "voltage_max_pu": max(voltages.values()),
                          "max_voltage_violation_pu": max(v_limits.values()),
                          "voltage_violations_pu": {n: v for n, v in v_limits.items() if v > 1e-8},
                          "max_overload_percentage_points": max(overload.values()),
                          "overloads_percentage_points": {n: v for n, v in overload.items() if v > 1e-8}},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("archive", type=Path)
    args = ap.parse_args()
    net, tables = load_network(args.archive)
    check_inputs(net, tables)
    pp.runpp(net, **AC_OPTIONS)
    require(bool(net.converged), "pandapower Newton did not converge")
    print(json.dumps(source_results(net, tables), allow_nan=False, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
