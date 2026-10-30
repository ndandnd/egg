# LaTeX manuscript

`main.tex` builds research draft 0.10 for coauthor discussion. The 23-page PDF is
`output/pdf/egg-journal-v0.10-coauthor-draft.pdf`, with five figures and three tables.
This release separates computation from coordination, proves convergence of the
quadratic iteration's weighted hull average, adds the best-price corollary and
two-institution table, and reports the saved HiGHS price selection. The abstract
has 147 words. Public-timetable support remains unresolved. All earlier PDFs and
the development supplement are preserved. Reviews, citation qualifications and
release QA are in `research-20260929/review-response-v010/`.

Compile from this directory with an existing output folder:

```sh
tectonic --keep-logs --outdir ../../tmp/pdfs/review-v010 main.tex
```

The new exact derivation, LP implementation and reviews are in
`research-20260929/generation-dispatch-pilot/`. The theory, source checks, full
20,000-call analytic trace and release QA are in
`research-20260929/nonsmooth-coordination/`. The trace records current and best
bounds separately. Do not overwrite historical receipts to reproduce a figure.

From the repo root, exact algebra and focused dispatch tests can be checked by:

```sh
python3 research-20260929/generation-dispatch-pilot/exact_certificate.py
PYTHONPATH=src python3 -m pytest -q src/tests/test_convex_dispatch.py
```

The LP pilot now writes a fresh timestamped output, or a new path specified by
`--output`; its protocol and execution log distinguish the discarded two-period
exploration from the reviewed three-consecutive-hour model. These tiny local
checks establish no timetable solver speedup. New cluster comparisons require
a justified formulation and a prospective resource budget.

Historical public availability floors and merged table remain reproducible with
`research-20260929/charging-availability-bound/compute.py` and
`research-20260929/review-response-v08/build_joint_table.py`; the original exact
cycle uses `paper/make_cyclic_price_update.py`. Native upper witnesses remain
conditional on ideal-model feasibility except the separately reviewed exact
depot-15 original-market witness. Later public sensitivity receipts remain in
their own package and are not silently substituted into this manuscript.
