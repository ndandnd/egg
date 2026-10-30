# Final legend correction

Both v2 images were inspected. Titles fit, but the first panel legend still
intersects the horizontal physical branch. Version3 changes only this legend
to7-point type with tighter line spacing, and writes a fresh figures-v3 folder.
The v2 images and receipt remain unchanged. Their charge is0.48CPU/0.63elapsed,
retained0.50. This is ordinary visual editing of unchanged formulas.

One command after source commit, new50CPU/60wall allowance with existing
script30CPU/45wall limits; inclusive external meter adopted once:

OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /usr/bin/time -p /Users/nadan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -I -B paper/focused-theory-20261029/render_figures_v3.py > paper/focused-theory-20261029/figure-v3-time.txt 2>&1
