"""Summarize E3/E5 outputs (out/*/e3.json). Read-only. Usage: summarize.py OUTDIR [prefix]"""
import json, sys, collections, statistics as st
from pathlib import Path
root = Path(sys.argv[1]); prefix = sys.argv[2] if len(sys.argv) > 2 else ""
ARMS = ("cold", "cold4", "learned", "learned4", "lp", "random")
rows = [json.loads(p.read_text()) for p in sorted(root.glob(prefix + "*/e3.json"))]
by = collections.defaultdict(dict)
for r in rows:
    by[(r["case"], r["seconds"])][r["arm"]] = r
best = collections.defaultdict(lambda: float("inf"))
for (case, T), arms in by.items():
    for r in arms.values():
        if r.get("bill") is not None: best[case] = min(best[case], r["bill"])
def val(r): return r.get("bill") if r and r.get("bill") is not None else None
out = {"cells": [], "pairs": {}}
pairs = [("learned", "cold"), ("learned", "lp"), ("learned", "random"), ("learned4", "cold4"),
         ("learned4", "cold"), ("cold4", "cold"), ("lp", "cold")]
counts = {p: collections.Counter() for p in pairs}; deltas = {p: collections.defaultdict(list) for p in pairs}
print("| Case | T s | " + " | ".join(ARMS) + " |"); print("|---|---:|" + "---:|"*len(ARMS))
for (case, T), arms in sorted(by.items(), key=lambda k: (k[0][1], k[0][0])):
    cells = []
    for a in ARMS:
        r = arms.get(a)
        if r is None: cells.append("")
        elif val(r) is None: cells.append("fail" if r.get("failure") else (r.get("status") or "none"))
        else: cells.append(f"{100*(val(r)/best[case]-1):.2f}%")
    print(f"| {case} | {T:g} | " + " | ".join(cells) + " |")
    for a, b in pairs:
        ra, rb = arms.get(a), arms.get(b)
        if ra is None or rb is None: continue
        va, vb = val(ra), val(rb)
        if va is None and vb is None: k = "both_fail"
        elif va is None: k = "loss"
        elif vb is None: k = "win"
        else:
            k = "win" if va < vb - 1e-6*abs(vb) else ("loss" if va > vb + 1e-6*abs(vb) else "tie")
            deltas[(a, b)][T].append(100*(va/vb-1))
        counts[(a, b)][(T, k)] += 1
    out["cells"].append({"case": case, "T": T, "bills": {a: val(arms[a]) for a in arms}, "best_any": best[case],
                         "kept": {a: arms[a].get("movements_kept") for a in arms},
                         "rounds": {a: len(arms[a].get("rounds", [])) or None for a in arms}})
print("\nPairwise (win/tie/loss; failures count as losses; mean % bill difference over both-successful pairs)")
for p in pairs:
    for T in sorted({t for (t, _) in counts[p]}):
        c = counts[p]; d = deltas[p][T]
        print(f"{p[0]} vs {p[1]} @ {T:g}s: {c[(T,'win')]}/{c[(T,'tie')]}/{c[(T,'loss')]+c[(T,'both_fail')]}"
              f"  mean diff {st.mean(d):+.3f}%  median {st.median(d):+.3f}%" if d else f"{p[0]} vs {p[1]} @ {T:g}s: no pairs")
        out["pairs"][f"{p[0]}_vs_{p[1]}_T{T:g}"] = {"win": c[(T,'win')], "tie": c[(T,'tie')],
            "loss": c[(T,'loss')], "both_fail": c[(T,'both_fail')], "mean_pct": st.mean(d) if d else None}
json.dump(out, open(root.parent / f"summary_{prefix or 'all'}.json", "w"), indent=1)
