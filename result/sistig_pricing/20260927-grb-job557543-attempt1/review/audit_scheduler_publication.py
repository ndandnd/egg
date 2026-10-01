#!/usr/bin/env python3
"""Read-only scheduler and sensitive whole-file publication checks.
Never emit stdout contents or a license/token-server value.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

COMMIT='282e00b80b6fd9457006429b089269b2a9e2be92'
TAR_SHA='eda8c161372c4f0c774036b217fed56c072d4749f1865329e9ee314eec321ef5'
MANIFEST_SHA='826e79867437b5d1f464e3f54a0f204bb18a8541470e06a2344345881b0b1d01'

def need(v,m):
    if not v:raise AssertionError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())

def audit(transfer,tar):
    attempt=transfer/'result/sistig_pricing/20260927-grb-job557543-attempt1'
    scheduler=transfer/'public-pricing-submission-20260927'
    need(sha(tar.read_bytes())==TAR_SHA,'full completed transfer archive hash')
    need(sha((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'raw manifest hash')
    manifest=read(attempt/'MANIFEST.json');need(len(manifest['files'])==17,'all17 raw artifacts')
    original={}
    for name,e in manifest['files'].items():
        b=(attempt/name).read_bytes();need(len(b)==e['bytes'] and sha(b)==e['sha256'],'raw file '+name);original[name]=e
    initial=(scheduler/'SCONTROL.txt').read_text();fields=dict(re.findall(r'([\w/]+)=(\S+)',initial))
    expected={'JobId':'557543','Partition':'default_partition','NumCPUs':'1','NumNodes':'1',
        'MinMemoryNode':'8G','TimeLimit':'00:12:00','ExcNodeList':'scaglione-compute-01','Requeue':'0'}
    need(all(fields.get(k)==v for k,v in expected.items()),'initial allocation resource policy')
    need(fields['Command'].endswith('/src/cluster/sistig_pricing_pilot.sbatch') and fields['Command'].startswith(fields['WorkDir']+'/'),'isolated checkout wrapper')
    need(COMMIT in (scheduler/'INTENT.txt').read_text() and '557543' in (scheduler/'SUBMITTED.txt').read_text(),'submission intent/job link')
    rows=[line.split('|') for line in (scheduler/'SACCT_COMPLETED.txt').read_text().splitlines() if line]
    need([r[0] for r in rows]==['557543','557543.batch','557543.extern'],'one job and its batch/extern records')
    need(all(len(r)==7 and r[2]=='COMPLETED' and r[3]=='0:0' and r[6]=='snavely-cpu-16' for r in rows),'completed exits and allowed execution node')
    need(rows[0][4]==rows[1][4]=='00:06:35' and rows[2][4]=='00:06:36','saved job/step elapsed times')
    need(rows[1][5]=='397140K','actual MaxRSS receipt')
    need('expired' in (scheduler/'SCONTROL_COMPLETED_UNAVAILABLE.txt').read_text(),'missing post-completion scontrol explained explicitly')
    supervisor=read(attempt/'supervisor_receipt.json')
    need(supervisor['returncode']==0 and supervisor['timeout_exit'] is False and supervisor['elapsed_whole_seconds']==375,
        'successful preserved outer receipt')
    need(supervisor['outer_cap_s']==560 and supervisor['kill_grace_s']==10,'outer timeout policy')
    frozen=read(attempt/'frozen.json');summary=read(attempt/'summary.json')
    need(frozen['freeze_label']==COMMIT and summary['all_pass'] and summary['source_hashes_unchanged'],'scientific run completion')
    env=frozen['environment'];runtimes=[];omissions=[]
    for name in ('depot_15_flat','depot_16_flat'):
        package=read(attempt/name/'result.json');need(package['environment']==env,'worker/freeze Python/package environment equality')
        launch=read(attempt/name/'launch.json')
        need(launch['hard_timeout_s']==255 and launch['command'][0]==env['executable'],'worker runtime/external cap')
        command=launch['command'];out=command[command.index('--output')+1];ff=command[command.index('--frozen')+1]
        need(out.startswith(fields['WorkDir']+'/') and ff.startswith(fields['WorkDir']+'/'),'worker paths under isolated checkout')
        need(out.endswith('/'+name) and ff.endswith('/frozen.json'),'worker scientific input/output ownership')
        need(0<package['elapsed_s']<=240,'scientific routine budget')
        runtimes.append({'cell':name,'routine_elapsed_s':package['elapsed_s'],'hard_child_cap_s':255})
        relative=name+'/stdout.txt';b=(attempt/relative).read_bytes();s=b.decode()
        license_label=bool(re.search(r'license\s*(?:id|number)',s,re.I));token_label=bool(re.search(r'token\s*server|tokenserver',s,re.I))
        need(license_label and token_label,'sensitive labels verified in whole omitted stdout')
        omissions.append({'relative_path':relative,**original[relative],
            'reason':'Whole solver stdout contains license identifier and token-server configuration; full original retained locally',
            'sensitive_content_verified':True})
    scheduler_hashes={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in scheduler.iterdir() if p.is_file()}
    outer_hashes={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in [transfer/'egg-sistig-pilot-557543.out',transfer/'egg-sistig-pilot-557543.err']}
    return {'audit_status':'PASS scheduler, runtime and publication-omission eligibility',
        'source_commit':COMMIT,'job_id':557543,'transfer_archive_sha256':TAR_SHA,'raw_manifest_sha256':MANIFEST_SHA,
        'raw_files':17,'raw_bytes':sum(e['bytes'] for e in original.values()),'allocation':expected,
        'completion':{'state':'COMPLETED','exit':'0:0','elapsed_s':395,'batch_maxrss_kib':397140,'node':'snavely-cpu-16'},
        'post_completion_scontrol':'Expired; original allocation and completed sacct retained. Initial packaging interruption did not rerun scientific work.',
        'runtime':{k:env[k] for k in ('python','mip_version','gurobipy_version','platform')},'routine_receipts':runtimes,
        'supervisor_receipt':supervisor,'scheduler_file_hashes':scheduler_hashes,'private_outer_log_hashes':outer_hashes,
        'verified_publication_omissions':omissions,'expected_public_scientific_files':15,
        'publication_scope':'Eligibility verified; future public copy must retain all other scientific files byte-identically and include original raw manifest plus omission manifest. No log contents or license/token-server values are included here.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--transfer',type=Path,required=True)
    p.add_argument('--tar',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    need(not args.out.exists(),'exclusive new report')
    r=audit(args.transfer,args.tar)
    with args.out.open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'status':r['audit_status'],'raw_files':r['raw_files'],'bytes':r['raw_bytes'],'out':str(args.out),'omitted_stdout_files':len(r['verified_publication_omissions'])}))

if __name__=='__main__':main()
