# Next comparison: does prediction add useful search guidance?

Prospective design, 24 October 2026. No cases generated, assets opened, inference,
training, solver calls or numerical checks performed for this package. This
addendum supersedes the **unlaunched** question, arm/cohort counts, retention rule,
primary estimand and resource plan in `RECOVERY_STUDY_DESIGN.md`; preserve that
proposal as history. It incorporates the three companion design/source notes and
`RECOVERY_STUDY_ADVERSARIAL_CHECK.md`, with the changes below taking precedence.
It is not an executable manifest or evidence of a better model.

## Why this question comes first

Historical 80-trip savings mostly reduced vehicle cost. The frozen comparison
heuristic did not see tariffs, whereas graph-v8 and CatBoost receive linear
prices `a`. Neither receives curvature `b`; native charging uses both. We need
to distinguish useful prediction from graph reduction, fleet construction and
the optimizer's own charging response. Model input availability alone proves
none of these effects.

The primary comparison is frozen graph-v8 recovery versus the proposed CA1
charging-aware ranking with recovery. Direct secondary comparisons are graph
versus frozen CatBoost and versus the CF1 constructive proposal. Random recovery
and cold unrestricted eight-round search remain reference arms: **six arms**.
All are complete timed methods, including their scoring and initialization.
CA1/CF1 are explicit, unvalidated candidate classical controls, not a claim to
exhaust strong classical methods. Winning this pilot would not settle that issue.

## Fix graph density before comparing rankers

Applying 30% retention and each ranker's top-three incident edges gives different
union sizes. The resulting contrast would mix scoring and problem size. For this
new study, use a common price-blind coverage backbone and an exact flexible-edge
count, without evaluating competing models in another arm for free:

1. Let `F` be the original flexible intertrip movement IDs, and `M=|F|`.
   Preserve every declared pullout/pullin boundary movement outside this count.
2. Use the existing frozen price-blind heuristic and movement-ID tie rule to
   take up to three flexible incoming and outgoing movements per trip. Their
   union is the same backbone `B` in every ranking arm and tariff variant.
3. Set `K=min(M,max(ceil(0.30*M),|B|))`. Each arm retains `B` and fills the
   remaining `K-|B|` slots from `F\B` with its own descending score, ties by movement ID.
   Random scores are keyed by base and solver seed, fixed across tariff variants.
4. Charge backbone construction, scoring and selection inside every arm's clock.
   Archive original/retained IDs, backbone and mask hashes, `M`, `|B|` and `K`.

This is a **new** common selection rule; historical outcomes under rank-specific
coverage cannot be pooled with it. The backbone is structural coverage, not a
feasibility certificate. If it consumes all `K` slots, the ranker has no remaining
choice: keep that case, label zero exposure and do not replace it. Equal edge
counts control density, not topology/search difficulty. Scoring time and the
chosen topology remain legitimate parts of the method contrast. The primary
test asks whether learning adds value *beyond this common classical backbone*.
It does not estimate the benefit of the historical pruning policy.

CA1 receives `a,b`; its proportional charging cost is a ranking proxy, not an
actual fleet bill or an admissible bound. This deliberately compares deployable
methods, not identical input information. Graph versus CatBoost has the same
price-feature interface. CF1 greedily merges routes, then attempts fixed-route
charging, replay and a binary-only full-model start; it is not a proved
minimum-fleet solution. See `RECOVERY_CLASSICAL_BASELINE_SPEC.md` for the bounded
algorithms. No new-cohort outcome may select their settings.

## Cohort, tariff intervention and common clock

Reserve eight fresh synthetic bases, four at 40 trips and four at 80, each base
at one size, with identity-only disjointness checks against recorded registries.
Do not open sealed data to check disjointness. Keep all variants of a base
together. Use solver seeds 17, 41 and 73 in all arms: **144 day-tariff decisions**.
These are development groups under shared generator physics, not external
confirmation. Four bases per size give limited population evidence.

Before outcomes, choose two bases per size by salted identity order for a
mechanism subset. Relocate cheap linear-price periods by a prespecified cyclic
permutation, preserving the `a` multiset, interval boundaries, `b`, physics and
movement set. Freeze the permutation rule and all identities before inference;
no shift chosen by label, bill or learned score. On the shifted target tariff,
cross graph/CatBoost with fresh-target versus original-day scoring inputs:
**48 additional decisions**, **192 total**. Both score conditions are recomputed
inside their clocks; both native optimizers and charging completions use the
same shifted target tariff. The original-day scores are not cached for free.

Record feature, score, ordering and retained-mask changes for every selected
base, including zero-exposure cases. In exact arithmetic a multiset-preserving
shift leaves global mean/spread and nonwindow CatBoost row features unchanged;
freeze numerical comparison tolerances before execution. Their relative ranks
can still change when other rows change. GNN messages may transmit neighboring
charging-window changes; this is a testable possible channel, not an observed
benefit. A `b`-only change has no direct frozen-scorer input channel. That limits
this nonlinear-planner surrogate, but is not a general criticism of a
price-taking oracle supplied its intended marginal price vector.

