# Draft 0.10 release — 29 September 2026

Final artifact: `output/pdf/egg-journal-v0.10-coauthor-draft.pdf`.
SHA256: `fefb6f1488fe4478bd1403197247e96964ad3fe97f095290aeccd3598b4ad7d7`. 23 pages, five figures, three tables; abstract 147 words.
Status: suitable for coauthor discussion, not a submission-ready computational paper.
Public-timetable optimal-fleet support remains unresolved. All earlier PDFs remain.

## Accepted changes and qualifications

- Section 5.2 distinguishes column-generation computation from dual coordination.
  Same-model archive: three pricing calls, including initialization; final interval
  about 1e-6 wide under global tolerance 1e-4 and pool tolerance 1e-6. The analytic
  run's best error is 1.21877605e-6, first reached at call 10,356 and retained at
  20,000. It never crossed the strict 1e-6 target. No matched runtime claim.
- A two-row table separates own-load marginal-tariff reset from supply-demand
  imbalance updates. Neither is silently presented as the other.
- New appendix proof establishes weighted cost/load convergence for the actual
  quadratic recurrence with alpha=.5/sqrt(k). Weighted one-bus frequency tends
  to .675; both bus-count responses recur infinitely often. Finite-run value .6603
  remains unchanged. LPS1999 and Gustavsson et al.2015 provide averaging context;
  no square-summable-step theorem is misapplied. AW2009 stays in the review note
  as LP-specific context. Sol independently verified the proof transcription.
- Section 3 adds the minimum-regret corollary at a hull-optimal load. The price
  set must be marginal prices and contain an attained hull-dual price if restricted.
  The proof is checked independently. This is not an arbitrary-price statement.
- Section 5.3 reports the saved HiGHS endpoint (6,5,5), which fails to support the
  optimal fleet mixture, and the slow/cheap-terminal versus flexible/dearer-terminal
  generator story. No claim that A is cheaper in every hour. Gross generation cost
  is renamed C_gen to distinguish it from fleet excess cost H(x).
- Section 4.1 leads with the proved gap/incentive decoupling and the reserved-pair
  comparison. It does not attribute an absolute-regret bound to Shapley–Folkman or
  claim to derive Alizadeh's network as a continuum limit.
- Abstract, introductory hull explanation, interpretation and evidence map are
  clearer. Luna reviewed the targeted text and evidence. This is an editorial
  assessment, not a 'humanizer' score or certification; no such skill was installed.

## Verification and execution scope

Primary bibliography metadata and the 2015 open article were checked; access
limits for the other averaging papers are recorded in THEORY_AND_AVERAGING.md.
The new argument is written out rather than imported through a broad citation.
The final Tectonic build has no overfull/underfull or undefined-reference warnings.
All 23 pages were inspected in rendered montages; final pages 5, 11, 17, 20 and 21
were inspected at readable resolution after the final edits. The two-row table,
corollary, averaging formulas, figures and references render without clipping.

No new solver, experiment, timing comparison, cluster call or protected outcome
was used. Existing code/tests and result receipts are unchanged. Authoring issues:
an initial text replacement stopped at a failed assertion after earlier file edits;
its remaining replacements were applied against exact current text. A subsequent
editor script used the wrong working directory and failed before changes; it was
rerun in the repository root. An unavailable pdftotext command was replaced by
pypdf extraction. Initial justified table cells caused underfull warnings; ragged
columns resolved them. These were authoring/formatting failures, not solver runs.
