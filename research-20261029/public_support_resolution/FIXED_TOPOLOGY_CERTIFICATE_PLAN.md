# Prospective exact charging construction on a fixed native topology

29 October 2026. Mathematics/source-only proposal, with no authority to execute it. This would be a **new, separately frozen construction phase**, not a reinterpretation or silent repair of an earlier native candidate. Preserve the original candidate and its strict replay result unchanged. No data or old plans were read for this note.

## Objective and possible outcomes

Given a selected full movement path cover from a new native proposal, construct an exact feasible charging allocation for that *same* topology under the original stored-input rational physical model. A successful independently replayed allocation gives a physical upper bound. It does not certify global routing optimality, D, CH or price support. A failed strict replay of the original numeric allocation is not evidence that its topology is infeasible.

The construction must permit three honest outcomes: exact feasible allocation found; exact infeasibility certificate for this fixed topology; or construction unresolved within its frozen budget. Near-feasibility of the numeric proposal does not guarantee the first outcome. In particular, a route can exceed an inventory limit by a tiny amount that a native tolerance admitted, making the exact fixed topology infeasible.

## An exact transshipment formulation

Under the target assumptions, fixed-topology charging feasibility is a rational capacitated-flow problem. This is stronger than hoping that a rounded active face remains feasible.

First independently reconstruct the selected paths, all service/leg consumptions and every charging window. Reject invalid coverage, chronology, movement ownership, or unsupported modes before considering energy adjustments. Keep the source movement choices fixed; do not add, remove or reorder movements or services.

Use battery-energy units for the flow. For the common constant efficiency eta, an allocation of grid energy q delivers p=eta*q. Shared interval capacity in these units is eta*cap_k. This scaling remains an ordinary network flow because eta is common and constant; bus-dependent efficiencies or state-dependent losses would require a different argument.

For each bus, transform inventory to s=SOC-r, so it lies in `[0,B-r]`. Take its event times to include all selected service/leg completion times, all service starts needed for reporting, and the independently reconstructed charging-interval endpoints. Nonnegative consumption can be booked at the end of each noncharging leg/service: no charging occurs within that activity, so endpoint reserve bounds also certify all intermediate inventory. At a time shared with the end of charging, account for completed charge before instantaneous subsequent noncharging consumption, while checking the pre-consumption capacity.

Create an inventory node at each bus event, split by a capacity arc of upper bound B-r. Incoming carried inventory and delivered charge must pass through that capacity arc before any event consumption is withdrawn. After it, a fixed-demand arc withdraws the exact service/leg consumption due at that event; the remainder carries forward to the next event. Carry arcs also have finite upper bound B-r. A fixed initial injection of B-r and a fixed final withdrawal of B-r enforce full start and full finish separately for each bus. Every consumption withdrawal has equal lower and upper bound at its exact stored coefficient. If several noncharging consumptions occur at one timestamp, their nonnegative amounts can be combined exactly or retained individually.

For each original elementary charging interval k, create a grid-allocation node. A supply arc into it has capacity eta*cap_k. An outgoing arc to the inventory node of each eligible selected visit's bus, at the interval's right endpoint, carries its delivered energy p_mk. Its upper bound is eta*cap_k. The original q_mk is recovered as p_mk/eta. An unavailable or unselected visit has no such arc.

The global external supply is the fixed total battery consumption D_total plus the buses' initial usable inventories. Terminal inventory withdrawals and all consumption withdrawals have the same total demand. Equivalently use a standard lower-bounded circulation reduction. Full replenishment forces delivered charging energy to equal D_total, and hence grid purchases to equal D_total/eta. Initial inventory is repaid; the network supplies no net inventory credit.

### Why interval-end injection is exact here

An eligible bus is parked at the depot for the *entire* elementary interval. It has no positive consumption inside that interval: selected visit windows are disjoint from its service and movement legs, and depot auxiliary draw is zero. Consequently moving the accounting of its within-interval charging to the right endpoint cannot hide an intermediate energy requirement. Its maximum inventory is reached after the accumulated charge and is checked by the inventory-capacity arc. Other buses may have consumption events inside this interval; they do not change this bus's argument or create extra connector capacity.

