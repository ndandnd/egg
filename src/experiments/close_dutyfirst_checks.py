"""Summaries and conservative loop classification from immutable closed packets."""
import csv
from collections import Counter
import gzip
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.run_matched_opf import ROOT,write_json
out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
src=ROOT/"src/runs"
def zipped(name,obj):
    (out/name).write_bytes(gzip.compress(json.dumps(obj,allow_nan=False,separators=(",",":")).encode(),mtime=0))
all_lift=[]
for tag in ("lift01","lift02"):
    all_lift+=json.loads((src/f"opf-matched-20261103-{tag}/results.json").read_text())["rows"] if tag=="lift02" else [
      r for r in json.loads((src/f"opf-matched-20261103-{tag}/results.json").read_text())["rows"]
      if r["hull_status"]!="optimal_inaccurate"]
zipped("physical_brackets.json.gz",all_lift)
loops=[json.loads(p.read_text()) for p in (src/"opf-loops-20261103-attempt01").glob("*.json") if p.name!="roster.json"]
for r in loops:
    run=r["methods"]["0.1"]
    if run["outcome"]=="cycle":
        run["original_outcome"]="cycle"
        run["outcome"]="unresolved_small_recurrence"
        # The old approximate recurrence could stop a contracting trajectory too soon.
        # Continue its price arithmetic with only already paid, cached oracle responses.
        start=run["history"][-1]; price=.9*np.asarray(start["posted"])+.1*np.asarray(start["clearing"])
        lookup={tuple(o["load"]):o for o in r["oracle_calls"]}
        import importlib.util
        # Reuse the committed fleet projection without importing the runner's top-level dispatch.
        from experiments.run_matched_opf import make_fleet
        sizes=json.loads((ROOT/"result/opf_qualification/repair02/depot_sizes.json").read_text())
        site=next(s for s in sizes if s["node"].endswith(" "+("78" if r["site"]=="near" else "68")) and round(s["target_fraction"]*100)==r["size"])
        fleet,_,_=make_fleet(r["window"],r["fleet"],site["chargers"],site["services_per_batch"])
        for k in range(len(run["history"]),100):
            choices=[]
            from fractions import Fraction
            for l in fleet.layers():
                for e in set((l.early_min_kwh,l.early_max_kwh)):
                    choices.append((float(l.fee_eur)+(price[0]*float(e)+price[1]*float(fleet.total_grid_kwh-e))/1000,l.buses,e,l))
            best=min(z[0] for z in choices); _,b,e,l=min((z for z in choices if z[0]<=best+1e-6),key=lambda z:(z[1],z[2]))
            e=min(max(Fraction(str(float(e))),l.early_min_kwh),l.early_max_kwh)
            loads=(float(e),float(fleet.total_grid_kwh-e))
            oracle=lookup.get(loads)
            if oracle is None or not oracle["qualified"]:
                run["outcome"]="cached_continuation_unavailable";break
            pi=np.asarray(oracle["prices"]);res=float(max(abs(pi-price)))
            rec=dict(iteration=k,posted=price.tolist(),clearing=pi.tolist(),undamped_price_residual=res,loads=list(loads),cached_arithmetic_extension=True)
            run["history"].append(rec)
            if res<=1e-4:
                run["outcome"]="fixed_point";break
            price=.9*price+.1*pi
        else:run["outcome"]="budget_exhausted"
zipped("loop_records.json.gz",loops)
summary={"loops":{}}
for w in ("all","primary","secondary"):
    group=loops if w=="all" else [r for r in loops if r["window"]==w]
    summary["loops"][w]={k:dict(Counter(r["methods"][k]["outcome"] for r in group)) for k in ("1","0.5","0.1","diminishing")}
    q=[r for r in all_lift if w=="all" or r["window"]==w]
    summary.setdefault("brackets",{})[w]=dict(assigned=len(q),feasible=sum(r.get("arms",{}).get("strong",{}).get("qualified",False) for r in q),
        cent=sum(r.get("arms",{}).get("strong",{}).get("bracket_within_cent",False) for r in q))
flagship={}
for tag in ("flagship-dutyfirst-20261103-repair01","flagship-energytie-20261103-attempt01"):
    rs=[json.loads(p.read_text()) for p in (src/tag).glob("s*.json")]
    zipped(tag+".json.gz",rs)
    good=[r for r in rs if r.get("qualified")]
    flagship[tag]=dict(assigned=64,qualified=len(good),positive_over_cent=sum(r["regret_lower"]>.01 for r in good),
        mean_interval=[sum(r[k] for r in good)/64 for k in ("regret_lower","regret_upper")],
        max_lower=max(r["regret_lower"] for r in good),max_upper=max(r["regret_upper"] for r in good),
        maximum_total_percent_upper=max(100*r["regret_upper"]/r["original_joint_lower"] for r in good),
        certificate_inversions=[r for r in good if r["regret_upper"]<-.01])
summary["flagship"]=flagship
capacity=json.loads((src/"opf-capacity-20261103-attempt01/capacity.json").read_text())
for row in capacity:
    rs=[r for r in all_lift if r["window"]=="primary" and r["fleet"]==row["fleet"]]
    original=next((ROOT/"src/runs/opf-matched-20261103-attempt01/cells").glob(f"primary-2024-01-17-*-{'near' if row['node'].endswith('78') else 'far'}-hard-{row['fleet']}.json"))
    # The original diagnostics for the exact same fleet size supply the all-pairing floor bound.
    for p in (ROOT/"src/runs/opf-matched-20261103-attempt01/cells").glob(f"primary-2024-01-17-*-{'near' if row['node'].endswith('78') else 'far'}-hard-{row['fleet']}.json"):
        cell=json.loads(p.read_text())
        if abs(cell["total_grid_kwh"]-row["daily_kwh"])>1e-5: continue
        layers=cell["layer_diagnostics"]["by_count"]
        l=next(x for x in layers if x["pairs"]==row["n"])
        if l["best_chargeable"]:
            # Different site designs have different total service energy.
            if abs(cell["total_grid_kwh"]-row["daily_kwh"])>1e-5:continue
            row["worst_matching_floor_kwh"]=l["max_floor_grid_kwh"]
            row["every_matching_admits_balanced_peak"]=bool(l["worst_chargeable"] and l["max_floor_grid_kwh"]<=row["daily_kwh"]/3<=l["common_ceiling_grid_kwh"])
            break
write_json(out/"capacity.json",capacity)
summary["capacity_all_pairings_balanced"]=all(r.get("every_matching_admits_balanced_peak") for r in capacity)
write_json(out/"summary.json",summary)
print(json.dumps(summary,indent=1))
