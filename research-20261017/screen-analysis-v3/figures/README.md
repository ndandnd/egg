# Completed development screen figure

`local_ranking_screen_v3.png`, `.pdf`, and `.svg` show all 20 independent timetable
medians for v8 and the newly trained CatBoost comparator versus the frozen nonlearned
ranking, plus validity counts for all six arms. The 40-trip and 80-trip panels use
explicitly separate x scales to preserve their markedly different ranges. Every point
requires three valid positive-bill seed pairs. None of these 40 model/group medians
is missing. Exact rational bill fields are used through the median; conversion to
floating point occurs only for display and CSV percentage columns.

Validity follows the stored worker and supervisor receipts, including censoring;
physical replay was not rerun. Counts out of 60 decisions: v8 60, CatBoost 60,
nonlearned 60, random 59, full4 44, cold8 59. The shaded remainder is absence of a
valid endpoint, not necessarily a solver infeasibility diagnosis. Results concern
synthetic development timetables at a 60-second end-to-end budget, not final tests.

`per_group.csv` contains 40 model/group rows; `per_cell_endpoints.csv` contains all
360 decisions. `plot_provenance.json` hashes the lock and 720 input receipt files.
No native JSONL, raw stdout/stderr, private tracebacks, models or solver calls were
read or executed for this figure. The parent analysis outputs are untouched.

Reproduce with the worktree's `.venv-local/bin/python` and `sourceplot.py` after moving
previous figure outputs aside; the script refuses to overwrite its own figure/CSV
files. The PNG was visually inspected for label clarity and clipping.
