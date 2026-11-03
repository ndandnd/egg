# Scoped continuation after qualification 01

Prepared on 2 November, execution pending separate approval. Source revision ead4242109f33911efb892b3762a0f22d2341bea. This control, its own commit and the source pin identify the proposed continuation. Preserve attempt01 and its 3.60 displayed CPU and 9.89 elapsed-sum seconds. Exclude all 416 successful historical assignments and all four successful two-bus fixtures. No fleet campaign, solver tuning, case substitution, dependency installation or second attempt under this control.

Three distinct endpoints failed. The installed case33bw file and the independent AC backend were never reached. Make only the missing installed packaging 23.2 distribution visible to that process. For the unpublished day diagnostic the native values were not retained, so the whole diagnostic must be paid for again to obtain a packet. The JSON writer converts comparison values to native Booleans. For the three public inputs retain the identical URLs, dates, validation and byte limits. Use the system HTTPS trust store, including verification on redirects. Received data remain local. Fetching alone does not qualify a German deployment scenario.

One serial dispatch each in the order below. The funding ceiling is 250 CPU seconds and 435 wall seconds inclusive of preparation, result inspection and closure. Allow 100 CPU/145 wall seconds to each of the first two endpoints, 30 CPU/120 wall to acquisition, and 20 CPU/25 wall for shared work. Stop remaining work if a process is unresolved or a resource ceiling is exceeded. Each numerical worker uses serial QDLDL, one native thread, and at most 5 GiB observed RSS. Local input staging and dependency visibility do not change numerical parameters or acceptance thresholds. The CPU and wall guards below interrupt early. The POSIX meter covers cold startup, child CPU and output. Monitor only the owned commands. Preserve failed or missing packets. No repeat on an ordinary failure. The resident-size observations from the numerical Python workers cover their processes; peak curl RSS is unknown unless separately observed. Resource accounting covers worker command times and identifies unmetered desk work separately.

Run from this worktree only after approval, with the same source tree at the control revision. Start with these commands, ending immediately if any preparation step fails.

    QDIR=/private/tmp/egg-opf-repair-20261102-a02
    mkdir "$QDIR" && mkdir "$QDIR/deps" || exit 1
    test -f /Users/nadan/Library/Python/3.12/lib/python/site-packages/packaging/__init__.py || exit 1
    ln -s /Users/nadan/Library/Python/3.12/lib/python/site-packages/packaging "$QDIR/deps/packaging" || exit 1
    export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 RAYON_NUM_THREADS=1
    export MPLCONFIGDIR="$QDIR/mpl" NUMBA_CACHE_DIR="$QDIR/numba"
    OPFPY=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3
    OPFENTRY='import atexit,resource,runpy,sys; atexit.register(lambda: print("peak_rss_bytes",resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,file=sys.stderr)); dep=sys.argv[1]; sys.path[:0]=[dep] if dep else []; sys.argv=sys.argv[2:]; runpy.run_path(sys.argv[0],run_name="__main__")'

Issue these bodies separately and check exit and resource receipts before dispatching the next one. The owner records each status even when nonzero.

    (ulimit -t 90 && /usr/bin/time -p /usr/bin/perl -e 'alarm 130; exec @ARGV' "$OPFPY" -I -B -c "$OPFENTRY" "$QDIR/deps" src/experiments/qualify_radial_opf.py --case33-only) > "$QDIR/case33.json" 2> "$QDIR/case33.meter"
    echo "$?" > "$QDIR/case33.exit"

    (ulimit -t 90 && /usr/bin/time -p /usr/bin/perl -e 'alarm 130; exec @ARGV' "$OPFPY" -I -B -c "$OPFENTRY" '' src/experiments/qualify_opf_day.py) > "$QDIR/day.json" 2> "$QDIR/day.meter"
    echo "$?" > "$QDIR/day.exit"

    (ulimit -t 25 && /usr/bin/time -p /usr/bin/perl -e 'alarm 110; exec @ARGV' "$OPFPY" -I -B -c "$OPFENTRY" '' src/experiments/pin_opf_inputs.py "$QDIR/inputs") > "$QDIR/inputs.json" 2> "$QDIR/inputs.meter"
    echo "$?" > "$QDIR/inputs.exit"

The numerical thresholds, data checks, input domains, algorithms, versioned source of the installed 33-bus case and environment are inherited from QUALIFICATION_FREEZE.md and INPUT_FREEZE.md. A completed acquisition is permission to assess its metadata and attribution, not empirical evidence for any fleet-price hypothesis.
