# Local physical-model and reuse qualification — 21 September 2026

The local solver is restored, eight physical controls pass, and all twelve
reuse cells meet the same clean certificate. On this small control, retained
columns remove all pricing work except the mandatory final verification call.
Adding a shifted-price proposal adds work. This qualifies the adapters and
supports testing harder reuse workloads before investing in learning; it does
not establish operational performance or a general negative result for ML.

## Environment and execution

The original MIP 2.0.0/CBCBox 2.935 environment was killed by macOS code-signing
enforcement during native loading. A clean same-version install reproduced the
failure. A separate native arm64 Python 3.12.2 environment with official PyPI
`mip==1.17.6`, `cbcbox==2.929`, `cffi==2.1.1`, `numpy==2.5.3` and `pytest==9.1.1`
passed LP objective 1, binary MILP objective/bound 3, and infeasibility controls.
Selected wheel hashes match official metadata; native signatures were unchanged.
The restored interpreter is `.research-venv-repaired-1176/bin/python` in the
parent workspace. This is a local qualified configuration, not a new global
dependency pin or evidence of solver performance equivalence.

Physical code/protocol/tests were frozen at `8e9c7df` before the first run;
reuse code/protocol/tests were frozen at `9c57b45` before its first run.
The frozen results retain those execution identities. Both are based on main
`7e18463`. Production solver, enumeration, A2 and evidence-pipeline modules are
unchanged. Experiments are seed-free, local, single-threaded and process-capped.
No cluster jobs, protected outcomes or frozen pilot parameters were involved.

## Continuous physical controls

The adapter completely enumerates trip-chain/arc structures but retains
continuous charging within each. Its separate replay reconstructs energy and
SOC, checks trip coverage, charging windows, individual power, shared power,
intrinsic costs and aggregate load. It retains solved tangent-model lower bounds
and replayed true-quadratic evaluations, with a declared numerical allowance.
Unresolved statuses fail; only proved numerical infeasibility excludes a structure.
Bounds remain conditional on numerical solver/replay tolerances, not exact
rational or interval-arithmetic proofs.

| Fixture | Analytic physical D | Analytic CH | Feasible / enumerated structures |
|---|---:|---:|---:|
| Linear supply, two trips | 8 | 8 | 2 / 3 |
| Convex supply, two trips | 13 | 12.2 | 2 / 3 |
| Same, forced one bus | 13 | 13 | 1 / 2 |
| Shared charging caps 4/4 | 14 | 14 | 1 / 3 |
| Fully replenished terminal marker | .5 | .5 | 1 / 2 |
| Replenishment with caps .4/.4 | Infeasible | Infeasible | 0 / 2 |
| Two simultaneous bus chains, uncapped | 36 | 36 | 2 / 8 |
| Same, shared charging caps 8/12 | 36.8 | 36.8 | 2 / 8 |

Every analytical target lies within its reported numerical enclosure. The
positive-gap interval is **[0.7999957634, 0.8000103401]**, enclosing 4/5. The
single run completed in 0.442 seconds including its worker imports; this is a
small correctness exercise, not a timing benchmark.

In the positive-gap case, one bus must buy 10 kWh in two hourly windows. With
operating cost 7, a=.1 and b=.2, its balanced physical cost is 13; two initially
full buses cost 14 and buy no energy. A convex combination with one-bus weight
lambda has cost `14 - 6 lambda + 5 lambda²`, minimized at lambda=.6 and 12.2.
The stored numerical witness is approximately .600586, not exactly .6. The
result depends on the declared depleted-terminal policy: additional buses bring
additional starting stored energy. It does not establish cyclic-fleet economics.

The replenishment control explicitly inserts a zero-energy terminal marker
after the final real trip. This creates a final charging window in the
inter-trip formulation and restores initial SOC. It is a modeling device, not
an ordinary passenger trip or a native production overnight-charging feature.

Shared-power caps are imposed **inside each entire scaled fleet structure**.
An aggregate-only cap would convexify infeasible schedules and incorrectly keep
CH 12.2 in the caps 4/4 case, giving a spurious 1.8 gap against a weaker relaxation.
Correctly restricting structures first gives D=CH 14. In the active two-bus case,
the cap moves aggregate energy 10/10 to 8/12 and cost 36 to 36.8.

