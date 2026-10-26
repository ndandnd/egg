"""Metered source-only AST closure and candidate preparation; no project imports."""
import time
START = time.monotonic()
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import threading

ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE = ROOT/'research-20261026/adjacent_nonlinear_reuse'
SIBLING = Path('/Users/nadan/Documents/projects/demandresponse/.codex-work/capacity-packed-20261001')
SRC = SIBLING/'src'
REVISION = '3a0ab6a8ab50e4af7d5a7be7688d5ffa1fbbf78c'
LOCAL = (
    'research-20261026/adjacent_nonlinear_reuse/run.py',
    'research-20261026/adjacent_nonlinear_reuse/prepare.py',
    'research-20261026/adjacent_nonlinear_reuse/worker.py',
    'research-20261026/adjacent_nonlinear_reuse/PROTOCOL.md',
    'research-20261026/adjacent_nonlinear_reuse/OWNER_NOTE.md',
    'research-20261026/adjacent_nonlinear_reuse/WORKER_NOTE.md',
    'research-20261026/adjacent_nonlinear_design/column_contract.py',
    'research-20261026/adjacent_nonlinear_design/bank_master.py',
    'research-20261026/adjacent_nonlinear_design/ORACLE_AND_TARGET_CONTRACT.md',
    'research-20261026/adjacent_nonlinear_design/ECONOMIC_COMPOSITION.md',
    'research-20261026/descriptor_wire_repair/descriptor.py',
    'research-20261026/adjacent_bridge_qualification/fixture.py',
    'research-20261026/adjacent_oracle_boundary/boundary.py',
    'src/egglab/__init__.py',
    'src/egglab/market.py',
)


def cpu():
    u = resource.getrusage(resource.RUSAGE_SELF)
    return u.ru_utime+u.ru_stime


def stop(signum, frame):
    raise TimeoutError('Preparation resource stop '+str(signum))


