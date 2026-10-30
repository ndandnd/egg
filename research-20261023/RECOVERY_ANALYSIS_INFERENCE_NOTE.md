# Recovery comparison: scoring and inference contract

Prospective nonnumerical recommendation, 24 October 2026. This note specifies
analysis for the **unlaunched 192-decision development design** in
`RECOVERY_LEARNED_VALUE_STUDY_ADDENDUM.md`, which remains authoritative. It
changes no arm, cohort, practical tolerance, resource limit or launch gate. No
cases, scores, solver outcomes, imports or tests were produced. Historical
results are not pooled into this cohort.

## 1. Fixed units, contrasts and weights

Let `h ∈ {40,80}` index size, `b ∈ B_h` index its four assigned bases, and
`s ∈ S={17,41,73}` index the three paired solver seeds. Every tariff variant,
arm and seed belonging to a base stays in that base. The primary day-tariff
contrast is graph-v8 recovery versus CA1 recovery. The two direct secondary
contrasts are graph versus CatBoost and graph versus CF1; random recovery and
cold unrestricted eight-round search are descriptive reference arms. There is
no outcome-selected classical comparator.

For any oriented pair `(A,C)`, a positive score favors `A`. Define `V_A=1` only
for the actual deployed fallback that is replay-valid, correctly billed and
durably finalized within the common 60-second endpoint. A rejected candidate
is not an admitted witness; a timely valid fallback can still give `V_A=1`.
A complete healthy receipt chain establishing a genuine algorithmic no-plan or
algorithmically late endpoint gives `V_A=0`. Use receipts to classify causes
before pair scoring, without reference to the preferred arm's bill.

Clock/ownership/monitor failure, serialization-integrity failure, unexpected
native-interface failure, ambiguous causes and an undispatched assignment are
unknown. One such endpoint makes the pair unknown even if its opponent is
valid. An invalid admitted witness triggers the engineering stop and is not
converted into an algorithmic loss. Retain it and all uncompleted assignments
in the ledger. Healthy replay/capture/write latency belongs inside the method's
clock; a demonstrated broken capture contract is an engineering failure.

For a pair with known algorithmic endpoints, use exactly

```
τ(A,C) = 0.005 max(|B_A|, |B_C|, 1 currency unit),  when both V=1

X_b,s(A,C) = +1  if V_A=1,V_C=0,
             -1  if V_A=0,V_C=1,
              0  if V_A=0,V_C=0,
             +1  if both V=1 and B_C-B_A > τ(A,C),
             -1  if both V=1 and B_A-B_C > τ(A,C),
              0  if both V=1 and |B_A-B_C| ≤ τ(A,C).
```

Bills are those of the deployed timely valid plans, with the common billing
policy. Equality at the tolerance boundary is a tie. Never compare a nonexistent
or late plan's bill. This score measures practical net wins of complete timed
methods; it is not a mean currency-saving estimand or equal-information learning
attribution. In particular CA1 sees `a,b`, whereas the learners see `a`.

With complete outcomes, the fixed three-seed base, size and overall estimands are

```
D_b(A,C) = (1/3) Σ_s X_b,s(A,C)
θ_h(A,C) = (1/4) Σ_{b∈B_h} D_b(A,C)
θ(A,C)   = (θ_40+θ_80)/2 = (1/8) Σ_b D_b(A,C).
```

Each of the 24 paired seed scores therefore has fixed overall weight `1/24`.
These are the finite assigned-cohort estimands for the fixed seeds and policies.
They do not themselves estimate performance on external networks or tariffs.
Report seed wins/ties/losses and algorithmic validity alongside each `D_b`, both
`θ_h`, and `θ`; preserve denominators 3, 4 and 8. Report every base's signed
outcome and regressions, including zero-exposure cases.

## 2. Missing outcomes: exact conservative completion bounds

For base `b`, let `O_b` contain its known pair scores, let `q_b=Σ_{s∈O_b}X_b,s`,
and let `m_b=3-|O_b|`. Freeze the base interval as

