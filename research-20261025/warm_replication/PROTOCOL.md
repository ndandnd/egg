# Prospective eight-group fixed-fleet warm study with a strong charging control

Prospective selected protocol,25 October2026. Execute only the separately frozen
LAUNCH.json command after the affected source reviews pass. This protocol does
not alter the completed warm experiment, QP diagnostics, earlier protocol,
cohort-selection history or post-result critique. No numerical work was performed
to prepare it.

## Question, cohort and fixed methods

Does the fixed GNN replanning policy retain a useful operational advantage on new
development groups after controlling for a competent constructive pool and
direct convex charging optimization on the known prior topology? Separately,
does target-price scoring improve decisions over the same GNN scored with the
original day prices? These are conditional warm-policy and inference-conditioning
questions, not trained-price-information causality or a novel pruning theorem.

Use exactly base IDs **50604,50606,50607,50608,50609,50610,50611,50612**, in that
order, with40/80-trip nested variants and native seeds17/41/73. There are eight
base-group units,16 physical variants,48 case/seed blocks and384 active decisions.
IDs were selected from the permitted prior-use metadata before generating these
cases. If a later exposure is discovered, retain the ID and disclose it; no
outcome-selected replacement. Do not pool the preceding four groups into this
new-cohort gate or treat the48 repeated size/seed blocks as independent groups.

Keep the unchanged generator. Check shared trip/induced-movement records during
measured generation. Preserve one connector and the existing size-scaled power
rule180kW at40 trips/270kW at80. Within each variant, day→late shifts the linear
price vector a; b and the physical case stay unchanged. The size contrast is not
a fixed-resource scale experiment.

Canonical active arms, in order:

`GNN, CatBoost, CA1, CoverCA1, random, full, fixed_route_QP, GNN_day`.

`fixed_route_QP` **replaces**, rather than supplements, the old capped
`fixed_route` arm in this new study. The old control remains honestly labeled in
old results. GNN is the prespecified primary learned family; CatBoost is
secondary and reported separately. Keep both classical pools, random and full
even if another arm appears stronger. Do not select a winning learned family,
checkpoint, numerical method or quota using these new outcomes. No fitting,
feature change, calibration, ensembling or new model family is allowed.

## Common prior, physics and candidate masks

Acquire ONE predetermined CoverCA1 day prior per variant, seed17, with the same
pure fleet-count acquisition objective and original physical model. There are16
acquisitions, with preparation30/native90/native-cap60/final120-second boundaries.
Do not select a cheaper prior from several seeds, repair acquisition failure,
replace the case, or retry. Measure acquisition separately from warm replanning
and include it in the study resource total. A missing prior makes all assigned
decisions for that variant genuinely missing, not zero-cost or silently excluded.

Every active arm receives the same physically replay-valid prior for its variant
and fixes active fleet count to that prior's count. Preserve original battery,
SOC/reserve, efficiency, terminal, charging and shared-resource constraints.
Optimize integrated system cost `operating + a·L + .5*sum(b_t*L_t²)`, not the
atomic all-units marginal-price payment objective.

Restricted arms use the unchanged price-blind base B and **original**
`K=min(M,max(ceil(.30*M),|B|))`. With S0 the known prior's flexible movement IDs,
protect common Bw=B union S0. All boundaries remain. CoverCA1 also protects its
frozen route-only cover union C. Fill remaining slots using fresh arm scores to
exactly original K. If Bw or Bw union C exceeds K, preserve the design failure
and fallback; do not increase quota or dispatch a substitute method. Record
baseB/S0/Bw/K, cover extras, fill/exposure counts and pool overlap. Successful
masks must contain the common prior. Full uses all original movements at the
same fixed fleet; it is not an unrestricted variable-fleet certificate.

GNN and CatBoost use the existing locked checkpoints/preprocessing and observe a,
not b. CA1/CoverCA1 policies stay fixed. Random's deterministic case/seed/movement
ordering remains price/stage blind. Every model object and preprocessing input
is loaded anew inside the decision clock; OS caches need not be cold. No old
chosen score vector or pool is reused.

