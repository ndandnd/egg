"""Standalone retained-evidence verification: stdlib only, no Git or solver."""
import argparse
from fractions import Fraction as Q
import gzip
import hashlib
import json
from pathlib import Path
import resource
import re
import sys
import time
import types

CASE_TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
REFINED_LOWER=Q('80662634237282610902559758444585953851595472957985/182687704666362864775460604089535377456991567872')
MEMBERS=('checkers/physical.py','checkers/semantic.py','checkers/tree.py',
         'evidence/case.json','evidence/physical.json.gz','evidence/response.json.gz',
         'evidence/mixture.json.gz','evidence/tree.json.gz','evidence/refinement.json.gz','verify.py','README.md')


def need(ok,message):
    if not ok:raise ValueError(message)


def decode(raw):
    def pairs(items):
        result={}
        for key,value in items:
            need(key not in result,'duplicate JSON key');result[key]=value
        return result
    def invalid(value):raise ValueError('nonfinite JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)


def q(value):
    need(not isinstance(value,bool),'boolean quantity');return Q(value)


def _module(name,raw):
    result=types.ModuleType(name);exec(compile(raw,name,'exec'),result.__dict__);return result


def fixed_mixture(left,right,mixture,a,b,periods):
    w=q(mixture['lambda_right'])
    need(0<=w<=1 and q(mixture['lambda_left'])==1-w,'mixture weights')
    need(len(left['loads'])==len(right['loads'])==periods,'market dimensions')
    loads=tuple((1-w)*x+w*y for x,y in zip(left['loads'],right['loads']))
    ops=(1-w)*left['ops']+w*right['ops']
    upper=ops+sum((a*e+b*e*e/2 for e in loads),Q(0))
    need(tuple(map(q,mixture['loads']))==loads and q(mixture['ops'])==ops
         and q(mixture['objective'])==upper,'fixed mixture direct value')
    return upper


def graft_tree(original,refinement,expected_base_nodes=303,expected_frontier=152,expected_new_nodes=72):
    """Pure reference expansion; no claimed old/new bound or flag is trusted.

    Every inherited base_bound is replaced by its ORIGINAL algebraic proof,
    checked later under the complete grafted root-to-leaf decision path.
    """
    old=original['tree'];nodes=old['nodes'];new=refinement['refinements']
    need(len(nodes)==expected_base_nodes and old['root'] in nodes,'old partition shape')
    leaves={identifier for identifier,node in nodes.items() if node['kind']!='branch'}
    need(len(leaves)==expected_frontier and set(new)==leaves,'full refinement frontier denominator')
    need(sum(len(tree['nodes'])-1 for tree in new.values())==expected_new_nodes,'new descendant denominator')
    output={}
    def oldname(identifier):return 'old/'+identifier
    def localname(leaf,identifier):return 'local/'+str(len(leaf))+':'+leaf+'/'+identifier
    def target(identifier):
        need(identifier in nodes,'missing original child')
        return localname(identifier,new[identifier]['root']) if identifier in leaves else oldname(identifier)
    for identifier,node in nodes.items():
        need(isinstance(identifier,str),'old string identity')
        if node['kind']=='branch':
            need(set(node['children'])=={'0','1'},'old both-child coverage')
            output[oldname(identifier)]=dict(kind='branch',movement=node['movement'],
                children={v:target(child) for v,child in node['children'].items()})
            continue
        need(node['kind'] in ('bound','infeasible'),'old leaf needs exact certificate')
        old_certificate=original['proofs'][node['certificate_ref']]['certificate']
        tree=new[identifier];need(tree['root'] in tree['nodes'],'missing local root')
        if node['kind']=='infeasible':
            need(len(tree['nodes'])==1 and tree['nodes'][tree['root']]['kind'] in ('base_bound','base_infeasible'),
                 'old infeasible region must retain its original contradiction')
        for local_id,local in tree['nodes'].items():
            need(isinstance(local_id,str),'local string identity');kind=local['kind']
            name=localname(identifier,local_id)
            if kind=='branch':
                need(set(local['children'])=={'0','1'},'new both-child coverage')
                need(all(child in tree['nodes'] for child in local['children'].values()),'missing new child')
                output[name]=dict(kind='branch',movement=local['movement'],
                    children={v:localname(identifier,child) for v,child in local['children'].items()})
            elif kind in ('base_bound','base_infeasible'):
                need(local['base_leaf_id']==identifier,'foreign inherited base proof')
                need(kind!='base_infeasible' or node['kind']=='infeasible','unproved inherited infeasibility')
                output[name]=dict(kind=node['kind'],certificate=old_certificate)
            else:
                need(kind in ('bound','infeasible'),'open/native-only refinement leaf')
                certificate=refinement['proofs'][local['certificate_ref']]['certificate']
                # Select the proposed stronger proof, never a trusted bound.
                # Its claimed scalar is checked by the immutable algebra below.
                if kind=='bound' and node['kind']=='bound' and q(old_certificate['claimed_lower'])>q(certificate['claimed_lower']):
                    certificate=old_certificate
                output[name]=dict(kind=kind,certificate=certificate)
    need(len(output)==expected_base_nodes+expected_new_nodes,'combined partition denominator')
    return dict(root=target(old['root']),nodes=output)


def literal_qualification():
    """New adapter literals only, no public replay or old checker qualification."""
    checks=[]
    def reject(name,action):
        try:action()
        except (ValueError,KeyError,TypeError):checks.append(dict(id=name,rejected=True))
        else:raise ValueError('literal corruption accepted: '+name)
    left=dict(loads=(Q(0),),ops=Q(2));right=dict(loads=(Q(2),),ops=Q(4))
    mix=dict(lambda_left=Q(1,2),lambda_right=Q(1,2),loads=[1],ops=3,objective=5)
    need(fixed_mixture(left,right,mix,Q(1),Q(2),1)==5,'literal mixture anchor')
    reject('duplicate-json',lambda:decode('{"x":1,"x":2}'))
    reject('nonfinite-json',lambda:decode('{"x":NaN}'))
    reject('boolean-quantity',lambda:q(True))
    for key,value in [('lambda_left',0),('loads',[2]),('ops',4),('objective',6)]:
        changed=dict(mix);changed[key]=value
        reject('changed-'+key,lambda c=changed:fixed_mixture(left,right,c,Q(1),Q(2),1))
    reject('wrong-dimension',lambda:fixed_mixture(left,right,mix,Q(1),Q(2),2))
    old=dict(tree=dict(root='r',nodes={'r':dict(kind='branch',movement='m0',children={'0':'a','1':'b'}),
        'a':dict(kind='bound',certificate_ref='a'),'b':dict(kind='infeasible',certificate_ref='b')}),
        proofs={'a':dict(certificate={'multipliers':{},'claimed_lower':1}),'b':dict(certificate={'multipliers':{'x':1}})})
    new=dict(refinements={'a':dict(root='r',nodes={
        'r':dict(kind='branch',movement='m1',children={'0':'z','1':'o'}),
        'z':dict(kind='base_bound',base_leaf_id='a'),'o':dict(kind='bound',certificate_ref='p')}),
        'b':dict(root='r',nodes={'r':dict(kind='base_bound',base_leaf_id='b')})},
        proofs={'p':dict(certificate={'multipliers':{'y':1},'claimed_lower':2})})
    graft=graft_tree(old,new,3,2,2)
    need(len(graft['nodes'])==5 and sum(n['kind']=='infeasible' for n in graft['nodes'].values())==1,
         'literal exact-proof graft anchor')
    import copy
    for name,mutate in (
        ('missing-refinement',lambda r:r['refinements'].pop('b')),
        ('foreign-base-proof',lambda r:r['refinements']['a']['nodes']['z'].__setitem__('base_leaf_id','b')),
        ('missing-local-child',lambda r:r['refinements']['a']['nodes']['r']['children'].pop('1')),
        ('missing-new-proof',lambda r:r['proofs'].pop('p')),
        ('native-only-new-leaf',lambda r:r['refinements']['a']['nodes'].__setitem__('o',dict(kind='native_optimal'))),
    ):
        changed=copy.deepcopy(new);mutate(changed)
        reject(name,lambda r=changed:graft_tree(old,r,3,2,2))
    return dict(status='PASS',anchor_checks=2,negative_controls=checks,native_calls=0,
                scope='New decoder/mixture/graft adapter only; not public evidence or exact-tree requalification')


def verify_bundle(directory,expected_manifest_sha256,limits=None):
    """One new full check; caller funds complete construction/admission/closure.

    expected digest must come from a separately trusted builder/public receipt,
    not be calculated from an untrusted manifest and accepted without binding.
    """
    limits=dict(dict(seconds=500,checker_seconds=450,rss_bytes=2*1024**3,tree_nodes=375,tree_depth=375,
                     compressed_bytes=512*1024**2,decompressed_bytes=512*1024**2,
                     total_bytes=1024**3),**(limits or {}))
    started=time.monotonic();root=Path(directory).resolve();steps=[]
    def gate():
        need(time.monotonic()-started<limits['seconds'],'verification wall checkpoint')
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        need(rss<=limits['rss_bytes'],'observed RSS limit')
    try:
        need(isinstance(expected_manifest_sha256,str) and re.fullmatch('[0-9a-f]{64}',expected_manifest_sha256) is not None,
             'trusted full SHA-256 digest required')
        gate();manifest_path=root/'MANIFEST.json'
        need(not manifest_path.is_symlink() and manifest_path.stat().st_size<=1024**2,'manifest path/size')
        raw=manifest_path.read_bytes()
        need(hashlib.sha256(raw).hexdigest()==expected_manifest_sha256,'untrusted manifest digest')
        manifest=decode(raw)
        need(manifest['schema']=='public-sign-bundle-v1' and manifest['case_token']==CASE_TOKEN,'manifest schema/case')
        need(manifest['redistribution_status']=='UNRESOLVED' and manifest['purpose']=='local author review',
             'unreviewed distribution declaration')
        files=manifest['files'];need(set(files)==set(MEMBERS),'exact bundle member closure')
        buffers={};total=0
        for name in MEMBERS:
            gate();path=root/name
            need(not path.is_symlink() and path.resolve().is_relative_to(root),'unsafe bundle member')
            size=path.stat().st_size;need(size<=limits['compressed_bytes'],'member size limit')
            value=path.read_bytes();total+=len(value)
            need(total<=limits['total_bytes'],'total input size')
            need(len(value)==files[name]['bytes'] and hashlib.sha256(value).hexdigest()==files[name]['sha256'],
                 'member integrity: '+name)
            buffers[name]=value
        def packet(name):
            gate();value=buffers.pop(name)
            if name.endswith('.gz'):
                import io
                with gzip.GzipFile(fileobj=io.BytesIO(value)) as stream:
                    value=stream.read(limits['decompressed_bytes']+1)
                need(len(value)<=limits['decompressed_bytes'],'decompressed size limit')
            return decode(value)
        physical=_module('portable_physical',buffers.pop('checkers/physical.py'))
        semantic=_module('portable_semantic',buffers.pop('checkers/semantic.py'))
        treechecker=_module('portable_tree',buffers.pop('checkers/tree.py'))
        case=packet('evidence/case.json')
        # The trusted manifest binds the exact descriptor. Independent semantics
        # also reject undeclared schema/coefficients; no native identity import.
        points=[]
        for name in ('evidence/physical.json.gz','evidence/response.json.gz'):
            data=packet(name);candidate=data['recovery']['candidate'];del data
            gate();audit=physical.verify(case,candidate)
            need(all(audit.get(k) is True for k in ('strict_pass','physical_strict_pass',
                 'objective_is_certified_physical_upper')),'strict physical witness failure')
            points.append(dict(loads=tuple(map(q,audit['loads_exact'])),ops=q(audit['ops_exact']),
                               objective=q(audit['objective_exact'])))
            steps.append(dict(stage=name,status='STRICT_PHYSICAL_PASS'))
        mixture=packet('evidence/mixture.json.gz')['mixture'];a,b=Q(float(.2)),Q(float(1/900))
        upper=fixed_mixture(points[0],points[1],mixture,a,b,30)
        steps.append(dict(stage='mixture',status='FEASIBLE_HULL_UPPER',value=upper))
        data=packet('evidence/tree.json.gz');need(data['case_token']==CASE_TOKEN,'tree case token')
        refinement=packet('evidence/refinement.json.gz')
        proof=graft_tree(data,refinement);del data,refinement
        gate();context=treechecker.prepare(case,semantic._reconstruct,mode='quadratic',fleet_count=2,case_token=CASE_TOKEN)
        need(context['minimum_fleet_proof']['minimum_fleet']>=2,'uncovered zero/one-bus plans')
        floor=dict(case_token=CASE_TOKEN,minimum_fleet=3,proof_kind='quadratic_affine_service_floor',scope='physical_ge_3',
                   lower_bound=3*q(case['vehicle_cost'])+a*sum((q(t['energy_kwh']) for t in case['trips']),Q(0))/q(case['efficiency']))
        allowance=min(limits['checker_seconds'],limits['seconds']-(time.monotonic()-started))
        need(allowance>0,'exact tree check funding')
        audit=treechecker.verify_tree(context,proof,exclusion=floor,admit_transfer=lambda r:r is floor,
            limits=dict(nodes=limits['tree_nodes'],depth=limits['tree_depth'],operations=100000000,fraction_bits=32768,seconds=allowance))
        need(audit.get('status')=='COMPLETE' and audit.get('complete') is True
             and isinstance(audit.get('global_lower_bound'),Q),'complete physical coverage unavailable')
        lower=audit['global_lower_bound'];need(lower>upper,'strict positive gap not certified')
        need(lower>=REFINED_LOWER,'stronger retained physical lower not reproduced')
        gate();steps.append(dict(stage='tree',status='GLOBAL_PHYSICAL_LOWER',value=lower,checked_nodes=audit['checked_nodes']))
        return dict(status='PASS',case_token=CASE_TOKEN,physical_upper=min(p['objective'] for p in points),
                    hull_upper=upper,physical_lower=lower,gap_lower=lower-upper,steps=steps,
                    declared_movement_model_only=True,native_calls=0,external_replication=False,
                    author_written_retained_evidence_check=True,elapsed_s=time.monotonic()-started)
    except Exception as exc:
        return dict(status='FAIL_OR_UNRESOLVED',reason=type(exc).__name__+': '+str(exc),steps=steps,
                    native_calls=0,elapsed_s=time.monotonic()-started)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--output',required=True);args=parser.parse_args()
    result=verify_bundle(Path(__file__).resolve().parent,args.manifest_sha256)
    with Path(args.output).open('x') as stream:json.dump(result,stream,default=str,indent=2);stream.write('\n')
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
