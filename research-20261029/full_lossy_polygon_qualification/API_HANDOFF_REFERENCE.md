# Independent raw reference API — source only

`reference.py` has definitions and stdlib imports only; it has NOT been imported, compiled, tested or executed. Parent must separately review/freeze/fund its eventual consumption. No historical outputs were read.

## Literal schema

`spec` has exactly `id,B,a,b,alpha,delta,K,H,fee,d,edges`. `a,b` are equal-length lists,1<=n<=2; `edges` is a duplicate-free list of zero-based `[i,j]` pairs. Energies satisfy0<a_i,b_j<=B, B>0;0<alpha,delta<=1;K,H,fee,d>=0. `d` is compulsory common matched-edge consumption, scheduled AFTER early charging and BEFORE B. It is zero on standalones. Every declared allowed edge must satisfy `b_j+d<=B`; violation rejects the whole input without filtering an edge. All admissible matchings remain in the denominator; resource-infeasible branches remain empty. Numeric inputs accept exact integer/fraction strings (e.g. `"3/4"`), integers or Fraction objects; floats, bools, decimals/exponents and nonfinite tokens reject. String length<=4096 and fraction bits<=16384.

The common timing is A[0,1], early[1,2], transition[2,3], B[3,4], terminal[4,5]. Grid-side shared early/terminal powers are K/H; each bus accepts these powers. Start/end full, reserve0, common efficiencies, arbitrary finite early direction changes, charge-only terminal, no waiting/auxiliary draw/switching cost/time/minimum session. Each used bus serves at least one service; this API enumerates service-assigned matchings, not additional idle-bus labels. The full projection can have signed net early load. No objective or candidate formula is used.

## Calls and records

`enumerate_physical(spec) -> dict` returns `status="ENUMERATED", id, records, matching_count, feasible_count, strict_replayed_vertices, operations, limits, provenance`. The strict replay count equals the total number of returned vertices; each was freshly replayed once. The comparator should adopt these receipts rather than replaying them again. All allowed partial matchings are enumerated independently (at most7 at n=2). A record has:

- `id`: `m0:empty`, `m1:0-1`, etc.; `pairs`: canonical tuple of allowed pairs;
- `cardinality,fleet,buses,total_consumption,strict_replayed_vertices` (the last equals this record's vertex count);
- `raw_bus_polygons`: each bus's exact five linear SOC/nonnegativity/gross rows and all raw polygon vertices;
- `dimension`:−1 empty,0 point,1 segment,2 polygon;
- `vertices`: cyclic monotone-hull order, with duplicate/collinear interior points removed.

Each returned vertex has exact Fraction `C,X,Q,E,L,ops`, `allocation=[{"C":Fraction,"X":Fraction},...]` in canonical bus order, and `witness`. The witness contains `early` and `terminal` action lists with `bus,kind,energy,start,end,power`, plus declared windows. Buses list paired buses first, then unmatched A, then unmatched B; bus IDs are0..fleet−1, with original A/B indices retained. `None` denotes absence of that service. All matching records, including infeasible ones, remain in `records`.

`replay(spec,record,vertex) -> dict` reconstructs canonical coverage/bus assignments from `pairs`, then replays A consumption, every early action, transition consumption, B consumption and terminal actions. It independently checks serial clocks, no connector overlap, exact power/energy/duration, direction and window rights, SOC after every monotone action/service, each bus's full terminal inventory, aggregate C/X/Q/E/L/ops, individual C/X allocations and total resource/accounting identities. It returns `strict_pass,violations,C,X,Q,E,L,ops,operations`. Schema/unknown assignment/resource-limit failures raise; physical/report corruption normally gives `strict_pass=False`. It never repairs. Generated vertices invoke this replay once each before enumeration returns, and the replay operation counts are included in enumeration's total.

## Independent construction and exactness

For each bus the reference directly intersects pairs of the five raw halfplanes `C_v>=0`, `X_v>=0`, `l_v<=alpha C_v−X_v/delta<=u_v`, `C_v+X_v<=K`; it checks every resulting intersection against every row. The SOC box is constructed from that bus's own A/transition/B consumption and headroom. A bounded nonempty polygon, point or segment has vertices among these intersections. Adding the per-bus gross bound is necessary for every globally feasible nonnegative allocation and therefore loses no point.

Minkowski summation combines these raw vertices and retains the contributing individual allocations through a standard rational monotone-chain hull. The resulting polygon is clipped against shared gross<=K and terminal sufficiency `Q>=S_matching−alpha H`. Every new clip intersection linearly interpolates its two endpoint allocation witnesses. This yields the complete per-matching aggregate polygon without using r_m, a cardinality threshold, or the proposed aggregate polygon as a construction rule.

For each individual allocation, the schedule separates its net one-direction exchange from residual neutral cycling. It splits residual battery throughput into chunks<=B/2, using charge-first or discharge-first according to that bus's own early initial SOC. Cycles return to the same inventory; the baseline action then reaches the raw box endpoint. All early actions serialize at K and full terminal refills at H. K=0 implies no positive early action; H=0 implies no positive terminal action. Lossless cases retain the C/X polygon even when its E/L image collapses. No division by kappa or special nondegeneracy assumption is used.

The source also supports independently prepared interior records using the same allocation/witness schema: convex interpolation preserves raw feasibility; its explicit action witness must still pass `replay`. No public helper for fabricating such an interior witness is promised by this narrow API.

## Prospective ceilings and failure semantics

`LIMITS`:2,000,000 tracked exact-operation/checkpoint events per enumeration (including generated replay counts);16,384 fraction bits;4096 hull vertices;16,384 early actions per witness and per replay phase;4096 numeric characters. These are explicit algorithmic guardrails, NOT measured CPU/wall/RSS qualification or a count of every Python arithmetic instruction. Large K/B can require too many finite cycles; exceeding a guard raises `ReferenceLimit` and fails the whole call without a success record or silently omitted branch. The future owner must separately bound runtime/memory and record all assigned literal outcomes. No native backend, source hash, controller, manifest, run or empirical claim is included here.
