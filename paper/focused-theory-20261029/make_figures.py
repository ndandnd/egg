"""Render proved analytical formulas, not new experimental observations."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import time

started=time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('45s authoring boundary')))
signal.alarm(45)
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/egg-paper-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

here=Path(__file__).resolve().parent
out=here/'figures'
out.mkdir(exist_ok=True)
for name in ('physical_cost_frontier.png','support_regions.png','FIGURE_RECEIPT.json'):
    if (out/name).exists(): raise FileExistsError('No silent authoring overwrite: '+name)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
    'axes.spines.right':False,'axes.labelsize':9,'legend.fontsize':8,'savefig.dpi':240})
navy,teal,orange='#163f5b','#167b73','#bf5936'
x=np.linspace(0,10,501)
g=90-2*x+x*x/5
fig,axes=plt.subplots(1,2,figsize=(7.1,3.0),layout='constrained')
ax=axes[0]
ax.plot(x,np.full_like(x,14),color=navy,lw=2.2,label='Physical two-bus branch')
ax.scatter([10],[7],color=navy,s=45,zorder=5,label='Physical one-bus plan')
ax.plot(x,14-.7*x,color=teal,lw=2,ls='--',label='Lower hull boundary')
ax.scatter([6.75],[14-.7*6.75],facecolors='white',edgecolors=teal,s=55,zorder=6)
ax.annotate('Hull optimum\nnot a physical cost',xy=(6.75,9.275),xytext=(.4,7.2),
            arrowprops={'arrowstyle':'->','color':teal},fontsize=8,color=teal)
ax.set(xlim=(-.2,10.3),ylim=(6.5,15),xlabel='Early energy E (kWh)',ylabel='Vehicle operating cost',title='(a) Joint load–cost frontier')
ax.legend(loc='upper right',frameon=False)
ax=axes[1]
ax.plot(x,14+g,color=navy,lw=2.2,label='Physical two-bus cost')
ax.plot(x,14-.7*x+g,color=teal,lw=2,ls='--',label='Convexified cost')
ax.scatter([10],[97],color=navy,s=45,zorder=5)
ax.axhline(97,color=navy,lw=.8,ls=':')
ax.scatter([6.75],[7591/80],facecolors='white',edgecolors=teal,s=55,zorder=6)
ax.annotate('',xy=(6.75,97),xytext=(6.75,7591/80),arrowprops={'arrowstyle':'<->','color':orange})
ax.text(6.25,98.2,'D = 97',color=navy,fontsize=8)
ax.text(1.0,94.3,'CH = 94.8875',color=teal,fontsize=8)
ax.text(7.05,95.6,'Gap\n2.1125',color=orange,fontsize=8)
ax.set(xlim=(-.2,10.3),ylim=(93.5,105),xlabel='Early energy E (kWh)',ylabel='Vehicle + supply cost',title='(b) Physical and hull objectives')
ax.legend(loc='upper right',frameon=False)
fig.savefig(out/'physical_cost_frontier.png')
plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(7.1,3.1),layout='constrained')
K=np.linspace(20,30,801)
d=K-20
lower=np.maximum(0,.4*d*(5-d))
upper=2*d
ax=axes[0]
ax.fill_between(K,lower,upper,color=orange,alpha=.2,label='Strictly positive gap (interior)')
ax.plot(K,upper,color=orange,lw=1.5)
ax.plot(K,lower,color=orange,lw=1.5)
ax.axhline(7,color=navy,ls=':',lw=1)
ax.scatter([23.5],[7],facecolors='white',edgecolors=navy,s=35,zorder=5)
ax.text(20.3,7.5,'Fee 7: threshold K = 23.5',fontsize=8,color=navy)
ax.text(25.8,8.5,'Unsupported',color=orange,fontsize=9)
ax.text(20.7,17,'Supported',color=teal,fontsize=9)
ax.set(xlim=(20,30),ylim=(0,21),xlabel='Terminal connector K (kW)',ylabel='Used-bus fee f',title='(a) Capacity can expose the obstruction')
ax=axes[1]
B=np.linspace(20,30,1001)
a=30-B
qtop=np.minimum(14+2*a-.4*a*a,7+(10-a)*(.4*a-2))
valid=(a>5)&(qtop>=7)
ax.axhspan(7,10.4,color=orange,alpha=.09)
ax.fill_between(B,7,qtop,where=valid,color=teal,alpha=.32)
ax.plot(B[valid],qtop[valid],color=teal,lw=1.5)
threshold=(55-np.sqrt(95))/2
ax.plot([threshold,30],[7,7],color=teal,lw=2.5)
ax.scatter([25],[8],color=orange,s=35,zorder=5)
ax.annotate('B = 25, fee 8:\ngap = 0.05',xy=(25,8),xytext=(26.1,8.7),
            arrowprops={'arrowstyle':'->','color':orange},fontsize=8,color=orange)
ax.text(22.9,7.55,'Supported',color=teal,fontsize=8,rotation=90)
ax.text(20.3,9.7,'Unsupported outside the green set',color=orange,fontsize=8)
ax.set(xlim=(20,30),ylim=(6.8,10.4),xlabel='Added battery capacity B (kWh)',ylabel='Added-bus fee q',title='(b) Better equipment need not restore support')
fig.savefig(out/'support_regions.png')
plt.close(fig)
signal.alarm(0)
own=resource.getrusage(resource.RUSAGE_SELF)
receipt={'status':'CREATED','kind':'analytical-formula illustrations, no empirical observations',
    'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'outputs':['physical_cost_frontier.png','support_regions.png'],
    'self_cpu_s':own.ru_utime+own.ru_stime,'elapsed_s':time.monotonic()-started,
    'peak_rss_native_units':own.ru_maxrss,'cpu_ceiling_s':30,'wall_ceiling_s':45,
    'visual_qa':'PENDING','runtime':'Matplotlib Agg; full external time meter authoritative'}
with (out/'FIGURE_RECEIPT.json').open('x') as stream: json.dump(receipt,stream,indent=2)
