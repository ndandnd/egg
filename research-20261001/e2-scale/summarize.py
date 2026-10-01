"""Summarize E2 outputs (out/*/e2.json) into a markdown table + JSON. Read-only."""
import json, sys
from pathlib import Path
root = Path(sys.argv[1]); rows = []
for p in sorted(root.glob("*/e2.json")):
    if "smoke" in p.parent.name: continue
    d = json.loads(p.read_text()); best = d.get("incumbent"); prog = d.get("progress", [])
    def within(eps):
        for t, (lb, ub) in prog:
            if ub is not None and best is not None and ub <= best*(1+eps)+1e-9: return round(t, 1)
    first = next((round(t, 1) for t, (lb, ub) in prog if ub is not None and ub < 1e99), None)
    gap = (best-d["bound"])/best*100 if best and d.get("bound") is not None else None
    rows.append({"cell": p.parent.name, "trips": d.get("services"), "movements": d.get("movements"),
        "build_s": d.get("build_seconds"), "status": d.get("status"), "incumbent": best, "gap_pct": gap,
        "first_s": first, "t05_s": within(.005), "t01_s": within(.001), "solve_s": d.get("solve_seconds"),
        "buses": (d.get("replay") or {}).get("vehicles"), "failure": (d.get("failure") or {}).get("message")})
json.dump(rows, open(root.parent / "e2_rows.json", "w"), indent=1)
f = lambda v, n=1: "-" if v is None else f"{v:.{n}f}"
print("| Cell | Trips | Movements | Build s | Status (600 s) | Incumbent | Gap % | 1st inc s | 0.5% s | 0.1% s | Buses |")
print("|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|")
for r in sorted(rows, key=lambda r: (r["trips"], r["cell"])):
    print(f"| {r['cell']} | {r['trips']} | {r['movements']} | {f(r['build_s'])} | {r['status']} | {f(r['incumbent'],2)} | "
          f"{f(r['gap_pct'],2)} | {f(r['first_s'])} | {f(r['t05_s'])} | {f(r['t01_s'])} | {r['buses']} |")
