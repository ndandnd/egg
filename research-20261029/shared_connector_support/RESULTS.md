# Fixed shared-connector qualification — CLOSED_PASS

29 October 2026. One fresh `cycle01`, frozen scientific source `28ee0fc651086667a7838191583ef42a48d64097`, control `cbcbdd06`. Owner28200 exited0; worker52303 exited0 and was reaped. The stored master reports14 assigned,14 attempted,14 passed,0 unattempted and no failures. All24 negative controls rejected and the arithmetic smoke check passed.

The fourteen fixed cases contain two positive-gap results, ten feasible zero-gap results and two infeasible results. The complete exact table is [cycle01/TABLE.md](cycle01/TABLE.md). The first positive-gap example retains `D=2681/20`, `CH=434201/3240`, gap `121/3240`; the three-per-batch clipped example has gap `1/15`. No replacement, additional scan or rerun was used.

Two prospective boundary additions close the earlier source-review coverage gaps. Stored fields in both implementations report:

|Case|Physical early energy|Hull early energy|Stored matching thresholds|Stored clipping|D=CH|
|---|---:|---:|---|---|---:|
|collinear-physical-threshold|20|20|0,10,20,30|L=0,U=30|850/3|
|clipped-first-edge-lower-boundary|5|5|0,0,0,8|L=5,U=10|425/3|

Thus the collinear case physically attains its intermediate threshold E20 rather than treating the interior of a merged face as necessarily unsupported. The clipped case physically attains E5=L, although5 is absent from its original matching thresholds. The stored physical optimum records have zero regret in both cases. These statements project existing result fields; no calculation or witness replay was repeated for this readout.

The reference exhausts partial crossmatchings, raw per-bus SOC polytopes and single-connector serial witnesses. The analytical candidate uses sorted matching thresholds and the clipped cost frontier. The comparison includes complete assignment intervals, optimal labels, prices/regrets, individual allocation continua and flat-response continua. Agreement qualifies these implementations for the declared synthetic class; continuous-domain claims rely on the proof.

Final package meter:3.39 displayed CPU seconds,3.48 wall seconds,3.41 retained CPU seconds; observed peak RSS58,163,200 bytes. All resource gates passed. Worker and owner measurements overlap this package and are not added again. The parent's separate figure-v2 work (.48 CPU,.63wall,.50retained CPU) is explicitly outside the package.

This is distinct from the earlier eight-case adequate-resource/n-connector qualification. Neither run is an empirical fleet cohort, external replication, speedup demonstration or public-timetable support certificate. Resource details and interpretation are recorded separately in this namespace.
