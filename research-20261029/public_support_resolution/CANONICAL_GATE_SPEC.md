# Second metadata gate: canonical modes, access and exact energy

Prospective source-only specification. Prior OD-gate PASS is parent-reported closed evidence and would be transferred by immutable identity, not rechecked. Read only movement-field/path notes and narrow constructor/adapter/schema source. No actual rich input, descriptor, plan values, imports, hashes, tests, execution or solve were consumed.

**A bounded second gate is plausible, but OD triangles alone do not remove the finite-mode scope.** The first gate established a property of aligned source matrix cells. Exact modeled-energy compatibility, exhaustive mode predicates, charging-access semantics and the separate dominance proof remain necessary. Failure of any prerequisite blocks the broader theorem rather than authorizing a regenerated instance.

## Modeled arcs versus empirical route realization

Yes: a mathematical extension can explicitly DEFINE each directed matrix cell's aligned (distance,time) pair as an admitted modeled arc. No empirical joint route witness is required for that abstract opportunity set. The conclusion must then say “walks over these modeled paired arcs,” not that actual travel paths jointly attain independently recorded distance/time minima. Empirical paired-path realizability remains UNKNOWN, even after a metadata PASS. Other charging locations, roads or routing alternatives outside this location/arc universe remain outside the extension.

This distinction is substantive. Componentwise distance/time triangles make the direct cell no worse than a modeled multi-arc walk only when each paired cell is an available arc by definition and consumption has the required exact additive semantics. They cannot prove empirical attainability or equality to an unrestricted real transport network.

## Source-bound inputs and minimal projection

Use the already identified rich public JSON and the certified depot15 NativeCase descriptor, each at prospectively fixed revision/path/byte identity. Transfer the first gate's exact location order, OD values/representation, denominators and complete PASS receipt; do not repeat its l³ checks. Shared source OD values must be identical to that admission. Decode once, select ONLY the unique native_cases entry with selected_depot_id15, and ignore every other variant. No original archive, private input, sibling operator, physical witness or optimization packet is needed.

Required new fields:

- selected variant case_identity/case_name/depot place, vehicle cap, resource_policy, market_edges_min, charging_model, cost_policy, initial_inventory_policy and terminal_policy;
- selected variant availability_horizon_sec and time_representation, plus top-level time horizon/terminal opening, departure policies, off-depot wait and zero parked-depot draw policies;
- all selected variant trips[].native and their source_trip_id, source_times_sec, source_distance_km and model_energy provenance;
- all movement_modes and movement_provenance, with movement IDs/kinds/service incidence/depot split and each leg's role, source OD IDs, depart/arrive/duration seconds, source distance/travel time and modeled energy components;
- energy_model's declared traction/auxiliary coefficients and source_energy_observed=false; shared stop IDs/depot flags solely for access/wait classification;
- the exact descriptor itself, bound field by field to the projected native case rather than merely a claimed matching case_identity string.

## Complete mode and window predicates

Let n be the admitted mandatory service count, l the transferred location count, d the selected depot, h0/h1 the declared horizon. Freeze all ordered service identities and source order before outcomes. For each service i, check one pullout predicate (latest departure s_i−time(d,start_i) within the horizon) and one pullin predicate (immediate departure e_i, arrival e_i+time(end_i,d) within the horizon).

For every ordered distinct pair i,j, evaluate BOTH predicates:

1. Direct: depart at e_i, travel end_i→start_j, arrive no later than s_j; append the exact stationary destination wait if arrival<s_j. Require the expected mode exactly once when its frozen timing predicate is true, or an explicit time-infeasible absence when false.
2. Via selected depot: inbound leaves e_i and reaches d at e_i+time(end_i,d); outbound leaves d at s_j−time(d,start_j) and reaches the service at s_j. Require the inbound/outbound feasibility and horizon predicates, the exact two legs and split1, and the entire maximal charging gap between those times. Zero-length gaps must be handled explicitly, not dropped as favorable cases.

Compare native minutes to source seconds exactly, including full half-minute conversion wherever the existing instance uses it. Existing modes must match endpoint incidence, ordered legs, expected stationary waits, no hidden charging split, all exact timestamps, and descriptor mapping. Extra, duplicate, misclassified and omitted feasible modes fail. Do not insert a new mode to make coverage pass. The direct and depot alternatives remain distinct even if endpoints or times coincide.

Canonical window containment then follows conditionally from the transferred time triangles: any admitted modeled walk to the SAME depot cannot arrive earlier than the direct inbound arc, and any such outbound walk cannot depart later while reaching the next fixed service. Keeping original charge sessions within the larger canonical gap preserves the common shared connector; no new simultaneous capacity is assumed. Pullout/pullin use analogous latest/earliest representatives. This mathematical step also needs nonnegative travel/wait consumption, capacity-preserving charge curtailment, no minimum session, no parked-depot draw and no extra access/mandatory task along omitted excursions. The separately reviewed theorem must supply these assumptions; metadata matching alone does not prove it.

