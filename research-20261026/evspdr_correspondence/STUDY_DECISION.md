# Selected bounded next test: duty commitment and economic lens

Prospective scientific selection, 26 October 2026. STATIC implementation may now
proceed in NEW `research-20261026/duty_market_seam`. This document is not a launch
manifest. No original TRAIN/GIRO data, old plan or sealed bank is an input.

## Question and contribution boundary

Within one explicitly representable physical model, how much delivered improvement
comes from charging an unchanged movement path, changing charging visits while
keeping the trip duties, and changing the duties themselves? Does this decomposition
depend on choosing posted-price payment, strategic uniform-price payment or
integrated system cost? This checks an actual control/objective correspondence
missing from the recent learned study. It is a small diagnostic, not a new theorem,
population experiment, proof of a computational bottleneck or an ML promotion gate.

Do not infer that a model needs learning from a difference, nor that learning is
impossible from a tie. A faithful multi-station EVSP-DR oracle connection remains
separate work; no station aggregation is claimed here.

## Exact synthetic input design

One new literal synthetic base, `duty-market-seam-v1`, eight service trips in four
waves. Wave starts are 60,240,420,600 minutes; each has one A→B trip at that time
and one B→A trip ten minutes later, each lasting45 minutes and consuming20 kWh.
Two predetermined duties alternate direction: duty0 takes wave0 A→B, wave1 B→A,
wave2 A→B, wave3 B→A; duty1 takes the complementary trips. Every service exactly
once, committed N=2 (also max_vehicles=2). No selection using solver outcomes.

Horizon0–960 minutes, hourly market edges; terminal opening720/deadline960.
Battery80/reserve10 kWh, efficiency.9, full initial and per-bus full terminal SOC.
One depot D, one connector, bus/grid power60kW throughout. D↔A travel10min/2kWh,
D↔B15min/3kWh, A↔B10min/2kWh; same-place travel0/energy0.
All chronological direct and via-depot movements are declared, with stationary
waiting energy0. Vehicle cost100 and movement-duration cost0 are explicit synthetic
assumptions; this seam does not calibrate monetary stakes or copy Partille physics.

The reference uses the two duties and via-depot movement between every pair.
Construct a serial full-refill schedule in ascending window-release order,
breaking ties by duty index, with charge amount from physical SOC accounting.
Reject if any window/SOC/resource condition fails; no repair or alternative fixture.
Independent unchanged native replay is mandatory before native dispatch.

Hourly a=.25 except periods4,5,12,13 (zero-based), where a=.125.
Background U=32kWh in periods0–7 and64kWh in8–15. Four declared contexts:
U is background load in the price-forming market, not extra load on the fleet's
connector. The60kW resource is the fleet charging limit/residual connection
capacity; do not subtract U from it or call it the total market system capacity.
1. b=0, all three economic objectives coincide (one set of solves, aliases reported).
2. b=1/1024, posted p=a+bU.
3. b=1/1024, integrated system cost.
4. b=1/1024, strategic uniform-price payment.
Coefficients are dyadic for an exact coefficient bridge; no b/cap/price scan,
retuning, favorable replacement or claim these are empirically estimated values.

## Controls and immutable denominator

Twelve assigned workers: per context, one fixed-movement QP common acquisition,
then fixed-duty MIQP and full-declared-graph exact-N MIQP. Both dependent methods
start from the same admitted target-QP retained U, with separate paid clocks and
unchanged common fallback. Fixed duty retains all declared movements connecting
successive service trips in each predetermined duty plus its first pullout/last
pullin. It may choose direct/depot movement; full routing may reassign trips.

Reuse unchanged `warm_replication/qp_control.py.solve` and
`economic_recourse_pilot/miqp_control.py.solve`; no copied sibling solver, added
completion/polish call or alternate optimizer. A restricted NativeCase is explicitly
identified as a movement-subset view. Re-identify the input plan for that view,
then restore the original case identity and independently replay every retained
endpoint in the full physical case. Check exactN and the fixed ordered duties.
The restricted bound, if present, is not a full-graph bound. Do not mutate frozen
helper sources or relax extraction/replay tolerances.

Each QP requires a timely fresh physical candidate, native OPTIMAL and existing
source/copy guards. Its returned U can be old B, not unreturned C/native N.
If QP qualification fails, preserve both dependent assignments as missing; no cold
substitute. MIQP supported-status physical delivery may qualify without OPTIMAL;
native status/gap and strict success stay distinct. Preserve fallback on ordinary
failure. Attribute/copy/configuration failure stops onward without automatic retry.
Same-movement-path improvement beyond the existing source agreement guard is a
discrepancy, not reassignment value. Report fixed-duty mode changes separately
from changes to the ordered service duties.

Operational references: unchanged constructive reference and paid target-QP U.
Record absolute original-lens costs, all three cross-valuations, ops/fleet,
service+movement/grid energy, linear/quadratic terms and period loads. Main
contrasts: QP→fixed-duty; QP→full; fixed-duty→full, alongside their complete
success/missing/fallback states. Complete reporting needs all four contexts, with
contrasts reported separately in each target institution. Do not pool target
costs/gains across institutions or count the three b=0 aliases as replicated solves.
One base is one descriptive unit, not four independent cases. No invented
economic promotion threshold, new training, statistical significance or equivalence.

## Selected resources and next admission

NEW package1500CPU/2400wall, dispatch1320CPU/closure180CPU. Twelve workers at most,
hard90CPU each, native52/final parent admission60/cleanup3 seconds from parent
before Popen. One worker/native thread, observed worker RSS≤5GiB. Reserve all three
workers before starting a context. Preflight/source preparation≤60CPU and final
publication≤60CPU/90wall are inside the total; source preparation suballowance
10CPU/30wall. Source checks, construction, imports, build, search, replay,
publication and parent admission are paid. Each QP→MIQP comparison branch has two
paid anchors and continuous latency, not a single60s method or a cold-speedup claim.
A complete context has three workers/three anchors; all are charged once.

Next implement only fixture/economic/duty adapters, thin worker and owner reusing
the current bounded execution pattern; no new monitoring framework. One focused
integration review must fix exact source/import closure, literal input fields,
command, namespace `attempt01`, funding and prospective source-bound launch.
DRAFT/PENDING must refuse fixture generation and dispatch. Hash consumed sources
once within a metered preparation/batch, never an independent reviewer hash pass.
Review completed receipts before any subsequent study. Old numerical charges
remain19923.95 displayedCPU/20520.60elapsed-sum, retained19924.31CPU, with separate
legacyguard2546.091499549272 and old reviewCPU UNKNOWN; this design adds no measured
numerical spend and reopens no closed package.