```
L_b=(q_b-m_b)/3,   U_b=(q_b+m_b)/3.

[L_h,U_h] = [(1/4)Σ_{b∈B_h}L_b, (1/4)Σ_{b∈B_h}U_b]
[L,U]     = [(L_40+L_80)/2, (U_40+U_80)/2].
```

The prescribed conservative treatment leaves every unknown practical-pair score
unrestricted in `[-1,1]`. These are finite-cohort partial-identification intervals,
sharp in this deliberately coarse score-level completion set for each contrast
separately, not necessarily sharp given all endpoint information or jointly
attainable across contrasts sharing an arm. They describe what completion of the
fixed comparison could show, not a sampling confidence interval or an estimate
of what repairing infrastructure would cause. A missing base remains
`[-1,1]`; a missing seed is never removed from its three-seed denominator. The
complete prefix and missing suffix retain their originally assigned weights.
Do not use complete-case reweighting, missing-at-random imputation, opponent-win
coding, or a both-invalid tie for infrastructure failures.

Also report the per-arm algorithmic validity fraction and its difference within
each size and overall. For a single arm take known `V∈{0,1}` literally and an
unknown `V∈[0,1]`. For a validity difference use the interval for `V_A-V_C`, keeping
a known opponent's value: for example, valid versus unknown gives `[0,1]`, and
unknown versus known algorithmic failure gives `[0,1]`. Average these intervals
with the same fixed weights. This retains information for the separate validity
endpoint without changing the unknown practical-pair score range `[-1,1]`.
Report acquisition failure, algorithmic no-plan/late, engineering-unknown and
undispatched counts separately; a numerical reliability count does not resolve
an efficacy comparison.

## 3. Four-base price-input mechanism contrast

Let `M_h⊂B_h` be the two bases per size chosen by the frozen salted identity rule,
and let `ℓ∈{graph,CatBoost}`. Within the same shifted target tariff and seed,
compare learner `ℓ` scored with fresh-target prices (`F`) versus recomputed
original-day scoring prices (`O`). Both native optimization/charging policies use
the shifted target tariff. Apply the identical practical score above, oriented
`F` versus `O`, including endpoint cause precedence and the same bill tie band:

```
D_b,ℓ^price = (1/3) Σ_s X_b,s(ℓF,ℓO)
φ_h,ℓ      = (1/2) Σ_{b∈M_h} D_b,ℓ^price
φ_ℓ        = (φ_40,ℓ+φ_80,ℓ)/2 = (1/4) Σ_{b∈M} D_b,ℓ^price.
```

Each of the 12 paired seed scores for one learner has overall weight `1/12`.
Use the same missing-seed base bounds, then weights `1/2` within size and `1/4`
overall. This is a finite-budget method contrast for supplying the ranking
prices on these four fixed bases, three seeds and one prescribed shift. It
neither isolates an abstract graph representation effect nor establishes tariff
generalization. Retain unchanged-feature, unchanged-mask and zero-flexible-choice
cases. For each base and learner, show the frozen-tolerance feature/score/order/
mask-change diagnostics beside these outcomes. A changed score or mask alone is
not economic benefit. The four bases are a subset of the main eight, not four
additional independent confirmation groups.

## 4. Descriptive bill information and fixed reporting table

For both-valid pairs, show paired bills and `B_C-B_A` in currency, plus the
fleet, deadhead/other operations, linear-electricity and quadratic-electricity
components, vehicle count and interval load. For the mechanism pair orient this
as `B_O-B_F`. Mark the both-valid seed denominator for every base; any aggregate
of these conditional gains must also show contributing bases and seeds and be
labelled conditional/descriptive. Do not mix bills with failure penalties, impute
bills for unknown/no-plan endpoints, or claim a bounded currency effect from the
bounded win score. Equal-vehicle subsets remain descriptive, not mediation.

The mandatory main table has one row per assigned base and contrast: size,
three seed endpoint classifications, known wins/ties/losses, unknown count,
`[L_b,U_b]` (or `D_b` when complete), per-arm validity and unknown counts,
both-valid bill/component differences with denominators, and zero-exposure
status. Show the two size summaries before the overall summary. The mechanism
table uses the four fixed bases for each learner and adds its change diagnostics.
No case, seed, tariff or reference arm is silently dropped.

