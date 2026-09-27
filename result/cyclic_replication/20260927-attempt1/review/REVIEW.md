# Independent audit of cyclic fleet replication

27 September 2026. Frozen source/protocol commit:
`ce84e9e62b8e3f33d32010d381fd845415eff458`.
Original result SHA-256:
`87523bcad8cdb8a3a3383391a6db42566e83498a85da547a184b8218b69cfb1a`.

**Verdict: PASS for the stated exact synthetic model.** The independently
implemented auditor reconstructs all 86 cases, all 6,448 continuous branch
minima and all 88 physical optima, including both ties at n=20 and n=60.
Physical feasibility, finite connector assignments, the complete projected
hull, price responses, supplier conjugates, LOC accounts and normalizations
all agree exactly. Twenty-one deliberately corrupted copies are rejected.
The original result file is unchanged.

The auditor uses only Python's standard library and `Fraction`; it imports
no author module and runs no optimizer. Frozen Git files are read only to
verify provenance hashes. This is an independent reconstruction, not a
blinded review: the reviewer saw the candidate formulas and inspected the
frozen implementation/protocol, but did not author either executable.

## Reproduction

From the repository root, with Python 3.8 or later and Git:

```sh
python3 -B result/cyclic_replication/20260927-attempt1/review/audit_cyclic_replication.py \
  --result result/cyclic_replication/20260927-attempt1/results.json \
  --repository .
```

The checkout must contain the frozen commit. No CBC, Gurobi, NumPy or author
package installation is required. The result and checkout paths default to
the containing artifact and repository when the script remains packaged
here. A copied script can use explicit paths from any working directory.
Output defaults to a uniquely named file in the system temporary directory;
the final console receipt gives its absolute path. An explicit `--out` must
name a new file outside the source checkout and outside every detected Git
repository. Existing files, existing symlinks, and paths resolving into a
repository are rejected. Exclusive creation also prevents overwriting a file
created after the preflight check. `audit_wall_s` is the only expected output
difference between otherwise identical replays of the same auditor revision.

[audit_cyclic_replication.py](audit_cyclic_replication.py) is the executable
check; [audit-result.json](audit-result.json) records all exact reconstructed
values, tie cases, the selected subsequence and rejected corruptions.
`MANIFEST.json` separately hashes these derived review files and references
the unchanged original result identity.

The output-safety revision changes only CLI output validation/creation and
console path reporting. Its regenerated scientific report is identical to
the previous report after excluding the auditor hash and elapsed audit time.
[io-safety-controls.json](io-safety-controls.json) records six rejected output
destinations: the raw result, the protocol, a new in-repository filename, an
existing external file, a dangling symlink, and a path entering the repository
through an external symlink. A new external output succeeded. The regenerated
report was copied into this derived review package as a separate maintenance
step; the auditor itself cannot write here. Neither the original result nor
the original experiment manifest/protocol was altered.

## Coverage and arithmetic

| Check | Count |
|---|---:|
| Prospective case sizes | 86 |
| Complete physical partition branches | 6,448 |
| Physical optima, including both ties | 88 |
| Exact rational fields and matching decimal displays | 17,076 |
| Physical templates constructed/replayed | 19,604 |
| Group-level SOC events checked | 288,890 |
| Linear endpoint objective evaluations | 25,782 |
| Deliberately corrupted copies rejected | 21 |

The physical templates cover every branch minimizer and both endpoints,
the two physical hull-supporting components for every n, and every stored
physical-optimum witness. Group multiplicities represent 57,680,595 bus-SOC
events; the audit checks the exact common trace and its integer multiplicity,
rather than falsely claiming to have materialized that many distinct buses.

Every reported exact fraction is parsed as a rational. Its companion decimal
must equal Python's float rendering of that fraction. All economic and
physical checks then use rational arithmetic with equality, not numerical
tolerances or rounding. This is appropriate because the archived physical
construction itself is rationally specified. It differs from the earlier
reuse experiment's floating physical witnesses and numerical replay.

## Complete physical feasible set and finite connectors

At most one A service and one B service can occur on a bus: services within
each family are simultaneous. With n services in each family, let m be the
number of A+B buses. The remaining n−m A services and n−m B services occupy
separate buses, giving exactly `2n−m` used buses, with `0≤m≤n`. Under the
identical-trip, common-depot and zero-deadhead assumptions, labeled service
permutations do not change energy, cost or the aggregate feasible set.
For example, assign A_i and B_i to one bus for i≤m, and to separate buses
for i>m. This proves complete coverage without needing an n! label search.

