# doc

LaTeX write-ups, papers, thesis chapters, and presentations.

Conventions (to adopt when the first document lands):
- One subdirectory per document (e.g. `doc/paper-damping-is-stabilization/`),
  each self-contained with its own `main.tex` and `Makefile`/`latexmk` setup.
- Bibliographies draw on `ref/papers.csv`; cite only works whose evidence
  tier permits it (full-text audited for substantive claims).
- Generated PDFs are not committed; figures/tables are imported from
  `result/`, never duplicated here.
