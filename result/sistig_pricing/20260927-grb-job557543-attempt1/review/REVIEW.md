# Independent audit: full public timetable flat-price pilot

27 September 2026. **PASS for the two saved conditional numerical pricing
intervals, complete physical witnesses, source/evidence integrity and execution
accounting.** Both outcomes remain `bounded` with native status `FEASIBLE`.
Neither interval certifies an optimum. No independent global optimization or
exact global lower-bound proof was performed.

The audited first attempt is Slurm job557543 at frozen source
`282e00b80b6fd9457006429b089269b2a9e2be92`. All37 services and every declared
movement mode are retained separately in the two single-depot adaptations.
These are synthetic price/cost scenarios on a public timetable, not the
publisher's two-depot optimization problem or an operational fleet plan.

| Single-depot scenario | Native status | Conditional lower | Replayed upper including guard | Width | Used buses | Grid kWh |
|---|---|---:|---:|---:|---:|---:|
|15|FEASIBLE|237.1414876407|408.5331368839|171.3916492432|2|1042.6656794194|
|16|FEASIBLE|232.1463316455|433.7460862172|201.5997545717|2|1168.7304260861|

The price is a synthetic constant0.2 per grid kWh, with100 per used bus and
zero deadhead-time cost. The upper endpoints add the frozen1e-6 guard to the
independently reconstructed physical objective; lower endpoints subtract it
from the native global bound. Two-bus feasible witnesses do not prove that two
buses are necessary, or that their charging/movement choices minimize cost.
All bound interpretations retain the qualified floating numerical assumptions.

## Independent evidence reconstruction

The audit imports only standard-library code and independent replay/matrix
helpers. It does not import the author model, adapter or a native optimizer.
The public cases were reconstructed field by field from the pinned derived JSON
and matched their exact full case identities, all37 service records, all30
flat prices and the complete directed mode graphs:666 direct modes in each
case,630/595 depot modes and37 pullouts/pullins each. The prior independent
source-archive/workbook/matrix review remains separate evidence; this result
audit does not claim to have repeated that entire source extraction.

All17 complete-local raw artifacts, totaling13,587,430 bytes, matched the raw
manifest before and after audit. Every saved dependency hash was checked
against the frozen Git commit, including the prerequisite twenty-control
compact gate, its independent review, public source payload and model sources.
The complete result trace in each cell contains exactly one ordered round-zero
pricing phase. Raw native statuses equal saved result statistics; all prices,
identities, phase counts, native time totals, child exits and scientific routine
receipts agree. No second pricing query, retry, warm start or hull/planner phase
appears in the scientific trace.

The independent auditor reconstructed both compact variable maps and every
physical row: movement activation, mandatory degree-one flow, fleet count,
service SOC, all big-M movement/depot/terminal equations, interval charging
capacity, battery bounds and market load sums. It derived selected paths from
the flat graph independently and checked the raw objective against the saved
incumbent. There are21,796/20,501 variables,42,297 total. The largest exact
binary-rational raw row residual is3.289812866569264e-12, below the fixed1e-8
raw audit tolerance.

Every selected service and movement leg, directed ownership, charging window,
shared connector, energy balance, SOC trajectory and terminal full recharge was
replayed independently. The two plans have19/22 sessions and114/117 SOC events:
41 sessions and231 events total. Peak charging is360kW. The maximum SOC residual
is6.991740519879386e-12kWh, below the unchanged1e-6 physical tolerance. Both
incumbents have zero negative-energy normalization, zero capacity correction
and zero objective-correction ledger. No positive session was dropped.

Sixteen independently corrupted evidence copies were rejected, covering foreign
or duplicate phases, missing raw variables, fractional coverage, SOC changes,
row counts, normalization/decoding ledgers, deleted sessions, altered physical
SOC, mismatched native statistics, invented lower endpoints, prices, incomplete
accounting, a late scientific routine and timeout after a result. Raw files were
never edited. Prior preparation tests also replayed all31 saved small compact
incumbents and independently reconstructed both public feasibility references.

