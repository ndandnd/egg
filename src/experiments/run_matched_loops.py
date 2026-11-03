"""Prespecified price-state iterations on the original 73 resolved hull cases."""
import argparse
from collections import Counter
from datetime import datetime
from fractions import Fraction
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.run_matched_opf import ROOT,RAW,ARCHIVE,OFFERS,make_fleet,roster,write_json,snapshot
from egglab.simbench_radial import read_simbench_radial
from egglab.matched_profiles import NativeACValidator,read_matched_profiles
from egglab.two_window_opf import TwoWindowOPF

def response(fleet,prices):
    offers=[]
    for l in fleet.layers():
        for e in set((l.early_min_kwh,l.early_max_kwh)):
            c=float(l.fee_eur)+(prices[0]*float(e)+prices[1]*float(fleet.total_grid_kwh-e))/1000
            offers.append((c,l.buses,float(e),l))
    v=min(z[0] for z in offers)
    tied=[z for z in offers if z[0]<=v+1e-6]
    winner=min(tied,key=lambda z:(z[1],z[2]))
    return winner, len({z[2] for z in tied})>1, v

p=argparse.ArgumentParser();p.add_argument("output",type=Path);args=p.parse_args()
args.output.mkdir(exist_ok=False)
old=ROOT/"src/runs/opf-matched-20261103-attempt01/cells"
rows=[r for r in roster() if json.loads((old/(r["id"]+".json")).read_text())["arms"]["hull"]["qualified"]]
if len(rows)!=73:raise ValueError("wrong original loop cohort")
write_json(args.output/"roster.json",rows)
model=read_simbench_radial(ARCHIVE); profiles=read_matched_profiles(ARCHIVE,model);ac=NativeACValidator(ARCHIVE,model)
sizes=json.loads((ROOT/"result/opf_qualification/repair02/depot_sizes.json").read_text())
hourly={}
for name in ("DE-2024-01-17.json","summer-after-cooldown/DE-2024-07-17.json"):
    for r in json.loads((RAW/name).read_text())["records"]:
        if r["PriceArea"]!="DE":raise ValueError("wrong price area")
        t=datetime.fromisoformat(r["HourUTC"]+"+00:00").astimezone(ZoneInfo("Europe/Berlin"))
        hourly[t.date().isoformat(),t.hour]=r["SpotPriceEUR"]
