"""One-shot completed-receipt summary and lossless archival; no numerical rerun."""
import gzip
import hashlib
import json
from pathlib import Path
import resource
import signal
import time
from fractions import Fraction

BASE = Path(__file__).resolve().parent
signal.alarm(180)
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
start, cpu = time.monotonic(), time.process_time()
root = json.loads((BASE / 'attempt01/receipt.json').read_text())
out = {'scope': root['scope'], 'cohort_complete': root['complete'],
       'feasible_cases': root['feasible_cases'], 'cases': [], 'archives': [],
       'native_process_time': (BASE / 'process-time.txt').read_text(),
       'native_observed_peak_rss_bytes': root['observed_peak_rss_bytes']}
for row in root['cases']:
    path = BASE / 'attempt01' / row['case'].replace(':', '-') / 'receipt.json'
    d = json.loads(path.read_text())
    comp = d.get('completion', {})
    brief = {**row, 'constructed_vehicles': d.get('constructed_vehicles'),
             'stages': d.get('stages'), 'failures': d.get('failures'),
             'completion_status': comp.get('status'),
             'completion_error': comp.get('error'),
             'completion_error_type': comp.get('error_type'),
             'historical_context': d.get('historical_graph_context')}
    if row.get('objective_exact'):
        brief['objective_float'] = float(Fraction(row['objective_exact']))
    for name in ('failures', 'error', 'termination_reason', 'status'):
        if name in comp:
            value = comp[name]
            brief['completion_' + name] = value if len(str(value)) < 4000 else str(value)[:4000]
    out['cases'].append(brief)
    del d, comp
    archive = path.with_suffix('.json.gz')
    if archive.exists():
        raise FileExistsError(archive)
    h = hashlib.sha256()
    with path.open('rb') as source, archive.open('xb') as dest:
        with gzip.GzipFile(filename='', mode='wb', fileobj=dest, mtime=0, compresslevel=6) as packed:
            while chunk := source.read(1024*1024):
                h.update(chunk)
                packed.write(chunk)
    out['archives'].append({'source': str(path.relative_to(BASE)),
                            'archive': str(archive.relative_to(BASE)),
                            'source_sha256': h.hexdigest(),
                            'source_bytes': path.stat().st_size,
                            'archive_bytes': archive.stat().st_size,
                            'verification': 'streamed same source bytes into SHA256 and gzip; no second hash pass'})
out['postprocess_cpu_s'] = time.process_time() - cpu
out['postprocess_wall_s'] = time.monotonic() - start
out['postprocess_peak_rss_bytes_darwin'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
target = BASE / 'summary.json'
with target.open('x') as stream:
    json.dump(out, stream, indent=2)
print(json.dumps(out, indent=2))