The auditor did not author the compact path-flow model, public pilot runner or
public source adapter. The auditor authored earlier indexed native-model/hull
work. The physical replay core originated in another independently authored
review and was preserved verbatim; the compact row/path reconstruction is this
reviewer's separately implemented audit code. This is implementation-level
independent evidence, not independence from the entire research project.

## Constructive reference and limits

Exact rational arithmetic on the stored input energies reconstructed37 dedicated
service buses per case, with all pullouts/pullins and a sequential finite360kW
terminal connector. Both fully replenish by the1800-minute deadline. The
reference upper objectives are4117.975288199719 and4253.9628958838775, ending
at1490.5238145685698 and1501.1225345685698 minutes. Their energy totals are
2089.8764409985943 and2769.8144794193886kWh. The saved summaries agree.

These deliberately simple witnesses independently establish feasibility and
cross-check that neither native lower bound contradicts a known feasible
objective. The returned two-bus upper bounds are substantially tighter; that
comparison is not an operational savings estimate against a publisher schedule.
The report records `independent_global_optimum: null` for both cases. A valid
future LP strengthening must be a separate source version and attempt; it
cannot improve these archived first-run intervals retrospectively.

## Resource and scheduler accounting

Initial Slurm scontrol records verify one CPU, one node,8GB, default partition,
12 minutes, exclusion of `scaglione-compute-01`, no requeue and the isolated
research checkout wrapper. Completed sacct records show job and batch exit0:0,
elapsed6m35s, node`snavely-cpu-16`, and batch MaxRSS397140KiB. The extern step
lasted6m36s. Post-completion scontrol had expired; its explicit unavailability
note and original pending allocation are retained. The initial packaging
interruption did not rerun scientific work.

Both calls requested GRB with one thread and180-second native caps. Reported
native wall times are180.0124767660 and180.0174127608 seconds, preserving the
small native-return overhead rather than hiding it. The entire scientific
routines, including replay/admission, took184.6948992931 and184.5684277071
seconds, below240 seconds each. External child limits are255 seconds. The
outer wrapper reports375 whole seconds, exit0, no timeout and the unchanged
560-second cap/10-second kill grace. Freeze and worker Python/package metadata
match; both calls record the same GRB native-library SHA-256
`57f87a886aa5a1fd8356494fa1b81e9f9c7d957c898d09e96145440c76c762b7`.
These saved identities support provenance; this review does not remotely
recompute the cluster library bytes.

## Confidential logs and public packaging

The complete local archive was audited. Each cell's152-byte stdout contains a
license identifier and token-server configuration; neither value is reproduced
here. Both stdout files have SHA-256
`4d6f5fb03c58ea40fc56b696dedb61dc744dbe9c824576c069c2fb20b8cc6932`.
The frozen publication policy permits omission of these two whole files from a
separate public copy, with path/size/hash/reason listed and originals retained
locally. All other15 scientific artifacts must remain byte-identical, and the
public package must include the original raw manifest and explicit omissions.
The accompanying scheduler/publication report verifies omission eligibility;
the later assembled public copy still needs its own byte comparison.

Raw manifest SHA-256:
`826e79867437b5d1f464e3f54a0f204bb18a8541470e06a2344345881b0b1d01`.
Full completed transfer archive SHA-256:
`eda8c161372c4f0c774036b217fed56c072d4749f1865329e9ee314eec321ef5`.
The earlier zero-byte failed-transfer placeholder is not the completed archive.

`numerical-audit.json` contains detailed per-row checks, exact stored-number
arithmetic, references and corruption results. Its scheduler field records
that scheduler inspection was a separate pending stage when the numerical
report was produced; `scheduler-publication-audit.json` completes that stage
with a PASS and immutable receipt hashes. Together they support this final
verdict. The two read-only audit scripts permit reproduction without a solver.
