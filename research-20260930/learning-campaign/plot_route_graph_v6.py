"""Paired descriptive comparison of frozen inner-selected model policies."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
v5 = json.loads((ROOT / 'ROUTE_FAMILIES_V5_REPLAY.json').read_text())
v6 = json.loads((ROOT / 'ROUTE_GRAPH_V6_REPLAY.json').read_text())
a = v5['per_group_seed_and_source_averages']
b = v6['per_group_seed_and_source_averages']
groups = sorted(a)
if set(groups) != set(b) or len(groups) != 128:
    raise ValueError('Mismatched comparison cohorts')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4))
for ax, key, title, scale in zip(axes,
        ('weighted_log_loss', 'input_trip_count_topk_recall_mean_by_fleet'),
        ('Probability log loss: lower is better', 'Top-k edge recall (%): higher is better'), (1, 100)):
    x = np.array([a[g]['inner_promoted'][key] for g in groups]) * scale
    y = np.array([b[g]['inner_promoted'][key] for g in groups]) * scale
    lo, hi = min(x.min(), y.min()), max(x.max(), y.max())
    pad = (hi-lo)*.06
    ax.plot([lo-pad, hi+pad], [lo-pad, hi+pad], color='#929da6', ls='--', lw=1, label='Equal score')
    ax.scatter(x, y, s=21, alpha=.65, color='#216b8e', edgecolors='none')
    ax.scatter([x.mean()], [y.mean()], s=95, color='#d1642c', marker='D', edgecolors='white', linewidth=.8, zorder=4, label='Mean')
    ax.set(xlabel='Tree-family policy (v5)', ylabel='Graph policy (v6)', title=title,
           xlim=(lo-pad,hi+pad), ylim=(lo-pad,hi+pad))
    ax.grid(alpha=.16)
    ax.set_aspect('equal', adjustable='box')
    ax.text(.04, .96, f'Means: {x.mean():.4f} → {y.mean():.4f}' if scale == 1 else f'Means: {x.mean():.2f}% → {y.mean():.2f}%', transform=ax.transAxes, va='top', fontsize=9)
axes[1].legend(loc='lower right', frameon=False, fontsize=9)
fig.suptitle('Graph models improve edge ranking; probability loss remains mixed', fontsize=13, y=.99)
fig.text(.5, .025, '128 TRAIN timetables; each point averages source fleets and three seeds. Both policies select using inner validation.\nExploratory edge imitation: route feasibility, fleet cost and online speedup require separate evaluation.', ha='center', fontsize=8.5, color='#414b53')
fig.tight_layout(rect=(0,.12,1,.95))
out=ROOT/'figures';out.mkdir(exist_ok=True)
fig.savefig(out/'route_graph_v6_paired.png',dpi=190)
fig.savefig(out/'route_graph_v6_paired.pdf')
