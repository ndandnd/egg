"""Read only three E11 archives in memory; emit JSON, never extract or execute members."""
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import statistics
import tarfile

ROOT = Path(__file__).resolve().parent
SPECS = (
    ('00-71', 'e8072c3ebbd02f519d17e4b1d9540a797721724d960c10a79cf9f2540d3587c1'),
    ('72-73', '79d53406bb2d2a0ee6495a98145ba0c1351d192ab5f665d571caee4ddcd376f9'),
    ('74-95', 'bc7d074d1c39784b2bca72cfcd21e661baf676efdf9e0f8f6ef34c2ad57a9991'),
)
ARMS = (('cold', None), ('cold4', None), ('learned4', .15), ('learned4', .30))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    archives, hashes = {}, []
    for tag, expected in SPECS:
        path = ROOT / f'e11-tasks-{tag}-20261002.tar.gz'
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        require(digest == expected, f'Archive hash mismatch: {path.name}')
        with tarfile.open(path) as archive:
            members = [member for member in archive.getmembers() if member.isfile()]
            names = [member.name for member in members]
            require(len(names) == len(set(names)), f'Duplicate archive members: {tag}')
            archives[tag] = {member.name: archive.extractfile(member).read() for member in members}
        hashes.append({'archive': path.name, 'sha256': digest})
    commands = archives['72-73']['cmds.txt'].decode().splitlines()
    require(len(commands) == 96, 'Expected 96 manifest rows')
    rows, tasks = {}, []
    for task in range(96):
        tag = '00-71' if task < 72 else '72-73' if task < 74 else '74-95'
        members = archives[tag]
        tokens = shlex.split(commands[task])
        fields = {tokens[i]: tokens[i + 1] for i in range(len(tokens) - 1) if tokens[i].startswith('--')}
        member = 'out/' + fields['--output'].split('/')[-1] + '/e3.json'
        result = json.loads(members[member])
        require(result['case'] == fields['--case'] and result['arm'] == fields['--arm']
                and result['grb_seed'] == int(fields['--grb-seed'])
                and result['keep'] == float(fields['--keep'])
                and result['tariff'] == 'day' and result['seconds'] == 60,
                f'Manifest/result mismatch: task {task}')
        key = (result['case'], result['arm'], result['keep'] if result['arm'] == 'learned4' else None,
               result['grb_seed'])
        require(key not in rows, f'Duplicate result key: {key}')
        rows[key] = result
        log = members[f'logs/egg-claude-e11-798833_{task}.out'].decode()
        commits = re.findall(r'commit=([a-f0-9]+)', log)
        require(bool(commits) and all(commit.startswith('711c3d7') for commit in commits),
                f'Source mismatch: task {task}')
        status = result.get('status')
        require(status in ('bounded', 'unresolved', None), f'Unexpected status: task {task}')
        bill = result.get('bill')
        require(bill is None or (isinstance(bill, (int, float)) and math.isfinite(bill)),
                f'Nonfinite or nonnumeric bill: task {task}')
        require((status == 'bounded') == (result.get('bill') is not None),
                f'Status/bill inconsistency: task {task}')
        require(status is not None or result.get('failure') is not None,
                f'Missing status without failure: task {task}')
        tasks.append({'task': task, 'key': key, 'status': status, 'bill': result.get('bill'),
                      'failure': result.get('failure'), 'source_commits': commits,
                      'result_total_seconds': result.get('total_seconds')})
    expected = {(f'scale:{case}:{size}', arm, keep, seed)
                for case in range(50000, 50004) for size in (60, 80)
                for arm, keep in ARMS for seed in (1, 2, 3)}
    require(set(rows) == expected, 'Incomplete or unexpected cohort keys')
    pairs = []
    for keep in (.15, .30):
        for reference in ('cold', 'cold4'):
            counts, finite = collections.Counter(), collections.Counter()
            for case in sorted({key[0] for key in rows}):
                for seed in (1, 2, 3):
                    a = rows[(case, 'learned4', keep, seed)].get('bill')
                    b = rows[(case, reference, None, seed)].get('bill')
                    if a is None and b is None:
                        counts['joint_failure'] += 1
                    elif a is None:
                        counts['loss'] += 1
                        counts['learned_only_failure'] += 1
                    elif b is None:
                        counts['win'] += 1
                        counts['reference_only_failure'] += 1
                    else:
                        outcome = 'win' if a < b * (1 - 1e-6) else 'loss' if a > b * (1 + 1e-6) else 'tie'
                        counts[outcome] += 1
                        finite[outcome] += 1
            pairs.append({'learned_keep': keep, 'reference': reference, 'expected_pairs': 24,
                          **{key: counts[key] for key in ('win', 'tie', 'loss', 'joint_failure',
                                                        'learned_only_failure', 'reference_only_failure')},
                          'both_finite_counts': {key: finite[key] for key in ('win', 'tie', 'loss')},
                          'both_finite_denominator': sum(finite.values())})
    summaries, arm_counts = [], []
    for arm, keep in ARMS:
        selected = [value for key, value in rows.items() if key[1:3] == (arm, keep)]
        arm_counts.append({'arm': arm, 'keep': keep, 'expected': 24,
                           'finite_bill': sum(value.get('bill') is not None for value in selected),
                           'null_bill': sum(value.get('bill') is None for value in selected),
                           'status_counts': dict(collections.Counter(value.get('status') for value in selected))})
    for case in sorted({key[0] for key in rows}):
        for arm, keep in ARMS:
            values = [rows[(case, arm, keep, seed)].get('bill') for seed in (1, 2, 3)]
            finite = [value for value in values if value is not None]
            summaries.append({'case': case, 'arm': arm, 'keep': keep, 'observed': 3,
                              'finite_bill': len(finite), 'min': min(finite) if finite else None,
                              'median': statistics.median(finite) if finite else None,
                              'max': max(finite) if finite else None})
    print(json.dumps({'archives': hashes, 'unique_keys': len(rows), 'tasks': tasks,
                      'paired_results': pairs, 'arm_counts': arm_counts,
                      'per_cell_arm_summary': summaries,
                      'reporting_convention': 'Retrospective: finite bill beats null bill; null/null is joint failure. '
                      'The original protocol did not specify this ranking; both-finite metrics are reported separately. '
                      'Relative 1e-6 finite-bill tie rule follows historical summarizer.',
                      'verification_scope': 'Project outputs only; no independent physical replay or solver execution.'}, indent=2))


if __name__ == '__main__':
    main()
