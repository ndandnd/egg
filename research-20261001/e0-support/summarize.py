"""Summarize E0 outputs (out/g*/e0.json) into a table and JSON. Read-only."""
import json, sys
from pathlib import Path
root = Path(sys.argv[1]); rows = []
for path in sorted(root.glob("g*/e0.json")):
    d = json.loads(path.read_text()); s = d["summary"]
    def st(k):
        if k not in d: return "absent"
        r = d[k]
        if r["status"] != "completed": return "failed:" + r["failure"]["message"][:60]
        res = r["result"]
        return res.get("assessment", {}).get("status") or res.get("status")
    rows.append({"group": d["group_id"], "D": s["D"], "CH": s["CH"], "gap": s.get("gap"),
                 "regret": s.get("regret"), "cold_hull": st("cold_hull"), "retained_hull": st("retained_hull"),
                 "response": st("response"),
                 "hull_seconds": {k: round(d[k]["wall_seconds"], 1) for k in ("cold_hull", "retained_hull") if k in d},
                 "response_seconds": round(d["response"]["wall_seconds"], 1) if "response" in d else None})
json.dump(rows, open(root.parent / "e0_rows.json", "w"), indent=1)
pos = [r for r in rows if r["gap"] and r["gap"][0] > 1e-6]
print(f"groups {len(rows)}; certified positive gap {len(pos)}; both hulls certified "
      f"{sum(r['cold_hull']=='certified' and r['retained_hull']=='certified' for r in rows)}")
print("| Group | D | CH | Gap D-CH | Own-price regret of cold incumbent | Hulls (s) |")
print("|---|---|---|---|---|---|")
f = lambda v: "-" if v is None else f"{v:.3f}"
for r in rows:
    g = r["gap"] or [None, None]; rg = r["regret"] or [None, None]
    print(f"| {r['group']} | [{f(r['D'][0])}, {f(r['D'][1])}] | [{f(r['CH'][0])}, {f(r['CH'][1])}] | "
          f"[{f(g[0])}, {f(g[1])}] | [{f(rg[0])}, {f(rg[1])}] | {r['cold_hull']}/{r['retained_hull']} "
          f"{r['hull_seconds']} |")
