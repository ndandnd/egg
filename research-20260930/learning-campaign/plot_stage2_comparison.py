"""Plot archived development bounds; no optimizer or model is invoked."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
ARMS = ['cold', 'retained', 'nearest_price', 'cheapest_bill', 'learned']
NAMES = {'cold':'Cold', 'retained':'Retained pool', 'nearest_price':'Nearest price',
         'cheapest_bill':'Cheapest cached fleet', 'learned':'Learned selection'}
with (HERE / 'RESULTS_STAGE2_CELLS.csv').open() as stream:
    rows = list(csv.DictReader(stream))
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10,
                     'axes.spines.top':False, 'axes.spines.right':False,
                     'axes.spines.left':False, 'svg.fonttype':'none'})
fig, axes = plt.subplots(2, 1, figsize=(8, 9.7))
for ax, seed, services in zip(axes, (2016, 2017), (20, 28)):
    selected = {r['arm']:r for r in rows if int(r['seed']) == seed}
    lower = min(float(selected[a]['hull_lower']) for a in ARMS)
    upper = max(float(selected[a]['physical_upper']) for a in ARMS)
    span = upper-lower
    labels = []
    for y, arm in enumerate(ARMS):
        row = selected[arm]
        lo, hi, fleet = [float(row[k]) for k in ('hull_lower','mixture_upper','physical_upper')]
        color = '#C46420' if arm == 'learned' else '#315B76'
        ax.hlines(y, lo, hi, color=color, linewidth=3)
        ax.plot([lo, hi], [y,y], '|', color=color, markersize=11, markeredgewidth=1.6)
        ax.plot(fleet, y, '^', color=color, markersize=7)
        ax.annotate(f'{fleet:.2f}', (fleet,y), xytext=(5,-3), textcoords='offset points',
                    color=color, fontsize=9)
        labels.append(f"{NAMES[arm]}\n{float(row['wall_seconds']):.1f} s")
    ax.set_yticks(range(len(ARMS)), labels)
    ax.tick_params(axis='y', length=0, pad=9)
    ax.invert_yaxis()
    ax.set_ylim(4.55,-0.6)
    ax.set_xlim(lower-0.055*span, upper+0.27*span)
    ax.xaxis.grid(True, color='#E6E6E6', linewidth=.8)
    ax.set_axisbelow(True)
    ax.set_xlabel('Objective value (cost units)', labelpad=9)
    ax.set_title(f'{services} services · development timetable {seed}',
                 loc='left', fontsize=12, weight='bold', pad=15)
fig.suptitle('Larger fleets: feasible solutions arrive\nbefore tight bounds',
             x=.03, ha='left', fontsize=16, weight='bold', y=.99)
fig.text(.03,.897,'Learned selection chose the same cached fleet as nearest-price\nand cheapest-cost selection in both cases.',
         fontsize=10, color='#444444')
legend = [Line2D([0],[0],color='#315B76',lw=3,marker='|',markersize=10,label='Hull lower–upper bounds'),
          Line2D([0],[0],color='#315B76',lw=0,marker='^',markersize=7,label='Best feasible fleet found')]
fig.legend(handles=legend, loc='lower left', bbox_to_anchor=(.02,.055), ncol=2,
           frameon=False, fontsize=10)
fig.text(.03,.018,'Times are target-cell wall time; source acquisition and inference are additional.\n'
         'Single development runs; intervals are optimization bounds, not confidence intervals.',
         fontsize=8.8, color='#555555')
fig.subplots_adjust(left=.29,right=.97,top=.84,bottom=.15,hspace=.53)
for extension in ('png','svg'):
    fig.savefig(HERE / f'stage2_development_bounds.{extension}',dpi=180,facecolor='white')