for row in rows:
    saved=json.loads((old/(row["id"]+".json")).read_text())
    site=next(s for s in sizes if s["node"].endswith(" "+("78" if row["site"]=="near" else "68")) and round(s["target_fraction"]*100)==row["size"])
    fleet,_,_=make_fleet(row["window"],row["fleet"],site["chargers"],site["services_per_batch"])
    days=[q for q in profiles[row["date"]] if row["window"]=="primary" or q["hour"]!=23]
    windows=[int(q["hour"]!=12) for q in days];prices=[hourly[row["date"],q["hour"]] for q in days]
    node=model["bus_index"][site["node"]];net=dict(model["solver"],open_end_leaves=model["passive_open_ends"])
    backup=(node,1.,OFFERS[row["market"]]) if OFFERS[row["market"]] is not None else None
    engines={s:TwoWindowOPF(net,node,[q["p_mw"] for q in days],[q["q_mvar"] for q in days],
        [.25]*len(days),prices,float(fleet.total_grid_kwh),window_ids=windows,backup=backup,solver=s) for s in ("GUROBI","CLARABEL")}
    calls={}; hits=Counter()
    def fixed(loads):
        key=tuple(float(x) for x in loads)
        hits[key]+=1
        if key in calls:return calls[key]
        attempts=[]
        for solver in engines:
            point=engines[solver].fixed_loads(key)
            accepted=point["physical_pass"]
            if accepted:
                checks=[ac.check(days[i],node,q["depot_mw"],q,backup_node=node if backup else None) for i,q in enumerate(point["periods"])]
                accepted=len(checks)==len(days) and all(z.get("converged") and z.get("within_native_limits") and z.get("comparison_pass") for z in checks)
            else:checks=[]
            attempts.append(dict(solver=solver,accepted=bool(accepted),point=snapshot(point),
                                 ac_max=max((max(z["max_abs_discrepancies"].values()) for z in checks),default=None)))
            if accepted or point["status"]=="infeasible":break
        result=dict(qualified=bool(accepted),attempts=attempts,prices=point["depot_price_per_mwh"],
                    value=point["grid_cost"],status=point["status"])
        calls[key]=result;return result
    methods={}
    for rule in ("1","0.5","0.1","diminishing"):
        price=np.asarray(saved["window_spot_eur_mwh"],float);history=[];verdict="budget_exhausted";period=None
        for k in range(100):
            (_,buses,e,layer),tie,_=response(fleet,price)
            exact=min(max(Fraction(str(e)),layer.early_min_kwh),layer.early_max_kwh)
            fleet.service_witness(layer.pairs,exact)
            loads=[float(exact),float(fleet.total_grid_kwh-exact)]
            obs=fixed(loads)
            rec=dict(iteration=k,posted=price.tolist(),buses=buses,loads=loads,fleet_tie=tie,status=obs["status"])
            history.append(rec)
            if not obs["qualified"]:
                verdict="infeasible_response" if obs["status"]=="infeasible" else "unqualified_grid"
                break
            clearing=np.asarray(obs["prices"],float)
            residual=float(max(abs(clearing-price)))
            chosen_cost=float(layer.fee_eur)+np.dot(clearing,loads)/1000
            regret=chosen_cost-response(fleet,clearing)[2]
            rec.update(clearing=clearing.tolist(),undamped_price_residual=residual,regret_eur=float(regret))
            if residual<=1e-4 and regret<=.01:
                verdict="fixed_point";break
            if rule!="diminishing":
                # Two completed copies of the same price-state period are required.
                for d in range(2,min(20,len(history)//2)+1):
                    if all(max(abs(np.asarray(history[-1-j]["posted"])-np.asarray(history[-1-j-d]["posted"])))<=1e-4 for j in range(d)):
                        verdict="cycle";period=d;break
                if verdict=="cycle":break
            alpha=1/(k+1) if rule=="diminishing" else float(rule)
            price=(1-alpha)*price+alpha*clearing
        methods[rule]=dict(outcome=verdict,period=period,history=history)
    probes=[]
    recurring=[key for key,n in hits.items() if n>=2]
    for load in recurring:
        center=fixed(load)
        if not center["qualified"]:continue
        for w in (0,1):
            values=[]
            for delta in (-1.,1.):
                altered=list(load);altered[w]+=delta
                if altered[w]<0:
                    values.append(dict(delta=delta,qualified=False,status="negative_load"));continue
                point=fixed(altered)
                values.append(dict(delta=delta,qualified=point["qualified"],status=point["status"],
                    secant=1000*(point["value"]-center["value"])/delta if point["qualified"] else None))
            ambiguous=all(v["qualified"] for v in values) and abs(values[1]["secant"]-values[0]["secant"])>.5
            probes.append(dict(load=list(load),window=w,sides=values,ambiguity_diagnostic=bool(ambiguous)))
    for rule,run in methods.items():
        run["cause_flags"]=dict(positive_gap_certified=False,price_ambiguity_diagnostic=any(p["ambiguity_diagnostic"] for p in probes),
             distinct_load_fleet_tie=any(h["fleet_tie"] for h in run["history"]),step_only_verified=False)
        flags=[k for k,v in run["cause_flags"].items() if v]
        run["cause_label"]=flags[0] if len(flags)==1 else "indeterminate"
    write_json(args.output/(row["id"]+".json"),dict(**row,methods=methods,probes=probes,
        oracle_calls=[dict(load=list(key),**v) for key,v in calls.items()]))
    print(row["id"],{k:v["outcome"] for k,v in methods.items()},flush=True)
    ac.references.clear()
