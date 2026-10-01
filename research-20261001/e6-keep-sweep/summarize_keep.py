"""E6: learned4 bills by keep fraction vs cold/cold4 on scaled cases. Read-only.
Usage: summarize_keep.py OUTDIR (e3-prune out/). hfix reruns replace artifact rows."""
import json, sys, collections, statistics as st
from pathlib import Path
root = Path(sys.argv[1]); cells = collections.defaultdict(dict)
for p in sorted(root.glob("scale*/e3.json")):
    r = json.loads(p.read_text()); name = p.parent.name
    if r["arm"] not in ("cold", "cold4", "learned4"): continue
    key = r["arm"] if r["arm"] != "learned4" else f"learned4_k{int(round(r['keep']*100))}"
    slot = (r["case"], r["seconds"])
    if name.endswith("-hfix") or key not in cells[slot]:
        cells[slot][key] = r
cols = ("cold", "cold4", "learned4_k15", "learned4_k30", "learned4_k50")
best = collections.defaultdict(lambda: float("inf"))
for (c, T), d in cells.items():
    for r in d.values():
        if r.get("bill") is not None: best[c] = min(best[c], r["bill"])
print("| Case | T s | " + " | ".join(cols) + " |"); print("|---|---:|" + "---:|"*len(cols))
wins = collections.Counter(); diffs = collections.defaultdict(list)
for (c, T) in sorted(cells, key=lambda k: (k[1], int(k[0].split(":")[2]), k[0])):
    d = cells[(c, T)]; row = []
    for k in cols:
        r = d.get(k); b = r.get("bill") if r else None
        row.append("" if r is None else ("fail" if b is None else f"{100*(b/best[c]-1):.2f}%"))
    print(f"| {c} | {T:g} | " + " | ".join(row) + " |")
    for k in ("learned4_k15", "learned4_k30", "learned4_k50"):
        for ref in ("cold", "cold4"):
            a, b = d.get(k), d.get(ref)
            if a is None or b is None: continue
            va, vb = a.get("bill"), b.get("bill")
            res = ("loss" if va is None else "win" if vb is None else
                   "win" if va < vb*(1-1e-6) else "loss" if va > vb*(1+1e-6) else "tie")
            wins[(k, ref, T, res)] += 1
            if va is not None and vb is not None: diffs[(k, ref, T)].append(100*(va/vb-1))
print()
for k in ("learned4_k15", "learned4_k30", "learned4_k50"):
    for ref in ("cold", "cold4"):
        for T in (60, 300):
            w = [wins[(k, ref, T, x)] for x in ("win", "tie", "loss")]
            d = diffs[(k, ref, T)]
            print(f"{k} vs {ref} @{T}s: {w[0]}/{w[1]}/{w[2]}" + (f"  median {st.median(d):+.2f}%" if d else ""))
