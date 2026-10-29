"""One newly frozen five-state energy-flow diagnostic; no retry or fallback solve.

Detailed native/ledger/checker packets are streamed directly into gzip. Master
and per-stage receipts stay compact and retain every assigned stop state.
"""
import argparse
import copy
from dataclasses import asdict
from fractions import Fraction as Q
import gc
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import resource
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL='research-20261029/public_energy_flow/'
MODEL='research-20261029/public_support_resolution/'
SOURCES=[REL+n for n in ('worker.py','run.py','PROTOCOL.md')]+[
    MODEL+n for n in ('energy_flow.py','exact_dual.py','independent_verify.py')]+[
    'src/egglab/__init__.py','src/egglab/native_recharge.py']
ASSIGNED=('Q0','ROOT_QP','MIQP','PRICE_LP','PRICE_MIP')
ALLOWANCES={'Q0':45,'ROOT_QP':90,'MIQP':300,'PRICE_LP':60,'PRICE_MIP':240}
CASE_REVISION='253c1e29295e766b3889fc8f5c28d9808e00b3d6'
TRANSFER_REVISION='929bd0052b064c2aa9ef10b77fa067b70c7653af'
PRODUCER_SOURCE='ef0b088193bc19527476f9db9e632c37379d9a2a'
INPUT_PATHS=dict(case='research-20261029/public_support_resolution/attempt01/case_descriptor.json',
    upper='research-20261029/public_terminal_certificate/cycle01/new_candidate.json',
    upper_replay='research-20261029/public_terminal_certificate/cycle01/independent_replay.json',
    transfer='research-20261029/public_terminal_certificate/TRANSFER_AUTHORITY.json')


def encode(value):
    if isinstance(value,Q): return str(value)
    raise TypeError(type(value).__name__)


def write(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,default=encode,allow_nan=False)
        stream.write('\n')


def compressed(path,value):
    with gzip.open(path,'xt',encoding='utf-8',compresslevel=6) as stream:
        json.dump(value,stream,default=encode,allow_nan=False,separators=(',',':'))
        stream.write('\n')


def usage():
    own,children=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime,
                peak_rss_bytes=max(own.ru_maxrss,children.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))


def load_module(name,relative,cache,package=False):
    module=types.ModuleType(name)
    module.__file__=str(ROOT/relative)
    module.__package__=name if package else name.rpartition('.')[0]
    if package: module.__path__=[]
    sys.modules[name]=module
    exec(compile(cache[relative],module.__file__,'exec'),module.__dict__)
    return module


def case_from_dict(nr,data):
    values=dict(data)
    values['trips']=tuple(nr.Trip(**row) for row in data['trips'])
    values['movements']=tuple(nr.Movement(**dict(row,legs=tuple(nr.Leg(**leg) for leg in row['legs'])))
                              for row in data['movements'])
    values['resources']=tuple(nr.Resource(**row) for row in data['resources'])
    values['market_edges_min']=tuple(data['market_edges_min'])
    return nr.NativeCase(**values)


