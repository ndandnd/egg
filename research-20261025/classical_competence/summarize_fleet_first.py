"""Compact completed control receipts and losslessly archive large diagnostics."""
import gzip
import hashlib
import json
from pathlib import Path
import resource
import signal
import time
from fractions import Fraction

base = Path(__file__).resolve().parent
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
signal.alarm(90)
start, cpu = time.monotonic(), time.process_time()
master = json.loads((base/'fleet-first-attempt01/receipt.json').read_text())
result = {'scope': master['scope'], 'complete': master['complete'],
          'feasible_cases': master['feasible_cases'], 'cases': [], 'archives': []}
for c in master['cases']:
    folder = base/'fleet-first-attempt01'/c['case'].replace(':', '-')
    r = json.loads((folder/'receipt.json').read_text())
    result['cases'].append({**c, 'cost_float': float(Fraction(c['integrated_cost_exact'])),
         'solver_status': r['native']['status'], 'fleet_lower_bound': r['native']['lower_bound'],
         'physical_rows': r['inventory']['physical_rows'], 'columns': r['inventory']['columns'],
         'native_solve_wall_s': r['native']['wall_s'], 'failures': r['failures'],
         'stages': r['stages']})
    for name in ('native-capture.json', 'physical-inventory.jsonl'):
        source = folder/name
        archive = source.with_name(name+'.gz')
        digest = hashlib.sha256()
        with source.open('rb') as src, archive.open('xb') as dest:
            with gzip.GzipFile(filename='', mode='wb', fileobj=dest, mtime=0, compresslevel=6) as packed:
                while chunk := src.read(1024*1024):
                    digest.update(chunk); packed.write(chunk)
        result['archives'].append({'source': str(source.relative_to(base)),
            'archive': str(archive.relative_to(base)), 'source_sha256': digest.hexdigest(),
            'source_bytes': source.stat().st_size, 'archive_bytes': archive.stat().st_size})
result.update(postprocess_cpu_s=time.process_time()-cpu, postprocess_wall_s=time.monotonic()-start,
    measurement='one streaming source hash during lossless gzip; no duplicated verification or numerical rerun')
with (base/'fleet-first-summary.json').open('x') as target:
    json.dump(result, target, indent=2)
print(json.dumps({'complete': result['complete'], 'cases': result['cases']}, indent=2))
