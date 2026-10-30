# Independent review: Sistig one-bus obstruction

27 September 2026. **PASS for the one-bus infeasibility proof in both frozen
single-depot cases.** I independently read the frozen JSON with standard-library
code and recomputed service and forced-transition energy as exact fractions of
the stored numeric values. I did not import the diagnostic, model, optimizer,
or matching implementation.

The frozen input SHA-256 is
`35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b`; the
post-pilot result SHA-256 is
`cdc2603b1e53dba7fdff757e63c2f64265b0d190aef1174f4792d607ecf2b3e9`, and its
recorded diagnostic script SHA-256 is
`fada2a1ef1fc2b1aa0f54f8c847d0f84cfa6659f56f8638f02ed9550094d4b5f`. The
diagnostic's `parents[3]` root resolves to the repository root, and its default
frozen-input path is the file matching that digest.

For each depot case, the 37 services have positive durations and form a
nonoverlapping chronological order. I checked all movement modes for temporal
forwardness and found exactly one available mode between each of the 36
consecutive services: a direct mode, with no depot mode. Thus a one-bus cover
cannot insert a modeled recharge opportunity between mandatory services. The
mandatory-service energy alone is exactly
`250264333071608593/281474976710656` kWh (889.1175194194), against 400 kWh
available inventory. This is already a strict obstruction. Independently
recomputed direct/wait movement energy is
`12835258938005913/140737488355328` kWh (91.2); service plus those forced legs
is `275934850947620419/281474976710656` kWh (980.3175194194). The first 16
services and their 15 forced transitions consume exactly
`15081332800189559/35184372088832` kWh (428.6372586702) by 14:07, before any
modeled depot opportunity. The direct-mode stationary waits are represented
as their own movement legs; their auxiliary energy is not counted twice in
service energy.

This proves a lower bound of two buses for each exact declared graph and
battery policy. The stronger statement that the minimum is exactly two also
uses the separately audited first-pilot two-bus incumbents: that review reports
complete replayed witnesses for both cases under the same frozen input and
source commit. Those upper witnesses are floating-point physical replays under
the admitted tolerance, not exact-rational feasibility certificates. Together
the lower proof and qualified replay support minimum cardinality two for these
modeled cases only; they say nothing about cost optimality or an unrestricted
network. The proof's 2000-kWh counterchecks correctly mean only that this
particular obstruction no longer proves infeasibility.

The candidate sensitivity note now records the reviewed scope and accounts for
40 fresh response phases. Its routine-cap sum is 592 minutes; 68 child margins
of 15 seconds add 17 minutes, for 609 minutes (10 h 9 min) within the candidate
11-hour envelope. This remains planning only, not execution authorization.
