"""Pair E7 multi8-score learned4 runs with v8-score learned4 keep-0.30 runs. Read-only.
Usage: pair.py E7_OUT V8_DIR [V8_DIR ...]"""
import json, sys, statistics as st
from pathlib import Path
m8 = {}
for p in Path(sys.argv[1]).glob("*/e3.json"):
    r = json.loads(p.read_text()); m8[(r["case"], r["seconds"])] = r
v8 = {}
for d in sys.argv[2:]:
    for p in Path(d).glob("*learned4*/e3.json"):
        r = json.loads(p.read_text())
        if abs(r["keep"]-0.3) < 1e-9 and r["arm"] == "learned4":
            k = (r["case"], r["seconds"])
            if p.parent.name.endswith("-hfix") or k not in v8: v8[k] = r
print("| Case | T s | v8 bill (buses) | multi8 bill (buses) | diff % |"); print("|---|---:|---:|---:|---:|")
w = t = l = 0; ds = []
for k in sorted(m8, key=lambda k: (k[0].split(":")[0], k[1], k[0])):
    a, b = v8.get(k), m8[k]
    va = a.get("bill") if a else None; vb = b.get("bill")
    f = lambda r, v: "fail" if v is None else f"{v:.2f} ({r['vehicles']})"
    if va is not None and vb is not None:
        d = 100*(vb/va-1); ds.append(d); w += d < -1e-4; l += d > 1e-4; t += abs(d) <= 1e-4; dd = f"{d:+.2f}"
    else:
        dd = "-"; w += (va is None and vb is not None); l += (vb is None and va is not None)
    print(f"| {k[0]} | {k[1]:g} | {f(a, va) if a else 'missing'} | {f(b, vb)} | {dd} |")
print(f"\nmulti8 vs v8 (same case/T/keep 0.30/learned4): {w} better / {t} tie / {l} worse; median {st.median(ds):+.2f}%, mean {st.mean(ds):+.2f}%")
