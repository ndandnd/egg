# Tiny local-move column proposer laboratory

Status: **normative bounded-spike specification**. This is the risky
feasibility check for a local structural column proposer. A valid negative
result is an acceptable and publication-worthy outcome of the spike.

Git base: exact `origin/main`
`5b63e725d0fd85cfb0b83f462a612016e7f4321a`.

This laboratory is standalone. It does not depend on the unmerged tiny
branch-and-price work, does not modify A2 or A6, and does not launch a cluster
campaign.

## 1. Question and non-claims

At a clean restricted-master dual, can a deterministic one-move neighborhood
around the active complete-schedule columns produce any **strictly
negative-reduced-cost, physically replayable, novel master column**?

Only that question is scored. In particular, the laboratory does not score:

- raw move count, structural novelty, or schedule-hash changes;
- a heuristic objective or an un-replayed solver aggregate;
- wall time or the number of fixed-partition solves;
- agreement with the structure returned by the full pricing MILP; or
- convergence acceleration, exact-pricer replacement, or global pricing
  completeness.

The fixed-partition proposer is never a source of a convex-hull lower bound.
Clean full-fleet pricing remains the only source of global pricing evidence.

## 2. Frozen population and limits

The population is exactly six already-burned synthetic development cells:

```text
seed in {0, 11, 15}
n_trips = 4
b in {0.01, 0.05}
market shape = duck
all other synthetic_instance arguments = committed defaults
```

The generator default gives `max_vehicles = 2`. No seed in 16--37 is
generated or inspected. The six cells are a tiny mechanism laboratory, not an
external-validity sample.

Each cell first runs unchanged production A2 with:

```text
epsilon = 1e-3
budget = 80 full-fleet pricing calls
pwl_tol = 1e-4
full-fleet max_mip_gap = 1e-9
```

The cell is invalid unless A2 certifies. The proposal study then evaluates
every insertion-ordered prefix of the certified A2 column list. It does not
add proposal columns to A2 and therefore cannot change A2's path or
certificate.

Frozen numerical constants:

```text
reduced-cost tolerance RC_TOL = 1e-6  (the production A2 constant)
active-lambda tolerance = 1e-8
fixed-partition max_mip_gap = 1e-9
replay tolerance = the committed EVSP REPLAY_TOL_KWH
```

## 3. Prefix snapshots and the recorded dual

For each prefix `C[0:k]`, `k = 1, ..., len(C)`, the laboratory independently
solves the ordinary clean RMP through `b2a2.solve_rmp`. Let its link duals be
`pi`, its convexity dual be `sigma`, and define exact recorded oracle prices

```text
p = -pi.
```

The proposer is evaluated only at this exact full-precision `(p, sigma)`.
The regenerated prefix dual need not equal the historical dual that originally
generated column `k`: LP duals can be degenerate. This is deliberate. Every
claim is conditional on the recorded dual representative and active primal
support in the emitted artifact.

Active source columns are exactly those with `lambda > 1e-8`. Vehicle labels
are removed by canonicalizing each source to lexicographically ordered,
time-ordered trip chains. Multiple active columns with the same canonical trip
partition contribute one source partition.

## 4. Frozen local-move catalog

The proposer changes the trip partition only. Arc kind and charging are
re-optimized exactly afterward.

For each active canonical source partition, enumerate in lexical order:

1. **Relocate:** remove one trip from its chain and insert it into any other
   existing chain; also insert it into a new singleton chain when the source
   chain has at least two trips and the fleet limit permits it. Empty source
   chains are removed.
2. **Swap:** exchange one trip from one chain with one trip from a different
   chain.

Trips inside a resulting chain are ordered by `(start_min, id)`, and chains
are ordered lexicographically by their trip-id tuples. Resulting partitions
are deduplicated before pricing. All origins that yield the same partition are
retained as diagnostics, but the partition is priced once.

A resulting partition already represented anywhere in the current RMP prefix
is excluded. An unchanged partition is not a local move. There is no
post-outcome tuning, random ordering, candidate cap, heuristic ranking, or
early stop after the first accepted candidate.

## 5. Exact re-realization and admission

Every unique candidate partition is passed to
`evsp.solve_fixed_sequences(inst, sequences, ("linear", p))`. This MILP
re-optimizes direct/depot arc kinds and continuous charging for the fixed trip
partition.

The outcomes are:

- `INFEASIBLE-PARTITION`: the oracle returns no incumbent;
- `INVALID / HALT`: non-OPTIMAL status, missing/nonfinite bound, malformed
  evidence, or failed physical replay;
- otherwise, apply the B2 physical-load canonicalization, build the ordinary
  complete-schedule column, and independently recompute

  ```text
  rc_candidate = ops_cost + dot(p, physical_load) - sigma.
  ```

The candidate is **ACCEPTED** if and only if:

