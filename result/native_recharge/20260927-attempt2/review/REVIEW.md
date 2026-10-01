# Independent V2 native-recharge artifact audit

27 September 2026. Source/protocol freeze:
`997575d049a66d952a0cb8d79f974f7ba5f4ccf0`.
Original evidence manifest SHA-256:
`d32b90ed66deea0418e56e5996219401eeea1d0d998ee2cab21e9bd239ac5a10`.

**PASS for the frozen V2 synthetic qualification and its numerical witness
policy.** All 15 controls passed: 12 accepted numerical certificates and three
analytically confirmed expected infeasibilities. The independent audit verifies
raw incumbents, constraint residuals, correction ledgers, actual sessions,
objectives, lower bounds and failure-free accounting. Attempt1 remains separate
failed evidence: 12/15 passing, including three extraction/replay exceptions.
Nothing from attempt1 has been overwritten or reclassified.

The auditor uses Python's standard library and the colocated independently
written fixture-audit core. It imports no author implementation and executes no
optimizer. The reviewer inspected the intended model, prospective targets and
source, so this is independent reconstruction rather than a blinded review.

## Verified coverage

| Check | Count/result |
|---|---:|
| Original raw files verified against manifest | 107 |
| Complete controls | 15 |
| Accepted certificates | 12 |
| Expected infeasibilities independently confirmed | 3 |
| Native calls started and returned | 30 / 30 |
| Raw statuses | 27 OPTIMAL; 3 INFEASIBLE |
| Raw incumbent snapshots checked | 27 |
| Raw variable values checked | 1,030 |
| Finite native objectives minimized independently | 27 |
| Physical witness instances replayed | 27 |
| Explicit charging sessions | 60 |
| SOC events, excluding initial states | 215 |
| Corrected negative variables | 1 |
| Incumbents with nonzero combined correction | 7 |
| Corrupted copies rejected | 16 |

All 107 files and the original manifest remain byte-for-byte unchanged. Frozen
Git object hashes match the archived four-file source snapshot. Controller
elapsed time is 33.73427754128352 seconds; saved native phases total
30.514087001327425 seconds. Every call returned, no hard timeout occurred, and
all declared controls were retained without retries in this attempt.

The twelve certificate widths range from `1.999999966528776e-6` to
`2.0000000944264684e-6` objective units. Every interval contains the independent
exact binary-rational physical optimum of its frozen fixture. These widths
primarily reflect the prescribed two-sided `1e-6` guard. They are not a general
proof that CBC intervals or floating models always have that exact accuracy.
All actual finite solves returned OPTIMAL; the FEASIBLE admission path was tested
with fake oracles during preflight but is not exercised by this native attempt.

| Control | Independently confirmed target | V2 disposition |
|---|---:|---|
| single_linear | 22 | Certified |
| efficiency_linear | 433/19 | Certified |
| cyclic_flat | 37 | Certified |
| cyclic_own_price | 134 | Certified |
| cyclic_hull_price | 153.5 | Certified |
| cyclic_planner | 97 | Certified |
| preserved_reserve_planner | 97 | Certified |
| joint_flat | 733/19 | Certified |
| joint_planner | 38527/361 | Certified |
| fixed_reserve_planner | 99 | Certified |
| fixed_reserve_one_bus | Infeasible | Expected infeasibility |
| terminal_capacity_failure | Infeasible | Expected infeasibility |
| partial_overlap_failure | Infeasible | Expected infeasibility |
| serial_connector | 24 | Certified |
| directed_multileg | 36 | Certified |

The displayed fractions use intended decimal parameters. The auditor actually
minimizes the exact binary-rational coefficients obtained from the stored floats;
these agree with the displayed targets within `1e-10`. It does not replace the
stored efficiency 0.95 or curvature 0.2 by nearby decimal fractions silently.

## Raw incumbent and common-model audit

For every finite solve, the event sequence is required to be exactly: start,
returned native status, raw incumbent, charge normalization, serial decoding,
objective reconstruction, and (for planning) replayed iteration. Every native
variable is present with its index, type, bounds, value and raw representation.
Every variable is mapped exactly once to used-vehicle indicators, trip
assignments, movement selections, before/after SOC, interval charging, market
loads or planner epigraphs. Missing/nonfinite values or mismatched mappings fail.

The auditor reconstructs the elementary intervals directly from frozen case
windows, market edges and resource boundaries, then compares the result with
the snapshot. It reconstructs every following constraint class from input data
and raw values, without invoking the author's model builder:

- Variable bounds and binary integrality; trip coverage; per-vehicle pull-out,
  pull-in and service-flow equalities; used-vehicle ordering.
- Charge selection, complete eligible charging-variable keys, per-interval shared
  resource capacity and at most one available visit per vehicle.
- Owned SOC bounds, service energy equality, every movement's active/inactive
  big-M equality, depot arrival reserve/capacity and full pull-in replenishment.
- Market-load aggregation and every saved planner tangent-epigraph inequality.
- The native linear objective or actual epigraph objective, including driving
  and used-vehicle cost from the raw native values.

Residuals are evaluated in exact binary-rational arithmetic. The maximum positive
reconstructed constraint residual is `4.343192472333612e-12`, below the frozen
`1e-8` native feasibility tolerance. This maximum combines different model units
(SOC/energy, dimensionless indicators and objective units); it must not be
reported as a battery-energy residual. Reconstructing these constraints checks
the archived candidate against the declared mathematical model. It is not an
independent inspection of the solver's internal matrix or an exact proof of
floating feasibility.

