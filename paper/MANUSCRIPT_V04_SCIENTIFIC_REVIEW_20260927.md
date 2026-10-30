# Referee-style scientific review of manuscript 0.4

27 September 2026. Reviewed source: `paper/manuscript.md`, SHA-256
`bd1a40b56f7a9c35f804eb3d5230b025a2d7b28a28cff3443ac4acc103981060`.
This is a source-level scientific review, not a rendered-PDF or renewed
bibliographic verification. Line references below refer to that snapshot.
No manuscript, optimizer, cluster or raw-result changes were made.

**Assessment:** the central statements are mathematically sound within their
stated assumptions, and the public pilot is reported with appropriate caution.
I found no blocking error in Proposition 1, the quadratic regret-radius bound,
the exact cyclic/robustness formulas or the participant-normalization argument.
The draft is scientifically credible but is not yet an excellent journal first
draft: its central transportation question still lacks a nonlinear timetable
comparison, and its method/evidence presentation remains closer to a research
progress record than a self-contained paper.

**Authorship disclosure.** This reviewer authored native recharge, hull,
synthetic reuse and prospective energy-band work. Sections 6.3, 7 and those
portions of the reproducibility narrative are therefore author-consistency
checks, not independent certification of this reviewer's models or experiments.
The root-authored economic synthesis, propositions, radius bound and replication
interpretation receive an independent mathematical reading here. This reviewer
also performed the separate public-pilot result audit; the present review checks
how the manuscript uses that evidence and does not relabel the same audit as a
second independent validation. Other independent audit reports remain the
appropriate basis for model/result admission.

## Priority 1: make the main transportation evidence answer the main question

Section 8 correctly calls the two public outcomes bounded and avoids savings or
minimum-fleet claims. There is nevertheless an important structural distinction
to state explicitly: **with linear F, the complete physical and convexified
objectives have the same minimum**, because a linear functional has the same
minimum over a set and its convex hull. The flat-price pilot cannot reveal a
positive D-CH even with an exact optimizer. It qualifies input, model and witness
machinery; it is not a weakly powered empirical test of the central mechanism.
The author was notified of this clarification during review.

The already planned common-set nonlinear comparison is consequently the main
remaining research requirement if the paper is pitched as a transportation
study with operational evidence. A minimally interpretable result must pair a
physical objective enclosure with a complete-hull enclosure under the same
predeclared nonlinear F and physical assumptions, then report the gap enclosure
and a physical schedule's own-price regret enclosure. If the gap interval spans
zero, report that outcome; it is still scientifically informative. A stronger
flat-price native bound or exact matching relaxation is useful supporting work,
but does not replace that comparison.

No arbitrary positive curvature should be described as a measured electricity
market effect. The manuscript already distinguishes tariffs, supply costs and
charger rents; preserve that distinction in the eventual scenario table. An
explicitly stylized sensitivity is defensible if the chosen scale and economic
object are stated. It cannot establish operational prevalence or a real savings
amount. No additional datasets or broad benchmark campaign are requested by
this review; close the stated study on the already admitted full timetable.

If computation does not yield useful common-set nonlinear enclosures, the
alternative is a deliberately narrower theoretical mechanism paper with the
public pilot as implementation feasibility evidence. That is a different
submission emphasis, not grounds to overinterpret the current two intervals.

## Priority 1: present the actual certificate method in the paper

The abstract/subtitle promise complete-fleet certificates, but most computational
explanation is currently qualification history. Section 4 defines enclosures
and LOC correctly; Section 6.3 describes the physical implementation in prose;
the detailed hull computation appears mainly in the final reproducibility
paragraph. A reader cannot yet reconstruct the implemented certificate without
following multiple repository documents.

Add a short, self-contained method subsection or algorithm box using the
already established objects. Show the complete-fleet pricing oracle
`q(p)=min_s[c(s)+p·L(s)]`, a replay-valid convex mixture upper value
`cbar+F(Lbar)`, and the fresh lower certificate `q_lower(p)-F_+*(p)`.
State which numerical status/bound information is admitted, how the true upper
is distinguished from a PWL master objective, and why retained columns carry
physical witnesses but never stale bounds. One concise pseudocode loop and an
appendix giving the compact path-flow/SOC/interval formulation would be enough.
The exact stored-number simplex/polishing and numerical physical qualifiers
must remain distinct.

This is a presentation gap, not a request for another algorithm. All necessary
ingredients already exist and have been reviewed. Avoid reproducing every
software repair in the main method section; preserve that history in a clear
reproducibility appendix and immutable artifacts.

## Priority 2: sharpen the paper's contribution hierarchy

The strongest coherent main thread is complete physical schedules → price
support/LOC criterion → replenished continuous-charging counterexample →
reserve/loss/connector robustness → replication and bounded participants →
qualified timetable interpretation. Section 7 is a legitimate development
result, but it currently gives a second computational narrative without a
learning experiment or central transportation result.

Keep its negative finding and full failure accounting, while considering a
short main-text summary and detailed tables/protocol history in an appendix.
Do not present the existence of two or three retained clean calls as evidence
that learning would help. The existing twelve-transition 17-versus-24 call
argument is useful and correctly limited to that proposal architecture.

The abstract has not caught up with the body: it prominently mentions the
45-cell reuse diagnostic but omits the radius upper bound, the reserved-pair
normalization result and the completed public qualification. After the final
study scope is fixed, rewrite it around the actual main contribution and state
what the public study does and does not establish. This is more useful than
adding another claim to the present abstract.

