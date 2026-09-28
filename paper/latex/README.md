# LaTeX manuscript

`main.tex` builds the current integrated research draft 0.6. The delivered
19-page PDF is `output/pdf/egg-journal-v0.6-computational-draft.pdf` at repository
root. It includes five figures, four tables, twelve cited references and a
149-word abstract. Source maps, independent reviews, presentation QA and artifact
hashes are in `research-20260928/manuscript-integration/`.

From this directory, compile into an existing output directory:

```sh
tectonic --keep-logs --outdir ../../output/pdf main.tex
```

This produces `main.pdf`; the reviewed release uses the versioned name above.
`model_theory.tex`, `exact_results.tex`, `public_case.tex`, `related_work.tex`
and `proof_appendix.tex` hold the new integrated material. The previously
reviewed `computational_results.tex` is included unchanged. Its standalone
`computational_review.tex` and six-page PDF remain available.

Regenerate computational figures from repository root, using Python with
Matplotlib, only if the figure sources change:

```sh
python paper/latex/build_computational_figures.py
```

The other three figures reuse reviewed vector exports in `paper/figures/`.
The historical Markdown v0.5, its PDF and release pins remain untouched.
This integrated first draft is a review milestone; public global gaps remain
open, retrieval and learned methods remain untested, and it is not a journal
submission.
