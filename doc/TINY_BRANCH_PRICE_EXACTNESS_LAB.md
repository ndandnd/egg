# Tiny branch-and-price exactness laboratory

Status: **normative spike specification**. The implementation and tests must
conform to this note. This is a tiny-instance correctness laboratory, not a
production solver or an experiment launcher.

Git base: exact `origin/main`
`5b63e725d0fd85cfb0b83f462a612016e7f4321a`.

## 1. Scope and mathematical objects

Let \(\mathcal S\) be the universe of complete, physically feasible fleet
schedules for one instance. A member \(s\in\mathcal S\) includes:

1. an unlabeled path cover of every trip, with a chosen movement kind between
   consecutive trips;
2. continuous charge quantities on the depot-detour dwell arcs; and
3. the resulting load \(e(s)\), operating cost \(c(s)\), and SOC trajectory.

Vehicle indices used inside the MILP are formulation artifacts. They are not
part of schedule identity.

For every trip \(i\), define the following label-invariant structural arcs:

* \((\mathrm{out},i)\): depot pull-out before \(i\);
* \((i,\mathrm{in})\): depot pull-in after \(i\);
* \((i,j,\mathrm{dir})\): direct movement from trip \(i\) to trip \(j\); and
* \((i,j,\mathrm{dep})\): movement from \(i\) to \(j\) through the depot.

For a complete schedule \(s\), \(x_a(s)\in\{0,1\}\) says whether structural
arc \(a\) occurs after summing over all vehicle labels. Exact trip coverage and
per-vehicle flow imply that every trip has exactly one incoming choice
(pull-out or an inter-trip arc) and exactly one outgoing choice (pull-in or an
inter-trip arc). Consequently, the selected aggregate arcs form an unlabeled
path cover and uniquely determine its trip chains and direct/depot kinds.

The only branching objects in this laboratory are these aggregate incidences.
Charging amounts, vehicle labels, generated-column identifiers, and schedule
hashes are not branching objects.

## 2. The root relaxation is exactly A2

The root problem is A2's full complete-fleet-schedule convex-hull master:

\[
\begin{array}{ll}
\min & \displaystyle\sum_{s\in\mathcal S}\lambda_s c(s)
       +\Delta C(L)\\
\text{s.t.} &
       \displaystyle\sum_{s\in\mathcal S}\lambda_s e_t(s)-L_t=0
       \quad\forall t,\\
&      \displaystyle\sum_{s\in\mathcal S}\lambda_s=1,\\
&      \lambda_s\geq0,\quad L_t\geq0.
\end{array}
\]

Here
\(\Delta C(L)=\sum_t[(a_t+b_tU_t)L_t+\tfrac12b_tL_t^2]\).
The schedule universe is the complete physical universe, including all
continuous charging realizations. It is not the finite pool generated so far.

This identity is definitional and operational:

* the clean restricted master has the same link rows, convexity row,
  operating-cost term, and adaptive tangent model as A2;
* root pricing is the same full-fleet taker MILP at prices
  \(p_t=-\pi_t\); and
* with one convexity block, every certified root lower bound is
  \[
  z_{\mathrm{RMP}}^{\mathrm{model}}+
  \min\{0,\underline z_{\mathrm{price}}-\sigma\},
  \]
  using the pricing MILP's certified bound, never its incumbent.

Therefore the laboratory root and a separately run A2 solve differ only by
declared numerical tolerances. The compact vehicle-indexed MILP relaxation is
not the root relaxation.

Setting binary variables on lambdas in a generated root pool is also not an
exact integer problem: a missing complete schedule can improve the incumbent,
and root pricing completeness does not imply that the root pool contains an
optimal schedule for every descendant. This laboratory never uses binary
lambdas as an exactness claim.

## 3. Branching disjunction and partition proof

At a node \(N\), let \(B_N\) be a consistent set of decisions \(x_a=b_a\),
\(b_a\in\{0,1\}\), and let

\[
\mathcal S_N=\{s\in\mathcal S:x_a(s)=b_a\ \forall(a,b_a)\in B_N\}.
\]

The node LP is the same convex-hull master as in Section 2 with
\(\mathcal S\) replaced by \(\mathcal S_N\). Given an optimal node mixture,
compute
\[
\bar x_a=\sum_{s\in\mathcal S_N}\lambda_s x_a(s).
\]

If \(0<\bar x_a<1\), create children

\[
B_{N0}=B_N\cup\{x_a=0\},\qquad
B_{N1}=B_N\cup\{x_a=1\}.
\]

