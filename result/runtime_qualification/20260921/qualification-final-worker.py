
import json, platform, sys, importlib.metadata as md
import numpy as np
assert np.allclose(np.array([1.0,2.0]) @ np.array([1.0,2.0]), 5.0)
from mip import Model, CBC, CONTINUOUS, BINARY, MINIMIZE, OptimizationStatus
results = []
def model():
    m = Model(sense=MINIMIZE, solver_name=CBC)
    m.threads = 1
    m.verbose = 0
    m.max_mip_gap = 0
    return m
m = model()
x = m.add_var(name='x', var_type=CONTINUOUS, lb=0)
m += x >= 1
m.objective = x
s = m.optimize(max_seconds=5)
results.append({'test':'lp_min_x_ge_1','status':s.name,'objective':m.objective_value,'x':x.x})
assert s == OptimizationStatus.OPTIMAL and abs(m.objective_value-1)<1e-9 and abs(x.x-1)<1e-9
m = model()
x = m.add_var(name='x', var_type=BINARY)
y = m.add_var(name='y', var_type=BINARY)
m += 2*x + y >= 2
m.objective = 3*x + 2*y
s = m.optimize(max_seconds=5)
results.append({'test':'binary_min_3x_2y','status':s.name,'objective':m.objective_value,'bound':m.objective_bound,'x':x.x,'y':y.x})
assert s == OptimizationStatus.OPTIMAL and abs(m.objective_value-3)<1e-9 and abs(m.objective_bound-3)<1e-9 and abs(x.x-1)<1e-9 and abs(y.x)<1e-9
m = model()
x = m.add_var(name='x', var_type=BINARY)
m += x >= 1
m += x <= 0
m.objective = x
s = m.optimize(max_seconds=5)
results.append({'test':'binary_infeasible','status':s.name,'num_solutions':m.num_solutions})
assert s == OptimizationStatus.INFEASIBLE and m.num_solutions == 0
import mip.cbc
print(json.dumps({'passed':True,'results':results,'python':sys.version,'interpreter':sys.executable,'architecture':platform.machine(),'versions':{k:md.version(k) for k in ['mip','cbcbox','cffi']},'cbc_library':mip.cbc.libfile,'threads':1}), flush=True)
