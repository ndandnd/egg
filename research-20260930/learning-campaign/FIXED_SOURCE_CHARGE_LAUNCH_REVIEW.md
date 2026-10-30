# Fixed-source charging launch review

Reviewed 30 September 2026 before any result from this attempt. The eight-cell
comparison isolates inherited charging from source route topology on development
seeds 2016–2019. It completes a missing cheap baseline before further model work.
It uses only pinned pre-target source fleets for charging and source selection;
historical target outcomes are reporting controls. Test seeds remain untouched.

The movement set is fixed exactly. Charging minimizes the linear tariff, then
independent physical replay and exact nonlinear rescoring determine candidate
cost. No fresh hull, global optimum or matched-runtime speedup is asserted.
The two single-LP selectors and the two-LP best-of-two comparison pay different
online costs. Historical source acquisition and model preparation stay separate;
any unknown timing makes its aggregate unknown.

Root and a bounded independent reviewer checked missing direct-receipt recovery,
provisional plan salvage, case/market/source/hash/topology and physical replay,
and timing separation. A valid saved plan remains provisional after any failed
or timed-out child, even when its result file was already written. All failure
receipts and spent time remain available. Source catalogs and pre-target source
provenance are pinned; no previous checkout or attempt is overwritten.

Validation: the implementation's related pure tests passed 20/20. After final
missing-time and failed-receipt status fixes, the focused test file passed 6/6
in 2.26 seconds, including both failure paths. Shell syntax and design checks
passed: eight cells, 12 execution source hashes, 18 archived input hashes.
These checks used archived replay and mocks, not local native solving.

Prospective caps: charging 45 seconds phase / 55 seconds wall, child 100 seconds,
controller 1200, shell 1350, Slurm 1800. One CPU, 8 GB, one native thread,
no retry/requeue; exclude scaglione-compute-01. Eight child caps fit within the
controller cap. The guarded launch rejects any active EGG job and an existing
target checkout, and records a unique submission before returning its job ID.

Ready for exactly one submission after this reviewed source is committed and
pushed. Results remain pending independent review.
