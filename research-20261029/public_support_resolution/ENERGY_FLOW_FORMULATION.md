# A perspective energy-flow formulation of the declared complete-fleet model

29 October 2026. Mathematical/source-only derivation. No data, backend, imports, numerical runs, tests or hashes. This is an ideal-model formulation and proof, not a qualified implementation or a performance result.

## Scope and notation

Use the same one-depot declared movement graph as `native_pathflow.build_feasible_model` and the physical charging windows in `native_recharge._window`/`compile_case`. Every service i is mandatory, occurs over a fixed positive-duration interval, consumes E_i >= 0, and is covered exactly once. Every allowed internal movement i->j respects service chronology, so the service graph is a DAG. Movement choices include pullout, direct, depot and pull-in modes, retaining all parallel alternatives. No new discretionary trip or charging access is introduced.

There are at most V homogeneous used buses, each initially and terminally full at B, with reserve r in [0,B], constant charging efficiency eta > 0, nonnegative stored per-leg consumption, zero depot-parked draw, and no switching time. Recharge occurs only at the single depot, in the exact declared windows. A single shared connector and all buses have the resource-period powers specified by the case. The public case has r=0, eta=1 and 360 kW for both limits. The proof also covers the stated symbolic r and eta.

All coefficients below are exact rationals under the ideal stored-input interpretation. In particular, a movement's energy is the sum of its **individual exact per-leg coefficients**, not a newly rounded floating aggregate.

For each movement m introduce a binary selection y_m. It is an arc from its preceding service or the source depot to its following service or the terminal depot. Impose

* sum of selected incoming movements at i = 1;
* sum of selected outgoing movements at i = 1;
* sum of pullouts = sum of pull-ins <= V.

The DAG property makes any integer solution a disjoint collection of source-to-terminal paths covering all services; disconnected cycles cannot occur. Each path is one bus. This is the existing complete-graph path cover, with all admitted fleet counts retained.

## Energy carried on movements

For every movement m, introduce continuous variables U_m and W_m. U is battery inventory leaving its origin service (or initially leaving the source depot); W is inventory entering its destination service (or the required full terminal inventory after terminal charging). Their perspective bounds are

`r y_m <= U_m <= B y_m`,

`r y_m <= W_m <= B y_m`.

For service i introduce optional aggregate inventories a_i after service and b_i before service, or eliminate them using

`b_i = sum_{m incoming i} W_m`,

`a_i = sum_{m outgoing i} U_m`,

`b_i - a_i = E_i`.

Because incoming and outgoing selections each sum to one, the perspective bounds imply `r <= a_i,b_i <= B`, even in the relaxation. The service energy is unconditional: every mandatory service occurs once. It must **not** be multiplied by an individual incoming or outgoing movement selection.

### Direct movement

For total movement consumption H_m >= 0 and no charging,

`W_m = U_m - H_m y_m`.

At integer selection, the endpoint bounds ensure reserve throughout every noncharging leg: inventory decreases monotonically, and all intermediate prefix consumptions are no larger than the total. At zero selection every inventory vanishes.

### Pullout

Set `U_m = B y_m`, with the same noncharging conservation to W. It reaches the first service from a genuinely full initial battery; no inventory credit is introduced.

### Internal depot movement

Let H^-_m be exact consumption on legs before the depot gap and H^+_m consumption after it. Let q_m be total grid energy charged during that gap. Introduce arrival C_m and departure D_m:

`C_m = U_m - H^-_m y_m`,

`D_m = C_m + eta q_m`,

`W_m = D_m - H^+_m y_m`,

`r y_m <= C_m <= D_m <= B y_m`.

The explicit arrival reserve prevents using energy that has not yet been bought. The departure headroom prevents charging beyond capacity before the outbound legs. Nonnegative inbound/outbound consumption and monotone charging make these bounds sufficient for all intermediate inventories. The split must be exactly the stored depot split; no transit-leg charging is allowed.

### Pull-in and full terminal replenishment

Let H_m be consumption on all pull-in legs. Set

`C_m = U_m - H_m y_m`,

`r y_m <= C_m <= B y_m`,

`W_m = C_m + eta q_m = B y_m`.

Here q is available only after arrival and terminal opening and before the declared deadline. This restores each **used** bus to its own full capacity, rather than merely conserving inventory in aggregate.