Every A+B bus requires 10 early kWh, reaches SOC zero after B and then buys
20 terminal kWh. Each A-only bus may buy `u∈[0,10]` early and `15−u` terminal
kWh. Each B-only bus starts full, buys nothing early and buys 15 terminal
kWh. Hence the early range is exactly `[10m,10n]`. For any point x in this
interval and m<n, choose

`u=(x−10m)/(n−m)`.

For m=n the only point is x=10n. The auditor reconstructs every group's
five battery states, bounds them within [0,20], and verifies final SOC 20.
The aggregate charge is exactly 30n for every structure. Additional used
buses therefore do not donate net initial energy.

Finite resource sufficiency is checked before convexification:

- Early: assign one of the n 10 kW connectors to each A-serving bus. Paired
  buses charge at 10 kW and A-only buses at u kW for the one-hour window.
  Aggregate power is constantly x≤10n.
- Terminal: assign one connector to each of the m A+B buses, charging at
  20 kW for one hour. Pair each remaining A-only bus with a B-only bus on
  one of the n−m remaining connectors. Run that connector at constant
  power `30−u≤30`; A uses it for `(15−u)/(30−u)` hour and B for the rest.
  These are nonoverlapping, uninterrupted sessions. Aggregate terminal
  power is constantly `20m+(n−m)(30−u)=30n−x≤30n`.

This uses exactly n available connector positions in each window, with no
simultaneous sharing of one plug. All bus powers and SOC trajectories are
feasible, and the aggregate power is constant within each one-hour window.
Thus the quadratic cost in window energy has no hidden intra-window power
spike caused by sequencing buses. Zero connector switching time, continuous
power, no taper, zero reserve and lossless charging remain explicit model
assumptions. No production EVSP adapter or operational bus is qualified by
this audit.

## Independent branch and complete-hull reconstruction

For fixed m, the physical objective is

`H_n(m,x)=104n−7m−2x+x²/(5n)`, with `10m≤x≤10n`.

The verifier evaluates both endpoints and the derivative's stationary point
when it is inside the interval. It reproduces every recorded minimizer and
cost, then compares every branch to find **all** global optima.

The full projected hull in `(x,c)` is the triangle with vertices

`(0,14n)`, `(10n,7n)`, `(10n,14n)`.

Every physical branch obeys `c+(7/10)x≥14n`, `c≤14n` and `0≤x≤10n`.
All three triangle vertices are physical schedules. These two facts prove
both inclusions, so this is the complete projected hull, rather than a
relaxation inferred from a sample menu. The archived `hull_vertices` field
contains only the **lower hull boundary**, namely the first two vertices.
That boundary suffices for minimization, but the field should not be called
the full triangle's vertex list in manuscript prose.

Minimizing the lower-boundary polynomial

`104n−(27/10)x+x²/(5n)`

gives `x*=27n/4`, intrinsic cost `371n/40`, and `CH_n=7591n/80`.
The physical realizing mixture has weight 27/40 on the all-paired schedule
and 13/40 on the all-single schedule with zero early charging. The auditor
replays both components under their own full physical constraints. Their
mean load is not asserted to be a physically dispatchable fractional fleet
or to deliver its supply cost by randomizing realized days.

## Why the nearest-integer formula holds beyond the tested sizes

For `m≥n/2`, substitution of the physical branch minimizer gives

`H_n(m)=CH_n+20(m−27n/40)²/n`.

For `m<n/2`, the branch value is `99n−7m`, so it is at least `(191/2)n`.
For n≥3, a nearest integer to `27n/40` lies at or above n/2 and has value
at most `CH_n+5/n`. The latter is strictly below `(191/2)n` because
`49n/80>5/n` for n≥3. Therefore no branch below n/2 can defeat a nearest
integer. This comparison completes the argument; merely noting that a
nearest integer lies above n/2 would not by itself exclude the other
piece of the objective.

For n=1, the branch values are 99 and 97. For n=2, they are 198, 191 and
194. These establish the small cases directly. Thus every optimizer has
`δ=m−27n/40` with `|δ|≤1/2`, and

`D_n−CH_n=20δ²/n≤5/n`.

Exactly two nearest integers tie when `n≡20 (mod 40)`. The raw first run
preserves both tested instances:

