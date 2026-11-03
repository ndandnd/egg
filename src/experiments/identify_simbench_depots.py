"""Identify near and far MV supply buses using only static SimBench CSV tables.

The distance metric is the exact decimal sum of energized native line lengths
from the external grid; switches and transformers contribute zero length.
Imported power, profiles, voltage solutions and prices play no part in siting.
"""
import argparse
import csv
import io
import json
import math
from collections import defaultdict, deque
from decimal import Decimal
from pathlib import Path
from zipfile import BadZipFile, ZipFile


class TopologyError(ValueError):
    pass


def read_table(archive, name, fields):
    members = [m for m in archive.namelist() if Path(m).name == name + ".csv"]
    if len(members) != 1:
        raise TopologyError(f"expected one {name}.csv, found {len(members)}")
    with archive.open(members[0]) as stream, io.TextIOWrapper(stream, encoding="utf-8-sig") as text:
        records = csv.DictReader(text, delimiter=";")
        missing = set(fields) - set(records.fieldnames or ())
        if missing:
            raise TopologyError(f"{name}.csv lacks {sorted(missing)}")
        rows = {}
        for row in records:
            if not row["id"] or row["id"] in rows:
                raise TopologyError(f"missing or duplicate identifier in {name}.csv")
            rows[row["id"]] = row
        return rows


class SwitchClasses:
    def __init__(self, nodes):
        self.parent = {n: n for n in nodes}

    def representative(self, n):
        if n not in self.parent:
            raise TopologyError(f"undefined native node {n!r}")
        while self.parent[n] != n:
            self.parent[n] = self.parent[self.parent[n]]
            n = self.parent[n]
        return n

    def close(self, a, b):
        a, b = sorted((self.representative(a), self.representative(b)))
        self.parent[b] = a


def positive(value, description):
    x = float(value)
    if not math.isfinite(x) or x <= 0:
        raise TopologyError(f"invalid {description}: {value!r}")
    return x


def group_edges(members):
    """Parallel equipment must have a demonstrable equal-sharing nameplate."""
    if len(members) > 1:
        # Two distinct paths through unmatched impedances or taps are not one
        # circuit with the sum of their ratings. Refuse that identification.
        if any(m["kind"] != "transformer" for m in members):
            raise TopologyError("parallel line group needs separate sharing model")
        features = {(m["type"], m["tap_pos"], m["hv_class"], m["lv_class"],
                     m["loading_max_percent"], m["auto_tap"], m["auto_tap_side"])
                    for m in members}
        if len(features) != 1:
            raise TopologyError("parallel transformers differ in type, orientation, tap or limit")
    first = members[0]
    return {
        "members": sorted(members, key=lambda m: m["id"]),
        "length_km": first["length_km"],
        "thermal_nameplate_mva": sum(m["thermal_nameplate_mva"] for m in members),
        "operating_rating_mva": sum(
            m["thermal_nameplate_mva"] * m["loading_max_percent"] / 100 for m in members
        ),
    }


def rooted_tree(equipment, root):
    network = defaultdict(list)
    for (a, b), members in equipment.items():
        if a == b:
            raise TopologyError(f"equipment has shorted terminals: {members[0]['id']}")
        link = group_edges(members)
        network[a].append((b, link))
        network[b].append((a, link))
    # Keep terminal stubs of one-ended open lines. At this stage they can
    # contribute degree and shunt current but cannot feed a load through a switch.
    parent, lengths = {root: None}, {root: Decimal(0)}
    incoming, queue = {}, deque([root])
    while queue:
        bus = queue.popleft()
        for child, edge in network[bus]:
            if child == parent[bus]:
                continue
            if child in parent:
                raise TopologyError(f"multiple energized paths involving {bus} and {child}")
            parent[child] = bus
            incoming[child] = edge
            lengths[child] = lengths[bus] + edge["length_km"]
            queue.append(child)
    return parent, incoming, lengths