## Correction and endpoint audit

Exactly one raw negative charge is normalized to zero: `cyclic_own_price`,
round 0, native charge key `[1,1,1]` (vehicle 1, its A-only pull-in mode, early
interval), with value `-5.166411062336897e-15` kWh. The exact correction fraction,
variable mapping, before/after entry and period/objective effects agree with the
saved ledger. Its linear charge-correction effect is approximately
`3.099846637402138e-14` objective units. All positive raw charge values remain
represented in the decoded sessions; none is dropped, moved to another market
period or assigned to an unselected vehicle/movement.

For each nonempty interval, the audit independently reconstructs cumulative
energy-proportional endpoints using exact binary-rational arithmetic. First
start and last end equal the exact interval boundaries; every retained positive
energy has a strictly increasing representable float session. The resulting
session list must equal both the decoding event and final plan exactly.

For every actual emitted float duration, the audit recomputes its positive
capacity excess. It sums these excesses and adds the negative-to-zero L1
correction, checking the one `1e-8`-kWh budget for the entire incumbent. It also
checks the separately saved interval aggregate residuals, all exact/decimal
ledger fields and per-period load changes. Maximum combined correction is
`7.105427357601002e-15` kWh, in `joint_planner` round 0. The maximum interval
aggregate excess is `3.552713678800501e-15` kWh. Seven of the 27 incumbents have
nonzero combined correction; even the maximum is more than a million times
smaller than the prospective budget.

The per-incumbent correction is a declared numerical convention, not proof of
exact real-arithmetic feasible repair. Grid energy is retained across endpoint
adjustment, and the independent physical replay checks all resulting schedules
under the frozen tolerances. The larger `1e-6`-kWh physical replay tolerance does
not substitute for the stricter aggregate `1e-8` correction-budget check.

## Physical and global objective reconstruction

The independent fixture core is a byte-for-byte copy of the separately authored
attempt1 auditor. The V2 entry point uses its pure reconstruction helpers with
V2's separate manifest and original success/failure outcomes; it does not run
the core's historical CLI or apply V2 outcomes to attempt1.

Physical replay retains all saved float energies and timestamps unchanged.
It checks exact trip coverage, ownership and windows; travel/service exclusion;
strict pairwise single-connector nonoverlap; resource intersections; grid loads;
intrinsic cost; event SOC; and full replenishment. The maximum observed SOC-bound
residual is `1.1013412404281553e-13` kWh, and maximum reconstructed power is
`30.000000000000014` kW. These residuals remain visible under the frozen
`1e-6`-kWh / `1e-7`-minute physical convention. They are not rationalized away.
The 27 witnesses are archived instances, including all planner rounds, rather
than a claim of 27 distinct operating schedules.

The complete cyclic fixture projects to one- and two-bus intervals in early grid
energy x. With `T=30/eta`, early connector power P, capacity C and reserve r:

- One bus: `max(0,(30+r-C)/eta,T-30) <= x <= min(P,15/eta)`, fleet cost 7.
- Two buses: `max(0,T-30) <= x <= min(P,15/eta)`, fleet cost 14.

Grid loads are `(0,x,0,T-x)`. Early charge uses the A-serving bus. Terminal
energies can be sequenced on the single 30-kW connector precisely when their
total is at most 30; this proves both necessity and constructive sufficiency of
the projected intervals. Fleet-cap one removes the second branch. The other
fixtures reduce to fixed service/travel energy or to the available partial-window
capacity of the simultaneous-service pair.

On each interval the auditor evaluates linear endpoints, quadratic stationary
points and endpoints, or every relevant saved affine-piece intersection for a
PWL envelope. Exact rational candidate evaluation gives a complete global
minimum for these small fixtures. All 27 finite native objective/lower-bound
pairs agree within `1e-6`. The three infeasibilities follow independently from
insufficient early, terminal or partial-window capacity. Saved tangent evolution,
immutable snapshots, native epigraph slack, true versus envelope objectives,
correction effects, outward guards and final best-witness/bound selection also
reconstruct. Final intervals contain the independent exact fixture optima.

This is fixture-specific analytical confirmation. It does not validate arbitrary
operational source graphs, prove unrestricted pricing completeness, establish
larger-instance performance, or independently certify arbitrary native bounds.
A separate frozen cross-backend replication is now a justified next gate; it has
not been performed by this review and must retain its own results and failures.

## Corruption controls and reproduction

Sixteen corrupted in-memory copies fail: raw SOC, raw assignment/integrality,
missing raw snapshot, inconsistent numeric representation, duplicate mapping,
compiled capacity, negative exact total, omitted correction, materialized excess,
endpoint spill, deleted positive session, objective correction, saved SOC,
native bound, final interval and tangent history. Original artifacts are never
changed by these checks.

Run from the research worktree:

```sh
python3 -B result/native_recharge/20260927-attempt2/review/audit_native_attempt2.py --repository .
```

For portability, copy both Python files and pass explicit `--attempt` and
`--repository` paths. The repository must contain the frozen Git object. No
CBC, Gurobi, Python-MIP, NumPy or author package installation is required.
Output defaults to an exclusively created unique temporary file; its absolute
path is printed. Explicit `--out` must be a new file outside Git repositories.
The archived report was copied into this derived directory separately. The
separate review manifest hashes both audit files, this report and audit output;
the original experiment manifest remains unchanged.
