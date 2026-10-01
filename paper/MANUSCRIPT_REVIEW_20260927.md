# Manuscript and visual review — working draft 0.1

Reviewed on 27 September 2026. Scope: scientific framing, definitions, clarity,
likely journal objections, all three figure PNGs, and every page of the
10-page PDF. This reviewer authored the reuse-frontier implementation and
interpretation: **Section 7 checks below are author consistency checks, not
independent verification.** The exact cyclic construction has a separate
non-author audit reported as PASS; this review does not replace that audit.
No manuscript, renderer, figure, protocol or raw result was edited here.

## Review verdict

The draft has a coherent, inspectable analytical core and is appropriately
labeled a working manuscript rather than submission-ready. Its strongest
features are complete-schedule opportunity sets, explicit full replenishment,
component-wise shared-capacity feasibility, separation of own-price regret
from common-price participant LOC, and preservation of the unsuccessful
numerical cell. No contradiction in the stated cyclic construction was found
in this manuscript reading. Its main journal vulnerability is contribution
and operational relevance, not an uncovered counterexample arithmetic error.
The draft itself correctly acknowledges that a qualified timetable study and
defensible economic interpretation are still missing.

## Prioritized corrections that fit the current scope

### P1 — Specify the supply opportunity domain before using its conjugate

Section 3 assumes F is defined on a neighborhood of the feasible load hull.
Section 4 then defines F*(p) by a supremum over **all** nonnegative loads. That
supremum is not defined by the stated local-domain assumption, and its finiteness
is not guaranteed. This is a formal assumption gap in the general accounting
paragraph, not an identified error in the specific quadratic example.

Concrete repair: define the supplier's convex feasible domain explicitly and
assume the corresponding proper closed convex cost on that domain, or strengthen
the stated model to a globally defined convex cost on the nonnegative orthant.
Condition finite LOC statements on finite F*(p); identify the regularity/strong
duality premise where the dual-optimal-price identity is used. Preserve the
weaker local assumptions where sufficient for Proposition 1 if desired. The
parent has acknowledged this correction and is editing it.

### P1 — Define the ambient two-period supply cost, not only its restriction

Section 5 defines G(x)=4x+[x²+(30−x)²]/10 along the fixed-energy line, then reports
two distinct marginal prices and an orthant supply conjugate. G determines
the **difference** between the period prices along that line; it does not by
itself specify both prices or the supplier's full opportunity set.

Concrete repair: state F(e_early,e_terminal)=a*e_early+
(e_early²+e_terminal²)/10 on the chosen nonnegative domain, with a=4 in the
central example, and then define G(x)=F(x,30−x). This makes the quoted gradients,
conjugate and price-dependent LOC reproducible from the manuscript alone.
The parent has acknowledged this correction and is editing it.

### P2 — Handle the lambda=1 endpoint in the constructive hull proof

The sufficient mixture construction uses (x−10lambda)/(1−lambda), which is
undefined at lambda=1 even though that endpoint belongs to the displayed hull.
The intended result is correct: lambda=1 forces x=10 and is the physical
one-bus point. Add that one-sentence boundary case, and apply the formula only
for lambda<1. This needs no new experiment or theorem.

### P2 — Make the classical result's attribution and contribution boundary local

The introduction already avoids claiming a new convex-hull-pricing principle.
Maintain that restraint at Proposition 1 by explicitly calling it a fleet
specialization/corollary of the convexification/duality perspective in the cited
literature. Cite the relevant foundational references immediately beside its
setup rather than expecting readers to carry Section 2 forward. Do not claim
that a focused 11-paper review proves the replenished fleet construction is
the first of its kind.

