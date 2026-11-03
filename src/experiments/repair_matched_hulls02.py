"""One Gurobi continuation for each previously inaccurate matched hull."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.run_matched_opf import ROOT,RAW,ARCHIVE,DAYS,roster,evaluate,write_json
from egglab.simbench_radial import read_simbench_radial
from egglab.matched_profiles import NativeACValidator,read_matched_profiles

p=argparse.ArgumentParser(); p.add_argument("output",type=Path); a=p.parse_args()
a.output.mkdir(exist_ok=False)
old=ROOT/"src/runs/opf-matched-20261103-attempt01/cells"
rows=[r for r in roster() if json.loads((old/(r["id"]+".json")).read_text())["arms"]["hull"]["status"]=="optimal_inaccurate"]
prior=ROOT/"src/runs/opf-matched-20261103-gurobi01"
rows=[r for r in rows if not json.loads((prior/(r["id"]+".json")).read_text())["arms"]["hull"]["qualified"]]
if len(rows)!=17: raise ValueError("expected exactly 17 unresolved Gurobi calls")
write_json(a.output/"roster.json",rows)
model=read_simbench_radial(ARCHIVE); profiles=read_matched_profiles(ARCHIVE,model); ac=NativeACValidator(ARCHIVE,model)
sizes=json.loads((ROOT/"result/opf_qualification/repair02/depot_sizes.json").read_text())
prices={}
for day,name in zip(DAYS,("DE-2024-01-17.json","summer-after-cooldown/DE-2024-07-17.json")):
    recs=json.loads((RAW/name).read_text())["records"]
    if len(recs)!=24 or any(r["PriceArea"]!="DE" for r in recs): raise ValueError("bad DE records")
    prices[day]={datetime.fromisoformat(r["HourUTC"]+"+00:00").astimezone(ZoneInfo("Europe/Berlin")).hour:r["SpotPriceEUR"] for r in recs}
for r in rows:
    site=next(s for s in sizes if s["node"].endswith(" "+("78" if r["site"]=="near" else "68")) and round(s["target_fraction"]*100)==r["size"])
    packet=evaluate(r,model,ac,profiles[r["date"]],prices[r["date"]],site,solver="GUROBI",hull_only=True)
    write_json(a.output/(r["id"]+".json"),packet)
    print(r["id"],packet["arms"]["hull"]["status"],packet["arms"]["hull"]["qualified"],flush=True)
    ac.references.clear()
