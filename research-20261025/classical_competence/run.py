"""Two-case offline classical construction/charging competence check; no recovery controller."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import threading
import time

CASES = ('scale:50685:40', 'scale:50605:80')
THREAD_KEYS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
               'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')
for key in THREAD_KEYS:
    os.environ[key] = '1'


def save_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path, value):
    temporary = path.with_name(path.name+'.final.tmp')
    save_new(temporary, value)
    os.replace(temporary, path)  # Only this process's exclusive incomplete placeholder.


def rss_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(raw if sys.platform == 'darwin' else raw*1024)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    receipt = output/'receipt.json'
    save_new(receipt, {'complete': False, 'passed': False, 'pid': os.getpid(),
        'failure': 'No complete offline competence report published'})
    start, cpu0 = time.monotonic(), time.process_time()
    hashes, seen_sources, stopped = {}, set(), None
    report = {'complete': False, 'passed': False, 'cases': [], 'pid': os.getpid(),
        'scope': 'offline classical competence; not main60s comparison or native controller qualification',
        'seed_policy': 'backend default, unmodified; actual numeric default not independently exposed',
        'seed17_claim': False, 'repairs': 0, 'pruning': False, 'full_search': False,
        'scientific_qualification': False}

    def check(deadline=None):
        if stopped is not None:
            raise TimeoutError('Offline package stop retained: '+str(stopped))
        if time.process_time()-cpu0 >= 225 or time.monotonic()-start >= 165:
            raise TimeoutError('Package body225CPU/165wall exhausted; reserve15 for closure')
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError('Offline case stage deadline exhausted')
        if rss_bytes() > 5*1024**3 or threading.active_count() != 1:
            raise RuntimeError('Observed peakRSS5GiB or single-Python-thread limit failed')

    def read(path, *, expected=None, parse=True):
        check()
        path = path.resolve()
        name = str(path.relative_to(root))
        if name in hashes:
            raise ValueError('Input/source already read and hashed: '+name)
        with path.open('rb') as stream:
            raw = stream.read(64*1024*1024+1)
        if len(raw) > 64*1024*1024:
            raise ValueError('Input/source exceeds64MiB')
        digest = hashlib.sha256(raw).hexdigest()
        hashes[name] = digest
        if expected is not None and expected.get(name) != digest:
            raise ValueError('Historical context receipt digest differs: '+name)
        return json.loads(raw) if parse else None

    def source_closure():
        for name, module in sorted(tuple(sys.modules.items())):
            if name == 'egglab' or name.startswith('egglab.'):
                filename = getattr(module, '__file__', None)
                if filename and filename.endswith('.py'):
                    path = Path(filename).resolve()
                    if not path.is_relative_to(root/'src/egglab'):
                        raise ValueError('Project module outside this worktree: '+name)
                    if path not in seen_sources:
                        read(path, parse=False); seen_sources.add(path)

    try:
        def interrupted(signum, frame):
            nonlocal stopped
            if stopped is None:
                stopped = signum
            raise TimeoutError('Offline package received stop/alarm'+str(signum))
        resource.setrlimit(resource.RLIMIT_CPU, (240, 240))
        for sig in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, interrupted)
        signal.alarm(180)
        read(Path(__file__), parse=False)
        read(Path(__file__).with_name('PROTOCOL.md'), parse=False)
        lock = read(root/'research-20261017/local-assets-v3.json')
        summary = read(root/'research-20261017/screen-analysis-v3-final/summary.json')
        audit = read(root/'research-20261017/FINAL_REPLAY_VERIFICATION.json')
        if not summary.get('complete') or not audit.get('passed') or audit.get('mismatch_count') != 0:
            raise ValueError('Historical development context is incomplete')
        screen = lock['manifest']['cohorts']['screen']
        selected = tuple(min(c['case_key'] for c in screen if c['services'] == size) for size in (40, 80))
        if selected != CASES:
            raise ValueError('Prospectively selected lexicographic screen cases differ')
        context = {}
        for case_key in CASES:
            matches = [c for c in summary['cells'] if c['task']['case_key'] == case_key
                and c['task']['seed'] == 17 and c['task']['arm'] == 'v8' and c['valid']]
            if len(matches) != 1:
                raise ValueError('Missing unique historical graph context')
            cell = matches[0]
            folder = root/'research-20261017/local-screen-v3'/cell['directory']
            result = read(folder/'result.json', expected=audit['input_sha256'])
            supervisor = read(folder/'supervisor.json', expected=audit['input_sha256'])
            if (result['task'] != cell['task'] or result.get('accepted_valid') is not True
                    or supervisor.get('endpoint_valid') is not True or supervisor.get('endpoint_censored') is not False):
                raise ValueError('Historical graph context admission differs')
            context[case_key] = {'directory': cell['directory'], 'vehicles': result['vehicles'],
                'bill_exact': result['bill_exact'], 'seed': 17,
                'interpretation': 'unmatched historical learned/pruned endpoint; different default seed/allocation; no speedup or paired effect'}
        sys.path.insert(0, str(root/'src'))
        from egglab import claude_cases, physical_learning_cases as bank
        from egglab import constructive_control as control, constructive_charging as charging
        from egglab import native_recharge as nr, native_pathflow as pf, native_hull as nh
        source_closure()
        optimizer, builder = pf._optimize_once, pf.build_feasible_model
        if optimizer is not nr._optimize_once:
            raise RuntimeError('Unexpected preinstalled native hook; no hook is disabled or replaced')
        report['policies'] = {'construction': control.POLICY, 'completion': charging.POLICY}
        for case_key in CASES:
            check()
            folder = output/case_key.replace(':', '-')
            folder.mkdir(exist_ok=False)
            case_receipt = folder/'receipt.json'
            anchor, case_cpu = time.monotonic(), time.process_time()
            end, charging_end = anchor+60., anchor+55.
            save_new(case_receipt, {'complete': False, 'case': case_key})
            row = {'case': case_key, 'anchor_monotonic': anchor, 'deadline': end,
                'completion_deadline': charging_end, 'complete': False, 'physical_witness_valid': False,
                'stages': [], 'failures': [], 'historical_graph_context': context[case_key],
                'native_seed': None, 'native_seed_policy': report['seed_policy']}
            events = (folder/'events.jsonl').open('x')
            stage = 'case_construction'
            def timed(label, operation):
                nonlocal stage
                stage = label
                entry, cpu = time.monotonic(), time.process_time()
                try:
                    return operation()
                finally:
                    row['stages'].append({'stage': label, 'wall_s': time.monotonic()-entry,
                        'cpu_s': time.process_time()-cpu, 'observed_peak_rss_bytes': rss_bytes()})
            def record(event):
                check(charging_end)
                events.write(json.dumps(event, allow_nan=False)+'\n')
                events.flush()
                check(charging_end)
            try:
                case = timed('case_construction', lambda: claude_cases.make(case_key))
                check(anchor+10.)
                mapping = lock['cases'][case_key]
                if case.identity() != mapping['identity'] or [m.id for m in case.movements] != mapping['movement_ids']:
                    raise ValueError('Original full physical case/movement mapping differs')
                market = bank.market(case, 'day')
                row.update(case_identity=case.identity(), market_identity=market.identity(),
                    full_movements=len(case.movements), trips=len(case.trips))
                ledger = timed('construct_routes', lambda: control.construct_routes(case, deadline=anchor+10.))
                timed('save_construction', lambda: save_new(folder/'construction.json', ledger))
                check(anchor+10.)
                row['constructed_vehicles'] = len(ledger['routes'])
                if ledger['status'] != 'proposal' or not ledger['selected_ids']:
                    row['status'] = 'no_constructive_proposal'
                else:
                    remaining = charging_end-time.monotonic()
                    check(charging_end)
                    budget = nr.Budget(backend='GRB', threads=1, phase_seconds=remaining,
                        wall_seconds=remaining, max_rounds=3, epsilon=1e-4)
                    completed = timed('complete_topology', lambda: charging.complete_topology(
                        case, ledger['selected_ids'], market.a, market.b, budget,
                        deadline=charging_end, record=record))
                    row['completion'] = completed
                    if any(s['stats'].get('threads') != 1 for s in completed.get('stages', []) if 'stats' in s):
                        raise RuntimeError('Native stage did not report one thread')
                    check(charging_end)
                    if completed.get('plan') is None:
                        row['status'] = 'charging_unresolved'
                    else:
                        plan = completed['plan']
                        replay = timed('independent_replay', lambda: nr.replay_native(case, plan))
                        check(end)
                        bill = F(replay['ops_cost'])+nh.supply(market, replay['load'])
                        if (replay.get('replay_ok') is not True or replay != completed['replay']
                                or bill != F(completed['true_bill_exact'])
                                or {mid for v in plan['vehicles'] for mid in v['movements']} != set(ledger['selected_ids'])):
                            raise ValueError('Independent physical/topology/exact-objective check failed')
                        timed('save_physical_witness', lambda: (
                            save_new(folder/'plan.json', plan), save_new(folder/'replay.json', replay)))
                        check(end)
                        old = F(context[case_key]['bill_exact'])
                        row.update(status='replayed_offline_witness', physical_witness_valid=True,
                            vehicles=len(plan['vehicles']), objective_exact=str(bill),
                            unmatched_relative_objective_context=str((old-bill)/old),
                            witness_ready_monotonic=time.monotonic())
                if pf._optimize_once is not optimizer or pf.build_feasible_model is not builder:
                    raise RuntimeError('Unexpected native hook mutation')
            except Exception as exc:
                row.update(status='failed_or_unresolved')
                row['failures'].append({'stage': stage, 'type': type(exc).__name__, 'message': str(exc)})
            finally:
                events.flush(); os.fsync(events.fileno()); events.close()
                row.update(complete=True, elapsed_before_receipt_s=time.monotonic()-anchor,
                    cpu_before_receipt_s=time.process_time()-case_cpu, observed_peak_rss_bytes=rss_bytes())
                publish(case_receipt, row)
            elapsed = time.monotonic()-anchor
            report['cases'].append({'case': case_key, 'receipt': str(case_receipt.relative_to(root)),
                'status': row['status'], 'elapsed_including_receipt_s': elapsed,
                'cpu_including_receipt_s': time.process_time()-case_cpu,
                'accepted_within_offline60': row['physical_witness_valid'] and elapsed <= 60.,
                'physical_witness_valid': row['physical_witness_valid'],
                'vehicles': row.get('vehicles'), 'objective_exact': row.get('objective_exact')})
            if pf._optimize_once is not optimizer or pf.build_feasible_model is not builder:
                raise RuntimeError('Unexpected hook mutation stops the offline package')
            source_closure()
        check()
        report.update(complete=True, passed=True,
            feasible_cases=sum(c['accepted_within_offline60'] for c in report['cases']))
    except BaseException as exc:
        report.update(passed=False, failure={'type': type(exc).__name__, 'message': str(exc)})
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report.update(input_source_sha256=hashes, cpu_s=time.process_time()-cpu0,
            stop_signal=stopped,
            wall_s=time.monotonic()-start, observed_peak_rss_bytes=rss_bytes(),
            rusage={'utime_s': usage.ru_utime, 'stime_s': usage.ru_stime,
                'maxrss_platform_units': usage.ru_maxrss, 'platform': sys.platform},
            budget={'total_cpu_s': 240, 'outer_wall_s': 180, 'case_s': 60,
                'constructor_s': 10, 'completion_cutoff_s': 55, 'replay_final_s': 5},
            interpretation='passed means completed diagnostic records, not feasible construction in every case or comparative superiority')
        publish(receipt, report)
        signal.alarm(0)
    print(json.dumps({'complete': report['complete'], 'passed': report['passed'],
        'feasible_cases': report.get('feasible_cases'), 'receipt': str(receipt)}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
