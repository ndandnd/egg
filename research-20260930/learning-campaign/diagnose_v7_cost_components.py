"""Saved v7 cost-component arithmetic only; no new inference, replay or solve."""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
from egglab import physical_learning_cases as physical

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT/'research-20260930/learning-campaign'
RAW = ROOT/'result/physical_learning/20260930-route-proposal-train-v7'
ARMS = ('tabular_v3','families_v5','graph_v6')


def read(path): return json.loads(Path(path).read_text())


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, label):
    if not condition: raise ValueError(label)


def save(path, data):
    with Path(path).open('x') as stream:
        json.dump(data,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')


def number(value): return {'exact':str(value),'value':float(value)}


def components(row, market, verified):
    replay=row['replay']; loads=[Q(x) for x in replay['load']]
    require(row['status']=='replayed' and replay['replay_ok'] is True, 'Not a saved admitted replay')
    require(row['plan_hash']==verified['plan_hash'] and row['objective_exact']==verified['objective_exact'], 'Stage plan/bill differs from reviewed ledger')
    require(row['vehicle_count']==verified['vehicle_count'], 'Fleet count differs')
    actual=sorted({m for v in row['plan']['vehicles'] for m in v['movements']})
    require(actual==verified['selected_movements'],'Topology differs from reviewed ledger')
    require(len(loads)==len(market.a)==len(market.b),'Wrong known-market load dimensions')
    operations=Q(replay['ops_cost'])
    linear=sum((Q(a)*load for a,load in zip(market.a,loads)),Q(0))
    quadratic=sum((Q(b)*load**2/2 for b,load in zip(market.b,loads)),Q(0))
    bill=Q(row['objective_exact'])
    require(operations+linear+quadratic==bill,'Exact operations/linear/quadratic identity failed')
    low,high=min(Q(a) for a in market.a),max(Q(a) for a in market.a)
    require(set(Q(a) for a in market.a)=={low,high},'This diagnostic requires the fixed two-tier day tariff')
    total=sum(loads,Q(0));cheap=sum((load for a,load in zip(market.a,loads) if Q(a)==low),Q(0))
    quantity=high*total;allocation=(low-high)*cheap
    require(quantity+allocation==linear,'Linear total-energy/cheap-period-discount identity failed')
    return {'operations':operations,'linear':linear,'quadratic':quadratic,'supply':linear+quadratic,'bill':bill,
        'linear_quantity_reference_high_tariff':quantity,'linear_cheap_period_discount':allocation,
        'grid_kwh':Q(replay['grid_kwh']),'consumption_kwh':Q(replay['consumption_kwh']),
        'cheap_period_load_kwh':cheap,'sum_period_load_kwh':total,'vehicle_count':row['vehicle_count'],
        'selected_movements':actual,'plan_hash':row['plan_hash'],'topology_novel_vs_admitted_bank':verified['topology_novel']}


def serialized(parts):
    return {key:number(value) if isinstance(value,Q) else value for key,value in parts.items()}


def paired(primary, source):
    names=('operations','linear','quadratic','supply','bill','linear_quantity_reference_high_tariff',
        'linear_cheap_period_discount','grid_kwh','consumption_kwh','cheap_period_load_kwh','sum_period_load_kwh')
    delta={key:primary[key]-source[key] for key in names}
    require(delta['operations']+delta['linear']+delta['quadratic']==delta['bill'],'Paired component identity failed')
    require(delta['linear_quantity_reference_high_tariff']+delta['linear_cheap_period_discount']==delta['linear'],'Paired linear identity failed')
    delta.update(vehicle_count=primary['vehicle_count']-source['vehicle_count'],
        same_as_selected_source_topology=primary['selected_movements']==source['selected_movements'],
        topology_symmetric_difference_movements=len(set(primary['selected_movements'])^set(source['selected_movements'])),
        topology_novel_vs_admitted_bank=primary['topology_novel_vs_admitted_bank'])
    return delta


def summarize(rows):
    numeric=('operations','linear','quadratic','supply','bill','linear_quantity_reference_high_tariff',
        'linear_cheap_period_discount','grid_kwh','consumption_kwh','cheap_period_load_kwh','sum_period_load_kwh')
    n=len(rows);require(n>0,'Empty common cohort')
    totals={key:sum((row[key] for row in rows),Q(0)) for key in numeric}
    means={key:value/n for key,value in totals.items()}
    require(means['operations']+means['linear']+means['quadratic']==means['bill'],'Mean component identity failed')
    return {'groups':n,'mean_delta':serialized(means),'sum_delta':serialized(totals),
        'vehicle_delta_counts':dict(Counter(row['vehicle_count'] for row in rows)),
        'zero_operations_delta_groups':sum(row['operations']==0 for row in rows),
        'same_selected_source_topology_groups':sum(row['same_as_selected_source_topology'] for row in rows),
        'novel_vs_any_admitted_source_groups':sum(row['topology_novel_vs_admitted_bank'] is True for row in rows),
        'mean_topology_symmetric_difference_movements':sum(row['topology_symmetric_difference_movements'] for row in rows)/n,
        'descriptive_supply_relation_with_existing_report_0_01_tolerance':{
            'lower':sum(row['supply'] < -Q('0.01') for row in rows),
            'within':sum(abs(row['supply'])<=Q('0.01') for row in rows),
            'higher':sum(row['supply'] > Q('0.01') for row in rows)}}


def build(output,report):
    ledger_path=DOC/'ROUTE_PROPOSAL_TRAIN_V7_REPLAY.json'; ledger=read(ledger_path)
    require(ledger['verified_artifact_and_physical_replay'] and ledger['exact_saved_bills_reproduced'] and ledger['array_job_id']==728823,'Reviewed v7 replay does not pass')
    manifest_path=DOC/'ROUTE_PROPOSAL_TRAIN_V7_INPUTS.json';manifest=read(manifest_path)
    require(sha(manifest_path)==ledger['input_manifest_sha256'],'Frozen input hash differs')
    archive_path=DOC/'RESULT_MANIFEST_ROUTE_PROPOSAL_V7.json';archive=read(archive_path)
    require(sha(archive_path)==ledger['raw_archive_manifest_sha256'],'Preserved raw archive binding differs')
    source_paths=('src/egglab/physical_learning_cases.py','src/egglab/native_hull.py','src/egglab/native_recharge.py')
    source_hashes={p:sha(ROOT/p) for p in source_paths}
    require(all(digest==manifest['source_hashes'][p] for p,digest in source_hashes.items()),'Known market/source implementation changed')
    pinned={};units=[];common=ledger['common_complete_primary_groups']
    require(common==[g for g in range(10064,10080) if g!=10069],'Common complete primary cohort changed')

    def stage(folder,key):
        path=folder/(key+'.json');relative=str(path.relative_to(ROOT));expected=archive['files'][relative]
        require(sha(path)==expected['sha256'] and path.stat().st_size==expected['bytes'],'Saved replay output changed')
        pinned[relative]=expected['sha256'];return read(path)

    for task in ledger['tasks']:
        group=task['group_id'];folder=RAW/f"task{task['task_id']:02d}"
        # Construct only the frozen physical case/market identity, never a model or plan.
        case=physical.make_case(group);market=physical.market(case,'day')
        require(case.identity()==task['case_identity'] and market.identity()==task['market_identity'],'Known physical target identity changed')
        source_name=task['source_policy']['selected_arm']
        require(source_name.endswith('_recharged'),'Unexpected source policy type')
        source_key=source_name.removesuffix('_recharged')
        src_stage=stage(folder,source_key+'_replay')
        require(src_stage['group_id']==group and src_stage['market_identity']==market.identity(),'Source stage target differs')
        source=components(src_stage['data'],market,task['source_recharge_checks'][source_name])
        require(source['bill']==Q(task['source_policy']['objective_exact']),'Selected source policy bill differs')
        primary={};delta={}
        for arm in ARMS:
            verified=task['primary'][arm]
            if verified is None:
                primary[arm]=None;delta[arm]=None;continue
            row=stage(folder,arm+'_replay')
            require(row['group_id']==group and row['market_identity']==market.identity(),'Primary stage target differs')
            primary[arm]=components(row['data'],market,verified)
            delta[arm]=paired(primary[arm],source)
            require(delta[arm]['bill']==Q(task['paired_primary_vs_source'][arm]['delta_exact']),'Paired bill differs from reviewed replay')
        units.append({'group_id':group,'task_id':task['task_id'],'common15_member':group in common,
            'selected_source_policy':source_name,'case_identity':case.identity(),'market_identity':market.identity(),
            'market_coefficients_exact':{'a':[str(Q(a)) for a in market.a],'b':[str(Q(b)) for b in market.b]},
            'source':source,'primary':primary,'paired_delta':delta})
    summary={arm:summarize([unit['paired_delta'][arm] for unit in units if unit['common15_member']]) for arm in ARMS}
    for arm in ARMS:
        require(abs(summary[arm]['mean_delta']['bill']['value']-ledger['primary_summary'][arm]['common15_bill_delta']['mean'])<1e-12,'Common15 mean differs')
    absent=next(unit for unit in units if unit['group_id']==10069)
    require(absent['primary']['graph_v6'] is None and absent['primary']['families_v5'] is None,'10069 missing status changed')
    result={'scope':'Companion descriptive arithmetic of reviewed v7 saved replay outputs; fixed common15 plus explicit missing10069',
        'array_job_id':728823,'script_sha256':sha(Path(__file__)),'reviewed_replay_sha256':sha(ledger_path),
        'input_manifest_sha256':sha(manifest_path),'raw_archive_manifest_sha256':sha(archive_path),
        'source_hashes':source_hashes,'saved_replay_output_hashes':dict(sorted(pinned.items())),
        'common_groups':common,'all_intended_groups':ledger['group_ids'],'all_exact_component_identities_passed':True,
        'no_new_model_inference_or_plan_replay_or_optimizer_or_outer_promotion':True,
        'component_definition':'ops + sum(a_t L_t) + sum(b_t L_t^2/2); exact rational arithmetic of saved binary-float coefficients and replay loads',
        'linear_rebasing_definition':'max(a)*sum(L) + (min(a)-max(a))*sum(cheap-period L); arithmetic identity, not a causal counterfactual',
        'common15_summary':summary,'all16_tabular_summary':summarize([unit['paired_delta']['tabular_v3'] for unit in units]),
        'missing_group10069':{'source':serialized(absent['source']),'tabular':serialized(absent['primary']['tabular_v3']),
            'tabular_delta':serialized(absent['paired_delta']['tabular_v3']),'family':None,'graph':None,
            'reason':'Existing5-second cover caps without integral incumbent; no imputation or new retry'},
        'units':[{**unit,'source':serialized(unit['source']),
            'primary':{arm:serialized(value) if value else None for arm,value in unit['primary'].items()},
            'paired_delta':{arm:serialized(value) if value else None for arm,value in unit['paired_delta'].items()}} for unit in units],
        'limitations':['Post-hoc descriptive mechanism audit, not model selection or causality',
            'Observed linear/quadratic components do not identify separate route-opportunity versus charging-solver causal effects',
            'All32hull controls remain failed; no missing scientific work retried',
            'TRAIN-only, no DEV/TEST, no route-optimality or speedup claim']}
    save(output,result);write_report(report,result)
    print(json.dumps({'exact_identities_passed':True,'common_groups':15,'saved_replay_files':len(pinned),
        'mean_delta_components':{arm:{k:row['mean_delta'][k]['value'] for k in ('operations','linear','quadratic','bill')}
            for arm,row in summary.items()}},sort_keys=True))
    return result


def write_report(path,data):
    lines=['# V7 saved cost-component diagnosis\n\n',
        'The graph’s common15 mean bill gap of+4.599760 cost units versus the predeclared source policy is entirely charging/supply cost. All three learned arms have exactly the same fleet count and operations cost as their selected source policy on every common15 timetable. This audits the already-reviewed saved plans; no inference, replay, optimization or new solve is run.\n\n',
        '| Same common15 | Mean Δoperations | Mean Δlinear tariff | Mean Δquadratic supply | Mean Δbill | Same winning-source topology | Novel vs any admitted source |\n',
        '|---|---:|---:|---:|---:|---:|---:|\n']
    for arm,row in data['common15_summary'].items():
        mean=row['mean_delta'];lines.append(f"| {arm} | {mean['operations']['value']:+.6f} | {mean['linear']['value']:+.6f} | {mean['quadratic']['value']:+.6f} | {mean['bill']['value']:+.6f} | {row['same_selected_source_topology_groups']}/15 | {row['novel_vs_any_admitted_source_groups']}/15 |\n")
    lines+=['\nEvery common15 vehicle delta is zero; observed operations costs are100units per vehicle. Graph’s supply loss splits into+3.919111 linear tariff and+0.680649 curvature. Different movement covers, rather than an extra vehicle on these15cases, accompany the loss: graph differs from the winning-source movement set on13/15cases and is novel against the entire two-source bank on11/15. Topology novelty alone is not a cost improvement.\n\n',
        'For the fixed `day` tariff (cheap periods10–13 at0.10, other periods0.30), linear cost can be rebased exactly as0.30·total grid load minus0.20·cheap-period load. The paired arithmetic separates energy quantity from where charging occurs; it does not estimate a causal effect of changing routes or tariff.\n\n',
        '| Same common15 | Mean Δgrid kWh | Mean Δcheap-period kWh | Δquantity at high tariff | Δcheap-period discount | Δcurvature |\n',
        '|---|---:|---:|---:|---:|---:|\n']
    for arm,row in data['common15_summary'].items():
        mean=row['mean_delta'];lines.append(f"| {arm} | {mean['grid_kwh']['value']:+.6f} | {mean['cheap_period_load_kwh']['value']:+.6f} | {mean['linear_quantity_reference_high_tariff']['value']:+.6f} | {mean['linear_cheap_period_discount']['value']:+.6f} | {mean['quadratic']['value']:+.6f} |\n")
    lines+=['\nGraph uses only1.663704more grid kWh on average, but17.100000fewer kWh in cheap periods. Thus its linear gap is+0.499111 from quantity at the high-tariff reference plus+3.420000 from a smaller cheap-period discount. The remaining+0.680649 is the quadratic load term. The bulk of the graph bill gap is therefore observed tariff allocation, not fleet count or simply more total energy. These are identities of the saved loads, not causal counterfactuals.\n\n',
        'On10071 graph’s−0.041949bill delta combines−1.973333linear cost with+1.931385curvature: cheaper linear charging is almost cancelled by the curved term. Conversely, on10075 graph is+9.465424worse despite−0.141243curvature, because linear tariff cost is+9.606667. This motivates charging-opportunity and full supply-cost awareness within same-fleet route construction; it does not select an architecture from these outcomes.\n\n',
        'The common15 cohort is unchanged from the reviewed replay and contains every timetable where all primary arms replayed.10069 remains missing for family and graph because of their existing5-second cover caps. The successful tabular plan there uses6vehicles against source5: its+113.915027bill gap is+100operations and+13.915027supply. Across all16 tabular outcomes, mean gap remains+7.570038 (=+6.250000operations,+1.320038supply); it is not replaced by the common15 result. No missing cost is imputed.\n\n',
        'All component and paired-mean identities hold exactly using rational arithmetic on the known market coefficients and saved replay loads. Near-zero bill signs and the prior report’s post-hoc0.01descriptive tolerance are unchanged. The two-source source policy, INNER promotions, failures and all spent time remain fixed. These TRAIN observations do not separate causal route opportunity, load scheduling and solver effects, and provide no optimality/speedup or DEV/TEST claim. All32hull failures remain outside usable scientific scope.\n']
    with Path(path).open('x') as stream:stream.write(''.join(lines))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=DOC/'V7_COST_COMPONENT_DIAGNOSIS.json')
    parser.add_argument('--report',type=Path,default=DOC/'V7_COST_COMPONENT_DIAGNOSIS.md')
    args=parser.parse_args();build(args.output,args.report)


if __name__=='__main__':main()
