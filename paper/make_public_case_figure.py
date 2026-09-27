"""Render a static intake figure from the final public derived JSON only.

No source archive, optimizer, or private workbook is read by this figure script.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "paper" / "figures"
SOURCE = ROOT / "data" / "public" / "sistig_26088190_v1" / "hildenbrand_native_cases.json"
STEM = "public_case_intake"
CAPTION = (
    "Source-timetable intake and modeled energy accounting for Hildenbrand's 37 fixed services. "
    "(A) Each bar spans source departure to arrival on elapsed time from the selected-day boundary; "
    "the 24:00 line preserves the next-day offset rather than wrapping it. (B) Stacked totals "
    "separate common EB-3 modeled service energy from depot-specific modeled pullout and pull-in "
    "energy for 37 one-trip-per-bus paths. These are constructed, replay-checked feasibility "
    "references using one 360 kW connector and terminal recharge by 30:00, not optimized. Energy "
    "is model-derived, not source-observed."
)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "svg.hashsalt": "egg-public-case-intake-20260927",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

ROUTE_A = "#555555"
ROUTE_B = "#eeeeee"
SERVICE_GREY = "#8a8a8a"
MOVEMENT_GREY = "#f2f2f2"
INK = "#222222"
MID_GREY = "#777777"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def display_route_name(value: str) -> str:
    return str(value).split(" (", 1)[0]


def time_label(hour: int) -> str:
    return f"{hour:02d}:00"


def load_input() -> dict:
    document = json.loads(SOURCE.read_text(encoding="utf-8"))
    trips = document["source_data"]["service_trips"]
    if len(trips) != 37 or len({int(t["trip_id"]) for t in trips}) != 37:
        raise ValueError("Expected the final JSON to contain all 37 unique mandatory services")
    variants = document["native_cases"]
    if {int(v["selected_depot_id"]) for v in variants} != {15, 16}:
        raise ValueError("Expected separate single-depot references for source depots 15 and 16")
    for variant in variants:
        witness = variant.get("preflight_witness_and_dimensions", {})
        if (witness.get("classification") != "constructed one-trip-per-bus feasible witness; not optimized"
                or witness.get("replay_ok") is not True
                or witness.get("used_vehicle_count") != 37
                or witness.get("solver_invoked") is not False):
            raise ValueError("Expected the replay-checked, explicitly non-optimized 37-bus reference")
    return document


def make_figure(document: dict):
    source = document["source_data"]
    trips = source["service_trips"]
    routes = sorted(source["routes"], key=lambda r: int(r["bus_route_id"]))
    route_by_id = {int(r["bus_route_id"]): r for r in routes}
    route_palette = [ROUTE_A, ROUTE_B]
    route_hatches = [None, "////"]

    fig = plt.figure(figsize=(8.4, 7.4), layout="constrained")
    grid = fig.add_gridspec(2, 1, height_ratios=[4.8, 1.75], hspace=0.15)
    ax_time = fig.add_subplot(grid[0, 0])
    ax_energy = fig.add_subplot(grid[1, 0])

    # Panel A: one source service per row, grouped by source route.
    ordered_groups: list[tuple[dict, int, list[dict]]] = []
    next_y = 0
    y_positions: list[float] = []
    y_labels: list[str] = []
    group_specs = []
    for route_index, route in enumerate(routes):
        rid = int(route["bus_route_id"])
        group = sorted((t for t in trips if int(t["bus_route_id"]) == rid),
                       key=lambda t: (int(t["dep_time_sec"]), int(t["arr_time_sec"]), int(t["trip_id"])))
        if len(group) != int(route["num_trips"]):
            raise ValueError(f"Route {rid} count does not match its source route metadata")
        ys = list(range(next_y, next_y + len(group)))
        for y, trip in zip(ys, group):
            start_h = int(trip["dep_time_sec"]) / 3600.0
            end_h = int(trip["arr_time_sec"]) / 3600.0
            if end_h <= start_h or end_h > 30:
                raise ValueError(f"Invalid source-offset timetable interval for trip {trip['trip_id']}")
            ax_time.barh(
                y, end_h - start_h, left=start_h, height=0.66,
                color=route_palette[route_index], edgecolor=INK, linewidth=0.55,
                hatch=route_hatches[route_index], zorder=3,
            )
            y_positions.append(y)
            y_labels.append(f"{int(trip['trip_id'])}")
        group_specs.append({
            "route": route,
            "route_index": route_index,
            "first_y": ys[0],
            "last_y": ys[-1],
            "count": len(group),
            "trips": group,
        })
        next_y += len(group) + 2

    # Group labels use the otherwise empty post-24:00 area, retaining individual
    # source trip IDs at the left of the full-width timeline.
    for group in group_specs:
        y_mid = (group["first_y"] + group["last_y"]) / 2
        route_name = display_route_name(group["route"].get("bus_route_name", group["route"]["bus_route_id"]))
        ax_time.text(26.2, y_mid, f"Route {route_name}\n{group['count']} services",
                     ha="center", va="center", color=INK, fontsize=8.5,
                     bbox={"boxstyle": "round,pad=0.25", "facecolor": "white",
                           "edgecolor": "#bbbbbb", "linewidth": 0.6}, zorder=4)

    ax_time.axvspan(24, 30, color="#f7f7f7", zorder=0)
    ax_time.axvline(24, color=MID_GREY, linewidth=1.0, linestyle=(0, (4, 2)), zorder=2)
    ax_time.text(24.22, -0.82, "24:00 · day-offset boundary", ha="left", va="bottom",
                 color=MID_GREY, fontsize=7.4)
    ax_time.set_xlim(0, 30)
    ax_time.set_ylim(next_y - 2.0, -1.3)
    label_rows = {group["first_y"]+i for group in group_specs
                  for i in sorted(set(range(0,group["count"],3)) | {group["count"]-1})}
    ax_time.set_yticks([y for y in y_positions if y in label_rows],
                      [label for y,label in zip(y_positions,y_labels) if y in label_rows])
    ax_time.tick_params(axis="y", labelsize=8.5, length=0, pad=3)
    ax_time.set_xticks(np.arange(0, 31, 6), [time_label(x) for x in range(0, 31, 6)])
    ax_time.tick_params(axis="x", labelsize=9)
    ax_time.set_xlabel("Elapsed time from selected-day boundary (hh:mm; source day offset retained)", labelpad=5)
    ax_time.set_ylabel("Source trip ID (selected labels)", labelpad=7)
    ax_time.set_title("(A) Full mandatory timetable · 37 source services", loc="left", pad=9, fontweight="bold")
    ax_time.grid(axis="x", color="#dedede", linewidth=0.55, zorder=1)
    ax_time.set_axisbelow(True)
    # Panel B: exact aggregate energy fields copied from the JSON preflight.
    variants = sorted(document["native_cases"], key=lambda v: int(v["selected_depot_id"]))
    y = np.arange(len(variants))
    service = np.array([v["preflight_witness_and_dimensions"]["service_energy_total_kwh"]
                        for v in variants], dtype=float)
    movement = np.array([v["preflight_witness_and_dimensions"]["one_trip_per_bus_pullout_pullin_energy_total_kwh"]
                         for v in variants], dtype=float)
    totals = service + movement
    labels = [f"Depot {int(v['selected_depot_id'])}" for v in variants]
    h = 0.52
    ax_energy.barh(y, service, height=h, color=SERVICE_GREY, edgecolor=INK,
                   linewidth=0.7, label="Common modeled service energy", zorder=3)
    ax_energy.barh(y, movement, left=service, height=h, color=MOVEMENT_GREY,
                   edgecolor=INK, linewidth=0.7, hatch="////",
                   label="Modeled pullout + pull-in energy", zorder=3)
    for yy, service_kwh, movement_kwh, total_kwh in zip(y, service, movement, totals):
        ax_energy.text(service_kwh / 2, yy, f"Service\n{service_kwh:,.1f}",
                       ha="center", va="center", color="white", fontsize=8.2, fontweight="bold")
        ax_energy.text(service_kwh + movement_kwh / 2, yy,
                       f"Pullout + pull-in\n{movement_kwh:,.1f}",
                       ha="center", va="center", color=INK, fontsize=8.2,
                       bbox={"facecolor":"white","edgecolor":"none","pad":1.5})
        ax_energy.text(total_kwh + 55, yy, f"{total_kwh:,.1f} kWh",
                       ha="left", va="center", color=INK, fontsize=8.3, fontweight="bold")
    ax_energy.set_yticks(y, labels)
    ax_energy.tick_params(axis="y", labelsize=8.5, length=0)
    ax_energy.set_xlim(0, max(totals) * 1.20)
    ax_energy.set_ylim(1.42, -0.48)
    ax_energy.set_xlabel("Modeled energy summed over the 37 one-trip-per-bus reference paths (kWh)", labelpad=5)
    ax_energy.set_title("(B) Constructed 37-bus feasibility reference, not optimized",
                        loc="left", pad=8, fontweight="bold")
    ax_energy.grid(axis="x", color="#dedede", linewidth=0.55, zorder=1)
    ax_energy.set_axisbelow(True)
    ax_energy.text(0.995, 0.5,
                   "EB-3 modeled; energy not source-observed",
                   transform=ax_energy.transAxes, ha="right", va="top",
                   fontsize=7.5, color=MID_GREY)

    fig.suptitle("Public timetable intake and modeled energy reference", x=0.02, ha="left",
                 fontsize=12, fontweight="bold")
    return fig, {
        "service_energy_kwh": service.tolist(),
        "pullout_pullin_energy_kwh": movement.tolist(),
        "combined_energy_kwh": totals.tolist(),
        "depot_ids": [int(v["selected_depot_id"]) for v in variants],
        "route_groups": [{
            "source_route_id": int(g["route"]["bus_route_id"]),
            "display_name": display_route_name(g["route"].get("bus_route_name", g["route"]["bus_route_id"])),
            "service_count": g["count"],
            "trip_ids_in_plot_order": [int(t["trip_id"]) for t in g["trips"]],
        } for g in group_specs],
    }


def write_provenance(document: dict, figure_data: dict) -> None:
    variants = {int(v["selected_depot_id"]): v for v in document["native_cases"]}
    input_hash = sha256(SOURCE)
    output_hashes = {f"{STEM}.{ext}": sha256(FIG_DIR / f"{STEM}.{ext}")
                     for ext in ("png", "pdf", "svg")}
    provenance = {
        "title": "Public timetable intake and modeled energy reference",
        "caption": CAPTION,
        "source": {
            "dataset_title": document["dataset"]["title"],
            "dataset_doi": document["dataset"]["doi"],
            "license": document["dataset"]["license"],
            "source_json_path": "data/public/sistig_26088190_v1/hildenbrand_native_cases.json",
            "source_json_sha256": input_hash,
            "source_archive_included_or_read": False,
            "source_data_used": "Final derived public JSON only; no workbook, archive, publisher solution, or optimizer read.",
        },
        "figure_script": {
            "path": "paper/make_public_case_figure.py",
            "sha256": sha256(Path(__file__).resolve()),
        },
        "outputs": output_hashes,
        "population": {
            "mandatory_service_count": len(document["source_data"]["service_trips"]),
            "unique_source_trip_ids": len({int(t["trip_id"]) for t in document["source_data"]["service_trips"]}),
            "route_groups": figure_data["route_groups"],
            "source_day_type_ids": document["source_data"]["source_day_type_ids"],
            "calendar_date_present": document["source_data"]["calendar_date_present"],
        },
        "time_axis": {
            "unit": "hours elapsed from selected-day boundary",
            "display_range_hours": [0, 30],
            "day_offset_preserved": True,
            "day_offset_boundary_hour": 24,
            "first_departure_sec": min(int(t["dep_time_sec"]) for t in document["source_data"]["service_trips"]),
            "last_arrival_sec": max(int(t["arr_time_sec"]) for t in document["source_data"]["service_trips"]),
            "last_arrival_text_source": next(t["arr_time"] for t in document["source_data"]["service_trips"]
                                               if int(t["arr_time_sec"]) == max(int(x["arr_time_sec"]) for x in document["source_data"]["service_trips"])),
        },
        "energy_accounting_kwh": {
            "values_source": "native_cases[*].preflight_witness_and_dimensions in final derived JSON",
            "source_energy_observed": False,
            "all_aggregates_exactly_as_stored_in_json": True,
            "variants": [{
                "source_depot_id": depot,
                "reference_classification": variants[depot]["preflight_witness_and_dimensions"]["classification"],
                "replay_ok": variants[depot]["preflight_witness_and_dimensions"]["replay_ok"],
                "used_vehicle_count": variants[depot]["preflight_witness_and_dimensions"]["used_vehicle_count"],
                "service_energy_total": variants[depot]["preflight_witness_and_dimensions"]["service_energy_total_kwh"],
                "pullout_pullin_energy_total": variants[depot]["preflight_witness_and_dimensions"]["one_trip_per_bus_pullout_pullin_energy_total_kwh"],
                "combined_reference_energy_total": variants[depot]["preflight_witness_and_dimensions"]["one_trip_per_bus_total_battery_energy_kwh"],
                "maximum_one_trip_bus_energy": variants[depot]["preflight_witness_and_dimensions"]["maximum_one_trip_bus_energy_kwh"],
                "latest_pullin_arrival_min": variants[depot]["preflight_witness_and_dimensions"]["latest_pullin_arrival_min"],
                "terminal_charge_complete_min": variants[depot]["preflight_witness_and_dimensions"]["last_terminal_charge_end_min"],
                "solver_invoked": variants[depot]["preflight_witness_and_dimensions"]["solver_invoked"],
            } for depot in figure_data["depot_ids"]],
            "vehicle_concept": document["modeling_assumptions"]["vehicle_concept"],
        },
        "rendering": {
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "formats": ["png", "pdf", "svg"],
            "grayscale_friendly": True,
            "solver_invoked": False,
        },
        "interpretation_limits": [
            "The two single-depot variants restrict a source two-depot dataset; they are not the source model.",
            "The one-trip-per-bus schedules are constructive feasibility references, not optimized fleet schedules.",
            "Energy values use declared EB-3 modeling assumptions and are not measured or source-observed energy.",
            "The source calendar date is absent; the encoded day offset is retained on the elapsed-time axis.",
        ],
    }
    (FIG_DIR / "public_case_provenance.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    document = load_input()
    fig, figure_data = make_figure(document)
    fig.savefig(FIG_DIR / f"{STEM}.png", dpi=320, bbox_inches="tight",
                metadata={"Software": "Matplotlib", "Title": "Public timetable intake and modeled energy reference"})
    fig.savefig(FIG_DIR / f"{STEM}.pdf", bbox_inches="tight",
                metadata={"Creator": "Matplotlib", "Title": "Public timetable intake and modeled energy reference",
                          "CreationDate": None, "ModDate": None})
    fig.savefig(FIG_DIR / f"{STEM}.svg", bbox_inches="tight", metadata={"Title": "Public timetable intake and modeled energy reference"})
    plt.close(fig)
    write_provenance(document, figure_data)
    print(json.dumps({
        "outputs": [str(FIG_DIR / f"{STEM}.{ext}") for ext in ("png", "pdf", "svg")],
        "provenance": str(FIG_DIR / "public_case_provenance.json"),
        "source_json_sha256": sha256(SOURCE),
        "population": len(document["source_data"]["service_trips"]),
        "energy_aggregates_kwh": {
            "depot15": figure_data["combined_energy_kwh"][0],
            "depot16": figure_data["combined_energy_kwh"][1],
        },
        "solver_invoked": False,
    }, indent=2))


if __name__ == "__main__":
    main()
