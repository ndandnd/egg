# Independent half-minute source-time preflight

27 September 2026. **Ready for a separate prospectively frozen 19-cell local
qualification.** No blocking implementation, mathematical or evidence-preservation
issue was identified in this snapshot. The reviewer did not edit the native
implementation, runner, tests or protocol and did not import or run an optimizer.
This is a preflight verdict, not a claim of successful native execution or
operational-source qualification.

## Reviewed files

| File | SHA-256 |
|---|---|
| `src/egglab/native_recharge.py` | `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3` |
| `src/experiments/native_recharge_qualification.py` | `200c5bec8e6f8c7f7e466ef045b439dceae9fa2b35984cc452d4d29471dfde1e` |
| `src/experiments/native_halfminute_qualification.py` | `1ca683c897828c7033d7d21862aae49aa25f0244c10e12abbd2c19065aa90c63` |
| `src/tests/test_native_recharge.py` | `500ae0e1164511c4e677167038f5decccf809657dc2091e991f5d49a2c6d7bc9` |
| `src/tests/test_native_halfminute.py` | `deb6b9ca0ee029004cc01a6c68807f9d5c0ee717094b01d7a487bb808e3aaa5d` |
| `doc/NATIVE_HALFMINUTE_QUALIFICATION_PROTOCOL_20260927.md` | `bc18bc9d2dfced1b32401bab9ad052d835616e611f0c4d5db4a9fd9dc08a48f5` |

## Validation and compatibility

The new `_timestamp` predicate is separate from `_minute`. It accepts only
nonnegative builtin integer/float values on the exact half-minute lattice, up
to 2^20 minutes; bool is excluded. The bound comparison precedes multiplication,
so arbitrarily large integer inputs are rejected without an overflow-inducing
float conversion. NaN/infinities fail the bounded comparisons. Exact modulo
rejects off-lattice values without rounding or a closeness tolerance.

All exogenous timestamp fields use this predicate: service start/end, movement
leg departure/arrival, resource boundaries, market edges, terminal opening and
recharge deadline. Vehicle identifiers, connector labels/counts, fleet counts,
depot-split indices, threads, iteration limits and event round indices retain
strict integer validation. Solver-decoded session endpoints remain continuous;
only input timestamps are restricted to the source lattice.

At 2^20 minutes the double-precision spacing is 2^-32 minutes, approximately
2.3283064365386963e-10, below the existing 1e-7-minute replay tolerance. Every
accepted half-step and every difference between accepted endpoints is exactly
representable. Division by 60 can still introduce ordinary floating arithmetic,
so model capacities and materialized sessions remain governed by the existing
native feasibility, exact correction ledger and replay policies. No extra
rounding or timing tolerance was introduced.

The fifteen previous control JSON definitions, objectives, targets and case
identities are unchanged. Original integer values are not coerced to floats;
only dataclass annotations and timestamp validation broaden to permit halves.
The new ceiling is also a deliberate restriction: extremely large integer
horizons formerly accepted are now rejected. Compatibility therefore applies
to the retained controls and declared bounded domain, not to every imaginable
previous integer input. No source adapter or missing-energy inference is
validated by this change.

## Mathematical and physical equivalence

Strictly positive service durations remain positive (at least half a minute).
Chronological movement arcs still make service start times strictly increase,
so the path-coverage/acyclicity argument is unchanged. Exact input boundaries
produce the same event-partition construction. Big-M, SOC, grid-energy units,
reserve, efficiency, native full recharge and shared single-connector constraints
are unchanged.

For the multileg equivalence control, transform time by `t'=t/2`, power by
`P'=2P`, and driving cost per minute by `d'=2d`, preserving every service/travel
energy, battery parameter and market coefficient. A mapped charging schedule
has the same grid energy because doubled power acts for half as long. Driving
cost is unchanged because `d' delta_t' = d delta_t`. Resource intersections,
service/travel exclusions, SOC event states, market-period load vectors and
objectives correspond in both directions. The existing multileg fixture therefore
retains 14 grid kWh, intrinsic cost 22 and unit-price objective 36; its 5-minute
legs become 2.5 minutes. This is a synthetic time-scale equivalence test, not an
assumption about real vehicles becoming twice as powerful.

