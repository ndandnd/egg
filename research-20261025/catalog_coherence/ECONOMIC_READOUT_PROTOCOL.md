# Economic readout for the fixed two-witness catalog

Prospective reporting contract, 25 October 2026. Based only on
`fit_target_support/NEXT_CATALOG_COHERENCE_DECISION.md` and the completed
`fit_target_support/RESULTS.md`. No original metadata, tables, witnesses,
charges, loads, costs or labels were read; no computations, imports, tests,
hashes, replay or solver work ran. This note specifies interpretation, not an
executable source/field manifest or permission to broaden access.

## Four valuations and an unambiguous sign convention

For a fixed group, P0 is its stored source0 whole-schedule witness and P1 its
stored source1 witness. Independently replay each **unmodified** witness against
the same stored physical case. Let c_j and L_j be the recomputed operating cost
and grid-load vector for witness j. Cached source_replay, stored objective and
stored load are not substitutes for recomputation. A failed replay or identity
check leaves that witness unadmitted; do not repair or substitute a schedule.

The mathematical integrated system-cost expression at source tariff t is

`F[t,j] = c_j + Σ_h a[t,h] L[j,h] + (1/2) Σ_h b[t,h] L[j,h]^2`.

The parent's final representation choice, superseding the earlier float-total
choice after the replay source contract was established, is the native-hull
policy: `F[t,j]=nh.rational(replay['ops_cost']) +
nh.supply(market_t,recomputed_load_j)`. `nh.supply` already returns a Fraction;
preserve it without a float downcast. Reuse the same sequentially recomputed
replay operating value c_j in both markets. D values are exact Fraction
differences of these F values. Validate each market through `nh.validate_market`
before valuation. Linear/quadratic components use the same `nh.rational`
conversions; Ebar is the exact electricity sum divided by4.

| Evaluating market | Fixed P0 | Fixed P1 | Signed difference |
|---|---|---|---|
| source0 | F[0,0], P0 own context | F[0,1], P1 cross context | D0=F[0,1]−F[0,0] |
| source1 | F[1,0], P0 cross context | F[1,1], P1 own context | D1=F[1,1]−F[1,0] |

Positive D always favors P0; negative D always favors P1. Crossing a tariff
changes only a/b in valuation: paths, sessions, load and operating cost of each
witness stay fixed. These are integrated supply/planner costs, not marginal-price
payments. There is no charging reoptimization, route search or QP in this table.

## All nine sign combinations and own-context gaps

Freeze absolute reporting tolerance `τ=10^-6 generator cost units`. For each
exact represented-value D, sign is `+` when D>τ, `−` when D<−τ, otherwise `0`.
Equality at either threshold is in the tie band. Keep exact D even inside it.

| sign D0 \ sign D1 | + | 0 | − |
|---|---|---|---|
| + | P0 wins both; P1 own-context dominated | P0 wins source0, tie source1 | Own-context reversal: each witness wins its own market |
| 0 | Tie source0, P0 wins source1; P1 dominated | Two numerical ties | Tie source0, P1 wins source1 |
| − | Opposite reversal: both own-context witnesses dominated | P1 wins source0, tie source1; P0 dominated | P1 wins both; P0 own-context dominated |

Define independent flags `dominated_P0=(D0<−τ)` and
`dominated_P1=(D1>τ)`; they can overlap. Define raw nonnegative two-witness gaps
`R0=max(0,−D0)` and `R1=max(0,D1)`. Do **not** subtract τ, round the costs before
comparison, or zero a positive R merely because the sign is a numerical tie.
The flags are tolerance-based reporting classifications; R retains the actual
represented catalog difference. Neither R is a full-problem optimality gap.

## Component accounting and scale

For each admitted witness report vehicle count, the fleet operating component,
the movement/deadhead-time quantity used by the unchanged replay's cost formula,
its coefficient and resulting cost, total operating cost c_j, and recomputed
grid energy. Do not relabel a replay-defined movement-leg duration as driving
distance or road-travel time without source support. Source review must bind the
exact quantity and return types; this note does not invent a physical metric.

