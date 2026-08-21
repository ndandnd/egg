# Certified uplift settlement and best-response regret

Status: normative, outcome-blind evidence contract. This specification defines
arithmetic and validation only. It does not connect to, read, or adapt from a
committed B2/B3/A6 result population.

## 1. Scientific and accounting boundary

The implementation consumes one purpose-built JSON certificate and refuses
repository `result/` input/output paths before content I/O. It is not a
population adapter. Unknown keys fail closed.

Accounting is per fleet/participant block. A schedule may contain several
vehicles, but the contract:

- does not allocate a fleet payment among vehicles;
- does not claim individual rationality for a vehicle, driver, or other
  sub-fleet actor;
- does not claim incentive compatibility under private information; and
- does not claim budget balance.

The two-part tariff is a complete-information, performance-contingent
supporting settlement.

## 2. Versioned endpoint schema

The sole input schema is `uplift-settlement-endpoints-v2`; the sole output
schema is `uplift-settlement-arithmetic-v2`. Decimal endpoint strings are
claim-bearing. Binary floating-point endpoints are forbidden.

For slot `t`, signed net withdrawal `q_t` is positive for demand/charging and
negative for supply. Thus `p_t q_t` is a charge to the fleet. The assigned
private cost is

```text
A(s*,p) = intrinsic_cost(s*) + sum_t p_t q_t(s*).
```

Top-level convex-hull price intervals are outer coordinate projections of one
joint certificate, not a Cartesian set of supporting prices. Each
best-response record additionally carries one full exact price vector inside
those projections. All reported fleet blocks must use the same vector.

## 3. Global best-response evidence

Every participant carries one
`uplift-best-response-evidence-v1` record with:

- certificate id and certified status;
- instance hash;
- full ordered price vector, its SHA-256, and the matching top-level price
  certificate id;
- objective convention
  `minimize-intrinsic-cost-plus-price-dot-net-withdrawal`;
- a feasible schedule (trip chains, arc kinds, charges, fleet count), exact
  load vector, intrinsic cost, full witness SHA-256, and load SHA-256;
- a passed replay result, replay policy, and empty violations;
- solver backend/version/status and maximum MIP gap;
- feasible incumbent (upper bound for minimization); and
- certified global dual bound (lower bound).

The only globally certifying evidence tier is
`global-exact-oracle-certified-bound-v1`. Restricted-pool, truncated,
heuristic, or locally searched evidence cannot be represented as a global
certificate: validation requires that exact literal tier.

The parser recomputes price/load/witness hashes, checks schedule shape and
charge association, recomputes the witness private objective, and requires it
to agree with the incumbent within the declared absolute tolerance `1e-6`.
The dual bound must not exceed the incumbent. The resulting best-response
value certificate is

```text
V(p) in [certified_dual_bound, incumbent].
```

The endpoint producer remains responsible for independently replaying physical
feasibility against the bound instance. The settlement record binds and
requires a passed replay result; it does not import an optimizer.

## 4. Price-conditioned regret

For assigned target schedule `s*`, exact evidence price `p`, and
`V(p) in [LB,UB]`:

```text
regret(s*,p) = max(0, private_cost(s*,p) - V(p))
raw interval = [target - UB, target - LB]
tightened    = [max(0, target - UB), max(0, target - LB)].
```

`target` is recomputed from assigned intrinsic cost, assigned net withdrawal,
and the evidence price vector. If assigned primitives themselves are
interval-valued, the implementation applies the same directed-outward
subtraction to their resulting target interval. Both raw and nonnegative-
tightened endpoints are retained. A negative raw upper endpoint contradicts
target feasibility and fails closed.

## 5. Lost-opportunity cost and tariff

For top-level price projections and certified best-response interval:

```text
E_i       = sum_t p_t q_it
A_i       = c_i + E_i
LOC_i_raw = A_i - V_i
LOC_i     = [max(0, LOC_i_raw.lo), LOC_i_raw.hi].
```

All interval operations use `Decimal` with 80-digit directed-outward rounding:

```text
X + Y = [down(x_lo+y_lo), up(x_hi+y_hi)]
X - Y = [down(x_lo-y_hi), up(x_hi-y_lo)]
X * Y = hull of all four endpoint products, outward rounded.
```

The tariff charges `E_i` and pays the fleet `LOC_i`, conditional on performance
of the assigned action. Equivalently its fixed charge to the fleet is
`-LOC_i`. The scalar `LOC_i.hi` is the conservative guaranteed payment for
every value admitted by the interval. Dependency-safe net charge at the exact
minimum payment is computed as `V_i-c_i`, not by independently subtracting
widened intervals.

## 6. System internal uplift and joint identity

With certified system objectives:

```text
U_raw = z_D - z_CH
U     = [max(0,U_raw.lo), U_raw.hi].
```

Internal uplift is not generally one target fleet's price-conditioned regret.
The committed tiny counterexample has:

```text
target fleet regret = [2,2]
other fleet regret  = [1,1]
internal uplift     = [3,3].
```

The valid relation in that fixture comes from a separate complete joint
identity certificate:

```text
sum over all certified fleet-block regrets = total LOC = z_D-z_CH = 3.
```

No universal equality or inequality between one fleet's regret and system
uplift is claimed.

Coverage alone cannot assert `sum LOC = z_D-z_CH`. The separate
`uplift_loc_identity_certificate` must certify:

1. complete separable-block coverage;
2. joint feasibility and exact balance;
3. integer optimality of the assigned profile;
4. one common dual-optimal price;
5. convex-hull strong duality; and
6. best responses at that same price.

Without all premises, uplift, LOC, and regret are reported separately.
Partial coverage supports neither residual allocation nor a subtotal
inequality.

## 7. Validation and determinism

Acceptance includes:

- complete tiny schedule-partition enumeration;
- actual CBC `regimes.solve_taker` certificates on burned seeds
  `{0,11,15}` with `n_trips <= 8`;
- independent physical replay of those witnesses;
- exact-oracle tier rejection for restricted/heuristic records;
- adversarial price, witness, instance, bound, solver, and replay tampering;
- raw-versus-tightened interval tests;
- the explicit uplift-versus-regret counterexample;
- duplicate-key and unknown-key refusal;
- deterministic canonical JSON and no-replace output; and
- refusal of repository result paths before I/O.

No generated settlement or committed result population is part of this
contract.