GNN_day freshly scores with **a_day**, using exactly the same fixed GNN, feature
transform and mask contract as GNN, then optimizes **the late objective**. GNN
scores with a_late. The difference is inference-time ranking conditioning; it
does not replace comparably selected trained tariff-blind models. If warm
protection exhausts K or both scores retain identical pools, record that lack of
exposure/adaptation instead of changing K or the feature set.

## Strong fixed-route QP and other optimization policies

For every fixed_route_QP assignment use a **fresh worker and one direct QP**,
uniformly Method=0, on the common prior's exact topology. This is not a casewise
choice between the seven earlier v2 outcomes and the later one-case method
diagnostic. The replication-local helper is a narrow copy of frozen v3: its seed
guard admits only prospectively assigned17/41/73, and each actual outer seed and
Method0 are set/read back. The frozen diagnostic helper remains17-only and
unchanged. Do not reuse a QP solution across the three assigned seeds.

Clone the original stored path-flow matrix into the public QP API with every
routing variable fixed to the prior's0/1 value. Fixed routing variables may be
continuous singleton bounds. Preserve all finite bounds, nonzero coefficients,
senses/RHS, index/type checks, documented side-specific infinity semantics and
the exact sparse linear/diagonal-quadratic objective. Keep numerical accuracy
settings, original-index snapshot facade, unchanged extraction/roundoff/decoder,
physical replay and objective-consistency guards. No charge clipping, interval
extension, physical relaxation, repair solve or second optimize call.

Record Method, seed, native status/solution count, quality attributes, call counts,
copy contract, physical candidate admission and parent-timely eligibility
separately. A finite nonoptimal incumbent can be replayed and retained provisionally
within the admission window. Numerical OPTIMAL alone is not a feasible bill;
unsupported/raw bounds remain telemetry. Require a physical admitted candidate
for candidate-cost comparisons. Strong numerical QP success requires OPTIMAL
plus the unchanged physical/admission checks. A valid fallback is still available
after failure, but must not be labeled a converged QP solution.

The other ranking/full arms retain the fixed existing supporting-tangent and
completion policy, warm prior/zero-load tangents and fixed-fleet equality. The QP
arm intentionally uses a stronger specialized continuous optimizer. Therefore
this comparison is between complete operational policies under a common clock,
not a pure ranker-only or same-backend algorithm ablation. Record all actual
native/completion calls; do not force equal call counts by adding work to QP.

## Clocks, retention, assignment order and failures

Each active assignment has one60-second inclusive clock anchored by the parent
before process creation. Native cutoff52 leaves admission/publication time; all
imports, cold loading, scoring, model construction/copy/readback, native work,
extraction, replay and durable output are paid. Native time-limit overrun is
recorded; a returned candidate may use remaining admission time, with no extra
call or deadline extension. The parent must observe worker exit and complete
receipt read within60, not rely on a prewrite timestamp. One native/computation
thread, observed peak RSS<=5GiB, existing bounded cleanup only; no new timing or
transport controller.

Retain/reprice/replay the common prior inside every decision before new work.
Keep an independently admitted improvement before later ordinary failures where
the established admission interface permits. Operational intention-to-treat cost
is the best parent-admitted physical plan, or the pre-existing valid prior after
late output, crash, no useful candidate or selection failure. Method success,
native search completion, physical admission, lateness and fallback use remain
distinct. Missing acquisition never becomes an available fallback. Raw numerical
objectives, rejected points and missing packets never substitute for physical cost.

All384 assignments remain in the ledger, including undispatched tasks after
funding/fatal stops. No automatic retry, changed order, replacement or extra
seed/time/quota follows from a poor outcome. A fatal configuration, source,
identity, resource or admitted-physical-contract violation stops later dispatch
and prevents the continuation gate, including a fatal final assignment.

For block `b=((group_index*2+size_index)*3+seed_index)`, rotate the canonical eight
arms left by b mod8 and reverse when floor(b/8) is odd. Across48 blocks, every
arm occupies every position six times. Do not claim balanced carryover effects.

