# Fifth focused-draft PDF snapshot — prospective artifact freeze

Scientific TeX/Bib/figure source is
756871f6ba2609a3a9e918bbf8f196f8eadcbc6a. New material comprises the
independently reviewed exact-law public certificate and value-preservation
proof, common/edge-varying transition boundaries, complete-graph positive-gap
construction, focused primary-source updates and visually admitted analytical
figure. This is an internal research draft, not submission-ready. No scientific
computation, certificate replay or old source audit is repeated.

NEW120CPU/180wall inclusive for one compile and one110dpi rendering. Each
command has selfCPU60 and inherited90-second wall alarm, external POSIX meter,
exclusive logs and a fresh output directory. Parent closes exact sessions
and preserves failures; no automatic rerun. The earlier PDF artifact marker
already applies and is not repeated. Tool/static/visualQA CPU is UNKNOWN.
Configured numerical-library threads1; no scientific native solver call.

Compile cwd paper/focused-theory-20261029, exact shell command:

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir ../../output/pdf/focused-theory-20261029-v5 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /opt/homebrew/bin/tectonic --keep-logs --outdir ../../output/pdf/focused-theory-20261029-v5 main.tex' > compile05-console.txt 2> compile05-time.txt
```

Only after compile exit0, render cwd repository root:

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir tmp/pdfs/focused-theory-20261029-v5 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 output/pdf/focused-theory-20261029-v5/main.pdf tmp/pdfs/focused-theory-20261029-v5/page' > paper/focused-theory-20261029/render05-console.txt 2> paper/focused-theory-20261029/render05-time.txt
```

Every rendered page must be visually inspected. Specific material defects get
repairs and a fresh separately metered snapshot, preserving this one. Closed
prefix23981.10displayedCPU/24914.07elapsed-sum/23982.84retainedCPU. External
meters are adopted once; no nested observation is added. Legacyguard unchanged.
Parent control review PASS: reviewed source, artifact-only inputs, exact two
commands/fresh outputs and inclusive funding bound before dispatch.