For every complete schedule, \(x_a(s)\) is binary. Hence every
\(s\in\mathcal S_N\) belongs to exactly one child universe:

\[
\mathcal S_N=\mathcal S_{N0}\mathbin{\dot\cup}\mathcal S_{N1}.
\]

The current fractional mixture satisfies neither child equality, so the split
removes the current fractional structural point while preserving every
integer schedule exactly once. Repeating the split is finite because the
structural arc set is finite and an already fixed arc is never selected
again.

Branch selection is deterministic: among unfixed fractional aggregate arcs,
maximize \(\min(\bar x_a,1-\bar x_a)\), then use canonical arc order to break
ties. Numerical integrality and support tolerances are recorded in the resume
identity.

## 4. Restrictions belong inside the full-fleet oracle

The vehicle-indexed oracle already has binary variables \(o_{vi}\), \(z_{vi}\),
\(x^{\mathrm{dir}}_{vij}\), and \(x^{\mathrm{dep}}_{vij}\). Every branch
decision is imposed on every feasibility, seed, and pricing solve as:

\[
\begin{array}{rcl}
\sum_v o_{vi}&=&b_{(\mathrm{out},i)},\\
\sum_v z_{vi}&=&b_{(i,\mathrm{in})},\\
\sum_v x^{\mathrm{dir}}_{vij}&=&b_{(i,j,\mathrm{dir})},\\
\sum_v x^{\mathrm{dep}}_{vij}&=&b_{(i,j,\mathrm{dep})}.
\end{array}
\]

Exact coverage bounds each aggregate by one, so these equalities implement
the schedule-universe restriction exactly. They are label invariant and do
not choose a vehicle.

Post-filtering a generated pool is invalid: it can falsely declare a child
infeasible or optimal while an ungenerated eligible schedule exists. Child
pricing must optimize over the full restricted fleet MILP. A child with no
seed schedule is fathomed only when that restricted MILP returns certified
`INFEASIBLE`; absence of an incumbent, timeout, or an empty filtered pool is
not an infeasibility certificate.

Gurobi solves node masters and full-fleet MILP oracles. `gurobipy` is an
optional dependency for this laboratory and is deliberately absent from the
repository-wide requirements: install it separately to run these tests.
CBC-only installs must still import and collect the rest of the repository.
The tree, branching, queue, bounds, pruning, checkpointing, and replay are
external Python logic; no Gurobi branch-and-price callback or solver-managed
tree is used.

## 5. Binding tolerance ledger

One operand-scaled policy governs every numerical comparison:

\[
\tau_{\mathrm{obj}}(v)=10^{-8}+10^{-9}\max(1,\max_i|v_i|).
\]

The serialized ledger is binding; a run rejects identity changes on resume.

| Component | Declared limit | Propagation rule |
|---|---:|---|
| Master tangent/PWL | \(10^{-4}\) objective units | record actual true-minus-model slack and add it to the node lower-bound allowance |
| Solver objective numerics | operand-scaled formula above | subtract from solver-attested lower bounds |
| Pricing MIP gap | \(10^{-9}\) relative | retain the Gurobi bound and its scaled objective allowance |
| Integrality | \(10^{-8}\) | branch outside the integral band; account for any omitted support in leaf conversion |
| Master support | \(10^{-9}\) | record dropped lambda weight plus resulting load/objective residual |
| Physical-load reconstruction | \(10^{-4}\) kWh policy cap | propagate \(\sum_t |p_t|\,|L_t^{raw}-L_t^{physical}|\) |
| Charge extraction | \(0\) kWh | serialize every positive solved charge; dropping positive charge is fatal |
| SOC/physics replay | \(10^{-4}\) kWh | describe feasibility as within replay policy and convert one policy unit using the active maximum absolute price |
| Final global gap | \(10^{-2}\) objective units by default | must strictly exceed the accumulated lower-bound and incumbent allowances |

Every pricing call enforces

\[
\underline z_{\mathrm{price}}
\le z_{\mathrm{physical\ incumbent}}+\delta_{\mathrm{pricing}},
\]

where \(\delta_{\mathrm{pricing}}\) is serialized by component. The safe node
lower bound subtracts both master and pricing allowances. The global gap uses
the physical incumbent plus its leaf-conversion allowance. A result is
reported certified only if the robust gap is within epsilon **and**
epsilon is strictly wider than the accumulated allowance.

## 6. Why structural integrality yields one physical schedule

