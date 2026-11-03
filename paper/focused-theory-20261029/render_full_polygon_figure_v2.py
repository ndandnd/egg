"""Bounded one-shot renderer; no authority until parent separately freezes/launches.

Whole invocation proposed allowance 50 CPU/60 wall; internal45 CPU/55 wall
leaves closure headroom. Fresh versioned outputs are exclusive, no retry.
"""
import time
started=time.monotonic()
import signal
def expired(signum,frame):raise TimeoutError('55-second whole figure boundary')
signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,55)
import resource
resource.setrlimit(resource.RLIMIT_CPU,(45,45))
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys

here=Path(__file__).resolve().parent;root=here.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--source-revision',required=True)
args=parser.parse_args()
if not re.fullmatch('[0-9a-f]{40}',args.source_revision):raise ValueError('Require frozen40hex source revision')
if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize):
    raise ValueError('Require -I -S -B without optimization')
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    if os.environ.get(key)!='1':raise ValueError('Require one-thread artifact environment')
manifest={};cache={}
for name in ('make_full_polygon_figure_v2.py','render_full_polygon_figure_v2.py'):
    raw=(here/name).read_bytes()
    frozen=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',
        args.source_revision+':paper/focused-theory-20261029/'+name],cwd=root,timeout=2)
    if raw!=frozen:raise ValueError('Figure source differs from frozen revision: '+name)
    cache[name]=raw;manifest[name]=dict(revision=args.source_revision,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
runtime='/private/tmp/egg-paper-plot-libs-20261029'
receipt=json.loads((here/'PLOT_RUNTIME_RECEIPT.json').read_text())
if receipt['status']!='PASS' or receipt['resource_pass'] is not True or receipt['target']!=runtime:
    raise ValueError('Artifact runtime is not admitted')
sys.path.insert(0,runtime)
if importlib.metadata.version('matplotlib')!='3.9.4':raise ValueError('Artifact Matplotlib version mismatch')
body=cache['make_full_polygon_figure_v2.py']
exec(compile(body,str(here/'make_full_polygon_figure_v2.py'),'exec'),
    {'__name__':'__main__','__file__':str(here/'make_full_polygon_figure_v2.py'),
     '_artifact_started':started,'_source_manifest':manifest})
own=resource.getrusage(resource.RUSAGE_SELF);kids=resource.getrusage(resource.RUSAGE_CHILDREN)
cpu=own.ru_utime+own.ru_stime+kids.ru_utime+kids.ru_stime
if cpu>=50 or time.monotonic()-started>=60:raise RuntimeError('Complete figure allowance exceeded')
signal.setitimer(signal.ITIMER_REAL,0)
