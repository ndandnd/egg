# First computational screen: implementation handoff

The prospective source is `src/experiments/computational_benchmark.py`, with
the separate declared protocol at `doc/COMPUTATIONAL_SCREEN_PROTOCOL_20260928.md`.
This is one development screen, not an ML evaluation or a new physics model.
No optimizer has been run during implementation.

The frozen design has two qualified synthetic base timetables (two-service
cyclic and three-service multivisit) and two single-depot variants of the same
37-service Hildenbrand base timetable. Each receives two deterministic market
states. The cyclic pair retains its high-curvature counterexample coefficients;
multivisit and public cases use the explicitly declared uniform and structured
time-of-use intercepts. All exact stored float vectors and serialized physical
cases are in `frozen.json`. There is no RNG or train/test split.

For each of eight case-state groups, the runner attempts physical planning,
cold full-fleet hull certification, retained full-fleet hull certification and
the named planner incumbent's own-price response. State zero charges each hull
arm for its own fresh initialization. State-one retained import requires its
same-arm, same-case state-zero predecessor to have an on-time, complete,
certified result; the native import then checks policy and state identity.
Missing predecessor or planner evidence makes the dependent stage ineligible.
The other stages continue. These hull columns are complete fleet plans, not
per-duty route columns. A later learned route proposer would need complete
fleet assembly and physical repair before fresh global pricing could certify it.

Every stage is a child process with a native wall target and a hard target 30 s
later. The controller execution cap is 5,400 s; the outer supervisor hard cap
is 5,500 s from supervisor precheck through reconciliation and sealing, within one 2-hour
Slurm allocation requesting one CPU/8 GB, no requeue and the reserved-node
exclusion. Environment setup and exclusive freeze precede this supervisor cap;
the sibling wrapper receipt records the supervisor invocation elapsed time,
outside the sealed attempt manifest. Full job elapsed time, including setup and
freeze, is collected separately with scoped Slurm accounting. Worker stdout/stderr,
including any license diagnostics, remain
private in full raw archives; a later public copy needs a separate omission
manifest. A hard timeout or child failure retains partial files and a receipt.
The controller process group includes its current worker, so total-cap
termination kills the tree before manifest sealing. A partial controller run
gets a 32-row postmortem accounting of receipted, interrupted and unstarted
stages; truncated result files remain intact and cannot seed dependent stages.
If process-group quiescence cannot be confirmed, the receipt records that
failure and no stable manifest is claimed. One attempt path and
create-exclusive writes preclude implicit retries.

The hull uses the unchanged exact pairwise polisher with 20 s cumulative soft
algorithm stop target, 64 steps and 4,096-bit limit. A non-preemptible final
step may cross the soft target; actual elapsed and excess remain visible. This
does not retroactively turn the prior strict 5 s pilot failure into a pass.
`budget_exhausted` can carry a valid global lower certificate and feasible
mixture upper value; an open restricted/global residual is never relabeled
certified. Repeated exact polishing may still be the bottleneck. A future,
separately reviewed restricted-QP proposal could use numerical restricted
optimization followed by exact simplex/true-cost/residual replay and fresh
global pricing; this screen does not implement that change.

Raw event streams, complete solver results, case/market features, movement
masks, fleet plans, charging/SOC/load, prices, bounds, stage receipts and
source/runtime identities are saved for descriptive iteration analysis. The
summary is author-side and does not replace an independent result audit.
Compare eligible cold/retained transitions only at matched case, market and
quality, counting both states' full calls and time. No scalability, learning
efficacy, protocol speedup or exact ideal-model claim follows from this screen.
