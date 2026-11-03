# Analytical transition figure: prospective artifact freeze

Reviewed sources: 3e2aeda3d97d221c57bffd92c9e912d86add7303,
`make_transition_figure.py` and `render_transition_figure.py`, with the
independent `PAPER_FIGURE_SOURCE_REVIEW05.md`. This renders a proved literal
k=3 construction, not data, a scientific solver run, or model qualification.
Input constants are k=3, w=(1,2,4), B=80, K=148, H=Smax=380,
R=(0,6,12,18,24,30,36,42), fleet6, omitted constant operating fee.
No alternative case or layout selection after outcomes. Output namespace
`figures-transition` must not exist. Earlier artifact marker already applies.

NEW inclusive 50 CPU seconds / 60 wall seconds; body/wrapper at most30/45,
one configured native thread, observed RSS <=5GiB. The external POSIX meter
is adopted once. Source self-hash occurs once inside the paid body. The
previously admitted isolated Matplotlib3.9.4 runtime is reused, with no install
or scientific-environment change. A failure is retained, without auto-retry.
The 60-second outer alarm survives exec; the body receives the wrapper start
clock so runtime loading cannot reset its 45-second allowance. No child worker
is created. Parent/static/tool/visual inspection CPU remains UNKNOWN.

Exact command, cwd `paper/focused-theory-20261029`:

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 60; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 50
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -I -S -B render_transition_figure.py' > transition-figure-console.txt 2> transition-figure-time.txt
```

Require exit0, complete body receipt, resource pass, and actual visual review
before including the figure. PNG and PDF describe the same analytical object.
Closed prefix23969.33 displayedCPU/24900.82 elapsed-sum/23971.02 retainedCPU;
legacyguard2546.091499549272 separate. No nested double counting or exact
whole-session accounting claim.

Parent control review PASS: exact source, constants, fresh output, isolated
runtime, environment, command and inclusive funding are bound here. The two
reviewed panels distinguish exponential physical pieces from a simple hull;
they make no numerical-performance or computational-hardness claim.
