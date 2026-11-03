"""One metadata reconciliation batch, with2.5s closure provision inside phase25."""
import hashlib
import json
from pathlib import Path
import time
START, CPU = time.monotonic(), time.process_time()
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'research-20261024/cf1-entry-repaired-v5d'
HERE = Path(__file__).resolve().parent
def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def times(path):
    values={line.split()[0]:float(line.split()[1]) for line in path.read_text().splitlines()}
    return values,max(values['real'],values['user']+values['sys'])+.02
result = read(BASE/'freeze-attempt01/result.json')
lock = read(BASE/'lock.json')
prior = read(ROOT/'research-20261024/cf1-entry-repaired-checks/attempt07-accounting.json')
assert result['passed'] and not result['source_changes'] and result['accounting_observations_complete']
assert result['termination']['reaped'] and result['termination']['group_absent']
assert not result['termination']['cleanup_errors'] and not result['termination']['probe_diagnostics']
assert lock['carried_charge_s']==prior['charged_cpu_s']==result['prior_charged_cpu_s']
whole, outer=times(BASE/'freeze-whole-wrapper-time.txt')
prep_times, prep=times(HERE/'freeze-preparation4-time.txt')
prep=max(prep,read(HERE/'freeze-preparation4.json')['charged_cpu_s'])
external=max(0.,outer-result['charged_cpu_s'])
current=result['charged_cpu_s']+external+prep+2.5
assert current<=25.
evidence=dict(prior['evidence_hashes'])
for path in [BASE/'lock.json',BASE/'freeze-attempt01/result.json',
             BASE/'freeze-attempt01/attempt.json',BASE/'freeze-attempt01/stdout.log',
             BASE/'freeze-attempt01/stderr.log',BASE/'design.json',BASE/'freeze-command.json',
             BASE/'freeze-whole-wrapper-time.txt',BASE/'freeze-whole-wrapper-output.json',
             HERE/'freeze-preparation4-time.txt',HERE/'freeze-preparation4.json',Path(__file__).resolve(),
             ROOT/'research-20261024/cf1-entry-repaired-checks/attempt07-accounting.json']:
    evidence[str(path)]=digest(path)
assert evidence[str(BASE/'lock.json')]==result['lock_sha256']
account={'policy':'cf1-entry-repaired-v5','phase':'metadata_freeze',
    'non_native_sample_policy':result['non_native_sample_policy'],
    'prior_charge_s':lock['carried_charge_s'],'current_charge_s':current,
    'charged_cpu_s':lock['carried_charge_s']+current,'internal_charge_s':result['charged_cpu_s'],
    'external_reconciliation_charge_s':external,'whole_wrapper_time':whole,
    'metadata_preparation_charge_s':prep,'metadata_preparation_time':prep_times,
    'conservative_closure_charge_s':2.5,'phase_limit_s':25.,
    'hard_total_ceiling_s':3000.,'dispatch_stop_s':2820.,'shutdown_reserve_s':180.,
    'freeze_passed':True,'metadata_freeze':True,'native_dispatch':False,
    'accounting_observations_complete':True,'owned_groups_absent_and_reaped':True,
    'accounting_unresolved':False,'charge_is_lower_bound':False,
    'historical_accounting_observations_complete':False,'prior_actual_cpu_s':None,
    'accepted_conservative_guard':True,'owned_pgids':result['termination']['owned_pgids'],
    'actual_receipt_cumulative_s':result['cumulative_qualification_charge_s'],
    'scope':'Actual v5d metadata closure with sampled non-native resources; all prior failures retained; no native dispatch or scientific qualification',
    'evidence_hashes':evidence}
assert account['prior_charge_s']+account['current_charge_s']==account['charged_cpu_s']
assert account['prior_charge_s']==prior['charged_cpu_s']
owned=account['owned_pgids']
assert type(owned) is list and owned and all(type(pgid) is int and pgid>0 for pgid in owned)
assert len(set(owned))==len(owned)
assert account['metadata_freeze'] is True and account['freeze_passed'] is True
assert account['hard_total_ceiling_s']==3000. and 'hard_ceiling_s' not in account
assert account['charged_cpu_s']+7.5+62.5+45.+30.<=2701.723449631016
assert (time.monotonic()-START)+(time.process_time()-CPU)+.05<=2.5
with (BASE/'freeze-accounting.json').open('x') as stream:
    json.dump(account,stream,indent=2);stream.write('\n')
print(json.dumps({'charged_cpu_s':account['charged_cpu_s'],'current_charge_s':current,
    'expected_native_reserved_end_s':account['charged_cpu_s']+145.,'proofs':len(evidence)}))
