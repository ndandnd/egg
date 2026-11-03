"""Reproduce manuscript figures from archived exact artifacts; no solver."""
from pathlib import Path
import json
import hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/figures'
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'result/cyclic_gap/20260927-attempt1/results.json'
r=json.loads(SOURCE.read_text())
v=lambda obj: obj['value']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,
                     'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False,
                     'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':240,'svg.hashsalt':'egg-journal-v1'})
BLUE='#156082'; GOLD='#AE6F00'; RED='#B5493B'; GREY='#59616A'

def save(fig,name):
    for ext in ('png','pdf','svg'):
        path=OUT/(name+'.'+ext)
        fig.savefig(path,bbox_inches='tight',facecolor='white')
        if ext == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
    plt.close(fig)

fig,ax=plt.subplots(1,2,figsize=(10.4,4.0),gridspec_kw={'width_ratios':[1.35,1]},layout='constrained')
x=np.linspace(0,10,401)
a=4; f=7; g=a*x+(x*x+(30-x)**2)/10
ax[0].plot(x,2*f+g,color=BLUE,lw=2.3,label='Physical: two buses')
ax[0].plot(x,2*f-f*x/10+g,color=GOLD,lw=2.3,label='Complete-schedule hull')
ax[0].scatter([10],[97],s=75,marker='s',color=RED,zorder=5,label='Physical: one bus')
ax[0].scatter([6.75],[94.8875],s=80,marker='*',color=GOLD,zorder=6)
ax[0].annotate('Hull minimum\n94.8875',(6.75,94.8875),xytext=(2.1,92.8),
               arrowprops={'arrowstyle':'-','color':GOLD},color=GOLD)
ax[0].annotate('Physical minimum: 97',(10,97),xytext=(6.0,103.0),
               arrowprops={'arrowstyle':'-','color':RED},color=RED)
ax[0].set(xlabel='Early charge x (kWh)',ylabel='System cost (synthetic currency)',
          xlim=(-.35,10.4),ylim=(91,109),title='(a) Indivisible duties leave a gap')
ax[0].legend(loc='upper left',frameon=False,fontsize=8.5)
ax[0].grid(axis='y',alpha=.2)
nom=r['nominal_prices']['physical_branch_optima'][0]
reg=v(nom['own_price_regret']); supply=v(nom['supply_LOC_at_hull_price'])
ax[1].bar([0,1],[reg,0],color=BLUE,width=.55,label='Fleet LOC')
ax[1].bar([0,1],[0,supply],color=GOLD,width=.55,label='Supply LOC')
ax[1].text(0,reg+.3,f'{reg:g}',ha='center',color=BLUE)
ax[1].text(1,supply+.3,f'{supply:g}',ha='center',color=GOLD)
ax[1].set_xticks([0,1],['Own price\n(6, 4)','Hull price\n(5.35, 4.65)'])
ax[1].set(ylabel='Lost-opportunity cost (synthetic currency)',ylim=(0,16),
          title='(b) Accounting depends on the price')
ax[1].legend(frameon=False,loc='upper right',fontsize=9)
ax[1].grid(axis='y',alpha=.2)
save(fig,'cyclic_gap_and_prices')

fig,ax=plt.subplots(figsize=(8.0,3.8),layout='constrained')
states=[20,5,15,0,20]
ax.plot(range(5),states,color=BLUE,lw=2.6)
ax.scatter(range(5),states,color=BLUE,s=35,zorder=5)
labels=['0\nStart','1\nService A ends','2\nEarly charge ends','3\nService B ends','4\nReplenished']
ax.set_xticks(range(5),labels,rotation=0,fontsize=8.5)
ax.set(ylim=(-1.5,24),ylabel='Battery energy (kWh)',xlabel='Elapsed time (h)',title='One feasible continuous SOC trajectory with full replenishment')
for i,s in enumerate(states): ax.text(i,s+1.0,f'{s}',ha='center',fontsize=9,color=BLUE)
for x0,txt in [(0.5,'-15 kWh\nservice'),(1.5,'+10 kWh\ncharge'),(2.5,'-15 kWh\nservice'),(3.5,'+20 kWh\ncharge')]:
    ax.text(x0,22,txt,ha='center',va='center',fontsize=8,color=GREY)
ax.axhline(20,color=GREY,lw=.8,ls='--',alpha=.6)
ax.grid(axis='y',alpha=.2)
save(fig,'cyclic_energy_accounting')

fs=[1,3,7,10,15,20]; aa=[0,2,4,6]
m=np.array([[next(v(c['gap']) for c in r['cases'] if v(c['fleet_cost'])==f and v(c['early_intercept'])==a) for f in fs] for a in aa])
fig,ax=plt.subplots(figsize=(7.2,3.8),layout='constrained')
im=ax.imshow(m,cmap='cividis',aspect='auto',vmin=0)
for i in range(len(aa)):
 for j in range(len(fs)):
  ax.text(j,i,f'{m[i,j]:.3g}',ha='center',va='center',color='white' if m[i,j]<m.max()*.45 else '#17252D')
ax.set_xticks(range(len(fs)),fs); ax.set_yticks(range(len(aa)),aa)
ax.set(xlabel='Cost per used bus f (synthetic currency)',ylabel='Early tariff intercept a\n(synthetic currency/kWh)',title='Exact planning gap across the fixed 24-case analytical grid')
fig.colorbar(im,ax=ax,label='Gap (synthetic currency)',shrink=.88)
save(fig,'cyclic_gap_grid')
# Display mathematics is typeset with MathText, not left as source notation.
for number, line in enumerate([line.strip() for line in (ROOT/'paper/manuscript.md').read_text().splitlines() if line.startswith('$$')], 1):
    formula='$'+line[2:-2]+'$'
    fig=plt.figure(figsize=(7,.34))
    fig.text(.5,.5,formula,ha='center',va='center',fontsize=13)
    fig.savefig(OUT/f'equation_{number:02}.png',dpi=300,bbox_inches='tight',pad_inches=.05,facecolor='white')
    plt.close(fig)
(OUT/'provenance.json').write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),
 'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'manuscript_sha256':hashlib.sha256((ROOT/'paper/manuscript.md').read_bytes()).hexdigest(),
 'matplotlib':matplotlib.__version__,'numpy':np.__version__,
 'interpretation':'exact analytical cases, not independent samples; PNG/PDF/SVG figures'},indent=2)+'\n')
