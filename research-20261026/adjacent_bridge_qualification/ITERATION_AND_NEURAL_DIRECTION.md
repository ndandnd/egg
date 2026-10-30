# Price–route feedback: cycling, optimization and a conditional neural role

26 October 2026. Source-only analysis of relevant `src/egglab/market.py` and `regimes.py` objective/iteration definitions. No data, fixture, imports, hashes, tests, numerical run, replay or solver was used. This note neither adds an iteration to the proposed adjacent bridge nor authorizes training or execution.

## A full posted-price response can cycle

Consider a hypothetical finite catalog of two complete allowed schedules, `A=(1,0)` and `B=(0,1)` kWh in two periods, with equal operations, `a=U=0` and `b=1` in both periods. The naive update is

`p^k = p(L^k) = L^k`, then `L^(k+1) = argmin_{s in {A,B}} p^k · s`.

At A, the frozen posted quote strictly favors B; at B it strictly favors A. Thus a full replacement alternates forever. True integrated system cost is `.5` at each schedule; strategic uniform-price payment is `1` at each. The apparent improvement under yesterday's frozen quote is not an improvement after the fleet's own price effect is restored. Keeping the earlier schedule on a true-cost tie prevents oscillating **delivered incumbents**, but does not make the inner price iteration converge or certify opportunity.

This is a period-two feedback cycle, not a literal three-action rock–paper–scissors game. A single fleet against fixed background U has a nonlinear optimization problem with a well-defined finite-catalog optimum; it need not have a pure schedule that is a price-taking best response to its own induced prices. Indeed, neither A nor B is supported by its own gradient quote even though both minimize the corresponding pure-catalog nonlinear objective. The fractional average `(.5,.5)` would have system cost `.25`, but need not be one admissible physical fleet-day schedule. No such fixture or physical realization is constructed here.

## Which gradient, and what the current code does

For fixed background U and `d=a+bU`, the source's energy objectives are

`S(L)=d·L+.5 sum b_t L_t²`, with `grad S=d+bL=p(U+L)`,

`C(L)=d·L+sum b_t L_t²`, with `grad C=d+2bL`.

The first is incremental system cost; the second is the atomic fleet's uniform-price payment. A posted-price solve at `d+bL` is a system **linearization oracle**, not the fleet's true strategic best response. Using `d+2bL` is the correct strategic linearization, not automatically its global optimum over discrete routes. `market.py`'s strategist/taker-at-own-marginal-outlay remark is a convex first-order characterization, or a sufficient supporting-price condition on a general feasible set; it is not necessary for a discrete nonlinear optimum. The two-schedule example demonstrates that distinction.

The inspected `regimes._solve_convex_adaptive` is **not** the naive replacement loop. It accumulates globally valid objective tangents, resolves a tangent-relaxed older-Instance MILP, retains the best true-cost feasible upper point, and compares it with the running maximum of returned finite native dual bounds. Max-round termination and the recorded convergence flag are distinct. This source pattern does not by itself qualify any bound, end-to-end clock or newly connected adjacent solver. In particular, the proposed adjacent capacity master currently solves an additive posted-price problem, not this nonlinear outer master.

On a compact convex feasible domain, a correct-gradient linear oracle plus line search or justified diminishing steps can produce a convergent conditional-gradient method under its assumptions. The exact Frank–Wolfe gap bounds convex suboptimality; an approximate or learned oracle needs an explicit supported error condition, not a confidence score. See [Jaggi (2013)](https://proceedings.mlr.press/v28/jaggi13.pdf). A retained-column convex master can avoid throwing away earlier options and optimize their aggregate combination. But fractional route/full-fleet columns are not automatically one physical schedule. Integer recovery and unchanged physical/shared-capacity admission are still required; a valid convex relaxation bound and a feasible pure incumbent remain different objects. Do not output a fractional mixture as operational recourse or infer global pure optimality from convex-master convergence.

For multiple fleets, update protocol matters too. With finite independent action sets, private own-operations costs, common affine separable prices and fixed U, strategic payments admit the exact potential

`Phi = sum_i ops_i + d·sum_i L_i + .5 sum_t b_t(sum_i L_it)² + .5 sum_i,t b_t L_it²`.

A unilateral change has exactly that player's cost change. Strict unilateral improvements therefore cannot form a finite cycle; this gives a finite improvement property, not a globally optimal system allocation. The classical potential-game distinction is [Monderer and Shapley (1996)](https://people.csail.mit.edu/jrennie/trg/papers/monderer-potential-96.pdf). Simultaneous best responses need not decrease this potential: two fleets each switching away from the currently crowded period can move together and oscillate. Coupled feasibility, non-affine institutions, asynchronous information and different update rules require their own analysis. Neither source function establishes a general multi-agent game or an RPS result.

## Where neural prediction could have a decision role

Cycling alone is not a reason for a neural model. First use the correct objective, retain a physical incumbent and choose a conventional update/master with explicit feasibility and bound scope. A network cannot turn an inadmissible convex mixture into a fleet schedule, repair the wrong private/system gradient, or supply a missing pricing certificate.

A concrete conditional role is **proposing valuable route columns or prioritizing pricing expansions at the current master state**. Inputs would include the actual institution-correct linear prices/gradient, trip/terminal/fleet/plug duals, duty commitments and relevant physical opportunities. The target is a physically valid column with useful reduced cost or delivered master improvement per paid effort, with uncertainty/missing outcomes retained—not membership in one teacher route and not a forecast that an uncontrolled price loop will settle. The adjacent capacity pricer's occupied-minute surcharges and terminal rewards must remain part of that value context; exogenous a alone is insufficient.

Compare any such proposal with the existing exact/conventional pricer, cheap ranking and retained-column baselines. Verify proposed columns with original realization/admission and let the master decide value. If the learned proposal is the only pricing search, missing a negative column leaves certification incomplete; preserve an exact fallback or a justified oracle-error bound where a certificate is claimed. Retain actual loading/inference/search/publication costs and all failed cases. An advantage would require a demonstrated expensive decision bottleneck, independently grouped evidence and matched trained-blind/classical controls. Fast conventional pricing or no useful residual columns would remove the proposed role.

The old learned-family no-go results remain valid for their tested pipeline, not universal negative results for every pricing/column task. Conversely, a new institution or an oscillating toy does not revive those models or promise learning value. The parent's bounded adjacent bridge is first a callable/physical/ownership qualification at one posted quote; it is not an authorized nonlinear feedback experiment or label-generation campaign. No new fit, source change, extra native call or numerical study follows from this note.