| n | Optimal m values | Own-price whole-fleet regrets |
|---:|---|---|
| 20 | 13 and 14 | 7 and 14 |
| 60 | 40 and 41 | 20/3 and 41/3 |

The planning gap is common to the tied schedules, but their own gradients
and regrets differ. Any regret figure or table must preserve both values or
state a predeclared selection rule. This experiment preserves both.

## Price, supplier and LOC accounting

At an optimal physical schedule, x=10m and its own marginal prices are

`p=(4+2m/n,6−2m/n)`.

The independent response calculation minimizes the linear fleet objective
over both endpoints of every complete branch. It does not compare only
physical social optima or keep the current pairing count fixed. For a
candidate paired count k, the minimum early endpoint has private objective

`194n−60m+(40m/n−27)k`.

Accordingly, if δ>0 the best response has k=0; if δ<0 it has k=n; and if
δ=0 every paired count is privately optimal at its lower endpoint. This
gives the independently verified whole-operator own-price regret

`40(m/n)δ` for δ≥0,

`40(1−m/n)(−δ)` for δ<0.

Prices stay fixed during this comparison; the operator does not anticipate
the grid repricing its large deviation. This is a whole-fleet price-taking
regret, not a strategic-equilibrium gain, an individual bus's incentive or
an independent firm's gain in a many-firm market.

The supplier conjugate is optimized over nonnegative independent supplies;
the fleet's fixed total 30n is not incorrectly imposed on that supplier
problem. At the physical schedule's own gradient, supply LOC is exactly
zero. At the common hull price `(107/20,93/20)`, fleet response value is
`307n/2`, supplier conjugate is `4689n/80`, and their difference is `CH_n`.
Every physical planner optimizer has fleet LOC zero and supplier LOC exactly
`D_n−CH_n` at these common prices. The audit reconstructs the bills and both
LOC terms directly. Hull prices and own marginal prices must remain distinct
in the text; no budget-balanced payment mechanism is established here.

## Normalization and the subsequence claim

The supply function is deliberately scaled as

`F_n(E,L)=n F_1(E/n,L/n)`.

Demand and supply capacity grow together, preserving marginal prices at fixed
per-copy load. Increasing n while retaining unscaled quadratic curvature
would be a different model, not a replication of this result.

On `n=40k+1`, the unique optimizer has `δ=13/40`, and exact identities are

`gap=169/(80n)`,

`gap/CH_n=169/(7591n²)`,

`R_n=351/40+169/(40n)`,

`R_n/(2n−m)=(351n+169)/[n(53n−13)]`,

`R_n/D_n=2(351n+169)/(7591n²+169)`.

The audit checks all of these for the sampled subsequence n=1, 41, 401 and
1001. The general limits follow from the exact formulas: absolute gap and
relative gap vanish, while the whole operator's absolute own-price regret
approaches `351/40=8.775`; regret per **actual used bus** and relative to the
physical objective both vanish. The record's relative gap uses CH_n in its
denominator; its relative regret uses D_n. Neither is silently replaced by
the other convention.

There is **no nonzero whole-fleet regret limit along all integer n**. Every
size divisible by 40 has exactly zero gap and zero own-price regret; all six
such sizes in the frozen grid are retained. More generally R_n≤20 and
`2n−m≥n`, so per-used-bus regret vanishes along the full integer sequence,
as does relative regret. The distinction is a mathematical normalization
result in synthetic currency, not a statement that a constant regret of
8.775 has material operational or monetary significance.

## Rejected corruptions and remaining scope

The 21 controls independently perturb branch cost, continuous minimizer,
partition completeness, tied-optimum completeness, hull value/boundary,
SOC, terminal energy, group coverage, finite connector counts, paired-single
terminal energy, own price/regret, per-bus and relative-gap denominators,
fleet and supply LOC, supplier conjugate, fleet response value, displayed
decimal agreement and a selected subsequence gap. For mathematical
perturbations, both exact and decimal fields are updated together so the
control reaches the intended reconstruction check rather than failing only
at formatting consistency.

The finite grid is a deterministic verification of a general analytical
identity, not a statistical sample or population runtime comparison. The
stored author runtime is provenance metadata, not independently remeasured
author execution. No data, learning method, independent operators, charging
loss, positive reserve, nonzero switching delay, real timetable or native
adapter is introduced by this replication audit. These limitations are
consistent with the frozen protocol and the separate robustness work.
