# Analysis contract for the unlaunched learned-value pilot

24 October 2026. Prospective analysis clarification of
`RECOVERY_LEARNED_VALUE_STUDY_ADDENDUM.md`, which remains authoritative for arms,
cohorts, retention and clocks. This document fixes endpoint interpretation and
reporting before fresh outcomes. It neither launches the study nor changes its
budget, data access, engineering gates or pending qualification-budget decision.
No new data, model assets, inference, tests, solver or cluster work was used.
This integrated parent decision takes precedence over the three companion
RECOVERY_ANALYSIS_*_NOTE.md recommendations where they differ, particularly the
descriptive-only inference choice and the future failure-only controller path.

## What this pilot can answer

Compare complete timed methods on eight independent synthetic development bases,
four per size, with three solver seeds per base. Primary contrast is graph-v8
recovery versus CA1 recovery; direct secondaries are graph versus CatBoost and
CF1. Random recovery and cold unrestricted search are reference arms. This is a
method comparison, not an isolated architecture/learning intervention: CA1 sees
`a,b`, the learners see `a`, computation differs, and equal edge count does not
equalize topology or search difficulty. No static arms means no restoration-effect
estimate. The four mechanism bases are a subset of these eight, not new
independent groups. Existing engineering/October17 outcomes are not pilot data.

All 144 primary and 48 mechanism cells remain assigned even if the budget stops
the study. Do not replace cases, seeds, failures or undispatched suffixes. Do not
select a baseline variant, model, tariff shift or reporting subset using these
outcomes. No publication-readiness, broad tariff-generalization or generic-pruning
novelty claim follows from a positive result.

## Keep three questions separate

1. **Qualification:** was the required charging/start mechanism exercised and
   independently verified? V1/V2 remain failed. A later small pass proves that
   mechanism only, without reclassifying their80-trip outcomes.
2. **Deployable method output:** did this assigned method deliver a timely,
   replay-valid selected plan, possibly its cold fallback, under the common clock?
3. **Evidence integrity:** can receipt/clock/ownership/capture/replay/accounting
   evidence establish that answer? Ambiguous or broken evidence is unknown.

The current `comparison_native_worker.WorkerStorage.materialize` is explicitly
qualification machinery: it requires acquired durable fallback and attributable
warm processing, otherwise writes `UnexercisedNativePath` into engineering events.
Its analyzer also requires the charged/warm path. Reusing those all-path-required
rules unchanged would reject legitimate cold and no-acquisition comparison
outcomes. A future comparison worker/analyzer needs an explicit separate policy
and receipt schema; do not suppress its error list or relabel historical receipts.
No runtime source is changed by this analysis contract.

## Required endpoint record and precedence

Each immutable assigned cell must identify base, physical/tariff variant, scoring
input condition, arm, solver seed, clock, source/model/environment/library hashes,
original full case and selector identities. Preserve all raw diagnostics. Add
structured, separately audited fields for evidence integrity, output timing,
selected physical witness, acquisition outcome, warm-start processing and bound
scope. Required schema axes are `qualification`, `integrity`, `acquisition`,
`executed_mode`, `deployment`, `dispatch_state`, `stop_scope`, `primary_eligible`
and causal evidence references. Link candidate/witness IDs from capture to
rejection/admission, durable artifact, selected output and start source. A flat
success/failure flag or error-string allowlist is insufficient.

| Situation | Primary endpoint | Separate report/action |
| --- | --- | --- |
| Timely independently replayed selected witness and complete healthy receipts | Valid bill | Record acquisition/start/bound statuses separately |
| Acquisition times out or has no proposal, then timely valid cold fallback | Valid fallback bill | Acquisition failure; no credit for a warm path never exercised |
| A raw candidate is rejected, but retained selected witness remains valid | Valid selected bill | Preserve rejection; do not treat rejected raw plan as admitted |
| Healthy completed method has no replay-valid witness | Algorithmic failure | Record every attempted stage/status |
| Complete healthy evidence proves method finalization/ACK exceeded endpoint | Algorithmically late, no timely output | Preserve any late plan as diagnostic, not deployable bill |
| Unexpectedly missing/malformed ACK without an independently qualified failure certificate; uncertain clock, monitor/ownership failure, inconsistent capture/hash or ambiguous cause | Unknown | Engineering stop, retain evidence and fixed-denominator missing contribution |
| Complete independently qualified controller certificate proves an ordinary method deadline with no timely deployment | Algorithmic deadline failure | Failure-only certificate; no plan/bill/bound or qualification credit |
| Invalid admitted witness or false unrestricted-bound claim | Invalid/unknown for primary scoring | Engineering stop; no primary win/loss inferred from bad plan/bound |
| Known method acquisition failure and an evidence-integrity fault coexist | Unknown | Integrity fault takes precedence over favorable or unfavorable bill |
| Not dispatched after budget/engineering stop | Undispatched/unknown | Preserve preassigned cell and incomplete suffix |

