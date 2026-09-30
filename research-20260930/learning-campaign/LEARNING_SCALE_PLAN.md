# Scaling from source selection to learned routes

30 September 2026. This is a design for a **new, versioned dataset and model campaign**, not an executed experiment or a change to any archived result. The [battery-regime note](BATTERY_REGIMES_AND_TRAINING_DIRECTION.md) defines the physical motivation. No manuscript work is part of this plan.

## What the existing evidence says

The current charging-response model has eight ridge coefficients and 12 labels from six independent training timetables. Its original four development choices all selected source 1; an always-source-1 rule made the same choices. The independently checked tariff-variant run shows tariff-dependent switches, but its flat-tariff switches are worse in three groups and tied in one; mean paired excess is 0.5342 versus 0.0670 for the older EdgePrior. This is evidence to improve feature and physical-regime coverage, not evidence that adaptation already works. More epochs on that fitted ridge cannot help. The older EdgePrior scores movement edges, but its actual usable output is projected onto already solved source fleets. Neither model learns a new complete route plan. The next investment is independent physical timetables and better labels, followed by route generation; repeated two-source selector variants alone will not answer the user's ML question.

## Freeze the registry before labels

- Create **128 training, 32 development, and 32 sealed test base timetables** with new identities, fixed before any target optimization. Keep all tariff variants and battery variants of a base timetable in its assigned split. Preserve historical attempts and reserved seeds 2004/2005/2020/2021.
- Cross-balance two case sizes, consumption and depot-opportunity patterns, and the explicitly modeled operating spans **80, 174.24, and 232.32 kWh** across the registry. Assign one primary battery regime to each base group; any same-base sensitivity variants stay in that split and need a separate label budget. The last two spans map a 290.4-kWh nameplate pack to illustrative 20–80% and 10–90% SOC windows; they are modeling sensitivities, not a claim about manufacturer usable capacity. Specify distance, travel time, consumption, reserve, charging power, connector count, and full-recharge deadline together. Require a constructive, independently replayed complete-fleet witness for each physical case before expensive labeling.
- Record the generator version, exact case/market identities, random seeds, split, and immutable source hashes. Reject a shard whose physical witness fails; record the rejection rather than tuning individual routes after seeing model outcomes. A base timetable, not each correlated tariff or battery variant, is the independent statistical unit.

## Build labels in bounded shards

1. Use **eight-base-group training shards**. The first shard has 8 groups × (2 source solves + 2 sources × 3 fixed-route tariff charges) = **64 cells**; repeat only after its physical and receipt audit. For each group, obtain two replayed source-market fleets and six paired charging labels. Save direct and post-charge exact curved costs, movements, full plans, load, battery/charger replay, bound/status, solver budget, and acquisition/charging wall time. Cold target solves and any stronger route oracle are separate references, never inputs to prospective selection.
2. Complete and audit the first 8 groups, then compare at 32, 64, and 128. At each checkpoint, fit only on the accumulated training groups and compare a constant/majority source rule, cheapest exact direct bill, the existing ridge, and one modest nonlinear tabular model (for example, a small gradient-boosted tree). Choose hyperparameters and preprocessing through **grouped cross-validation inside training only**. Freeze each checkpoint model and choices before running or reading its development outcomes. Plot paired cost and feasibility against the number of independent groups, with uncertainty resampled by base timetable.
3. Do not count a failed solve as a bad route label or an optimal answer. Distinguish a physically replayed incumbent, a fixed-route linear-tariff LP optimum, a target-market lower certificate, and an open gap. Treat no-incumbent outcomes as censored/missing for supervised targets; record their frequency and use matched budgets when comparing methods. The response target may remain post-charge minus direct cost per trip, but reconstruct and evaluate **exact full target cost** and paired regret against the best of the two observed charged source plans.

## Learn a fleet proposal, then verify it

