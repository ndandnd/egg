# Adversarial review of the focused theory draft

29 October 2026. Source-only review of `paper/focused-theory-20261029/{main,framework,construction,expansion,ownership,proofs}.tex`. No numerical run, import, test, hash, data access or underlying source edit. This is a correctness and significance assessment, not submission approval.

## Findings requiring correction

### 1. Restricted-price universal quantifier is too strong

In `framework.tex`, the support definition permits an externally restricted admissible price set. The qualification subsequently requires that this set contain an attained hull-dual price. The proposition nevertheless says that when D=CH, every physical planner optimum is supported by **every attained maximizer** of `V(p)-F*(p)`.

Containing one dual maximizer does not imply containing them all. For a counterexample, let the projected physical set consist only of `(e,c)=(0,0)`, take `F(e)=|e|`, and declare admissible prices to be `{0}`. All compactness, finite-convex-function and dual attainment conditions hold. D=CH=0 and the unique physical plan has admissible support at zero. Every price in `[-1,1]` is an attained hull-dual maximizer, but price 1 is inadmissible and cannot support under the stated economic definition.

The proof correctly establishes the unrestricted mathematical facts: every dual optimizer has zero regret and belongs to the supply subdifferential at every physical optimum. Repair the economic sentence to say **every admissible attained maximizer**. Alternatively retain the universal zero-regret/subgradient conclusion and distinguish it from admissible support. This does not undermine any unrestricted quadratic result in the draft.

### 2. The n=20 replication example reverses the regrets

The final paragraph of `proofs.tex` gives m=13 and m=14, deviations -1/2 and +1/2, followed by regrets "14 and 7 respectively." Applying the theorem's correct formula gives:

* m=13: seven unpaired choices are disadvantaged by one each, hence regret **7**.
* m=14: fourteen paired choices are disadvantaged by one each, hence regret **14**.

The ordered numerical statement must read **7 and 14 respectively**. The theorem's formula and the unordered statement in `ownership.tex` are correct. Because this illustration explains why tied planner optima can have different incentives, preserving the association between the chosen plan and its regret matters.

### 3. Reserved-ownership comparison needs a small scope clarification

The aggregate planner permits an arbitrary matching between identical copies of A and B. The later ownership institution assigns each participant a fixed A/B pair and reserved connectors. An aggregate optimal schedule can match A_i to B_j with i different from j; that literal schedule is not an allocation in the fixed-pair ownership institution.

This does not threaten the formulas: every optimal projected outcome can be implemented by m one-bus owners and n-m two-bus owners with the reserved pairs, giving exactly the stated regrets. State this implementation step and apply the corollary to an optimum **implemented in the reserved-pair institution**, rather than implying every literal cross-matched aggregate schedule already defines individual ownership. No altered bound or new computation is needed.

## Core arguments checked

I found no counterexample to the main construction or continuous parameter characterizations under their declared assumptions.

* The support inequality follows directly from linear minimization over complete-plan mixtures and the subgradient inequality. The finite-minorant alternative is sound: a global minorant has a conjugate at least F*, allowing its attained dual price to attain the original hull value by weak duality. The proof's zero-sum decomposition correctly handles all physical optima and all unrestricted attained dual maximizers.
* The connector model includes both unlabeled service partitions, all continuous charges, K=20, f=0, planner ties, and flat-price response intervals. For positive fee, a gap is equivalent to the hull minimizer lying strictly between the two projected endpoints. The stated strict inequalities correctly translate that condition. In particular, a zero gap at a boundary means weak support, not unique response.
* The reserve/loss neighborhood has the necessary headroom and reserve restrictions. Its strict inequalities make the one-bus lower endpoint lie above the two-bus supply minimizer while leaving early power slack. Constant efficiency preserves total purchased energy 30/eta and the serial terminal construction. Continuity gives a local positive-gap neighborhood; the claim does not silently extend to arbitrary efficiency or reserve changes.
* Movement-only stability uses a valid complete-plan dominator, not just lower total energy. A two-bus addition with early purchase u has the old plan `(u,30-u)` as a componentwise dominator. A one-bus addition still needs ten early units before B completes, so its early purchase is fixed at ten. This remains true if movement consumption occurs before service, between services or after B, provided all the stated restrictions on equipment, access, energy and costs hold. Replacing each component inside a hull mixture is legitimate because F is coordinatewise nondecreasing on nonnegative loads. Convexity alone would not suffice; the actual F has the required monotonicity.
* Expansion preserves every old plan's deviation opportunity, so old-plan regret cannot fall. The dual-safe condition and the two simultaneous equalities give the correct necessary-and-sufficient erasure test with an unchanged hull value. Without that condition, the old hull value is only a necessary benchmark. The fee-8 example correctly demonstrates insufficiency.
* The battery theorem checks the whole opportunity set. Every mixed/new two-bus branch has the same early interval as an old two-bus branch and no lower operating cost. No old plan can be rescued by expansion. On the new one-bus interval, only its strictly convex physical minimizer can be supported; the two affine bill comparisons yield A(a) and C(a). The weak boundary conditions, equal-fee threshold and fee-12 physical tie are consistent.
* In replication, per-bus acceptance and the number of connectors permit the claimed projection: each paired bus receives ten early units; unpaired A buses distribute the remainder; each unpaired A/B pair can share one terminal connector. The two fixed-m physical regimes meet correctly. Nearest-integer minimization, the O(1/n) planning gap, the declared nonzero absolute whole-owner regret subsequence and the O(1/n) reserved-owner bound follow. The result appropriately relies on scaled supply and compatible reserved rights.

## Significance, separately from correctness

The strongest defensible contribution is an unusually explicit physical realization of a classical convexification obstruction: finite-horizon inventory is fully restored, both service assignments are present, continuous charge opportunities are exhausted, and equipment/fee changes have exact weak-support boundaries. The expansion discussion also prevents a misleading monotonicity claim about global gaps, and the replication example makes participant ownership concrete.

These are useful analytical contributions, but their proofs reduce to low-dimensional projection, convex minimization and standard support duality. Movement stability is a conditional dominance theorem; it should not be marketed as broad robustness to routing flexibility. The equipment example is a carefully specified enlargement, not evidence that a neglected original duty was discovered. Replication supplies a clean illustration of an aggregation distinction, not a new general aggregation theorem.

I cannot conclude from this source review that these results are sufficiently original or significant for a particular venue. A serious novelty case needs direct comparison with the closest indivisible-load/charging examples and ownership-dependent aggregation results, beyond acknowledging classical hull pricing. Exact implementation agreement supports arithmetic reliability, not novelty or empirical importance. The honest treatment of the public case as unresolved is appropriate: its current bounds do not establish optimal-fleet price-support failure. Correcting the findings above would improve mathematical precision, but would not itself establish submission readiness.
