# Conditional integer-completion value

## Known obstruction, not a novelty theorem

Six abstract service rows form A={1,2,3}, B={4,5,6}. P has the three pair subsets of each group, cost1 each, and a protected all-six column of cost10. Require exact coverage and at most3 selected columns. This is an abstract set-partition model; the fallback's one-column interpretation is not a physical bus route or the earlier fleet-four model.

The LP uses every pair at1/2, objective3, column count3. Row duals y_i=1/2 and fleet dual0 give a matching lower bound. Add a=A and b=B with costs3/2+epsilon each, 0<=epsilon<7/2. Both reduced costs are epsilon; the same primal/dual certify LP optimum3 over the entire listed universe.

For exact integer value F(Q), no odd triple can be partitioned by its pairs. Thus F(P)=F(P+a)=F(P+b)=10, but F(P+a+b)=3+2epsilon. Protected utility U_P(S)=F(P)-F(P+S) is zero for either singleton and7-2epsilon for the pair. Even strictly positive reduced-cost columns can be jointly useful. Changing a's cost to1 gives a negative initial reduced cost but still zero singleton integer utility. At epsilon=7/2 the pair merely ties; complementarity need not imply useful economic improvement.

This illustrates ordinary integrality and nonadditivity. It neither identifies the cause of the closed EGG failures nor demonstrates ML is needed. A direct classical integer completion finds the pair.

## Exact target and the comparison that prevents an artificial ML advantage

Let P include an admitted common incumbent, U be a fixed candidate universe, and k the maximum number of newly used columns. With original service/resource constraints, define

    V(P,U,k) = min over S subset U, |S|<=k of F(P union S).

For optional columns and exact optimization this equals the single ordinary binary master over P union U with the additional constraint

    sum_{j in U minus P} x_j <= k.

Proof: every feasible solution under an augmentation S uses at most k new columns; conversely any binary master solution uses a set S of at most k new columns and is feasible in P union S. The common incumbent is feasible in every case. The equivalence also holds for a common nonlinear objective if both problems use exactly the same objective and constraints; it provides no efficient solver or full-space certificate.

This comparator receives the same candidate information. Artificially forcing classical methods to choose independently while allowing learning joint choice would manufacture the claimed advantage. When candidate generation itself is the learned action, unseen future candidates may not be handed to a method free of charge; acquisition and selection are separate estimands.

Exact F decreases monotonically when optional columns are added, but **fixed-time solver output is not guaranteed to improve across separate runs on larger pools**. Retention guarantees only that an independently admitted stored incumbent remains available. Therefore keep exact labels/bounds, time-limited teacher outcomes and operational retained outcomes distinct. Do not call a timed teacher endpoint the optimal bundle or merge ties into one label.

## Candidate hypothesis

Condition on current pool, independently admitted incumbent, remaining services, shared plug occupancy, SOC/terminal contract, objective context and remaining paid budget. Predict an augmentation/recovery action whose completed physical fleet improves the retained outcome faster than competent classical completion. Preserve several useful actions and ties, their provenance and costs. Individual routes that occur in different incompatible optima are not one positive bundle.

Minimal ablations if an empirical opportunity exists: independent membership/additive scoring; classical joint completion; compatibility-aware deterministic and random proposals; residual-state-blind versus conditioned bundle supervision. If price information is claimed, train an otherwise matched price-blind proposal; downstream optimization stays price-aware in both. No architecture or fit is selected here.

Potential paper claim, currently UNPROVEN: conditional joint supervision improves decision quality versus time across unused grouped instances beyond strong conventional recovery and additive supervision. A useful theory contribution would explain a nontrivial regime/guarantee of the actual algorithm; the elementary example/equivalence and incumbent preservation are not enough. A strong empirical mechanism could support a paper without inventing an ornamental theorem.