All events align with full hourly slots. Slot energy therefore admits a constant
power realization. This is shared depot power, not finite plug count; partially
overlapping windows need an event-grid formulation. Production A2 has no such
shared-capacity extension and was not compared on the capped fixtures.

## Fresh-state reuse comparison

The compatible original-physics fixture has one bus, two trips, two charging
windows and a 10 kWh minimum purchase. Four tariff states are baseline, an
unchanged control, positive tilt, and negative tilt. Their exact optimal
charging loads are 5/5, 5/5, 4/6, 6/4; costs are 18, 18, 17.8, 17.8.

Each arm pays for its own initial cold solve. Reuse imports only its own
immediately preceding physical column pool. Every column is replayed; bounds,
duals, tangents and retry state restart. The shifted-price arm makes exactly
one proposal per transition at `q_previous + delta_a`, then uses the same clean
master/full-pricing certificate as the other arms. Proposal bounds never enter
the certified lower bound. Every proposal, including duplicates, is charged.

| Arm | Initial-state calls | Calls at each of three transitions | Total calls | Observed complete subprocess time |
|---|---:|---:|---:|---:|
| Cold | 3 | 3 / 3 / 3 | 12 | 1.115s |
| Retained columns | 3 | 1 / 1 / 1 | 6 | .951s |
| Retained + analytic proposal | 3 | 2 / 2 / 2 | 9 | 1.015s |

All 12 cells certified within epsilon .01; the largest observed interval width
is below .0004 and all enclose the independently derived optimum. The total run
took 3.088 seconds. Tiny fixed-order subprocess times are descriptive only;
startup/noise and this single fixture preclude a general speedup claim.

Two retained endpoint schedules span the relevant minimum-energy charging
segment under these positive tariffs. They already suffice for all new optima,
so every transition needs only one clean verification call. The shifted proposal
has no useful missing column to find. One proposal is recorded as novel by the
production full-precision key, but its load differs from a retained endpoint
by only about 7.1e-15 kWh. This is a numerical near duplicate, not meaningful
physical discovery; original keys and evidence remain unmodified.

The optimal charging-slot marginal prices stay 1.3 as loads shift. The residual
after the analytic price translation cancels the tariff change on this fixture.
Accurate price prediction would still not remove the required verification
call. This is an informative control for the adapter, not an ML evaluation set.

## Independent verification and next gate

Nineteen physical regression checks include all analytical controls and corrupted
replay/status cases. Fifteen reuse checks reject cross-arm/future-state imports
and corrupted columns, and demonstrate that stale or proposal bounds do not
leak into the new certificate. Hosted full-suite verification is recorded with
the PR's exact head after packaging.

The independent physical auditor imported no adapter code and used no solver.
It checked all 31 structures, 169 resolved solver calls, raw-event trajectories
and objective arithmetic, and normalized all 19 positive-weight components.
All passed; maximum observed SOC shortfall was approximately 1.78e-15 kWh.
Seven corrupted output controls were rejected. Independent reuse review and
reconstruction accompany the saved artifacts.

Next, freeze a small workload with competing fleet structures and additional
charging opportunities, then determine whether old pools actually miss useful
columns. This should precede a learned residual or larger PR53 campaign.
Operational ingestion also needs complete source schema, trip-energy units,
time-dependent deadhead handling and boundary-energy policy. A public dataset
has been pinned separately, but no operational source data were optimized or
redistributed in this qualification.

## Reproduction

From this checkout, using the qualified interpreter and fresh output paths:

```sh
python -B src/experiments/physical_qualification.py --output NEW_PHYSICAL_DIRECTORY
python -B src/experiments/reuse_qualification.py --output NEW_REUSE_DIRECTORY
python -m pytest src/tests/test_physical_qualification.py src/tests/test_reuse_qualification.py -q
```

The fixed source/protocol/output digests and independent checkers accompany
`result/physical_qualification/20260921-attempt1` and
`result/reuse_qualification/20260921-attempt1`. Fresh runs have different time
and execution-commit metadata; scientific agreement, not whole-file identity,
is the relevant reproduction comparison.
