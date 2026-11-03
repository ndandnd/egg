# Focused integrated prelaunch review

Verdict: **Static mathematical/comparison review passes. Final source admission
requires the already identified fatal-row status correction to be saved and
confirmed before freeze.**

Scope: source-only reading of candidate.py, cases.json, verify.py, run.py,
PROTOCOL.md, and the added equal-fee paragraph of PROOF.md; rely on the prior
physical reference and full proof review. No numerical execution, import,
test, hash computation, old replay, native solver, or commit was performed.
This review writes only this document and establishes no runtime outcome.

The candidate correctly implements the equal-fee battery threshold using
a*a-5*a-35/2 rather than approximate square roots; its positive-gap hull
formula and supported physical point agree algebraically with the proof.
The battery25 variable-fee hull pieces meet at fee21/2, and physical optima
are both retained at fee12. Movement elimination is used only in the
analytical candidate and justified by energy/cost dominance; the independent
reference retains physical movement branches.

The comparison deliberately merges only identical projected optimum points
and unions overlapping response intervals having identical total energy and
operating cost. This preserves the full projected continuous deviation set.
It does not claim equality of labeled bus assignments or duty identities;
those remain in the reference raw records. The candidate's smaller formula
domain is adequate for the closed assigned set: baseline, movement, six
equal-fee battery cases, and six battery25 fee cases. All fourteen IDs,
order, and parameter states are checked. Finite cases qualify implementation;
the written proof, not this count, covers continuous parameters.

The controls address objective corruption, projected planner-tie loss, flat
response truncation, charging/service/power corruption, movement timing and
invalid domains. Outputs are exclusive and source closure is checked against
the committed revision using cached consumed buffers. Assertions are required.
The prospective command's isolated Python flags and declared thread variables
are consistent with the source protocol.

The worker has a40-second self CPU cap, observed inclusive45-second and
60-second wall acceptance gates and an observed512MiB RSS gate. The owner
has sufficient inherited hard CPU ceiling for the worker to set its limit,
owns its new process group, kills/reaps on timeout, records package resource
observations and uses exclusive output paths. The external POSIX meter
remains authoritative for complete startup/shutdown and the package60CPU/
90wall allowance. Nested receipts must not be added again to that charge.
The protocol correctly distinguishes practical containment/observations from
an exact aggregate OS CPU or instantaneous memory cap.

Remaining source-status detail at the reviewed bytes: a fatal exception while
evaluating a case can leave its row as ATTEMPTED. Convert that begun row to
FAIL with the fatal reason before appending later UNATTEMPTED cases. Preserve
assigned14, attempted/unattempted and passed counts. The parent has already
identified this fix; no other blocker was found. A failure/missing receipt or
resource excess after launch must block promotion rather than trigger a retry.

Interpretation remains conditional on the declared resources, full refill,
fixed posted tariffs and complete plan set. Added equipment is explicitly a
model expansion; the result is not empirical prevalence, ML benefit, or a
new general pricing theorem.

Parent completion: the saved verify.py exception handler was read after this
review. It now converts the begun ATTEMPTED row to FAIL with the exception
reason before adding UNATTEMPTED rows. This resolves the only open item.
Final verdict: PASS for one prospective frozen execution, not runtime success.
