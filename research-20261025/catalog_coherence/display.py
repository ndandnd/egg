"""Once-only decimal formatting of already computed aggregate Fractions."""
import json
from fractions import Fraction
from pathlib import Path
import resource
import signal

resource.setrlimit(resource.RLIMIT_CPU, (8, 10))
signal.signal(signal.SIGALRM, signal.SIG_DFL)
signal.setitimer(signal.ITIMER_REAL, 20)
root = Path(__file__).resolve().parent
target = root/'DISPLAY.json'
with target.open('x') as stream:
    source = root/'attempt01/receipt.json'
    if source.stat().st_size > 8*1024*1024:
        raise ValueError('Completed receipt exceeds formatting bound')
    r = json.loads(source.read_text())
    if not r['receipt_complete'] or not r['checks_passed']:
        raise ValueError('Formatting requires the complete admitted receipt')
    result = dict(display_only=True, source='attempt01/receipt.json',
        policy='Existing aggregate Fraction fields converted to float and rounded9 decimals; no new metrics, signs or gates')
    for name, group in [('full', r['aggregate']['full'])]+list(r['aggregate']['strata'].items()):
        result[name] = {key: group[key] for key in ('planned', 'valid_pairs', 'missing_or_invalid', 'sign_counts', 'dominated_P0', 'dominated_P1')}
        result[name]['distributions'] = {}
        for metric in ('D0', 'D1', 'R0_raw', 'R1_raw'):
            fields = group['exact_raw_distributions'][metric]
            result[name]['distributions'][metric] = {key: fields[key] for key in ('planned', 'defined', 'missing')}
            for key in ('mean_over_admitted_groups', 'complete_planned_mean', 'median', 'minimum', 'maximum'):
                value = fields[key]
                result[name]['distributions'][metric][key] = None if value is None else round(float(Fraction(value)), 9)
    json.dump(result, stream, indent=2, allow_nan=False)
    stream.write('\n')
signal.setitimer(signal.ITIMER_REAL, 0)
