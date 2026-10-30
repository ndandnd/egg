"""Compact byte-preserving review archive. Does not run or alter experiments."""
from pathlib import Path
import hashlib,json,time,zipfile
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research-20261017'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    started=time.process_time();lock=json.loads((BASE/'local-assets-v3.json').read_text())
    files={}
    def add(p,name=None):
        p=p.resolve();key=name or str(p.relative_to(ROOT))
        if key in files and files[key]!=p:raise ValueError('Archive collision '+key)
        files[key]=p
    names=['REVIEWER_HANDOFF_20261017.md','CONTINUATION.md','INDEPENDENT_SCREEN_CHECK.md','FINAL_REPLAY_VERIFICATION.json','FINAL_REPLAY_VERIFICATION.md','VERIFY_REVIEW_EVIDENCE.py','LOCAL_CAMPAIGN_PROTOCOL.md','LOCAL_CAMPAIGN_MANIFEST_V3.json','LOCAL_MONITORING.md','local-assets-v3.json','ANALYSIS_RULES.md','analyze_local_campaign.py','STOP_RECEIPT_20261017.json','RECOVERY_IMPLEMENTATION_CONTRACT.md','GOOGLE_DOC_REVIEW_CHECKPOINT_20261017.md','BUILD_REVIEW_BUNDLE.py','CLOSEOUT_ACCOUNTING.json']
    for name in names:add(BASE/name)
    for folder in ['screen-analysis-v3-final','screen-analysis-v3/figures','recovery-prototype','classical-training/attempt1/catboost']:
        for p in sorted((BASE/folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:add(p)
    add(BASE/'classical-training/RESULTS.md');add(BASE/'screen-analysis-v3/ANALYSIS_ATTEMPT_FAILURE.json')
    keep={'attempt.json','result.json','supervisor.json','completion.json','plan.json','replay.json'}
    for p in sorted((BASE/'local-screen-v3').rglob('*')):
        if p.is_file() and (p.name in keep or p.name in {'campaign.json','ledger.jsonl'}):add(p)
    for path,expected in lock['sources'].items():
        p=Path(path);assert sha(p)==expected;add(p)
    models={}
    for path,expected in lock['assets'].items():
        p=Path(path);assert sha(p)==expected
        name='review-models/'+('v8/task00/inner_progress/' if '/claude-local/v8/' in path else 'catboost/')+p.name
        add(p,name);models[path]={'archive_path':name,'sha256':expected}
    manifest={'purpose':'independent review of complete synthetic-development screen; no final-test/optimality claim','original_project_root':str(ROOT),'read_first':'research-20261017/REVIEWER_HANDOFF_20261017.md','portable_notes':'Original lock/audit uses absolute local paths. Relocate paths with unchanged byte hashes for reproduction; all physical plans and generated case keys are included. No license/runtime is included.','raw_artifacts':'Native variable traces and stdout/stderr remain local, identified in screen-analysis-v3-final/artifact_hashes.json; no raw logs are in this archive.','model_path_map':models,'files':{name:{'bytes':p.stat().st_size,'sha256':sha(p)} for name,p in sorted(files.items())}}
    manifest_path=BASE/'REVIEW_BUNDLE_MANIFEST_20261017.json'
    with manifest_path.open('x') as f:json.dump(manifest,f,indent=2);f.write('\n')
    archive=BASE/'REVIEW_BUNDLE_20261017.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(manifest_path,'BUNDLE_MANIFEST.json')
        for name,p in sorted(files.items()):z.write(p,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,item in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==item['sha256']
    receipt={'archive':archive.name,'sha256':sha(archive),'bytes':archive.stat().st_size,'payload_file_count':len(files),'roundtrip_crc_and_sha256_verified':True,'build_verify_cpu_s':time.process_time()-started}
    (BASE/'REVIEW_BUNDLE_RECEIPT_20261017.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
if __name__=='__main__':main()
