"""Proved negative-price anchor, literal illustration only; parent launch required."""
from fractions import Fraction
import json
import os
from pathlib import Path
import resource
import sys
import time

if '_artifact_started' not in globals():
    raise RuntimeError('Use the separately frozen bounded render wrapper')
started=_artifact_started
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/egg-paper-matplotlib-full-polygon-20261029')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D

here=Path(__file__).resolve().parent
out=here/'figures';out.mkdir(exist_ok=True)
names=('full_lossy_polygon-v1.pdf','full_lossy_polygon-v1.png')
receipt_name='full_lossy_polygon-v1-receipt.json'
if any((out/name).exists() for name in names+(receipt_name,)):
    raise FileExistsError('One fresh version only; no overwrite or automatic retry')

# Exact proved literals, converted only for graphical coordinates. No solver,
# experiment, data packet, sampling, simulation or new case selection.
vertices=(('1','2'),('3/2','3/2'),('5/3','3/2'),('4/3','2'))
points=[tuple(float(Fraction(v)) for v in row) for row in vertices]
blue,orange,teal='#17609a','#d55e00','#008575'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
    'axes.labelsize':10,'axes.titlesize':11,'legend.fontsize':9,
    'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,
    'savefig.dpi':260})
fig,axes=plt.subplots(1,2,figsize=(9.6,4.8))
fig.subplots_adjust(left=.085,right=.98,bottom=.25,top=.79,wspace=.38)
fig.suptitle('Negative prices can reward a finite neutral cycle',fontsize=13,y=.98)
ax=axes[0]
ax.add_patch(Polygon(points,closed=True,facecolor=blue,edgecolor=blue,alpha=.16,lw=1.8))
closed=points+[points[0]]
ax.plot([p[0] for p in closed],[p[1] for p in closed],color=blue,lw=1.7)
ax.plot([1,1.5],[2,1.5],color=teal,lw=3.2)
ax.scatter([1.5],[1.5],marker='o',color=teal,s=55,zorder=5)
ax.scatter([5/3],[1.5],marker='D',color=orange,s=55,zorder=6)
ax.annotate('Efficient-set best: −1',xy=(1.5,1.5),xytext=(1.01,1.34),
    color=teal,fontsize=10,arrowprops={'arrowstyle':'->','color':teal},ha='left')
ax.annotate('Full-set best: −3/2',xy=(5/3,1.5),xytext=(1.39,1.86),
    color=orange,fontsize=10,arrowprops={'arrowstyle':'->','color':orange},ha='left')
ax.set(xlim=(.94,1.79),ylim=(1.27,2.15),title='(a) Paired one-bus load polygon',
    xlabel='Early net grid purchase E (energy units)',
    ylabel='Terminal grid purchase L (energy units)')
ax.set_xticks([1,4/3,1.5,5/3],['1','4/3','3/2','5/3'])
ax.set_yticks([1.5,2],['3/2','2'])
ax.grid(alpha=.16,lw=.6)
handles=[Line2D([0],[0],color=blue,lw=2,label='Complete paired polygon'),
         Line2D([0],[0],color=teal,lw=3,label='Efficient paired segment')]
ax.legend(handles=handles,loc='upper left',frameon=False,fontsize=8.5)

ax=axes[1]
times=[0,1/6,1/4,1];soc=[1/4,5/12,1/4,1]
ax.plot(times,soc,color=blue,lw=2.5,marker='o',markersize=4)
ax.axhline(1,color='0.5',ls=':',lw=1)
ax.annotate('Buy 1/3',xy=(1/12,1/3),xytext=(.01,.61),fontsize=10,
    arrowprops={'arrowstyle':'->','color':'0.35'})
ax.annotate('Export 1/6',xy=(5/24,1/3),xytext=(.34,.48),fontsize=10,
    arrowprops={'arrowstyle':'->','color':'0.35'})
ax.text(.66,.71,'Buy 3/2',fontsize=10,rotation=31,ha='center',color=blue)
ax.text(.01,1.025,'Battery capacity = 1',fontsize=9,color='0.35')
ax.set(xlim=(-.025,1.04),ylim=(.12,1.12),title='(b) Finite serial actions within early window',
    xlabel='Elapsed early-window time (window units)',
    ylabel='Battery inventory (energy units)')
ax.set_xticks([0,1/6,1/4,1],['0','1/6','1/4','1'])
ax.set_yticks([1/4,5/12,1],['1/4','5/12','1'])
ax.grid(alpha=.16,lw=.6)
fig.text(.5,.15,'Fixed prices p = (−3, 1), vehicle fee c = 2: score = 2 − 3E + L.  Linear query: D = CH = −3/2.',
    ha='center',fontsize=10)
fig.text(.5,.092,'After B: inventory 1/4; terminal purchases 3/2 restore full. Early power 2; terminal power 3.',
    ha='center',fontsize=9)
fig.text(.5,.037,'Analytical illustration of a proved anchor; no simultaneous import/export, experiment or positive support gap.',
    ha='center',fontsize=9)
for name in names:
    # Exclusive handle prevents accidental overwrite even after the initial gate.
    with (out/name).open('xb') as stream:
        fig.savefig(stream,format=name.rsplit('.',1)[1],facecolor='white')
plt.close(fig)
own=resource.getrusage(resource.RUSAGE_SELF)
cpu=own.ru_utime+own.ru_stime;elapsed=time.monotonic()-started
rss=own.ru_maxrss*(1 if sys.platform=='darwin' else 1024)
receipt=dict(status='CREATED',kind='Proved anchor illustration, not experiment or support-gap evidence',
    source_manifest=_source_manifest,outputs=list(names),vertices_exact=vertices,
    early_time_exact=['0','1/6','1/4','1'],inventory_exact=['1/4','5/12','1/4','1'],
    full_score_exact='-3/2',efficient_score_exact='-1',linear_query_gap_exact='0',
    self_cpu_s=cpu,elapsed_s=elapsed,observed_rss_bytes=rss,
    resource_pass=cpu<45 and elapsed<55 and rss<=5*1024**3,
    external_allowance=dict(cpu_s=50,wall_s=60),visual_qa='PENDING')
with (out/receipt_name).open('x') as stream:
    json.dump(receipt,stream,indent=2);stream.write('\n')
if not receipt['resource_pass']:raise RuntimeError('Prospective figure resource allowance exceeded')
