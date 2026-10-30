"""Explicit new artifact runtime; original unsuccessful authoring stays saved."""
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
packages={item.metadata['Name']:item.version for item in importlib.metadata.distributions(path=[runtime])}
if packages.get('matplotlib')!='3.9.4': raise ValueError('Plotting version mismatch')
with (here/'PLOT_RUNTIME_PACKAGES.json').open('x') as stream: json.dump(packages,stream,indent=2)
runpy.run_path(str(here/'make_figures.py'),run_name='__main__')
