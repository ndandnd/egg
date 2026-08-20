# Strict undamped two-cycle witness

`result/strict_two_cycle/WITNESS.json` is a canonical, machine-checkable
computational witness for one synthetic EVSP instance. It is regenerated with:

```bash
cd src
python3 experiments/minimize_strict_cycle.py \
  --out ../result/strict_two_cycle/WITNESS.json
python3 experiments/minimize_strict_cycle.py \
  --out ../result/strict_two_cycle/WITNESS.json --check
python3 -m egglab.enumerate_tiny \
  --replay ../result/strict_two_cycle/WITNESS.json
```

The reducer uses a closed fixture recipe only. It starts with the four trips
from `synthetic_instance(seed=5, n_trips=4)`, one forced-singleton padding
trip, three vehicle slots, and affine feedback in every time slot. Deterministic
chunk deletion plus a one-minimal pass removes the padding trip, one vehicle
slot, and every inactive feedback coefficient. The result has four trips, two
vehicle slots, and one nonzero feedback coefficient. If that target is missed,
the driver stops at its one-agent-day/128-oracle budget; it does not expand to
another seed or grid.

## Operational strictness

The witness calls a cycle strict only when:

1. the undamped (`alpha=1`) price state has prime period two;
2. the two responses have different trip-partition/arc-kind structures;
3. complete tiny enumeration optimizes the continuous charging LP of every
   feasible structure at each cycle price;
4. the best structure beats every other optimized structure by more than all
   objective tolerances; and
5. an optimal-face calculation confirms that the selected structure's
   aggregate load is unique at the stated replay tolerance.

A linear program has no positive objective gap to an arbitrarily nearby
feasible point. Accordingly, the positive margins in the JSON are explicitly
discrete-structure and opposite-endpoint margins. They are not presented as a
uniform margin over the continuous charging polytope.

## Computational evidence versus theorem statement

The JSON keeps these separate.

The computational section contains the serialized instance and market, both
schedules, loads, induced prices, all three solves through first recurrence,
strict margins, every feasible/infeasible enumerated structure, physical
replay, trip/feature irreducibility trials, dictator subproblems, and the
convex-hull interval.

The fixed-point conclusion additionally invokes the separately labeled lemma
`T1-fixed-point-necessary-dictator`: with diagonal nonnegative affine slopes, a
self-confirming posted-price best response must minimize

```text
operations + a·L + 0.5 Lᵀ diag(b) L.
```

This follows by adding
`0.5 (L'−L)ᵀ diag(b) (L'−L) >= 0` to every best-response inequality. Complete
enumeration finds a unique dictator structure/load for this instance, while a
different response improves its posted-price objective at its induced price by
more than the tolerance ceiling. Under the lemma, no fixed point exists for
this serialized continuous-charging instance.

This is not a universal cycling, convergence, or real-fleet theorem.