The novelty language is appropriately restrained. The current literature
section distinguishes complete participant schedules from individual duty
columns and avoids claiming an exact-hull empirical benchmark from a source
that does not supply one. This review did not independently reread those
papers and does not certify novelty priority. The final manuscript should
identify the specific new fleet construction/scaling interpretation rather
than treating a familiar duality identity as its principal contribution.

## Priority 2: reduce reporting ambiguity and artifact dependence

- Tables jump from Table 1 to Table 3; no Table 2 appears in this source. Renumber
  after deciding the final section structure.
- Section 8 says a study must “specify directed and time-dependent deadheads.”
  The public matrix is time-independent, while its movement modes have specific
  timestamps. Clarify “state whether travel times are time-dependent and how
  they are modeled,” so timestamped modes are not mistaken for a calibrated
  traffic model.
- The robustness paragraph cites a “supplementary derivation” for an open
  neighborhood without a paper appendix label. Supply a concrete appendix
  reference and the strict inequalities; otherwise an external referee cannot
  check the stronger-than-one-point claim from the manuscript alone.
- The final reproducibility paragraph mixes qualification versions, successful
  results and repaired failures into a long narrative. A compact evidence table
  with question, mathematical/numerical status, fixed design, first-attempt
  outcome and artifact pointer would make it easier to distinguish proof from
  software qualification and timetable outcomes. The complete failure history
  remains available in the supplement.
- The source is labeled draft 0.4 but its last reviewed PDF is 0.3. After source
  corrections, render and inspect the final 0.4 PDF before calling the draft
  ready. This review has not checked clipping, figure legends or page layout.

## Mathematical checks and boundaries

**Proposition 1 (Section 4).** The inequality follows by combining the global
linear response minimum with the supporting plane of F, then minimizing on
the same joint cost/load hull. The converse uses attained physical/hull minima
and a directional first-order condition. The compactness/common-set premises
are doing real work, and the source states them. A best response here holds
price fixed; the manuscript now says so explicitly. No convergence or uniqueness
claim is inferred. At a zero gap every physical planner optimizer is supported,
not merely a favorable chosen tie.

**LOC and supply domain.** The nonnegative-domain conjugate and distinct common
versus own-gradient prices are correct. Convexity gives zero supplier LOC at
an own-gradient price, including boundary loads under the stated smooth
extension. At a dual-optimal hull price the sum of fleet and supplier LOC is
the planning gap for a physical optimizer. The text correctly does not turn
that accounting into funded transfers, truthful bidding or budget balance.

**Quadratic radius bound.** The proof permits singular PSD B and boundary
loads, and H is the cost excess of any physical schedule over CH, not just the
optimal gap. The identity `LOC(s;p*)=H-d²/2` and the comparison with a fixed-price
response give `H<=r<=H-d²/2+dR_B<=H+R_B sqrt(2H)`. A lower hull bound can replace
CH in the increasing loose upper expression only when the physical schedule
and load-radius bound are valid. This independent review previously checked
three adverse finite sets, including nonoptimal schedules, null directions and
zero curvature; those checks are documented separately in
`doc/QUADRATIC_REGRET_RADIUS_ASTRA_REVIEW_20260927.md`.

**Fully replenished counterexample.** The two physical partitions, continuous
early interval and lower hull boundary are consistent. The mixture's expected
physical-day cost 99.275 differs correctly from supply cost at the mean load
94.8875; no daily randomization is sold as a physical convex-hull optimum.
The nominal one-bus point does sit on a binding early-power limit. Section 6.1
acknowledges that reserve/loss can remove it and supplies a separately modified
positive-gap case, rather than silently moving battery capacity.

**Robust intervals.** For r in [0,5], the two-bus early interval is bounded below
by terminal energy capacity and above by early power and A-bus inventory. The
one-bus interval adds the reserve/second-service requirement. Sequential
terminal sessions at a common aggregate rate establish the one-connector
realization. The r=1, eta=19/20, P=12, K=30 example is consistent with the displayed
SOC trace and grid-side units. The claim for terminal sensitivity explicitly
stops at the 30 kW vehicle-acceptance cap. Zero switching time and no taper are
stated limitations, not concealed modeling freedoms.

**Replication and bounded participants.** The scaled B=I/(5n), complete diameter
sqrt(40n), nearest-integer gap 20δ²/n and nonvanishing regret subsequence are
consistent. At tie sizes both optima remain visible. The reserved-pair argument
uses a different explicit institution: each assigned pair has zero LOC at the
common hull price, retains its own charging rights, and has diameter
sqrt(40/n). Thus each regret is at most 20/n while the sum can approach a positive
constant. Bounded participant size alone would not establish that result for
arbitrary allocations or shared-charger games; the manuscript correctly states
the extra rights/price-taking assumptions.

**Public first pilot.** The displayed intervals, two-bus witnesses, modeled
energy, qualification scope and omitted confidential stdout description match
the completed audit. The first-run wide intervals are not replaced by later
strengthening or matching results. It is especially important to keep the
37-bus construction as a deliberately simple feasibility reference rather than
an operational comparison. The native lower bounds remain solver-conditioned;
the independently replayed upper witnesses do not make them exact certificates.

No mathematical repair is requested by this review. The main work remaining
is to close the stated nonlinear timetable question, explain the already
implemented method self-containedly, and turn the evidence history into a
focused journal argument with a freshly verified rendered draft.
