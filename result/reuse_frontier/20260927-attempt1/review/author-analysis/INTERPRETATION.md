# Interpretation and next-step limits

The new diagnostic establishes remaining work after retaining physically valid
columns: four of twelve tariff transitions require more than one clean pricing
call. That is a useful advance over the previous two-window qualification,
where every retained transition stopped after its first clean call. It does
not yet establish a useful learned-pricing problem.

The four cases are depleted_f20/early-cheap (2 clean calls),
depleted_f20/late-cheap (3), depleted_f26/late-cheap (2), and the fixed-two-bus
replenished/late-cheap case (2). All unchanged and return-to-base retained
transitions certify in one clean call. The last result is about revisiting a
market after accumulating columns; it is not an independent cold replicate.

The shifted-price arm makes exactly the same number of clean calls as retention
alone at every transition and pays an additional proposal call. Three proposals
are genuinely new at the 1e-7 load/cost projection tolerance, all in the
replenished case. They increase the pool but do not reduce clean pricing calls.
Thus full-precision key novelty and even economically distinct projected loads
are insufficient measures of proposal utility. All three arms have the same
state-zero pricing costs, totaling 27 calls over the three fixtures.

There is a simple accounting obstruction for the **always-propose architecture
on this fixed trajectory**. Retention needs 17 pricing calls over the twelve
transitions. One paid proposal and at least one fresh clean verification per
transition require at least 24 calls, even if every proposal were perfect.
The observed shifted arm uses 29. Consequently, improving the proposal alone
cannot make this always-propose architecture beat the observed retained
pricing-call total here. A selective policy or a genuinely cheap proposal
mechanism would be a different architecture requiring a new frozen evaluation.
This observation concerns counts of complete pricing solves; it does not bound
runtime because solves and master refinements have unequal cost. The observed
retained and shifted arms also use identical totals of 192 clean-master LP
calls, so this run offers no evidence of a master-call offset to proposal cost.

The run remains incomplete under its own frozen success definition: 44 of 45
comparison cells are certified/reference-checked; all 15 references finish.
The cold depleted_f20 return-to-base cell stops when CBC reports FEASIBLE after
the prescribed 10-second pricing limit. Its incumbent-minus-bound interval is
about 2.106e-5 in pricing objective, but the frozen optimizer policy requires
OPTIMAL. Its 7 pricing attempts and 21.088 seconds of complete cell time remain
failed work. That status must not be silently relabeled as success even though
a different bound-aware policy might plausibly certify it.

On the 14 fixture-state keys where all arms finish and agree with the reference,
cold/retained/shifted calls are 116/43/54 and complete times are
78.506/27.656/31.375 seconds. This is a success-conditioned descriptive subset;
the failed cell is separately disclosed. It is not a general speedup estimate.
Only one run was made, the cases are tiny, ordering is prospectively rotated,
and the model omits deadheads, partial windows and shared charging resources.
The depleted cases also let fleet size change initial inventory. The
replenished control is fixed at two buses, with explicit terminal markers and
a possible marker-only idle chain; it is not an optimal cyclic fleet-sizing
benchmark.

The next sound step is independent auditing and manuscript integration of the
positive reuse result, adverse proposal result and preserved status failure.
Before any further experiment, consider a separately frozen **bound-aware
pricing admission** contract: physically replayed feasible incumbents supply
upper bounds, trustworthy finite solver bounds supply lower bounds, and a
FEASIBLE pricing status can be acceptable only when the final clean certificate
closes. Clean master duals would still require an optimal solve. This requires
proof of the exact solver/bound/reconstruction contract, adversarial tests and
an equal policy across arms. It is a prospective robustness change, not a
retrospective repair of this run or evidence of learned-model utility.

Do not launch an ML campaign from this outcome. The fixed grid exhibits five
clean pricing calls beyond the twelve mandatory first verifications, with only
four positive transition cells; that is too little evidence for a broad
learning claim and gives no held-out generalization result. A later campaign
should establish enough larger, reviewer-relevant variation and a plausible
cost advantage for a selective/cheap proposal, with discovery/evaluation
separation frozen before observing outcomes.
