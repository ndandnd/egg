"""One prospectively frozen uncertainty-learning campaign; no automatic retry."""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
METHODS=('mean','ridge','quadratic_ridge','boosted_trees','neural_small_mse',
         'neural_large_mse','neural_large_dfl','blind_large_mse','blind_large_dfl',
         'conditional_mean_reference','perfect_information_reference','fixed_conditional_reference')
THREADS=('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
         'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS')

def write(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    tmp.replace(path)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--anchor',type=float,required=True)
    parser.add_argument('--source-receipt',type=Path,required=True)
    args=parser.parse_args()
    folder=HERE/'attempt01'
    end=args.anchor+6980
    started=time.monotonic()
    report=dict(status='RUNNING',receipt_complete=False,failures=[],planned_bank_calls=128,
        planned_test_calls=768,planned_test_groups=8,planned_test_contexts=64,
        bank_rows=[],test_rows=[],bank_complete=False,fit_complete=False,
        source_admitted=False,primary_native_optimize_count=0,scope='Synthetic development mechanism; consumption-only affine system cost')
    stage='admission'
    def check(reserve=0.):
        now=time.monotonic()
        usage=resource.getrusage(resource.RUSAGE_SELF)
        rss=usage.ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        if now+reserve>=end or usage.ru_utime+usage.ru_stime+reserve>=5320:
            raise TimeoutError('Campaign inclusive budget or full-next-stage funding exhausted')
        if rss>5*1024**3 or any(os.environ.get(k)!='1' for k in THREADS):
            raise RuntimeError('Campaign observed RSS/thread environment violation')
    def stop(signum,frame):
        raise TimeoutError('Campaign stop signal '+str(signum))
    def cost(u,load):
        return sum((.2+float(v)/900)*float(l)+float(l)**2/1800 for v,l in zip(u,load))
    def topology(plan):
        return sorted([v['movements'] for v in plan['vehicles']])
    def compact(raw):
        return {k:v for k,v in raw.items() if k not in
            ('admitted_plan','retained_witness','witness_replay','helper_result','events')}
    try:
        resource.setrlimit(resource.RLIMIT_CPU,(5340,5340))
        for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGALRM,signal.SIGXCPU):
            signal.signal(sig,stop)
        signal.setitimer(signal.ITIMER_REAL,max(.01,end-time.monotonic()))
        check(20)
        if args.source_receipt.resolve()!=folder/'source_receipt.json':
            raise ValueError('Source receipt path not literal owned path')
        source=json.loads(args.source_receipt.read_text())
        launch=json.loads((HERE/'LAUNCH.json').read_text())
        if launch['mode']!='FROZEN' or launch['review_disposition']!='PASS':
            raise ValueError('Unfrozen source cannot generate or fit')
        # The owner has already checked each consumed source buffer once.
        if source.get('source_admitted') is not True or source.get('source_revision')!=launch['source_revision']:
            raise ValueError('Owner source receipt is incomplete or differently bound')
        report['source_admitted']=True
        report['source_revision']=launch['source_revision']
        sys.path[:0]=[str(HERE),str(ROOT/'src')]
        import numpy as np
        import physics
        import learning
        import importlib.metadata
        report['environment']={name:importlib.metadata.version(name) for name in
            ('numpy','scipy','scikit-learn','torch','mip','gurobipy')}
        if report['environment']!=launch['packages']:
            raise ValueError('Frozen installed package versions differ; no generation')
        report['python']=sys.version
        stage='prospective_construction'
        groups={}; aliases={}
        for seed in physics.SEEDS:
            check(10)
            split=physics.split_of(seed)
            n={'train':24,'validation':16,'test':8}[split]
            case=physics.make_case(seed); witness=physics.make_witness(case)
            descriptor=asdict(case)
            physical_descriptor=dict(descriptor);physical_descriptor.pop('name')
            canonical=json.dumps(physical_descriptor,sort_keys=True,separators=(',',':')).encode()
            alias=hashlib.sha256(canonical).hexdigest()
            aliases.setdefault(alias,[]).append(seed)
            context=learning.contexts(seed+1000000,n)
            groups[seed]=dict(seed=seed,split=split,case=case,witness=witness,context=context,bank=[])
            write(folder/f'input-{seed}.json',dict(seed=seed,split=split,case=descriptor,
                case_identity=case.identity(),physical_alias=alias,witness=witness,context=context))
        report['alias_clusters']=list(aliases.values())
        if any(len(v)>1 for v in aliases.values()):
            raise ValueError('Physical aliases retained; predeclared distinct-group readiness failed; no replacement')
        report['constructed_groups']=len(groups)
        write(folder/'worker_receipt.json',report)
        stage='training_validation_bank_acquisition'
        for seed in physics.TRAIN_SEEDS+physics.VALIDATION_SEEDS:
            g=groups[seed]
            for index in range(8):
                check(8)
                raw=physics.joint_solve(g['case'],[.2+u/900 for u in g['context']['U'][index]],
                    [1/900]*30,g['witness'],min(end-20,time.monotonic()+6))
                report['primary_native_optimize_count']+=raw['native_calls']
                row=dict(seed=seed,index=index,**compact(raw))
                report['bank_rows'].append(row)
                # Complete admitted bank required; failures remain planned and stop fitting.
                if raw['strict_method_success'] and raw['admitted_plan'] is not None:
                    g['bank'].append(raw['load'])
                    write(folder/f'bank-{seed}-{index}.json',dict(plan=raw['admitted_plan'],receipt=row))
                if (raw.get('helper_result') or {}).get('fatal_contract'):
                    raise RuntimeError('Fatal source/matrix contract in bank acquisition')
                write(folder/'worker_receipt.json',report)
        report['bank_complete']=all(len(g['bank'])==8 for g in groups.values() if g['split']!='test')
        report['bank_diversity']={str(seed):dict(records=len(g['bank']),
            distinct_loads_rounded_6=len({tuple(round(v,6) for v in l) for l in g['bank']}))
            for seed,g in groups.items() if g['split']!='test'}
        if not report['bank_complete']:
            raise RuntimeError('Incomplete bank acquisition; no invalid record dropping or fitted fallback')
        def rows(split,key):
            return [x for g in groups.values() if g['split']==split for x in g['context'][key]]
        def banks(split):
            return [g['bank'] for g in groups.values() if g['split']==split for _ in g['context']['X']]
        def ids(split):
            return [g['seed'] for g in groups.values() if g['split']==split for _ in g['context']['X']]
        stage='model_fitting'
        check(1200)
        fit_start=time.monotonic(); fit_cpu=time.process_time()
        fitted=learning.fit_models(rows('train','X'),rows('train','U'),rows('validation','X'),rows('validation','U'),
            train_banks=banks('train'),val_banks=banks('validation'),conditional_trainU=rows('train','conditional_U'),
            train_groups=ids('train'),val_groups=ids('validation'))
        report['fit_elapsed_s']=time.monotonic()-fit_start
        report['fit_cpu_s']=time.process_time()-fit_cpu
        report['fit_complete']=True
        fit_metadata={k:v for k,v in fitted.items() if k!='models'}
        write(folder/'fit_receipt.json',fit_metadata)
        # Persist new local model artifacts only; never load old weights or private data.
        import pickle
        with (folder/'models.pkl').open('wb') as handle:
            pickle.dump(fitted['models'],handle,protocol=pickle.HIGHEST_PROTOCOL)
        report['capacity_diagnostic']=fitted['capacity_diagnostic']
        stage='held_out_development_evaluation'
        rng=np.random.default_rng(20261027)
        for seed in physics.TEST_SEEDS:
            g=groups[seed]
            prediction_started=time.monotonic()
            predictions={name:learning.predict(fitted,g['context']['X'],name).tolist() for name in METHODS[:9]}
            report.setdefault('prediction_elapsed_s',{})[str(seed)]=time.monotonic()-prediction_started
            predictions['conditional_mean_reference']=g['context']['conditional_U']
            predictions['perfect_information_reference']=g['context']['U']
            predictions['fixed_conditional_reference']=g['context']['conditional_U']
            for index in range(8):
                order=list(METHODS);rng.shuffle(order)
                for method in order:
                    check(8)
                    predicted=predictions[method][index]
                    solver=physics.fixed_solve if method=='fixed_conditional_reference' else physics.joint_solve
                    raw=solver(g['case'],[.2+u/900 for u in predicted],[1/900]*30,g['witness'],
                        min(end-20,time.monotonic()+6))
                    report['primary_native_optimize_count']+=raw['native_calls']
                    row=dict(seed=seed,index=index,method=method,**compact(raw))
                    load=raw['load'] if raw['admitted_plan'] is not None else g['witness']['load']
                    plan=raw['admitted_plan'] or g['witness']
                    row.update(expected_electricity=cost(g['context']['conditional_U'][index],load),
                        realized_electricity=cost(g['context']['U'][index],load),
                        prediction_rmse_to_mean=float(np.mean((np.asarray(predicted)-g['context']['conditional_U'][index])**2)**.5),
                        prediction_rmse_to_realized=float(np.mean((np.asarray(predicted)-g['context']['U'][index])**2)**.5),
                        topology=topology(plan),grid_kwh=sum(float(v) for v in load),
                        operational_fallback_only=not raw['strict_method_success'])
                    report['test_rows'].append(row)
                    write(folder/f'test-{seed}-{index}-{method}.json',dict(plan=plan,predicted_U=predicted,receipt=row))
                    write(folder/'worker_receipt.json',report)
                    if (raw.get('helper_result') or {}).get('fatal_contract'):
                        raise RuntimeError('Fatal source/matrix contract during held-out evaluation')
        stage='inline_readout'
        check(10)
        complete=len(report['test_rows'])==768
        by={(r['seed'],r['index'],r['method']):r for r in report['test_rows']}
        summary={}
        for method in METHODS:
            rr=[r for r in report['test_rows'] if r['method']==method]
            strict=len(rr)==64 and all(r['strict_method_success'] for r in rr)
            summary[method]=dict(assigned=64,attempted=len(rr),strict=sum(r['strict_method_success'] for r in rr),
                native_optimal=sum(r['native_status_optimal'] for r in rr),
                mean_expected_electricity=sum(r['expected_electricity'] for r in rr)/64 if len(rr)==64 else None,
                mean_realized_electricity=sum(r['realized_electricity'] for r in rr)/64 if len(rr)==64 else None,
                mean_forecast_rmse=sum(r['prediction_rmse_to_mean'] for r in rr)/64 if len(rr)==64 else None,
                all_strict=strict)
        contrasts={}
        pairs=[('mean','conditional_mean_reference'),('fixed_conditional_reference','conditional_mean_reference'),
            ('neural_small_mse','neural_large_mse'),('neural_large_mse','neural_large_dfl'),
            ('blind_large_dfl','neural_large_dfl')]+[(control,'neural_large_dfl') for control in METHODS[:4]]
        for control,method in pairs:
            eligible=complete and summary[control]['all_strict'] and summary[method]['all_strict'] and summary['mean']['all_strict']
            group_values=[]
            if eligible:
                for seed in physics.TEST_SEEDS:
                    ratios=[]
                    for i in range(8):
                        denominator=by[seed,i,'mean']['expected_electricity']
                        if denominator<=0:raise ValueError('Nonpositive frozen electricity denominator')
                        ratios.append((by[seed,i,control]['expected_electricity']-by[seed,i,method]['expected_electricity'])/denominator)
                    group_values.append(float(np.mean(ratios)))
            mean=float(np.mean(group_values)) if eligible else None
            half=float(2.365*np.std(group_values,ddof=1)/np.sqrt(8)) if eligible else None
            contrasts[control+' minus '+method]=dict(qualified=eligible,group_means=group_values,
                mean_paired_ratio=mean,positive_groups=sum(v>1e-9 for v in group_values),
                descriptive_t_interval=[mean-half,mean+half] if eligible else None)
        information=contrasts['mean minus conditional_mean_reference']
        learn=[contrasts[c+' minus neural_large_dfl'] for c in METHODS[:4]]
        ready=complete and all(s['all_strict'] for s in summary.values())
        references_qualified=ready and all(summary[m]['native_optimal']==64 for m in METHODS[9:])
        optimization_qualified=ready and all(s['native_optimal']==64 for s in summary.values())
        information_pass=bool(references_qualified and summary['mean']['native_optimal']==64 and information['qualified'] and information['mean_paired_ratio']>.01 and information['positive_groups']>=6)
        learning_pass=bool(optimization_qualified and information_pass and fitted['capacity_diagnostic']['passed'] and
            all(c['qualified'] and c['mean_paired_ratio']>.01 and c['positive_groups']>=6 for c in learn))
        readout=dict(status='COMPLETE' if complete else 'INCOMPLETE',all_strict=ready,references_qualified=references_qualified,optimization_qualified=optimization_qualified,methods=summary,
            contrasts=contrasts,information_screen_pass=information_pass,learning_screen_pass=learning_pass,
            scope='Expected-cost ratios use paired mean-policy electricity. 8 independent development timetable groups, no empirical forecasting/generalization/V2G claim.',
            reference_scope='Conditional mean is risk-neutral sufficient statistic; numerical solve bounds/tolerances limit optimized reference. Perfect information is a realized-cost reference only.')
        write(folder/'READOUT.json',readout)
        report['readout']=readout
        report['status']='CLOSED_COMPLETE' if complete else 'CLOSED_INCOMPLETE'
    except BaseException as exc:
        report['status']='CLOSED_FAILED'
        report['failures'].append(dict(stage=stage,type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        usage=resource.getrusage(resource.RUSAGE_SELF)
        report.update(receipt_complete=True,final_stage=stage,worker_elapsed_s=time.monotonic()-started,
            cpu_s=usage.ru_utime+usage.ru_stime,peak_observed_rss_bytes=usage.ru_maxrss*(1 if sys.platform=='darwin' else 1024),
            attempted_bank_states=len(report['bank_rows']),unattempted_bank_states=128-len(report['bank_rows']),
            attempted_test_states=len(report['test_rows']),unattempted_test_states=768-len(report['test_rows']))
        write(folder/'worker_receipt.json',report)
        print(json.dumps({k:report[k] for k in ('status','fit_complete','attempted_bank_states','attempted_test_states','cpu_s')}))
    return 0 if report['status']=='CLOSED_COMPLETE' else 1

if __name__=='__main__':
    sys.exit(main())
