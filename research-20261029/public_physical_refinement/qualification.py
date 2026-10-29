"""Prospective structure/admission-interface literals, not exact algebra tests."""
import copy
from fractions import Fraction as Q


def run(wrapper,extractor=None):
    checks=[]
    def mark(name,ok):checks.append(dict(id=name,pass_check=bool(ok)))
    class MockExact:
        # Intentionally does no algebra: these literals qualify path forwarding
        # and structure only; immutable node algebra has its own transferred gate.
        @staticmethod
        def verify_node(context,path,certificate,infeasible=False,limits=None):
            if tuple(path)!=tuple(certificate.get('expected_path',())):
                return dict(status='REJECTED',reason='mock path mismatch')
            if certificate.get('literal_authority')!='MOCK_INTERFACE_ONLY':
                return dict(status='REJECTED',reason='native flag is not certificate')
            if infeasible:return dict(status='CERTIFIED_INFEASIBLE',lower_bound=None,contradiction=Q(1))
            return dict(status='CERTIFIED_BOUND',lower_bound=Q(certificate['literal_lower']))
    try:
        context=dict(case_token='literal',fleet_count=2,mode='quadratic',movement_variables={'m0':'y0','m1':'y1'},
                     minimum_fleet_proof={'minimum_fleet':2})
        base=dict(status='SOURCE_BOUND_BASE_ADMITTED',case_token='literal',minimum_fleet=2,fleet_count=2,
            epsilon=Q(1,10000),physical_upper=Q(8),target=Q(79999,10000),
            old_global_physical_lower=Q(5),floor_ge3=Q(10),base_nodes=3,
            base_tree=dict(root='r',nodes={'r':dict(kind='branch',movement='m0',children={'0':'a','1':'b'}),
                'a':dict(kind='admitted_base_leaf',leaf_id='a'),'b':dict(kind='admitted_base_leaf',leaf_id='b')}),
            frontier=[dict(leaf_id='a',decisions=(('m0',0),),status='CERTIFIED_BOUND',lower_bound=Q(5)),
                      dict(leaf_id='b',decisions=(('m0',1),),status='CERTIFIED_INFEASIBLE',contradiction=Q(1))])
        seal=wrapper.seal_base(base)
        packet=dict(refinements={'a':dict(root='x',nodes={'x':dict(kind='base_bound',base_leaf_id='a')}),
                                 'b':dict(root='x',nodes={'x':dict(kind='base_infeasible',base_leaf_id='b')})},proofs={})
        def invoke(b=base,p=packet,authority=None,snapshot=seal):
            return wrapper.verify_refinements(context,b,p,MockExact,
                (lambda x:x is base) if authority is None else authority,base_seal=snapshot)
        result=invoke();mark('retain-complete-base',result['global_lower_bound']==5)
        improved=copy.deepcopy(packet)
        improved['refinements']['a']=dict(root='r',nodes={
            'r':dict(kind='branch',movement='m1',children={'0':'z','1':'o'}),
            'z':dict(kind='bound',certificate=dict(expected_path=(('m0',0),('m1',0)),
                literal_authority='MOCK_INTERFACE_ONLY',literal_lower=6)),
            'o':dict(kind='bound',certificate=dict(expected_path=(('m0',0),('m1',1)),
                literal_authority='MOCK_INTERFACE_ONLY',literal_lower=6))})
        result=invoke(p=improved);mark('new-prefix-forwarded-full-coverage',result['global_lower_bound']==6 and result['new_nodes_checked']==2)
        weaker=copy.deepcopy(improved)
        for name in ('z','o'):weaker['refinements']['a']['nodes'][name]['certificate']['literal_lower']=4
        mark('weaker-new-keeps-old',invoke(p=weaker)['global_lower_bound']==5)
        mark('false-authority',invoke(authority=lambda x:False)['status']=='REJECTED')
        foreign=copy.deepcopy(base)
        mark('foreign-object',invoke(b=foreign)['status']=='REJECTED')
        mark('missing-seal',invoke(snapshot=None)['status']=='REJECTED')
        base['floor_ge3']=Q(11)
        mark('same-object-mutated-floor',invoke()['status']=='REJECTED');base['floor_ge3']=Q(10)
        base['frontier'][0]['lower_bound']=Q(6)
        mark('same-object-mutated-lower',invoke()['status']=='REJECTED');base['frontier'][0]['lower_bound']=Q(5)
        for name,mutation in (
            ('missing-base-id',lambda p:p['refinements'].pop('b')),
            ('foreign-base-id',lambda p:p['refinements'].__setitem__('foreign',p['refinements']['a'])),
        ):
            changed=copy.deepcopy(packet);mutation(changed);mark(name,invoke(p=changed)['status']=='REJECTED')
        for name,mutation in (
            ('missing-local-child',lambda t:t['nodes']['r']['children'].pop('1')),
            ('repeat-inherited-branch',lambda t:t['nodes']['r'].__setitem__('movement','m0')),
            ('native-optimal-only',lambda t:t['nodes'].__setitem__('z',dict(kind='bound',certificate={'raw_status':'OPTIMAL'}))),
            ('explicit-open-fringe',lambda t:t['nodes'].__setitem__('z',dict(kind='open'))),
            ('wrong-inherited-proof-path',lambda t:t['nodes']['z']['certificate'].__setitem__('expected_path',(('m1',0),))),
        ):
            changed=copy.deepcopy(improved);mutation(changed['refinements']['a']);answer=invoke(p=changed)
            mark(name,answer['status']=='VALID_BASE_WITH_REJECTED_REFINEMENTS'
                 and answer['global_lower_bound']==5 and answer['rejected_refinements']==['a'])
        changed=copy.deepcopy(packet);changed['refinements']['a']['nodes']['x']['base_leaf_id']='b'
        mark('foreign-base-bound',invoke(p=changed)['status']=='VALID_BASE_WITH_REJECTED_REFINEMENTS')
        if extractor is not None:
            try:extractor.adopt({}, {}, {}, {}, {}, {})
            except (ValueError,KeyError,TypeError):mark('extractor-invalid-pins',True)
            else:mark('extractor-invalid-pins',False)
            # Source-defined SCHEMA fixture only. This never authenticates a
            # public packet or recomputes any old numerical certificate.
            nodes={};audited=[]
            for j in range(151):
                root='r'+str(j);left='l'+str(j)
                right='r'+str(j+1) if j<150 else 'last'
                nodes[root]=dict(kind='branch',movement='synthetic_m'+str(j),children={'0':left,'1':right})
                nodes[left]=dict(kind='bound',certificate_ref='synthetic_'+left)
                audited.append(dict(id=left,status='CERTIFIED_BOUND',lower_bound=extractor.UPPER-1,contradiction=None))
            nodes['last']=dict(kind='bound',certificate_ref='synthetic_last')
            audited.append(dict(id='last',status='CERTIFIED_BOUND',lower_bound=extractor.UPPER-1,contradiction=None))
            tree=dict(case_token=extractor.CASE_TOKEN,tree=dict(root='r0',nodes=nodes))
            audit=dict(status='COMPLETE',complete=True,checked_nodes=303,scope='D_two',global_scope='D_physical',
                global_lower_bound=extractor.UPPER-1,leaves=audited,
                higher_fleet_exclusion=dict(status='ADMITTED_GE_3_FLOOR',scope='physical_ge_3',
                    case_token=extractor.CASE_TOKEN,lower_bound=extractor.UPPER+1))
            results=dict(status='CLOSED',assigned=3,resource_pass=True,scientific_outcome='POSITIVE_GAP_CERTIFIED',
                rows=[dict(id=n,status='DELIVERED',summary=dict(status='PASS',backend_calls=0))
                      for n in ('Q0','PUBLIC_TREE','INDEPENDENT_TREE_CHECK')])
            owner=dict(source_revision=extractor.OLD_SOURCE,result_status='CLOSED',child_exit=0,reaped=True,
                       resource_pass=True,failure=None)
            upper=dict(status='QUALIFIED_TRANSFER',case_identity=extractor.CASE_TOKEN,
                packet_artifact_revision='0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee',
                producer_source_revision='425bf35452eb3f5444f20058ad6fd6b540ffed88',primal_admitted=True,
                worker_reaped=True,resource_pass=True,producer_exit=0,upper_exact=extractor.UPPER)
            inputs=[tree,audit,results,owner,upper,extractor.PINS]
            adopted=extractor.adopt(*inputs)
            mark('extractor-synthetic-schema-positive',adopted['base_nodes']==303
                 and len(adopted['frontier'])==152 and adopted['status']=='SOURCE_BOUND_BASE_ADMITTED')
            mutations=[('extractor-missing-audited-leaf',lambda v:v[1]['leaves'].pop()),
                ('extractor-duplicate-audited-leaf',lambda v:v[1]['leaves'].append(copy.deepcopy(v[1]['leaves'][0]))),
                ('extractor-wrong-scope',lambda v:v[1].__setitem__('scope','V(p)')),
                ('extractor-missing-floor-field',lambda v:v[1]['higher_fleet_exclusion'].pop('lower_bound')),
                ('extractor-wrong-floor-scope',lambda v:v[1]['higher_fleet_exclusion'].__setitem__('scope','response_ge_3')),
                ('extractor-missing-tree-schema',lambda v:v[0].pop('tree'))]
            for name,mutation in mutations:
                changed=copy.deepcopy(inputs);mutation(changed)
                try:extractor.adopt(*changed)
                except (ValueError,KeyError,TypeError):mark(name,True)
                else:mark(name,False)
        return dict(status='PASS' if all(c['pass_check'] for c in checks) else 'FAIL',checks=checks,
                    native_calls=0,exact_algebra_requalified=False,
                    scope='Synthetic structure/authentication interface with mock node algebra only')
    except Exception as exc:
        return dict(status='FAIL',checks=checks,reason=type(exc).__name__+': '+str(exc),native_calls=0)
