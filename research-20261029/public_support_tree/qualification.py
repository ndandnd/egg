"""Prospective exact literal checker controls; no backend or public data."""
import copy
from fractions import Fraction as Q


def run(checker,exact):
    checks=[]
    def record(name,result,status,lower=None,clean=False):
        passed=result.get('status')==status
        if lower is not None: passed=passed and result.get('lower_bound',result.get('global_lower_bound'))==lower
        if clean:
            passed=passed and not any(k in result for k in
                ('global_lower_bound','global_lower_exceeds_target','strict_excess','higher_fleet_exclusion'))
        checks.append(dict(id=name,pass_check=passed,result=result))
    def reject(name,action):
        try: value=action()
        except (ValueError,KeyError,TypeError): value=dict(status='REJECTED',reason='Descriptor admission rejected')
        record(name,value,'REJECTED',clean=True)
    try:
        def scalar_semantic(case):
            return ({'x':(0,10),'y0':(0,1)},
                {'ge':('>=',2,{'x':1}),'le':('<=',8,{'x':1}),'eq':('=',1,{'y0':1})},
                [],{'y0':Q(3)},['x'],{'minimum_fleet':1})
        scalar=dict(movements=[dict(id='m',kind='pullout')])
        linear=checker.prepare(scalar,scalar_semantic,mode='linear',prices=[Q(1)])
        negative=checker.prepare(scalar,scalar_semantic,mode='linear',prices=[Q(-1)])
        quadratic=checker.prepare(scalar,scalar_semantic,mode='quadratic')
        positive=dict(multipliers={'ge':1,'eq':3})
        record('scalar-ge-equality',checker.verify_node(linear,(),positive),'CERTIFIED_BOUND',Q(5))
        record('scalar-le-negative-price',checker.verify_node(negative,(),dict(multipliers={'le':-1,'eq':3})),
               'CERTIFIED_BOUND',Q(-5))
        record('free-negative-equality',checker.verify_node(linear,(),dict(multipliers={'ge':1,'eq':-1})),
               'CERTIFIED_BOUND',Q(1))
        projected=checker.verify_node(linear,(),dict(multipliers={'ge':-1,'eq':3}))
        record('sign-projection-anchor',projected,'CERTIFIED_BOUND',Q(3))
        checks[-1]['pass_check'] &= projected.get('sign_projected_rows')==1
        record('finite-box-nonzero-residual',checker.verify_node(negative,(),dict(multipliers={})),
               'CERTIFIED_BOUND',Q(-10))
        a,b=Q(float(.2)),Q(float(1/900))
        tangent=dict(tangent_loads=[Q(6)],multipliers={'ge':a+6*b,'eq':3})
        record('quadratic-away-tangent',checker.verify_node(quadratic,(),tangent),
               'CERTIFIED_BOUND',3+2*a-6*b)
        contradiction=dict(multipliers={'eq':1,'__branch_0':-1},claimed_contradiction=Q(1))
        record('positive-farkas-empty-node',checker.verify_node(linear,(('m',0),),contradiction,True),
               'CERTIFIED_INFEASIBLE')
        reject('feasible-node-no-farkas',lambda:checker.verify_node(linear,(),dict(multipliers={}),True))
        reject('negative-farkas',lambda:checker.verify_node(linear,(('m',0),),dict(multipliers={'eq':-1,'__branch_0':1}),True))
        reject('altered-farkas-claim',lambda:checker.verify_node(linear,(('m',0),),dict(contradiction,claimed_contradiction=2),True))
        reject('unavailable-branch-row',lambda:checker.verify_node(linear,(),contradiction,True))
        reject('altered-bound-claim',lambda:checker.verify_node(linear,(),dict(positive,claimed_lower=6)))
        tree=dict(root='r',nodes={'r':dict(kind='branch',movement='m',children={'0':'z','1':'o'}),
            'z':dict(kind='infeasible',certificate=contradiction),'o':dict(kind='bound',certificate=positive)})
        complete=checker.verify_tree(linear,tree,target=0)
        record('complete-binary-linear-tree',complete,'COMPLETE',Q(5))
        checks[-1]['pass_check'] &= complete.get('complete') is True and complete.get('target_is_certified_here') is False
        qtree=copy.deepcopy(tree);qtree['nodes']['o']['certificate']=tangent
        qresult=checker.verify_tree(quadratic,qtree)
        record('quadratic-physical-not-CH',qresult,'COMPLETE',3+2*a-6*b)
        checks[-1]['pass_check'] &= qresult.get('global_scope')=='D_physical' and qresult.get('unrestricted_CH_claim') is False
        def malformed(name,mutation):
            changed=copy.deepcopy(tree);mutation(changed)
            reject(name,lambda:checker.verify_tree(linear,changed,target=0))
        malformed('omitted-child',lambda t:t['nodes']['r']['children'].pop('1'))
        malformed('shared-child',lambda t:t['nodes']['r']['children'].__setitem__('1','z'))
        malformed('cyclic-child',lambda t:t['nodes']['r']['children'].__setitem__('0','r'))
        malformed('missing-child',lambda t:t['nodes']['r']['children'].__setitem__('0','absent'))
        malformed('unreachable-node',lambda t:t['nodes'].__setitem__('extra',dict(kind='open')))
        malformed('unknown-movement',lambda t:t['nodes']['r'].__setitem__('movement','unknown'))
        def repeat(t):
            t['nodes']['o']=dict(kind='branch',movement='m',children={'0':'a','1':'b'})
            t['nodes']['a']=dict(kind='bound',certificate=positive)
            t['nodes']['b']=dict(kind='bound',certificate=positive)
        malformed('repeated-branch',repeat)
        opened=copy.deepcopy(tree);opened['nodes']['o']=dict(kind='open',reason='literal unresolved')
        record('explicit-open-not-global',checker.verify_tree(linear,opened,target=0),'OPEN_TREE',clean=True)
        for name,limit in [('node-limit',dict(nodes=2)),('depth-limit',dict(depth=0)),('checkpoint-limit',dict(operations=0))]:
            record(name,checker.verify_tree(linear,tree,target=0,limits=limit),'UNRESOLVED',clean=True)
        def literal_case():
            c=dict(name='tree-fleet-literal',depot='D',max_vehicles=3,battery_kwh=20,reserve_kwh=0,
                terminal_open_min=0,recharge_deadline_min=120,vehicle_cost=7,deadhead_cost_per_min=0,efficiency=1,
                graph_scope='declared-movement-modes-only',market_edges_min=[0,60,120],
                resources=[dict(start_min=0,end_min=120,per_bus_kw=20,grid_kw=20,connectors=1)],trips=[],movements=[])
            for i in range(2):
                tid='T'+str(i)
                c['trips'].append(dict(id=tid,start_min=0,end_min=30,start_place='D',end_place='D',energy_kwh=5))
                for kind,time,before,after in [('pullout',0,None,tid),('pullin',30,tid,None)]:
                    c['movements'].append(dict(id=kind+tid,kind=kind,before=before,after=after,depot_split=None,
                        legs=[dict(origin='D',destination='D',depart_min=time,arrive_min=time,energy_kwh=0)]))
            return c
        case=literal_case();token='literal-source-case'
        two=checker.prepare(case,exact._reconstruct,mode='quadratic',fleet_count=2,case_token=token)
        certificate=dict(tangent_loads=[0,0],multipliers={'__fleet_count__':7})
        one=dict(root='r',nodes={'r':dict(kind='bound',certificate=certificate)})
        floor=dict(case_token=token,minimum_fleet=3,proof_kind='quadratic_affine_service_floor',
                   scope='physical_ge_3',lower_bound=21+10*a)
        admitted=checker.verify_tree(two,one,exclusion=floor,admit_transfer=lambda r:r is floor)
        record('literal-two-plus-source-floor',admitted,'COMPLETE',Q(14))
        conditional=checker.verify_tree(two,one)
        record('two-bus-remains-conditional',conditional,'COMPLETE')
        checks[-1]['pass_check'] &= conditional.get('global_lower_bound') is None and conditional.get('scope')=='D_two'
        def floor_reject(name,changed,context=two,callback=lambda r:True):
            reject(name,lambda:checker.verify_tree(context,one,exclusion=changed,admit_transfer=callback,target=0))
        floor_reject('wrong-case-token',dict(floor,case_token='other'))
        floor_reject('denied-transfer',floor,callback=lambda r:False)
        floor_reject('excessive-floor',dict(floor,lower_bound=floor['lower_bound']+1))
        def weak(case):
            values=list(exact._reconstruct(case));values[-1]=dict(values[-1],minimum_fleet=1);return tuple(values)
        no_obstruction=checker.prepare(case,weak,mode='quadratic',fleet_count=2,case_token=token)
        floor_reject('missing-one-bus-obstruction',floor,context=no_obstruction)
        lp=checker.prepare(case,exact._reconstruct,mode='linear',prices=[a,Q(.3)],fleet_count=2,case_token=token)
        lpone=dict(root='r',nodes={'r':dict(kind='bound',certificate=dict(multipliers={'__fleet_count__':7}))})
        linear_floor=dict(case_token=token,minimum_fleet=3,proof_kind='linear_min_price_service_floor',
            scope='response_ge_3',prices=[a,Q(.3)],lower_bound=21+10*a)
        record('exact-linear-price-floor',checker.verify_tree(lp,lpone,exclusion=linear_floor,admit_transfer=lambda r:True),'COMPLETE',Q(14))
        reject('nonlinear-floor-at-new-price',lambda:checker.verify_tree(lp,lpone,exclusion=floor,admit_transfer=lambda r:True,target=0))
        reject('changed-exclusion-price',lambda:checker.verify_tree(lp,lpone,exclusion=dict(linear_floor,prices=[a,Q(.31)]),admit_transfer=lambda r:True,target=0))
        neg=checker.prepare(case,exact._reconstruct,mode='linear',prices=[Q(-.1),a],fleet_count=2,case_token=token)
        reject('negative-price-exclusion',lambda:checker.verify_tree(neg,lpone,exclusion=dict(linear_floor,prices=[Q(-.1),a]),admit_transfer=lambda r:True,target=0))
        for name,mutation in [('negative-fee',lambda c:c.__setitem__('vehicle_cost',-1)),
            ('negative-omitted-cost',lambda c:c.__setitem__('deadhead_cost_per_min',-1)),
            ('negative-omitted-energy',lambda c:c['movements'][0]['legs'][0].__setitem__('energy_kwh',-1)),
            ('unknown-schema',lambda c:c.__setitem__('hidden_waiting_cost',-1))]:
            changed=copy.deepcopy(case);mutation(changed)
            reject(name,lambda c=changed:checker.prepare(c,exact._reconstruct,mode='quadratic',fleet_count=2,case_token=token))
        return dict(status='PASS' if all(c['pass_check'] for c in checks) else 'FAIL',checks=checks,
                    backend_calls=0,scope='Literal exact checker qualification, not public backend qualification')
    except Exception as exc:
        return dict(status='FAIL',checks=checks,unexpected_failure=type(exc).__name__+': '+str(exc),backend_calls=0)
