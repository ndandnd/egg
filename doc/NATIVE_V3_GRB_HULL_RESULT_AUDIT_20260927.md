# Native V3 GRB hull result audit

**PASS.** I independently reconstructed all eight frozen hull controls from
the sealed GRB run. The result supports admission of this qualification gate;
it does not by itself authorize the separate nonlinear pilot.

The audited attempt is
`result/native_pathflow_hull_grb/20260927-attempt1`, frozen at commit
`62976f11ecf35c837b0573079892ae5095e846b9`. Its immutable manifest SHA-256 is
`a8e1a883f03c5f8e1d6a710ec70500836f950404b3158331a2ffe668c753acf4` (66
listed files; 1,193,246 bytes). The controller and GRB wrapper both report
that source hashes remained unchanged. I checked the 20 frozen source hashes
against Git blobs at the pinned commit and checked all 28 wrapper source pins.

For every control, the audit rebuilt the physical pricing witnesses, exact
stored-coefficient tangent master, fresh global Fenchel lower bound, retained
pool state, mixture cost and outward-rounded interval. It independently
enumerated the declared complete hull and confirmed the target was enclosed
by the recorded interval. The eight target objectives were 94.8875 for
`nominal_cold_s0`, `nominal_cold_s2`, `nominal_retained_s0`, and
`nominal_retained_s2`; 96.1875 for `nominal_cold_s1` and
`nominal_retained_s1`; 103.45952216066483 for `joint_cold`; and 99 for
`fixed_reserve_cold`. Recorded interval widths were approximately 1e-6,
including only the expected outward-rounding difference.

The frozen controls and budgets match CBC V3 attempt 2 exactly except for the
declared backend change and the resulting backend-specific state identities.
The recorded GRB runtime is `mip.gurobi` with MIP 1.17.6 and gurobipy 12.0.3;
all 36 native calls reported one consistent GRB runtime/library fingerprint,
with no CBC fallback. The archive records 21 pricing calls, 15 LP master
calls, 9 polish transfers, 24 polish checks, and 44 replayed charging
sessions. The audit rejected all 48 targeted corruptions covering raw
variables, native lower bounds, tangent rows, physical SOC, V3 policy and
oracle identity, mixture reconstruction, retained-state import, polishing,
and final interval claims.

Execution receipts also agree: Slurm job 559602 completed with exit 0,
one CPU, 8 GB, and 26 seconds reported; the wrapper and controller exited 0
without timeout or source drift. The sealed launch sentinel, transport
receipt, scheduler accounting and pinned physical admission were checked.
Full license-bearing stdout files remain preserved in the complete archive;
the audit report records their integrity without reproducing their contents.

The solver-free independent audit package is in
`research-20260927/agent-notes/grb-hull-result-review/`. Its machine report
is copied byte-for-byte to
`result/native_pathflow_hull_grb/20260927-attempt1-publication/independent-audit.json`
for the downstream evidence pin; this is outside the immutable raw attempt.
The full result remains a bounded qualification audit, not a claim about
large-market performance or the separate nonlinear pilot.