The targeted primary-source check confirmed that Madani et al. already study
nonconvex **demand** bids and compare classical price rules with computational
and economic examples; the mere presence of demand-side nonconvexity is therefore
not the paper's novelty. The current fleet interpretation and replenishment
accounting are the defensible narrower contribution. [Madani et al., inspected
arXiv v1](https://arxiv.org/abs/1804.00048v1). The Andrianesis DOI could not be
retrieved in this particular spot-check, so this review makes no new claim
based on its inaccessible full text and relies on the existing source matrix.

### P2 — Integrate the completed audit status and trace caveat when available

The reviewed snapshot still says the reuse audit is being completed. Once the
independent reviewer finishes, replace that status with its exact supported
scope, and mention the logging-only snapshot repair in reproducibility. The
original 7d3d764 result must retain its identity. Explain that the old trace's
solved tangent sets were reconstructed and audited, if and only if that audit
passes; do not imply that a prospective deepcopy repair changed historical
outputs or that all 45 cells passed.

### P2 — Add one compact matched accounting summary for the reuse diagnostic

The existing by-state call table is accurate and displays the failed cell.
For a reviewer assessing acceleration, add either a short sentence or a compact
supplement table with complete cell time, all attempted cost and a clearly
labeled matched successful subset. Available numbers already verified by the
author-side descriptive reporter are:

| View | Cold | Retained | Retained + shift |
|---|---:|---:|---:|
| All attempted pricing calls | 123 | 44 | 56 |
| Certified/reference-checked cells | 14/15 | 15/15 | 15/15 |
| All complete cell seconds | 99.593 | 28.062 | 31.881 |
| Calls at 14 jointly successful fixture-state keys | 116 | 43 | 54 |
| Complete seconds at those same 14 keys | 78.506 | 27.656 | 31.375 |

The failed cold cell alone costs 7 attempts and 21.088 seconds. These are
single-run descriptive totals, not a generalized speedup estimate; success
conditioning must remain explicit. The latest reviewed PDF already includes
the important 24-call always-propose floor versus 17 retained warm calls and
correctly says a selective/cheap proposal would be a different architecture.
Three projected proposals are novel, all in the replenished fixture, but none
reduces clean-call counts; that is a useful one-sentence distinction between
novelty and utility. This recommendation is an **author consistency check**.

## Cyclic assumptions and economic interpretation

The one-bus trajectory respects the stated battery capacity and finishes full:
20→5→15→0→20 kWh. The two-bus family buys 30 kWh in total, with each used bus
restored. The early and terminal charging bounds are imposed within each
physical component. At least enough connectors, constant/lossless charging,
zero reserve, no deadheads and no auxiliaries are explicit. The projected hull
and its supporting mixture therefore do not depend on an extra vehicle donating
net initial energy. Keep these details in the main text; they answer a material
reviewer objection to depleted-horizon examples.

The native terminal recharge window in Section 5 is clearly distinguished from
the simultaneous-marker construction in Section 7. Preserve that distinction.
The latter is fixed at two buses and may include a marker-only idle chain; it
cannot be used as evidence for the former variable-fleet cyclic mechanism.

The price-taking deviation keeps the posted price fixed, which is stated
correctly. A fleet being a best response at the common hull price does not by
itself eliminate supplier LOC or produce implementable market clearing. The
text handles that distinction well. Likewise, the mean-load cost 94.8875 and
randomized physical cost 99.275 answer different questions; the manuscript
rightly reports both rather than interpreting the hull as a deployable
fractional bus or as an average realized daily cost.

The current title is defensible because the introduction specifies own-load
marginal-price support. The paper should continue to avoid broader suggestions
that **no** price can make the physical optimum a fleet best response: its own
example shows fleet LOC zero at the hull price. The missing supply-side support
is central to that distinction.

## Likely major journal objections, without adding new scope

1. **What remains beyond known nonconvex pricing theory?** The current answer
   is an exact fleet-specific replenished construction plus audit-ready physical
   and accounting distinctions. Make that answer concrete in one contribution
   paragraph. Do not sell the generic inequality as a new welfare result.
2. **How relevant is this to bus operations?** The current draft has no
   operational outcome. Its qualified statement of the pending timetable study
   is appropriate; the manuscript cannot be called an excellent submission
   draft until the already-planned empirical evidence is supplied or the paper
   is explicitly positioned as a narrow analytical note.
3. **What is the economic curvature?** Demand charges, exogenous tariffs,
   incremental supply costs and charger scarcity rents are different. Section 8
   already says so. Keep synthetic monetary units and explain the ambient F,
   rather than interpreting a stylized tariff coefficient as calibrated market
   supply elasticity.
4. **Why is the reuse experiment part of the same paper?** Add a bridging
   sentence: repeated certified hull/pricing calculations motivate reuse, and
   the diagnostic is a baseline/negative result rather than a second claimed
   methodological breakthrough. The existing Section 7 can remain compact,
   with detailed software qualification moved to the supplement later.
5. **Can the results be independently reproduced?** The exact and numerical
   evidence streams have different guarantees. Preserve their distinct audit
   descriptions, source commits and failure rules; an independent exact audit
   does not certify the entire EVSP production adapter or the numerical driver.

## PDF and figure QA

The complete reviewed snapshot is 504,953 bytes, 10 pages, SHA-256
`1dd32627352486f208be8fdff161b2e1ec02f5d3bd57d7cf9e396d87e8b91826`.
It passes strict pypdf parsing and all page text extracts. All ten pages were
visually inspected from an in-memory PDFium render, stored as
`manuscript-qa/latest-page-01.png` through `latest-page-10.png`. Earlier Poppler
renders under `page-*.png` can include the preceding revision: the file changed
while that first rendering was running, causing transient parser warnings.
Use only the hashed in-memory snapshot for this review's layout findings.

No clipped text, colliding objects, broken table, black-square glyphs, missing
figure labels or orphan **headings** were found. Page numbers, footer lines,
reference links and figure/caption associations are consistent. The table on
page 8 remains within its columns; the long fixed-two-bus label fits.

Concrete refinements:

- **Page 4 begins with a one-line paragraph remainder** (“formal exact-arithmetic
  certificates.”). Apply a widow/orphan rule or keep the short bounds paragraph
  together. Page 4 also leaves a substantial blank region before Figure 1 on
  page 5; a slightly smaller SOC panel or modest repagination can improve flow
  without detaching its caption.
- **Equations on pages 3–6 are dense ASCII prose.** Display the proposition,
  bound interval, conjugate and principal quadratic equations using proper
  subscripts/superscripts and mathematical symbols. This is readability, not
  just decoration: `L_D-U_CH`, `p_s`, `>=` and `^2` slow technical review.
- **Figure 2 is readable but its in-panel legend and annotations are small at
  printed width.** A modest label increase would help. The two color channels
  are sufficiently distinct, and the special physical/hull markers help retain
  meaning beyond color alone.
- **Figure 3 annotations are rounded despite exact underlying calculations.**
  Add “labels rounded; exact rational values archived” to its caption, or use a
  consistent decimal convention. This prevents 2.11 from looking inconsistent
  with the main result 2.1125. The heatmap itself is legible and includes all
  declared zero cases; its cell layout should be understood as a categorical
  grid, not continuously interpolated parameter spacing.
- **Subtitle terminology:** “Complete-duty certificates” can suggest a master
  of individual bus duties, precisely the relaxation the body distinguishes
  from complete fleet schedules. “Complete-fleet certificates” or
  “Complete-schedule certificates” would align the title with the model.

The parent is editing the mathematical premises, typography and pagination.
**A final rendered QA pass is still required on the new final PDF hash.** The
findings above apply only to the identified snapshot, not to unseen revisions.

## Final candidate QA addendum — reviewed after corrections

**Verdict: PASS for sharing/backing up working draft 0.1.** This is a document
and scoped scientific-consistency verdict, not a claim of journal readiness.
The outstanding operational-evidence and contribution-positioning limits above
remain appropriate future work; none of the previously identified immediate
corrections requires holding this working draft.

Final inspected PDF SHA-256:
`a5b4c9c9754d5a5620704ee8622cea26ca5eef25fdf0c6359677b086615e699a`.
It is 587,066 bytes and 11 pages. The SHA was asserted before rendering, strict
pypdf parsing succeeded, every page extracted text, and all 11 pages were
visually inspected from an in-memory PDFium render. QA images are
`manuscript-qa/final-page-01.png` through `final-page-11.png`.

Confirmed corrections:

- The global nonnegative supplier domain and finite-conjugate premise are now
  stated, with the local assumptions needed for price support distinguished.
- The two-period ambient quadratic F is explicit before the price/LOC example.
- The lambda=1 mixture endpoint is handled separately.
- The subtitle now says complete-fleet, and the proposition explicitly cites
  the classical convexification/duality perspective without a novelty claim.
- Displayed equations are clear and contain the correct inequality directions,
  interval endpoints, accounting sign, objective values and completed square.
- Heatmap rounding and categorical grid interpretation are now explicit.
- The matched success-conditioned call/time summary and separate failed cost
  agree with the author-side reuse report. The 24-versus-17 architecture
  argument retains the correct limited interpretation.
- Reproducibility reports the completed independent 44-successful-cell audit,
  the preserved failure, recoverable legacy tangent-log issue and prospective
  repair without suggesting that old results were replaced. This review does
  not recast the reuse section as an independent review by its author.

The final rendering has no clipping, object overlaps, broken tables, missing
glyphs, detached figure captions or orphan headings. The prior one-line bounds
paragraph remainder is gone. The three figures remain legible; equations and
subscripts are substantially clearer. The pricing table fits its columns and
stays with its caption. References continue onto page 11 without splitting an
individual entry across the page break. Page numbers and footers correctly
show 1/11 through 11/11. The short final reference page is acceptable for this
working draft and is not a blocking defect.

No manuscript, rendering source, figure or raw research artifact was modified
by this review. Only this note and its QA renders were written.

## Principal-researcher layout check — working draft 0.2

The 27 September version 0.2 PDF is 14 pages, 927,910 bytes, SHA-256
`1cf8ed050ad5b6d142353996eb299c6d9578a92d7f1f3cd320ed5c08e9af4697`.
The principal researcher rendered a fixed in-memory PDFium snapshot, inspected
all 14 page layouts and all five figures, and corrected the small reuse table
so its three rows and caption remain together. The final affected pages were
re-rendered and re-inspected. No clipped content, detached captions, unreadable
mathematical glyphs or orphan headings remain. All-page images and the checked
PDF identity are retained locally in `research-20260927/agent-notes/manuscript-qa-v02`.

This is author layout/consistency QA, not an independent review of the newly
written prose. The underlying robustness and replication results have separate
non-author exact audits; their claims preserve changed-hardware, zero-switching,
whole-operator, tie and normalization qualifications. Version 0.2 is ready for
working-draft sharing/backups. It is not submission-ready: native-model
qualification, source-faithful operational evidence and a final independent
manuscript review remain open.
