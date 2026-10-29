# Fourth focused-draft PDF snapshot — prospective artifact freeze

Scientific TeX/Bib/figure source is fa0b8c03b81a582e316b48cba1427e35f9b29307.
This snapshot implements the independently reviewed focused structure:
principal frontier/public results in the body, complete secondary analyses
and proofs in appendices, with the qualified classical regret bound.
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
mkdir ../../output/pdf/focused-theory-20261029-v4 || exit 1
exec /opt/homebrew/bin/tectonic --keep-logs --outdir ../../output/pdf/focused-theory-20261029-v4 main.tex' > compile04-console.txt 2> compile04-time.txt
```

Only after compile exit0, render cwd repository root:

```sh
set -C
/usr/bin/time -p /usr/bin/perl -e 'alarm 90; exec @ARGV or die $!;' /bin/sh -c 'ulimit -t 60
mkdir tmp/pdfs/focused-theory-20261029-v4 || exit 1
exec /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm -png -r 110 output/pdf/focused-theory-20261029-v4/main.pdf tmp/pdfs/focused-theory-20261029-v4/page' > paper/focused-theory-20261029/render04-console.txt 2> paper/focused-theory-20261029/render04-time.txt
```

Every rendered page must be visually inspected. Any material defect gets a
specific repair and fresh separately metered snapshot, preserving this one.
Closed prefix23910.30displayedCPU/24838.79elapsed-sum/23911.77retainedCPU.
The two external meters are adopted once; no nested observation is added.
No native solver, data generation, model fit or consumed-source modification.
