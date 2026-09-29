# LaTeX manuscript

`main.tex` builds research draft0.8. The reviewed PDF is
`output/pdf/egg-journal-v0.8-reviewed-draft.pdf`. It has17pages,3figures,2tables
and18references. Both markets use the strongest reviewed public bounds; the
exact undamped price cycle replaces the historical flat-price witness figure.
The historical v0.7 development supplement and all prior reviewed PDFs remain
preserved. The new sources/review/QA are in `research-20260929/review-response-v08/`.

Compile from this directory with an existing output folder:

```sh
tectonic --keep-logs --outdir ../../tmp/pdfs/review-v08 main.tex
```

Reproduce the availability floors, merged table and exact cycle from repo root:

```sh
python3 research-20260929/charging-availability-bound/compute.py
python3 research-20260929/review-response-v08/build_joint_table.py
python3 paper/make_cyclic_price_update.py
```

The reporting-only availability calculation makes no native optimization call.
Its proof and independent check are in `research-20260929/charging-availability-bound/`.
Native upper witnesses remain conditional on feasibility for the ideal model,
except the separately reviewed exact depot-15 original-market upper witness.
The accompanying new six-cell economic experiment has its own frozen source,
protocol and receipts; its results are not assumed by this manuscript release.
