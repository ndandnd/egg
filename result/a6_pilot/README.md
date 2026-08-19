# A6 burned-pilot selection

Canonical artifact: [`20260819T005514Z/SELECTION.json`](20260819T005514Z/SELECTION.json).

The 24-cell burned-seed implementation pilot passed its full audit: 12/12
`a6_a4` and 12/12 `a6_a3` cells were complete, sane, certified, OPTIMAL,
and replay-valid. The prespecified one-shot selection rule chose
`a6_a4`: `a6_a3` won 2/12 matched scores, below the required 9/12.

These pilot results are development evidence used only to select the
single holdout arm. They are not holdout evaluation evidence. The frozen
decision and provenance are recorded in `doc/DECISION_LOG.md`.
