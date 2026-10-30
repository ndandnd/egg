# Ninth focused-draft PDF snapshot — prospective consolidated freeze

Reviewed source 1908e34ba2e46d687d15ce1cf04227dba42f3ff9. Changes since08:
explicit feasible-anchor membership; independently derived/reviewed setup
matching counterexample; exact classical charge-only fixed-matching and
duty-MILP appendix; associated cross-references. Fresh source reviews PASS.
No numerical result, public input, figure or certificate is rerun or changed.
All prior snapshots, defects, failed attempts and charges remain preserved.

NEW120CPU/180wall inclusive for one compile and one110dpi render, each
selfCPU60 and inherited90-second alarm. Basic external POSIX meters cover
startup, build/export and shutdown. One configured numerical-library thread,
no native scientific solver. Observed RSS/instantaneous process-tree containment
UNKNOWN for these artifact meters; tool/static/agent/visual/remote CPU UNKNOWN
separately. Parent owns exact sessions. No automatic retry or source/hash audit.

Exact compile command, cwd paper/focused-theory-20261029:
```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir ../../output/pdf/focused-theory-20261029-v9 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /opt/homebrew/bin/tectonic --keep-logs --outdir ../../output/pdf/focused-theory-20261029-v9 main.tex' > compile09-console.txt 2> compile09-time.txt
```

Only after compile exit0, exact render command, cwd repository root:
```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir tmp/pdfs/focused-theory-20261029-v9 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 output/pdf/focused-theory-20261029-v9/main.pdf tmp/pdfs/focused-theory-20261029-v9/page' > paper/focused-theory-20261029/render09-console.txt 2> paper/focused-theory-20261029/render09-time.txt
```

Inspect every actual new PNG once in disjoint bounded page partitions.
No old render/export/scientific replay. Prefix24042.75displayedCPU/
24985.11elapsed-sum/24044.79retainedCPU, legacy2546.091499549272 separate.
Adopt both external meters once with rounding allowances; no child doublecount.
Full180seconds must remain before18:10:45UTC. Parent exact source-delta,
command, environment and allowance review PASS. Commit and push this separate
control before dispatch. Consumed sources frozen through this snapshot.
