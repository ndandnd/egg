# Independent review of the quadratic regret-radius derivation

27 September 2026. Verdict: **PASS under the stated compact complete-set,
quadratic PSD supply and fixed-price deviation assumptions.** No mathematical
correction is required. This is an explanatory proof review, not a new solver
experiment or a novelty assessment. The reviewer did not author the derivation.
The reviewer has authored other native model/hull code in this project; none is
used as an oracle in the exact checks below.

Reviewed source: `doc/QUADRATIC_REGRET_RADIUS_DERIVATION_20260927.md`, SHA-256
`1e830230544a1e82c07bc5cce3866c4c0f9c9c9b6a69e6589a0d1f97ed405afa`.
The archived replication data were read without alteration from
`result/cyclic_replication/20260927-attempt1/results.json`, SHA-256
`87523bcad8cdb8a3a3383391a6db42566e83498a85da547a184b8218b69cfb1a`.
No native optimizer, cluster command, manuscript edit or raw-data edit occurred.

## General complete cost/load hull

The proof correctly convexifies the joint cost/load image, not loads alone.
In finite-dimensional space, nonempty compact K has compact conv(K). The
quadratic objective is continuous there, so the hull minimizer exists. For
every `(c,L)` in conv(K), directional first-order optimality along the feasible
line segment from `(c*,L*)` gives

`(c-c*) + (a+BL*)·(L-L*) >= 0`.

This directly proves that the same point minimizes the linear objective
`c+p*·L` on the hull. A linear functional has equal infima on a set and its
convex hull, and compactness attains the physical minimum. Therefore
`V(p*)=c*+p*·L*`, including a nonunique hull minimizer or singular B.
There is no hidden assumption that intrinsic cost is a function of load.

For every physical schedule s, quadratic expansion at L* gives exactly

`H = [c(s)+p*·L(s)-V(p*)] + (L(s)-L*)ᵀB(L(s)-L*)/2`.

Both terms on the right are nonnegative. Thus LOC equals `H-d²/2` and
`d²<=2H`. This is valid for an arbitrary physical schedule; replacing H by the
optimal planning gap is justified only when that schedule is a physical optimum.
The derivation makes that distinction correctly.

For any own-price minimizer t at the **fixed** price `p_s=a+BL(s)`, subtraction
at p* gives

`r(s)=LOC(s;p*)-LOC(t;p*)+(L(s)-L*)ᵀB(L(s)-L(t))`.

Dropping the nonnegative `LOC(t;p*)` and using PSD Cauchy–Schwarz proves the
claimed sharpened bound `H-d²/2+d R_B`, and then the looser monotone bound
`H+sqrt(2H) R_B`. This regret is nonnegative because s itself is an admissible
price response. It is the price-taking objective improvement at a posted price,
not a strategic deviation that changes the price or a difference of social
objectives. Adding the phrase “hold p_s fixed during the deviation” would make
the standalone statement less open to misreading.

## Boundary loads, null directions and lower bounds

A boundary load does not invalidate the argument. Only directional optimality
on conv(K) is used; no unconstrained supply minimum or inverse Hessian is used.
For supply restricted to nonnegative quantities, all relevant loads and their
segments remain in that domain. The polynomial gradient is a valid supporting
choice there, including at zero. A differentiable extension of the indicator
outside that domain is unnecessary.

PSD Cauchy–Schwarz follows by applying Euclidean Cauchy–Schwarz to `B^(1/2)`.
If d=0 then `B(L(s)-L*)=0`, even when the load vectors differ in the nullspace.
Consequently a zero-gap physical schedule has the same gradient price and zero
regret. If B=0, prices are constant and the exact identity is `r=H=LOC`.
The stated weaker bound is then exact. No strict curvature is missing.

The diameter is finite and attained because it is a continuous function of
two points in compact K. No finite bound on individual intrinsic cost changes
is required beyond the compact-image assumption; those changes are already
accounted for in H and LOC.

