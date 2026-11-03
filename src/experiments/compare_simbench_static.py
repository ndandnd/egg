"""Compare one fixed, no-depot conic operating point to an independently saved AC solution."""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from egglab.radial_opf import solve_radial
from egglab.simbench_radial import read_simbench_radial


def compare(model, point, ac):
    # Error tolerances use physical units. A numerical match cannot override
    # the model's physical gate or make a violated native limit feasible.
    errors = {"voltage_pu": 0., "terminal_mw": 0., "terminal_mvar": 0., "terminal_ka": 0.}
    missing = []

    def check(key, value, target, tag):
        if target is None or not math.isfinite(target) or not math.isfinite(value):
            missing.append(tag)
        else:
            errors[key] = max(errors[key], abs(value - target))

    bus_voltage = ac["voltage_pu"]
    seen_classes = set()
    for name, i in model["bus_index"].items():
        if bus_voltage.get(name) is None:
            continue  # converter can remove a switch-terminal alias
        check("voltage_pu", point["voltage_pu"][i], bus_voltage[name], name)
        seen_classes.add(i)
    uncovered = set(range(len(point["voltage_pu"]))) - seen_classes
    by_id = ac["lines"] | ac["transformers"]
    native_ids = {member for group in model["branch_members"] for member in group}
    missing.extend(sorted(set(by_id) ^ native_ids))
    terminal_count = 0
    peak_loading_pct = 0.
    for edge, group in enumerate(model["branch_members"]):
        parent, child = model["solver"]["parent"][edge], edge + 1
        for member in group:
            if member not in by_id:
                continue
            row = by_id[member]
            if row["loading_percent"] is None or not math.isfinite(row["loading_percent"]):
                missing.append(member + ".loading")
            else:
                peak_loading_pct = max(peak_loading_pct, row["loading_percent"])
            for side, node in zip(("a", "b"), model["branch_terminal_nodes"][member]):
                i = model["bus_index"][node]
                if i not in (parent, child):
                    raise ValueError(f"{member} disagrees with the oriented topology")
                send = i == parent
                real = point["p_send_mw" if send else "p_to_mw"][edge] / len(group)
                reactive = point["q_send_mvar" if send else "q_to_mvar"][edge] / len(group)
                check("terminal_mw", real, row[f"p_{side}_mw"], member)
                check("terminal_mvar", reactive, row[f"q_{side}_mvar"], member)
                nominal = model["bus_kv"][node]
                amp = point["current_from_pu" if send else "current_to_pu"][edge]
                amp *= model["solver"]["base_mva"] / (len(group) * math.sqrt(3) * nominal)
                check("terminal_ka", amp, row.get(f"i_{side}_ka"), member)
                terminal_count += 1
    for key in ("import_mw", "import_mvar", "loss_mw"):
        errors[key] = 0.
        check(key, point[key], ac[key], key)
    return dict(max_abs_discrepancies=errors, unmatched_or_nonfinite=missing,
                covered_voltage_classes=len(seen_classes), total_voltage_classes=len(point["voltage_pu"]),
                uncovered_voltage_classes=[model["bus_classes"][i] for i in sorted(uncovered)],
                native_assets=len(native_ids), matched_terminal_count=terminal_count,
                peak_ac_loading_percent=peak_loading_pct,
                comparison_pass=not missing and not uncovered and all(x <= 1e-4 for x in errors.values()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("ac_reference", type=Path)
    parser.add_argument("--save-point", type=Path, help="Retain raw conic arrays for diagnosis before comparison")
    args = parser.parse_args()
    ac = json.loads(args.ac_reference.read_text())
    model = read_simbench_radial(args.archive)
    point = solve_radial(**model["solver"], price=50., hours=1.)
    if args.save_point is not None:
        with args.save_point.open("x") as output:
            json.dump(point, output, allow_nan=False)
    keys = ("status", "import_mw", "import_mvar", "loss_mw", "cone_abs", "cone_rel", "cone_rel_floor",
            "balance_max_pu", "voltage_eq_max_pu", "limit_violation_max_pu", "point_ac_residuals_pass")
    result = dict(scope="Static CSV injections, no fleet, fixed taps, positive linear procurement.",
                  tolerance_by_unit=1e-4, solver={k: point[k] for k in keys},
                  ac={k: ac[k] for k in ("import_mw", "import_mvar", "loss_mw", "converged",
                                          "within_native_limits")})
    if point["status"] in ("optimal", "optimal_inaccurate") and point["voltage_pu"] is not None:
        result.update(compare(model, point, ac))
    result["qualified"] = (result.get("comparison_pass") is True and point["status"] == "optimal"
                           and point["point_ac_residuals_pass"] is True
                           and ac.get("converged") is True and ac.get("within_native_limits") is True)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
