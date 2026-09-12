# Repeated convexified coordination pilot — design for review

Date: 2026-09-12. This is a prospective engineering design, not an executed
experiment or an authorization artifact. The accompanying
[plan manifest](plans/reoptimization_pilot_v1.json) uses symbolic instance IDs
and null seeds. No seed allocation is implied.

## Question, population, and split

Measure learning's marginal improvement over strong reuse on repeated A2
coordination with the same final certificate. This differs from reusing a MIP
incumbent in repeated integer best responses.

Use 24 independent base instances, one distinct fresh seed each after a registry
check, stratified by n_trips in {16,24} and b in {0.01,0.05}. Each of four strata
has three training, one validation and two test bases: 12/4/8 overall. T=28
hourly slots, baseline synthetic battery/power settings, and all physical
constraints remain fixed within a four-state trajectory. The current synthetic
generator's vehicle cap grows with n; this is a workload comparison, not a
controlled fleet-size experiment. The operational protocol is separate.

Construct the baseline market with the existing duck shape, a_level=1,
a_amp=0.8, base_load=50 kWh/slot, and the assigned b. Let
`v_t = cos(2*pi*(t mod 24)/24)`; use linear-cost arrays
`a0`, `a0+0.1*v`, `a0-0.1*v`, `a0+0.2*v` in that order. In one predefined test
base per stratum, replace the final state with `a0+0.4*v`. This is a fixed
larger-shock stress stratum, not a promised peak-order reversal or general OOD
claim. Freeze the generator and manifest before any outcome is produced.

All states and traces of a base remain in one split. Training/validation may
determine normalization, predictor and baseline selection; test data may not.
Test arms can reuse their own earlier states, never future states or another
arm's solutions. Do not split individual solve calls into training and test.

## Arms and adapters that must be reviewed

Run four baseline arms on all 24 bases: cold A2; feasible-incumbent/column-pool
reuse; reuse with the intercept-adjusted previous oracle price
`q_(k-1) + (a_k-a_(k-1))` as an initial pricing center; and reuse with a fixed
bundle-level strategy. The analytic translation is a cheap baseline the learner
must improve upon. The current
A2 API rejects a changed-market checkpoint: implement an explicit fresh-state
adapter rather than changing checkpoint identity or replaying old bounds.

Use the same pool cap and deterministic eviction rule for reuse arms. Column
feasibility persists under fixed physics, but reduced costs and objective bounds
must be recomputed. Current `ops_cost` is intrinsic; market charges must never
be folded into it when reusing a complete fleet column. Prices are p=-pi.

After profiling, select one residual predictor (regularized linear or
nearest-neighbor) using validation only; use its arm only on the four validation
and eight test bases. Defer large networks and
learned pricing-network reduction. If baseline qualification is incomplete or
there is little avoidable cost, stop before generating a learning dataset.

For transitions k=1,2,3, the target is the 28-component residual
`q_k - q_(k-1) - (a_k-a_(k-1))`, where q is the last clean-master oracle price
`-pi` recorded by
the cold-A2 training trajectory. Features are flattened arrays `a_k`,
`a_k-a_(k-1)`, b, U and q_(k-1), plus n_trips and total service-trip energy.
Fit feature normalization on training only. Use multi-output ridge regression,
selecting its penalty from {0.0001,0.01,1,100}. Compare it with one nearest-neighbor
predictor using Euclidean distance in those same standardized features, a
training-only library, and lexicographic base/state tie-breaking. Select the
candidate with minimum mean squared 28-slot residual error on the existing
cold-A2 validation labels; break equal errors in favor of nearest-neighbor,
then the larger ridge penalty. This selection requires no additional solves.
All fitting and selection costs count toward the offline cap. A final master
price is a solver-selected label,
not a claim of unique or exact dual optimality. Record its originating objective
interval and label convention; do not average an unverified optimal face.

At deployment, q_(k-1) comes only from the same arm's previous state. Form
`q_hat = q_(k-1) + (a_k-a_(k-1)) + predicted_residual`. Like the analytic initializer,
q_hat proposes one full-feasible-set pricing solve at the transition, counted
in time and call budgets. Admit only a replay-valid novel column, then use the
ordinary clean RMP and complete pricing certificate. Do not substitute q_hat
for a master dual inside the bound formula. State zero uses the same charged
cold initialization. The bundle-level arm still needs its separate validated
adapter; this design does not claim that implementation is complete.

Preserve the true-quadratic upper bound and full-pricing lower-bound contract,
0.001 tangent tolerance and 0.01 final absolute certificate. Predictor proposals
and pricing incumbents are not pricing lower bounds. A finite fallback must
return to the complete pricing problem. Do not alter frozen A6/B3 rules.

## Resources and measurement

96 baseline plus 12 learned trajectories, four CPU threads and one hour per
complete four-state trajectory, yield 432 allocated CPU-hours. Add 16 CPU-hours
for labels, training, tuning and nearest-neighbor validation: 448 total. Within
each state enforce both 15 minutes and 240 pricing calls; at most four concurrent
trajectories imply 16 CPUs and a proposed 128 GB total memory (32 GB each).
Budget hits remain results. This is a ceiling, not a runtime estimate or verified
cluster capacity. Separate adapter/feasibility qualification has no allocation
yet and is not hidden inside the 448-hour number.

Measure complete elapsed time from input load through final validated output,
including construction, cache checks, replay, inference, solves, fallback,
checkpointing and audit. Charge first-state solves fairly. Separately report
solver wall, CPU time, peak memory, queue delay, offline cost and failures.
Amortization comparisons must use consistent CPU, elapsed-time or monetary units.

## Engineering decision rule

Freeze the strongest reuse baseline on validation before test inspection.
Proceed only if all validity checks pass and all eight candidate and selected
baseline test trajectories certify all four states within their budgets.
Any unresolved trajectory makes the engineering gate non-advancing; do not
treat cap times as successful time-to-certificate observations. Then require
the paired geometric-mean complete-time ratio to be at most 0.85,
at least six of eight tests are faster, and none is more than 2x slower. Report
paired differences and the predefined shock strata. Eight independent test
bases are an engineering gate, not evidence of broad statistical generalization.

## Before execution

Review adapters and complete small qualification checks; resolve tested solver
versions; check cluster allocation, licenses and capacity; check the seed
registry and allocate only unused seeds >=10000; freeze identities and paths;
then obtain the operator direction required by the supplied handoff. This plan
contains no launcher and never authorizes protected analysis or recovery.
