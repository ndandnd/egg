# Review: prospective path-flow orphan-charge repair

27 September 2026. **Conditional PASS to proceed with the pure extraction
helper and no-optimizer tests.** The proposed projection is a conservative
post-solve interpretation of a tiny, unowned positive charge; it does not
change the physical graph, solver rows, or shared indexed extractor. This is a
design review only. I did not modify code or run an optimizer.

The accounting is dimensionally consistent in grid kWh and uses the same
stored-float rationalization as the shared `1e-8 kWh` budget. `N+O` counts all
negative-to-zero and positive-orphan-to-zero changes. The raw-row residual
`|L-R|`, projected-to-plan residual `|H-P|`, interval and session capacity
excesses `I+J`, and replay-load residual are then accumulated against that same
single ceiling. Counting both capacity stages is conservative. The plan also
retains independent existing `1e-6 kWh` replay checks; they are not a substitute
for or an enlargement of the new exact budget. The shared indexed normalizer
must remain unchanged.

One implementation detail is essential for sound objective reconstruction.
In the present path-flow code, `raw_solver_load` is the saved native load row
`L`, while `raw_charge_load` is the sum `R` of raw charge variables. Current
linear and PWL correction diagnostics use `H-R` (see
`src/egglab/native_pathflow.py`, `_extract`, `solve_pricing` and `solve_planner`).
The new policy must separately retain and account for `L-R`, and compute the
objective change from `L` to the replayed plan load `H`, as the design states;
using only `H-R` would omit a native load-row residual. Reconstruct the saved
linear/tangent objective on `L`, calculate the feasible upper from the fully
replayed `H`, preserve the native global lower bound with the unchanged
`BOUND_GUARD`, and reject a candidate if existing objective-admission checks
(`OBJECTIVE_TOL` / bound ordering) fail. Do not convert the raw incumbent into
a physical upper bound or improve the solver lower bound from projection.

The policy identity must invalidate old compact-hull state: version the
path-flow extraction/formulation and compact-hull oracle identity together,
including raw-incumbent tags, plan/result metadata and qualification freeze.
Keep the shared negative-normalizer identity separately visible, and disclose
that the native constraint matrix and energy-band policy remain V2. Preserve
every raw value and its `repr` before projection, including when a subsequent
budget, decode, objective or replay check rejects the candidate.

The proposed pure tests cover the material failure modes: cumulative rather
than per-variable overflow, negative plus orphan correction in one budget,
capacity/load/replay residual accumulation, preservation of every positive
selected charge, malformed or unknown inputs, terminal-SOC replay failure,
objective deltas, and unchanged shared-policy rejection. Include the exact
budget boundary and a case with a nonzero `L-R` residual so the two load ledgers
cannot accidentally collapse to one. The frozen 19/20 attempt and its raw
artifacts remain failed and untouched; only a new immutable 20-control attempt
after independent preflight can qualify the prospective policy.
