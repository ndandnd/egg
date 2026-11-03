"""Freeze ID-based pilot cohort from the already completed derived receipt."""
import hashlib
import json
from pathlib import Path
import resource
import signal

resource.setrlimit(resource.RLIMIT_CPU, (25, 30))
signal.signal(signal.SIGALRM, signal.SIG_DFL)
signal.setitimer(signal.ITIMER_REAL, 60)
HERE = Path(__file__).resolve().parent
SOURCE_RECEIPT = HERE.parent/'catalog_coherence/attempt01/receipt.json'
output = HERE/'COHORT.json'
with output.open('x') as stream:
    pins = {}
    for path in (Path(__file__).resolve(), HERE/'COHORT_SELECTION_PROTOCOL.md', HERE/'COHORT_SELECTION_LAUNCH.json', SOURCE_RECEIPT):
        if path.stat().st_size > 8*1024*1024:
            raise ValueError('Selection input exceeds8MiB')
        raw = path.read_bytes()
        pins[str(path)] = hashlib.sha256(raw).hexdigest()
        if path == SOURCE_RECEIPT:
            receipt = json.loads(raw)
    if not (receipt['receipt_complete'] and receipt['checks_passed'] and receipt['catalog_report_complete']):
        raise ValueError('Requires the completed coherent-catalog receipt')
    rows = receipt['groups']
    if len(rows) != 80 or len({r['group'] for r in rows}) != 80:
        raise ValueError('Expected80fixedFITgroups')
    def services(base):
        if type(base) is not int or not 10000 <= base < 10128:
            raise ValueError('Unrecognized declaredTRAINbase')
        j = (7*(base-10000)) % 54
        return 20 if (j//3) % 2 == 0 else 28
    selected = []
    for size in (20, 28):
        for stratum, count in (('different_membership', 3), ('same_membership', 1)):
            bucket = sorted((r for r in rows if r['expected_pair'] and r['membership_stratum'] == stratum
                and services(r['base_id']) == size), key=lambda r: r['base_id'])
            if len(bucket) < count:
                raise ValueError('Insufficient predeclared size/membership stratum; no substitution')
            selected.extend((row, size) for row in bucket[:count])
    # IDs are fixed above without consulting any cost magnitude. Only now copy
    # already admitted baseline scalars for the selected groups; no plans/rows.
    groups, tasks = [], []
    for group_index, (row, size) in enumerate(selected):
        groups.append(dict(group=row['group'], base_id=row['base_id'], services=size,
            membership_stratum=row['membership_stratum'], Ebar=row['coherence']['Ebar'],
            baseline={route: {target: row['witnesses'][route]['markets'][target]['F']
                for target in ('source0', 'source1')} for route in ('source0', 'source1')}))
        cells = [('source0', 'source0'), ('source0', 'source1'), ('source1', 'source0'), ('source1', 'source1')]
        offset = group_index % 4
        cells = cells[offset:]+cells[:offset]
        if (group_index//4) % 2:
            cells.reverse()
        for route, target in cells:
            index = len(tasks)+1
            tasks.append(dict(index=index, task_id=f'T{index:03d}-g{row["base_id"]}-r{route}-t{target}-s17',
                group=row['group'], base_id=row['base_id'], services=size,
                route_source=route, target_source=target))
    result = dict(cohort_complete=True, selection_rule='3different+1same per20/28; ascendingbaseID, costs unused',
        assignment_formula='j=(7*(base_id-10000))%54; services=20 if(j//3)%2==0 else28',
        selection_cost_fields_consulted=False, baseline_copy_after_ID_selection=True,
        source_receipt_sha256=pins[str(SOURCE_RECEIPT)], input_sha256=pins,
        groups=groups, tasks=tasks, intended_FIT_groups=80, original_complete_pairs=79,
        selected_groups=8, selected_cells=32, numerical_QP_outcomes_observed=False,
        output_is_launch_manifest=False)
    json.dump(result, stream, indent=2, allow_nan=False)
    stream.write('\n')
signal.setitimer(signal.ITIMER_REAL, 0)
