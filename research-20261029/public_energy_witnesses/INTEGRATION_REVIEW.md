# Independent source integration review

Scoped PASS after the owner validation repair below. This is source review of the new worker, owner, protocol and draft control only, with the unchanged constructor/verifier callable contracts checked. No input packets, executions, imports, tests, hashes, native calls or commits were performed. This review does not authorize a draft launch or repeat the old constructor qualification.

## Scope and mathematical admission

- Exactly two fixed constructions are assigned, `MIQP_new` and `PRICE_MIP_new`; exactly three fixed pairs cover every pair among those and the protected component. Missing inputs/components retain their assigned rows. Each available new candidate gets at most one constructor call, followed by at most one independent replay. Strict physical and certified-objective flags are all required. Original raw native statuses cannot admit the original candidates.
- The unchanged qualified constructor and verifier are executed from their admitted cached source buffers at `ef0b088193bc19527476f9db9e632c37379d9a2a`. Their interfaces agree with the new calls. The new integration does not alter their terminal-only preservation rule or independently requalify that old rule.
- Case, protected transfer and two raw packets have fixed source paths and revisions (`253c…`, `929bd…`, `f8a…` respectively). Byte admission precedes use. The protected transfer checks the producer, case, paths, field contract, strict flags, closure flags and exact upper. It reuses its certified component without another physical replay. No data-supplied path is followed.
- Q0 is a new abstract mixture qualification: right weight `1/4`, objective `7/8`. Its independent check recomputes the actual quadratic and endpoint/interior derivative conditions. The changed-weight control has a self-consistent mean and objective, so rejection genuinely exercises KKT; the changed-objective control exercises direct evaluation.
- For a segment, the helper uses exact original binary coefficients and clamps its rational quadratic minimizer to `[0,1]`. The independent evaluator does not trust the helper's polynomial coefficients or endpoint objective. Flat segments return the entire weight interval. Each admitted answer is only an upper bound for the hull problem along a feasible two-plan segment; it establishes neither physical executability of the mean nor hull optimality nor a support sign. Three pairwise minima also need not minimize over the three-component simplex.

## Failure and resource closure

Ordinary missing-candidate, construction and strict-replay failures preserve outcomes and permit the other assigned work. Source/configuration/Q0 errors and unexpected replay/programming errors are fatal. Fatal reports pad later rows explicitly; abrupt master loss becomes owner `UNKNOWN_UNREPORTED`, not invented scientific success. Exit zero denotes administrative closure and is separate from `scientific_all_delivered`.

The worker has no native import or solver call. Source admission, decoding, new construction/replay, mixtures and publication fall inside the externally metered owner process and waited child. Worker self CPU is capped at 90 seconds; nested observations use 100 CPU/150 wall and 5 GiB RSS, while package observations use 120 CPU/180 wall. Worker group cleanup and reaping are explicit. Nested worker CPU/RSS observations precede final report serialization, and owner observations precede owner-receipt serialization; the protocol correctly makes the external meter authoritative for complete publication and shutdown. RSS is an observed process maximum rather than aggregate instantaneous memory enforcement.

## Repair made during review

`run.py` previously checked row IDs but subsequently read row `status` and master `resource_pass` outside its malformed-master guard. A master with correct IDs but a missing status or closure field could prevent the owner receipt. The new guard validates each candidate/pair terminal status and requires actual Boolean resource/administrative/scientific flags before subsequent access. Malformed masters now follow the existing failure/UNKNOWN ledger path. This minimal new-source repair was reported to the parent; it has not been executed or tested.

No remaining source blocker found within this bounded scope. A source freeze, separate frozen launch control, one authorized dispatch and external closure inspection remain necessary before any scientific result is promoted.
