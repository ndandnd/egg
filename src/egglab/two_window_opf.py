"""Parameterized joint energy/branch-flow master for two constant-power depot windows.

All chronological periods retain their own nodal P/Q, prices, voltage, current and
optional local generation. Only the depot MW is common within each window. The
network follows solve_radial's sending-side tap and pi-shunt conventions.
"""
from __future__ import annotations

import cvxpy as cp
import numpy as np
from scipy import sparse

from .radial_opf import _index, _vector, conic_options


def cone_screen(p_mw, q_mvar, sending_vm2, current_sq_pu, base_mva):
    """Absolute plus relative tolerance on EACH series branch, on physical MVA²."""
    power = np.asarray(p_mw)**2 + np.asarray(q_mvar)**2
    product = np.asarray(sending_vm2) * current_sq_pu * base_mva**2
    discrepancy = np.abs(power - product)
    threshold = 1e-5 + 1e-5*np.maximum(np.abs(power), np.abs(product))
    ratio = discrepancy / threshold
    return dict(cone_max_mva2=float(np.max(discrepancy, initial=0.)),
                cone_max_mixed_ratio=float(np.max(ratio, initial=0.)),
                cone_worst_edge=int(np.argmax(ratio)) if ratio.size else None,
                cone_failed_edges=np.flatnonzero(~(ratio <= 1.)).tolist(),
                cone_abs_tol_mva2=1e-5, cone_rel_tol=1e-5)


def _row_soc(left, real, imag, right):
    """Elementwise 2x2 Hermitian PSD cone on arrays of time x branch."""
    def vec(a):
        return cp.vec(a, order="F")
    return cp.SOC(vec(left + right),
                  cp.vstack([2*vec(real), 2*vec(imag), vec(left - right)]))


def _native_bound(problem, solver):
    """Numerical backend dual objective/bound for this zero-offset formulation."""
    if solver == "CLARABEL":
        native = problem._solver_cache.get("CLARABEL")
        if hasattr(native,"get_solution"):
            native = native.get_solution()
        bound = getattr(native,"obj_val_dual",None)
    else:
        model = problem.solver_stats.extra_stats
        try:
            bound = model.ObjBound
        except (AttributeError, RuntimeError):
            bound = None
    return float(bound) if bound is not None and np.isfinite(bound) else None


