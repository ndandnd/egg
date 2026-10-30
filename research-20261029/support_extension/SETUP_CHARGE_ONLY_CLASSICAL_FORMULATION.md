# Classical charge-only duty formulation with per-action setup

Analytical formulation only. No numerical work, commands, imports, data, compilation, hashes, solver, commits or agents. This is an ordinary duty/set-partitioning MILP with continuous charging, not a new algorithm or hardness result. It shows why failure of the minimum-r statistic does NOT imply that exponential matching enumeration or a learning method is necessary.

## Model and exhaustive polynomial duty set

There are n simultaneous A services, n later simultaneous B services, a fixed allowed successor graph, common B>0, service energies0<a_i,b_j<=B, full initial/final SOC and zero reserve/other draw. Every used bus serves at least one service; counted idle buses are outside this stated class. All used buses are available throughout a unit early window between batches and a unit terminal window after B. Early charging is CHARGE-ONLY, at common accepted grid power K_c>0 and efficiency alpha in(0,1]. Each nonzero bus-specific early action has setup time tau>0 occupying the same connector with no energy exchange. Terminal charging is charge-only with efficiency alpha and total grid power/budget H>=0, accepted by every bus, with no terminal setup. There is no taper, switching/task overhead beyond this setup, minimum session, degradation, or cost depending on within-window action timing. All resource capacities are shared, not multiplied by fleet size.

Candidate duties D contain one (i,j) for every allowed pair, one (i,*) for every standalone A, and one (*,j) for every standalone B. Thus |D|<=n²+2n. A used bus cannot serve two simultaneous services in either batch, so these duties exhaust all service-assigned plans. For duty d define A_d and B_d as its respective service energies, using0 for an absent service; s_d=A_d+B_d. Initial early SOC is B−A_d; post-early demand is B_d. Monetary duty cost is one common used-bus fee f>=0 (or a separately specified fixed duty cost).

## Variables and constraints

For every duty d use y_d in{0,1} (activate one bus on that duty), z_d in{0,1} (permit/charge the early setup), q_d>=0 (early GRID purchase), and t_d>=0 (terminal GRID purchase). Impose:

1. Exact service cover:

       y_(i,*) + sum_j:(i,j)allowed y_(i,j) = 1  for every A_i;
       y_(*,j) + sum_i:(i,j)allowed y_(i,j) = 1  for every B_j.

2. Activation, early capacity and post-service reserve:

       0<=z_d<=y_d,
       alpha*q_d <= A_d*z_d,
       alpha*q_d >= (s_d−B)*y_d.

   Together with q_d>=0 these enforce the correct active-duty interval

       [s_d−B]_+/alpha <= q_d <= A_d/alpha.

   Inactive duties have zero q; B-only duties have A_d=0 and cannot charge early. An optional additional alpha*q_d<=A_d*y_d is redundant but harmless.

3. Exact full terminal refill and finite terminal bounds:

       alpha*(q_d+t_d)=s_d*y_d,
       0<=alpha*t_d<=B*y_d.

   The equality repays every service's initial-inventory consumption. The lower t bound prevents overfilling; its upper bound agrees with feasible post-service SOC and also forces inactive terminal charge to zero.

4. Shared windows:

       sum_d q_d/K_c + tau*sum_d z_d <=1,
       sum_d t_d <=H.

   The terminal inequality handles H=0 without division. An optional fleet cap is sum y_d<=N_max; otherwise exact coverage already gives n<=sum y_d<=2n. The matching cardinality is sum paired y, and total fleet is2n minus that cardinality. No matching bank, initial seed or full-plan enumeration is needed.

The setup indicator need not enforce the strict biconditional z_d=1 iff q_d>0. A solution may have z_d=1,q_d=0, thereby OVERCOUNTING setup time; omitting that zero-energy action only frees connector time and preserves all projected quantities. Conversely every positive q forces z=1. This is an exact formulation for projected energy/cost decisions, not a claim that z counts actual nonzero actions in every representation. An objective rewarding fictitious setup indicators, or asking their literal exact count, is outside this formulation; strict positivity cannot simply be inserted as a closed MILP constraint without a physical minimum action size.

## Objectives and exactness

Define E=sum q_d, L=sum t_d, c=f*sum y_d, optionally adding common affine purchase/terminal wear to c. Any affine query in these aggregate coordinates is a MILP objective, including arbitrary fixed energy-price signs. A convex quadratic supply objective c+F(E,L) gives a standard convex MIQP; other convex F gives its corresponding mixed-integer convex formulation. This is a PHYSICAL planning/response formulation. Its continuous relaxation is not automatically the complete-plan convex hull or a hull-price certificate.

**Physical schedule to formulation.** Each actual service-assigned bus induces one candidate duty, and exact service cover selects it once. Under charge-only early operation, all actions on that bus monotonically increase SOC and can be merged into ONE action with total q_d: there is no intervening service, draw or availability change in the common window. The endpoint inequalities are necessary. Merging reduces or preserves setup count and preserves transfer duration. Summing required time gives the modeled early inequality. Terminal refill is exactly the displayed equality and its total budget. Set z=1 exactly for duties with positive q. Thus every physical load/cost point has a feasible integer model representative, without pretending its literal split-action timetable is preserved.

**Formulation to schedule.** Activate one bus per selected duty. After its A service (if any) its SOC is B−A_d. If q_d>0, execute one setup then charge that amount at K_c; serialize these duties in any order. Their total time is at most the modeled occupancy, even when z overcounts a zero action. Early capacity follows from alpha*q_d<=A_d; after B, SOC is B−s_d+alpha*q_d>=0. Consumption is nonnegative, so service prefixes also respect inventory. Refill t_d at the terminal connector serially. Its equality restores exactly B and its nonnegative bounded amount starts from a feasible SOC. The shared terminal budget guarantees a schedule in the unit terminal window; if H=0 every t is zero. All services, resources, fleet fees and aggregate quantities are realized. Therefore both projected feasible sets coincide and every permitted aggregate objective has the same physical optimum/infimum.

## Scope and interpretation

The binary formulation has O(n²) duties/variables/constraints, rather than one object per complete matching. It says nothing about polynomial solution time: setup and assignment coupling can still make the MIP difficult, and no complexity classification is proved here. Nor is a native solver's objective or MIP bound an independently checked exact certificate merely because the model is exact. The setup counterexample establishes loss of a particular sufficient statistic, not hardness, an exponential-method necessity, an ML opportunity or an operational finding.

The compact duty set depends on only two simultaneous service batches and common complete windows; general many-service paths or time-varying access need a different formulation. V2G invalidates the simple charge-only session merge and requires additional action/state modeling. Bus-dependent efficiencies, session-dependent monetary cost, setup overlap, minimum duration and nonlinear SOC/depth wear are not silently included. A common compulsory post-early task can be represented by adding its energy to paired s_d and checking post-early capacity, but that is a separately explicit model extension. No public-data or prior certificate transfer follows from this analytical baseline.
