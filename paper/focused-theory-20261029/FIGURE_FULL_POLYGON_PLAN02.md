# Frozen v2 layout-repair illustration command

Reviewed new source df17345af1db1d65501c485f2358906f5a5f07ba.
Only layout/output-version changes relative to the closed v1; see
FIGURE_FULL_POLYGON_REPAIR02.md. No numerical result, case, proof or source
input is changed or replayed. Old sources, outputs and charges stay frozen.

NEW50CPU60wall inclusive, same internal45CPU55wall, one configured thread,
observedRSS5GiB ceiling. Cached new source buffers hash once inside the meter;
existing admitted artifact runtime/font cache may be reused. External meter
includes all startup/loading/drawing/export/publication/waitedchild/shutdown.
No exact whole-session or instantaneous aggregate memory claim.

Exact command, cwd /Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017:

```sh
set -C
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /usr/bin/time -p /Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/.venv-local/bin/python -I -S -B /Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/paper/focused-theory-20261029/render_full_polygon_figure_v2.py --source-revision df17345af1db1d65501c485f2358906f5a5f07ba > paper/focused-theory-20261029/full-polygon-figure02-console.txt 2> paper/focused-theory-20261029/full-polygon-figure02-time.txt
```

Fresh exclusive outputs figures/full_lossy_polygon-v2.pdf/png and itsreceipt.
One render only after this separate control is committed/pushed; no automatic
retry. Actual new PNG inspection required. Current closedprefix24014.69CPU/
24950.65elapsed-sum/24016.60retained, legacyguard2546.091499549272 separate.
Parent/tool/static/visualQA CPU UNKNOWN. Launch only with full60seconds before
18:10:45UTC. Parent exact delta/command/resources/source review PASS.
