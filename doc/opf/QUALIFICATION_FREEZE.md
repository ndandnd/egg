# OPF qualification 01

Source revision 853967d5, three disjoint commands. Assessment precedes the scaled joint-fleet study. Executable and solver versions come from the installed Python 3.12 system environment, NumPy 1.26.4, SciPy 1.13.1, cvxpy 1.6.0, Clarabel 0.9.0 with serial QDLDL selected explicitly, pandas 2.2.1 and pandapower distribution 2.14.11. DefaultSettings in Clarabel 0.9 lacks the later max_threads field. All units, thresholds and analytic fixtures live in the source and model memo. Source and benchmarks are upstream Git objects except the installed pandapower case33bw.json and AC/solver packages named above. Use only the 416 synthetic T1 cells and their corresponding two archive directories identified in the replay program. No other experiments are input. Pin generated observations to this source. Controls do not authorize a new fleet campaign.

Run the lines below from this worktree at most once. QDIR must start absent, commands serial. Each command uses its own output/meter; the meter includes cold imports. The allowance per child is 100 CPU seconds, 145 wall, 5 GiB observed maximum RSS, one native math thread. The external deadline is 130 seconds and CPU guard 90. Total package 335 CPU seconds/475 wall inclusive of already consumed 0.15 CPU/2.48 wall input acquisition, local staging/receipt allowances, three potential child runs. Subprocess figures overlap each external meter. No automatic retry. An ordinary failure in one independent test is reported and does not change another's assigned inputs. Unresolved ownership or resource violation ends remaining dispatches. Report exactness failures within each case and every dependency failure. Full live re-dispatch of the 49,993-solve historical campaign is outside this allowance. No raw data redistribution or source copy of the brief.

    QDIR=/private/tmp/egg-opf-qualification-20261102-a01
    mkdir "$QDIR"
    export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 RAYON_NUM_THREADS=1
    export MPLCONFIGDIR="$QDIR/mpl" NUMBA_CACHE_DIR="$QDIR/numba"
    for task in qualify_ideal_history qualify_radial_opf qualify_opf_day
    do
        (ulimit -t 90 && /usr/bin/time -p /usr/bin/perl -e 'alarm 130; exec @ARGV' /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -I -B -c 'import atexit,resource,runpy,sys; atexit.register(lambda: print("peak_rss_bytes",resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,file=sys.stderr)); runpy.run_path(sys.argv[1],run_name="__main__")' "src/experiments/$task.py") > "$QDIR/$task.json" 2> "$QDIR/$task.meter"
        echo "$?" > "$QDIR/$task.exit"
    done

The shell loop above describes independent dispatches; the owner may issue its bodies consecutively to examine exit/resource receipts between them. Impose exclusive output directory before the first body. Success requires exact coverage and the checks in each script. A conditional replay with cached responses preserves the old tie choices, and does not establish robustness to re-solving a MILP at small conic-dual errors. The conic test and the analytical recurrence check are complementary.

**Independent public-source acquisition.** Input worker 16197 exited 1 after three TLS trust-chain errors. Two Energinet days and the SimBench archive all failed before data admission. Original resource meter 0.08 user + 0.07 system s, 2.48 elapsed. The unaltered compact receipt is under result/opf_qualification/input01.json. No scientific input replacement or TLS bypass.