def check():
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform == 'darwin' else 1024)
    if cpu() >= 6 or time.monotonic()-START >= 15 or peak > 5*1024**3 or threading.active_count() != 1:
        raise TimeoutError('Preparation body6CPU/15wall exhausted')


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 20-(time.monotonic()-START)))
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    if (Path(__file__).resolve() != HERE/'prepare.py' or Path.cwd().resolve() != ROOT
            or len(args.source_revision) != 40
            or any(c not in '0123456789abcdef' for c in args.source_revision)):
        raise ValueError('Exact owner root and complete prospective source revision required')
    folder = HERE/'preparation01'; folder.mkdir(exist_ok=False)
    report = dict(receipt_complete=False, preparation_complete=False, failures=[], source_sha256={},
        source_revision=args.source_revision, sibling_source_revision=REVISION,
        phase_cpu_cap_s=10, phase_wall_cap_s=20, original_data_read=False,
        fixture_generation=False, sibling_imports=False, project_imports=False, native_calls=0,
        external_meter_pending=True, one_cached_read_per_source=True)
    # Exclusive placeholder persists even if final publication is interrupted.
    save(folder/'receipt.json', dict(receipt_complete=False, preparation_complete=False))
    cache = {}; total_bytes = 0; local_modules = {}; external = set(); unresolved_dynamic = []

    def read(path):
        nonlocal total_bytes
        path = Path(path)
        if path in cache:
            return cache[path]
        check(); before = path.stat()
        if (path.is_symlink() or path.resolve() != path or not path.is_file()
                or before.st_size > 2*1024**2 or total_bytes+before.st_size > 24*1024**2):
            raise ValueError('Source/control path or byte cap violated '+str(path))
        with path.open('rb') as stream:
            raw = stream.read(2*1024**2+1)
        after = path.stat()
        if (len(raw) != before.st_size or (before.st_ino,before.st_size,before.st_mtime_ns)
                != (after.st_ino,after.st_size,after.st_mtime_ns)):
            raise ValueError('Source/control changed during read '+str(path))
        total_bytes += len(raw); cache[path] = raw
        return raw

    def local_path(name):
        if not name or any(not part.isidentifier() for part in name.split('.')):
            return None
        stem = SRC.joinpath(*name.split('.'))
        for path in (stem.with_suffix('.py'), stem/'__init__.py'):
            if path.is_file():
                return path
        return None

    def add_module(name):
        path = local_path(name)
        if path is None:
            external.add(name)
            return
        # Package initializers are real dependencies too.
        parts = name.split('.')
        for i in range(1, len(parts)):
            prefix = '.'.join(parts[:i]); initial = local_path(prefix)
            if initial is not None and initial.name == '__init__.py':
                local_modules.setdefault(prefix, initial)
        local_modules.setdefault(name, path)
        if len(local_modules) > 192:
            raise ValueError('Static sibling dependency closure exceeds192modules')

    passed = False
    try:
        launch = json.loads(read(HERE/'LAUNCH.json'))
        if (launch.get('mode') != 'DRAFT' or launch.get('review_disposition') != 'PENDING'
                or launch.get('workdir') != str(ROOT)
                or launch.get('sibling_source_revision') != REVISION
                or launch.get('sibling_source_root') != str(SIBLING)
                or launch.get('source_closure', {}).get('roots') != ['run_capacity_terminal_cg']):
            raise ValueError('Source preparation needs reviewed DRAFT/PENDING with literal registered roots')
        report['draft_launch_sha256'] = hashlib.sha256(cache[HERE/'LAUNCH.json']).hexdigest()
        for relative in LOCAL:
            path = ROOT/relative
            report['source_sha256'][str(path)] = hashlib.sha256(read(path)).hexdigest()
        add_module('run_capacity_terminal_cg')
        visited = set()
        while set(local_modules)-visited:
            name = sorted(set(local_modules)-visited)[0]
            path = local_modules[name]; visited.add(name)
            raw = read(path)
            if str(path) not in report['source_sha256']:
                report['source_sha256'][str(path)] = hashlib.sha256(raw).hexdigest()
            tree = ast.parse(raw, filename=str(path))
            package = name if path.name == '__init__.py' else name.rpartition('.')[0]
            for node in ast.walk(tree):
                check()
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        add_module(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        parts = package.split('.') if package else []
                        if node.level > len(parts):
                            raise ValueError('Relative import escapes sibling package '+name)
                        base = '.'.join(parts[:len(parts)-node.level+1])
                        target = '.'.join(p for p in (base,node.module) if p)
                    else:
                        target = node.module or ''
                    add_module(target)
                    for alias in node.names:
                        child = target+'.'+alias.name
                        if alias.name != '*' and local_path(child) is not None:
                            add_module(child)
                elif isinstance(node, ast.Call) and (isinstance(node.func, ast.Name)
                        and node.func.id == '__import__' or isinstance(node.func, ast.Attribute)
                        and node.func.attr == 'import_module'):
                    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        add_module(node.args[0].value)
                    else:
                        unresolved_dynamic.append(dict(module=name,line=node.lineno))
        if unresolved_dynamic:
            raise ValueError('Unresolved dynamic imports require explicit narrow source decision; no automatic expansion')
        check()
        closure = dict(roots=['run_capacity_terminal_cg'], sibling_python_paths=sorted({str(p) for p in local_modules.values()}),
            modules={n:str(p) for n,p in sorted(local_modules.items())},
            nonlocal_import_names=sorted(external),
            scope='Static reachable local import statements, including conditional/function bodies; actual loaded subset checked by worker',
            native_installed_dependencies='Installed external packages/extensions are named, not hashed or runtime-qualified here',
            unresolved_dynamic_imports=unresolved_dynamic)
        candidate = dict(launch)
        candidate.update(mode='SOURCE_PINNED', review_disposition='PENDING', source_revision=args.source_revision,
            source_freeze_assumption='parent-approved-frozen-commit', source_sha256=report['source_sha256'],
            source_closure=closure,
            preparation_accounting=dict(external_accepted=False,charged_cpu_s=None,elapsed_s=None,
                purpose='Source-only10CPU20wall inside combined preflight60/total480; parent external reconciliation required'))
        save(HERE/'LAUNCH_FROZEN_CANDIDATE.json', candidate)
        report.update(preparation_complete=True, source_closure=closure,
            candidate_path=str(HERE/'LAUNCH_FROZEN_CANDIDATE.json'))
        passed = True
    except BaseException as exc:
        report['failures'].append(dict(type=type(exc).__name__,message=str(exc)))
    finally:
        report.update(receipt_complete=True,self_cpu_prepublication_s=cpu(),elapsed_prepublication_s=time.monotonic()-START,
            source_bytes_read=total_bytes, observed_self_peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*
                (1 if sys.platform == 'darwin' else 1024)),
            children_cpu_s=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+
                resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime, external_meter_pending=True)
        temporary = folder/'receipt.final.tmp'
        save(temporary, report); os.replace(temporary, folder/'receipt.json')
        print(json.dumps({k:report[k] for k in ('preparation_complete','failures','self_cpu_prepublication_s','elapsed_prepublication_s')}))
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
