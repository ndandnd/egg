"""Read-only manuscript reconciliation of archived public flat pricing evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
paths = {
    'nonlinear_freeze': 'result/sistig_nonlinear/20260927-attempt2/frozen.json',
    'flat_input': 'result/sistig_pricing/20260927-grb-job557543-attempt1/depot_15_flat/input.json',
    'planner_events': 'result/sistig_nonlinear/20260927-attempt2/planner/events.jsonl',
}
data = {key: json.loads((ROOT / name).read_text()) for key, name in paths.items() if key != 'planner_events'}
records = {}
with (ROOT / paths['planner_events']).open() as stream:
    for line in stream:
        row = json.loads(line)
        if row.get('round') == 0 and row.get('event') in ('native_start', 'native_status', 'objective_reconstruction'):
            records[row['event']] = row
n, f = data['nonlinear_freeze'], data['flat_input']
assert n['case'] == f['case'] and n['case_identity'] == f['case_identity']
assert f['objective'] == 'pricing'
assert len(f['prices']) == len(n['market']['a']) == 30
assert f['prices'] == n['market']['a'] == [0.2] * 30
assert records['native_start']['tangents'] == [[[p, 0.0]] for p in f['prices']]
stats = records['native_status']['stats']
assert stats['status'] == 'OPTIMAL'
shared = set(n['source_hashes']) & set(f['source_hashes'])
report = {
    'case_equal': True, 'case_identity': n['case_identity'],
    'flat_objective_equal_after_epigraph_elimination': True,
    'prices': {'periods': 30, 'constant': 0.2},
    'native_status': {k: stats[k] for k in ('status', 'incumbent', 'lower_bound', 'wall_s', 'seconds_cap')},
    'round0_objective_reconstruction': records['objective_reconstruction'],
    'changed_shared_source_paths': sorted(k for k in shared if n['source_hashes'][k] != f['source_hashes'][k]),
    'input_sha256': {k: hashlib.sha256((ROOT / v).read_bytes()).hexdigest() for k, v in paths.items()},
    'scope': 'Existing conditional native evidence only; no solver call, exact ideal optimum, or experiment reclassification.',
}
print(json.dumps(report, indent=2, sort_keys=True))
