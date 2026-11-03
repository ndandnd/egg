"""Translate the pinned SimBench MV1 archive's static operating point.

Uses a balanced positive-sequence network with the native fixed switch/tap
positions. Negative net demand denotes export. Table units are documented in
SimBench v1 §4.3 (Tables 4.14–4.25). Transformer T-to-pi conversion follows
the equal-leakage-arm convention of pandapower build_branch._wye_delta.
"""
from collections import defaultdict
from decimal import Decimal
from math import isfinite, sqrt
from pathlib import Path
from zipfile import ZipFile

from experiments.identify_simbench_depots import SwitchClasses, positive, read_table, rooted_tree


FIELDS = {
    "Node": "vmR vmMin vmMax vmSetp vaSetp",
    "ExternalNet": "node calc_type",
    "Switch": "nodeA nodeB type cond",
    "Line": "nodeA nodeB type length loadingMax",
    "LineType": "r x b iMax",
    "Transformer": "nodeHV nodeLV type tappos autoTap autoTapSide loadingMax",
    "TransformerType": "sR vmHV vmLV va0 vmImp pCu pFe iNoLoad tapNeutr",
    "Load": "node pLoad qLoad",
    "RES": "node calc_type pRES qRES",
}
# These tables add no device to this static operating point. Do not open them.
METADATA = {"LoadProfile", "RESProfile", "NodePFResult", "StudyCases",
            "Substation", "Measurement", "Coordinates"}


def number(value):
    value = float(value)
    if not isfinite(value):
        raise ValueError("nonfinite SimBench parameter")
    return value


def quadrature(magnitude, real):
    if not 0 <= real <= magnitude:
        raise ValueError("inconsistent transformer current/loss or impedance test")
    return sqrt((magnitude - real) * (magnitude + real))


def transformer_pi(tt, tap_position, base_mva):
    """Return z and per-end y for ONE transformer on the common power base.

    On matched rated voltage bases the T arms have impedance z/2. Eliminating
    the midpoint with excitation admittance y gives series z*(1+z*y/4) and
    each terminal shunt y/(2+z*y/2). Iron loss conducts, magnetization absorbs
    vars. Consistent per-unit voltage bases remove the nominal turns ratio.
    """
    if tap_position != number(tt["tapNeutr"]):
        raise ValueError("non-neutral tap unsupported in this static case")
    sn = positive(tt["sR"], "rated MVA")
    copper = number(tt["pCu"]) / 1000 / sn
    short = number(tt["vmImp"]) / 100
    z = complex(copper, quadrature(short, copper)) * base_mva / sn
    iron = number(tt["pFe"]) / 1000
    no_load = number(tt["iNoLoad"]) * sn / 100
    y = complex(iron, -quadrature(no_load, iron)) / base_mva
    return z * (1 + z*y/4), y / (2 + z*y/2)


def native_topology(tables, base):
    nodes = tables["Node"]
    kv = {n: positive(row["vmR"], "nominal kV") for n, row in nodes.items()}
    sources = list(tables["ExternalNet"].values())
    if len(sources) != 1 or sources[0]["calc_type"] != "vavm":
        raise ValueError("requires one fixed-angle, fixed-voltage external source")
    source = sources[0]["node"]
    switches = SwitchClasses(nodes)
    for s in tables["Switch"].values():
        a, b = s["nodeA"], s["nodeB"]
        if s["type"] not in {"CB", "LBS"} or s["cond"] not in {"0", "1"} or kv[a] != kv[b]:
            raise ValueError(f"unsupported switch or voltage at {s['id']}")
        if s["cond"] == "1":
            switches.close(a, b)
    rep = {n: switches.representative(n) for n in nodes}
    root = rep[source]

    equipment = defaultdict(list)
    for row in tables["Line"].values():
        a, b = row["nodeA"], row["nodeB"]
        if kv[a] != kv[b]:
            raise ValueError(f"{row['id']}: inconsistent line terminal voltages")
        lt = tables["LineType"][row["type"]]
        length = Decimal(row["length"])
        km = positive(length, "line length (km)")
        zbase = kv[a]**2 / base
        z = complex(number(lt["r"]), number(lt["x"])) * km / zbase
        y_half = 1j * number(lt["b"]) * 1e-6 * km * zbase / 2
        equipment[tuple(sorted((rep[a], rep[b])))].append(dict(
            kind="line", id=row["id"], length_km=length, z=z, y_half=y_half,
            thermal_nameplate_mva=sqrt(3)*kv[a]*positive(lt["iMax"], "rated A")/1000,
            loading_max_percent=positive(row["loadingMax"], "line loadingMax"),
        ))
    for row in tables["Transformer"].values():
        tt = tables["TransformerType"][row["type"]]
        hv, lv = row["nodeHV"], row["nodeLV"]
        if (number(tt["vmHV"]), number(tt["vmLV"])) != (kv[hv], kv[lv]) or rep[hv] != root:
            raise ValueError(f"{row['id']}: unsupported base voltages or transformer direction")
        tap = number(row["tappos"])
        z, y_half = transformer_pi(tt, tap, base)
        equipment[tuple(sorted((rep[hv], rep[lv])))].append(dict(
            kind="transformer", id=row["id"], type=row["type"], tap_pos=tap,
            auto_tap=row["autoTap"], auto_tap_side=row["autoTapSide"],
            hv_class=rep[hv], lv_class=rep[lv], length_km=Decimal(0), z=z, y_half=y_half,
            phase=number(tt["va0"]), thermal_nameplate_mva=positive(tt["sR"], "rated MVA"),
            loading_max_percent=positive(row["loadingMax"], "transformer loadingMax"),
        ))
    parents, incoming, _ = rooted_tree(equipment, root)
    if set(parents) != set(rep.values()):
        raise ValueError("disconnected native node class; refusing to discard equipment")
    return source, rep, parents, incoming