def identify(archive):
    nodes = read_table(archive, "Node", ("id", "vmR", "voltLvl", "type"))
    switches = read_table(archive, "Switch", ("id", "nodeA", "nodeB", "cond"))
    lines = read_table(archive, "Line", ("id", "nodeA", "nodeB", "length", "type", "loadingMax"))
    ltypes = read_table(archive, "LineType", ("id", "iMax"))
    trafos = read_table(archive, "Transformer", ("id", "nodeHV", "nodeLV", "type",
                                                 "tappos", "autoTap", "autoTapSide", "loadingMax"))
    ttypes = read_table(archive, "TransformerType", ("id", "sR", "vmHV", "vmLV"))
    sources = read_table(archive, "ExternalNet", ("id", "node", "calc_type"))
    loads = read_table(archive, "Load", ("id", "node", "pLoad"))
    if len(sources) != 1 or next(iter(sources.values()))["calc_type"] != "vavm":
        raise TopologyError("expected one fixed-angle, fixed-voltage external source")
    source = next(iter(sources.values()))["node"]
    kv = {n: positive(r["vmR"], f"{n} nominal voltage") for n, r in nodes.items()}

    classes = SwitchClasses(nodes)
    for switch in switches.values():
        a, b = switch["nodeA"], switch["nodeB"]
        if a not in nodes or b not in nodes or switch["cond"] not in {"0", "1"}:
            raise TopologyError(f"{switch['id']}: undefined switch state or endpoint")
        if switch["cond"] == "1":
            if kv[a] != kv[b]:
                raise TopologyError(f"{switch['id']}: cannot fuse dissimilar voltage levels")
            classes.close(a, b)
    root = classes.representative(source)
    equipment = defaultdict(list)
    for row in lines.values():
        a, b = row["nodeA"], row["nodeB"]
        group = tuple(sorted((classes.representative(a), classes.representative(b))))
        if kv[a] != kv[b]:
            raise TopologyError(f"{row['id']}: line crosses voltage levels")
        length = Decimal(row["length"])
        if not length.is_finite() or length <= 0:
            raise TopologyError(f"{row['id']}: invalid line length")
        amps = positive(ltypes[row["type"]]["iMax"], f"{row['id']} iMax")
        equipment[group].append(dict(
            kind="line", id=row["id"], type=row["type"], node_a=a, node_b=b,
            length_km=length, rated_voltage_kv=kv[a], rated_current_amp=amps,
            thermal_nameplate_mva=math.sqrt(3) * kv[a] * amps / 1000.0,
            loading_max_percent=positive(row["loadingMax"], "line loadingMax"),
        ))

    mv_roots = set()
    for row in trafos.values():
        a, b = row["nodeHV"], row["nodeLV"]
        hv, lv = classes.representative(a), classes.representative(b)
        ttype = ttypes[row["type"]]
        if (kv[a], kv[b]) != (float(ttype["vmHV"]), float(ttype["vmLV"])):
            raise TopologyError(f"{row['id']}: transformer voltage levels disagree")
        if hv != root or kv[b] != 20:
            raise TopologyError(f"{row['id']}: not an HV-source to 20-kV distribution transformer")
        mv_roots.add(lv)
        equipment[tuple(sorted((hv, lv)))].append(dict(
            kind="transformer", id=row["id"], type=row["type"], node_hv=a, node_lv=b,
            hv_class=hv, lv_class=lv, tap_pos=int(row["tappos"]), auto_tap=row["autoTap"],
            auto_tap_side=row["autoTapSide"], length_km=Decimal(0),
            thermal_nameplate_mva=positive(ttype["sR"], "transformer rating"),
            loading_max_percent=positive(row["loadingMax"], "transformer loadingMax"),
        ))
    if not mv_roots:
        raise TopologyError("no source-connected HV/MV transformer")
    parent, incoming, lengths = rooted_tree(equipment, root)

    # Exclude the source-side busbars themselves. A standing load located on
    # the substation's 20-kV root rail is not a downstream connection.
    candidates = defaultdict(set)
    for row in loads.values():
        n = row["node"]
        bus = classes.representative(n)
        demand = float(row["pLoad"])
        if not math.isfinite(demand):
            raise TopologyError(f"{row['id']}: nonfinite static load")
        if demand <= 0 or nodes[n]["voltLvl"] != "5" or kv[n] != 20:
            continue
        if bus not in parent:
            raise TopologyError(f"{n}: energized path to positive static MV load unresolved")
        if bus != root and bus not in mv_roots:
            candidates[bus].add(n)
    if len(candidates) < 2:
        raise TopologyError("fewer than two distinct eligible supply buses")
    # Original CSV IDs, including lexical ties after switch-class contraction.
    labels = {bus: min(names) for bus, names in candidates.items()}
    near = min(labels, key=lambda bus: (lengths[bus], labels[bus]))
    far = min(labels, key=lambda bus: (-lengths[bus], labels[bus]))
    if lengths[far] == lengths[near]:
        raise TopologyError("near and far placements have no distance contrast")

    def describe(depot):
        path = []
        child = depot
        while child != root:
            prev = parent[child]
            path.append(dict(from_bus_class=prev, to_bus_class=child, **incoming[child]))
            child = prev
        path.reverse()
        if path[0]["members"][0]["kind"] != "transformer":
            raise TopologyError("depot path does not pass through a source transformer")
        nominal = min(g["thermal_nameplate_mva"] for g in path)
        operating = min(g["operating_rating_mva"] for g in path)
        return {
            "node": labels[depot], "load_bus_aliases": sorted(candidates[depot]),
            "nominal_voltage_kv": kv[labels[depot]], "distance_km": lengths[depot],
            "path_nameplate_mva": nominal,
            "nameplate_limiting_groups": [[m["id"] for m in g["members"]] for g in path
                                          if g["thermal_nameplate_mva"] == nominal],
            "path_rating_after_loadingMax_mva": operating, "path": path,
        }

    return {
        "status": "PASS", "grid": "1-MV-rural--0-sw", "external_grid_node": source,
        "energized_switch_classes": len(parent), "eligible_20kv_supply_classes": len(labels),
        "closed_switches": sum(s["cond"] == "1" for s in switches.values()),
        "open_switches": sum(s["cond"] == "0" for s in switches.values()),
        "tie_rule": "ascending original CSV load-bus identifier in Unicode lexical order",
        "near_substation": describe(near), "feeder_end": describe(far),
        "scope": ("Topology and three-phase nameplate on the selected energized paths. "
                  "Finite current ratings converted at nominal voltage; no background headroom, "
                  "security-of-supply guarantee, power-flow calculation or actual depot identity. "
                  "Fixed native switch states and current tap positions. Identical parallel "
                  "transformers share equally under this fixed arrangement. Open tie stubs may "
                  "still draw cable charging current in the later physical model."),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("archive", type=Path, help="pinned 1-MV-rural--0-sw.zip")
    args = ap.parse_args()
    try:
        if args.archive.name != "1-MV-rural--0-sw.zip":
            raise TopologyError("unexpected archive name")
        with ZipFile(args.archive) as archive:
            result = identify(archive)
    except (OSError, BadZipFile, csv.Error, KeyError, ValueError, ArithmeticError) as exc:
        result = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    # All Decimal values are native decimal route lengths, in km.
    print(json.dumps(result, indent=2, allow_nan=False, default=float))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
