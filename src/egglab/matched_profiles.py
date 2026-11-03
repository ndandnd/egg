"""SimBench 2016 quarter hours paired to 2024 price intervals for the German study.

Match ISO week/weekday and the local clock label. This is a season/weekday
proxy, not a reconstruction of the network's weather or demand in 2024.
SimBench 1.5.3 networks/profiles.py, get_absolute_values and
get_absolute_profiles_from_relative_profiles, define the scaling conventions.
"""
import csv
import io
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from zipfile import ZipFile
from zoneinfo import ZoneInfo

from egglab.simbench_radial import number
from experiments.identify_simbench_depots import read_table


DAYS = ("2024-01-17", "2024-07-17")
HOURS = (12, 22, 23)


def _selected_relative(archive, name, requested, columns):
    """Scan the annual file once; decode numeric values only at selected labels."""
    members = [m for m in archive.namelist() if Path(m).name == name + ".csv"]
    if len(members) != 1:
        raise ValueError(f"missing or duplicate {name} table")
    selected = {}
    with archive.open(members[0]) as stream, io.TextIOWrapper(stream, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        headers = reader.fieldnames or ()
        if len(set(headers)) != len(headers) or not (columns | {"time"}) <= set(headers):
            raise ValueError(f"incomplete or duplicate {name} columns")
        for row in reader:
            stamp = row["time"]
            if stamp in requested:
                if stamp in selected:
                    raise ValueError(f"ambiguous time in {name}: {stamp}")
                selected[stamp] = {col: number(row[col]) for col in columns}
    if selected.keys() != requested:
        raise ValueError(f"missing timestamps in {name}: {sorted(requested - selected.keys())}")
    return selected


def read_matched_profiles(archive_path, model, price_days=DAYS, hours=HOURS):
    days = tuple(date.fromisoformat(str(day)) for day in price_days)
    hours = tuple(hours)
    if not days or len(set(days)) != len(days) or any(d.isoformat() not in DAYS for d in days):
        raise ValueError("expected unique prespecified 2024 benchmark dates")
    if not hours or tuple(sorted(set(hours))) != hours or not set(hours) <= set(HOURS):
        raise ValueError("expected ordered, unique benchmark window hours")
    windows = {}
    berlin = ZoneInfo("Europe/Berlin")
    for day in days:
        iso = day.isocalendar()
        proxy = date.fromisocalendar(2016, iso.week, iso.weekday)
        windows[day.isoformat()] = []
        for hour in hours:
            for minute in (0, 15, 30, 45):
                local = datetime(day.year, day.month, day.day, hour, minute, tzinfo=berlin)
                label = datetime(proxy.year, proxy.month, proxy.day, hour, minute)
                windows[day.isoformat()].append(dict(time_local=local.isoformat(),
                    profile_time_local=label.isoformat(), profile_csv_time=label.strftime("%d.%m.%Y %H:%M"),
                    hour=hour, minute=minute, interval_hours=.25))
    requested = {q["profile_csv_time"] for quarters in windows.values() for q in quarters}
    with ZipFile(archive_path) as archive:
        loads = read_table(archive, "Load", ("id", "node", "profile", "pLoad", "qLoad"))
        res = read_table(archive, "RES", ("id", "node", "calc_type", "profile", "pRES", "qRES"))
        lp = {r["profile"]+suffix for r in loads.values() for suffix in ("_pload", "_qload")}
        rp = {r["profile"] for r in res.values()}
        load_factors = _selected_relative(archive, "LoadProfile", requested, lp)
        renewable_factors = _selected_relative(archive, "RESProfile", requested, rp)

    for quarters in windows.values():
        for quarter in quarters:
            lf = load_factors[quarter["profile_csv_time"]]
            rf = renewable_factors[quarter["profile_csv_time"]]
            p_mw = [0.] * len(model["bus_classes"])
            q_mvar = [0.] * len(p_mw)
            for row in loads.values():
                i = model["bus_index"][row["node"]]
                p_mw[i] += number(row["pLoad"]) * lf[row["profile"]+"_pload"]
                q_mvar[i] += number(row["qLoad"]) * lf[row["profile"]+"_qload"]
            for row in res.values():
                if row["calc_type"] != "pq":
                    raise ValueError(f"{row['id']}: unsupported renewable control")
                i = model["bus_index"][row["node"]]
                p_mw[i] -= number(row["pRES"]) * rf[row["profile"]]
                # The official profile controller changes sgen P only.
                q_mvar[i] -= number(row["qRES"])
            quarter.update(p_mw=p_mw, q_mvar=q_mvar, load_factors=lf, renewable_factors=rf)
    return windows


class NativeACValidator:
    """One official converter, one independent absolute-profile build per time,
    and at most one Newton power flow per distinct quarter and net injection.

    check() compares *each* conic witness, even when the native PF is cached.
    The instance is used serially in a single process.
    """
    def __init__(self, archive_path, model):
        from experiments.qualify_simbench_static import check_inputs, load_network, native_ids
        self.model = model
        self.net, self.tables = load_network(Path(archive_path))
        check_inputs(self.net, self.tables)
        self.native_buses = native_ids(self.net.bus)
        self.base_quarters = {}
        self.references = {}

    def _locate(self, native_or_index):
        index = (self.model["bus_index"][native_or_index] if isinstance(native_or_index, str)
                 else native_or_index)
        eligible = [self.native_buses[name] for name, i in self.model["bus_index"].items()
                    if i == index and name in self.native_buses]
        if not eligible or index in self.model["passive_open_ends"]:
            raise ValueError(f"external injection at unavailable or open-terminal bus {native_or_index!r}")
        return index, min(eligible)

    def _background(self, quarter):
        import pandas as pd
        import simbench as sb
        import numpy as np

        # Independently multiply the raw coefficients on the officially
        # converted device tables. Verify bus sums against the radial inputs.
        net = deepcopy(self.net)
        p = np.zeros(len(self.model["bus_classes"]))
        q = np.zeros_like(p)
        idx = self.model["bus_index"]
        for kind, factor_key, sign in (("load", "load_factors", 1), ("sgen", "renewable_factors", -1)):
            profiles = pd.DataFrame([quarter[factor_key]])
            for attribute in (("p_mw", "q_mvar") if kind == "load" else ("p_mw",)):
                vals = sb.get_absolute_profiles_from_relative_profiles(
                    self.net, kind, attribute, relative_profiles=profiles)
                if vals.shape != (1, len(net[kind])) or not vals.columns.equals(net[kind].index):
                    raise ValueError(f"official profile-library output disagrees with {kind} device IDs")
                net[kind].loc[:, attribute] = vals.iloc[0].to_numpy(dtype=float)
            for row in net[kind].itertuples():
                bus = idx[str(net.bus.at[row.bus, "name"])]
                p[bus] += sign * row.p_mw
                q[bus] += sign * row.q_mvar
        if not (np.allclose(p, quarter["p_mw"], rtol=0, atol=1e-10)
                and np.allclose(q, quarter["q_mvar"], rtol=0, atol=1e-10)):
            raise ValueError("official absolute-profile nodal injections disagree with radial inputs")
        return net

    def check(self, quarter, depot_node, depot_mw, point, *, backup_node=None, backup_mw=None):
        import pandapower as pp
        from experiments.qualify_simbench_static import AC_OPTIONS, source_results
        from experiments.compare_simbench_static import compare

        stamp = quarter["profile_csv_time"]
        gen = number(point["backup_mw"])
        if backup_mw is not None and abs(number(backup_mw) - gen) > 1e-9:
            raise ValueError("posted backup injection differs from conic witness")
        depot_mw = number(depot_mw)
        depot, native_depot = self._locate(depot_node)
        if gen != 0 and backup_node is None:
            raise ValueError("missing native location of backup dispatch")
        backup = self._locate(backup_node) if backup_node is not None else None
        injections = {depot: depot_mw}
        if backup:
            injections[backup[0]] = injections.get(backup[0], 0.) - gen
        key = (stamp, tuple(sorted((i, v) for i, v in injections.items() if v != 0)))
        found = key in self.references
        if not found:
            try:
                if stamp not in self.base_quarters:
                    self.base_quarters[stamp] = self._background(quarter)
                net = deepcopy(self.base_quarters[stamp])
                if depot_mw:
                    pp.create_load(net, native_depot, p_mw=depot_mw, q_mvar=0., name="study depot")
                if gen:
                    pp.create_sgen(net, backup[1], p_mw=gen, q_mvar=0., name="study backup")
                pp.runpp(net, **AC_OPTIONS)
                if not net.converged:
                    raise ValueError("native Newton PF did not converge")
                self.references[key] = source_results(net, self.tables)
            except Exception as exc:
                self.references[key] = {"error": f"{type(exc).__name__}: {exc}"}
        ac = self.references[key]
        if "error" in ac:
            return dict(qualified=False, reference_cached=found, profile_csv_time=stamp, **ac)
        comparison = compare(self.model, point, ac)
        return dict(qualified=bool(comparison["comparison_pass"] and ac["within_native_limits"]
                                   and point["status"] == "optimal" and point["point_ac_residuals_pass"]),
                    reference_cached=found, profile_csv_time=stamp, converged=ac["converged"],
                    within_native_limits=ac["within_native_limits"], import_mw=ac["import_mw"],
                    import_mvar=ac["import_mvar"], loss_mw=ac["loss_mw"],
                    native_limits=ac["native_limits"], **comparison)
