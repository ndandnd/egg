"""One metered source05 preservation/closure batch, within parent5s provision."""
import hashlib
import json
from pathlib import Path
import resource
import time

START, CPU = time.monotonic(), time.process_time()
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'research-20261024/cf1-entry-repaired-checks'
HERE = Path(__file__).resolve().parent
FOLDER = BASE/'attempt05'
def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_new(path, value):
    with path.open('x') as stream: json.dump(value, stream, indent=2); stream.write('\n')
def whole(path):
    parts = {line.split()[0]: float(line.split()[1]) for line in path.read_text().splitlines()}
    return parts, max(parts['real'], parts['user']+parts['sys'])+.02

result, attempt = read(FOLDER/'result.json'), read(FOLDER/'attempt.json')
assert result['passed'] and result['termination']['reaped'] and result['termination']['group_absent']
assert result['source_changes']==[] and result['accounting_observations_complete']
previous = read(BASE/'attempt04/source-snapshot-manifest.json')['sources']
reusable = {entry['sha256']:entry['snapshot_path'] for entry in previous.values()}
evidence = dict(attempt['prior_evidence_hashes'])
manifest, new_count = {}, 0
for name, expected in attempt['source_hashes'].items():
    snapshot = reusable.get(expected)
    if snapshot is None:
        source = Path(name); snapshot = str(FOLDER/'source-snapshot'/source.relative_to(ROOT))
        target = Path(snapshot); target.parent.mkdir(parents=True, exist_ok=True)
        raw = source.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==expected, name
        target.write_bytes(raw); new_count += 1
    manifest[name] = {'snapshot_path':snapshot, 'sha256':expected}
    evidence[snapshot] = expected
manifest_path = FOLDER/'source-snapshot-manifest.json'
write_new(manifest_path, {'scope':'Exact passed source05 bytes; prior immutable snapshots reused without duplicate review hashes', 'sources':manifest})
for path in [manifest_path, Path(__file__).resolve(), FOLDER/'attempt.json', FOLDER/'result.json',
             FOLDER/'stdout.log', FOLDER/'stderr.log',
             BASE/'attempt05-design/whole-wrapper-time.txt', BASE/'attempt05-design/whole-wrapper-output.json',
             HERE/'manifest2-preparation-time.txt', HERE/'manifest2-preparation-output.json',
             BASE/'attempt05-design/preparation.json']:
    evidence[str(path)] = digest(path)
times, outer = whole(BASE/'attempt05-design/whole-wrapper-time.txt')
prep_times, prep = whole(HERE/'manifest2-preparation-time.txt')
prep = max(prep, read(BASE/'attempt05-design/preparation.json')['charged_cpu_s'])
external = max(0., outer-result['charged_cpu_s'])
preservation = (time.monotonic()-START)+(time.process_time()-CPU)+.05
parent = prep+1.+preservation+.75
assert parent<=5., parent
current = result['charged_cpu_s']+external+parent
prior = read(HERE/'failed-freeze-accounting.json')['charged_cpu_s']
assert prior==2443.974196631565 and current<=20.
account = {'policy':'cf1-entry-repaired-v5','phase':'resumption2_source_check',
    'prior_charge_s':prior,'current_charge_s':current,'charged_cpu_s':prior+current,
    'internal_charge_s':result['charged_cpu_s'],'external_reconciliation_charge_s':external,
    'whole_wrapper_time':times,'manifest_preparation_charge_s':prep,'manifest_preparation_time':prep_times,
    'source_preservation_charge_s':preservation,'conservative_static_preparation_charge_s':1.,
    'conservative_finalization_charge_s':.75,'parent_provision_charge_s':parent,'parent_provision_limit_s':5.,
    'accounting_observations_complete':True,'observation_scope':'Fresh source05 only; accepted historical actual CPU remains unknown',
    'historical_accounting_observations_complete':False,'prior_actual_cpu_s':None,'accepted_conservative_guard':True,
    'owned_pgids':result['termination']['owned_pgids'],'owned_groups_absent_and_reaped':True,
    'hard_total_ceiling_s':3000.,'dispatch_stop_s':2820.,'shutdown_reserve_s':180.,
    'package_hard_end_s':2651.723449631016,'source_phase_hard_end_s':2463.974196631565,
    'check_passed':True,'selected_tests':result['executed_tests'],'native_dispatch':False,'metadata_freeze':False,
    'source_snapshot_manifest':str(manifest_path),'new_snapshots':new_count,'reused_snapshots':len(manifest)-new_count,
    'evidence_hashes':evidence}
write_new(BASE/'attempt05-accounting.json', account)
print(json.dumps({'charged_cpu_s':account['charged_cpu_s'],'current_charge_s':current,
    'proofs':len(evidence),'new_snapshots':new_count,'reused_snapshots':len(manifest)-new_count}))
