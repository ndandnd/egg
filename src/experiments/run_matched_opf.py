"""Run the preregistered matched fleet/grid comparison on the fixed local public inputs."""
import argparse
from datetime import datetime
from fractions import Fraction
from functools import lru_cache
import itertools
import json
import math
from pathlib import Path
import sys
import time
from zoneinfo import ZoneInfo

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from egglab.matched_fleets import FleetProjection, read_matched_fleet
from egglab.matched_profiles import NativeACValidator, read_matched_profiles
from egglab.simbench_radial import read_simbench_radial
from egglab.two_peak import ChargeWindow
from egglab.two_window_opf import TwoWindowOPF

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "src/runs/opf-inputs-20261103"
ARCHIVE = RAW / "grid/1-MV-rural--0-sw.zip"
ENERGY = ROOT.parent / "paper-draft1/paper/draft1/data/peak_runs.json"
DAYS = ("2024-01-17", "2024-07-17")
OFFERS = {"hard": None, "backup_low": 414.7235, "backup_high": 510.5304}
FEE = 50


def json_scalar(value):
    if isinstance(value,np.generic):
        return value.item()
    raise TypeError(f"unsupported result field type {type(value).__name__}")


def write_json(path, obj):
    tmp = path.with_suffix(".partial")
    tmp.write_text(json.dumps(obj, allow_nan=False, indent=1, default=json_scalar) + "\n")
    tmp.replace(path)


def roster():
    rows = []
    for window, day, size, site, market, fleet in itertools.product(
            ("primary","secondary"), DAYS, (10,40,80), ("near","far"), OFFERS, ("homogeneous","sistig")):
        tag = f"{window}-{day}-{size}-{site}-{market}-{fleet}"
        rows.append(dict(id=tag,window=window,date=day,size=size,site=site,market=market,fleet=fleet))
    return rows


@lru_cache(None)
def make_fleet(window, kind, plugs, n):
    early = ChargeWindow(1,plugs,125)
    late = ChargeWindow(2 if window=="primary" else 1,plugs,125)
    if window=="secondary" and kind=="homogeneous":
        fleet = FleetProjection((140,)*n,(90,)*n,early,late,FEE)
        provenance = {"source":"original 140/90 kWh fleet"}
    else:
        fleet,provenance = read_matched_fleet(ENERGY,n,early,late,FEE,homogeneous=kind=="homogeneous")
    diagnostics = fleet.diagnostics()
    layers = fleet.layers()
    rows = diagnostics["by_count"]
    spreads = [r["max_floor_grid_kwh"]-r["min_floor_grid_kwh"] for r in rows if r["worst_chargeable"]]
    top = next((r for r in rows if layers and r["pairs"]==layers[-1].pairs),None)
    compact = dict(max_same_count_floor_spread_kwh=max(spreads,default=None),
                   min_fleet_floor_spread_kwh=(top["max_floor_grid_kwh"]-top["min_floor_grid_kwh"]
                    if top and top["worst_chargeable"] else None), by_count=rows,
                   impossible_singleton_ids=diagnostics["impossible_singleton_ids"])
    return fleet,provenance,compact


def hull(fleet):
    layers = fleet.layers()
    low = [l.early_min_kwh for l in layers]
    slopes = [b-a for a,b in zip(low,low[1:])]
    if (any(l.pairs!=i for i,l in enumerate(layers))
        or any(l.early_max_kwh!=layers[0].early_max_kwh for l in layers)
        or any(s<0 for s in slopes) or any(b<a for a,b in zip(slopes,slopes[1:]))):
        raise ValueError("layer hypotheses failed")
    lines = set()
    for a,b in zip(layers,layers[1:]):
        if b.early_min_kwh>a.early_min_kwh:
            slope = (b.fee_eur-a.fee_eur)/(b.early_min_kwh-a.early_min_kwh)
            lines.add((slope,a.fee_eur-slope*a.early_min_kwh))
    lines.add((Fraction(0),layers[-1].fee_eur))
    return tuple(sorted(lines))


def wholesale(fleet,lines,prices):
    layers = fleet.layers()
    def bill(e):
        return (prices[0]*float(e)+prices[1]*float(fleet.total_grid_kwh-e))/1000
    def compare(layer):
        if layer is None:
            return None
        e = layer.early_min_kwh if prices[0]>=prices[1] else layer.early_max_kwh
        return float(layer.fee_eur)+bill(e)
    joint = min(compare(l) for l in layers)
    endpoints = set(l.early_min_kwh for l in layers)|{layers[-1].early_max_kwh}
    return dict(fixed=compare(fleet.fixed_cover_layer()),strong=compare(fleet.strong_cover_layer()),
                joint=joint,buses=min(l.buses for l in layers if abs(compare(l)-joint)<1e-9),hull=min(bill(e)+float(max(s*e+c for s,c in lines)) for e in endpoints))


