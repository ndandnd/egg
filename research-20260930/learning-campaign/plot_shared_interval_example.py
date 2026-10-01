#!/usr/bin/env python3
"""Plot the saved, independently replayed 2016 learned repair plan."""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator, FuncFormatter


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from egglab import native_recharge as nr

ATTEMPT = ROOT / "result/learning_repair/20260930-shared-interval-attempt1"
STAGE2 = ROOT / "result/learning_campaign/20260930-stage2-attempt1"
CASE_NAME = "learning_s2016_n20"
MODE = "cost_learned"
CELL = ATTEMPT / CASE_NAME / "state0" / MODE
REPAIR_PATH = CELL / "repair.json"
RESULT_PATH = CELL / "result.json"
REPLAY_PATH = CELL / "independent_replay.json"
ATTEMPT_FROZEN_PATH = ATTEMPT / "frozen.json"
CASE_FROZEN_PATH = STAGE2 / "frozen.json"
OUT_DIR = Path(__file__).resolve().parent / "figures"
PNG_PATH = OUT_DIR / "shared_interval_2016_learned.png"
SVG_PATH = OUT_DIR / "shared_interval_2016_learned.svg"

BUS_COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7")
CHARGE_FACE = "#FFF2CC"
CAP_COLOR = "#858585"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clock_label(hour: float, _position: float) -> str:
    total_minutes = int(round(hour * 60))
    day = total_minutes // (24 * 60)
    clock_hour = (total_minutes // 60) % 24
    suffix = " +1d" if day else ""
    return f"{clock_hour:02d}:{total_minutes % 60:02d}{suffix}"


def main() -> None:
    repair_doc = json.loads(REPAIR_PATH.read_text(encoding="utf-8"))
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    replay_doc = json.loads(REPLAY_PATH.read_text(encoding="utf-8"))
    attempt_frozen = json.loads(ATTEMPT_FROZEN_PATH.read_text(encoding="utf-8"))
    stage2_frozen = json.loads(CASE_FROZEN_PATH.read_text(encoding="utf-8"))

    repair = repair_doc["result"]
    plan = repair["plan"]
    case_row = stage2_frozen["design"]["groups"][CASE_NAME]
    case = case_row["case"]
    replay = replay_doc["replay"]

    case_identity = case_row["case_identity"]
    market_identity = case_row["market_identities"]["target"]
    plan_hash = result["candidate_plan_hash"]
    objective_exact = result["candidate_objective_exact"]
    objective = float(Fraction(objective_exact))

    if case.get("name") != CASE_NAME or case_identity != repair["case_identity"]:
        raise ValueError("Frozen case identity does not match the saved repair")
    if market_identity != repair["market_identity"]:
        raise ValueError("Frozen target market does not match the saved repair")
    if result.get("candidate_kind") != "repaired" or result.get("repair_status") != "replayed":
        raise ValueError("Selected result is not a replayed repair")
    if nr.digest(plan) != plan_hash:
        raise ValueError("Saved plan digest does not match the selected candidate hash")
    if not replay.get("replay_ok"):
        raise ValueError("Saved independent replay did not pass")
    if (replay_doc.get("plan_hash") != plan_hash
            or replay_doc.get("objective_exact") != objective_exact):
        raise ValueError("Result and independent replay plan/cost differ")
    if attempt_frozen["design"]["stage2_input_hashes"]["frozen.json"] != sha256(CASE_FROZEN_PATH):
        raise ValueError("Frozen stage-2 case hash differs from the attempt pin")
    if len(plan["vehicles"]) != 4 or len(case["trips"]) != 20:
        raise ValueError("Expected the selected 20-service, four-bus development case")

    trips = {trip["id"]: trip for trip in case["trips"]}
    vehicle_by_trip: dict[str, int] = {}
    routes_by_vehicle: dict[int, dict] = {}
    for vehicle in plan["vehicles"]:
        vehicle_id = int(vehicle["vehicle"])
        routes_by_vehicle[vehicle_id] = vehicle
        for trip_id in vehicle["trips"]:
            if trip_id in vehicle_by_trip:
                raise ValueError(f"Trip assigned to multiple vehicles: {trip_id}")
            vehicle_by_trip[trip_id] = vehicle_id
    if set(vehicle_by_trip) != set(trips):
        raise ValueError("Plan does not assign each frozen service exactly once")

    charges = []
    for segment in plan["charges"]:
        grid_kwh = float(segment["grid_kwh"])
        if grid_kwh <= 1e-10:
            continue
        start_min = float(segment["start_min"])
        end_min = float(segment["end_min"])
        if end_min <= start_min:
            raise ValueError("Nonpositive serialized charging segment duration")
        vehicle_id = int(segment["vehicle"])
        movement = segment["movement"]
        if (vehicle_id not in routes_by_vehicle
                or movement not in routes_by_vehicle[vehicle_id]["movements"]):
            raise ValueError("Charging segment is not attached to its saved depot movement")
        charges.append({
            "vehicle": vehicle_id,
            "movement": movement,
            "start_min": start_min,
            "end_min": end_min,
            "grid_kwh": grid_kwh,
            "power_kw": grid_kwh / ((end_min - start_min) / 60.0),
            "connector": segment.get("connector"),
        })
    if not charges:
        raise ValueError("Saved repaired plan has no positive charging segments")

    # The frozen 2016 case has one connector. Verify its serialized charge
    # segments do not overlap before treating their bus-colored powers as the
    # aggregate station load.
    resources = case["resources"]
    if len(resources) != 1 or int(resources[0]["connectors"]) != 1:
        raise ValueError("This figure expects the frozen single-connector case")
    resource = resources[0]
    available_kw = min(float(resource["per_bus_kw"]), float(resource["grid_kw"]))
    ordered_charges = sorted(charges, key=lambda item: (item["start_min"], item["end_min"]))
    for before, after in zip(ordered_charges, ordered_charges[1:]):
        if after["start_min"] < before["end_min"] - 1e-9:
            raise ValueError("Serialized charge segments overlap on the shared connector")
    if max(item["power_kw"] for item in charges) > available_kw + 1e-6:
        raise ValueError("Serialized charging power exceeds available per-bus/grid power")

    # Show both active windows at useful scale. The inactive interval is a
    # true broken axis, not compressed/interpolated data: every serialized
    # service and positive charge segment must fit wholly in one window.
    time_windows = ((6.0, 11.5), (21.5, 26.0))
    x_min = min(window[0] for window in time_windows)
    x_max = max(window[1] for window in time_windows)

    def owning_window(start_hour: float, end_hour: float) -> int:
        hits = [i for i, (left, right) in enumerate(time_windows)
                if start_hour >= left - 1e-9 and end_hour <= right + 1e-9]
        if len(hits) != 1:
            raise ValueError(
                f"Actual interval {start_hour:.3f}-{end_hour:.3f}h is outside or crosses the displayed windows"
            )
        return hits[0]

    for trip in trips.values():
        owning_window(float(trip["start_min"]) / 60.0, float(trip["end_min"]) / 60.0)
    for charge in charges:
        owning_window(charge["start_min"] / 60.0, charge["end_min"] / 60.0)

    event_hours = {x_min, x_max}
    for charge in charges:
        event_hours.add(charge["start_min"] / 60.0)
        event_hours.add(charge["end_min"] / 60.0)
    for row in resources:
        event_hours.add(max(x_min, float(row["start_min"]) / 60.0))
        event_hours.add(min(x_max, float(row["end_min"]) / 60.0))
    edges = sorted(value for value in event_hours if x_min - 1e-12 <= value <= x_max + 1e-12)

    vehicle_ids = sorted(routes_by_vehicle)
    profiles: dict[int, list[float]] = {vehicle_id: [] for vehicle_id in vehicle_ids}
    capacity_profile: list[float] = []
    for left, right in zip(edges, edges[1:]):
        middle_min = (left + right) * 30.0
        for vehicle_id in vehicle_ids:
            power = sum(
                charge["power_kw"] for charge in charges
                if charge["vehicle"] == vehicle_id
                and charge["start_min"] <= middle_min < charge["end_min"]
            )
            profiles[vehicle_id].append(power)
        capacity = sum(
            min(float(row["per_bus_kw"]), float(row["grid_kw"]))
            * int(row["connectors"])
            for row in resources
            if float(row["start_min"]) <= middle_min < float(row["end_min"])
        )
        capacity_profile.append(capacity)
    total_profile = [sum(profiles[v][i] for v in vehicle_ids)
                     for i in range(len(edges) - 1)]
    if any(total > cap + 1e-6 for total, cap in zip(total_profile, capacity_profile)):
        raise ValueError("Aggregate serialized load exceeds shared charger capacity")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(
        2, 2, figsize=(14.0, 8.3), sharey="row",
        gridspec_kw={"height_ratios": [1.2, 1.0], "width_ratios": [1.18, 1.0],
                     "wspace": 0.11, "hspace": 0.31},
        facecolor="white",
    )
    fig.patch.set_facecolor("white")
    ax_service_morning, ax_service_overnight = axes[0]
    ax_power_morning, ax_power_overnight = axes[1]
    service_axes = (ax_service_morning, ax_service_overnight)
    power_axes = (ax_power_morning, ax_power_overnight)

    title = "Development example: 20 services, 4 buses"
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.982, color="#20252B")
    fig.text(
        0.5, 0.942,
        f"2016 learned repair · {objective:.2f} cost units · physical replay passed · cover optimality gap open",
        ha="center", va="center", fontsize=10.5, color="#41484F",
    )

    # Shared figure-level legend stays above the data panels.
    legend_handles = [
        Patch(facecolor=BUS_COLORS[index % len(BUS_COLORS)], edgecolor="white",
              alpha=0.9, label=f"Bus {vehicle_id + 1} service/power")
        for index, vehicle_id in enumerate(vehicle_ids)
    ]
    legend_handles.extend([
        Patch(facecolor=CHARGE_FACE, edgecolor="#7A5B00", hatch="///", label="Depot charge"),
        Line2D([0], [0], color="#24292E", linewidth=1.4, label="Aggregate actual"),
        Line2D([0], [0], color=CAP_COLOR, linestyle="--", linewidth=1.6,
               label="Available power cap"),
    ])
    fig.legend(
        handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, 0.925),
        ncol=8, frameon=False, fontsize=8.1, handlelength=1.8,
        columnspacing=1.0, handletextpad=0.45,
    )

    for index, vehicle_id in enumerate(vehicle_ids):
        row_y = float(index)
        vehicle = routes_by_vehicle[vehicle_id]
        for trip_id in vehicle["trips"]:
            trip = trips[trip_id]
            start = float(trip["start_min"]) / 60.0
            duration = (float(trip["end_min"]) - float(trip["start_min"])) / 60.0
            window_index = owning_window(start, start + duration)
            ax_service = service_axes[window_index]
            color = BUS_COLORS[index % len(BUS_COLORS)]
            ax_service.broken_barh(
                [(start, duration)], (row_y - 0.23, 0.46),
                facecolors=color, edgecolors="white", linewidth=0.8, zorder=3,
            )
            ax_service.text(
                start + duration / 2.0, row_y, trip_id,
                ha="center", va="center", fontsize=6.8, color="white",
                fontweight="bold", zorder=4, clip_on=True,
            )
        for charge in charges:
            if charge["vehicle"] != vehicle_id:
                continue
            start = charge["start_min"] / 60.0
            duration = (charge["end_min"] - charge["start_min"]) / 60.0
            window_index = owning_window(start, start + duration)
            ax_service = service_axes[window_index]
            ax_service.broken_barh(
                [(start, duration)], (row_y + 0.30, 0.15),
                facecolors=CHARGE_FACE, edgecolors=color, linewidth=1.0,
                hatch="///", zorder=4,
            )

    service_titles = ("Service + charging · 06:00–11:30",
                      "Service + charging · 21:30–02:00 (+1 day)")
    for index, ax_service in enumerate(service_axes):
        ax_service.set_title(service_titles[index], loc="left", fontsize=10.2,
                             color="#20252B", pad=7)
        ax_service.set_yticks(list(range(len(vehicle_ids))))
        ax_service.set_yticklabels([f"Bus {v + 1}" for v in vehicle_ids], fontsize=9)
        ax_service.tick_params(axis="y", length=0, pad=8)
        # Extra range keeps the final bus's outlined charging rail fully visible.
        ax_service.set_ylim(len(vehicle_ids) - 0.15, -0.58)
        ax_service.set_xlim(*time_windows[index])
        ax_service.xaxis.set_major_locator(MultipleLocator(1.0))
        ax_service.xaxis.set_minor_locator(MultipleLocator(0.5))
        ax_service.xaxis.set_major_formatter(FuncFormatter(clock_label))
        ax_service.grid(axis="x", which="major", color="#D8DDE2", linewidth=0.7)
        ax_service.grid(axis="x", which="minor", color="#EDF0F2", linewidth=0.45)
        ax_service.set_axisbelow(True)

    for index, ax_power in enumerate(power_axes):
        for bus_index, vehicle_id in enumerate(vehicle_ids):
            color = BUS_COLORS[bus_index % len(BUS_COLORS)]
            ax_power.stairs(
                profiles[vehicle_id], edges, baseline=0, fill=True,
                facecolor=color, edgecolor=color, linewidth=1.15, alpha=0.34,
                zorder=3 + bus_index,
            )
        ax_power.stairs(
            total_profile, edges, baseline=None, color="#24292E", linewidth=1.15,
            zorder=8,
        )
        ax_power.stairs(
            capacity_profile, edges, baseline=None, color=CAP_COLOR,
            linestyle="--", linewidth=1.6, zorder=2,
        )
        ax_power.set_xlim(*time_windows[index])
        ax_power.set_ylim(0, max(100.0, available_kw * 1.12))
        ax_power.xaxis.set_major_locator(MultipleLocator(1.0))
        ax_power.xaxis.set_minor_locator(MultipleLocator(0.5))
        ax_power.xaxis.set_major_formatter(FuncFormatter(clock_label))
        ax_power.yaxis.set_major_locator(MultipleLocator(20.0))
        ax_power.grid(axis="both", which="major", color="#E2E6E9", linewidth=0.65)
        ax_power.grid(axis="x", which="minor", color="#F0F2F4", linewidth=0.4)
        ax_power.set_axisbelow(True)
        ax_power.set_xlabel("Clock time", fontsize=9.5)
    ax_power_morning.set_title("Actual charging power · 06:00–11:30", loc="left",
                               fontsize=10.2, color="#20252B", pad=7)
    ax_power_overnight.set_title("Actual charging power · overnight", loc="left",
                                 fontsize=10.2, color="#20252B", pad=7)
    ax_power_morning.set_ylabel("Power (kW)", fontsize=9)

    overnight_ticks = [22.0, 23.0, 24.0, 26.0]
    overnight_labels = ["22:00", "23:00", "00:00 +1d", "02:00 +1d"]
    for ax in (ax_service_overnight, ax_power_overnight):
        ax.set_xticks(overnight_ticks)
        ax.set_xticklabels(overnight_labels, ha="center")

    # Diagonal marks show the omitted inactive 11:30–21:30 interval in each row.
    break_style = dict(color="#3D454C", linewidth=1.1, clip_on=False, zorder=10)
    diagonal = 0.012
    for ax_left, ax_right in zip((ax_service_morning, ax_power_morning),
                                 (ax_service_overnight, ax_power_overnight)):
        for y in (0, 1):
            ax_left.plot((1 - diagonal, 1 + diagonal),
                         (y - diagonal, y + diagonal), transform=ax_left.transAxes,
                         **break_style)
            ax_right.plot((-diagonal, diagonal),
                          (y - diagonal, y + diagonal), transform=ax_right.transAxes,
                          **break_style)

    # The final 02:00 tick sits exactly at the overnight window boundary;
    # right-align it so its next-day marker stays inside the figure canvas.
    fig.canvas.draw()
    for ax in (ax_service_overnight, ax_power_overnight):
        tick_labels = ax.get_xticklabels()
        if tick_labels:
            tick_labels[-1].set_ha("right")

    fig.text(
        0.5, 0.055,
        "Deadhead legs omitted; inactive midday hours omitted. Clock labels marked +1d denote the next day.",
        ha="center", va="center", fontsize=8.5, color="#525B63",
    )
    fig.subplots_adjust(left=0.095, right=0.985, top=0.835, bottom=0.13)

    metadata = {
        "case": CASE_NAME,
        "mode": MODE,
        "case_identity": case_identity,
        "market_identity": market_identity,
        "candidate_plan_hash": plan_hash,
        "objective_exact": objective_exact,
        "objective_cost_units": objective,
        "independent_replay_ok": bool(replay["replay_ok"]),
        "repair_json": str(REPAIR_PATH.relative_to(ROOT)),
        "repair_json_sha256": sha256(REPAIR_PATH),
        "result_json": str(RESULT_PATH.relative_to(ROOT)),
        "result_json_sha256": sha256(RESULT_PATH),
        "independent_replay_json": str(REPLAY_PATH.relative_to(ROOT)),
        "independent_replay_json_sha256": sha256(REPLAY_PATH),
        "stage2_frozen_case_json": str(CASE_FROZEN_PATH.relative_to(ROOT)),
        "stage2_frozen_case_sha256": sha256(CASE_FROZEN_PATH),
        "attempt_frozen_json": str(ATTEMPT_FROZEN_PATH.relative_to(ROOT)),
        "attempt_frozen_json_sha256": sha256(ATTEMPT_FROZEN_PATH),
        "stage2_frozen_sha256_pin_matches": True,
        "positive_charge_segments": len(charges),
        "charge_rate_formula": "grid_kwh / ((end_min - start_min) / 60)",
        "shared_connector_segments_nonoverlapping": True,
        "available_power_kw": available_kw,
        "time_windows_hours": [list(window) for window in time_windows],
        "inactive_midday_hours_omitted": True,
        "plan_digest_matches_candidate_hash": True,
    }
    description = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    fig.savefig(PNG_PATH, dpi=220, facecolor="white",
                metadata={"Title": title, "Description": description})
    fig.savefig(SVG_PATH, facecolor="white",
                metadata={"Title": title, "Creator": "Matplotlib", "Description": description})
    plt.close(fig)
    print(json.dumps({"png": str(PNG_PATH), "svg": str(SVG_PATH), **metadata}, sort_keys=True))


if __name__ == "__main__":
    main()
