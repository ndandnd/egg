# Independent reuse qualification review — 21 September 2026

**PASS for the stated engineering qualification. No blocking certificate or physical-feasibility defect found.** The reviewer did not author or edit the experiment driver, its protocol, tests or outcomes. Review and checks target frozen commit `9c57b459e2f10a967f5ffc9e2a09fc5255de4f79` and `result/reuse_qualification/20260921-attempt1`.

## Evidence checked

The 15 committed unit/adversarial tests passed independently in 0.15 seconds using the repaired interpreter. A separate standard-library-only [audit](independent-audit.py) then checked all 12 completed cells without importing the author runner or EGG functions and without launching a solver. Its [results](independent-audit.json) retain cell hashes and independently reconstructed counts.

For every state, the audit reconstructed each physical charge event's ownership, admissible slot, energy, slot power, battery feasibility, projected load and intrinsic cost. Each retained schedule serves exactly the two specified trips on one bus; the observed columns charge 10 kWh across the two admissible slots. It reconstructed all 27 pricing objectives and compared each certified lower bound against the exact continuous linear-pricing optimum on this fixture.

For all 18 clean certification iterations, it reconstructed the master mixture, exact quadratic upper bound, dual-price sign, reduced-cost lower/upper bounds, running best lower bound and final gap. It independently minimized each saved piecewise-linear master by enumerating intersections of its tangent lines over the retained load interval. Thus the audit did not simply recalculate the driver's final formula from an unchecked master optimum. The independent continuous physical/CH optima are 18, 18, 17.8, 17.8, and all reported intervals enclose them. The final interval widths are approximately 0.000398597, below the frozen 0.01 criterion.

All 93 optimizer-wrapper records have CBC/OPTIMAL/one-thread evidence. Each pricing wrapper includes an LP-first phase and a MILP phase; 93 is the number of recorded wrapper invocations, not a claim that there were only 93 low-level solver optimizations. Recorded native timings, full subprocess timings, oracle-purpose counts, source hashes, distribution versions and selected native-library hashes agree. Six deliberate mutations to saved lower/upper bounds, gap, clean-call count, intrinsic cost and proposal price were rejected by the independent audit.

## Code and prospective-protocol assessment

- Fresh tangents, duals, lower/upper history and solve records are initialized at each new state. The driver does not bypass production checkpoint identity checks.
- Only the same arm's immediately preceding certified state can supply columns. Replays check the physical evidence itself; a saved `replay_ok` flag is insufficient. The old pricing bound remains provenance inside a column but never feeds the new state's lower bound.
- `q_previous + a_new - a_previous` has the correct sign as a fixed-load price-shift heuristic with unchanged slopes and base load. It is not assumed to predict the new optimum.
- The proposal is charged as one full pricing call per transition, even when it returns a duplicate; its bound never contributes to certification. Every arm uses a fresh clean master and full clean pricing for the same certificate/tolerances.
- A 24-call state budget, 96-column cap, ten-second solve cap, 40-second process-group cap and 300-second overall admission limit bound execution. Frozen output roots are exclusive. The source reads hand-authored inputs and same-run predecessor files; no protected data or cluster work is involved.

The only preliminary evidence finding was missing package/native-library identity in run provenance. The author corrected it before freezing: the parent records package versions without loading CBC; workers record the library actually loaded after native solves, within the process watchdog.

## Observed result and important interpretation

| Arm, all four states | Seed calls | Clean calls | Proposal calls | Total pricing calls |
|---|---:|---:|---:|---:|
| Cold | 4 | 8 | 0 | 12 |
| Retained columns | 1 | 5 | 0 | 6 |
| Retained plus analytic shift | 1 | 5 | 3 | 9 |

After initialization, retained columns need one clean certification call per state. Adding the analytic proposal leaves that clean count unchanged and adds three calls. This fixture therefore contains no demonstrated remaining discovery work for learning to improve.

**Exact-key novelty must not be reported as meaningful physical discovery.** The state-2 proposal has `novel=true` because its full-precision load differs from an imported endpoint by only `7.105427357601002e-15` kWh. The other two proposals are exact duplicates. This is consistent with the production column-key contract and does not invalidate any bound, but it makes the raw novelty flag a poor measure of useful proposal diversity here. Preserve the frozen fields; any later report should show both exact-key novelty and a separate, clearly declared numerical proximity diagnostic. Do not silently round or rewrite these results.

This is one hand-authored fixture with a fixed convex continuous charging segment, a fixed state/arm order and noisy subsecond subprocess timings. It does not establish a general speedup, behavior under changing physical feasibility or shared capacity, a nonconvex planning gap, or a case for an ML campaign. A harder prospective reuse workload should demonstrate remaining discovery work after column retention before learning is tested.

## Portability-only packaging addendum

The checker now accepts explicit `--repo`, `--run` and `--report` arguments. `--run` may be absolute or relative to the specified checkout. It resolves each known arm/state file inside that run directory rather than following the original Mac absolute paths embedded in the summary. A report path is required, and existing reports are refused using exclusive creation. All mathematical checks and the expected frozen source commit/hashes remain unchanged. For example, from a fresh checkout:

```
python result/reuse_qualification/20260921-attempt1/review/independent-audit.py --repo . --run result/reuse_qualification/20260921-attempt1 --report /tmp/new-reuse-audit.json
```

Every saved cell must still contain the previously verified historical CBC hash. To additionally rehash the historical binary, pass `--cbc-library PATH_TO_LIBCBC_DYLIB`; the checker only reads those bytes and never loads them. Without this optional artifact, the report explicitly limits native-library verification to recorded hashes. The local portability rerun included the actual binary and passed all original checks; [independent-audit-portable.json](independent-audit-portable.json) preserves the new result while [independent-audit.json](independent-audit.json) remains unchanged.

A second solver-free check copied only the recorded source files and result JSON into a temporary fresh-checkout layout, placed the run outside that checkout, and successfully audited it without reading the old absolute result paths or requiring the historical Mac library. Every field in the original audit report matched both new runs. An overwrite attempt was rejected with the report bytes unchanged. See [portability-verification.json](portability-verification.json). No author source, frozen protocol, experiment result, or native experiment was changed or rerun.
