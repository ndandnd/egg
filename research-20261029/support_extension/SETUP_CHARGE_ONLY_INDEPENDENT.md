# Exact fixed-matching charge-only setup projection

**PASS: the feasible total charge is one closed interval, possibly empty.** Its upper endpoint follows from a sort-and-scan calculation. This is elementary fixed-assignment resource allocation, not an exact joint-matching reduction or a new complexity/empirical result. Independent analytical reasoning only; no execution, data, imports, tests, hashes or other agent's candidate were used.

## Assumptions and notation

Fix the buses and their service assignment. In the common unit early window bus i has a TRUE physical early-charge interval `[r_i,u_i]`, with0<=r_i<=u_i. Charge only; no exports. Each positive recipient incurs one setup tau>=0 occupying the shared connector without energy. Transfer power is at most common K, accepted by every bus. There is no other draw, intrawindow deadline, taper, minimum session, additional switching cost or access asymmetry. Terminal charging has no setup and restores each battery full. All energies and power-times use consistent units; the formulas below use unit efficiency.

Under charge-only monotone SOC and full common availability, multiple early sessions for one bus are unnecessary: combine its assigned energy into one action and serialize buses. Thus “one setup per active bus” and the best feasible schedule under “one setup per nonzero early action” agree here. This would not hold without the stated timing/access assumptions.

Let mandatory set M={i:r_i>0}, q=|M|, and R=sum_i r_i. Let U_M=sum_{i in M}u_i. Discard only ZERO-capacity optional recipients from the capacity scan, retaining their buses in the physical/fee count. Sort the remaining optional capacities as v_1>=...>=v_p>0. For k=q,...,q+p define

`A_k=U_M+sum_{j=1}^{k−q}v_j`, `T_k=K(1−tau k)`.

## Exact early interval

For K>0, if `R>T_q`, the early problem is infeasible. Otherwise

`C_max=max_{q<=k<=q+p} min(A_k,T_k)`

and the attainable totals are EXACTLY `[R,C_max]`.

This expression is valid even if some later T_k are zero/negative: the feasible baseline k=q already contributes at least R. Such later candidates cannot improve the maximum and do not imply a schedule with a fictitious active zero-energy recipient.

### Proof

For a charge vector with k active recipients, necessity of shared time is

`C/K+tau k<=1`.

All mandatory recipients are active. Among any k−q optional recipients, their summed capacity is no greater than the sum of the largest k−q optional capacities. Thus C<=A_k and C<=T_k. The necessary minimum total is R, and its minimum setup count is q. Failure of R<=T_q therefore proves infeasibility, independently of any capacity ordering.

Conversely mandatory recipients alone attain every total in[R,U_M]. For k>q, the selected top k−q positive optional capacities together with mandatory intervals attain every total in(R,A_k] with all selected optional recipients positive. Positivity causes no missing upper endpoint: an arbitrarily small positive allocation can be given to each selected optional bus and the rest distributed through the interval headrooms. A candidate `min(A_k,T_k)>R` is consequently attained by exactly k active recipients and fits the connector time; if the maximum equals R, use only the q mandatory recipients. All endpoint cases are therefore attained, including C_max.

Finally, if a vector with total C is feasible, decrease optional charges to zero as needed and decrease mandatory charges no lower than their r_i to reach ANY C' in[R,C]. The active count cannot increase, transfer time decreases, and removing a zero action removes its setup. Hence the attainable set has no holes. This proves the closed interval claim.

Equivalently, for R<=C<=A_{q+p}, the minimum number of active recipients is

`k_min(C)=min{k:C<=A_k}`.

Feasibility is exactly `C/K+tau k_min(C)<=1`. The stepwise nondecreasing count explains why feasible totals form a lower interval despite setup discontinuities. The scan identifies the maximum of that interval without solving a mixed-integer program.

## Boundary and terminal cases

If q=0, then R=0,A_0=0. The zero total is attained with NO action or setup, for every tau, even tau>=1. The k=0 scan term is0. If all u_i=0, C_max=0. If q>0, R>0; tau q>=1 makes positive transfer impossible and is detected by the baseline test. Equality R=T_q is feasible with mandatory recipients charging exactly their r_i; later optional choices cannot improve it.

If K=0, division by power is not used. The only possible early total is0, feasible exactly when every r_i=0. There are no active early recipients or setups. Empty algebraic recipient lists likewise give only0, though the fleet model normally contains mandatory services. At tau=0 the formula reduces to the familiar `[R,min(sum u_i,K)]` when nonempty.

Let D be the fixed fleet's total service/transition energy that must be replenished from the grid under unit efficiency. Full refill gives terminal purchase L=D−C. With terminal budget H>=0, the final joint projection is

`C in [max(R,D−H,0), min(C_max,D)]`, `E=C`, `L=D−C`, `c=fN`,

provided the early interval exists and the displayed endpoints are ordered. Otherwise it is empty. In an actual full-start two-batch SOC model, u_i is already no larger than that bus's total consumption, so sum u_i<=D and the upper clipping by D is redundant; retaining it makes the accounting explicit. H=0 requires C=D and all buses already full after their last consumption, not merely a net inventory credit. The point interval is admitted if its physical boxes allow it.

For common equal charging efficiency alpha in both windows, define r_i,u_i as GRID-side early quantities and D=S/alpha. The same setup/time scan and L=D−C apply. One must not mix battery-side r_i with grid-side power K. Unequal window efficiencies need the corresponding affine terminal-accounting adjustment, not this unmodified D−C expression.

## Actual SOC and serial realization

The premise that `[r_i,u_i]` is the complete physical box is essential. In the unit-efficiency two-batch model, a bus consuming a_i before early charging and v_i afterward has

`r_i=max(0,a_i+v_i−B)`, `u_i=a_i`.

For A-only/B-only buses set the absent consumption to0. Require0<=a_i<=B and0<=v_i<=B; otherwise the nonempty-box premise can fail. These bounds keep pre-early, post-early and post-service inventory in[0,B], with nonnegative draw throughout the prescribed service/task blocks. Monotone early charge between valid endpoints preserves SOC during transfer; energy-neutral setup/wait also preserves it. Charging all selected buses serially at power K after their respective setups takes exactly C/K+tau k<=1. Each terminal refill D_i−C_i is nonnegative and within capacity, and serializes at terminal power H when their total L<=H.

A generic upper bound u_i that ignores individual headroom or nonnegative terminal refill is NOT enough; aggregate clipping C<=D cannot repair an invalid per-bus box. Nor does this argument cover service charging, regeneration, differing common-window availability, auxiliary draw during setup, per-bus acceptance below K, minimum positive energies or a fixed monetary cost per setup without revising the projection/cost coordinates.

## Fixed matching versus joint matching

The scan needs the mandatory COUNT q, mandatory capacity U_M and ordered optional capacities, in addition to the total requirement R. These depend on the assignment in ways not determined by its summed r-value. The previously reviewed complete-graph example B=10,a=b=(8,4),K=8,tau=1/4 illustrates this directly: the minimum-R cross assignment has two mandatory recipients, while identity has one. Its exact same-fee aggregate sets differ despite the lower R of the cross assignment.

Therefore this provides a clean exact calculation ONCE THE MATCHING IS FIXED. Enumerating or optimizing over matchings is a separate problem; no minimum-R sufficiency, global polynomial matching algorithm, hardness result, new runtime comparison or empirical experiment follows from this sort-and-scan derivation.
