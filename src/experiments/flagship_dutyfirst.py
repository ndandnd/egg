"""Boundary test on the complete 64-instance flagship development roster."""
from dataclasses import asdict
import csv
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.evsp import solve_evsp,solve_fixed_sequences,validate_solution
from experiments.run_matched_opf import write_json,ROOT
import numpy as np
out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
with (ROOT/"result/b2_full/20260818T140356Z/cells.csv").open() as f:
    rows=[r for r in csv.DictReader(f) if r["method"]=="a2"]
if len(rows)!=64 or len({(r["seed"],r["n_trips"],r["b"]) for r in rows})!=64: raise ValueError("bad flagship roster")
write_json(out/"roster.json",rows)
zero={}
for r in rows:
    seed,n,b=int(r["seed"]),int(r["n_trips"]),float(r["b"])
    tag=f"s{seed}-n{n}-b{b}";packet={"seed":seed,"n_trips":n,"b":b,"original_joint_upper":float(r["z_d_ub"]),"original_joint_lower":float(r["z_d_ub"])-float(r["tol_d"])}
    st=time.monotonic()
    try:
        inst=synthetic_instance(seed=seed,n_trips=n); market=make_affine_market(inst,b_scale=b)
        key=seed,n
        if key not in zero:
            z=solve_evsp(inst,("linear",np.zeros(inst.n_slots)),max_mip_gap=1e-8,time_limit_s=60.)
            errs=validate_solution(inst,z)
            if errs or z.stats.status!="OPTIMAL": raise ValueError(f"zero-price:{z.stats.status}, {errs}")
            zero[key]=z
            write_json(out/f"zero-s{seed}-n{n}.json",asdict(z))
        z=zero[key]
        segs=market.system_delta_segments(inst.charge_power_kw*inst.slot_min/60*inst.max_vehicles,16)
        lb=-float("inf");ub=float("inf");best=None;history=[]
        for round_no in range(25):
            s=solve_fixed_sequences(inst,z.sequences,("pwl",segs),max_mip_gap=1e-8,time_limit_s=30.)
            if s is None: raise ValueError("zero-price cover absent")
            errs=validate_solution(inst,s)
            if errs or s.stats.bound is None: raise ValueError(f"fixed replay:{errs}")
            val=s.ops_cost+market.system_cost_delta(s.load)
            lb=max(lb,s.stats.bound)
            if val<ub:ub,best=val,s
            history.append({"status":s.stats.status,"lb":lb,"ub":ub,"stats":s.stats.to_dict()})
            if ub-lb<=.01:break
            if s.stats.status!="OPTIMAL":break
            for t,row in enumerate(market.system_delta_tangents_at(s.load)):segs[t].append(row)
        packet.update(state="evaluated",qualified=ub-lb<=.01,lb=lb,ub=ub,history=history,solution=asdict(best),
                      regret_lower=lb-packet["original_joint_upper"],regret_upper=ub-packet["original_joint_lower"],
                      original_electricity_denominator=packet["original_joint_upper"]-best.ops_cost)
    except Exception as exc:
        packet.update(state="failure",error=f"{type(exc).__name__}: {exc}")
    packet["elapsed_s"]=time.monotonic()-st;write_json(out/(tag+".json"),packet)
    print(tag,packet["state"],packet.get("regret_lower"),packet.get("regret_upper"),flush=True)