## Prespecified readout and continuation rule

Report all arms and unchanged prior, all assigned/attempted/accepted/method-success
and missing/fallback/fatal/late counts, native/QP status and candidate qualification.
Show absolute integrated cost, vehicle operating cost, deadhead, linear and
quadratic electricity components, total grid energy and change from the unchanged
late-repriced prior. Fixed vehicle count removes fleet acquisition as an
explanation; it does **not** remove deadheading/energy-demand differences.

For learned family L and control C, define

`d=(operational_cost_C-operational_cost_L)/E0`,

where E0 is the same prior's **late-tariff electricity cost**, not total bill or
candidate electricity cost. A positive d favors L. This is a total integrated-
cost difference normalized by E0, not necessarily electricity savings. Preserve
exact stored costs. Missing prior or zero E0 leaves the comparison undefined.

Each base-group median uses all six observations (two sizes × three seeds).
The paired mean uses all48 planned comparisons. No available-only mean or partial
group median can satisfy a gate. Report wins, ties/near-zero values, losses and
loss tails alongside means; no exclusion of failed methods whose operational
fallback remains available.

The **primary GNN continuation gate** requires BOTH comparisons, against CoverCA1
and fixed_route_QP, independently to have at least **six of eight strictly
positive complete group medians** AND exact mean d **greater than0.01** over all48
pairs. Ties do not count as positive. Before either criterion can pass require:
all16 predetermined priors valid/admitted; all384 assignments attempted and
recorded; complete comparison denominators; campaign passed/complete and complete
accounting; no stop/unresolved-child reserve; no fatal configuration/resource/
identity/contract flags or invalid physical admission, including in the last task.
An uncompleted study cannot pass by showing only available comparisons.

**Additional prospective strong-control prerequisite, chosen before any new
cohort outcomes:** all48 fixed_route_QP assignments must have a timely,
parent-observed physically admitted QP candidate AND native OPTIMAL status.
Neither a retained-prior operational endpoint nor raw OPTIMAL without physical
admission qualifies. A valid nonoptimal candidate remains reported/provisional,
but does not satisfy this prerequisite. If any of the48 fails qualification,
retain all384 operational analyses and their failures, mark the control gate
false and the primary learned continuation **inconclusive**, and do not credit
learning for charging-control/materialization failures. Do not retry or replace
the failed control to complete the gate. This new-cohort rule leaves the original
four-group exploratory gate and results unchanged.

Compute the same prespecified criteria for **secondary CatBoost separately**;
do not substitute it for GNN or choose the better learned family after these
outcomes. Also report CA1, random and full comparisons even though they are not
the two gate comparators. A gate pass is a research-direction diagnostic, not
significance, robust superiority or model promotion. Both learned families share
the additional all48 strong-QP qualification prerequisite. Operational contrasts
remain descriptive even when that prerequisite fails; no available-only qualified
QP subset can restore continuation. Even a fully qualified positive result is
conditional on this fixed-fleet problem, clock and cohort, not a broader optimality
or learned-information claim.

For GNN versus GNN_day report all48 point/normalized differences, eight complete
group medians, wins/losses/near-zero counts and pool overlap/exposure. Keep the
existing descriptive `|d|<=1e-6` near-zero convention separate from the gate;
there is **no automatic promotion threshold** for this conditioning contrast.
No causal trained-information claim follows from either contrast.

## Resource direction and launch prerequisites

Prospective total: **8CPUh=28800 seconds /10wallh=36000 seconds**, including
source/asset preflight,16 acquisitions,384 decisions, startup, failures, shutdown,
accounting and finalization. Dispatch stops at28200CPU, leaving600CPU closure
reserve. Compact finalization/byte-only baseline preservation is at most120CPU/
180wall **inside** that closure provision. One local worker/native thread and
observed5GiB. Funding stops preserve unattempted assignments, not an automatic
larger budget. These are design constraints, not an executable reservation or
a reconstructed carried ledger. Parent must bind actual accounting prefixes,
funding checks and the concrete command separately; no historical charge is
refunded or assumed zero by this draft. No budget approval question is pending.

