# Decision on transferring the gap across an energy-law change

Analytical assessment only. This note uses EXACT_ENERGY_DOMINANCE_LEMMA.md and the reported conservative public separation D−CH >= 0.390674; it reads no coefficients, plans, certificates or instance values. It authorizes no model change or computation.

**Decision: retain the declared coefficient/mode scope unless additional feasibility and certificate premises are established.** The gap supplies a possible perturbation budget, not the missing premises. Neither small rounding errors nor an objective continuity argument alone establishes scope transfer.

## A sufficient transfer statement

Let the certified model have lower bound L on EVERY physical plan and upper bound U on its convexified optimum, with L−U >= g > 0. Let the proposed additive-law model be a separately defined target. Two independently justified inequalities suffice:

1. Every target physical plan can be mapped to a certified-model feasible plan with certified objective at most its target objective plus epsilon_D. Then D_target >= L−epsilon_D.
2. A target-feasible convex mixture is constructed whose target cost is at most U+epsilon_CH. Then CH_target <= U+epsilon_CH.

Consequently D_target−CH_target >= g−epsilon_D−epsilon_CH. Strict support separation survives if epsilon_D+epsilon_CH < g, using the same participant, differentiable-convex supply and attainment assumptions as the original support theorem. Equality of this sum with g does not establish a strictly positive gap. Nonnegative error allowances can be chosen without loss for this sufficient statement. The reported g permits 0.390674 as a conservative threshold, but no allowance is established here.

If the two mappings additionally provide componentwise or norm-bounded load changes and controlled operating costs, a bound on the supply gradient over a common compact load domain gives an objective error allowance. For example, |F(u)−F(v)| <= M||u−v|| when ||grad F||_* <= M on their connecting segments. This classical inequality is useful ONLY after feasible mappings and a common domain exist. Nonlinear supply cost must be evaluated at the mixed load for a mixture; averaging component objective errors without controlling that aggregate is insufficient.

## The decisive obstruction is feasibility

A uniform bound on per-leg energy perturbations does not furnish either mapping. With no reserve or time/power slack, arbitrarily small increases in service/leg consumption can make a previously feasible duty exceed usable battery capacity before its next charging opportunity. No increase in later terminal energy repairs that earlier violation. Similarly, full terminal inventory and a saturated terminal charging window can make an arbitrarily small extra recharge requirement infeasible. These obstructions persist even when the supply objective is smooth and strongly convex and all energy coefficients remain positive.

In the opposite direction, an arbitrarily small decrease can admit a previously infeasible low-fleet duty. A discrete fleet-cost saving need not tend to zero with the coefficient change: the feasibility threshold can be crossed at an arbitrarily small perturbation. Thus there is no general bound |D_target−D_certified| <= C times rounding_error based solely on compact loads, smooth supply, finite leg count or the observed positive gap. The attainable-set correspondence can be discontinuous. Charge curtailment in the exact dominance lemma handles excess SOC, not missing energy or a new infeasible capacity prefix. It cannot justify the required mappings by itself.

This is also why independently small errors on many rounded waits are insufficient: a global path/wait error bound is needed first, then a feasible correction argument. Arbitrary continuous subdivision of a floating waiting function is not controlled by sampling canonical waits. Redefining that function to exact linear waiting changes the model and requires an explicit target definition and inclusion argument.

## Could retained dual certificates supply a robust lower bound?

In principle, yes, without a new optimizer: use the retained multipliers as proposals for a NEW exact certificate under target rows. For a linearized convex lower objective h(x)=beta+c^T x, target constraints A'x >= b', x in finite box [l',u'], and sign-feasible multipliers lambda >= 0, weak duality gives

    h(x) >= beta + lambda^T b' +
            sum_i min{(c−A'^T lambda)_i l'_i,
                       (c−A'^T lambda)_i u'_i}.

Equalities have unrestricted multipliers with consistent sign convention. This finite-box residual formula does not require native optimality or vanishing residuals. A supporting tangent to the TARGET convex objective supplies h. Relative to old rows, the elementary perturbation loss is bounded by sum_j |lambda_j| (|delta b_j| + sum_i |delta A_ji| max{|l_i|,|u_i|}) when the objective/box are unchanged; objective and box changes need their own terms. Large multipliers can make a tiny row perturbation expensive.

However, using that route here requires target-valid row semantics, a complete perturbation bound for every relevant retained leaf certificate, and unchanged exhaustive branch coverage. Old infeasibility certificates and energy-dependent fleet exclusions cannot simply retain their truth values after perturbation. All-fleet lower bounds must cover newly feasible fleet counts too; old one-bus exclusion or higher-fleet energy floors require separate validity. A global target lower bound is the minimum of valid target leaf/fleet bounds, not the value of a convenient old dual. This is a prospective new exact certificate evaluation, even if no solve is used; the existing closed audit does not already provide it.

Moreover, robust lower bounds alone do not transfer the retained hull upper. Both constituent schedules must remain target-feasible, including all intermediate SOC, shared resources and exact final inventory. No upper-bound error allowance follows from their old objective values alone. A new feasibility proof or constructive correction is indispensable, and the task explicitly supplies no slack with which to make one.

## Recommendation

Do not claim that 0.390674 dominates rounding until BOTH target feasibility and quantified certificate errors are established. A no-resolve robust transfer is mathematically possible under those stronger premises, but they are unavailable in this bounded assessment and are substantive, not clerical. Finish the canonical metadata/provenance gate as its own result; retain the certified finite-mode/binary-coefficient scope unless the exact-energy lemma closes directly. This is more defensible than adding a speculative perturbation pipeline solely because the numerical gap is positive. The abstract paired-arc theorem and empirical road completeness remain separate questions throughout.
