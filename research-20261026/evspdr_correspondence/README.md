# EVSP-DR-to-EGG correspondence: the model exists; the interfaces differ

26 October 2026. This is a completed source correspondence and a prospective
implementation package, not a numerical result. The human's correction stands:
service/fleet commitments, charging restrictions and separate strategic/system
economics already exist in the project's foundation. The scoped learned-policy
negative results do not establish a permanent negative for neural route prediction.

Read `PHYSICAL_INTERFACE.md` for the constraint matrix, `ECONOMIC_INTERFACE.md`
for the objective translation, and `ORACLE_CONNECTION.md` for the actual callable
boundaries. These identify four concrete differences rather than a missing problem:

1. The registered EVSP-DR oracle has station-specific powers and plug occupancy,
   covering/partition choices, fixed duties, fleet caps and terminal policies.
   Native EGG is an explicit one-depot/one-connector, exactly-once, full-recharge
   abstraction. Those feasible sets cannot be treated as interchangeable.
2. EGG's recent fixed-path QP fixes charging-visit choices. EVSP-DR's fixed-duty
   comparator preserves service order while allowing charging visits/times to
   change. This leaves a meaningful intermediate control untested by recent pilots.
3. EGG's earlier local `Instance` path already has a fixed-sequence analogue and
   strategic/planner objectives. It is not an implemented import of the adjacent
   EVSP-DR oracle, and it has different terminal/resource semantics from NativeCase.
4. Native system-cost helpers can express posted/strategic/planner objectives by
   an explicit coefficient translation with background U. The original market
   and true institutional valuations must remain visible; current GNN inputs do
   not automatically gain b/U information through this mathematical translation.

`STUDY_DECISION.md` selects a NEW literal synthetic diagnostic, implemented only
under `research-20261026/duty_market_seam`: twelve assignments on one base, comparing
fixed paths, fixed duties and full exact-N routing under four declared economic
contexts. It is a test of model/control correspondence, not an EVSP-DR deployment,
population benchmark or reason by itself to fit another model. No original TRAIN,
GIRO or held-out input is used. No prior case/failed gate is rerun or replaced.

Implementation/launch state and precise next action belong in `HANDOFF.md`.
All historical numerical outcomes, failures and accounting remain immutable.

Source provenance: EGG inspection started at
`7c3188541c5dbdef2e1fb1f6150645db959f8b67`. The registered adjacent checkout HEAD
is `3a0ab6a8ab50e4af7d5a7be7688d5ffa1fbbf78c`; a scoped `git diff --name-only HEAD`
reported no changes for the five named capacity/fixed-duty/event/power/pricer
source files. This is source-inspection provenance, not data/fixture/runtime
equivalence or a hash audit. No adjacent runtime is imported by the selected seam.
