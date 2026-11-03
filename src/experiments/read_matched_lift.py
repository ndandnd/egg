"""Produce a per-assignment table without another optimization or power flow."""
import argparse
import csv
from fractions import Fraction
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original",type=Path)
    parser.add_argument("recovery",type=Path)
    parser.add_argument("csv_output",type=Path)
    args=parser.parse_args()
    recovered=json.loads((args.recovery/"results.json").read_text())["rows"]
    records=[]
    for r in recovered:
        cell=json.loads((args.original/"cells"/(r["id"]+".json")).read_text())
        record={k:r[k] for k in ("id","date","window","fleet","site","size","market","hull_status","hull_qualified")}
        record["state"]=r["state"]
        record["original_joint_qualified"]=cell["arms"]["joint"]["qualified"]
        for arm in ("strong","fixed"):
            a=r["arms"].get(arm,{})
            for k in ("buses","qualified","ac_total_eur","bracket_within_cent","upper_minus_native_lower_eur","early_adjustment_kwh"):
                record[arm+"_"+k]=a.get(k)
        s,f=(r["arms"].get(k,{}) for k in ("strong","fixed"))
        if s.get("qualified"):
            q=s["quarters"]
            record["backup_mwh"]=.25*sum(p["gen_mw"] for p in q)
            record["voltage_active_quarters"]=sum(bool(p["voltage_active"]) for p in q)
            record["thermal_active_quarters"]=sum(bool(p["thermal_active"]) for p in q)
        # Secondary numerical sensitivity for commitments on the adverse side of a strict hull point.
        # The fixed endpoint minimises the affine grid tangent in exactly these directional cases.
        if s.get("bracket_within_cent") and f.get("qualified"):
            h=cell["arms"]["hull"]["solver"]
            pe,pl=h["depot_price_per_mwh"]
            move=f["early_adjustment_kwh"]
            if move*(pe-pl)>0:
                e=float(Fraction(f["early_kwh_exact"]))
                late=cell["total_grid_kwh"]-e
                estimate=(h["grid_cost"]+f["fee_eur"]+
                          (pe*(e-h["fleet_kwh"][0])+pl*(late-h["fleet_kwh"][1]))/1000)
                record["fixed_tangent_minus_strong_ac_eur"]=estimate-s["ac_total_eur"]
                layers=[l for l in cell["layer_diagnostics"]["by_count"] if l["best_chargeable"]]
                m_max=max(l["pairs"] for l in layers)
                n_services=s["buses"]+m_max
                slope=(pe-pl)/1000
                endpoint="min_floor_grid_kwh" if slope>=0 else "common_ceiling_grid_kwh"
                hull_support=min(50*(n_services-l["pairs"])+slope*l[endpoint] for l in layers)
                fixed_support=f["fee_eur"]+slope*e
                record["fixed_dual_shift_minus_strong_ac_eur"]=(r["numerical_hull_lb"]+
                    fixed_support-hull_support-s["ac_total_eur"])
                record["fixed_ac_minus_strong_ac_eur"]=f["ac_total_eur"]-s["ac_total_eur"]
        records.append(record)
    with args.csv_output.open("x",newline="") as dest:
        writer=csv.DictWriter(dest,fieldnames=list(dict.fromkeys(k for r in records for k in r)),lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


if __name__=="__main__":
    main()
