# Third focused-draft PDF snapshot — prospective artifact freeze

Scientific TeX/Bib/figure source is c4a06fa9a3b8d5db21bb54023a123ce0a998b336.
This snapshot includes the refined public interval, portable verification,
common-loss frontier/proofs, algorithmic consequences and explicit scope.
It remains an internal research draft. No scientific computation is repeated.

NEW120CPU/180wall inclusive for one compile and one110dpi rendering. Each
command has selfCPU60 and inherited90-second wall alarm, external POSIX meter,
exclusive log files and a fresh output directory. Parent closes exact sessions
and preserves failures; no automatic rerun. The earlier PDF artifact marker
already applies, and is not repeated. Tool/static/visualQA CPU is UNKNOWN.

Compile cwd paper/focused-theory-20261029, exact shell command:

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir ../../output/pdf/focused-theory-20261029-v3 || exit 1
exec /opt/homebrew/bin/tectonic --keep-logs --outdir ../../output/pdf/focused-theory-20261029-v3 main.tex' > compile03-console.txt 2> compile03-time.txt
```

Only after compile exit0, render cwd repository root:

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir tmp/pdfs/focused-theory-20261029-v3 || exit 1
exec /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 output/pdf/focused-theory-20261029-v3/main.pdf tmp/pdfs/focused-theory-20261029-v3/page' > paper/focused-theory-20261029/render03-console.txt 2> paper/focused-theory-20261029/render03-time.txt
```

Every rendered page must be visually inspected. Any material defect gets a
specific repair and fresh separately metered snapshot, preserving this one.
Closed prefix23902.64displayedCPU/24830.82elapsed-sum/23904.07retainedCPU.
The two external meters are adopted once; no nested observation is added.
No native solver, data generation, model fit or consumed-source modification.
