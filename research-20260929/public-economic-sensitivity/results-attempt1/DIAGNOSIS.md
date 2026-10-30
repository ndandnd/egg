# Why the eight public intervals stayed wide

The native physical planner received a 180 s coordinator / 160 s phase
budget in each cell. It performed 19 tangent-MIP rounds across eight cells:
two rounds in five cells and three in three. Every final round ended with a
`FEASIBLE` incumbent after its native time allowance, while earlier rounds
were `OPTIMAL` for their *piecewise-linear tangent* objectives. The eight
planner children cost 1469.95 s, of which 1411.77 s is recorded native solver
time. The first tangent is just the 0.20 linear intercept. At the best
returned incumbent, the true quadratic objective exceeds its replayed
tangent envelope by roughly 106–282 units. All saved native epigraph slack
and raw-to-replayed charging-objective correction scalars are essentially
zero. Thus the wide physical interval is primarily an incomplete nonlinear
tangent/MIP certificate, not an observed charge-extraction error. A larger
round-count cap would not help unless the expensive native rounds can finish.

The cold hull issued 24 pricing requests and 24 restricted-master calls
across eight cells (two to four per cell), below the cap of 16 pricing calls
and 64 master calls. All eight stops state `pricing reserve prevented a new
request` near the 180 s wall. The numerical-QP proposal totals only 6.29 s;
its exact replay totals 3.19 s. Pairwise simplex polishing took zero steps
and zero recorded seconds; projected rational sizes were 262–273 bits versus
8192 allowed. The 1402.01 s aggregate hull child time minus those QP/replay
counter totals is **not a measured pricing time**: it includes route-pricing
MIPs, model construction, column validation, recording and other unbroken-out
work. Still, raising the bit or restricted-master call caps would miss the
observed stop. Response children cost 357.64 s, including 318.70 s recorded
native solver time; five of their eight one-call MIPs remained bounded.

The replayed hull pool also contains individual **physical fleets**. A
separate exact-binary-arithmetic evaluation of each saved column's operating
cost plus the declared quadratic supply (the author-side hull assessment
already replayed each column) gives:

| Depot | Fee | Curvature | Best individual pool fleet cost | Planner native upper | Guarded upper improvement |
| --- | ---: | ---: | ---: | ---: | ---: |
| 15 | 100 | 1 | 504.643749 | 514.526312 | 9.882562 |
| 16 | 100 | 1 | 530.658906 | 530.658907 | ~0 |
| 15 | 40 | 1 | 414.782221 | 424.066238 | 9.284015 |
| 16 | 40 | 1 | 457.093021 | 440.689057 | 0 |
| 15 | 20 | 1 | 407.947218 | 366.859047 | 0 |
| 16 | 20 | 1 | 377.231311 | 377.231312 | ~0 |
| 15 | 40 | 2 | 579.857606 | 570.123141 | 0 |
| 16 | 40 | 2 | 561.488191 | 568.144846 | 6.656655 |

The improvement column includes the native 1e-6 objective guard and treats
gains no larger than that guard as zero; all pool fleets have two buses. The
[reproducible replay](evaluate_pool.py) and [eight-candidate receipt](pool_candidates.json)
verify each saved column's hash, frozen case/market/state, physical resource
replay, stored projection and objective, with the sealed manifest and
on-time hull stage as prerequisites. Those gates **do suffice** to admit each
best individual fleet as a separate, tolerance-qualified *native* physical
upper; they do not establish exact feasibility for the ideal stored-input
model. No convex mixture is treated as a physical fleet. The three material
post hoc uppers are 504.643750 (depot 15, f100), 414.782222 (depot 15,
f40), and 561.488192 (depot 16, f40/curvature2). Their native gap upper caps
become 96.110615, 126.249088 and 258.333062, respectively. The primary
[RESULTS.md](RESULTS.md) table retains the originally reported stage
enclosures; every post hoc gap interval still contains zero.

The own-price regret of the bounded planner incumbents ranges from about
204 to 563, but does not isolate an optimal-dispatch incentive effect. For a
replayed incumbent $x$ and its own gradient price $p_x$, the exact
identity is

\[
r(x)=[J(x)-D]+[D-CH]+[CH-(V(p_x)-F^*(p_x))].
\]

The first term can be large here because the planner enclosures are wide;
neither the gap nor the dual-price term is identified. The observed two-bus
planner, response and pool plans likewise do not establish two-bus
optimality at low fee.

**Next bounded target.** The saved pool's best whole-fleet upper is now
admitted separately with no new optimization. The next development package
should be one proof-driven certificate pilot, not a time/cap sweep: validate the
[published cardinality-energy inequality](../../charging-availability-bound/PROOF.md)
on the exact public input,

\[
E\ge E_s,\qquad E\ge E_2-(E_2-E_s)(k-2)\quad(k\ge2),
\]

against the actual native energy and used-bus variables and tolerances;
check whether it is already implied by the compact model's aggregate
energy-balance rows and whether it improves the **root relaxation** in the
two diagnostic cells (depot 15, f=100, curvature 1; depot 16, f=40,
curvature 2). Only a demonstrated nonredundant root improvement would justify
a bounded matched planner/pricing ablation. The availability floor itself is
reporting-only and must not be inserted as a native lower certificate.
Charging correction was zero and current exact pool polishing took no steps;
neither measured quantity supports a polishing-cap expansion. A new
route-fixed quadratic charging refinement might improve a physical upper,
but it would need a separately specified convex solve and physical replay,
not an assumption that an existing pool-polish routine performs it.