For a valid lower bound `L_CH<=CH`, the replacement
`Hbar=c(s)+F(L(s))-L_CH` satisfies `Hbar>=H>=0`. The looser bound is monotone
in H for nonnegative H and R_B, so substitution is sound. If only a verified
upper enclosure U_s of the feasible schedule objective is available, the still
more conservative `U_s-L_CH` is also admissible. Neither substitution verifies
the schedule or the diameter; those remain separate evidence requirements.
The derivation appropriately avoids substituting an uncertain estimate into an
exact certificate.

## Exact replication and participant interpretation

The replication feasible loads occupy the complete line segment
`(E,30n-E)`, `0<=E<=10n`: the all-two-bus branch alone reaches both endpoints
and the entire interval. Under `B=I/(5n)`, the squared endpoint distance is
`[(10n)²+(10n)²]/(5n)=40n`. Hence the asserted diameter is exactly
`sqrt(40n)`, not merely an upper bound.

At an audited physical optimum, the load displacement from the hull point is
`(10δ,-10δ)`. Its squared B-seminorm is `40δ²/n=2Δ`. The fleet LOC at p* is
zero, so the sharpened bound reduces to `d R_B=40|δ|<=20`. On `n=40k+1`,
δ=13/40 and this gives 13. The exact regret is
`351/40+169/(40n)`, which equals 13 at n=1 and tends to 8.775. Thus there is
no missing factor of n or square root. The statement concerns a subsequence;
it does not imply one nonzero limit across all integer n.

For a reserved A/B participant, the feasible pair load segment is
`(x,30-x)`, `0<=x<=10`, with the additional one-bus cost/load point. Its squared
diameter in the **same aggregate** B-seminorm is `40/n`. The aggregate price
displacement is still generated by the aggregate vector `(10δ,-10δ)`.
Their product is `40|δ|/n`, yielding the stated per-participant bound.

This step does need the asserted extra premise that each assigned pair is a
best response at the common hull price. It holds here: the nominal hull-price
difference is 7/10, making the one-bus point `(c,E,L)=(7,10,20)` and the
zero-early two-bus point `(14,0,30)` exactly indifferent and jointly minimal.
Reserved connectors make these complete pair alternatives feasible without
depending on other operators' choices. Bounded size alone would not imply
zero common-price LOC in an arbitrary allocation or a shared-resource game.
The derivation states the requisite institution and does not generalize it.

## Deliberate counterexample search and exact checks

Pure Python `Fraction` arithmetic checked the identities and squared forms of
both bounds on three finite cost/load sets. In each case, the candidate hull
point lies in conv(K), and direct support inequalities independently establish
its global optimality. These are algebraic checks, not native solver outcomes:

| Stress case | a; diagonal B | Physical points `(c,L)` | Checked hull point |
|---|---|---|---|
| Singular curvature; a nonoptimal physical schedule | `(0,0)`; `(1,0)` | `(0,(0,0))`, `(-2,(2,7))`, `(2,(4,3))` | `(-1,(1,7/2))` |
| Nonnegative-domain boundary; null direction | `(1,3)`; `(2,0)` | `(0,(0,0))`, `(-6,(0,2))`, `(-5,(1,2))` | `(0,(0,0))` |
| Zero curvature; arbitrary physical cost excess | `(1,-1)`; `(0,0)` | `(2,(0,1))`, `(-1,(2,0))`, `(4,(1,1))` | `(2,(0,1))` |

All nine physical schedules passed exact LOC, nonnegativity, d²<=2H,
sharpened-radius and loose-radius checks. Replacing H by the conservative
`H+1/3` also preserved the loose bound. The deliberately nonoptimal point
`(2,(4,3))` in the first set has `H=21/2`, `d=3`, `R_B=4` and regret 18;
the sharpened bound equals 18 exactly. This rules out inadvertently using
physical optimality in that argument. The boundary fixture's last point also
attains its sharpened bound, with H=3, d²=R_B²=2 and regret 4.

Finally, exact read-only checks over all 86 archived replication sizes and all
88 physical optimizer records, retaining both ties, verified d²=2Δ, zero fleet
LOC, `r<=40|δ|<=20`, the pair-radius product and the stated `n=40k+1` formula.
These checks support transcription; the preceding algebra supplies the general
proof. No counterexample or missing substantive assumption was found within
the explicitly declared scope.
