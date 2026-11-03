"""One narrow export of existing economic/qualification receipts; no project APIs."""
import time
T0=time.monotonic()
import hashlib,json,os,resource,signal
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path
H=Path(__file__).resolve().parent
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('Export wall60')))
signal.setitimer(signal.ITIMER_REAL,60)
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve(),H/'ECONOMIC_EXPORT_LAUNCH.json')}
r=json.loads((H/'attempt01/receipt.json').read_text())
first=json.loads((H/'COMPACT_READOUT.json').read_text())
if not r['receipt_complete'] or not first['receipt_complete'] or len(r['cells'])!=32:
    raise ValueError('Require complete32-cell owner and closed first export')
def f(x): return None if x is None else float(Q(x))
rows=[]; exact_points={}
for c in r['cells']:
    w=c.get('worker',{});s=w.get('stats',{});a=w.get('numerical_agreement',{})
    exact_points[(c['group'],c['route_source'],c['target_source'])] = (
        Q(w['candidate_bill_exact']) if w.get('candidate_bill_exact') is not None else None,
        Q(a['e_agree_exact']) if a.get('e_agree_exact') is not None else None)
    rows.append(dict(index=c['index'],group=c['group'],route=c['route_source'],target=c['target_source'],
      qualified=c.get('cell_qualified'),calls=w.get('native_calls'),native_status=s.get('Status'),
      native_optimal=s.get('native_optimal'),copy_pass=w.get('copy_contract',{}).get('passed'),
      parent_elapsed_s=c.get('parent_elapsed_s'),worker_peak_rss_bytes=w.get('resources',{}).get('peak_rss_bytes'),
      route_identity_method=w.get('route_identity_method'),used_fallback=w.get('used_fallback'),
      C=f(w.get('candidate_bill_exact')),B=f(w.get('fallback_bill_exact')),U=f(w.get('true_bill_exact')),
      N=w.get('native_point'),
      F=f(w.get('baseline_F_exact')),Ebar=f(w.get('original_Ebar_exact')),
      gain=f(w.get('charging_gain_exact')),gain_over_original_Ebar=f(w.get('charging_gain_over_original_Ebar')),
      e_agree=f(a.get('e_agree_exact')),source_guards_passed=a.get('source_guards_passed'),
      fallback_discrepancy=w.get('optimal_candidate_fallback_discrepancy'),
      native_bound=w.get('native_bound'),native_lower_bound=w.get('native_lower_bound'),
      quality={k:s.get(k) for k in ('MaxVio','ConstrVio','BoundVio','DualVio','ComplVio','ConstrResidual','DualResidual')},
      decomposition={k:(f(v) if k.endswith('_exact') else v) for k,v in w.get('selected_decomposition',{}).items()}))
groups=[]
for g in r['selected_groups']:
    cells=[c for c in rows if c['group']==g['group']]
    controls=[]
    if g['canonical_paths_equal']:
        for t in ('source0','source1'):
            pair={c['route']:c for c in cells if c['target']==t}
            a,b=pair['source0'],pair['source1']
            ca,ea=exact_points[(g['group'],'source0',t)]
            cb,eb=exact_points[(g['group'],'source1',t)]
            defined=all(x is not None for x in (ca,ea,cb,eb))
            delta,bound=(cb-ca,ea+eb) if defined else (None,None)
            controls.append(dict(target=t,defined=defined,
              point_delta=f(delta),point_delta_exact=str(delta) if defined else None,
              agreement_sum=f(bound),agreement_sum_exact=str(bound) if defined else None,
              above_agreement_screen=abs(delta)>bound if defined else None))
    gains=[c['gain'] for c in cells if c['gain'] is not None]
    ratios=[c['gain_over_original_Ebar'] for c in cells if c['gain_over_original_Ebar'] is not None]
    groups.append(dict(group=g['group'],services=g['services'],stratum=g['membership_stratum'],
      canonical_paths_equal=g['canonical_paths_equal'],cells_planned=4,cells_present=len(cells),
      qualified=sum(bool(c['qualified']) for c in cells),gain_denominator=len(gains),ratio_denominator=len(ratios),
      mean_retained_charging_gain=sum(gains)/len(gains) if len(gains)==4 else None,
      mean_retained_gain_over_fixed_Ebar=sum(ratios)/len(ratios) if len(ratios)==4 else None,
      same_route_numeric_checks=controls))
out=dict(receipt_complete=True,input_source_sha256=pins,
 owner_receipt_identity_backreference=first['input_sha256'][str(H/'attempt01/receipt.json')],
 cells_planned=32,groups_planned=8,rows=rows,groups=groups,
 counts=dict(qualified=sum(bool(c['qualified']) for c in rows),native_status=dict(Counter(str(c['native_status']) for c in rows)),
 route_identity=dict(Counter(str(c['route_identity_method']) for c in rows)),
 used_fallback=sum(bool(c['used_fallback']) for c in rows),
 source_guards=sum(c['source_guards_passed'] is True for c in rows),
 fallback_discrepancies=sum(bool(c['fallback_discrepancy']) for c in rows),
 native_bound_null=sum(c['native_bound'] is None for c in rows),
 max_parent_elapsed_s=max(c['parent_elapsed_s'] for c in rows),
 max_worker_observed_rss_bytes=max(c['worker_peak_rss_bytes'] for c in rows)),
 interpretation='Feasible point diagnostics; source agreement is not an optimization-gap bound; ideal ordering UNRESOLVED',
 prepublication_cpu_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,
 prepublication_elapsed_s=time.monotonic()-T0)
with (H/'ECONOMIC_EXPORT.json').open('x') as s:
    json.dump(out,s,indent=2,allow_nan=False);s.write('\n');s.flush();os.fsync(s.fileno())
print(json.dumps({k:out[k] for k in ('counts','groups')},indent=2))
