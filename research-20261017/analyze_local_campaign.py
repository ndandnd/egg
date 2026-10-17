"""Read completed campaign receipts; no solver/model imports. See ANALYSIS_RULES.md."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import tempfile

SEED=20261017

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ident(value):return hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest()
def number(value):return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
def load(path,issues,label):
    try:
        value=json.loads(path.read_text())
        if not isinstance(value,dict):raise ValueError('object required')
        return value
    except (OSError,ValueError,TypeError):issues.append(label);return {}

def expected(lock,stage):
    seeds=[17] if stage=='qualification' else lock['manifest']['solver_seeds']
    blocks=[(c['case_key'],s) for c in lock['manifest']['cohorts'][stage] for s in seeds]
    blocks.sort(key=lambda b:ident(['egg-ranking-local-20261017-v1',*b,'block']))
    for i,(case,seed) in enumerate(blocks):
        arms=lock['arms'];arms=arms[i%len(arms):]+arms[:i%len(arms)]
        if i%2:arms=list(reversed(arms))
        for arm in arms:yield {'case_key':case,'seed':seed,'arm':arm,'block':i,'seconds':30 if stage=='qualification' else 60}

def observe(root,task,locksha,require_completion=False):
    folder=root/ident(task)[:20];issues=[]
    attempt=load(folder/'attempt.json',issues,'missing_or_corrupt_attempt')
    sup=load(folder/'supervisor.json',issues,'missing_or_corrupt_supervisor')
    row=load(folder/'result.json',issues,'missing_or_corrupt_worker')
    if attempt and (attempt.get('task')!=task or attempt.get('lock_sha256')!=locksha):issues.append('attempt_mapping_violation')
    if row and row.get('task')!=task:issues.append('worker_mapping_violation')
    if require_completion:
        marker=load(folder/'completion.json',issues,'missing_or_corrupt_completion_marker')
        anchor=attempt.get('parent_monotonic');finished=marker.get('finished_monotonic')
        if (marker.get('task')!=task or marker.get('lock_sha256')!=locksha
                or not number(anchor) or not number(finished) or finished<anchor
                or marker.get('parent_monotonic')!=anchor
                or not (folder/'result.json').exists()
                or marker.get('result_sha256')!=sha(folder/'result.json')):
            issues.append('invalid_completion_marker')
        elif not number(sup.get('wall_s')) or abs(sup['wall_s']-(finished-anchor))>1e-8:
            issues.append('completion_endpoint_mismatch')
        if sup.get('completion_marker_issue'):issues.append('supervisor_completion_marker_issue')
    wall=sup.get('wall_s');cpu=sup.get('charged_cpu_s');rss=sup.get('peak_tree_rss_bytes')
    if not all(number(v) and v>=0 for v in (wall,cpu,rss)):issues.append('unknown_resource_accounting')
    accepted=row.get('accepted_valid') is True
    endpoint=sup.get('endpoint_valid') is True
    censored=sup.get('endpoint_censored') is True or (number(wall) and wall>task['seconds'])
    if 'endpoint_valid' not in sup or 'endpoint_censored' not in sup:issues.append('unknown_endpoint_flags')
    replay={}
    if accepted:
        replay=load(folder/'replay.json',issues,'missing_or_corrupt_accepted_replay')
        if replay.get('replay_ok') is not True:issues.append('accepted_replay_unverified')
    bill=None
    if accepted:
        try:
            exact=Fraction(row['bill_exact']);bill=float(exact)
            if not math.isfinite(bill):raise ValueError()
        except (KeyError,ValueError,TypeError,ZeroDivisionError,OverflowError):issues.append('invalid_bill');bill=None
    infra=bool(sup.get('failure') or sup.get('returncode') not in (0,) or sup.get('missing_worker_receipt'))
    valid=accepted and endpoint and not censored and bill is not None and not issues and not infra
    rejection=Counter();native_issue=False
    native=folder/'native.jsonl'
    if native.exists():
        try:
            for line in native.read_text().splitlines():
                event=json.loads(line)
                if event.get('event') in ('candidate_rejected','raw_candidate_rejected','completion_failed'):
                    rejection[event['event']]+=1
        except (ValueError,TypeError,AttributeError):native_issue=True
    failure_type=(row.get('failure') or {}).get('type','') if isinstance(row.get('failure'),dict) else ''
    if valid:category='valid'
    elif not attempt:category='missing'
    elif infra or issues:category='infrastructure_or_unknown'
    elif censored:category='censored'
    elif row.get('failure') or rejection:category='extraction_replay_or_worker_failure'
    else:category='no_plan'
    return {'task':task,'directory':folder.name,'attempted':bool(attempt),'terminal':bool(sup),
            'accepted_valid_worker':accepted,'endpoint_valid_supervisor':endpoint,'valid':valid,
            'censored':censored,'bill':bill,'category':category,'issues':issues,
            'rejected_candidates':dict(rejection),'native_log_corrupt':native_issue,
            'failure_type':failure_type,'supervisor_failure':sup.get('failure'),'wall_s':wall,'charged_cpu_s':cpu,'peak_rss_bytes':rss,
            'invalid_accepted':accepted and replay.get('replay_ok') is not True,
            'mapping_violation':any('mapping_violation' in x for x in issues),
            'overrun_gt_2s':number(wall) and wall>task['seconds']+2}

def weighted_median_by_size(values):
    if any(not v for v in values.values()):return None
    pool=sorted((x,1/(len(values)*len(v))) for v in values.values() for x in v)
    total=0
    for i,(x,w) in enumerate(pool):
        total+=w
        if total>=.5-1e-12:
            if abs(total-.5)<1e-12 and i+1<len(pool):return (x+pool[i+1][0])/2
            return x

def compare(cells,cohort,seeds,control,draws=10000):
    lookup={(r['task']['case_key'],r['task']['seed'],r['task']['arm']):r for r in cells}
    bysize=defaultdict(list);pairs=[]
    for case in cohort:
        key=case['case_key'];gains=[];wins=losses=ties=validloss=0
        for seed in seeds:
            a=lookup[key,seed,'v8'];b=lookup[key,seed,control]
            gain=None
            if a['valid'] and b['valid']:
                if a['bill']>0 and b['bill']>0:gain=(b['bill']-a['bill'])/b['bill'];gains.append(gain)
                if a['bill']<b['bill']:wins+=1
                elif a['bill']>b['bill']:losses+=1
                else:ties+=1
            elif a['valid']:wins+=1
            elif b['valid']:losses+=1;validloss+=1
            else:ties+=1
            pairs.append({'case_key':key,'seed':seed,'both_valid':a['valid'] and b['valid'],
                          'relative_gain':gain,'v8_valid':a['valid'],'control_valid':b['valid']})
        bysize[case['services']].append({'group_id':case['group_id'],'case_key':key,
             'both_valid_positive_bill_pairs':len(gains),'complete_three_pairs':len(gains)==len(seeds)==3,
             'median_gain':statistics.median(gains) if gains else None,
             'failure_aware_wins':wins,'failure_aware_losses':losses,'failure_aware_ties':ties,
             'v8_validity_losses':validloss})
    values={s:[g['median_gain'] for g in gs if g['median_gain'] is not None] for s,gs in bysize.items()}
    result={'control':control,'groups_by_size':dict(bysize),'pairs':pairs,
            'median_gain_by_size':{s:statistics.median(v) if v else None for s,v in values.items()},
            'median_gain_equal_size':weighted_median_by_size(values),
            'relative_gain_applicable':all(not p['both_valid'] or p['relative_gain'] is not None for p in pairs),
            'nonpositive_both_valid_pairs':sum(p['both_valid'] and p['relative_gain'] is None for p in pairs),
            'both_valid_denominator':sum(p['both_valid'] for p in pairs),
            'relative_gain_denominator':sum(p['relative_gain'] is not None for p in pairs),
            'worst_paired_gain':min((p['relative_gain'] for p in pairs if p['relative_gain'] is not None),default=None)}
    rng=random.Random(SEED);boots=[]
    for _ in range(draws):
        sampled={s:[rng.choice(gs)['median_gain'] for _ in gs] for s,gs in bysize.items()}
        sampled={s:[v for v in vs if v is not None] for s,vs in sampled.items()}
        value=weighted_median_by_size(sampled)
        if value is not None:boots.append(value)
    boots.sort()
    result['bootstrap']={'seed':SEED,'draws':draws,'finite_draws':len(boots),'interval_95_percentile':
                          [boots[int((len(boots)-1)*q)] for q in (.025,.975)] if boots else None}
    return result

def screen_gates(cells,comparisons,cohort,complete):
    primary=comparisons.get('nonlearned');random_cmp=comparisons.get('random');sizes=sorted({c['services'] for c in cohort})
    def counts(arm,size):return sum(r['valid'] for r in cells if r['task']['arm']==arm and int(r['task']['case_key'].split(':')[-1])==size)
    gates={'complete_cohort':complete,'integrity':not any(r['invalid_accepted'] or r['mapping_violation'] or r['overrun_gt_2s'] or r['issues'] or r['native_log_corrupt'] for r in cells)}
    # A missing/unknown resource receipt already fails integrity; do not let a
    # recorded safety stop in a secondary arm disappear into economic missingness.
    resource_stops={'worker_memory_limit','aggregate_memory_limit','system_memory_pressure',
                    'campaign_cpu_limit','campaign_safety_stop'}
    gates['resource_limits_all_arms']=all(number(r['peak_rss_bytes']) and 0<=r['peak_rss_bytes']<=5*1024**3
        and r.get('supervisor_failure') not in resource_stops for r in cells)
    gates['positive_bills_all_valid_endpoints']=all(number(r['bill']) and r['bill']>0 for r in cells if r['valid'])
    if primary is None or random_cmp is None:return {**gates,'required_comparators':False}
    gates['relative_bill_gates_applicable']=primary['relative_gain_applicable'] and random_cmp['relative_gain_applicable']
    gates['v8_validity_vs_nonlearned']=all(counts('v8',s)>=counts('nonlearned',s) for s in sizes)
    gates['validity_losses_at_most_one_per_size']=all(sum(g['v8_validity_losses'] for g in primary['groups_by_size'][s])<=1 for s in sizes)
    gates['at_least_eight_complete_groups_per_size']=all(sum(g['complete_three_pairs'] for g in primary['groups_by_size'][s])>=8 for s in sizes)
    gates['overall_gain_at_least_one_percent']=primary['median_gain_equal_size'] is not None and primary['median_gain_equal_size']>=.01
    gates['nonnegative_gain_each_size']=all(v is not None and v>=0 for v in primary['median_gain_by_size'].values())
    gates['positive_gain_seven_groups_per_size']=all(sum(g['complete_three_pairs'] and g['median_gain']>0 for g in primary['groups_by_size'][s])>=7 for s in sizes)
    gates['no_paired_regression_above_five_percent']=primary['worst_paired_gain'] is not None and primary['worst_paired_gain']>=-.05
    gates['v8_validity_vs_random']=all(counts('v8',s)>=counts('random',s) for s in sizes)
    gates['nonnegative_overall_gain_vs_random']=random_cmp['median_gain_equal_size'] is not None and random_cmp['median_gain_equal_size']>=0
    return gates

def analyze(lock_path,runroot,stage,output,allow_incomplete=False,draws=10000):
    lock_path=Path(lock_path);runroot=Path(runroot);output=Path(output)
    lock=json.loads(lock_path.read_text());plan=list(expected(lock,stage));locksha=sha(lock_path)
    # Presence-only preflight: no real outcome reading until cohort is terminal.
    missing=[ident(t)[:20] for t in plan if not all((runroot/ident(t)[:20]/f).exists() for f in ('attempt.json','supervisor.json'))]
    if missing and not allow_incomplete:raise RuntimeError(f'Cohort not terminal: {len(missing)} missing receipt pairs; no outcomes read')
    expected_names={ident(t)[:20] for t in plan}
    unknown=[p.name for p in runroot.iterdir() if p.is_dir() and p.name not in expected_names]
    issues=[];binding=load(runroot/'campaign.json',issues,'missing_campaign_binding')
    if binding!={'stage':stage,'lock_sha256':locksha,'mock':False}:issues.append('campaign_binding_mismatch')
    require_completion=lock['manifest'].get('execution',{}).get('qualification_revision',0)>=3
    cells=[observe(runroot,t,locksha,require_completion) for t in plan]
    complete=not missing and not unknown and not issues and all(c['attempted'] and c['terminal'] for c in cells)
    counts={arm:dict(Counter(c['category'] for c in cells if c['task']['arm']==arm)) for arm in lock['arms']}
    resource_summary={'charged_worker_cpu_s':sum(c['charged_cpu_s'] for c in cells if number(c['charged_cpu_s'])),
        'wall_s_sum':sum(c['wall_s'] for c in cells if number(c['wall_s'])),
        'peak_worker_rss_bytes':max((c['peak_rss_bytes'] for c in cells if number(c['peak_rss_bytes'])),default=None),
        'unknown_resource_cells':sum('unknown_resource_accounting' in c['issues'] for c in cells),
        'freeze_cpu_s':lock.get('freeze_cpu_s',0),
        'prior_qualification_cpu_s':lock.get('prior_qualification',{}).get('charged_cpu_s',0),'supervisor_cpu_s':0,'ledger_issues':[]}
    ledger=runroot/'ledger.jsonl'
    if ledger.exists():
        try:
            events=[json.loads(line) for line in ledger.read_text().splitlines()]
            resource_summary['supervisor_cpu_s']=sum(e.get('supervisor_cpu_s',0) for e in events if e.get('event')=='summary')
            resource_summary['safety_events']=dict(Counter(e.get('event') for e in events if e.get('event') in ('supervisor_failure','shutdown_receipt')))
        except (ValueError,TypeError):resource_summary['ledger_issues'].append('corrupt_ledger')
    else:resource_summary['ledger_issues'].append('missing_ledger')
    if stage=='qualification' and not (number(resource_summary['prior_qualification_cpu_s']) and resource_summary['prior_qualification_cpu_s']>=0):
        resource_summary['ledger_issues'].append('unknown_prior_qualification_accounting')
        resource_summary['prior_qualification_cpu_s']=0
    resource_summary['total_charged_cpu_s']=resource_summary['charged_worker_cpu_s']+resource_summary['supervisor_cpu_s']+(resource_summary['freeze_cpu_s']+resource_summary['prior_qualification_cpu_s'] if stage=='qualification' else 0)
    resource_summary['cpu_budget_s']=(.5 if stage=='qualification' else 8)*3600
    accounting_ok=not resource_summary['ledger_issues'] and not resource_summary['unknown_resource_cells'] and resource_summary['total_charged_cpu_s']<=resource_summary['cpu_budget_s']
    summary={'stage':stage,'development_only':True,'complete':complete,'planned':len(plan),'counts_by_arm':counts,
             'binding_issues':issues,'unknown_directories':unknown,'missing_receipts':missing,'cells':cells,'resources':resource_summary}
    if stage=='qualification':
        health={'complete':complete,'accounting_known_within_budget':accounting_ok,'no_worker_or_infrastructure_failure':all(c['category'] in ('valid','no_plan','censored') for c in cells),
                'integrity':not any(c['invalid_accepted'] or c['mapping_violation'] or c['overrun_gt_2s'] or c['issues'] for c in cells),
                'memory_limit':all(number(c['peak_rss_bytes']) and c['peak_rss_bytes']<=5*1024**3 for c in cells)}
        summary.update(qualification_health=health,qualification_engineering_pass=all(health.values()),
                       ranking_promotion='not evaluated on qualification')
    else:
        comparisons={arm:compare(cells,lock['manifest']['cohorts'][stage],lock['manifest']['solver_seeds'],arm,draws)
                     for arm in lock['arms'] if arm!='v8'}
        gates=screen_gates(cells,comparisons,lock['manifest']['cohorts'][stage],complete)
        gates['accounting_known_within_budget']=accounting_ok
        summary.update(comparisons=comparisons,gates=gates,decision='GO to separately frozen recovery study' if all(gates.values()) else 'NO-GO / INCONCLUSIVE; diagnose and prospectively revise',model_recommendation=None)
        cb=comparisons.get('catboost_v5')
        if cb and cb['median_gain_equal_size'] is not None and cb['median_gain_equal_size']<=0:
            summary['graph_complexity_statement']='Graph complexity has not earned its cost against this fixed CatBoost comparator.'
    output.mkdir(parents=True,exist_ok=False)
    hashes={str(p.relative_to(runroot)):sha(p) for p in sorted(runroot.rglob('*')) if p.is_file()}
    manifest={'lock_sha256':locksha,'analysis_source_sha256':sha(__file__),'input_artifact_hashes':hashes,
              'raw_stdout_stderr':'private; hashes only; no raw log text included'}
    (output/'artifact_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    lines=[f'# {stage.capitalize()} development campaign',f'Complete cohort: {complete}.',
           'Qualification supplies engineering health only.' if stage=='qualification' else summary['decision'],
           '| Arm | Valid | No plan | Censored | Worker/replay failures | Infrastructure/unknown | Missing |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for arm,cs in counts.items():lines.append('| '+arm+' | '+' | '.join(str(cs.get(k,0)) for k in ('valid','no_plan','censored','extraction_replay_or_worker_failure','infrastructure_or_unknown','missing'))+' |')
    lines+=['','See summary.json for full health cells, denominators, group summaries and accounting. Raw stdout/stderr remain private.']
    (output/'SUMMARY.md').write_text('\n\n'.join(lines[:3])+'\n\n'+'\n'.join(lines[3:])+'\n')
    return summary

def self_test():
    with tempfile.TemporaryDirectory(prefix='egg-analysis-fixtures-') as tmp:
        root=Path(tmp);run=root/'run';run.mkdir()
        cohort=[{'case_key':f'scale:{50600+i}:{s}','services':s,'group_id':str(50600+i)} for i,s in enumerate((40,80))]
        lock={'arms':['v8','nonlearned','random'],'manifest':{'cohorts':{'screen':cohort},'solver_seeds':[17,41,73]}}
        lp=root/'lock.json';lp.write_text(json.dumps(lock));ls=sha(lp)
        (run/'campaign.json').write_text(json.dumps({'stage':'screen','lock_sha256':ls,'mock':False}))
        plan=list(expected(lock,'screen'))
        try:analyze(lp,run,'screen',root/'blocked',draws=10)
        except RuntimeError as e:assert 'no outcomes read' in str(e)
        else:raise AssertionError('Missing cohort must block default reading')
        for task in plan:
            p=run/ident(task)[:20];p.mkdir()
            (p/'attempt.json').write_text(json.dumps({'task':task,'lock_sha256':ls}))
            (p/'supervisor.json').write_text(json.dumps({'returncode':0,'failure':None,'missing_worker_receipt':False,'endpoint_valid':True,'endpoint_censored':False,'wall_s':59,'charged_cpu_s':50,'peak_tree_rss_bytes':1000}))
            (p/'result.json').write_text(json.dumps({'task':task,'accepted_valid':True,'bill_exact':'98' if task['arm']=='v8' else '100'}))
            (p/'replay.json').write_text(json.dumps({'replay_ok':True}))
        (run/'ledger.jsonl').write_text(json.dumps({'event':'summary','supervisor_cpu_s':1})+'\n')
        # A worker accepts but parent censors: never a valid economic endpoint.
        task=next(t for t in plan if t['arm']=='v8');p=run/ident(task)[:20]
        receipt=json.loads((p/'supervisor.json').read_text());receipt.update(endpoint_valid=False,endpoint_censored=True,wall_s=61)
        (p/'supervisor.json').write_text(json.dumps(receipt))
        result=analyze(lp,run,'screen',root/'summary',draws=100)
        cell=next(c for c in result['cells'] if c['task']==task)
        assert cell['accepted_valid_worker'] and not cell['valid'] and cell['censored']
        assert result['comparisons']['nonlearned']['both_valid_denominator']==5
        assert result['decision'].startswith('NO-GO') and result['model_recommendation'] is None
        assert (root/'summary'/'artifact_hashes.json').exists()
        (p/'supervisor.json').write_text('{corrupt')
        broken=analyze(lp,run,'screen',root/'broken',draws=10)
        assert not broken['gates']['integrity'] and not broken['gates']['accounting_known_within_budget']
        assert broken['model_recommendation'] is None
        v3_accounting_regressions(root)
        promotion_regressions()
        print('PASS: missing preflight, parent censor overrides worker acceptance, paired denominators, conservative gates, private-log hashes, nonpositive bills and resource stops.')

def v3_accounting_regressions(root):
    cohort=[{'case_key':'scale:50600:40','services':40,'group_id':'50600'}]
    lock={'arms':['v8'],'freeze_cpu_s':7.,'prior_qualification':{'charged_cpu_s':123.},
          'manifest':{'cohorts':{'qualification':cohort},'execution':{'qualification_revision':3}}}
    lp=root/'v3-lock.json';lp.write_text(json.dumps(lock));locksha=sha(lp)
    run=root/'v3-run';run.mkdir()
    (run/'campaign.json').write_text(json.dumps({'stage':'qualification','lock_sha256':locksha,'mock':False}))
    task=next(expected(lock,'qualification'));folder=run/ident(task)[:20];folder.mkdir()
    (folder/'attempt.json').write_text(json.dumps({'task':task,'lock_sha256':locksha,'parent_monotonic':100.}))
    (folder/'result.json').write_text(json.dumps({'task':task,'accepted_valid':True,'bill_exact':'98'}))
    (folder/'replay.json').write_text(json.dumps({'replay_ok':True}))
    (folder/'supervisor.json').write_text(json.dumps({'returncode':0,'failure':None,'missing_worker_receipt':False,
        'endpoint_valid':True,'endpoint_censored':False,'wall_s':29.,'supervisor_elapsed_s':31.,
        'charged_cpu_s':20.,'peak_tree_rss_bytes':1000}))
    marker={'task':task,'lock_sha256':locksha,'parent_monotonic':100.,'finished_monotonic':129.,
            'result_sha256':sha(folder/'result.json')}
    (folder/'completion.json').write_text(json.dumps(marker))
    (run/'ledger.jsonl').write_text(json.dumps({'event':'summary','supervisor_cpu_s':1.})+'\n')
    report=analyze(lp,run,'qualification',root/'v3-analysis',draws=0)
    assert report['qualification_engineering_pass']
    assert report['resources']['total_charged_cpu_s']==151.
    assert report['resources']['prior_qualification_cpu_s']==123.
    # Cleanup duration is outside the endpoint; result serialization is inside it.
    assert report['cells'][0]['valid'] and not report['cells'][0]['censored']
    marker['result_sha256']='stale'
    (folder/'completion.json').write_text(json.dumps(marker))
    assert not observe(run,task,locksha,True)['valid']
    (folder/'completion.json').unlink()
    assert not observe(run,task,locksha,True)['valid']
    # V2 has no marker requirement and its original wall remains authoritative.
    assert observe(run,task,locksha,False)['valid']


def promotion_regressions():
    # Full 20-group toy screen passes before introducing each isolated violation.
    cohort=[{'case_key':f'scale:{50600+i}:{size}','services':size,'group_id':str(i)}
            for i,size in enumerate([40]*10+[80]*10)]
    seeds=[17,41,73];cells=[]
    for case in cohort:
        for seed in seeds:
            for arm in ('v8','nonlearned','random','cold'):
                cells.append({'task':{'case_key':case['case_key'],'seed':seed,'arm':arm},
                    'valid':True,'bill':98. if arm=='v8' else 100.,'invalid_accepted':False,
                    'mapping_violation':False,'overrun_gt_2s':False,'issues':[],
                    'native_log_corrupt':False,'peak_rss_bytes':1000,'supervisor_failure':None})
    def gates():
        comparisons={arm:compare(cells,cohort,seeds,arm,draws=0) for arm in ('nonlearned','random','cold')}
        return screen_gates(cells,comparisons,cohort,True),comparisons
    assert all(gates()[0].values())
    bad=next(r for r in cells if r['task']['arm']=='v8')
    for bill in (0.,-1.):
        bad['bill']=bill;g,comparisons=gates()
        assert not g['positive_bills_all_valid_endpoints'] and not g['relative_bill_gates_applicable']
        assert not comparisons['nonlearned']['relative_gain_applicable']
        assert comparisons['nonlearned']['nonpositive_both_valid_pairs']==1
        # Other performance thresholds can pass: the applicability gate is essential.
        assert g['overall_gain_at_least_one_percent'] and g['positive_gain_seven_groups_per_size']
        assert not all(g.values())
    bad['bill']=98.
    secondary=next(r for r in cells if r['task']['arm']=='cold')
    secondary['bill']=0.
    assert not gates()[0]['positive_bills_all_valid_endpoints']
    secondary['bill']=100.
    for reason in ('worker_memory_limit','aggregate_memory_limit','system_memory_pressure',
                   'campaign_cpu_limit','campaign_safety_stop'):
        secondary.update(valid=False,bill=None,supervisor_failure=reason)
        g,_=gates()
        assert not g['resource_limits_all_arms'] and not all(g.values())
        assert g['overall_gain_at_least_one_percent']
    secondary.update(valid=True,bill=100.,supervisor_failure=None)
    for rss in (5*1024**3+1,None):
        secondary['peak_rss_bytes']=rss
        assert not gates()[0]['resource_limits_all_arms']


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--lock');p.add_argument('--runs');p.add_argument('--stage',choices=('qualification','screen'));p.add_argument('--output');p.add_argument('--allow-incomplete',action='store_true')
    args=p.parse_args()
    if args.self_test:return self_test()
    if not all((args.lock,args.runs,args.stage,args.output)):p.error('--lock --runs --stage --output required')
    summary=analyze(args.lock,args.runs,args.stage,args.output,args.allow_incomplete)
    print(json.dumps({k:summary[k] for k in ('stage','complete','planned')}))
if __name__=='__main__':main()
