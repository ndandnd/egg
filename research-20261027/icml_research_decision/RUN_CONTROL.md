# Frozen literal run control

Reviewed source: `4a20f8da41c81f75b3a68527371140850606c5e1` on `codex/ml-prediction-20261017`.
This control is committed separately before dispatch. Parent review: PASS for the literal check only. Namespace: `research-20261027/icml_research_decision/literal_attempt01`, not an EVSP attempt. No preparation, solver, data generation, training or further child is authorized.

NEW allowance5CPU/10wall; script CPU3soft/4hard and alarm5. One isolated stdlib interpreter, all numerical-thread environment variables below1. External POSIX meter covers the interpreter including startup/publication; shell/tool/review costs are not whole-session metered and are not claimed zero. All historical charges remain intact. Any nonzero exit/incomplete publication/limit violation closes this version without retry.

Exact shell command, working directory `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017`:

```sh
set -C
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 /usr/bin/time -p .venv-local/bin/python -I -S -B research-20261027/icml_research_decision/literal_check.py --source-revision 4a20f8da41c81f75b3a68527371140850606c5e1 --output research-20261027/icml_research_decision/literal_attempt01 > research-20261027/icml_research_decision/literal_stdout.txt 2> research-20261027/icml_research_decision/literal_stderr_and_time.txt
```

`set -C` prevents overwriting the stdout/meter files; the script independently refuses an existing output directory. Source self-hash is computed only inside this metered run from one consumed source buffer. No expected-source hash is recomputed by reviewers. No actual transport inputs, old metadata or artifact-supplied paths are read.

Allowed closeout: read new results/meter once, reconcile overlapping external/self observations, save a compact interpretation/resource handoff, and back up this meaningful milestone. No repeated check/readout/export/hash or transport dispatch follows automatically.
