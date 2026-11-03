# One optimal QP point failed physical session materialization

25 October 2026. Static source/compact-receipt diagnosis only. Inspected the
008 `scale:50603:80` [QP result](attempt02/008-qp-scale-50603-80/qp-result.json)
and [worker receipt](attempt02/008-qp-scale-50603-80/receipt.json), and the relevant
original extraction/projection/serial-decoding code. No raw matrix, solution
vector, model asset or trace was inspected; no source edit, import, test, hash,
replay, solve or repeat was performed. Attempts01 and02 remain immutable.

## What the receipt establishes

The matrix-copy contract passed. The one QP returned native Status2/OPTIMAL,
SolCount1 and 13 barrier iterations. Its native call took0.122206s, with zero
native-deadline overrun; the full worker receipt was prepared at10.859s. This
failure was not a missing incumbent or exhausted52/60-second allowance.

Unchanged extraction raised `Positive charge has no representable
interval-contained session`. Accordingly `qp_success=false` and
`qp_candidate_admitted=false`. The independently replayed four-vehicle prior
remained the accepted operational endpoint, cost1422.6779732510288. The native
objective1299.011935736556 is a numerical QP value, **not an admitted physical
plan cost**. This note does not independently audit the other seven witnesses.

## Exact failure path

`native_pathflow._project_charge_energy` sets admitted negative residuals and
positive unselected charges to zero under the existing whole-incumbent budget.
Every selected strictly positive charge remains positive. `_extract` passes
these values into unchanged `native_recharge.decode_serial`.

For each elementary interval `[s,t]`, the decoder sorts positive rows by
vehicle/movement. It accumulates their energies exactly as Fractions. With total
E and cumulative C_i, an interior endpoint is

`end_i = float(s + (t-s)*C_i/E)`.

The last endpoint is the interval end. The cursor is the preceding rounded
endpoint. Before making a session, the decoder requires
`cursor < end_i <= t`. With positive interval duration and positive energies,
the exact cumulative endpoints increase; rounding them to binary64 can still
collapse two endpoints onto the same value. A preceding endpoint may also round
to t before a later positive row. The interval compiler constructs strictly
increasing edges, and the decoder deliberately rejects a zero-duration or
out-of-interval materialization instead of deleting a positive charge.

The failed guard precedes the per-session capacity-excess check. It does not
establish physical infeasibility, an exhausted roundoff budget, or excessive
energy demand. Barrier's positive residual allocations are a plausible mechanism,
consistent with the observed barrier iterations, **not an identified culprit**.
The compact evidence omits the failing interval, vehicle, movement, energy,
total/cumulative energy, row position and endpoint representations. Neither its
location nor magnitude can be recovered from these receipts; in particular,
there is no evidence that it was negligible or safe to erase.

## Minimal prospective option, not a retry decision

A small existing-public-API option is a separately frozen one-call QP policy
using **Method=0, primal simplex**, with the same matrix, objective, accuracy
settings, clock, unchanged decoder and independent replay. Gurobi's
[version12 manual](https://docs.gurobi.com/_/downloads/optimizer/en/12.0/pdf/)
supports simplex for continuous QP; the
[Method reference](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameter:Method)
identifies0 as primal simplex. This requests a different numerical solution
allocation and may avoid interior residual charges; it guarantees neither
representable sessions nor removal of this failure. Any prospective use must
retain all outcomes and cannot replace the original7/8 record.

Do not clip positive energy, permit equal endpoints, extend a session beyond its
interval, widen replay/projection tolerances, or replace this allocation with
full-window reduced-power charging. Those actions change established assumptions
and need separate justification. Parent scientific readout and a fresh explicit
decision must precede any numerical experiment; no new command is cleared here.