Only a complete, healthy chain may classify method lateness or ordinary no-plan.
`endpoint_censored=True` alone cannot distinguish known late work from missing
evidence. A valid result paired with an unknown result remains an unknown pair.
Adjudicate from structural receipts/stage events, before pairwise bill comparison;
never use the favored arm's bill to decide cause. Preserve source evidence and
adjudication reason codes. No automatic retry, replacement or retrospective pass.

Timely deployment requires the hash/identity-bound post-fsync ACK by anchor+60,
uncensored result/completion/outcome, and complete healthy terminal evidence.
Keep result-fsync, completion-fsync, post-outcome ACK and owned cleanup times
separate. Existing `endpoint_wall_s` describes result-fsync timing; alone it
does not establish startup-to-final-ACK latency. A healthy late complete ACK can
prove method lateness; a missing ACK alone cannot. The61/62.5 supervision/cleanup
limits never extend the60-second deployment endpoint.

A distinct future comparison controller may certify `algorithmic_deadline_no_deployment`
without a worker ACK only through a separately qualified failure-only terminal
contract. Require frozen identity/clock/ownership; the full uninterrupted assigned
method window; positive evidence of the preset ordinary deadline causing the stop;
affirmative stage health; no preceding/concurrent integrity, interface, resource
or accounting fault; ACK-channel drain/closure after all owned writers terminate;
and proven owned cleanup with complete charges. Preserve bytes, times and all
malformed/partial-message diagnostics. Silence or an `outer_wall_deadline` string
is not affirmative health/causation evidence. Administrative/budget cancellation
before the complete method window cannot receive this certificate.

Such a certificate establishes no timely deployment only, not plan validity,
successful capture/finalization, useful bound or qualified warm mechanism. It
can score as an algorithmic failure opposite a valid plan. Transport/read failure,
partial/malformed ACK, hidden stage faults or ambiguous cause remains unknown.
Current supervisor receipts lack this qualified drain-to-EOF/no-writer certificate;
do not infer it retrospectively from current cleanup. Unless and until that new
path is implemented and qualified, missing current ACK evidence remains unknown.

Physical admission requires full independent replay and exact bill. Full-start
submission, processing, acceptance and physical fallback validity are different
facts. A rejected/unobserved start need not invalidate an independently valid
fallback in a comparison; it does fail a qualification requiring that start path.
Only original unrestricted full-model bounds may be labeled global. Missing or
weak full bounds can coexist with useful valid plans. Restricted/fixed-route
bounds remain diagnostic; contradictions or false scope claims trigger a stop.

Bill tie bands are pairwise conventions; they need not be transitive across
methods. Do not turn these contrasts into an outcome-selected global method
ranking or a deployable hindsight best-classical comparator.

## Fixed-denominator practical scores

For base g and seed s, compare graph G with control C. Let `d_gs` be +1 for a
graph win, -1 for a graph loss and 0 for a tie. One timely valid plan beats a
healthy algorithmic no-plan/late endpoint; two healthy algorithmic failures tie.
If both plans are valid, bills are exact independently replayed rationals and

`tau = 0.005 * max(abs(B_G), abs(B_C), 1 currency unit)`.

Graph wins if `B_C-B_G > tau`, loses if `B_G-B_C > tau`, otherwise ties. Implement
0.005 as exact1/200 and treat equality as a tie; do not let float rounding select
a side. Keep the currency unit fixed in the manifest. Missing/unknown pairs have
set-valued contribution[-1,+1], never a zero imputation.

Average the three assigned seeds within each base, four assigned bases within
each size, then the two sizes equally. With this balanced design every primary
seed pair has weight1/24. For any one primary/direct-secondary contrast, if S is
the sum of known pair scores and u is the number of unknown/undispatched pairs,
the conservative assigned-cohort net-win interval is

`[(S-u)/24, (S+u)/24]`.

Show the known-score component S/24, missing mass u/24 and interval together;
do not renormalize to completed pairs. Per-base bounds divide by3; per-size bounds
divide by12. Unknowns shared across contrasts are coupled: these are marginal
conservative intervals, not a jointly attainable winner ranking. They are
missing-outcome bounds, NOT sampling confidence intervals.

Report per-arm deployment-validity fractions separately: with v known valid and
u unknown outcomes among n fixed assignments, its validity interval is
[v/n,(v+u)/n]. For a validity difference retain known opponent information; e.g.
valid minus unknown is[0,1], not[-1,1]. Average with the same fixed group weights.
These validity bounds do not change the conservative[-1,1] convention for an
unknown practical-win pair and do not impute currency bills.

