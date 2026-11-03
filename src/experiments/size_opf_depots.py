"""Translate native feeder ratings into whole chargers and serviceable fleet loads.

This engineering calculation uses equipment and duty requirements only. It does
not evaluate prices, network feasibility, or any scientific outcome.
"""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from egglab.two_peak import ChargeWindow, TwoPeakDepot


def size_path(site, fraction):
    rating = site["path_nameplate_mva"]
    charger_kw = 125
    plugs = max(1, math.floor(1000 * rating * fraction / charger_kw + 0.5))
    connection_kw = plugs * charger_kw
    per_batch = (4 * plugs + 4) // 5  # ceil(0.8 * plugs)
    window = ChargeWindow(1, plugs, charger_kw, connection_kw)
    # Homogeneous services use 140 and 90 battery kWh. A 350-kWh nameplate
    # with 30 kWh reserved leaves 320 usable. The fee is unused by layers().
    fleet = TwoPeakDepot(per_batch, per_batch, 140, 90, 320, 1, window, window,
                         efficiency="0.95")
    layers = fleet.layers()
    row = dict(node=site["node"], target_fraction=fraction, path_mva=rating,
               chargers=plugs, site_mw=connection_kw / 1000,
               nameplate_fraction=connection_kw / (1000 * rating),
               services_per_batch=per_batch, feasible_counts=len(layers))
    if not layers:
        return dict(**row, status="no_feasible_count")
    low = min(layers, key=lambda l: l.early_min_kwh)
    high = max(layers, key=lambda l: l.early_max_kwh)
    for layer, energy in ((low, low.early_min_kwh), (high, high.early_max_kwh)):
        witness = fleet.service_witness(layer.pairs, energy)
        if (len(witness) != layer.buses or sum(w[2] for w in witness) != energy
                or sum(w[3] for w in witness) != fleet.total_grid_kwh - energy):
            raise ValueError("reconstructed endpoint witness does not match the layer")
    # One-hour windows: AC kWh / 1000 gives average MW. Within each window
    # the exact shared-plug construction can sustain that power continuously.
    early = [float(low.early_min_kwh / 1000), float(high.early_max_kwh / 1000)]
    late = [float((fleet.total_grid_kwh - x) / 1000)
            for x in (high.early_max_kwh, low.early_min_kwh)]
    return dict(**row, status="fleet_endpoints_verified",
                bus_count_range=[min(l.buses for l in layers), max(l.buses for l in layers)],
                early_mw_range=early, terminal_mw_range=late,
                max_fleet_mw_fraction=max(early[1], late[1]) / rating)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path)
    sites = json.loads(parser.parse_args().paths.read_text())
    if sites.get("status") != "PASS":
        raise ValueError("sizing requires admitted native path ratings")
    rows = [size_path(sites[placement], target) for placement in
            ("near_substation", "feeder_end") for target in (0.10, 0.40, 0.80)]
    print(json.dumps(rows, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
