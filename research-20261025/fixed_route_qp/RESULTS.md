# Stronger fixed-route charging control: seven witnesses, one materialization failure

The direct convex charging diagnostic completed on all eight saved prior
topologies. All eight native QPs reported OPTIMAL and passed the original-matrix
copy contract; **seven produced timely independently replayed QP plans**. The
last case,50603/80, failed unchanged physical session extraction and retained
its valid prior. Eight operational fallbacks/endpoints are not eight successful
QP witnesses. No case was retried. All original warm outcomes remain unchanged.

| Case | Prior cost | Admitted selected cost | QP physical witness | Inclusive elapsed (s) |
|---|---:|---:|---|---:|
|50600/40|783.989505|714.952629|yes|1.636|
|50600/80|1297.417389|1191.664722|yes|10.969|
|50601/40|737.717768|685.050909|yes|1.532|
|50601/80|1328.145350|1256.373180|yes|11.097|
|50602/40|1008.081471|941.241584|yes|1.463|
|50602/80|1258.306152|1221.736689|yes|10.275|
|50603/40|836.090355|763.838408|yes|1.610|
|50603/80|1422.677973|1422.677973|no; prior retained|10.964|

Costs are the original integrated system cost with the same fixed prior routes,
fleet and physical matrix. This is conditional charging optimization, not an
unrestricted EVSP certificate. Numerical OPTIMAL status is not an exact physical
certificate; independent replay is a separate admission check. A different
backend/procedure and unequal realized runtimes prohibit a clean speedup claim.

## What this changes scientifically

The stronger admitted QP candidates beat every corresponding capped four-round
charging endpoint in the seven cases (21 old seed comparisons). But their
complete-group median gains over the capped control are only0.09885%,0.07694%
and0.15976% of prior late electricity E0 for50600,50601,50602. Missing50603/80
means no complete all-eight candidate mean is reported. Do not hide it by using
the raw native objective or an available-only aggregate.

Every admitted QP candidate is still more expensive than each corresponding
old GNN endpoint. This does not establish a learning or tariff-information
mechanism: the QP fixes the common prior's route topology, whereas GNN can
change connections. The saved energy summaries show that QP keeps almost the
same total energy as the prior, while GNN uses less. A new compact energy
diagnostic relative to both classical routing controls is therefore warranted
before interpreting the larger fixed-route contrast. The modest frozen
GNN–CoverCA1 result remains the relevant learning-versus-competent-control signal.

The operational QP pipeline's24 repeated comparisons include the failed last
case's prior; its apparent GNN advantage of13.4222%E0 is inflated by that failure.
It is **not** a new headline ML gain. Four base groups remain the independent
group units; one QP seed17 witness is reused against three old GNN seeds.

## Failures, provenance and next decision

Attempt01 failed before optimize on the combined bound/index/type readback.
V2's bounded examples show source upper1e100 versus public API readbackinf,
with equivalent documented unbounded semantics. The v1 receipt did not identify
its first offender. All finite bounds, stored rows/objective and original replay
guards remained unchanged; no LP/MPS roundtrip or private CFFI patch was used.

The last v2 QP's numerical objective1299.011935736556 is NOT an admitted plan
cost. The serial session decoder rejected coincident rounded endpoints while
materializing positive charges. The particular interval/energy is unidentified;
there is no basis for calling it negligible or erasing it. See
EXTRACTION_FAILURE_DIAGNOSIS.md. A separately frozen Method0 primal-QP mechanism
check is a possible next design, not a cleared retry or guaranteed remedy.

The prepared broad replication stays HELD. Resolve the conventional-control
admission issue and examine energy differences before a new study manifest.
Do not change completed outcomes, refit models or expand solver time blindly.

Read analysis.json for exact rational outputs and full denominators; DISPLAY.json
is a rounded display derived from that same frozen readout using BigInt rational
scaling, not a second experiment. Analysis executed once, with no solver, model,
replay, hashing or raw-capture activity. Source/static reviews and failure records
are preserved alongside both attempts.
