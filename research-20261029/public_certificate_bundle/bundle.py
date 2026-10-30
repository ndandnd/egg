"""Prospective local-only bundle construction; no work happens on import."""
import hashlib
import json
import re
from pathlib import Path
import subprocess

SEM='3278d50f8323618bd36809b1bbb1a0da081e23ff'
TREE='6a171357b65254b52cade63ed95dcce798485f36'
CASE='253c1e29295e766b3889fc8f5c28d9808e00b3d6'
PRICE='f5ec2aa5770188d173af7297620a5fcea99fef9a'
MODEL='research-20261029/public_support_resolution/'
PINS={
 'checkers/physical.py':(SEM,MODEL+'independent_verify.py'),
 'checkers/semantic.py':(SEM,MODEL+'exact_dual.py'),
 'checkers/tree.py':(TREE,'research-20261029/public_support_tree/checker.py'),
 'evidence/case.json':(CASE,MODEL+'attempt01/case_descriptor.json'),
 'evidence/physical.json.gz':('0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee','research-20261029/public_rational_recovery/attempt01/PUBLIC_PRIMAL.json.gz'),
 'evidence/response.json.gz':(PRICE,'research-20261029/public_price_witness/attempt01/EXACT_PRIMAL.json.gz'),
 'evidence/mixture.json.gz':(PRICE,'research-20261029/public_price_witness/attempt01/MIXTURE.json.gz'),
 'evidence/tree.json.gz':('ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9','research-20261029/public_support_tree/attempt01/PUBLIC_TREE.json.gz'),
 'evidence/refinement.json.gz':('d8e22ffd3753fced3ec825c68714fd549d914230','research-20261029/public_physical_refinement/attempt01/PUBLIC_REFINEMENT.json.gz')}
CASE_TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'


def build(repo_root,out_dir,source_revision,source_buffers=None):
    """Future metered admission/export only; never verifies or runs a solver."""
    if not isinstance(source_revision,str) or re.fullmatch('[0-9a-f]{40}',source_revision) is None:
        raise ValueError('immutable full source revision required')
    repo=Path(repo_root).resolve();out=Path(out_dir).resolve()
    if out.exists():raise ValueError('fresh bundle directory required')
    pins=dict(PINS);pins['verify.py']=(source_revision,'research-20261029/public_certificate_bundle/verify.py')
    cache={};manifest={}
    for destination,(revision,path) in pins.items():
        raw=(source_buffers or {}).get(destination)
        if raw is None:raw=(repo/path).read_bytes()
        frozen=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=repo,timeout=5)
        if raw!=frozen:raise ValueError('pinned buffer differs: '+path)
        cache[destination]=raw
        manifest[destination]=dict(revision=revision,path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    readme=('LOCAL AUTHOR REVIEW BUNDLE; REDISTRIBUTION/LICENSE STATUS UNRESOLVED.\n'
            'No license is assigned and no publication is authorized.\n'
            'Requirements: qualified CPython with stdlib; no Git, network, solver or packages for verification.\n'
            'Run: python3 -I -S -B verify.py --manifest-sha256 TRUSTED_DIGEST --output verification.json\n'
            'Take TRUSTED_DIGEST from the separate admitted builder receipt, not from an untrusted bundle.\n'
            'PASS certifies retained evidence for the finite declared-movement model only.\n'
            'Author-written/author-run verification is not external replication.\n').encode()
    cache['README.md']=readme;manifest['README.md']=dict(bytes=len(readme),sha256=hashlib.sha256(readme).hexdigest(),generated=True)
    record=dict(schema='public-sign-bundle-v1',case_token=CASE_TOKEN,purpose='local author review',
                redistribution_status='UNRESOLVED',files=manifest)
    raw=json.dumps(record,sort_keys=True,indent=2).encode()+b'\n'
    out.mkdir(parents=True,exist_ok=False)
    for name,value in cache.items():
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(value)
    with (out/'MANIFEST.json').open('xb') as stream:stream.write(raw)
    return dict(status='BUILT_LOCAL_REVIEW_ONLY',manifest_sha256=hashlib.sha256(raw).hexdigest(),
                manifest=record,redistribution_status='UNRESOLVED',source_revision=source_revision,
                native_calls=0,verification_performed=False)
