"""One metered v6 source preservation/closure batch, within parent5s provision."""
import hashlib
import json
from pathlib import Path
import resource
import time

START, CPU = time.monotonic(), time.process_time()
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'research-20261025/cf1-responsive-checks'
HERE = Path(__file__).resolve().parent
FOLDER = BASE/'attempt01'
def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_new(path, value):
    with path.open('x') as stream: json.dump(value, stream, indent=2); stream.write('\n')
def whole(path):
    parts = {line.split()[0]: float(line.split()[1]) for line in path.read_text().splitlines()}
    return parts, max(parts['real'], parts['user']+parts['sys'])+.02

result, attempt = read(FOLDER/'result.json'), read(FOLDER/'attempt.json')
assert result['revision']==6 and result['policy']=='cf1-responsive-supervision-v6'
assert result['passed'] and result['termination']['reaped'] and result['termination']['group_absent']
assert result['source_changes']==[] and result['accounting_observations_complete']
previous = read(ROOT/'research-20261024/cf1-entry-repaired-checks/attempt08/source-snapshot-manifest.json')['sources']
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
write_new(manifest_path, {'scope':'Exact passed v6 source bytes; immutable source08 snapshots reused without duplicate review hashes', 'sources':manifest})
for path in [manifest_path, Path(__file__).resolve(), FOLDER/'attempt.json', FOLDER/'result.json',
             FOLDER/'stdout.log', FOLDER/'stderr.log',
             BASE/'attempt01-design/whole-wrapper-time.txt', BASE/'attempt01-design/whole-wrapper-output.json',
             HERE/'prepare-source-gate-time.txt', HERE/'prepare-source-gate-output.json',
             BASE/'attempt01-design/preparation.json']:
    evidence[str(path)] = digest(path)
times, outer = whole(BASE/'attempt01-design/whole-wrapper-time.txt')
prep_times, prep = whole(HERE/'prepare-source-gate-time.txt')
prep = max(prep, read(BASE/'attempt01-design/preparation.json')['charged_cpu_s'])
external = max(0., outer-result['charged_cpu_s'])
preservation = (time.monotonic()-START)+(time.process_time()-CPU)+.05
parent = prep+1.+preservation+.75
assert parent<=5., parent
current = result['charged_cpu_s']+external+parent
prior = read(HERE/'budget-adoption.json')['charged_cpu_s']
assert prior==attempt['carried_charge_s']==result['carried_charge_s'] and current<=30.
account = {'policy':'cf1-responsive-supervision-v6','phase':'responsive_source_check',
    'non_native_sample_policy':result['non_native_sample_policy'],
    'prior_charge_s':prior,'current_charge_s':current,'charged_cpu_s':prior+current,
    'internal_charge_s':result['charged_cpu_s'],'external_reconciliation_charge_s':external,
    'whole_wrapper_time':times,'manifest_preparation_charge_s':prep,'manifest_preparation_time':prep_times,
    'source_preservation_charge_s':preservation,'conservative_static_preparation_charge_s':1.,
    'conservative_finalization_charge_s':.75,'parent_provision_charge_s':parent,'parent_provision_limit_s':5.,
    'accounting_observations_complete':True,'observation_scope':'Fresh metered v6 fake-execution source/preparation/preservation only; historical CPU and legacy owner observations remain incomplete',
    'historical_accounting_observations_complete':False,'prior_actual_cpu_s':None,'accepted_conservative_guard':True,
    'historical_actual_cpu_s':None,'legacy_owner_observations_complete':False,
    'owned_pgids':result['termination']['owned_pgids'],'owned_groups_absent_and_reaped':True,
    'hard_total_ceiling_s':3600.,'dispatch_stop_s':3420.,'shutdown_reserve_s':180.,
    'package_hard_end_s':3026.723449631016,'source_phase_hard_end_s':prior+30.,
    'check_passed':True,'selected_tests':result['executed_tests'],'native_dispatch':False,'metadata_freeze':False,
    'source_gate_passed':True,'primitive_passed':False,'metadata_freeze_passed':False,
    'no_native_primitive_performed':False,'research_data_loaded_for_analysis':False,
    'model_source_asset_access':False,'automatic_retry_performed':False,
    'source_snapshot_manifest':str(manifest_path),'new_snapshots':new_count,'reused_snapshots':len(manifest)-new_count,
    'evidence_hashes':evidence}
assert account['prior_charge_s']+account['current_charge_s']==account['charged_cpu_s']
assert account['owned_pgids'] and len(set(account['owned_pgids']))==len(account['owned_pgids'])
assert all(type(pgid) is int and pgid>0 for pgid in account['owned_pgids'])
assert account['charged_cpu_s']+20.+25.+65.+62.5+120.+45.<=3026.723449631016
write_new(BASE/'attempt01-accounting.json', account)
print(json.dumps({'charged_cpu_s':account['charged_cpu_s'],'current_charge_s':current,
    'proofs':len(evidence),'new_snapshots':new_count,'reused_snapshots':len(manifest)-new_count}))
