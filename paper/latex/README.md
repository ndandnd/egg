# LaTeX manuscript work

`computational_results.tex` is the reviewed computational chapter, with the
standalone wrapper `computational_review.tex`. The six-page rendered component
is `output/pdf/egg-computational-chapter-20260928.pdf` at repository root.
It contains four tables and two vector figures, using already reviewed scalar
summaries. Evidence and presentation records are in
`research-20260928/manuscript-computational/`.

Regenerate the figures with Python and Matplotlib from repository root:

```sh
python paper/latex/build_computational_figures.py
```

Then compile in this directory, choosing an existing output directory:

```sh
tectonic --keep-logs --outdir ../../output/pdf computational_review.tex
```

The computational chapter requires standard AMS math, graphicx, booktabs and
array support; the standalone wrapper adds float and typography controls.
`main.tex` remains the earlier preliminary outline, and `references.bib` stages
seven core pricing/optimization references. Neither replaces the historical
`paper/manuscript.md` or v0.5 PDF. The next consolidation must integrate the exact
theory, physical/economic model, literature and this chapter into a complete
reviewable paper. No journal submission or publication is authorized here.
