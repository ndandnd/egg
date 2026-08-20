# Cursor handoff: outcome-blind certified uplift settlement

Date: 2026-08-20

Status: normative implementation specification. This task builds arithmetic
and tests only. It does not apply the arithmetic to any committed B2 or B3
population.

## 1. Scientific boundary

The implementation MUST NOT read, inspect, summarize, select, or adapt to any
committed B2/B3 population or outcome. In particular:

- no file under `result/` is an input;
- no B2/B3 CSV, checkpoint, run tree, analyzer, or population manifest is
  imported or parsed;
- tests use invented endpoint certificates in temporary directories only;
- no solver, experiment, confirmation stage, launcher, or result artifact is
  run; and
- connecting this arithmetic to real B2/B3 evidence is a separate reviewed
  task.

The production interface consumes one purpose-built endpoint certificate. It
must refuse an input or output path under the repository's `result/` tree
before reading or writing it. Its exact schema is not a population adapter:
unknown keys fail closed.

## 2. Convention and certified inputs

All arithmetic uses decimal endpoint strings and directed outward rounding.
Binary floating-point is not claim-bearing.

For slot `t`, `p_t in [p_t.lo, p_t.hi]` is an outer coordinate projection of
one joint convex-hull-price certificate. The coordinate box is NOT asserted to
be Cartesian: an arbitrary endpoint combination or midpoint need not be a
supporting price. For participant `i`:

- `q_it` is signed net withdrawal (demand/charging is positive; supply is
  negative);
- `c_i` is assigned intrinsic cost, excluding energy transfers;
- `v_i(p) = min_x {c_i(x) + p*q_i(x)}` is a certified enclosure of the
  participant's best-response objective over the SAME price certificate; and
- the assigned action is feasible for that same participant model.

The endpoint producer, not this calculator, certifies those premises. A later
adapter must bind them to replayed solver evidence. Merely labelling an
arbitrary vector a convex-hull price is not a certificate.

The system endpoints are:

```
z_D  in [z_D.lo,  z_D.hi]   # integrated integer/dictator optimum
z_CH in [z_CH.lo, z_CH.hi]  # integrated convex-hull optimum
```

The certificate declares participant coverage as:

- `complete`: every separable objective/decision block in the Lagrangian is
  represented; or
- `partial`: the listed LOCs are only a subtotal and no equality claim is made.

Coverage alone does not authorize an equality claim. A separate
`uplift_loc_identity_certificate` may assert `sum_i LOC_i = z_D - z_CH` only
when it certifies ALL of the following:

1. complete separable-block coverage;
2. a jointly feasible and exactly balanced assigned profile;
3. that assigned profile attains the integrated integer optimum `z_D`;
4. one common price represented by the price certificate is dual-optimal;
5. convex-hull strong duality at that price; and
6. every participant best-response enclosure is evaluated at that same price.

To see why each premise is load-bearing, let `d(p) = sum_i v_i(p)` and let
`C(x_hat)` be the intrinsic cost of a balanced assignment. Then

```
sum_i LOC_i(p)
  = (z_D - z_CH)
    + (C(x_hat) - z_D)
    + (z_CH - d(p)).
```

Complete coverage does not remove assignment or dual suboptimality. If the
identity certificate is absent, the calculator reports uplift and total LOC
separately even when coverage is `complete`.

## 3. Interval arithmetic

For intervals `X=[x_lo,x_hi]`, `Y=[y_lo,y_hi]`:

```
X + Y = [down(x_lo + y_lo), up(x_hi + y_hi)]
X - Y = [down(x_lo - y_hi), up(x_hi - y_lo)]
X * Y = hull_down/up of all four endpoint products
```

The assigned volumetric charge and private cost are:

```
E_i = sum_t p_t * q_it
A_i = c_i + E_i
```

Raw lost-opportunity cost:

```
LOC_i_raw = A_i - v_i
          = [A_i.lo - v_i.hi, A_i.hi - v_i.lo].
```

Feasibility implies `LOC_i >= 0`. Preserve the raw interval and report the
theorem-tightened interval
`LOC_i = [max(0, LOC_i_raw.lo), LOC_i_raw.hi]`. A strictly negative raw upper
endpoint contradicts the certificate and must fail.

The two-part tariff uses a charge-positive-to-participant convention:

1. volumetric charge: `E_i`;
2. minimum fixed commitment payment **to** the participant, conditional on
   performing the assigned action: `LOC_i`;
3. equivalently, fixed tariff charge to the participant: `-LOC_i`.

An unconditional payment does not alter action incentives and is not a
supporting tariff.

At the exact minimum payment, the assigned all-in private cost equals `v_i`.
For interval reporting, compute the net charge through the dependency-safe
identity `v_i - c_i`; do not naively subtract independently widened `E_i` and
`LOC_i`. A scalar payment of `LOC_i.hi` is the conservative payment that
supports the assignment for every value admitted by the endpoint certificate;
report its resulting net-charge and all-in-cost enclosures separately.

System uplift:

```
U_raw = z_D - z_CH
      = [z_D.lo - z_CH.hi, z_D.hi - z_CH.lo].
```

The theorem `z_D >= z_CH` gives
`U = [max(0, U_raw.lo), U_raw.hi]`. A negative raw upper endpoint is a
contradiction.

When (and only when) the separate identity certificate proves every premise
above, `sum_i LOC_i = U`; the certified intervals must intersect and an empty
intersection fails closed. Otherwise report both intervals without an equality
claim. In particular, `partial` coverage does not support residual allocation
or even a subtotal inequality unless an additional subset/decomposition
certificate is supplied (not part of this schema).

## 4. Non-claims

Endpoint arithmetic alone does not prove:

- that the supplied price enclosure is a convex-hull-price certificate;
- that arbitrary coordinate combinations or the midpoint of the price
  projections are supporting prices;
- that a best-response enclosure was computed at the supplied price set;
- assignment optimality, exact balance, or strong duality;
- incentive compatibility under private information;
- budget balance (even under complete coverage, zero-balance volumetric
  charges sum to zero while positive commitment credits need funding);
- a unique price or payment when an interval has positive width; or
- equality of one fleet's LOC and total uplift when other decision blocks are
  omitted.

The two-part tariff is a complete-information supporting settlement, not a
mechanism-design result.

## 5. Deliverables and acceptance

- `src/experiments/uplift_settlement.py`: stdlib-only interval library and CLI.
- `src/tests/test_uplift_settlement.py`: synthetic, adversarial battery.
- No generated settlement, population adapter, or `result/` change.

Acceptance tests cover signed interval products, outward rounding, raw versus
theorem-tightened bounds, negative-upper contradictions, complete/partial
coverage separated from the explicit joint identity premises,
assignment-contingent/dependency-safe tariff identities, price-projection and
budget-balance nonclaims, exact schema rejection, dimension/ID mismatches,
non-finite/binary-float refusal, deterministic serialization, no-replace
output, and refusal of repository `result/` paths before I/O.
