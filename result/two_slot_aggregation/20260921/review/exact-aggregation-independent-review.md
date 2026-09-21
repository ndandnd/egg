# Independent review: exact two-slot aggregation experiment

Reviewed 21 September 2026. **PASS, no blocking finding in the reviewed experiment.** This is an independent mathematical and artifact check of the finite menu experiment, not validation of operational fleet performance. No protected outcomes, previous experiment data, cluster access, training, or solver were used. The author's worktree was not modified.

## Scope and reproducibility

The reviewed source and protocol are [two_slot_aggregation.py](../../../../src/experiments/two_slot_aggregation.py) and [protocol](../../../../doc/TWO_SLOT_AGGREGATION_PROTOCOL_20260921.md), committed together at **`7e139b32f8ae762482e33b688f75092e1a2afdf2`**. Their working bytes match that commit exactly. The [output](../../../../result/two_slot_aggregation/20260921/exact_results.json) records the same commit, Python 3.9.6, and Fraction arithmetic. Its SHA-256 is **`540525dbba02d507b407cf69e823a0286237b6e6e2e9349372145a5343747960`**. Source SHA-256: `e092be9f5a3b91fa072f8f6c226cfa50cda9fa7cf39fbf244315b698a2e61270`; protocol: `fc8d36765f7cbeb650f36bf853de94a34188fcb8fa1aa96e379d9f276cb40814`.

The independent [reproducer](check_exact_aggregation_independent.py) imports no author functions. It enumerates profiles by bit masks, retains the cheapest intrinsic cost at each early load, and minimizes the objective on **every pairwise segment**, rather than constructing the author's lower hull. This is exact: every tested segment lies in the convex hull, and its lower boundary consists of segments among those points. Because intrinsic cost enters with coefficient +1, a convex optimum occurs on that lower boundary. An independent supporting-line inequality calculation also verifies reported hull vertex counts.

Run command:

```sh
/Users/nadan/Documents/ChatGPT/egg/.research-venv/bin/python -B \
  check_exact_aggregation_independent.py \
  ../../../../result/two_slot_aggregation/20260921/exact_results.json
```

The check completed successfully under Python 3.12.2; the [recorded check summary](exact-aggregation-independent-check.json) preserves its output.

| Evidence checked | Result |
|---|---|
| Parameter grid and unique names | 36 homogeneous + 54 heterogeneous, exact match |
| Separate shared-capacity witness | 1, exact match |
| Exhaustive physical profiles | 30,621 |
| Candidate convexification segments | 3,715 |
| Every saved objective, load, choice, regret, LOC, support flag, count and rational relative gap | Exact agreement |
| All-profile regret inequalities and all optimal-profile support when gap is zero | Pass |
| Independent pairwise owner regrouping, without capacity coupling | Pass |
| Gap distribution in the 90-case grid | 55 positive, 35 zero |
| Nonzero settlement terms | 7 positive fleet LOC; 55 positive supplier LOC |
| Deliberately corrupted objective/gap/regret/LOC output fields | All six rejected |

The author's self-checks are useful, but share code paths for hull values and convexification. The independent calculation addresses that dependency. Nonzero gaps, nonzero fleet LOC, nonzero supplier LOC, and both support outcomes make these checks substantive, rather than identities tested only at zero. The six negative controls test rejection of incorrect artifacts; they are not a mutation-testing claim about every production assertion.

## Closed forms and interpretation

For homogeneous positive block size `e`, curvature `b`, zero intrinsic costs and zero linear offsets, `zCH = b N² e² / 4`. Even N admits exact balance: gap and both minimum regret measures are zero. For odd N:

- `gap = b e² / 4` and `gap/zCH = 1/N²`.
- Minimum joint own-price regret is `b e² (N+1)/2`.
- Minimum maximum individual own-price regret is `b e²`.
- At the convex supporting price, fleet LOC is zero and supplier LOC equals the gap.

All 36 cases agree with these independently derived formulas. The resulting distinctions matter:

| Regime, odd N | Absolute gap | Minimum maximum individual regret | Minimum joint regret |
|---|---|---|---|
| Fixed blocks and supply slope: e=1, b=1 | 1/4 | 1 | (N+1)/2 |
| Unit blocks, flattened supply: e=1, b=1/N | 1/(4N) | 1/N | (N+1)/(2N) |
| Fixed total energy: e=1/N, b=1 | 1/(4N²) | 1/N² | (N+1)/(2N²) |

Thus decreasing relative planner gap alone does not establish vanishing absolute gap, joint regret, or individual regret. The fixed-block example directly disproves that inference. Declining odd-N subsequences also must not be described as monotone sequences across even and odd N.