## Shared connector and continuous-time realization

Independently form elementary intervals k by sorting market boundaries, resource boundaries, terminal opening, and **every** charging-window endpoint from every declared depot/pull-in movement. This is the partition used by `compile_case`; it is not a time grid approximation. Within an interval, resource powers and market ownership are constant and a movement's charging window either contains the whole interval or none of it.

For each m whose window contains k, introduce grid energy q_mk >= 0, with

`q_m = sum_k q_mk`,

`q_mk <= cap_k y_m`,

`sum_m q_mk <= cap_k`,

where `cap_k = min(P_bus,k, P_grid,k) * (end_k-start_k)/60` for an available single connector, and zero when it is unavailable. Inactive or noncharging movements have no q variables. Hourly load e_t is the sum of q_mk for intervals belonging to market period t.

Operating cost is `c=f*sum_pullouts y_m + sum_m d_m*y_m`, where d_m is the exact declared movement monetary cost (zero in the public target). Linear pricing minimizes `c+p dot e`; quadratic planning minimizes `c+sum_t(a_t*e_t+b_t*e_t^2/2)`. No fleet-count restriction beyond the declared V is added.

These interval capacities are exactly realizable for **integer** movement selections. Within each k, list its positive selected allocations in any order and charge them serially at rate `min(P_bus,k,P_grid,k)`. Their total duration is at most the interval length. Every session stays inside its owner's declared window. The same selected bus cannot have two overlapping positive-length visit windows: its path is chronological and successive charging gaps are separated by a mandatory service. Each bus remains at the depot throughout its gap; serial rescheduling creates no service or movement conflict. Aggregate q_m fixes its final gap inventory, and monotonic charging keeps every intermediate inventory between C_m and D_m. Zero switching time is essential to this exact serialization argument.

This construction does not prove exact realizability for multiple connectors, bus-dependent acceptance limits, parked auxiliary draw, taper, switching delays or charging during travel. Those changes require a separate formulation/proof. They are not present in the target case.

## Integer equivalence: both directions

**Physical plan to integer energy flow.** Select its declared movement arcs. Set U/W to the bus inventories at the stated boundaries, and C/D to actual depot arrival/departure inventories. Integrate each charging session over elementary intervals to obtain q_mk. A single connector with the stated powers gives the shared interval capacity, and selection gives each perspective bound. Physical conservation proves every leg/depot equation and each service balance. Full initial and terminal inventory proves the pullout and pull-in endpoint equalities. Thus every ideal physical plan maps to a feasible integer solution with exactly the same load, bus count and operating cost.

**Integer energy flow to physical plan.** Recover its DAG paths. At every service, the unique selected incoming W and outgoing U are exactly b_i and a_i, whose difference is E_i. At every selected movement, the endpoint/depot equations give its inventory transitions. All inactive flow variables vanish. Apply the serial construction above in each charging interval. It realizes precisely q_mk while respecting shared power and individual availability; inventory follows the feasible movement/service states. Nonnegative leg consumption and monotone charging ensure reserve and headroom between the checked states as well. Every path begins and ends full. Thus every integer solution yields a feasible physical complete fleet with identical projected `(e,c)`.

The claim is equivalence in projected feasibility and objective, not equality of raw charging-session timing: different serial schedules can implement the same interval allocation.

## Relaxation validity and comparison with ideal big-M rows

Relax y to [0,1]. Every integer physical solution remains feasible, hence so does every convex combination of its extended variables. Minimizing any linear price objective or the convex quadratic supply objective over this relaxation gives a valid lower bound on the physical minimum. It is generally still a relaxation of the complete-plan hull; there is no claim that all fractional energy flows are implementable mixtures of full fleets.

There is a useful analytic dominance comparison with the existing compact **ideal** big-M system when both use identical exact coefficients, bounds and charging intervals. Define a_i and b_j by the service sums. For an internal movement m from i to j, write residual inventories of the other outgoing/incoming movements as A and Z. Then

`a_i = U_m + A`, `b_j = W_m + Z`,

`r(1-y_m) <= A,Z <= B(1-y_m)`.

The movement conservation equation implies

`b_j - a_i + H_m - eta q_m = H_m(1-y_m)+Z-A`.

