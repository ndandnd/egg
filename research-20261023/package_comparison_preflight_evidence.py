"""Preserve native captures losslessly; no solver or application imports."""
from pathlib import Path
import gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'research-20261023/comparison-native-preflight-v1'
out=base/'compressed-captures';out.mkdir(exist_ok=False)
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
rows=[]
for source in sorted((base/'runs').glob('*/capture-*.json')):
    target=out/(source.parent.name+'-'+source.name+'.gz')
    with source.open('rb') as raw,target.open('xb') as stream:
        with gzip.GzipFile(filename='',fileobj=stream,mode='wb',mtime=0,compresslevel=1) as zipped:
            shutil.copyfileobj(raw,zipped,1024*1024)
    digest=hashlib.sha256()
    with gzip.open(target,'rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    if digest.hexdigest()!=sha(source):raise ValueError('Lossless evidence verification failed')
    rows.append({'raw_path':str(source),'raw_sha256':sha(source),'raw_bytes':source.stat().st_size,
                 'gzip_path':str(target),'gzip_sha256':sha(target),'gzip_bytes':target.stat().st_size,
                 'lossless_hash_verified':True})
with (out/'manifest.json').open('x') as stream:
    stream.write(json.dumps({'policy':'lossless-native-capture-backup-v1','rows':rows,
                 'native_stdout_stderr':'local only, hash-indexed in supervisor receipt'},indent=2)+'\n')
print(json.dumps({'captures':len(rows),'raw_bytes':sum(x['raw_bytes'] for x in rows),
                  'gzip_bytes':sum(x['gzip_bytes'] for x in rows),'verified':True}))
