# Strict undamped two-cycle witness

`result/strict_two_cycle/WITNESS.json` is a canonical, machine-checkable
computational witness for one synthetic EVSP instance. It is regenerated with:

```bash
cd src
python3 experiments/minimize_strict_cycle.py \
  --out ../result/strict_two_cycle/WITNESS.json \
  --analysis-code-commit <full-code-commit-sha>
python3 experiments/minimize_strict_cycle.py \
  --out ../result/strict_two_cycle/WITNESS.json \
  --analysis-code-commit <full-code-commit-sha> --check
python3 -m egglab.enumerate_tiny \
  --replay ../result/strict_two_cycle/WITNESS.json --require-backend CBC
```

The reducer uses a closed fixture recipe only. It starts with the four trips
from `synthetic_instance(seed=5, n_trips=4)`, one forced-singleton padding
trip, three vehicle slots, and affine feedback in every time slot. Deterministic
chunk deletion plus a one-minimal pass removes the padding trip, one vehicle
slot, and every inactive feedback coefficient. The result has four trips, two
vehicle slots, and one nonzero feedback coefficient. If that target is missed,
the driver stops at its one-agent-day/128-oracle budget; it does not expand to
another seed or grid.

Here and in the witness, **irreducible means 1-minimal-only on the tested
trip, vehicle-capacity, and affine-feedback deletion axes**. It is not a claim
of global minimality or minimality over a seed grid.

## Operational strictness

The witness calls a cycle strict only when:

1. the undamped (`alpha=1`) price state has prime period two;
2. the two responses have different trip-partition/arc-kind structures;
3. complete tiny enumeration optimizes the continuous charging LP of every
   feasible structure at each cycle price;
4. the best structure beats every other optimized structure by more than all
   objective tolerances; and
5. certified lower/upper extrema over the selected structure's near-optimal
   load face confirm that its aggregate load is unique at the stated replay
   tolerance.

The witness carries the load-uniqueness certificate, not an invariance-over-
all-selections certificate. Complete enumeration supplies a certified positive
margin to every other structure; certified coordinate extrema then bound load
variation within the winning structure. Replay recomputes both parts.

A linear program has no positive objective gap to an arbitrarily nearby
feasible point. Accordingly, the positive margins in the JSON are explicitly
discrete-structure and opposite-endpoint margins. They are not presented as a
uniform margin over the continuous charging polytope.

## Computational evidence versus theorem statement

The JSON keeps these separate.

The computational section contains the serialized instance and market, both
schedules, loads, induced prices, all three solves through first recurrence,
strict margins, invariant certificates for every feasible/infeasible
enumerated structure, exact physical replay of selected responses,
trip/feature irreducibility trials, dictator subproblems, and the
convex-hull interval.

The fixed-point conclusion additionally invokes the separately labeled lemma
`T1-fixed-point-necessary-dictator`: with diagonal nonnegative affine slopes, a
self-confirming posted-price best response must minimize

```text
operations + (a + diag(b)U)·L + 0.5 Lᵀ diag(b) L.
```

This follows by adding
`0.5 (L'−L)ᵀ diag(b) (L'−L) >= 0` to every best-response inequality. Complete
enumeration finds a unique dictator structure/load for this instance, while a
different response improves its posted-price objective at its induced price by
more than the tolerance ceiling. Under the lemma, no fixed point exists for
this serialized continuous-charging instance.

The serialized witness uses the exact normalization
`a' = a + diag(b)U, U' = 0`; this preserves both the price map and dictator
objective for every load. The general lemma above nevertheless retains the
base-load term explicitly.

This is not a universal cycling, convergence, or real-fleet theorem.
