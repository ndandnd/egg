"""Reproducible closeout plots; reads only frozen lock and terminal result/supervisor receipts."""
from __future__ import annotations
import csv
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import statistics
os.environ.setdefault('MPLCONFIGDIR','/tmp/egg-closeout-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RUNS=ROOT/'research-20261017/local-screen-v3'
LOCK=ROOT/'research-20261017/local-assets-v3.json'
NAMES={'v8':'v8 graph attention','catboost_v5':'CatBoost (new, 17 Oct)','nonlearned':'Nonlearned','random':'Random','full4':'Full, 4 rounds','cold':'Full, ≤8 rounds'}
COLORS={'v8':'#b64c3b','catboost_v5':'#236ea4'}

def dumpcsv(path,rows):
    with path.open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    lock=json.loads(LOCK.read_text());cohort=lock['manifest']['cohorts']['screen'];arms=lock['arms'];seeds=lock['manifest']['solver_seeds']
    index={};records=[];hashes={str(LOCK.relative_to(ROOT)):hashlib.sha256(LOCK.read_bytes()).hexdigest()}
    directories=sorted(p for p in RUNS.iterdir() if p.is_dir())
    if len(directories)!=360:raise RuntimeError(f'Expected 360 terminal task directories, found {len(directories)}')
    for directory in directories:
        paths=[directory/'result.json',directory/'supervisor.json']
        if not all(p.is_file() for p in paths):raise RuntimeError(f'Incomplete terminal cell {directory.name}')
        row,sup=(json.loads(p.read_text()) for p in paths);task=row['task']
        for p in paths:hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
        key=(task['case_key'],task['seed'],task['arm'])
        if key in index:raise RuntimeError('Duplicate task')
        bill=None
        try:bill=Fraction(row['bill_exact'])
        except (KeyError,ValueError,TypeError,ZeroDivisionError):pass
        valid=(row.get('accepted_valid') is True and sup.get('endpoint_valid') is True and
               sup.get('endpoint_censored') is False and not sup.get('failure') and
               sup.get('returncode')==0 and not sup.get('missing_worker_receipt') and bill is not None)
        item={'case_key':task['case_key'],'size':int(task['case_key'].split(':')[-1]),'solver_seed':task['seed'],
              'arm':task['arm'],'worker_accepted':row.get('accepted_valid') is True,
              'supervisor_endpoint_valid':sup.get('endpoint_valid') is True,
              'endpoint_censored':sup.get('endpoint_censored'),'valid_endpoint':valid,
              'bill_exact':str(bill) if bill is not None else '',
              'bill_display':float(bill) if bill is not None else '',
              'endpoint_wall_s':sup.get('wall_s'),'cpu_s':sup.get('charged_cpu_s'),
              'peak_rss_bytes':sup.get('peak_tree_rss_bytes'),'worker_status':row.get('status'),
              'failure_type':(row.get('failure') or {}).get('type',''),
              'supervisor_failure':sup.get('failure') or ''}
        index[key]=(valid,bill);records.append(item)
    expected={(c['case_key'],seed,arm) for c in cohort for seed in seeds for arm in arms}
    if set(index)!=expected:raise RuntimeError('Terminal receipts do not match frozen cohort/arms/seeds')
    groups=[]
    for case in cohort:
        for arm in ('v8','catboost_v5'):
            gains=[];both=0
            for seed in seeds:
                av,ab=index[case['case_key'],seed,arm];bv,bb=index[case['case_key'],seed,'nonlearned']
                if av and bv:both+=1
                if av and bv and ab>0 and bb>0:gains.append((bb-ab)/bb)
            median=statistics.median(gains) if len(gains)==3 else None
            groups.append({'base_id':case['base_id'],'case_key':case['case_key'],'size':case['services'],
                           'arm':arm,'control':'nonlearned','both_valid_pairs':both,
                           'positive_bill_gain_pairs':len(gains),'required_pairs':3,
                           'median_gain_fraction_exact':str(median) if median is not None else '',
                           'median_bill_gain_percent':100*float(median) if median is not None else '',
                           'missing_three_pair_median':median is None})
    counts={arm:sum(r['valid_endpoint'] for r in records if r['arm']==arm) for arm in arms}
    bysize={(arm,size):sum(r['valid_endpoint'] for r in records if r['arm']==arm and r['size']==size) for arm in arms for size in (40,80)}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','pdf.fonttype':42,'svg.fonttype':'none'})
    fig=plt.figure(figsize=(14,9.5),facecolor='white')
    grid=fig.add_gridspec(2,2,height_ratios=[3.2,1.7],hspace=.55,wspace=.18)
    values=[g['median_bill_gain_percent'] for g in groups if g['median_bill_gain_percent']!='']
    lo=min([0]+values);hi=max([0]+values);span=max(hi-lo,1);xmin=lo-.16*span;xmax=hi+.20*span
    for col,size in enumerate((40,80)):
        size_values=[g['median_bill_gain_percent'] for g in groups if g['size']==size and g['median_bill_gain_percent']!='']
        lo=min([0]+size_values);hi=max([0]+size_values);span=max(hi-lo,.5);xmin=lo-.16*span;xmax=hi+.22*span
        ax=fig.add_subplot(grid[0,col]);cases=[c for c in cohort if c['services']==size]
        cases=sorted(cases,key=lambda c:c['base_id'])
        for i,case in enumerate(cases):
            if i%2==0:ax.axhspan(i-.5,i+.5,color='#f4f5f6',zorder=0)
            for arm,offset,marker in [('v8',-.13,'o'),('catboost_v5',.13,'s')]:
                group=next(g for g in groups if g['case_key']==case['case_key'] and g['arm']==arm)
                value=group['median_bill_gain_percent']
                if value=='':
                    ax.scatter(xmin+.025*span,i+offset,color=COLORS[arm],marker='x',s=48,zorder=4)
                    ax.text(xmin+.055*span,i+offset,'missing 3 pairs',va='center',fontsize=7,color=COLORS[arm])
                else:
                    ax.scatter(value,i+offset,color=COLORS[arm],marker=marker,s=46,zorder=4,edgecolors='white',linewidths=.6)
                    ax.annotate(f'{value:+.1f}',(value,i+offset),xytext=(6,0),textcoords='offset points',va='center',fontsize=8,color=COLORS[arm])
        ax.axvline(0,color='#656b71',linewidth=1,linestyle='--',zorder=2)
        ax.set(yticks=range(len(cases)),yticklabels=[str(c['base_id']) for c in cases],ylim=(len(cases)-.4,-.6),xlim=(xmin,xmax),xlabel='Bill gain versus nonlearned (%)',title=f'{size} trips · 10 independent timetables · own x scale')
        ax.set_ylabel('Base timetable ID');ax.grid(axis='x',alpha=.15)
    ax=fig.add_subplot(grid[1,:]);xs=range(len(arms));small=[bysize[a,40] for a in arms];large=[bysize[a,80] for a in arms]
    ax.bar(xs,[60]*len(arms),color='#eceeef',width=.6,label='No valid endpoint')
    ax.bar(xs,small,color='#748c9d',width=.6,label='Valid · 40 trips (30 decisions)')
    ax.bar(xs,large,bottom=small,color='#263f52',width=.6,label='Valid · 80 trips (30 decisions)')
    for i,arm in enumerate(arms):ax.text(i,counts[arm]+.7,f'{counts[arm]}/60',ha='center',va='bottom',fontsize=10,fontweight='bold')
    ax.set(xticks=list(xs),xticklabels=[NAMES[a] for a in arms],ylim=(0,67),ylabel='Valid endpoints',yticks=[0,15,30,45,60],title='Validity at the recorded 60-second end-to-end deadline')
    ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.23),ncol=3,frameon=False,fontsize=9)
    fig.suptitle('Ranking-source comparison on synthetic development timetables',x=.055,y=.98,ha='left',fontsize=18,fontweight='bold',color='#203444')
    fig.text(.055,.945,'60 s per decision · 20 timetable groups · 3 paired solver seeds · no final-test or novelty claim',fontsize=11,color='#4d5963')
    handles=[Line2D([0],[0],marker=m,color='none',markerfacecolor=COLORS[a],markeredgecolor='white',markersize=8,label=NAMES[a]) for a,m in [('v8','o'),('catboost_v5','s')]]
    fig.legend(handles=handles,loc='upper right',bbox_to_anchor=(.95,.935),ncol=2,frameon=False,fontsize=10)
    fig.text(.055,.90,'Each dot: median of 3 paired bill gains; all 3 valid positive-bill pairs required. Positive = lower bill. Panels use separate x scales.',fontsize=9,color='#4d5963')
    fig.text(.055,.025,'Stored supervisor validity and censoring are authoritative. Shaded bar remainder = no valid endpoint; seeds are repeats, not independent timetables.\nCatBoost is newly trained (17 Oct 2026). Panels preserve size and timetable heterogeneity; no pooled headline median.',fontsize=9,color='#4d5963')
    fig.subplots_adjust(left=.075,right=.96,top=.855,bottom=.14)
    for suffix in ('png','pdf','svg'):
        target=HERE/f'local_ranking_screen_v3.{suffix}'
        if target.exists():raise FileExistsError(target)
        fig.savefig(target,dpi=180,facecolor='white')
    plt.close(fig)
    dumpcsv(HERE/'per_group.csv',groups);dumpcsv(HERE/'per_cell_endpoints.csv',sorted(records,key=lambda r:(r['size'],r['case_key'],r['solver_seed'],r['arm'])))
    provenance={'scope':'synthetic development only, 60s end-to-end, no final-test claim',
                'independent_units':20,'paired_solver_seeds':seeds,'decision_count':len(records),
                'validity_counts':counts,'invalid_counts':{a:60-counts[a] for a in arms},
                'missing_three_pair_medians':sum(g['missing_three_pair_median'] for g in groups),
                'input_sha256':hashes,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE/'plot_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({k:provenance[k] for k in ('decision_count','validity_counts','invalid_counts','missing_three_pair_medians')}))
if __name__=='__main__':main()