def summary(packet):
    native=packet.get('native',{})
    audit=packet.get('replay')
    exact=packet.get('exact_certificate')
    result=dict(raw_status=native.get('raw_status'),solution_count=native.get('solution_count'),
                optimize_called=native.get('optimize_called'),
                inclusive_elapsed_s=native.get('inclusive_elapsed_s'),
                raw_objective=native.get('raw_objective'),raw_bound=native.get('raw_bound'),
                raw_gap=native.get('raw_gap'),native_start_acceptance=native.get('native_start_acceptance'),
                exact_global_optimum_claim=False,external_incumbent_substituted=False)
    if audit is not None:
        result['replay']=dict(strict_pass=audit['strict_pass'],physical_strict_pass=audit['physical_strict_pass'],
            violations=len(audit['violations']),classification=audit['classification'],
            certified_physical_upper=str(audit['objective_exact']) if audit.get('objective_is_certified_physical_upper') else None)
    if exact is not None:
        result['exact_certificate']=dict(status=exact['status'],stage=exact.get('stage'),
                                       lower_bound=exact.get('lower_bound'),reason=exact.get('reason'))
    if 'qualification_status' in packet:
        result['qualification_status']=packet['qualification_status']
        result['negative_controls']=packet['negative_controls']
        result['known_exact_value']=packet['known_exact_value']
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--source-revision',required=True)
    args=parser.parse_args()
    out=Path(args.out).resolve()
    started=time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU,(1700,1700))
    rows,failures,cache,manifest=[],[],{},{}
    active=None
    def event(value):
        with (out/'events.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(worker_elapsed_s=time.monotonic()-started,**value),default=encode,allow_nan=False)+'\n')
    def funding(seconds):
        observation=usage()
        if observation['cpu_s']+seconds+120>=1700 or time.monotonic()-started+seconds+180>=2200:
            raise RuntimeError('Insufficient complete next-stage funding plus closure reserve')
        if observation['peak_rss_bytes']>5*1024**3:
            raise RuntimeError('Observed RSS ceiling exceeded')
    def stage(name,action):
        nonlocal active
        seconds=ALLOWANCES[name]
        funding(seconds)
        active=dict(id=name,status='ATTEMPTED',native_allowance_s=seconds)
        rows.append(active)
        anchor=time.monotonic()
        event(dict(event='stage_begin',id=name,seconds=seconds))
        packet=action()
        packet.update(id=name,stage_clock_scope='prepublication diagnostic with compressed detailed packet')
        compressed(out/(name+'.json.gz'),packet)
        elapsed=time.monotonic()-anchor
        active.update(status='DELIVERED' if elapsed<=seconds+45 else 'LATE',
                      stage_elapsed_s=elapsed,stage_clock_scope='through complete gzip packet serialization',
                      packet=name+'.json.gz',summary=summary(packet),resources=usage())
        write(out/(name+'.status.json'),active)
        event(dict(event='stage_end',id=name,status=active['status'],elapsed_s=time.monotonic()-anchor))
        answer=dict(active)
        active=None
        del packet
        gc.collect()
        return answer
    try:
        control_raw=(HERE/'LAUNCH.json').read_bytes()
        control=json.loads(control_raw)
        if control.get('status')!='FROZEN' or control.get('run_id')!='attempt01' or control.get('source_revision')!=args.source_revision:
            raise ValueError('No exact frozen worker launch authority')
        if (control.get('package_cpu_s'),control.get('package_wall_s'),control.get('worker_cpu_s'),control.get('worker_wall_s'))!=(1800,2400,1700,2200):
            raise ValueError('Resource declaration mismatch')
        manifest['LAUNCH.json']=dict(bytes=len(control_raw),sha256=hashlib.sha256(control_raw).hexdigest())
        for relative in SOURCES:
            raw=(ROOT/relative).read_bytes()
            committed=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',
                args.source_revision+':'+relative],cwd=ROOT,timeout=2)
            if raw!=committed: raise ValueError('Frozen source mismatch: '+relative)
            cache[relative]=raw
            manifest[relative]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        packages={'gurobipy':importlib.metadata.version('gurobipy')}
        if packages!={'gurobipy':'12.0.1'}: raise ValueError('Unexpected backend package version')
        admitted={}
        specs=control.get('inputs',[])
        if len(specs)!=4 or {s.get('id') for s in specs}!=set(INPUT_PATHS):
            raise ValueError('Exactly four fixed-path prospectively pinned inputs required')
        for spec in specs:
            if (not re.fullmatch('[0-9a-f]{40}',spec.get('revision','')) or
                ('sha256' in spec and not re.fullmatch('[0-9a-f]{64}',spec['sha256'])) or
                not isinstance(spec.get('path'),str) or not spec['path'] or
                Path(spec['path']).is_absolute() or '..' in Path(spec['path']).parts):
                raise ValueError('PENDING input revision/pin/path cannot be consumed')
            expected_revision=CASE_REVISION if spec['id']=='case' else TRANSFER_REVISION
            if spec['path']!=INPUT_PATHS[spec['id']] or spec['revision']!=expected_revision:
                raise ValueError('Input is not the fixed declared source-bound transfer')
            raw=(ROOT/spec['path']).read_bytes()
            committed=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',
                spec['revision']+':'+spec['path']],cwd=ROOT,timeout=2)
            if raw!=committed: raise ValueError('Input differs from its closed pinned commit: '+spec['id'])
            digest=hashlib.sha256(raw).hexdigest()
            if 'sha256' in spec and digest!=spec['sha256']: raise ValueError('Input byte-pin mismatch: '+spec['id'])
            admitted[spec['id']]=json.loads(raw)
            manifest['input:'+spec['id']]=dict(spec,bytes=len(raw),consumed_sha256=digest)
        case_spec=next(s for s in specs if s['id']=='case')
        if case_spec['revision']!=CASE_REVISION:
            raise ValueError('Public descriptor must come from the declared revision')
        write(out/'source_admission.json',dict(revision=args.source_revision,files=manifest,packages=packages,python=sys.version))
        package=load_module('egglab','src/egglab/__init__.py',cache,True)
        nr=load_module('egglab.native_recharge','src/egglab/native_recharge.py',cache)
        package.native_recharge=nr
        flow=load_module('energy_flow',MODEL+'energy_flow.py',cache)
        exact=load_module('exact_dual',MODEL+'exact_dual.py',cache)
        verifier=load_module('independent_verify',MODEL+'independent_verify.py',cache)
        def native(case,method,seconds,continuous=False,prices=None,start=None):
            built=flow.build(case,continuous=continuous)
            try:
                return flow.solve(built,method=method,seconds=seconds,prices=prices,
                                  startmovementids=start,record=event)
            finally:
                built['model'].dispose()
                built.clear()
                gc.collect()
        def qualification():
            def leg(start,end): return nr.Leg('D','D',start,end,0)
            q=nr.NativeCase(name='literal-two-service-energy-flow',
                trips=(nr.Trip('A',0,20,'D','D',15),nr.Trip('B',30,50,'D','D',15)),
                movements=(nr.Movement('outA','pullout',None,'A',(leg(0,0),)),
                    nr.Movement('outB','pullout',None,'B',(leg(30,30),)),
                    nr.Movement('inA','pullin','A',None,(leg(20,20),)),
                    nr.Movement('inB','pullin','B',None,(leg(50,50),)),
                    nr.Movement('AB','direct','A','B',(leg(20,30),))),
                resources=(nr.Resource(0,120,40,40,1),),market_edges_min=(0,60,120),
                depot='D',max_vehicles=2,battery_kwh=20,reserve_kwh=0,
                terminal_open_min=0,recharge_deadline_min=120,vehicle_cost=7)
            result=native(q,'miqp',30,continuous=True)
            certificate=exact.verify_and_bound(asdict(q),result)
            known=Q(14)+30*Q(float(.2))+225*Q(float(1/900))
            if result.get('raw_status')!=2 or certificate['status']!='CERTIFIED_LOWER_BOUND':
                raise ValueError('Literal continuous QP qualification unavailable')
            bound=Q(certificate['lower_bound'])
            if not bound<=known or known-bound>Q(1,10**7):
                raise ValueError('Literal exact lower certificate is invalid or too weak')
            if result['exactledger']['minimum_fleet_proof']['minimum_fleet']!=2:
                raise ValueError('Literal semantic fleet cut missing')
            if result.get('raw_objective') is None or abs(Q(result['raw_objective'])-known)>Q(1,10**7):
                raise ValueError('Literal native objective differs from known QP value')
            controls=[]
            for kind in ('row-rhs','finite-bound','minimum-fleet-metadata','objective'):
                bad=copy.deepcopy(result)
                ledger=bad['exactledger']
                if kind=='row-rhs': ledger['rows'][0]['rhs']+=1
                elif kind=='finite-bound': ledger['variables'][0]['upper']+=1
                elif kind=='minimum-fleet-metadata': ledger['minimum_fleet_proof']['minimum_fleet']+=1
                else:
                    i,value=ledger['objective']['linear'][0]
                    ledger['objective']['linear'][0]=(i,value+1)
                rejected=exact.verify_and_bound(asdict(q),bad)
                if rejected['status']!='REJECTED': raise ValueError('Literal corruption accepted '+kind)
                controls.append(dict(id=kind,rejected=True,stage=rejected['stage']))
            return dict(native=result,exact_certificate=certificate,qualification_status='PASS',
                        known_exact_value=known,known_display_value='20.25',negative_controls=controls)
        stage('Q0',qualification)
        case_data=admitted['case']
        case=case_from_dict(nr,case_data)
        if case.identity()!='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7':
            raise ValueError('Public descriptor identity mismatch')
        upper=admitted['upper']
        recorded=admitted['upper_replay']
        authority=admitted['transfer']
        # These fields are metadata comparisons only. Never follow a path or
        # select a different artifact based on values inside the authority.
        expected=dict(status='QUALIFIED_TRANSFER',producer_source_revision=PRODUCER_SOURCE,
            producer_frozen_control='6ed44942',
            producer_namespace='research-20261029/public_terminal_certificate/cycle01',
            case_input_revision=CASE_REVISION,case_path=INPUT_PATHS['case'],
            case_identity='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7',
            candidate_path=INPUT_PATHS['upper'],replay_path=INPUT_PATHS['upper_replay'],
            results_path='research-20261029/public_terminal_certificate/cycle01/results.json',
            verifier_source_path=MODEL+'independent_verify.py',
            candidate_fields=['selected_movement_ids','charge_by_interval'],fleet_count=2,producer_exit=0)
        if any(authority.get(key)!=value for key,value in expected.items()):
            raise ValueError('Source-bound transfer metadata mismatch')
        for key in ('strict_pass','physical_strict_pass','objective_is_certified_physical_upper',
                    'worker_reaped','resource_pass'):
            if authority.get(key) is not True:
                raise ValueError('Unqualified producer transfer: '+key)
        if (recorded.get('strict_pass') is not True or recorded.get('physical_strict_pass') is not True
            or recorded.get('objective_is_certified_physical_upper') is not True
            or Q(recorded['objective_exact'])!=Q(authority['upper_exact'])
            or len(recorded['routes'])!=authority['fleet_count']
            or set(upper)!=set(expected['candidate_fields'])):
            raise ValueError('Passed producer replay/candidate does not match transfer authority')
        certified_loads=list(map(Q,recorded['loads_exact']))
        if len(certified_loads)!=len(case.market_edges_min)-1 or any(x<0 for x in certified_loads):
            raise ValueError('Transferred certified load dimension/sign mismatch')
        # Reuse the passed strict certificate through its source-bound closed
        # commit. Do not repeat that physical replay merely to reuse the upper.
        fixed_prices=[Q(float(.2))+Q(float(1/900))*load for load in certified_loads]
        start=list(upper['selected_movement_ids'])
        protected=dict(objective_exact=Q(recorded['objective_exact']),loads_exact=certified_loads,
                       prices_exact=fixed_prices,selection=start,
                       source='source-bound separately certified terminal construction; no duplicate replay',
                       transfer_revision=TRANSFER_REVISION,producer_source_revision=PRODUCER_SOURCE,
                       metadata_linkage_verified=True,
                       never_substituted_for_native_method_result=True)
        write(out/'protected_incumbent.json',protected)
        def public(continuous,method,seconds):
            result=native(case,method,seconds,continuous=continuous,
                          prices=fixed_prices if method=='linear' else None,
                          start=None if continuous else start)
            packet=dict(native=result)
            if method=='linear' and list(map(Q,result.get('prices',[])))!=fixed_prices:
                raise ValueError('Caller fixed own-price vector differs from exported linear prices')
            if continuous:
                packet['exact_certificate']=exact.verify_and_bound(case_data,result)
            elif result.get('candidate') is not None:
                # This raw integer candidate is replayed exactly once. A failure
                # is preserved, with no construction or incumbent substitution.
                packet['replay']=verifier.verify(case_data,result['candidate'])
            return packet
        stage('ROOT_QP',lambda:public(True,'miqp',90))
        stage('MIQP',lambda:public(False,'miqp',300))
        stage('PRICE_LP',lambda:public(True,'linear',60))
        stage('PRICE_MIP',lambda:public(False,'linear',240))
    except BaseException as exc:
        text=type(exc).__name__+': '+str(exc)
        failures.append(text)
        if active is not None:
            active.update(status='FAILED',reason=text)
            try: write(out/(active['id']+'.status.json'),active)
            except OSError: pass
        event(dict(event='worker_failure',reason=text))
    present={row['id'] for row in rows}
    for name in ASSIGNED:
        if name not in present:
            rows.append(dict(id=name,status='UNATTEMPTED',reason='prior failure or insufficient full-stage funding'))
    observation=usage()
    elapsed=time.monotonic()-started
    resource_pass=observation['cpu_s']<1700 and elapsed<2200 and observation['peak_rss_bytes']<=5*1024**3
    status='CLOSED' if not failures and all(row['status']=='DELIVERED' for row in rows) and resource_pass else 'CLOSED_FAILED'
    report=dict(status=status,assigned=5,rows=rows,failures=failures,resources=observation,
                elapsed_s=elapsed,resource_pass=resource_pass,
                fixed_prices_source='separately exact-certified external upper; never reset by this campaign',
                scientific_scope='classical native proposals plus independently reconstructed exact lower bounds and strict integer replay',
                exact_public_optimum_or_support_claim=False,
                compressed_detail_policy='native candidates, ledgers and certificates only inside stage gzip packets; no repeated raw exports')
    write(out/'results.json',report)
    write(out/'worker_receipt.json',dict(status=status,elapsed_s=time.monotonic()-started,**usage(),
          resource_pass=resource_pass,worker_cpu_limit_s=1700,worker_wall_allowance_s=2200,
          memory_limit_bytes=5*1024**3,threads=1,no_native_retry=True))
    return 0 if status=='CLOSED' else 1


if __name__=='__main__':
    raise SystemExit(main())
