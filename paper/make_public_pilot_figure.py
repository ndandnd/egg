"""Display both archived public pilot witnesses, with no optimizer or repair."""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = ROOT / "result/sistig_pricing/20260927-grb-job557543-attempt1"
FIG = ROOT / "paper/figures"
STEM = "public_pilot_witnesses"
COLORS = ["#21618c", "#b35416"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "svg.hashsalt": "egg-public-pilot-witnesses-20260927",
                     "pdf.fonttype": 42})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((ATTEMPT / "MANIFEST.json").read_text())["files"]
    fig, axes = plt.subplots(2, 2, figsize=(9.3, 5.5),
                             gridspec_kw={"width_ratios": [1.32, 1]},
                             layout="constrained")
    sources, diagnostics = {}, []
    for row, depot in enumerate((15, 16)):
        base = f"depot_{depot}_flat"
        for name in (f"{base}/input.json", f"{base}/result.json"):
            if sha(ATTEMPT / name) != manifest[name]["sha256"]:
                raise ValueError("Archived input or result differs from manifest")
            sources[name] = sha(ATTEMPT / name)
        payload = json.loads((ATTEMPT / base / "input.json").read_text())
        result = json.loads((ATTEMPT / base / "result.json").read_text())["result"]
        case = payload["case"]
        plan = result["plan"]
        if result["status"] != "bounded" or len(plan["vehicles"]) != 2 or not plan["replay"]["replay_ok"]:
            raise ValueError("Expected audited bounded two-bus witness")
        trips = {t["id"]: t for t in case["trips"]}
        movements = {m["id"]: m for m in case["movements"]}
        covered = [t for v in plan["vehicles"] for t in v["trips"]]
        if len(covered) != 37 or set(covered) != set(trips):
            raise ValueError("Incomplete or duplicate service coverage")
        ax, soc = axes[row]
        for v in plan["vehicles"]:
            k = v["vehicle"]
            for mid in v["movements"]:
                for leg in movements[mid]["legs"]:
                    left, right = leg["depart_min"] / 60, leg["arrive_min"] / 60
                    if right > left:
                        ax.barh(2-k, right-left, left=left, height=.43,
                                color="#d0d0d0", edgecolor="#666666", linewidth=.35)
            for tid in v["trips"]:
                t = trips[tid]
                ax.barh(2-k, (t["end_min"]-t["start_min"])/60,
                        left=t["start_min"]/60, height=.6, color=COLORS[k],
                        edgecolor="white", linewidth=.35)
        for charge in plan["charges"]:
            ax.barh(0, (charge["end_min"]-charge["start_min"])/60,
                    left=charge["start_min"]/60, height=.6,
                    color=COLORS[charge["vehicle"]], hatch="////",
                    edgecolor="white", linewidth=.3)
        for k, trajectory in enumerate(plan["replay"]["soc_trajectories"]):
            for kind, marker in (("charge", "^"), ("other", "o")):
                points = [x for x in trajectory if (x["kind"] == "charge") == (kind == "charge")]
                soc.scatter([x["time_min"]/60 for x in points], [x["soc_kwh"] for x in points],
                            color=COLORS[k], marker=marker, s=13 if marker == "o" else 25,
                            linewidths=.35, edgecolors="white", zorder=3)
        ax.set_yticks([2, 1, 0], ["Bus 1", "Bus 2", "Connector"])
        ax.set_ylim(-.6, 2.75)
        ax.set_title(f"{'A' if row == 0 else 'C'}  Depot {depot}: complete returned schedule", loc="left", fontsize=10)
        soc.set_title(f"{'B' if row == 0 else 'D'}  Recorded battery events", loc="left", fontsize=10)
        soc.axhline(400, color="#555555", linestyle="--", linewidth=.6)
        soc.axhline(0, color="#555555", linewidth=.6)
        soc.set_ylim(-12, 419)
        soc.set_yticks([0, 100, 200, 300, 400])
        soc.set_ylabel("Stored energy (kWh)")
        for a in (ax, soc):
            a.set_xlim(0, 30)
            a.set_xticks([0, 6, 12, 18, 24, 30])
            a.axvline(24, color="#777777", linestyle=":", linewidth=.7, zorder=0)
            a.set_xlabel("Hours from selected-day boundary")
        # Show complete initial/deadline markers instead of clipping at axes.
        soc.set_xlim(-.3, 30.3)
        diagnostics.append({"depot": depot, "service_bars": len(covered),
                            "charge_sessions": len(plan["charges"]),
                            "soc_points": sum(map(len, plan["replay"]["soc_trajectories"])),
                            "status": result["status"], "lower": result["lower"], "upper": result["upper"]})
    axes[0, 0].legend(handles=[Patch(color=COLORS[0], label="Bus 1 service"),
                      Patch(color=COLORS[1], label="Bus 2 service"),
                      Patch(color="#d0d0d0", label="Movement / modeled wait"),
                      Patch(facecolor="white", edgecolor="#555555", hatch="////", label="Charging")],
                      loc="upper left", bbox_to_anchor=(0, 1.35), ncols=2, frameon=False, fontsize=8)
    axes[0, 1].legend(handles=[Line2D([], [], marker="o", color="none", markerfacecolor="#555555",
                                    markersize=4, label="Service / movement / initial"),
                              Line2D([], [], marker="^", color="none", markerfacecolor="#555555",
                                    markersize=5, label="Charge completion")],
                      loc="upper left", bbox_to_anchor=(0, 1.35), frameon=False, fontsize=8)
    FIG.mkdir(exist_ok=True)
    for extension in ("png", "pdf", "svg"):
        metadata = {"Title": "Audited public timetable pilot witnesses"}
        if extension == "pdf":
            metadata.update(CreationDate=None, ModDate=None)
        fig.savefig(FIG / f"{STEM}.{extension}", dpi=320, bbox_inches="tight", metadata=metadata)
    plt.close(fig)
    svg = FIG / f"{STEM}.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    provenance = {"script_sha256": sha(Path(__file__)), "original_input_result_sha256": sources,
                  "raw_manifest_sha256": sha(ATTEMPT / "MANIFEST.json"),
                  "diagnostics": diagnostics, "optimizer_invoked": False,
                  "matplotlib_version": matplotlib.__version__,
                  "scope": "Both attempt1 incumbents, not optima; event SOC accounting, not a within-leg trajectory",
                  "outputs": {ext: sha(FIG / f"{STEM}.{ext}") for ext in ("png", "pdf", "svg")}}
    (FIG / f"{STEM}_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