Consequently its residual lies in

`[(H_m-(B-r))(1-y_m), (H_m+B-r)(1-y_m)]`,

which is contained in the usual `[-(B+H_m)(1-y_m), +(B+H_m)(1-y_m)]` big-M band. The same calculation for a pullout bounds `b_j-(B-H_m)` between `(r-B+H_m)(1-y_m)` and `H_m(1-y_m)`. For a pull-in, `a_i-H_m+eta q_m-B` lies between `-(B+H_m-r)(1-y_m)` and `-H_m(1-y_m)`. These imply the existing endpoint big-M bands.

The depot arrival inequality follows from `C_m>=r y_m` and the other outgoing inventories: `a_i-H^-_m >= r-H^-_m(1-y_m)`. Likewise `D_m<=B y_m` gives `a_i-H^-_m+eta q_m <= B-H^-_m(1-y_m)`. Both imply the weaker existing relaxed reserve/headroom rows with M=B+H_m. Shared charging rows and service bounds also agree or are implied. Thus the projected energy-flow LP relaxation is no weaker than the ideal compact big-M relaxation. This is weak dominance, not proof of strict improvement on the public instance or faster branching.

Both ideal formulations also conserve total grid energy exactly when eta=1 and starts/ends are full. The current native pathflow implementation adds an outward aggregate-energy band to account jointly for intended per-leg conservation and rounded native rows. The exact energy-flow model satisfies intended conservation and therefore the intended portion of that valid outer band. A claim of native relaxation dominance still requires accounting for every independently rounded coefficient and right-hand side; it does not follow just from the symbolic argument above.

### A derived minimum-fleet cut

The maximum number of mandatory services simultaneously active on half-open intervals `[start,end)` is a valid fleet lower bound. It can be computed exactly at all service start times, with services ending at that time already inactive. The nonempty-case bound is at least one.

There is an additional one-bus obstruction when all services are chronologically disjoint. A single bus must cover them in that chronological order, so every consecutive pair requires a permitted connecting movement in the declared graph. If a pair has no such movement, one bus is impossible. If every consecutive pair has at least one option and every option is direct, no intermediate recharge window exists on a one-bus route. Nonnegative movement energy and full initial inventory then imply that service energy alone exceeding `B-reserve` makes one bus impossible. Terminal recharge cannot supply energy before the last service is completed. In either obstruction case, two is a valid lower bound. Taking the maximum of this bound and the overlap bound yields `sum_pullouts y >= derived_minimum_fleet`.

This cut derives only from the current case's exact times, energies and entire permitted connection list; it does not read or reuse a historical result. The ledger records those proof conditions for independent reconstruction. It excludes no physically feasible fleet cardinality in the declared graph and does not assume that an optimum uses two buses. A one-service feasible control retains the bound one.

## Per-leg implementation and the binary-float seam

A robust implementation can avoid H^- and H^+ aggregate coefficients entirely: introduce an inventory at each movement leg boundary and write each noncharging transition as

`s_next = s_previous - energy_leg * y_m`,

with `r*y_m <= s <= B*y_m` at each boundary. At the one permitted depot gap insert `s_after = s_before + eta*sum_k q_mk`; impose full source/terminal boundaries as above. This extended formulation uses only the original stored per-leg coefficients, eliminating one source of rounded energy aggregation and all large-M residual constants. It remains unlabelled by bus, although it uses more continuous variables than the current compact SOC model.

Resource capacities still involve time/power arithmetic; constructing their native RHS with floating multiplication can round inward or outward. An exact certificate must use exact rational capacities, or record rigorously outward-rounded relaxation capacities and independently verify the resulting relaxation's bounds. The physical upper witness must always be checked against the original exact capacity, never the relaxed native RHS. Objective coefficient assembly, deadhead monetary costs, and aggregate reporting have analogous seams. A native optimizer working with binary-float rows is not an exact rational solver.

For the classical diagnostic, retain the full cardinality range, use the same frozen market and common start policy as the compact baseline, compare at common bound quality and charge all construction/verification work. For an exact lower certificate, export the actual rational rows and independently verify LP primal/dual or Farkas certificates and, if needed, an exhaustive integer branch proof. The stronger relaxation may make such a proof easier, but no speedup or closure is established by this derivation alone.