Economic ownership regrouping preserves joint support and total regret only when each new owner retains the full Cartesian product of its constituent menus. It does not establish invariance of the maximum per-owner regret. Shrinking an indivisible block changes physical feasibility; merely changing its owner's name does not. The heterogeneous grid is deterministic illustration, not 90 independent population draws or evidence that the observed positive-gap frequency generalizes.

Own-gradient regret and LOC at the convex supporting price are different quantities. The verified bound is `r(s) >= h(s)-zCH >= gap`; a positive regret alone cannot certify a positive gap. The settlement identity instead evaluates the chosen physical optimum at the common convex supporting price and includes supplier LOC.

## Shared capacity and limits

The witness correctly gives `zd=zCH=3`, physical/convex load `(1,1)`, and energy price `(1,3)`. The late participant's unrestricted gain from moving early is 2, but that deviation violates the shared early capacity. Residual-capacity regrets are both zero. Adding early capacity price 2 produces all-in participant prices `(3,3)` and zero unrestricted regrets, with capacity rent 2.

Consequently, zero **joint-feasible** gap does not imply independent support under unrestricted menu deviations when a shared resource is unpriced. The witness's zero `fleet_loc_at_ch_price` is the LOC of the jointly constrained feasible set; it is not the sum of unrestricted participant LOCs, which is 2 at the energy-only price. The capacity rent requires separate resource-owner settlement accounting; this experiment does not demonstrate a complete budget-balanced mechanism. Supplier LOC uses the energy price, not the participant price including scarcity charges.

Remaining limits are appropriately bounded. Two fixed slots, fixed total energy per profile, and binary menus omit routing, charging trajectories, networks and endogenous fleet demand. The recorded 6.78 seconds is one execution's elapsed time, not optimization acceleration evidence. The output's `code_commit` field alone does not attest a clean source tree at execution time; exact source matching now and independent reproduction support this artifact, but are not cryptographic run attestation. None of these limits blocks use as a reviewed explanatory experiment. The useful next empirical question is which menu granularity and supply scaling represent a declared operational setting, before transferring any aggregation conclusion to fleet data.

## Addendum: plotting and focused tests

Reviewed the newly added [plotter](../../../../src/experiments/plot_two_slot_aggregation.py) and [focused tests](../../../../src/tests/test_two_slot_aggregation.py), initially uncommitted. The test-file SHA-256 was `55721d85c0604e5f51a754b5c915e0e85cf8f76e8b97a96424f6e86acb309faf`. Independent execution with Python 3.12.2, bytecode disabled and pytest's cache provider disabled passed **3 tests in 0.10 seconds**. These exercise 24 homogeneous closed-form cases, a nonzero menu-cost interior optimum (`xCH=1/8`, `zCH=31/64`), and the capacity deviation-set witness. They compare production functions against independently derived expected values, rather than merely asserting that execution succeeds. No repeat of the completed 90-case mathematical enumeration was needed.

The plotter accurately selects the odd-N homogeneous cases, converts exact fractions only for display, distinguishes absolute gap from minimum maximum individual regret, and draws the common relative-gap curve once. The [rendered PNG](../../../../result/two_slot_aggregation/20260921/scaling.png) is legible with correct curves, scales, legends and regime labels. It makes no computational-speed claim. Initial plotter SHA-256: `51769a923a47a2db4092846cbd52beec1b8493e1de48e532351f8fffc5ec3ede`.

One minor presentation finding was reported and **resolved**: the footer now says “All even-N homogeneous cases have zero gap and regret,” preventing accidental application to the separate heterogeneous grid. The corrected source and regenerated PNG were inspected. Corrected plotter SHA-256: `5d86d22885183ad47b56acff9131f0ed8b6e7c1c3a0ba394b0ed90c96a0eaf73`. No plotting or test findings remain open.

The subsequently added [results note](../../../../doc/TWO_SLOT_AGGREGATION_RESULTS_20260921.md), SHA-256 `1995586cbc651d30e6d601dbb7f021b29eae3b70f95813051a75da06028296d6`, also passes this interpretation review. Its formulas and case counts agree with the independent check. It explicitly distinguishes fixed posted-price deviations from recomputing prices, relative from absolute regret measures, full-product ownership regrouping from changes in indivisibility, and joint-feasible LOC from independent unrestricted LOC. The capacity accounting is correct: consumer payments 6 split into supplier revenue 4 and resource rent 2; supplier cost is 3 and profit is 1. The note correctly warns that the supporting scarcity price does not ensure feasible arbitrary tie breaking. Its limitations on sampled-menu conclusions and operational transfer are appropriate. The claimed second non-author review was corroborated against the [economic review](aggregation-economic-review.md). This addendum checks the results note's interpretation against the experiment; the separate literature memo owns the literature review. **Final addendum verdict: PASS, no blocking or outstanding findings in these additions.**
