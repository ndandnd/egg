"""Summarize a completed pilot and losslessly archive its large diagnostics."""
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
wall, cpu = time.monotonic(), time.process_time()
master = json.loads((base/'attempt01/receipt.json').read_text())
out = {'scope': master.get('scope'), 'diagnostic_complete': master.get('complete'),
       'diagnostic_passed': master.get('passed'), 'failure': master.get('failure'),
       'cases': [], 'archives': []}
targets = {'scale:50685:40': 3, 'scale:50605:80': 5}
for c in master.get('cases', []):
    folder = base/'attempt01'/c['case'].replace(':', '-')
    receipt = json.loads((folder/'receipt.json').read_text())
    pool = json.loads((folder/'candidate-pool.json').read_text()) if (folder/'candidate-pool.json').exists() else {}
    native = receipt.get('native', {})
    out['cases'].append({**c, 'competence_target': targets[c['case']],
        'competence_passed': bool(c.get('accepted_within_offline120') and c.get('vehicles') is not None
                                 and c['vehicles'] <= targets[c['case']]),
        'cost_float': float(Fraction(c['integrated_cost_exact'])) if c.get('integrated_cost_exact') else None,
        'native_status': native.get('status'), 'restricted_fleet_lower_bound': native.get('lower_bound'),
        'native_solve_wall_s': native.get('wall_s'), 'failures': receipt.get('failures'),
        'cover_secondary': [x['secondary'] for x in pool.get('covers', [])],
        'cover_pairs': [x['matched_pairs'] for x in pool.get('covers', [])],
        'union_pairs': len(pool.get('selected_pairs', [])), 'boundaries': len(pool.get('all_boundary_modes', [])),
        'excluded_nonchronological_modes': len(pool.get('excluded_nonchronological_modes', [])),
        'stages': receipt.get('stages')})
    for name in ('native-capture.json', 'physical-inventory.jsonl'):
        source = folder/name
        if not source.exists():
            continue
        archive = source.with_name(name+'.gz')
        digest = hashlib.sha256()
        with source.open('rb') as src, archive.open('xb') as dest:
            with gzip.GzipFile(filename='',mode='wb',fileobj=dest,mtime=0,compresslevel=6) as packed:
                while chunk := src.read(1024*1024):
                    digest.update(chunk); packed.write(chunk)
        out['archives'].append({'source': str(source.relative_to(base)), 'archive': str(archive.relative_to(base)),
            'source_sha256': digest.hexdigest(), 'source_bytes': source.stat().st_size,
            'archive_bytes': archive.stat().st_size})
out['competence_passed'] = len(out['cases']) == 2 and all(c['competence_passed'] for c in out['cases'])
out.update(postprocess_cpu_s=time.process_time()-cpu, postprocess_wall_s=time.monotonic()-wall,
           measured_native_process_time=(base/'process-time.txt').read_text(),
           prior_reset_measured_cpu_s=146.47,
           legacy_conditional_guard_s=2546.091499549272, legacy_actual_review_cpu='UNKNOWN',
           legacy_reset=False, whole_session_exact_cpu_claim=False,
           archive_policy='same source streamed into SHA256 and lossless gzip; originals retained; no second hash audit')
with (base/'summary.json').open('x') as stream:
    json.dump(out, stream, indent=2)
print(json.dumps({'diagnostic_complete': out['diagnostic_complete'], 'competence_passed': out['competence_passed'],
                  'cases': [{k: c.get(k) for k in ('case','vehicles','cost_float','native_status',
                      'restricted_fleet_lower_bound','elapsed_including_receipt_s','competence_passed','pool',
                      'failures')} for c in out['cases']]}, indent=2))
