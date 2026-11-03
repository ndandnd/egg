"""One bounded display export of the completed exact readout, no model/solver."""
import json
from fractions import Fraction as Q
from pathlib import Path
import re
import resource
import signal
import statistics
import time

resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
signal.alarm(30)
base=Path(__file__).resolve().parent
cpu0,wall0=time.process_time(),time.monotonic()
s=json.loads((base/'summary.json').read_text())
number=re.compile(r'^-?[0-9]+(?:/[0-9]+)?$')
def display(v):
    if isinstance(v,dict): return {k:display(x) for k,x in v.items()}
    if isinstance(v,list): return [display(x) for x in v]
    if isinstance(v,str) and number.fullmatch(v): return float(Q(v))
    return v
out={k:s.get(k) for k in ('finalization_complete','finalization_passed','denominators',
    'campaign_complete','campaign_passed','campaign_resources','campaign_elapsed_s',
    'continuation_eligibility_checks','learned_continuation','pairwise_summaries',
    'group_arm_summaries','validation_errors','fatal_rows','failures','invalid_admissions')}
out['acquisitions']=s['acquisitions']
out['non_successful_cells']=[r for r in s['cells'] if not r.get('method_success')]
out['post_hoc_arm_display']=[]
for arm in ('GNN','CatBoost','CA1','CoverCA1','random','full','fixed_route'):
    rows=[r for r in s['cells'] if r['arm']==arm]
    defined=[r for r in rows if r.get('cost_defined')]
    cost=[Q(r['operational_cost']) for r in defined]
    saving=[Q(r['E0_normalized_saving']) for r in defined if r.get('E0_normalized_saving') is not None]
    out['post_hoc_arm_display'].append(dict(arm=arm,planned=len(rows),defined=len(defined),
        method_accepted=sum(r.get('method_endpoint_accepted',False) for r in rows),
        method_success=sum(r.get('method_success',False) for r in rows),
        mean_cost=sum(cost,Q(0))/len(cost) if cost else None,
        median_cost=statistics.median(cost) if cost else None,
        mean_E0_normalized_saving=sum(saving,Q(0))/len(saving) if saving else None,
        median_E0_normalized_saving=statistics.median(saving) if saving else None))
# Fraction objects in added descriptive displays are converted explicitly.
def added(v):
    if isinstance(v,Q): return float(v)
    if isinstance(v,dict): return {k:added(x) for k,x in v.items()}
    if isinstance(v,list): return [added(x) for x in v]
    return v
out=added(display(out))
out['export_receipt']={'cpu_s_before_publication':time.process_time()-cpu0,
    'wall_s_before_publication':time.monotonic()-wall0,'cpu_cap_s':15,'wall_cap_s':30,
    'original_exact_summary_modified':False,'solver_calls':0,'inference_calls':0,'replay_calls':0,
    'extra_arm_aggregates_are_post_hoc_descriptive':True}
with (base/'COMPACT_RESULTS.json').open('x') as f:
    json.dump(out,f,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({k:out[k] for k in ('denominators','learned_continuation','post_hoc_arm_display','non_successful_cells')},indent=2))