For each learner's four-base mechanism comparison, fresh-target scoring versus
original-day scoring uses the same shifted target tariff. Apply the same endpoint
score; all12 assigned base/seed pairs have weight1/12, yielding[(S-u)/12,(S+u)/12].
Keep learners separate. Never pool four bases times two learners times three seeds
as24 independent observations.

## Report exploratory evidence without manufacturing precision

This development pilot's primary outputs are per-base/per-size score tables,
conservative missing bounds, validity/timeliness counts, all material regressions,
and both-valid bill decomposition with its explicit selected denominator.
No confirmatory p-value or nominal population-confidence claim is authorized by
this contract. Seeds characterize search variability within a timetable; they
do not create more independent timetables. Leave-one-base-out summaries, if shown,
are sensitivity displays, not confidence intervals or a basis for model selection.

An exact two-sided sign-flip calculation requires a null law invariant under
every independent base sign flip: conditional on magnitudes, nonzero signs must
be jointly uniform over all2^n patterns (independent fair signs). Independent
effects symmetric about zero are sufficient; mean zero or exchangeability alone
is not. Paired solver seeds, fixed hash order
and rotating arm order do not by themselves supply random assignment or that
null. Even under those assumptions, eight nonzero base contributions give a
minimum attainable two-sided p of2/2^8=1/128. Four mechanism bases give2/2^4=1/8,
so this mechanism pilot cannot produce a two-sided5% result under that exact
test with four independent groups. More solver seeds cannot change its resolution.
Zero contributions/ties can only reduce the effective sign count. A binomial
sign test addresses a different sign-probability null, not automatically the
mean practical-net-win effect. Do not substitute it after seeing results.

This choice closes the old addendum's optional inferential branch for this pilot:
primary-first/Holm language is not permission to try several tests and select a
favorable one. A later independent confirmatory study needs its own prospective
population, estimand, sampling/randomization assumptions, power/precision design
and multiplicity policy before outcomes; it cannot retrofit these eight bases.

## Price information: require the whole exposure chain

Record, for every prespecified mechanism base/seed/learner, the supplied price
vector, original feature rows, transformed model inputs, finite scores, rank order,
common backbone B, exact K, retained mask/identity, acquisition/output statuses,
stage times and exact realized load/bill decomposition. Scoring and all artifacts
pay the original clock. Both native planners always use the same shifted target
`a,b`; stale scoring inputs are recomputed, not cached for free.

Separate these observations: feature change; score/rank change; changed retained
mask; changed accepted route/load; lower deployed bill. Neither an earlier link
nor a changed bill proves the intervening links. Common B/K and boundary IDs must
match exactly; filling excludes B. Preserve zero-exposure K=|B| cases. If masks
match, topology-selection information has not changed, although scoring latency,
native wall-clock search and machine variability can still change output. Report
that negative control rather than crediting price-responsive pruning or dropping
the pair. A price-aware native optimizer can change charging without any learned
ranking response.

The shifted tariff preserves the linear-price multiset. Current feature code uses
unweighted global mean and spread, so their real-arithmetic invariance is an input
audit, not a measured sensitivity finding; local window features can change.
Adopt exact aligned finite represented-value comparison (`atol=rtol=0`), archive
dtype/full values and hashes, changed-value counts and maximum absolute differences,
plus exact discrete masks. A byte/hash change alone can reflect signed-zero or
serialization differences rather than changed numeric value. Do not turn rounding-scale
differences into an economic-responsiveness claim. No score epsilon may change
the selector's frozen score/ID tie order. The companion mechanism note refines
the machine-arithmetic audit without adding data or arms.

The intervention estimates a paired finite-budget complete-method contrast for
these assigned cases, including scoring latency. It does not by itself isolate
graph topology as a causal mediator, retraining value, architecture superiority,
`b` responsiveness or general tariff transfer. Same-machine repeated seeds and
balanced order reduce nuisance variation but do not make wall-clock search a
deterministic potential outcome.

## Before any executable manifest

Freeze a separate comparison endpoint policy/schema and cause-adjudication table;
implement exact score arithmetic and fixed denominators; then qualify those
affected paths with handcrafted data under a source-bound prospective budget.
That is a future package, not an instruction to run tests now. Applicable native
mechanics and resource/evidence behavior still require qualification before the
pilot. Sources/models must stay locked while workers run. The192-cell cost plan
remains an upper-budget proposal that can stop incomplete; do not expand it or
borrow qualification/shutdown funds to achieve significance.
