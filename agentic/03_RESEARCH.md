# 03 — Scientific state and what to do next

## The thesis in one paragraph

`egg` studies price formation for indivisible mobile flexibility: an electric
bus fleet whose mandatory, trip-covering duties make its charging load large
enough to move the electricity price it faces. Posted price -> optimal
trip-covering schedule and charging load -> market price moves -> fleet responds
again. The contribution is not that prices and charging interact (well
occupied), but the combination of mandatory indivisible duties, endogenous
shared price formation, exact/certificate-bearing optimization, and defensible
settlement accounting. Working title: "Price formation for indivisible mobile
flexibility: from benevolent dictator to market."

## Established, on a certified synthetic laboratory

- Naive price-taking tatonnement commonly cycles under moderate/strong price
  impact. At `b=0.05`, zero fixed points across 176 baseline cells; all 49
  undamped cycles had length exactly 2.
- Constant damping usually converts two-cycles into long orbits (median 11-14,
  max 140) rather than reliable convergence.
- Strategic price-making nearly recovers planner welfare (within 3.74 of the
  dictator); price-taking distortion grows sharply with impact (mean/max
  taker-minus-dictator ~25.97/79.8 at `b=0.05`).
- Economically meaningful response discontinuities are often duty changes: 92
  switches in 43/64 sweeps, of which 57 duty and 35 charging-only. 2,559
  degenerate tie changes were excluded -- learning raw schedule hashes would
  mostly learn solver tie-breaking.
- Plain certified column generation (A2) reliably solves the convex-hull
  coordination problem: 256/256 method-cells certified within 240 calls.
- B3 baseline: 38/64 instances certify strictly positive internal uplift
  (`z_D - z_CH`); intervals containing zero mean non-resolution, not absence.

All synthetic. No real-data external-validity claim exists.

## Claims to state carefully

- **Do NOT** claim "first price-making EV fleet" or "first EVSP whose cost
  depends on its own load". Demand charges and peak-load objectives already
  exist in exact EVSP (Wu et al. 2021 TRB and descendants). The defensible claim
  is an exact trip-covering scheduled fleet embedded in shared price formation
  with certificate-bearing coordination and settlement.
- **Scope the stabilization result**: *dense iterative* stabilization (A3-A5)
  loses on total oracle calls *at n in {8,12}*. Gains are known to concentrate
  on large degenerate instances, and learned dual-optimal inequalities with
  exact recovery report 55-83% root-CG time cuts at zero bound loss. A2 itself
  is already a successful certified alternative to tatonnement.
- **Do NOT write "novelty re-verified"**: the 2026-08-20 sweep found no
  collision; canonical ingestion, dimensional scoring and full-text
  verification are pending.
- Anna Scaglione is a **coauthor**. arXiv:2505.04532 (Yao et al., CDC 2025) is
  the nearest neighbour on the endogenous fixed point and a coordination
  bridge, not a threat. Position jointly with her.

## The open niche worth claiming soon

Convex-hull pricing and uplift for an **indivisible demand-side asset** has no
occupant. The 2025-26 pricing frontier (SDP relaxations, European
paradoxical-order strong duality) is explicitly supply-side and treats
demand-side blocks only via sufficient conditions. Our certified internal
uplift for a scheduled fleet is an opportunity; two active vectors could close
it.

## Next experiments, in priority order

1. **Finish the B3 factor pilot decision** (see `02_AFTER_BREAK.md`). The
   population is complete and audited; only the analysis and freeze remain.
2. **The fresh-seed confirmation**, if and only if the frozen decision is GO:
   seeds 32-37, S0 versus the selected factor, 24 contrasts / 48 method-cells,
   gate >= 18/24 direction-consistent zero-excluding and signed median > 0.04.
3. **Market calibration** (no cluster, high value): fit the affine slope `b_t`
   against real published aggregated bid curves. OMIE (Spain/Portugal) is the
   lead: free, no registration, daily `curva_pbc_YYYYMMDD.1` files since 2023
   plus yearly ZIPs back to 2018. Validation is built in -- the reconstructed
   supply/demand intersection must reproduce OMIE's published marginal price.
   Three corrections to earlier guidance: OMIE's Legal Warning is *not* an
   explicit open-data licence, so confirm reuse terms before publishing curve
   excerpts; 15-minute intervals are already live (96 periods/day); and a local
   step-curve slope is neither an OMIE-published value nor the derivative of
   the real clearing model (EUPHEMIA handles block orders a naive fit ignores).
   Treat the calibration as exploratory.
4. **The ML direction** (advisor's request). The consensus architecture is *ML
   proposes, the exact oracle certifies*. Our own measurements agree: a naive
   local-move proposer went 0-for-160 under exact reduced-cost plus replay
   admission, and raw schedule identities carry a 2,559:92 degeneracy ratio.
   Ranked targets: (a) dual-trajectory warm starts across the price loop --
   our loop is textbook parametric reoptimization and the closest published
   work reports ~2x to a *certified* gap; (b) learned pricing-network
   reduction, already demonstrated on multi-depot electric bus scheduling at
   3.5x for 2.2% cost; (c) parametric strategy/support prediction; (d)
   pricing-value regression. Preregister the kill baseline: **reuse the
   previous iterate's duals**. It is free, and an ML method that cannot beat it
   is dead. Labels must be canonicalized (barrier/analytic-centre or averaged
   over the optimal face) and margin-filtered; last-iterate simplex duals are
   the noisiest possible label. Training data would come from a bounded
   cluster tranche using seeds >= 10000 only -- every lower range is committed.
5. **Theory that needs no compute**: the B1 equivalence and minimal cycling
   example (PR #39 already contains a machine-checked strict two-cycle witness
   with load-uniqueness margins -- use it, do not redo it); how integer
   response kinks relate to fixed-point existence; turning B2's negative
   total-call result into a mechanism/overhead story.

## Venue fit

Universal bar: **speedup at unchanged certificate quality**, reported
with-guarantees and without-guarantees separately. INFORMS Journal on Computing
is the best fit for an ML-warm-started certified negotiation paper;
Transportation Science if the EVSP application carries it; EJOR as the
methodological fallback; IEEE TPWRS or Energy Economics for the price-formation
and uplift half, expecting a calibrated market. A machine-learning venue is
only plausible for a generic contribution -- the candidate there is the
degeneracy-robust labelling methodology, since few papers actually *measure*
multiple-optima label noise and we have the 2,559-vs-92 measurement.
