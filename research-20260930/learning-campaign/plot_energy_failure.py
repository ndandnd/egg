"""Plot selected-route necessary energy violations; no optimization."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
report = json.loads((HERE/'ENERGY_FEASIBILITY_DIAGNOSIS.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
    'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
fig, axes = plt.subplots(2, 2, figsize=(9, 7.2), sharex=True)
for ax, cell in zip(axes.flat, report['cells']):
    buses = cell['vehicles']
    values = [max(float(s['consumption_kwh']) for s in v['segments']) for v in buses]
    learned = cell['policy']=='cost_learned'
    color = '#BC6327' if learned else '#315B76'
    ax.barh(range(len(buses)), values, height=.58, color=color)
    ax.axvline(80, color='#8B2429', linewidth=1.5, linestyle='--')
    for i,value in enumerate(values):
        ax.text(value+3,i,f'{value:.1f}',va='center',fontsize=9)
    ax.set_yticks(range(len(buses)), [f'Bus {v["vehicle"]+1}' for v in buses])
    ax.set_ylim(len(buses)-.45,-.65)
    ax.set_xlim(0,275)
    services = 20 if '2016' in cell['case'] else 28
    ax.set_title(f'{services} services · '+('Learned tie score' if learned else 'Cost only'),loc='left',fontsize=11,pad=12)
    ax.set_xticks([0,80,160,240])
    ax.xaxis.grid(True,alpha=.16)
    ax.set_axisbelow(True)
    ax.tick_params(axis='y',length=0)
for ax in axes[1]: ax.set_xlabel('Longest uncharged stretch (kWh)',labelpad=10)
fig.suptitle('Fewer buses, but routes exceed the battery range',x=.07,ha='left',fontsize=16,weight='bold',y=.98)
fig.text(.07,.902,'All 14 proposed routes exceed the usable 80 kWh battery (dashed line).\nEnergy includes service trips and travel; depot departures are optimistically fully charged.',fontsize=10,color='#444444')
fig.text(.07,.025,'Four development cells; these failures concern the selected routes only.\nThey do not establish that every fleet with three or four buses is infeasible.',fontsize=9,color='#555555')
fig.subplots_adjust(left=.10,right=.975,top=.82,bottom=.15,wspace=.27,hspace=.38)
for ext in ('png','svg'): fig.savefig(HERE/f'cost_aware_energy_failure.{ext}',dpi=180,facecolor='white')

svg = HERE / "cost_aware_energy_failure.svg"
svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")
