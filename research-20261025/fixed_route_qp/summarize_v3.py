"""One closed-v3 compact readout; no hashes, project imports or numerical calls."""
import time
START, CPU0 = time.monotonic(), time.process_time()
import json, math, os, resource, signal
from decimal import Decimal as D
from fractions import Fraction as Q
from pathlib import Path
BASE = Path(__file__).resolve().parent

def check():
    if time.monotonic()-START > 19 or time.process_time()-CPU0 > 14:
        raise TimeoutError('Readout body allowance exhausted; publication reserve1')

def read(path):
    check()
    return json.loads(path.read_text())

def display(value):
    try:
        number = float(Q(value))
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        return None

def main():
    output = BASE/'mechanism-summary-v3.json'
    if output.exists():
        raise FileExistsError('Exclusive v3 readout already exists')
    report = dict(complete=False, scope='separate one-case Method0 fixed-route qualification',
        old_attempts_modified=False, numerical_calls=0, failure=None)
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    def expired(signum, frame):
        raise TimeoutError('Readout wall20 exhausted')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 20-(time.monotonic()-START)))
    try:
        parts = [line.split() for line in (BASE/'process-time-v3.txt').read_text().splitlines() if line.strip()]
        if len(parts) != 3 or any(len(pair) != 2 for pair in parts):
            raise ValueError('Require one closed external real/user/sys meter')
        meter = {key: D(value) for key, value in parts}
        if set(meter) != {'real', 'user', 'sys'} or any(not v.is_finite() or v < 0 for v in meter.values()):
            raise ValueError('Malformed external v3 meter')
        cpu, wall = meter['user']+meter['sys'], meter['real']
        if cpu+D(15) > D(120) or wall+D(20) > D(180) or D('48.88')+cpu+D(15) > D(1800) or D('50.65')+wall+D(20) > D(2700):
            raise ValueError('Actual v3 run plus readout reserve is not prospectively funded')
        closed = read(BASE/'FINAL_RESOURCE_RECEIPT.json')
        expected = {'closed_QP_package_cpu_s': '48.88', 'closed_QP_package_elapsed_sum_s': '50.65',
            'closed_cumulative_cpu_s': '7053.23', 'closed_cumulative_elapsed_sum_s': '7227.87'}
        if any(D(str(closed[k])) != D(v) for k, v in expected.items()):
            raise ValueError('Immutable closed-resource carry differs')
        report['external_reconciliation'] = dict(closed_package_cpu_s='48.88', closed_package_elapsed_sum_s='50.65',
            v3_cpu_s=str(cpu), v3_elapsed_s=str(wall), package_through_v3_cpu_s=str(D('48.88')+cpu),
            package_through_v3_elapsed_sum_s=str(D('50.65')+wall), cumulative_through_v3_cpu_s=str(D('7053.23')+cpu),
            cumulative_through_v3_elapsed_sum_s=str(D('7227.87')+wall), own_external_postmeter='PENDING',
            measurement='decimal reconciliation of rounded external process meters; excludes this readout until its external meter closes')
        report['legacy'] = {k: closed[k] for k in ('legacy_conditional_guard_s', 'legacy_actual_review_cpu', 'historical_charges_reset')}
        master = read(BASE/'attempt03/receipt.json')
        if len(master['cases']) != 1 or master['cases'][0]['case'] != 'scale:50603:80':
            raise ValueError('Require exactly the assigned v3 case')
        external = master['cases'][0]
        folder = BASE/'attempt03/008-qp-scale-50603-80'
        if Path(external['folder']).resolve() != folder.resolve():
            raise ValueError('Closed v3 worker folder differs')
        worker, helper = external['worker'], read(folder/'qp-result.json')
        old = read(BASE/'attempt02/008-qp-scale-50603-80/qp-result.json')
        old_receipt = read(BASE/'attempt02/008-qp-scale-50603-80/receipt.json')
        prior = Q(old_receipt['fallback_bill_exact'])
        if Q(helper['fallback_bill_exact']) != prior or Q(worker['fallback_bill_exact']) != prior:
            raise ValueError('Common prior cost differs across policies')
        endpoint = all(x is True for x in (external.get('method_endpoint_accepted'), worker.get('method_endpoint_accepted'), worker.get('physical_witness_valid')))
        admitted = endpoint and helper.get('qp_candidate_admitted') is True and worker.get('qp_candidate_admitted') is True
        retained = Q(worker['objective_exact']) if endpoint else None
        candidate = Q(helper['candidate_bill_exact']) if admitted else None
        if retained is not None and (retained != Q(helper['true_bill_exact']) or retained > prior):
            raise ValueError('Accepted retained cost is inconsistent or worse than prior')
        report.update(complete=True, campaign_complete=master.get('complete'), campaign_passed=master.get('passed'),
            method_endpoint_accepted=endpoint, qp_candidate_admitted=admitted,
            qp_success=admitted and helper.get('qp_success') is True and worker.get('qp_success') is True,
            native_calls=helper['native_calls'], stats=helper['stats'], copy_contract=helper['copy_contract'],
            helper_failures=helper['failures'], worker_failures=worker['failures'], external_failures=external['failures'],
            prior_cost_exact=str(prior), retained_cost_exact=None if retained is None else str(retained),
            candidate_cost_exact=None if candidate is None else str(candidate),
            retained_saving_vs_prior_exact=None if retained is None else str(prior-retained),
            candidate_saving_vs_prior_exact=None if candidate is None else str(prior-candidate),
            old_v2=dict(qp_success=old['qp_success'], qp_candidate_admitted=old['qp_candidate_admitted'],
                native_status=old['stats']['Status'], raw_objective_telemetry=old['stats']['ObjVal'],
                retained_prior_cost_exact=old_receipt['objective_exact'] if old_receipt.get('method_endpoint_accepted') is True and old_receipt.get('physical_witness_valid') is True else None, failures=old['failures'],
                raw_value_is_not_an_admitted_physical_cost=True))
    except Exception as exc:
        report['failure'] = dict(type=type(exc).__name__, message=str(exc))
    report['readout'] = dict(cpu_s_before_publication=time.process_time()-CPU0, wall_s_before_publication=time.monotonic()-START,
        cpu_cap_s=15, wall_cap_s=20, own_external_meter_pending=True, final_package_totals_pending_external_postmeter=True)
    with output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps(dict(complete=report['complete'], qp_success=report.get('qp_success'), retained_cost=display(report.get('retained_cost_exact')))))
    return 0 if report['complete'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