## 5. Why an exact sign-flip p-value is not automatically justified

If complete base effects are `d_1,…,d_n`, an exact two-sided sign-flip calculation
with the fixed aggregate weights would enumerate all `2^n` signs and use

```
T(d)=|Σ_b w_b d_b|
p_flip = #{ε∈{-1,+1}^n : |Σ_b w_b ε_b d_b| ≥ T(d)} / 2^n.
```

The observed pattern is included and ties count in the tail. Exact enumeration
is not a Monte Carlo sample requiring a plus-one correction. This is a valid
null test only when the null law is invariant under every independent base sign
flip (equivalently, conditional on magnitudes, nonzero signs have the required
uniform sign-pattern law). Independent effects individually symmetric about zero
are sufficient; mean zero alone is not. Identical distributions across sizes
are unnecessary under that stronger symmetry condition, but pairing and size
stratification do not establish it. An actual randomized exchange of method
labels within bases could supply a different randomization justification; this
design does not randomize algorithms to units. Rotating execution order and
sharing seeds do not make method-label swaps randomized assignments.

Under that symmetry assumption, the minimum attainable two-sided p-value for
nonzero effects is `2/2^n`, since a sign pattern and its global reversal have
the same absolute statistic. Thus:

| Aggregate | Maximum independent base groups | Smallest possible two-sided p |
| --- | ---: | ---: |
| Main overall contrast | 8 | 1/128 |
| Main within one size | 4 | 1/8 |
| Either learner's overall price-input contrast | 4 | 1/8 |
| Price-input contrast within one size | 2 | 1/2 |

Zeros, ties or fewer observed groups can make resolution coarser, never finer.
Missing outcomes cannot be filled with favorable signs to obtain a test. Even
under justified symmetry, the first step of Holm adjustment across the two
learner price-input contrasts has a minimum adjusted p-value of `2×(1/8)=1/4`.
Three seeds per base do not turn eight groups into 24, or four into 12. They
average solver variability within each fixed timetable; the shared timetable,
tariff variants and learner inputs remain clustered. Treating those replications
as independent signs tests an unsupported null and fabricates resolution.

A sign test has different assumptions and a different target: under independent
base signs with equal positive/negative probabilities it can test sign balance
(handling zeros prospectively), not arbitrary zero mean practical net wins.
Neither that balance nor sign symmetry follows from the current design. A
cluster bootstrap, t interval, or seed-level permutation does not remove the
need for sampling/model assumptions with eight or four groups.

Independent draws from an explicitly specified generator could support some
population inference under separately justified sampling assumptions; bounded
scores can even support conservative distribution-free concentration bounds
under independent sampling. The present fixed development cohort/seed contract
alone supplies neither a target population sampling law nor exchangeability or
independence evidence sufficient to invoke those results. “Distribution-free”
does not mean assumption-free, and more seeds cannot create independent base
draws or evidence about external-network/tariff populations.

## 6. Concrete preregistration decision

**Adopt Sections 1–4 and descriptive inference as the default frozen analysis.**
Report finite-cohort scores, exact missing-completion bounds, full per-base and
per-size tables, conditional bill decompositions and operational reliability.
Do not report confirmatory p-values, nominal population confidence intervals,
“statistically significant” learning/tariff effects or a superiority declaration.
An entirely positive missing-completion bound supports only the literal statement
that practical net wins remain positive across all allowed completions of these
fixed assignments; it is not a population claim or an expansion threshold.

Preserve graph-versus-CA1 as the sole primary comparison. Assess the two direct
secondaries only in that primary-first order; descriptive reporting still shows
all outcomes regardless of direction. If a separately justified inferential
protocol is ever adopted, it must be frozen before fresh cases/outcomes and state
the target, sampling/null assumptions, missing-data treatment and significance
level explicitly: test the primary first, gate the two direct secondaries behind
it and apply Holm to those two; treat the two learner mechanism contrasts as a
separate Holm family. Do not activate that protocol retrospectively or borrow
significance from reference arms. This note recommends no such activation and
introduces no new efficacy threshold. A larger independent study remains a
separate decision under the addendum's existing evidence and engineering gates.
