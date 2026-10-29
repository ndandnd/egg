# Eighth focused-draft PDF snapshot — prospective editorial freeze

Reviewed source d237b8ba50b31d4fd90976a2377b8d05a44ec661. Changes from07 are
the documented signed-domain cross-reference correction, rephrased overlong
lines/heading, removal of a page-split inline formula, and a clear appendix
page break. No theorem, scientific calculation, dataset, figure or certificate
is changed or rerun. All07 outputs, visual defects and costs remain preserved.

NEW120CPU/180wall inclusive for one compile and one110dpi render, each selfCPU60
and inherited90-second alarm. Basic external POSIX meters include startup,
build/export and shutdown. Exact sessions closed by parent. No automatic retry.
Configured numerical-library threads1; no native scientific solver. RSS and
instantaneous process-tree containment UNKNOWN under these artifact meters;
tool/static/agent/visual/remote CPU UNKNOWN separately. No source/hash audits.

Exact compile command, cwd paper/focused-theory-20261029:
```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir ../../output/pdf/focused-theory-20261029-v8 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /opt/homebrew/bin/tectonic --keep-logs --outdir ../../output/pdf/focused-theory-20261029-v8 main.tex' > compile08-console.txt 2> compile08-time.txt
```

Only after compile exit0, exact render command, cwd repository root:
```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir tmp/pdfs/focused-theory-20261029-v8 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 output/pdf/focused-theory-20261029-v8/main.pdf tmp/pdfs/focused-theory-20261029-v8/page' > paper/focused-theory-20261029/render08-console.txt 2> paper/focused-theory-20261029/render08-time.txt
```

Inspect all actual new PNGs once, bounded parent/reviewer page partitions.
No old render, export, proof or science replay. Closed prefix24029.71displayedCPU/
24969.91elapsed-sum/24031.71retainedCPU; legacy2546.091499549272 separate.
Adopt two meters once, no nested observation added. Full180seconds must remain
before18:10:45UTC. Parent source-delta/control review PASS. Commit and push this
separate control before dispatch. Source frozen through the snapshot.