Before launch, reconcile the arm label and QP policy across cohort manifest,
caller/scorer/helper, finalizer, status and final protocol; bind exact current
sources, existing selected model/preprocessing bytes, input/cohort metadata and
public solver version policy in one metered preflight batch. The local seed-guard
change and Method0 set/readback need focused static integration review. Keep
inherited provenance honest; do not repeat broad old source/hash/test matrices.
Preserve the established independent replay and count the inherited backend
fingerprinting cost. Parent reviews this draft/critique and freezes the final
manifest, source/asset assumptions, admission/failure rules, resources and exact
command. Until then, STATUS remains HOLD.

No new training, cluster/sealed/protected sources, wider sweep, market-equilibrium
claim, recovery/certification stage or manuscript/publication action is authorized.
Eight deterministic development groups, one tariff change, nested sizes with
scaled resources, a-only learned features and possible demand changes limit what
can be concluded even if all numerical criteria pass.

## Parent source, data-admission and resource freeze addendum

This addendum supersedes draft-only administrative language above. Numerical
dispatch is authorized only through the exact LAUNCH.json after SOURCE_REVIEW_QP
and the affected TRAIN-admission/pool-report reviews pass. All source/model/input
bytes remain frozen until the campaign closes. No old study or passed source
matrix is repeated. The separately frozen finalizer command runs once only after
the owner exits and its external process meter is final; its allowance is inside
the selected total and closure reserve, not added afterwards.

Use the existing five selected checkpoint/preprocessing assets specified by
the immutable warm_replanning/scoring.py expected_assets function and
research-20261017/local-assets-v3.json. Verify their pinned bytes once in the
ordinary metered campaign preflight. No fitting, early stopping, new checkpoint,
ensemble, feature family or data-driven model selection occurs. GNN_day loads
the same GNN objects freshly, altering only scoring a before the same late solve.

Also bind ONLY the exact TRAIN pool manifest
/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/pool_manifest.json
once in that same preflight. After the five assets verify, parse only the two
preprocessors' fit/inner/outer group identifiers and CatBoost's pool manifest
digest. Require the registry digest to match that pin and train_only=true.
Require its actual group_eligibility base_group→integer base_id mapping to be
unique, cover both models' declared group union, and be disjoint from planned
base IDs. Failure stops before any acquisition, with all assignments preserved
as missing; no group replacement or unreceipted retry. Never open row tables,
labels, source_inputs.jsonl or DEV/TEST/sealed indexes. A pass supports only
source-bound declared TRAIN base-ID nonoverlap, not global/variant alias closure
or new population transfer. Preserve that scope in the preflight and readout.

Record GNN/GNN_day retained flexible-ID pool overlap and free ranking exposure
from already computed selections; do not put arm-specific pools in the common
B/K contract. Identical pools or exhausted ranking room remain informative,
with missing-pool denominators shown. Do not attribute solver/clock variation
between identical pools to learned price information.

The day prior is acquired by pure fleet count and is not a proven day-economic
optimum. This is conditional replanning from a common feasible prior; no claim
of benefit after an optimal day schedule or a realistic market shock follows.
The strong late charging control addresses charging optimization on that known
topology, while both classical routing controls address changed connections.

Before this numerical campaign, closed process accounting is7064.41CPU/
7239.65elapsed-sum, including the separately closed.02CPU/.04elapsed metadata
inquiry; see PREPARATORY_RESOURCE_RECEIPT.json. Do not charge that historical
sum again into the NEW prospective8CPUh/10wallh numerical campaign. Its own
preflight, acquisitions,384 decisions and finalization are all included in that
new total. Preserve all historical costs, the separate2546.091499549272
conditional guard and UNKNOWN actual old reviewCPU. Rounded process sums do
not measure exact whole-session CPU or continuous elapsed. No cap reset or
restored historical compliance is claimed.
