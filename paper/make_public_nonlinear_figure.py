"""Render an independently audited off-protocol secondary diagnostic.

Requires machine audit PASS for numerical evidence and explicit budget FAIL.
Never overwrites an existing figure; never certifies the primary experiment.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = ROOT / "result/sistig_nonlinear/20260927-attempt2"
PUBLIC_MANIFEST = ROOT / "result/sistig_nonlinear/20260927-attempt2-publication/PUBLIC_MANIFEST.json"
FIG = ROOT / "paper/figures"
STEM = "public_nonlinear_evidence"
MANIFEST_SHA = "68032692ea5c5b349115bd6bd64740f0bd799fac9a8a4dcdf09462a844901cf9"
PUBLIC_MANIFEST_SHA = "facff4a3b2d6c38d0ce01e5cdaf0789b080ec30da5e9f621a026145763410137"
FROZEN_SHA = "eb1d9f5dc8b8f7f1561c21dd8f8cad6105f8cfbc272c23b8c8a334e6a626f352"
COMMIT = "e23a653dcd77b6ce02eb0af5e544fea7edab9eca"
PROTOCOL = "sistig-nonlinear-one-cell-20260927-v2"
COLORS = {"planner": "#21618c", "hull": "#ae6f00", "own_price": "#b5493b"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "svg.hashsalt": "egg-public-nonlinear-v2-20260927"})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def q(value):
    need(type(value) in (int, float, str), "Non-numeric stored value")
    return Q(value)


def load_evidence(attempt):
    manifest_path = attempt / "MANIFEST.json"
    need(sha(manifest_path) == MANIFEST_SHA, "Raw manifest hash changed")
    need(sha(PUBLIC_MANIFEST) == PUBLIC_MANIFEST_SHA, "Public-copy manifest hash changed")
    manifest = json.loads(manifest_path.read_text())
    public = json.loads(PUBLIC_MANIFEST.read_text())
    need(manifest.get("protocol") == PROTOCOL, "Manifest protocol changed")
    entries = manifest["files"]
    omitted = public["omitted_files"]
    published = public["unchanged_published_files"]
    need(public["original_manifest_sha256"] == MANIFEST_SHA
         and public["source_commit"] == COMMIT
         and public["raw_attempt"] == "result/sistig_nonlinear/20260927-attempt2"
         and set(omitted) == {"planner/stdout.txt", "hull/stdout.txt", "own_price/stdout.txt"}
         and set(entries) == set(omitted) | set(published)
         and all({k: v[k] for k in ("bytes", "sha256")} == entries[name]
                 for name, v in {**omitted, **published}.items()),
         "Public-copy manifest differs from original raw manifest")
    for name, record in entries.items():
        path = Path(name)
        need(not path.is_absolute() and ".." not in path.parts, "Unsafe manifest path")
        full = attempt / path
        if not full.is_file() and name in omitted:
            continue  # Only the three declared licensing-only banners may be absent.
        need(full.is_file() and full.stat().st_size == record["bytes"]
             and sha(full) == record["sha256"], "Manifest entry changed: " + name)
    actual = {str(path.relative_to(attempt)) for path in attempt.rglob("*") if path.is_file()}
    need(actual - set(entries) <= {"MANIFEST.json", "slurm_wrapper_receipt.json"},
         "Unexpected raw-attempt file")
    wrapper = attempt / "slurm_wrapper_receipt.json"
    receipt_pin = public["postseal_receipts"]["slurm_wrapper_receipt.json"]
    need(wrapper.is_file() and wrapper.stat().st_size == receipt_pin["bytes"]
         and sha(wrapper) == receipt_pin["sha256"], "Postseal wrapper receipt changed")
    need(entries["frozen.json"]["sha256"] == FROZEN_SHA, "Frozen hash changed")
    def read(name):
        need(name in entries, "Unmanifested scientific input: " + name)
        return json.loads((attempt / name).read_text())
    frozen, summary, supervisor = (read(x) for x in (
        "frozen.json", "summary.json", "supervisor_receipt.json"))
    need(frozen["protocol"] == summary["protocol"] == supervisor["protocol"] == PROTOCOL
         and frozen["source_commit"] == COMMIT and frozen["backend"] == "GRB"
         and frozen["case_identity"] == "1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7",
         "Frozen execution identity changed")
    need(frozen["routine_caps"] == {"planner": 240, "hull": 1440, "own_price": 240}
         and frozen["native_wall_caps"] == {"planner": 225, "hull": 1380, "own_price": 225}
         and frozen["total_cap"] == 2040, "Frozen timing identity changed")
    need(summary["complete"] is True and summary["source_hashes_unchanged"] is True
         and summary["frozen_sha256"] == FROZEN_SHA and summary["report"]
         and len(summary["stages"]) == 3 and all(x["pass"] is True for x in summary["stages"])
         and supervisor["returncode"] == 0 and supervisor["outer_timeout"] is False
         and supervisor["source_hashes_unchanged"] is True, "Attempt not complete and source-stable")
    stages = {s: read(f"{s}/result.json") for s in ("planner", "hull", "own_price")}
    for stage, package in stages.items():
        need(package["stage"] == stage and package["frozen_sha256"] == FROZEN_SHA
             and package["assessment"]["status"] == package["result"]["status"],
             "Stage result identity changed: " + stage)
    need([stages[s]["result"]["status"] for s in stages] ==
         ["bounded", "budget_exhausted", "certified"], "Unexpected bounded stage labels")
    return manifest, frozen, summary, stages, read("own_price/input.json")


def reconstruct(frozen, summary, stages, own_input):
    p, h, r = (stages[s]["assessment"] for s in ("planner", "hull", "own_price"))
    d = tuple(q(p[x]) for x in ("lower_exact_stored", "upper_exact_stored"))
    ch = tuple(q(h[x]) for x in ("lower_exact_stored", "upper_exact_stored"))
    response = tuple(q(r[x]) for x in ("lower_exact_stored", "upper_exact_stored"))
    need(all(lo <= hi for lo, hi in (d, ch, response)), "Reversed objective interval")
    report = summary["report"]
    gap = (d[0] - ch[1], d[1] - ch[0])
    need(gap == tuple(map(q, report["gap_interval_exact_stored"])), "Gap endpoints changed")
    resolution, guard = q(report["resolution"]), q(report["negative_guard"])
    need(resolution == 5 and guard == Q(1, 10000), "Classification policy changed")
    need(gap[0] <= gap[1] and gap[1] >= -guard, "Gap consistency guard failed")
    classification = ("resolvably_positive_above_five" if gap[0] > resolution else
                      "gap_at_most_five_under_declared_numerical_policy"
                      if gap[1] <= resolution and gap[0] >= -guard else "unresolved_at_five")
    need(classification == report["gap_classification"], "Gap classification changed")
    raw = (p["replay"]["load"], stages["hull"]["result"]["mixture"]["load_exact"],
           r["replay"]["load"])
    loads = [list(map(q, row)) for row in raw]
    need(all(len(row) == 30 and all(x >= 0 for x in row) for row in loads),
         "Missing/nonphysical 30-hour load")
    need(ch[0] == q(stages["hull"]["result"]["lower_certificate"]["lower"])
         and ch[1] == q(stages["hull"]["result"]["mixture"]["upper"]),
         "Hull endpoints differ from global certificate or replayed mixture")
    prices = report["own_price_vector"]
    market = frozen["market"]
    need(prices == own_input["prices"] and len(prices) == 30
         and prices == [float(a + b*e) for a, b, e in zip(market["a"], market["b"], raw[0])],
         "Own-price vector differs from planner load")
    own_value = q(p["replay"]["ops_cost"]) + sum((q(x)*e for x, e in zip(prices, loads[0])), Q(0))
    regret = (own_value - response[1], own_value - response[0])
    need(own_value == q(report["own_price_plan_value_exact_stored"])
         and regret == tuple(map(q, report["own_price_regret_interval_exact_stored"])),
         "Own-price regret endpoints changed")
    need(report["regret_subject"] == "named_planner_incumbent"
         and p["plan_hash"] == report["planner_plan_hash"]
         and h["bounded_budget_limited"] is True, "Incumbent/hull qualifier changed")
    return {"loads": loads, "planner": d, "hull": ch, "response": response,
            "gap": gap, "regret": regret, "classification": classification,
            "regret_subject": report["regret_subject"], "resolution": resolution,
            "negative_guard": guard, "plan_hash": p["plan_hash"], "own_value": own_value}


def check_secondary_audit(audit, frozen, manifest, attempt):
    """Require explicit numerical admission while preserving protocol failure."""
    need(audit.get("attempt") == "result/sistig_nonlinear/20260927-attempt2"
         and audit.get("source_commit") == COMMIT
         and audit.get("frozen_sha256") == FROZEN_SHA
         and audit.get("raw_manifest_sha256") == MANIFEST_SHA
         and audit.get("numerical_evidence_audit_status") == "PASS"
         and audit.get("protocol_compliance_status") == "FAIL"
         and audit.get("reporting_scope") == "off_protocol_secondary_diagnostic",
         "Independent off-protocol numerical audit not admitted")
    violation = audit.get("known_budget_violation")
    need(isinstance(violation, dict)
         and violation.get("metric") == "hull.polish_wall_s"
         and "hull/receipt.json" in manifest["files"],
         "Known hull polish violation missing from audit or manifest")
    receipt = json.loads((attempt / "hull/receipt.json").read_text())
    observed = q(receipt["accounting"]["polish_wall_s"])
    cap = q(frozen["budgets"]["hull"]["polish_seconds"])
    need(observed == q(violation.get("observed_s"))
         and cap == q(violation.get("cap_s"))
         and observed > cap,
         "Audited hull polish violation differs from frozen evidence")
    return observed, cap


def interval(ax, pair, y, color, precision=3):
    lo, hi = map(float, pair)
    scale = 10 ** precision
    lower = pair[0].numerator * scale // pair[0].denominator
    upper = -((-pair[1].numerator * scale) // pair[1].denominator)
    def label(value):
        sign = "−" if value < 0 else ""
        whole, part = divmod(abs(value), scale)
        return f"{sign}{whole}.{part:0{precision}d}"
    ax.plot([lo, hi], [y, y], color=color, linewidth=3, solid_capstyle="round")
    ax.scatter([lo, hi], [y, y], color=color, s=27, zorder=3)
    ax.text(lo, y + .13, label(lower), ha="left", va="bottom", fontsize=7.6, color=color)
    ax.text(hi, y - .13, label(upper), ha="right", va="top", fontsize=7.6, color=color)


def draw(data, polish_observed, polish_cap):
    fig = plt.figure(figsize=(7.0, 7.6))
    fig.suptitle("OFF-PROTOCOL SECONDARY DIAGNOSTIC\n"
                 f"Hull polish {float(polish_observed):.4f} s > {float(polish_cap):.1f} s frozen cap",
                 y=.96, fontsize=10, fontweight="bold", color="#9b332a")
    grid = fig.add_gridspec(2, 2, height_ratios=[1.08, 1])
    fig.subplots_adjust(left=.17, right=.95, top=.76, bottom=.16, hspace=.48, wspace=.58)
    top = fig.add_subplot(grid[0, :])
    obj = fig.add_subplot(grid[1, 0])
    signed = grid[1, 1].subgridspec(2, 1, hspace=1.05)
    gap_ax, regret_ax = fig.add_subplot(signed[0]), fig.add_subplot(signed[1])
    for row, key, label in zip(data["loads"], ("planner", "hull", "own_price"),
                               ("Physical planner (bounded)",
                                "Hull mixture mean (not executable)",
                                "Own-price response (certified)")):
        top.step(range(31), [float(x) for x in row] + [float(row[-1])],
                 where="post", color=COLORS[key], linewidth=1.8, label=label)
    top.set(xlim=(0, 30), xticks=[0, 6, 12, 18, 24, 30],
            xlabel="Hour within finite 30-hour service block",
            ylabel="Grid energy $L_t$ (kWh per hour period)",
            title="A  Hourly grid energy")
    top.grid(axis="y", alpha=.2)
    top.legend(frameon=False, fontsize=8, ncols=2, loc="lower center", bbox_to_anchor=(.5, 1.09))
    interval(obj, data["planner"], 1, COLORS["planner"])
    interval(obj, data["hull"], 0, COLORS["hull"])
    obj.set_yticks([1, 0], ["Planner\n(bounded)", "Hull\n(budget-limited)"])
    obj.set(ylim=(-.55, 1.55), xlabel="Objective (synthetic units)",
            title="B  Numerical objective intervals")
    obj.text(.98, .02, "Hull upper: replayed mixture", transform=obj.transAxes,
             ha="right", va="bottom", fontsize=7.6)
    obj.grid(axis="x", alpha=.2)
    interval(gap_ax, data["gap"], 0, COLORS["planner"])
    gap_ax.set_yticks([0], ["Gap $D-CH$"])
    gap_ax.axvline(0, color="#333333", linewidth=.9)
    gap_ax.axvline(float(data["resolution"]), color="#666666", linestyle="--", linewidth=.8)
    gap_ax.axvline(-float(data["negative_guard"]), color="#b5493b", linestyle=":", linewidth=.8)
    gap_ax.set(ylim=(-.45, .45), xlabel="Signed gap (synthetic units)",
               title="C  Signed gap (unresolved at +5)")
    interval(regret_ax, data["regret"], 0, COLORS["own_price"], precision=6)
    regret_ax.set_yticks([0], ["Incumbent\nregret"])
    regret_ax.axvline(0, color="#333333", linewidth=.9)
    regret_ax.set(ylim=(-.45, .45), xlabel="Signed own-price regret (synthetic units)",
                  title="D  Named-incumbent regret")
    for axis in (obj, gap_ax, regret_ax):
        axis.tick_params(axis="y", length=0)
    fig.text(.5, .024, "Gap markers: zero solid, +5 resolution dashed, −1e−4 guard dotted.\n"
             "Synthetic depot-15 finite block; hull mixture mean is not executable.\n"
             "Signed stored-float intervals; incumbent regret is not an optimal-fleet claim.\n"
             "Numerical audit only; primary experiment failed its frozen polish budget.",
             ha="center", fontsize=7.3)
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-json", required=True, type=Path,
                        help="independent machine audit with numerical PASS and protocol FAIL")
    parser.add_argument("--audit-sha256", required=True, help="pinned SHA-256 of machine audit")
    parser.add_argument("--off-protocol-secondary-diagnostic", required=True,
                        action="store_true", help="explicitly accept secondary diagnostic scope")
    args = parser.parse_args()
    audit_path = args.audit_json.resolve()
    need(audit_path.is_file() and sha(audit_path) == args.audit_sha256,
         "Independent machine audit missing or hash changed")
    audit = json.loads(audit_path.read_text())
    manifest, frozen, summary, stages, own_input = load_evidence(ATTEMPT)
    polish_observed, polish_cap = check_secondary_audit(audit, frozen, manifest, ATTEMPT)
    data = reconstruct(frozen, summary, stages, own_input)
    targets = [FIG / f"{STEM}.{ext}" for ext in ("png", "pdf", "svg")]
    provenance_path = FIG / f"{STEM}_provenance.json"
    need(not any(path.exists() for path in targets + [provenance_path]),
         "Figure/provenance already exists; exclusive output only")
    FIG.mkdir(parents=True, exist_ok=True)
    fig = draw(data, polish_observed, polish_cap)
    for ext, path in zip(("png", "pdf", "svg"), targets):
        metadata = {"Title": "Off-protocol secondary diagnostic: depot-15 nonlinear evidence"}
        if ext == "pdf":
            metadata.update(CreationDate=None, ModDate=None)
        fig.savefig(path, dpi=320, bbox_inches="tight", facecolor="white", metadata=metadata)
    plt.close(fig)
    svg = targets[2]
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    provenance = {"script_sha256": sha(Path(__file__)), "raw_manifest_sha256": sha(ATTEMPT / "MANIFEST.json"),
                  "public_copy_manifest_sha256": sha(PUBLIC_MANIFEST),
                  "public_copy_omitted_license_stdout": ["planner/stdout.txt", "hull/stdout.txt",
                                                         "own_price/stdout.txt"],
                  "frozen_sha256": FROZEN_SHA, "source_commit": COMMIT,
                  "independent_machine_audit_path": str(audit_path),
                  "independent_machine_audit_sha256": sha(audit_path),
                  "numerical_evidence_audit_status": "PASS", "protocol_compliance_status": "FAIL",
                  "known_budget_violation": {"metric": "hull.polish_wall_s",
                                             "observed_s": str(polish_observed), "cap_s": str(polish_cap)},
                  "scientific_input_sha256": {name: manifest["files"][name]["sha256"] for name in
                      ("frozen.json", "summary.json", "planner/result.json", "hull/result.json",
                       "own_price/result.json", "own_price/input.json")},
                  "exact_intervals": {key: [str(x) for x in data[key]] for key in
                      ("planner", "hull", "response", "gap", "regret")},
                  "gap_classification": data["classification"],
                  "regret_subject": data["regret_subject"], "planner_plan_hash": data["plan_hash"],
                  "resolution": str(data["resolution"]), "negative_guard": str(data["negative_guard"]),
                  "scope": "Off-protocol secondary numerical diagnostic; no runtime comparison, exact gap, optimum, or optimal-fleet support conclusion",
                  "hull_mean_is_executable": False, "optimizer_invoked": False,
                  "matplotlib_version": matplotlib.__version__,
                  "outputs": {ext: sha(path) for ext, path in zip(("png", "pdf", "svg"), targets)}}
    with provenance_path.open("x") as out:
        json.dump(provenance, out, indent=2, sort_keys=True)
        out.write("\n")


if __name__ == "__main__":
    main()
