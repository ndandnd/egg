"""Analytical k=3 transition construction, not an experimental observation.

Source-only preparation: parent must freeze and launch once before rendering.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

started=globals().get('_artifact_started',time.monotonic())
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
def expired(signum,frame):raise TimeoutError('45-second analytical figure boundary')
signal.signal(signal.SIGALRM,expired)
remaining=45-(time.monotonic()-started)
if remaining<=0:raise TimeoutError('Artifact startup consumed the wall allowance')
signal.setitimer(signal.ITIMER_REAL,remaining)
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/egg-paper-matplotlib-transition-20261029')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

here=Path(__file__).resolve().parent;out=here/'figures-transition'
out.mkdir(exist_ok=False)
blue,orange='#17609a','#c65c21'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,
    'axes.titlesize':10,'axes.spines.top':False,'axes.spines.right':False,
    'legend.fontsize':8,'savefig.dpi':260,'pdf.fonttype':42})

# Literal values of the proved family: k=3, w=(1,2,4), B=80.
# No solver, data, random generator, interpolation or case selection is used.
requirements=tuple(range(0,43,6));K=148;S_max=380
fig,axes=plt.subplots(1,2,figsize=(8.1,3.9))
fig.subplots_adjust(left=.085,right=.98,bottom=.25,top=.74,wspace=.27)
fig.suptitle('Varying transition energy: physical pieces and a simple hull',fontsize=11,y=.985)
for ax in axes:
    for i,R in enumerate(requirements):
        right=requirements[i+1] if i+1<len(requirements) else K
        y0,y1=S_max-3*R,S_max-2*R-right
        ax.plot([R,right],[y0,y1],color=blue,lw=2.7,zorder=3)
        ax.scatter([R],[y0],s=25,color=blue,zorder=6,clip_on=False)
        if i+1<len(requirements):
            ax.scatter([right],[y1],s=25,facecolors='white',edgecolors=blue,linewidths=1.3,zorder=6)
        else:
            ax.scatter([right],[y1],s=25,color=blue,zorder=6)
    ax.plot([0,42,148],[380,254,148],color=orange,lw=1.9,ls=(0,(5,3)),zorder=4)
    ax.set_xlabel('Early grid energy E (synthetic energy units)')
    ax.set_ylabel('Terminal grid energy L (same units)')
    ax.grid(axis='both',alpha=.14,lw=.6)
axes[0].set(xlim=(-2,151),ylim=(140,390),title='(a) Entire efficient frontier')
axes[0].set_xticks([0,42,100,148]);axes[0].set_yticks([148,254,320,380])
axes[1].set(xlim=(0,48),ylim=(240,390),title='(b) Zoom: 0 <= E <= 48')
axes[1].set_xticks([0,6,12,18,24,30,36,42,48]);axes[1].set_yticks([254,290,335,380])
handles=[Line2D([0],[0],color=blue,lw=2.7,label='Efficient physical pieces'),
    Line2D([0],[0],color=orange,lw=1.9,ls=(0,(5,3)),label='Lower convex hull'),
    Line2D([0],[0],marker='o',color='none',markerfacecolor=blue,markeredgecolor=blue,markersize=4.5,label='Included endpoint'),
    Line2D([0],[0],marker='o',color='none',markerfacecolor='white',markeredgecolor=blue,markersize=4.5,label='Excluded right endpoint')]
fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.52,.92),ncol=2,frameon=False,columnspacing=2.0,handlelength=2.6,labelspacing=.6)
fig.text(.5,.105,'Analytical illustration: k = 3, weights (1, 2, 4), capacity B = 80; constant six-bus fee omitted.',ha='center',fontsize=8)
fig.text(.5,.055,'The right panel enlarges the first 48 energy units. Eight physical pieces do not imply eight hull vertices or hardness.',ha='center',fontsize=8)

names=('transition_frontier.png','transition_frontier.pdf')
for name in names:fig.savefig(out/name,facecolor='white')
plt.close(fig)
own=resource.getrusage(resource.RUSAGE_SELF)
cpu=own.ru_utime+own.ru_stime;elapsed=time.monotonic()-started
rss=own.ru_maxrss*(1 if sys.platform=='darwin' else 1024)
receipt=dict(status='CREATED',kind='Proved analytical family illustration; not numerical qualification or empirical experiment',
    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),outputs=list(names),
    parameters=dict(k=3,weights=[1,2,4],battery=80,early_budget=148,terminal_budget=380,requirements=list(requirements),fleet=6),
    physical_rule='L=380-2R-E; R<=E<R_next, final42<=E<=148',
    hull_vertices=[[0,380],[42,254],[148,148]],self_cpu_s=cpu,elapsed_s=elapsed,observed_rss_bytes=rss,
    cpu_ceiling_s=30,wall_ceiling_s=45,observed_rss_ceiling_bytes=5*1024**3,
    resource_pass=cpu<30 and elapsed<45 and rss<=5*1024**3,visual_qa='PENDING',
    runtime='Admitted Matplotlib3.9.4 Agg; separate external50CPU/60wall inclusive meter authoritative')
with (out/'FIGURE_RECEIPT.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
signal.alarm(0)
if not receipt['resource_pass']:raise RuntimeError('Rendered output exceeds prospective body allowance')