def snapshot(point):
    return {k:point.get(k) for k in ("status","error","physical_pass","early_kwh","fleet_kwh",
            "fee_eur","grid_cost","objective","native_bound","energy_residual_kwh",
            "fee_residual_eur","depot_price_per_mwh")}


def unavailable(reason):
    return dict(status=reason,qualified=False,objective_eur=None,quarters=[])


def evaluate(row, model, ac, hours, hourly, site):
    days = [q for q in hours if row["window"]=="primary" or q["hour"]!=23]
    windows = [int(q["hour"]!=12) for q in days]
    prices = [hourly[q["hour"]] for q in days]
    window_prices = [sum(p for p,i in zip(prices,windows) if i==w)/windows.count(w) for w in (0,1)]
    fleet,source,diag = make_fleet(row["window"],row["fleet"],site["chargers"],site["services_per_batch"])
    layers=fleet.layers()
    out=dict(**row,source=source,layer_diagnostics=diag,window_spot_eur_mwh=window_prices,arms={},
             total_grid_kwh=float(fleet.total_grid_kwh),wholesale={})
    if not layers:
        out.update(state="structural_infeasible",arms={k:unavailable("fleet_infeasible") for k in ("fixed","strong","joint","hull")})
        return out
    index=model["bus_index"][site["node"]]
    lines=hull(fleet)
    out["wholesale"]=wholesale(fleet,lines,window_prices)
    network=dict(model["solver"],open_end_leaves=model["passive_open_ends"])
    backup=(index,1.,OFFERS[row["market"]]) if OFFERS[row["market"]] is not None else None
    engine=TwoWindowOPF(network,index,[q["p_mw"] for q in days],[q["q_mvar"] for q in days],
                        [.25]*len(days),prices,float(fleet.total_grid_kwh),window_ids=windows,backup=backup)
    solves={}
    def dispatch(lo,hi,pieces=()):
        key=(lo,hi,pieces)
        if key not in solves:
            solves[key]=engine.optimize(float(lo),float(hi),[(float(a),float(b)) for a,b in pieces])
        return solves[key]
    receipts={}
    def verify(point):
        if id(point) not in receipts:
            quarters=[]
            for k,p in enumerate(point["periods"]):
                if p.get("depot_mw") is None:
                    continue
                a=ac.check(days[k],index,p["depot_mw"],p,backup_node=index if backup else None)
                quarters.append(dict(time=days[k]["time_local"],grid_ok=p["physical_pass"],
                    ac_ok=bool(a.get("comparison_pass") and a.get("within_native_limits") and a.get("converged")),
                    ac_error=a.get("error"),ac_max_abs=a.get("max_abs_discrepancies"),
                    ac_limits=a.get("native_limits"),v_binding=bool(p["binding_vmin"] or p["binding_vmax"]),
                    t_binding=bool(p["binding_from"] or p["binding_to"]),v_nodes=p["binding_vmin"]+p["binding_vmax"],
                    thermal_edges=sorted(set(p["binding_from"]+p["binding_to"])),
                    depot_mw=p["depot_mw"],backup_mw=p["backup_mw"],grid_import_mw=p["import_mw"],
                    loss_mw=p["loss_mw"],mixed_cone_ratio=p["cone_max_mixed_ratio"]))
            receipts[id(point)]=quarters
        return receipts[id(point)]
    def arm(point,layer=None,cover="joint",offset=0):
        quarters=verify(point)
        ok=point["physical_pass"] and len(quarters)==len(days) and all(q["ac_ok"] for q in quarters)
        if point["objective"] is None:
            return dict(unavailable(point["status"]),solver=snapshot(point))
        witness=None
        if layer is not None:
            e=Fraction(str(point["early_kwh"]))
            inside=min(max(e,layer.early_min_kwh),layer.early_max_kwh)
            witness=fleet.service_witness(layer.pairs,inside,cover=cover)
            ok=ok and abs(float(inside-e))<=1e-5 and len(witness)==layer.buses
        return dict(status=point["status"],qualified=bool(ok),objective_eur=point["objective"]+float(offset),
                    fee_eur=point["fee_eur"]+float(offset),early_kwh=point["early_kwh"],
                    pairs=layer.pairs if layer else None,buses=layer.buses if layer else None,
                    solver=snapshot(point),witness_buses=len(witness) if witness is not None else None,quarters=quarters)
    def physical(layer,cover):
        if layer is None:
            return unavailable("committed_cover_infeasible")
        point=dispatch(layer.early_min_kwh,layer.early_max_kwh)
        return arm(point,layer,cover,layer.fee_eur)
    simple=len(lines)==1
    h=dispatch(layers[0].early_min_kwh,layers[0].early_max_kwh,() if simple else lines)
    out["arms"]["hull"]=arm(h,offset=layers[-1].fee_eur if simple else 0)
    out["arms"]["fixed"]=physical(fleet.fixed_cover_layer(),"fixed")
    out["arms"]["strong"]=physical(fleet.strong_cover_layer(),"strong")
    out["identical_lower_envelopes"]=simple
    if h["early_kwh"] is None:
        out["arms"]["joint"]=unavailable("hull_interval_"+h["status"])
    else:
        # The minimizer of the convex count-value function brackets an integer minimizer.
        # Include both neighbors of the boundary as protection against rounding of E.
        E=h["early_kwh"]
        idx=max((i for i,l in enumerate(layers) if float(l.early_min_kwh)<=E+1e-7),default=0)
        ids=([len(layers)-1] if simple else list(range(max(0,idx-1),min(len(layers),idx+3))))
        candidates=[(layers[i],dispatch(layers[i].early_min_kwh,layers[i].early_max_kwh)) for i in ids]
        data=[(p["objective"]+float(l.fee_eur),l,p) for l,p in candidates if p["objective"] is not None]
        out["integer_search"]=[dict(pairs=l.pairs,status=p["status"],grid_eur=p["objective"]) for l,p in candidates]
        if data:
            _,l,p=min(data,key=lambda z:z[0])
            ans=arm(p,l,offset=l.fee_eur)
            # Failed comparisons cannot be silently discarded. A separately qualified physical
            # selected point is distinct from qualification of the optimal count selection.
            ans["selected_point_qualified"]=ans["qualified"]
            ans["qualified"]=bool(ans["qualified"] and (simple or h["status"]=="optimal")
                                and all(z["status"] in ("optimal","infeasible") for _,z in candidates))
            out["arms"]["joint"]=ans
        else:
            out["arms"]["joint"]=unavailable("no_integer_selection")
    if (row["window"],row["size"],row["fleet"],row["market"])==("primary",80,"sistig","hard"):
        joint=out["arms"]["joint"]
        out["directional_prices"]=[]
        if joint["qualified"]:
            base=joint["solver"]["fleet_kwh"]
            center=engine.fixed_loads(base)
            for j in (0,1):
                for delta in (-1.,1.):
                    changed=list(base)
                    changed[j]+=delta
                    if changed[j]<0:
                        out["directional_prices"].append(dict(window=j,delta_kwh=delta,status="negative_load"))
                        continue
                    side=engine.fixed_loads(changed)
                    valid=center["physical_pass"] and side["physical_pass"]
                    out["directional_prices"].append(dict(window=j,delta_kwh=delta,status=side["status"],
                        center_status=center["status"],conic_point_pass=bool(valid),eur_mwh=(
                        1000*(side["grid_cost"]-center["grid_cost"])/delta if valid else None)))
            out["directional_solves"]=1+sum(z["status"]!="negative_load" for z in out["directional_prices"])
    out["state"]="evaluated"
    out["native_solves"]=len(solves)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    dest=args.output
    dest.mkdir(exist_ok=False)
    (dest/"cells").mkdir()
    rows=roster()
    write_json(dest/"roster.json",rows)
    sizes=json.loads((ROOT/"result/opf_qualification/repair02/depot_sizes.json").read_text())
    admitted={}
    for day,path in zip(DAYS,(RAW/"DE-2024-01-17.json",RAW/"summer-after-cooldown/DE-2024-07-17.json")):
        members=json.loads(path.read_text())["records"]
        if len(members)!=24 or any(r["PriceArea"]!="DE" for r in members):
            raise ValueError("German price-area admission failed")
        local=ZoneInfo("Europe/Berlin")
        prices={datetime.fromisoformat(r["HourUTC"]+"+00:00").astimezone(local):r["SpotPriceEUR"] for r in members}
        if len(prices)!=24 or not all(t.date().isoformat()==day for t in prices):
            raise ValueError("bad German local hours")
        admitted[day]={t.hour:v for t,v in prices.items()}
    write_json(dest/"spot_ranges.json",{d:max(p.values())-min(p.values()) for d,p in admitted.items()})
    model=read_simbench_radial(ARCHIVE)
    profiles=read_matched_profiles(ARCHIVE,model)
    validator=NativeACValidator(ARCHIVE,model)
    for row in rows:
        st=time.monotonic()
        site=next(s for s in sizes if s["node"].endswith(" "+("78" if row["site"]=="near" else "68"))
                  and round(s["target_fraction"]*100)==row["size"])
        try:
            result=evaluate(row,model,validator,profiles[row["date"]],admitted[row["date"]],site)
        except Exception as exc:
            result=dict(**row,state="error",error=f"{type(exc).__name__}: {exc}",arms={})
            write_json(dest/"cells"/(row["id"]+".json"),result)
            raise  # stop a common implementation error instead of repeating it for all assignments
        result["elapsed_s"]=time.monotonic()-st
        write_json(dest/"cells"/(row["id"]+".json"),result)
        # The full reference arrays are only needed for scope-local deduplication.
        validator.references.clear()
        if len(list((dest/"cells").glob("*.json")))%12==0:
            print(row["id"],result["state"],flush=True)


if __name__=="__main__":
    main()
