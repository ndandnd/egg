# doc

LaTeX write-ups, papers, thesis chapters, and presentations.

Project operations and evidence:

- [`ENGINEERING_INCIDENTS.md`](ENGINEERING_INCIDENTS.md) is the durable
  bug/incident ledger: symptoms, root causes, prevention invariants,
  regression coverage, and scientific handling.
- [`DECISION_LOG.md`](DECISION_LOG.md) records research decisions and their
  evidence.
- [`UNICORN_RUNBOOK.md`](UNICORN_RUNBOOK.md) records cluster procedures and
  recovery commands.

The incident ledger is authoritative about repair status: a procedure or test
described in the runbook is not production-ready while its incident remains
**FOUND — IN PROGRESS**.

Conventions (to adopt when the first document lands):
- One subdirectory per document (e.g. `doc/paper-damping-is-stabilization/`),
  each self-contained with its own `main.tex` and `Makefile`/`latexmk` setup.
- Bibliographies draw on `ref/papers.csv`; cite only works whose evidence
  tier permits it (full-text audited for substantive claims).
- Generated PDFs are not committed; figures/tables are imported from
  `result/`, never duplicated here.
