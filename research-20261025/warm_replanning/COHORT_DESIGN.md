# Prospective warm-replanning cohort

25 October 2026. Static design only: no case generation, import, test, hashing,
solver call or outcome inspection. Parent accepted the fixed IDs below. The
companion [GROUP_MANIFEST.json](GROUP_MANIFEST.json) freezes the selection and
ordering rules; source/asset digests, case identities and numerical commands
must still be bound prospectively before execution.

## Fixed groups and prior-use rule

Use base IDs **50600, 50601, 50602, 50603**, with both `scale:<base>:40` and
`scale:<base>:80`, native seeds **17, 41, 73**, and all variants kept within their
base group. The outcome-blind rule is ascending IDs in 50600–50999, excluding
bases named in the checked prior-use metadata, then taking the first four. No
regime, score, generated timetable or outcome was used to choose among them.
This is a deterministic convenience sample, not a random representative draw.

The October17 v2/v3 local-assets manifest cohorts list 22 exposed scale bases;
none of these four is listed. Checked October23 recovery v1–v7 and preparation/
comparison/CF1 design metadata name 50997/50999, and October24 repaired design
metadata reuse 50997. The current handoff identifies later pilots as reuse of
50685/50605. TRAIN pool/group metadata use physical-v2 10000-series groups rather
than these scale keys. Exact inspected file paths are in the manifest.

**This prior-use search is not globally exhaustive.** Filename inventory found
no complete historical scale-exposure register. No old result, score, selected
route or protected bank was opened to resolve that limitation. If later metadata
reveals prior exposure, retain these IDs and disclose it; do not replace a group
using its performance. Describe them as prospectively selected development
groups absent from the inspected registers, not proven never-seen evaluation.

## What is genuinely nested

`claude_cases.make('scale:<base>:<services>')` delegates to
`claude_scale_cases.make_case`. Its duty draws depend on generator/base/duty/
field, never on service count. For a fixed base, the 40-trip records T001–T040
are therefore exactly the first 20 duties of the 80-trip case, including times,
locations and energy. Movements between those same trips and their boundary
modes have the same IDs and physical data; their positions in the full movement
list need not be a prefix because all boundaries precede intertrip modes.

Keep the generator unchanged. These are **nested timetables with size-scaled
resources**, not fixed-resource nested physical instances: the single shared
connector and grid power are `90*ceil(services/28)`, hence 180 kW at40 and270 kW
at80; max_vehicles changes too. Larger variants add later duties as well as more
trips. Do not attribute a size contrast solely to trip count, computational
complexity or fixed-capacity congestion. Static source reasoning should be
confirmed by one metered generation-time comparison of shared trip/movement
records, without changing a group on failure.

Within each fixed size variant, **day to late changes only market coefficients**.
Trip/movement records, battery/reserve, charging resources, market period edges,
terminal windows and efficiency must remain identical. That within-variant
intervention is the warm-replanning comparison; the 180/270 kW scaling is only
across sizes. The generator borrows physical regimes from TRAIN assignments and
uses a stylized two-location duty system and one connector; four new base draws
do not establish transfer to new physical populations or real operations.

## Frozen arms and balanced order

Active arms are `GNN, CatBoost, CA1, CoverCA1, random, full, fixed_route`;
`unchanged` is a zero-work reference, not an eighth active solve. Four groups ×
two sizes ×three seeds ×seven arms gives168 active decisions and24 reference
blocks. Acquire one predetermined day CoverCA1 prior per size variant, separately
accounted and shared across all target seeds/arms; preserve failed acquisition as
missing endpoints for every assigned arm without replacement.

Enumerate groups ascending, sizes40 then80, seeds17/41/73. For zero-based block
index b, cyclically left-rotate the canonical seven-arm list by b modulo7, then
reverse the rotated list when floor(b/7) is odd. Each full seven-block cycle puts
every arm once in every position; across24 blocks each arm occupies each position
three or four times. This balances position approximately, not every carryover
or machine-state effect. The unchanged reference is evaluated per block without
joining the active order. Do not reorder based on failures or observed timing.

## Controls still needing the executable protocol

Freeze the exact common B/K and boundary policy, economic objective and solver
schedule, cold model-load/scoring costs, admission reserve and full budget/stop
rules. All arms retain the same full-case replay-valid fallback; native start
eligibility is separate, particularly when prior-plan arcs are absent from an
arm's exact-K pool. Do not silently enlarge one pool or claim equal consumed
starts if a backend cannot use them. Fixed-route charging and unchanged-plan
references help separate charging response from route selection. Report all
assigned/missing/late endpoints, acquisition and replanning costs separately,
and group-level fleet/energy/electricity decompositions.

This diagnostic still lacks a comparably selected trained tariff-blind model,
resource/curvature interventions, and independent physical populations. Current
GNN input contains a but not b. Neither day/late sensitivity nor beating these
classical controls alone identifies learned electricity-information value.
Seeds and nested sizes are repeated measurements: the cohort has **four groups**.