def read_simbench_radial(archive_path, base_mva=10.0):
    """Return keyword-ready solve_radial inputs plus reversible bus/asset IDs.

    The caller supplies a pinned archive and chooses the price and interval.
    Fixed native Load/RES maxima used together form a synthetic static case.
    No time-series profiles, control loop or price data are read.
    """
    base = positive(base_mva, "common MVA base")
    with ZipFile(archive_path) as archive:
        names = {Path(m).stem for m in archive.namelist() if m.endswith(".csv")}
        unsupported = names - set(FIELDS) - METADATA
        if unsupported:
            raise ValueError(f"unsupported SimBench table(s): {sorted(unsupported)}")
        tables = {key: read_table(archive, key, ["id", *names.split()])
                  for key, names in FIELDS.items()}
    source, rep, parents, incoming = native_topology(tables, base)
    buses = list(parents)  # rooted_tree inserts children in breadth-first order
    position = {bus: i for i, bus in enumerate(buses)}
    index = {n: position[c] for n, c in rep.items()}
    size = len(buses)
    nodes = tables["Node"]
    solver = {"parent": [position[parents[child]] for child in buses[1:]],
              "p_mw": [0.] * size, "q_mvar": [0.] * size, "base_mva": base,
              "slack_vm_pu": positive(nodes[source]["vmSetp"], "slack voltage"),
              "vmin": [0.] * size, "vmax": [float("inf")] * size}
    for n, row in nodes.items():
        i = index[n]
        solver["vmin"][i] = max(solver["vmin"][i], positive(row["vmMin"], "Vmin"))
        solver["vmax"][i] = min(solver["vmax"][i], positive(row["vmMax"], "Vmax"))
        if solver["vmin"][i] > solver["vmax"][i]:
            raise ValueError(f"incompatible voltage limits on fused class of {n}")

    for device, p, q, sign in (("Load", "pLoad", "qLoad", 1), ("RES", "pRES", "qRES", -1)):
        for row in tables[device].values():
            if device == "RES" and row["calc_type"] != "pq":
                raise ValueError(f"{row['id']}: non-PQ generation requires a control model")
            i = index[row["node"]]
            solver["p_mw"][i] += sign * number(row[p])
            solver["q_mvar"][i] += sign * number(row[q])

    phase_shifts, branch_members = [], []
    for key in ("r", "x", "tap_ratio", "g_from_pu", "b_from_pu", "g_to_pu",
                "b_to_pu", "imax_from_pu", "imax_to_pu"):
        solver[key] = []
    for child in buses[1:]:
        edge = incoming[child]
        members = edge["members"]
        first = members[0]
        # group_edges accepted either one line or electrically identical
        # energized parallel transformers. Their currents divide equally.
        z = first["z"] / len(members)
        y = first["y_half"] * len(members)
        cap = edge["operating_rating_mva"] / base
        solver["r"].append(z.real)
        solver["x"].append(z.imag)
        solver["tap_ratio"].append(1.)  # matched nominal bases and frozen neutral taps
        for end in ("from", "to"):
            solver[f"g_{end}_pu"].append(y.real)
            solver[f"b_{end}_pu"].append(y.imag)
            solver[f"imax_{end}_pu"].append(cap)
        phase_shifts.append(first.get("phase", 0.))
        branch_members.append([m["id"] for m in members])

    terminal_nodes = {}
    for device, first_end, second_end in (("Line", "nodeA", "nodeB"),
                                          ("Transformer", "nodeHV", "nodeLV")):
        for ident, row in tables[device].items():
            if ident in terminal_nodes:
                raise ValueError(f"duplicate branch ID across device types: {ident}")
            terminal_nodes[ident] = (row[first_end], row[second_end])

    return {"solver": solver, "bus_index": index, "bus_classes": buses,
            "bus_kv": {n: number(row["vmR"]) for n, row in nodes.items()},
            "branch_terminal_nodes": terminal_nodes,
            "branch_members": branch_members, "phase_shift_degree": phase_shifts,
            "slack_angle_degree": number(nodes[source]["vaSetp"]), "source_node": source,
            "n_static_loads": len(tables["Load"]), "n_static_res": len(tables["RES"]),
            "scope": ("All native closed-switch classes and cable terminal shunts; "
                      "native neutral tap positions held fixed even for automatic tap changers. "
                      "Angles can be restored with the listed oriented phase shifts on this tree. "
                      "Current ratings apply to both physical terminals on their local voltage bases.")}
