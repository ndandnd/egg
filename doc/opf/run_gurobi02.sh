#!/bin/sh
set -eu
out=src/runs/opf-matched-20261103-gurobi02
test ! -e "$out" && test ! -e "$out.meter" || exit 3
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 RAYON_NUM_THREADS=1
export MPLCONFIGDIR=/private/tmp/egg-simbench-static-ac-20261103/mpl
export NUMBA_CACHE_DIR=/private/tmp/egg-matched-numba
ulimit -t 1100
/usr/bin/time -p /usr/bin/perl -e 'alarm 1700; exec @ARGV' /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -I -B -c 'import sys, runpy, atexit, resource; atexit.register(lambda: print("peak_rss_bytes",resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,file=sys.stderr)); sys.path[:0]=["/private/tmp/egg-simbench-static-ac-20261103/lib","/private/tmp/egg-opf-repair-20261102-a02/deps"]; sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name="__main__")' src/experiments/repair_matched_hulls02.py "$out" >"$out.progress" 2>"$out.meter"
