#!/bin/sh
# Explicit editorial continuation of the successfully rendered 25-page review build.
# Figure 1's annotation touched a leader, Figure 2's legend covered data, and
# three reproducibility lines spilled onto page 25. Preserve build 01 and its costs.
# One fresh run from the checkout: /usr/bin/time -p /usr/bin/perl -e 'alarm 180; exec @ARGV or die $!;' /bin/sh paper/draft1/review/build_circulation_copy.sh
# Redirect stdout and stderr exclusively to the adjacent /private/tmp a02.stdout and a02.time paths.
# Inclusive 120 CPU seconds / 180 wall seconds; per-tool CPU 60; one configured native thread.
# Render the existing two illustrations from their reviewed sources and fixed inputs.
# No calibrated study, certificate, fitting or new scientific search.
set -eu
umask 077
ulimit -t 60
stage=/private/tmp/egg-pr57-reviewed-pdf-20261102-a02
mkdir "$stage"
git archive 989f855d15befa881674b7a258be6c57a133b417 paper/draft1/main.tex paper/draft1/appendix.tex paper/draft1/references.bib paper/draft1/figures paper/draft1/make.sh paper/draft1/code/figures.py paper/draft1/code/twobatch.py paper/draft1/results/study.json > "$stage/source.tar"
tar -xf "$stage/source.tar" -C "$stage"
cd "$stage/paper/draft1"
export PATH=/opt/homebrew/bin:/usr/bin:/bin
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export MPLCONFIGDIR="$stage/mpl"
(cd code && /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -B -c 'import figures; figures.fig_anchor(); figures.fig_critical()')
/bin/sh make.sh --pdf-only
mkdir "$stage/pages"
/Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 build/main.pdf "$stage/pages/page"
