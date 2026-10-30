# Independent review of native-recharge attempt 1

27 September 2026. Frozen implementation/protocol:
`d37878392f0848d34f28921c97b6e8d8e6533a77`.
Original evidence manifest SHA-256:
`9e8f76cbfabf7d7387792f9305123aaaf9cb7da4e0e47108279b001f47bb71db`.

**The first qualification remains FAILED: 12 of 15 controls passed.**
The independent audit passes the narrower claim that the archived results and
failure accounting are consistent. Nine controls produced accepted numerical
certificates; three correctly reported the prospectively expected infeasibility;
three failed during physical extraction/replay. None of those failures is
reclassified, retried, repaired in place, or omitted here.

The reviewer saw the prospective targets and frozen implementation; this is an
independent reconstruction, not a blinded review. The reviewer authored a
standalone standard-library auditor with no author-module
imports and no optimizer. It verifies all 107 manifest-listed raw files, frozen
Git source hashes, input/case identities, every returned native objective/bound,
all archived physical witness instances, tangent history and controller receipts.
The original 107 files and original manifest are unchanged. Derived review files
have a separate manifest in this directory.

## What was independently checked

| Item | Result |
|---|---:|
| Declared and attempted controls | 15 |
| Accepted certificates | 9 |
| Correct expected infeasibilities | 3 |
| Preserved extraction/replay failures | 3 |
| Native calls started and returned | 28 / 28 |
| Raw native statuses | 25 OPTIMAL; 3 INFEASIBLE |
| Finite native objective/bound pairs minimized independently | 25 |
| Archived physical witness instances replayed | 22 |
| Charging sessions checked | 49 |
| SOC events checked, excluding initial state | 174 |
| Corrupted copies rejected | 12 |

All calls returned; no hard timeout, missing status, truncated artifact or retry
is recorded. Native solve time sums to 20.409328292123973 seconds. Controller
elapsed time is 23.573551082983613 seconds. A native phase slightly exceeds its
requested ten-second cap in two receipts, consistent with the protocol's soft
native time cap and separate sixty-second process cap. All raw statuses are
OPTIMAL or INFEASIBLE; this run does not exercise the prospective FEASIBLE-bound
admission path on an actual backend.

The nine accepted interval widths range from
`1.999999966528776e-6` to `2.0000000944264684e-6` objective units. Every interval
contains the independently minimized physical objective for the frozen fixture.
These widths primarily reflect the prescribed two-sided `1e-6` guard. They are
not an empirical estimate of model accuracy, nor a claim that the underlying
solver generally proves an exact interval of that width.

| Control | Independent target | Original disposition |
|---|---:|---|
| single_linear | 22 | Certified |
| efficiency_linear | 433/19 | Certified |
| cyclic_flat | 37 | Certified |
| cyclic_own_price | 134 | **Failed extraction** |
| cyclic_hull_price | 153.5 | Certified |
| cyclic_planner | 97 | Certified |
| preserved_reserve_planner | 97 | **Failed replay in round 1** |
| joint_flat | 733/19 | Certified |
| joint_planner | 38527/361 | Certified |
| fixed_reserve_planner | 99 | Certified |
| fixed_reserve_one_bus | Infeasible | Expected infeasibility |
| terminal_capacity_failure | Infeasible | Expected infeasibility |
| partial_overlap_failure | Infeasible | Expected infeasibility |
| serial_connector | 24 | **Failed replay** |
| directed_multileg | 36 | Certified |

The displayed rational targets use the intended decimal parameters. Exact
binary-rational minimization of the actual stored floating coefficients agrees
with these targets to better than `1e-10`; the audit retains the exact binary
rational rather than silently replacing the input efficiency or curvature with
a nearby decimal fraction.

## Independent global objective reconstruction

This audit is stronger than checking whether a native lower bound is below a
replayed incumbent: it independently minimizes the linear and saved PWL
objectives for these small fixtures. It does not solve a general native MILP.

For the two sequential 15-kWh cyclic services, every feasible bus serves either
A+B, A only, or B only. Hence the complete fleet consists of one paired bus or
two separate buses; the declared direct mode cannot carry both services without
recharge at these usable capacities. The inactive extra buses have no path and
cannot donate energy. Let efficiency be eta, capacity C, reserve r, and early
connector power P. All selected travel consumes zero in these fixtures. Total
grid recharge is `T=30/eta`. With early grid energy x, the load vector is
`(0,x,0,T-x)`.

The one-bus projection is

`max(0, (30+r-C)/eta, T-30) <= x <= min(P,15/eta)`.

The two-bus projection is

`max(0,T-30) <= x <= min(P,15/eta)`.

Only the A-serving bus can charge early. Post-A capacity bounds its gain by
15 battery kWh. The lower bound `T-30` enforces the one finite terminal
connector's available energy. For a paired bus, the additional reserve
inequality gives `(30+r-C)/eta`. For separate buses the late energies are
`15/eta-x` and `15/eta`: nonnegative and schedulable consecutively on the
30-kW terminal connector precisely when their total is at most 30. Early
charging uses one bus and one connector. Thus every point in these intervals
has a constructive physical schedule, and every physical schedule projects
into them. Fleet intrinsic costs are 7 and 14 respectively. Fleet cap one
removes the second branch.

This yields a complete one-dimensional branch minimization. Linear objectives
reach a branch endpoint. True quadratic objectives require only the endpoints
and any interior stationary point. For a saved PWL envelope, the auditor uses
exact rational arithmetic to enumerate endpoints and every within-period
intersection of saved affine pieces. The sum of maxima is affine between these
breakpoints, so this candidate set contains a global minimum on each interval.
Both branches are compared. Every saved native start snapshot is checked against
the tangent sequence generated by the previously archived load. This includes
the failed reserve control's second-round PWL objective, although that native
incumbent has no archived physical witness.

