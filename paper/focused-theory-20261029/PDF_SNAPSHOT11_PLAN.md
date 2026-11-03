# Eleventh focused-draft PDF snapshot — consolidated review copy

Reviewed source eb2633fc88886a6395dac744d319f83b55e4ec97. Parent reviewed the narrow integration diff: newly verified Müller etal cost-aggregation prior art, separate exact-additive solver-free portability, precise trust limits and updated certificate index. The independent portable interpretation review passed. Existing proofs, numerical inputs, figures and all old attempts remain unchanged. PDF10 remains the earlier66-page reviewed copy; this is a distinct snapshot, not a rerender or retry.

NEW120CPU/180wall inclusive for one compile and one110dpi render; each selfCPU60 and inherited90-second alarm. External POSIX meters include startup/build/export/shutdown. Configured numerical-library threads1; no scientific solver. RSS and instantaneous process-tree containment UNKNOWN under these artifact meters; tool/static/agent/visual/remote CPU UNKNOWN separately. No automatic retry. Require full180seconds remaining before18:10:45UTC.

Exact compile command, cwd paper/focused-theory-20261029:
```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir ../../output/pdf/focused-theory-20261029-v11 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /opt/homebrew/bin/tectonic --keep-logs --outdir ../../output/pdf/focused-theory-20261029-v11 main.tex' > compile11-console.txt 2> compile11-time.txt
```

Only after compile exit0, exact render command, cwd repository root:
```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir tmp/pdfs/focused-theory-20261029-v11 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 output/pdf/focused-theory-20261029-v11/main.pdf tmp/pdfs/focused-theory-20261029-v11/page' > paper/focused-theory-20261029/render11-console.txt 2> paper/focused-theory-20261029/render11-time.txt
```

Inspect all actual new PNGs once in disjoint page partitions. Prefix24102.45displayedCPU/25047.67elapsed-sum/24104.61retainedCPU; legacy2546.091499549272 separate. Adopt both external meters once, no nested observations or scientific/source/hash audit. Parent source/command/environment/allowance review PASS under the autonomous research window. Commit/push this separate control before dispatch. Consumed sources stay frozen through compile/render. No submission-ready claim follows from a successful build.
