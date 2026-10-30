# Independent Gurobi replication audit

27 September 2026. Execution freeze:
`24c7e4ef30777700e4ea17ddfaacae2de92155ce`.
Complete original evidence manifest SHA-256:
`5227bfa17bc1d8721e62990bbe53480c5315ed334be51c913ac10aa2a9905030`.

**PASS for the frozen fifteen-case Gurobi replication.** Twelve controls produced
accepted certificates and three produced the expected infeasibility. The audit
independently reconstructs the raw variables, constraints, numerical conversions,
physical witnesses, global fixture objectives and bound intervals. The first CBC
attempt remains separate FAILED evidence (12/15 controls passing); neither later
successful run changes that history.

The auditor executed against the **complete external archive of all 107 original
files**, including original stdout. It did not merely check a partial public
copy. The full archive and original manifest were unchanged after the audit.
The public artifact intentionally omits stdout containing license infrastructure
identifiers; its access note/public manifest must identify omissions and original
hashes. This review does not repeat those identifiers. Full original-manifest
verification requires the complete archive; public-file verification is a
different, narrower operation.

## Results and backend identity

| Check | Result |
|---|---:|
| Complete original files verified | 107 |
| Declared/attempted controls | 15 / 15 |
| Accepted certificates / expected infeasibilities | 12 / 3 |
| Native starts and returned statuses | 30 / 30 |
| Raw statuses | 27 OPTIMAL; 3 INFEASIBLE |
| Raw incumbent snapshots / variable values | 27 / 1,030 |
| Finite native objectives independently minimized | 27 |
| Physical witness instances / charging sessions | 27 / 62 |
| SOC events, excluding initial states | 217 |
| Negative native values corrected | 0 |
| Nonzero correction-budget incumbents | 1 |
| Deliberately corrupted copies rejected | 18 |

Every runtime receipt identifies requested/model backend GRB, implementation
`SolverGurobi` in `mip.gurobi`. Recorded versions are Python-MIP 1.17.6 and
gurobipy 12.0.3. The reported interface-binary fingerprint is consistently
`57f87a886aa5a1fd8356494fa1b81e9f9c7d957c898d09e96145440c76c762b7`.
This is the receipt's fingerprint of its reported native interface file; it is
not presented as an independent hash of every Gurobi kernel/library dependency.
The frozen native wrapper rejects a backend name/module mismatch. The audit
also rejects deliberately substituted CBC module/class receipts, rather than
assuming the CBC auditor can be reused unchanged.

All four native runtime/protocol source hashes match the successful CBC V2
qualification. The complete fifteen input/objective/target definitions also
match exactly, with canonical JSON SHA-256
`064ce4f4879de27a62da17b770ec63fcb280fa8a40b4b4e4a6a199fb7dfbb1ca`.
Execution is pinned to the separate cluster commit above. Backend selection is
the declared change; native phase/thread/budget limits and numerical policy are
otherwise unchanged.

Controller elapsed time is 26.03973172599217 seconds; recorded native calls sum
to 0.18261995184002444 seconds. Process startup, library initialization, replay and
other overhead are outside that native-only time. All calls returned, with no
hard timeout or retry. These small qualification receipts on different local
and cluster environments do not support a backend speed comparison or scaling
claim.

## Independent numerical and physical checks

The original manifest, all files, frozen Git objects and full input definitions
are checked before auditing results. Raw lambda or hull machinery is not involved
here: these are native physical pricing/planning controls. Every raw variable
is finite and mapped exactly once. The auditor reconstructs every declared
constraint class: bounds/integrality, coverage and path flow, used-vehicle
ordering, charge ownership, interval resources, SOC/service/movement big-M
relations, terminal replenishment, period loads and saved tangent epigraphs.
It recomputes actual native objectives from those raw values.

The largest positive raw constraint residual, evaluated in exact binary-rational
arithmetic, is `2.032058731808655e-14`, below the prospective native tolerance
`1e-8`. This maximum spans different model units and must not be described as
battery kWh. The raw tableau/internal solver matrix itself is not independently
exported or verified; the check reconstructs the declared model from input and
mapped incumbent values.

