"""Separate retrospective physical-unit screen and one reduced static Gurobi check."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from egglab.radial_opf import solve_radial
from egglab.simbench_radial import read_simbench_radial
from egglab.two_window_opf import cone_screen
from experiments.compare_simbench_static import compare


def screen(net, point):
    if point.get("p_series_send_mw") is None:
        return dict(status=point["status"], mixed_physical_pass=False, error=point.get("error"))
    v=np.asarray(point["voltage_pu"])**2
    w=v[net["parent"]]/np.asarray(net["tap_ratio"])**2
    checks=cone_screen(point["p_series_send_mw"],point["q_series_send_mvar"],w,
                       np.asarray(point["current_sq_pu"]),net["base_mva"])
    limits=max(point[k] for k in ("limit_violation_max_pu","balance_max_pu","voltage_eq_max_pu"))
    return dict(status=point["status"],original_scope_pass=point["point_ac_residuals_pass"],
                import_mw=point["import_mw"],import_mvar=point["import_mvar"],loss_mw=point["loss_mw"],
                legacy_cone_abs_pu=point["cone_abs"],legacy_cone_rel=point["cone_rel"],
                other_residual_max_pu=limits, **checks, mixed_physical_pass=bool(
                    point["status"]=="optimal" and limits<=1e-7 and not checks["cone_failed_edges"]))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive",type=Path)
    parser.add_argument("raw_static_dir",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    with args.output.open("x") as sink:
        native=read_simbench_radial(args.archive,base_mva=10.)
        ac=json.loads((args.raw_static_dir/"reference.json").read_text())
        prior={}
        for file,base in (("point.json",10.),("open-ends-point.json",10.),
                          ("native-base-point.json",1.)):
            point=json.loads((args.raw_static_dir/file).read_text())
            # Parent, tap and voltage/per-unit observation belong to this exact
            # physical layout on either base. Restore the original point's base.
            prior[file]=screen(dict(native["solver"],base_mva=base),point)
        net=native["solver"]
        point=solve_radial(**net,price=50.,hours=1.,open_end_leaves=native["passive_open_ends"],
                           solver="GUROBI")
        gurobi=screen(net,point)
        if point["voltage_pu"] is not None:
            gurobi["against_saved_AC"]=compare(native,point,ac)
        out=dict(scope="Three retrospective numerical labels; one new reduced static Gurobi solve.",
                 archive=args.archive.name,base_mva=10.,prior_decisions_immutable=True,
                 per_branch_criterion="abs(P²+Q²-v*l*Sbase²) <= 1e-5 MVA² + 1e-5 max(abs(P²+Q²),abs(v*l*Sbase²)); P,Q in MW/MVAr",
                 background="independent static raw CSV, no fleet", prior=prior, gurobi=gurobi)
        json.dump(out,sink,indent=2,allow_nan=False)
        sink.write("\n")
    print(json.dumps({"prior":{p:(r["status"],r["mixed_physical_pass"]) for p,r in prior.items()},
                      "gurobi":gurobi},allow_nan=False))


if __name__=="__main__":
    main()