The other fixtures have independent elementary reductions:

- A single service and fixed directed travel have fixed total grid recharge;
  all recharge occurs in the last market period. The multileg control consumes
  8 service plus 6 travel kWh, with intrinsic cost 7+15=22, giving objective 36.
- Two simultaneous services require two buses and 10 grid kWh. From minute 30
  to deadline 60 the one 10-kW connector supplies only 5 kWh, proving
  infeasibility. Deadline 90 gives exactly 10 kWh of capacity, with loads (5,5)
  across the two market periods and intrinsic cost 14, giving objective 24.
- The terminal-capacity negative control needs 15 grid kWh but has only 10.
- The fixed-reserve one-bus control needs 11 early battery/grid kWh but has only
  10 available, so the single allowed branch is empty.

These reductions establish the expected infeasibilities without relying on CBC.
They also independently reproduce all 25 finite native objective/lower-bound
pairs within `1e-6`. This is conditional on the frozen declared fixture graphs;
it does not establish unrestricted source-graph completeness or global pricing
for an arbitrary operational input.

## Physical witness conventions and checks

The independent replay uses the stored floating session times and energies
unchanged. There is **no rationalization, energy clipping, endpoint snapping,
negative-charge repair, or deletion of small positive sessions**. It checks
complete service coverage, movement ownership, native charge windows, vehicle
travel/service exclusions, strict pairwise connector disjointness, each resource
intersection's power/energy limit, grid-period load, travel cost, all SOC events
and full replenishment. Pairwise session disjointness is a separate implementation
from the author's active-set sweep. Stored SOC traces, replay summaries, raw
solver aggregate loads and intrinsic costs are compared against reconstruction.

The physical tolerances match the frozen `1e-6` kWh and `1e-7` minute convention.
Resource comparisons allow at most `1e-6` kWh over each intersected resource
segment. No positive connector overlap is admitted. Charge completion precedes
a simultaneous instantaneous outbound consumption event. The largest observed
SOC-bound residual is `1.1013412404281553e-13` kWh; maximum reconstructed power
is `30.000000000000014` kW. Those values remain visible rather than being
presented as exact rational feasibility. Twenty-two means archived witness
*instances*, including each saved planner round, not 22 distinct operating
schedules. Copies of the same round in events/result are required to agree.

For each saved planner round the audit checks native incumbent versus saved
PWL envelope, envelope versus true cost, outward lower/upper guards, saved
epigraph slack, and final best-bound/physical-witness selection. The final
accepted intervals are additionally compared directly against the independent
exact binary-rational optimum. General numerical solver certificates still
remain solver-conditional; this fixture-specific analytical check does not
validate arbitrary future native bounds.

## The three failures and evidence limits

`cyclic_own_price` returned native OPTIMAL with objective/bound 134 before
raising `Negative/nonfinite extracted native charge`. The frozen optimizer
wrapper normalized its returned numeric fields; the available exception and
source show a charge failed the decoder's finite/nonnegative check. The failing
charge's value, owner and magnitude were not archived. We cannot establish
whether it was a tiny negative numerical residual, a material negative value,
or which full incumbent assignment produced it.

`preserved_reserve_planner` saved one valid round-0 physical witness (two buses,
true cost approximately 104) and then returned native OPTIMAL PWL value/bound 77
in round 1. It raised `Simultaneous charging exceeds connector/vehicle count`
before saving that second witness. The earlier valid witness remains part of
this audit; the cell remains failed.

`serial_connector` returned native OPTIMAL value/bound 24 and then raised the
same connector exception. It saved no physical incumbent witness.

The frozen decoder allows an interval endpoint to exceed its boundary by up to
`1e-7` minute, then starts the next interval exactly at its boundary. A pure
arithmetic example shows that `5.000000000000002` kWh at 10 kW over a nominal
half-hour yields end time `60.000000000000014`, creating an overlap with the
next interval. This is a plausible mechanism, identified separately by the
author, not a reconstruction of either failed incumbent. The missing raw
variables prevent a causal diagnosis. Native objective agreement cannot replace
those missing physical witnesses or convert a failed control into a pass.

Any subsequent attempt needs raw incumbent variables and their mappings flushed
before extraction, plus a prospectively documented rounding/endpoint policy.
Positive energies must be preserved, repairs must be explicit and quantified,
and an unrepresentable positive-duration session must fail. New source requires
a new freeze and a separately preserved attempt. The present review does not
approve a hidden repair or relabeling of this first run.

## Corruption controls and reproduction

Twelve deliberately corrupted in-memory copies are rejected: charge energy,
connector overlap, saved SOC, saved load, intrinsic cost, native lower bound,
final interval, raw status, tangent history, case identity, failed-cell status
and a missing returned call. Original files are never mutated for these checks.

From the research worktree, with Python and Git:

```sh
python3 -B result/native_recharge/20260927-attempt1/review/audit_native_attempt1.py --repository .
```

The default result is an exclusively created, uniquely named temporary file;
its path is printed. `--out` accepts only a new path outside Git repositories.
For a copied auditor, pass `--attempt` and `--repository` explicitly. The auditor
reads frozen Git objects only to verify hashes; it never imports their code.
No CBC, Gurobi, Python-MIP, NumPy or author package is required. The archived
`audit-result.json` was copied here separately after this command succeeded.
Only audit runtime should change when rerunning the same auditor revision.