## Exact energy seam: a separate decisive prerequisite

The original constructor computes travel energy using the ORDERED floating operations `km=distance_m/1000.0`, `traction=0.96*km`, `auxiliary=16.0*time_sec/3600.0`, then `traction+auxiliary`. Stationary wait uses `16.0*duration_sec/3600.0`. Service uses its separately declared distance/duration formula. The descriptor stores each resulting total as a binary floating coefficient. The first gate instead preserves exact JSON decimal tokens. These are different exact rational representations and may not be interchanged silently.

Check two different obligations:

**Provenance consistency:** every stored modeled component/total must match its source fields and the declared original operation order/representation, and native leg/service totals must match descriptor coefficients exactly. A prospective pure metadata checker may evaluate this declared function under a frozen IEEE-binary64 contract; this is a new consistency check, not a new physical solve or replacement coefficient. Alternatively a rational expression equality may be used, but if binary rounding makes it false the result is FAILED/UNKNOWN, not tolerance-qualified equality.

**Dominance in the certified coefficient model:** provenance consistency alone does NOT establish that the stored exact binary direct-leg energy is at most the sum on every modeled detour. Real-valued distance/time triangles can acquire a wrong-sign residual after separately rounded products/sums. Need either (a) a proved exact energy representation/rounding margin that implies all required dominance inequalities, or (b) a source-defined complete modeled OD energy table with exact rational binary entries and an independently checked energy-dominance certificate. Missing energy weights for unused OD arcs cannot be inferred from whichever emitted legs happen to exist. Defining those absent-arc weights is part of the proposed larger opportunity-set definition and requires explicit parent approval; it must not rewrite the old descriptor.

Stationary waiting is another seam: direct travel followed by a separately rounded wait sum need not equal a single formula for the total service gap exactly. Any timing relocation or path replacement must preserve the necessary prefix-SOC inequalities and weakly reduce exact energy/purchases, not just match a decimal approximation. Without an exact argument for these wait/travel sums, retain the finite-mode scope even if every source formula recomputes.

## Charging access and depot endpoints

Only the selected depot may supply charging in the proposed extension, with the descriptor's one connector, power/acceptance, intervals and terminal deadline. Pullout/direct modes do not gain charging merely because a place ID is a depot. The constructor explicitly rejects a direct-mode stationary wait at ANY source-flagged depot, to avoid ambiguity about zero depot auxiliary draw. The gate must classify every potential direct wait's destination against those flags, including selected-depot endpoints. If such a feasible wait requires a policy not represented by the constructor, report BLOCKED_ACCESS_POLICY; do not pretend it is an ordinary off-depot wait or silently add charging. The presence of a second source depot does not admit it as another charger.

An absent/zero diagonal source arc, zero travel or service endpoint at the selected depot must be explicitly checked, not assumed equivalent to an external off-depot wait. Repeated same-depot excursions are dominated only under the no-task/no-distinct-access/nonnegative-consumption conditions of the proof. Other depot visits with different access cannot be deleted by that argument.

## Prospective denominators and stop states

Freeze n service mappings; n pullout+n pullin predicates; 2n(n−1) ordered distinct-service direct/depot predicates; every emitted mode and leg provenance mapping; every resource/market/policy field; and every classified stationary wait. If exact modeled energy dominance needs a complete new OD energy table, its l² entries and l³ comparisons are a separately declared subgate, not an unnoticed rerun of the already closed distance/time triangles. If proving wait dominance needs duration-dependent checks, freeze their complete finite domain or prove an analytical inequality; do not sample favorable gaps.

Retain PRESENT_CANONICAL, ABSENT_TIME_INFEASIBLE, FAILED_MAPPING, FAILED_EXACT_ENERGY, BLOCKED_ACCESS_POLICY and UNKNOWN_PREREQUISITE states with fixed denominators. An incomplete/false source property must leave downstream dominance/extension UNATTEMPTED. No tolerance, imputation, mode regeneration, metric closure, new route solve, old physical replay or favorable case replacement is included.

## Decision boundary

The smallest useful second phase first verifies rich-to-descriptor identity, exhaustive canonical predicates and policy/energy provenance, while reporting the exact stored-energy dominance seam separately. A complete PASS plus an explicit modeled-paired-arc definition and reviewed energy/window dominance proof could justify a larger *modeled* path opportunity class. It would still not establish empirical route realizability, arbitrary charging access or external replication. If exact energy/wait rounding or depot-endpoint policy cannot be closed transparently, stop with the already valid finite declared-mode result; do not promote a metric PASS into an operational completeness claim.
