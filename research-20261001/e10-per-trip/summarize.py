"""E10: per-trip top-m pruning vs global keep fractions and cold arms. Read-only.
Usage: summarize.py DIR [DIR ...] (E3/E5/E8/E10 out dirs). hfix reruns replace artifacts."""
import json, glob, sys, collections, statistics as st
rows = collections.defaultdict(dict)
for d in sys.argv[1:]:
    for p in glob.glob(d + "/*/e3.json"):
        r = json.load(open(p)); n = p.split("/")[-2]
        if r["arm"] in ("cold", "cold4"): k = r["arm"]
        elif r["arm"] == "learned4":
            k = f"m{r['min_options']}" if r["keep"] == 0 else f"k{int(round(r['keep']*100))}"
        else: continue
        slot = (r["case"], r["seconds"])
        if n.endswith("-hfix") or k not in rows[slot]: rows[slot][k] = r
cols = ("cold", "cold4", "k5", "k15", "k30", "m3", "m5", "m8")
best = collections.defaultdict(lambda: 1e18)
for (c, T), d in rows.items():
    for r in d.values():
        if r.get("bill"): best[c] = min(best[c], r["bill"])
keys = [k for k in rows if any(x in rows[k] for x in ("m3", "m5", "m8"))]
order = lambda k: (k[0].split(":")[0], int(k[0].split(":")[2]) if k[0].startswith("scale") else 0, k[1], k[0])
print("| Case | T s | " + " | ".join(cols) + " | kept m3/m5/m8 |"); print("|---|---:|" + "---:|"*len(cols) + "---|")
for (c, T) in sorted(keys, key=order):
    d = rows[(c, T)]; cells = []
    for k in cols:
        r = d.get(k); b = r.get("bill") if r else None
        cells.append("" if r is None else ("fail" if b is None else f"{100*(b/best[c]-1):.2f}%"))
    kept = "/".join(str(d[m].get("movements_kept")) if m in d else "-" for m in ("m3", "m5", "m8"))
    print(f"| {c} | {T:g} | " + " | ".join(cells) + f" | {kept} |")
print("\nPaired (wins/ties/losses; a failure counts as a loss; median % over both-successful):")
for m in ("m3", "m5", "m8"):
    for ref in ("cold", "cold4", "k15", "k30"):
        w = t = l = 0; ds = []
        for (c, T) in keys:
            a, b = rows[(c, T)].get(m), rows[(c, T)].get(ref)
            if not a or not b: continue
            va, vb = a.get("bill"), b.get("bill")
            if va is None and vb is None: continue
            if va is None: l += 1; continue
            if vb is None: w += 1; continue
            d = 100*(va/vb-1); ds.append(d); w += d < -1e-4; l += d > 1e-4; t += abs(d) <= 1e-4
        print(f"- {m} vs {ref}: {w}/{t}/{l}" + (f", median {st.median(ds):+.2f}%" if ds else ""))
