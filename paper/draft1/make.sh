#!/bin/sh
# Regenerate results, figures and the PDF for draft1.
# Requires: python3 with numpy, scipy, matplotlib, openpyxl; tectonic.
# SISTIG_ROOT must point at 10__data/20__Selected_transport_operators of the
# extracted archive doi:10.6084/m9.figshare.26088190.v1 (only for calibrate).
set -e
cd "$(dirname "$0")"
if [ -n "$SISTIG_ROOT" ]; then
  (cd code && python3 calibrate.py "$SISTIG_ROOT" ../data/peak_runs.json)
fi
(cd code && python3 study.py > ../results/study_stdout.txt && python3 figures.py)
if [ "$1" = "--tests" ]; then (cd code && python3 test_twobatch.py); fi
tectonic --keep-logs main.tex
