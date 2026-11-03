"""E11: seed robustness. Per case/arm min/median/max bill over Gurobi seeds; paired by
seed: learned4 (k15, k30) vs cold and cold4. Read-only. Usage: summarize.py OUTDIR"""
import json, glob, sys, collections, statistics as st
rows = collections.defaultdict(dict)
for p in glob.glob(sys.argv[1] + "/*/e3.json"):
    r = json.load(open(p))
    arm = r["arm"] if r["arm"] != "learned4" else f"learned4_k{int(round(r['keep']*100))}"
    rows[(r["case"], arm)][r["grb_seed"]] = r.get("bill")
arms = ("cold", "cold4", "learned4_k15", "learned4_k30")
cases = sorted({c for c, _ in rows}, key=lambda c: (int(c.split(":")[2]), c))
f = lambda v: "fail" if v is None else f"{v:.1f}"
print("| Case | " + " | ".join(f"{a} min/med/max (n)" for a in arms) + " |"); print("|---|" + "---|"*len(arms))
for c in cases:
    cells = []
    for a in arms:
        v = rows.get((c, a), {}); ok = [x for x in v.values() if x is not None]
        cells.append(f"{f(min(ok)) if ok else 'fail'} / {f(st.median(ok)) if ok else '-'} / {f(max(ok)) if ok else '-'} ({len(ok)}/{len(v)})")
    print(f"| {c} | " + " | ".join(cells) + " |")
print("\nPaired by seed (wins/ties/losses; failure = loss):")
for a in ("learned4_k15", "learned4_k30"):
    for ref in ("cold", "cold4"):
        w = t = l = 0
        for c in cases:
            A, B = rows.get((c, a), {}), rows.get((c, ref), {})
            for s in set(A) & set(B):
                va, vb = A[s], B[s]
                if va is None and vb is None: continue
                if va is None: l += 1
                elif vb is None: w += 1
                elif va < vb*(1-1e-6): w += 1
                elif va > vb*(1+1e-6): l += 1
                else: t += 1
        print(f"- {a} vs {ref}: {w}/{t}/{l}")
