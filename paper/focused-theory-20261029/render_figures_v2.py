"""Separate layout revision in the admitted isolated artifact runtime."""
import importlib.metadata
import json
from pathlib import Path
import runpy
import sys
here=Path(__file__).resolve().parent
runtime='/private/tmp/egg-paper-plot-libs-20261029'
receipt=json.loads((here/'PLOT_RUNTIME_RECEIPT.json').read_text())
if receipt['status']!='PASS' or not receipt['resource_pass'] or receipt['target']!=runtime:
    raise ValueError('Artifact runtime is not admitted')
sys.path.insert(0,runtime)
if importlib.metadata.version('matplotlib')!='3.9.4': raise ValueError('Version mismatch')
runpy.run_path(str(here/'make_figures_v2.py'),run_name='__main__')
