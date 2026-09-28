# Prospective retrieval comparison runner

`src/experiments/retrieval_comparison.py` implements the frozen development
design in `doc/RETRIEVAL_COMPARISON_PROTOCOL_20260928.md`. Import, `design`, and
the pure tests allocate no optimizer model. Do not run an optimizer during
source review. The published execution commit and single attempt are pinned
by `freeze` and checked again by the Slurm wrapper.

The six cases are five prespecified generated development cases, pinned by
`SYNTHETIC_PREFLIGHT.json`, and the single admitted Eberbach/depot36 public
payload. The generator preflight records replayed charging pressure and its
service-energy lower bound. The runner reconstructs the cases and checks all
physical IDs and 30 hourly periods before a child begins. Hildenbrand is not
run. All fixed a/b market choices, budgets, case order, rotating target-arm
order, solver seed, runtime and source files enter `frozen.json`.

For each case, the controller pays for two source hull children once, then
writes a source pool. A source with an open or failed solve can contribute a
column only when its pricing request, native result, global-bound event,
complete-fleet witness, physical projection and admitted native bound all
match. A later unresolved pricing call does not erase an earlier admissible
fleet. The failed/late source status and unused calls remain recorded. The
pool preserves price-label ties for one physical projection. Retrieval picks
from this same pool by squared Euclidean distance to target a, or the exact
stored-number `ops+a·L` bill, with source/call/key ties. Squared Euclidean
distance has the same ordering as Euclidean distance.

The controller writes `pool_preparation_receipt.json` after source admission,
event/physical replay, candidate extraction and the `pool.json` write. This
measured work is paid once with the two source-child times. The deterministic
`pool.json` contains no timing field, so later workers can rebuild and compare
it against pinned source files.

The current hull interface accepts one predecessor. For each retrieved arm,
the runner constructs a `derived_feasible_pool_import` compatibility envelope
from the checked source candidates. It has a replayed feasible one-hot upper,
`bounded` status, original provenance nested inside each adapter-facing
column, and a lineage digest over physical ID, source file hashes, source
state IDs, every actual price label, selected keys and policy. The envelope
has no previous lower, gap or solver statistics. It is neither a source result
nor a certificate. It is passed to `feasible_pool` admission; target global
lower bounds require fresh pricing. Every target arm, including cold, uses
the same numerical QP master and 10-second pricing reserve, without a pricing
bound cache or native MIP start.

Each selected column is replayed as an executable individual fleet. Its
linear bill and nonlinear operating-plus-supply cost are reported separately.
The repair field says `identity/no repair: same physical case`; there is no
repair optimizer. Hull mixtures remain convex certificates, not individual
fleet schedules. The shared target physical planner and its own-marginal-price
response yield qualified D, CH, D-minus-CH and own-price regret intervals
where on-time returned bounds and plans exist; missing intervals remain null.
Late or failed raw assessments remain in their rows but cannot enter primary
comparison metrics. Retrieval workers save `proposal.json` immediately after
lookup and physical replay, before adapter construction and full target
verification. A later hard stop therefore preserves the direct proposal and
its measured lookup/replay time. `preparation.json` records subsequent adapter
and setup costs before the iterative target call.

Each of 48 declared children runs once. Core allowance totals 5160 seconds;
the 30-second per-child complete-process margin yields nominal 6600 seconds.
The parent records complete child elapsed time, including setup, checking and
extraction, and terminates an over-limit child with a bounded signal grace.
The supervisor kills the controller process group at 6900 seconds and has an
outer 7100-second limit for cleanup and sealing; Slurm ends at 7200 seconds.
Signal grace can make an individual timeout receipt exceed its nominal
allowance; the controller and outer caps still bound the attempt. An abnormal
controller exit produces a 48-row postmortem, then a manifest only after its
process group is quiescent. No retry or replacement is implemented.

`case_summary.json` reports each source's paid child time separately, online
target child time, a source-plus-target total, and illustrative amortization
of the once-paid source pool over 1, 2, 4 or 8 target reuses. Amortization is
an accounting scenario, not an observed speedup. Each worker event includes
elapsed wall time before JSON serialization for any supported time-to-quality
analysis. No common-quality speedup should be inferred from final times alone.

After publication of the final commit, the authorized execution sequence is
one `freeze`, one Slurm submission of `src/cluster/retrieval_comparison.sbatch`,
and independent review of sealed results. Source/results paths are fixed at
`result/retrieval_comparison/20260928-attempt1`. This note records the intended
sequence; it does not authorize an extra exploratory solve.
