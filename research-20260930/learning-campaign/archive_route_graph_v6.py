"""Lossless, hash-verified Git backup of the completed v6 graph artifacts.

Raw files remain locally and on Unicorn. This only creates deterministic gzip
archives and verifies every archived byte against the collected originals.
"""
import gzip
import hashlib
import json
import re
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'result/physical_learning/20260930-route-model128-graph-v6'
BACKUP = ROOT / 'result/physical_learning/20260930-route-model128-graph-v6-backup'
MANIFEST = ROOT / 'research-20260930/learning-campaign/RESULT_MANIFEST_ROUTE_GRAPH_V6.json'
TASKS = range(12)


def digest(handle):
    h = hashlib.sha256()
    while block := handle.read(1024 * 1024):
        h.update(block)
    return h.hexdigest()


def main():
    BACKUP.mkdir(exist_ok=True)
    files = sorted(p for p in RAW.rglob('*') if p.is_file())
    records = {}
    for p in files:
        with p.open('rb') as handle:
            records[str(p.relative_to(ROOT))] = {'bytes': p.stat().st_size, 'sha256': digest(handle)}
    archive_rows = []
    assigned = set()
    buckets = {}
    for path in files:
        top = path.relative_to(RAW).parts[0]
        match = re.match(r'task(\d+)(?:\.|$)', top)
        if match is None or int(match[1]) not in TASKS:
            raise ValueError(f'Unexpected artifact path: {path}')
        arm = next((arm for arm in ('mean_message', 'graph_attention') if path.name.startswith(arm)), 'metadata')
        buckets.setdefault((int(match[1]), arm), []).append(path)
    for (task, arm), members in sorted(buckets.items()):
        prefix = f'task{task:02d}_{arm}'
        target = BACKUP / f'{prefix}.tar.gz'
        if target.exists():
            raise FileExistsError(target)
        with target.open('xb') as stream, gzip.GzipFile(filename='', fileobj=stream, mode='wb', compresslevel=6, mtime=0) as zipped, tarfile.open(fileobj=zipped, mode='w|') as archive:
            for p in members:
                name = str(p.relative_to(ROOT))
                info = archive.gettarinfo(str(p), arcname=name)
                info.uid = info.gid = 0
                info.uname = info.gname = ''
                info.mtime = 0
                with p.open('rb') as handle:
                    archive.addfile(info, handle)
                assigned.add(name)
        verified = []
        with tarfile.open(target, mode='r|gz') as archive:
            for member in archive:
                if not member.isfile():
                    raise ValueError(f'Unexpected non-file archive member: {member.name}')
                handle = archive.extractfile(member)
                if handle is None:
                    raise ValueError(f'Unreadable archive member: {member.name}')
                if {'bytes': member.size, 'sha256': digest(handle)} != records[member.name]:
                    raise ValueError(f'Archive member differs from raw file: {member.name}')
                verified.append(member.name)
        if set(verified) != {str(p.relative_to(ROOT)) for p in members} or len(verified) != len(members):
            raise ValueError(f'Archive member coverage mismatch: {target}')
        with target.open('rb') as handle:
            archive_rows.append({'path': str(target.relative_to(ROOT)), 'bytes': target.stat().st_size, 'sha256': digest(handle), 'members': verified, 'all_member_hashes_verified': True})
        print(json.dumps({'task': task, 'arm': arm, 'archive_bytes': target.stat().st_size, 'members': len(verified)}), flush=True)
    if assigned != set(records):
        raise ValueError('Some raw files were not assigned to a task archive')
    payload = {'raw_root': str(RAW.relative_to(ROOT)), 'complete_tasks': list(TASKS), 'raw_count': len(records), 'raw_bytes': sum(r['bytes'] for r in records.values()), 'files': [{'path': name, **r} for name, r in records.items()], 'archives': archive_rows, 'archive_bytes': sum(r['bytes'] for r in archive_rows), 'all_archived_bytes_verified_against_raw': True, 'restore': 'From the repository root, run tar -xzf for each listed archive. Archives contain repository-relative raw paths. Verify extracted sizes and SHA256 against this manifest.', 'raw_preserved_local_and_remote': True, 'remote_checkout': '/home/nc437/egg-route-graph-20260930-v6'}
    MANIFEST.write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps({k: payload[k] for k in ('raw_count', 'raw_bytes', 'archive_bytes')}))


if __name__ == '__main__':
    main()