1. the fixed-partition solve is OPTIMAL;
2. the complete physical schedule independently replays;
3. its full-precision `(load, ops_cost)` `column_key` is absent from the RMP
   prefix; and
4. `rc_candidate < -RC_TOL`.

Other valid outcomes are `DUPLICATE`, `TOLERANCE-TIE` for
`abs(rc_candidate) <= RC_TOL`, and `NONIMPROVING`.

A duplicate with `rc_candidate < -RC_TOL` is a clean-dual/master
inconsistency and invalidates the run. Structural or schedule-hash novelty
never overrides the projected master-column duplicate gate.

The fixed-partition MILP bound is evidence only about that partition. It is
never inserted into `LB_CH`, `lb_best`, or any certification formula.

## 6. Full-fleet opportunity label

At the same `(p, sigma)`, the unchanged full-fleet taker MILP is solved with
`max_mip_gap = 1e-9`, physically canonicalized, and replayed. Record

```text
global_rc_ub = physical incumbent objective - sigma
global_rc_lb = certified full-fleet bound - sigma.
```

A snapshot is a **global improvement opportunity** exactly when the
full-fleet incumbent is novel and `global_rc_ub < -RC_TOL`.

The snapshot is invalid if:

- a duplicate full-fleet incumbent has strictly negative reduced cost;
- `global_rc_lb < -RC_TOL` but no improving incumbent is available (ambiguous
  global pricing at the frozen tolerance);
- a locally accepted candidate exists while the full-fleet solve claims no
  opportunity; or
- any accepted candidate is below the full-fleet certified bound beyond the
  declared numerical tolerance.

Snapshots without a global opportunity remain in the artifact but are absent
from the capture-rate denominator.

## 7. Score and outcome taxonomy

For each opportunity snapshot:

```text
captured = at least one local candidate is ACCEPTED
```

The primary score is:

```text
captured_opportunities / global_opportunities.
```

Candidate counts, move origins, global/local reduced-cost gaps, and solver
statistics are diagnostics only.

The laboratory disposition is the first applicable state:

1. **INVALID-HALT**: any baseline, exactness, replay, provenance, arithmetic,
   completeness, or audit gate fails. This is not a scientific result.
2. **NO-OPPORTUNITY**: the six valid cells contain no global improvement
   opportunity snapshots. The design is uninformative.
3. **HONEST-NEGATIVE**: at least one opportunity exists and none is captured.
4. **LIMITED-SIGNAL**: capture rate is strictly between 0 and 0.5.
5. **POSITIVE-SPIKE**: capture rate is at least 0.5.

The 0.5 threshold is a frozen engineering gate, not a significance level.
Even `POSITIVE-SPIKE` authorizes only a separately specified integration
experiment. `HONEST-NEGATIVE` closes this exact proposer definition without
changing moves, seeds, tolerances, or denominators after seeing the result.

## 8. Evidence and audit

The canonical report records:

- full 40-character analysis commit and exact base commit;
- solver backend/library identity and every frozen constant;
- exact cell and instance/market hashes;
- A2 certification outcome and insertion-ordered column keys;
- every prefix's full-precision dual/prices, lambdas, active source
  partitions, and complete move catalog;
- full replay evidence for the global pricing incumbent and every feasible
  candidate;
- exact reduced costs, novelty, classifications, opportunity/capture labels;
  and
- aggregate counts and mechanically derived disposition.

The independent no-solver auditor reconstructs the six instances and markets,
regenerates every local-move catalog, re-sums every physical load from charge
events, recomputes operating cost, column identity, reduced cost,
classification, counts, and disposition, and runs the ordinary EVSP replay.
It does not trust stored `replay_ok`, reduced costs, or summary labels.

Publication is atomic into a fresh output directory. The manifest hashes the
report and summary. Existing output or raw-run roots are refused.

## 9. Interpretation limits

- Results are conditional on one solver-selected clean dual representative
  per regenerated prefix. Dual degeneracy means a negative result is not a
  theorem that every optimal dual face defeats every local move.
- The active-support seed set is itself solver-selected. Raw schedule flips
  are especially uninformative under degeneracy, which is why they are never
  scored.
- Fixed-partition solves may cost more in aggregate than one global pricing
  solve. This spike makes no efficiency claim.
- Four-trip synthetic path covers can make a one-move neighborhood unusually
  broad. No result is extrapolated to the n=8/12 population or GIRO data.
- A strict accepted column proves only that the frozen local proposer found a
  valid improving column at that dual. It is not a global pricing certificate.

## 10. Stop rule

Commit the specification, implementation, and tests before producing the
six-cell outcome. Run once under the committed code, audit it, and publish the
result whether positive, limited, no-opportunity, or honestly negative.
Do not tune and rerun. Do not launch a cluster job or downstream campaign.
