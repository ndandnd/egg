"""Construct whole-fleet dispatches at the registered hull load and check fresh AC upper costs."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.run_matched_opf import ARCHIVE, ROOT, OFFERS, make_fleet, roster, write_json
from experiments.qualify_simbench_static import AC_OPTIONS, source_results
from egglab.matched_profiles import NativeACValidator, read_matched_profiles
from egglab.simbench_radial import read_simbench_radial


def check_schedule(fleet, layer, energy, cover):
    schedule = fleet.service_witness(layer.pairs, energy, cover=cover)
    morning, afternoon = [], []
    for i, j, early, late in schedule:
        a = fleet.morning_kwh[i] if i is not None else 0
        b = fleet.afternoon_kwh[j] if j is not None else 0
        remaining = fleet.usable_kwh-a
        before_pm = remaining+early*fleet.efficiency
        end = before_pm-b+late*fleet.efficiency
        if not (0<=remaining<=before_pm<=fleet.usable_kwh and before_pm>=b and end==fleet.usable_kwh):
            raise ValueError("battery witness failed")
        if not (0<=early<=fleet.early.plug_kw*fleet.early.hours and 0<=late<=fleet.terminal.plug_kw*fleet.terminal.hours):
            raise ValueError("individual plug energy failed")
        if i is not None:
            morning.append(i)
        if j is not None:
            afternoon.append(j)
    energies = [sum(s[k] for s in schedule) for k in (2,3)]
    if (sorted(morning)!=list(range(len(fleet.morning_kwh))) or sorted(afternoon)!=list(range(len(fleet.afternoon_kwh)))
        or len(schedule)!=layer.buses or energies!=[energy,fleet.total_grid_kwh-energy]
        or energies[0]>fleet.early.grid_limit_kwh or energies[1]>fleet.terminal.grid_limit_kwh):
        raise ValueError("fleet-wide witness failed")
    return energies


def main():
    import pandapower as pp

    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--repaired-only",action="store_true")
    args=parser.parse_args()
    args.output.mkdir(exist_ok=False)
    assigned=json.loads((args.inputs/"roster.json").read_text())
    if assigned!=roster():
        raise ValueError("original roster mismatch")
    if args.repaired_only:
        old=ROOT/"src/runs/opf-matched-20261103-attempt01/cells"
        assigned=[r for r in assigned if json.loads((old/(r["id"]+".json")).read_text())["arms"]["hull"]["status"]=="optimal_inaccurate"]
        if len(assigned)!=25: raise ValueError("repair cohort mismatch")
    model=read_simbench_radial(ARCHIVE)
    profiles=read_matched_profiles(ARCHIVE,model)
    validator=NativeACValidator(ARCHIVE,model)
    quarters={p["time_local"]:p for day in profiles.values() for p in day}
    sizes=json.loads((ROOT/"result/opf_qualification/repair02/depot_sizes.json").read_text())
    # Use the same admitted prices. The two distinct late delivery hours must be billed separately.
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from experiments.run_matched_opf import RAW
    prices={}
    for name in ("DE-2024-01-17.json","summer-after-cooldown/DE-2024-07-17.json"):
        records=json.loads((RAW/name).read_text())["records"]
        if len(records)!=24 or any(r["PriceArea"]!="DE" for r in records):
            raise ValueError("German price-area mismatch")
        for r in records:
            stamp=datetime.fromisoformat(r["HourUTC"]+"+00:00").astimezone(ZoneInfo("Europe/Berlin"))
            prices[(stamp.date().isoformat(),stamp.hour)]=r["SpotPriceEUR"]

    @lru_cache(None)
    def flow(stamp,node,net_load):
        q=quarters[stamp]
        if stamp not in validator.base_quarters:
            validator.base_quarters[stamp]=validator._background(q)
        grid=deepcopy(validator.base_quarters[stamp])
        native=validator._locate(node)[1]
        pp.create_load(grid,native,p_mw=net_load,q_mvar=0.)
        try:
            pp.runpp(grid,**AC_OPTIONS)
            ac=source_results(grid,validator.tables)
        except Exception as exc:
            return dict(ok=False,error=str(exc))
        active_v=[i for i,v in ac["voltage_pu"].items() if model["bus_index"][i] not in (0,*model["passive_open_ends"])
                  and (v-float(validator.tables["Node"][i]["vmMin"])<=1e-5 or float(validator.tables["Node"][i]["vmMax"])-v<=1e-5)]
        active_t=[k for kind,label in (("lines","Line"),("transformers","Transformer")) for k,e in ac[kind].items()
                  if e["loading_percent"]>=float(validator.tables[label][k]["loadingMax"])*(1-1e-4)]
        return dict(ok=bool(ac["converged"] and ac["within_native_limits"]),grid_import_mw=ac["import_mw"],
                    native_limits=ac["native_limits"],voltage_active=active_v,thermal_active=active_t)

    results=[]
    for desc in assigned:
        r=json.loads((args.inputs/"cells"/(desc["id"]+".json")).read_text())
        if any(r.get(k)!=v for k,v in desc.items()):
            raise ValueError("cell identity mismatch")
        h=r["arms"]["hull"]
        out=dict(**desc,hull_status=h["status"],hull_qualified=h["qualified"],arms={})
        results.append(out)
        if h.get("early_kwh") is None:
            out["state"]=r["state"] if r["state"]=="structural_infeasible" else "no_hull_point"
            continue
        site=next(s for s in sizes if s["node"].endswith(" "+("78" if r["site"]=="near" else "68"))
                  and round(100*s["target_fraction"])==r["size"])
        fleet,_,_=make_fleet(r["window"],r["fleet"],site["chargers"],site["services_per_batch"])
        e=Fraction(str(h["early_kwh"]))
        lb=h["solver"]["native_bound"]
        if lb is not None:
            lb+=h["objective_eur"]-h["solver"]["objective"]
        out.update(state="tested",numerical_hull_lb=lb,hull_eur=h["objective_eur"])
        for cover,layer in (("strong",fleet.strong_cover_layer()),("fixed",fleet.fixed_cover_layer())):
            if layer is None:
                out["arms"][cover]=dict(qualified=False,reason="absent_cover")
                continue
            target=min(max(e,layer.early_min_kwh),layer.early_max_kwh)
            en=check_schedule(fleet,layer,target,cover)
            bill=float(layer.fee_eur)
            steps=[]
            offer=OFFERS[r["market"]]
            for p in h["quarters"]:
                stamp=p["time"]
                hour=quarters[stamp]["hour"]
                w=int(hour!=12)
                duration=(fleet.early,fleet.terminal)[w].hours
                mw=float(en[w]/(duration*1000))
                gen=min(max(p["backup_mw"],0.),1.) if offer is not None else 0.
                ac=flow(stamp,site["node"],mw-gen)
                steps.append(dict(time=stamp,load_mw=mw,gen_mw=gen,**ac))
                if ac["ok"]:
                    bill+=.25*(ac["grid_import_mw"]*prices[r["date"],hour]+gen*(offer or 0))
            ok=len(steps)==(12 if r["window"]=="primary" else 8) and all(z["ok"] for z in steps)
            difference=bill-lb if ok and lb is not None else None
            bound_ok=(h["status"]=="optimal" and lb is not None and abs(h["objective_eur"]-lb)<=.01)
            out["arms"][cover]=dict(qualified=ok,buses=layer.buses,early_kwh_exact=str(target),
                 early_adjustment_kwh=float(target-e),fee_eur=float(layer.fee_eur),ac_total_eur=bill if ok else None,
                 upper_minus_native_lower_eur=difference,bracket_within_cent=bool(bound_ok and difference is not None and abs(difference)<=.01),
                 quarters=steps)
    write_json(args.output/"results.json",dict(rows=results,distinct_ac_calls=flow.cache_info().misses))
    print("rows",len(results),"distinct_ac_calls",flow.cache_info().misses)


if __name__=="__main__":
    main()
