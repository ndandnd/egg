"""Peak-run service energies from the public Sistig et al. timetables.

For every operator in the CC BY 4.0 dataset (doi:10.6084/m9.figshare.26088190.v1)
we take the weekday day type with the most service trips, and form
  A = minimum-fleet chains of the trips departing in the morning peak window,
  B = minimum-fleet chains of the trips departing in the afternoon peak window.
A chain is a vehicle run: consecutive trips must be reachable using the
source's directed deadhead time matrix. The minimum number of chains is
(#trips - maximum bipartite matching) on the reachability DAG (Dilworth /
Fulkerson). Each run's energy uses the EB-3 vehicle of the source study
(1.2 kWh/km in service, 0.96 kWh/km deadheading, 16 kWh/h auxiliary while
away from the depot), including pull-out from and pull-in to the nearest
depot. These runs are the A and B services of the two-batch model.

This is a stylized calibration of service-energy heterogeneity: off-peak
service, crew rules and multi-depot assignment are not modelled.

Usage: python3 calibrate.py <path to 20__Selected_transport_operators> <out.json>
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import openpyxl
import scipy.io
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching

KWH_KM_SERVICE = 1.2
KWH_KM_DEADHEAD = 0.96
KWH_H_AUX = 16.0
AM = (5 * 3600 + 30 * 60, 9 * 3600 + 30 * 60)    # departures in [05:30, 09:30)
PM = (14 * 3600 + 30 * 60, 18 * 3600 + 30 * 60)  # departures in [14:30, 18:30)
MIN_LAYOVER = 0  # seconds; the source deadhead matrix already has zero diagonal
MAX_KMH = 90.0   # data-quality filter: implied trip speed above this is a source error


def _rows(path):
    ws = openpyxl.load_workbook(path, read_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[0]
    return [dict(zip(hdr, r)) for r in rows[1:] if r and r[0] is not None]


def load_operator(d):
    raw = [t for t in _rows(os.path.join(d, "trip_set.xlsx")) if t["bool_service"]]
    trips = [t for t in raw if float(t["distance"]) <= MAX_KMH * max(t["arr_time_sec"] - t["dep_time_sec"], 1) / 3600.0]
    load_operator.dropped = len(raw) - len(trips)
    stops = _rows(os.path.join(d, "bus_stops.xlsx"))
    m = scipy.io.loadmat(os.path.join(d, "deadhead_trip_matrix.mat"))["deadhead_trip_matrix"][0, 0]
    ids = [int(x) for x in np.asarray(m["bus_stop_id"]).ravel()]
    idx = {s: k for k, s in enumerate(ids)}
    dist = np.asarray(m["distances"], float) / 1000.0  # km
    time = np.asarray(m["times"], float)                # s
    depots = [int(s["id"]) for s in stops if s["b_depot"] and int(s["id"]) in idx]
    return trips, idx, dist, time, depots


def chains(trips, idx, time):
    """Minimum-fleet chains of the given trips (Fulkerson)."""
    n = len(trips)
    if n == 0:
        return []
    order = sorted(range(n), key=lambda k: trips[k]["dep_time_sec"])
    T = [trips[k] for k in order]
    rows, cols = [], []
    for i in range(n):
        ai, si = T[i]["arr_time_sec"], idx.get(int(T[i]["arr_stop_id"]))
        for j in range(n):
            if i == j:
                continue
            sj = idx.get(int(T[j]["dep_stop_id"]))
            if si is None or sj is None:
                continue
            if T[j]["dep_time_sec"] >= ai + time[si, sj] + MIN_LAYOVER:
                rows.append(i)
                cols.append(j)
    G = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    match = maximum_bipartite_matching(G, perm_type="column")  # match[i] = successor of i
    has_pred = set(int(j) for j in match if j >= 0)
    out = []
    for i in range(n):
        if i in has_pred:
            continue
        run, k = [], i
        while k >= 0:
            run.append(T[k])
            k = int(match[k])
        out.append(run)
    assert sum(len(r) for r in out) == n
    return out


def run_energy(run, idx, dist, time, depots):
    def dh(a, b):
        ia, ib = idx[a], idx[b]
        return KWH_KM_DEADHEAD * dist[ia, ib] + KWH_H_AUX * time[ia, ib] / 3600.0, time[ia, ib]

    e = 0.0
    for t in run:
        e += KWH_KM_SERVICE * float(t["distance"]) + KWH_H_AUX * (t["arr_time_sec"] - t["dep_time_sec"]) / 3600.0
    for t, u in zip(run, run[1:]):
        ee, tt = dh(int(t["arr_stop_id"]), int(u["dep_stop_id"]))
        wait = u["dep_time_sec"] - t["arr_time_sec"] - tt
        e += ee + KWH_H_AUX * max(0.0, wait) / 3600.0  # off-depot waiting keeps auxiliaries on
    first, last = int(run[0]["dep_stop_id"]), int(run[-1]["arr_stop_id"])
    if depots:
        e += min(dh(p, first)[0] for p in depots) + min(dh(last, p)[0] for p in depots)
    return e


def operator_instance(d):
    trips, idx, dist, time, depots = load_operator(d)
    by_day = {}
    for t in trips:
        by_day.setdefault(t["day_type_id"], []).append(t)
    day, tr = max(by_day.items(), key=lambda kv: len(kv[1]))
    tr = [t for t in tr if idx.get(int(t["dep_stop_id"])) is not None and idx.get(int(t["arr_stop_id"])) is not None]
    am = [t for t in tr if AM[0] <= t["dep_time_sec"] < AM[1]]
    pm = [t for t in tr if PM[0] <= t["dep_time_sec"] < PM[1]]
    A = [run_energy(r, idx, dist, time, depots) for r in chains(am, idx, time)]
    B = [run_energy(r, idx, dist, time, depots) for r in chains(pm, idx, time)]
    return dict(operator=os.path.basename(d), day_type=day, n_trips_day=len(tr),
                n_trips_dropped_speed_filter_all_days=load_operator.dropped,
                n_am_trips=len(am), n_pm_trips=len(pm), depots=len(depots),
                a_kwh=sorted(A), b_kwh=sorted(B))


def main(root, out):
    res = []
    for d in sorted(glob.glob(os.path.join(root, "*"))):
        if not os.path.isfile(os.path.join(d, "trip_set.xlsx")):
            continue
        try:
            r = operator_instance(d)
        except Exception as exc:  # report, never silently drop
            r = dict(operator=os.path.basename(d), error=repr(exc))
        print(r["operator"], r.get("error") or (len(r["a_kwh"]), len(r["b_kwh"]),
              round(max(r["a_kwh"] or [0]), 1), round(max(r["b_kwh"] or [0]), 1)))
        res.append(r)
    meta = dict(source="Sistig et al. (2025), doi:10.6084/m9.figshare.26088190.v1, CC BY 4.0",
                am_window_sec=AM, pm_window_sec=PM, kwh_km_service=KWH_KM_SERVICE,
                kwh_km_deadhead=KWH_KM_DEADHEAD, kwh_h_aux=KWH_H_AUX, max_kmh_filter=MAX_KMH)
    json.dump(dict(meta=meta, operators=res), open(out, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
