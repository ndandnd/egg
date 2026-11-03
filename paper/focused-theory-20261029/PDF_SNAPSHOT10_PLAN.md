# Tenth focused-draft PDF snapshot — prospective repaired build

Reviewed source90784b7e172d10855c6b7a999393fd9d056b7bfc. PDF09 is CLOSED_FAILED:
standard appendix lettering exceeded Z, no finished PDF/render. Its failed
0.37CPU/.42wall, retained.41, and all outputs are preserved. This deliberately
separate build groups the two new setup sections within the existing setup
appendix and shortens one overlong opening paragraph. Parent source review:
only section hierarchy/editorial wording changed; proofs, data, figures and
certificates are unchanged. No retry of09 namespace or command.

NEW120CPU/180wall inclusive for one compile and one110dpi render; each selfCPU60
and inherited90-second alarm. External POSIX meters include startup/build/export/
shutdown. Configured numerical-library threads1; no scientific solver. RSS and
instantaneous process-tree containment UNKNOWN under these artifact meters;
tool/static/agent/visual/remote CPU UNKNOWN separately. No automatic retry.

Exact compile command, cwd paper/focused-theory-20261029:
```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir ../../output/pdf/focused-theory-20261029-v10 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /opt/homebrew/bin/tectonic --keep-logs --outdir ../../output/pdf/focused-theory-20261029-v10 main.tex' > compile10-console.txt 2> compile10-time.txt
```

Only after compile exit0, exact render command, cwd repository root:
```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir tmp/pdfs/focused-theory-20261029-v10 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 output/pdf/focused-theory-20261029-v10/main.pdf tmp/pdfs/focused-theory-20261029-v10/page' > paper/focused-theory-20261029/render10-console.txt 2> paper/focused-theory-20261029/render10-time.txt
```

Inspect all actual new PNGs once in disjoint page partitions. Prefix24043.12
displayedCPU/24985.53elapsed-sum/24045.20retainedCPU; legacy2546.091499549272
separate. Adopt both external meters once, no nested observations. No old
source/hash audit, rerender/export or scientific replay. Full180seconds must
remain before18:10:45UTC. Parent source/command/environment/allowance review
PASS under the autonomous research window. Commit/push separate control
before dispatch. Consumed source frozen through build and rendering.
