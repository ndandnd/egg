"""Exact minimum depot peak under each of the two declared committed covers."""
from fractions import Fraction
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.run_matched_opf import ROOT,make_fleet,write_json
rows=[]
for site in json.loads((ROOT/"result/opf_qualification/repair02/depot_sizes.json").read_text()):
    for kind in ("homogeneous","sistig"):
        fleet,_,_=make_fleet("primary",kind,site["chargers"],site["services_per_batch"])
        strong,fixed=fleet.strong_cover_layer(),fleet.fixed_cover_layer()
        def peak(layer):
            if layer is None:return None
            balanced=fleet.total_grid_kwh*fleet.early.hours/(fleet.early.hours+fleet.terminal.hours)
            e=min(max(balanced,layer.early_min_kwh),layer.early_max_kwh)
            return max(e/fleet.early.hours,(fleet.total_grid_kwh-e)/fleet.terminal.hours)
        ps,pf=peak(strong),peak(fixed)
        if ps is None or pf is None:raise ValueError("primary capacity cover missing")
        delta=pf-ps
        rows.append(dict(node=site["node"],n=site["services_per_batch"],fleet=kind,
          fixed_early_floor_kw=float(fixed.early_min_kwh/fleet.early.hours),
          strong_early_floor_kw=float(strong.early_min_kwh/fleet.early.hours),
          fixed_minimum_peak_kw=float(pf),strong_minimum_peak_kw=float(ps),reducible_peak_kw=float(delta),
          daily_kwh=float(fleet.total_grid_kwh),annual_use_hours_365=float(365*fleet.total_grid_kwh/ps),
          annual_capacity_low_eur=float(delta*Fraction("12.22")),annual_capacity_high_eur=float(delta*Fraction("88.64")),
          connection_BKZ_reduction_eur=float(delta*Fraction("95.64"))))
out=Path(sys.argv[1]);out.mkdir(exist_ok=False);write_json(out/"capacity.json",rows)
print(json.dumps(rows,indent=1))