There are no negative-to-zero charge corrections in this run. One incumbent,
`joint_planner` round 0, has nonzero materialized-session capacity excess:
`7.105427357601002e-15` kWh (`1/140737488355328` exactly). This is also the maximum
combined correction, far below the one `1e-8`-kWh whole-incumbent budget. Maximum
interval aggregate excess is `1.7763568394002505e-15` kWh. All positive raw charge
values are retained. The exact energy-proportional endpoints, actual sessions,
per-period changes and linear/PWL/true-cost correction effects reconstruct from
raw variables; exact and decimal ledger fields agree.

The separate physical replay uses the stored floating timestamps/energies without
snapping, clipping, deleting positive sessions or rationalizing their SOC traces.
It checks path coverage, ownership, windows, service/travel exclusion, strict
pairwise single-connector nonoverlap, resource intersections, grid loads,
intrinsic cost, every SOC event and full replenishment. Maximum SOC-bound
residual is `1.9539925233402755e-14` kWh; maximum reconstructed instantaneous power
is `30.000000000000014` kW. The frozen physical tolerances still apply. Sixty-two
sessions versus CBC V2's sixty reflects different valid native witnesses; the
controls and feasible-set definitions are identical.

All 27 finite pricing or saved PWL objective minima are reconstructed without an
optimizer using complete scalar projections of these fixtures. For cyclic
cases, one- and two-bus branches have load `(0,x,0,30/eta-x)`, with exact early
intervals determined by reserve, capacity and early/terminal connector limits.
Linear endpoints, true-quadratic stationary points and every relevant saved
PWL intersection give complete global minima. The other controls reduce to
fixed service/travel energy or available partial-window capacity. The three
infeasibilities are therefore established analytically, not only by a solver
status. All saved native objective/lower-bound pairs agree with these independent
minima within `1e-6`.

The 12 certificate widths range from `1.9999999949504854e-6` to
`2.00000000916134e-6` objective units. Every interval encloses the independent
exact binary-rational physical optimum. The targets remain 22, 433/19, 37, 134,
153.5, 97, 97, 733/19, 38527/361, 99, 24 and 36 for the twelve feasible controls; the
three capacity/reserve negative controls remain infeasible. Displayed fractions
use intended decimal parameters; exact stored-binary values agree within
`1e-10`. The two-sided guard dominates the reported interval widths and is not
a general exactness claim for numerical solvers.

This establishes replication of these small synthetic model/implementation
checks across the declared CBC and GRB environments. It does not establish
complete operational input graphs, realistic economic calibration, arbitrary
native-oracle certification or larger-instance performance. No FEASIBLE native
status occurred, so that admission path remains supported here by earlier fake
preflight controls rather than this cluster run.

## Corruption controls and reproducibility

Eighteen corrupted in-memory copies are rejected. They cover raw SOC,
assignment/integrality, missing snapshot, numeric representation, duplicate
mapping, compiled capacity, false negative-correction totals/entries,
materialized excess, endpoint spill, deleted positive session, objective
correction, saved SOC, native lower bound, final interval, tangent history,
backend module fallback and wrong implementation class. No original file is
changed to perform these controls.

The portable package contains `audit_native_grb557318.py` and
`independent_fixture_core.py`. The latter reuses the independently written
fixture mathematics, with GRB-specific receipt checks; neither file imports
the author's research implementation or any optimizer.

From the research worktree, with access to the complete archive:

```sh
python3 -B result/native_recharge/20260927-grb-job557318-attempt1/review/audit_native_grb557318.py \
  --attempt /path/to/full-107-file-archive \
  --repository .
```

A copied package can use any repository containing the frozen Git commit.
Only Python's standard library and Git are required. The explicit external
`--attempt` form was exercised successfully for this audit. Pointing it at an
incomplete public copy correctly fails; the script never silently skips omitted
stdout and labels that a full audit. Output is a new exclusive temporary file
by default; explicit `--out` must be new and outside Git repositories. The
archived audit output was copied into this derived review folder separately.
A separate review manifest hashes both audit files, this prose and audit output.
