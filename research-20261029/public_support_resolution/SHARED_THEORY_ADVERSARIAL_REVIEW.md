# Adversarial review of the fixed shared-connector theorem

Verdict: **Scoped mathematical PASS.** No counterexample found under the
declared positive-energy, f>0, common-window, lossless/no-switching assumptions.
This is a source-only mathematical review of the newly added shared-resource
and ordered-matching statements in heterogeneous.tex/heterogeneous_proofs.tex.
No execution, literal test, import, hash, commit, new agent or data access.

## Physical projection and boundaries

For a selected matching every A bus is at the depot throughout the common
early window; its allowed grid charge is [r_ij,a_i] if paired, [0,a_i] if not.
The lower bound never exceeds a_i because b_j<=B. Their interval sum is
[R(M),sum a_i]. Serial allocation at the same per-bus/connector power K is
possible exactly when E<=K, with no extra individual-time constraint once
total energy satisfies this inequality. Common windows, zero auxiliary draw
and zero switching time are essential. They must not be generalized to
bus-dependent windows merely because total energy fits.

Every bus is present throughout the terminal window. Its refill demand is
nonnegative and at most B; summing yields S-E. At common power H, serial
charging therefore needs exactly (S-E)/H hours when H>0. This restores each
bus individually; it is not an aggregate-inventory shortcut. The upper bound
U=min(sum a_i,K) and lower bound L=max(0,S-H) follow. The zero-matching
assignment realizes the interval whenever L<=U, so the feasibility iff is sound.

K=0 permits only E=0; feasible matching cardinalities then require r_m=0
and H>=S. H=0 is actually infeasible under the strict b_j>0 assumptions:
S>sum a_i>=U, so L=S>U. Neither proof divides by zero. If L=U the projection
has one load, lowest operating cost is physical and the gap is zero.

## Truncation, duplicate thresholds and lower hull

r_m>U means an empty physical branch, so deleting that cardinality is valid.
It must not become an artificial endpoint at U. Because r_m is nondecreasing,
the discarded cardinalities are a suffix. Feasibility ensures m0<=mmax.
All r_m<=L collapse onto the left endpoint; f>0 makes the largest such
cardinality cheapest. The first retained increment r_(m0+1)-L is strictly
positive and no larger than the corresponding original increment. All later
increments are original, nondecreasing positive increments. Hence the claimed
clipped frontier has nondecreasing slopes -f/increment, followed by zero.

The construction includes every physical endpoint and lies below all physical
horizontal branches. Convexity and endpoint feasibility prove exactness of
the whole-plan lower hull. Collinear physical intermediate thresholds remain
attainable and cannot be erased from the support criterion by merging faces.
There are no later repeated positive thresholds under nonnegative discrete-
convex increments; the possible duplicates are handled in the initial block.

## Support and strict convexity

Strict convexity of G is a sufficient uniqueness condition, not necessary in
every individual instance. Its use in the corollary is correct: one minimizing
load, physical frontier at the listed thresholds/final flat segment, and a
strict operating-cost separation on every adjacent open sloping interval.
Compactness then gives a strictly positive attained gap when the unique
minimizer is in such an interval. Value equality becomes admissible-price
support only with the separately stated supply/attainment qualification.

Dropping uniqueness without changing the criterion would be wrong. For
n=1,a=b=15,B=20,K=10,H=30,f=7, the hull frontier is14-0.7E.
With affine supply G(E)=0.7E, every E in[0,10] is hull optimal, including
interior points, yet physical endpoints attain D=CH=14. Without strict
convexity/another uniqueness assumption, the correct condition is that the
whole hull argmin set intersect the physical lower-frontier set. The current
corollary does not make the invalid stronger claim.

At f=0, the zero-matching branch has zero operating cost at every feasible
load, so D=CH. The body expressly excludes that case from its strict-interior
criterion. No extension of the positive-fee assertion to f=0 is justified.

## Ordered matching reduction

The sorted-smallest/opposite-pairing formula is correct. Replacing a selected
energy by an unused smaller one preserves the matching's size and cannot
raise any positive-part edge cost. Thus both selected sets may be the m
smallest. The displayed convex-increment inequality has the correct direction:
same-order pairs cost at least the exchanged opposite-order pairs. Repeated
uncrossing yields reverse order, including ties and zero costs. This is a
classical monotone/convex assignment reduction, appropriately not claimed as
new matching theory.

## Qualification and one clarity repair

The fixed shared-connector conclusion, including its analytical realization
of the n=2 example at K=15,H=49, follows from the new theorem. It is not covered
by the eight qualified cases using n10kW/n30kW connectors and grid10n/30n.
Their individual allocation polytopes and witness timings differ. The manuscript
states this distinction and does not reuse the parallel charging schedules.

I repaired only the closing scope paragraph of heterogeneous.tex: it previously
described the whole section as requiring scaled adequate resources after a
fixed-resource theorem had been added. It now distinguishes the two hardware
policies and retains their common two-batch/zero-travel restriction. No theorem,
formula, proof result or numerical evidence was altered.

This PASS is not implementation qualification, operational generality,
closest-prior-art clearance or a submission-readiness judgment.
