"""One-shot physical replay audit of terminal screen witnesses; never optimization.

Run from the worktree with PYTHONPATH=src and the existing .venv-local interpreter.
No native event logs or raw stdout/stderr are read. Output files are exclusive-create.
"""
from __future__ import annotations
import hashlib
import importlib.abc
import json
import os
from pathlib import Path
import platform
import sys
import time
from fractions import Fraction

for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
BANNED=('mip','gurobipy','pyscipopt','torch','catboost','sklearn')
class ForbidOptimizationImports(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in BANNED:raise RuntimeError('Forbidden numerical/model import: '+fullname)
        return None
sys.meta_path.insert(0,ForbidOptimizationImports())
ROOT=Path(__file__).resolve().parent.parent
LOCK=ROOT/'research-20261017/local-assets-v3.json'
RUNS=ROOT/'research-20261017/local-screen-v3'
OUT=ROOT/'research-20261017/FINAL_REPLAY_VERIFICATION.json'
MD=ROOT/'research-20261017/FINAL_REPLAY_VERIFICATION.md'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stable(value):return hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest()
def read(path,hashes):
    hashes[str(path.relative_to(ROOT))]=sha(path)
    return json.loads(path.read_text())
def forbidden(*args,**kwargs):raise RuntimeError('Optimization/model building is prohibited in physical audit')

def main():
    started=time.monotonic();cpu=time.process_time()
    if OUT.exists() or MD.exists():raise FileExistsError('Audit outputs already exist; refusing duplicate/overwrite')
    lock=json.loads(LOCK.read_text());hashes={str(LOCK.relative_to(ROOT)):sha(LOCK)}
    source_mismatches=[];asset_mismatches=[]
    for field,destination in (('sources',source_mismatches),('assets',asset_mismatches)):
        for name,expected in lock[field].items():
            if sha(name)!=expected:destination.append(name)
    if source_mismatches or asset_mismatches:raise RuntimeError('Immutable source/model hash mismatch; audit cannot proceed')
    from egglab import claude_cases,native_recharge as nr,native_hull as nh
    from egglab import physical_learning_cases as bank
    nr._optimize_once=forbidden
    for module in (nr,nh):
        for name in ('build_feasible_model','solve_planner','solve_pricing','verify_global'):
            if hasattr(module,name):setattr(module,name,forbidden)
    expected={(c['case_key'],seed,arm) for c in lock['manifest']['cohorts']['screen']
              for seed in lock['manifest']['solver_seeds'] for arm in lock['arms']}
    seen=set();mismatches=[];records=[];casecache={};counts={a:{'decisions':0,'supervisor_valid':0,
        'replayed_valid':0,'exact_bill_matches':0,'nonvalid_censored':0,'nonvalid_uncensored':0,
        'worker_accepted_but_not_endpoint_valid':0} for a in lock['arms']}
    binding=read(RUNS/'campaign.json',hashes)
    if binding!={'stage':'screen','lock_sha256':sha(LOCK),'mock':False}:raise RuntimeError('Campaign binding mismatch')
    folders=sorted(p for p in RUNS.iterdir() if p.is_dir())
    for folder in folders:
        row=read(folder/'result.json',hashes);sup=read(folder/'supervisor.json',hashes);attempt=read(folder/'attempt.json',hashes)
        task=row['task'];key=(task['case_key'],task['seed'],task['arm'])
        if key not in expected or key in seen:raise RuntimeError('Unknown/duplicate task')
        seen.add(key);arm=task['arm'];counts[arm]['decisions']+=1
        issues=[]
        if attempt.get('task')!=task or attempt.get('lock_sha256')!=sha(LOCK) or stable(task)[:20]!=folder.name:
            issues.append('attempt_task_or_lock_hash_mismatch')
        if row.get('lock_sha256')!=sha(LOCK):issues.append('result_lock_hash_mismatch')
        valid=sup.get('endpoint_valid') is True
        record={'case_key':task['case_key'],'solver_seed':task['seed'],'arm':arm,
                'supervisor_valid':valid,'endpoint_censored':sup.get('endpoint_censored'),
                'replay_pass':None,'exact_bill_match':None,'issues':issues}
        if not valid:
            counts[arm]['nonvalid_censored' if sup.get('endpoint_censored') is True else 'nonvalid_uncensored']+=1
            if row.get('accepted_valid') is True:counts[arm]['worker_accepted_but_not_endpoint_valid']+=1
        else:
            counts[arm]['supervisor_valid']+=1
            if row.get('accepted_valid') is not True or sup.get('endpoint_censored') is not False:
                issues.append('inconsistent_validity_flags')
            if sup.get('returncode')!=0 or sup.get('failure') or sup.get('missing_worker_receipt'):
                issues.append('valid_endpoint_with_infrastructure_failure')
            try:
                plan=read(folder/'plan.json',hashes);savedreplay=read(folder/'replay.json',hashes)
                if task['case_key'] not in casecache:
                    case=claude_cases.make(task['case_key']);casecache[task['case_key']]=(case,bank.market(case,'day'))
                case,market=casecache[task['case_key']];mapping=lock['cases'][task['case_key']]
                if case.identity()!=mapping['identity'] or [m.id for m in case.movements]!=mapping['movement_ids']:
                    raise ValueError('full_case_identity_or_movement_mapping_mismatch')
                if row.get('case_identity')!=case.identity() or plan.get('case_identity')!=case.identity():
                    raise ValueError('result_or_plan_case_identity_mismatch')
                replay=nr.replay_native(case,plan)
                record['replay_pass']=replay.get('replay_ok') is True
                if not record['replay_pass']:issues.append('independent_full_case_replay_failed')
                else:counts[arm]['replayed_valid']+=1
                actual=Fraction(replay['ops_cost'])+nh.supply(market,replay['load'])
                saved=Fraction(row['bill_exact']);record['exact_bill_match']=actual==saved
                if actual==saved:counts[arm]['exact_bill_matches']+=1
                else:issues.append('exact_bill_mismatch');record.update(saved_bill_exact=str(saved),recomputed_bill_exact=str(actual))
                record['stored_replay_projection_match']=all(savedreplay.get(k)==replay[k] for k in ('replay_ok','load','ops_cost','grid_kwh','consumption_kwh'))
                if not record['stored_replay_projection_match']:issues.append('stored_replay_projection_mismatch')
            except Exception as exc:
                issues.append('audit_exception:'+type(exc).__name__+':'+str(exc))
        if issues:mismatches.append(record)
        records.append(record)
    if seen!=expected:raise RuntimeError(f'Incomplete cohort: {len(expected-seen)} missing tasks')
    forbidden_imports=sorted(name for name in sys.modules if name.split('.')[0] in BANNED)
    if forbidden_imports:raise RuntimeError('Forbidden imports found: '+repr(forbidden_imports))
    validcount=sum(c['supervisor_valid'] for c in counts.values())
    report={'scope':'independent physical replay and exact-bill verification of every stored supervisor-valid synthetic-development endpoint; no optimization or final-test claim',
            'passed':not mismatches,'decisions':len(records),'supervisor_valid_endpoints':validcount,
            'nonvalid_endpoints':len(records)-validcount,'counts_by_arm':counts,'mismatch_count':len(mismatches),
            'mismatches':mismatches,'records':records,'input_sha256':hashes,'lock_sha256':sha(LOCK),
            'source_sha256':sha(__file__),'locked_source_files_verified':len(lock['sources']),
            'locked_model_artifacts_verified':len(lock['assets']),'forbidden_imports':forbidden_imports,
            'optimizer_calls':0,'model_builds':0,'training_calls':0,'threads':1,'host':platform.uname()._asdict(),
            'wall_s':time.monotonic()-started,'cpu_s':time.process_time()-cpu}
    with OUT.open('x') as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    lines=['# Final physical replay verification','',
           f"Audit {'PASS' if report['passed'] else 'FAIL'}: {validcount} supervisor-valid endpoints audited from {len(records)} completed decisions; {len(mismatches)} mismatches.",'',
           '| Arm | Decisions | Supervisor valid | Replay passed | Exact bills matched | Censored nonvalid | Other nonvalid |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for arm,c in counts.items():lines.append('| '+arm+' | '+' | '.join(str(c[k]) for k in ('decisions','supervisor_valid','replayed_valid','exact_bill_matches','nonvalid_censored','nonvalid_uncensored'))+' |')
    lines+=['',f"Wall {report['wall_s']:.3f} s; process CPU {report['cpu_s']:.3f} s. No optimizer/model/training imports or calls. Source and model artifact hashes matched the immutable lock.",'',
            'Every audited plan was replayed on its original full generated case, with day tariff. Exact Fraction(ops_cost) + native_hull.supply(load) matched the stored exact bill. Stored validity/censoring of the remaining endpoints was preserved; failures did not become successes.',
            '', 'Evidence JSON includes per-cell results, source/lock/input hashes and mismatches. Raw solver event logs and stdout/stderr were not read. This is a physical-witness audit of synthetic development evidence, not a new solver experiment or final test.']
    with MD.open('x') as f:f.write('\n'.join(lines)+'\n')
    print(json.dumps({k:report[k] for k in ('passed','decisions','supervisor_valid_endpoints','nonvalid_endpoints','mismatch_count','wall_s','cpu_s')}))
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
