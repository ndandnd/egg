# EGG working manuscript

`manuscript.md` is the editable scientific draft. `CLAIM_EVIDENCE_LEDGER.md`
tracks what is established and what remains. `related-work/` contains source
checks and BibTeX. `figures/` contains PNG, SVG and vector PDF exports plus
provenance. `../output/pdf/egg-journal-working-draft.pdf` is the review copy.
The reviewed PDF is version 0.3: 17 pages, six figures, SHA-256
`fac524aff668c2c1d81d027bf67a74894ad943953bf0638ca09d0ab51d035500`.
`MANUSCRIPT_V03_LAYOUT_REVIEW_20260927.md` records the independent all-page
layout check. This working draft includes native-model qualification, public
source intake and explicit participant normalization. Public economic evidence
and final whole-manuscript scientific review remain open.

Reproduce figures with Python, NumPy and Matplotlib:

```sh
python paper/make_figures.py
python paper/make_extension_figures.py
python paper/make_public_case_figure.py
```

The first script builds the three original cyclic figures and manuscript
equation images. The extension script reads the immutable robustness and
replication results, writes `cyclic_robustness` and `cyclic_replication` in
PNG/SVG/PDF, and records input/script hashes in
`figures/extension_provenance.json`. It displays all 16 robustness cases and
the first 80 of the 86 prospectively declared replication sizes, retaining
both planner optima at ties. Neither script runs a scientific optimizer.

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

The two exact cyclic extensions also have portable, non-author audits:

```sh
python result/cyclic_robustness/20260927-attempt1/review/independent_robustness_audit.py \
  --repo . --result result/cyclic_robustness/20260927-attempt1/results.json \
  --report NEW_ROBUSTNESS_REPORT.json

python -B result/cyclic_replication/20260927-attempt1/review/audit_cyclic_replication.py \
  --repository . --result result/cyclic_replication/20260927-attempt1/results.json \
  --out /tmp/NEW_REPLICATION_REPORT.json
```

Use new output paths (replication rejects outputs inside any Git repository) and retain the corresponding frozen Git commits:

| Artifact | Frozen source/protocol | Raw result SHA-256 |
|---|---|---|
| `cyclic_robustness/20260927-attempt1/results.json` | `bd022ac32ef680446ee17bc4400843a764acb9f6` | `3d5c20a39b2c7176b6ece22bbeb464a42ea7b3bc58498c0959e227469e25ed29` |
| `cyclic_replication/20260927-attempt1/results.json` | `ce84e9e62b8e3f33d32010d381fd845415eff458` | `87523bcad8cdb8a3a3383391a6db42566e83498a85da547a184b8218b69cfb1a` |

Paths in this table are relative to `../result/`. Robustness needs Python 3.10
or later; replication needs Python 3.8 or later. Both use the standard library
and Git, with no solver dependency. Their review directories contain detailed
scope reports and separate derived manifests; raw output/manifests remain
unchanged. Robustness's canonical report is `independent-audit-v2.json`
(22 corruption controls), and replication's is `audit-result.json`
(21 controls). These are exact synthetic constructions, not native-model or
operational qualification.

`MANUSCRIPT_REVIEW_20260927.md` records version 0.1's reviewed 11-page PDF hash
and visual QA. Its appended principal-researcher check records the 14-page version 0.2 PDF hash and all-page layout review. The original reviewer authored
the reuse experiment and declares that conflict;
the cyclic and reuse artifact audits above were performed by a non-author.
The manuscript remains a working draft pending credible timetable evidence and
renewed manuscript/visual review. Native recharge qualification passed all 15
controls on corrected CBC V2 and the identical GRB replication; each has an
independent raw-variable, physical-witness and bound audit. First CBC attempt1
remains FAILED 12/15. See the corresponding `result/native_recharge/` reviews.
GRB licensing stdout is retained only in the complete external original archive;
its public access note and manifest disclose all omissions. The separate
the half-minute and compact physical gates have passed independent result audits.
The corrected native hull gate returned eight certificates and is under independent
result review; its original failed attempt remains preserved. The public pricing
pilot is separately reviewed and frozen before execution.
The excellent-first-draft goal is active and incomplete.
