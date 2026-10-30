# Independent source integration review

29 October 2026. Reviewed only this new package's reference, candidate, verifier, owner, twelve literal cases, protocol and draft control. No execution, import, test, hash, backend, actual timetable data, old numerical packet or frozen public source was used or changed.

**Verdict: scoped source PASS after a narrow owner robustness correction.** This is readiness for parent freeze consideration, not an execution PASS, resource result or novelty assessment.

## Scientific implementations and comparison

The raw reference exhausts partial bipartite crossmatchings, keeps separate assignment labels and constructs per-A early variables from inventory/headroom and full-refill equations. Shared constraints are sum early<=K and total terminal<=H. Separate per-bus power inequalities are not missing: nonnegative allocations and the common connector/acceptance powers imply each allocation is no larger than the shared total. Fixed windows and no consumption while charging permit explicit serial sessions on the one connector. Replay checks canonical service coverage, no connector overlap, power limits, per-bus inventory at every elementary time slice, full endpoints and exact total energy. Zero K avoids division by zero; zero H yields no feasible vertices for positive B-service energies.

The analytical implementation is structurally different. It chooses the m smallest A/B energies and pairs them oppositely. This threshold formula is valid because positive-part pair cost is increasing in either energy and convex in their sum: replacing a selected service by a smaller one cannot raise cost, and the convex rearrangement inequality favors opposite pairing. The code then uses the clipped matching frontier rather than generic hull construction. It still enumerates all assignment labels for full response and allocation comparisons.

Both implementations correctly use the quadratic stationary point `(S-20n)/2`; the20 comes from the supply intercept4 and quadratic scaling, not the battery capacity parameter. The raw reference obtains its lower hull by generic monotone chains. The candidate retains intermediate matching thresholds even when collinear, includes the clipped L endpoint, discards cardinalities with threshold>U and separately handles f=0. The final horizontal piece starts at the last actually retained frontier point, including the case m0=mmax.

The verifier compares every assignment's feasibility interval and full individual allocation polytope, not just D/CH. Candidate boxes are converted to inequalities, clipped by total bounds, and compared by generic vertices against the reference's raw SOC polytope. Removing only the two shared-resource rows recovers independent raw matching minima even for globally infeasible cases. Optimal assignment ties, prices, regrets, response intervals and full response allocation continua are retained and checked. Endpoint representatives are not substituted for flat response sets. Its assertion that every physical optimum has zero regret when the gap is zero is valid for this differentiable finite quadratic model.

## Twelve literals and negative controls

The source independently fixes all twelve literal tuples, capacities20 and order, rather than merely trusting twelve IDs from JSON. They cover a positive gap, lower-window clipping, excluded full-pairing cardinalities, total infeasibility, K=0, H=0, f=0, an upper support boundary, a singleton load, zero-fee assignment ties and a flat-price response continuum. The first exact arithmetic smoke anchor agrees with the separately hand-derived heterogeneous example.

There are exactly24 negative controls: eleven analytical/result mutations, two reduced-power checks against an unchanged serial witness, one removed terminal charge, and ten invalid-domain calls across both implementations. Their intended failures are substantive. The label mutation changes the association between heterogeneous services; the allocation mutation removes the actual optimum allocation; fake upper clipping invents an infeasible cardinality; collapse-flat-response erases genuine interval responses. Reducing K/H under the fixed witness rejects its excessive power, not a claim that the newly reduced-power physical problem is infeasible. The smoke check is additional to the24 controls.

**Coverage limitation, not a detected source error:** every current literal has at most one positive matching-threshold increment. Thus this finite qualification does not directly exercise successive positive frontier slopes or a physical intermediate threshold lying inside a merged collinear hull face. It also does not directly place a supported optimum at L strictly between original r thresholds: the three-batch clipped-boundary case reaches its upper threshold. The source logic handles these cases and the proof covers them, but the twelve-state qualification should not claim they were tested. Parent may strengthen the prospective literals before freeze; I did not change them. For a future targeted literal, three15-energy services in each batch have thresholds0,10,20,30; fee20/3 makes E=20 a physical optimum on their collinear frontier under adequate K/H, explicitly testing why intermediate thresholds must be retained.

## Owner robustness correction made in this new namespace

The original owner parsed results.json without exception handling. If the worker was killed during JSON publication, a partial file could exist and the owner would raise before writing its receipt or preserving the twelve assigned states.

I changed only this package's `run.py`:

* added the twelve source-defined IDs;
* guarded result reading and validated complete unique assigned IDs and recognized row statuses;
* retained an explicit read error and twelve `UNKNOWN_UNREPORTED` administrative states when no complete report exists, never inferring unattempted work after abrupt loss;
* tolerated the race where a child exits between polling and process-group kill.

No scientific code, literal, or frozen public source was edited. The new owner version therefore belongs in the parent's eventual source freeze.

## Resources and dispatch

The proposed owner/worker declarations agree: new60CPU/90wall package, worker40 self-CPU ceiling plus observed45 inclusive CPU/60wall and512MiB, owner5soft/50hard CPU,60wall child wait,87wall observation boundary with3seconds cleanup. Source Git calls are serial and counted within the worker/owner. The worker runs only cached source bytes after frozen-revision comparison and hash-on-consumption, with isolated stdlib Python and assertions enabled. Full external metering remains authoritative for startup, shutdown and publication.

These are observed gates and practical containment, not an OS-enforced instantaneous memory or aggregate package-CPU ceiling. Whether exact Fraction work and publication fit the proposed limits remains an execution question; source review cannot establish it. No automatic retry or result-selected replacement is authorized. The only supplied control is explicitly DRAFT and has no source revision; a separately reviewed FROZEN LAUNCH.json is required for dispatch.

The qualification remains internal exact implementation agreement for a synthetic theorem class. It contributes no public-timetable support conclusion, empirical denominator, algorithmic speedup, external replication or submission-readiness judgment.
