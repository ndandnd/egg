"""Minimal wrapper in the previously admitted isolated artifact runtime.

No execution authority: parent freezes exact source/command and meters the
single render before this is invoked. Fresh output directory forbids overwrite.
"""
import time
started=time.monotonic()
import signal
def expired(signum,frame):raise TimeoutError('45-second whole artifact boundary')
signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,45)
import resource
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
import importlib.metadata
import json
import os
from pathlib import Path
import runpy
import sys

here=Path(__file__).resolve().parent
runtime='/private/tmp/egg-paper-plot-libs-20261029'
receipt=json.loads((here/'PLOT_RUNTIME_RECEIPT.json').read_text())
if receipt['status']!='PASS' or receipt['resource_pass'] is not True or receipt['target']!=runtime:
    raise ValueError('Artifact runtime is not admitted')
if not sys.flags.isolated or not sys.flags.no_site or sys.flags.optimize:
    raise ValueError('Require -I -S -B without optimization')
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    if os.environ.get(key)!='1':raise ValueError('Require one-thread artifact environment')
sys.path.insert(0,runtime)
if importlib.metadata.version('matplotlib')!='3.9.4':raise ValueError('Artifact Matplotlib version mismatch')
runpy.run_path(str(here/'make_transition_figure.py'),run_name='__main__',init_globals={'_artifact_started':started})
