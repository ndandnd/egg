#!/bin/sh
# Regenerate results, figures and the PDF for draft1.
# Requires: python3 with numpy, scipy, matplotlib, openpyxl; tectonic.
# SISTIG_ROOT must point at 10__data/20__Selected_transport_operators of the
# extracted archive doi:10.6084/m9.figshare.26088190.v1 (only for calibrate;
# the derived data/peak_runs.json is committed).
set -e
cd "$(dirname "$0")"
mkdir -p results figures build
if [ "${1:-}" = "--pdf-only" ]; then
  exec tectonic --keep-logs --outdir build main.tex
fi
if [ -n "$SISTIG_ROOT" ]; then
  (cd code && python3 calibrate.py "$SISTIG_ROOT" ../data/peak_runs.json)
fi
(cd code && python3 study.py > ../results/study_stdout.txt && python3 figures.py)
review_tmp=$(mktemp -d)
trap 'rm -f "$review_tmp/gap_bands.json"; rmdir "$review_tmp"' EXIT
python3 -I -S -B code/gap_bands.py --output "$review_tmp/gap_bands.json"
mv "$review_tmp/gap_bands.json" results/gap_bands.json
python3 -B code/check_review.py
if [ "$1" = "--tests" ]; then (cd code && python3 test_twobatch.py); fi
tectonic --keep-logs --outdir build main.tex
