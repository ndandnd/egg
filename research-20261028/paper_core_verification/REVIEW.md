# Integrated pre-execution review

Status: **PASS — static pre-execution review; no remaining identified blocker.**

Scope: read only reference.py, candidate.py, verify.py, run.py, PROOF.md,
PROTOCOL.md and cases.json. No execution, import, hashing, numerical tests,
historical result replay, native solver, or runtime qualification was performed.

The full-domain derivation correctly separates infeasibility, K=20, f=0,
interior gaps and both equality boundaries. Both physical planner optima are
retained at fee ties. The complete linear deviation set is represented by its
endpoints, with whole flat intervals retained in the argmin description.
The reference independently obtains feasible endpoints from rational SOC
polytope vertex enumeration and optimizes every hull edge; it does not import
the candidate's projected intervals or gap formula. Its chronological charging
witnesses are sufficient in the declared zero-switching, constant-power model.
Exact comparisons cover objective values, every planner optimum, prices,
regret, complete response sets and the unique hull load. Boundary cases and
copy-only corruption controls are appropriate. The finite cases qualify the
implementation; PROOF.md, rather than their number, establishes the continuum
claim. No performance or operational-prevalence conclusion follows.

Focused correction review: run.py now installs its owner alarm and soft CPU
reserve before startup work, bounds the branch subprocess, and retains a hard
ceiling permitting the worker's self cap. verify.py bounds each source Git call.
PROTOCOL.md accurately distinguishes aggregate observed acceptance from exact
OS containment and includes external startup/shutdown measurements. These
changes resolve the original two resource-control objections.

Final focused tail review confirms verify.py now records total worker process
CPU including startup plus waited-child CPU, checks that sum below 15 seconds,
combines that check with the observed memory ceiling, and gates successful exit
on both numerical checks and this resource acceptance. The last consistency
objection is resolved. Measurements precede final receipt/shutdown work; the
owner and external meter remain authoritative for full publication acceptance.

The observed-only memory ceiling is already accurately described. Exclusive
output creation, isolated stdlib execution, cached reference/candidate source
buffers, source revision comparison, and retained failures support the stated
preservation design. Static review establishes no runtime, resource-usage, or
successful-reproduction claim. Runtime qualification remains pending.
