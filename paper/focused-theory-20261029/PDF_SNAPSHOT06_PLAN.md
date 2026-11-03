# Sixth focused-draft PDF snapshot — prospective artifact freeze

Scientific TeX/Bib/figure source is
fdc1faf0a7c8e6993de934d3e5dab41b77f2618d. It adds the independently reviewed
strict-curvature relative-robustness proof, a verified counterexample to a
fractional-cardinality shortcut, focused abstract/introduction and specific
PDF05 editorial repairs. The manuscript remains an internal research draft,
not submission-ready. No scientific computation, certificate replay, old
source audit, figure regeneration or numerical result changes occur.

NEW120CPU/180wall inclusive for one compile and one110dpi rendering. Each
command has selfCPU60 and inherited90-second wall alarm, external POSIX meter,
exclusive logs and a fresh output directory. Parent closes exact sessions
and preserves failures; no automatic rerun. Tool/static/visualQA CPU is UNKNOWN.
Configured numerical-library threads1; no scientific native solver call.
Actual RSS is not inferred from the POSIX meter or a configured resource cap.

Compile cwd paper/focused-theory-20261029, exact shell command:

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir ../../output/pdf/focused-theory-20261029-v6 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /opt/homebrew/bin/tectonic --keep-logs --outdir ../../output/pdf/focused-theory-20261029-v6 main.tex' > compile06-console.txt 2> compile06-time.txt
```

Only after compile exit0, render cwd repository root:

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir tmp/pdfs/focused-theory-20261029-v6 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 output/pdf/focused-theory-20261029-v6/main.pdf tmp/pdfs/focused-theory-20261029-v6/page' > paper/focused-theory-20261029/render06-console.txt 2> paper/focused-theory-20261029/render06-time.txt
```

Inspect every rendered page visually, including the new main remark and final
robustness proof. Specific defects require source repair and a separately
frozen fresh snapshot; preserve this one. Closed prefix23991.22displayedCPU/
24924.75elapsed-sum/23993.00retainedCPU. Adopt two external meters once, no
nested observations added. Legacyguard2546.091499549272 remains separate.
Parent control review PASS: reviewed source, artifact-only inputs, exact two
commands/fresh outputs and inclusive funding are bound before dispatch.
