# LaTeX manuscript

`main.tex` builds research draft 0.7. The versioned reviewed PDF is
`output/pdf/egg-journal-v0.7-reviewed-draft.pdf` at repository root.
`development_supplement.tex` builds the separate historical development record,
`output/pdf/egg-journal-v0.7-development-supplement.pdf`. The main draft has
three figures, three tables and fifteen references.

From this directory, compile each wrapper into an existing scratch directory:

```sh
tectonic --keep-logs --outdir ../../tmp/pdfs/review-v07 main.tex
tectonic --keep-logs --outdir ../../tmp/pdfs/review-v07 development_supplement.tex
```

The new `computational_support.tex` and generated `joint_support_table.tex`
report analytical public floors and joint numerical support diagnostics.
Reproduce the new calculations and table from repository root:

```sh
python3 research-20260928/review-response-v07/analytic-bounds/compute_bounds.py --repo . > /tmp/egg-v07-bounds.json
python3 research-20260928/review-response-v07/build_joint_table.py
```

The first command reads frozen metadata and curated scalar evidence without
solving; compare its output with the tracked `analytic-bounds/bounds.json`.
The second generates the table from that tracked JSON. The response folder
contains the source map, derivation, literature checks, independent review,
presentation QA and release hashes.

`computational_results.tex` remains byte-identical to the v0.6 chapter and is
now included only by the development supplement and its historical standalone
wrapper. Old PDFs, figures, Markdown v0.5 and release pins remain untouched.
No new native optimization or cluster allocation produced draft 0.7.
It is an author-review milestone, not journal submission clearance.
