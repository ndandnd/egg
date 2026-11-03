"""Read the frozen matched-study roster and compact completed/failed cell packets.

No optimization, population inference, or imputation. Monetary comparisons
below use displayed EUR objective points. Numerical agreement is not an exact
support witness or a global primal/dual gap certificate.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from itertools import product
import json
import math
from pathlib import Path
from statistics import mean, median


LEVELS = {"window": ("primary", "secondary"), "fleet": ("homogeneous", "sistig"),
          "site": ("near", "far"), "size": (10, 40, 80),
          "date": ("2024-01-17", "2024-07-17"), "market": ("hard", "backup_low", "backup_high")}
ARMS = ("fixed", "strong", "joint", "hull")
CONTRASTS = (("joint", "hull"), ("fixed", "joint"), ("strong", "joint"))
EUR_TOL = .01


def finite(x):
    return type(x) in (int, float) and math.isfinite(x)


def metric(values, assigned):
    values = list(values)
    return {"defined": len(values), "assigned": assigned, "missing": assigned-len(values),
            "mean_all": mean(values) if values and len(values) == assigned else None,
            "mean_available": mean(values) if values else None,
            "median_available": median(values) if values else None,
            "min": min(values, default=None), "max": max(values, default=None)}


def contrast(values, assigned):
    values = list(values)
    return {**metric(values, assigned), "above_cent": sum(v > EUR_TOL for v in values),
            "within_cent": sum(abs(v) <= EUR_TOL for v in values),
            "below_minus_cent": sum(v < -EUR_TOL for v in values)}


def load_json(path):
    def no_duplicates(pairs):
        obj = dict(pairs)
        if len(obj) != len(pairs):
            raise ValueError(f"duplicate JSON key in {path.name}")
        return obj
    def nonfinite(value):
        raise ValueError(f"non-finite JSON constant {value}")
    return json.loads(path.read_text(), object_pairs_hook=no_duplicates, parse_constant=nonfinite)


def input_rows(folder):
    roster = load_json(folder / "roster.json")
    keys = list(LEVELS)
    grid = set(product(*LEVELS.values()))
    if (not isinstance(roster, list) or len(roster) != len(grid) or
            {tuple(r[k] for k in keys) for r in roster} != grid):
        raise ValueError("roster must cover the 144 registered descriptor combinations once each")
    ids = [r["id"] for r in roster]
    if len(set(ids)) != len(ids) or any(not isinstance(cell, str) or not cell or
                                       Path(cell).name != cell or cell in (".", "..") for cell in ids):
        raise ValueError("duplicate or invalid roster ID")
    sub = folder / "cells"
    extra = sorted(p.name for p in sub.glob("*.json") if p.stem not in ids)
    rows = []
    for desc in roster:
        path = sub / (desc["id"] + ".json")
        try:
            packet = load_json(path)
            if not isinstance(packet, dict) or any(k in packet and packet[k] != desc[k]
                                                  for k in ["id", *keys]):
                raise ValueError("cell packet has wrong type or does not match its roster descriptor")
            if not isinstance(packet.get("state"), str) or not isinstance(packet.get("arms", {}), dict):
                raise ValueError("invalid state/arms")
        except FileNotFoundError:
            packet = {"state": "missing_packet"}
        except (ValueError, OSError, TypeError) as exc:
            packet = {"state": "invalid_packet", "read_error": str(exc)}
        rows.append({**packet, **desc})
    return rows, extra


def arm(row, name):
    rec = row.get("arms", {}).get(name)
    return rec if isinstance(rec, dict) else {}


def point(row, name, qualified):
    rec = arm(row, name)
    obj = rec.get("objective_eur")
    available = finite(obj)
    if qualified:
        available = available and rec.get("qualified") is True and row["state"] not in (
            "structural_infeasible", "invalid_packet", "missing_packet")
    return float(obj) if available else None


def delta(row, left, right, qualified):
    a, b = point(row, left, qualified), point(row, right, qualified)
    return None if a is None or b is None else a-b


def one_fee(row):
    joint = arm(row, "joint")
    fee, buses = joint.get("fee_eur"), joint.get("buses")
    if finite(fee) and finite(buses) and buses > 0 and fee > 0:
        return fee / buses
    return None


def joint_quarters(row):
    """Admit one complete physical trajectory. Unknown binding flags stay missing."""
    if point(row, "joint", True) is None:
        return None, None
    qs = arm(row, "joint").get("quarters")
    hours = (12, 22, 23) if row["window"] == "primary" else (12, 22)
    assigned = {(h, m) for h in hours for m in (0, 15, 30, 45)}
    if not isinstance(qs, list) or len(qs) != len(assigned):
        return None, "wrong or missing number of selected quarters"
    observed = set()
    entries = []
    for q in qs:
        if not isinstance(q, dict) or q.get("ac_ok") is not True or q.get("grid_ok") is not True:
            return None, "quarter lacks physical/AC qualification"
        try:
            t = datetime.fromisoformat(q["time"])
        except (ValueError, TypeError, KeyError):
            return None, "invalid time"
        if (t.date().isoformat() != row["date"] or t.second or t.microsecond
                or (t.hour, t.minute) not in assigned or (t.hour, t.minute) in observed):
            return None, "date, quarter coverage or unique times disagree"
        observed.add((t.hour, t.minute))
        if any(type(q.get(k)) is not bool for k in ("v_binding", "t_binding")):
            return None, "missing voltage or thermal flag"
        if any(not finite(q.get(k)) for k in ("depot_mw", "backup_mw")):
            return None, "nonfinite depot or backup dispatch"
        # Auxiliary repeated-assignment sensitivity: only physical dispatch is
        # keyed, with a one-watt rounding grid. Conflicting classifications
        # within one key are exposed as ambiguous, never majority-voted.
        key = (row["date"], row["site"], t.hour, t.minute,
               round(q["depot_mw"], 6), round(q["backup_mw"], 6))
        entries.append((key, (q["v_binding"], q["t_binding"])))
    return entries, None


def incidence(pairs):
    pairs = list(pairs)
    return {"denominator": len(pairs), "voltage": sum(v for v,t in pairs),
            "thermal": sum(t for v,t in pairs), "either": sum(v or t for v,t in pairs),
            "both": sum(v and t for v,t in pairs), "neither": sum(not(v or t) for v,t in pairs)}


def group_summary(rows):
    n = len(rows)
    out = {"assigned": n, "state": dict(Counter(r["state"] for r in rows)),
           "arms": {}, "contrasts_eur": {}, "wholesale_only_eur": {}}
    for name in ARMS:
        points = [v for r in rows if (v := point(r, name, False)) is not None]
        accepted = [v for r in rows if (v := point(r, name, True)) is not None]
        statuses = Counter(str(arm(r, name).get("status", "not_reported:" + r["state"])) for r in rows)
        out["arms"][name] = {"numerical_points": len(points), "qualified": len(accepted),
                             "missing_qualified": n-len(accepted), "statuses": dict(statuses),
                             "objective_eur": metric(accepted, n)}
    for left, right in CONTRASTS:
        key = left + "_minus_" + right
        out["contrasts_eur"][key] = {}
        for label, qual in (("all_available_points", False), ("qualified_pairs", True)):
            values = [v for r in rows if (v := delta(r, left, right, qual)) is not None]
            out["contrasts_eur"][key][label] = contrast(values, n)
        comp, paired_grid_effect = [], []
        for r in rows:
            w = r.get("wholesale") or {}
            if isinstance(w, dict) and finite(w.get(left)) and finite(w.get(right)):
                wdelta = w[left]-w[right]
                comp.append(wdelta)
                grid_delta = delta(r, left, right, True)
                if grid_delta is not None:
                    paired_grid_effect.append(grid_delta - wdelta)
        out["wholesale_only_eur"][key] = contrast(comp, n)
        out.setdefault("grid_minus_wholesale_contrast_eur", {})[key] = contrast(paired_grid_effect, n)

    out["schedule_choices"] = {}
    for name in ("fixed", "strong"):
        pairs = []
        for r in rows:
            advantage = delta(r, name, "joint", True)
            b0, b1 = (arm(r, k).get("buses") for k in (name, "joint"))
            if advantage is not None and finite(b0) and finite(b1):
                pairs.append((b1-b0, advantage))
        out["schedule_choices"][name] = {
            "assigned": n, "defined": len(pairs), "joint_more_buses": sum(d>0 for d,_ in pairs),
            "joint_fewer_buses": sum(d<0 for d,_ in pairs),
            "same_count": sum(d==0 for d,_ in pairs),
            "same_count_joint_saves_above_cent": sum(d==0 and adv>EUR_TOL for d,adv in pairs),
            "more_buses_joint_saves_above_cent": sum(d>0 and adv>EUR_TOL for d,adv in pairs)}
    out["layer_spread_kwh"] = {}
    for key in ("max_same_count_floor_spread_kwh", "min_fleet_floor_spread_kwh"):
        spreads = [(r.get("layer_diagnostics") or {}).get(key) for r in rows]
        out["layer_spread_kwh"][key] = metric([v for v in spreads if finite(v)], n)

    fee_checks = []
    for r in rows:
        d = delta(r, "joint", "hull", True)
        f = one_fee(r)
        if d is not None and f is not None:
            fee_checks.append((r["id"], d, f))
    out["one_fee"] = {
        "defined": len(fee_checks), "assigned": n,
        "gap_over_fee": metric([d/f for _,d,f in fee_checks], n),
        "outside_tolerance": [c for c,d,f in fee_checks if d < -EUR_TOL or d > f + EUR_TOL],
        "upper_boundary_within_cent": [c for c,d,f in fee_checks if abs(d-f) <= EUR_TOL],
    }

    cells, quarters, all_keys, omissions = [], [], defaultdict(set), {}
    case_quarters = {}
    for r in rows:
        records, err = joint_quarters(r)
        if err:
            omissions[r["id"]] = err
        if records is None:
            continue
        flags = [pair for _, pair in records]
        case_quarters[r["id"]] = incidence(flags)
        cells.append((any(v for v,t in flags), any(t for v,t in flags)))
        quarters.extend(flags)
        for key, flags in records:
            all_keys[key].add(flags)
    out["joint_binding"] = {"assigned_cells": n, "cells": incidence(cells),
        "assigned_quarter_occurrences": sum(12 if r["window"]=="primary" else 8 for r in rows),
        "quarter_occurrences": incidence(quarters), "unique_dispatch_keys": len(all_keys),
        "unique_unambiguous": incidence(next(iter(flags)) for flags in all_keys.values() if len(flags)==1),
        "ambiguous_rounded_keys": sum(len(flags)>1 for flags in all_keys.values()),
        "incomplete_qualified_trajectories": omissions, "per_cell_quarters": case_quarters}
    return out


def cell_summary(row):
    arms = {}
    for name in ARMS:
        a = arm(row, name)
        obj = point(row, name, True)
        fields = {k: a.get(k) for k in ("status", "fee_eur", "early_kwh", "pairs", "buses")}
        early, total = a.get("early_kwh"), row.get("total_grid_kwh")
        fields.update(objective_point_eur=point(row, name, False), qualified=obj is not None,
                      late_kwh=total - early if finite(total) and finite(early) else None)
        # Descriptive operating quantities are published only for qualified arms.
        if obj is not None:
            qs = a.get("quarters") or []
            by_period = {k: [q.get(k) for q in qs if isinstance(q, dict)] for k in
                         ("backup_mw", "depot_mw", "grid_import_mw", "loss_mw")}
            for k, values in by_period.items():
                if values and all(map(finite, values)):
                    fields[k + "_range"] = [min(values), max(values)]
                    fields[k.removesuffix("_mw") + "_mwh"] = sum(values) * .25
            price = (a.get("solver") or {}).get("depot_price_per_mwh")
            fields["depot_eur_mwh"] = price
        arms[name] = fields
    diagnostics = row.get("layer_diagnostics") or {}
    return {**{k: row[k] for k in ("id", *LEVELS)}, "state": row["state"],
            "error": row.get("error") or row.get("read_error"), "arms": arms,
            "contrast_eur": {x + "_minus_" + y: delta(row, x, y, True) for x, y in CONTRASTS},
            "wholesale": row.get("wholesale") or {}, "window_spot_eur_mwh": row.get("window_spot_eur_mwh"),
            "layer_diagnostics": {k: diagnostics.get(k) for k in
                                  ("max_same_count_floor_spread_kwh", "min_fleet_floor_spread_kwh")},
            "one_bus_fee_eur": one_fee(row)}


def complete_summary(folder):
    rows, extras = input_rows(folder)
    return {"display_resolution_eur": EUR_TOL, "extra_packets_excluded": extras,
            "all": group_summary(rows),
            "strata": {k: {str(v): group_summary([r for r in rows if r[k] == v])
                           for v in vs} for k, vs in LEVELS.items()},
            "cells": [cell_summary(r) for r in rows]}


def fmt(v):
    return "—" if v is None else f"{v:,.3f}"


def report(summary):
    g = summary["all"]
    n = g["assigned"]
    lines = ["# Matched German feeder dispatch", "",
             f"The frozen roster has {n} assignments. The cell states are " +
             ", ".join(f"{k} ({v})" for k, v in sorted(g["state"].items())) + ".",
             "The same two dates, grid, sites and fleet families recur across assignments. "
             "Each count below describes this design.", "", "## Baseline completeness", "",
             "| Arm | Assigned | Numerical objective | Qualified | Missing qualified |",
             "|---|---:|---:|---:|---:|"]
    for a, rec in g["arms"].items():
        lines.append(f"| {a} | {n} | {rec['numerical_points']} | {rec['qualified']} | {rec['missing_qualified']} |")
    lines += ["", "Fixed commits to the predetermined rank pairing. Strong commits to the widest "
              "interval at minimum fleet size. Joint may choose the physical duty count. Hull may "
              "mix whole schedules before the network serves the mean demand.",
              "", "## Paired costs", "", "The table counts differences above €0.01. "
              "The available mean uses only qualified pairs. A dash in the full mean records at least "
              "one missing pair. Differences within one cent leave exact support unresolved.", "",
              "| EUR difference | All numerical pairs | Numerical > €0.01 | Qualified pairs / assigned "
              "| Qualified > €0.01 | Within ±€0.01 | Below −€0.01 | Available mean | Full mean |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, c in g["contrasts_eur"].items():
        p, q = c["all_available_points"], c["qualified_pairs"]
        lines.append(f"| {name.replace('_minus_', ' − ')} | {p['defined']} | {p['above_cent']} | "
                     f"{q['defined']}/{n} | {q['above_cent']} | {q['within_cent']} | "
                     f"{q['below_minus_cent']} | {fmt(q['mean_available'])} | {fmt(q['mean_all'])} |")
    fee = g["one_fee"]
    lines += ["", f"The one-bus-fee prediction could be compared with numerical objectives in "
              f"{fee['defined']}/{n} assignments. {len(fee['outside_tolerance'])} fell outside "
              f"the range [0, fee] by more than €0.01. "
              f"{len(fee['upper_boundary_within_cent'])} were within €0.01 of the upper boundary. "
              "The strict inequality follows from the stated layer assumptions. Native objectives "
              "alone cannot certify a strictly positive gap or equality.",
              "", "## Where native limits bound the selected joint dispatch", "",
              "| Counting unit | Admitted / assigned or distinct | Voltage | Thermal | Either | Both | Neither |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    b = g["joint_binding"]
    for name, d, count in (("Joint trajectories", b["cells"], n),
                           ("Quarter occurrences", b["quarter_occurrences"], b["assigned_quarter_occurrences"]),
                           ("Distinct quarter-dispatches", b["unique_unambiguous"], b["unique_dispatch_keys"])):
        lines.append(f"| {name} | {d['denominator']}/{count} | {d['voltage']} | {d['thermal']} | "
                     f"{d['either']} | {d['both']} | {d['neither']} |")
    lines += ["", "A trajectory counts a limit if it is active in any selected quarter. Voltage and "
              "thermal may bind in different quarters of one trajectory. The quarter rows require a "
              "complete qualified dispatch, one time per date and site within each assignment. "
              "The sensitivity groups repeated observations by date, site, quarter and both depot and "
              f"backup MW rounded to one watt. {b['ambiguous_rounded_keys']} rounded keys had "
              "conflicting labels. Native constraint activity alone cannot identify a nonzero "
              "shadow price. Marginal losses can affect prices when neither limit binds.",
              "", "## Results by design factor", "",
              "| Factor | Level | Assigned | Fixed qual. | Strong qual. | Joint qual. | Hull qual. | "
              "Joint−hull pairs | > €0.01 | Fixed−joint pairs | > €0.01 | Strong−joint pairs | > €0.01 | "
              "Any voltage / joint cells | Any thermal / joint cells |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for factor, values in summary["strata"].items():
        for level, s in values.items():
            entries = [factor, level, s["assigned"], *[s["arms"][a]["qualified"] for a in ARMS]]
            for left, right in CONTRASTS:
                q = s["contrasts_eur"][left + "_minus_" + right]["qualified_pairs"]
                entries.extend([q["defined"], q["above_cent"]])
            c = s["joint_binding"]["cells"]
            entries.extend(f"{c[k]}/{c['denominator']}" for k in ("voltage", "thermal"))
            lines.append("| " + " | ".join(map(str, entries)) + " |")
    lines += ["", "## Wholesale-only control", "",
              "| Difference | Available / assigned | Above €0.01 | Available mean EUR |",
              "|---|---:|---:|---:|"]
    for name, c in g["wholesale_only_eur"].items():
        lines.append(f"| {name.replace('_minus_', ' − ')} | {c['defined']}/{n} | "
                     f"{c['above_cent']} | {fmt(c['mean_available'])} |")
    lines += ["", "The wholesale control omits feeder losses, voltage and current constraints, and "
              "local generation. The per-cell JSON records schedule counts, energies and the control "
              "costs for comparisons on the same assignment.",
              "", "The machine-readable companion retains the full roster, including failed and "
              "structurally infeasible cells, every native arm status, the conditional one-fee checks, "
              "within-assignment quarter counts, and incomplete trajectory diagnostics."]
    lines += ["", "## Schedule choices in matched qualified comparisons", "",
              "| Committed control | Defined / assigned | Joint uses more buses | More buses and saves > €0.01 | "
              "Equal bus count | Equal count and saves > €0.01 | Joint uses fewer buses |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for name, q in g["schedule_choices"].items():
        lines.append(f"| {name} | {q['defined']}/{n} | {q['joint_more_buses']} | "
                     f"{q['more_buses_joint_saves_above_cent']} | {q['same_count']} | "
                     f"{q['same_count_joint_saves_above_cent']} | {q['joint_fewer_buses']} |")
    lines += ["", "At the same count, a saving relative to the predefined pairing can be compared "
              "with the strong minimum-floor matching to assess the role of pair selection. These counts "
              "do not identify a globally unique pairing."]
    if fee["outside_tolerance"]:
        lines.append("\nCases outside the one-fee tolerance: " + ", ".join(fee["outside_tolerance"]) + ".")
    if summary["extra_packets_excluded"]:
        lines.append("\nUnexpected unregistered packet filenames: " + ", ".join(summary["extra_packets_excluded"]) + ".")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    folder = parser.parse_args().output
    paths = [folder / "summary.json", folder / "SUMMARY.md"]
    if any(p.exists() for p in paths):
        parser.error("summary already present; publication requires a fresh namespace")
    summary = complete_summary(folder)
    outputs = [json.dumps(summary, indent=1, allow_nan=False) + "\n", report(summary)]
    for path, output in zip(paths, outputs):
        with path.open("x") as file:
            file.write(output)
    print(json.dumps({"assigned": summary["all"]["assigned"], "state": summary["all"]["state"],
                      "qualified": {k: v["qualified"] for k, v in summary["all"]["arms"].items()}}))


if __name__ == "__main__":
    main()
