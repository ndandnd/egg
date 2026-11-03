# Exact comparison score primitive

24 October 2026. Source-only implementation of the fixed-denominator arithmetic
in `RECOVERY_ANALYSIS_CONTRACT.md`, with the compatible portions of
`RECOVERY_ANALYSIS_INFERENCE_NOTE.md`. No pilot data, identities, model, runtime,
solver, cluster, inference, or test execution is included in this change.

`src/egglab/comparison_scoring.py` accepts externally adjudicated `EndpointKind`
values: valid, algorithmic failure, unknown, and undispatched. A valid endpoint
requires an exact bill; all other statuses forbid a bill. This source does not
read receipts, establish endpoint causes, or certify independent replay. The
caller remains responsible for the contract's separate evidence and endpoint
adjudication. Invalid input records are rejected rather than scored.

Records do not carry arm, learner, tariff, or scoring-input identities. Before
scoring, the caller and external verifier must establish identity-only joins and
alignment for one oriented contrast. These arithmetic primitives cannot detect
cross-learner or cross-tariff misjoins that share an assignment key, or mechanically
enforce separation of learner comparisons.

Bills and positive currency units accept only integers (excluding bool),
`Fraction`, or canonical reduced rational strings; strings must match
`str(Fraction(value))`. The exact pair tie band is
`max(abs(A), abs(C), currency_unit)/200`, including equality as a tie. Valid beats
healthy algorithmic failure; two such failures tie. Either unknown or
undispatched endpoint leaves the practical pair in `[-1,1]`, including against
a known valid endpoint. No failure receives an invented bill.

`AssignmentRoster` requires explicit caller-supplied synthetic base identifiers,
sizes 40/80, and seeds 17/41/73: primary has four bases per size (24 pairs),
mechanism has two per size (12 pairs, one learner per call). It rejects duplicate
keys, cross-size base identities, incomplete rosters, and unlisted/duplicate
observations. One fixed currency unit applies throughout the roster and every
observed endpoint. Omitted observations retain their assignment as unknown.

`summarize_comparison` returns every base, both sizes, then overall summaries,
with known score component, missing mass, exact marginal completion bounds,
win/tie/loss/unknown counts, per-arm validity counts/bounds, and validity
difference bounds retaining known opponent information. Validated balanced
rosters make its seed weights exactly equal to three-seed base averages,
equal-base size averages, and equal size weights. There is no complete-case
renormalization, exposure conditioning, p-value, or sampling confidence interval.
Each call is intended for one aligned contrast; the caller must keep learner
comparisons separate. Bounds shared across contrasts are not a jointly attainable
method ranking.

`src/tests/test_comparison_scoring.py` contains bounded handcrafted tests for
rational boundaries, negative bills, large integers, sign reversal, source-only
stdlib import isolation, status precedence, malformed inputs, fixed rosters,
missing groups/seeds, and separate validity bounds. The tests load this source
directly without importing the `egglab` package. They are proposed tests only;
execution and receipt qualification require the separately authorized gate.