Use a 60-second total endpoint anchored before interpreter/model loading and
ending after replay, billing, captures and durable finalization. Retain the old
proposal's halfway acquisition boundary, completion/finalization reserves and
eight-round total cap; qualify their 60-second implementation without resetting
clocks. All ranking arms use the same recovery policy and full feasible set
after restoration. CF1 pays construction/completion before its full search.
No static arms: this design cannot identify restoration's causal benefit.
Pair base/seed blocks on the same Mac, hash-order blocks, rotate arm order across
two single-thread workers, and record resource/thermal context when available.
Do not compare local results directly to cluster outcomes as matched replicates.

## Budget: a cap that can terminate an incomplete study

The prospective ceiling remains 8 CPUh, at most two workers, 5 GiB each and
10 GiB aggregate. Concurrency saves wall time, not charged work. The separate
qualification remains capped at 900 seconds pending the existing user decision;
this document changes no limit and requests no new approval.

| Planned charge | Seconds |
| --- | ---: |
| 192 worker allocations at 62.5 seconds | 12,000 |
| Supervision/monitoring allowance | 12,000 |
| Source/baseline checks, freeze and preparation | 1,200 |
| Independent endpoint verification and analysis | 1,200 |
| Shutdown/audit reserve | 1,800 |
| Total planning envelope | 28,200 |

Hard ceiling 28,800; dispatch stop 27,000. The plan leaves only 600 seconds before
the dispatch stop beyond its nonshutdown components. The old native-v3 overhead
ratio is calibration evidence, not a forecast at 60 seconds/two workers/new
captures. This allocation **does not establish that 192 decisions will fit**.
Before dispatch, record a source-bound implementation/resource manifest, charge
preparation already spent, and admit each next allocation with supervision and
remaining analysis/shutdown reserves. If overhead or setup exhausts its envelope,
stop and report the complete prefix with missing suffix; do not cut unfavorable
arms or silently buy capacity. No automatic retries or 120-second extension.
Standing authorization covers routine work within the frozen budget after the
applicable engineering gates; it does not answer the pending qualification-cap
question. This proposal is not a launch manifest.

## Endpoints, attribution and decisions

For each primary graph/classical pair, a timely replay-valid plan beats a genuine
algorithmic no-plan or algorithmically late result. Both genuine algorithmic
failures tie. With both valid, use the symmetric practical bill tolerance
`0.005*max(abs(B_graph),abs(B_control),1 currency unit)`; compare lower bills
outside that band. Record wins/ties/losses, first average the three seeds within
base, then give each base equal weight and each size equal weight. Seeds are
not independent timetables. Infrastructure-unknown or undispatched endpoints
remain missing, with each missing seed contribution bounded in [-1,1]; never
score them as graph wins or both-invalid ties. A valid result paired with an
infrastructure failure is still a scientifically missing comparison. Report
all operational reliability counts separately and classify causes from receipts,
not from the favored arm's bill.

Cause precedence is fixed prospectively: evidence of clock/ownership/monitor,
serialization-integrity or unexpected native-interface failure triggers an
engineering stop and an unknown primary outcome. Ambiguous causes are unknown.
Only a complete, healthy receipt chain can classify an ordinary deadline stop,
no replay-valid witness or policy-compliant finalization that runs late as an
algorithmic endpoint. Healthy replay/capture/write latency belongs to the timed
method; a demonstrated broken capture contract belongs to engineering failure.
Rejected candidates stay in the ledger and a timely valid fallback still counts.
An invalid *admitted* witness stops the study; it is not a bill or a primary win.

Primary practical net-win contrast: graph versus CA1. Direct secondaries: graph
versus CatBoost and CF1. Report per-base/per-size outcomes and worst regressions;
any inferential analysis must be frozen before cases are generated, use bases as
units and acknowledge the tiny development population. No seed-level significance
claim. If pursued, use a primary-first hierarchy and Holm across the two direct
secondaries; multiplicity-adjust the two learner mechanism contrasts separately.
Hindsight best-classical envelopes are descriptive, not deployable baselines.

Both-valid bill gains are secondary and always show their denominator. Decompose
currency savings into fleet, deadhead/other operations, linear electricity and
quadratic electricity, plus vehicle count and interval load. Equal-vehicle subsets
are descriptive, not causal mediation. The score-input intervention can identify
the finite-budget effect of the supplied ranking prices under its fixed target
tariff; it cannot establish broad tariff generalization from four bases.

Stop on invalid admission, false full-bound claims, lost process ownership,
clock/accounting failure or resource breach. Correctly recorded no-plan is an
endpoint, not permission for replacement. Restricted/fixed-route bounds never
become full-problem certificates. Preserve failures and all spend. Engineering
qualification, constructive witness replay and common evidence policy must work
before a comparison launch. A complete positive pilot may justify a larger,
independent study only with direct learned benefit, no material validity loss
and disclosed regressions in each size. Null/heterogeneous results are useful:
they redirect effort toward classical construction, labels or model information,
rather than an automatic expansion of training.
