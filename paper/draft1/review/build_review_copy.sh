#!/bin/sh
set -eu
umask 077
ulimit -t 60
stage=/private/tmp/egg-pr57-reviewed-pdf-20261102-a01
mkdir "$stage"
git archive c593bc759a72e030956be3c686f958aa02592d6b paper/draft1/main.tex paper/draft1/appendix.tex paper/draft1/references.bib paper/draft1/figures paper/draft1/make.sh > "$stage/source.tar"
tar -xf "$stage/source.tar" -C "$stage"
cd "$stage/paper/draft1"
export PATH=/opt/homebrew/bin:/usr/bin:/bin
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
/bin/sh make.sh --pdf-only
mkdir "$stage/pages"
/Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 build/main.pdf "$stage/pages/page"
