"""Lossless, exclusive per-task archive of the completed v7 attempt."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'result/physical_learning/20260930-route-proposal-train-v7'
OUT = ROOT / 'result/physical_learning/20260930-route-proposal-train-v7-backup'
MANIFEST = ROOT / 'research-20260930/learning-campaign/RESULT_MANIFEST_ROUTE_PROPOSAL_V7.json'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def main():
    paths = sorted(p for p in RAW.rglob('*') if p.is_file())
    if not paths or any(p.is_symlink() for p in RAW.rglob('*')):
        raise ValueError('Missing raw files or unexpected symlink')
    if OUT.exists() or MANIFEST.exists():
        raise ValueError('Exclusive archive already exists; inspect rather than overwrite')
    groups = {}
    for path in paths:
        relative = path.relative_to(RAW)
        key = relative.parts[0] if len(relative.parts) > 1 else 'metadata'
        groups.setdefault(key, []).append(path)
    if set(groups) != {'metadata', *(f'task{i:02d}' for i in range(16))}:
        raise ValueError('Unexpected or missing task groups')
    OUT.mkdir()
    files, archives, verified = {}, [], set()
    for group, members in sorted(groups.items()):
        archive = OUT / (group + '.tar.gz')
        with archive.open('xb') as stream:
            with gzip.GzipFile(filename='', fileobj=stream, mode='wb', mtime=0) as gz:
                with tarfile.open(fileobj=gz, mode='w') as tar:
                    for path in members:
                        value = path.read_bytes()
                        name = str(path.relative_to(ROOT))
                        info = tarfile.TarInfo(name)
                        info.size, info.mode, info.mtime = len(value), 0o600, 0
                        tar.addfile(info, io.BytesIO(value))
                        files[name] = {'bytes': len(value), 'sha256': sha(value),
                                       'archive': str(archive.relative_to(ROOT))}
        with tarfile.open(archive, 'r:gz') as tar:
            for member in tar:
                if not member.isfile() or member.name in verified or member.name not in files:
                    raise ValueError('Unexpected or duplicate archive member')
                value = tar.extractfile(member).read()
                expected = files[member.name]
                if len(value) != expected['bytes'] or sha(value) != expected['sha256']:
                    raise ValueError('Archive byte verification failed')
                verified.add(member.name)
        data = archive.read_bytes()
        archives.append({'path': str(archive.relative_to(ROOT)), 'bytes': len(data),
                         'sha256': sha(data), 'member_count': len(members)})
    if verified != set(files) or len(files) != len(paths):
        raise ValueError('Archive coverage differs from full raw attempt')
    result = {'array_job_id': 728823, 'raw_root': str(RAW.relative_to(ROOT)),
              'file_count': len(files), 'raw_bytes': sum(v['bytes'] for v in files.values()),
              'archive_bytes': sum(v['bytes'] for v in archives),
              'all_archive_members_byte_verified': True, 'archives': archives, 'files': files,
              'scope': 'Complete raw scientific attempt, including all failures and wrapper receipts. External Slurm logs have a separate receipt.'}
    with MANIFEST.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('files', 'archives')}))


if __name__ == '__main__':
    main()
