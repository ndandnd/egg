# Review: cardinality-gated path-cover flow relaxation

27 September 2026. **PASS on the mathematical reduction and primal/dual
certificate.** This review covers the prospective design only; no flow
algorithm, public calculation, or optimizer was run.

For a DAG on the 37 services, a matching with (m) allowed real edges has
indegree and outdegree at most one at every service. Its components are paths,
so it has exactly (37-m) paths. A physical schedule using (K) nonempty bus
paths induces (37-K) consecutive real edges. Given the separately reviewed
one-bus obstruction, the exact stored-input structural argument gives
(K\geq2), hence (m\leq35). The gate therefore retains every such physical
path cover while possibly discarding cheaper relaxed covers. Minimization over
this restricted relaxation remains a valid lower bound for the stated ideal
full-recharge flat-price objective. Replacing parallel alternatives by the
least exact stored-input cost for each ordered service pair is valid because
the relaxation has no other mode-coupling constraints. The baseline and edge
savings agree with `flat_energy_relaxation.path_cover_problem`.

The fixed-flow network implements that set correctly: the 37 unit-capacity
source-to-row arcs are all saturated by flow value 37; each row sends its unit
to either its unmatched arc or one real connection; each successor column has
capacity one; and the gate limits aggregate real edges to 35. The unmatched
flow makes the network feasible even with no real edges. The service-DAG
property rules out cycles, so integral flows decode to path covers. Integer
capacities and supplies with a directed node-arc incidence matrix give an
integral optimal basic flow even for signed rational costs.

The certificate dual is also correct under the convention
`outflow − inflow = b`. With reduced cost
`r_a = c_a − pi_tail + pi_head`, any bounded flow satisfies

`cost = sum_v b_v*pi_v + sum_a r_a*f_a`

and `r_a*f_a >= u_a*min(0,r_a)`. Thus the stated dual expression is a lower
bound. The forward/reverse residual sign checks enforce arcwise attainment of
these minima; primal feasibility plus exact equality of primal and dual
objectives proves optimality. Normalizing `pi_t=0` does not affect the result.
The document should explicitly state this balance-sign convention beside the
supplies so a verifier cannot reverse the potential signs.

One required preflight condition: the independent certificate verifier must
rebuild the network from the frozen source case, rather than trust the
archived arc list and costs. In particular it should independently confirm
every allowed ordered pair, the selected cheapest parallel mode and its exact
cost, all pullout/pullin minima, the baseline, and the gate capacity before
checking flow and potentials. Otherwise a self-consistent certificate for an
omitted or mispriced arc could certify the wrong lower bound. The design's
future independent reconstruction gate points in this direction; make this
source-to-network check explicit in the freeze checklist.

Scope wording is appropriately limited: the exact result is an ideal
stored-input objective lower bound, conditional on the exact one-bus proof and
its graph. The prior two-bus witnesses are tolerance-qualified numerical
replays, not exact feasibility certificates. Report the exact one-bus
obstruction/lower bound of two and the separate two-bus replay references; do
not call their combination an exact minimum-fleet certificate. This flow bound
does not become a native-MILP bound, a physical optimum, or a nonlinear/hull
result.
