# Exact flat-price matching relaxation: prospective protocol

27 September 2026. Candidate protocol pending independent preflight and a
published source freeze. No matching calculation on either public case has
been performed at this checkpoint. This is a new analysis motivated by the
wide bounds in public pricing attempt1, not a prespecified analysis of that
earlier attempt and not a replacement of its archived result.

## Question and model

Can an independently checkable combinatorial relaxation improve our knowledge
of the minimum flat-price full-recharge cost, without another native MIP solve?
Use both complete37-service variants of the pinned Sistig public payload,
SHA256 `af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6`,
in depot15 then depot16 order. Keep every service and declared movement mode,
the pinned EGG-modeled energy inputs, efficiency1, synthetic used-bus cost100,
deadhead cost0 and the exact stored binary float0.2 as the flat grid price.
The charge rate, battery size and terminal deadline remain part of input
identity, but their feasibility restrictions are explicitly relaxed here.

Interpret every individually stored input energy, time, price and efficiency
as an exact rational number. Full replenishment implies that total grid energy
equals total service and selected movement energy divided by efficiency.
This is exact for the intended physical equations. It is not an assertion
that the rounded native big-M matrix has exactly the same feasible set, and
the matching bound will not silently replace a saved native lower endpoint.

Let w(m) be deadhead-rate times exact sum of leg durations plus price/efficiency
times exact sum of leg energies. Let o(i),h(i) be cheapest declared pullout and
pullin costs for service i (lexicographic movement ID breaks cost ties).
Require at least one declared endpoint mode of each kind per trip; otherwise
reject this reduction rather than fabricate an arc. Starting with each trip
alone gives baseline

`price/efficiency * sum(service_energy) + sum_i(f + o(i) + h(i))`.

A connection i→j changes this baseline by
`min_connection w(i,j) - h(i) - o(j) - f`.
The timing-validated service graph is acyclic. At most one selected successor
and predecessor therefore gives disjoint paths, with no circulation. Relax
SOC, charging availability, shared resource constraints and the maximum fleet
count. Every ideal physical solution maps to this relaxation; the converse is
not required. The relaxed number of paths need not be physically feasible.

## Exact certificate

Build37 assignment rows and74 columns:37 real successor services and37 free
dummy unmatched columns. Absent connections stay absent. Choose one distinct
column per row. A Hungarian augmentation implementation uses an exact common
integer scale for all rational coefficients, with deterministic index ties.
Its correctness is not assumed solely from the algorithm name: every output
must pass an exact primal/dual certificate.

For all allowed row/column pairs, check `u_i + v_j <= a_ij`, with `v_j <= 0`.
Check one allowed edge per row, distinct assigned columns, and equality of
primal assignment cost with `sum(u)+sum(v)`. This proves the exact assignment
minimum by weak duality, including unmatched columns. Adding the baseline
gives an exact lower bound for the ideal full-recharge physical problem.
Reconstruct selected movement IDs and bus-path cost separately and require
exact equality. Store fractions without decimal rounding.

Qualification uses exhaustive independent permutation minima on all4096
sparse signed2×3 matrices, larger small matrices, corruption controls and
synthetic service-path/efficiency/parallel-mode examples. These tests are
algorithm qualification, not public-case experimental results. A non-author
must review the reduction and implementation before public execution, and
independently reconstruct both public certificates afterward without importing
the author implementation or invoking an optimizer.

## Freeze, execution and accounting

Publish all runner dependencies, this protocol and the independent preflight.
The freeze command requires each dependency to match its committed Git blob,
records the source commit and hashes, and writes a new exclusive attempt
directory `result/sistig_matching/20260927-attempt1`. Input identities, exact
flat price and two case order are fixed. Execution refuses changed sources,
changed frozen inputs or an existing STARTED sentinel. Exactly two algorithm
calls are planned; no tuning, alternate reductions or retries within attempt1.
An integrity or algorithm exception retains all existing files and blocks any
not-yet-run cells. A revision requires a separate named attempt and source
freeze, with the failure preserved.

Run locally with one process,30seconds complete routine cap and45seconds hard
subprocess cap, preserving stdout/stderr and a supervisor receipt. No cluster
resources, Gurobi, CBC, random seeds, charging optimization or private data are
used. Manifest all original output files after the subprocess ends. Do not
modify raw files during the independent result audit.

Use the runner's `freeze` mode first, followed by `supervise`, never a bare
experimental `run`. The exclusive supervisor launch record prevents relaunch.
It launches exactly one child with a45-second timeout, kills and waits on
timeout, records process exit and elapsed time, and manifests the completed or
failed raw archive. Runtime Python/platform identity is checked against freeze.

## Interpretation

Report both exact lower bounds, relaxation path counts and audited assignment
certificates. Compare descriptively with the first native pilot, keeping
ideal stored-input lower bounds separate from numerical native bounds and
tolerance-conditional physical witnesses. A tight numerical comparison is not
automatically an exact ideal physical optimum: any such conclusion requires
an exact physical feasibility/objective witness or a separately justified
roundoff enclosure. Do not infer physically feasible matching paths, nonlinear
planning/convexification gaps, own-price regret or operational benefit from
this relaxation. It is a lower-bound diagnostic under synthetic flat prices.