class TwoWindowOPF:
    """Repeated native-network solves on a fixed feeder, depot and window partition.

    network is the original solver mapping. p_mw/q_mvar in that mapping are
    superseded by the explicit period-by-bus backgrounds. open_end_leaves must
    be set explicitly. backup=(bus, MW capacity, EUR/MWh) is physical supply.
    Fee lines passed to optimize are (EUR/kWh slope, EUR intercept).
    """
    def __init__(self, network, depot, background_mw, reactive_mvar, hours, upstream_prices,
                 total_kwh, *, window_ids=None, backup=None, solver="CLARABEL"):
        raw = dict(network)
        total_kwh = float(total_kwh)
        raw.pop("p_mw", None)
        raw.pop("q_mvar", None)
        self.parent = np.asarray([_index(i) for i in raw.pop("parent")], dtype=int)
        edges = len(self.parent)
        n = edges + 1
        self.n = n
        if not edges or np.any(self.parent < 0) or np.any(self.parent > np.arange(edges)):
            raise ValueError("expected a parent-before-child radial feeder with at least one edge")
        def read(key, default, size=edges, allow_inf=False):
            arg = raw.pop(key, default)
            if arg is None and allow_inf:
                arg = np.inf
            return _vector(arg, size, key, allow_scalar=True, allow_infinity=allow_inf)
        self.r = read("r", None)
        self.x = read("x", None)
        self.tap = read("tap_ratio", 1.)
        self.gf, self.bf = read("g_from_pu", 0.), read("b_from_pu", 0.)
        self.gt, self.bt = read("g_to_pu", 0.), read("b_to_pu", 0.)
        self.gs = read("g_bus_pu", 0., n).copy()
        self.bs = read("b_bus_pu", 0., n).copy()
        np.add.at(self.gs, self.parent, self.gf/self.tap**2)
        np.add.at(self.bs, self.parent, self.bf/self.tap**2)
        self.gs[1:] += self.gt
        self.bs[1:] += self.bt
        self.low, self.high = read("vmin", .9, n), read("vmax", 1.1, n)
        self.imax, self.imax_f, self.imax_t = (read(k, np.inf, allow_inf=True)
            for k in ("imax_pu", "imax_from_pu", "imax_to_pu"))
        self.base = float(raw.pop("base_mva", 1.))
        self.slack = float(raw.pop("slack_vm_pu", 1.))
        self.curvature = float(raw.pop("curvature", 0.))
        self.root_cap = raw.pop("root_import_cap_mw", None)
        backup_setting = raw.pop("backup", None)
        if backup is not None and backup_setting is not None:
            raise ValueError("supply backup once")
        self.backup = backup if backup is not None else backup_setting
        marked = tuple(_index(i) for i in raw.pop("open_end_leaves", ()))
        self.marked = np.array(sorted(set(marked)), dtype=int)
        if raw:
            raise ValueError(f"unsupported network keys: {sorted(raw)}")
        if (np.any(self.r < 0) or np.any(self.x < 0) or np.any(self.tap <= 0) or
                np.any(self.low <= 0) or np.any(self.low > self.high) or
                min(np.min(self.imax), np.min(self.imax_f), np.min(self.imax_t)) < 0 or
                not np.all(np.isfinite([self.base, self.slack, self.curvature, total_kwh])) or
                min(self.base, self.slack) <= 0 or min(self.curvature, total_kwh) < 0 or
                (self.root_cap is not None and not np.isfinite(self.root_cap))):
            raise ValueError("invalid network, cost or energy bounds")
        self.depot = _index(depot)
        if (len(marked) != len(self.marked) or any(not 0 < j < n or j in self.parent for j in marked)
                or not 0 <= self.depot < n or self.depot in marked):
            raise ValueError("invalid open-end leaves or depot bus")
        if self.backup is not None:
            bus, capacity, cost = self.backup
            bus = _index(bus)
            if (not 0 <= bus < n or bus in marked or capacity < 0 or
                    not np.isfinite([capacity, cost]).all()):
                raise ValueError("invalid backup generator")
            self.backup = (bus, float(capacity), float(cost))
        self.hours = np.asarray(hours, dtype=float)
        self.T = len(self.hours)
        if self.hours.shape != (self.T,) or self.T < 2 or not np.isfinite(self.hours).all() or np.any(self.hours <= 0):
            raise ValueError("hours must be positive finite interval lengths")
        if window_ids is None:
            if self.T % 2:
                raise ValueError("unequal windows require explicit window_ids")
            window_ids = [0]*(self.T//2) + [1]*(self.T//2)
        self.ids = np.asarray([_index(i) for i in window_ids], dtype=int)
        if self.ids.shape != (self.T,) or set(self.ids) != {0, 1} or np.any(np.diff(self.ids)<0):
            raise ValueError("window_ids must assign each period to chronological window 0 or 1")
        self.duration = np.bincount(self.ids, weights=self.hours, minlength=2)
        self.total = float(total_kwh)
        self.solver = solver.upper()
        if self.solver not in ("CLARABEL", "GUROBI"):
            raise ValueError("choose CLARABEL or GUROBI")
        self.bp = cp.Parameter((self.T, n))
        self.bq = cp.Parameter((self.T, n))
        self.price = cp.Parameter(self.T)
        self.set_market(background_mw, reactive_mvar, upstream_prices)
        self._models = {}
        self._build()

    def set_market(self, background_mw, reactive_mvar, upstream_prices):
        p, q = np.asarray(background_mw, dtype=float), np.asarray(reactive_mvar, dtype=float)
        price = _vector(upstream_prices, self.T, "upstream_prices", allow_scalar=True)
        if (p.shape != (self.T, self.n) or q.shape != p.shape or not np.isfinite(p).all()
                or not np.isfinite(q).all() or np.any(p[:, self.marked]) or np.any(q[:, self.marked])):
            raise ValueError("invalid market shapes, values, or injection at a marked open end")
        self.bp.value, self.bq.value, self.price.value = p, q, price

    def _build(self):
        T, n = self.T, self.n
        edges = np.arange(n-1)
        self.out_inc = sparse.csc_matrix((np.ones(n-1), (edges, self.parent)), shape=(n-1,n))
        # Explicitly tile data rows. CVXPY 1.6.0 can infer the NumPy
        # broadcasting shape but build an invalid sparse canonical matrix.
        def grid(row):
            return np.tile(row,(T,1))
        def mat(left, right):
            if len(left.shape)==2 and isinstance(right,np.ndarray) and right.ndim==1:
                right = grid(right)
            return cp.multiply(left,right)
        self.p, self.q, self.v = (cp.Variable((T,n), name=s) for s in ("P", "Q", "v"))
        p, q, v = self.p[:,1:], self.q[:,1:], self.v
        marked = np.isin(edges+1,self.marked)
        self.ideal = (self.r == 0) & (self.x == 0) & ~marked
        lifted = ~(self.ideal | marked)
        # Passive ends use I = (y_bus+y_to) V_child identically. Ideal
        # connectors use true terminal power in limits and no free lift.
        ell = mat(v[:,1:], marked*(self.gs[1:]**2+self.bs[1:]**2))
        if np.any(lifted):
            size = int(sum(lifted))
            scatter = sparse.csc_matrix((np.ones(size),(np.arange(size),edges[lifted])),
                                        shape=(size,n-1))
            ell += cp.Variable((T,size), nonneg=True, name="series_i2") @ scatter
        self.ell = ell
        w = mat(v[:,self.parent], 1/self.tap**2)
        vf, vt = v[:,self.parent], v[:,1:]
        self.energy = cp.Variable(2, name="depot_MWh")
        self.load = mat(self.energy[self.ids], 1/self.duration[self.ids])
        zero = np.zeros((T,1))
        def injection(series, bus):
            basis = np.zeros((1,n))
            basis[0,bus] = 1.
            return cp.reshape(series, (T,1), order="F") @ basis
        self.gen = cp.Variable(T, nonneg=True, name="backup_MW") if self.backup else None
        req_p = self.bp/self.base + mat(v,self.gs) + p @ self.out_inc + injection(self.load,self.depot)/self.base
        req_q = self.bq/self.base - mat(v,self.bs) + q @ self.out_inc
        cons = [v[:,0] == self.slack**2, v >= grid(self.low**2), v <= grid(self.high**2)]
        if self.gen is not None:
            req_p -= injection(self.gen,self.backup[0])/self.base
            cons.append(self.gen <= self.backup[1])
        imp = self.p[:,0]*self.base
        if self.root_cap is not None:
            cons.append(imp <= self.root_cap)
        self.bal_p = req_p + cp.hstack([zero, mat(ell,self.r)]) == self.p
        self.bal_q = req_q + cp.hstack([zero, mat(ell,self.x)]) == self.q
        cons.extend([self.bal_p, self.bal_q, vt == w-2*(mat(p,self.r)+mat(q,self.x))+
                     mat(ell,self.r**2+self.x**2)])
        if np.any(lifted):
            cons.append(_row_soc(w[:,lifted],p[:,lifted],q[:,lifted],ell[:,lifted]))
        ellf = mat(ell + 2*(mat(p,self.gf)-mat(q,self.bf)) + mat(w,self.gf**2+self.bf**2),
                   1/self.tap**2)
        ellt = ell - 2*(mat(p-mat(ell,self.r),self.gt)-mat(q-mat(ell,self.x),self.bt)) + mat(vt,self.gt**2+self.bt**2)
        pf, qf = p + mat(w,self.gf), q - mat(w,self.bf)
        pt, qt = -p + mat(vt,self.gt), -q - mat(vt,self.bt)
        for rating, i2, vend, pend, qend in ((self.imax, ell, w, p, q),
                (self.imax_f, ellf, vf, pf, qf), (self.imax_t, ellt, vt, pt, qt)):
            bound = np.isfinite(rating)
            standard, ideal = bound & ~self.ideal, bound & self.ideal
            if standard.any():
                cons.append(i2[:,standard] <= grid(rating[standard]**2))
            if ideal.any():
                rhs = np.broadcast_to(rating[ideal]**2, (T,int(sum(ideal))))
                cons.append(_row_soc(vend[:,ideal],pend[:,ideal],qend[:,ideal],rhs))
        hourly = mat(self.price, imp)
        if self.curvature:
            hourly += self.curvature/2 * cp.square(imp)
        if self.backup:
            hourly += self.backup[2]*self.gen
        self.grid = self.hours @ hourly
        self.constraints = cons

    def fixed(self, early_kwh):
        return self.fixed_loads([early_kwh,self.total-float(early_kwh)])

    def fixed_loads(self, fleet_kwh):
        # Independent changes to either window support directional price checks.
        loads = _vector(fleet_kwh, 2, "fleet_kwh")
        if "fixed" not in self._models:
            target = cp.Parameter(2)
            self._models["fixed"] = cp.Problem(cp.Minimize(self.grid),self.constraints+
                                               [self.energy == target]), target
        problem,target = self._models["fixed"]
        target.value = loads/1000
        return self._solve(problem, None)

    def optimize(self, lo_kwh, hi_kwh, fee_lines=()):
        lo, hi = float(lo_kwh), float(hi_kwh)
        if not np.isfinite([lo,hi]).all() or not 0 <= lo <= hi <= self.total:
            raise ValueError("layer bounds must be within [0,total_kwh]")
        lines = np.asarray(tuple(fee_lines),dtype=float)
        k = len(lines)
        if k and (lines.shape != (k,2) or not np.isfinite(lines).all()):
            raise ValueError("fee lines require finite slopes and intercepts")
        if k not in self._models:
            bounds = cp.Parameter(2)
            cons = self.constraints + [self.energy[0]>=bounds[0], self.energy[0]<=bounds[1],
                                       cp.sum(self.energy)==self.total/1000]
            slope = intercept = fee = None
            if k:
                slope,intercept,fee = cp.Parameter(k),cp.Parameter(k),cp.Variable()
                cons.append(fee >= slope*self.energy[0]+intercept)
            self._models[k] = cp.Problem(cp.Minimize(self.grid + (fee if k else 0.)),cons), bounds,slope,intercept
        problem,bounds,slope,intercept = self._models[k]
        bounds.value = [lo/1000,hi/1000]
        if k:
            slope.value,intercept.value = 1000*lines[:,0],lines[:,1]
        return self._solve(problem, (lo,hi,lines))

    def _solve(self, problem, layer):
        out = dict(status="solver_error", solver=self.solver, physical_pass=False, early_kwh=None,
                   fleet_kwh=None, fee_eur=None, grid_cost=None, objective=None,
                   native_bound=None, native_bound_scope="numerical_solver_value_only",
                   depot_price_per_mwh=None, periods=[])
        try:
            # CVXPY 1.6.0's native Eigen canonicalizer crashes on a replicated
            # sparse time/bus product. Use its SciPy implementation explicitly.
            problem.solve(solver=self.solver, warm_start=True, canon_backend="SCIPY",
                          **conic_options(self.solver))
        except Exception as exc:
            # CVXPY backends may raise native license or numerical exceptions.
            return dict(out, error=f"{type(exc).__name__}: {exc}")
        out["status"] = problem.status
        if problem.status not in (cp.OPTIMAL,cp.OPTIMAL_INACCURATE):
            return out
        loads = 1000*np.asarray(self.energy.value)
        if not np.isfinite(loads).all() or not np.isfinite(problem.value):
            return dict(out,error="nonfinite primal or objective")
        fee, fee_error, energy_error = 0.,0.,0.
        if layer is not None:
            lo,hi,lines = layer
            if len(lines):
                fee=float(np.max(lines[:,0]*loads[0]+lines[:,1]))
            energy_error=max(0.,lo-loads[0],loads[0]-hi,abs(sum(loads)-self.total))
            fee_error=abs(float(problem.value)-float(self.grid.value)-fee)
        else:
            target=self._models["fixed"][1].value*1000
            energy_error=float(np.max(np.abs(loads-target)))
        periods=[self._recover(k,problem.status) for k in range(self.T)]
        duals = self.bal_p.dual_value
        prices = None
        if duals is not None and np.isfinite(duals[:,self.depot]).all():
            prices=(np.bincount(self.ids,weights=duals[:,self.depot]/self.base,minlength=2)
                    /self.duration).tolist()
        return dict(out, physical_pass=problem.status==cp.OPTIMAL and energy_error<=1e-5 and
                    fee_error<=1e-5 and all(p["physical_pass"] for p in periods),
                    early_kwh=float(loads[0]), fleet_kwh=loads.tolist(), periods=periods,
                    objective=float(problem.value), fee_eur=fee, grid_cost=float(self.grid.value),
                    native_bound=_native_bound(problem,self.solver), energy_residual_kwh=float(energy_error),
                    fee_residual_eur=fee_error, depot_price_per_mwh=prices)

    def _recover(self, k, status):
        base, up = self.base,self.parent
        ps, qs, v = self.p.value[k],self.q.value[k],self.v.value[k]
        if not np.isfinite([ps,qs,v]).all() or np.any(v<=0):
            return dict(physical_pass=False,error="invalid voltage or power")
        p,q = ps[1:],qs[1:]
        ell = self.ell.value[k].copy()
        w = v[up]/self.tap**2
        ell[self.ideal]=((p**2+q**2)/w)[self.ideal]
        lp,lq=self.r*ell,self.x*ell
        pf,qf=p+self.gf*w,q-self.bf*w
        pt,qt=-p+lp+self.gt*v[1:],-q+lq-self.bt*v[1:]
        ef=(ell+2*(self.gf*p-self.bf*q)+(self.gf**2+self.bf**2)*w)/self.tap**2
        et=ell-2*(self.gt*(p-lp)-self.bt*(q-lq))+(self.gt**2+self.bt**2)*v[1:]
        vf,vt=np.sqrt(np.maximum(ef,0.)),np.sqrt(np.maximum(et,0.))
        vm=np.sqrt(v)
        load=float(self.load.value[k])
        gen=0. if self.gen is None else float(self.gen.value[k])
        dp=self.bp.value[k]/base+self.gs*v + np.asarray(p@self.out_inc).ravel()-ps
        dq=self.bq.value[k]/base-self.bs*v + np.asarray(q@self.out_inc).ravel()-qs
        dp[1:]+=lp
        dq[1:]+=lq
        dp[self.depot]+=load/base
        if self.backup:
            dp[self.backup[0]]-=gen/base
        balance=max(np.max(abs(dp)),np.max(abs(dq)))
        voltage=max(abs(v[0]-self.slack**2),np.max(abs(v[1:]-w+2*(self.r*p+self.x*q)-self.r*lp-self.x*lq)))
        limit=max(0.,np.max(self.low-vm),np.max(vm-self.high),np.max(-ell),np.max(-ef),np.max(-et),
                  np.max(vf-self.imax_f),np.max(vt-self.imax_t),np.max(np.sqrt(np.maximum(ell,0))-self.imax))
        if self.backup:
            limit=max(limit,-gen/base,(gen-self.backup[1])/base)
        if self.root_cap is not None:
            limit=max(limit,ps[0]-self.root_cap/base)
        mixed=cone_screen(p*base,q*base,w,ell,base)
        cone_abs=np.abs(p**2+q**2-w*ell)
        cone_rel=cone_abs/np.maximum(w*ell,1e-8)
        phys=bool(status==cp.OPTIMAL and max(limit,voltage,balance)<=1e-7 and
                  mixed["cone_max_mixed_ratio"]<=1.)
        include=np.ones(self.n,dtype=bool)
        include[np.r_[0,self.marked]]=False
        vlow=np.flatnonzero(include&(vm-self.low<=1e-5)).tolist()
        vhigh=np.flatnonzero(include&(self.high-vm<=1e-5)).tolist()
        def binding(current,cap):
            return np.flatnonzero(include[1:]&np.isfinite(cap)&(current>=cap*(1-1e-4))).tolist()
        def dlmp(row):
            if row.dual_value is None:
                return None
            return [None if j in self.marked else float(value)/(self.hours[k]*base)
                    for j,value in enumerate(row.dual_value[k])]
        obj=self.hours[k]*(self.price.value[k]*ps[0]*base+self.curvature*(ps[0]*base)**2/2+
                           (self.backup[2]*gen if self.backup else 0.))
        return dict(status=status,physical_pass=phys,**mixed,objective=float(obj),
                    depot_mw=load,backup_mw=gen,import_mw=float(ps[0]*base),import_mvar=float(qs[0]*base),
                    voltage_pu=vm.tolist(),p_send_mw=(pf*base).tolist(),q_send_mvar=(qf*base).tolist(),
                    p_to_mw=(pt*base).tolist(),q_to_mvar=(qt*base).tolist(),
                    p_series_send_mw=(p*base).tolist(),q_series_send_mvar=(q*base).tolist(),
                    current_sq_pu=ell.tolist(),current_from_pu=vf.tolist(),current_to_pu=vt.tolist(),
                    dlmp=dlmp(self.bal_p),dlmp_q=dlmp(self.bal_q),series_loss_mw=float(lp.sum()*base),
                    shunt_loss_mw=float(self.gs@v*base),loss_mw=float((self.gs@v+sum(lp))*base),
                    cone_abs=float(np.max(cone_abs)),cone_rel=float(np.max(cone_rel)),
                    balance_max_pu=float(balance),voltage_eq_max_pu=float(voltage),
                    limit_violation_max_pu=float(limit), point_ac_residuals_pass=bool(status==cp.OPTIMAL and
                    max(limit,voltage,balance,max(cone_abs))<=1e-7 and max(cone_rel)<=1e-5),
                    binding_vmin=vlow,binding_vmax=vhigh,binding_from=binding(vf,self.imax_f),
                    binding_to=binding(vt,self.imax_t))
