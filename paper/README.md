# EGG working manuscript

The current integrated research draft is **0.6**, built from `latex/main.tex`:
[19-page computational draft](../output/pdf/egg-journal-v0.6-computational-draft.pdf).
It includes five figures, four tables and the reviewed theory/computational
material. See `../research-20260928/manuscript-integration/` for source maps,
reviews and artifact pins. It is ready for author review; broader computational
validation remains needed before journal submission.

## Historical Markdown draft

`manuscript.md` preserves research draft 0.5: 27 pages, eight figures and
five tables in the independently reviewed PDF. Its SHA-256 is
`a97a7f9267d9aa69fdd5d9975bf5282eda47f0aaa10760d270ef86c509f3c88e`.
The reviewed PDF is `../output/pdf/egg-journal-working-draft-v05-reviewed.pdf`
(SHA-256 `8c8192c6259b5294449c655047313f7799ee1aa74092fc669748362bbfdad8eb`).
The byte-identical canonical `../output/pdf/egg-journal-working-draft.pdf` is
ready for expert user review, not journal submission clearance. The release
pins are in `RELEASE_V05_20260927.json`. `CLAIM_EVIDENCE_LEDGER.md` tracks claim scope,
`related-work/` contains source checks and BibTeX, and `figures/` contains
PNG/SVG/vector PDF exports and provenance.

The preserved `../output/pdf/egg-journal-working-draft-v04-reviewed.pdf` is the
historically reviewed version 0.4: 22 pages, seven figures, SHA-256
`acae4e1bc915fdf7e7a4cafcd997b91aa6941afe73a9075b37cb6b50514663ca`.
`MANUSCRIPT_V04_LAYOUT_REVIEW_20260927.md` records its visual and text-integrity
checks. The prior version 0.3 PDF (17 pages, six figures; SHA-256
`fac524aff668c2c1d81d027bf67a74894ad943953bf0638ca09d0ab51d035500`) remains
in Git history. The older version 0.4 R2 pagination candidate is
`../output/pdf/egg-journal-working-draft-v04-r2-candidate.pdf`.

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
both planner optima at ties. Neither script runs a scientific optimizer. Draft
0.5 also uses the audited Figure 8 exports in
`figures/public_nonlinear_evidence.*`; input and audit hashes are in
`figures/public_nonlinear_evidence_provenance.json`.

Render equation images and a separate reviewed working PDF with ReportLab:

```sh
python paper/render_equations.py
python paper/render_manuscript.py --output output/pdf/NEW-v05-review-candidate.pdf
```

The renderer uses locally available DejaVu Serif when found and otherwise
standard PDF Times fonts. Exact pagination can depend on that choice. This
review-PDF generator is not a journal-specific typesetting template. Use an
explicit `--output` path to keep pre-review renders identifiable. Publication
format and authorship will be set once the paper's evidence and destination are
ready.
The final submission has not been made. Use a new output path to preserve both
reviewed versions and the canonical PDF.

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
The public timetable section is now in the editable draft. It distinguishes
exact ideal stored-input evidence from tolerance-qualified native numerical
results. The depot-15 exact rational two-bus witness and one-bus obstruction
prove a minimum fleet of two for that declared finite-block ideal model; its
flat-cost enclosure and analytic nonlinear `CH <= D` enclosure do not identify
an optimum or a positive nonlinear gap. Depot 16 has an exact at-least-two
obstruction and lower bound, but its two-bus upper witness remains numerical.
See `../doc/SISTIG_EXACT_PUBLIC_WITNESS_ADMISSION_20260927.md`,
`../doc/SISTIG_EXACT_NONLINEAR_ENCLOSURE_20260927.md`, and the independently
reconstructed flow certificate under
`../result/sistig_cardinality_flow/20260927-attempt1/review/`.

The compact physical and full-fleet hull controls passed separate independent
CBC and GRB audits (20/20 physical and 8/8 hull on each backend). Figure 7 and
Table 3 preserve the original flat-price public pilot's numerical two-bus
incumbents without claiming cost optimality. Figure 8 and Table 4 report the
independently reconstructed nonlinear attempt 2 **only as an off-protocol
secondary diagnostic**: aggregate hull polishing took 5.190904918592423 s
against the frozen 5.0 s cap. Its signed gap is unresolved at five, and positive
own-price regret belongs only to a named bounded planner incumbent, not an
optimal fleet. Attempt 1's earlier planner-cap failure remains unchanged. See
`../doc/SISTIG_NONLINEAR_V2_SECONDARY_REPORTING_20260927.md` and the public
machine audit at
`../research-20260927/agent-notes/nonlinear-v2-result-review/audit-report-public.json`.
Neither diagnostic establishes a calibrated market effect, operational savings,
recurring daily feasibility, or a protocol-passing nonlinear experiment.

To verify the published copy's exact omission policy without a solver, run this
from the repository root:

```sh
python3 research-20260927/agent-notes/nonlinear-v2-result-review/test_public_copy_mode.py
```

The public copy omits only three complete licensing-only stdout files, as pinned
in `../result/sistig_nonlinear/20260927-attempt2-publication/PUBLIC_MANIFEST.json`.
The 28 other raw-manifest entries, original manifest and wrapper receipt remain
unchanged. The complete private archive is preserved separately. A missing
scientific input fails the public-copy check. Figure 8 is generated only from a
SHA-pinned public audit with numerical PASS, protocol FAIL and an explicit
off-protocol scope argument; its renderer invokes no optimizer and refuses to
overwrite existing exports. The reviewed v0.5 PDF is ready for expert user
review under these stated limitations.
