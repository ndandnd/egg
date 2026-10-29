"""Prospective literal algebra/coverage controls; never run on import."""
import copy
from fractions import Fraction as Q


def run(admission,checker):
    checks=[]
    def test(name,ok): checks.append(dict(id=name,pass_check=bool(ok)))
    def reject(name,action):
        try: result=action()
        except (ValueError,KeyError,TypeError): test(name,True)
        else: test(name,isinstance(result,dict) and result.get('status')=='REJECTED')
    try:
        # F(u)=u+u², ubar=2, cbar=3: H=9,p=5,k=-4.
        record=admission.derive([2],3,9,[1],[2])
        test('exact-gradient-constant-target',record['p']==[5] and record['k']==-4
             and record['target']==Q(129999,10000))
        test('tangent-direct-value',record['k']+5*2==6)
        closed=admission.close_bound(record,Q(13))
        test('hull-lower-identity',closed['hull_lower']==9 and closed['width']==0 and closed['epsilon_met'])
        for key,value in [('p',[6]),('k',-3),('target',13),('fleet_count',2),
                          ('all_bus_counts_retained',False),('epsilon',Q(1,1000))]:
            changed=copy.deepcopy(record);changed[key]=value
            reject('tampered-'+key,lambda r=changed:admission.validate_derived(r))
        reject('invalid-mixture-objective',lambda:admission.derive([2],3,10,[1],[2]))
        reject('negative-curvature',lambda:admission.derive([2],3,9,[1],[-2]))
        reject('missing-target',lambda:admission.validate_derived({k:v for k,v in record.items() if k!='target'}))
        reject('lower-above-feasible-upper',lambda:admission.close_bound(record,14))
        # A literal complete domain with two binary alternatives. Both must remain
        # represented; these synthetic rows are not a public physical model.
        def semantic(case):
            return ({'x':(0,10),'y0':(0,1),'y1':(0,1)},
                    {'choose':('=',1,{'y0':1,'y1':1})},[],
                    {'y0':Q(6),'y1':Q(9)},['x'],{'minimum_fleet':2})
        case=dict(movements=[dict(id='left',kind='pullout'),dict(id='right',kind='pullout')])
        context=checker.prepare(case,semantic,mode='linear',prices=[Q(5)],fleet_count=None)
        cert=dict(multipliers={'choose':6},claimed_lower=6)
        node=checker.verify_node(context,(),cert)
        test('literal-all-domain-linear-bound',node['status']=='CERTIFIED_BOUND' and node['lower_bound']==6
             and context['scope']=='V(p)' and '__fleet_count__' not in context['rows'])
        tree=dict(root='r',nodes={'r':dict(kind='branch',movement='left',children={'0':'z','1':'o'}),
                    'z':dict(kind='bound',certificate=cert),'o':dict(kind='bound',certificate=cert)})
        audited=checker.verify_tree(context,tree)
        test('both-branches-complete',audited['status']=='COMPLETE' and audited['global_lower_bound']==6)
        missing=copy.deepcopy(tree);missing['nodes']['r']['children'].pop('1')
        reject('omitted-binary-child',lambda:checker.verify_tree(context,missing))
        opened=copy.deepcopy(tree);opened['nodes']['o']=dict(kind='open',reason='literal unresolved')
        test('open-fringe-not-global',checker.verify_tree(context,opened)['status']=='OPEN_TREE')
        reject('changed-price-bound-claim',lambda:checker.verify_node(
            checker.prepare(case,semantic,mode='linear',prices=[Q(-1)]),(),cert))
        # This tests the invalid old exact-two row explicitly, not only a label.
        reject('unavailable-two-fleet-multiplier',lambda:checker.verify_node(
            context,(),dict(multipliers={'__fleet_count__':3})))
        return dict(status='PASS' if all(c['pass_check'] for c in checks) else 'FAIL',
                    checks=checks,backend_calls=0)
    except Exception as exc:
        return dict(status='FAIL',checks=checks,backend_calls=0,
                    unexpected_failure=type(exc).__name__+': '+str(exc))
