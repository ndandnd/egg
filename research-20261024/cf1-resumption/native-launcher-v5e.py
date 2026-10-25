"""Unexecuted binding draft for the sole CF1 v5 case in fresh namespace v5e.

Failed v5d entry and launcher remain preserved. A passing source attempt08,
a separately successful v5e freeze and a prospectively metered invocation are
required before this draft may be used. No retry is provided.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'research-20261024/cf1-entry-repaired-v5e'
POLICY = 'cf1-entry-repaired-v5'


def main():
    if len(sys.argv) != 1:
        raise ValueError('Only the one frozen CF1 v5e binding command is allowed')
    if sys.executable != str(ROOT/'.venv-local/bin/python'):
        raise ValueError('Require the frozen local Python interpreter')
    # One metadata batch only; no independent source/fixture/library hash audit.
    paths = {'lock_path': BASE/'lock.json',
        'freeze_receipt_path': BASE/'freeze-attempt01/result.json',
        'accounting_path': BASE/'freeze-accounting.json'}
    raw = {key: path.read_bytes() for key, path in paths.items()}
    metadata = {key: json.loads(value) for key, value in raw.items()}
    digests = {key: hashlib.sha256(value).hexdigest() for key, value in raw.items()}
    lock, receipt, account = (metadata[key] for key in paths)
    if (lock.get('policy') != POLICY or receipt.get('policy') != POLICY
            or account.get('policy') != POLICY or receipt.get('passed') is not True
            or account.get('freeze_passed') is not True
            or account.get('metadata_freeze') is not True
            or account.get('native_dispatch') is not False
            or account.get('accounting_observations_complete') is not True
            or account.get('owned_groups_absent_and_reaped') is not True):
        raise ValueError('Require actual successful closed v5e freeze metadata')
    # Catch the diagnosed v5b parent header mismatch before any owner Popen.
    if (account.get('hard_total_ceiling_s'), account.get('dispatch_stop_s'),
            account.get('shutdown_reserve_s')) != (3000., 2820., 180.):
        raise ValueError('Require exact launch-accounting total/dispatch/shutdown headers')
    if (account['evidence_hashes'].get(str(paths['lock_path'])) != digests['lock_path']
            or account['evidence_hashes'].get(str(paths['freeze_receipt_path']))
                != digests['freeze_receipt_path']):
        raise ValueError('Freeze account does not bind the independently read roots')
    roots = {key: str(path) for key, path in paths.items()}
    roots.update(expected_lock_sha256=digests['lock_path'],
        expected_freeze_receipt_sha256=digests['freeze_receipt_path'],
        expected_accounting_sha256=digests['accounting_path'],
        expected_cumulative_charge_s=account['charged_cpu_s'], expected_policy=POLICY)
    command = [sys.executable, '-m', 'experiments.cf1_entry_repaired', 'run',
        '--lock', roots['lock_path'], '--output', str(BASE/'runs'),
        '--freeze-receipt', roots['freeze_receipt_path'],
        '--accounting', roots['accounting_path'],
        '--expected-lock-sha256', roots['expected_lock_sha256'],
        '--expected-freeze-receipt-sha256', roots['expected_freeze_receipt_sha256'],
        '--expected-accounting-sha256', roots['expected_accounting_sha256'],
        '--expected-cumulative-charge-s', repr(roots['expected_cumulative_charge_s'])]
    os.chdir(ROOT)
    os.environ['PYTHONPATH'] = str(ROOT/'src')
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT/'src'))
    from experiments import cf1_entry_repaired as v5
    task, = v5.task_matrix()
    if lock.get('tasks') != [task]:
        raise ValueError('Frozen lock must contain exactly the inspected v5 task')
    if ((v5.PACKAGE_START, v5.PACKAGE_LIMIT, v5.PACKAGE_CAP)
            != (2426.723449631016, 350., 2776.723449631016)):
        raise ValueError('Qualified package bindings changed')
    if (v5.ENTRY_PRECHARGE_S, v5.entry_owner.ENTRY_S) != (20., 20.):
        raise ValueError('Require matching twenty-second whole-entry provision')
    if any((BASE/name).exists() for name in ('runs', 'entry-owner.json', 'entry-owner-attempt01')):
        raise FileExistsError('Existing or partial owned native namespace')
    with v5.revision5():
        q = v5.adapter.q
        if (q.CEILING, q.DISPATCH_STOP, q.SHUTDOWN_RESERVE) != (3000., 2820., 180.):
            raise ValueError('Qualified global limits changed')
        for key in q.THREAD_KEYS:
            os.environ[key] = '1'
        # The unchanged controller preparation performs the qualified closure
        # checks; these retained values come from this independent parent batch.
        q.write_new(BASE/'native-launch-bindings.json', {
            'policy': POLICY, 'command': command, 'roots': roots, 'task': task,
            'output': str(BASE/'runs'), 'automatic_retry': False,
            'entry_precharge_s': 20.,
            'external_whole_launcher_metering_required': True})
        owner = v5.entry_owner.OwnerSupervisor(directory=BASE/'entry-owner-attempt01',
            roots=roots, task=task, output=BASE/'runs', policy=POLICY)
        result = owner.run(command)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