Suppose every \(\bar x_a\) at a node solution is integral. Since
\(\lambda_s\geq0\), \(\sum_s\lambda_s=1\), and each \(x_a(s)\) is binary:

* if \(\bar x_a=0\), every positive-weight column has \(x_a(s)=0\);
* if \(\bar x_a=1\), every positive-weight column has \(x_a(s)=1\).

Thus all positive-weight columns have the same complete structural incidence
\(x^\star\), which uniquely determines one unlabeled path cover and all of its
arc kinds. Their operating costs are identical, because fleet count and
deadhead movements are fixed by \(x^\star\).

For fixed \(x^\star\), collect each schedule's depot-arc/slot charging amounts
and SOC variables into \(y_s\). The fixed-structure physical constraints are
linear equalities and inequalities: charge bounds, SOC propagation, SOC
floors, battery caps, and terminal SOC. Their feasible set \(P_{x^\star}\) is
therefore convex. The weighted average

\[
\bar y=\sum_s\lambda_s y_s
\]

lies in \(P_{x^\star}\), and its load is
\(\bar e=\sum_s\lambda_s e(s)=L\). Pair/slot charging is keyed by the
label-invariant depot arc, so averaging does not require matching vehicle
labels.

It follows that the structurally integral master point converts to one
physically feasible schedule with the same operating cost, load, and true
objective. Lambda integrality is unnecessary. The implementation must build
this averaged schedule independently from the master columns, derive its
chains from \(x^\star\), and pass the ordinary physical replay validator.
Failure to do so is fatal; selecting an arbitrary positive lambda is not an
acceptable substitute because convex charging cost can make the averaged load
strictly better.

## 7. Solver-attested bounds and independent physical replay

Each node runs clean restricted column generation to the ledger tolerance. Its
bounds and infeasibility statuses are **solver-attested**. Physical columns and
integral leaves are replayed independently. This is not an independently
reconstructed global certificate. The checkpoint retains:

* every clean master solve and exact-evaluation upper bound;
* every pricing vector, incumbent, certified bound, reduced-cost interval,
  and physically replayed column;
* the monotone best node lower bound;
* the final lambdas, aggregate structural incidences, and branch choice; and
* certified infeasibility evidence where applicable.

The external best-bound tree maintains a physically replayed incumbent.
Branch children replace their parent in the active partition. A node may be
closed only by certified infeasibility, a valid lower-bound prune, or
structural integrality followed by successful independent realization.
At termination, the terminal node regions partition the root schedule
universe; the minimum of their retained valid lower bounds is the global lower
bound, and the incumbent is the global upper bound.

The checkpoint is the source of truth. It records the exact base SHA, instance
and market hashes, Gurobi backend/version evidence, tolerances, deterministic
queue, complete node states, restrictions, pricing calls, columns, node
bounds, incumbent history, terminal partition, and pending work. Writes are
atomic. Resume rejects any identity change and may repeat at most one
uncommitted solver call.

## 8. Tiny acceptance and stop rules

Only independently enumerable fixtures with \(n\leq4\) are in scope. Tests
must establish all of the following:

1. the laboratory root interval agrees with a separately certified A2 root;
2. the final incumbent and global-bound interval agree with complete tiny
   enumeration;
3. every generated column and every realized leaf passes physical replay and
   its node restrictions;
4. a genuinely fractional root is closed by the external branching tree;
5. at least one fixture closes after one split, including certified handling
   of any infeasible child; and
6. interruption/resume preserves bounds, calls, restrictions, incumbents,
   queue order, and the final result exactly apart from volatile timing.

The burned B2 seeds used here are all below 16:

* seeds 0 and 15 use \(n=4\);
* seed 11 at \(n=4\), `max_vehicles=2` has no time-feasible path cover and is
  retained as an explicit root-infeasibility fixture; its feasible
  cross-validation fixture uses \(n=3\), `max_vehicles=2`;
* seed 1 supplies the one-split fractional tree and tied-price fixture; and
* seed 9 with \(n=4\), duck prices, and \(b=0.2\) supplies a tree of depth at
  least two.

Additional adversarial checks cover a feasible parent with an infeasible
restricted child, both sides of the near-integral branching band, and
interruptions after uncommitted seed, master, and pricing solves.

The spike stops and remains a documented draft if a one-split tree cannot
reproduce tiny truth, a node claimed infeasible lacks a solver certificate, or
a structurally integral leaf cannot be independently converted and replayed.
No larger campaign, service, cluster job, or downstream experiment is launched
from this laboratory.