The actual half-minute capacity control consumes 0.5 kWh and returns at minute 0.5.
Its only window ends at minute 1, so 60 kW supplies exactly `60*(0.5/60)=0.5` kWh.
One used bus costs 7; unit-priced full recharge gives objective 7.5. At 59 kW the
capacity is 59/120 kWh, strictly less than 0.5, proving infeasibility independently
of an optimizer. This control exercises fractional duration rather than merely
shifting integer-length intervals.

The coincidence control uses one bus with capacity 1 and reserve 0. Service A
consumes 1 kWh during `[0,0.5]`; the depot visit recharges 1 kWh during `[0.5,1.5]`.
An instantaneous outbound leg consumes 1 kWh at 1.5, before a declared zero-energy
second service ending at 2. The `[2,2.5]` 120-kW terminal window supplies the final
1 kWh. The SOC sequence is `1 -> 0 -> 1 -> 0 -> 1`; total grid energy 2 and vehicle
cost 7 give objective 9. Charge completion must precede the simultaneous outbound
consumption. There is no direct A–B alternative and only one bus, so coverage
forces the intended depot path. This artificial zero-energy service is a
regression fixture for event ordering, not an operational route or a new
positive-gap research example.

## Controller and evidence review

The dedicated runner preserves all fifteen existing controls before appending
the four new controls. The prospective gate expects 15 certificates and four
infeasibilities. Native objectives, input data and targets are frozen before
execution; no analytical schedule is supplied as a solver seed.

AST comparison confirms that `worker`, `read_worker_evidence` and `main` are
identical to the previously reviewed V2 implementations. The controller's AST
is identical except for the worker module's deliberate change to
`experiments.native_halfminute_qualification`. The new runner has its own
protocol/output root/source hashes and hashes the imported original runner and
native module as well as tests and protocol. It does not dispatch the original
fifteen-case worker accidentally.

Exclusive attempt creation, per-cell inputs, native starts/statuses, raw
incumbents before decoding, correction/session/objective records, exceptions,
valid-prefix handling and continuation after failures retain the qualified V2
structure. Counts and raw statuses remain separate. Each worker keeps the
one-thread, 10-second native phase, 45-second routine and 60-second process caps;
maximum declared worker allowance is 19 times 60 seconds plus controller overhead.
This protocol does not claim a separate tighter hard controller timeout. It
contains no retry, cap extension or fallback inside an attempt. The freeze label
still requires the principal researcher's actual commit/hash verification; the
CLI's nonempty-string check is not itself Git attestation.

## Independent pure checks actually run

With pytest plugin autoload disabled and a meta-path blocker raising on imports
of `mip`, `mip.*`, `gurobipy` or `gurobipy.*`, the reviewer ran both native and
half-minute test modules: **79 passed in 0.08 seconds**. No optimizer was imported,
initialized or executed. Tests include old JSON identities, bounded/exact timing,
nonfinite and off-lattice rejection, integer-only discrete fields, fractional
resource/market edges, actual capacity success/failure, coincidence ordering and
multileg equivalence, in addition to all earlier native pure/fake controls.

The reviewer additionally checked 10,001 half-step values from 0 to 5000 minutes:
each is accepted and has exact rational denominator 1 or 2, while the adjacent
floating values on either side are rejected (at zero only the positive adjacent
value is checked). The ceiling's ULP is explicitly below the replay time tolerance.
These direct checks used the same native-import blocker.

The new 19-cell native qualification and its artifact audit are still required.
Subsequent operational scheduling or hull experiments require their own declared
inputs, source provenance and appropriate scientific gates. This preflight adds
no support for missing directed arcs, unknown travel energy or source-data
publication permissions.
