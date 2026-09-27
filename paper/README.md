# EGG working manuscript

`manuscript.md` is the editable scientific draft. `CLAIM_EVIDENCE_LEDGER.md`
tracks what is established and what remains. `related-work/` contains source
checks and BibTeX. `figures/` contains PNG, SVG and vector PDF exports plus
provenance. `../output/pdf/egg-journal-working-draft.pdf` is the review copy.

Reproduce figures with Python, NumPy and Matplotlib:

```sh
python paper/make_figures.py
```

Render the review copy with ReportLab:

```sh
python paper/render_manuscript.py
```

The renderer uses locally available DejaVu Serif when found and otherwise
standard PDF Times fonts. Exact pagination can depend on that choice. This
review-PDF generator is not a journal-specific typesetting template. Publication
format and authorship will be set once the paper's evidence and destination are
ready. The final submission has not been made.

The exact cyclic audit is independently rerunnable from the repository root:

```sh
python result/cyclic_gap/20260927-attempt1/review/independent_cyclic_audit.py \
  --repo . --result result/cyclic_gap/20260927-attempt1/results.json \
  --report NEW_REPORT.json
```

Keep the frozen7bf913a commit available. Use a new report path; the auditor
refuses to overwrite reports. First-run numerical evidence is immutable; the
later trace snapshot repair does not silently replace it.

The reuse frontier has a separate independent audit of exact rational pricing
and dual bounds, with numerical physical replay. See
`../result/reuse_frontier/20260927-attempt1/review/REVIEW.md` for the portable
command and the reference-bound limitations. That audit preserves the failed
cell and does not repeat any scientific solve.

`MANUSCRIPT_REVIEW_20260927.md` records the final 11-page PDF hash and visual
QA. The reviewer authored the reuse experiment and declares that conflict;
the cyclic and reuse artifact audits above were performed by a non-author.
The manuscript remains a working draft pending qualified operational evidence.
