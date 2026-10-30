"""One whitelisted TRAIN registry metadata read; never follow any table path."""
import json
from pathlib import Path
import resource
import signal
import time

START = time.monotonic()
BASE = Path(__file__).resolve().parent
PATH = Path('/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/pool_manifest.json')
IDS = {'base_id', 'group', 'group_id', 'group_key', 'shared_timetable_group',
       'shared_timetable_group_id', 'timetable_group', 'case_key', 'case_keys',
       'case_id', 'case_ids', 'generator', 'generator_version', 'variants',
       'variant_keys', 'variant_aliases', 'aliases'}

def main():
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    def expired(signum, frame):
        raise TimeoutError('TRAIN metadata read allowance20wall reached')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 19)
    out = dict(complete=False, path=str(PATH), schema_only=True, table_paths_followed=False,
               case_generation=False, hashes=0, failure=None, records=[])
    try:
        with PATH.open('rb') as stream:
            raw = stream.read(8*1024*1024+1)
        if len(raw) > 8*1024*1024:
            raise ValueError('Whitelisted metadata exceeds8MiB; no broader read')
        doc = json.loads(raw)
        out['root_keys'] = sorted(doc)
        def walk(value, address):
            if isinstance(value, dict):
                if 'base_id' in value:
                    fields = {k: v for k, v in value.items() if k in IDS
                              and (v is None or isinstance(v, (str, int, float, bool))
                                   or isinstance(v, list) and all(isinstance(x, (str, int)) for x in v))}
                    out['records'].append(dict(address=address, keys=sorted(value), identifiers=fields))
                for key, child in value.items():
                    if isinstance(child, (dict, list)):
                        walk(child, address+'/'+str(key))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    if isinstance(child, (dict, list)):
                        walk(child, address+'/'+str(index))
        walk(doc, '')
        out['complete'] = True
    except Exception as exc:
        out['failure'] = dict(type=type(exc).__name__, message=str(exc))
    out.update(elapsed_before_publication_s=time.monotonic()-START,
               cpu_before_publication_s=time.process_time())
    with (BASE/'train-registry-schema.json').open('x') as stream:
        json.dump(out, stream, indent=2); stream.write('\n')
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps(dict(complete=out['complete'], failure=out['failure'], root_keys=out.get('root_keys'),
        records=len(out['records']), first=out['records'][:1], last=out['records'][-1:])))
    return 0 if out['complete'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
