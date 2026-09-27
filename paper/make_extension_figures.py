"""Figures from archived cyclic extensions; do not run any scientific solve."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'paper/figures'
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10,
                     'axes.spines.top':False, 'axes.spines.right':False,
                     'svg.hashsalt':'egg-cyclic-extensions-20260927'})
BLUE, GOLD, GREY = '#176487', '#b17900', '#62727c'
def val(q):
    return float(Fraction(q['exact']))
def save(fig, stem):
    for ext in ['png', 'svg', 'pdf']:
        path=OUT/f'{stem}.{ext}'
        fig.savefig(path, dpi=240, bbox_inches='tight')
        if ext=='svg':
            path.write_text('\n'.join(s.rstrip() for s in path.read_text().splitlines())+'\n')
    plt.close(fig)

robust_path=ROOT/'result/cyclic_robustness/20260927-attempt1/results.json'
robust=json.loads(robust_path.read_text())
matrix=np.array([val(c['gap']) for c in robust['cases'][:12]]).reshape(4,3)
fig, ax=plt.subplots(1,2,figsize=(8.2,3.65),layout='constrained',gridspec_kw={'width_ratios':[1.15,1]})
im=ax[0].imshow(matrix,cmap='YlGnBu',vmin=0,vmax=4,aspect='auto')
for i in range(4):
    for j in range(3):
        v=matrix[i,j]
        ax[0].text(j,i,f'{v:.4f}' if v else '0',ha='center',va='center',
                   color='white' if v>2.5 else '#14252f',fontsize=10)
ax[0].set(xticks=range(3),xticklabels=['10','11','12'],
          yticks=range(4),yticklabels=['0 / 1.00','0 / 0.95','1 / 1.00','1 / 0.95'],
          xlabel='Early power limit (kW)',ylabel='Reserve (kWh) / efficiency',
          title='(a) Fixed battery; terminal power 30 kW')
fig.colorbar(im,ax=ax[0],label='Gap',shrink=.8)
terminal=[robust['cases'][12],robust['cases'][13],robust['cases'][14],robust['cases'][15],robust['cases'][0]]
values=[val(c['gap']) if c['gap'] else 0 for c in terminal]
ax[1].bar(range(5),values,color=[GREY,GREY,GREY,GOLD,BLUE],width=.62)
for i,v in enumerate(values):
    ax[1].text(i,v+.075,'Infeasible' if i==0 else f'{v:.4f}' if v else '0',
               ha='center',va='bottom',fontsize=8.5,rotation=90 if i==0 else 0)
ax[1].set(xticks=range(5),xticklabels=['10','20','23.5','24','30'],ylim=(0,2.7),
          xlabel='Single terminal connector power (kW)',ylabel='Planning gap',
          title='(b) Reserve 0; efficiency 1; early 10 kW')
save(fig,'cyclic_robustness')

rep_path=ROOT/'result/cyclic_replication/20260927-attempt1/results.json'
rep=json.loads(rep_path.read_text())
rows=[c for c in rep['cases'] if c['n']<=80]
fig, ax=plt.subplots(1,2,figsize=(8.2,3.5),layout='constrained')
n=np.array([c['n'] for c in rows])
ax[0].plot(n,5/n,color=GREY,lw=1.1,ls='--',label='Upper bound 5/n')
ax[0].scatter(n,[val(c['gap']) for c in rows],s=16,color=BLUE,label='Exact physical–hull gap',zorder=3)
ax[0].set(xlabel='Replicated service pairs n',ylabel='Gap (synthetic currency)',
          title='(a) The absolute cost gap vanishes',ylim=(-.08,2.5),xlim=(0,82))
ax[0].legend(frameon=False,fontsize=8.5)
for c in rows:
    regrets=[val(w['own_price_regret']) for w in c['physical_optimizers']]
    ax[1].scatter([c['n']]*len(regrets),regrets,s=17,color=GOLD,zorder=3)
    if len(regrets)>1:
        ax[1].plot([c['n']]*2,[min(regrets),max(regrets)],color=GREY,lw=1)
ax[1].annotate('Both planner optima\nretained at ties',xy=(20,10.5),xytext=(27,14.8),
               fontsize=8.5,arrowprops={'arrowstyle':'-','color':GREY})
ax[1].set(xlabel='Replicated service pairs n',ylabel='Whole-operator own-price regret',
          title='(b) Regret depends on integer rounding',ylim=(-.5,17.2),xlim=(0,82))
save(fig,'cyclic_replication')

provenance={'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in [robust_path,rep_path]},
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'matplotlib':matplotlib.__version__, 'numpy':np.__version__,
            'scope':'All 16 robustness cases; first 80 of the 86 predeclared replication sizes. Exact rational data, rounded display labels. No statistical samples.'}
(OUT/'extension_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
