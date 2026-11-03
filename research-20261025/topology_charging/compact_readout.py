"""Once-only compact stored-receipt readout; no project imports or numerical jobs."""
import time
WALL0=time.monotonic()
import hashlib,json,os,resource,signal,sys
from fractions import Fraction as Q
from pathlib import Path
HERE=Path(__file__).resolve().parent
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('Readout wall90')))
signal.setitimer(signal.ITIMER_REAL,90)
pins={}
def read(path):
    raw=path.read_bytes()
    pins[str(path)]=hashlib.sha256(raw).hexdigest()
    return raw
read(Path(__file__).resolve())
launch=json.loads(read(HERE/'READOUT_LAUNCH.json'))
r=json.loads(read(HERE/'attempt01/receipt.json'))
if not r.get('receipt_complete'):
    raise ValueError('Owner receipt incomplete; do not synthesize closeout')
def number(x):
    return None if x is None else float(Q(x))
rows=[]
for row in r['cells']:
    w=row.get('worker',{});a=w.get('point_agreement',w.get('objective_agreement',{}))
    rows.append(dict(index=row['index'],group=row.get('group'),route=row.get('route_source'),
      target=row.get('target_source'),attempted=row.get('attempted'),
      accepted=row.get('parent_endpoint_accepted'),qualified=row.get('cell_qualified'),
      returncode=row.get('returncode'),elapsed_s=row.get('parent_elapsed_s',row.get('elapsed_s')),
      worker_keys=list(w) if not w.get('cell_qualified') else None,
      calls=w.get('native_calls'),candidate=number(w.get('candidate_bill_exact')),
      fallback=number(w.get('fallback_bill_exact')),retained=number(w.get('true_bill_exact')),
      route_identity_method=w.get('route_identity_method'),
      objective_agreement=a,failures=w.get('failures'),parent_failures=row.get('failures'),
      qualified_flag=w.get('cell_qualified'),native_optimal=w.get('native_optimal'),
      helper=w.get('numerical',{})))
groups=[]
for g in r.get('summary',{}).get('groups',[]):
    points={}
    for target,c in g['target_point_comparisons'].items():
        points[target]={k:(number(v) if 'difference' in k and v is not None else v)
                       for k,v in c.items()}
    groups.append(dict(group=g['group'],services=g['services'],membership_stratum=g['membership_stratum'],
      canonical_paths_equal=g['canonical_paths_equal'],qualified_cells=g['qualified_cells'],points=points))
summary=r.get('summary',{})
out=dict(receipt_complete=True,owner_complete=r['receipt_complete'],owner_passed=r.get('passed'),
 accounting_complete=r.get('accounting_complete'),config_failure=r.get('config_failure'),
 resource_violation=r.get('resource_violation'),failures=r.get('failures'),findings=r.get('findings'),
 counts={k:v for k,v in summary.items() if k!='groups'},resources=r.get('resources'),
 package_cpu_prepublication=r.get('package_cpu_s_through_preparation'),
 package_elapsed_prepublication=r.get('package_elapsed_sum_s_through_preparation'),
 groups=groups,rows=rows,input_sha256=pins,
 interpretation='Displayed rational point contrasts, not ideal route ordering or optimization-gap bounds',
 readout_prepublication_cpu_s=sum((resource.getrusage(resource.RUSAGE_SELF).ru_utime,resource.getrusage(resource.RUSAGE_SELF).ru_stime)),
 readout_prepublication_elapsed_s=time.monotonic()-WALL0)
with (HERE/'COMPACT_READOUT.json').open('x') as f:
    json.dump(out,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({k:out[k] for k in ('owner_passed','accounting_complete','config_failure','resource_violation','failures','counts','resources','groups')},indent=2))
