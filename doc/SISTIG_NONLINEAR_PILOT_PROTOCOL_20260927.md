# Prospective one-cell Sistig nonlinear pilot protocol

27 September 2026. **Preparation only: NOT-YET-QUALIFIED. No public nonlinear
planner, hull, pricing, cluster job or optimizer has run under this protocol.**
The research-lead decision in
`SISTIG_MINIMAL_NONLINEAR_PILOT_RECOMMENDATION_20260927.md` selects one cell:
all 37 mandatory services in source depot 15's declared single-depot graph,
400-kWh usable battery, 360-kW one-connector charging, 30:00 full-recharge
deadline and 30 hourly grid-energy periods. The synthetic objective has stored
float coefficients `a_t=.2`, `b_t=1/900` in
`F(L)=sum_t(a_t L_t + b_t L_t^2/2)`. The binary stored floats, rather than
symbolic decimal/rational replacements, determine native objective arithmetic.
All source movements, recharge physics, replay and fleet cost are identical
between physical and hull routines. Depot 16, deadlines, hardware changes,
reuse arms and common-mixture-price LOC are outside this attempt.
The 30:00 deadline is a synthetic finite service-block boundary. Replenishment
by 30:00 does not prove recurring 24-hour operational feasibility or that
charging can finish before the next day's departures; that overlap is not
modeled or tested here.

## Admission hold and source freeze

Production backend is **GRB only after fresh same-source GRB qualification**.
The prior GRB 15-control and CBC 20-control evidence do not satisfy this gate.
Before `freeze` can create the exclusive
`result/sistig_nonlinear/20260927-attempt1`, an independent reviewer must
publish `doc/SISTIG_NONLINEAR_PILOT_IMPLEMENTATION_REVIEW_20260927.md`
containing `**PASS**`, and a committed
`doc/SISTIG_NONLINEAR_PILOT_ADMISSION_20260927.json` with `status: PASS`,
`backend: GRB`, and `physical` and `hull` objects. Each object must pin
`frozen`, `summary` and `audit` JSON under `result/` by relative path and
SHA-256. The physical gate must have 20 passing controls, source unchanged,
independent audit PASS, V3 formulation/extraction identity and GRB budget.
The hull gate must have eight passing controls, source unchanged, independent
audit PASS, V3 compact oracle/extraction identity and GRB budget. Both frozen
gate control manifests and full GRB budgets must match the current pure V3
qualification builders exactly, including targets and state identities. Both
gate source hashes must equal the current physical dependencies; the hull gate
must also match current `native_hull.py` and `native_pathflow_hull.py`. Missing,
changed or mismatched evidence raises `NOT-YET-QUALIFIED` before an attempt or
optimizer call. The admission reviewer must check matched feasible sets,
bound/replay policy, one-cell identities and the fixed five-unit resolution.

The `freeze` mode also requires every file in the runner's `SOURCES` to match
the published `HEAD` blob. This includes the full public payload, this
protocol, implementation review, admission JSON, native modules, all imported
qualification/accounting helpers, runner, tests, batch script and environment
script. It records complete case and market data/identities, hashes, GRB
backend, Python/executable/platform and solver-package versions, three budgets
and caps. The payload SHA-256 is
`af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6`;
the depot-15 case identity is
`1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7`.
All stages recheck the frozen source and gate. Review and source publication
are separate manager-owned steps; this document does not authorize launch.

## Three sequential routines and evidence

1. **Physical PWL planner.** Use compact V3 `solve_planner` with one GRB
   thread, at most 48 tangent rounds, 180 seconds per native phase and
   240 seconds for the complete routine. The child hard stop is 255 seconds.
   Admit a finite global interval `[L_D,U_D]` only with a replayed complete
   whole-fleet incumbent, source/formulation/extraction identity, preserved
   raw rounds, bound statistics, plan/movement IDs, charging and SOC ledger,
   hourly load and intrinsic/true objective. A bounded result remains bounded.
