# Prospective local quadratic-toy replay

29 September 2026. This protocol is written before this run. It tests the pasted
note's qualitative dual-coordination claim on the existing exact two-service
model, with every charging alternative preserved analytically. No timetable MIP,
training data, cluster allocation or held-out case is used.

- One bus: cost 7, load (10,20); two buses: cost 14, load (x,30-x), x in [0,10].
- Supply F(u)=4u1+(u1^2+u2^2)/10 on u>=0. Supply response is
  s(p)=(5 max(p1-4,0),5 max(p2,0)).
- Initial posted price p1=(6,4), one-bus own marginal price. At each k, compute
  globally exact analytic fleet/supply responses at p_k, then update
  p_(k+1)=max(0,p_k+0.5/sqrt(k)*(fleet_load-supply_load)).
- Two-bus linear tie selects x=0; a tie between bus counts selects one bus.
- Fixed horizon 20,000 iterations, one cheap analytic oracle call per iteration.
  Report all calls; this is not 20,000 timetable solves and proves no runtime
  benefit. No retry or parameter search to reproduce the note's rounded table.
- Log before-update prices, current dual objective, best-so-far dual objective,
  primal supply-demand mismatch, response counts, both unweighted and step-weighted
  averages. Checkpoints 1,100,1000,20000; preserve full numeric trajectory.
- Exact reference: CH=7591/80, p*=(107/20,93/20), one-bus hull weight 27/40.
  Current and best-so-far dual metrics must never be conflated. In particular,
  the pasted price (5.50,4.50) has current dual 92.75, not approximately 94.887.
- α_k=0.5/sqrt(k) is not square summable. Finite traces demonstrate numerical
  behavior only. General last-price/primal convergence claims need separately
  stated assumptions; diminishing steps and convexity alone are not enough for
  every such claim. Plot dual bounds and schedule choices without asserting a
  proof of convergence from a finite run.

Local budget: one serial Python invocation, 20,000 analytic iterations, 30-second
loop ceiling; plots afterward. Preserve a failure receipt if this budget is hit.
