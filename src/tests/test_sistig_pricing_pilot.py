"""Admission checks for the prospective full public-timetable pilot; no solver."""
from copy import deepcopy
import pytest
import json
from types import SimpleNamespace
from experiments import sistig_pricing_pilot as pilot


def test_full_cases_preserve_source_identity_and_replenished_reference():
    cells = pilot.controls()
    assert [c['id'] for c in cells] == ['depot_15_flat','depot_16_flat']
    assert [len(c['case'].movements) for c in cells] == [1370,1335]
    for cell,energy in zip(cells,[2089.876441,2769.8144794]):
        assert len(cell['case'].trips) == 37
        assert len(cell['prices']) == 30
        assert cell['reference_witness']['replay_ok']
        assert cell['reference_upper'] == pytest.approx(3700+.2*energy)
        assert cell['reference_witness']['used_vehicle_count'] == 37


def test_bounded_interval_is_reported_without_optimality(monkeypatch):
    cell={'case':SimpleNamespace(identity=lambda:'fixture'),'prices':[.2],'reference_upper':1200.}
    result={'status':'bounded','lower':700.,'upper':900.000001,
            'gap':200.000001,'plan':{},'case_identity':'fixture','prices':[.2],
            'stats':{'status':'FEASIBLE','incumbent':900.,'lower_bound':700.000001,
                     'backend':'GRB','threads':1,'backend_runtime':{'requested':'GRB','solver_module':'mip.gurobi','model_solver_name':'GRB'}}}
    monkeypatch.setattr(pilot.nr,'replay_native',lambda *a:{'pricing_objective':900.})
    assessment=pilot.assess(cell,result,'GRB')
    assert assessment['pass'] and not assessment['optimality_certified']
    for key,value in [('lower',1201.),('gap',0.),('status','certified'),
                      ('upper',float('nan')),('lower',True),('status','infeasible'),
                      ('case_identity','foreign'),('prices',[.21]),('stats',{})]:
        corrupted=deepcopy(result);corrupted[key]=value
        assert not pilot.assess(cell,corrupted,'GRB')['pass']
    monkeypatch.setattr(pilot.nr,'replay_native',lambda *a:{'pricing_objective':901.})
    assert not pilot.assess(cell,result,'GRB')['pass']


def test_physical_rejection_cannot_be_saved_by_native_optimal_status(monkeypatch):
    def reject(*args):
        raise ValueError('Missed mandatory service')
    monkeypatch.setattr(pilot.nr,'replay_native',reject)
    cell={'case':SimpleNamespace(identity=lambda:'fixture'),'prices':[.2],'reference_upper':1200.}
    result={'status':'certified','lower':899.999999,'upper':900.000001,
            'gap':.000002,'plan':{},'case_identity':'fixture','prices':[.2]}
    assert not pilot.assess(cell,result,'GRB')['pass']


def test_raw_phase_identity_order_and_status_are_required(tmp_path):
    stats={'wall_s':1.}
    names=['native_start','native_status','native_incumbent','charge_normalization',
           'serial_decoding','objective_reconstruction']
    events=[{'event':name,'round':0,**({'stats':stats} if name=='native_status' else {})} for name in names]
    package={'assessment':{'pass':True},'result':{'status':'bounded','stats':stats}}
    (tmp_path/'result.json').write_text(json.dumps(package))
    def check(rows):
        (tmp_path/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in rows))
        return pilot.read_worker_evidence(tmp_path)[2]
    assert not check(events)
    wrong=deepcopy(events);wrong[1]['round']=1
    assert check(wrong)
    assert check(events[:2])
    assert check([events[1],events[0],*events[2:]])
    assert check(events+[events[-1]])
    wrong=deepcopy(events);wrong[1]['stats']['wall_s']=2.
    assert check(wrong)


def test_deadline_failure_preserves_scientific_verdict_without_admission():
    original={'pass':True,'issues':[],'optimality_certified':True}
    assert pilot.assess_runtime(original,240.,240.)['pass']
    for elapsed in [240.00001,float('inf'),float('nan'),-1,True]:
        failed=pilot.assess_runtime(original,elapsed,240.)
        assert not failed['pass'] and not failed['optimality_certified']
        assert original=={'pass':True,'issues':[],'optimality_certified':True}
