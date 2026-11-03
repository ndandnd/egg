"""One compact stored-energy export; no model, plan, replay, hash or optimizer."""
import time
WALL0 = time.monotonic()
from collections import Counter
from fractions import Fraction as Q
import json
from pathlib import Path
import resource
import signal

BASE = Path(__file__).resolve().parent
ARMS = ('GNN', 'CatBoost', 'CA1', 'CoverCA1', 'random', 'full', 'fixed_route')
CASES = tuple(f'scale:{g}:{n}' for g in range(50600, 50604) for n in (40, 80))
SEEDS = (17, 41, 73)
COMPONENTS = ('ops_exact', 'fleet_operating_exact', 'deadhead_exact', 'linear_electricity_exact',
              'quadratic_electricity_exact', 'electricity_exact', 'grid_kwh_exact', 'total_exact')


def median(values):
    values = sorted(values)
    n = len(values)
    return None if not n else values[n//2] if n % 2 else (values[n//2-1]+values[n//2])/2


def summary(rows, key):
    values = [r[key] for r in rows if r[key] is not None]
    groups = []
    for group in range(50600, 50604):
        v = [r[key] for r in rows if r['group'] == group and r[key] is not None]
        groups.append(dict(group=group, planned=6, defined=len(v), median=median(v) if len(v) == 6 else None))
    return dict(planned=24, defined=len(values), missing=24-len(values), groups=groups,
        mean=sum(values, Q(0))/24 if len(values) == 24 else None,
        median=median(values) if len(values) == 24 else None,
        negative=sum(v < 0 for v in values), zero=sum(v == 0 for v in values), positive=sum(v > 0 for v in values))


def main():
    def expired(signum, frame):
        raise TimeoutError('Energy diagnostic body provision exhausted')
    resource.setrlimit(resource.RLIMIT_CPU, (8, 10))
    signal.signal(signal.SIGXCPU, expired); signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 18-(time.monotonic()-WALL0)))
    out = dict(complete=False, passed=False, cells=[], pairs=[], failures=[], summary_reads=0, scientific_qualification=False)
    try:
        if 48.84+10 > 1800 or 50.59+20 > 2700:
            raise ValueError('Shared QP package cannot fund this provision')
        with (BASE.parents[1]/'research-20261025/warm_replanning/summary.json').open() as stream:
            saved = json.load(stream)  # Exactly one summary read; access only prior/operational fields below.
        out['summary_reads'] = 1
        if saved.get('finalization_passed') is not True:
            raise ValueError('Original compact summary did not pass')
        priors = {r['case']: r for r in saved['acquisitions']}
        records = saved['cells']
        expected = {(case, seed, arm) for case in CASES for seed in SEEDS for arm in ARMS}
        if (set(priors) != set(CASES) or len(records) != 168
                or {(r['case'], r['seed'], r['arm']) for r in records} != expected):
            raise ValueError('Frozen eight-case/168-cell denominator differs')
        indexed = {}
        for r in records:
            prior, parts = priors[r['case']], r.get('operational_decomposition')
            if not r.get('cost_defined') or prior.get('valid_prior') is not True or parts is None:
                raise ValueError('Missing operational cost/prior; no available-only substitute')
            p = prior['target_decomposition']; e0, eprior = Q(prior['target_E0']), Q(p['grid_kwh_exact'])
            if e0 <= 0 or eprior <= 0:
                raise ValueError('Undefined prior energy/electricity normalization')
            c = {k: Q(parts[k]) for k in COMPONENTS}
            row = dict(case=r['case'], group=r['group'], size=r['size'], seed=r['seed'], arm=r['arm'],
                method_accepted=r['method_endpoint_accepted'], method_success=r['method_success'],
                energy_kwh=c['grid_kwh_exact'], E0=e0, cost=c['total_exact'], components=c,
                prior_energy_kwh=eprior, energy_change_vs_prior_kwh=c['grid_kwh_exact']-eprior,
                energy_fraction_vs_prior=(c['grid_kwh_exact']-eprior)/eprior,
                cost_saving_vs_prior_over_E0=(Q(p['total_exact'])-c['total_exact'])/e0)
            out['cells'].append(row); indexed[(r['case'], r['seed'], r['arm'])] = row
        for control in ('CoverCA1', 'CA1', 'random'):
            for case in CASES:
                for seed in SEEDS:
                    g, c = indexed[(case, seed, 'GNN')], indexed[(case, seed, control)]
                    de, dc = g['energy_kwh']-c['energy_kwh'], g['cost']-c['cost']
                    out['pairs'].append(dict(control=control, case=case, group=g['group'], size=g['size'], seed=seed,
                        GNN_minus_control_energy_kwh=de,
                        GNN_minus_control_energy_fraction=None if c['energy_kwh'] == 0 else de/c['energy_kwh'],
                        energy_fraction_missing_reason='zero control energy' if c['energy_kwh'] == 0 else None,
                        control_cost_minus_GNN_cost_over_E0=-dc/g['E0'],
                        energy_change_sign=(de > 0)-(de < 0), GNN_minus_control_cost_sign=(dc > 0)-(dc < 0)))
        out['paired_summaries'] = {}
        for control in ('CoverCA1', 'CA1', 'random'):
            rows = [r for r in out['pairs'] if r['control'] == control]
            out['paired_summaries'][control] = dict(energy=summary(rows, 'GNN_minus_control_energy_fraction'),
                cost=summary(rows, 'control_cost_minus_GNN_cost_over_E0'),
                descriptive_energy_cost_sign_table=dict(Counter('%s,%s' % (r['energy_change_sign'],
                    r['GNN_minus_control_cost_sign']) for r in rows)))
        out['prior_summaries'] = {arm: {key: summary([r for r in out['cells'] if r['arm'] == arm], key)
            for key in ('energy_fraction_vs_prior', 'cost_saving_vs_prior_over_E0')} for arm in ARMS}
        out.update(complete=True, passed=True, denominators=dict(arms=7, cells=168, pairs=72,
            paired_cells_per_control=24, base_units=4, repeated_size_seed_cells_per_base=6))
    except BaseException as exc:
        out['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        signal.signal(signal.SIGXCPU, signal.SIG_IGN); signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 20-(time.monotonic()-WALL0)))
        cpu, wall = time.process_time(), time.monotonic()-WALL0
        out.update(resource=dict(provision_cpu_s=10, provision_wall_s=20, body_cpu_s=8, body_wall_s=18,
            cpu_before_publication_s=cpu, elapsed_before_publication_s=wall,
            shared_QP_cpu_before_this_export_s=48.84, shared_QP_elapsed_before_this_export_s=50.59,
            cumulative_before_this_export_cpu_s=7053.19, cumulative_before_this_export_elapsed_s=7227.81,
            external_meter_required_for_complete_new_cost=True),
            plan_reads=0, replay_calls=0, solver_calls=0, hash_calls=0,
            caveats=['Four exposed base units; nested sizes and repeated seeds are not independent samples',
                'Energy fractions use control energy; cost ratios use prior late electricity E0',
                'Sign table axes are GNN-minus-control energy and cost; association is descriptive only',
                'No causal tariff-information, timing decomposition, speedup or model-promotion claim'])
        with (BASE/'energy-diagnostic.json').open('x') as stream:
            json.dump(out, stream, indent=2, allow_nan=False, default=lambda v: str(v) if isinstance(v, Q) else v)
            stream.write('\n')
        print(json.dumps(dict(complete=out['complete'], passed=out['passed'], failures=out['failures'],
            denominators=out.get('denominators'), paired_summaries=out.get('paired_summaries'),
            GNN_prior_energy=out.get('prior_summaries', {}).get('GNN', {}).get('energy_fraction_vs_prior')),
            indent=2, allow_nan=False, default=lambda v: float(v) if isinstance(v, Q) else v))
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if out['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