For each of the four valuations retain linear electricity, quadratic electricity,
their sum and integrated total. Fleet/deadhead quantities and c_j are invariant
across the two tariff rows for a fixed witness. Equal paired vehicle counts in
the support audit do not imply equal route energy, sessions, grid load or total
operating cost after independent replay. Do not drop a component just because a
coefficient is expected to be zero. Report the component-recalculation residual
against c_j. Do not force reconciliation by changing physics or rounding away
that residual, and do not invent a new physical/cost admission guard for it.

Absolute cost differences and R values are primary. If included, the only
proposed common scale is
`Ebar=(electricity[0,0]+electricity[0,1]+electricity[1,0]+electricity[1,1])/4`.
Report D_t/Ebar and R_t/Ebar only for a defined strictly positive Ebar; otherwise
normalization is undefined. No epsilon floor. This is not the warm prior's E0,
an electricity-saving percentage or a percentage of a comparator's total bill.
Units remain generator cost units; do not silently label them calibrated currency.

## Exactness, replay guards and tolerance limits

The chosen API retains Fraction totals from `nh.rational(c_j)+nh.supply(...)`;
retain its represented a/b/load values rather than substituting ideal
decimal/rational inputs such as1/10 or1/900. Compute D by exact Fraction
subtraction and use `tau=Fraction(1,10**6)`; R remains raw and Ebar uses exact
sum/4. This preserves rational evaluation of the represented inputs, including
any rounding already present in sequential replay operating arithmetic.
Converting that operating value through `nh.rational` need not equal separately
recomputing rational fleet/deadhead products; report the exact component residual
rather than changing c_j. Source review binds the unchanged replay and market
validation APIs and their conversions.

Thus “exact D” means an exact difference of source-policy Fraction totals on
specified represented inputs. It is not
a real-number/physical certificate, a teacher optimum or proof that the retained
charge schedule has no numerical uncertainty. The absolute1e-6 band is a fixed
reporting convention, not an economic materiality threshold or statistical test.
It must not widen the unchanged replay's time/energy/cost consistency guards.
Source review must confirm those guards and the selected representation before
command freeze. Only unchanged-source guards and explicit finite/representation
assertions apply; no extra cost/physical tolerance is inferred from this note.
A plan rejected by replay is not made valid by a small catalog difference.

## Denominators, missingness and allowed conclusions

Retain80 intended groups,79 expected paired comparisons and159 expected witness
records. Distinguish expected/present/identity-admitted/replay-valid/replay-failed/
missing witness counts; distinguish valid paired valuations from incomplete or
invalid pairs. The source1-only10037 group contributes its one witness's
bookkeeping but no pair, sign, gap or zero-valued imputation. An unexpected failed
witness remains a finding and reduces the actual paired denominator; it does
not trigger a replacement, available-only positive gate or recovery solve.

Tabulate all nine sign counts over actual valid pairs, with79 expected visible.
Report both dominance flags and their overlap so double domination is not
mistaken for disjoint categories. Weight physical groups equally, not the four
valuations or individual edges. Keep all31 identical-membership pairs and all48
different-membership pairs in the primary planned set. The frozen membership
strata can describe results, but do not select a cost-favorable subset; identical
membership can conceal different charging witnesses. Means, medians, normalized
and absolute quantities must name their own defined denominators.

A coherent reversal supports tariff-dependent preference **within this fixed
two-schedule catalog**. Uniform preference or own-context domination shows that
an observed alternative schedule is cheaper under the specified valuation; it
does not diagnose teacher noise, budget or initialization as its cause. Neither
outcome separates routing from charging effects or proves global optimality,
learned price information, training readiness or generalization. There is no
new statistical/model continuation gate. The completed warm practical-margin
failure remains unchanged; parent decides any next scientific step separately.
