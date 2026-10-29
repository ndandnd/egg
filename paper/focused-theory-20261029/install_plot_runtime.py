"""Isolated artifact-only dependency setup; never modifies scientific venv."""
import json
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

started=time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU,(80,80))
signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('117s setup boundary')))
signal.alarm(117)
here=Path(__file__).resolve().parent
target=Path('/private/tmp/egg-paper-plot-libs-20261029')
if target.exists(): raise FileExistsError('New isolated setup target required')
target.mkdir()
command=[sys.executable,'-m','pip','install','--disable-pip-version-check','--no-cache-dir',
         '--target',str(target),'matplotlib==3.9.4']
failure=None
code=None
try:
    with (here/'plot-runtime-install.log').open('x') as stream:
        result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=110)
        code=result.returncode
except BaseException as exc:
    failure=type(exc).__name__+': '+str(exc)
signal.alarm(0)
own,child=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
cpu=own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime
elapsed=time.monotonic()-started
receipt=dict(status='PASS' if code==0 and not failure else 'FAILED',command=command,
    target=str(target),exit_code=code,failure=failure,cpu_s=cpu,elapsed_s=elapsed,
    resource_pass=cpu<100 and elapsed<120,scientific_environment_changed=False,
    scope='Artifact runtime setup only; external meter authoritative; all failure spending retained')
with (here/'PLOT_RUNTIME_RECEIPT.json').open('x') as stream: json.dump(receipt,stream,indent=2)
raise SystemExit(0 if receipt['status']=='PASS' and receipt['resource_pass'] else 1)
