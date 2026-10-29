# Twelfth focused-draft PDF snapshot — final referee clarifications

Reviewed source977f8ea9c68f1c97ecd9995628de8be0d19483b3. Two meaningful source refinements follow the fresh significance review: explicitly exclude same-batch chaining in the main and inherited model; concede Müller's population-update and fixed-matching aggregation overlap while isolating the unproved cross-matching containment bridge. The focused subsumption note and fresh referee addendum preserve novelty/significance uncertainty. This is a distinct consolidated review copy after source edits, not a rerun of successfulPDF11 or a scientific recalculation.

NEW120CPU/180wall inclusive for one compile and one110dpi render; each selfCPU60 and inherited90-second alarm. External POSIX meters include startup/build/export/shutdown. Configured numerical-library threads1; no scientific solver. Observed RSS/instantaneous containment and tool/static/agent/visual/remoteCPU UNKNOWN separately. No automatic retry. Require full180seconds before18:10:45UTC. Parent reviewed source/commands/environment/funding, with separate control commit/push before dispatch.

Exact compile, cwd paper/focused-theory-20261029:
```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir ../../output/pdf/focused-theory-20261029-v12 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /opt/homebrew/bin/tectonic --keep-logs --outdir ../../output/pdf/focused-theory-20261029-v12 main.tex' > compile12-console.txt 2> compile12-time.txt
```

After compileexit0, exact render, cwd repositoryroot:
```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir tmp/pdfs/focused-theory-20261029-v12 || exit 1
exec /usr/bin/env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 output/pdf/focused-theory-20261029-v12/main.pdf tmp/pdfs/focused-theory-20261029-v12/page' > paper/focused-theory-20261029/render12-console.txt 2> paper/focused-theory-20261029/render12-time.txt
```

Inspect every actual newPNG once in disjoint partitions. Prefix24114.81displayedCPU/25060.42elapsed-sum/24117.01retainedCPU; legacy2546.091499549272 separate. Adopt externalmeters once, no nestedcharge, oldsource/hash audit, scientific replay or otherexport. Consumedsource frozen throughcompile/render. Successfulvisualqualification doesnot establishsubmissionreadiness.