2. **Full-fleet hull.** Use the compact V3 coordinator from a cold seed at
   `p=a`, with one GRB thread, 180 seconds per native/master phase, six global
   pricing calls, eight masters, 48 columns, existing exact-polish caps and
   24 minutes for the whole routine. The child hard stop is 24 minutes
   15 seconds. Require a global pricing/Fenchel lower bound `[L_CH]` and a
   replayed convex mixture of complete feasible fleets for `U_CH`; never
   promote a restricted pool lower bound. Preserve every column, mixture
   weight, price, supporting residual, global certificate and call trace.
   `stalled_bounded` or `budget_exhausted` may yield an honestly labeled
   bounded interval only when the saved finite global bound and feasible
   physical mixture both replay. A missing bound or failed replay stops the
   cell. Replay every final column; the saved mixture may use an ordered
   subset because a later priced candidate can extend the final column list.
   A valid `budget_exhausted` result keeps that raw label, may proceed to the
   own-price stage under the original caps, and is never called certified or
   optimal. A hard timeout stops the cell. The worker writes its returned raw
   result before assessment so failed admission cannot erase it.
3. **Own-price physical response.** Derive the fixed price vector
   `p_s,t=.2+L_s,t/900` from the saved planner incumbent's replayed load.
   Run one fresh compact V3 global linear pricing solve with one GRB thread,
   a 180-second phase cap and 240-second routine cap; child hard stop
   255 seconds. Replay its whole-fleet response and admit its global
   `[L_p,U_p]`. Do not reuse a hull pool bound as the response bound.

The routine caps sum to 1,920 seconds. Child caps sum to 1,965 seconds.
The supervised complete attempt cap is **2,040 seconds (34 minutes)**,
including 75 seconds for fixed overhead. The batch wrapper has a 2,070-second
shell stop and 36-minute Slurm allocation; these do not extend a scientific
routine. Use one CPU, one solver thread, at most 8 GB RAM, no retries,
retuning, extra price samples, seed swaps or response substitutions. Failed
and unstarted stages remain visible. The supervisor owns a process group,
records launch, stdout/stderr, timeouts, return codes and source drift, and
seals a SHA-256 manifest even after controller failure. Every attempt file
is write-once. The later Slurm wrapper receipt is separate from that sealed
supervisor manifest.

## Interpretation and independent audit

Preserve raw signed stored-float intervals:

`Delta in [L_D-U_CH, U_D-L_CH]`,

`r(s;p_s) in [A-U_p, A-L_p]`, where `A=c(s)+p_s·L(s)`.

Use exact fractions of stored binary floats for the saved endpoint differences;
this is bookkeeping of conditional numerical endpoints, not an exact physical
objective proof. The predeclared pilot classification resolution is **five
synthetic objective units** and the negative consistency guard is `1e-4`
unit. A gap lower endpoint above five is resolvably positive. A gap upper
endpoint at most five with a lower endpoint above `-1e-4` supports only the
literal conclusion **“gap at most five units under the declared numerical
policy.”** Otherwise report unresolved; a materially reversed enclosure is
a consistency failure. Report any positive lower endpoint even below five.
Do not call the at-most-five conclusion an exact zero gap. Regret belongs to
the named planner incumbent unless planner optimality is separately certified
under the declared numerical policy. Preserve all distinct tied optima found.
The analytic linear zero-gap identity is context; no fresh flat solve is in
this attempt and no universal flat `1e-4` prerequisite applies.

After any future admitted execution, an auditor independent of the runner
and native implementation must reconstruct physical/hull/pricing identities,
backend and call accounting, whole-fleet replay, global lower bounds, Fenchel
arithmetic, mixtures, prices, interval subtraction, stop/timeout receipts and
manifest before a scientific conclusion is admitted. This one synthetic
single-depot cell cannot establish a sensitivity trend, source two-depot
fleet result, repeated-daily feasibility, calibrated tariff or operational bus
recommendation.