After the label pipeline is stable, train a model that scores **route decisions**, not merely which of two old fleets to import. Start with variable-size trip and movement features: time, location, travel energy, charge window, battery/reserve regime, shared grid/connector availability, and tariff intervals. A pooled/tabular edge scorer plus flow-constrained decoder is the simple baseline; consider a graph model only if grouped validation shows a material gain. Use feasible replayed fleets as positive structured examples and better-cost plans as preference signals. Solver incumbents are best-known, often censored by budget; they are not ground-truth optimal routes. Freeze learned scores before target labels, decode legal paths, solve fixed-route charging, replay physical feasibility, then run a **fresh target global-bound check**. Keep prediction, repair, native verification, and true cost in separate receipts.

Promote a selector or route model only after it beats the strongest simple baseline on **group-paired exact cost with a confidence interval excluding zero**, maintains independently replayed feasibility, and improves total paid online time or cost at a matched solver budget without a large adverse tail in any battery regime. Report cold, direct, best-of-two (an information-rich retrospective ceiling), and bound gaps separately. If a constant rule matches the learned selector, stop tuning that selector and prioritize route proposals. Use the 32 development groups for model choice; open the 32 sealed groups once, after architecture, thresholds, and analysis code are frozen. A single sealed-test gain is evidence of transfer, not proof of global optimality.

Ridge, boosted trees, feature extraction, and the charging/native solvers are CPU work. Request a GPU only if a graph/sequence model reaches a measured training bottleneck that CPU cannot meet; a GPU will not accelerate license-limited label solves. Freeze resource budgets per shard before launch and retain complete failure, timing, and replay receipts.

## Sustained execution and scaling

The first physical-label shard is a single 1-CPU, 8-GB job capped at two hours.
The initial 128 training groups require sixteen distinct eight-group shards,
so their conservative requested-allocation ceiling is 32 CPU-hours before
separate model fitting and development evaluation. This is a first learning-curve
milestone, not a claim that 128 timetables are enough for deployment. Extend the
registry prospectively if validation curves and route coverage justify it.

After the first shard verifies the physics, label yield and actual memory use,
freeze the next launch budget. Up to four independent 1-CPU / 8-GB label workers
would be a reasonable next step if available capacity and native licensing permit
it: at most four CPUs and 32 GB concurrently, with separate immutable shard
receipts, two-hour job caps and the existing excluded node. This is a planned
scaling option, not an active allocation. Do not consume other projects' held
resources or turn the user's long-horizon authorization into an unbounded job.

Checkpoint models, preprocessing, group splits, learning curves and the best-known
feasible route bank so work can resume over weeks or months. Collect a completed
shard once, perform compact evidence checks, and move on; do not repeat broad
audits on unchanged infrastructure. Existing hourly follow-ups continue useful
implementation and training between batches. User notifications remain limited
to learning results, important failures and consequential decisions.

## Data-health gate at every size checkpoint

Before fitting the next selector, report these measures **by physical regime and case size**, with base timetables as the counting unit: the fraction of source0/source1 plans with identical movement topology (and separately identical full-plan hashes); the fraction of intended charging labels that are replayed, provisional after a solver limit, missing, or censored; the entropy of the observed two-source target winner; and the distribution of exact winner margins, including near-ties at a prespecified cost tolerance. Also record how many distinct feasible route topologies the source bank and any stronger oracle actually contain. A large collection of correlated tariffs is not a substitute for independent route diversity.

If doubling from 32 to 64 groups mainly adds identical source pairs, near-tied outcomes, or the same source winner, do not keep fitting a more complex selector to that signal. Expand tariff/route opportunity coverage or begin structured route proposals with physical replay gates. At each checkpoint compare the cheap frozen EdgePrior as well as constant and direct-bill controls; the latest tariff evidence indicates it can outperform ridge on mean paired excess, so model complexity alone is not a promotion criterion. Continue to 128 only as a prospectively budgeted learning-curve measurement, not as a promise that sample count will solve an uninformative-label problem.