Thus one can retain the original charging interval indices instead of splitting the charge proposal at every other bus's event. There is at most one selected eligible visit per bus per interval. The single grid-node capacity enforces total delivered energy at most eta*cap_k. Charging those allocations serially at the original exact rate realizes them in continuous time. Every allocated energy is inside its declared window, and all buses satisfy reserve/headroom. This is the same physical serialization fact used in the energy-flow formulation, independently checked again in the upper-witness replay.

Conversely, integrating any physical fixed-topology charging schedule gives these network flows. Its inventories at event boundaries give carry flows, and its charge increments satisfy the grid-node capacities. Therefore exact feasibility of this network is equivalent to charging feasibility of the declared fixed topology under the stated assumptions.

## A bounded construction close to the native proposal

Use a rational lower-bound/max-flow feasibility algorithm, or exact rational min-cost transshipment with an explicit iteration/operation budget. A feasible rational flow is already a compact primal certificate. An exact infeasibility report needs a checked max-flow/min-cut or equivalent circulation-cut certificate, not a native INFEASIBLE status.

For a controlled nearest-proposal construction, minimize

`sum_(m,k) |p_mk/eta - q_native,mk|`

over the feasible network. Each native proposal coefficient is retained as its exact binary rational. This is separable piecewise-linear convex cost on the visit allocation arcs. It can be represented by two parallel arcs: capacity up to the target has marginal cost -1/eta, and remaining capacity has marginal cost +1/eta, with the appropriate fixed constant. Targets outside an arc's feasible range merely change the constant and leave a single slope. The cheaper parallel arc is filled first in any min-cost flow. Preserve and report any native orphan/unselected allocation as a distance constant, rather than quietly discarding it from the comparison.

This L1 objective gives a precise construction policy; feasibility does not require proving that the distance is globally minimal if the budget expires with a feasible primal flow. If a nearest-flow optimum is claimed, check its residual reduced-cost/potential certificate exactly. Report exact per-allocation and total movement of energy and the original strict violations. No closeness guarantee follows merely from a small native residual.

For improved supply cost after feasibility is established, add an hourly aggregation node upstream of that hour's grid-interval nodes. Its flow P_t is delivered battery energy and its cost is `a_t*P_t/eta + b_t*(P_t/eta)^2/2`. This is a separable convex quadratic flow problem. A numerical QP may propose an active set, followed by rational reconstruction and exact KKT verification against the full fixed-topology constraints. A reconstructed point is accepted only if every primal inequality and equality passes exactly; fixed-topology optimality additionally needs exact stationarity, multiplier signs and complementarity. Degenerate/singular active sets must be handled without assuming a unique charging vector. Failure to reconstruct is unresolved, not infeasibility.

The simpler rational feasible-flow construction is preferable as the first upper-certificate mechanism. It needs no favorable numerical active face. The quadratic variant is an optional separately budgeted refinement, not an automatic second solve hidden inside repair.

## Independent publication checks and limitations

Publish a new candidate containing the exact q_mk, unchanged movement IDs, exact reconstructed intervals, an explicit serial session witness and exact hourly loads. Recompute physical inventories from original per-leg coefficients rather than the flow program's aggregate consumption claims. Independently verify every network arc bound/conservation equation, full initial/terminal inventories, reserve/headroom, charging windows, connector capacity and service coverage. Then evaluate the original binary-stored market coefficients with exact rational arithmetic to obtain the physical upper bound.

If the original native objective changes after construction, state both numbers and the exact allocation distance; the original number was not an exact physical bound unless its own strict replay passed. Finite load caps allow a deterministic gradient/Lipschitz bound on supply-cost change, but no small-change claim is justified until the actual new allocation is certified.

Freeze the selected-topology provenance, exact source/market semantics, operation and wall/CPU limits, construction policy, independent checker and negative controls before consuming candidates. Useful controls alter a consumption coefficient, terminal inventory, one grid capacity, an allocation, a selected window, or a purported cut/potential certificate. The construction phase may establish a new upper or topology-level infeasibility; it must not relabel the original native failure as a success, establish global infeasibility, claim exact global optimality, or retroactively improve the original method's timing.
