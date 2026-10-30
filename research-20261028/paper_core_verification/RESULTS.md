# Exact capacity/fee cycle — complete

Source2407a28f7773ede756a9b17d87d60ca59163a3e5, frozen control424f3fdb.
The single owner completed exit0; child65741 completed exit0 and was reaped.
No retry, old run replay, native solver, data acquisition or model fitting ran.
All20 assigned cases were attempted and matched exactly; no failure or missing
case. Two were correctly infeasible, twelve had zero gap and six positive gap.
These counts describe a boundary qualification set, not estimated frequencies.
The arithmetic smoke passed and all12 negative controls were rejected: six
deliberate result/witness defects and six invalid-domain calls across the methods.

## What changed and how it was checked

The reproduced baseline is a new independent rational physical formulation:
enumerate both service partitions' SOC-polytope vertices, minimize on continuous
physical segments, and convexify only complete feasible plans. The justified
change replaces enumeration with a closed-form capacity/fee characterization.
Both methods received exactly the same20 predeclared rational cases, cost,
full terminal replenishment, charger model and complete deviation rights.
No sampled charging grid, learned predictor, selected-column restriction,
native tolerance, excluded failure or available-only comparison is involved.

The reference code was separately authored without the candidate's phase
formula; a non-author reviewer inspected both source implementations, proof
and saved outputs. This is an internal independent-formulation check, not an
external replication. Agreement of agents is not proof. The derivation in
PROOF.md supplies the continuous-domain argument; finite checks qualify code.

The nominal baseline reproduces D=97, CH=7591/80, gap169/80 and own-price regret13.
That old fee-7 anchor was already independently audited; this is an explicit
regression anchor in a new implementation, not discovery of the same result.

## Scientific result and limits

For the stated lossless two-service model and 20<K<=30, write l=30-K and
d=K-20. At a strictly positive vehicle fee f, the physical–complete-fleet-hull
gap is positive **if and only if**

    max(0, (2/5)d(l-5)) < f < 2d.

K<20 is infeasible; K=20 and f=0 are handled separately and have zero gap when
feasible. The full physical and hull objectives, all ties and all continuous
posted-price deviations follow the formulas and proof in PROOF.md. This is
a broader within-project characterization than the existing fee-7 threshold,
not a novelty claim for parameterized convexification or pricing theory.

It clarifies the mechanism: charging flexibility and vehicle cost jointly
determine whether nonconvex assignment matters for price support. Increasing
terminal capacity can create a support failure while never increasing optimal
system cost. This does not mean chargers worsen welfare or that the synthetic
tariff is a realistic settlement institution.

An economically relevant tie is retained: at K30/f5 both physical partitions
have system cost95, but their own-price regrets are15 and5. Their own prices
differ; neither scalar selected-plan regret describes all optimal fleets.
At K25/f0, the entire two-bus early-charge interval[5,10] is a posted-price
best response, along with the one-bus plan. Endpoint checks certify the value,
but the output also records the full tied interval. No convenient local-only
deviation restriction is used.

This result strengthens the narrow analytical paper. It does not settle
operational prevalence, calibrated magnitude, public optimal-fleet support,
V2G, strategy-proof settlement or any ML advantage. Those remain absent or
unresolved. The general support/hull theorem remains attributed prior art.

## Artifacts and one known presentation defect

- `cycle01/results.json` is the authoritative complete exact result, including
  baseline/candidate outputs, physical witnesses, all price-response sets and
  corruption outcomes. Fractions are exact numerator/denominator strings.
- `cycle01/source_manifest.json` pins cached sources/configuration and Python
  version; each buffer was hashed once inside the paid execution.
- `cycle01/TABLE.md` was generated inline by verify.py from the same rows.
  Its raw `A|B` labels contain an unescaped Markdown pipe, so rendered columns
  may misalign. This is a presentation defect, not a numeric mismatch. Raw
  output and consumed source remain unchanged. Do not copy that table into a
  manuscript; escape labels in a separately versioned renderer if needed.
- `REVIEW.md` and `INTERPRETATION_REVIEW.md` record source and outcome review.
  Original manuscript/PDFs, historical experiments and Google Doc unchanged.

Whole command cost:0.44displayedCPU/0.74elapsed seconds; retained0.46CPU.
Worker/source/child costs overlap the owner meter and are included once.
Peak observed workerRSS23052288bytes; no native solver or parallel worker.
20CPU/30wall aggregate acceptance passed. Practical per-process limits and
timeouts do not constitute an exact instantaneous aggregate resource guarantee.
See FINAL_RESOURCE_RECEIPT.json for preserved accounting and limitations.
