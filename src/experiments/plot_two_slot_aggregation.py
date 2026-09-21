"""Render the exact exploratory output; this performs no optimization."""
import argparse
from fractions import Fraction
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.result.read_text())
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.3), layout='constrained')
    definitions = [
        ('fixed_unit_and_slope', 'Unit blocks; fixed supply slope', '#215d9c'),
        ('replicated_market', 'Unit blocks; supply slope 1/N', '#d77b24'),
        ('fixed_total_energy', 'Fixed total energy; fixed slope', '#239079'),
    ]
    metrics = [('gap', 'Absolute planning gap', 'Cost units'),
               ('relative_gap', 'Relative planning gap', 'Gap / convexified cost'),
               ('minimum_max_individual_unrestricted_regret',
                'Best attainable worst-fleet regret', 'Cost units')]
    for prefix, label, color in definitions:
        rows = [r for r in data['rows'] if r['name'].startswith(prefix+'_n')
                and r['participants'] % 2]
        for index, (metric, title, ylabel) in enumerate(metrics):
            if index == 1 and prefix != 'fixed_unit_and_slope':
                continue  # Exact same 1/N^2 curve for all three normalizations.
            axes[index].plot([r['participants'] for r in rows],
                             [float(Fraction(r[metric])) for r in rows],
                             marker='o', color=color,
                             label='All three regimes' if index == 1 else label)
            axes[index].set(title=title, xlabel='Participants N (odd values)', ylabel=ylabel,
                            yscale='log', xticks=[1, 3, 5, 7, 9, 11])
            axes[index].grid(alpha=.2, which='both')
    axes[1].text(.55, .75, 'Same relative gap;\ndifferent private incentives',
                 transform=axes[1].transAxes, ha='center', fontsize=10)
    axes[0].legend(fontsize=8, loc='lower left')
    fig.suptitle('Finite duty menus: a small relative gap does not determine individual regret', fontsize=13)
    fig.supxlabel('Exact rational calculations, zero base price. All even-N homogeneous cases have zero gap and regret.\n'
                  'Explanatory two-slot menus; not a full bus-scheduling or empirical scaling result.', fontsize=9)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output.with_suffix('.png'), dpi=180)
    fig.savefig(args.output.with_suffix('.pdf'))


if __name__ == '__main__':
    main()
