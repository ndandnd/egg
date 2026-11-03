#!/bin/sh
# Frozen single-host review of the published scenarios and revised comparison.
set -eu
umask 077
ulimit -t 200
dest=/private/tmp/egg-pr57-sensitivity-review-20261102-a01
mkdir "$dest"
git archive 81a7993b3e72f0304705955389aabaa1e43b2b6a paper/draft1/code paper/draft1/data/peak_runs.json paper/draft1/results/study.json > "$dest/inputs.tar"
tar -xf "$dest/inputs.tar" -C "$dest"
cd "$dest/paper/draft1"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
exec /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -I -B - <<'PY'
import json, os, resource, subprocess, sys, time
from pathlib import Path
out = Path.cwd().parents[1]
published = json.loads(Path("results/study.json").read_text())["sweeps"]
stages = [
    ("published_intervals", [sys.executable, "-I", "-S", "-B", "code/gap_bands.py", "--output", str(out/"bands.json")], 90),
    ("revised_study", [sys.executable, "-B", "code/study.py"], 120),
    ("independent_assignments", [sys.executable, "-B", "code/check_review.py"], 60),
]
for label, command, limit in stages:
    start = time.monotonic()
    with (out / (label+".log")).open("x") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=limit)
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    print(label, result.returncode, round(time.monotonic()-start, 3), "s; cumulative child peak RSS", peak, flush=True)
    if result.returncode or peak > 5*2**30:
        raise SystemExit(1)
revised = json.loads(Path("results/study.json").read_text())["sweeps"]
if published != revised:
    raise SystemExit("Published and revised sweep rows differ; preserve both and investigate.")
print("All published sweep rows reproduced, including all cycle flags and objectives.")
PY
